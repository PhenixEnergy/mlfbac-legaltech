"""
Semantische Suchmaschine für dnoti Rechtsgutachten
Integriert ChromaDB, Hierarchical Chunking und Query Processing
"""

from typing import Dict, List, Optional, Union, Tuple, Any
from dataclasses import dataclass, field
from datetime import datetime
import logging
import re
import json
import asyncio
from pathlib import Path

# Local imports
from ..vectordb.chroma_client import ChromaDBClient
from ..data.chunker import HierarchicalChunker, TextChunk, ChunkMetadata

logger = logging.getLogger(__name__)


@dataclass
class SearchQuery:
    """Repräsentiert eine Suchanfrage mit Kontext"""
    text: str
    filters: Dict[str, Any] = field(default_factory=dict)
    max_results: int = 10
    min_similarity: float = 0.1
    include_metadata: bool = True
    search_strategy: str = "hybrid"  # semantic, keyword, hybrid
    legal_context: Optional[str] = None  # Rechtlicher Kontext


@dataclass
class SearchResult:
    """Einzelnes Suchergebnis"""
    chunk_id: str
    text: str
    similarity_score: float
    relevance_score: float
    metadata: Dict[str, Any]
    source_gutachten_id: str
    section_type: Optional[str] = None
    legal_norms: List[str] = field(default_factory=list)
    keywords: List[str] = field(default_factory=list)
    rank: int = 0


@dataclass
class SearchResponse:
    """Vollständige Suchantwort"""
    query: SearchQuery
    results: List[SearchResult]
    total_found: int
    search_time_ms: float
    strategy_used: str
    suggestions: List[str] = field(default_factory=list)
    aggregations: Dict[str, Any] = field(default_factory=dict)
    avg_similarity_score: float = 0.0
    query_analysis: Dict[str, Any] = field(default_factory=dict)


