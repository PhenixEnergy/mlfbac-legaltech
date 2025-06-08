"""
FastAPI Router für Admin-Endpoints
Verwaltung der Datenbank, Monitoring und Wartung
"""

from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks
from typing import Dict, List, Any, Optional
import logging
import psutil
import time
from datetime import datetime, timedelta
from pathlib import Path

# Local imports
from .models import DatabaseStats, HealthCheck, ErrorResponse
from .dependencies import (
    get_database_client, get_search_engine, get_qa_system,
    get_health_check_dependencies, cleanup_dependencies
)
from ..vectordb.chroma_client import ChromaDBClient
from ..search.semantic_search import SemanticSearchEngine
from ..llm.lm_studio_client import LegalQASystem

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/admin", tags=["administration"])

# Globale Statistiken für Uptime-Tracking
_startup_time = datetime.now()


@router.get("/health", response_model=HealthCheck)
async def health_check():
    """
    Umfassender Gesundheitscheck der API und aller Services
    """
    try:
        # Dependency-Status überprüfen
        deps_status = get_health_check_dependencies()
        
        # Memory-Usage ermitteln
        memory_usage = psutil.virtual_memory().used / (1024 * 1024)  # MB
        
        # Uptime berechnen
        uptime = (datetime.now() - _startup_time).total_seconds()
        
        # Gesamt-Status bestimmen
        overall_status = "healthy"
        if any(status == "error" for status in deps_status.values()):
            overall_status = "degraded"
        
        health = HealthCheck(
            status=overall_status,
            timestamp=datetime.now(),
            database_status=deps_status.get('database', 'unknown'),
            llm_status=deps_status.get('llm', 'unknown'),
            embedding_status=deps_status.get('search_engine', 'unknown'),
            uptime_seconds=uptime,
            memory_usage_mb=memory_usage
        )
        
        return health
        
    except Exception as e:
        logger.error(f"Error in health check: {str(e)}")
        return HealthCheck(
            status="error",
            database_status="error",
            llm_status="error",
            embedding_status="error",
            uptime_seconds=0,
            memory_usage_mb=0
        )


@router.get("/stats", response_model=DatabaseStats)
async def get_database_statistics(
    db_client: ChromaDBClient = Depends(get_database_client)
):
    """
    Detaillierte Datenbank-Statistiken
    """
    try:
        # Collection-Statistiken abrufen
        collections = db_client.list_collections()
        collection_stats = {}
        total_chunks = 0
        
        for collection_name in collections:
            stats = db_client.get_collection_stats(collection_name)
            collection_stats[collection_name] = stats
            total_chunks += stats.get('count', 0)
        
        # Rechtsgebiete-Verteilung
        legal_areas = await db_client.get_legal_areas_distribution()
        
        # Datenbank-Größe schätzen
        db_path = Path(db_client.config.get('chromadb', {}).get('persist_directory', './data/vectordb'))
        db_size_mb = 0
        if db_path.exists():
            db_size_mb = sum(f.stat().st_size for f in db_path.rglob('*') if f.is_file()) / (1024 * 1024)
        
        # Durchschnittliche Tokens pro Chunk
        avg_tokens = 0
        if total_chunks > 0:
            total_tokens = sum(stats.get('total_tokens', 0) for stats in collection_stats.values())
            avg_tokens = total_tokens / total_chunks
        
        database_stats = DatabaseStats(
            total_gutachten=len(await db_client.get_all_gutachten_ids()),
            total_chunks=total_chunks,
            avg_tokens_per_chunk=avg_tokens,
            legal_areas_distribution=legal_areas,
            database_size_mb=db_size_mb,
            last_updated=datetime.now(),
            collection_names=collections
        )
        
        return database_stats
        
    except Exception as e:
        logger.error(f"Error getting database stats: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Fehler beim Abrufen der Datenbank-Statistiken: {str(e)}"
        )


@router.post("/reindex")
async def reindex_database(
    background_tasks: BackgroundTasks,
    collection_name: Optional[str] = None,
    db_client: ChromaDBClient = Depends(get_database_client)
):
    """
    Startet Neuindizierung der Datenbank im Hintergrund
    """
    try:
        def reindex_task():
            """Hintergrund-Task für Neuindizierung"""
            try:
                if collection_name:
                    # Spezifische Collection neuindizieren
                    db_client.reindex_collection(collection_name)
                    logger.info(f"Reindexing completed for collection: {collection_name}")
                else:
                    # Alle Collections neuindizieren
                    collections = db_client.list_collections()
                    for coll_name in collections:
                        db_client.reindex_collection(coll_name)
                    logger.info(f"Reindexing completed for all collections")
                    
            except Exception as e:
                logger.error(f"Error during reindexing: {e}")
        
        background_tasks.add_task(reindex_task)
        
        return {
            "message": "Neuindizierung gestartet",
            "collection": collection_name or "alle Collections",
            "status": "running"
        }
        
    except Exception as e:
        logger.error(f"Error starting reindex: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Fehler beim Starten der Neuindizierung: {str(e)}"
        )


