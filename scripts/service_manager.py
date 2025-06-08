#!/usr/bin/env python3
"""
Service Management Script für Legal Tech System
Überwacht und verwaltet alle Services (API, Streamlit, LM Studio)
"""

import os
import sys
import time
import json
import signal
import subprocess
import requests
from pathlib import Path
from typing import Dict, List, Optional
from datetime import datetime
import logging
from dataclasses import dataclass

# Logging setup
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('data/logs/service_manager.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


@dataclass
class ServiceConfig:
    """Konfiguration für einen Service"""
    name: str
    command: List[str]
    port: int
    health_endpoint: str
    working_dir: Optional[str] = None
    env_vars: Optional[Dict[str, str]] = None
    required: bool = True
    startup_delay: int = 0


class ServiceManager:
    """Verwaltet alle Services für das Legal Tech System"""
    
    def __init__(self, config_file: str = "config/services.json"):
        self.config_file = Path(config_file)
        self.services: Dict[str, subprocess.Popen] = {}
        self.service_configs: Dict[str, ServiceConfig] = {}
        self.running = False
        
        # Lade Service-Konfiguration
        self.load_service_config()
        
        # Signal Handler für graceful shutdown
        signal.signal(signal.SIGINT, self.signal_handler)
        signal.signal(signal.SIGTERM, self.signal_handler)
    
    def load_service_config(self):
        """Lade Service-Konfiguration"""
        default_config = {
            "fastapi": {
                "name": "FastAPI Backend",
                "command": ["python", "-m", "uvicorn", "src.api.main:app", "--reload", "--port", "8000"],
                "port": 8000,
                "health_endpoint": "/health",
                "required": True,
                "startup_delay": 2
            },
            "streamlit": {
                "name": "Streamlit Frontend", 
                "command": ["streamlit", "run", "streamlit_app.py", "--server.port", "8501"],
                "port": 8501,
                "health_endpoint": "/",
                "required": True,
                "startup_delay": 5
            },
            "lm_studio": {
                "name": "LM Studio",
                "command": [],  # External service
                "port": 1234,
                "health_endpoint": "/v1/models",
                "required": False,
                "startup_delay": 0
            }
        }
        
        # Lade Konfiguration von Datei oder verwende Default
        if self.config_file.exists():
            try:
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    config_data = json.load(f)
            except Exception as e:
                logger.warning(f"Could not load config file: {e}, using defaults")
                config_data = default_config
        else:
            config_data = default_config
            # Speichere Default-Konfiguration
            self.save_service_config(config_data)
        
        # Konvertiere zu ServiceConfig Objekten
        for service_id, config in config_data.items():
            self.service_configs[service_id] = ServiceConfig(**config)
    
    def save_service_config(self, config_data: Dict):
        """Speichere Service-Konfiguration"""
        try:
            self.config_file.parent.mkdir(parents=True, exist_ok=True)
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(config_data, f, indent=2, ensure_ascii=False)
        except Exception as e:
            logger.error(f"Could not save config file: {e}")
    
    def check_port_available(self, port: int) -> bool:
        """Prüfe ob Port verfügbar ist"""
        try:
            import socket
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.settimeout(1)
                result = s.connect_ex(('localhost', port))
                return result != 0
        except Exception:
            return False
    
    def check_service_health(self, service_id: str) -> bool:
        """Prüfe Service-Gesundheit"""
        config = self.service_configs[service_id]
        
        try:
            url = f"http://localhost:{config.port}{config.health_endpoint}"
            response = requests.get(url, timeout=5)
            return response.status_code == 200
        except Exception:
            return False
    
    def start_service(self, service_id: str) -> bool:
        """Starte einzelnen Service"""
        config = self.service_configs[service_id]
        
        # Prüfe ob Service bereits läuft
        if service_id in self.services:
            if self.services[service_id].poll() is None:
                logger.info(f"Service {config.name} is already running")
                return True
        
        # Externe Services (wie LM Studio) nicht starten
        if not config.command:
            logger.info(f"External service {config.name} - checking availability")
            return self.check_service_health(service_id)
        
        # Prüfe Port-Verfügbarkeit
        if not self.check_port_available(config.port):
            logger.error(f"Port {config.port} for {config.name} is already in use")
            return False
        
        try:
            logger.info(f"Starting {config.name}...")
            
            # Umgebungsvariablen vorbereiten
            env = os.environ.copy()
            if config.env_vars:
                env.update(config.env_vars)
            
            # Service starten
            process = subprocess.Popen(
                config.command,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                cwd=config.working_dir,
                env=env,
                text=True,
                bufsize=1,
                universal_newlines=True
            )
            
            self.services[service_id] = process
            
            # Warte auf Startup
            if config.startup_delay > 0:
                logger.info(f"Waiting {config.startup_delay}s for {config.name} to start...")
                time.sleep(config.startup_delay)
            
            # Prüfe ob Service erfolgreich gestartet
            if process.poll() is None:
                logger.info(f"Service {config.name} started successfully")
                return True
            else:
                logger.error(f"Service {config.name} failed to start")
                return False
                
        except Exception as e:
            logger.error(f"Failed to start {config.name}: {e}")
            return False
    
    def stop_service(self, service_id: str):
        """Stoppe einzelnen Service"""
        if service_id not in self.services:
            return
        
        config = self.service_configs[service_id]
        process = self.services[service_id]
        
        try:
            logger.info(f"Stopping {config.name}...")
            
            # Graceful shutdown versuchen
            process.terminate()
            
            # Warte auf ordentliches Beenden
            try:
                process.wait(timeout=10)
            except subprocess.TimeoutExpired:
                logger.warning(f"Force killing {config.name}")
                process.kill()
                process.wait()
            
            del self.services[service_id]
            logger.info(f"Service {config.name} stopped")
            
        except Exception as e:
            logger.error(f"Error stopping {config.name}: {e}")
    
    def start_all_services(self) -> bool:
        """Starte alle Services"""
        logger.info("Starting all services...")
        
        success_count = 0
        required_count = 0
        
        for service_id, config in self.service_configs.items():
            if config.required:
                required_count += 1
                
            if self.start_service(service_id):
                success_count += 1
                
                # Prüfe Service-Gesundheit nach Start
                if config.command:  # Nur für gestartete Services
                    time.sleep(2)
                    if self.check_service_health(service_id):
                        logger.info(f"Service {config.name} health check passed")
                    else:
                        logger.warning(f"Service {config.name} health check failed")
            else:
                if config.required:
                    logger.error(f"Required service {config.name} failed to start")
                else:
                    logger.warning(f"Optional service {config.name} not available")
        
        self.running = True
        
        # Prüfe ob alle erforderlichen Services laufen
        if success_count >= required_count:
            logger.info(f"Successfully started {success_count} services")
            return True
        else:
            logger.error(f"Only {success_count} of {required_count} required services started")
            return False
    
    def stop_all_services(self):
        """Stoppe alle Services"""
        logger.info("Stopping all services...")
        
        for service_id in list(self.services.keys()):
            self.stop_service(service_id)
        
        self.running = False
        logger.info("All services stopped")
    
    def monitor_services(self):
        """Überwache Services und starte bei Bedarf neu"""
        logger.info("Starting service monitoring...")
        
        while self.running:
            try:
                for service_id, config in self.service_configs.items():
                    if service_id in self.services:
                        process = self.services[service_id]
                        
                        # Prüfe ob Prozess noch läuft
                        if process.poll() is not None:
                            logger.error(f"Service {config.name} has died, restarting...")
                            self.start_service(service_id)
                    
                    # Health Check
                    if not self.check_service_health(service_id):
                        logger.warning(f"Service {config.name} health check failed")
                
                time.sleep(30)  # Check every 30 seconds
                
            except KeyboardInterrupt:
                break
            except Exception as e:
                logger.error(f"Error in service monitoring: {e}")
                time.sleep(5)
    
    def show_status(self):
        """Zeige Status aller Services"""
        print("\n" + "="*50)
        print("SERVICE STATUS")
        print("="*50)
        
        for service_id, config in self.service_configs.items():
            status = "UNKNOWN"
            
            if service_id in self.services:
                process = self.services[service_id]
                if process.poll() is None:
                    status = "RUNNING"
                else:
                    status = "STOPPED"
            else:
                if self.check_service_health(service_id):
                    status = "EXTERNAL"
                else:
                    status = "NOT AVAILABLE"
            
            health = "✓" if self.check_service_health(service_id) else "✗"
            required = "(Required)" if config.required else "(Optional)"
            
            print(f"{config.name:20} [{status:12}] {health} Port: {config.port} {required}")
        
        print("="*50)
    
    def signal_handler(self, signum, frame):
        """Signal Handler für graceful shutdown"""
        logger.info(f"Received signal {signum}, shutting down...")
        self.running = False
        self.stop_all_services()
        sys.exit(0)


def main():
    """Hauptfunktion"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Legal Tech Service Manager")
    parser.add_argument("action", choices=["start", "stop", "restart", "status", "monitor"], 
                       help="Action to perform")
    parser.add_argument("--service", help="Specific service to act on")
    parser.add_argument("--config", default="config/services.json", 
                       help="Service configuration file")
    
    args = parser.parse_args()
    
    manager = ServiceManager(args.config)
    
    try:
        if args.action == "start":
            if args.service:
                success = manager.start_service(args.service)
                sys.exit(0 if success else 1)
            else:
                success = manager.start_all_services()
                if success:
                    print("\nAll services started successfully!")
                    print("Press Ctrl+C to stop all services")
                    manager.monitor_services()
                sys.exit(0 if success else 1)
        
        elif args.action == "stop":
            if args.service:
                manager.stop_service(args.service)
            else:
                manager.stop_all_services()
        
        elif args.action == "restart":
            if args.service:
                manager.stop_service(args.service)
                time.sleep(2)
                manager.start_service(args.service)
            else:
                manager.stop_all_services()
                time.sleep(2)
                manager.start_all_services()
        
        elif args.action == "status":
            manager.show_status()
        
        elif args.action == "monitor":
            manager.monitor_services()
            
    except KeyboardInterrupt:
        logger.info("Interrupted by user")
        manager.stop_all_services()
    except Exception as e:
        logger.error(f"Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
