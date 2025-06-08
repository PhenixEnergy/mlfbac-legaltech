"""
LM Studio Client für Deepseek V2 Lite 16B Integration
Implementiert RAG-Pipeline mit intelligenter Antwortgenerierung
"""

import requests
import json
from typing import Dict, List, Optional, Union, Any, Generator
from dataclasses import dataclass, field
import logging
from datetime import datetime
import time
import yaml
from pathlib import Path

# Local imports
from ..search.semantic_search import SearchResult, SearchResponse

logger = logging.getLogger(__name__)


@dataclass
class LLMConfig:
    """Konfiguration für LM Studio Client"""
    base_url: str = "http://localhost:1234"
    model_name: str = "deepseek-v2-lite-16b"
    max_tokens: int = 1000
    temperature: float = 0.1
    top_p: float = 0.9
    stream: bool = False
    timeout: int = 30
    max_retries: int = 3


@dataclass
class PromptTemplate:
    """Template für Prompt-Generierung"""
    system_prompt: str
    user_template: str
    context_template: str
    legal_context_boost: bool = True


@dataclass
class LLMResponse:
    """Antwort vom Language Model"""
    response_text: str
    confidence_score: float
    token_count: int
    processing_time_ms: float
    sources_used: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    @property
    def text(self) -> str:
        """Alias für response_text für API-Kompatibilität"""
        return self.response_text
    
    @property
    def tokens_generated(self) -> int:
        """Alias für token_count für API-Kompatibilität"""
        return self.token_count
    legal_references: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)


