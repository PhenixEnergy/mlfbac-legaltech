#!/usr/bin/env python3
"""
Alternative approach to check collection dimensions.
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent / 'src'))

import chromadb
from src.config import config

try:
    # Connect to ChromaDB
    client = chromadb.PersistentClient(path="./data/vectordb")
    collection = client.get_collection(config.CHROMA_COLLECTION_NAME)
    
    print(f"Collection '{config.CHROMA_COLLECTION_NAME}' has {collection.count()} documents")
    
    # Try to peek at the collection
    peek_result = collection.peek(limit=1)
    
    print("Peek result keys:", list(peek_result.keys()) if peek_result else "None")
      if peek_result and 'embeddings' in peek_result:
        embeddings = peek_result['embeddings']
        print(f"Embeddings type: {type(embeddings)}")
        if embeddings is not None and len(embeddings) > 0:
            print(f"Number of embeddings: {len(embeddings)}")
            first_embedding = embeddings[0]
            print(f"First embedding type: {type(first_embedding)}")
            if hasattr(first_embedding, '__len__'):
                dimensions = len(first_embedding)
                print(f"🔍 FOUND: {dimensions} dimensions")
                
                if dimensions == 768:
                    print("✅ IBM Granite dimensions (768) - Configuration is correct!")
                elif dimensions == 384:
                    print("❌ Old model dimensions (384) - MISMATCH FOUND!")
                    print("   The collection was indexed with the old embedding model.")
                    print("   This is why search returns 0 results.")
                else:
                    print(f"❓ Unknown dimensions: {dimensions}")            else:
                print("Cannot determine dimensions")
        else:
            print("No embeddings in collection")
    else:
        print("No embeddings found in peek result")
        
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()
