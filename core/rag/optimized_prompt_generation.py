"""
Optimierte Prompt-Generierung für RAG Training und Fine-Tuning Segmentierung
===========================================================================

Dieses Modul enthält verbesserte Methodiken für die Prompt-Generierung in der
LegalTech NLP Pipeline, optimiert für sowohl RAG Training als auch Fine-Tuning
Segmentierung.

Hauptverbesserungen:
- Erweiterte kontextuelle Prompt-Templates (100+ Varianten)
- Adaptive Prompt-Generierung basierend auf Texttyp und Komplexität
- Verbessertes Semantic Weighting für bessere Segmentierung
- Multi-Strategie Query Generation für RAG Training
- Hierarchische Prompt-Strukturierung
- Domain-spezifische Prompt-Anpassung
"""

import re
import random
import logging
from typing import Dict, List, Tuple, Optional
from enum import Enum
from dataclasses import dataclass
from collections import defaultdict
import json

# Logging Setup
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class LegalTextType(Enum):
    """Erweiterte Klassifikation von Rechtstexttypen"""
    SACHVERHALT = "sachverhalt"
    RECHTSFRAGE = "rechtsfrage"
    SUBSUMTION = "subsumtion"
    URTEIL = "urteil"
    NORM = "norm"
    DEFINITION = "definition"
    KOMMENTAR = "kommentar"
    LITERATUR = "literatur"
    RECHTSPRECHUNG = "rechtsprechung"
    VERFAHREN = "verfahren"
    ARGUMENTATION = "argumentation"
    BEWEISWUERDIGUNG = "beweiswuerdigung"
    RECHTSFOLGE = "rechtsfolge"
    AUSLEGUNG = "auslegung"
    ANWENDUNG = "anwendung"

class PromptComplexity(Enum):
    """Komplexitätsstufen für Prompt-Generierung"""
    BASIC = "basic"
    INTERMEDIATE = "intermediate"
    ADVANCED = "advanced"
    EXPERT = "expert"

@dataclass
class PromptContext:
    """Kontextuelle Informationen für Prompt-Generierung"""
    text_type: LegalTextType
    complexity: PromptComplexity
    domain: str
    metadata: Dict
    previous_context: Optional[str] = None
    legal_norms: List[str] = None
    keywords: List[str] = None

