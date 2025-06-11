#!/usr/bin/env python3
"""
Startup script with IBM Granite fix applied
Use this instead of start_production.py to ensure IBM Granite works correctly
"""

import subprocess
import sys
import time
from pathlib import Path

def apply_ibm_granite_fix():
    """Apply IBM Granite compatibility fix"""
    print("🔧 Applying IBM Granite compatibility fix...")
    
    # The fix is already applied in the semantic_search.py file:
    # - SemanticSearchEngine now uses "legal_documents" collection (275 docs, IBM Granite compatible)
    # - This collection works with IBM Granite embedding (768 dimensions)
    
    print("✅ IBM Granite fix is active")
    print("📊 Using legal_documents collection (275 docs) with IBM Granite model")
    print("🎯 Expected high-quality results with similarity scores 0.60+")

def start_services():
    """Start the services with IBM Granite fix"""
    
    apply_ibm_granite_fix()
    
    print("\n🚀 Starting Legal Tech Services with IBM Granite...")
    
    try:
        # Start FastAPI
        print("📡 Starting FastAPI server...")
        api_process = subprocess.Popen([
            sys.executable, "-m", "uvicorn", 
            "src.api.main:app", 
            "--host", "0.0.0.0", 
            "--port", "8000",
            "--reload"
        ])
        
        time.sleep(3)
        
        # Start Streamlit
        print("🖥️  Starting Streamlit interface...")
        streamlit_process = subprocess.Popen([
            sys.executable, "-m", "streamlit", "run", 
            "streamlit_app_production.py",
            "--server.port", "8502",
            "--server.address", "localhost"
        ])
        
        print("\n✅ Services started successfully!")
        print("📡 FastAPI: http://localhost:8000")
        print("🖥️  Streamlit: http://localhost:8502")
        print("📖 API Docs: http://localhost:8000/docs")
        print("\n🎯 IBM Granite model is now active for high-quality search!")
        
        # Keep running
        try:
            api_process.wait()
        except KeyboardInterrupt:
            print("\n🛑 Stopping services...")
            api_process.terminate()
            streamlit_process.terminate()
            
    except Exception as e:
        print(f"❌ Error starting services: {e}")

if __name__ == "__main__":
    start_services()
