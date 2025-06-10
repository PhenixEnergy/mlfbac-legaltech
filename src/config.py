"""
Konfigurationsmodul für LegalTech Application
Lädt Umgebungsvariablen aus .env Datei und stellt sie zur Verfügung
"""
import os
from pathlib import Path
from typing import Optional
from dotenv import load_dotenv

# Load .env file
env_path = Path(__file__).parent.parent / '.env'
if env_path.exists():
    load_dotenv(env_path)
    print(f"✅ Environment variables loaded from {env_path}")
else:
    print(f"⚠️  No .env file found at {env_path}")

class Config:
    """Zentrale Konfigurationsklasse"""
    
    # Database Configuration
    CHROMA_DB_PATH = os.getenv('CHROMA_DB_PATH', './data/vectordb')
    CHROMA_COLLECTION_NAME = os.getenv('CHROMA_COLLECTION_NAME', 'legal_documents_v2')
    CHROMA_BATCH_SIZE = int(os.getenv('CHROMA_BATCH_SIZE', '1000'))
    CHROMA_PERSIST_DIRECTORY = os.getenv('CHROMA_PERSIST_DIRECTORY', './data/vectordb')
    CHROMA_ANONYMIZED_TELEMETRY = os.getenv('CHROMA_ANONYMIZED_TELEMETRY', 'false').lower() == 'true'
    CHROMA_ALLOW_RESET = os.getenv('CHROMA_ALLOW_RESET', 'true').lower() == 'true'
    
    # LM Studio Configuration
    LM_STUDIO_BASE_URL = os.getenv('LM_STUDIO_BASE_URL', 'http://localhost:1234/v1')
    LM_STUDIO_API_KEY = os.getenv('LM_STUDIO_API_KEY', 'lm-studio')
    LM_STUDIO_MODEL = os.getenv('LM_STUDIO_MODEL', 'deepseek-coder-v2-lite-16b-q8')
    LM_STUDIO_MAX_TOKENS = int(os.getenv('LM_STUDIO_MAX_TOKENS', '2000'))
    LM_STUDIO_TEMPERATURE = float(os.getenv('LM_STUDIO_TEMPERATURE', '0.1'))
    
    # Embedding Model Configuration
    EMBEDDING_MODEL = os.getenv('EMBEDDING_MODEL', 'ibm-granite/granite-embedding-278m-multilingual')
    EMBEDDING_BATCH_SIZE = int(os.getenv('EMBEDDING_BATCH_SIZE', '32'))
    EMBEDDING_DEVICE = os.getenv('EMBEDDING_DEVICE', 'auto')
    
    # Search Configuration
    SEARCH_TOP_K_DEFAULT = int(os.getenv('SEARCH_TOP_K_DEFAULT', '10'))
    SEARCH_SIMILARITY_THRESHOLD = float(os.getenv('SEARCH_SIMILARITY_THRESHOLD', '0.7'))
    SEARCH_RERANK_ENABLED = os.getenv('SEARCH_RERANK_ENABLED', 'true').lower() == 'true'
    
    # Application Configuration
    APP_LOG_LEVEL = os.getenv('APP_LOG_LEVEL', 'INFO')
    APP_DEBUG_MODE = os.getenv('APP_DEBUG_MODE', 'false').lower() == 'true'
    
    # API Server Configuration
    API_HOST = os.getenv('API_HOST', '0.0.0.0')
    API_PORT = int(os.getenv('API_PORT', '8000'))
    API_RELOAD = os.getenv('API_RELOAD', 'true').lower() == 'true'
    
    # Streamlit Configuration
    STREAMLIT_HOST = os.getenv('STREAMLIT_HOST', 'localhost')
    STREAMLIT_PORT = int(os.getenv('STREAMLIT_PORT', '8501'))
    
    # Database URLs
    DATABASE_URL = os.getenv('DATABASE_URL', 'sqlite:///./data/app.db')
    POSTGRES_URL = os.getenv('POSTGRES_URL', 'postgresql://localhost:5432/legaltech')
    
    # Security Settings
    SECRET_KEY = os.getenv('SECRET_KEY', 'your-secret-key-here')
    ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv('ACCESS_TOKEN_EXPIRE_MINUTES', '30'))
    
    # Logging Configuration
    LOG_FILE = os.getenv('LOG_FILE', './logs/app.log')
    LOG_MAX_SIZE = os.getenv('LOG_MAX_SIZE', '10MB')
    LOG_BACKUP_COUNT = int(os.getenv('LOG_BACKUP_COUNT', '5'))
    
    # Development Settings
    DEVELOPMENT = os.getenv('DEVELOPMENT', 'true').lower() == 'true'
    DEBUG = os.getenv('DEBUG', 'true').lower() == 'true'
    TESTING = os.getenv('TESTING', 'false').lower() == 'true'
    
    # External APIs
    HUGGINGFACE_API_KEY = os.getenv('HUGGINGFACE_API_KEY', 'your-hf-api-key-here')
    OPENAI_API_KEY = os.getenv('OPENAI_API_KEY', 'your-openai-api-key-here')
    
    # Data Processing
    MAX_CHUNK_SIZE = int(os.getenv('MAX_CHUNK_SIZE', '1000'))
    CHUNK_OVERLAP = int(os.getenv('CHUNK_OVERLAP', '200'))
    MIN_CHUNK_SIZE = int(os.getenv('MIN_CHUNK_SIZE', '100'))
    
    # Performance Settings
    MAX_WORKERS = int(os.getenv('MAX_WORKERS', '4'))
    BATCH_PROCESSING_SIZE = int(os.getenv('BATCH_PROCESSING_SIZE', '50'))
    CACHE_TTL = int(os.getenv('CACHE_TTL', '3600'))
    
    @classmethod
    def validate_config(cls) -> bool:
        """Validiert kritische Konfigurationsparameter"""
        critical_paths = [
            cls.CHROMA_DB_PATH,
            cls.CHROMA_PERSIST_DIRECTORY
        ]
        
        for path in critical_paths:
            if not Path(path).exists():
                try:
                    Path(path).mkdir(parents=True, exist_ok=True)
                    print(f"✅ Created directory: {path}")
                except Exception as e:
                    print(f"❌ Could not create directory {path}: {e}")
                    return False
        
        return True
    
    @classmethod
    def get_env_info(cls) -> dict:
        """Gibt Übersicht über geladene Konfiguration zurück"""
        return {
            'database': {
                'chroma_path': cls.CHROMA_DB_PATH,
                'collection': cls.CHROMA_COLLECTION_NAME,
                'batch_size': cls.CHROMA_BATCH_SIZE
            },
            'llm': {
                'base_url': cls.LM_STUDIO_BASE_URL,
                'model': cls.LM_STUDIO_MODEL,
                'max_tokens': cls.LM_STUDIO_MAX_TOKENS
            },
            'embedding': {
                'model': cls.EMBEDDING_MODEL,
                'batch_size': cls.EMBEDDING_BATCH_SIZE,
                'device': cls.EMBEDDING_DEVICE
            },
            'api': {
                'host': cls.API_HOST,
                'port': cls.API_PORT,
                'debug': cls.APP_DEBUG_MODE
            }
        }

# Globale Konfigurationsinstanz
config = Config()

# Validiere Konfiguration beim Import
if not config.validate_config():
    print("⚠️  Configuration validation failed!")

# Export für einfache Imports
__all__ = ['Config', 'config']
