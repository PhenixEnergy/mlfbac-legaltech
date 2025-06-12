#!/usr/bin/env python3
"""
Clean up incomplete ChromaDB collections
Keeps only the complete 'legal_documents' collection with 3,936 documents
"""

import chromadb
import sys

def cleanup_incomplete_collections():
    """Delete incomplete collections from ChromaDB"""
    
    try:
        client = chromadb.PersistentClient(path="./data/vectordb")
        collections = client.list_collections()
        
        print("🧹 CHROMADB CLEANUP STARTED")
        print("=" * 50)
        
        # Collections to keep (complete data)
        keep_collections = ['legal_documents']
        
        # Collections to delete (incomplete data)
        collections_to_delete = [
            'dnoti_legal_documents',  # Only 930 docs instead of 3,936
            'dnoti_test',            # Only 5 docs (test data)
            'test_collection',       # Only 1 doc (test data)  
            'dnoti_gutachten'        # Only 4 docs (incomplete)
        ]
        
        print(f"📋 Found {len(collections)} total collections:")
        for col in collections:
            print(f"   - {col.name} ({col.count():,} documents)")
        
        print(f"\n✅ Collections to KEEP:")
        for col_name in keep_collections:
            for col in collections:
                if col.name == col_name:
                    print(f"   - {col_name} ({col.count():,} documents) ← COMPLETE DATA")
        
        print(f"\n❌ Collections to DELETE (incomplete data):")
        deleted_count = 0
        
        for col_name in collections_to_delete:
            try:
                # Check if collection exists
                collection_exists = any(col.name == col_name for col in collections)
                
                if collection_exists:
                    # Get document count before deletion
                    col = client.get_collection(col_name)
                    doc_count = col.count()
                    
                    # Delete the collection
                    client.delete_collection(col_name)
                    print(f"   ✅ Deleted '{col_name}' ({doc_count:,} documents)")
                    deleted_count += 1
                else:
                    print(f"   ⚠️  '{col_name}' not found (already deleted?)")
                    
            except Exception as e:
                print(f"   ❌ Error deleting '{col_name}': {str(e)}")
        
        print(f"\n🎉 CLEANUP COMPLETE!")
        print(f"   - Deleted: {deleted_count} incomplete collections")
        print(f"   - Kept: {len(keep_collections)} complete collection(s)")
        
        # Verify final state
        print(f"\n📊 FINAL DATABASE STATE:")
        remaining_collections = client.list_collections()
        total_docs = 0
        
        for col in remaining_collections:
            doc_count = col.count()
            total_docs += doc_count
            print(f"   - {col.name}: {doc_count:,} documents")
        
        print(f"\n✅ Total documents available: {total_docs:,}")
        
        if len(remaining_collections) == 1 and remaining_collections[0].name == 'legal_documents':
            print("🎯 Perfect! Only the complete 'legal_documents' collection remains.")
            print("   Your database is now clean and consistent!")
        
        return True
        
    except Exception as e:
        print(f"❌ Error during cleanup: {str(e)}")
        return False

if __name__ == "__main__":
    success = cleanup_incomplete_collections()
    sys.exit(0 if success else 1)
