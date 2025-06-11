#!/usr/bin/env python3
"""
Gutachten Counter - Genaue Anzahl der Gutachten in der ChromaDB
"""

import json
import chromadb
from datetime import datetime
import os

def count_gutachten_in_chromadb():
    """Zählt die tatsächliche Anzahl der Gutachten in allen Collections"""
    
    print("📊 GUTACHTEN-ZÄHLUNG IN CHROMADB")
    print("=" * 50)
    print(f"⏰ Analyse-Zeit: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    # ChromaDB Client initialisieren
    client = chromadb.PersistentClient(path="./data/vectordb")
    collections = client.list_collections()
    
    total_gutachten = 0
    total_chunks = 0
    gutachten_details = {}
    
    for collection in collections:
        coll = client.get_collection(collection.name)
        count = coll.count()
        total_chunks += count
        
        print(f"📁 Collection: {collection.name}")
        print(f"   📊 Chunks: {count:,}")
        
        # Versuche Gutachten-IDs zu identifizieren
        if count > 0:
            # Hole Sample-Daten
            try:
                result = coll.get(limit=min(100, count), include=['metadatas'])
                unique_gutachten = set()
                
                for metadata in result['metadatas']:
                    if metadata:
                        # Verschiedene Möglichkeiten für Gutachten-IDs
                        gutachten_id = (
                            metadata.get('source_gutachten_id') or
                            metadata.get('gutachten_nummer') or
                            metadata.get('original_id') or
                            metadata.get('url', '').split('/')[-1] if metadata.get('url') else None
                        )
                        
                        if gutachten_id and gutachten_id != 'unknown':
                            unique_gutachten.add(gutachten_id)
                
                # Hochrechnung basierend auf Sample
                if unique_gutachten and count > 100:
                    sample_ratio = len(unique_gutachten) / min(100, count)
                    estimated_gutachten = int(count * sample_ratio)
                else:
                    estimated_gutachten = len(unique_gutachten)
                
                gutachten_details[collection.name] = {
                    'chunks': count,
                    'estimated_gutachten': estimated_gutachten,
                    'sample_gutachten': len(unique_gutachten)
                }
                
                print(f"   📋 Geschätzte Gutachten: {estimated_gutachten:,}")
                total_gutachten += estimated_gutachten
                
            except Exception as e:
                print(f"   ❌ Fehler bei Gutachten-Analyse: {e}")
                gutachten_details[collection.name] = {
                    'chunks': count,
                    'estimated_gutachten': 0,
                    'error': str(e)
                }
        
        print()
    
    return total_gutachten, total_chunks, gutachten_details

def count_original_data():
    """Zählt Gutachten in den Original-Daten"""
    
    print("📄 ORIGINAL-DATEN ANALYSE")
    print("=" * 30)
    
    original_file = "Database/Original/dnoti_all.json"
    
    if os.path.exists(original_file):
        try:
            with open(original_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            if isinstance(data, list):
                original_count = len(data)
                print(f"✅ Original dnoti_all.json: {original_count:,} Gutachten")
                return original_count
            elif isinstance(data, dict):
                original_count = len(data.keys())
                print(f"✅ Original dnoti_all.json: {original_count:,} Gutachten (Dict)")
                return original_count
                
        except Exception as e:
            print(f"❌ Fehler beim Lesen der Original-Daten: {e}")
    else:
        print(f"❌ Original-Datei nicht gefunden: {original_file}")
    
    return 0

def main():
    print("🔍 LEGAL TECH - GUTACHTEN ANALYSE")
    print("=" * 60)
    print()
    
    # ChromaDB Analyse
    total_gutachten, total_chunks, details = count_gutachten_in_chromadb()
    
    # Original-Daten Analyse
    original_count = count_original_data()
    
    print()
    print("📋 ZUSAMMENFASSUNG")
    print("=" * 30)
    print(f"🎯 Geschätzte Gutachten in ChromaDB: {total_gutachten:,}")
    print(f"📊 Total Chunks in ChromaDB: {total_chunks:,}")
    print(f"📄 Original Gutachten (dnoti_all.json): {original_count:,}")
    
    if original_count > 0:
        coverage = (total_gutachten / original_count) * 100
        print(f"📈 Abdeckung: {coverage:.1f}%")
    
    print()
    print("📂 DETAILS PRO COLLECTION:")
    for coll_name, info in details.items():
        print(f"   {coll_name}: {info['estimated_gutachten']:,} Gutachten, {info['chunks']:,} Chunks")
    
    # Speichere Ergebnisse
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    result_file = f"gutachten_count_{timestamp}.json"
    
    results = {
        'timestamp': datetime.now().isoformat(),
        'total_gutachten_chromadb': total_gutachten,
        'total_chunks_chromadb': total_chunks,
        'original_gutachten_count': original_count,
        'coverage_percentage': (total_gutachten / original_count * 100) if original_count > 0 else 0,
        'collection_details': details
    }
    
    with open(result_file, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    
    print(f"💾 Ergebnisse gespeichert in: {result_file}")

if __name__ == "__main__":
    main()
