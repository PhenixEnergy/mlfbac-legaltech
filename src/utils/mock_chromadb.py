"""Mock ChromaDB client for testing API structure without full ML dependencies."""

import json
import os
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime
from pathlib import Path


class MockCollection:
    """Mock ChromaDB collection for testing."""
    
    def __init__(self, name: str):
        self.name = name
        self._data = []
        self._metadata = {}
        
    def add(self, documents: List[str] = None, metadatas: List[Dict] = None, 
           ids: List[str] = None, embeddings: List[List[float]] = None):
        """Mock add method."""
        if not documents:
            return
            
        for i, doc in enumerate(documents):
            item = {
                'id': ids[i] if ids else f"doc_{len(self._data)}",
                'document': doc,
                'metadata': metadatas[i] if metadatas else {},
                'embedding': embeddings[i] if embeddings else [0.1] * 768
            }
            self._data.append(item)
    
    def query(self, query_embeddings: List[List[float]] = None, 
             query_texts: List[str] = None, n_results: int = 10,
             where: Dict = None, include: List[str] = None):
        """Mock query method."""
        # Return mock results
        results = {
            'ids': [['doc_0', 'doc_1']],
            'distances': [[0.1, 0.2]],
            'documents': [['Mock document 1', 'Mock document 2']],
            'metadatas': [[{'source': 'test1'}, {'source': 'test2'}]]
        }
        return results
        
    def get(self, ids: List[str] = None, where: Dict = None, 
           include: List[str] = None):
        """Mock get method."""
        return {
            'ids': ids or ['doc_0'],
            'documents': ['Mock document'],
            'metadatas': [{'source': 'test'}]
        }
        
    def count(self):
        """Mock count method."""
        return len(self._data)
        
    def delete(self, ids: List[str] = None, where: Dict = None):
        """Mock delete method."""
        if ids:
            self._data = [item for item in self._data if item['id'] not in ids]


class MockChromaClient:
    """Mock ChromaDB client for testing."""
    
    def __init__(self, path: str = None):
        self.path = path
        self._collections = {}
        
    def create_collection(self, name: str, metadata: Dict = None, 
                         embedding_function=None):
        """Mock create collection."""
        collection = MockCollection(name)
        self._collections[name] = collection
        return collection
        
    def get_collection(self, name: str, embedding_function=None):
        """Mock get collection."""
        if name not in self._collections:
            return self.create_collection(name)
        return self._collections[name]
        
    def get_or_create_collection(self, name: str, embedding_function=None,
                               metadata: Dict = None):
        """Mock get or create collection."""
        return self.get_collection(name, embedding_function)
        
    def list_collections(self):
        """Mock list collections."""
        return [type('Collection', (), {'name': name})() for name in self._collections.keys()]
        
    def delete_collection(self, name: str):
        """Mock delete collection."""
        if name in self._collections:
            del self._collections[name]


class MockEmbeddingFunction:
    """Mock embedding function."""
    
    def __call__(self, texts: List[str]) -> List[List[float]]:
        """Mock embedding generation."""
        return [[0.1] * 768 for _ in texts]
        
    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        return self(texts)
        
    def embed_query(self, text: str) -> List[float]:
        return [0.1] * 768


# Mock module functions
def PersistentClient(path: str = None, settings=None):
    return MockChromaClient(path)

def Client():
    return MockChromaClient()

def get_mock_embedding_function():
    """Get mock embedding function."""
    return MockEmbeddingFunction()


class MockChromaDB:
    """Mock chromadb module for import replacement."""
    
    def __init__(self):
        self.client = MockChromaClient()
    
    def get_or_create_collection(self, name: str, embedding_function=None,
                               metadata: Dict = None):
        """Mock get or create collection."""
        return self.client.get_or_create_collection(name, embedding_function, metadata)
    
    def create_collection(self, name: str, metadata: Dict = None, 
                         embedding_function=None):
        """Mock create collection."""
        return self.client.create_collection(name, metadata, embedding_function)
        
    def get_collection(self, name: str, embedding_function=None):
        """Mock get collection."""
        return self.client.get_collection(name, embedding_function)
    
    PersistentClient = staticmethod(PersistentClient)
    Client = staticmethod(Client)


# Add sample data loading functionality
def load_sample_data():
    """Load sample data from files"""
    sample_data_dir = Path(__file__).parent.parent.parent / "sample_data"
    
    documents = []
    qa_pairs = []
    
    try:
        if (sample_data_dir / "sample_documents.json").exists():
            with open(sample_data_dir / "sample_documents.json", "r", encoding="utf-8") as f:
                documents = json.load(f)
        
        if (sample_data_dir / "sample_qa.json").exists():
            with open(sample_data_dir / "sample_qa.json", "r", encoding="utf-8") as f:
                qa_pairs = json.load(f)
                
    except Exception as e:
        print(f"Warning: Could not load sample data: {e}")
    
    return documents, qa_pairs

# Global sample data
SAMPLE_DOCUMENTS, SAMPLE_QA = load_sample_data()
