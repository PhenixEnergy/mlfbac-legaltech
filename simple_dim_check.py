#!/usr/bin/env python3
"""
Simple dimension check
"""

import chromadb
import numpy as np

def simple_check():
    print("🔍 SIMPLE DIMENSION CHECK")
    print("=" * 30)
    
    client = chromadb.PersistentClient(path="./data/vectordb")
    collection = client.get_collection("legal_documents")
    
    print(f"Collection: {collection.name}")
    print(f"Documents: {collection.count()}")
    
    # Get sample with query
    results = collection.query(
        query_texts=["test"],
        n_results=1
    )
    
    if results['embeddings'] and len(results['embeddings']) > 0:
        dim = len(results['embeddings'][0])
        print(f"Embedding dimension: {dim}")
        
        if dim == 384:
            print("Model: sentence-transformers/all-MiniLM-L6-v2")
        elif dim == 768:
            print("Model: IBM Granite (768d)")
        else:
            print(f"Unknown model ({dim}d)")
    else:
        print("No embeddings found")

if __name__ == "__main__":
    simple_check()
