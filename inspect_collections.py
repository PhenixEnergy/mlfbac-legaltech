#!/usr/bin/env python3
"""
Direct ChromaDB Collection Inspector
Bypasses configuration to check actual collection contents
"""
import chromadb
from pathlib import Path

def inspect_collections():
    """Inspect all collections directly in ChromaDB"""
    print("🔍 DIRECT CHROMADB COLLECTION INSPECTION")
    print("="*50)
    
    # Connect directly to ChromaDB
    client = chromadb.PersistentClient(path="./data/vectordb")
    
    # List all collections
    collections = client.list_collections()
    print(f"📁 Total Collections: {len(collections)}")
    
    for collection in collections:
        print(f"\n📂 Collection: {collection.name}")
        
        try:
            # Get collection object
            coll = client.get_collection(collection.name)
            
            # Get basic stats
            count = coll.count()
            print(f"   📊 Document Count: {count}")
            
            if count > 0:
                # Get a sample document
                sample = coll.get(limit=1, include=["metadatas", "documents"])
                if sample['ids']:
                    print(f"   🔹 Sample ID: {sample['ids'][0]}")
                    if sample['metadatas'] and sample['metadatas'][0]:
                        metadata = sample['metadatas'][0]
                        print(f"   🔹 Sample Metadata Keys: {list(metadata.keys())}")
                    if sample['documents'] and sample['documents'][0]:
                        doc_preview = sample['documents'][0][:100] + "..." if len(sample['documents'][0]) > 100 else sample['documents'][0]
                        print(f"   🔹 Sample Document: {doc_preview}")
            
        except Exception as e:
            print(f"   ❌ Error accessing collection: {e}")
    
    print("\n" + "="*50)

if __name__ == "__main__":
    inspect_collections()
