#!/usr/bin/env python3
"""
Legal Tech - Robuste Streamlit Startup Reparatur
Behebt Streamlit-Installation und -Startprobleme
"""

import subprocess
import sys
import os
import shutil
import time
import webbrowser
from pathlib import Path

class Colors:
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    END = '\033[0m'

def print_header():
    """Zeigt Header mit Diagnose-Info"""
    print(f"{Colors.CYAN}=" * 60)
    print(f"{Colors.GREEN}🔧 Legal Tech - Streamlit Startup Reparatur")
    print(f"{Colors.CYAN}=" * 60)
    print(f"{Colors.END}")

def check_environment():
    """Prüft und bereitet die Umgebung vor"""
    project_dir = Path(__file__).parent
    venv_python = project_dir / "venv" / "Scripts" / "python.exe"
    
    print(f"{Colors.YELLOW}📁 Projektverzeichnis: {project_dir}")
    
    if not venv_python.exists():
        print(f"{Colors.RED}❌ Virtual Environment nicht gefunden!")
        print(f"{Colors.YELLOW}Erstelle neues Virtual Environment...")
        
        # Neues venv erstellen
        subprocess.run([sys.executable, "-m", "venv", "venv"], 
                      cwd=project_dir, check=True)
        print(f"{Colors.GREEN}✅ Virtual Environment erstellt")
    
    return project_dir, venv_python

def fix_streamlit_installation(project_dir, venv_python):
    """Repariert Streamlit-Installation"""
    print(f"{Colors.YELLOW}🔧 Repariere Streamlit-Installation...")
    
    # Cache-Ordner löschen
    cache_dirs = [
        project_dir / ".streamlit",
        Path.home() / ".streamlit",
        project_dir / "venv" / "Lib" / "site-packages" / "streamlit" / ".streamlit"
    ]
    
    for cache_dir in cache_dirs:
        if cache_dir.exists():
            try:
                shutil.rmtree(cache_dir)
                print(f"{Colors.GREEN}✅ Cache gelöscht: {cache_dir.name}")
            except:
                pass
    
    # Streamlit komplett deinstallieren
    print(f"{Colors.YELLOW}🗑️ Deinstalliere alte Streamlit-Version...")
    subprocess.run([str(venv_python), "-m", "pip", "uninstall", "streamlit", "-y"], 
                  capture_output=True)
    
    # Pip upgraden
    print(f"{Colors.YELLOW}⬆️ Upgrade pip...")
    subprocess.run([str(venv_python), "-m", "pip", "install", "--upgrade", "pip"], 
                  capture_output=True)
    
    # Streamlit neu installieren
    print(f"{Colors.YELLOW}📦 Installiere Streamlit...")
    result = subprocess.run([
        str(venv_python), "-m", "pip", "install", 
        "streamlit==1.39.0", "--force-reinstall", "--no-cache-dir"
    ], capture_output=True, text=True)
    
    if result.returncode == 0:
        print(f"{Colors.GREEN}✅ Streamlit erfolgreich installiert")
        return True
    else:
        print(f"{Colors.RED}❌ Streamlit-Installation fehlgeschlagen:")
        print(result.stderr)
        return False

def create_fallback_app(project_dir):
    """Erstellt eine einfache Fallback-Streamlit-App"""
    fallback_content = '''#!/usr/bin/env python3
"""
Legal Tech - Fallback Streamlit App
Einfache App ohne komplexe Templates
"""

import streamlit as st
import sys
from pathlib import Path

# Basis-Konfiguration
st.set_page_config(
    page_title="Legal Tech - Fallback",
    page_icon="⚖️",
    layout="wide"
)

def main():
    # Header
    st.title("⚖️ Legal Tech - System Online")
    st.markdown("---")
    
    # Status
    st.success("✅ Streamlit läuft erfolgreich!")
    
    # System Info
    st.subheader("📊 System-Information")
    col1, col2 = st.columns(2)
    
    with col1:
        st.info(f"**Python Version:** {sys.version}")
        st.info(f"**Streamlit Version:** {st.__version__}")
    
    with col2:
        st.info(f"**Projektverzeichnis:** {Path.cwd()}")
        st.info(f"**Status:** System bereit")
    
    # Service Links
    st.subheader("🔗 Service-Links")
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("🌐 Frontend (aktuell)", type="primary"):
            st.balloons()
    
    with col2:
        st.link_button("📊 Backend API", "http://localhost:8000")
    
    with col3:
        st.link_button("📖 API Docs", "http://localhost:8000/docs")
    
    # Nächste Schritte
    st.subheader("🚀 Nächste Schritte")
    st.markdown("""
    1. **Backend starten:** Wenn noch nicht aktiv
    2. **Hauptanwendung testen:** Nach Reparatur verfügbar
    3. **LM Studio:** Optional für erweiterte KI-Features
    """)
    
    # Footer
    st.markdown("---")
    st.caption("Legal Tech System - Fallback Mode")

if __name__ == "__main__":
    main()
'''
    
    fallback_file = project_dir / "streamlit_fallback.py"
    with open(fallback_file, 'w', encoding='utf-8') as f:
        f.write(fallback_content)
    
    print(f"{Colors.GREEN}✅ Fallback-App erstellt: {fallback_file.name}")
    return fallback_file

