#!/usr/bin/env python3
"""
Simple script to check embedding dimensions in the stored collection.
"""

import sys
import os
from pathlib import Path

# Add the src directory to Python path
sys.path.insert(0, str(Path(__file__).parent / 'src'))

import chromadb
from src.config import config

def check_dimensions():
    """Check embedding dimensions."""
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
            # Get one sample document to check embedding dimensions
            sample = collection.get(limit=1, include=['embeddings'])
            
            if sample and sample.get('embeddings'):
                embeddings = sample['embeddings']
                if embeddings and len(embeddings) > 0:
                    embedding = embeddings[0]
                    if embedding:
                        dimensions = len(embedding)
                        print(f"Sample document: {dimensions} dimensions")
                        print(f"First 5 values: {embedding[:5]}")
                        
                        print(f"\n📊 Expected dimensions for IBM Granite: 768")
                        print(f"📊 Expected dimensions for old model: 384")
                        
                        if dimensions == 768:
                            print("✅ Stored embeddings match IBM Granite dimensions")
                        elif dimensions == 384:
                            print("❌ Stored embeddings are from old model - DIMENSION MISMATCH!")
                            print("   This explains why search returns 0 results.")
                            print("   Solution: Re-index the collection with IBM Granite embeddings")
                        else:
                            print(f"❓ Unknown embedding dimensions: {dimensions}")
                    else:
                        print("❌ Empty embedding")
                else:
                    print("❌ No embeddings in sample")
            else:
                print("❌ No embeddings found")
        else:
            print("❌ Collection is empty")
            
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    check_dimensions()
