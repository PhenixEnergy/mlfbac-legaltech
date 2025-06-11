#!/usr/bin/env python3
"""
Comprehensive diagnostic for IBM Granite search issues
"""

def test_chroma_direct():
    """Test ChromaDB directly"""
    print("🔍 Testing ChromaDB directly...")
    
    try:
        import chromadb
        from sentence_transformers import SentenceTransformer
        
        # Load IBM Granite model
        print("Loading IBM Granite model...")
        model = SentenceTransformer('ibm-granite/granite-embedding-278m-multilingual')
        
        # Test embedding generation
        test_query = "Schadensersatz"
        query_embedding = model.encode([test_query])
        print(f"✅ Query embedding shape: {query_embedding.shape}")
        
        # Connect to ChromaDB
        client = chromadb.PersistentClient(path='./data/vectordb')
        print(f"✅ Connected to ChromaDB")
        
        # Get collection
        collections = client.list_collections()
        print(f"Available collections: {[c.name for c in collections]}")
        
        if any(c.name == 'legal_documents' for c in collections):
            collection = client.get_collection('legal_documents')
            count = collection.count()
            print(f"✅ legal_documents collection has {count} documents")
            
            # Test direct search
            print("Testing direct ChromaDB search...")
            results = collection.query(
                query_embeddings=query_embedding.tolist(),
                n_results=3,
                include=['documents', 'metadatas', 'distances']
            )
            
            if results['documents'] and results['documents'][0]:
                print(f"✅ SUCCESS! Found {len(results['documents'][0])} results")
                print(f"Best distance: {results['distances'][0][0]:.4f}")
                print(f"Sample text: {results['documents'][0][0][:100]}...")
                return True
            else:
                print("❌ No results from ChromaDB direct search")
                return False
        else:
            print("❌ legal_documents collection not found")
            return False
            
    except Exception as e:
        print(f"❌ Error in direct test: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_api_health():
    """Test API health"""
    print("\n💊 Testing API health...")
    
    try:
        import requests
        response = requests.get('http://localhost:8000/health', timeout=5)
        if response.status_code == 200:
            print("✅ API health check passed")
            return True
        else:
            print(f"❌ API health check failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ API health check error: {e}")
        return False

def main():
    print("🧪 IBM Granite Search Diagnostic")
    print("=" * 50)
    
    # Set working directory
    import os
    os.chdir(r'c:\Users\rafael.schumm\LegalTech\mlfbac-legaltech')
    
    # Test ChromaDB directly
    direct_works = test_chroma_direct()
    
    # Test API
    api_works = test_api_health()
    
    print("\n📊 SUMMARY:")
    print(f"Direct ChromaDB search: {'✅ WORKS' if direct_works else '❌ FAILED'}")
    print(f"API health: {'✅ WORKS' if api_works else '❌ FAILED'}")
    
    if direct_works and api_works:
        print("\n🎯 DIAGNOSIS: Both ChromaDB and API work - issue might be in search engine routing")
    elif direct_works and not api_works:
        print("\n🎯 DIAGNOSIS: ChromaDB works but API has issues")
    elif not direct_works:
        print("\n🎯 DIAGNOSIS: ChromaDB direct search fails - embedding/collection issue")

if __name__ == "__main__":
    main()
