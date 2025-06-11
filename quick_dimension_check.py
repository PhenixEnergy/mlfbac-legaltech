#!/usr/bin/env python3
import chromadb

client = chromadb.PersistentClient(path='./data/vectordb')
collection = client.get_collection('legal_documents')
print(f'Documents: {collection.count()}')
result = collection.peek(limit=1)
print(f"Result keys: {result.keys()}")
if result['embeddings'] is not None and len(result['embeddings']) > 0:
    print(f'Embedding dimensions: {len(result["embeddings"][0])}')
else:
    print('No embeddings found')
