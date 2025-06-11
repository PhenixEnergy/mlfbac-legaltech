#!/usr/bin/env python3
"""
Simple test to check collection dimensions without sentence-transformers
"""

import chromadb
import os

def check_collection_dimensions():
    """Check what dimensions existing collections expect"""
    
    # Initialize ChromaDB client
    persist_directory = "./data/vectordb"
    client = chromadb.PersistentClient(path=persist_directory)
    
    # List all collections
    collections = client.list_collections()
    print(f"📋 Found {len(collections)} collections:")
    
    collection_info = {}
    
    for collection in collections:
        print(f"\n🗂️  Collection: {collection.name}")
          try:
            # Get a sample document to check embedding dimension
            results = collection.peek(limit=1)
            doc_count = collection.count()
            
            if results.get('embeddings') is not None and len(results['embeddings']) > 0:
                embedding_dim = len(results['embeddings'][0])
                print(f"   📊 Expected embedding dimension: {embedding_dim}")
                print(f"   📄 Documents in collection: {doc_count}")
                
                collection_info[collection.name] = {
                    'dimension': embedding_dim,
                    'count': doc_count
                }
            else:
                print("   ⚠️  No embeddings found in collection")
                print(f"   📄 Documents in collection: {doc_count}")
                collection_info[collection.name] = {
                    'dimension': None,
                    'count': doc_count
                }
                
        except Exception as e:
            print(f"   ❌ Error checking collection: {e}")
            collection_info[collection.name] = {
                'dimension': 'error',
                'count': 'unknown'
            }
    
    return collection_info

def check_env_config():
    """Check current environment configuration"""
    
    # Load .env file manually
    env_file = ".env"
    config = {}
    
    if os.path.exists(env_file):
        with open(env_file, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    config[key.strip()] = value.strip()
    
    print(f"\n⚙️  CURRENT CONFIGURATION:")
    print(f"   📄 Default collection: {config.get('CHROMA_COLLECTION_NAME', 'Not set')}")
    print(f"   🤖 Embedding model: {config.get('EMBEDDING_MODEL', 'Not set')}")
    
    return config

def suggest_solution(collection_info, config):
    """Suggest the best solution"""
    
    print(f"\n💡 ANALYSIS & RECOMMENDATIONS:")
    print("=" * 50)
    
    target_collection = config.get('CHROMA_COLLECTION_NAME', 'legal_documents')
    
    if target_collection in collection_info:
        target_dim = collection_info[target_collection]['dimension']
        target_count = collection_info[target_collection]['count']
        
        print(f"🎯 Target collection: {target_collection}")
        print(f"📊 Required dimension: {target_dim}")
        print(f"📄 Documents available: {target_count}")
        
        # Find compatible collections
        compatible_collections = []
        for name, info in collection_info.items():
            if info['dimension'] == 384:  # Current model uses 384
                compatible_collections.append((name, info['count']))
        
        print(f"\n🔧 RECOMMENDED SOLUTIONS:")
        
        if target_dim == 768:
            print(f"❌ PROBLEM: Target collection requires 768-dim embeddings")
            print(f"   Current model likely produces 384-dim embeddings")
            print(f"\n✅ SOLUTION 1 (QUICK FIX): Use compatible collection")
            for name, count in compatible_collections:
                print(f"   - {name}: {count} documents (384-dim compatible)")
            
            print(f"\n✅ SOLUTION 2 (OPTIMAL): Use 768-dim embedding model")
            print(f"   Update .env file:")
            print(f"   EMBEDDING_MODEL=sentence-transformers/all-mpnet-base-v2")
            print(f"   (or another 768-dimension model)")
            
        elif target_dim == 384:
            print(f"✅ GOOD NEWS: Target collection is compatible!")
            print(f"   Current 384-dim model should work fine")
            
        else:
            print(f"⚠️  UNKNOWN: Unexpected dimension {target_dim}")
    
    else:
        print(f"❌ ERROR: Target collection '{target_collection}' not found!")

def main():
    """Main function"""
    print("🔍 CHROMADB COLLECTION DIMENSION ANALYSIS")
    print("=" * 50)
    
    # Check collections
    collection_info = check_collection_dimensions()
    
    # Check configuration  
    config = check_env_config()
    
    # Suggest solution
    suggest_solution(collection_info, config)

if __name__ == "__main__":
    main()
