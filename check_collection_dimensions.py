#!/usr/bin/env python3
"""
Test script to check embedding dimensions in the stored collection.
"""

import sys
import os
from pathlib import Path

# Add the src directory to Python path
sys.path.insert(0, str(Path(__file__).parent / 'src'))

import chromadb
from src.config import config

def check_collection_dimensions():
    """Check the actual dimensions of embeddings stored in the collection."""
    print("=== Checking Collection Embedding Dimensions ===")
    
    try:
        # Connect to ChromaDB
        client = chromadb.PersistentClient(path="./data/vectordb")
        
        collection_name = config.CHROMA_COLLECTION_NAME
        print(f"Checking collection: {collection_name}")
        
        # Get the collection
        collection = client.get_collection(collection_name)
        
        # Get collection info
        count = collection.count()
        print(f"Collection has {count} documents")
        
        if count > 0:
            # Get a few sample documents to check embedding dimensions
            sample = collection.get(limit=3, include=['embeddings', 'metadatas', 'documents'])
              if sample and 'embeddings' in sample and sample['embeddings'] is not None:
                embeddings = sample['embeddings']
                if len(embeddings) > 0:
                    if embedding:
                        dimensions = len(embedding)
                        print(f"Document {i+1}: {dimensions} dimensions")
                        print(f"  First 5 values: {embedding[:5]}")
                        
                        # Check if these are real embeddings or dummy/mock embeddings
                        unique_values = set(embedding[:20])  # Check first 20 values
                        if len(unique_values) == 1:
                            print(f"  ⚠️  WARNING: All values are the same ({list(unique_values)[0]}) - likely mock embeddings")
                        else:
                            print(f"  ✅ Real embeddings detected (varied values)")
                
                print(f"\n📊 Expected dimensions for IBM Granite: 768")
                print(f"📊 Expected dimensions for old model: 384")
                
                stored_dims = len(sample['embeddings'][0]) if sample['embeddings'][0] else 0
                if stored_dims == 768:
                    print("✅ Stored embeddings match IBM Granite dimensions")
                elif stored_dims == 384:
                    print("❌ Stored embeddings are from old model - DIMENSION MISMATCH!")
                    print("   This explains why search returns 0 results.")
                    print("   Solution: Re-index the collection with IBM Granite embeddings")
                else:
                    print(f"❓ Unknown embedding dimensions: {stored_dims}")
            else:
                print("❌ No embeddings found in sample")
        else:
            print("❌ Collection is empty")
            
    except Exception as e:
        print(f"❌ Error checking collection: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    check_collection_dimensions()