class QueryProcessor:
    """
    Verarbeitet und erweitert Benutzer-Anfragen
    Extrahiert rechtliche Kontexte und optimiert Suchterme
    """
    
    def __init__(self):
        self._init_legal_patterns()
    
    def _init_legal_patterns(self):
        """Initialisiert Patterns für rechtliche Begriffe"""
        self.legal_norm_patterns = [
            r'§§?\s*(\d+(?:\s*[a-z])?(?:\s*-\s*\d+(?:\s*[a-z])?)?)\s*(BGB|ZPO|GBO|WEG|EuErbVO|GmbHG|AktG|HGB)',
            r'Art\.?\s*(\d+(?:\s*[a-z])?(?:\s*-\s*\d+(?:\s*[a-z])?)?)\s*(EuErbVO|EGBGB)',
        ]
        
        self.legal_concepts = {
            'vertragsrecht': ['Vertrag', 'Schuldverhältnis', 'Willenserklärung', 'AGB'],
            'schadensersatz': ['Schadensersatz', 'Haftung', 'Verschulden', 'Kausalität'],
            'eigentumsrecht': ['Eigentum', 'Besitz', 'Herausgabe', 'Vindikation'],
            'gesellschaftsrecht': ['GmbH', 'AG', 'Gesellschafter', 'Geschäftsführer'],
            'erbrecht': ['Erbe', 'Testament', 'Erbfolge', 'Pflichtteil'],
            'immobilienrecht': ['Grundstück', 'Grundbuch', 'Kaufvertrag', 'Auflassung']
        }
    
    def process_query(self, query_text: str) -> Dict[str, Any]:
        """
        Verarbeitet eine Suchanfrage und extrahiert relevante Informationen
        
        Args:
            query_text: Benutzer-Suchanfrage
            
        Returns:
            Dict mit verarbeiteter Query und Metadaten
        """
        result = {
            'original_query': query_text,
            'processed_query': query_text,
            'extracted_norms': [],
            'legal_concepts': [],
            'keywords': [],
            'suggested_expansions': [],
            'filters': {}
        }
        
        # Rechtsnormen extrahieren
        result['extracted_norms'] = self._extract_legal_norms(query_text)
        
        # Rechtliche Konzepte identifizieren
        result['legal_concepts'] = self._identify_legal_concepts(query_text)
        
        # Keywords extrahieren
        result['keywords'] = self._extract_keywords(query_text)
        
        # Query erweitern/optimieren
        result['processed_query'] = self._optimize_query(query_text, result)
        
        # Automatische Filter vorschlagen
        result['filters'] = self._suggest_filters(result)
        
        # Suchvorschläge generieren
        result['suggested_expansions'] = self._generate_expansions(result)
        
        return result
    
    def _extract_legal_norms(self, text: str) -> List[Dict[str, str]]:
        """Extrahiert Rechtsnormen aus dem Query"""
        norms = []
        
        for pattern in self.legal_norm_patterns:
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                norm = {
                    'full_reference': match.group(0),
                    'paragraph': match.group(1),
                    'law': match.group(2),
                    'position': match.start()
                }
                norms.append(norm)
        
        return norms
    
    def _identify_legal_concepts(self, text: str) -> List[str]:
        """Identifiziert rechtliche Konzepte im Query"""
        identified_concepts = []
        text_lower = text.lower()
        
        for concept, keywords in self.legal_concepts.items():
            for keyword in keywords:
                if keyword.lower() in text_lower:
                    if concept not in identified_concepts:
                        identified_concepts.append(concept)
                    break
        
        return identified_concepts
    
    def _extract_keywords(self, text: str) -> List[str]:
        """Extrahiert wichtige Keywords"""
        # Einfache Implementierung - kann erweitert werden
        words = re.findall(r'\b\w{4,}\b', text)  # Wörter mit mind. 4 Zeichen
        
        # Stoppwörter entfernen
        stopwords = {'dass', 'eine', 'einer', 'eines', 'wird', 'werden', 'wurde', 'wurden', 
                    'kann', 'könnte', 'soll', 'sollte', 'nach', 'unter', 'über', 'durch'}
        
        keywords = [word.lower() for word in words if word.lower() not in stopwords]
          # Duplikate entfernen und nach Häufigkeit sortieren
        keyword_counts = {}
        for keyword in keywords:
            keyword_counts[keyword] = keyword_counts.get(keyword, 0) + 1
        
        return sorted(keyword_counts.keys(), key=lambda x: keyword_counts[x], reverse=True)[:10]
    
    def _optimize_query(self, original_query: str, analysis: Dict) -> str:
        """Optimiert die Suchanfrage basierend auf der Analyse"""
        optimized = original_query
        
        # Rechtsnormen normalisieren
        for norm in analysis['extracted_norms']:
            normalized = f"§ {norm['paragraph']} {norm['law']}"
            optimized = optimized.replace(norm['full_reference'], normalized)
        
        return optimized
    
    def _suggest_filters(self, analysis: Dict) -> Dict[str, Any]:
        """Schlägt Filter basierend auf der Query-Analyse vor"""
        filters = {}
        
        # Filter für Rechtsnormen
        if analysis['extracted_norms']:
            legal_norms_filter = []
            for norm in analysis['extracted_norms']:
                legal_norms_filter.append(f"{norm['law']} § {norm['paragraph']}")
            filters['legal_norms'] = legal_norms_filter
        
        # Filter für Abschnittstypen basierend auf Konzepten
        # DISABLED: Automatic section_type filters cause issues when metadata fields don't exist
        # if analysis['legal_concepts']:
        #     if 'schadensersatz' in analysis['legal_concepts']:
        #         filters['section_type'] = 'rechtslage'
        
        return filters
    
    def _generate_expansions(self, analysis: Dict) -> List[str]:
        """Generiert Suchvorschläge zur Query-Erweiterung"""
        expansions = []
        
        # Expansionen basierend auf rechtlichen Konzepten
        for concept in analysis['legal_concepts']:
            if concept in self.legal_concepts:
                related_terms = self.legal_concepts[concept][:3]  # Top 3 verwandte Begriffe
                for term in related_terms:
                    if term.lower() not in analysis['original_query'].lower():
                        expansions.append(f"{analysis['original_query']} {term}")
        
        return expansions[:5]  # Maximal 5 Vorschläge


