"""
FastAPI Router für Search-Endpoints
Implementiert semantische Suche, Filterung und Ranking
"""

from fastapi import APIRouter, HTTPException, Depends, Query
from typing import List, Optional, Dict, Any
import logging
import time
from datetime import datetime

# Local imports
from .models import (
    SearchRequest, SearchResponse, SearchResult, 
    BulkSearchRequest, BulkSearchResponse,
    AutocompleteRequest, AutocompleteResponse,
    ErrorResponse
)
from .dependencies import get_search_engine, get_database_client
from ..search.semantic_search import SemanticSearchEngine
from ..vectordb.chroma_client import ChromaDBClient

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/search", tags=["search"])


@router.post("/semantic", response_model=SearchResponse)
async def semantic_search(
    request: SearchRequest,
    search_engine: SemanticSearchEngine = Depends(get_search_engine),
    db_client: ChromaDBClient = Depends(get_database_client)
):
    """
    Semantische Suche in der Gutachten-Datenbank
    
    Unterstützt verschiedene Suchtypen:
    - semantic: Reine Embedding-basierte Suche
    - hybrid: Kombination aus semantischer und Keyword-Suche
    - keyword: Traditionelle Keyword-Suche
    """
    start_time = time.time()
    
    try:
        # Query-Verarbeitung und Suche
        search_results = await search_engine.search(
            query=request.query,
            search_type=request.search_type.value,
            limit=request.limit,
            similarity_threshold=request.similarity_threshold,
            filters={
                'legal_areas': request.legal_areas,
                'legal_norms': request.legal_norms,
                'date_from': request.date_from,
                'date_to': request.date_to
            }
        )
        
        # Ergebnisse sortieren
        if request.sort_by.value == "similarity":
            search_results.results.sort(key=lambda x: x.similarity_score, reverse=True)
        elif request.sort_by.value == "date":
            search_results.results.sort(
                key=lambda x: x.gutachten_metadata.date_created or datetime.min, 
                reverse=True
            )
        # 'relevance' ist bereits Standard-Sortierung
        
        # Response-Modell anpassen
        response = SearchResponse(
            query=request.query,
            total_results=len(search_results.results),
            results=search_results.results,
            search_time_ms=(time.time() - start_time) * 1000,
            legal_areas_found=search_results.aggregations.get('legal_areas', {}),
            legal_norms_found=search_results.aggregations.get('legal_norms', {}),
            avg_similarity_score=search_results.avg_similarity_score,
            query_analysis=search_results.query_analysis
        )
        
        logger.info(f"Search completed: {len(search_results.results)} results in {response.search_time_ms:.2f}ms")
        return response
        
    except Exception as e:
        logger.error(f"Error in semantic search: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Fehler bei der Suche: {str(e)}"
        )


@router.post("/bulk", response_model=BulkSearchResponse)
async def bulk_search(
    request: BulkSearchRequest,
    search_engine: SemanticSearchEngine = Depends(get_search_engine)
):
    """
    Bulk-Suche für mehrere Queries gleichzeitig
    Optimiert für Batch-Verarbeitung und Evaluierung
    """
    start_time = time.time()
    
    try:
        results = {}
        successful_queries = 0
        failed_queries = []
        
        for query in request.queries:
            try:
                # Einzelne Suche für jede Query
                search_request = SearchRequest(
                    query=query,
                    search_type=request.search_type,
                    limit=request.limit_per_query,
                    similarity_threshold=request.similarity_threshold
                )
                
                search_results = await search_engine.search(
                    query=query,
                    search_type=request.search_type.value,
                    limit=request.limit_per_query,
                    similarity_threshold=request.similarity_threshold
                )
                
                results[query] = SearchResponse(
                    query=query,
                    total_results=len(search_results.results),
                    results=search_results.results,
                    search_time_ms=0,  # Wird am Ende berechnet
                    legal_areas_found=search_results.aggregations.get('legal_areas', {}),
                    legal_norms_found=search_results.aggregations.get('legal_norms', {}),
                    avg_similarity_score=search_results.avg_similarity_score,
                    query_analysis=search_results.query_analysis
                )
                
                successful_queries += 1
                
            except Exception as e:
                logger.error(f"Error processing query '{query}': {str(e)}")
                failed_queries.append(query)
        
        total_time_ms = (time.time() - start_time) * 1000
        
        response = BulkSearchResponse(
            queries=request.queries,
            results=results,
            total_processing_time_ms=total_time_ms,
            successful_queries=successful_queries,
            failed_queries=failed_queries
        )
        
        logger.info(f"Bulk search completed: {successful_queries}/{len(request.queries)} successful")
        return response
        
    except Exception as e:
        logger.error(f"Error in bulk search: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Fehler bei der Bulk-Suche: {str(e)}"
        )


