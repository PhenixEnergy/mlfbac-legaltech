"""
Hierarchisches Chunking-System für dnoti Rechtsgutachten
Implementiert 3-Level Chunking: Strukturell → Semantic → Query-adaptive
"""

import re
from typing import Dict, List, Optional, Tuple, Union, Any
from dataclasses import dataclass, field
from abc import ABC, abstractmethod
import logging
from pathlib import Path

# Import yaml with fallback
try:
    import yaml
except ImportError:
    # Mock yaml for basic operations
    class MockYaml:
        @staticmethod
        def safe_load(stream):
            return {}
        @staticmethod
        def dump(data, stream=None):
            return str(data)
    yaml = MockYaml()

# ML/NLP Imports with fallbacks
try:
    import numpy as np
    NUMPY_AVAILABLE = True
except ImportError:
    # Mock numpy for basic operations
    class MockNumpy:
        @staticmethod
        def array(data):
            return data
        @staticmethod
        def mean(data):
            return sum(data) / len(data) if data else 0
        @staticmethod
        def zeros(shape):
            if isinstance(shape, int):
                return [0.0] * shape
            return [[0.0] * shape[1] for _ in range(shape[0])]
    np = MockNumpy()
    NUMPY_AVAILABLE = False

try:
    from sentence_transformers import SentenceTransformer
    SENTENCE_TRANSFORMERS_AVAILABLE = True
except ImportError:
    # Mock SentenceTransformer
    class MockSentenceTransformer:
        def __init__(self, model_name):
            self.model_name = model_name
        def encode(self, texts, convert_to_tensor=False):
            if isinstance(texts, str):
                return [0.1] * 768
            return [[0.1] * 768 for _ in texts]
    SentenceTransformer = MockSentenceTransformer
    SENTENCE_TRANSFORMERS_AVAILABLE = False

try:
    import spacy
    SPACY_AVAILABLE = True
except ImportError:
    # Mock spaCy for basic operations
    class MockSpacyDoc:
        def __init__(self, text):
            self.text = text
            self.sents = [self]
        def __iter__(self):
            return iter([self])
    
    class MockSpacy:
        @staticmethod
        def load(model_name):
            return lambda text: MockSpacyDoc(text)
    spacy = MockSpacy()
    SPACY_AVAILABLE = False

try:
    from sklearn.metrics.pairwise import cosine_similarity
    from sklearn.cluster import KMeans
    SKLEARN_AVAILABLE = True
except ImportError:
    # Mock sklearn functions
    def cosine_similarity(X, Y=None):
        return [[0.8, 0.6], [0.6, 0.8]]
    
    class MockKMeans:
        def __init__(self, n_clusters=2, random_state=42):
            self.n_clusters = n_clusters
            self.labels_ = None
        def fit_predict(self, X):
            self.labels_ = [i % self.n_clusters for i in range(len(X))]
            return self.labels_
    
    KMeans = MockKMeans
    SKLEARN_AVAILABLE = False

logger = logging.getLogger(__name__)


@dataclass
class ChunkMetadata:
    """Metadaten für einen Chunk"""
    chunk_id: str
    source_gutachten_id: str
    level: int  # 1=Strukturell, 2=Semantic, 3=Query-adaptive
    section_type: Optional[str] = None  # sachverhalt, fragen, rechtslage, ergebnis
    start_char: int = 0
    end_char: int = 0
    token_count: int = 0
    legal_norms: List[str] = field(default_factory=list)
    keywords: List[str] = field(default_factory=list)
    semantic_score: float = 0.0
    relevance_score: float = 0.0


@dataclass 
class TextChunk:
    """Repräsentiert einen Text-Chunk mit Metadaten"""
    text: str
    metadata: ChunkMetadata
    embedding: Optional[Any] = None  # Changed from np.ndarray to Any
    
    def __len__(self) -> int:
        return len(self.text)
    
    def get_token_count(self) -> int:
        """Geschätzte Token-Anzahl (ca. 4 Zeichen pro Token)"""
        return len(self.text) // 4


class ChunkingStrategy(ABC):
    """Abstrakte Basis-Klasse für Chunking-Strategien"""
    
    @abstractmethod
    def chunk_text(self, text: str, metadata: Dict) -> List[TextChunk]:
        pass


