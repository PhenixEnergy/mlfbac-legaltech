"""
Pydantic Models für FastAPI Backend
Definiert Request/Response-Modelle für die Legal Search API
"""

from typing import Dict, List, Optional, Union, Any
from pydantic import BaseModel, Field, validator
from datetime import datetime
from enum import Enum


class SearchType(str, Enum):
    """Suchtypen für die semantische Suche"""
    SEMANTIC = "semantic"
    HYBRID = "hybrid"
    KEYWORD = "keyword"


class SortOrder(str, Enum):
    """Sortierreihenfolge für Suchergebnisse"""
    RELEVANCE = "relevance"
    DATE = "date"
    SIMILARITY = "similarity"


class LegalNorm(BaseModel):
    """Rechtsnorm-Modell"""
    article: str = Field(..., description="Artikel/Paragraph (z.B. '§ 280 BGB')")
    law: str = Field(..., description="Gesetz (z.B. 'BGB')")
    full_text: Optional[str] = Field(None, description="Volltext der Norm")


class GutachtenMetadata(BaseModel):
    """Metadaten für ein Gutachten"""
    gutachten_id: str = Field(..., description="Eindeutige Gutachten-ID")
    title: Optional[str] = Field(None, description="Titel des Gutachtens")
    author: Optional[str] = Field(None, description="Autor")
    date_created: Optional[datetime] = Field(None, description="Erstellungsdatum")
    legal_area: Optional[str] = Field(None, description="Rechtsgebiet")
    keywords: List[str] = Field(default_factory=list, description="Schlagwörter")
    legal_norms: List[LegalNorm] = Field(default_factory=list, description="Verwendete Rechtsnormen")


class ChunkMetadataResponse(BaseModel):
    """Chunk-Metadaten für API-Response"""
    chunk_id: str = Field(..., description="Eindeutige Chunk-ID")
    source_gutachten_id: str = Field(..., description="ID des Quell-Gutachtens")
    level: int = Field(..., description="Chunk-Level (1-3)")
    section_type: Optional[str] = Field(None, description="Abschnittstyp")
    start_char: int = Field(..., description="Start-Position im Text")
    end_char: int = Field(..., description="End-Position im Text")
    token_count: int = Field(..., description="Anzahl Tokens")
    semantic_score: Optional[float] = Field(None, description="Semantischer Kohärenz-Score")
    relevance_score: Optional[float] = Field(None, description="Relevanz-Score")
    legal_norms: List[str] = Field(default_factory=list, description="Erkannte Rechtsnormen")
    keywords: List[str] = Field(default_factory=list, description="Extrahierte Keywords")


class SearchResult(BaseModel):
    """Einzelnes Suchergebnis"""
    chunk_id: str = Field(..., description="Chunk-ID")
    content: str = Field(..., description="Chunk-Inhalt")
    similarity_score: float = Field(..., description="Ähnlichkeits-Score (0-1)")
    metadata: ChunkMetadataResponse = Field(..., description="Chunk-Metadaten")
    gutachten_metadata: Optional[GutachtenMetadata] = Field(None, description="Gutachten-Metadaten")
    

class SearchRequest(BaseModel):
    """Request-Modell für Suchfragen"""
    query: str = Field(..., min_length=3, max_length=1000, description="Suchfrage")
    search_type: SearchType = Field(SearchType.HYBRID, description="Art der Suche")
    limit: int = Field(10, ge=1, le=100, description="Maximale Anzahl Ergebnisse")
    similarity_threshold: float = Field(0.6, ge=0.0, le=1.0, description="Minimaler Ähnlichkeits-Score")
    
    # Filter-Optionen
    legal_areas: Optional[List[str]] = Field(None, description="Filter nach Rechtsgebieten")
    legal_norms: Optional[List[str]] = Field(None, description="Filter nach Rechtsnormen")
    date_from: Optional[datetime] = Field(None, description="Datum von")
    date_to: Optional[datetime] = Field(None, description="Datum bis")
    
    # Sortierung
    sort_by: SortOrder = Field(SortOrder.RELEVANCE, description="Sortierung")
    
    @validator('query')
    def validate_query(cls, v):
        if not v.strip():
            raise ValueError('Query darf nicht leer sein')
        return v.strip()


class SearchResponse(BaseModel):
    """Response-Modell für Suchergebnisse"""
    query: str = Field(..., description="Ursprüngliche Suchfrage")
    total_results: int = Field(..., description="Gesamtanzahl gefundener Ergebnisse")
    results: List[SearchResult] = Field(..., description="Suchergebnisse")
    search_time_ms: float = Field(..., description="Suchzeit in Millisekunden")
    
    # Aggregationen
    legal_areas_found: Dict[str, int] = Field(default_factory=dict, description="Gefundene Rechtsgebiete")
    legal_norms_found: Dict[str, int] = Field(default_factory=dict, description="Gefundene Rechtsnormen")
    avg_similarity_score: float = Field(..., description="Durchschnittlicher Ähnlichkeits-Score")
    
    # Query-Analyse
    query_analysis: Dict[str, Any] = Field(default_factory=dict, description="Analyse der Suchfrage")


