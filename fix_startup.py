#!/usr/bin/env python3
"""
Direkter Streamlit Starter - Behebt Verbindungsprobleme
"""

import subprocess
import sys
import time
import os
import webbrowser
from pathlib import Path

def start_services():
    """Startet Backend und Frontend direkt"""
    project_dir = Path(__file__).parent
    venv_python = project_dir / "venv" / "Scripts" / "python.exe"
    
    print("🔧 Legal Tech - Direkter Service Start")
    print(f"📁 Projektverzeichnis: {project_dir}")
    
    # Prüfe Virtual Environment
    if not venv_python.exists():
        print("❌ Virtual Environment nicht gefunden!")
        return False
    
    print("✅ Virtual Environment gefunden")
    
    # Alte Prozesse beenden
    try:
        subprocess.run(["taskkill", "/f", "/im", "python.exe"], 
                      capture_output=True, check=False)
        subprocess.run(["taskkill", "/f", "/im", "streamlit.exe"], 
                      capture_output=True, check=False)
        print("🧹 Alte Prozesse beendet")
        time.sleep(2)
    except:
        pass
    
    # Backend starten
    print("🚀 Starte FastAPI Backend...")
    backend_cmd = [
        str(venv_python), "-m", "uvicorn",
        "src.api.main:app",
        "--host", "0.0.0.0",
        "--port", "8000",
        "--reload"
    ]
    
    try:
        backend_process = subprocess.Popen(
            backend_cmd,
            cwd=project_dir,
            creationflags=subprocess.CREATE_NEW_CONSOLE
        )
        print(f"✅ Backend gestartet (PID: {backend_process.pid})")
        time.sleep(5)  # Warte auf Backend
    except Exception as e:
        print(f"❌ Backend-Start fehlgeschlagen: {e}")
        return False
    
    # Frontend starten
    print("🌐 Starte Streamlit Frontend...")
    frontend_cmd = [
        str(venv_python), "-m", "streamlit", "run",
        "streamlit_app.py",
        "--server.port", "8501",
        "--server.address", "0.0.0.0",
        "--server.headless", "false",
        "--browser.gatherUsageStats", "false"
    ]
    
    try:
        frontend_process = subprocess.Popen(
            frontend_cmd,
            cwd=project_dir,
            creationflags=subprocess.CREATE_NEW_CONSOLE
        )
        print(f"✅ Frontend gestartet (PID: {frontend_process.pid})")
        time.sleep(8)  # Warte auf Frontend
    except Exception as e:
        print(f"❌ Frontend-Start fehlgeschlagen: {e}")
        return False
    
    # Services testen
    print("🔍 Teste Services...")
    
    # Backend Test
    try:
        import requests
        response = requests.get("http://localhost:8000/health", timeout=5)
        if response.status_code == 200:
            print("✅ Backend erreichbar")
        else:
            print(f"⚠️ Backend antwortet mit Status {response.status_code}")
    except Exception as e:
        print(f"⚠️ Backend-Test fehlgeschlagen: {e}")
    
    # Frontend Test
    try:
        response = requests.get("http://localhost:8501", timeout=5)
        if response.status_code == 200:
            print("✅ Frontend erreichbar")
        else:
            print(f"⚠️ Frontend antwortet mit Status {response.status_code}")
    except Exception as e:
        print(f"⚠️ Frontend-Test fehlgeschlagen: {e}")
    
    # Browser öffnen
    try:
        webbrowser.open("http://localhost:8501")
        print("🌐 Browser geöffnet")
    except Exception as e:
        print(f"⚠️ Browser konnte nicht geöffnet werden: {e}")
    
    print("\n" + "="*50)
    print("🎉 Services erfolgreich gestartet!")
    print("📊 Backend:  http://localhost:8000")
    print("🌐 Frontend: http://localhost:8501")
    print("="*50)
    
    return True

if __name__ == "__main__":
    try:
        success = start_services()
        if success:
            print("\n✅ Start erfolgreich!")
            print("Die Services laufen in separaten Fenstern.")
            print("Schließen Sie diese Fenster NICHT!")
        else:
            print("\n❌ Start fehlgeschlagen!")
        
        input("\nDrücken Sie Enter zum Beenden...")
    
    except KeyboardInterrupt:
        print("\n🛑 Abgebrochen durch Benutzer")
    except Exception as e:
        print(f"\n❌ Unerwarteter Fehler: {e}")
        input("Drücken Sie Enter zum Beenden...")
