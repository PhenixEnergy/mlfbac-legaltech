"""
FastAPI Hauptanwendung
Legal Tech - KI-gestützte semantische Suche für dnoti Rechtsgutachten
"""

import logging
import sys
from pathlib import Path
from contextlib import asynccontextmanager
from datetime import datetime

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException

# Konfiguration importieren
try:
    from ..config import config
except ImportError:
    from src.config import config

# Local imports
try:
    from .search_router import router as search_router
    from .qa_router import router as qa_router
    from .admin_router import router as admin_router
    from .dependencies import initialize_global_dependencies, cleanup_dependencies
    from .models import ErrorResponse
except ImportError:
    # Fallback für absolute Imports
    from src.api.search_router import router as search_router
    from src.api.qa_router import router as qa_router
    from src.api.admin_router import router as admin_router
    from src.api.dependencies import initialize_global_dependencies, cleanup_dependencies
    from src.api.models import ErrorResponse

# Logging konfigurieren
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/legaltech.log', encoding='utf-8'),
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Startup und Shutdown Events für die Anwendung
    """
    # Startup
    logger.info("=== Legal Tech API Starting ===")
    try:
        # Logs-Verzeichnis erstellen
        Path("logs").mkdir(exist_ok=True)
        
        # Globale Abhängigkeiten initialisieren
        initialize_global_dependencies()
        
        logger.info("=== Legal Tech API Started Successfully ===")
        yield
        
    except Exception as e:
        logger.error(f"Error during startup: {e}")
        raise
    
    # Shutdown
    logger.info("=== Legal Tech API Shutting Down ===")
    try:
        cleanup_dependencies()
        logger.info("=== Legal Tech API Shutdown Complete ===")
    except Exception as e:
        logger.error(f"Error during shutdown: {e}")


# FastAPI-Anwendung erstellen
app = FastAPI(
    title="DNOTI Legal Tech API",
    description="""
    KI-gestützte semantische Suche für dnoti Rechtsgutachten
    
    ## Features
    
    * **Semantische Suche**: Embedding-basierte Suche mit Granite 278M
    * **Hybrid Search**: Kombination aus semantischer und Keyword-Suche
    * **RAG-basierte QA**: Frage-Antwort mit Deepseek V2 Lite 16B
    * **Intelligentes Chunking**: 3-Level hierarchisches Chunking-System
    * **Performance**: <500ms Suchzeit, ChromaDB Vektordatenbank
    
    ## Datenbasis
    
    35.426 dnoti Rechtsgutachten, automatisch verarbeitet und chunked.
    """,
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc"
)

# Middleware hinzufügen
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:8501"],  # React, Streamlit
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_middleware(GZipMiddleware, minimum_size=1000)


# Exception Handlers
@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(request: Request, exc: StarletteHTTPException):
    """
    Handler für HTTP-Exceptions
    """
    return JSONResponse(
        status_code=exc.status_code,
        content=ErrorResponse(
            error=exc.detail,
            error_code=f"HTTP_{exc.status_code}",
            timestamp=datetime.now().isoformat()
        ).dict()
    )


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """
    Handler für Validierungs-Exceptions
    """
    return JSONResponse(
        status_code=422,
        content=ErrorResponse(
            error=f"Validierungsfehler: {str(exc)}",
            error_code="VALIDATION_ERROR",
            timestamp=datetime.now().isoformat()
        ).dict()
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """
    Handler für allgemeine Exceptions
    """
    logger.error(f"Unhandled exception: {str(exc)}", exc_info=True)
    
    return JSONResponse(
        status_code=500,
        content=ErrorResponse(
            error="Interner Serverfehler",
            error_code="INTERNAL_ERROR",
            timestamp=datetime.now().isoformat()
        ).dict()
    )


# Request Logging Middleware
@app.middleware("http")
async def log_requests(request: Request, call_next):
    """
    Middleware für Request-Logging
    """
    start_time = datetime.now()
    
    # Request verarbeiten
    response = await call_next(request)
    
    # Log-Informationen
    process_time = (datetime.now() - start_time).total_seconds()
    log_data = {
        "method": request.method,
        "url": str(request.url),
        "status_code": response.status_code,
        "process_time": f"{process_time:.3f}s"
    }
    
    logger.info(f"Request: {log_data}")
    
    # Response-Header für Debugging
    response.headers["X-Process-Time"] = str(process_time)
    
    return response


# Router einbinden
app.include_router(search_router)
app.include_router(qa_router)
app.include_router(admin_router)


# Health Check Endpoints
@app.get("/health", response_model=dict, tags=["Health"])
async def health_check():
    """
    Health Check Endpoint für Load Balancer und Monitoring
    """
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "service": "Legal Tech API",
        "version": "1.0.0"
    }


# Root-Endpoint
@app.get("/", response_model=dict)
async def root():
    """
    Root Endpoint mit API-Informationen
    """
    return {
        "message": "DNOTI Legal Tech API",
        "version": "1.0.0",
        "docs": "/docs",
        "health": "/health",
        "status": "running"
    }


# API-Info Endpoint
@app.get("/info")
async def api_info():
    """
    Detaillierte API-Informationen
    """
    return {
        "api": {
            "name": "DNOTI Legal Tech API",
            "version": "1.0.0",
            "description": "KI-gestützte semantische Suche für Rechtsgutachten",
            "python_version": sys.version,
            "fastapi_version": "0.104.1"
        },
        "features": {
            "semantic_search": "Embedding-basierte Suche mit Similarity-Ranking",
            "hybrid_search": "Kombination Semantic + Keyword Search",
            "rag_qa": "Retrieval-Augmented Generation für Frage-Antwort",
            "intelligent_chunking": "3-Level hierarchisches Chunking",
            "legal_preprocessing": "Rechtsspezifische Text-Verarbeitung"
        },
        "models": {
            "embedding": {
                "name": "IBM Granite Embedding 278M Multilingual",
                "size": "803MB",
                "dimensions": 768,
                "languages": ["German", "English", "French", "Spanish"]
            },
            "generation": {
                "name": "Deepseek V2 Lite 16B",
                "quantization": "Q8",
                "context_length": 32768,
                "api": "LM Studio localhost:1234"
            }
        },
        "database": {
            "type": "ChromaDB",
            "persistence": "Local file-based",
            "collections": ["dnoti_gutachten_chunks"],
            "total_documents": 35426,
            "estimated_chunks": "~2.7M"
        }
    }


if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "src.api.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        reload_dirs=["src"],
        log_level="info"
    )