@router.post("/backup")
async def create_database_backup(
    backup_name: Optional[str] = None,
    db_client: ChromaDBClient = Depends(get_database_client)
):
    """
    Erstellt ein Backup der Datenbank
    """
    try:
        if not backup_name:
            backup_name = f"backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        backup_path = await db_client.create_backup(backup_name)
        
        return {
            "message": "Backup erfolgreich erstellt",
            "backup_name": backup_name,
            "backup_path": str(backup_path),
            "created_at": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error creating backup: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Fehler beim Erstellen des Backups: {str(e)}"
        )


@router.get("/backups")
async def list_database_backups(
    db_client: ChromaDBClient = Depends(get_database_client)
) -> List[Dict[str, Any]]:
    """
    Listet verfügbare Datenbank-Backups auf
    """
    try:
        backups = await db_client.list_backups()
        return backups
    except Exception as e:
        logger.error(f"Error listing backups: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Fehler beim Auflisten der Backups: {str(e)}"
        )


@router.post("/restore/{backup_name}")
async def restore_database_backup(
    backup_name: str,
    confirm: bool = False,
    db_client: ChromaDBClient = Depends(get_database_client)
):
    """
    Stellt Datenbank aus Backup wieder her
    ACHTUNG: Überschreibt aktuelle Datenbank!
    """
    if not confirm:
        raise HTTPException(
            status_code=400,
            detail="Backup-Wiederherstellung muss mit confirm=true bestätigt werden"
        )
    
    try:
        await db_client.restore_backup(backup_name)
        
        return {
            "message": "Backup erfolgreich wiederhergestellt",
            "backup_name": backup_name,
            "restored_at": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error restoring backup: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Fehler beim Wiederherstellen des Backups: {str(e)}"
        )


@router.get("/performance")
async def get_performance_metrics(
    search_engine: SemanticSearchEngine = Depends(get_search_engine)
) -> Dict[str, Any]:
    """
    Performance-Metriken der letzten 24 Stunden
    """
    try:
        metrics = await search_engine.get_performance_metrics(
            time_window=timedelta(hours=24)
        )
        
        return {
            "time_window": "24 hours",
            "total_searches": metrics.get('total_searches', 0),
            "avg_search_time_ms": metrics.get('avg_search_time_ms', 0),
            "avg_results_per_search": metrics.get('avg_results_per_search', 0),
            "popular_queries": metrics.get('popular_queries', []),
            "error_rate": metrics.get('error_rate', 0),
            "cache_hit_rate": metrics.get('cache_hit_rate', 0)
        }
        
    except Exception as e:
        logger.error(f"Error getting performance metrics: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Fehler beim Abrufen der Performance-Metriken: {str(e)}"
        )


@router.post("/cache/clear")
async def clear_cache(
    cache_type: str = "all",  # all, search, embeddings, qa
    search_engine: SemanticSearchEngine = Depends(get_search_engine),
    qa_system: LegalQASystem = Depends(get_qa_system)
):
    """
    Leert verschiedene Cache-Typen
    """
    try:
        cleared_caches = []
        
        if cache_type in ["all", "search"]:
            await search_engine.clear_cache()
            cleared_caches.append("search")
        
        if cache_type in ["all", "embeddings"]:
            await search_engine.clear_embedding_cache()
            cleared_caches.append("embeddings")
        
        if cache_type in ["all", "qa"]:
            await qa_system.clear_cache()
            cleared_caches.append("qa")
        
        return {
            "message": "Cache geleert",
            "cleared_caches": cleared_caches,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error clearing cache: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Fehler beim Leeren des Cache: {str(e)}"
        )


@router.get("/logs")
async def get_system_logs(
    level: str = "INFO",
    limit: int = 100,
    search_term: Optional[str] = None
) -> List[Dict[str, Any]]:
    """
    Gibt System-Logs zurück
    """
    try:
        # Hier würde normalerweise ein Log-Aggregator wie ELK Stack verwendet
        # Für Entwicklung: Einfache Log-Datei-Auswertung
        
        logs = []
        log_file = Path("logs/legaltech.log")
        
        if log_file.exists():
            with open(log_file, 'r', encoding='utf-8') as f:
                lines = f.readlines()
                
            # Einfache Log-Parsing (sollte in Produktion robuster sein)
            for line in lines[-limit:]:
                if level.upper() in line:
                    if not search_term or search_term.lower() in line.lower():
                        logs.append({
                            "timestamp": datetime.now().isoformat(),  # Vereinfacht
                            "level": level,
                            "message": line.strip()
                        })
        
        return logs
        
    except Exception as e:
        logger.error(f"Error getting logs: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Fehler beim Abrufen der Logs: {str(e)}"
        )


@router.post("/shutdown")
async def graceful_shutdown():
    """
    Initiiert einen ordnungsgemäßen Shutdown der API
    """
    try:
        # Cleanup durchführen
        cleanup_dependencies()
        
        logger.info("Graceful shutdown initiated")
        
        return {
            "message": "Shutdown eingeleitet",
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error during shutdown: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Fehler beim Shutdown: {str(e)}"
        )
