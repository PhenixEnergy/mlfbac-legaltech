#!/usr/bin/env python3
"""
DNOTI Auto-Update Service - Optimierte Version für Gutachten-Detail-URLs
Speziell angepasst für https://www.dnoti.de/gutachten/details/?tx_dnotionlineplusapi_expertises[nodeid]=...&cHash=...

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
from urllib.parse import urljoin, urlparse
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
    """Produktionskonfiguration für DNOTI Auto-Update mit Gutachten-URL-Optimierung"""
    
    # DNOTI TYPO3 Konfiguration
    BASE_URL: str = "https://www.dnoti.de/gutachten/"
    SEARCH_ENDPOINT: str = "https://www.dnoti.de/gutachten/"
    DETAILS_URL_PATTERN: str = "/gutachten/details/"
    
    # Exakte URL-Pattern für Gutachten-Details
    GUTACHTEN_DETAIL_PATTERN: str = r'/gutachten/details/\?tx_dnotionlineplusapi_expertises%5Bnodeid%5D=[a-f0-9-]+&cHash=[a-f0-9]+'
    
    # TYPO3 Formular-Parameter
    FORM_FIELD_PREFIX: str = "tx_dnotionlineplusapi_expertises"
    
    # Update-Strategien
    CHECK_INTERVAL_HOURS: int = 6
    BATCH_SIZE: int = 10
    MAX_PAGES_PER_RUN: int = 5
    
    # Performance & Rate Limiting
    REQUEST_DELAY_SECONDS: float = 2.0
    REQUEST_TIMEOUT_SECONDS: int = 30
    MAX_RETRIES: int = 3
    
    # Content-Validierung
    MIN_CONTENT_LENGTH: int = 200
    REQUIRED_KEYWORDS: List[str] = None
    
    # Datenbank
    COLLECTION_NAME: str = "dnoti_legal_documents"
    
    # Logging
    LOG_LEVEL: str = "INFO"
    LOG_FILE: str = "logs/dnoti_auto_update.log"
    
    def __post_init__(self):
        if self.REQUIRED_KEYWORDS is None:
            self.REQUIRED_KEYWORDS = [
                "gutachten", "rechtsbezug", "aktenzeichen", "entscheidung",
                "rechtsprechung", "sachverhalt", "norm"
            ]

# ========== DNOTI SCRAPER ==========

class DNOTIOptimizedScraper:
    """Optimierter DNOTI Scraper für Gutachten-Detail-URLs"""
    
    def __init__(self, config: DNOTIConfig):
        self.config = config
        self.session = requests.Session()
        
        # Optimierte Headers für TYPO3
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8',
            'Accept-Language': 'de-DE,de;q=0.9,en;q=0.8',
            'Accept-Encoding': 'gzip, deflate, br',
            'Cache-Control': 'no-cache',
            'Upgrade-Insecure-Requests': '1',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'none'
        })
        
        self.processed_urls: Set[str] = set()
        self.content_hashes: Set[str] = set()
        
        # Setup Logging
        self._setup_logging()
    
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
        self.logger.info("DNOTI Optimized Scraper initialisiert")
    
    def scan_for_gutachten_urls(self) -> List[str]:
        """Scannt nach Gutachten-Detail-URLs mit optimierten Suchmustern"""
        all_urls = set()
        
        # Scanne mehrere Jahre für vollständige Abdeckung
        current_year = datetime.now().year
        years_to_scan = [current_year, current_year - 1]
        
        for year in years_to_scan:
            year_urls = self._scan_year_for_urls(year)
            all_urls.update(year_urls)
            
            self.logger.info(f"Jahr {year}: {len(year_urls)} URLs gefunden")
            time.sleep(self.config.REQUEST_DELAY_SECONDS)
        
        # Konvertiere zu Liste und filtere nach Gutachten-Detail-Pattern
        filtered_urls = []
        detail_pattern = re.compile(self.config.GUTACHTEN_DETAIL_PATTERN, re.I)
        
        for url in all_urls:
            if detail_pattern.search(url):
                filtered_urls.append(url)
        
        self.logger.info(f"Gesamt gefilterte Gutachten-URLs: {len(filtered_urls)}")
        return filtered_urls
    
    def _scan_year_for_urls(self, year: int) -> Set[str]:
        """Scannt ein spezifisches Jahr nach Gutachten-URLs"""
        urls = set()
        
        for page_num in range(1, self.config.MAX_PAGES_PER_RUN + 1):
            try:
                page_urls = self._extract_urls_from_page(year, page_num)
                urls.update(page_urls)
                
                self.logger.debug(f"Jahr {year}, Seite {page_num}: {len(page_urls)} URLs")
                
                # Rate limiting
                time.sleep(self.config.REQUEST_DELAY_SECONDS)
                
            except Exception as e:
                self.logger.error(f"Fehler beim Scannen Jahr {year}, Seite {page_num}: {e}")
                continue
        
        return urls
    
    def _extract_urls_from_page(self, year: int, page: int) -> Set[str]:
        """Extrahiert URLs von einer spezifischen Seite"""
        
        # TYPO3-spezifische Parameter für Jahresfilterung
        form_data = {
            f'{self.config.FORM_FIELD_PREFIX}[year]': str(year),
            f'{self.config.FORM_FIELD_PREFIX}[page]': str(page),
            f'{self.config.FORM_FIELD_PREFIX}[action]': 'list'
        }
        
        try:
            response = self._make_request('POST', self.config.SEARCH_ENDPOINT, data=form_data)
            if not response:
                return set()
            
            soup = BeautifulSoup(response.text, 'html.parser')
            urls = self._extract_gutachten_urls_from_soup(soup)
            
            # Debug-Ausgabe für Entwicklung
            self._save_debug_page(soup, year, page)
            
            return urls
            
        except Exception as e:
            self.logger.error(f"Fehler beim Extrahieren von URLs (Jahr {year}, Seite {page}): {e}")
            return set()
    
    def _extract_gutachten_urls_from_soup(self, soup: BeautifulSoup) -> Set[str]:
        """Extrahiert Gutachten-Detail-URLs aus HTML mit optimierten Suchmustern"""
        urls = set()
        
        # Primäres Pattern: Exakte DNOTI Gutachten-Detail-URLs
        primary_pattern = re.compile(self.config.GUTACHTEN_DETAIL_PATTERN, re.I)
        
        # Sekundäres Pattern: Allgemeinere Gutachten-Details-URLs
        secondary_pattern = re.compile(
            r'/gutachten/details/.*tx_dnotionlineplusapi_expertises.*nodeid',
            re.I
        )
        
        # Suche mit primärem Pattern (höchste Priorität)
        primary_links = soup.find_all('a', href=primary_pattern)
        self.logger.debug(f"Primäres Pattern gefunden: {len(primary_links)} Links")
        
        for link in primary_links:
            href = link.get('href')
            if href:
                full_url = self._normalize_url(href)
                if full_url:
                    urls.add(full_url)
        
        # Fallback: Sekundäres Pattern wenn wenig gefunden
        if len(urls) < 5:
            secondary_links = soup.find_all('a', href=secondary_pattern)
            self.logger.debug(f"Sekundäres Pattern gefunden: {len(secondary_links)} zusätzliche Links")
            
            for link in secondary_links:
                href = link.get('href')
                if href:
                    full_url = self._normalize_url(href)
                    if full_url and self.config.DETAILS_URL_PATTERN in full_url:
                        urls.add(full_url)
        
        # Alternative Extraction-Strategien
        if len(urls) < 3:
            alternative_urls = self._extract_from_alternative_methods(soup)
            urls.update(alternative_urls)
        
        return urls
    
    def _extract_from_alternative_methods(self, soup: BeautifulSoup) -> Set[str]:
        """Alternative Extraktionsmethoden für URLs"""
        urls = set()
        
        # Methode 1: Alle Links mit "details" im href
        detail_links = soup.find_all('a', href=re.compile(r'details', re.I))
        for link in detail_links:
            href = link.get('href')
            if href and 'gutachten' in href.lower():
                full_url = self._normalize_url(href)
                if full_url:
                    urls.add(full_url)
        
        # Methode 2: Links in Listen-Elementen
        lists = soup.find_all(['ul', 'ol'])
        for list_elem in lists:
            items = list_elem.find_all('li')
            for item in items:
                link = item.find('a', href=True)
                if link:
                    href = link.get('href')
                    if href and 'gutachten' in href.lower() and 'details' in href.lower():
                        full_url = self._normalize_url(href)
                        if full_url:
                            urls.add(full_url)
        
        # Methode 3: Tabellenzeilen
        tables = soup.find_all('table')
        for table in tables:
            rows = table.find_all('tr')
            for row in rows:
                link = row.find('a', href=True)
                if link:
                    href = link.get('href')
                    if href and 'gutachten' in href.lower() and 'details' in href.lower():
                        full_url = self._normalize_url(href)
                        if full_url:
                            urls.add(full_url)
        
        self.logger.debug(f"Alternative Methoden gefunden: {len(urls)} URLs")
        return urls
    
    def _normalize_url(self, href: str) -> Optional[str]:
        """Normalisiert und validiert URLs"""
        if not href:
            return None
        
        # Erstelle vollständige URL
        if not href.startswith('http'):
            full_url = urljoin(self.config.BASE_URL, href)
        else:
            full_url = href
        
        # Validierung
        if 'dnoti.de' not in full_url:
            return None
        
        # URL-Dekodierung für TYPO3-Parameter
        if '%5B' in full_url and '%5D' in full_url:
            # URL ist bereits encodiert, belasse so
            pass
        
        return full_url
    
    def _make_request(self, method: str, url: str, **kwargs) -> Optional[requests.Response]:
        """Macht HTTP-Request mit Retry-Logik"""
        for attempt in range(self.config.MAX_RETRIES):
            try:
                if method.upper() == 'POST':
                    response = self.session.post(
                        url,
                        timeout=self.config.REQUEST_TIMEOUT_SECONDS,
                        **kwargs
                    )
                else:
                    response = self.session.get(
                        url,
                        timeout=self.config.REQUEST_TIMEOUT_SECONDS,
                        **kwargs
                    )
                
                response.raise_for_status()
                return response
                
            except requests.RequestException as e:
                self.logger.warning(f"Request-Fehler (Versuch {attempt + 1}): {e}")
                if attempt < self.config.MAX_RETRIES - 1:
                    time.sleep(2 ** attempt)  # Exponential backoff
                continue
        
        return None
    
    def _save_debug_page(self, soup: BeautifulSoup, year: int, page: int):
        """Speichert Debug-HTML für Analyse"""
        debug_file = f"debug_response_year_{year}_page_{page}.html"
        try:
            with open(debug_file, 'w', encoding='utf-8') as f:
                f.write(soup.prettify())
        except Exception as e:
            self.logger.warning(f"Konnte Debug-Datei nicht speichern: {e}")
    
    def extract_gutachten_content(self, url: str) -> Optional[Dict]:
        """Extrahiert Gutachten-Inhalt von einer Detail-URL"""
        try:
            response = self._make_request('GET', url)
            if not response:
                return None
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Titel extrahieren
            title = self._extract_title(soup)
            
            # Hauptinhalt extrahieren
            content = self._extract_content(soup)
            
            # Metadaten extrahieren
            metadata = self._extract_metadata(soup)
            
            if not content or len(content) < self.config.MIN_CONTENT_LENGTH:
                self.logger.warning(f"Zu wenig Inhalt gefunden: {url}")
                return None
            
            # Content-Hash für Duplikatserkennung
            content_hash = hashlib.sha256(content.encode()).hexdigest()
            if content_hash in self.content_hashes:
                self.logger.info(f"Duplikat erkannt: {url}")
                return None
            
            self.content_hashes.add(content_hash)
            
            return {
                'id': str(uuid.uuid4()),
                'title': title,
                'content': content,
                'url': url,
                'metadata': metadata,
                'scraped_at': datetime.now().isoformat(),
                'content_hash': content_hash
            }
            
        except Exception as e:
            self.logger.error(f"Fehler beim Extrahieren von {url}: {e}")
            return None
    
    def _extract_title(self, soup: BeautifulSoup) -> str:
        """Extrahiert Titel des Gutachtens"""
        # Verschiedene Selektoren für Titel
        title_selectors = [
            'h1',
            '.title',
            '.headline',
            '.gutachten-title',
            '[data-title]'
        ]
        
        for selector in title_selectors:
            title_elem = soup.select_one(selector)
            if title_elem:
                title = title_elem.get_text().strip()
                if title and len(title) > 5:
                    return title
        
        # Fallback: Aus page title
        if soup.title:
            title = soup.title.get_text().strip()
            if 'gutachten' in title.lower():
                return title
        
        return "Unbekannter Titel"
    
    def _extract_content(self, soup: BeautifulSoup) -> str:
        """Extrahiert Hauptinhalt des Gutachtens"""
        content_parts = []
        
        # Entferne unerwünschte Elemente
        for unwanted in soup(['nav', 'aside', 'footer', 'header', '.navigation', '.advertisement']):
            unwanted.decompose()
        
        # Verschiedene Content-Selektoren
        content_selectors = [
            '.content',
            '.main-content',
            'article',
            '.gutachten-content',
            'main'
        ]
        
        for selector in content_selectors:
            content_div = soup.select_one(selector)
            if content_div:
                # Extrahiere Paragraphen
                paragraphs = content_div.find_all(['p', 'div'])
                for p in paragraphs:
                    text = p.get_text().strip()
                    if text and len(text) > 20:  # Filtere sehr kurze Texte
                        content_parts.append(text)
                break
        
        # Fallback: Alle Paragraphen
        if not content_parts:
            paragraphs = soup.find_all('p')
            for p in paragraphs:
                text = p.get_text().strip()
                if text and len(text) > 20:
                    content_parts.append(text)
        
        return '\n\n'.join(content_parts)
    
    def _extract_metadata(self, soup: BeautifulSoup) -> Dict:
        """Extrahiert Metadaten des Gutachtens"""
        metadata = {}
        
        # Aktenzeichen
        for elem in soup.find_all(text=re.compile(r'aktenzeichen', re.I)):
            parent = elem.parent
            if parent:
                text = parent.get_text(strip=True)
                if ':' in text:
                    metadata['aktenzeichen'] = text.split(':', 1)[1].strip()
                    break
        
        # Erscheinungsdatum
        for elem in soup.find_all(text=re.compile(r'datum|erschein', re.I)):
            parent = elem.parent
            if parent:
                text = parent.get_text(strip=True)
                # Suche nach Datumsmuster
                date_match = re.search(r'\d{1,2}\.\d{1,2}\.\d{4}', text)
                if date_match:
                    metadata['erscheinungsdatum'] = date_match.group()
                    break
        
        # Rechtsbezug
        for elem in soup.find_all(text=re.compile(r'rechtsbezug', re.I)):
            parent = elem.parent
            if parent:
                text = parent.get_text(strip=True)
                if ':' in text:
                    metadata['rechtsbezug'] = text.split(':', 1)[1].strip()
                    break
        
        return metadata

# ========== DATABASE INTEGRATION ==========

class DNOTIDatabaseManager:
    """Verwaltet Datenbankoperationen für DNOTI Gutachten"""
    
    def __init__(self, config: DNOTIConfig):
        self.config = config
        self.logger = logging.getLogger(self.__class__.__name__)
        
        try:
            self.chroma_client = ChromaDBClient()
            self.collection = self.chroma_client.get_collection(config.COLLECTION_NAME)
            self.logger.info(f"Verbunden mit ChromaDB Collection: {config.COLLECTION_NAME}")
        except Exception as e:
            self.logger.error(f"Fehler bei ChromaDB-Verbindung: {e}")
            self.chroma_client = None
            self.collection = None
    
    def add_gutachten(self, gutachten_data: Dict) -> bool:
        """Fügt ein Gutachten zur Datenbank hinzu"""
        if not self.collection:
            self.logger.error("Keine Datenbankverbindung verfügbar")
            return False
        
        try:
            # Prüfe auf Duplikate
            if self._is_duplicate(gutachten_data):
                self.logger.info(f"Duplikat übersprungen: {gutachten_data['title'][:50]}...")
                return False
            
            # Füge zur ChromaDB hinzu
            self.collection.add(
                documents=[gutachten_data['content']],
                metadatas=[{
                    'title': gutachten_data['title'],
                    'url': gutachten_data['url'],
                    'scraped_at': gutachten_data['scraped_at'],
                    'content_hash': gutachten_data['content_hash'],
                    **gutachten_data.get('metadata', {})
                }],
                ids=[gutachten_data['id']]
            )
            
            self.logger.info(f"Gutachten hinzugefügt: {gutachten_data['title'][:50]}...")
            return True
            
        except Exception as e:
            self.logger.error(f"Fehler beim Hinzufügen des Gutachtens: {e}")
            return False
    
    def _is_duplicate(self, gutachten_data: Dict) -> bool:
        """Prüft auf Duplikate basierend auf Content-Hash oder URL"""
        try:
            # Suche nach gleichen URLs
            results = self.collection.query(
                query_texts=[""],
                where={"url": gutachten_data['url']},
                n_results=1
            )
            
            if results['ids'] and len(results['ids'][0]) > 0:
                return True
            
            # Suche nach gleichem Content-Hash
            results = self.collection.query(
                query_texts=[""],
                where={"content_hash": gutachten_data['content_hash']},
                n_results=1
            )
            
            return results['ids'] and len(results['ids'][0]) > 0
            
        except Exception as e:
            self.logger.warning(f"Fehler bei Duplikatsprüfung: {e}")
            return False
    
    def get_statistics(self) -> Dict:
        """Gibt Datenbankstatistiken zurück"""
        if not self.collection:
            return {"error": "Keine Datenbankverbindung"}
        
        try:
            count = self.collection.count()
            return {
                "total_documents": count,
                "collection_name": self.config.COLLECTION_NAME,
                "last_updated": datetime.now().isoformat()
            }
        except Exception as e:
            self.logger.error(f"Fehler beim Abrufen der Statistiken: {e}")
            return {"error": str(e)}

# ========== MAIN AUTO-UPDATE SERVICE ==========

class DNOTIAutoUpdateService:
    """Hauptservice für automatische DNOTI Updates"""
    
    def __init__(self):
        self.config = DNOTIConfig()
        self.scraper = DNOTIOptimizedScraper(self.config)
        self.db_manager = DNOTIDatabaseManager(self.config)
        self.logger = logging.getLogger(self.__class__.__name__)
        
        self.logger.info("DNOTI Auto-Update Service initialisiert")
    
    def run_update_cycle(self) -> Dict:
        """Führt einen kompletten Update-Zyklus durch"""
        start_time = time.time()
        stats = {
            "start_time": datetime.now().isoformat(),
            "urls_found": 0,
            "documents_added": 0,
            "duplicates_skipped": 0,
            "errors": 0
        }
        
        try:
            self.logger.info("Starte Update-Zyklus...")
            
            # 1. Scanne nach Gutachten-URLs
            self.logger.info("Scanne nach Gutachten-URLs...")
            urls = self.scraper.scan_for_gutachten_urls()
            stats["urls_found"] = len(urls)
            
            if not urls:
                self.logger.warning("Keine URLs gefunden")
                return stats
            
            self.logger.info(f"Gefunden: {len(urls)} Gutachten-URLs")
            
            # 2. Verarbeite jede URL
            for i, url in enumerate(urls):
                if url in self.scraper.processed_urls:
                    stats["duplicates_skipped"] += 1
                    continue
                
                self.logger.info(f"Verarbeite ({i+1}/{len(urls)}): {url}")
                
                # Extrahiere Gutachten-Inhalt
                gutachten_data = self.scraper.extract_gutachten_content(url)
                if gutachten_data:
                    # Füge zur Datenbank hinzu
                    if self.db_manager.add_gutachten(gutachten_data):
                        stats["documents_added"] += 1
                    else:
                        stats["duplicates_skipped"] += 1
                else:
                    stats["errors"] += 1
                
                # Markiere URL als verarbeitet
                self.scraper.processed_urls.add(url)
                
                # Rate limiting
                time.sleep(self.config.REQUEST_DELAY_SECONDS)
        
        except Exception as e:
            self.logger.error(f"Fehler im Update-Zyklus: {e}")
            stats["errors"] += 1
        
        # Finale Statistiken
        end_time = time.time()
        stats["end_time"] = datetime.now().isoformat()
        stats["duration_seconds"] = round(end_time - start_time, 2)
        
        self.logger.info(f"Update-Zyklus abgeschlossen: {stats}")
        return stats
    
    def run_continuous(self):
        """Führt kontinuierliche Updates durch"""
        self.logger.info("Starte kontinuierlichen Update-Modus...")
        
        while True:
            try:
                # Führe Update-Zyklus durch
                stats = self.run_update_cycle()
                
                # Zeige Zusammenfassung
                self.logger.info(
                    f"Zyklus abgeschlossen - "
                    f"URLs: {stats['urls_found']}, "
                    f"Hinzugefügt: {stats['documents_added']}, "
                    f"Übersprungen: {stats['duplicates_skipped']}, "
                    f"Fehler: {stats['errors']}"
                )
                
                # Warte bis zum nächsten Zyklus
                sleep_seconds = self.config.CHECK_INTERVAL_HOURS * 3600
                self.logger.info(f"Nächster Zyklus in {self.config.CHECK_INTERVAL_HOURS} Stunden...")
                time.sleep(sleep_seconds)
                
            except KeyboardInterrupt:
                self.logger.info("Update-Service gestoppt durch Benutzer")
                break
            except Exception as e:
                self.logger.error(f"Unerwarteter Fehler: {e}")
                time.sleep(300)  # 5 Minuten warten bei Fehler

# ========== MAIN ENTRY POINT ==========

def main():
    """Haupteinstiegspunkt"""
    print("="*60)
    print("DNOTI Auto-Update Service - Optimierte Version")
    print("Spezialisiert auf Gutachten-Detail-URLs")
    print("="*60)
    
    # Erstelle Service
    service = DNOTIAutoUpdateService()
    
    # Zeige Konfiguration
    db_stats = service.db_manager.get_statistics()
    print(f"Datenbank: {db_stats}")
    print(f"Check-Intervall: {service.config.CHECK_INTERVAL_HOURS} Stunden")
    print(f"Max. Seiten pro Durchlauf: {service.config.MAX_PAGES_PER_RUN}")
    print()
    
    try:
        # Frage Benutzer nach Modus
        mode = input("Modus wählen:\n1. Einmaliger Durchlauf\n2. Kontinuierlicher Betrieb\nEingabe (1/2): ").strip()
        
        if mode == "1":
            print("\nStarte einmaligen Update-Durchlauf...")
            stats = service.run_update_cycle()
            print(f"\nErgebnis: {stats}")
        
        elif mode == "2":
            print("\nStarte kontinuierlichen Betrieb...")
            service.run_continuous()
        
        else:
            print("Ungültige Eingabe. Starte einmaligen Durchlauf...")
            stats = service.run_update_cycle()
            print(f"\nErgebnis: {stats}")
    
    except KeyboardInterrupt:
        print("\nService gestoppt durch Benutzer")
    except Exception as e:
        print(f"Unerwarteter Fehler: {e}")

if __name__ == "__main__":
    main()