def test_streamlit_apps(venv_python, project_dir):
    """Testet verschiedene Streamlit-Apps"""
    apps_to_test = [
        ("streamlit_app.py", "Hauptanwendung"),
        ("simple_app.py", "Einfache App"),
        ("streamlit_fallback.py", "Fallback App")
    ]
    
    for app_file, app_name in apps_to_test:
        app_path = project_dir / app_file
        if app_path.exists():
            print(f"{Colors.YELLOW}🧪 Teste {app_name}...")
            
            # Test-Import
            test_cmd = [
                str(venv_python), "-c", 
                f"import sys; sys.path.append('{project_dir}'); "
                f"exec(open('{app_path}').read())"
            ]
            
            result = subprocess.run(test_cmd, capture_output=True, text=True, timeout=10)
            
            if result.returncode == 0:
                print(f"{Colors.GREEN}✅ {app_name} importiert erfolgreich")
                return app_file
            else:
                print(f"{Colors.RED}❌ {app_name} Import-Fehler:")
                print(result.stderr[:200] + "..." if len(result.stderr) > 200 else result.stderr)
    
    return "streamlit_fallback.py"  # Fallback

def start_streamlit(venv_python, project_dir, app_file):
    """Startet Streamlit mit der besten verfügbaren App"""
    print(f"{Colors.CYAN}🚀 Starte Streamlit mit {app_file}...")
    
    # Streamlit-Kommando
    cmd = [
        str(venv_python), "-m", "streamlit", "run", app_file,
        "--server.port", "8501",
        "--server.address", "0.0.0.0",
        "--browser.gatherUsageStats", "false",
        "--server.headless", "false"
    ]
    
    try:
        # Streamlit starten
        process = subprocess.Popen(
            cmd, cwd=project_dir,
            creationflags=subprocess.CREATE_NEW_CONSOLE
        )
        
        print(f"{Colors.GREEN}✅ Streamlit gestartet (PID: {process.pid})")
        print(f"{Colors.BLUE}🌐 URL: http://localhost:8501")
        
        # Warten und Browser öffnen
        time.sleep(8)
        
        try:
            webbrowser.open("http://localhost:8501")
            print(f"{Colors.GREEN}✅ Browser geöffnet")
        except:
            print(f"{Colors.YELLOW}⚠️ Browser konnte nicht automatisch geöffnet werden")
        
        return True
        
    except Exception as e:
        print(f"{Colors.RED}❌ Streamlit-Start fehlgeschlagen: {e}")
        return False

def main():
    """Hauptfunktion - Repariert und startet Streamlit"""
    print_header()
    
    try:
        # 1. Umgebung prüfen
        project_dir, venv_python = check_environment()
        
        # 2. Streamlit-Installation reparieren
        if not fix_streamlit_installation(project_dir, venv_python):
            print(f"{Colors.RED}❌ Streamlit-Reparatur fehlgeschlagen!")
            return False
        
        # 3. Fallback-App erstellen
        create_fallback_app(project_dir)
        
        # 4. Apps testen
        best_app = test_streamlit_apps(venv_python, project_dir)
        print(f"{Colors.GREEN}🎯 Beste verfügbare App: {best_app}")
        
        # 5. Streamlit starten
        if start_streamlit(venv_python, project_dir, best_app):
            print(f"{Colors.GREEN}🎉 Streamlit erfolgreich gestartet!")
            print(f"{Colors.CYAN}📋 Status:")
            print(f"   • App: {best_app}")
            print(f"   • URL: http://localhost:8501")
            print(f"   • PID: Läuft in separatem Fenster")
            return True
        else:
            return False
            
    except Exception as e:
        print(f"{Colors.RED}❌ Unerwarteter Fehler: {e}")
        return False

if __name__ == "__main__":
    try:
        success = main()
        if success:
            print(f"\n{Colors.GREEN}✅ Reparatur und Start erfolgreich!")
        else:
            print(f"\n{Colors.RED}❌ Reparatur fehlgeschlagen!")
        
        input(f"\n{Colors.YELLOW}Drücken Sie Enter zum Beenden...")
        
    except KeyboardInterrupt:
        print(f"\n{Colors.YELLOW}🛑 Abgebrochen durch Benutzer")
    except Exception as e:
        print(f"\n{Colors.RED}❌ Kritischer Fehler: {e}")
        input("Drücken Sie Enter zum Beenden...")