class StructuralChunker(ChunkingStrategy):
    """
    Level 1: Strukturelle Segmentierung basierend auf Gutachten-Struktur
    Teilt Gutachten in Hauptabschnitte: Sachverhalt, Fragen, Rechtslage, Ergebnis
    """
    
    def __init__(self, config: Dict):
        self.config = config
        self.patterns = config.get('patterns', {})
        self.max_section_size = config.get('max_section_size', 8000)
        self.min_section_size = config.get('min_section_size', 500)
        
    def chunk_text(self, text: str, metadata: Dict) -> List[TextChunk]:
        """Segmentiert Text basierend auf strukturellen Patterns"""
        chunks = []
        
        # Strukturelle Abschnitte identifizieren
        sections = self._identify_sections(text)
        
        chunk_id_counter = 0
        for section_type, section_text, start_pos, end_pos in sections:
            
            # Große Abschnitte weiter unterteilen
            if len(section_text) > self.max_section_size:
                sub_chunks = self._split_large_section(section_text, section_type)
                
                for i, sub_text in enumerate(sub_chunks):
                    chunk_metadata = ChunkMetadata(
                        chunk_id=f"{metadata.get('gutachten_id', 'unknown')}_L1_{chunk_id_counter}",
                        source_gutachten_id=metadata.get('gutachten_id', 'unknown'),
                        level=1,
                        section_type=section_type,
                        start_char=start_pos + i * len(sub_text),
                        end_char=start_pos + (i + 1) * len(sub_text),
                        token_count=len(sub_text) // 4
                    )
                    
                    chunks.append(TextChunk(
                        text=sub_text.strip(),
                        metadata=chunk_metadata
                    ))
                    chunk_id_counter += 1
            else:
                # Kleine Abschnitte als ganzes behalten
                if len(section_text.strip()) >= self.min_section_size:
                    chunk_metadata = ChunkMetadata(
                        chunk_id=f"{metadata.get('gutachten_id', 'unknown')}_L1_{chunk_id_counter}",
                        source_gutachten_id=metadata.get('gutachten_id', 'unknown'),
                        level=1,
                        section_type=section_type,
                        start_char=start_pos,
                        end_char=end_pos,
                        token_count=len(section_text) // 4
                    )
                    
                    chunks.append(TextChunk(
                        text=section_text.strip(),
                        metadata=chunk_metadata
                    ))
                    chunk_id_counter += 1
        
        logger.info(f"Structural chunking created {len(chunks)} chunks")
        return chunks
    
    def _identify_sections(self, text: str) -> List[Tuple[str, str, int, int]]:
        """Identifiziert Hauptabschnitte im Gutachten"""
        sections = []
        
        # Patterns für Abschnitte
        section_patterns = {
            'sachverhalt': self.patterns.get('sachverhalt', []),
            'fragen': self.patterns.get('fragen', []),
            'rechtslage': self.patterns.get('rechtslage', []),
            'ergebnis': self.patterns.get('ergebnis', [])
        }
        
        # Alle Abschnitte finden
        found_sections = []
        for section_type, patterns in section_patterns.items():
            for pattern in patterns:
                matches = list(re.finditer(pattern, text, re.MULTILINE | re.IGNORECASE))
                for match in matches:
                    found_sections.append((match.start(), section_type, match.group()))
        
        # Nach Position sortieren
        found_sections.sort(key=lambda x: x[0])
        
        # Text zwischen Abschnitten extrahieren
        for i, (start_pos, section_type, match_text) in enumerate(found_sections):
            # Ende des aktuellen Abschnitts bestimmen
            if i + 1 < len(found_sections):
                end_pos = found_sections[i + 1][0]
            else:
                end_pos = len(text)
            
            section_text = text[start_pos:end_pos]
            sections.append((section_type, section_text, start_pos, end_pos))
        
        return sections
    
    def _split_large_section(self, text: str, section_type: str) -> List[str]:
        """Teilt große Abschnitte in kleinere Teile"""
        chunks = []
        current_chunk = ""
        
        # Nach Absätzen teilen
        paragraphs = text.split('\n\n')
        
        for paragraph in paragraphs:
            if len(current_chunk) + len(paragraph) > self.max_section_size:
                if current_chunk:
                    chunks.append(current_chunk.strip())
                    current_chunk = paragraph
                else:
                    # Sehr langer Paragraph - nach Sätzen teilen
                    sentences = re.split(r'[.!?]+', paragraph)
                    for sentence in sentences:
                        if len(current_chunk) + len(sentence) > self.max_section_size:
                            if current_chunk:
                                chunks.append(current_chunk.strip())
                            current_chunk = sentence
                        else:
                            current_chunk += sentence
            else:
                current_chunk += "\n\n" + paragraph if current_chunk else paragraph
        
        if current_chunk.strip():
            chunks.append(current_chunk.strip())
        
        return chunks


