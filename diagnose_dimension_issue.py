#!/usr/bin/env python3
"""
Diagnose dimension mismatch between database and config
"""

import sys
import os
sys.path.append('.')

import chromadb
from src.config import config

def check_dimension_mismatch():
    """Check if there's a dimension mismatch"""
    
    print("🔍 DIMENSION MISMATCH DIAGNOSIS")
    print("=" * 50)
    
    # Connect to database
    persist_directory = "./data/vectordb"
    client = chromadb.PersistentClient(path=persist_directory)
    
    try:
        collection = client.get_collection("legal_documents")
        print(f"✅ Found collection: {collection.name}")
        print(f"📊 Document count: {collection.count()}")
        
        # Get a sample document
        results = collection.peek(limit=1)
        if results.get('embeddings') and len(results['embeddings']) > 0:
            actual_dim = len(results['embeddings'][0])
            print(f"📏 Actual embedding dimension: {actual_dim}")
            
            # Check configured model
            print(f"🤖 Configured model: {config.EMBEDDING_MODEL}")
            
            if "all-MiniLM-L6-v2" in str(actual_dim == 384):
                print(f"💡 Database created with: sentence-transformers/all-MiniLM-L6-v2 (384 dim)")
            elif actual_dim == 768:
                print(f"💡 Database created with: IBM Granite model (768 dim)")
            else:
                print(f"⚠️  Unknown embedding model for {actual_dim} dimensions")
            
            # Check if mismatch
            if config.EMBEDDING_MODEL == "ibm-granite/granite-embedding-278m-multilingual" and actual_dim != 768:
                print(f"\n❌ DIMENSION MISMATCH DETECTED!")
                print(f"   Database has: {actual_dim} dimensions")
                print(f"   Config expects: 768 dimensions (IBM Granite)")
                print(f"\n💡 SOLUTION OPTIONS:")
                print(f"   1. Update .env to use: sentence-transformers/all-MiniLM-L6-v2")
                print(f"   2. Recreate database with IBM Granite model")
                return "mismatch", actual_dim
            else:
                print(f"✅ Dimensions match configuration")
                return "match", actual_dim
                
        else:
            print(f"❌ No embeddings found in collection")
            return "no_embeddings", 0
            
    except Exception as e:
        print(f"❌ Error accessing collection: {e}")
        return "error", 0

if __name__ == "__main__":
    status, dim = check_dimension_mismatch()
    print(f"\nStatus: {status}, Dimension: {dim}")
