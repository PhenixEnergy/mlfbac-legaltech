"""
Datenverarbeitung für dnoti Gutachten

Dieses Modul lädt und verarbeitet die JSON-Daten der Rechtsgutachten
und bereitet sie für die weitere Verarbeitung vor.
"""

import json
import logging
from pathlib import Path
from typing import Dict, List, Optional, Iterator
from dataclasses import dataclass
from datetime import datetime

import pandas as pd

logger = logging.getLogger(__name__)


@dataclass
class Gutachten:
    """Datenklasse für ein einzelnes Rechtsgutachten."""
    id: int
    url: str
    erscheinungsdatum: str
    gutachten_nummer: str
    rechtsbezug: str
    normen: Optional[str]
    text: str
    
    # Berechnete Felder
    text_length: Optional[int] = None
    word_count: Optional[int] = None
    legal_entities: Optional[List[str]] = None
    
    def __post_init__(self):
        """Berechnet abgeleitete Felder nach Initialisierung."""
        if self.text:
            self.text_length = len(self.text)
            self.word_count = len(self.text.split())
    
    @property
    def estimated_tokens(self) -> int:
        """Geschätzte Token-Anzahl (grobe Schätzung: ~4 Zeichen pro Token)."""
        return self.text_length // 4 if self.text_length else 0
    
    def to_dict(self) -> Dict:
        """Konvertiert zu Dictionary für weitere Verarbeitung."""
        return {
            'id': self.id,
            'url': self.url,
            'erscheinungsdatum': self.erscheinungsdatum,
            'gutachten_nummer': self.gutachten_nummer,
            'rechtsbezug': self.rechtsbezug,
            'normen': self.normen,
            'text': self.text,
            'text_length': self.text_length,
            'word_count': self.word_count,
            'estimated_tokens': self.estimated_tokens,
            'legal_entities': self.legal_entities
        }


