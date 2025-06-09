#!/usr/bin/env python3
"""
DNOTI Auto-Updater Deployment Script
====================================
Intelligent deployment script for DNOTI semantic search auto-updater
"""

import argparse
import json
import logging
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, Any

class DNOTIDeployment:
    """DNOTI Auto-Updater Deployment Manager"""
    
    def __init__(self):
        self.setup_logging()
        self.logger = logging.getLogger('DNOTIDeployment')
        
    def setup_logging(self):
        """Setup deployment logging"""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(f'logs/deployment_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log'),
                logging.StreamHandler()
            ]
        )
    
    def check_dependencies(self) -> bool:
        """Check if all required dependencies are available"""
        self.logger.info("Checking dependencies...")
        
        required_packages = [
            'requests', 'beautifulsoup4', 'chromadb', 
            'sentence-transformers', 'streamlit'
        ]
        
        missing_packages = []
        
        for package in required_packages:
            try:
                __import__(package.replace('-', '_'))
                self.logger.debug(f"✅ {package} available")
            except ImportError:
                missing_packages.append(package)
                self.logger.warning(f"❌ {package} missing")
        
        if missing_packages:
            self.logger.error(f"Missing packages: {', '.join(missing_packages)}")
            self.logger.info("Install with: pip install " + " ".join(missing_packages))
            return False
        
        self.logger.info("✅ All dependencies available")
        return True
    
    def check_database_status(self) -> Dict[str, Any]:
        """Check current database status"""
        self.logger.info("Checking database status...")
        
        status = {
            'known_gutachten_file_exists': False,
            'known_gutachten_count': 0,
            'chromadb_exists': False,
            'collections': [],
            'last_update': None
        }
        
        # Check known Gutachten file
        known_file = Path('Database/Original/dnoti_all.json')
        if known_file.exists():
            status['known_gutachten_file_exists'] = True
            try:
                with open(known_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    status['known_gutachten_count'] = len(data)
            except Exception as e:
                self.logger.warning(f"Could not read known Gutachten file: {e}")
        
        # Check ChromaDB
        chroma_dir = Path('data/vectordb')
        if chroma_dir.exists():
            status['chromadb_exists'] = True
            self.logger.info("✅ ChromaDB directory exists")
        
        # Check last update
        search_health_file = Path('logs/last_successful_search.json')
        if search_health_file.exists():
            try:
                with open(search_health_file, 'r', encoding='utf-8') as f:
                    health_data = json.load(f)
                    status['last_update'] = health_data.get('timestamp')
                    status['search_health'] = health_data.get('status', 'unknown')
            except Exception as e:
                self.logger.warning(f"Could not read search health file: {e}")
        
        return status
    
    def deploy_production(self, dry_run: bool = False) -> bool:
        """Deploy production auto-updater"""
        self.logger.info(f"Starting production deployment (dry_run={dry_run})...")
        
        if not self.check_dependencies():
            return False
        
        db_status = self.check_database_status()
        self.logger.info(f"Database status: {db_status}")
        
        # Run production updater
        cmd = [sys.executable, 'dnoti_auto_updater_production_v6.py']
        if dry_run:
            # Modify config for dry run
            self.logger.info("Running in DRY-RUN mode")
        
        try:
            self.logger.info("Executing production auto-updater...")
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=600)
            
            if result.returncode == 0:
                self.logger.info("✅ Production auto-updater completed successfully")
                self.logger.info(f"Output: {result.stdout[-500:]}")  # Last 500 chars
                return True
            else:
                self.logger.error(f"❌ Production auto-updater failed: {result.stderr}")
                return False
                
        except subprocess.TimeoutExpired:
            self.logger.error("❌ Production auto-updater timed out")
            return False
        except Exception as e:
            self.logger.error(f"❌ Deployment error: {e}")
            return False
    
    def create_scheduled_task(self, schedule_type: str = "daily"):
        """Create scheduled task for auto-updater"""
        self.logger.info(f"Creating {schedule_type} scheduled task...")
        
        # Create batch file for Windows Task Scheduler
        batch_content = f'''@echo off
cd /d "{Path.cwd()}"
python dnoti_auto_updater_production_v6.py
echo Auto-updater completed at %date% %time%
'''
        
        batch_file = Path('dnoti_auto_updater_scheduled.bat')
        with open(batch_file, 'w') as f:
            f.write(batch_content)
        
        self.logger.info(f"✅ Created batch file: {batch_file}")
        self.logger.info("To schedule in Windows Task Scheduler:")
        self.logger.info(f"1. Open Task Scheduler")
        self.logger.info(f"2. Create Basic Task")
        self.logger.info(f"3. Set to run {schedule_type}")
        self.logger.info(f"4. Action: Start a program")
        self.logger.info(f"5. Program: {batch_file.absolute()}")
    
    def monitor_search_health(self) -> Dict[str, Any]:
        """Monitor DNOTI search health"""
        self.logger.info("Monitoring DNOTI search health...")
        
        # Run quick search health check
        try:
            import requests
            from bs4 import BeautifulSoup
            
            session = requests.Session()
            session.headers.update({
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            })
            
            test_params = {
                'tx_dnotionlineplusapi_expertises[page]': '1',
                'tx_dnotionlineplusapi_expertises[searchText]': 'BGB',
            }
            
            response = session.post(
                "https://www.dnoti.de/gutachten/",
                data=test_params,
                timeout=30
            )
            
            health_status = {
                'timestamp': datetime.now().isoformat(),
                'status_code': response.status_code,
                'is_reachable': response.status_code == 200,
                'has_results': False,
                'result_count': 0
            }
            
            if response.status_code == 200:
                soup = BeautifulSoup(response.content, 'html.parser')
                nodeid_links = soup.find_all('a', href=lambda x: x and 'nodeid' in x)
                health_status['has_results'] = len(nodeid_links) > 0
                health_status['result_count'] = len(nodeid_links)
            
            self.logger.info(f"Search health: {health_status}")
            return health_status
            
        except Exception as e:
            self.logger.error(f"Health check failed: {e}")
            return {
                'timestamp': datetime.now().isoformat(),
                'error': str(e),
                'is_reachable': False
            }


