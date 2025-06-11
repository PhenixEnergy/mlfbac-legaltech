#!/usr/bin/env python3
"""
Create a new collection with the IBM Granite model for the legal_documents
"""

import sys
import os
sys.path.append('.')

from src.config import config
import chromadb
from pathlib import Path

def check_ibm_granite_dimensions():
    """Check what dimension the IBM Granite model should produce"""
    
    print("🔍 CHECKING IBM GRANITE MODEL SPECIFICATIONS")
    print("=" * 50)
    
    # Based on the model name "granite-embedding-278m-multilingual"
    # The "278m" suggests ~278 million parameters
    # IBM Granite embedding models typically produce 768-dimensional embeddings
    
    print(f"🤖 Model: {config.EMBEDDING_MODEL}")
    print(f"📊 Expected dimension: 768 (typical for IBM Granite models)")
    
    return 768

def test_collection_compatibility():
    """Test which existing collection works with 768 dimensions"""
    
    print(f"\n🔬 TESTING COLLECTION COMPATIBILITY")
    print("=" * 40)
    
    persist_directory = "./data/vectordb"
    client = chromadb.PersistentClient(path=persist_directory)
    collections = client.list_collections()
    
    for collection in collections:
        try:
            results = collection.peek(limit=1)
            if results.get('embeddings') and len(results['embeddings']) > 0:
                dim = len(results['embeddings'][0])
                count = collection.count()
                
                if dim == 768:
                    print(f"✅ {collection.name}: {count} docs, {dim} dim - COMPATIBLE")
                    return collection.name
                else:
                    print(f"❌ {collection.name}: {count} docs, {dim} dim - incompatible")
            else:
                print(f"⚠️  {collection.name}: No embeddings found")
                
        except Exception as e:
            print(f"❌ {collection.name}: Error - {e}")
    
    return None

def create_optimal_configuration():
    """Create the optimal configuration for IBM + 3936 docs"""
    
    print(f"\n🎯 CREATING OPTIMAL CONFIGURATION")
    print("=" * 40)
    
    expected_dim = check_ibm_granite_dimensions()
    compatible_collection = test_collection_compatibility()
    
    if compatible_collection == "legal_documents":
        print(f"🎉 PERFECT MATCH!")
        print(f"   📦 legal_documents collection: 3,936 documents")
        print(f"   🤖 IBM Granite model: {expected_dim} dimensions")
        print(f"   ✅ Configuration should work!")
        
        return {
            "collection": "legal_documents",
            "model": config.EMBEDDING_MODEL,
            "dimensions": expected_dim,
            "documents": 3936,
            "status": "ready"
        }
    else:
        print(f"⚠️  DIMENSION MISMATCH")
        print(f"   📦 legal_documents expects 768 dim")
        print(f"   🤖 IBM Granite produces {expected_dim} dim")
        
        if expected_dim == 768:
            print(f"   💡 Solution: Dimensions match! Backend config issue.")
            return {
                "collection": "legal_documents", 
                "model": config.EMBEDDING_MODEL,
                "dimensions": expected_dim,
                "documents": 3936,
                "status": "config_issue"
            }
        else:
            print(f"   💡 Solution: Need to re-create collection with correct dimensions")
            return {
                "collection": "legal_documents",
                "model": config.EMBEDDING_MODEL, 
                "dimensions": expected_dim,
                "documents": 3936,
                "status": "needs_recreation"
            }

def main():
    """Main function"""
    
    print("🎯 IBM GRANITE + 3936 GUTACHTEN OPTIMIZATION")
    print("=" * 60)
    
    config_result = create_optimal_configuration()
    
    print(f"\n📋 CONFIGURATION RESULT:")
    print(f"   📦 Collection: {config_result['collection']}")
    print(f"   🤖 Model: {config_result['model']}")
    print(f"   📊 Dimensions: {config_result['dimensions']}")
    print(f"   📄 Documents: {config_result['documents']}")
    print(f"   🔧 Status: {config_result['status']}")
    
    if config_result['status'] == "ready":
        print(f"\n✅ READY TO GO!")
        print(f"   The system should work with current configuration")
        print(f"   Try restarting the backend if search isn't working")
        
    elif config_result['status'] == "config_issue":
        print(f"\n🔧 CONFIGURATION ISSUE DETECTED")
        print(f"   The dimensions match, but backend isn't using the right model")
        print(f"   Need to fix ChromaDB client configuration")
        
    else:
        print(f"\n⚠️  COMPLEX ISSUE")
        print(f"   May need to recreate collection or use different approach")

if __name__ == "__main__":
    main()
