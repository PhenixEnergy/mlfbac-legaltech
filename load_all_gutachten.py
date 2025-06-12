#!/usr/bin/env python3
"""
Vollständige Datenbank-Befüllung mit ALLEN DNOTI-Gutachten
Lädt alle 3.936 Gutachten in die ChromaDB
"""
import json
import sys
import os
from pathlib import Path
import time
from datetime import datetime

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

def load_all_gutachten():
    print("🚀 VOLLSTÄNDIGE DATENBANK-BEFÜLLUNG")
    print("=" * 60)
    print(f"⏰ Start: {datetime.now().strftime('%H:%M:%S')}")
    
    # 1. Load data file
    data_file = Path("Database/Original/dnoti_all.json")
    if not data_file.exists():
        print(f"❌ Data file not found: {data_file}")
        return False
    
    print(f"📄 Loading JSON data from: {data_file}")
    with open(data_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    print(f"✅ Loaded {len(data)} Gutachten from JSON")
      # 2. Import ChromaDB
    try:
        import chromadb
        from chromadb.utils import embedding_functions
        print("✅ ChromaDB imported successfully")
    except ImportError as e:
        print(f"❌ ChromaDB import failed: {e}")
        return False
    
    # 3. Create ChromaDB client
    print("💾 Connecting to ChromaDB...")
    try:
        # Verwende neue Konfiguration
        from src.config import config
        chroma_path = config.CHROMA_PERSIST_DIRECTORY
        os.makedirs(chroma_path, exist_ok=True)
        client = chromadb.PersistentClient(path=chroma_path)
        print(f"✅ Connected to ChromaDB at: {os.path.abspath(chroma_path)}")
    except Exception as e:
        print(f"❌ ChromaDB connection failed: {e}")
        return False
    
    # 4. Recreate collection (delete old and create new)
    print("🗑️ Removing old collection...")
    try:
        client.delete_collection("legal_documents")
        print("✅ Old collection deleted")
    except:
        print("ℹ️ No existing collection to delete")
    
    print("📚 Creating new collection...")
    try:
        # Use our custom embedding function with IBM Granite model from config
        from src.vectordb.chroma_client import GraniteEmbeddingFunction
        embedding_fn = GraniteEmbeddingFunction()  # Uses config.EMBEDDING_MODEL by default
        
        collection = client.create_collection(
            name="legal_documents",
            embedding_function=embedding_fn,
            metadata={
                "hnsw:space": "cosine"  # Use cosine similarity instead of L2
            }
        )
        print("✅ New collection 'legal_documents' created with cosine similarity")
    except Exception as e:
        print(f"❌ Collection creation failed: {e}")
        return False
    
    # 5. Process ALL documents
    print(f"📥 Processing ALL {len(data)} Gutachten...")
    print("⏳ This will take several minutes...")
    
    total_added = 0
    total_skipped = 0
    batch_size = 25  # Reasonable batch size for stability
    start_time = time.time()
    
    for i in range(0, len(data), batch_size):
        batch = data[i:i+batch_size]
        batch_start = time.time()
        
        try:
            documents = []
            metadatas = []
            ids = []
            
            for j, doc in enumerate(batch):
                doc_id = f"gutachten_{i+j:05d}"                # Get content - the field is called 'text'
                content = doc.get('text', '')
                
                # Clean and validate content
                if not content or len(content.strip()) < 100:  # Skip very short content
                    total_skipped += 1
                    continue
                
                content = content.strip()
                
                # Limit content length for better performance
                if len(content) > 8000:
                    content = content[:8000] + "..."
                
                # Create comprehensive metadata
                metadata = {
                    'source_gutachten_id': str(doc.get('gutachten_nummer', doc.get('id', f'unknown_{i+j}'))),
                    'erscheinungsdatum': str(doc.get('erscheinungsdatum', '')),
                    'rechtsbezug': str(doc.get('rechtsbezug', 'National')),
                    'normen': str(doc.get('normen', '')),
                    'url': str(doc.get('url', '')),
                    'section_type': 'full_gutachten',
                    'level': 1,
                    'token_count': len(content.split()),
                    'char_count': len(content),
                    'original_id': str(doc.get('id', '')),
                    'batch_number': i // batch_size + 1
                }
                  # Extract legal norms as list if possible
                normen_text = doc.get('normen', '')
                if normen_text and normen_text != '':
                    # Split normen by common separators
                    legal_norms = [norm.strip() for norm in normen_text.replace(';', ',').split(',') if norm.strip()]
                    # Convert list to comma-separated string for ChromaDB compatibility
                    metadata['legal_norms'] = '; '.join(legal_norms[:10])  # Limit to 10 norms
                else:
                    metadata['legal_norms'] = ''
                
                documents.append(content)
                metadatas.append(metadata)
                ids.append(doc_id)
            
            # Add batch to ChromaDB
            if documents:
                collection.add(
                    documents=documents,
                    metadatas=metadatas,
                    ids=ids
                )
                total_added += len(documents)
                
                batch_time = time.time() - batch_start
                estimated_remaining = (batch_time * (len(data) - i - batch_size)) / batch_size / 60
                
                print(f"   ✅ Batch {i//batch_size + 1:3d}/{(len(data)-1)//batch_size + 1}: "
                      f"{len(documents):2d} docs | "
                      f"Total: {total_added:4d} | "
                      f"Time: {batch_time:.1f}s | "
                      f"ETA: {estimated_remaining:.1f}min")
        
        except Exception as e:
            print(f"   ❌ Batch {i//batch_size + 1} failed: {e}")
            continue
    
    total_time = time.time() - start_time
    
    print("\n" + "=" * 60)
    print("📊 LOADING COMPLETE!")
    print(f"✅ Successfully added: {total_added:,} Gutachten")
    print(f"⚠️ Skipped (too short): {total_skipped:,} documents")
    print(f"⏱️ Total time: {total_time/60:.1f} minutes")
    print(f"📈 Average: {total_added/total_time:.1f} docs/second")
    
    # 6. Verify the database
    print("\n🔍 Verifying database...")
    try:
        final_count = collection.count()
        print(f"📚 Final document count: {final_count:,}")
        
        # Test search
        test_results = collection.query(
            query_texts=["Haftung Schadensersatz"],
            n_results=5
        )
        
        found_results = len(test_results.get('ids', [[]])[0])
        print(f"🔍 Test query results: {found_results}")
        
        if found_results > 0:
            print("✅ Database is working correctly!")
            
            # Show sample results
            for i, doc in enumerate(test_results['documents'][0][:3]):
                metadata = test_results['metadatas'][0][i]
                gutachten_id = metadata.get('source_gutachten_id', 'N/A')
                print(f"   Sample {i+1}: Gutachten {gutachten_id} - '{doc[:80]}...'")
        else:
            print("❌ Test query failed!")
            return False
            
    except Exception as e:
        print(f"❌ Verification failed: {e}")
        return False
    
    print(f"\n🎉 VOLLSTÄNDIGE DATENBANK BEREIT!")
    print(f"📊 {final_count:,} Gutachten verfügbar für semantische Suche")
    print(f"🌐 Testen Sie jetzt in der Streamlit-App: http://localhost:8501")
    print(f"⏰ Ende: {datetime.now().strftime('%H:%M:%S')}")
    
    return True

if __name__ == "__main__":
    success = load_all_gutachten()
    if not success:
        print("\n❌ Database loading failed!")
        sys.exit(1)