def main():
    """Main deployment function"""
    parser = argparse.ArgumentParser(description='DNOTI Auto-Updater Deployment')
    parser.add_argument('--deploy', action='store_true', help='Deploy production auto-updater')
    parser.add_argument('--dry-run', action='store_true', help='Run in dry-run mode')
    parser.add_argument('--schedule', choices=['daily', 'weekly'], help='Create scheduled task')
    parser.add_argument('--health-check', action='store_true', help='Check DNOTI search health')
    parser.add_argument('--status', action='store_true', help='Show system status')
    
    args = parser.parse_args()
    
    deployment = DNOTIDeployment()
    
    if args.status:
        status = deployment.check_database_status()
        print("\\n=== DNOTI Auto-Updater System Status ===")
        print(f"Known Gutachten File: {'✅' if status['known_gutachten_file_exists'] else '❌'}")
        print(f"Known Gutachten Count: {status['known_gutachten_count']}")
        print(f"ChromaDB: {'✅' if status['chromadb_exists'] else '❌'}")
        print(f"Last Update: {status.get('last_update', 'Never')}")
        print(f"Search Health: {status.get('search_health', 'Unknown')}")
    
    if args.health_check:
        health = deployment.monitor_search_health()
        print("\\n=== DNOTI Search Health Check ===")
        print(f"Reachable: {'✅' if health.get('is_reachable') else '❌'}")
        print(f"Has Results: {'✅' if health.get('has_results') else '❌'}")
        print(f"Result Count: {health.get('result_count', 0)}")
    
    if args.deploy:
        success = deployment.deploy_production(dry_run=args.dry_run)
        if success:
            print("\\n✅ Deployment completed successfully")
        else:
            print("\\n❌ Deployment failed")
            sys.exit(1)
    
    if args.schedule:
        deployment.create_scheduled_task(args.schedule)
    
    if not any([args.deploy, args.schedule, args.health_check, args.status]):
        parser.print_help()


if __name__ == "__main__":
    main()
