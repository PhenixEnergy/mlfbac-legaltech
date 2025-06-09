#!/usr/bin/env python3
"""
DNOTI Auto-Update Service - Korrigierte Version
Behebt ChromaDB Integration und DNOTI Website-Zugriff

Entwickelt für robuste, produktionsreife Updates der Legal Tech Datenbank
"""

import asyncio
import logging
import time
import hashlib
import json
import sys
import re
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple
from dataclasses import dataclass, asdict
from urllib.parse import urljoin, urlparse, parse_qs
import uuid

# Web Scraping
import requests
from bs4 import BeautifulSoup

# Projekt Imports
sys.path.append(str(Path(__file__).parent / "src"))
from src.vectordb.chroma_client import ChromaDBClient

# ========== KONFIGURATION ==========

@dataclass
class DNOTIConfig:
    """Korrigierte Konfiguration für DNOTI Auto-Update"""
    
    # DNOTI Website-Konfiguration
    BASE_URL: str = "https://www.dnoti.de"
    GUTACHTEN_SEARCH_URL: str = "https://www.dnoti.de/gutachten/"
    
    # Formular-Parameter für TYPO3
    FORM_FIELD_PREFIX: str = "tx_dnotionlineplusapi_expertises"
    
    # Update-Strategien
    CHECK_INTERVAL_HOURS: int = 6
    BATCH_SIZE: int = 10
    MAX_PAGES_PER_RUN: int = 10
    
    # Request-Konfiguration
    REQUEST_TIMEOUT: int = 30
    REQUEST_DELAY_SECONDS: float = 2.0
    MAX_RETRIES: int = 3
    
    # ChromaDB-Konfiguration  
    COLLECTION_NAME: str = "dnoti_gutachten"
    
    # Logging
    LOG_FILE: str = "logs/dnoti_auto_update.log"
    LOG_LEVEL: str = "INFO"

# ========== HAUPTKLASSE ==========