class SemanticSearchEngine:
    """
    Hauptklasse für semantische Suche in dnoti Rechtsgutachten
    
    Kombiniert:
    - ChromaDB für Vektorsuche
    - Hierarchical Chunking für Datenorganisation
    - Query Processing für optimierte Anfragen
    - Ranking-Algorithmen für beste Ergebnisse    """
    
    def __init__(self, 
                 vectordb_client: ChromaDBClient,
                 chunker: Optional[HierarchicalChunker] = None):
        """
        Initialisiert die Suchmaschine
        
        Args:
            vectordb_client: ChromaDB Client
            chunker: Hierarchical Chunker (optional)
        """
        self.vectordb = vectordb_client
        self.chunker = chunker
        self.query_processor = QueryProcessor()        # Standard Collection Name - nutze legal_documents mit IBM Granite für beste Qualität
        self.default_collection = "legal_documents"  # 275 docs, 768 dimensions, IBM Granite compatible
        
        logger.info("Semantic Search Engine initialized")
    
    async def search(self, 
                    query: Union[str, SearchQuery] = None,
                    search_type: str = "hybrid", 
                    limit: int = 10,
                    similarity_threshold: float = 0.1,
                    filters: Optional[Dict[str, Any]] = None) -> SearchResponse:
        """
        Führt eine semantische Suche durch - async version for FastAPI
        
        Args:
            query: Suchanfrage als String oder SearchQuery Objekt
            search_type: Art der Suche (semantic, hybrid, keyword)
            limit: Maximale Anzahl Ergebnisse
            similarity_threshold: Mindest-Ähnlichkeitsschwelle
            filters: Zusätzliche Filter
            
        Returns:
            SearchResponse mit Ergebnissen
        """
        start_time = datetime.now()
        
        # Query normalisieren - handle both old and new API
        if isinstance(query, str):
            search_query = SearchQuery(
                text=query,
                max_results=limit,
                min_similarity=similarity_threshold,
                search_strategy=search_type,
                filters=filters or {}
            )
        elif isinstance(query, SearchQuery):
            search_query = query
            # Override with API parameters if provided
            if limit != 10:  # Non-default value
                search_query.max_results = limit
            if similarity_threshold != 0.1:  # Non-default value
                search_query.min_similarity = similarity_threshold
            if search_type != "hybrid":  # Non-default value
                search_query.search_strategy = search_type
            if filters:
                search_query.filters.update(filters)
        else:
            # Fallback for None query
            search_query = SearchQuery(
                text="",
                max_results=limit,
                min_similarity=similarity_threshold,
                search_strategy=search_type,
                filters=filters or {}
            )
        
        try:
            # Query verarbeiten
            processed_query = self.query_processor.process_query(search_query.text)
            
            # Suchstrategie bestimmen
            if search_query.search_strategy == "hybrid":
                results = self._hybrid_search(search_query, processed_query)
            elif search_query.search_strategy == "semantic":
                results = self._semantic_search(search_query, processed_query)
            elif search_query.search_strategy == "keyword":
                results = self._keyword_search(search_query, processed_query)
            else:
                results = self._hybrid_search(search_query, processed_query)
            
            # Ergebnisse ranken und filtern
            ranked_results = self._rank_and_filter_results(results, search_query)
            
            # Response erstellen
            search_time = (datetime.now() - start_time).total_seconds() * 1000
            
            response = SearchResponse(
                query=search_query,
                results=ranked_results,
                total_found=len(ranked_results),
                search_time_ms=search_time,
                strategy_used=search_query.search_strategy,
                suggestions=processed_query.get('suggested_expansions', []),
                aggregations=self._generate_aggregations(ranked_results),
                avg_similarity_score=self._calculate_avg_similarity(ranked_results),
                query_analysis=processed_query
            )
            
            logger.info(f"Search completed: {len(ranked_results)} results in {search_time:.2f}ms")
            return response
            
        except Exception as e:
            logger.error(f"Error in search: {e}")
            # Fallback Response
            search_time = (datetime.now() - start_time).total_seconds() * 1000
            return SearchResponse(
                query=search_query,
                results=[],
                total_found=0,
                search_time_ms=search_time,
                strategy_used=search_query.search_strategy
            )
    
    def _hybrid_search(self, query: SearchQuery, processed_query: Dict) -> List[SearchResult]:
        """Kombiniert semantische und Keyword-Suche"""
        
        # Semantische Suche
        semantic_results = self._semantic_search(query, processed_query)
        
        # Keyword-Suche
        keyword_results = self._keyword_search(query, processed_query)
        
        # Ergebnisse kombinieren und Duplikate entfernen
        combined_results = {}
        
        # Semantische Ergebnisse (höheres Gewicht)
        for result in semantic_results:
            result.relevance_score = result.similarity_score * 0.7
            combined_results[result.chunk_id] = result
        
        # Keyword-Ergebnisse (niedrigeres Gewicht, aber additiv)
        for result in keyword_results:
            if result.chunk_id in combined_results:
                # Scores kombinieren
                existing = combined_results[result.chunk_id]
                existing.relevance_score += result.similarity_score * 0.3
                existing.relevance_score = min(1.0, existing.relevance_score)  # Cap bei 1.0
            else:
                result.relevance_score = result.similarity_score * 0.5
                combined_results[result.chunk_id] = result
        
        return list(combined_results.values())
    
    def _semantic_search(self, query: SearchQuery, processed_query: Dict) -> List[SearchResult]:
        """Führt reine semantische Vektorsuche durch"""
        
        # ChromaDB Suche
        chroma_results = self.vectordb.search_similar_chunks(
            query=processed_query['processed_query'],
            collection_name=self.default_collection,
            n_results=query.max_results * 2,  # Mehr holen für besseres Ranking
            filters=self._build_chroma_filters(query.filters, processed_query['filters'])
        )
        
        # Ergebnisse konvertieren
        search_results = []
        for i, result in enumerate(chroma_results.get('results', [])):
            if result['similarity_score'] >= query.min_similarity:
                search_result = SearchResult(
                    chunk_id=result['metadata'].get('chunk_id', f'unknown_{i}'),
                    text=result['text'],
                    similarity_score=result['similarity_score'],
                    relevance_score=result['similarity_score'],
                    metadata=result['metadata'],
                    source_gutachten_id=result['metadata'].get('source_gutachten_id', 'unknown'),
                    section_type=result['metadata'].get('section_type'),
                    legal_norms=self._parse_json_field(result['metadata'].get('legal_norms', '[]')),
                    keywords=self._parse_json_field(result['metadata'].get('keywords', '[]')),
                    rank=i + 1
                )
                search_results.append(search_result)
        
        return search_results
    
    def _keyword_search(self, query: SearchQuery, processed_query: Dict) -> List[SearchResult]:
        """Führt Keyword-basierte Suche durch (Fallback oder Ergänzung)"""
        
        # Für ChromaDB verwenden wir eine vereinfachte Keyword-Suche
        # Da ChromaDB primär für Vektorsuche ausgelegt ist
        
        keywords = processed_query['keywords'][:5]  # Top 5 Keywords
        
        if not keywords:
            return []
        
        # Mehrere Keyword-Abfragen kombinieren
        all_results = []
        
        for keyword in keywords:
            try:
                chroma_results = self.vectordb.search_similar_chunks(
                    query=keyword,
                    collection_name=self.default_collection,
                    n_results=query.max_results,
                    filters=self._build_chroma_filters(query.filters, processed_query['filters'])
                )
                
                # Keyword-spezifische Score-Berechnung
                for result in chroma_results.get('results', []):
                    keyword_score = self._calculate_keyword_score(keyword, result['text'])
                    
                    if keyword_score >= query.min_similarity:
                        search_result = SearchResult(
                            chunk_id=result['metadata'].get('chunk_id', 'unknown'),
                            text=result['text'],
                            similarity_score=keyword_score,
                            relevance_score=keyword_score,
                            metadata=result['metadata'],
                            source_gutachten_id=result['metadata'].get('source_gutachten_id', 'unknown'),
                            section_type=result['metadata'].get('section_type'),
                            legal_norms=self._parse_json_field(result['metadata'].get('legal_norms', '[]')),
                            keywords=self._parse_json_field(result['metadata'].get('keywords', '[]'))
                        )
                        all_results.append(search_result)
                        
            except Exception as e:
                logger.warning(f"Error in keyword search for '{keyword}': {e}")
                continue
        
        # Duplikate entfernen und beste Scores behalten
        unique_results = {}
        for result in all_results:
            if result.chunk_id not in unique_results or result.similarity_score > unique_results[result.chunk_id].similarity_score:
                unique_results[result.chunk_id] = result
        
        return list(unique_results.values())
    
    def _calculate_keyword_score(self, keyword: str, text: str) -> float:
        """Berechnet Keyword-Match Score"""
        text_lower = text.lower()
        keyword_lower = keyword.lower()
        
        # Exakte Matches
        exact_matches = text_lower.count(keyword_lower)
        
        # Wort-Grenze Matches (höher gewichtet)
        word_boundary_pattern = r'\b' + re.escape(keyword_lower) + r'\b'
        word_matches = len(re.findall(word_boundary_pattern, text_lower))
        
        # Score basierend auf Häufigkeit und Textlänge
        text_length = len(text.split())
        
        if text_length == 0:
            return 0.0
        
        # Normalisierter Score
        score = (word_matches * 2 + exact_matches) / text_length
        
        # Cap bei 1.0
        return min(1.0, score * 10)  # Faktor 10 für bessere Skalierung
    
    def _build_chroma_filters(self, user_filters: Dict, processed_filters: Dict) -> Optional[Dict]:
        """Baut ChromaDB-Filter aus Benutzer- und verarbeiteten Filtern"""
        all_filters = {}
        all_filters.update(user_filters)
        all_filters.update(processed_filters)
        
        if not all_filters:
            return None
        
        # ChromaDB-spezifische Filter-Syntax
        chroma_filters = {}
        
        for key, value in all_filters.items():
            if key == 'legal_norms' and isinstance(value, list):
                # Für JSON-Arrays in ChromaDB verwenden wir $contains
                continue  # Vereinfacht - kann erweitert werden
            elif key == 'section_type':
                chroma_filters['section_type'] = value
            elif key == 'source_gutachten_id':
                chroma_filters['source_gutachten_id'] = value
            elif key == 'level':
                chroma_filters['level'] = value
        
        return chroma_filters if chroma_filters else None
    
    def _rank_and_filter_results(self, results: List[SearchResult], query: SearchQuery) -> List[SearchResult]:
        """Rankt und filtert Suchergebnisse"""
        
        if not results:
            return []
        
        # Nach Relevanz-Score sortieren
        results.sort(key=lambda x: x.relevance_score, reverse=True)
        
        # Ranking-Adjustments
        for i, result in enumerate(results):
            result.rank = i + 1
            
            # Bonus für bestimmte Abschnittstypen
            if result.section_type == 'rechtslage':
                result.relevance_score += 0.05
            elif result.section_type == 'ergebnis':
                result.relevance_score += 0.03
            
            # Bonus für rechtliche Normen
            if result.legal_norms:
                result.relevance_score += len(result.legal_norms) * 0.02
        
        # Erneut sortieren nach Adjustments
        results.sort(key=lambda x: x.relevance_score, reverse=True)
        
        # Auf max_results begrenzen
        return results[:query.max_results]
    
    def _generate_aggregations(self, results: List[SearchResult]) -> Dict[str, Any]:
        """Generiert Aggregationen über die Suchergebnisse"""
        if not results:
            return {}
        
        aggregations = {
            'section_types': {},
            'source_gutachten': {},
            'legal_norms': {},
            'avg_similarity': 0.0,
            'total_results': len(results)
        }
        
        total_similarity = 0.0
        
        for result in results:
            # Section Types
            section = result.section_type or 'unknown'
            aggregations['section_types'][section] = aggregations['section_types'].get(section, 0) + 1
            
            # Source Gutachten
            source = result.source_gutachten_id
            aggregations['source_gutachten'][source] = aggregations['source_gutachten'].get(source, 0) + 1
            
            # Legal Norms
            for norm in result.legal_norms:
                aggregations['legal_norms'][norm] = aggregations['legal_norms'].get(norm, 0) + 1
            
            total_similarity += result.similarity_score
        
        # Durchschnittliche Ähnlichkeit
        aggregations['avg_similarity'] = total_similarity / len(results)
        
        return aggregations
    
    def _calculate_avg_similarity(self, results: List[SearchResult]) -> float:
        """Berechnet die durchschnittliche Ähnlichkeit der Ergebnisse"""
        if not results:
            return 0.0
        
        total_similarity = sum(result.similarity_score for result in results)
        return total_similarity / len(results)
    
    def _parse_json_field(self, json_string: str) -> List[str]:
        """Parsed JSON-String zu Liste"""
        try:
            return json.loads(json_string) if json_string else []
        except:
            return []
    
    def suggest_queries(self, partial_query: str, limit: int = 5) -> List[str]:
        """
        Schlägt Vervollständigungen für partial Queries vor
        
        Args:
            partial_query: Unvollständige Suchanfrage
            limit: Anzahl Vorschläge
            
        Returns:
            Liste von Suchvorschlägen
        """
        suggestions = []
        
        # Einfache Implementierung basierend auf häufigen rechtlichen Begriffen
        common_legal_terms = [
            "Schadensersatz nach § 280 BGB",
            "Eigentumsherausgabeanspruch § 985 BGB", 
            "Vertragsverletzung und Haftung",
            "Gesellschaftsrecht GmbH",
            "Erbrecht Testament",
            "Immobilienrecht Grundstück",
            "Verjährung § 195 BGB",
            "Gewährleistung Kaufvertrag"
        ]
        
        partial_lower = partial_query.lower()
        
        for term in common_legal_terms:
            if partial_lower in term.lower() or term.lower().startswith(partial_lower):
                suggestions.append(term)
                
                if len(suggestions) >= limit:
                    break
        
        return suggestions
    
    async def get_autocomplete_suggestions(self, 
                                         partial_query: str, 
                                         limit: int = 10,
                                         include_legal_norms: bool = True) -> Dict[str, List[str]]:
        """
        Async wrapper für Autocomplete-Vorschläge
        
        Args:
            partial_query: Unvollständige Suchanfrage
            limit: Anzahl Vorschläge
            include_legal_norms: Ob Rechtsnormen eingeschlossen werden sollen
            
        Returns:
            Dict mit general suggestions und legal_norms
        """
        try:
            # General suggestions using existing method
            general_suggestions = self.suggest_queries(partial_query, limit)
            
            suggestions = {
                'general': general_suggestions,
                'legal_norms': []
            }
            
            if include_legal_norms:
                # Legal norm suggestions
                legal_norm_suggestions = self._get_legal_norm_suggestions(partial_query, limit // 2)
                suggestions['legal_norms'] = legal_norm_suggestions
            
            return suggestions
            
        except Exception as e:
            logger.error(f"Error getting autocomplete suggestions: {e}")
            return {'general': [], 'legal_norms': []}
    
    def _get_legal_norm_suggestions(self, partial_query: str, limit: int) -> List[str]:
        """Generiert Rechtsnorm-spezifische Vorschläge"""
        suggestions = []
        partial_lower = partial_query.lower()
        
        # Common legal norms
        common_norms = [
            "§ 280 BGB - Schadensersatz wegen Pflichtverletzung",
            "§ 985 BGB - Eigentumsherausgabeanspruch", 
            "§ 433 BGB - Vertragstypische Pflichten beim Kaufvertrag",
            "§ 823 BGB - Schadensersatzpflicht",
            "§ 242 BGB - Leistung nach Treu und Glauben",
            "§ 195 BGB - Regelmäßige Verjährungsfrist",
            "§ 311 BGB - Schuldverhältnisse durch Rechtsgeschäft",
            "§ 434 BGB - Sachmangel",
            "§ 437 BGB - Rechte des Käufers bei Mängeln",
            "§ 1922 BGB - Anfall und Ausschlagung der Erbschaft"
        ]
        
        for norm in common_norms:
            if (partial_lower in norm.lower() or 
                any(word in norm.lower() for word in partial_lower.split() if len(word) > 2)):
                suggestions.append(norm)
                if len(suggestions) >= limit:
                    break
        
        return suggestions
    
    async def find_similar_to_chunk(self, 
                                   chunk_id: str, 
                                   limit: int = 10,
                                   similarity_threshold: float = 0.7) -> SearchResponse:
        """
        Findet ähnliche Chunks zu einem gegebenen Chunk
        
        Args:
            chunk_id: ID des Referenz-Chunks
            limit: Anzahl ähnlicher Chunks
            similarity_threshold: Mindest-Ähnlichkeitsschwelle
            
        Returns:
            SearchResponse mit ähnlichen Chunks
        """
        start_time = datetime.now()
        
        try:
            # Chunk-Daten abrufen
            chunk_data = await self._get_chunk_data(chunk_id)
            if not chunk_data:
                return SearchResponse(
                    query=SearchQuery(text=f"Similar to {chunk_id}"),
                    results=[],
                    total_found=0,
                    search_time_ms=0,
                    strategy_used="similarity"
                )
            
            # Ähnlichkeitssuche basierend auf Chunk-Text
            query = SearchQuery(
                text=chunk_data['text'],
                max_results=limit + 1,  # +1 weil der Original-Chunk enthalten sein könnte
                min_similarity=similarity_threshold,
                search_strategy="semantic"
            )
            
            search_response = await self.search(query)
            
            # Original-Chunk aus Ergebnissen entfernen
            filtered_results = [
                result for result in search_response.results 
                if result.chunk_id != chunk_id
            ][:limit]
            
            # Response anpassen
            search_time = (datetime.now() - start_time).total_seconds() * 1000
            
            return SearchResponse(
                query=SearchQuery(text=f"Similar to chunk {chunk_id}"),
                results=filtered_results,
                total_found=len(filtered_results),
                search_time_ms=search_time,
                strategy_used="similarity",
                aggregations=self._generate_aggregations(filtered_results),
                avg_similarity_score=self._calculate_avg_similarity(filtered_results)
            )
            
        except Exception as e:
            logger.error(f"Error finding similar chunks: {e}")
            search_time = (datetime.now() - start_time).total_seconds() * 1000
            return SearchResponse(
                query=SearchQuery(text=f"Similar to {chunk_id}"),
                results=[],
                total_found=0,
                search_time_ms=search_time,
                strategy_used="similarity"
            )
    
    async def _get_chunk_data(self, chunk_id: str) -> Optional[Dict[str, Any]]:
        """Ruft Chunk-Daten aus der Datenbank ab"""
        try:
            # ChromaDB query für spezifischen Chunk
            results = self.vectordb.get_chunks_by_ids([chunk_id], self.default_collection)
            
            if results and len(results.get('documents', [])) > 0:
                return {
                    'id': chunk_id,
                    'text': results['documents'][0],
                    'metadata': results['metadatas'][0] if results.get('metadatas') else {}
                }
            return None
            
        except Exception as e:
            logger.error(f"Error getting chunk data for {chunk_id}: {e}")
            return None
    
    async def get_popular_queries(self, limit: int = 20) -> List[Dict[str, Any]]:
        """
        Gibt beliebte Suchanfragen zurück (simuliert)
        
        Args:
            limit: Anzahl der zurückzugebenden Queries
            
        Returns:
            Liste von beliebten Queries mit Metadaten
        """
        try:
            # Simulierte beliebte Queries - in Produktion würde dies aus Analytics kommen
            popular_queries = [
                {
                    "query": "Schadensersatz § 280 BGB",
                    "frequency": 142,
                    "avg_results": 28,
                    "success_rate": 0.89,
                    "last_searched": "2024-12-20T10:30:00Z"
                },
                {
                    "query": "Eigentumsherausgabe § 985 BGB",
                    "frequency": 98,
                    "avg_results": 31,
                    "success_rate": 0.92,
                    "last_searched": "2024-12-20T09:15:00Z"
                },
                {
                    "query": "Vertragsverletzung Kaufvertrag",
                    "frequency": 87,
                    "avg_results": 24,
            
                    "success_rate": 0.85,
                    "last_searched": "2024-12-19T16:45:00Z"
                },
                {
                    "query": "GmbH Geschäftsführer Haftung",
                    "frequency": 76,
                    "avg_results": 19,
                    "success_rate": 0.81,
                    "last_searched": "2024-12-19T14:22:00Z"
                },
                {
                    "query": "Testament Erbrecht Anfechtung",
                    "frequency": 65,
                    "avg_results": 22,
                    "success_rate": 0.88,
                    "last_searched": "2024-12-19T11:10:00Z"
                },
                {
                    "query": "Grundstückskauf Auflassung",
                    "frequency": 58,
                    "avg_results": 17,
                    "success_rate": 0.79,
                    "last_searched": "2024-12-18T15:30:00Z"
                },
                {
                    "query": "Verjährung § 195 BGB",
                    "frequency": 54,
                    "avg_results": 26,
                    "success_rate": 0.91,
                    "last_searched": "2024-12-18T13:45:00Z"
                },
                {
                    "query": "Gewährleistung Sachmangel",
                    "frequency": 49,
                    "avg_results": 20,
                    "success_rate": 0.83,
                    "last_searched": "2024-12-18T10:20:00Z"
                }
            ]
            
            return popular_queries[:limit]
            
        except Exception as e:
            logger.error(f"Error getting popular queries: {e}")
            return []
    
    async def export_search_results(self, 
                                   search_id: str, 
                                   format: str = "json") -> Dict[str, Any]:
        """
        Exportiert Suchergebnisse in verschiedenen Formaten
        
        Args:
            search_id: ID der Suche (für Caching/Retrieval)
            format: Export-Format (json, csv, xlsx)
            
        Returns:
            Export-Daten oder Datei-Information
        """
        try:
            # In einer realen Implementierung würden Suchergebnisse gecacht/gespeichert
            # Hier simulieren wir den Export mit Beispieldaten
            
            sample_results = [
                {
                    "chunk_id": "chunk_001",
                    "text": "Beispiel-Text für Schadensersatz nach § 280 BGB...",
                    "similarity_score": 0.92,
                    "source_gutachten_id": "gutachten_123",
                    "section_type": "rechtslage",
                    "legal_norms": ["BGB § 280"],
                    "keywords": ["Schadensersatz", "Pflichtverletzung"]
                },
                {
                    "chunk_id": "chunk_002", 
                    "text": "Weitere rechtliche Ausführungen zu Vertragsverletzungen...",
                    "similarity_score": 0.87,
                    "source_gutachten_id": "gutachten_124",
                    "section_type": "ergebnis",
                    "legal_norms": ["BGB § 280", "BGB § 433"],
                    "keywords": ["Vertragsverletzung", "Erfüllung"]
                }
            ]
            
            if format == "json":
                return {
                    "search_id": search_id,
                    "format": "json",
                    "results": sample_results,
                    "total_count": len(sample_results),
                    "exported_at": datetime.now().isoformat()
                }
            
            elif format in ["csv", "xlsx"]:
                # Für CSV/XLSX würde hier eine temporäre Datei erstellt
                import tempfile
                import json
                
                temp_dir = tempfile.gettempdir()
                filename = f"search_results_{search_id}.{format}"
                file_path = f"{temp_dir}/{filename}"
                
                # Vereinfachte Datei-Erstellung (in Produktion: pandas/openpyxl)
                if format == "csv":
                    with open(file_path, 'w', encoding='utf-8') as f:
                        f.write("chunk_id,similarity_score,source_gutachten_id,section_type,text\n")
                        for result in sample_results:
                            f.write(f"{result['chunk_id']},{result['similarity_score']},{result['source_gutachten_id']},{result['section_type']},\"{result['text'][:100]}...\"\n")
                
                return {
                    "search_id": search_id,
                    "format": format,
                    "file_path": file_path,
                    "filename": filename,
                    "media_type": "text/csv" if format == "csv" else "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                }
            
            else:
                raise ValueError(f"Unsupported format: {format}")
                
        except Exception as e:
            logger.error(f"Error exporting search results: {e}")
            raise e


if __name__ == "__main__":
    # Test der Suchmaschine
    from ..vectordb.chroma_client import ChromaDBClient
    
    # Test-Setup
    vectordb_client = ChromaDBClient()
    search_engine = SemanticSearchEngine(vectordb_client)
    
    # Test-Query
    test_query = "Schadensersatz nach § 280 BGB bei Vertragsverletzung"
    
    # Query Processing testen
    processor = QueryProcessor()
    processed = processor.process_query(test_query)
    
    print("Query Processing Results:")
    print(f"Original: {processed['original_query']}")
    print(f"Processed: {processed['processed_query']}")
    print(f"Legal Norms: {processed['extracted_norms']}")
    print(f"Concepts: {processed['legal_concepts']}")
    print(f"Keywords: {processed['keywords']}")
    print(f"Suggestions: {processed['suggested_expansions']}")
    
    # Suchvorschläge testen
    suggestions = search_engine.suggest_queries("Schaden", limit=3)
    print(f"Suggestions for 'Schaden': {suggestions}")
    
    # Analytics testen
    analytics = search_engine.get_search_analytics()
    print(f"Search Analytics: {analytics}")
