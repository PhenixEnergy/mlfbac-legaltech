#!/usr/bin/env python3
"""
DNOTI Auto-Update Service - Windows-kompatible Version
Optimiert für TYPO3-basierte DNOTI Website

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
    """Produktionskonfiguration für DNOTI Auto-Update"""
      # DNOTI TYPO3 Konfiguration
    BASE_URL: str = "https://www.dnoti.de/gutachten/"
    SEARCH_ENDPOINT: str = "https://www.dnoti.de/gutachten/"
    DETAILS_URL_PATTERN: str = "/gutachten/details/"
    
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

class DNOTIProductionScraper:
    """Produktionsreifer DNOTI TYPO3 Scraper"""
    
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
        """Konfiguriert Logging ohne Emojis für Windows"""
        log_file = Path(self.config.LOG_FILE)
        log_file.parent.mkdir(parents=True, exist_ok=True)
        
        # Logger erstellen
        self.logger = logging.getLogger(f"{__name__}.scraper")
        self.logger.setLevel(getattr(logging, self.config.LOG_LEVEL))
        
        if not self.logger.handlers:
            # File Handler
            file_handler = logging.FileHandler(log_file, encoding='utf-8')
            file_formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            file_handler.setFormatter(file_formatter)
            self.logger.addHandler(file_handler)
    
    def search_gutachten_by_year(self, year: int = None) -> List[Dict]:
        """Sucht Gutachten über TYPO3 Formular-API"""
        
        if year is None:
            year = datetime.now().year
        
        self.logger.info(f"Suche Gutachten für Jahr: {year}")
        
        # Erst die Hauptseite aufrufen für Session/Cookies
        try:
            main_response = self.session.get(self.config.BASE_URL, timeout=self.config.REQUEST_TIMEOUT_SECONDS)
            main_response.raise_for_status()
            self.logger.info("Hauptseite erfolgreich geladen")
            
            time.sleep(self.config.REQUEST_DELAY_SECONDS)
            
        except Exception as e:
            self.logger.error(f"Fehler beim Laden der Hauptseite: {e}")
            return []
        
        # Erst prüfen: Gibt es überhaupt eine Suchfunktion mit Jahr?
        soup = BeautifulSoup(main_response.content, 'html.parser')
        year_input = soup.find('input', {'name': f'{self.config.FORM_FIELD_PREFIX}[reportYear]'})
        
        if not year_input:
            self.logger.warning("Keine Jahressuche gefunden - verwende allgemeine Suche")
            return self._search_general_content(soup)
        
        # TYPO3 Formular-Daten für Jahressuche
        form_data = {
            f'{self.config.FORM_FIELD_PREFIX}[page]': '1',
            f'{self.config.FORM_FIELD_PREFIX}[searchTitle]': '',
            f'{self.config.FORM_FIELD_PREFIX}[searchText]': '',
            f'{self.config.FORM_FIELD_PREFIX}[expertisesType]': 'dnotiReport',
            f'{self.config.FORM_FIELD_PREFIX}[reportYear]': str(year),
            f'{self.config.FORM_FIELD_PREFIX}[reportPage]': '',
            f'{self.config.FORM_FIELD_PREFIX}[expertiseReference]': ''
        }
        
        gutachten_list = []
        page = 1
        
        while page <= self.config.MAX_PAGES_PER_RUN:
            self.logger.info(f"Verarbeite Seite {page} für Jahr {year}")
            
            # Update Seitenzahl
            form_data[f'{self.config.FORM_FIELD_PREFIX}[page]'] = str(page)
            
            try:
                # POST Request an TYPO3
                response = self.session.post(
                    self.config.SEARCH_ENDPOINT,
                    data=form_data,
                    timeout=self.config.REQUEST_TIMEOUT_SECONDS
                )
                response.raise_for_status()
                
                # Speichere Response für Debugging
                debug_file = f"debug_response_year_{year}_page_{page}.html"
                with open(debug_file, 'w', encoding='utf-8') as f:
                    f.write(response.text)
                self.logger.info(f"Debug Response gespeichert: {debug_file}")
                
                soup = BeautifulSoup(response.content, 'html.parser')
                
                # Suche nach Ergebnisliste
                results = self._extract_search_results(soup, year, page)
                
                if not results:
                    self.logger.info(f"Keine weiteren Ergebnisse auf Seite {page}")
                    break
                
                gutachten_list.extend(results)
                self.logger.info(f"{len(results)} Gutachten auf Seite {page} gefunden")
                
                # Rate Limiting
                time.sleep(self.config.REQUEST_DELAY_SECONDS)
                page += 1
                
            except Exception as e:
                self.logger.error(f"Fehler bei Seite {page}: {e}")
                break
        
        self.logger.info(f"Gesamt gefunden: {len(gutachten_list)} Gutachten für Jahr {year}")
        return gutachten_list
    
    def _search_general_content(self, soup: BeautifulSoup) -> List[Dict]:
        """Fallback: Allgemeine Suche ohne Jahr"""
        
        self.logger.info("Führe allgemeine Content-Suche durch")
        
        # Suche nach allen relevanten Links auf der Hauptseite
        potential_links = []
        
        # Links die auf Gutachten hindeuten
        for link in soup.find_all('a', href=True):
            href = link.get('href')
            text = link.get_text().strip()
            
            # Prüfe ob Link relevant ist
            if any(keyword in href.lower() for keyword in ['details', 'gutachten', 'expertis']):
                if any(keyword in text.lower() for keyword in ['gutachten', '20', 'nr']):
                    potential_links.append({
                        'url': urljoin(self.config.BASE_URL, href),
                        'title': text
                    })
        
        # Konvertiere zu Standard-Format
        results = []
        for link_data in potential_links[:20]:  # Maximal 20 Links
            gutachten_data = self._create_gutachten_from_link(link_data)
            if gutachten_data:
                results.append(gutachten_data)
        
        self.logger.info(f"Allgemeine Suche: {len(results)} potentielle Gutachten gefunden")
        return results
    
    def _extract_search_results(self, soup: BeautifulSoup, year: int, page: int) -> List[Dict]:
        """Extrahiert Suchergebnisse aus TYPO3 Response"""
        
        results = []
        
        # Verschiedene Strategien für Ergebnisextraktion
        strategies = [
            self._extract_from_result_containers,
            self._extract_from_tables,
            self._extract_from_lists,
            self._extract_from_links
        ]
        
        for strategy in strategies:
            try:
                strategy_results = strategy(soup)
                if strategy_results:
                    self.logger.info(f"Strategie {strategy.__name__} erfolgreich: {len(strategy_results)} Ergebnisse")
                    results.extend(strategy_results)
                    break  # Verwende erste erfolgreiche Strategie
            except Exception as e:
                self.logger.warning(f"Strategie {strategy.__name__} fehlgeschlagen: {e}")
        
        return results
    
    def _extract_from_result_containers(self, soup: BeautifulSoup) -> List[Dict]:
        """Extraktion aus Result-Containern"""
        results = []
        
        selectors = [
            '.result-list .result-item',
            '.entries-list .entry',
            '.gutachten-list .gutachten-item',
            '.search-results .result',
            '.content-element'
        ]
        
        for selector in selectors:
            elements = soup.select(selector)
            if elements:
                for element in elements:
                    gutachten_data = self._parse_gutachten_element(element)
                    if gutachten_data:
                        results.append(gutachten_data)
                break
        
        return results
    
    def _extract_from_tables(self, soup: BeautifulSoup) -> List[Dict]:
        """Extraktion aus Tabellen"""
        results = []
        
        tables = soup.find_all('table')
        for table in tables:
            rows = table.find_all('tr')[1:]  # Skip header
            for row in rows:
                cells = row.find_all(['td', 'th'])
                if len(cells) >= 2:  # Mindestens 2 Spalten
                    # Suche nach Links in der Zeile
                    link = row.find('a', href=True)
                    if link:
                        gutachten_data = self._create_gutachten_from_table_row(row, link)
                        if gutachten_data:
                            results.append(gutachten_data)
        
        return results
    
    def _extract_from_lists(self, soup: BeautifulSoup) -> List[Dict]:
        """Extraktion aus Listen"""
        results = []
        
        lists = soup.find_all(['ul', 'ol'])
        for list_elem in lists:
            items = list_elem.find_all('li')
            for item in items:
                link = item.find('a', href=True)
                if link:                    gutachten_data = self._create_gutachten_from_link({
                        'url': urljoin(self.config.BASE_URL, link.get('href')),
                        'title': link.get_text().strip()
                    })
                    if gutachten_data:
                        results.append(gutachten_data)
        
        return results
    
    def _extract_from_links(self, soup: BeautifulSoup) -> List[Dict]:
        """Optimierte Extraktion aus Gutachten-Detail-Links mit verbesserter URL-Erkennung"""
        results = []
        
        # Primäres Pattern: Exakte DNOTI Gutachten-Detail-URLs
        primary_pattern = re.compile(
            r'/gutachten/details/\?tx_dnotionlineplusapi_expertises%5Bnodeid%5D=[a-f0-9-]+&cHash=[a-f0-9]+',
            re.I
        )
        
        # Sekundäres Pattern: Allgemeinere Gutachten-Details-URLs
        secondary_pattern = re.compile(
            r'/gutachten/details/.*tx_dnotionlineplusapi_expertises.*nodeid',
            re.I
        )
        
        # Tertiäres Pattern: Fallback für andere Gutachten-Links
        tertiary_pattern = re.compile(r'(details.*gutachten|gutachten.*details)', re.I)
        
        # Suche mit primärem Pattern (höchste Priorität)
        relevant_links = soup.find_all('a', href=primary_pattern)
        logging.info(f"Primäres Pattern gefunden: {len(relevant_links)} Links")
        
        # Wenn nicht genug Links gefunden, verwende sekundäres Pattern
        if len(relevant_links) < 5:
            additional_links = soup.find_all('a', href=secondary_pattern)
            relevant_links.extend(additional_links)
            logging.info(f"Sekundäres Pattern gefunden: {len(additional_links)} zusätzliche Links")
        
        # Als letzter Fallback: allgemeine Gutachten-Links
        if len(relevant_links) < 3:
            fallback_links = soup.find_all('a', href=tertiary_pattern)
            relevant_links.extend(fallback_links)
            logging.info(f"Tertiäres Pattern gefunden: {len(fallback_links)} Fallback-Links")
        
        # Deduplizierung basierend auf href
        seen_urls = set()
        unique_links = []
        for link in relevant_links:
            href = link.get('href')
            if href and href not in seen_urls:
                seen_urls.add(href)
                unique_links.append(link)
        
        logging.info(f"Nach Deduplizierung: {len(unique_links)} eindeutige Links")
        
        for link in unique_links[:25]:  # Verarbeite bis zu 25 Links
            href = link.get('href')
            if not href:
                continue
                
            # Stelle sicher, dass es ein vollständiger URL ist
            if not href.startswith('http'):
                href = urljoin(self.config.BASE_URL, href)
            
            # Priorität für echte Gutachten-Detail-URLs
            is_priority_url = (
                self.config.DETAILS_URL_PATTERN in href and 
                'tx_dnotionlineplusapi_expertises' in href and 
                'nodeid' in href
            )
            
            if is_priority_url or self.config.DETAILS_URL_PATTERN in href:
                gutachten_data = self._create_gutachten_from_link({
                    'url': href,
                    'title': link.get_text().strip(),
                    'priority': is_priority_url
                })
                if gutachten_data:
                    results.append(gutachten_data)
        
        # Sortiere Ergebnisse: Prioritäts-URLs zuerst
        results.sort(key=lambda x: x.get('priority', False), reverse=True)
        
        return results
    
    def _parse_gutachten_element(self, element) -> Optional[Dict]:
        """Parst ein Gutachten-Element"""
        
        # Suche nach Link
        link = element.find('a')
        if not link or not link.get('href'):
            return None
        
        href = link.get('href')
        if not href.startswith('http'):
            href = urljoin(self.config.BASE_URL, href)
        
        # Extrahiere Titel
        title = link.get_text().strip()
        if not title:
            title_elem = element.find(['h1', 'h2', 'h3', 'h4', '.title', '.headline'])
            title = title_elem.get_text().strip() if title_elem else "Unbekannter Titel"
        
        return self._create_standard_gutachten_dict(href, title, element.get_text())
    
    def _create_gutachten_from_table_row(self, row, link) -> Optional[Dict]:
        """Erstellt Gutachten-Daten aus Tabellenzeile"""
        
        href = urljoin(self.config.BASE_URL, link.get('href'))
        title = link.get_text().strip()
        
        # Extrahiere zusätzliche Daten aus anderen Zellen
        cells = row.find_all(['td', 'th'])
        row_text = ' '.join([cell.get_text().strip() for cell in cells])
        
        return self._create_standard_gutachten_dict(href, title, row_text)
    
    def _create_gutachten_from_link(self, link_data: Dict) -> Optional[Dict]:
        """Erstellt Gutachten-Daten aus Link-Daten"""
        
        url = link_data.get('url', '')
        title = link_data.get('title', '')
        
        if not url or not title or len(title) < 3:
            return None
        
        # Validierung der URL
        if not url.startswith('http') or 'dnoti.de' not in url:
            return None
        
        return self._create_standard_gutachten_dict(url, title, title)
    
    def _create_standard_gutachten_dict(self, url: str, title: str, content_text: str) -> Dict:
        """Erstellt Standard-Gutachten-Dictionary"""
        
        # Extrahiere Gutachten-Nummer aus Text
        gutachten_nummer = "Zu extrahieren"
        nummer_patterns = [
            r'Nr\.\s*(\d+/\d+)',
            r'(\d{4}/\d+)',
            r'Gutachten\s*(\d+)',
            r'([A-Z]\d+/\d+)'
        ]
        
        for pattern in nummer_patterns:
            match = re.search(pattern, content_text)
            if match:
                gutachten_nummer = match.group(1)
                break
        
        # Extrahiere Datum
        erscheinungsdatum = "Zu extrahieren"
        date_patterns = [
            r'(\d{1,2}\.\d{1,2}\.\d{4})',
            r'(\d{4}-\d{2}-\d{2})',
            r'(\d{1,2}/\d{1,2}/\d{4})'
        ]
        
        for pattern in date_patterns:
            match = re.search(pattern, content_text)
            if match:
                erscheinungsdatum = match.group(1)
                break
        
        return {
            'id': str(uuid.uuid4()),
            'url': url,
            'title': title,
            'gutachten_nummer': gutachten_nummer,
            'erscheinungsdatum': erscheinungsdatum,
            'rechtsbezug': "Zu extrahieren",
            'normen': "Zu extrahieren",
            'content': "",  # Wird später durch Detail-Scraping gefüllt
            'scraped_timestamp': datetime.now().isoformat(),
            'metadata': {'source_text': content_text}
        }
    
    def fetch_gutachten_details(self, gutachten_data: Dict) -> Optional[Dict]:
        """Lädt vollständige Details eines Gutachtens"""
        
        url = gutachten_data.get('url')
        if not url:
            return None
        
        self.logger.info(f"Lade Details für: {gutachten_data.get('title', 'Unbekannt')}")
        
        try:
            response = self.session.get(url, timeout=self.config.REQUEST_TIMEOUT_SECONDS)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Extrahiere vollständigen Content
            content = self._extract_full_content(soup)
            
            if content and len(content) >= self.config.MIN_CONTENT_LENGTH:
                # Update Gutachten-Daten
                gutachten_data['content'] = content
                gutachten_data['content_hash'] = hashlib.md5(content.encode()).hexdigest()
                
                # Extrahiere zusätzliche Metadaten
                self._extract_additional_metadata(soup, gutachten_data)
                
                # Markiere als verarbeitet
                self.processed_urls.add(url)
                
                return gutachten_data
            else:
                self.logger.warning(f"Unzureichender Content für: {url}")
                return None
                
        except Exception as e:
            self.logger.error(f"Fehler beim Laden der Details für {url}: {e}")
            return None
    
    def _extract_full_content(self, soup: BeautifulSoup) -> str:
        """Extrahiert vollständigen Content aus Detail-Seite"""
        
        # Verschiedene Content-Selektoren probieren
        content_selectors = [
            '.content',
            '.main-content',
            '.page-content',
            '.gutachten-content',
            '.detail-content',
            'main',
            '.container .row',
            '#content',
            'article'
        ]
        
        for selector in content_selectors:
            content_div = soup.select_one(selector)
            if content_div:
                # Entferne Navigation und unwichtige Elemente
                for unwanted in content_div.find_all(['nav', 'header', 'footer', '.navigation', '.menu']):
                    unwanted.decompose()
                
                text = content_div.get_text(separator=' ', strip=True)
                if len(text) >= self.config.MIN_CONTENT_LENGTH:
                    return text
        
        # Fallback: Gesamter Body-Text
        body = soup.find('body')
        if body:
            # Entferne Skripts und Styles
            for element in body.find_all(['script', 'style', 'nav', 'header', 'footer']):
                element.decompose()
            
            return body.get_text(separator=' ', strip=True)
        
        return ""
    
    def _extract_additional_metadata(self, soup: BeautifulSoup, gutachten_data: Dict):
        """Extrahiert zusätzliche Metadaten aus Detail-Seite"""
        
        text = soup.get_text().lower()
        
        # Extrahiere Rechtsbezug
        rechtsbezug_patterns = [
            r'rechtsbezug[:\s]*([^\n\.]+)',
            r'rechtsgebiet[:\s]*([^\n\.]+)',
            r'sachgebiet[:\s]*([^\n\.]+)'
        ]
        
        for pattern in rechtsbezug_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                gutachten_data['rechtsbezug'] = match.group(1).strip()
                break
        
        # Extrahiere Normen
        norm_patterns = [
            r'§\s*\d+[a-z]?\s*[A-Z]{2,4}',
            r'art\.\s*\d+',
            r'artikel\s*\d+'
        ]
        
        normen = []
        for pattern in norm_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            normen.extend(matches)
        
        if normen:
            gutachten_data['normen'] = '; '.join(set(normen))

# ========== HAUPT-UPDATE SERVICE ==========

class DNOTIAutoUpdateService:
    """Haupt-Service für automatische DNOTI Updates"""
    
    def __init__(self, config: DNOTIConfig = None):
        self.config = config or DNOTIConfig()
        self.scraper = DNOTIProductionScraper(self.config)
        self.chroma_client = None
        
        # Setup Logging
        self.logger = logging.getLogger(f"{__name__}.service")
        
        # Setup ChromaDB
        self._setup_database()
    
    def _setup_database(self):
        """Initialisiert ChromaDB"""
        try:
            self.chroma_client = ChromaDBClient()
            self.logger.info("ChromaDB erfolgreich initialisiert")
        except Exception as e:
            self.logger.error(f"Fehler bei ChromaDB Initialisierung: {e}")
            raise
    
    async def run_update_cycle(self) -> Dict:
        """Führt einen kompletten Update-Zyklus aus"""
        
        start_time = datetime.now()
        self.logger.info("Starte DNOTI Auto-Update Zyklus")
        
        metrics = {
            'start_time': start_time.isoformat(),
            'total_discovered': 0,
            'total_processed': 0,
            'total_added': 0,
            'errors': [],
            'success_rate': 0.0
        }
        
        try:
            # Suche neue Gutachten der letzten 2 Jahre
            current_year = datetime.now().year
            years_to_search = [current_year, current_year - 1]
            
            all_gutachten = []
            
            for year in years_to_search:
                self.logger.info(f"Suche Gutachten für Jahr: {year}")
                gutachten = self.scraper.search_gutachten_by_year(year)
                all_gutachten.extend(gutachten)
                
                # Rate limiting zwischen Jahren
                await asyncio.sleep(self.config.REQUEST_DELAY_SECONDS)
            
            metrics['total_discovered'] = len(all_gutachten)
            self.logger.info(f"Insgesamt entdeckt: {len(all_gutachten)} Gutachten")
            
            # Verarbeite Gutachten in Batches
            added_count = 0
            
            for i in range(0, len(all_gutachten), self.config.BATCH_SIZE):
                batch = all_gutachten[i:i + self.config.BATCH_SIZE]
                self.logger.info(f"Verarbeite Batch {i//self.config.BATCH_SIZE + 1}")
                
                batch_results = await self._process_batch(batch)
                added_count += batch_results
                
                metrics['total_processed'] += len(batch)
                
                # Rate limiting zwischen Batches
                await asyncio.sleep(self.config.REQUEST_DELAY_SECONDS * 2)
            
            metrics['total_added'] = added_count
            metrics['success_rate'] = (added_count / len(all_gutachten) * 100) if all_gutachten else 0
            
            end_time = datetime.now()
            duration = (end_time - start_time).total_seconds()
            
            metrics['end_time'] = end_time.isoformat()
            metrics['duration_seconds'] = duration
            
            self.logger.info(f"Update-Zyklus abgeschlossen: {added_count}/{len(all_gutachten)} erfolgreich")
            
            return metrics
            
        except Exception as e:
            self.logger.error(f"Fehler im Update-Zyklus: {e}")
            metrics['errors'].append(str(e))
            return metrics
    
    async def _process_batch(self, batch: List[Dict]) -> int:
        """Verarbeitet einen Batch von Gutachten"""
        
        added_count = 0
        
        for gutachten_data in batch:
            try:
                # Lade vollständige Details
                detailed_gutachten = self.scraper.fetch_gutachten_details(gutachten_data)
                
                if detailed_gutachten and self._is_new_content(detailed_gutachten):
                    # Füge zur Datenbank hinzu
                    success = self._add_to_database(detailed_gutachten)
                    if success:
                        added_count += 1
                        self.logger.info(f"Hinzugefügt: {detailed_gutachten.get('title', 'Unbekannt')}")
                    else:
                        self.logger.warning(f"Fehler beim Hinzufügen: {detailed_gutachten.get('title', 'Unbekannt')}")
                
                # Rate limiting zwischen einzelnen Gutachten
                await asyncio.sleep(self.config.REQUEST_DELAY_SECONDS)
                
            except Exception as e:
                self.logger.error(f"Fehler bei Gutachten-Verarbeitung: {e}")
        
        return added_count
    
    def _is_new_content(self, gutachten_data: Dict) -> bool:
        """Prüft ob Content neu ist"""
        
        content_hash = gutachten_data.get('content_hash')
        if not content_hash:
            return False
        
        if content_hash in self.scraper.content_hashes:
            return False
        
        # Vereinfachte Duplikatsprüfung
        self.scraper.content_hashes.add(content_hash)
        return True
    
    def _add_to_database(self, gutachten_data: Dict) -> bool:
        """Fügt Gutachten zur ChromaDB hinzu"""
        
        try:
            # Bereite Daten für ChromaDB vor
            documents = [gutachten_data['content']]
            metadatas = [{
                'id': gutachten_data['id'],
                'title': gutachten_data['title'],
                'gutachten_nummer': gutachten_data['gutachten_nummer'],
                'erscheinungsdatum': gutachten_data['erscheinungsdatum'],
                'rechtsbezug': gutachten_data['rechtsbezug'],
                'normen': gutachten_data['normen'],
                'url': gutachten_data['url'],
                'content_hash': gutachten_data['content_hash'],
                'scraped_timestamp': gutachten_data['scraped_timestamp']
            }]
            ids = [gutachten_data['id']]
            
            # Füge zur ChromaDB hinzu
            self.chroma_client.add_documents(
                collection_name=self.config.COLLECTION_NAME,
                documents=documents,
                metadatas=metadatas,
                ids=ids
            )
            
            return True
            
        except Exception as e:
            self.logger.error(f"Datenbank-Fehler: {e}")
            return False

# ========== CLI INTERFACE ==========

async def main():
    """Haupt-Einstiegspunkt"""
    
    print("DNOTI Auto-Update Service - Produktionsversion")
    print("=" * 60)
    
    config = DNOTIConfig()
    service = DNOTIAutoUpdateService(config)
    
    try:
        metrics = await service.run_update_cycle()
        
        print("\nUPDATE ABGESCHLOSSEN")
        print("-" * 30)
        print(f"Entdeckt: {metrics['total_discovered']}")
        print(f"Verarbeitet: {metrics['total_processed']}")
        print(f"Hinzugefügt: {metrics['total_added']}")
        print(f"Erfolgsrate: {metrics['success_rate']:.1f}%")
        print(f"Dauer: {metrics.get('duration_seconds', 0):.1f} Sekunden")
        
        if metrics['errors']:
            print(f"Fehler: {len(metrics['errors'])}")
            for error in metrics['errors']:
                print(f"   - {error}")
    
    except KeyboardInterrupt:
        print("\nUpdate durch Benutzer abgebrochen")
    except Exception as e:
        print(f"\nUnerwarteter Fehler: {e}")

if __name__ == "__main__":
    # Setup basic logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    asyncio.run(main())