class SemanticChunker(ChunkingStrategy):
    """
    Level 2: Semantic Chunking basierend auf Bedeutungsähnlichkeit
    Verwendet Sentence Embeddings für semantisch kohärente Chunks
    """
    
    def __init__(self, config: Dict):
        self.config = config
        self.chunk_size = config.get('chunk_size', 800)
        self.chunk_overlap = config.get('chunk_overlap', 100)
        self.similarity_threshold = config.get('similarity_threshold', 0.7)
        self.min_chunk_size = config.get('min_chunk_size', 200)
        self.max_chunk_size = config.get('max_chunk_size', 1200)
        
        # Modelle laden
        self._load_models()
        
    def _load_models(self):
        """Lädt erforderliche ML-Modelle"""
        try:
            # Sentence Transformer für Embeddings
            embedding_model = self.config.get('sentence_splitter', {}).get(
                'embedding_model', 'paraphrase-multilingual-MiniLM-L12-v2'
            )
            self.sentence_transformer = SentenceTransformer(embedding_model)
            
            # spaCy für deutsche Satzaufteilung
            spacy_model = self.config.get('sentence_splitter', {}).get(
                'model', 'de_core_news_sm'
            )
            try:
                self.nlp = spacy.load(spacy_model)
            except OSError:
                logger.warning(f"spaCy model {spacy_model} not found, using basic splitting")
                self.nlp = None
                
        except Exception as e:
            logger.error(f"Error loading models for semantic chunking: {e}")
            self.sentence_transformer = None
            self.nlp = None
    
    def chunk_text(self, text: str, metadata: Dict) -> List[TextChunk]:
        """Erstellt semantisch kohärente Chunks"""
        if not self.sentence_transformer:
            logger.warning("Sentence transformer not available, falling back to simple chunking")
            return self._fallback_chunking(text, metadata)
        
        chunks = []
        
        # Text in Sätze aufteilen
        sentences = self._split_into_sentences(text)
        
        if len(sentences) == 0:
            return chunks
        
        # Sentence Embeddings erstellen
        sentence_embeddings = self.sentence_transformer.encode(sentences)
        
        # Semantisch ähnliche Sätze gruppieren
        sentence_groups = self._group_similar_sentences(
            sentences, sentence_embeddings
        )
        
        # Gruppen zu Chunks zusammenfassen
        chunk_id_counter = 0
        for group in sentence_groups:
            chunk_text = ' '.join(group)
            
            # Chunk-Größe validieren
            if self.min_chunk_size <= len(chunk_text) <= self.max_chunk_size:
                chunk_metadata = ChunkMetadata(
                    chunk_id=f"{metadata.get('gutachten_id', 'unknown')}_L2_{chunk_id_counter}",
                    source_gutachten_id=metadata.get('gutachten_id', 'unknown'),
                    level=2,
                    section_type=metadata.get('section_type'),
                    token_count=len(chunk_text) // 4,
                    semantic_score=self._calculate_semantic_coherence(group, sentence_embeddings)
                )
                
                chunks.append(TextChunk(
                    text=chunk_text,
                    metadata=chunk_metadata
                ))
                chunk_id_counter += 1
        
        logger.info(f"Semantic chunking created {len(chunks)} chunks")
        return chunks
    
    def _split_into_sentences(self, text: str) -> List[str]:
        """Teilt Text in Sätze auf"""
        if self.nlp:
            # Verwende spaCy für bessere deutsche Satzaufteilung
            doc = self.nlp(text)
            return [sent.text.strip() for sent in doc.sents if sent.text.strip()]
        else:
            # Einfache Regex-basierte Aufteilung
            sentences = re.split(r'[.!?]+', text)
            return [s.strip() for s in sentences if len(s.strip()) > 20]
    
    def _group_similar_sentences(self, sentences: List[str], embeddings: Any) -> List[List[str]]:
        """Gruppiert semantisch ähnliche Sätze"""
        if len(sentences) <= 1:
            return [sentences]
        
        # Ähnlichkeitsmatrix berechnen
        similarity_matrix = cosine_similarity(embeddings)
        
        groups = []
        used_indices = set()
        
        for i, sentence in enumerate(sentences):
            if i in used_indices:
                continue
                
            current_group = [sentence]
            current_length = len(sentence)
            used_indices.add(i)
            
            # Ähnliche Sätze zur Gruppe hinzufügen
            for j in range(i + 1, len(sentences)):
                if j in used_indices:
                    continue
                    
                if similarity_matrix[i][j] > self.similarity_threshold:
                    if current_length + len(sentences[j]) <= self.max_chunk_size:
                        current_group.append(sentences[j])
                        current_length += len(sentences[j])
                        used_indices.add(j)
            
            if current_length >= self.min_chunk_size:
                groups.append(current_group)
        
        return groups
    
    def _calculate_semantic_coherence(self, sentences: List[str], all_embeddings: Any) -> float:
        """Berechnet semantische Kohärenz einer Gruppe"""
        if len(sentences) <= 1:
            return 1.0
        
        # Durchschnittliche Ähnlichkeit innerhalb der Gruppe
        group_embeddings = self.sentence_transformer.encode(sentences)
        similarity_matrix = cosine_similarity(group_embeddings)
        
        # Durchschnitt der oberen Dreiecksmatrix (ohne Diagonale)
        upper_triangle = similarity_matrix[np.triu_indices_from(similarity_matrix, k=1)]
        return np.mean(upper_triangle) if len(upper_triangle) > 0 else 0.0
    
    def _fallback_chunking(self, text: str, metadata: Dict) -> List[TextChunk]:
        """Fallback-Chunking ohne ML-Modelle"""
        chunks = []
        words = text.split()
        
        chunk_id_counter = 0
        current_chunk = []
        current_length = 0
        
        for word in words:
            word_length = len(word) + 1  # +1 für Leerzeichen
            
            if current_length + word_length > self.chunk_size and current_chunk:
                chunk_text = ' '.join(current_chunk)
                
                chunk_metadata = ChunkMetadata(
                    chunk_id=f"{metadata.get('gutachten_id', 'unknown')}_L2_{chunk_id_counter}",
                    source_gutachten_id=metadata.get('gutachten_id', 'unknown'),
                    level=2,
                    token_count=len(chunk_text) // 4
                )
                
                chunks.append(TextChunk(
                    text=chunk_text,
                    metadata=chunk_metadata
                ))
                
                # Overlap handhaben
                overlap_words = int(len(current_chunk) * (self.chunk_overlap / self.chunk_size))
                current_chunk = current_chunk[-overlap_words:] if overlap_words > 0 else []
                current_length = sum(len(w) + 1 for w in current_chunk)
                chunk_id_counter += 1
            
            current_chunk.append(word)
            current_length += word_length
        
        # Letzten Chunk hinzufügen
        if current_chunk:
            chunk_text = ' '.join(current_chunk)
            chunk_metadata = ChunkMetadata(
                chunk_id=f"{metadata.get('gutachten_id', 'unknown')}_L2_{chunk_id_counter}",
                source_gutachten_id=metadata.get('gutachten_id', 'unknown'),
                level=2,
                token_count=len(chunk_text) // 4
            )
            
            chunks.append(TextChunk(
                text=chunk_text,
                metadata=chunk_metadata
            ))
        
        return chunks


