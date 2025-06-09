import chromadb

def check_collections():
    try:
        # Initialize ChromaDB client
        client = chromadb.PersistentClient(path="./data/vectordb")
        
        # List all collections
        collections = client.list_collections()
        print(f"Found {len(collections)} collections:")
        
        for collection in collections:
            print(f"\nCollection: {collection.name}")
            print(f"Count: {collection.count()}")
            if collection.count() > 0:
                # Get a sample document
                results = collection.get(limit=1, include=['metadatas', 'documents'])
                if results['documents']:
                    print(f"Sample document preview: {results['documents'][0][:100]}...")
                if results['metadatas'] and results['metadatas'][0]:
                    print(f"Sample metadata: {results['metadatas'][0]}")
                    
    except Exception as e:
        print(f"Error checking collections: {e}")

if __name__ == "__main__":
    check_collections()
