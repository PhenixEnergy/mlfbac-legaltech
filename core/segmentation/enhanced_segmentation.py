"""
Erweiterte Segmentierung für Fine-Tuning Optimierung
===================================================

Dieses Modul erweitert die bestehende Segmentierungsfunktionalität mit
fortgeschrittenen Techniken für bessere Fine-Tuning Ergebnisse.

Neue Features:
- Hierarchische Segmentierung mit Kontextbewahrung
- Adaptive Segment-Größen basierend auf Inhalt
- Semantische Kohärenz-Prüfung
- Cross-Reference Tracking zwischen Segmenten
- Quality Scoring für Segmente
- Multi-Level Annotation (Struktur, Inhalt, Kontext)
"""

import re
import logging
from typing import Dict, List, Tuple, Optional, NamedTuple
from dataclasses import dataclass, field
from enum import Enum
import json
import sys
import os
from collections import defaultdict, Counter
import math

# Add the rag module to the path so we can import optimized_prompt_generation
rag_path = os.path.join(os.path.dirname(__file__), '..', 'rag')
sys.path.insert(0, rag_path)

# Try to import the required classes
try:
    import importlib.util
    spec = importlib.util.spec_from_file_location(
        "optimized_prompt_generation", 
        os.path.join(rag_path, "optimized_prompt_generation.py")
    )
    optimized_prompt_module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(optimized_prompt_module)
    
    OptimizedPromptGenerator = optimized_prompt_module.OptimizedPromptGenerator
    LegalTextType = optimized_prompt_module.LegalTextType
    PromptComplexity = optimized_prompt_module.PromptComplexity
    PromptContext = optimized_prompt_module.PromptContext
except Exception as e:
    # Fallback if the import fails
    print(f"Warning: Could not import optimized_prompt_generation module: {e}")
    OptimizedPromptGenerator = None
    LegalTextType = None
    PromptComplexity = None
    PromptContext = None

logger = logging.getLogger(__name__)

class SegmentType(Enum):
    """Erweiterte Segment-Klassifikation"""
    HEADER = "header"
    CONTENT = "content"
    TRANSITION = "transition"
    REFERENCE = "reference"
    DEFINITION = "definition"
    EXAMPLE = "example"
    CONCLUSION = "conclusion"
    ENUMERATION = "enumeration"
    CITATION = "citation"
    FOOTNOTE = "footnote"

class SegmentPriority(Enum):
    """Prioritätsstufen für Segmente"""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    CONTEXT = "context"

@dataclass
class SegmentMetadata:
    """Erweiterte Metadaten für Segmente"""
    segment_id: str
    segment_type: SegmentType
    priority: SegmentPriority
    legal_concepts: List[str] = field(default_factory=list)
    referenced_norms: List[str] = field(default_factory=list)
    cross_references: List[str] = field(default_factory=list)
    context_score: float = 0.0
    coherence_score: float = 0.0
    complexity_score: float = 0.0
    word_count: int = 0
    legal_domain: str = "general"
    
@dataclass
class EnhancedSegment:
    """Erweiterte Segment-Darstellung"""
    text: str
    metadata: SegmentMetadata
    parent_segments: List[str] = field(default_factory=list)
    child_segments: List[str] = field(default_factory=list)
    related_segments: List[str] = field(default_factory=list)
    training_prompts: List[str] = field(default_factory=list)