class DNOTIAutoUpdaterFixed:
    """Korrigierte Version des DNOTI Auto-Updaters"""
    
    def __init__(self, config: DNOTIConfig = None):
        self.config = config or DNOTIConfig()
        self.session = requests.Session()
        self.chroma_client = None
        
        # Setup User-Agent für bessere Website-Kompatibilität
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'de,en-US;q=0.7,en;q=0.3',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
        })
        
        # Setup Logging
        self._setup_logging()
        
        # Initialisiere ChromaDB
        self._initialize_chromadb()
    
    def _setup_logging(self):
        """Konfiguriert Logging für Windows-Kompatibilität"""
        log_dir = Path(self.config.LOG_FILE).parent
        log_dir.mkdir(exist_ok=True)
        
        logging.basicConfig(
            level=getattr(logging, self.config.LOG_LEVEL),
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(self.config.LOG_FILE, encoding='utf-8'),
                logging.StreamHandler(sys.stdout)
            ]
        )
        
        self.logger = logging.getLogger(self.__class__.__name__)
        self.logger.info("DNOTI Fixed Auto-Updater initialisiert")
    
    def _initialize_chromadb(self):
        """Initialisiert ChromaDB-Verbindung mit korrekten Methoden"""
        try:
            self.chroma_client = ChromaDBClient()
            
            # Stelle sicher, dass Collection existiert
            self.chroma_client.create_collection(
                collection_name=self.config.COLLECTION_NAME,
                reset_if_exists=False
            )
            
            self.logger.info(f"ChromaDB Collection '{self.config.COLLECTION_NAME}' erfolgreich initialisiert")
            
        except Exception as e:
            self.logger.error(f"Fehler beim Initialisieren von ChromaDB: {e}")
            raise
    
    def search_recent_gutachten(self, days_back: int = 30) -> List[Dict]:
        """
        Sucht nach neuen Gutachten über das DNOTI-Suchformular
        
        Args:
            days_back: Wie viele Tage zurück suchen
            
        Returns:
            Liste von Gutachten-Metadaten
        """
        try:
            self.logger.info(f"Suche nach Gutachten der letzten {days_back} Tage...")
            
            # Bestimme Suchzeitraum
            end_year = datetime.now().year
            start_year = end_year - 1 if days_back > 365 else end_year
            
            all_gutachten = []
            
            # Suche nach Jahr (DNOTI Report Format)
            for year in range(start_year, end_year + 1):
                year_gutachten = self._search_by_year(year)
                all_gutachten.extend(year_gutachten)
                
                self.logger.info(f"Jahr {year}: {len(year_gutachten)} Gutachten gefunden")
                time.sleep(self.config.REQUEST_DELAY_SECONDS)
            
            # Filtere nach Datum (falls möglich)
            cutoff_date = datetime.now() - timedelta(days=days_back)
            recent_gutachten = self._filter_by_date(all_gutachten, cutoff_date)
            
            self.logger.info(f"Gesamt gefunden: {len(all_gutachten)}, davon recent: {len(recent_gutachten)}")
            return recent_gutachten
            
        except Exception as e:
            self.logger.error(f"Fehler beim Suchen nach Gutachten: {e}")
            return []
    
    def _search_by_year(self, year: int) -> List[Dict]:
        """Sucht Gutachten für ein bestimmtes Jahr"""
        gutachten_list = []
        
        try:
            # Erstelle Suchformular-Daten
            form_data = {
                f"{self.config.FORM_FIELD_PREFIX}[page]": "1",
                f"{self.config.FORM_FIELD_PREFIX}[expertisesType]": "dnotiReport",
                f"{self.config.FORM_FIELD_PREFIX}[reportYear]": str(year),
                f"{self.config.FORM_FIELD_PREFIX}[searchTitle]": "",
                f"{self.config.FORM_FIELD_PREFIX}[searchText]": "",
            }
            
            page = 1
            max_pages = self.config.MAX_PAGES_PER_RUN
            
            while page <= max_pages:
                form_data[f"{self.config.FORM_FIELD_PREFIX}[page]"] = str(page)
                
                # Sende POST-Request
                response = self.session.post(
                    self.config.GUTACHTEN_SEARCH_URL,
                    data=form_data,
                    timeout=self.config.REQUEST_TIMEOUT
                )
                
                if response.status_code != 200:
                    self.logger.warning(f"Jahr {year}, Seite {page}: HTTP {response.status_code}")
                    break
                
                # Parse Ergebnisse
                page_gutachten = self._parse_search_results(response.text, year)
                
                if not page_gutachten:
                    self.logger.info(f"Jahr {year}, Seite {page}: Keine weiteren Ergebnisse")
                    break
                
                gutachten_list.extend(page_gutachten)
                self.logger.info(f"Jahr {year}, Seite {page}: {len(page_gutachten)} Gutachten gefunden")
                
                page += 1
                time.sleep(self.config.REQUEST_DELAY_SECONDS)
            
        except Exception as e:
            self.logger.error(f"Fehler beim Suchen für Jahr {year}: {e}")
        
        return gutachten_list
    
    def _parse_search_results(self, html_content: str, year: int) -> List[Dict]:
        """Parst Suchergebnisse und extrahiert Gutachten-Links"""
        gutachten_list = []
        
        try:
            soup = BeautifulSoup(html_content, 'html.parser')
            
            # Suche nach Gutachten-Links (Detail-URLs mit nodeid)
            detail_pattern = re.compile(r'/gutachten/details/\?tx_dnotionlineplusapi_expertises%5Bnodeid%5D=([a-f0-9-]+)&cHash=([a-f0-9]+)')
            
            # Finde alle Links, die dem Gutachten-Detail-Muster entsprechen
            for link in soup.find_all('a', href=True):
                href = link.get('href', '')
                match = detail_pattern.search(href)
                
                if match:
                    node_id = match.group(1)
                    c_hash = match.group(2)
                    
                    # Konstruiere vollständige URL
                    full_url = urljoin(self.config.BASE_URL, href)
                    
                    # Extrahiere Titel (falls verfügbar)
                    title = link.get_text(strip=True) or f"Gutachten {node_id[:8]}"
                    
                    gutachten_info = {
                        'url': full_url,
                        'node_id': node_id,
                        'c_hash': c_hash,
                        'title': title,
                        'year': year,
                        'found_date': datetime.now().isoformat()
                    }
                    
                    gutachten_list.append(gutachten_info)
            
            # Alternative: Suche nach anderen möglichen Link-Strukturen
            if not gutachten_list:
                self._try_alternative_parsing(soup, gutachten_list, year)
            
        except Exception as e:
            self.logger.error(f"Fehler beim Parsen der Suchergebnisse: {e}")
        
        return gutachten_list
    
    def _try_alternative_parsing(self, soup: BeautifulSoup, gutachten_list: List[Dict], year: int):
        """Versucht alternative Parsing-Methoden für Gutachten"""
        try:
            # Suche nach anderen möglichen Strukturen
            for element in soup.find_all(['div', 'article', 'section'], class_=re.compile(r'gutachten|expertise|result')):
                links = element.find_all('a', href=True)
                for link in links:
                    href = link.get('href', '')
                    if 'gutachten' in href and 'details' in href:
                        title = link.get_text(strip=True) or f"Gutachten {year}"
                        full_url = urljoin(self.config.BASE_URL, href)
                        
                        gutachten_info = {
                            'url': full_url,
                            'node_id': f"alt_{hash(href)%100000}",
                            'c_hash': '',
                            'title': title,
                            'year': year,
                            'found_date': datetime.now().isoformat(),
                            'parsing_method': 'alternative'
                        }
                        
                        gutachten_list.append(gutachten_info)
        
        except Exception as e:
            self.logger.debug(f"Alternative Parsing fehlgeschlagen: {e}")
    
    def _filter_by_date(self, gutachten_list: List[Dict], cutoff_date: datetime) -> List[Dict]:
        """Filtert Gutachten nach Datum (falls verfügbar)"""
        # Da Datumsextraktion komplex ist, geben wir zunächst alle zurück
        # TODO: Implementiere Datums-Parsing aus Gutachten-Details
        return gutachten_list
    
    def fetch_gutachten_content(self, gutachten: Dict) -> Optional[Dict]:
        """
        Lädt den vollständigen Inhalt eines Gutachtens
        
        Args:
            gutachten: Gutachten-Metadaten mit URL
            
        Returns:
            Vollständige Gutachten-Daten oder None
        """
        try:
            url = gutachten['url']
            self.logger.info(f"Lade Gutachten: {gutachten['title']} von {url}")
            
            response = self.session.get(url, timeout=self.config.REQUEST_TIMEOUT)
            
            if response.status_code != 200:
                self.logger.warning(f"HTTP {response.status_code} für {url}")
                return None
            
            # Parse Gutachten-Content
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Extrahiere Text-Content
            content = self._extract_gutachten_text(soup)
            
            if not content.strip():
                self.logger.warning(f"Kein Content gefunden für {url}")
                return None
            
            # Erstelle vollständiges Gutachten-Objekt
            full_gutachten = {
                **gutachten,
                'content': content,
                'content_hash': hashlib.md5(content.encode('utf-8')).hexdigest(),
                'scraped_date': datetime.now().isoformat(),
                'word_count': len(content.split())
            }
            
            return full_gutachten
            
        except Exception as e:
            self.logger.error(f"Fehler beim Laden von Gutachten {gutachten.get('url', 'unknown')}: {e}")
            return None
    
    def _extract_gutachten_text(self, soup: BeautifulSoup) -> str:
        """Extrahiert den Haupttext aus einem Gutachten"""
        content_parts = []
        
        try:
            # Suche nach häufigen Content-Containern
            content_selectors = [
                'div.content-wrapper',
                'div.gutachten-content',
                'div.expertise-content',
                'main',
                'article',
                'div.container',
                'div.row'
            ]
            
            content_element = None
            for selector in content_selectors:
                element = soup.select_one(selector)
                if element:
                    content_element = element
                    break
            
            if not content_element:
                content_element = soup.find('body')
            
            if content_element:
                # Entferne Navigation, Footer, etc.
                for unwanted in content_element.find_all(['nav', 'footer', 'header', 'aside']):
                    unwanted.decompose()
                
                # Extrahiere Text
                text = content_element.get_text(separator=' ', strip=True)
                
                # Bereinige Text
                text = re.sub(r'\s+', ' ', text)
                text = text.strip()
                
                return text
            
        except Exception as e:
            self.logger.error(f"Fehler beim Extrahieren des Gutachten-Texts: {e}")
        
        return ""
    
    def add_to_vectordb(self, gutachten_list: List[Dict]) -> bool:
        """
        Fügt neue Gutachten zur Vektor-Datenbank hinzu (korrigierte ChromaDB Integration)
        
        Args:
            gutachten_list: Liste der zu addierenden Gutachten
            
        Returns:
            True wenn erfolgreich
        """
        try:
            if not gutachten_list:
                self.logger.info("Keine neuen Gutachten zum Hinzufügen")
                return True
            
            # Bereite Daten für ChromaDB vor
            documents = []
            metadatas = []
            ids = []
            
            for gutachten in gutachten_list:
                if 'content' not in gutachten or not gutachten['content']:
                    continue
                
                # Document Text
                documents.append(gutachten['content'])
                
                # Metadata (ohne content für Effizienz)
                metadata = {k: v for k, v in gutachten.items() if k != 'content'}
                metadatas.append(metadata)
                
                # Eindeutige ID
                doc_id = gutachten.get('node_id', str(uuid.uuid4()))
                ids.append(doc_id)
            
            if not documents:
                self.logger.warning("Keine gültigen Dokumente zum Hinzufügen gefunden")
                return False
            
            # Verwende korrekte ChromaDBClient-Methode
            success = self.chroma_client.add_documents(
                collection_name=self.config.COLLECTION_NAME,
                documents=documents,
                metadatas=metadatas,
                ids=ids
            )
            
            if success:
                self.logger.info(f"Erfolgreich {len(documents)} Gutachten zur Vektor-DB hinzugefügt")
            else:
                self.logger.error("Fehler beim Hinzufügen zur Vektor-DB")
            
            return success
            
        except Exception as e:
            self.logger.error(f"Fehler beim Hinzufügen zur Vektor-DB: {e}")
            return False
    
    def run_update_cycle(self) -> Dict:
        """
        Führt einen vollständigen Update-Zyklus durch
        
        Returns:
            Statistiken des Update-Zyklus
        """
        start_time = time.time()
        stats = {
            'started_at': datetime.now().isoformat(),
            'gutachten_found': 0,
            'gutachten_fetched': 0,
            'gutachten_added': 0,
            'errors': 0,
            'duration_seconds': 0
        }
        
        try:
            self.logger.info("=== DNOTI Auto-Update Zyklus gestartet ===")
            
            # 1. Suche nach neuen Gutachten
            gutachten_metadata = self.search_recent_gutachten(days_back=30)
            stats['gutachten_found'] = len(gutachten_metadata)
            
            if not gutachten_metadata:
                self.logger.info("Keine neuen Gutachten gefunden")
                return stats
            
            # 2. Lade vollständige Inhalte
            full_gutachten = []
            for metadata in gutachten_metadata[:self.config.BATCH_SIZE]:
                content = self.fetch_gutachten_content(metadata)
                if content:
                    full_gutachten.append(content)
                    stats['gutachten_fetched'] += 1
                else:
                    stats['errors'] += 1
                
                time.sleep(self.config.REQUEST_DELAY_SECONDS)
            
            # 3. Zur Vektor-DB hinzufügen
            if full_gutachten:
                if self.add_to_vectordb(full_gutachten):
                    stats['gutachten_added'] = len(full_gutachten)
                else:
                    stats['errors'] += 1
            
            stats['duration_seconds'] = time.time() - start_time
            
            self.logger.info(f"=== Update-Zyklus abgeschlossen: {stats} ===")
            
        except Exception as e:
            self.logger.error(f"Fehler im Update-Zyklus: {e}")
            stats['errors'] += 1
            stats['duration_seconds'] = time.time() - start_time
        
        return stats

# ========== HAUPTFUNKTION ==========

def main():
    """Hauptfunktion zum Testen des korrigierten Auto-Updaters"""
    try:
        print("DNOTI Auto-Updater - Korrigierte Version")
        print("=" * 50)
        
        # Initialisiere Auto-Updater
        config = DNOTIConfig()
        updater = DNOTIAutoUpdaterFixed(config)
        
        # Führe Update-Zyklus durch
        stats = updater.run_update_cycle()
        
        print("\nUpdate-Statistiken:")
        for key, value in stats.items():
            print(f"  {key}: {value}")
        
        print("\nUpdate-Zyklus abgeschlossen!")
        
    except Exception as e:
        print(f"Fehler: {e}")
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
