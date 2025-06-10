#!/usr/bin/env python3
"""
Legal Tech Service Manager
Startet und überwacht alle benötigten Services für das Legal Tech System
"""

import subprocess
import time
import os
import sys
import signal
import requests
import threading
from pathlib import Path

class ServiceManager:
    def __init__(self):
        self.project_dir = Path(__file__).parent
        self.venv_python = self.project_dir / "venv" / "Scripts" / "python.exe"
        self.processes = []
        self.running = True
        
    def log(self, message, level="INFO"):
        timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
        print(f"[{timestamp}] [{level}] {message}")
        
    def check_python_env(self):
        """Überprüft ob Python und Virtual Environment verfügbar sind"""
        if not self.venv_python.exists():
            self.log("Virtual environment nicht gefunden!", "ERROR")
            self.log("Bitte führen Sie zuerst 'python -m venv venv' aus", "ERROR")
            return False
            
        try:
            result = subprocess.run([str(self.venv_python), "--version"], 
                                  capture_output=True, text=True, check=True)
            self.log(f"Python gefunden: {result.stdout.strip()}", "SUCCESS")
            return True
        except subprocess.CalledProcessError:
            self.log("Python Virtual Environment ist beschädigt", "ERROR")
            return False
            
    def install_requirements(self):
        """Installiert Requirements falls nötig"""
        try:
            # Prüfe ob Streamlit installiert ist
            result = subprocess.run([str(self.venv_python), "-c", "import streamlit"], 
                                  capture_output=True, text=True)
            if result.returncode != 0:
                self.log("Installiere Requirements...", "INFO")
                subprocess.run([str(self.venv_python), "-m", "pip", "install", "-r", "requirements.txt"], 
                             check=True, cwd=self.project_dir)
                self.log("Requirements installiert", "SUCCESS")
        except subprocess.CalledProcessError as e:
            self.log(f"Fehler bei Requirements Installation: {e}", "ERROR")
            return False
        return True
        
    def start_backend(self):
        """Startet FastAPI Backend"""
        self.log("Starte FastAPI Backend...", "INFO")
        try:
            cmd = [
                str(self.venv_python), "-m", "uvicorn", 
                "src.api.main:app",
                "--host", "127.0.0.1",
                "--port", "8000",
                "--reload"
            ]
            
            process = subprocess.Popen(
                cmd,
                cwd=self.project_dir,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1,
                universal_newlines=True
            )
            
            self.processes.append(("FastAPI Backend", process))
            
            # Warte auf Backend-Start
            for i in range(30):  # 30 Sekunden warten
                try:
                    response = requests.get("http://localhost:8000/health", timeout=2)
                    if response.status_code == 200:
                        self.log("FastAPI Backend erfolgreich gestartet auf http://localhost:8000", "SUCCESS")
                        return True
                except requests.RequestException:
                    pass
                time.sleep(1)
                
            self.log("Backend-Start-Timeout erreicht", "WARNING")
            return False
            
        except Exception as e:
            self.log(f"Fehler beim Starten des Backends: {e}", "ERROR")
            return False
            
    def start_frontend(self):
        """Startet Streamlit Frontend"""
        self.log("Starte Streamlit Frontend...", "INFO")
        try:
            cmd = [
                str(self.venv_python), "-m", "streamlit", "run",
                "streamlit_app.py",
                "--server.port", "8501",
                "--server.headless", "false",
                "--browser.gatherUsageStats", "false"
            ]
            
            process = subprocess.Popen(
                cmd,
                cwd=self.project_dir,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1,
                universal_newlines=True
            )
            
            self.processes.append(("Streamlit Frontend", process))
            
            # Warte auf Frontend-Start
            for i in range(30):
                try:
                    response = requests.get("http://localhost:8501", timeout=2)
                    if response.status_code == 200:
                        self.log("Streamlit Frontend erfolgreich gestartet auf http://localhost:8501", "SUCCESS")
                        return True
                except requests.RequestException:
                    pass
                time.sleep(1)
                
            self.log("Frontend erfolgreich gestartet (möglicherweise noch ladend)", "SUCCESS")
            return True
            
        except Exception as e:
            self.log(f"Fehler beim Starten des Frontends: {e}", "ERROR")
            return False
            
    def monitor_processes(self):
        """Überwacht laufende Prozesse"""
        while self.running:
            for name, process in self.processes:
                if process.poll() is not None:  # Prozess ist beendet
                    self.log(f"{name} ist unerwartet beendet worden (Code: {process.returncode})", "ERROR")
                    
            time.sleep(5)
            
    def signal_handler(self, signum, frame):
        """Handler für Shutdown-Signal"""
        self.log("Shutdown-Signal empfangen, beende Services...", "INFO")
        self.shutdown()
        
    def shutdown(self):
        """Beendet alle Services"""
        self.running = False
        self.log("Beende alle Services...", "INFO")
        
        for name, process in self.processes:
            try:
                self.log(f"Beende {name}...", "INFO")
                process.terminate()
                process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                self.log(f"Force-Kill {name}...", "WARNING")
                process.kill()
            except Exception as e:
                self.log(f"Fehler beim Beenden von {name}: {e}", "ERROR")
                
        self.log("Alle Services beendet", "INFO")
        
    def run(self):
        """Hauptfunktion"""
        # Signal Handler registrieren
        signal.signal(signal.SIGINT, self.signal_handler)
        signal.signal(signal.SIGTERM, self.signal_handler)
        
        self.log("=== Legal Tech Service Manager ===", "INFO")
        self.log(f"Projektverzeichnis: {self.project_dir}", "INFO")
        
        # Umgebung prüfen
        if not self.check_python_env():
            return False
            
        # Requirements installieren
        if not self.install_requirements():
            return False
            
        # Services starten
        if not self.start_backend():
            self.log("Backend konnte nicht gestartet werden", "ERROR")
            return False
            
        if not self.start_frontend():
            self.log("Frontend konnte nicht gestartet werden", "ERROR")
            return False
            
        # Browser öffnen
        try:
            import webbrowser
            webbrowser.open("http://localhost:8501")
            self.log("Browser geöffnet", "SUCCESS")
        except Exception as e:
            self.log(f"Browser konnte nicht geöffnet werden: {e}", "WARNING")
            
        self.log("=== Alle Services erfolgreich gestartet ===", "SUCCESS")
        self.log("Drücken Sie Ctrl+C zum Beenden", "INFO")
        
        # Monitoring starten
        monitor_thread = threading.Thread(target=self.monitor_processes)
        monitor_thread.daemon = True
        monitor_thread.start()
        
        try:
            # Warten bis Shutdown
            while self.running:
                time.sleep(1)
        except KeyboardInterrupt:
            self.log("Keyboard Interrupt empfangen", "INFO")
            
        self.shutdown()
        return True

if __name__ == "__main__":
    manager = ServiceManager()
    success = manager.run()
    sys.exit(0 if success else 1)