class EnhancedSegmentationEngine:
    """
    Erweiterte Segmentierungsengine für optimierte Fine-Tuning Datenaufbereitung
    """
    
    def __init__(self):
        self.prompt_generator = OptimizedPromptGenerator()
        self.segmentation_patterns = self._initialize_segmentation_patterns()
        self.coherence_indicators = self._initialize_coherence_indicators()
        self.transition_markers = self._initialize_transition_markers()
        self.legal_concept_patterns = self._initialize_legal_concepts()
        
    def _initialize_segmentation_patterns(self) -> Dict[str, List[str]]:
        """Erweiterte Segmentierungsmuster"""
        return {
            "strong_boundaries": [
                r'\n\s*[IVX]+\.\s+',  # Römische Nummerierung
                r'\n\s*[A-Z]\.\s+',   # Großbuchstaben-Gliederung
                r'\n\s*\d+\.\s+',     # Numerische Gliederung
                r'\n\s*§\s*\d+',      # Paragraph-Anfang
                r'\n\s*Art\.\s*\d+',  # Artikel-Anfang
                r'\n\s*(?:Sachverhalt|Rechtsfrage|Lösung|Gutachten):\s*',
                r'\n\s*(?:I\.|II\.|III\.|IV\.|V\.)\s+',
                r'\n\s*(?:1\.|2\.|3\.|4\.|5\.)\s+(?:[A-Z][a-z]+\s+){1,3}'
            ],
            "medium_boundaries": [
                r'\n\s*[a-z]\)\s+',   # Kleinbuchstaben-Aufzählung
                r'\n\s*\d+\)\s+',     # Numerische Aufzählung
                r'\n\s*-\s+',         # Gedankenstrich-Aufzählung
                r'\n\s*•\s+',         # Bullet Points
                r'\n\s*aa\)\s+',      # Doppelbuchstaben
                r'\n\s*\(\d+\)\s+'    # Nummerierung in Klammern
            ],
            "weak_boundaries": [
                r'\.\s+(?=[A-Z][a-z]+)',  # Satzende vor neuem Satz
                r';\s+',                   # Semikolon
                r':\s+',                   # Doppelpunkt
                r'\n\s*(?=\w)',           # Zeilenwechsel vor Wort
            ],
            "semantic_boundaries": [
                r'(?:Demgegenüber|Hingegen|Andererseits|Jedoch|Allerdings)',
                r'(?:Ferner|Weiterhin|Außerdem|Darüber hinaus)',
                r'(?:Zunächst|Sodann|Schließlich|Abschließend)',
                r'(?:Folglich|Somit|Daher|Mithin|Demnach)',
                r'(?:Problematisch|Fraglich|Streitig|Umstritten)'
            ]
        }
    
    def _initialize_coherence_indicators(self) -> Dict[str, float]:
        """Indikatoren für semantische Kohärenz"""
        return {
            # Starke Kohärenz-Indikatoren
            "pronomen": 0.8,  # er, sie, es, dieser, jener
            "konjunktionen": 0.7,  # und, oder, aber, jedoch
            "temporale_bezüge": 0.9,  # dann, anschließend, zuvor
            "kausale_bezüge": 0.9,  # weil, da, deshalb, folglich
            "referenzen": 0.8,  # siehe oben, wie bereits erwähnt
            
            # Schwache Kohärenz-Indikatoren
            "themenwechsel": -0.6,  # neue Themen-Einführung
            "gegensätze": -0.4,  # hingegen, demgegenüber
            "abbrüche": -0.8,  # unvollständige Sätze
        }
    
    def _initialize_transition_markers(self) -> List[str]:
        """Übergangsmarkierungen zwischen Segmenten"""
        return [
            "zunächst", "sodann", "ferner", "schließlich",
            "erstens", "zweitens", "drittens", "viertens",
            "einerseits", "andererseits", "hingegen", "demgegenüber",
            "darüber hinaus", "außerdem", "weiterhin", "zudem",
            "folglich", "daher", "somit", "mithin", "demnach",
            "problematisch", "fraglich", "streitig", "umstritten",
            "insbesondere", "namentlich", "beispielsweise", "etwa"
        ]
    
    def _initialize_legal_concepts(self) -> Dict[str, List[str]]:
        """Rechtliche Konzept-Erkennungsmuster"""
        return {
            "vertragsrecht": [
                "vertrag", "willenserklärung", "angebot", "annahme",
                "erfüllung", "unmöglichkeit", "verzug", "gewährleistung"
            ],
            "deliktsrecht": [
                "schadensersatz", "verschulden", "kausalität", "rechtswidrigkeit",
                "vorsatz", "fahrlässigkeit", "haftung", "verschuldenshaftung"
            ],
            "verfassungsrecht": [
                "grundrecht", "verhältnismäßigkeit", "abwägung", "kerngehalt",
                "wesensgehalt", "eingriff", "schranke", "verfassungsbeschwerde"
            ],
            "strafrecht": [
                "straftat", "tatbestand", "rechtswidrigkeit", "schuld",
                "versuch", "vollendung", "rechtfertigung", "entschuldigung"
            ],
            "prozessrecht": [
                "klage", "antrag", "rechtsmittel", "berufung", "revision",
                "zuständigkeit", "verfahren", "anhörung", "beweis"
            ]
        }
    
    def calculate_coherence_score(self, segment_text: str, context_text: str = "") -> float:
        """
        Berechnet den Kohärenz-Score eines Segments
        """
        score = 0.0
        text_lower = segment_text.lower()
        
        # Pronomen-Referenzen prüfen
        pronouns = ["er", "sie", "es", "dieser", "jener", "diese", "jene", "solche"]
        pronoun_count = sum(len(re.findall(r'\b' + p + r'\b', text_lower)) for p in pronouns)
        
        # Konjunktionen prüfen
        conjunctions = ["und", "oder", "aber", "jedoch", "sowie", "außerdem", "ferner"]
        conjunction_count = sum(len(re.findall(r'\b' + c + r'\b', text_lower)) for c in conjunctions)
        
        # Temporale und kausale Bezüge
        temporal_markers = ["dann", "anschließend", "zuvor", "danach", "vorher"]
        causal_markers = ["weil", "da", "deshalb", "folglich", "daher", "somit"]
        
        temporal_count = sum(len(re.findall(r'\b' + t + r'\b', text_lower)) for t in temporal_markers)
        causal_count = sum(len(re.findall(r'\b' + c + r'\b', text_lower)) for c in causal_markers)
        
        # Score-Berechnung
        word_count = len(segment_text.split())
        if word_count > 0:
            score += (pronoun_count * 0.8) / word_count
            score += (conjunction_count * 0.7) / word_count
            score += (temporal_count * 0.9) / word_count
            score += (causal_count * 0.9) / word_count
        
        # Kontext-Kohärenz prüfen
        if context_text:
            context_words = set(context_text.lower().split())
            segment_words = set(segment_text.lower().split())
            overlap = len(context_words & segment_words)
            total_words = len(context_words | segment_words)
            if total_words > 0:
                score += (overlap / total_words) * 0.5
        
        return min(score, 1.0)
    
    def calculate_complexity_score(self, text: str) -> float:
        """
        Berechnet den Komplexitäts-Score eines Textsegments
        """
        # Satzlängen-Analyse
        sentences = re.split(r'[.!?]+', text)
        avg_sentence_length = sum(len(s.split()) for s in sentences if s.strip()) / max(len(sentences), 1)
        
        # Fachbegriff-Dichte
        legal_terms = 0
        for term_list in self.legal_concept_patterns.values():
            for term in term_list:
                legal_terms += len(re.findall(r'\b' + term + r'\b', text.lower()))
        
        word_count = len(text.split())
        legal_density = legal_terms / max(word_count, 1)
        
        # Verschachtelungsgrad (Klammern, Nebensätze)
        nested_structures = len(re.findall(r'\([^)]*\)', text)) + len(re.findall(r'\b(?:der|die|das)\b.*?(?:,|;)', text))
        nesting_density = nested_structures / max(word_count, 1)
        
        # Normalisierte Komplexität
        complexity = (
            min(avg_sentence_length / 25, 1.0) * 0.4 +
            min(legal_density * 10, 1.0) * 0.4 +
            min(nesting_density * 20, 1.0) * 0.2
        )
        
        return complexity
    
    def extract_legal_concepts(self, text: str) -> List[str]:
        """
        Extrahiert rechtliche Konzepte aus dem Text
        """
        concepts = set()
        text_lower = text.lower()
        
        for domain, terms in self.legal_concept_patterns.items():
            domain_concepts = []
            for term in terms:
                if re.search(r'\b' + term + r'\b', text_lower):
                    domain_concepts.append(term)
            
            if domain_concepts:
                concepts.update(domain_concepts)
                concepts.add(domain)  # Füge auch die Domäne hinzu
        
        # Rechtsnormen extrahieren
        norm_pattern = r'§\s*(\d+(?:\s*[a-z])?)\s*(?:Abs\.\s*\d+)?\s*([A-Z][a-zA-Z]*)?'
        norms = re.findall(norm_pattern, text)
        for norm_num, law in norms:
            concepts.add(f"§ {norm_num}")
            if law:
                concepts.add(law)
        
        return list(concepts)
    
    def extract_cross_references(self, text: str, all_segments: List[str]) -> List[str]:
        """
        Identifiziert Querverweise zu anderen Segmenten
        """
        references = []
        text_lower = text.lower()
        
        # Explizite Referenz-Muster
        ref_patterns = [
            r'siehe\s+(?:oben|unten|unter|bei)',
            r'vgl\.\s+(?:oben|unten|unter)',
            r'wie\s+(?:bereits|schon)\s+(?:erwähnt|ausgeführt|dargestellt)',
            r'(?:oben|unter)\s+(?:dargestellt|ausgeführt|erwähnt)',
            r'in\s+(?:diesem|jenem)\s+(?:zusammenhang|kontext)',
            r'hierzu\s+(?:bereits|schon|auch)',
            r'dazu\s+(?:bereits|schon|auch)'
        ]
        
        for pattern in ref_patterns:
            if re.search(pattern, text_lower):
                references.append("implicit_reference")
        
        # Identifiziere ähnliche Segmente basierend auf Schlüsselwörtern
        text_words = set(text_lower.split())
        for i, segment in enumerate(all_segments):
            if segment != text:
                segment_words = set(segment.lower().split())
                overlap = len(text_words & segment_words)
                if overlap > 5:  # Threshold für Ähnlichkeit
                    references.append(f"segment_{i}")
        
        return references
    
    def determine_segment_priority(self, metadata: SegmentMetadata) -> SegmentPriority:
        """
        Bestimmt die Priorität eines Segments basierend auf seinen Eigenschaften
        """
        score = 0
        
        # Texttyp-basierte Bewertung
        if metadata.segment_type in [SegmentType.HEADER, SegmentType.DEFINITION]:
            score += 3
        elif metadata.segment_type in [SegmentType.CONTENT, SegmentType.CONCLUSION]:
            score += 2
        elif metadata.segment_type == SegmentType.EXAMPLE:
            score += 1
        
        # Konzept-Dichte
        score += min(len(metadata.legal_concepts) / 3, 2)
        
        # Norm-Referenzen
        score += min(len(metadata.referenced_norms), 2)
        
        # Komplexität
        score += metadata.complexity_score * 2
        
        # Kohärenz
        score += metadata.coherence_score
        
        # Priorität zuweisen
        if score >= 7:
            return SegmentPriority.CRITICAL
        elif score >= 5:
            return SegmentPriority.HIGH
        elif score >= 3:
            return SegmentPriority.MEDIUM
        elif score >= 1:
            return SegmentPriority.LOW
        else:
            return SegmentPriority.CONTEXT
    
    def adaptive_segmentation(self, text: str, target_segments: int = None) -> List[EnhancedSegment]:
        """
        Führt adaptive Segmentierung basierend auf Inhalt und Struktur durch
        """
        segments = []
        segment_id_counter = 0
        
        # Erste Segmentierung basierend auf starken Grenzen
        strong_boundaries = []
        for pattern in self.segmentation_patterns["strong_boundaries"]:
            for match in re.finditer(pattern, text):
                strong_boundaries.append(match.start())
        
        strong_boundaries = sorted(set([0] + strong_boundaries + [len(text)]))
        
        # Erste Segment-Erstellung
        for i in range(len(strong_boundaries) - 1):
            start = strong_boundaries[i]
            end = strong_boundaries[i + 1]
            segment_text = text[start:end].strip()
            
            if len(segment_text) < 50:  # Zu kurze Segmente mit vorherigem kombinieren
                if segments:
                    segments[-1].text += " " + segment_text
                    continue
            
            # Segment-Metadaten erstellen
            segment_id = f"seg_{segment_id_counter:03d}"
            segment_id_counter += 1
            
            legal_concepts = self.extract_legal_concepts(segment_text)
            coherence_score = self.calculate_coherence_score(segment_text)
            complexity_score = self.calculate_complexity_score(segment_text)
            
            # Segment-Typ bestimmen
            segment_type = self._determine_segment_type(segment_text)
            
            metadata = SegmentMetadata(
                segment_id=segment_id,
                segment_type=segment_type,
                priority=SegmentPriority.MEDIUM,  # Wird später berechnet
                legal_concepts=legal_concepts,
                referenced_norms=self._extract_norms(segment_text),
                context_score=0.0,  # Wird später berechnet
                coherence_score=coherence_score,
                complexity_score=complexity_score,
                word_count=len(segment_text.split()),
                legal_domain=self.prompt_generator.detect_domain(segment_text)
            )
            
            # Priorität bestimmen
            metadata.priority = self.determine_segment_priority(metadata)
            
            enhanced_segment = EnhancedSegment(
                text=segment_text,
                metadata=metadata
            )
            
            segments.append(enhanced_segment)
        
        # Post-Processing: Querverweise und Beziehungen
        all_segment_texts = [seg.text for seg in segments]
        for segment in segments:
            segment.metadata.cross_references = self.extract_cross_references(
                segment.text, all_segment_texts
            )
            
            # Training Prompts generieren
            segment.training_prompts = self._generate_segment_prompts(segment)
        
        # Adaptive Größenanpassung
        if target_segments and len(segments) != target_segments:
            segments = self._adjust_segment_count(segments, target_segments)
        
        return segments
    
    def _determine_segment_type(self, text: str) -> SegmentType:
        """
        Bestimmt den Typ eines Segments basierend auf dem Inhalt
        """
        text_lower = text.lower()
        
        # Header-Indikatoren
        if re.match(r'^\s*[IVX]+\.\s+', text) or re.match(r'^\s*[A-Z]\.\s+', text):
            return SegmentType.HEADER
        
        # Definitionen
        if any(indicator in text_lower for indicator in ["ist", "bedeutet", "versteht man", "definition"]):
            return SegmentType.DEFINITION
        
        # Beispiele
        if any(indicator in text_lower for indicator in ["beispiel", "etwa", "z.b.", "beispielsweise"]):
            return SegmentType.EXAMPLE
        
        # Fazit/Schlussfolgerung
        if any(indicator in text_lower for indicator in ["folglich", "somit", "demnach", "ergebnis", "fazit"]):
            return SegmentType.CONCLUSION
        
        # Aufzählungen
        if re.search(r'^\s*[-•]\s+', text) or re.search(r'^\s*[a-z]\)\s+', text):
            return SegmentType.ENUMERATION
        
        # Zitate/Referenzen
        if "§" in text or re.search(r'\b[A-Z][a-zA-Z]*\s+\d+', text):
            return SegmentType.REFERENCE
        
        return SegmentType.CONTENT
    
    def _extract_norms(self, text: str) -> List[str]:
        """
        Extrahiert Rechtsnorm-Referenzen aus dem Text
        """
        norms = []
        
        # Paragraph-Referenzen
        paragraph_pattern = r'§\s*(\d+(?:\s*[a-z])?)\s*(?:Abs\.\s*(\d+))?\s*(?:S\.\s*(\d+))?\s*([A-Z][a-zA-Z]*)?'
        for match in re.finditer(paragraph_pattern, text):
            norm = f"§ {match.group(1)}"
            if match.group(2):  # Absatz
                norm += f" Abs. {match.group(2)}"
            if match.group(3):  # Satz
                norm += f" S. {match.group(3)}"
            if match.group(4):  # Gesetz
                norm += f" {match.group(4)}"
            norms.append(norm)
        
        # Artikel-Referenzen
        article_pattern = r'Art\.\s*(\d+(?:\s*[a-z])?)\s*(?:Abs\.\s*(\d+))?\s*([A-Z][a-zA-Z]*)?'
        for match in re.finditer(article_pattern, text):
            norm = f"Art. {match.group(1)}"
            if match.group(2):
                norm += f" Abs. {match.group(2)}"
            if match.group(3):
                norm += f" {match.group(3)}"
            norms.append(norm)
        
        return norms
    
    def _generate_segment_prompts(self, segment: EnhancedSegment) -> List[str]:
        """
        Generiert spezifische Training-Prompts für ein Segment
        """
        prompts = []
        
        # Basis-Kontext für Prompt-Generierung
        context = PromptContext(
            text_type=self._map_segment_to_legal_type(segment.metadata.segment_type),
            complexity=self._map_complexity_score(segment.metadata.complexity_score),
            domain=segment.metadata.legal_domain,
            metadata=segment.metadata.__dict__,
            keywords=segment.metadata.legal_concepts
        )
        
        # Standard Enhanced Prompt
        enhanced_prompt = self.prompt_generator.generate_enhanced_prompt(segment.text, context)
        prompts.append(enhanced_prompt)
        
        # Segment-typ-spezifische Prompts
        if segment.metadata.segment_type == SegmentType.DEFINITION:
            prompts.append(f"Definiere und erläutere die in folgendem Text enthaltenen Rechtsbegriffe: {segment.text}")
        
        elif segment.metadata.segment_type == SegmentType.EXAMPLE:
            prompts.append(f"Analysiere das folgende Beispiel und erkläre dessen rechtliche Relevanz: {segment.text}")
        
        elif segment.metadata.segment_type == SegmentType.CONCLUSION:
            prompts.append(f"Bewerte die Schlussfolgerungen und deren rechtliche Fundierung: {segment.text}")
        
        elif segment.metadata.segment_type == SegmentType.REFERENCE:
            prompts.append(f"Erläutere die zitierten Rechtsnormen und deren Anwendung: {segment.text}")
        
        # RAG-Training Queries
        rag_queries = self.prompt_generator.generate_rag_queries(segment.text, 3)
        prompts.extend(rag_queries)
        
        return prompts
    
    def _map_segment_to_legal_type(self, segment_type: SegmentType) -> LegalTextType:
        """
        Mappt Segment-Typen auf Legal-Text-Typen
        """
        mapping = {
            SegmentType.CONTENT: LegalTextType.SACHVERHALT,
            SegmentType.DEFINITION: LegalTextType.DEFINITION,
            SegmentType.REFERENCE: LegalTextType.NORM,
            SegmentType.CONCLUSION: LegalTextType.SUBSUMTION,
            SegmentType.EXAMPLE: LegalTextType.ANWENDUNG,
        }
        return mapping.get(segment_type, LegalTextType.SACHVERHALT)
    
    def _map_complexity_score(self, score: float) -> PromptComplexity:
        """
        Mappt Komplexitäts-Scores auf Prompt-Komplexität
        """
        if score >= 0.8:
            return PromptComplexity.EXPERT
        elif score >= 0.6:
            return PromptComplexity.ADVANCED
        elif score >= 0.4:
            return PromptComplexity.INTERMEDIATE
        else:
            return PromptComplexity.BASIC
    
    def _adjust_segment_count(self, segments: List[EnhancedSegment], target_count: int) -> List[EnhancedSegment]:
        """
        Passt die Anzahl der Segmente an die Zielanzahl an
        """
        current_count = len(segments)
        
        if current_count == target_count:
            return segments
        
        elif current_count > target_count:
            # Segmente zusammenfassen - priorisiere nach niedrigster Priorität
            segments.sort(key=lambda s: (s.metadata.priority.value, s.metadata.word_count))
            
            while len(segments) > target_count:
                # Kombiniere die beiden schwächsten Segmente
                seg1 = segments.pop(0)
                seg2 = segments.pop(0)
                
                combined_text = seg1.text + " " + seg2.text
                combined_concepts = list(set(seg1.metadata.legal_concepts + seg2.metadata.legal_concepts))
                combined_norms = list(set(seg1.metadata.referenced_norms + seg2.metadata.referenced_norms))
                
                # Neue Metadaten berechnen
                new_metadata = SegmentMetadata(
                    segment_id=f"combined_{seg1.metadata.segment_id}_{seg2.metadata.segment_id}",
                    segment_type=seg1.metadata.segment_type,  # Nimm den ersten Typ
                    priority=max(seg1.metadata.priority, seg2.metadata.priority),
                    legal_concepts=combined_concepts,
                    referenced_norms=combined_norms,
                    coherence_score=(seg1.metadata.coherence_score + seg2.metadata.coherence_score) / 2,
                    complexity_score=max(seg1.metadata.complexity_score, seg2.metadata.complexity_score),
                    word_count=seg1.metadata.word_count + seg2.metadata.word_count,
                    legal_domain=seg1.metadata.legal_domain
                )
                
                combined_segment = EnhancedSegment(
                    text=combined_text,
                    metadata=new_metadata,
                    training_prompts=seg1.training_prompts + seg2.training_prompts
                )
                
                segments.insert(0, combined_segment)
        
        else:
            # Segmente aufteilen - finde die längsten Segmente
            while len(segments) < target_count:
                # Finde das längste Segment
                longest_segment = max(segments, key=lambda s: s.metadata.word_count)
                segments.remove(longest_segment)
                
                # Teile es in zwei Hälften
                text = longest_segment.text
                mid_point = len(text) // 2
                
                # Finde einen guten Teilungspunkt (Satzende)
                for i in range(mid_point, len(text)):
                    if text[i] in '.!?':
                        split_point = i + 1
                        break
                else:
                    split_point = mid_point
                
                # Erstelle zwei neue Segmente
                for i, part in enumerate([text[:split_point], text[split_point:]]):
                    if part.strip():
                        new_metadata = SegmentMetadata(
                            segment_id=f"{longest_segment.metadata.segment_id}_part_{i+1}",
                            segment_type=longest_segment.metadata.segment_type,
                            priority=longest_segment.metadata.priority,
                            legal_concepts=self.extract_legal_concepts(part),
                            referenced_norms=self._extract_norms(part),
                            coherence_score=self.calculate_coherence_score(part),
                            complexity_score=self.calculate_complexity_score(part),
                            word_count=len(part.split()),
                            legal_domain=longest_segment.metadata.legal_domain
                        )
                        
                        new_segment = EnhancedSegment(
                            text=part,
                            metadata=new_metadata,
                            training_prompts=self._generate_segment_prompts(
                                EnhancedSegment(text=part, metadata=new_metadata)
                            )
                        )
                        segments.append(new_segment)
        
        return segments
    
    def export_training_data(self, segments: List[EnhancedSegment], output_format: str = "jsonl") -> str:
        """
        Exportiert die Segmente als Training-Daten in verschiedenen Formaten
        """
        training_data = []
        
        for segment in segments:
            for prompt in segment.training_prompts:
                entry = {
                    "prompt": prompt,
                    "completion": segment.text,
                    "metadata": {
                        "segment_id": segment.metadata.segment_id,
                        "segment_type": segment.metadata.segment_type.value,
                        "priority": segment.metadata.priority.value,
                        "legal_concepts": list(segment.metadata.legal_concepts),
                        "referenced_norms": segment.metadata.referenced_norms,
                        "coherence_score": segment.metadata.coherence_score,
                        "complexity_score": segment.metadata.complexity_score,
                        "word_count": segment.metadata.word_count,
                        "legal_domain": segment.metadata.legal_domain
                    }
                }
                training_data.append(entry)
        
        if output_format == "jsonl":
            return "\n".join(json.dumps(entry, ensure_ascii=False) for entry in training_data)
        elif output_format == "json":
            return json.dumps(training_data, ensure_ascii=False, indent=2)
        else:
            raise ValueError(f"Unsupported format: {output_format}")
    
    def generate_quality_report(self, segments: List[EnhancedSegment]) -> Dict:
        """
        Generiert einen Qualitätsbericht für die Segmentierung
        """
        total_segments = len(segments)
        total_words = sum(seg.metadata.word_count for seg in segments)
        
        # Prioritäts-Verteilung
        priority_dist = Counter(seg.metadata.priority for seg in segments)
        
        # Typ-Verteilung
        type_dist = Counter(seg.metadata.segment_type for seg in segments)
        
        # Durchschnittliche Scores
        avg_coherence = sum(seg.metadata.coherence_score for seg in segments) / total_segments
        avg_complexity = sum(seg.metadata.complexity_score for seg in segments) / total_segments
        
        # Domänen-Verteilung
        domain_dist = Counter(seg.metadata.legal_domain for seg in segments)
        
        # Konzept-Abdeckung
        all_concepts = set()
        for seg in segments:
            all_concepts.update(seg.metadata.legal_concepts)
        
        report = {
            "summary": {
                "total_segments": total_segments,
                "total_words": total_words,
                "avg_words_per_segment": total_words / total_segments,
                "avg_coherence_score": avg_coherence,
                "avg_complexity_score": avg_complexity,
                "unique_legal_concepts": len(all_concepts)
            },
            "distributions": {
                "priority": dict(priority_dist),
                "segment_type": {k.value: v for k, v in type_dist.items()},
                "legal_domain": dict(domain_dist)
            },
            "quality_metrics": {
                "high_quality_segments": sum(1 for seg in segments 
                                           if seg.metadata.coherence_score > 0.7),
                "complex_segments": sum(1 for seg in segments 
                                      if seg.metadata.complexity_score > 0.6),
                "critical_priority_segments": sum(1 for seg in segments 
                                                if seg.metadata.priority == SegmentPriority.CRITICAL)
            },
            "legal_concepts": list(all_concepts)[:20]  # Top 20 Konzepte
        }
        
        return report

