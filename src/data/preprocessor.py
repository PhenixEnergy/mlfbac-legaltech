"""
Text Preprocessing Module für dnoti Rechtsgutachten
Implementiert rechtsspezifische Text-Bereinigung und -Normalisierung
"""

import re
import unicodedata
from typing import Dict, List, Optional, Tuple
import logging
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class PreprocessingConfig:
    """Konfiguration für Text-Preprocessing"""
    remove_extra_whitespace: bool = True
    normalize_unicode: bool = True
    preserve_legal_formatting: bool = True
    preserve_paragraph_numbers: bool = True
    preserve_article_numbers: bool = True
    normalize_legal_citations: bool = True
    extract_legal_norms: bool = True


class LegalTextPreprocessor:
    """
    Rechtsspezifischer Text-Preprocessor für dnoti Gutachten
    
    Funktionen:
    - Text-Bereinigung unter Beibehaltung der rechtlichen Struktur
    - Normalisierung von Rechtszitaten
    - Extraktion von Metadaten
    - Erhaltung wichtiger juristischer Formatierungen
    """
    
    def __init__(self, config: Optional[PreprocessingConfig] = None):
        self.config = config or PreprocessingConfig()
        self._init_patterns()
        
    def _init_patterns(self):
        """Initialisiert Regex-Patterns für juristische Texte"""
        
        # Rechtsnormen-Patterns
        self.legal_norms_patterns = {
            'bgb': r'§§?\s*(\d+(?:\s*[a-z])?(?:\s*-\s*\d+(?:\s*[a-z])?)?)\s*BGB',
            'zpo': r'§§?\s*(\d+(?:\s*[a-z])?(?:\s*-\s*\d+(?:\s*[a-z])?)?)\s*ZPO',
            'gbo': r'§§?\s*(\d+(?:\s*[a-z])?(?:\s*-\s*\d+(?:\s*[a-z])?)?)\s*GBO',
            'weg': r'§§?\s*(\d+(?:\s*[a-z])?(?:\s*-\s*\d+(?:\s*[a-z])?)?)\s*WEG',
            'euebrvo': r'Art\.?\s*(\d+(?:\s*[a-z])?(?:\s*-\s*\d+(?:\s*[a-z])?)?)\s*EuErbVO',
            'gmbhg': r'§§?\s*(\d+(?:\s*[a-z])?(?:\s*-\s*\d+(?:\s*[a-z])?)?)\s*GmbHG',
            'aktg': r'§§?\s*(\d+(?:\s*[a-z])?(?:\s*-\s*\d+(?:\s*[a-z])?)?)\s*AktG',
            'hgb': r'§§?\s*(\d+(?:\s*[a-z])?(?:\s*-\s*\d+(?:\s*[a-z])?)?)\s*HGB'
        }
        
        # Strukturelle Patterns
        self.structure_patterns = {
            'roman_numerals': r'[IVX]+\.\s*',
            'paragraph_numbers': r'^\s*\d+\.\s*',
            'sub_paragraph': r'^\s*[a-z]\)\s*',
            'double_sub_paragraph': r'^\s*[a-z]{2}\)\s*'
        }
        
        # Zitat-Patterns
        self.citation_patterns = {
            'court_decisions': r'(BGH|OLG|LG|AG)\s+.*?v\.\s+\d{1,2}\.\d{1,2}\.\d{4}',
            'journal_citations': r'[A-Z]{2,}\s+\d{4},\s*\d+',
            'case_numbers': r'[IVX\s]+\s*[A-Z]{1,3}\s+\d+/\d{2,4}'
        }
        
    def preprocess_text(self, text: str, gutachten_metadata: Optional[Dict] = None) -> Dict[str, any]:
        """
        Hauptmethode für Text-Preprocessing
        
        Args:
            text: Roher Gutachtentext
            gutachten_metadata: Optional - Metadaten des Gutachtens
            
        Returns:
            Dict mit bereinigtem Text und extrahierten Metadaten
        """
        result = {
            'original_text': text,
            'processed_text': text,
            'extracted_metadata': {},
            'statistics': {}
        }
        
        try:
            # 1. Basic Text Cleaning
            if self.config.normalize_unicode:
                result['processed_text'] = self._normalize_unicode(result['processed_text'])
                
            if self.config.remove_extra_whitespace:
                result['processed_text'] = self._clean_whitespace(result['processed_text'])
                
            # 2. Legal-specific processing
            if self.config.extract_legal_norms:
                result['extracted_metadata']['legal_norms'] = self._extract_legal_norms(text)
                
            if self.config.normalize_legal_citations:
                result['processed_text'] = self._normalize_citations(result['processed_text'])
                
            # 3. Structure preservation
            if self.config.preserve_legal_formatting:
                result['processed_text'] = self._preserve_legal_structure(result['processed_text'])
                
            # 4. Metadata extraction
            result['extracted_metadata'].update(self._extract_metadata(text, gutachten_metadata))
            
            # 5. Statistics
            result['statistics'] = self._calculate_statistics(result['processed_text'])
            
            logger.info(f"Text preprocessing completed. Original: {len(text)} chars, Processed: {len(result['processed_text'])} chars")
            
        except Exception as e:
            logger.error(f"Error in text preprocessing: {str(e)}")
            result['error'] = str(e)
            
        return result
    
    def _normalize_unicode(self, text: str) -> str:
        """Normalisiert Unicode-Zeichen"""
        return unicodedata.normalize('NFKC', text)
    
    def _clean_whitespace(self, text: str) -> str:
        """Bereinigt überflüssige Whitespace-Zeichen"""
        # Mehrfache Leerzeichen durch einzelne ersetzen
        text = re.sub(r' +', ' ', text)
        
        # Mehrfache Zeilenwechsel auf maximal zwei reduzieren
        text = re.sub(r'\n{3,}', '\n\n', text)
        
        # Leerzeichenzeilen bereinigen
        text = re.sub(r'\n +\n', '\n\n', text)
        
        return text.strip()
    
    def _extract_legal_norms(self, text: str) -> Dict[str, List[str]]:
        """Extrahiert Rechtsnormen aus dem Text"""
        found_norms = {}
        
        for norm_type, pattern in self.legal_norms_patterns.items():
            matches = re.finditer(pattern, text, re.IGNORECASE)
            norm_references = []
            
            for match in matches:
                full_match = match.group(0)
                paragraph = match.group(1) if match.groups() else None
                
                norm_references.append({
                    'full_reference': full_match,
                    'paragraph': paragraph,
                    'position': match.start()
                })
            
            if norm_references:
                found_norms[norm_type.upper()] = norm_references
                
        return found_norms
    
    def _normalize_citations(self, text: str) -> str:
        """Normalisiert Rechtszitate für bessere Konsistenz"""
        
        # Paragraph-Zeichen normalisieren
        text = re.sub(r'§§?\s*', '§ ', text)
        
        # Artikel-Referenzen normalisieren
        text = re.sub(r'Art\.?\s*', 'Art. ', text)
        
        # Datum-Normalisierung in Urteilen
        text = re.sub(r'v\.\s*(\d{1,2})\.(\d{1,2})\.(\d{4})', 
                     r'v. \1.\2.\3', text)
        
        return text
    
    def _preserve_legal_structure(self, text: str) -> str:
        """Erhält wichtige rechtliche Strukturelemente"""
        
        # Sicherstellen, dass römische Ziffern korrekt formatiert sind
        text = re.sub(r'([IVX]+)\s*\.\s*([A-ZÄÖÜ])', r'\1. \2', text)
        
        # Paragraph-Nummerierung
        text = re.sub(r'(\d+)\s*\.\s*([A-ZÄÖÜ])', r'\1. \2', text)
        
        return text
    
    def _extract_metadata(self, text: str, existing_metadata: Optional[Dict] = None) -> Dict:
        """Extrahiert Metadaten aus dem Gutachtentext"""
        metadata = existing_metadata.copy() if existing_metadata else {}
        
        # Gutachten-Nummer extrahieren
        gutachten_match = re.search(r'Gutachten\s+Nr\.\s*(\d+(?:/\d+)?)', text, re.IGNORECASE)
        if gutachten_match:
            metadata['gutachten_nummer'] = gutachten_match.group(1)
        
        # Datum extrahieren
        date_patterns = [
            r'(\d{1,2}\.\d{1,2}\.\d{4})',
            r'(\d{4}-\d{1,2}-\d{1,2})'
        ]
        
        for pattern in date_patterns:
            date_match = re.search(pattern, text)
            if date_match:
                metadata['datum'] = date_match.group(1)
                break
        
        # Schlüsselwörter extrahieren (einfache Implementierung)
        legal_keywords = [
            'Eigentum', 'Besitz', 'Vertrag', 'Schuldverhältnis', 'Anspruch',
            'Haftung', 'Schadensersatz', 'Gewährleistung', 'Verjährung',
            'Erbrecht', 'Gesellschaftsrecht', 'Immobilienrecht'
        ]
        
        found_keywords = []
        for keyword in legal_keywords:
            if re.search(r'\b' + re.escape(keyword) + r'\b', text, re.IGNORECASE):
                found_keywords.append(keyword)
        
        if found_keywords:
            metadata['keywords'] = found_keywords
        
        return metadata
    
    def _calculate_statistics(self, text: str) -> Dict[str, int]:
        """Berechnet Text-Statistiken"""
        return {
            'char_count': len(text),
            'word_count': len(text.split()),
            'paragraph_count': len([p for p in text.split('\n\n') if p.strip()]),
            'sentence_count': len(re.findall(r'[.!?]+', text))
        }
    
    def clean_for_embedding(self, text: str) -> str:
        """
        Spezielle Bereinigung für Embedding-Generierung
        Entfernt störende Elemente, die die Vektorqualität beeinträchtigen könnten
        """
        
        # Sehr lange Leerzeichen-Sequenzen entfernen
        text = re.sub(r'\s{10,}', ' ', text)
        
        # Sonderzeichen reduzieren (aber rechtlich relevante beibehalten)
        text = re.sub(r'[^\w\s§\.,:;()\-/äöüÄÖÜß]', '', text)
        
        # Übermäßige Wiederholungen reduzieren
        text = re.sub(r'(.)\1{5,}', r'\1\1\1', text)
        
        return text.strip()


