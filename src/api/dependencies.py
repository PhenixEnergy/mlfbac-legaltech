"""
Dependency Injection für FastAPI
Stellt Singleton-Instanzen der Core-Services bereit
"""

from functools import lru_cache
from typing import Optional
import logging
from pathlib import Path

# Local imports
try:
    from ..search.semantic_search import SemanticSearchEngine
    from ..vectordb.chroma_client import ChromaDBClient
    from ..llm.lm_studio_client import LegalQASystem
    from ..data.loader import DNOTIDataLoader
    from ..data.preprocessor import LegalTextPreprocessor, PreprocessingConfig
    from ..data.chunker import HierarchicalChunker
except ImportError:
    # Fallback für absolute Imports
    from src.search.semantic_search import SemanticSearchEngine
    from src.vectordb.chroma_client import ChromaDBClient
    from src.llm.lm_studio_client import LegalQASystem
    from src.data.loader import DNOTIDataLoader
    from src.data.preprocessor import LegalTextPreprocessor, PreprocessingConfig
    from src.data.chunker import HierarchicalChunker

logger = logging.getLogger(__name__)

# Globale Konfigurationspfade
CONFIG_DIR = Path(__file__).parent.parent.parent / "config"
DB_CONFIG_PATH = CONFIG_DIR / "database.yaml"
CHUNKING_CONFIG_PATH = CONFIG_DIR / "chunking.yaml"
MODELS_CONFIG_PATH = CONFIG_DIR / "models.yaml"


@lru_cache()
def get_database_client() -> ChromaDBClient:
    """
    Singleton ChromaDB Client
    """
    try:
        client = ChromaDBClient(config_path=DB_CONFIG_PATH)
        logger.info("ChromaDB client initialized")
        return client
    except Exception as e:
        logger.error(f"Error initializing ChromaDB client: {e}")
        raise


@lru_cache()
def get_search_engine() -> SemanticSearchEngine:
    """
    Singleton Semantic Search Engine
    """
    try:
        db_client = get_database_client()
        chunker = get_chunker()
        search_engine = SemanticSearchEngine(
            vectordb_client=db_client,
            chunker=chunker
        )
        logger.info("Semantic search engine initialized")
        return search_engine
    except Exception as e:
        logger.error(f"Error initializing search engine: {e}")
        raise


@lru_cache()
def get_qa_system() -> LegalQASystem:
    """
    Singleton Legal QA System
    """
    try:
        search_engine = get_search_engine()
        qa_system = LegalQASystem(
            search_engine=search_engine,
            config_path=MODELS_CONFIG_PATH
        )
        logger.info("Legal QA system initialized")
        return qa_system
    except Exception as e:
        logger.error(f"Error initializing QA system: {e}")
        raise


@lru_cache()
def get_data_loader() -> DNOTIDataLoader:
    """
    Singleton Data Loader
    """
    try:
        loader = DNOTIDataLoader()
        logger.info("Data loader initialized")
        return loader
    except Exception as e:
        logger.error(f"Error initializing data loader: {e}")
        raise


@lru_cache()
def get_text_preprocessor() -> LegalTextPreprocessor:
    """
    Singleton Text Preprocessor
    """
    try:
        config = PreprocessingConfig(
            remove_extra_whitespace=True,
            normalize_unicode=True,
            preserve_legal_formatting=True,
            extract_legal_norms=True
        )
        preprocessor = LegalTextPreprocessor(config)
        logger.info("Text preprocessor initialized")
        return preprocessor
    except Exception as e:
        logger.error(f"Error initializing text preprocessor: {e}")
        raise


@lru_cache()
def get_chunker() -> HierarchicalChunker:
    """
    Singleton Hierarchical Chunker
    """
    try:
        chunker = HierarchicalChunker(config_path=CHUNKING_CONFIG_PATH)
        logger.info("Hierarchical chunker initialized")
        return chunker
    except Exception as e:
        logger.error(f"Error initializing chunker: {e}")
        raise


def get_health_check_dependencies() -> dict:
    """
    Überprüft den Status aller Abhängigkeiten
    """
    status = {
        'database': 'unknown',
        'search_engine': 'unknown',
        'qa_system': 'unknown',
        'llm': 'unknown'
    }
    
    try:
        # Database-Status
        db_client = get_database_client()
        collections = db_client.list_collections()
        status['database'] = 'healthy' if collections else 'no_collections'
    except Exception as e:
        logger.error(f"Database health check failed: {e}")
        status['database'] = 'error'
    
    try:
        # Search Engine-Status
        search_engine = get_search_engine()
        status['search_engine'] = 'healthy'
    except Exception as e:
        logger.error(f"Search engine health check failed: {e}")
        status['search_engine'] = 'error'
    
    try:
        # QA System-Status
        qa_system = get_qa_system()
        # Test LLM-Verbindung
        llm_status = qa_system.llm_client.health_check()
        status['qa_system'] = 'healthy'
        status['llm'] = 'healthy' if llm_status else 'error'
    except Exception as e:
        logger.error(f"QA system health check failed: {e}")
        status['qa_system'] = 'error'
        status['llm'] = 'error'
    
    return status


def cleanup_dependencies():
    """
    Bereinigt alle Abhängigkeiten beim Shutdown
    """
    try:
        # Cache leeren
        get_database_client.cache_clear()
        get_search_engine.cache_clear()
        get_qa_system.cache_clear()
        get_data_loader.cache_clear()
        get_text_preprocessor.cache_clear()
        get_chunker.cache_clear()
        
        logger.info("Dependencies cleaned up successfully")
    except Exception as e:
        logger.error(f"Error during cleanup: {e}")


# Globale Instanzen für direkten Zugriff
_database_client: Optional[ChromaDBClient] = None
_search_engine: Optional[SemanticSearchEngine] = None
_qa_system: Optional[LegalQASystem] = None


def initialize_global_dependencies():
    """
    Initialisiert alle globalen Abhängigkeiten beim Startup
    """
    global _database_client, _search_engine, _qa_system
    
    try:
        logger.info("Initializing global dependencies...")
        
        # Abhängigkeiten in der richtigen Reihenfolge initialisieren
        _database_client = get_database_client()
        _search_engine = get_search_engine()
        _qa_system = get_qa_system()
        
        logger.info("Global dependencies initialized successfully")
        
    except Exception as e:
        logger.error(f"Error initializing global dependencies: {e}")
        raise


def get_global_database_client() -> ChromaDBClient:
    """Gibt die globale Database Client Instanz zurück"""
    if _database_client is None:
        raise RuntimeError("Database client not initialized")
    return _database_client


def get_global_search_engine() -> SemanticSearchEngine:
    """Gibt die globale Search Engine Instanz zurück"""
    if _search_engine is None:
        raise RuntimeError("Search engine not initialized")
    return _search_engine


def get_global_qa_system() -> LegalQASystem:
    """Gibt die globale QA System Instanz zurück"""
    if _qa_system is None:
        raise RuntimeError("QA system not initialized")
    return _qa_system
