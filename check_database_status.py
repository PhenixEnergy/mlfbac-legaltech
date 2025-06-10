#!/usr/bin/env python3
"""
Datenbank Status Checker
Überprüft den Füllstand und Status der ChromaDB
"""

import requests
import json
import sys
from pathlib import Path

def check_database_via_api():
    """Prüft Datenbank über API"""
    print("📊 DATENBANK STATUS REPORT")
    print("=" * 50)
    
    try:
        # API Stats abrufen
        response = requests.get("http://localhost:8000/admin/stats", timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            
            print(f"📁 Collections gefunden: {len(data.get('collection_names', []))}")
            for collection in data.get('collection_names', []):
                print(f"   - {collection}")
            
            print(f"\n📈 Dokument-Statistiken:")
            print(f"   Gesamt Gutachten: {data.get('total_gutachten', 0):,}")
            print(f"   Gesamt Chunks: {data.get('total_chunks', 0):,}")
            print(f"   Ø Tokens pro Chunk: {data.get('avg_tokens_per_chunk', 0):.1f}")
            
            print(f"\n💾 Datenbank Größe: {data.get('database_size_mb', 0):.1f} MB")
            print(f"🕐 Letztes Update: {data.get('last_updated', 'Unbekannt')}")
            
            # Bewertung
            total_chunks = data.get('total_chunks', 0)
            if total_chunks == 0:
                print(f"\n❌ DATENBANK IST LEER")
                print("   Die Datenbank existiert, enthält aber keine Dokumente.")
                return False
            elif total_chunks < 1000:
                print(f"\n⚠️  DATENBANK NUR TEILWEISE BEFÜLLT")
                print(f"   Nur {total_chunks} Chunks gefunden - möglicherweise unvollständig.")
                return True
            else:
                print(f"\n✅ DATENBANK GUT BEFÜLLT")
                print(f"   {total_chunks:,} Chunks gefunden - sieht vollständig aus.")
                return True
            
        else:
            print(f"❌ API Error: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Verbindungsfehler zur API: {e}")
        return False

def check_database_files():
    """Prüft Datenbank-Dateien direkt"""
    print(f"\n📁 DATENBANK-DATEIEN CHECK")
    print("-" * 30)
    
    db_paths = [
        "data/vectordb/chroma.sqlite3",
        "data/chroma/chroma.sqlite3", 
        "chroma_db/chroma.sqlite3"
    ]
    
    found_db = False
    for db_path in db_paths:
        path = Path(db_path)
        if path.exists():
            size_mb = path.stat().st_size / (1024 * 1024)
            print(f"✅ {db_path}: {size_mb:.1f} MB")
            found_db = True
        else:
            print(f"❌ {db_path}: Nicht gefunden")
    
    return found_db

def check_original_data():
    """Prüft Original-Daten"""
    print(f"\n📄 ORIGINAL-DATEN CHECK")
    print("-" * 25)
    
    original_files = [
        "Database/Original/dnoti_all.json",
        "sample_data/sample_documents.json"
    ]
    
    found_original = False
    for file_path in original_files:
        path = Path(file_path)
        if path.exists():
            size_mb = path.stat().st_size / (1024 * 1024)
            print(f"✅ {file_path}: {size_mb:.1f} MB")
            found_original = True
        else:
            print(f"❌ {file_path}: Nicht gefunden")
    
    return found_original

def main():
    """Hauptfunktion"""
    # API Check
    api_ok = check_database_via_api()
    
    # File Check
    files_ok = check_database_files()
    
    # Original Data Check
    original_ok = check_original_data()
    
    # Fazit
    print(f"\n" + "=" * 50)
    print(f"📋 FAZIT")
    print(f"=" * 50)
    
    if api_ok and files_ok:
        print("✅ Datenbank ist verfügbar und enthält Daten")
    elif files_ok and not api_ok:
        print("⚠️ Datenbank-Dateien vorhanden, aber API zeigt keine Inhalte")
        print("   Möglicherweise muss die Datenbank neu geladen werden.")
    elif not files_ok and original_ok:
        print("❌ Datenbank leer, aber Original-Daten vorhanden")
        print("   Datenbank muss aus Original-Daten befüllt werden.")
    else:
        print("❌ Weder Datenbank noch Original-Daten gefunden")
    
    # Empfehlungen
    print(f"\n💡 EMPFEHLUNGEN:")
    if not api_ok and original_ok:
        print("   1. python load_all_gutachten.py - Datenbank befüllen")
    elif not files_ok:
        print("   1. Original-Daten beschaffen")
        print("   2. python load_all_gutachten.py ausführen")
    else:
        print("   1. System ist bereit für Semantic Search")

if __name__ == "__main__":
    main()