class LMStudioClient:
    """
    Client für LM Studio API
    Implementiert Kommunikation mit lokal gehosteten Modellen
    """
    
    def __init__(self, config: Optional[LLMConfig] = None):
        """
        Initialisiert LM Studio Client
        
        Args:
            config: LLM-Konfiguration
        """
        self.config = config or LLMConfig()
        self.session = requests.Session()
        self.session.headers.update({
            'Content-Type': 'application/json'
        })
        
        # Verbindung testen
        self._test_connection()
        
    def _test_connection(self) -> bool:
        """Testet Verbindung zu LM Studio"""
        try:
            response = self.session.get(
                f"{self.config.base_url}/v1/models",
                timeout=5
            )
            
            if response.status_code == 200:
                models = response.json()
                logger.info(f"LM Studio connection successful. Available models: {len(models.get('data', []))}")
                return True
            else:
                logger.warning(f"LM Studio responded with status {response.status_code}")
                return False
                
        except Exception as e:
            logger.error(f"Failed to connect to LM Studio: {e}")
            return False
    
    def generate_completion(self, 
                           prompt: str, 
                           system_prompt: Optional[str] = None,
                           **kwargs) -> LLMResponse:
        """
        Generiert Completion über LM Studio API
        
        Args:
            prompt: Benutzer-Prompt
            system_prompt: System-Prompt (optional)
            **kwargs: Zusätzliche Parameter
            
        Returns:
            LLMResponse mit generierter Antwort
        """
        start_time = time.time()
        
        # Request-Payload erstellen
        messages = []
        
        if system_prompt:
            messages.append({
                "role": "system",
                "content": system_prompt
            })
        
        messages.append({
            "role": "user", 
            "content": prompt
        })
        
        payload = {
            "model": self.config.model_name,
            "messages": messages,
            "max_tokens": kwargs.get('max_tokens', self.config.max_tokens),
            "temperature": kwargs.get('temperature', self.config.temperature),
            "top_p": kwargs.get('top_p', self.config.top_p),
            "stream": kwargs.get('stream', self.config.stream)
        }
        
        # API-Call mit Retry-Logic
        for attempt in range(self.config.max_retries):
            try:
                response = self.session.post(
                    f"{self.config.base_url}/v1/chat/completions",
                    json=payload,
                    timeout=self.config.timeout
                )
                
                if response.status_code == 200:
                    result = response.json()
                    
                    # Response verarbeiten
                    content = result['choices'][0]['message']['content']
                    usage = result.get('usage', {})
                    
                    processing_time = (time.time() - start_time) * 1000
                    
                    return LLMResponse(
                        response_text=content,
                        confidence_score=self._estimate_confidence(content),
                        token_count=usage.get('total_tokens', 0),
                        processing_time_ms=processing_time,
                        metadata={
                            'model': self.config.model_name,
                            'attempt': attempt + 1,
                            'finish_reason': result['choices'][0].get('finish_reason'),
                            'usage': usage
                        }
                    )
                else:
                    logger.warning(f"LM Studio API error: {response.status_code} - {response.text}")
                    
            except Exception as e:
                logger.error(f"LM Studio API call failed (attempt {attempt + 1}): {e}")
                
                if attempt == self.config.max_retries - 1:
                    # Letzter Versuch fehlgeschlagen
                    processing_time = (time.time() - start_time) * 1000
                    return LLMResponse(
                        response_text="Entschuldigung, ich konnte Ihre Anfrage nicht bearbeiten. Bitte versuchen Sie es später erneut.",
                        confidence_score=0.0,
                        token_count=0,
                        processing_time_ms=processing_time,
                        metadata={'error': str(e), 'failed_attempts': attempt + 1}
                    )
                
                time.sleep(1)  # Kurze Pause vor Retry
        
        return LLMResponse(
            response_text="Unerwarteter Fehler bei der Antwortgenerierung.",
            confidence_score=0.0,
            token_count=0,
            processing_time_ms=0.0
        )
    
    def generate_streaming_completion(self, 
                                    prompt: str, 
                                    system_prompt: Optional[str] = None,
                                    **kwargs) -> Generator[str, None, None]:
        """
        Generiert Streaming Completion
        
        Args:
            prompt: Benutzer-Prompt
            system_prompt: System-Prompt (optional)
            **kwargs: Zusätzliche Parameter
            
        Yields:
            Chunks der generierten Antwort
        """
        messages = []
        
        if system_prompt:
            messages.append({
                "role": "system",
                "content": system_prompt
            })
        
        messages.append({
            "role": "user",
            "content": prompt
        })
        
        payload = {
            "model": self.config.model_name,
            "messages": messages,
            "max_tokens": kwargs.get('max_tokens', self.config.max_tokens),
            "temperature": kwargs.get('temperature', self.config.temperature),
            "top_p": kwargs.get('top_p', self.config.top_p),
            "stream": True
        }
        
        try:
            response = self.session.post(
                f"{self.config.base_url}/v1/chat/completions",
                json=payload,
                timeout=self.config.timeout,
                stream=True
            )
            
            if response.status_code == 200:
                for line in response.iter_lines():
                    if line:
                        line_str = line.decode('utf-8')
                        if line_str.startswith('data: '):
                            data_str = line_str[6:]  # Remove 'data: ' prefix
                            
                            if data_str.strip() == '[DONE]':
                                break
                            
                            try:
                                data = json.loads(data_str)
                                if 'choices' in data and data['choices']:
                                    delta = data['choices'][0].get('delta', {})
                                    content = delta.get('content', '')
                                    if content:
                                        yield content
                            except json.JSONDecodeError:
                                continue
            else:
                logger.error(f"Streaming failed: {response.status_code}")
                yield "Fehler beim Streaming der Antwort."
                
        except Exception as e:
            logger.error(f"Streaming error: {e}")
            yield f"Streaming-Fehler: {str(e)}"
    
    def _estimate_confidence(self, response_text: str) -> float:
        """
        Schätzt Konfidenz der generierten Antwort
        
        Args:
            response_text: Generierte Antwort
            
        Returns:
            Konfidenz-Score zwischen 0.0 und 1.0
        """
        # Einfache Heuristiken für Konfidenz-Schätzung
        confidence = 0.5  # Basis-Konfidenz
        
        # Länge der Antwort
        if len(response_text) > 200:
            confidence += 0.1
        elif len(response_text) < 50:
            confidence -= 0.2
        
        # Rechtliche Begriffe
        legal_terms = ['§', 'BGB', 'ZPO', 'Anspruch', 'Voraussetzung', 'Haftung']
        legal_term_count = sum(1 for term in legal_terms if term in response_text)
        confidence += min(0.3, legal_term_count * 0.05)
        
        # Strukturierung (Aufzählungen, etc.)
        if any(marker in response_text for marker in ['1.', '2.', 'a)', 'b)', '-']):
            confidence += 0.1
        
        # Unsicherheits-Indikatoren
        uncertainty_phrases = ['möglicherweise', 'eventuell', 'könnte', 'unsicher']
        uncertainty_count = sum(1 for phrase in uncertainty_phrases if phrase in response_text.lower())
        confidence -= min(0.2, uncertainty_count * 0.05)
        
        return max(0.0, min(1.0, confidence))


