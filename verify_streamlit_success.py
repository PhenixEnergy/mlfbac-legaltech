#!/usr/bin/env python3
"""
Legal Tech - Streamlit Success Verification
Bestätigung dass der Fix funktioniert hat
"""

import requests
import time
from datetime import datetime

def test_streamlit_services():
    """Testet ob Streamlit-Services laufen"""
    
    print("🎉 Legal Tech - Streamlit Fix Verifikation")
    print("=" * 60)
    print(f"Test-Zeit: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("")
    
    # Teste verschiedene Ports
    ports_to_test = [8501, 8502]
    running_services = []
    
    for port in ports_to_test:
        try:
            url = f"http://localhost:{port}"
            response = requests.get(url, timeout=3)
            
            if response.status_code == 200:
                print(f"✅ Streamlit läuft auf Port {port}")
                print(f"   URL: {url}")
                running_services.append(port)
            else:
                print(f"⚠️ Port {port}: HTTP {response.status_code}")
                
        except requests.exceptions.ConnectionError:
            print(f"❌ Port {port}: Keine Verbindung")
        except requests.exceptions.Timeout:
            print(f"⏱️ Port {port}: Timeout")
        except Exception as e:
            print(f"❓ Port {port}: {str(e)}")
    
    print("")
    print("=" * 60)
    
    if running_services:
        print("🎉 ERFOLG: Streamlit-Fix war erfolgreich!")
        print(f"✅ {len(running_services)} Service(s) laufen:")
        
        for port in running_services:
            print(f"   🌐 http://localhost:{port}")
        
        print("")
        print("📋 Nächste Schritte:")
        print("1. ✅ Streamlit funktioniert wieder")
        print("2. 🚀 Backend starten falls gewünscht")
        print("3. 🔍 Legal Tech Anwendung testen")
        print("4. 📊 Semantic Search ausprobieren")
        
        # Status in Datei speichern
        with open("streamlit_fix_success.txt", "w", encoding="utf-8") as f:
            f.write(f"Streamlit Fix erfolgreich - {datetime.now()}\n")
            f.write(f"Laufende Services: {running_services}\n")
            f.write("Status: SUCCESS\n")
        
        return True
    else:
        print("❌ Keine laufenden Streamlit-Services gefunden")
        print("💡 Versuchen Sie:")
        print("   streamlit run streamlit_test.py")
        print("   streamlit run simple_app.py")
        
        return False

if __name__ == "__main__":
    success = test_streamlit_services()
    
    print("")
    print("=" * 60)
    if success:
        print("🏆 STREAMLIT-FIX ERFOLGREICH ABGESCHLOSSEN!")
    else:
        print("🔧 Weitere Maßnahmen erforderlich")
    
    print("=" * 60)