class QARequest(BaseModel):
    """Request-Modell für Frage-Antwort-System"""
    question: str = Field(..., min_length=10, max_length=2000, description="Rechtliche Frage")
    context_limit: int = Field(5, ge=1, le=20, description="Maximale Anzahl Kontext-Chunks")
    include_sources: bool = Field(True, description="Quellen in Antwort einbinden")
    
    # RAG-Parameter
    temperature: float = Field(0.3, ge=0.0, le=1.0, description="Temperatur für Textgenerierung")
    max_tokens: int = Field(1000, ge=100, le=4000, description="Maximale Tokens in Antwort")
    
    @validator('question')
    def validate_question(cls, v):
        if not v.strip():
            raise ValueError('Frage darf nicht leer sein')
        return v.strip()


class QAResponse(BaseModel):
    """Response-Modell für Frage-Antwort"""
    question: str = Field(..., description="Ursprüngliche Frage")
    answer: str = Field(..., description="Generierte Antwort")
    confidence_score: float = Field(..., description="Vertrauen in die Antwort (0-1)")
    
    # Verwendete Quellen
    sources: List[SearchResult] = Field(..., description="Verwendete Quellen")
    
    # Generation-Metadaten
    generation_time_ms: float = Field(..., description="Generierungszeit in ms")
    tokens_generated: int = Field(..., description="Anzahl generierter Tokens")
    
    # Rechtliche Einschätzung
    legal_analysis: Dict[str, Any] = Field(default_factory=dict, description="Rechtliche Analyse")


class DatabaseStats(BaseModel):
    """Datenbank-Statistiken"""
    total_gutachten: int = Field(..., description="Gesamtanzahl Gutachten")
    total_chunks: int = Field(..., description="Gesamtanzahl Chunks")
    avg_tokens_per_chunk: float = Field(..., description="Durchschnittliche Tokens pro Chunk")
    
    # Verteilung nach Rechtsgebieten
    legal_areas_distribution: Dict[str, int] = Field(default_factory=dict)
    
    # Datenbank-Status
    database_size_mb: float = Field(..., description="Datenbankgröße in MB")
    last_updated: datetime = Field(..., description="Letzte Aktualisierung")
    collection_names: List[str] = Field(..., description="Verfügbare Collections")


class HealthCheck(BaseModel):
    """Gesundheitsstatus der API"""
    status: str = Field(..., description="API-Status")
    timestamp: str = Field(default_factory=lambda: datetime.now().isoformat(), description="Zeitstempel")
    version: str = Field("1.0.0", description="API-Version")
    
    # Service-Status
    database_status: str = Field(..., description="Datenbank-Status")
    llm_status: str = Field(..., description="LLM-Status")
    embedding_status: str = Field(..., description="Embedding-Status")
    
    # Performance-Metriken
    uptime_seconds: float = Field(..., description="Betriebszeit in Sekunden")
    memory_usage_mb: float = Field(..., description="Speicherverbrauch in MB")


class ErrorResponse(BaseModel):
    """Standard-Fehlerresponse"""
    error: str = Field(..., description="Fehlermeldung")
    error_code: str = Field(..., description="Fehlercode")
    timestamp: str = Field(default_factory=lambda: datetime.now().isoformat(), description="Zeitstempel")
    request_id: Optional[str] = Field(None, description="Request-ID für Debugging")


class BulkSearchRequest(BaseModel):
    """Request für Bulk-Suche"""
    queries: List[str] = Field(..., min_items=1, max_items=50, description="Liste von Suchfragen")
    search_type: SearchType = Field(SearchType.HYBRID, description="Art der Suche")
    limit_per_query: int = Field(5, ge=1, le=20, description="Maximale Ergebnisse pro Query")
    similarity_threshold: float = Field(0.6, ge=0.0, le=1.0, description="Minimaler Ähnlichkeits-Score")


class BulkSearchResponse(BaseModel):
    """Response für Bulk-Suche"""
    queries: List[str] = Field(..., description="Verarbeitete Queries")
    results: Dict[str, SearchResponse] = Field(..., description="Ergebnisse pro Query")
    total_processing_time_ms: float = Field(..., description="Gesamte Bearbeitungszeit")
    successful_queries: int = Field(..., description="Erfolgreich verarbeitete Queries")
    failed_queries: List[str] = Field(default_factory=list, description="Fehlgeschlagene Queries")


class AutocompleteRequest(BaseModel):
    """Request für Autocomplete-Funktion"""
    partial_query: str = Field(..., min_length=2, max_length=100, description="Unvollständige Suchanfrage")
    limit: int = Field(10, ge=1, le=50, description="Maximale Anzahl Vorschläge")
    include_legal_norms: bool = Field(True, description="Rechtsnormen in Vorschläge einbeziehen")


class AutocompleteResponse(BaseModel):
    """Response für Autocomplete"""
    partial_query: str = Field(..., description="Eingabe-Query")
    suggestions: List[str] = Field(..., description="Vorschläge")
    legal_norm_suggestions: List[str] = Field(default_factory=list, description="Rechtsnorm-Vorschläge")