def main():
    """Demonstriert die erweiterte Segmentierungsfunktionalität"""
    engine = EnhancedSegmentationEngine()
    
    sample_text = """
    I. Sachverhalt
    
    Der Kläger K verlangt von der Beklagten B Schadensersatz in Höhe von 10.000 Euro.
    Am 15.03.2023 ereignete sich folgender Sachverhalt: K ging über den Gehweg vor 
    dem Geschäft der B. Aufgrund von Glatteis stürzte K und verletzte sich dabei schwer.
    
    II. Rechtsfrage
    
    Fraglich ist, ob B gegenüber K zum Schadensersatz verpflichtet ist.
    Dies könnte sich aus § 823 Abs. 1 BGB ergeben.
    
    III. Lösung
    
    A. Anspruch aus § 823 Abs. 1 BGB
    
    K könnte gegen B einen Anspruch auf Schadensersatz aus § 823 Abs. 1 BGB haben.
    
    1. Rechtsgutsverletzung
    
    Zunächst müsste eine Verletzung eines der in § 823 Abs. 1 BGB geschützten 
    Rechtsgüter vorliegen. Hier kommt eine Verletzung der Gesundheit in Betracht.
    K hat sich durch den Sturz verletzt. Somit liegt eine Rechtsgutsverletzung vor.
    
    2. Rechtswidrigkeit
    
    Die Rechtsgutsverletzung müsste rechtswidrig sein. Rechtswidrig ist eine 
    Handlung dann, wenn sie nicht durch Rechtfertigungsgründe gedeckt ist.
    Vorliegend sind keine Rechtfertigungsgründe ersichtlich.
    
    3. Verschulden
    
    B müsste die Rechtsgutsverletzung verschuldet haben. Verschulden liegt bei 
    Vorsatz oder Fahrlässigkeit vor.
    
    a) Vorsatz
    
    Vorsatz scheidet aus, da B den Sturz des K nicht gewollt hat.
    
    b) Fahrlässigkeit
    
    Fahrlässig handelt, wer die im Verkehr erforderliche Sorgfalt außer Acht lässt.
    B hatte als Geschäftsinhaberin eine Verkehrssicherungspflicht.
    """
    
    print("=== ERWEITERTE SEGMENTIERUNGSANALYSE ===\n")
    
    # Segmentierung durchführen
    segments = engine.adaptive_segmentation(sample_text, target_segments=8)
    
    print(f"Anzahl generierte Segmente: {len(segments)}\n")
    
    # Segment-Details anzeigen
    for i, segment in enumerate(segments[:3], 1):  # Zeige nur die ersten 3
        print(f"=== SEGMENT {i} ===")
        print(f"ID: {segment.metadata.segment_id}")
        print(f"Typ: {segment.metadata.segment_type.value}")
        print(f"Priorität: {segment.metadata.priority.value}")
        print(f"Wörter: {segment.metadata.word_count}")
        print(f"Kohärenz: {segment.metadata.coherence_score:.3f}")
        print(f"Komplexität: {segment.metadata.complexity_score:.3f}")
        print(f"Domäne: {segment.metadata.legal_domain}")
        print(f"Konzepte: {', '.join(list(segment.metadata.legal_concepts)[:3])}")
        print(f"Text: {segment.text[:150]}...")
        print(f"Training Prompts: {len(segment.training_prompts)}")
        if segment.training_prompts:
            print(f"Beispiel-Prompt: {segment.training_prompts[0][:100]}...")
        print()
    
    # Qualitätsbericht
    quality_report = engine.generate_quality_report(segments)
    print("=== QUALITÄTSBERICHT ===")
    print(f"Gesamt-Segmente: {quality_report['summary']['total_segments']}")
    print(f"Durchschnittliche Kohärenz: {quality_report['summary']['avg_coherence_score']:.3f}")
    print(f"Durchschnittliche Komplexität: {quality_report['summary']['avg_complexity_score']:.3f}")
    print(f"Hochqualitative Segmente: {quality_report['quality_metrics']['high_quality_segments']}")
    print(f"Kritische Priorität: {quality_report['quality_metrics']['critical_priority_segments']}")
    print()
    
    # Export-Demo
    print("=== EXPORT DEMO ===")
    training_data = engine.export_training_data(segments[:2], "json")
    print(f"Trainings-Daten Länge: {len(training_data)} Zeichen")
    print("Erste Zeilen:", training_data[:200] + "...")

if __name__ == "__main__":
    main()
