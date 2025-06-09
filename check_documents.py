import chromadb
import json

# Check what's actually in the database
try:
    client = chromadb.PersistentClient(path='./data/chroma')
    collection = client.get_collection('dnoti_legal_documents')
    
    # Get some sample documents to see common terms
    results = collection.get(limit=5, include=['metadatas', 'documents'])
    
    print('=== Sample Documents ===')
    for i, (doc, metadata) in enumerate(zip(results['documents'], results['metadatas'])):
        print(f'\nDoc {i+1} - Gutachten {metadata.get("gutachten_nummer", "N/A")}:')
        print(f'Text: {doc[:300]}...')
        
        # Look for section information
        if 'Sektion' in doc or 'sektion' in doc:
            print('  -> Contains Sektion info')
        
        # Try a simple query with this doc's content
        sample_words = doc.split()[:5]
        print(f'Sample words: {sample_words}')
        
except Exception as e:
    print(f'Error: {e}')