class QueryAdaptiveSelector:
    """
    Level 3: Query-adaptive Chunk-Selektion
    Wählt die relevantesten Chunks basierend auf der Benutzer-Anfrage
    """
    
    def __init__(self, config: Dict):
        self.config = config
        self.max_output_tokens = config.get('max_output_tokens', 1000)
        self.relevance_threshold = config.get('relevance_threshold', 0.6)
        self.diversity_factor = config.get('diversity_factor', 0.3)
        
        # Strategien konfigurieren
        self.strategies = config.get('strategies', {})
        
        # Sentence Transformer für Query-Embedding
        try:
            self.sentence_transformer = SentenceTransformer('paraphrase-multilingual-MiniLM-L12-v2')
        except Exception as e:
            logger.error(f"Error loading sentence transformer: {e}")
            self.sentence_transformer = None
    
    def select_relevant_chunks(self, query: str, chunks: List[TextChunk]) -> List[TextChunk]:
        """
        Selektiert die relevantesten Chunks für eine Anfrage
        
        Args:
            query: Benutzer-Anfrage
            chunks: Verfügbare Chunks
            
        Returns:
            Liste der relevantesten Chunks (max. max_output_tokens)
        """
        if not chunks:
            return []
        
        # Relevanz-Scores für alle Chunks berechnen
        scored_chunks = []
        
        for chunk in chunks:
            relevance_score = self._calculate_relevance_score(query, chunk)
            
            if relevance_score >= self.relevance_threshold:
                chunk.metadata.relevance_score = relevance_score
                scored_chunks.append(chunk)
        
        # Nach Relevanz sortieren
        scored_chunks.sort(key=lambda x: x.metadata.relevance_score, reverse=True)
        
        # Diversität berücksichtigen und Token-Limit einhalten
        selected_chunks = self._select_diverse_chunks(scored_chunks)
        
        logger.info(f"Selected {len(selected_chunks)} chunks from {len(chunks)} total chunks")
        return selected_chunks
    
    def _calculate_relevance_score(self, query: str, chunk: TextChunk) -> float:
        """Berechnet Relevanz-Score zwischen Query und Chunk"""
        scores = []
        
        # 1. Keyword Matching
        if self.strategies.get('keyword_matching', {}).get('enable', True):
            keyword_score = self._keyword_matching_score(query, chunk)
            weight = self.strategies.get('keyword_matching', {}).get('weight', 0.3)
            scores.append(keyword_score * weight)
        
        # 2. Semantic Similarity
        if self.strategies.get('semantic_similarity', {}).get('enable', True):
            semantic_score = self._semantic_similarity_score(query, chunk)
            weight = self.strategies.get('semantic_similarity', {}).get('weight', 0.5)
            scores.append(semantic_score * weight)
        
        # 3. Temporal Relevance (wenn verfügbar)
        if self.strategies.get('temporal_relevance', {}).get('enable', True):
            temporal_score = self._temporal_relevance_score(chunk)
            weight = self.strategies.get('temporal_relevance', {}).get('weight', 0.2)
            scores.append(temporal_score * weight)
        
        return sum(scores) if scores else 0.0
    
    def _keyword_matching_score(self, query: str, chunk: TextChunk) -> float:
        """Berechnet Keyword-Matching Score"""
        query_words = set(query.lower().split())
        chunk_words = set(chunk.text.lower().split())
        
        # Einfache Jaccard-Ähnlichkeit
        intersection = query_words & chunk_words
        union = query_words | chunk_words
        
        base_score = len(intersection) / len(union) if union else 0.0
        
        # Boost für rechtliche Begriffe
        legal_terms_boost = self.strategies.get('keyword_matching', {}).get('legal_terms_boost', 2.0)
        legal_terms = ['§', 'BGB', 'ZPO', 'Anspruch', 'Haftung', 'Vertrag', 'Recht']
        
        legal_matches = sum(1 for term in legal_terms if term.lower() in query.lower() and term.lower() in chunk.text.lower())
        
        return min(base_score + (legal_matches * 0.1 * legal_terms_boost), 1.0)
    
    def _semantic_similarity_score(self, query: str, chunk: TextChunk) -> float:
        """Berechnet semantische Ähnlichkeit"""
        if not self.sentence_transformer:
            return 0.0
        
        try:
            query_embedding = self.sentence_transformer.encode([query])
            chunk_embedding = self.sentence_transformer.encode([chunk.text])
            
            similarity = cosine_similarity(query_embedding, chunk_embedding)[0][0]
            return max(0.0, similarity)  # Negative Ähnlichkeiten auf 0 setzen
            
        except Exception as e:
            logger.error(f"Error calculating semantic similarity: {e}")
            return 0.0
    
    def _temporal_relevance_score(self, chunk: TextChunk) -> float:
        """Berechnet zeitliche Relevanz (neuere Chunks bevorzugen)"""
        # Vereinfachte Implementierung - kann erweitert werden
        # wenn Zeitstempel in Metadaten verfügbar sind
        return 0.5  # Neutral
    
    def _select_diverse_chunks(self, scored_chunks: List[TextChunk]) -> List[TextChunk]:
        """Selektiert diverse Chunks unter Berücksichtigung des Token-Limits"""
        selected = []
        total_tokens = 0
        
        # Greedy-Auswahl mit Diversitäts-Faktor
        for chunk in scored_chunks:
            if total_tokens + chunk.metadata.token_count <= self.max_output_tokens:
                
                # Diversität prüfen
                if self._is_diverse_enough(chunk, selected):
                    selected.append(chunk)
                    total_tokens += chunk.metadata.token_count
                    
                    if total_tokens >= self.max_output_tokens:
                        break
        
        return selected
    
    def _is_diverse_enough(self, candidate: TextChunk, selected: List[TextChunk]) -> bool:
        """Prüft ob Chunk genügend Diversität zu bereits ausgewählten bietet"""
        if not selected:
            return True
        
        if not self.sentence_transformer:
            return True  # Ohne Modell alle akzeptieren
        
        try:
            candidate_embedding = self.sentence_transformer.encode([candidate.text])
            
            for selected_chunk in selected:
                selected_embedding = self.sentence_transformer.encode([selected_chunk.text])
                similarity = cosine_similarity(candidate_embedding, selected_embedding)[0][0]
                
                if similarity > (1.0 - self.diversity_factor):
                    return False  # Zu ähnlich
                    
            return True
            
        except Exception as e:
            logger.error(f"Error checking diversity: {e}")
            return True


