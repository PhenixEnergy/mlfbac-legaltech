#!/usr/bin/env python3
"""
Legal Tech - Einfacher Service Starter
Vereinfachte Version ohne komplexe Abhängigkeiten
"""

import subprocess
import time
import sys
import webbrowser
from pathlib import Path

def main():
    """Startet die Legal Tech Services"""
    project_dir = Path(__file__).parent
    venv_python = project_dir / "venv" / "Scripts" / "python.exe"
    
    print("=== Legal Tech - Einfacher Starter ===")
    print(f"Projektverzeichnis: {project_dir}")
    
    # Virtual Environment prüfen
    if not venv_python.exists():
        print("❌ Virtual Environment nicht gefunden!")
        print("Führen Sie zuerst aus: python -m venv venv")
        return False
    
    print("✅ Virtual Environment gefunden")
    
    # Backend starten
    print("🚀 Starte FastAPI Backend...")
    backend_cmd = [
        str(venv_python), "-m", "uvicorn",
        "src.api.main:app",
        "--host", "127.0.0.1",
        "--port", "8000",
        "--reload"
    ]
    
    # Backend in separatem Prozess starten
    try:
        subprocess.Popen(
            backend_cmd,
            cwd=project_dir,
            creationflags=subprocess.CREATE_NEW_CONSOLE if sys.platform == "win32" else 0
        )
        print("✅ Backend-Prozess gestartet")
    except Exception as e:
        print(f"❌ Backend-Start fehlgeschlagen: {e}")
        return False
    
    # Kurz warten
    print("⏳ Warte 5 Sekunden...")
    time.sleep(5)
    
    # Frontend starten
    print("🚀 Starte Streamlit Frontend...")
    frontend_cmd = [
        str(venv_python), "-m", "streamlit", "run",
        "streamlit_app.py",
        "--server.port", "8501",
        "--server.headless", "false"
    ]
    
    try:
        subprocess.Popen(
            frontend_cmd,
            cwd=project_dir,
            creationflags=subprocess.CREATE_NEW_CONSOLE if sys.platform == "win32" else 0
        )
        print("✅ Frontend-Prozess gestartet")
    except Exception as e:
        print(f"❌ Frontend-Start fehlgeschlagen: {e}")
        return False
    
    # Warten und Browser öffnen
    print("⏳ Warte 10 Sekunden für Service-Start...")
    time.sleep(10)
    
    try:
        webbrowser.open("http://localhost:8501")
        print("🌐 Browser geöffnet")
    except Exception as e:
        print(f"⚠️ Browser konnte nicht geöffnet werden: {e}")
    
    print("\n=== Services gestartet ===")
    print("📊 Backend:  http://localhost:8000")
    print("🌐 Frontend: http://localhost:8501")
    print("\nHinweis: LM Studio muss separat auf Port 1234 gestartet werden")
    print("für vollständige KI-Funktionalität.")
    
    return True

if __name__ == "__main__":
    success = main()
    if success:
        print("\n✅ Erfolgreich gestartet!")
    else:
        print("\n❌ Start fehlgeschlagen!")
    
    input("Drücken Sie Enter zum Beenden...")
