#!/usr/bin/env python3
"""
Production Startup Script for DNOTI Legal Tech
Comprehensive system initialization and monitoring
"""

import subprocess
import sys
import time
import os
import webbrowser
from pathlib import Path
import requests
import psutil
from datetime import datetime

class Colors:
    """ANSI color codes for terminal output."""
    BLUE = '\033[94m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    BOLD = '\033[1m'
    END = '\033[0m'

def print_banner():
    """Print startup banner."""
    print(f"""
{Colors.BLUE}{Colors.BOLD}
╔════════════════════════════════════════════════════════════════╗
║                    DNOTI LEGAL TECH                            ║
║                   Production Startup                           ║
║               KI-gestützte Semantische Suche                   ║
╚════════════════════════════════════════════════════════════════╝
{Colors.END}
""")

def check_requirements():
    """Check system requirements and dependencies."""
    print(f"{Colors.YELLOW}🔍 Checking system requirements...{Colors.END}")
    
    # Check Python version
    python_version = sys.version_info
    if python_version < (3, 8):
        print(f"{Colors.RED}❌ Python 3.8+ required. Current: {python_version.major}.{python_version.minor}{Colors.END}")
        return False
    
    print(f"{Colors.GREEN}✅ Python {python_version.major}.{python_version.minor}.{python_version.micro}{Colors.END}")
    
    # Check available memory
    memory = psutil.virtual_memory()
    available_gb = memory.available / (1024**3)
    if available_gb < 2:
        print(f"{Colors.YELLOW}⚠️  Low memory: {available_gb:.1f}GB available{Colors.END}")
    else:
        print(f"{Colors.GREEN}✅ Memory: {available_gb:.1f}GB available{Colors.END}")
    
    # Check ChromaDB database
    db_path = Path("./chroma_db/chroma.sqlite3")
    if db_path.exists():
        size_mb = db_path.stat().st_size / (1024*1024)
        print(f"{Colors.GREEN}✅ Database: {size_mb:.1f}MB{Colors.END}")
    else:
        print(f"{Colors.YELLOW}⚠️  Database not found - will be created{Colors.END}")
    
    return True

def install_dependencies():
    """Install required Python packages."""
    print(f"{Colors.YELLOW}📦 Installing dependencies...{Colors.END}")
    
    try:
        subprocess.check_call([
            sys.executable, "-m", "pip", "install", "-r", "requirements.txt", "--quiet"
        ])
        print(f"{Colors.GREEN}✅ Dependencies installed{Colors.END}")
        return True
    except subprocess.CalledProcessError as e:
        print(f"{Colors.RED}❌ Failed to install dependencies: {e}{Colors.END}")
        return False

def check_database():
    """Check and initialize database if needed."""
    print(f"{Colors.YELLOW}🗄️ Checking database...{Colors.END}")
    
    try:
        import chromadb
        client = chromadb.PersistentClient(path="./chroma_db")
        collection = client.get_collection("dnoti_gutachten")
        doc_count = collection.count()
        
        if doc_count > 0:
            print(f"{Colors.GREEN}✅ Database ready: {doc_count:,} documents{Colors.END}")
            return True
        else:
            print(f"{Colors.YELLOW}⚠️  Database empty - loading documents...{Colors.END}")
            return setup_database()
            
    except Exception as e:
        print(f"{Colors.YELLOW}⚠️  Database not found - creating new database...{Colors.END}")
        return setup_database()

def setup_database():
    """Setup and populate the database."""
    try:
        print(f"{Colors.YELLOW}📚 Loading documents into database...{Colors.END}")
        subprocess.check_call([sys.executable, "load_all_gutachten.py"])
        print(f"{Colors.GREEN}✅ Database setup complete{Colors.END}")
        return True
    except subprocess.CalledProcessError as e:
        print(f"{Colors.RED}❌ Database setup failed: {e}{Colors.END}")
        return False

def start_backend():
    """Start the FastAPI backend server."""
    print(f"{Colors.YELLOW}🚀 Starting FastAPI backend...{Colors.END}")
    
    try:
        # Start backend in background
        backend_process = subprocess.Popen([
            sys.executable, "-m", "uvicorn", 
            "src.api.main:app", 
            "--reload", 
            "--host", "0.0.0.0", 
            "--port", "8000"
        ], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        
        # Wait for backend to start
        for i in range(30):  # 30 second timeout
            try:
                response = requests.get("http://localhost:8000/health", timeout=1)
                if response.status_code == 200:
                    print(f"{Colors.GREEN}✅ Backend started at http://localhost:8000{Colors.END}")
                    return backend_process
            except:
                pass
            time.sleep(1)
        
        print(f"{Colors.RED}❌ Backend failed to start{Colors.END}")
        backend_process.kill()
        return None
        
    except Exception as e:
        print(f"{Colors.RED}❌ Backend startup error: {e}{Colors.END}")
        return None

def start_frontend():
    """Start the Streamlit frontend."""
    print(f"{Colors.YELLOW}🖥️ Starting Streamlit frontend...{Colors.END}")
    
    try:
        # Use production version if available
        app_file = "streamlit_app_production.py" if Path("streamlit_app_production.py").exists() else "streamlit_app.py"
        
        frontend_process = subprocess.Popen([
            sys.executable, "-m", "streamlit", "run", app_file,
            "--server.port", "8501",
            "--server.address", "0.0.0.0",
            "--browser.gatherUsageStats", "false"
        ], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        
        # Wait for frontend to start
        time.sleep(5)
        
        # Try to access frontend
        try:
            response = requests.get("http://localhost:8501", timeout=5)
            print(f"{Colors.GREEN}✅ Frontend started at http://localhost:8501{Colors.END}")
            return frontend_process
        except:
            print(f"{Colors.GREEN}✅ Frontend starting at http://localhost:8501{Colors.END}")
            return frontend_process
            
    except Exception as e:
        print(f"{Colors.RED}❌ Frontend startup error: {e}{Colors.END}")
        return None

def open_browser():
    """Open the application in the default browser."""
    print(f"{Colors.YELLOW}🌐 Opening browser...{Colors.END}")
    
    try:
        webbrowser.open("http://localhost:8501")
        print(f"{Colors.GREEN}✅ Browser opened{Colors.END}")
    except Exception as e:
        print(f"{Colors.YELLOW}⚠️  Could not open browser automatically: {e}{Colors.END}")
        print(f"{Colors.BLUE}📖 Please open: http://localhost:8501{Colors.END}")

def monitor_processes(backend_process, frontend_process):
    """Monitor running processes and handle shutdown."""
    print(f"""
{Colors.GREEN}{Colors.BOLD}
🎉 DNOTI Legal Tech is running!
{Colors.END}
{Colors.BLUE}📊 Frontend: http://localhost:8501
🔧 Backend:  http://localhost:8000
📚 API Docs: http://localhost:8000/docs

Press Ctrl+C to stop all services{Colors.END}
""")
    
    try:
        while True:
            # Check if processes are still running
            if backend_process and backend_process.poll() is not None:
                print(f"{Colors.RED}❌ Backend stopped unexpectedly{Colors.END}")
                break
            
            if frontend_process and frontend_process.poll() is not None:
                print(f"{Colors.RED}❌ Frontend stopped unexpectedly{Colors.END}")
                break
            
            time.sleep(5)
            
    except KeyboardInterrupt:
        print(f"\n{Colors.YELLOW}🛑 Shutting down services...{Colors.END}")
        
        if backend_process:
            backend_process.terminate()
            backend_process.wait()
            print(f"{Colors.GREEN}✅ Backend stopped{Colors.END}")
        
        if frontend_process:
            frontend_process.terminate()
            frontend_process.wait()
            print(f"{Colors.GREEN}✅ Frontend stopped{Colors.END}")
        
        print(f"{Colors.BLUE}👋 DNOTI Legal Tech stopped successfully{Colors.END}")

def main():
    """Main startup function."""
    start_time = datetime.now()
    print_banner()
    
    # System checks
    if not check_requirements():
        sys.exit(1)
    
    # Install dependencies
    if not install_dependencies():
        sys.exit(1)
    
    # Check/setup database
    if not check_database():
        sys.exit(1)
    
    # Start services
    backend_process = start_backend()
    if not backend_process:
        sys.exit(1)
    
    frontend_process = start_frontend()
    if not frontend_process:
        backend_process.kill()
        sys.exit(1)
    
    # Open browser
    open_browser()
    
    # Show startup time
    startup_time = (datetime.now() - start_time).total_seconds()
    print(f"{Colors.GREEN}⚡ Startup completed in {startup_time:.1f} seconds{Colors.END}")
    
    # Monitor processes
    monitor_processes(backend_process, frontend_process)

if __name__ == "__main__":
    main()