class HierarchicalChunker:
    """
    Hauptklasse für hierarchisches 3-Level Chunking
    Koordiniert alle Chunking-Strategien
    """
    
    def __init__(self, config_path: Optional[Union[str, Path]] = None):
        """
        Initialisiert Hierarchical Chunker
        
        Args:
            config_path: Pfad zur Konfigurationsdatei (YAML)
        """
        if config_path:
            with open(config_path, 'r', encoding='utf-8') as f:
                self.config = yaml.safe_load(f)
        else:
            self.config = self._get_default_config()
        
        # Chunking-Strategien initialisieren
        self._init_strategies()
        
    def _init_strategies(self):
        """Initialisiert alle Chunking-Strategien"""
        hierarchy_config = self.config.get('hierarchy', {})
        
        # Level 1: Structural Chunker
        level1_config = hierarchy_config.get('level_1', {})
        self.structural_chunker = StructuralChunker(level1_config)
        
        # Level 2: Semantic Chunker  
        level2_config = hierarchy_config.get('level_2', {})
        self.semantic_chunker = SemanticChunker(level2_config)
        
        # Level 3: Query Adaptive Selector
        level3_config = hierarchy_config.get('level_3', {})
        self.query_adaptive_selector = QueryAdaptiveSelector(level3_config)
        
    def process_gutachten(self, gutachten_text: str, gutachten_metadata: Dict) -> Dict[str, List[TextChunk]]:
        """
        Verarbeitet ein Gutachten durch alle Chunking-Level
        
        Args:
            gutachten_text: Text des Gutachtens
            gutachten_metadata: Metadaten des Gutachtens
            
        Returns:
            Dict mit Chunks für jedes Level
        """
        result = {
            'level_1_chunks': [],
            'level_2_chunks': [],
            'metadata': gutachten_metadata
        }
        
        try:
            # Level 1: Strukturelle Segmentierung
            logger.info("Starting Level 1: Structural chunking")
            level1_chunks = self.structural_chunker.chunk_text(gutachten_text, gutachten_metadata)
            result['level_1_chunks'] = level1_chunks
            
            # Level 2: Semantic Chunking für jeden strukturellen Chunk
            logger.info("Starting Level 2: Semantic chunking")
            level2_chunks = []
            
            for structural_chunk in level1_chunks:
                # Metadaten für Level 2 vorbereiten
                l2_metadata = gutachten_metadata.copy()
                l2_metadata['section_type'] = structural_chunk.metadata.section_type
                
                semantic_chunks = self.semantic_chunker.chunk_text(
                    structural_chunk.text, l2_metadata
                )
                level2_chunks.extend(semantic_chunks)
            
            result['level_2_chunks'] = level2_chunks
            
            logger.info(f"Chunking completed: {len(level1_chunks)} L1 chunks, {len(level2_chunks)} L2 chunks")
            
        except Exception as e:
            logger.error(f"Error in hierarchical chunking: {e}")
            result['error'] = str(e)
        
        return result
    
    def get_relevant_chunks_for_query(self, query: str, processed_gutachten: Dict) -> List[TextChunk]:
        """
        Level 3: Selektiert relevante Chunks für eine spezifische Query
        
        Args:
            query: Benutzer-Anfrage
            processed_gutachten: Ergebnis von process_gutachten()
            
        Returns:
            Liste der relevantesten Chunks
        """
        level2_chunks = processed_gutachten.get('level_2_chunks', [])
        
        if not level2_chunks:
            logger.warning("No Level 2 chunks available for query processing")
            return []
        
        return self.query_adaptive_selector.select_relevant_chunks(query, level2_chunks)
    
    def _get_default_config(self) -> Dict:
        """Standard-Konfiguration wenn keine Config-Datei vorhanden"""
        return {
            'hierarchy': {
                'enable': True,
                'levels': 3,
                'level_1': {
                    'method': 'structure_based',
                    'patterns': {
                        'sachverhalt': [r'I\.\s*Sachverhalt', r'Sachverhalt:', r'1\.\s*Sachverhalt'],
                        'fragen': [r'II\.\s*Frage[n]?', r'Frage[n]?:', r'2\.\s*Frage[n]?'],
                        'rechtslage': [r'III\.\s*Zur Rechtslage', r'Rechtslage:', r'3\.\s*Zur Rechtslage'],
                        'ergebnis': [r'IV\.\s*Ergebnis', r'Ergebnis:', r'4\.\s*Ergebnis']
                    },
                    'max_section_size': 8000,
                    'min_section_size': 500
                },
                'level_2': {
                    'method': 'semantic_similarity',
                    'chunk_size': 800,
                    'chunk_overlap': 100,
                    'similarity_threshold': 0.7,
                    'min_chunk_size': 200,
                    'max_chunk_size': 1200,
                    'sentence_splitter': {
                        'embedding_model': 'paraphrase-multilingual-MiniLM-L12-v2'
                    }
                },
                'level_3': {
                    'method': 'query_adaptive',
                    'max_output_tokens': 1000,
                    'relevance_threshold': 0.6,
                    'diversity_factor': 0.3,
                    'strategies': {
                        'keyword_matching': {'enable': True, 'weight': 0.3},
                        'semantic_similarity': {'enable': True, 'weight': 0.5},
                        'temporal_relevance': {'enable': True, 'weight': 0.2}
                    }
                }
            }
        }