class DNOTIDataLoader:
    """Lädt und verarbeitet dnoti Gutachten aus JSON-Datei."""
    
    def __init__(self, json_path: Path):
        """
        Initialisiert den DataLoader.
        
        Args:
            json_path: Pfad zur dnoti_all.json Datei
        """
        self.json_path = Path(json_path)
        self._gutachten_cache: Optional[List[Gutachten]] = None
        self._validate_file()
    
    def _validate_file(self) -> None:
        """Validiert die JSON-Datei."""
        if not self.json_path.exists():
            raise FileNotFoundError(f"JSON-Datei nicht gefunden: {self.json_path}")
        
        if not self.json_path.suffix.lower() == '.json':
            raise ValueError(f"Datei muss JSON-Format haben: {self.json_path}")
        
        logger.info(f"JSON-Datei validiert: {self.json_path}")
    
    def load_gutachten(self, limit: Optional[int] = None, 
                      skip_invalid: bool = True) -> List[Gutachten]:
        """
        Lädt alle Gutachten aus der JSON-Datei.
        
        Args:
            limit: Maximale Anzahl zu ladender Gutachten (für Tests)
            skip_invalid: Überspringe ungültige Einträge
            
        Returns:
            Liste von Gutachten-Objekten
        """
        if self._gutachten_cache is not None and limit is None:
            return self._gutachten_cache
        
        logger.info(f"Lade Gutachten aus {self.json_path}")
        
        try:
            with open(self.json_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
        except json.JSONDecodeError as e:
            logger.error(f"JSON-Decode Fehler: {e}")
            raise
        
        gutachten_list = []
        invalid_count = 0
        
        for i, item in enumerate(data):
            if limit and i >= limit:
                break
                
            try:
                gutachten = self._parse_gutachten(item)
                gutachten_list.append(gutachten)
            except Exception as e:
                invalid_count += 1
                if skip_invalid:
                    logger.warning(f"Überspringe ungültiges Gutachten {i}: {e}")
                    continue
                else:
                    logger.error(f"Fehler bei Gutachten {i}: {e}")
                    raise
        
        logger.info(f"Geladen: {len(gutachten_list)} Gutachten, "
                   f"Übersprungen: {invalid_count}")
        
        if limit is None:
            self._gutachten_cache = gutachten_list
            
        return gutachten_list
    
    def _parse_gutachten(self, item: Dict) -> Gutachten:
        """
        Parst ein einzelnes Gutachten aus JSON-Daten.
        
        Args:
            item: JSON-Dictionary eines Gutachtens
            
        Returns:
            Gutachten-Objekt
        """
        required_fields = ['id', 'text', 'gutachten_nummer']
        for field in required_fields:
            if field not in item or not item[field]:
                raise ValueError(f"Pflichtfeld fehlt oder leer: {field}")
        
        return Gutachten(
            id=item['id'],
            url=item.get('url', ''),
            erscheinungsdatum=item.get('erscheinungsdatum', ''),
            gutachten_nummer=item['gutachten_nummer'],
            rechtsbezug=item.get('rechtsbezug', ''),
            normen=item.get('normen'),
            text=item['text']
        )
    
    def get_statistics(self) -> Dict:
        """
        Berechnet Statistiken über die geladenen Gutachten.
        
        Returns:
            Dictionary mit Statistiken
        """
        gutachten_list = self.load_gutachten()
        
        if not gutachten_list:
            return {"error": "Keine Gutachten geladen"}
        
        # Basis-Statistiken
        total_count = len(gutachten_list)
        text_lengths = [g.text_length for g in gutachten_list if g.text_length]
        estimated_tokens = [g.estimated_tokens for g in gutachten_list]
        
        # Rechtsbezug-Verteilung
        rechtsbezug_counts = {}
        for g in gutachten_list:
            rb = g.rechtsbezug or "Unbekannt"
            rechtsbezug_counts[rb] = rechtsbezug_counts.get(rb, 0) + 1
        
        # Jahre-Verteilung (falls Datum verfügbar)
        jahr_counts = {}
        for g in gutachten_list:
            if g.erscheinungsdatum:
                try:
                    # Extrahiere Jahr aus verschiedenen Datumsformaten
                    jahr = g.erscheinungsdatum.split('.')[-1] if '.' in g.erscheinungsdatum else None
                    if jahr and jahr.isdigit():
                        jahr_counts[jahr] = jahr_counts.get(jahr, 0) + 1
                except:
                    continue
        
        return {
            "total_gutachten": total_count,
            "text_statistiken": {
                "durchschnittliche_laenge": sum(text_lengths) / len(text_lengths) if text_lengths else 0,
                "min_laenge": min(text_lengths) if text_lengths else 0,
                "max_laenge": max(text_lengths) if text_lengths else 0,
                "median_laenge": sorted(text_lengths)[len(text_lengths)//2] if text_lengths else 0
            },
            "token_statistiken": {
                "durchschnittliche_tokens": sum(estimated_tokens) / len(estimated_tokens) if estimated_tokens else 0,
                "min_tokens": min(estimated_tokens) if estimated_tokens else 0,
                "max_tokens": max(estimated_tokens) if estimated_tokens else 0,
                "total_tokens": sum(estimated_tokens) if estimated_tokens else 0
            },
            "rechtsbezug_verteilung": rechtsbezug_counts,
            "jahr_verteilung": jahr_counts,
            "datei_info": {
                "pfad": str(self.json_path),
                "groesse_mb": self.json_path.stat().st_size / (1024 * 1024)
            }
        }
    
    def to_dataframe(self, limit: Optional[int] = None) -> pd.DataFrame:
        """
        Konvertiert Gutachten zu Pandas DataFrame.
        
        Args:
            limit: Maximale Anzahl Gutachten
            
        Returns:
            Pandas DataFrame
        """
        gutachten_list = self.load_gutachten(limit=limit)
        data = [g.to_dict() for g in gutachten_list]
        return pd.DataFrame(data)
    
    def iterate_gutachten(self, batch_size: int = 100) -> Iterator[List[Gutachten]]:
        """
        Iterator für batch-weise Verarbeitung der Gutachten.
        
        Args:
            batch_size: Anzahl Gutachten pro Batch
            
        Yields:
            Listen von Gutachten-Objekten
        """
        gutachten_list = self.load_gutachten()
        
        for i in range(0, len(gutachten_list), batch_size):
            yield gutachten_list[i:i + batch_size]
    
    def filter_gutachten(self, 
                        rechtsbezug: Optional[str] = None,
                        jahr: Optional[str] = None,
                        min_tokens: Optional[int] = None,
                        max_tokens: Optional[int] = None,
                        normen_filter: Optional[str] = None) -> List[Gutachten]:
        """
        Filtert Gutachten nach verschiedenen Kriterien.
        
        Args:
            rechtsbezug: Filter nach Rechtsbezug
            jahr: Filter nach Erscheinungsjahr
            min_tokens: Minimale Token-Anzahl
            max_tokens: Maximale Token-Anzahl
            normen_filter: Filter nach Normen (Teilstring-Match)
            
        Returns:
            Gefilterte Liste von Gutachten
        """
        gutachten_list = self.load_gutachten()
        filtered = gutachten_list
        
        if rechtsbezug:
            filtered = [g for g in filtered if g.rechtsbezug == rechtsbezug]
        
        if jahr:
            filtered = [g for g in filtered if jahr in g.erscheinungsdatum]
        
        if min_tokens:
            filtered = [g for g in filtered if g.estimated_tokens >= min_tokens]
        
        if max_tokens:
            filtered = [g for g in filtered if g.estimated_tokens <= max_tokens]
        
        if normen_filter and normen_filter.strip():
            filtered = [g for g in filtered if g.normen and normen_filter.lower() in g.normen.lower()]
        
        logger.info(f"Gefiltert: {len(filtered)} von {len(gutachten_list)} Gutachten")
        return filtered


# Utility-Funktionen
def load_sample_data(json_path: Path, sample_size: int = 100) -> List[Gutachten]:
    """
    Lädt eine Stichprobe von Gutachten für Tests und Entwicklung.
    
    Args:
        json_path: Pfad zur JSON-Datei
        sample_size: Anzahl der zu ladenden Gutachten
        
    Returns:
        Liste von Gutachten-Objekten
    """
    loader = DNOTIDataLoader(json_path)
    return loader.load_gutachten(limit=sample_size)


def analyze_token_distribution(gutachten_list: List[Gutachten]) -> Dict:
    """
    Analysiert die Token-Verteilung für Chunking-Strategien.
    
    Args:
        gutachten_list: Liste von Gutachten
        
    Returns:
        Analyse der Token-Verteilung
    """
    tokens = [g.estimated_tokens for g in gutachten_list]
    
    # Perzentile berechnen
    sorted_tokens = sorted(tokens)
    n = len(sorted_tokens)
    
    percentiles = {}
    for p in [10, 25, 50, 75, 90, 95, 99]:
        idx = int(n * p / 100)
        percentiles[f"p{p}"] = sorted_tokens[idx] if idx < n else sorted_tokens[-1]
    
    # Chunking-Empfehlungen
    avg_tokens = sum(tokens) / len(tokens)
    chunk_recommendations = {
        "small_chunks": avg_tokens // 10,
        "medium_chunks": avg_tokens // 5,
        "large_chunks": avg_tokens // 3
    }
    
    return {
        "total_gutachten": len(gutachten_list),
        "token_statistiken": {
            "durchschnitt": avg_tokens,
            "minimum": min(tokens),
            "maximum": max(tokens),
            "standardabweichung": (sum((t - avg_tokens) ** 2 for t in tokens) / len(tokens)) ** 0.5
        },
        "perzentile": percentiles,
        "chunking_empfehlungen": chunk_recommendations
    }
