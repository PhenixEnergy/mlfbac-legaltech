"""
ChromaDB Client für dnoti Legal Tech Anwendung
Implementiert Vektordatenbank-Operationen mit IBM Granite Embeddings
"""

# Versuche ChromaDB zu importieren, verwende Mock falls nicht verfügbar
try:
    import chromadb
    from chromadb.config import Settings
    from chromadb.utils import embedding_functions
    CHROMADB_AVAILABLE = True
except ImportError:
    # Verwende Mock-Implementation für Entwicklung/Tests
    from ..utils.mock_chromadb import MockChromaDB, get_mock_embedding_function
    chromadb = MockChromaDB()
    Settings = None
    embedding_functions = type('MockEmbeddingFunctions', (), {
        'SentenceTransformerEmbeddingFunction': get_mock_embedding_function
    })()
    CHROMADB_AVAILABLE = False
    print("Warning: ChromaDB not available, using mock implementation")

# Weitere Imports mit Fallback
try:
    import numpy as np
    NUMPY_AVAILABLE = True
except ImportError:
    # Minimal numpy replacement for basic operations
    class MockNumpy:
        @staticmethod
        def array(data):
            return data
        @staticmethod
        def mean(data):
            return sum(data) / len(data) if data else 0
    np = MockNumpy()
    NUMPY_AVAILABLE = False

# Weitere Imports mit Fallback
try:
    from sentence_transformers import SentenceTransformer
    SENTENCE_TRANSFORMERS_AVAILABLE = True
except ImportError:
    # Mock SentenceTransformer
    class MockSentenceTransformer:
        def __init__(self, model_name):
            self.model_name = model_name
        def encode(self, texts, convert_to_numpy=True):
            if isinstance(texts, str):
                return [0.1] * 768
            return [[0.1] * 768 for _ in texts]
    SentenceTransformer = MockSentenceTransformer
    SENTENCE_TRANSFORMERS_AVAILABLE = False

try:
    import yaml
    YAML_AVAILABLE = True
except ImportError:
    # Mock yaml für basic operations
    class MockYaml:
        @staticmethod
        def safe_load(stream):
            return {}
    yaml = MockYaml()
    YAML_AVAILABLE = False

try:
    import psutil
    PSUTIL_AVAILABLE = True
except ImportError:
    psutil = None
    PSUTIL_AVAILABLE = False

from typing import Dict, List, Optional, Union, Tuple, Any
from pathlib import Path
import logging
import json
from datetime import datetime
import uuid

# Local imports
from ..data.chunker import TextChunk, ChunkMetadata

logger = logging.getLogger(__name__)