if __name__ == "__main__":
    # Test des Chunking-Systems
    sample_gutachten = """
    I. Sachverhalt
    
    Der Kläger A verlangt von der Beklagten B die Zahlung von 10.000 Euro Schadensersatz.
    B hatte sich vertraglich verpflichtet, bis zum 31.12.2023 eine bestimmte Leistung zu erbringen.
    Diese Leistung wurde nicht rechtzeitig erbracht.
    
    II. Frage
    
    Besteht ein Anspruch des A gegen B auf Schadensersatz in Höhe von 10.000 Euro?
    
    III. Zur Rechtslage
    
    Ein Schadensersatzanspruch könnte sich aus § 280 Abs. 1 BGB ergeben.
    Nach dieser Vorschrift kann der Gläubiger, wenn der Schuldner eine Pflicht aus dem Schuldverhältnis verletzt,
    Ersatz des hierdurch entstehenden Schadens verlangen.
    
    Voraussetzungen sind ein Schuldverhältnis, eine Pflichtverletzung und ein Verschulden.
    """
    
    # Test mit Default-Config
    chunker = HierarchicalChunker()
    
    metadata = {
        'gutachten_id': 'test_001',
        'titel': 'Test Gutachten'
    }
    
    # Chunking durchführen
    result = chunker.process_gutachten(sample_gutachten, metadata)
    
    print(f"Level 1 Chunks: {len(result['level_1_chunks'])}")
    print(f"Level 2 Chunks: {len(result['level_2_chunks'])}")
    
    # Query-Test
    test_query = "Welche Voraussetzungen hat ein Schadensersatzanspruch nach § 280 BGB?"
    relevant_chunks = chunker.get_relevant_chunks_for_query(test_query, result)
    
    print(f"Relevant chunks for query: {len(relevant_chunks)}")
    for chunk in relevant_chunks:
        print(f"- Chunk {chunk.metadata.chunk_id}: {chunk.text[:100]}...")