class OptimizedPromptGenerator:
    """
    Optimierte Klasse für die Generierung von Prompts für verschiedene
    Anwendungsfälle im LegalTech NLP Bereich
    """
    
    def __init__(self):
        self.base_templates = self._initialize_base_templates()
        self.rag_templates = self._initialize_rag_templates()
        self.semantic_weights = self._initialize_semantic_weights()
        self.domain_patterns = self._initialize_domain_patterns()
        self.complexity_modifiers = self._initialize_complexity_modifiers()
        
    def _initialize_base_templates(self) -> Dict[LegalTextType, List[str]]:
        """Initialisiert erweiterte Basis-Templates für verschiedene Texttypen"""
        return {
            LegalTextType.SACHVERHALT: [
                "Analysiere den folgenden Sachverhalt und identifiziere die rechtlich relevanten Tatsachen: {text}",
                "Extrahiere aus dem Sachverhalt die wesentlichen rechtlichen Aspekte: {text}",
                "Strukturiere den vorliegenden Sachverhalt nach rechtlichen Gesichtspunkten: {text}",
                "Identifiziere in dem Sachverhalt die entscheidungserheblichen Tatsachen: {text}",
                "Kategorisiere die rechtlich relevanten Elemente des Sachverhalts: {text}",
                "Bewerte die rechtliche Bedeutung der im Sachverhalt genannten Tatsachen: {text}",
                "Ordne den Sachverhalt systematisch nach rechtlichen Kategorien: {text}",
                "Analysiere die Kausalzusammenhänge im vorliegenden Sachverhalt: {text}",
                "Identifiziere potentielle Streitpunkte im gegebenen Sachverhalt: {text}",
                "Strukturiere den Sachverhalt chronologisch und rechtlich: {text}"
            ],
            LegalTextType.RECHTSFRAGE: [
                "Formuliere die zentrale Rechtsfrage basierend auf dem Text: {text}",
                "Identifiziere die zu klärenden Rechtsprobleme in: {text}",
                "Bestimme die rechtlichen Kernfragen des folgenden Textes: {text}",
                "Extrahiere die streitigen Rechtsfragen aus: {text}",
                "Analysiere die rechtsdogmatischen Fragen in: {text}",
                "Definiere die zu prüfenden Rechtsfragen anhand von: {text}",
                "Systematisiere die Rechtsprobleme in dem Text: {text}",
                "Hierarchisiere die Rechtsfragen nach ihrer Bedeutung: {text}",
                "Kategorisiere die verschiedenen Rechtsfragen in: {text}",
                "Konkretisiere die abstrakten Rechtsfragen aus: {text}"
            ],
            LegalTextType.SUBSUMTION: [
                "Führe eine detaillierte Subsumtion für den folgenden Text durch: {text}",
                "Prüfe systematisch die Tatbestandsmerkmale in: {text}",
                "Subsumiere die Tatsachen unter die einschlägigen Normen: {text}",
                "Analysiere die Subsumtion der rechtlich relevanten Tatsachen: {text}",
                "Überprüfe die Tatbestandserfüllung anhand von: {text}",
                "Wende die Subsumtionstechnik auf den folgenden Text an: {text}",
                "Strukturiere die Subsumtion nach dem Gutachtenstil: {text}",
                "Prüfe schrittweise die Tatbestandsmerkmale in: {text}",
                "Analysiere die Norm-Tatsachen-Zuordnung in: {text}",
                "Bewerte die Subsumtionsergebnisse in: {text}"
            ],
            LegalTextType.URTEIL: [
                "Analysiere die Urteilsstruktur und zentrale Entscheidungsgründe: {text}",
                "Extrahiere die Leitsätze und Kernaussagen des Urteils: {text}",
                "Systematisiere die Urteilsbegründung nach rechtlichen Aspekten: {text}",
                "Identifiziere die tragenden Gründe der Entscheidung: {text}",
                "Analysiere die Rechtsprechungslinie des Urteils: {text}",
                "Strukturiere die Urteilsargumentation systematisch: {text}",
                "Bewerte die rechtliche Überzeugungskraft des Urteils: {text}",
                "Kategorisiere die verschiedenen Urteilsaspekte: {text}",
                "Analysiere die Präzedenzwirkung der Entscheidung: {text}",
                "Identifiziere innovative Rechtsfortbildung im Urteil: {text}"
            ],
            LegalTextType.NORM: [
                "Analysiere den normativen Gehalt und die Anwendbarkeit: {text}",
                "Interpretiere die Rechtsnorm systematisch: {text}",
                "Bestimme den Regelungsbereich der Norm: {text}",
                "Analysiere die Tatbestandsmerkmale der Rechtsnorm: {text}",
                "Prüfe die Auslegung und Anwendung der Norm: {text}",
                "Systematisiere die Normstruktur und Rechtsfolgen: {text}",
                "Bewerte die praktische Relevanz der Rechtsnorm: {text}",
                "Analysiere Normkonflikte und Konkurrenzfragen: {text}",
                "Interpretiere unbestimmte Rechtsbegriffe in: {text}",
                "Prüfe die Verfassungskonformität der Norm: {text}"
            ]
        }
    
    def _initialize_rag_templates(self) -> Dict[str, List[str]]:
        """Initialisiert spezialisierte Templates für RAG Training"""
        return {
            "query_generation": [
                "Was besagt {concept} im Kontext von {domain}?",
                "Wie wird {concept} in der Rechtsprechung zu {domain} angewendet?",
                "Welche Voraussetzungen gelten für {concept} im Bereich {domain}?",
                "Erläutere die praktische Bedeutung von {concept} in {domain}",
                "Wie hat sich {concept} in der {domain}-Rechtsprechung entwickelt?",
                "Welche Probleme entstehen bei der Anwendung von {concept} in {domain}?",
                "Definiere {concept} im juristischen Kontext von {domain}",
                "Welche Ausnahmen gibt es bei {concept} im {domain}-Recht?",
                "Wie unterscheidet sich {concept} in verschiedenen {domain}-Bereichen?",
                "Welche Reformbestrebungen gibt es bezüglich {concept} in {domain}?"
            ],
            "context_enhancement": [
                "Im Zusammenhang mit {previous_context}, erläutere {current_topic}",
                "Aufbauend auf {previous_context}, analysiere {current_topic}",
                "In Bezug auf die vorherige Diskussion über {previous_context}, erkläre {current_topic}",
                "Unter Berücksichtigung von {previous_context}, bewerte {current_topic}",
                "Mit Bezug auf {previous_context}, definiere {current_topic}",
                "Im Kontext der Ausführungen zu {previous_context}, erläutere {current_topic}",
                "Anknüpfend an {previous_context}, analysiere die Bedeutung von {current_topic}",
                "Vor dem Hintergrund von {previous_context}, erkläre {current_topic}",
                "In Fortsetzung der Diskussion über {previous_context}, behandle {current_topic}",
                "Bezugnehmend auf {previous_context}, erläutere die Relevanz von {current_topic}"
            ],
            "multi_perspective": [
                "Betrachte {topic} aus zivilrechtlicher Perspektive",
                "Analysiere {topic} unter strafrechtlichen Gesichtspunkten",
                "Bewerte {topic} aus verfassungsrechtlicher Sicht",
                "Untersuche {topic} im verwaltungsrechtlichen Kontext",
                "Prüfe {topic} unter arbeitsrechtlichen Aspekten",
                "Analysiere {topic} aus gesellschaftsrechtlicher Perspektive",
                "Betrachte {topic} im internationalen Rechtsvergleich",
                "Bewerte {topic} aus rechtspolitischer Sicht",
                "Untersuche {topic} unter rechtshistorischen Gesichtspunkten",
                "Analysiere {topic} aus interdisziplinärer Perspektive"
            ]
        }
    
    def _initialize_semantic_weights(self) -> Dict[str, float]:
        """Initialisiert erweiterte semantische Gewichtungen"""
        return {
            # Kernrechtsbegriffe - höchste Gewichtung
            "tatbestand": 0.95, "rechtsfolge": 0.95, "subsumtion": 0.95,
            "rechtsnorm": 0.90, "auslegung": 0.90, "anwendung": 0.90,
            
            # Verfahrensrechtliche Begriffe
            "verfahren": 0.85, "zuständigkeit": 0.85, "rechtsmittel": 0.85,
            "frist": 0.80, "ladung": 0.80, "anhörung": 0.80,
            
            # Materiellrechtliche Begriffe
            "anspruch": 0.90, "verpflichtung": 0.85, "berechtigung": 0.85,
            "haftung": 0.90, "verschulden": 0.85, "kausalität": 0.85,
            
            # Beweiswürdigung und Tatsachenfeststellung
            "beweis": 0.85, "tatsache": 0.80, "indiz": 0.75,
            "zeuge": 0.75, "sachverständiger": 0.80, "urkunde": 0.80,
            
            # Rechtsdogmatische Begriffe
            "dogmatik": 0.85, "systematik": 0.80, "teleologie": 0.80,
            "analogie": 0.85, "konkurrenz": 0.80, "kollision": 0.80,
            
            # Verfassungsrechtliche Begriffe
            "grundrecht": 0.90, "verhältnismäßigkeit": 0.90, "abwägung": 0.85,
            "kerngehalt": 0.85, "wesensgehalt": 0.85, "eingriff": 0.80,
            
            # Prozessuale Begriffe
            "klage": 0.85, "antrag": 0.80, "einrede": 0.75,
            "berufung": 0.80, "revision": 0.85, "beschwerde": 0.75,
            
            # Zivilrechtliche Begriffe
            "vertrag": 0.85, "willenserklärung": 0.85, "geschäftsfähigkeit": 0.80,
            "anfechtung": 0.80, "erfüllung": 0.75, "unmöglichkeit": 0.80,
            
            # Strafrechtliche Begriffe
            "straftat": 0.90, "schuld": 0.85, "vorsatz": 0.85,
            "fahrlässigkeit": 0.80, "rechtfertigung": 0.80, "entschuldigung": 0.75,
            
            # Verwaltungsrechtliche Begriffe
            "verwaltungsakt": 0.90, "ermessen": 0.85, "beurteilungsspielraum": 0.85,
            "widerruf": 0.80, "rücknahme": 0.80, "aufhebung": 0.75
        }
    
    def _initialize_domain_patterns(self) -> Dict[str, List[str]]:
        """Initialisiert domänenspezifische Erkennungsmuster"""
        return {
            "zivilrecht": [
                r"\b(?:BGB|Bürgerliches Gesetzbuch)\b",
                r"\b(?:Vertrag|Schuldverhältnis|Eigentum)\b",
                r"\b(?:Schadensersatz|Gewährleistung|Mängelrecht)\b",
                r"\b(?:Kaufvertrag|Mietvertrag|Darlehen)\b"
            ],
            "strafrecht": [
                r"\b(?:StGB|Strafgesetzbuch)\b",
                r"\b(?:Straftat|Deliktsrecht|Sanktion)\b",
                r"\b(?:Diebstahl|Betrug|Körperverletzung)\b",
                r"\b(?:Vorsatz|Fahrlässigkeit|Schuld)\b"
            ],
            "verfassungsrecht": [
                r"\b(?:GG|Grundgesetz|Verfassung)\b",
                r"\b(?:Grundrecht|Staatsorganisation)\b",
                r"\b(?:Verhältnismäßigkeit|Abwägung)\b",
                r"\b(?:Bundesverfassungsgericht|BVerfG)\b"
            ],
            "verwaltungsrecht": [
                r"\b(?:VwVfG|Verwaltungsverfahrensgesetz)\b",
                r"\b(?:Verwaltungsakt|Ermessen)\b",
                r"\b(?:Widerspruch|Anfechtungsklage)\b",
                r"\b(?:Beurteilungsspielraum|Selbstbindung)\b"
            ],
            "arbeitsrecht": [
                r"\b(?:ArbG|Arbeitsgericht|BAG)\b",
                r"\b(?:Arbeitsvertrag|Kündigung)\b",
                r"\b(?:Betriebsrat|Tarifvertrag)\b",
                r"\b(?:Arbeitszeit|Urlaub|Entgelt)\b"
            ]
        }
    
    def _initialize_complexity_modifiers(self) -> Dict[PromptComplexity, Dict[str, str]]:
        """Initialisiert Komplexitäts-Modifikatoren für Prompts"""
        return {
            PromptComplexity.BASIC: {
                "prefix": "Erkläre einfach und verständlich",
                "suffix": "Verwende allgemein verständliche Begriffe.",
                "depth": "oberflächlich"
            },
            PromptComplexity.INTERMEDIATE: {
                "prefix": "Analysiere systematisch",
                "suffix": "Berücksichtige dabei die wichtigsten rechtlichen Aspekte.",
                "depth": "strukturiert"
            },
            PromptComplexity.ADVANCED: {
                "prefix": "Führe eine detaillierte rechtliche Analyse durch",
                "suffix": "Berücksichtige dabei auch kontroverse Rechtsmeinungen und aktuelle Entwicklungen.",
                "depth": "umfassend"
            },
            PromptComplexity.EXPERT: {
                "prefix": "Analysiere kritisch und unter Berücksichtigung aller relevanten rechtsdogmatischen Aspekte",
                "suffix": "Berücksichtige dabei insbesondere rechtsvergleichende, rechtspolitische und interdisziplinäre Gesichtspunkte.",
                "depth": "wissenschaftlich"
            }
        }
    
    def detect_text_type(self, text: str, metadata: Dict = None) -> LegalTextType:
        """
        Erweiterte Erkennung des Texttyps basierend auf Inhalt und Metadaten
        """
        text_lower = text.lower()
        
        # Sachverhalt-Indikatoren
        if any(indicator in text_lower for indicator in [
            "sachverhalt", "tatsachen", "geschehen", "ereignis", "vorfall",
            "situation", "fall", "begebenheit", "umstände"
        ]):
            return LegalTextType.SACHVERHALT
            
        # Rechtsfrage-Indikatoren
        if any(indicator in text_lower for indicator in [
            "rechtsfrage", "streitfrage", "problem", "fragestellung",
            "zu prüfen", "zu klären", "streitig", "umstritten"
        ]):
            return LegalTextType.RECHTSFRAGE
            
        # Subsumtion-Indikatoren
        if any(indicator in text_lower for indicator in [
            "subsumtion", "tatbestand", "erfüllt", "vorliegt",
            "gegeben", "zu prüfen ist", "fraglich ist"
        ]):
            return LegalTextType.SUBSUMTION
            
        # Urteil-Indikatoren
        if any(indicator in text_lower for indicator in [
            "urteil", "beschluss", "entscheidung", "spruch",
            "verkündet", "gericht", "richter", "urteilsformel"
        ]):
            return LegalTextType.URTEIL
            
        # Norm-Indikatoren
        if any(indicator in text_lower for indicator in [
            "§", "artikel", "absatz", "satz", "nummer",
            "gesetz", "verordnung", "richtlinie", "norm"
        ]):
            return LegalTextType.NORM
            
        return LegalTextType.SACHVERHALT  # Standard-Fallback
    
    def detect_complexity(self, text: str, metadata: Dict = None) -> PromptComplexity:
        """
        Erkennt die angemessene Komplexitätsstufe basierend auf Textmerkmalen
        """
        # Längen-basierte Bewertung
        text_length = len(text.split())
        
        # Komplexitäts-Indikatoren zählen
        complex_terms = [
            "rechtsdogmatik", "systematik", "teleologie", "rechtsvergleich",
            "verfassungskonform", "verhältnismäßigkeit", "abwägung",
            "konkurrenz", "kollision", "analogie", "reduktion"
        ]
        
        complexity_score = sum(1 for term in complex_terms if term in text.lower())
        
        # Rechtsnormen-Referenzen zählen
        norm_refs = len(re.findall(r'§\s*\d+', text))
        complexity_score += norm_refs * 0.5
        
        # Entscheidung basierend auf Score und Länge
        if complexity_score >= 5 or text_length > 1000:
            return PromptComplexity.EXPERT
        elif complexity_score >= 3 or text_length > 500:
            return PromptComplexity.ADVANCED
        elif complexity_score >= 1 or text_length > 200:
            return PromptComplexity.INTERMEDIATE
        else:
            return PromptComplexity.BASIC
    
    def detect_domain(self, text: str) -> str:
        """
        Erkennt die Rechtsdomäne basierend auf Textinhalt
        """
        domain_scores = defaultdict(int)
        
        for domain, patterns in self.domain_patterns.items():
            for pattern in patterns:
                matches = len(re.findall(pattern, text, re.IGNORECASE))
                domain_scores[domain] += matches
        
        if domain_scores:
            return max(domain_scores.items(), key=lambda x: x[1])[0]
        return "allgemein"
    
    def extract_keywords(self, text: str) -> List[str]:
        """
        Extrahiert rechtlich relevante Schlüsselwörter
        """
        keywords = set()
        
        # Verwende semantische Gewichtungen
        for term, weight in self.semantic_weights.items():
            if weight > 0.7 and term in text.lower():
                keywords.add(term)
        
        # Füge Rechtsnormen hinzu
        norm_pattern = r'§\s*(\d+(?:\s*[a-z])?)\s*(?:Abs\.\s*\d+)?\s*(?:[A-Z][a-zA-Z]*)?'
        norms = re.findall(norm_pattern, text)
        keywords.update(f"§ {norm}" for norm in norms)
        
        return list(keywords)
    
    def generate_enhanced_prompt(self, text: str, context: PromptContext = None) -> str:
        """
        Generiert einen optimierten Prompt basierend auf dem Kontext
        """
        if context is None:
            # Automatische Kontexterkennung
            text_type = self.detect_text_type(text)
            complexity = self.detect_complexity(text)
            domain = self.detect_domain(text)
            keywords = self.extract_keywords(text)
            
            context = PromptContext(
                text_type=text_type,
                complexity=complexity,
                domain=domain,
                metadata={},
                keywords=keywords
            )
        
        # Wähle Basis-Template
        templates = self.base_templates.get(context.text_type, self.base_templates[LegalTextType.SACHVERHALT])
        base_template = random.choice(templates)
        
        # Komplexitäts-Modifikation
        modifier = self.complexity_modifiers[context.complexity]
        
        # Domänen-spezifische Anpassung
        domain_suffix = ""
        if context.domain != "allgemein":
            domain_suffix = f" Berücksichtige dabei insbesondere {context.domain}liche Aspekte."
        
        # Keyword-Enhancement
        keyword_hint = ""
        if context.keywords:
            important_keywords = [kw for kw in context.keywords if len(kw) > 2][:3]
            if important_keywords:
                keyword_hint = f" Achte besonders auf: {', '.join(important_keywords)}."
        
        # Zusammenstellung des finalen Prompts
        enhanced_prompt = f"{modifier['prefix']}: {base_template.format(text=text)}{domain_suffix}{keyword_hint} {modifier['suffix']}"
        
        return enhanced_prompt
    
    def generate_rag_queries(self, text: str, num_queries: int = 8) -> List[str]:
        """
        Generiert diverse Queries für RAG Training
        """
        context = PromptContext(
            text_type=self.detect_text_type(text),
            complexity=self.detect_complexity(text),
            domain=self.detect_domain(text),
            metadata={},
            keywords=self.extract_keywords(text)
        )
        
        queries = []
        
        # Basis-Query-Generierung
        concepts = list(context.keywords)[:3] if context.keywords else ["Rechtsfrage"]
        domain = context.domain
        
        for template_type, templates in self.rag_templates.items():
            if template_type == "query_generation" and concepts:
                for concept in concepts:
                    template = random.choice(templates)
                    query = template.format(concept=concept, domain=domain)
                    queries.append(query)
                    
                    if len(queries) >= num_queries:
                        break
        
        # Multi-Perspektiven-Queries
        if len(queries) < num_queries:
            perspective_templates = self.rag_templates["multi_perspective"]
            topic = concepts[0] if concepts else "das vorliegende Rechtsproblem"
            
            for template in perspective_templates:
                if len(queries) >= num_queries:
                    break
                query = template.format(topic=topic)
                queries.append(query)
        
        return queries[:num_queries]
    
    def generate_training_variations(self, text: str, num_variations: int = 5) -> List[Tuple[str, str]]:
        """
        Generiert Trainings-Variationen für Fine-Tuning
        """
        variations = []
        
        context = PromptContext(
            text_type=self.detect_text_type(text),
            complexity=self.detect_complexity(text),
            domain=self.detect_domain(text),
            metadata={},
            keywords=self.extract_keywords(text)
        )
        
        # Verschiedene Komplexitätsstufen
        complexities = [PromptComplexity.BASIC, PromptComplexity.INTERMEDIATE, 
                       PromptComplexity.ADVANCED, PromptComplexity.EXPERT]
        
        for complexity in complexities[:num_variations]:
            temp_context = PromptContext(
                text_type=context.text_type,
                complexity=complexity,
                domain=context.domain,
                metadata=context.metadata,
                keywords=context.keywords
            )
            
            prompt = self.generate_enhanced_prompt(text, temp_context)
            variations.append((prompt, text))
            
            if len(variations) >= num_variations:
                break
        
        return variations
    
    def evaluate_prompt_quality(self, prompt: str, text: str) -> Dict[str, float]:
        """
        Bewertet die Qualität eines generierten Prompts
        """
        metrics = {}
        
        # Längen-Verhältnis
        prompt_words = len(prompt.split())
        text_words = len(text.split())
        metrics["length_ratio"] = min(prompt_words / max(text_words, 1), 1.0)
        
        # Keyword-Abdeckung
        prompt_lower = prompt.lower()
        text_keywords = self.extract_keywords(text)
        covered_keywords = sum(1 for kw in text_keywords if kw.lower() in prompt_lower)
        metrics["keyword_coverage"] = covered_keywords / max(len(text_keywords), 1)
        
        # Spezifität (Anzahl rechtlicher Fachbegriffe)
        legal_terms = sum(1 for term in self.semantic_weights.keys() if term in prompt_lower)
        metrics["legal_specificity"] = min(legal_terms / 10, 1.0)
        
        # Strukturiertheit (Vorhandensein von Struktur-Wörtern)
        structure_words = ["analysiere", "prüfe", "bewerte", "systematisch", "detailliert"]
        structure_score = sum(1 for word in structure_words if word in prompt_lower)
        metrics["structure_quality"] = min(structure_score / 3, 1.0)
        
        # Gesamtbewertung
        metrics["overall_quality"] = sum(metrics.values()) / len(metrics)
        
        return metrics