class GraniteEmbeddingFunction:
    """
    Custom Embedding Function für IBM Granite Modell
    Wrapper um sentence-transformers für Chroma-Kompatibilität
    """
    
    def __init__(self, model_name: str = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"):
        self.model_name = model_name
        self.model = None  # Lazy loading
        logger.info(f"Initialized embedding function with model: {model_name}")
    
    def name(self) -> str:
        """Return the name of the embedding function for ChromaDB compatibility"""
        return self.model_name
    
    def _load_model(self):
        """Lazy load the model only when needed"""
        if self.model is None:
            try:
                if SENTENCE_TRANSFORMERS_AVAILABLE:
                    from sentence_transformers import SentenceTransformer
                    self.model = SentenceTransformer(self.model_name)
                    logger.info(f"Loaded embedding model: {self.model_name}")
                else:
                    self.model = MockSentenceTransformer(self.model_name)
                    logger.info(f"Using mock embedding model: {self.model_name}")
            except Exception as e:
                logger.error(f"Failed to load embedding model {self.model_name}: {e}")
                self.model = MockSentenceTransformer(self.model_name)
                logger.info("Falling back to mock embedding model")
    
    def __call__(self, input: List[str]) -> List[List[float]]:
        """
        Erstellt Embeddings für eine Liste von Texten
        
        Args:
            input: Liste von Texten
            
        Returns:
            Liste von Embedding-Vektoren
        """
        try:
            self._load_model()  # Ensure model is loaded
            embeddings = self.model.encode(input, convert_to_numpy=True)
            if hasattr(embeddings, 'tolist'):
                return embeddings.tolist()
            else:
                return embeddings  # Already a list from mock
        except Exception as e:
            logger.error(f"Error creating embeddings: {e}")
            # Return mock embeddings as fallback
            return [[0.1] * 768 for _ in input]


class ChromaDBClient:
    """
    ChromaDB Client für Legal Tech Vektordatenbank
    
    Funktionen:
    - Verbindungsmanagement zu ChromaDB
    - Collection-Management für Gutachten
    - Chunk-Speicherung mit Metadaten
    - Semantische Suche
    - Batch-Operationen für große Datenmengen
    """

class ChromaDBClient:
    """
    ChromaDB Client für Legal Tech Vektordatenbank
    
    Funktionen:
    - Verbindungsmanagement zu ChromaDB
    - Collection-Management für Gutachten
    - Chunk-Speicherung mit Metadaten
    - Semantische Suche
    - Batch-Operationen für große Datenmengen
    """
    
    def __init__(self, config_path: Optional[Union[str, Path]] = None):
        """
        Initialisiert ChromaDB Client
        
        Args:
            config_path: Pfad zur Datenbank-Konfigurationsdatei
        """
        self.config = self._load_config(config_path)
        self.client = None
        self.collections = {}
        self.embedding_function = None
        
        # Client initialisieren
        self._init_client()
        self._init_embedding_function()
        self._load_existing_collections()
        
    def _load_config(self, config_path: Optional[Union[str, Path]]) -> Dict:
        """Lädt Datenbank-Konfiguration"""
        if config_path and Path(config_path).exists():
            with open(config_path, 'r', encoding='utf-8') as f:
                return yaml.safe_load(f)
        else:
            return self._get_default_config()
    
    def _get_default_config(self) -> Dict:
        """Standard-Konfiguration für ChromaDB"""
        return {
            'chromadb': {
                'host': 'localhost',
                'port': 8000,
                'persist_directory': './data/vectordb',
                'settings': {
                    'anonymized_telemetry': False,
                    'allow_reset': True
                }
            },
            'collections': {
                'gutachten_chunks': {
                    'name': 'dnoti_gutachten_chunks',
                    'metadata': {
                        'description': 'Chunked legal documents from dnoti database',
                        'version': '1.0'
                    }
                }
            },
            'embedding': {
                'model': 'sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2',
                'dimensions': 384
            }
        }
    
    def _init_client(self):
        """Initialisiert ChromaDB Client"""
        try:
            chroma_config = self.config.get('chromadb', {})
            
            # Persistenter Client mit lokalem Verzeichnis
            persist_directory = chroma_config.get('persist_directory', './data/vectordb')
            Path(persist_directory).mkdir(parents=True, exist_ok=True)
            
            settings = Settings(
                persist_directory=persist_directory,
                anonymized_telemetry=chroma_config.get('settings', {}).get('anonymized_telemetry', False),
                allow_reset=chroma_config.get('settings', {}).get('allow_reset', True)
            )
            
            self.client = chromadb.PersistentClient(
                path=persist_directory,
                settings=settings
            )
            
            logger.info(f"ChromaDB client initialized with persist directory: {persist_directory}")
            
        except Exception as e:
            logger.error(f"Failed to initialize ChromaDB client: {e}")
            raise
    
    def _init_embedding_function(self):
        """Initialisiert Embedding-Funktion"""
        try:
            model_name = self.config.get('embedding', {}).get('model', 
                'sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2')
            self.embedding_function = GraniteEmbeddingFunction(model_name)
            logger.info("Embedding function initialized")
        except Exception as e:
            logger.error(f"Failed to initialize embedding function: {e}")
            raise
    
    def _load_existing_collections(self):
        """Lädt existierende Collections in das collections Dictionary"""
        try:
            existing_collections = self.client.list_collections()
            for collection in existing_collections:
                self.collections[collection.name] = collection
            logger.info(f"Loaded {len(self.collections)} existing collections")
        except Exception as e:
            logger.warning(f"Could not load existing collections: {e}")

    def _get_collection(self, collection_name: str) -> Any:
        """
        Holt eine Collection, lädt sie falls nötig
        
        Args:
            collection_name: Name der Collection
            
        Returns:
            Collection object
        """
        if collection_name not in self.collections:
            try:
                collection = self.client.get_collection(collection_name)
                self.collections[collection_name] = collection
                logger.info(f"Loaded collection: {collection_name}")
            except Exception as e:
                raise ValueError(f"Collection {collection_name} not found: {e}")
        
        return self.collections[collection_name]

    def create_collection(self, collection_name: str, reset_if_exists: bool = False) -> Any:
        """
        Erstellt oder lädt eine ChromaDB Collection
        
        Args:
            collection_name: Name der Collection
            reset_if_exists: Ob Collection zurückgesetzt werden soll falls sie existiert
            
        Returns:
            ChromaDB Collection Objekt
        """
        try:
            if reset_if_exists:
                try:
                    self.client.delete_collection(collection_name)
                    logger.info(f"Deleted existing collection: {collection_name}")
                except:
                    pass  # Collection existierte nicht
              # Collection erstellen oder laden
            collection_metadata = self.config.get('collections', {}).get(collection_name, {}).get('metadata', {})
            # Ensure metadata is not empty for ChromaDB
            if not collection_metadata:
                collection_metadata = {"created_by": "legaltech_system"}
            
            collection = self.client.get_or_create_collection(
                name=collection_name,
                embedding_function=self.embedding_function,
                metadata=collection_metadata
            )
            
            self.collections[collection_name] = collection
            logger.info(f"Collection ready: {collection_name}")
            
            return collection
            
        except Exception as e:
            logger.error(f"Error creating collection {collection_name}: {e}")
            raise
    
    def add_chunks_to_collection(self, 
                                                                collection_name: str, 
                                chunks: List[TextChunk], 
                                batch_size: int = 100) -> Dict[str, Any]:
        """
        Fügt Text-Chunks zur Collection hinzu
        
        Args:
            collection_name: Name der Collection
            chunks: Liste von TextChunk Objekten
            batch_size: Anzahl Chunks pro Batch
            
        Returns:
            Statistiken über den Import        """
        if collection_name not in self.collections:
            raise ValueError(f"Collection {collection_name} not found")
        
        collection = self.collections[collection_name]
        
        stats = {
            'total_chunks': len(chunks),
            'successful_adds': 0,
            'failed_adds': 0,
            'batches_processed': 0,
            'errors': []
        }
        
        try:
            # Chunks in Batches verarbeiten
            for i in range(0, len(chunks), batch_size):
                batch_chunks = chunks[i:i + batch_size]
                
                try:
                    # Daten für Batch vorbereiten
                    documents = []
                    metadatas = []
                    ids = []
                    
                    for chunk in batch_chunks:
                        documents.append(chunk.text)
                        
                        # Metadaten für ChromaDB vorbereiten (nur Strings/Numbers)
                        metadata = self._prepare_metadata_for_chroma(chunk.metadata)
                        metadatas.append(metadata)
                        
                        # Eindeutige ID generieren wenn nicht vorhanden
                        chunk_id = chunk.metadata.chunk_id or str(uuid.uuid4())
                        ids.append(chunk_id)
                    
                    # Batch zur Collection hinzufügen
                    collection.add(
                        documents=documents,
                        metadatas=metadatas,
                        ids=ids
                    )
                    
                    stats['successful_adds'] += len(batch_chunks)
                    stats['batches_processed'] += 1
                    
                    logger.info(f"Added batch {stats['batches_processed']}: {len(batch_chunks)} chunks")
                    
                except Exception as batch_error:
                    stats['failed_adds'] += len(batch_chunks)
                    stats['errors'].append(f"Batch {i//batch_size + 1}: {str(batch_error)}")
                    logger.error(f"Error adding batch {i//batch_size + 1}: {batch_error}")
            
            logger.info(f"Chunk import completed. Success: {stats['successful_adds']}, Failed: {stats['failed_adds']}")
            
        except Exception as e:
            logger.error(f"Error in add_chunks_to_collection: {e}")
            stats['errors'].append(str(e))
        
        return stats
    
    def _prepare_metadata_for_chroma(self, metadata: ChunkMetadata) -> Dict[str, Union[str, int, float]]:
        """
        Bereitet Metadaten für ChromaDB vor (nur primitive Typen erlaubt)
        
        Args:
            metadata: ChunkMetadata Objekt
            
        Returns:
            Dict mit ChromaDB-kompatiblen Metadaten
        """
        chroma_metadata = {
            'chunk_id': metadata.chunk_id,
            'source_gutachten_id': metadata.source_gutachten_id,
            'level': metadata.level,
            'start_char': metadata.start_char,
            'end_char': metadata.end_char,
            'token_count': metadata.token_count,
            'semantic_score': metadata.semantic_score,
            'relevance_score': metadata.relevance_score,
            'created_at': datetime.now().isoformat()
        }
        
        # Optionale Felder hinzufügen wenn vorhanden
        if metadata.section_type:
            chroma_metadata['section_type'] = metadata.section_type
        
        # Listen in JSON-Strings konvertieren
        if metadata.legal_norms:
            chroma_metadata['legal_norms'] = json.dumps(metadata.legal_norms)
        
        if metadata.keywords:
            chroma_metadata['keywords'] = json.dumps(metadata.keywords)
        
        return chroma_metadata
    
    def search_similar_chunks(self, 
                             query: str, 
                             collection_name: str,
                             n_results: int = 10,
                             filters: Optional[Dict] = None) -> Dict[str, Any]:
        """
        Sucht ähnliche Chunks basierend auf semantischer Ähnlichkeit
        
        Args:
            query: Suchanfrage
            collection_name: Name der Collection
            n_results: Anzahl gewünschter Ergebnisse
            filters: Optionale Metadaten-Filter
              Returns:
            Suchergebnisse mit Chunks und Similarity Scores
        """
        collection = self._get_collection(collection_name)
        
        try:
            # Semantische Suche durchführen
            results = collection.query(
                query_texts=[query],
                n_results=n_results,
                where=filters,
                include=['documents', 'metadatas', 'distances']
            )
            
            # Ergebnisse strukturieren
            formatted_results = {
                'query': query,
                'total_results': len(results['documents'][0]) if results['documents'] else 0,
                'results': []
            }
            
            if results['documents'] and results['documents'][0]:
                for i in range(len(results['documents'][0])):                    # Convert distance to similarity score
                    # ChromaDB uses squared euclidean distance for this model
                    # Use decay function to convert distance to similarity [0,1]
                    distance = results['distances'][0][i]
                    
                    # Decay function: smaller distances = higher similarity
                    # This gives reasonable scores: ~0.18 for distance 4.3
                    similarity_score = 1.0 / (1.0 + distance)
                    
                    result_item = {
                        'text': results['documents'][0][i],
                        'metadata': results['metadatas'][0][i],
                        'similarity_score': similarity_score,
                        'rank': i + 1
                    }
                    
                    # Metadaten rekonstruieren
                    if 'legal_norms' in result_item['metadata']:
                        try:
                            result_item['metadata']['legal_norms'] = json.loads(
                                result_item['metadata']['legal_norms']
                            )
                        except:
                            pass
                    
                    if 'keywords' in result_item['metadata']:
                        try:
                            result_item['metadata']['keywords'] = json.loads(
                                result_item['metadata']['keywords']
                            )
                        except:
                            pass
                    
                    formatted_results['results'].append(result_item)
            
            logger.info(f"Search completed: {formatted_results['total_results']} results for query: '{query[:50]}...'")
            return formatted_results
            
        except Exception as e:
            logger.error(f"Error in semantic search: {e}")
            raise
    
    def search_with_filters(self, 
                           collection_name: str,
                           filters: Dict,
                           limit: Optional[int] = None) -> List[Dict]:
        """
        Sucht Chunks basierend auf Metadaten-Filtern
        
        Args:
            collection_name: Name der Collection
            filters: Metadaten-Filter (ChromaDB Where-Klausel)
            limit: Maximale Anzahl Ergebnisse
            
        Returns:        Liste von gefilterten Chunks
        """
        collection = self._get_collection(collection_name)
        
        try:
            results = collection.get(
                where=filters,
                limit=limit,
                include=['documents', 'metadatas']
            )
            
            formatted_results = []
            
            if results['documents']:
                for i in range(len(results['documents'])):
                    result_item = {
                        'text': results['documents'][i],
                        'metadata': results['metadatas'][i]
                    }
                    formatted_results.append(result_item)
            
            logger.info(f"Filter search completed: {len(formatted_results)} results")
            return formatted_results
            
        except Exception as e:
            logger.error(f"Error in filter search: {e}")
            raise
    
    def get_collection_stats(self, collection_name: str) -> Dict[str, Any]:
        """
        Ruft Statistiken über eine Collection ab
        
        Args:
            collection_name: Name der Collection
            
        Returns:
            Statistiken über die Collection        """
        collection = self._get_collection(collection_name)
        
        try:
            total_count = collection.count()
            
            # Sample-Metadaten für Analyse
            sample_results = collection.get(
                limit=min(100, total_count),
                include=['metadatas']
            )
            
            stats = {
                'collection_name': collection_name,
                'total_chunks': total_count,
                'sample_size': len(sample_results.get('metadatas', [])),
                'metadata_analysis': {}
            }
            
            # Metadaten-Analyse
            if sample_results.get('metadatas'):
                metadata_analysis = {}
                
                for metadata in sample_results['metadatas']:
                    # Gutachten-Verteilung
                    gutachten_id = metadata.get('source_gutachten_id', 'unknown')
                    if gutachten_id not in metadata_analysis:
                        metadata_analysis[gutachten_id] = 0
                    metadata_analysis[gutachten_id] += 1
                
                stats['metadata_analysis']['gutachten_distribution'] = metadata_analysis
                
                # Level-Verteilung
                level_dist = {}
                section_dist = {}
                
                for metadata in sample_results['metadatas']:
                    level = metadata.get('level', 'unknown')
                    level_dist[f'level_{level}'] = level_dist.get(f'level_{level}', 0) + 1
                    
                    section = metadata.get('section_type', 'unknown')
                    section_dist[section] = section_dist.get(section, 0) + 1
                
                stats['metadata_analysis']['level_distribution'] = level_dist
                stats['metadata_analysis']['section_distribution'] = section_dist
            
            return stats
            
        except Exception as e:
            logger.error(f"Error getting collection stats: {e}")
            raise
    
    def delete_collection(self, collection_name: str) -> bool:
        """
        Löscht eine Collection
        
        Args:
            collection_name: Name der Collection
            
        Returns:
            True wenn erfolgreich gelöscht
        """
        try:
            self.client.delete_collection(collection_name)
            
            if collection_name in self.collections:
                del self.collections[collection_name]
            
            logger.info(f"Collection {collection_name} deleted successfully")
            return True
            
        except Exception as e:
            logger.error(f"Error deleting collection {collection_name}: {e}")
            return False
    
    def list_collections(self) -> List[str]:
        """
        Listet alle verfügbaren Collections auf
        
        Returns:
            Liste von Collection-Namen
        """
        try:
            collections = self.client.list_collections()
            collection_names = [c.name for c in collections]
            logger.info(f"Found {len(collection_names)} collections: {collection_names}")
            return collection_names
        except Exception as e:
            logger.error(f"Error listing collections: {e}")
            return []
    
    def backup_collection(self, collection_name: str, backup_path: Union[str, Path]) -> bool:
        """
        Erstellt ein Backup einer Collection
        
        Args:
            collection_name: Name der Collection
            backup_path: Pfad für das Backup
            
        Returns:
            True wenn Backup erfolgreich        """
        collection = self._get_collection(collection_name)
        
        try:
            
            # Alle Daten aus der Collection exportieren
            all_data = collection.get(include=['documents', 'metadatas', 'embeddings'])
            
            backup_data = {
                'collection_name': collection_name,
                'created_at': datetime.now().isoformat(),
                'total_items': len(all_data.get('documents', [])),
                'data': all_data
            }
            
            # Backup speichern
            backup_path = Path(backup_path)
            backup_path.parent.mkdir(parents=True, exist_ok=True)
            
            with open(backup_path, 'w', encoding='utf-8') as f:
                json.dump(backup_data, f, ensure_ascii=False, indent=2)
            
            logger.info(f"Collection {collection_name} backed up to {backup_path}")
            return True
            
        except Exception as e:
            logger.error(f"Error backing up collection {collection_name}: {e}")
            return False
    
    def close(self):
        """Schließt ChromaDB Client und räumt Ressourcen auf"""
        try:
            # Collections zurücksetzen
            self.collections.clear()
            
            # Client auf None setzen (ChromaDB Client hat keine explizite close-Methode)
            self.client = None
            
            logger.info("ChromaDB client closed successfully")
            
        except Exception as e:
            logger.error(f"Error closing ChromaDB client: {e}")
    
    def __enter__(self):
        """Context Manager Eingang"""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context Manager Ausgang"""
        self.close()

    async def get_chunk_by_id(self, chunk_id: str, collection_name: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """
        Async method to get a specific chunk by ID
        
        Args:
            chunk_id: ID of the chunk to retrieve
            collection_name: Name of the collection (optional)
            
        Returns:
            Chunk data or None if not found
        """
        try:
            collection_name = collection_name or self.config['collections']['gutachten_chunks']['name']
            collection = self.client.get_collection(collection_name)
            
            # Query for specific chunk ID
            results = collection.get(
                ids=[chunk_id],
                include=['documents', 'metadatas']
            )
            
            if results['documents'] and len(results['documents']) > 0:
                return {
                    'id': chunk_id,
                    'text': results['documents'][0],
                    'metadata': results['metadatas'][0] if results['metadatas'] else {}
                }
            
            return None
            
        except Exception as e:
            logger.error(f"Error getting chunk by ID {chunk_id}: {e}")
            return None
    
    async def get_legal_areas_distribution(self, collection_name: Optional[str] = None) -> Dict[str, int]:
        """
        Async method to get distribution of legal areas
        
        Args:
            collection_name: Name of the collection (optional)
            
        Returns:
            Dict mapping legal area to count
        """
        try:
            collection_name = collection_name or self.config['collections']['gutachten_chunks']['name']
            collection = self.client.get_collection(collection_name)
            
            # Get all metadatas to analyze legal areas
            results = collection.get(include=['metadatas'])
            
            legal_areas = {}
            for metadata in results['metadatas']:
                area = metadata.get('legal_area', 'Unknown')
                legal_areas[area] = legal_areas.get(area, 0) + 1
            
            return legal_areas
            
        except Exception as e:
            logger.error(f"Error getting legal areas distribution: {e}")
            return {}
    
    async def get_legal_norms_distribution(self, collection_name: Optional[str] = None) -> Dict[str, int]:
        """
        Async method to get distribution of legal norms
        
        Args:
            collection_name: Name of the collection (optional)
            
        Returns:
            Dict mapping legal norm to count
        """
        try:
            collection_name = collection_name or self.config['collections']['gutachten_chunks']['name']
            collection = self.client.get_collection(collection_name)
            
            # Get all metadatas to analyze legal norms
            results = collection.get(include=['metadatas'])
            
            legal_norms = {}
            for metadata in results['metadatas']:
                norms = metadata.get('legal_norms', [])
                if isinstance(norms, str):
                    try:
                        norms = json.loads(norms)
                    except:
                        norms = [norms] if norms else []
                
                for norm in norms:
                    legal_norms[norm] = legal_norms.get(norm, 0) + 1
            
            return legal_norms
            
        except Exception as e:
            logger.error(f"Error getting legal norms distribution: {e}")
            return {}
    
    async def get_all_gutachten_ids(self, collection_name: Optional[str] = None) -> List[str]:
        """
        Async method to get all gutachten IDs
        
        Args:
            collection_name: Name of the collection (optional)
            
        Returns:
            List of unique gutachten IDs
        """
        try:
            collection_name = collection_name or self.config['collections']['gutachten_chunks']['name']
            collection = self.client.get_collection(collection_name)
            
            # Get all metadatas to extract gutachten IDs
            results = collection.get(include=['metadatas'])
            
            gutachten_ids = set()
            for metadata in results['metadatas']:
                gutachten_id = metadata.get('source_gutachten_id')
                if gutachten_id:
                    gutachten_ids.add(gutachten_id)
            
            return list(gutachten_ids)
            
        except Exception as e:
            logger.error(f"Error getting all gutachten IDs: {e}")
            return []
    
    def reindex_collection(self, collection_name: str):
        """
        Reindexiert eine Collection (vereinfachte Implementierung)
        
        Args:
            collection_name: Name der Collection
        """
        try:
            # Für ChromaDB ist eine explizite Neuindizierung normalerweise nicht nötig
            # Diese Implementierung ist ein Platzhalter für potentielle Optimierungen
            collection = self.client.get_collection(collection_name)
            
            # Collection-Metadaten abrufen und validieren
            count = collection.count()
            logger.info(f"Collection {collection_name} reindexed - {count} items verified")
            
        except Exception as e:
            logger.error(f"Error reindexing collection {collection_name}: {e}")
            raise
    
    async def create_backup(self, backup_name: str) -> Path:
        """
        Erstellt ein Backup der Datenbank
        
        Args:
            backup_name: Name des Backups
            
        Returns:
            Pfad zum Backup
        """
        try:
            import shutil
            
            # Backup-Verzeichnis erstellen
            backup_dir = Path("./backups")
            backup_dir.mkdir(exist_ok=True)
            
            # Quell-Verzeichnis der Datenbank
            db_path = Path(self.config.get('chromadb', {}).get('persist_directory', './data/vectordb'))
            
            # Backup-Pfad
            backup_path = backup_dir / f"{backup_name}.backup"
            
            # Backup erstellen (kopiert das gesamte DB-Verzeichnis)
            if backup_path.exists():
                shutil.rmtree(backup_path)
            
            shutil.copytree(db_path, backup_path)
            
            logger.info(f"Backup created: {backup_path}")
            return backup_path
            
        except Exception as e:
            logger.error(f"Error creating backup: {e}")
            raise
    
    async def list_backups(self) -> List[Dict[str, Any]]:
        """
        Listet verfügbare Backups auf
        
        Returns:
            Liste von Backup-Informationen
        """
        try:
            backup_dir = Path("./backups")
            if not backup_dir.exists():
                return []
            
            backups = []
            for backup_path in backup_dir.glob("*.backup"):
                stat = backup_path.stat()
                backups.append({
                    "name": backup_path.stem,
                    "path": str(backup_path),
                    "created_at": datetime.fromtimestamp(stat.st_ctime).isoformat(),
                    "size_mb": stat.st_size / (1024 * 1024)
                })
            
            # Nach Erstellungsdatum sortieren (neueste zuerst)
            backups.sort(key=lambda x: x['created_at'], reverse=True)
            return backups
            
        except Exception as e:
            logger.error(f"Error listing backups: {e}")
            return []
    
    async def restore_backup(self, backup_name: str) -> bool:
        """
        Stellt ein Backup wieder her
        
        Args:
            backup_name: Name des Backups
            
        Returns:
            True wenn erfolgreich
        """
        try:
            import shutil
            
            backup_path = Path(f"./backups/{backup_name}.backup")
            if not backup_path.exists():
                raise FileNotFoundError(f"Backup {backup_name} nicht gefunden")
            
            # Aktuelle Datenbank sichern
            db_path = Path(self.config.get('chromadb', {}).get('persist_directory', './data/vectordb'))
            temp_backup = db_path.parent / f"{db_path.name}_temp_backup"
            
            if db_path.exists():
                shutil.move(db_path, temp_backup)
            
            try:
                # Backup wiederherstellen
                shutil.copytree(backup_path, db_path)
                
                # Client neu initialisieren
                self.close()
                self._init_client()
                
                # Temporäres Backup löschen
                if temp_backup.exists():
                    shutil.rmtree(temp_backup)
                
                logger.info(f"Backup {backup_name} successfully restored")
                return True
                
            except Exception as e:
                # Bei Fehler: Original wiederherstellen
                if temp_backup.exists():
                    if db_path.exists():
                        shutil.rmtree(db_path)
                    shutil.move(temp_backup, db_path)
                raise e
                
        except Exception as e:
            logger.error(f"Error restoring backup: {e}")
            return False
    
    async def get_performance_metrics(self) -> Dict[str, Any]:
        """
        Ruft Performance-Metriken ab
        
        Returns:
            Dict mit Performance-Daten
        """
        try:
            # Datenbank-Statistiken
            collections = self.list_collections()
            total_chunks = 0
            total_size = 0
            
            for collection_name in collections:
                stats = self.get_collection_stats(collection_name)
                total_chunks += stats.get('count', 0)
            
            # Speicher-Nutzung (optional, falls psutil verfügbar)
            memory_metrics = {}
            try:
                import psutil
                process = psutil.Process()
                memory_info = process.memory_info()
                memory_metrics = {
                    "memory_usage_mb": memory_info.rss / (1024 * 1024),
                    "memory_percent": process.memory_percent()
                }
            except ImportError:
                memory_metrics = {
                    "memory_usage_mb": "N/A (psutil not installed)",
                    "memory_percent": "N/A (psutil not installed)"
                }
            
            # Datenbank-Größe
            db_path = Path(self.config.get('chromadb', {}).get('persist_directory', './data/vectordb'))
            if db_path.exists():
                total_size = sum(f.stat().st_size for f in db_path.rglob('*') if f.is_file()) / (1024 * 1024)
            
            metrics = {
                "database_metrics": {
                    "total_collections": len(collections),
                    "total_chunks": total_chunks,
                    "database_size_mb": total_size
                },
                "memory_metrics": memory_metrics,
                "performance_metrics": {
                    "avg_chunks_per_collection": total_chunks / len(collections) if collections else 0,
                    "storage_efficiency": total_chunks / total_size if total_size > 0 else 0
                },
                "timestamp": datetime.now().isoformat()
            }
            
            return metrics
            
        except Exception as e:
            logger.error(f"Error getting performance metrics: {e}")
            return {}

    def add_documents(self, 
                     collection_name: str,
                     documents: List[str],
                     metadatas: List[Dict],
                     ids: List[str]) -> bool:
        """
        Fügt Dokumente direkt zur Collection hinzu (für Auto-Update Service)
        
        Args:
            collection_name: Name der Collection
            documents: Liste der Dokumente-Texte  
            metadatas: Liste der Metadaten
            ids: Liste der IDs
            
        Returns:
            True wenn erfolgreich
        """
        try:
            collection = self._get_collection(collection_name)
            
            # Dokumente zur Collection hinzufügen
            collection.add(
                ids=ids,
                documents=documents,
                metadatas=metadatas
            )
            
            logger.info(f"Successfully added {len(documents)} documents to collection {collection_name}")
            return True
            
        except Exception as e:
            logger.error(f"Error adding documents to collection {collection_name}: {e}")
            return False

if __name__ == "__main__":
    # Test des ChromaDB Clients
    from ..data.chunker import TextChunk, ChunkMetadata
    
    # Test-Client erstellen
    client = ChromaDBClient()
    
    # Test-Collection erstellen
    collection_name = "test_collection"
    collection = client.create_collection(collection_name, reset_if_exists=True)
    
    # Test-Chunks erstellen
    test_chunks = []
    for i in range(5):
        metadata = ChunkMetadata(
            chunk_id=f"test_chunk_{i}",
            source_gutachten_id="test_gutachten_1",
            level=2,
            section_type="rechtslage",
            token_count=100 + i * 20,
            legal_norms=["BGB § 280"],
            keywords=["Schadensersatz", "Haftung"]
        )
        
        chunk = TextChunk(
            text=f"Test chunk {i}: Dies ist ein Beispieltext für Rechtsgutachten mit § 280 BGB Bezug.",
            metadata=metadata
        )
        test_chunks.append(chunk)
    
    # Chunks hinzufügen
    stats = client.add_chunks_to_collection(collection_name, test_chunks)
    print(f"Added chunks - Success: {stats['successful_adds']}, Failed: {stats['failed_adds']}")
    
    # Suche testen
    search_results = client.search_similar_chunks(
        "Schadensersatz nach BGB", 
        collection_name, 
        n_results=3
    )
    
    print(f"Search results: {search_results['total_results']} found")
    for result in search_results['results']:
        print(f"- Similarity: {result['similarity_score']:.3f}, Text: {result['text'][:50]}...")
    
    # Statistiken abrufen
    collection_stats = client.get_collection_stats(collection_name)
    print(f"Collection stats: {collection_stats}")
    
    # Aufräumen
    client.close()