@router.get("/autocomplete", response_model=AutocompleteResponse)
async def autocomplete(
    partial_query: str = Query(..., min_length=2, max_length=100),
    limit: int = Query(10, ge=1, le=50),
    include_legal_norms: bool = Query(True),
    search_engine: SemanticSearchEngine = Depends(get_search_engine)
):
    """
    Autocomplete-Funktion für Suchvorschläge
    Basiert auf häufigen Suchbegriffen und Rechtsnormen
    """
    try:
        suggestions = await search_engine.get_autocomplete_suggestions(
            partial_query=partial_query,
            limit=limit,
            include_legal_norms=include_legal_norms
        )
        
        response = AutocompleteResponse(
            partial_query=partial_query,
            suggestions=suggestions.get('general', []),
            legal_norm_suggestions=suggestions.get('legal_norms', [])
        )
        
        return response
        
    except Exception as e:
        logger.error(f"Error in autocomplete: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Fehler bei Autocomplete: {str(e)}"
        )


@router.get("/similar/{chunk_id}", response_model=SearchResponse)
async def find_similar_chunks(
    chunk_id: str,
    limit: int = Query(10, ge=1, le=50),
    similarity_threshold: float = Query(0.7, ge=0.0, le=1.0),
    search_engine: SemanticSearchEngine = Depends(get_search_engine),
    db_client: ChromaDBClient = Depends(get_database_client)
):
    """
    Findet ähnliche Chunks zu einem gegebenen Chunk
    Nützlich für "Ähnliche Dokumente" Funktionalität
    """
    start_time = time.time()
    
    try:
        # Chunk-Inhalt abrufen
        chunk_data = await db_client.get_chunk_by_id(chunk_id)
        if not chunk_data:
            raise HTTPException(
                status_code=404,
                detail=f"Chunk mit ID {chunk_id} nicht gefunden"
            )
        
        # Ähnliche Chunks suchen
        search_results = await search_engine.find_similar_to_chunk(
            chunk_id=chunk_id,
            limit=limit,
            similarity_threshold=similarity_threshold
        )
        
        response = SearchResponse(
            query=f"Ähnlich zu Chunk {chunk_id}",
            total_results=len(search_results.results),
            results=search_results.results,
            search_time_ms=(time.time() - start_time) * 1000,
            legal_areas_found=search_results.aggregations.get('legal_areas', {}),
            legal_norms_found=search_results.aggregations.get('legal_norms', {}),
            avg_similarity_score=search_results.avg_similarity_score,
            query_analysis={}
        )
        
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error finding similar chunks: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Fehler bei der Suche nach ähnlichen Chunks: {str(e)}"
        )


@router.get("/filters/legal-areas")
async def get_available_legal_areas(
    db_client: ChromaDBClient = Depends(get_database_client)
) -> Dict[str, int]:
    """
    Gibt verfügbare Rechtsgebiete mit Anzahl Gutachten zurück
    """
    try:
        legal_areas = await db_client.get_legal_areas_distribution()
        return legal_areas
    except Exception as e:
        logger.error(f"Error getting legal areas: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Fehler beim Abrufen der Rechtsgebiete: {str(e)}"
        )


@router.get("/filters/legal-norms")
async def get_available_legal_norms(
    db_client: ChromaDBClient = Depends(get_database_client)
) -> Dict[str, int]:
    """
    Gibt verfügbare Rechtsnormen mit Häufigkeit zurück
    """
    try:
        legal_norms = await db_client.get_legal_norms_distribution()
        return legal_norms
    except Exception as e:
        logger.error(f"Error getting legal norms: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Fehler beim Abrufen der Rechtsnormen: {str(e)}"
        )


@router.get("/trends/popular-queries")
async def get_popular_queries(
    limit: int = Query(20, ge=1, le=100),
    search_engine: SemanticSearchEngine = Depends(get_search_engine)
) -> List[Dict[str, Any]]:
    """
    Gibt die beliebtesten Suchanfragen zurück
    """
    try:
        popular_queries = await search_engine.get_popular_queries(limit=limit)
        return popular_queries
    except Exception as e:
        logger.error(f"Error getting popular queries: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Fehler beim Abrufen beliebter Suchanfragen: {str(e)}"
        )


@router.get("/export/results/{search_id}")
async def export_search_results(
    search_id: str,
    format: str = Query("json", regex="^(json|csv|xlsx)$"),
    search_engine: SemanticSearchEngine = Depends(get_search_engine)
):
    """
    Exportiert Suchergebnisse in verschiedenen Formaten
    """
    try:
        exported_data = await search_engine.export_search_results(
            search_id=search_id,
            format=format
        )
        
        if format == "json":
            return exported_data
        else:
            # Für CSV/XLSX: File-Response zurückgeben
            from fastapi.responses import FileResponse
            return FileResponse(
                path=exported_data['file_path'],
                media_type=exported_data['media_type'],
                filename=exported_data['filename']
            )
            
    except Exception as e:
        logger.error(f"Error exporting search results: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Fehler beim Export der Suchergebnisse: {str(e)}"
        )