class RAGPipeline:
    """
    Retrieval-Augmented Generation Pipeline
    Kombiniert semantische Suche mit LLM-Generierung
    """
    
    def __init__(self, 
                 lm_studio_client: LMStudioClient,
                 prompt_templates: Optional[Dict[str, PromptTemplate]] = None):
        """
        Initialisiert RAG Pipeline
        
        Args:
            lm_studio_client: LM Studio Client
            prompt_templates: Prompt Templates für verschiedene Aufgaben
        """
        self.llm_client = lm_studio_client
        self.prompt_templates = prompt_templates or self._get_default_templates()
        
        logger.info("RAG Pipeline initialized")
    
    def _get_default_templates(self) -> Dict[str, PromptTemplate]:
        """Standard Prompt Templates"""
        return {
            'legal_qa': PromptTemplate(
                system_prompt="""Du bist ein spezialisierter KI-Assistent für deutsches Recht. 
                Deine Aufgabe ist es, basierend auf den bereitgestellten Rechtsgutachten präzise und fundierte Antworten zu geben.
                
                Beachte dabei:
                - Gib nur Informationen weiter, die in den bereitgestellten Quellen enthalten sind
                - Zitiere relevante Rechtsnormen korrekt
                - Strukturiere deine Antwort klar und verständlich
                - Kennzeichne Unsicherheiten oder fehlende Informationen
                - Verwende juristische Fachsprache angemessen""",
                
                user_template="""Basierend auf den folgenden Rechtsgutachten, beantworte bitte die Frage:

                FRAGE: {query}

                RELEVANTE GUTACHTEN:
                {context}

                Bitte gib eine strukturierte Antwort, die:
                1. Die rechtliche Einordnung erklärt
                2. Relevante Normen und Voraussetzungen nennt
                3. Das Ergebnis begründet
                4. Auf die spezifische Frage eingeht""",
                
                context_template="""[Gutachten {source_id}]
                Abschnitt: {section_type}
                Relevanz: {relevance_score:.2f}
                
                {text}
                
                ---"""
            ),
            
            'legal_summary': PromptTemplate(
                system_prompt="""Du bist ein KI-Assistent, der Rechtsgutachten zusammenfasst.
                Erstelle prägnante, strukturierte Zusammenfassungen der wichtigsten rechtlichen Aspekte.""",
                
                user_template="""Erstelle eine Zusammenfassung der folgenden Rechtsgutachten:

                {context}

                Die Zusammenfassung soll enthalten:
                - Zentrale Rechtsfragen
                - Angewandte Normen
                - Wichtigste Argumente
                - Ergebnisse""",
                
                context_template="""[Gutachten {source_id}]
                {text}
                ---"""
            )
        }
    
    def generate_answer(self, 
                       query: str, 
                       search_results: SearchResponse,
                       template_name: str = 'legal_qa',
                       max_context_tokens: int = 800) -> LLMResponse:
        """
        Generiert Antwort basierend auf Suchergebnissen
        
        Args:
            query: Benutzer-Frage
            search_results: Ergebnisse der semantischen Suche
            template_name: Name des zu verwendenden Templates
            max_context_tokens: Maximale Tokens für Kontext
            
        Returns:
            LLMResponse mit generierter Antwort
        """
        if template_name not in self.prompt_templates:
            raise ValueError(f"Unknown template: {template_name}")
        
        template = self.prompt_templates[template_name]
        
        # Kontext aus Suchergebnissen erstellen
        context = self._build_context(search_results.results, template, max_context_tokens)
        
        # Prompt zusammenstellen
        user_prompt = template.user_template.format(
            query=query,
            context=context
        )
        
        # LLM aufrufen
        llm_response = self.llm_client.generate_completion(
            prompt=user_prompt,
            system_prompt=template.system_prompt
        )
        
        # Response erweitern
        llm_response.sources_used = [r.source_gutachten_id for r in search_results.results[:5]]
        llm_response.legal_references = self._extract_legal_references(llm_response.response_text)
        llm_response.metadata.update({
            'query': query,
            'template_used': template_name,
            'context_tokens': len(context) // 4,  # Grobe Schätzung
            'search_results_used': len(search_results.results)
        })
        
        return llm_response
    
    def generate_streaming_answer(self, 
                                 query: str, 
                                 search_results: SearchResponse,
                                 template_name: str = 'legal_qa',
                                 max_context_tokens: int = 800) -> Generator[str, None, None]:
        """
        Generiert Streaming-Antwort basierend auf Suchergebnissen
        
        Args:
            query: Benutzer-Frage
            search_results: Ergebnisse der semantischen Suche
            template_name: Name des zu verwendenden Templates
            max_context_tokens: Maximale Tokens für Kontext
            
        Yields:
            Chunks der generierten Antwort
        """
        if template_name not in self.prompt_templates:
            yield f"Fehler: Unbekanntes Template '{template_name}'"
            return
        
        template = self.prompt_templates[template_name]
        
        # Kontext erstellen
        context = self._build_context(search_results.results, template, max_context_tokens)
        
        # Prompt zusammenstellen
        user_prompt = template.user_template.format(
            query=query,
            context=context
        )
        
        # Streaming-Antwort generieren
        yield from self.llm_client.generate_streaming_completion(
            prompt=user_prompt,
            system_prompt=template.system_prompt
        )
    
    def _build_context(self, 
                      search_results: List[SearchResult], 
                      template: PromptTemplate,
                      max_tokens: int) -> str:
        """
        Erstellt Kontext aus Suchergebnissen
        
        Args:
            search_results: Liste der Suchergebnisse
            template: Prompt Template
            max_tokens: Maximale Token-Anzahl
            
        Returns:
            Formatierter Kontext-String
        """
        context_parts = []
        current_tokens = 0
        
        for result in search_results:
            # Kontext-Teil formatieren
            context_part = template.context_template.format(
                source_id=result.source_gutachten_id,
                section_type=result.section_type or 'Unbekannt',
                relevance_score=result.relevance_score,
                text=result.text
            )
            
            # Token-Count schätzen (ca. 4 Zeichen pro Token)
            part_tokens = len(context_part) // 4
            
            if current_tokens + part_tokens > max_tokens:
                # Token-Limit erreicht
                break
            
            context_parts.append(context_part)
            current_tokens += part_tokens
        
        return '\n'.join(context_parts)
    
    def _extract_legal_references(self, text: str) -> List[str]:
        """Extrahiert Rechtsnormen aus der generierten Antwort"""
        import re
        
        patterns = [
            r'§§?\s*\d+(?:\s*[a-z])?\s*(?:Abs\.\s*\d+\s*)?(?:S\.\s*\d+\s*)?(?:BGB|ZPO|GBO|WEG|EuErbVO|GmbHG|AktG|HGB)',
            r'Art\.\s*\d+(?:\s*[a-z])?\s*(?:Abs\.\s*\d+\s*)?(?:EuErbVO|EGBGB)'
        ]
        
        references = []
        for pattern in patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            references.extend(matches)
        
        return list(set(references))  # Duplikate entfernen
    
    def add_custom_template(self, name: str, template: PromptTemplate):
        """Fügt ein benutzerdefiniertes Template hinzu"""
        self.prompt_templates[name] = template
        logger.info(f"Added custom template: {name}")
    
    def get_available_templates(self) -> List[str]:
        """Gibt verfügbare Template-Namen zurück"""
        return list(self.prompt_templates.keys())


