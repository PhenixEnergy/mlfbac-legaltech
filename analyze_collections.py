#!/usr/bin/env python3
"""
Analysis script to understand collection dimensions and find the best solution
"""

import sys
sys.path.append('.')
from src.vectordb.chroma_client import ChromaDBClient, GraniteEmbeddingFunction

def analyze_collections():
    print("=== Collection Analysis ===")
    
    client = ChromaDBClient()
    
    # List all collections
    collections = client.client.list_collections()
    print(f"Found {len(collections)} collections:")
    
    for collection_info in collections:
        name = collection_info.name
        count = collection_info.count()
        
        print(f"\nCollection: {name}")
        print(f"  Documents: {count}")
        
        # Try to get a sample document to understand the embedding dimension
        try:
            # Test with default embedding function (might fail)
            collection_default = client.client.get_collection(name)
            sample_results = collection_default.query(
                query_texts=["test"],
                n_results=1
            )
            
            if sample_results['documents'] and sample_results['documents'][0]:
                print(f"  ✅ Compatible with default embedding function")
            else:
                print(f"  ⚠️  No documents found with default function")
                
        except Exception as e:
            print(f"  ❌ Default embedding failed: {str(e)[:100]}...")
            
            # Try with Granite embedding function
            try:
                collection_granite = client.client.get_collection(
                    name, 
                    embedding_function=client.embedding_function
                )
                sample_results = collection_granite.query(
                    query_texts=["test"],
                    n_results=1
                )
                
                if sample_results['documents'] and sample_results['documents'][0]:
                    print(f"  ✅ Compatible with Granite embedding function")
                else:
                    print(f"  ⚠️  No documents found with Granite function")
                    
            except Exception as e2:
                print(f"  ❌ Granite embedding also failed: {str(e2)[:100]}...")

def find_working_collection():
    """Find a collection that works with Granite embedding function"""
    print("\n=== Finding Working Collection ===")
    
    client = ChromaDBClient()
    collections = client.client.list_collections()
    
    for collection_info in collections:
        name = collection_info.name
        count = collection_info.count()
        
        if count == 0:
            continue
            
        try:
            collection = client.client.get_collection(
                name, 
                embedding_function=client.embedding_function
            )
            
            # Test search
            results = collection.query(
                query_texts=["Schadensersatz"],
                n_results=3
            )
            
            if results['documents'] and results['documents'][0]:
                print(f"🎯 WORKING COLLECTION: {name}")
                print(f"   Documents: {count}")
                print(f"   Search results: {len(results['documents'][0])}")
                
                # Show sample results
                for i, doc in enumerate(results['documents'][0]):
                    distance = results['distances'][0][i] if results['distances'] else 0
                    similarity = 1.0 / (1.0 + distance)
                    print(f"   Result {i+1}: similarity={similarity:.3f}")
                    
                return name
                
        except Exception as e:
            continue
    
    print("❌ No working collection found")
    return None

if __name__ == "__main__":
    analyze_collections()
    working_collection = find_working_collection()
    
    if working_collection:
        print(f"\n💡 SOLUTION: Use collection '{working_collection}' in SemanticSearchEngine")
        print(f"   Modify src/search/semantic_search.py line ~241:")
        print(f"   self.default_collection = \"{working_collection}\"")
    else:
        print("\n❌ No compatible collection found. Database recreation may be needed.")
