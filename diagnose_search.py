#!/usr/bin/env python3
"""
Test script to diagnose why search is returning 0 results.
"""

import sys
import os
from pathlib import Path

# Add the src directory to Python path
sys.path.insert(0, str(Path(__file__).parent / 'src'))

from src.config import config
from src.vectordb.chroma_client import ChromaDBClient
from src.search.semantic_search import SemanticSearchEngine

def diagnose_search_issue():
    """Diagnose why search is returning 0 results."""
    print("=== Diagnosing Search Issue ===")
    
    # Test 1: Check configuration
    print(f"Config collection name: {config.CHROMA_COLLECTION_NAME}")
    print(f"Config embedding model: {config.EMBEDDING_MODEL}")
    
    # Test 2: Check ChromaDB client
    print("\n--- Initializing ChromaDB Client ---")
    try:
        db_client = ChromaDBClient()
        print(f"Available collections: {list(db_client.collections.keys())}")
        
        # Check if target collection exists and has data
        collection_name = config.CHROMA_COLLECTION_NAME
        if collection_name in db_client.collections:
            collection = db_client.collections[collection_name]
            count = collection.count()
            print(f"Collection '{collection_name}' contains {count} documents")
            
            # Get a sample document to check embedding dimensions
            if count > 0:
                sample = collection.peek(limit=1)
                if sample and 'embeddings' in sample and sample['embeddings']:
                    embedding_dim = len(sample['embeddings'][0])
                    print(f"Embedding dimensions: {embedding_dim}")
        else:
            print(f"❌ Collection '{collection_name}' not found!")
            
    except Exception as e:
        print(f"❌ Error with ChromaDB client: {e}")
        return
    
    # Test 3: Check semantic search engine
    print("\n--- Testing Semantic Search Engine ---")
    try:
        search_engine = SemanticSearchEngine(db_client)
        print(f"Search engine default collection: {search_engine.default_collection}")
        
        # Test a simple search
        print("\n--- Testing simple search ---")
        results = search_engine.search("Vertrag", top_k=3)
        print(f"Search returned {results.get('total_results', 0)} results")
        
        if results.get('total_results', 0) > 0:
            print("✅ Search is working!")
            for i, result in enumerate(results.get('results', [])):
                print(f"  Result {i+1}: {result.get('chunk_text', '')[:100]}...")
        else:
            print("❌ Search returned 0 results")
            
    except Exception as e:
        print(f"❌ Error with search engine: {e}")

if __name__ == "__main__":
    diagnose_search_issue()