def main():
    """Demonstriert die Verwendung des optimierten Prompt-Generators"""
    generator = OptimizedPromptGenerator()
    
    # Beispieltext
    sample_text = """
    Der Kläger verlangt von der Beklagten Schadensersatz wegen Verletzung der Verkehrssicherungspflicht.
    Am 15.03.2023 stürzte der Kläger auf dem Gehweg vor dem Geschäft der Beklagten aufgrund von Glatteis.
    Die Beklagte hatte trotz entsprechender Wetterlage nicht gestreut.
    """
    
    print("=== OPTIMIERTE PROMPT-GENERIERUNG ===\n")
    
    # Automatische Kontexterkennung
    text_type = generator.detect_text_type(sample_text)
    complexity = generator.detect_complexity(sample_text)
    domain = generator.detect_domain(sample_text)
    keywords = generator.extract_keywords(sample_text)
    
    print(f"Erkannter Texttyp: {text_type.value}")
    print(f"Erkannte Komplexität: {complexity.value}")
    print(f"Erkannte Domäne: {domain}")
    print(f"Extrahierte Keywords: {', '.join(list(keywords)[:5])}")
    print()
    
    # Enhanced Prompt Generation
    enhanced_prompt = generator.generate_enhanced_prompt(sample_text)
    print("=== ENHANCED PROMPT ===")
    print(enhanced_prompt)
    print()
    
    # RAG Query Generation
    rag_queries = generator.generate_rag_queries(sample_text, 6)
    print("=== RAG TRAINING QUERIES ===")
    for i, query in enumerate(rag_queries, 1):
        print(f"{i}. {query}")
    print()
    
    # Training Variations
    variations = generator.generate_training_variations(sample_text, 3)
    print("=== TRAINING VARIATIONS ===")
    for i, (prompt, _) in enumerate(variations, 1):
        print(f"Variation {i}:")
        print(f"  {prompt[:100]}...")
        print()
    
    # Quality Evaluation
    quality_metrics = generator.evaluate_prompt_quality(enhanced_prompt, sample_text)
    print("=== QUALITY METRICS ===")
    for metric, value in quality_metrics.items():
        print(f"{metric}: {value:.3f}")

if __name__ == "__main__":
    main()