class LegalQASystem:
    """
    Hauptklasse für Legal Question-Answering System
    Integriert Suche und LLM-Generierung
    """
    
    def __init__(self, 
                 search_engine,  # SemanticSearchEngine
                 lm_studio_client: Optional[LMStudioClient] = None,
                 config_path: Optional[Path] = None):
        """
        Initialisiert Legal QA System
        
        Args:
            search_engine: Semantic Search Engine
            lm_studio_client: LM Studio Client (optional, wird erstellt falls None)
            config_path: Pfad zur Konfigurationsdatei
        """
        self.search_engine = search_engine
        
        # LM Studio Client erstellen falls nicht übergeben
        if lm_studio_client is None:
            lm_studio_client = LMStudioClient()
        
        self.rag_pipeline = RAGPipeline(lm_studio_client)
        
        # Konfiguration laden
        if config_path and config_path.exists():
            with open(config_path, 'r', encoding='utf-8') as f:
                self.config = yaml.safe_load(f)
        else:
            self.config = self._get_default_config()
        
        logger.info("Legal QA System initialized")
    
    def answer_question(self, 
                       question: str,
                       search_params: Optional[Dict] = None,
                       streaming: bool = False) -> Union[LLMResponse, Generator[str, None, None]]:
        """
        Beantwortet eine rechtliche Frage
        
        Args:
            question: Rechtliche Frage
            search_params: Parameter für die Suche
            streaming: Ob Streaming-Antwort gewünscht
            
        Returns:
            LLMResponse oder Generator für Streaming
        """
        # Default Search-Parameter
        default_params = {
            'max_results': self.config.get('search', {}).get('max_results', 10),
            'min_similarity': self.config.get('search', {}).get('min_similarity', 0.6),
            'search_strategy': 'hybrid'
        }
        
        if search_params:
            default_params.update(search_params)
        
        # Semantische Suche durchführen
        search_results = self.search_engine.search(question, **default_params)
        
        if not search_results.results:
            if streaming:
                def no_results_stream():
                    yield "Entschuldigung, ich konnte keine relevanten Rechtsgutachten zu Ihrer Frage finden."
                return no_results_stream()
            else:
                return LLMResponse(
                    response_text="Entschuldigung, ich konnte keine relevanten Rechtsgutachten zu Ihrer Frage finden.",
                    confidence_score=0.0,
                    token_count=0,
                    processing_time_ms=0.0
                )
        
        # Antwort generieren
        if streaming:
            return self.rag_pipeline.generate_streaming_answer(
                query=question,
                search_results=search_results,
                template_name='legal_qa',
                max_context_tokens=self.config.get('llm', {}).get('max_context_tokens', 800)
            )
        else:
            return self.rag_pipeline.generate_answer(
                query=question,
                search_results=search_results,
                template_name='legal_qa',
                max_context_tokens=self.config.get('llm', {}).get('max_context_tokens', 800)
            )
    
    def summarize_topic(self, topic: str, max_gutachten: int = 5) -> LLMResponse:
        """
        Erstellt eine Zusammenfassung zu einem rechtlichen Thema
        
        Args:
            topic: Rechtliches Thema
            max_gutachten: Maximale Anzahl Gutachten
            
        Returns:
            LLMResponse mit Zusammenfassung
        """
        # Suche nach relevanten Gutachten
        search_results = self.search_engine.search(
            topic,
            max_results=max_gutachten,
            search_strategy='semantic'
        )
        
        # Zusammenfassung generieren
        return self.rag_pipeline.generate_answer(
            query=f"Erstelle eine Übersicht zum Thema: {topic}",
            search_results=search_results,
            template_name='legal_summary'
        )
    
    def _get_default_config(self) -> Dict:
        """Standard-Konfiguration"""
        return {
            'search': {
                'max_results': 10,
                'min_similarity': 0.6,
                'default_strategy': 'hybrid'
            },
            'llm': {
                'max_context_tokens': 800,
                'temperature': 0.1,
                'max_tokens': 1000
            }
        }
    
    async def generate_general_legal_response(self, 
                                             question: str,
                                             temperature: float = 0.1,
                                             max_tokens: int = 1000) -> LLMResponse:
        """
        Generiert eine allgemeine rechtliche Antwort ohne spezifischen Kontext
        
        Args:
            question: Rechtliche Frage
            temperature: Temperatur für Generierung
            max_tokens: Maximale Token-Anzahl
            
        Returns:
            LLMResponse mit Antwort
        """
        try:
            response = self.rag_pipeline.lm_client.generate_completion(
                prompt=question,
                temperature=temperature,
                max_tokens=max_tokens
            )
            
            return LLMResponse(
                response_text=response.response_text,
                confidence_score=response.confidence_score * 0.8,  # Lower confidence without context
                token_count=response.token_count,
                processing_time_ms=response.processing_time_ms,
                sources_used=[]
            )
            
        except Exception as e:
            logger.error(f"Error generating general legal response: {e}")
            return LLMResponse(
                response_text="Entschuldigung, es gab einen Fehler bei der Antwortgenerierung.",
                confidence_score=0.0,
                token_count=0,
                processing_time_ms=0.0,
                sources_used=[]
            )
    
    async def answer_question(self, 
                             question: str,
                             context_chunks: List[SearchResult],
                             temperature: float = 0.1,
                             max_tokens: int = 1000,
                             include_sources: bool = True) -> LLMResponse:
        """
        Async version of answer_question with context chunks
        
        Args:
            question: Rechtliche Frage
            context_chunks: Gefundene Kontext-Chunks
            temperature: Temperatur für Generierung
            max_tokens: Maximale Token-Anzahl
            include_sources: Ob Quellen eingeschlossen werden sollen
            
        Returns:
            LLMResponse mit Antwort
        """
        try:
            if not context_chunks:
                return await self.generate_general_legal_response(
                    question=question,
                    temperature=temperature,
                    max_tokens=max_tokens
                )
            
            # Create SearchResponse from chunks for compatibility
            from ..search.semantic_search import SearchResponse, SearchQuery
            search_response = SearchResponse(
                query=SearchQuery(text=question),
                results=context_chunks,
                total_found=len(context_chunks),
                search_time_ms=0,
                strategy_used="provided"
            )
            
            # Generate answer using RAG pipeline
            response = self.rag_pipeline.generate_answer(
                query=question,
                search_results=search_response,
                template_name='legal_qa',
                max_context_tokens=self.config.get('llm', {}).get('max_context_tokens', 800)
            )
            
            # Add metadata
            if hasattr(response, 'metadata'):
                response.metadata = response.metadata or {}
            else:
                response.metadata = {}
                
            response.metadata['legal_analysis'] = {
                'sources_count': len(context_chunks),
                'confidence_factors': {
                    'context_relevance': sum(chunk.similarity_score for chunk in context_chunks) / len(context_chunks),
                    'sources_diversity': len(set(chunk.source_gutachten_id for chunk in context_chunks))
                }
            }
            
            if include_sources:
                response.sources_used = [chunk.chunk_id for chunk in context_chunks]
            
            return response
            
        except Exception as e:
            logger.error(f"Error answering question: {e}")
            return LLMResponse(
                response_text="Entschuldigung, es gab einen Fehler bei der Antwortgenerierung.",
                confidence_score=0.0,
                token_count=0,
                processing_time_ms=0.0,
                sources_used=[]
            )
    
    async def explain_legal_concept(self, 
                                   concept: str,
                                   context_chunks: List[SearchResult],
                                   max_tokens: int = 800) -> LLMResponse:
        """
        Erklärt ein rechtliches Konzept basierend auf gefundenen Chunks
        
        Args:
            concept: Zu erklärendes Konzept
            context_chunks: Relevante Kontext-Chunks
            max_tokens: Maximale Token-Anzahl
            
        Returns:
            LLMResponse mit Erklärung
        """
        try:
            # Spezieller Prompt für Konzept-Erklärung
            explanation_prompt = f"""Erkläre das rechtliche Konzept '{concept}' basierend auf den folgenden Informationen:

Verwende eine klare, verständliche Sprache und strukturiere die Erklärung wie folgt:
1. Definition und Grundlagen
2. Rechtliche Grundlagen und Normen
3. Praktische Anwendung
4. Wichtige Aspekte oder Fallstricke

Kontext:"""
            
            # Context aus Chunks zusammenstellen
            context_text = ""
            for i, chunk in enumerate(context_chunks[:5]):  # Limit to 5 chunks
                context_text += f"\n\n--- Quelle {i+1} ---\n{chunk.text}"
            
            full_prompt = explanation_prompt + context_text + f"\n\nErkläre nun das Konzept '{concept}' präzise und verständlich:"
            
            response = self.rag_pipeline.lm_client.generate_completion(
                prompt=full_prompt,
                max_tokens=max_tokens,
                temperature=0.1
            )
            
            # Add metadata
            response.metadata = {
                'legal_analysis': {
                    'concept': concept,
                    'sources_used': len(context_chunks),
                    'explanation_type': 'concept_definition'
                }
            }
            
            return response
            
        except Exception as e:
            logger.error(f"Error explaining legal concept: {e}")
            return LLMResponse(
                response_text=f"Entschuldigung, ich konnte das Konzept '{concept}' nicht erklären.",
                confidence_score=0.0,
                token_count=0,
                processing_time_ms=0.0,
                sources_used=[]
            )
    
    async def summarize_legal_text(self, 
                                  text: str,
                                  summary_length: str = "medium",
                                  focus: str = "general") -> LLMResponse:
        """
        Erstellt eine Zusammenfassung eines rechtlichen Textes
        
        Args:
            text: Zu zusammenfassender Text
            summary_length: Länge der Zusammenfassung (short, medium, long)
            focus: Fokus der Zusammenfassung (general, legal_norms, key_points)
            
        Returns:
            LLMResponse mit Zusammenfassung
        """
        try:
            # Längen-Parameter bestimmen
            length_tokens = {
                "short": 150,
                "medium": 300,
                "long": 500
            }
            max_tokens = length_tokens.get(summary_length, 300)
            
            # Fokus-spezifische Prompts
            focus_prompts = {
                "general": "Erstelle eine allgemeine Zusammenfassung des folgenden rechtlichen Textes:",
                "legal_norms": "Erstelle eine Zusammenfassung mit Fokus auf die erwähnten Rechtsnormen und Gesetze:",
                "key_points": "Erstelle eine Zusammenfassung mit Fokus auf die wichtigsten rechtlichen Kernpunkte:"
            }
            
            prompt = focus_prompts.get(focus, focus_prompts["general"])
            full_prompt = f"""{prompt}

{text}

Zusammenfassung (ca. {summary_length})s:"""
            
            response = self.rag_pipeline.lm_client.generate_completion(
                prompt=full_prompt,
                max_tokens=max_tokens,
                temperature=0.1
            )
            
            # Add metadata
            response.metadata = {
                'legal_analysis': {
                    'summary_length': summary_length,
                    'focus': focus,
                    'original_text_length': len(text),
                    'compression_ratio': len(response.response_text) / len(text) if text else 0
                }
            }
            
            return response
            
        except Exception as e:
            logger.error(f"Error summarizing legal text: {e}")
            return LLMResponse(
                response_text="Entschuldigung, es gab einen Fehler bei der Textzusammenfassung.",
                confidence_score=0.0,
                token_count=0,
                processing_time_ms=0.0,
                sources_used=[]
            )
    
    async def compare_legal_cases(self, 
                                 cases_data: List[Dict[str, Any]],
                                 comparison_aspects: List[str]) -> Dict[str, Any]:
        """
        Vergleicht mehrere Rechtsfälle miteinander
        
        Args:
            cases_data: Liste von Fall-Daten
            comparison_aspects: Aspekte für den Vergleich
            
        Returns:
            Dict mit Vergleichsergebnissen
        """
        try:
            if len(cases_data) < 2:
                return {
                    "error": "Mindestens 2 Fälle zum Vergleich erforderlich",
                    "comparison": None
                }
            
            # Vergleichs-Prompt erstellen
            cases_text = ""
            for i, case in enumerate(cases_data):
                cases_text += f"\n\n--- Fall {i+1} (ID: {case.get('id', 'unknown')}) ---\n"
                cases_text += case.get('text', 'Kein Text verfügbar')
            
            aspects_text = ", ".join(comparison_aspects)
            
            comparison_prompt = f"""Vergleiche die folgenden Rechtsfälle unter besonderer Berücksichtigung von: {aspects_text}

{cases_text}

Erstelle einen strukturierten Vergleich mit:
1. Gemeinsamkeiten
2. Unterschiede
3. Rechtliche Bewertung
4. Fazit

Vergleich:"""
            
            response = self.rag_pipeline.lm_client.generate_completion(
                prompt=comparison_prompt,
                max_tokens=1000,
                temperature=0.1
            )
            
            return {
                "comparison_text": response.response_text,
                "cases_compared": len(cases_data),
                "comparison_aspects": comparison_aspects,
                "confidence_score": response.confidence_score,
                "processing_time_ms": response.processing_time_ms,
                "metadata": {
                    "legal_analysis": {
                        "comparison_type": "multi_case",
                        "aspects_analyzed": comparison_aspects,
                        "cases_count": len(cases_data)
                    }
                }
            }
            
        except Exception as e:
            logger.error(f"Error comparing legal cases: {e}")
            return {
                "error": f"Fehler beim Fallvergleich: {str(e)}",
                "comparison": None
            }

if __name__ == "__main__":
    # Test der LLM-Integration
    
    # LM Studio Client testen
    client = LMStudioClient()
    
    test_prompt = "Was sind die Voraussetzungen für einen Schadensersatzanspruch nach § 280 BGB?"
    
    # Einfache Completion testen
    response = client.generate_completion(test_prompt)
    
    print("LM Studio Test:")
    print(f"Response: {response.response_text}")
    print(f"Confidence: {response.confidence_score}")
    print(f"Tokens: {response.token_count}")
    print(f"Time: {response.processing_time_ms:.2f}ms")
    
    # RAG Pipeline testen (ohne echte Suchergebnisse)
    rag = RAGPipeline(client)
    templates = rag.get_available_templates()
    print(f"\nAvailable templates: {templates}")
    
    print("\nLLM Integration ready for use with Semantic Search Engine.")
