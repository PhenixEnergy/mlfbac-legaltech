"""ChromaDB Client with IBM Granite support"""

import chromadb
from chromadb.config import Settings
from sentence_transformers import SentenceTransformer
import logging
from typing import Dict, List, Optional, Any
from pathlib import Path
import json

logger = logging.getLogger(__name__)

class GraniteEmbeddingFunction:
    def __init__(self, model_name="ibm-granite/granite-embedding-278m-multilingual"):
        self.model_name = model_name
        self.model = None
        logger.info(f"GraniteEmbeddingFunction initialized with {model_name}")
    
    def name(self):
        return self.model_name
    
    def _load_model(self):
        if self.model is None:
            logger.info(f"Loading model {self.model_name}")
            self.model = SentenceTransformer(self.model_name)
            logger.info(f"Model {self.model_name} loaded successfully")
    
    def __call__(self, input):
        self._load_model()
        embeddings = self.model.encode(input, convert_to_numpy=True)
        return embeddings.tolist()

class DefaultEmbeddingFunction:
    def __init__(self, model_name="sentence-transformers/all-MiniLM-L6-v2"):
        self.model_name = model_name
        self.model = None
        logger.info(f"DefaultEmbeddingFunction initialized with {model_name}")
    
    def name(self):
        return self.model_name
    
    def _load_model(self):
        if self.model is None:
            logger.info(f"Loading model {self.model_name}")
            self.model = SentenceTransformer(self.model_name)
            logger.info(f"Model {self.model_name} loaded successfully")
    
    def __call__(self, input):
        self._load_model()
        embeddings = self.model.encode(input, convert_to_numpy=True)
        return embeddings.tolist()

class ChromaDBClient:
    def __init__(self):
        logger.info("Initializing ChromaDBClient")
        self.client = None
        # Don't initialize immediately to avoid import issues
        
    def _init_client(self):
        if self.client is not None:
            return
            
        logger.info("Initializing ChromaDB connection")
        try:
            persist_directory = "./data/vectordb"
            Path(persist_directory).mkdir(parents=True, exist_ok=True)
            
            settings = Settings(
                persist_directory=persist_directory,
                anonymized_telemetry=False,
                allow_reset=True
            )
            
            self.client = chromadb.PersistentClient(
                path=persist_directory,
                settings=settings
            )
            
            logger.info("ChromaDB client initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize ChromaDB client: {e}")
            raise
    
    def _get_embedding_function(self, collection_name: str):
        if collection_name == "legal_documents":
            return GraniteEmbeddingFunction()
        else:
            return DefaultEmbeddingFunction()
    
    def search_similar_chunks(self, query: str, collection_name: str, n_results: int = 10, filters: Optional[Dict] = None) -> Dict[str, Any]:
        # Initialize client on first use
        self._init_client()
        
        try:
            embedding_function = self._get_embedding_function(collection_name)
            logger.info(f"Using embedding function: {embedding_function.name()} for collection: {collection_name}")
            
            collection = self.client.get_collection(collection_name, embedding_function=embedding_function)
            
            results = collection.query(
                query_texts=[query],
                n_results=n_results,
                where=filters,
                include=['documents', 'metadatas', 'distances']
            )
            
            formatted_results = {
                'query': query,
                'total_results': len(results['documents'][0]) if results['documents'] else 0,
                'results': []
            }
            
            if results['documents'] and results['documents'][0]:
                for i in range(len(results['documents'][0])):
                    distance = results['distances'][0][i]
                    similarity_score = 1.0 / (1.0 + distance)
                    
                    result_item = {
                        'text': results['documents'][0][i],
                        'metadata': results['metadatas'][0][i] if results['metadatas'] else {},
                        'similarity_score': similarity_score,
                        'rank': i + 1
                    }
                    
                    if 'legal_norms' in result_item['metadata']:
                        try:
                            result_item['metadata']['legal_norms'] = json.loads(
                                result_item['metadata']['legal_norms']
                            )
                        except:
                            pass
                    
                    formatted_results['results'].append(result_item)
            
            logger.info(f"Search completed: {formatted_results['total_results']} results found")
            return formatted_results
            
        except Exception as e:
            logger.error(f"Error in search_similar_chunks: {e}")
            raise

logger.info("ChromaDBClient module loaded successfully")