class TextQualityValidator:
    """Validiert Textqualität nach der Preprocessing"""
    
    @staticmethod
    def validate_processed_text(processed_result: Dict) -> Dict[str, bool]:
        """
        Validiert die Qualität des verarbeiteten Texts
        
        Returns:
            Dict mit Validierungsergebnissen
        """
        validation_results = {}
        text = processed_result.get('processed_text', '')
        
        # Mindestlänge-Check
        validation_results['min_length_ok'] = len(text) >= 100
        
        # Struktur-Check
        validation_results['has_structure'] = bool(
            re.search(r'[IVX]+\.\s|^\s*\d+\.\s', text, re.MULTILINE)
        )
        
        # Legal content check
        legal_indicators = ['§', 'Art.', 'BGB', 'ZPO', 'Anspruch', 'Recht']
        validation_results['has_legal_content'] = any(
            indicator in text for indicator in legal_indicators
        )
        
        # Encoding check
        try:
            text.encode('utf-8')
            validation_results['encoding_ok'] = True
        except UnicodeError:
            validation_results['encoding_ok'] = False
        
        # Overall quality score
        validation_results['overall_quality'] = sum(validation_results.values()) / len(validation_results)
        
        return validation_results


if __name__ == "__main__":
    # Test der Preprocessing-Funktionalität
    sample_text = """
    I. Sachverhalt
    
    Der Kläger verlangt von der Beklagten Schadensersatz nach § 280 Abs. 1 BGB.
    
    II. Frage
    
    Besteht ein Anspruch auf Schadensersatz gemäß § 280 BGB?
    
    III. Zur Rechtslage
    
    Nach § 280 Abs. 1 BGB kann der Gläubiger...
    """
    
    preprocessor = LegalTextPreprocessor()
    result = preprocessor.preprocess_text(sample_text)
    
    print("Preprocessing Result:")
    print(f"Processed Text Length: {len(result['processed_text'])}")
    print(f"Legal Norms Found: {result['extracted_metadata'].get('legal_norms', {})}")
    print(f"Statistics: {result['statistics']}")
