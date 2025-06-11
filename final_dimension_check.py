#!/usr/bin/env python3
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent / 'src'))

import chromadb
from src.config import config
import numpy as np

try:
    client = chromadb.PersistentClient(path="./data/vectordb")
    collection = client.get_collection(config.CHROMA_COLLECTION_NAME)
    
    print(f"Collection '{config.CHROMA_COLLECTION_NAME}' has {collection.count()} documents")
    
    peek_result = collection.peek(limit=1)
    
    if peek_result and 'embeddings' in peek_result:
        embeddings = peek_result['embeddings']
        print(f"Embeddings shape: {embeddings.shape}")
        
        if len(embeddings) > 0:
            dimensions = embeddings.shape[1]  # Second dimension is the embedding size
            print(f"🔍 Embedding dimensions: {dimensions}")
            
            if dimensions == 768:
                print("✅ IBM Granite dimensions (768) - Collection is correctly indexed!")
            elif dimensions == 384:
                print("❌ Old model dimensions (384) - DIMENSION MISMATCH!")
                print("   The collection contains embeddings from the old model.")
                print("   This explains why search returns 0 results with the new IBM Granite model.")
                print("   SOLUTION: Re-index the collection with IBM Granite embeddings.")
            else:
                print(f"❓ Unknown dimensions: {dimensions}")
        else:
            print("No embeddings found")
    else:
        print("No embeddings in peek result")
        
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()
