#!/usr/bin/env python3
"""
DNOTI Auto-Update Service - Advanced Version with Form-Based Search
Erweiterte Lösung basierend auf Deep Analysis Ergebnissen

Entwickelt für den MLFBAC Legal Tech Semantic Search
Version 4.0 - Mit Form-basierter Gutachten-Suche
"""

import logging
import time
import hashlib
import json
import sys
import re
import os
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple
from dataclasses import dataclass
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
class DNOTIAdvancedConfig:
    """Erweiterte Konfiguration basierend auf Deep Analysis"""
    
    # DNOTI Website-Konfiguration
    BASE_URL: str = "https://www.dnoti.de"
    GUTACHTEN_SEARCH_URL: str = "https://www.dnoti.de/gutachten/"
    
    # Form-basierte Suchstrategien
    SEARCH_STRATEGIES: List[str] = None
    
    # Update-Konfiguration
    CHECK_INTERVAL_HOURS: int = 6
    BATCH_SIZE: int = 15
    MAX_RETRIES: int = 3
    
    # Request-Konfiguration
    REQUEST_TIMEOUT: int = 30
    REQUEST_DELAY_SECONDS: float = 2.0
    
    # ChromaDB-Konfiguration  
    COLLECTION_NAME: str = "dnoti_gutachten"
    
    # Logging-Konfiguration
    LOG_LEVEL: str = "INFO"
    LOG_DIR: str = "logs"
    
    # Form Search Konfiguration
    SEARCH_YEARS: List[int] = None
    SEARCH_KEYWORDS: List[str] = None
    MAX_PAGES_PER_SEARCH: int = 5
    
    def __post_init__(self):
        if self.SEARCH_STRATEGIES is None:
            self.SEARCH_STRATEGIES = [
                "form_all_types",
                "form_dnoti_reports",
                "form_by_year",
                "form_keyword_search",
                "form_expertise_ref"
            ]
        
        if self.SEARCH_YEARS is None:
            current_year = datetime.now().year
            self.SEARCH_YEARS = [current_year, current_year - 1, current_year - 2]
        
        if self.SEARCH_KEYWORDS is None:
            self.SEARCH_KEYWORDS = [
                "Notar",
                "Beurkundung", 
                "Immobilie",
                "Grundstück",
                "Kaufvertrag",
                "Vollmacht",
                "Erbrecht",
                "Gesellschaftsrecht",
                "Handelsregister",
                "Grundbuch"
            ]


class DNOTIAdvancedAutoUpdater:
    """Erweiterte DNOTI Auto-Updater mit Form-basierter Suche"""
    
    def __init__(self, config: DNOTIAdvancedConfig):
        self.config = config
        self.session = requests.Session()
        self.stats = {
            'started_at': datetime.now().isoformat(),
            'website_accessible': False,
            'search_strategies_used': [],
            'total_searches_performed': 0,
            'gutachten_found': 0,
            'gutachten_processed': 0,
            'gutachten_added': 0,
            'errors': 0,
            'duration_seconds': 0.0,
            'status': 'initialized'
        }
        
        # Setup
        self._setup_logging()
        self._setup_session()
        self._initialize_chromadb()
        
        self.logger.info("DNOTI Advanced Auto-Updater v4.0 initialisiert")
    
    def _setup_logging(self):
        """Setup Logging System"""
        log_dir = Path(self.config.LOG_DIR)
        log_dir.mkdir(exist_ok=True)
        
        self.logger = logging.getLogger("DNOTIAdvancedV4")
        self.logger.setLevel(getattr(logging, self.config.LOG_LEVEL))
        
        # Console Handler
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(logging.INFO)
        console_formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        console_handler.setFormatter(console_formatter)
        
        # File Handler
        file_handler = logging.FileHandler(
            log_dir / "dnoti_auto_update_advanced_v4.log",
            encoding='utf-8'
        )
        file_handler.setLevel(logging.DEBUG)
        file_formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        file_handler.setFormatter(file_formatter)
        
        # Clear existing handlers
        self.logger.handlers.clear()
        self.logger.addHandler(console_handler)
        self.logger.addHandler(file_handler)
    
    def _setup_session(self):
        """Setup HTTP Session mit optimierten Headers"""
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'de-DE,de;q=0.9,en;q=0.8',
            'Accept-Encoding': 'gzip, deflate, br',
            'DNT': '1',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Referer': self.config.BASE_URL
        })
    
    def _initialize_chromadb(self):
        """Initialisiere ChromaDB-Verbindung"""
        try:
            self.logger.info("Initialisiere ChromaDB-Verbindung...")
            self.chroma_client = ChromaDBClient()
            
            # Collection sicherstellen
            self.chroma_client.create_collection(
                collection_name=self.config.COLLECTION_NAME,
                reset_if_exists=False
            )
            
            self.logger.info(f"ChromaDB Collection '{self.config.COLLECTION_NAME}' bereit")
            
        except Exception as e:
            self.logger.error(f"ChromaDB-Initialisierung fehlgeschlagen: {e}")
            raise
    
    def check_website_accessibility(self) -> bool:
        """Überprüfe DNOTI-Website-Zugänglichkeit"""
        try:
            self.logger.info("Überprüfe DNOTI-Website-Zugänglichkeit...")
            
            response = self.session.get(
                self.config.BASE_URL,
                timeout=self.config.REQUEST_TIMEOUT
            )
            
            if response.status_code == 200:
                self.logger.info("DNOTI-Website ist erreichbar")
                self.stats['website_accessible'] = True
                return True
            else:
                self.logger.warning(f"DNOTI-Website antwortet mit Status {response.status_code}")
                return False
                
        except Exception as e:
            self.logger.error(f"Website-Zugänglichkeitsprüfung fehlgeschlagen: {e}")
            return False
    
    def search_for_new_gutachten(self) -> List[Dict]:
        """Erweiterte Form-basierte Suche nach DNOTI-Gutachten"""
        self.logger.info("Starte erweiterte Form-basierte Gutachten-Suche...")
        
        all_gutachten = []
        
        for strategy in self.config.SEARCH_STRATEGIES:
            self.logger.info(f"Verwende Strategie: {strategy}")
            self.stats['search_strategies_used'].append(strategy)
            
            try:
                if strategy == "form_all_types":
                    gutachten = self._search_form_all_types()
                elif strategy == "form_dnoti_reports":
                    gutachten = self._search_form_dnoti_reports()
                elif strategy == "form_by_year":
                    gutachten = self._search_form_by_year()
                elif strategy == "form_keyword_search":
                    gutachten = self._search_form_keyword_search()
                elif strategy == "form_expertise_ref":
                    gutachten = self._search_form_expertise_ref()
                else:
                    self.logger.warning(f"Unbekannte Strategie: {strategy}")
                    continue
                
                if gutachten:
                    self.logger.info(f"✓ {strategy}: {len(gutachten)} Gutachten gefunden")
                    all_gutachten.extend(gutachten)
                else:
                    self.logger.info(f"- {strategy}: Keine Gutachten gefunden")
                
                self.stats['total_searches_performed'] += 1
                time.sleep(self.config.REQUEST_DELAY_SECONDS)
                
            except Exception as e:
                self.logger.error(f"Strategie {strategy} fehlgeschlagen: {e}")
                self.stats['errors'] += 1
        
        # Duplikate entfernen
        unique_gutachten = self._remove_duplicates(all_gutachten)
        
        self.logger.info(f"Suchergebnis: {len(all_gutachten)} gesamt, {len(unique_gutachten)} eindeutig")
        self.stats['gutachten_found'] = len(unique_gutachten)
        
        return unique_gutachten
    
    def _search_form_all_types(self) -> List[Dict]:
        """Suche mit 'all' Gutachten-Typen"""
        try:
            # Suche nach allen Typen ohne spezifische Filter
            search_data = {
                'tx_dnotionlineplusapi_expertises[page]': '1',
                'tx_dnotionlineplusapi_expertises[searchTitle]': '',
                'tx_dnotionlineplusapi_expertises[searchText]': '',
                'tx_dnotionlineplusapi_expertises[expertisesType]': 'all'
            }
            
            return self._perform_form_search(search_data, "all_types")
            
        except Exception as e:
            self.logger.error(f"Form-Suche 'all types' fehlgeschlagen: {e}")
            return []
    
    def _search_form_dnoti_reports(self) -> List[Dict]:
        """Suche spezifisch nach DNOTI-Reports"""
        try:
            found_gutachten = []
            
            # Suche DNOTI-Reports der letzten Jahre
            for year in self.config.SEARCH_YEARS[:2]:  # Begrenzt auf 2 Jahre
                search_data = {
                    'tx_dnotionlineplusapi_expertises[page]': '1',
                    'tx_dnotionlineplusapi_expertises[searchTitle]': '',
                    'tx_dnotionlineplusapi_expertises[searchText]': '',
                    'tx_dnotionlineplusapi_expertises[expertisesType]': 'dnotiReport',
                    'tx_dnotionlineplusapi_expertises[reportYear]': str(year),
                    'tx_dnotionlineplusapi_expertises[reportPage]': ''
                }
                
                year_results = self._perform_form_search(search_data, f"dnoti_reports_{year}")
                if year_results:
                    found_gutachten.extend(year_results)
                    self.logger.debug(f"Jahr {year}: {len(year_results)} Gutachten gefunden")
                
                time.sleep(self.config.REQUEST_DELAY_SECONDS)
            
            return found_gutachten
            
        except Exception as e:
            self.logger.error(f"DNOTI-Reports-Suche fehlgeschlagen: {e}")
            return []
    
    def _search_form_by_year(self) -> List[Dict]:
        """Jahres-basierte Suche"""
        try:
            found_gutachten = []
            
            for year in self.config.SEARCH_YEARS:
                search_data = {
                    'tx_dnotionlineplusapi_expertises[page]': '1',
                    'tx_dnotionlineplusapi_expertises[searchTitle]': '',
                    'tx_dnotionlineplusapi_expertises[searchText]': str(year),
                    'tx_dnotionlineplusapi_expertises[expertisesType]': 'all'
                }
                
                year_results = self._perform_form_search(search_data, f"year_search_{year}")
                if year_results:
                    found_gutachten.extend(year_results)
                    self.logger.debug(f"Jahres-Suche {year}: {len(year_results)} Gutachten")
                
                time.sleep(self.config.REQUEST_DELAY_SECONDS)
            
            return found_gutachten
            
        except Exception as e:
            self.logger.error(f"Jahres-basierte Suche fehlgeschlagen: {e}")
            return []
    
    def _search_form_keyword_search(self) -> List[Dict]:
        """Stichwort-basierte Suche"""
        try:
            found_gutachten = []
            
            # Begrenzt auf wichtigste Keywords um Server nicht zu überlasten
            for keyword in self.config.SEARCH_KEYWORDS[:5]:
                # Titel-Suche
                search_data = {
                    'tx_dnotionlineplusapi_expertises[page]': '1',
                    'tx_dnotionlineplusapi_expertises[searchTitle]': keyword,
                    'tx_dnotionlineplusapi_expertises[searchText]': '',
                    'tx_dnotionlineplusapi_expertises[expertisesType]': 'all'
                }
                
                title_results = self._perform_form_search(search_data, f"keyword_title_{keyword}")
                if title_results:
                    found_gutachten.extend(title_results)
                
                time.sleep(self.config.REQUEST_DELAY_SECONDS)
                
                # Volltext-Suche
                search_data['tx_dnotionlineplusapi_expertises[searchTitle]'] = ''
                search_data['tx_dnotionlineplusapi_expertises[searchText]'] = keyword
                
                text_results = self._perform_form_search(search_data, f"keyword_text_{keyword}")
                if text_results:
                    found_gutachten.extend(text_results)
                
                time.sleep(self.config.REQUEST_DELAY_SECONDS)
            
            return found_gutachten
            
        except Exception as e:
            self.logger.error(f"Keyword-Suche fehlgeschlagen: {e}")
            return []
    
    def _search_form_expertise_ref(self) -> List[Dict]:
        """Suche nach Expertise-Referenzen"""
        try:
            found_gutachten = []
            
            # Test verschiedene Expertise-Referenz-Pattern
            expertise_refs = [
                "1", "2", "3", "4", "5",  # Einfache Nummern
                "2024-1", "2024-2", "2025-1",  # Jahr-basierte Refs
                "NR-1", "NR-2", "NR-3"  # Nummer-Pattern
            ]
            
            for ref in expertise_refs[:5]:  # Begrenzt auf 5 Tests
                search_data = {
                    'tx_dnotionlineplusapi_expertises[page]': '1',
                    'tx_dnotionlineplusapi_expertises[searchTitle]': '',
                    'tx_dnotionlineplusapi_expertises[searchText]': '',
                    'tx_dnotionlineplusapi_expertises[expertisesType]': 'expertiseReference',
                    'tx_dnotionlineplusapi_expertises[expertiseReference]': ref
                }
                
                ref_results = self._perform_form_search(search_data, f"expertise_ref_{ref}")
                if ref_results:
                    found_gutachten.extend(ref_results)
                    self.logger.debug(f"Expertise-Ref {ref}: {len(ref_results)} Gutachten")
                
                time.sleep(self.config.REQUEST_DELAY_SECONDS)
            
            return found_gutachten
            
        except Exception as e:
            self.logger.error(f"Expertise-Referenz-Suche fehlgeschlagen: {e}")
            return []
    
    def _perform_form_search(self, search_data: Dict, search_context: str) -> List[Dict]:
        """Führe Form-basierte Suche durch und extrahiere Ergebnisse"""
        try:
            found_gutachten = []
            
            # Durchlaufe mehrere Seiten wenn verfügbar
            for page in range(1, self.config.MAX_PAGES_PER_SEARCH + 1):
                search_data['tx_dnotionlineplusapi_expertises[page]'] = str(page)
                
                response = self.session.post(
                    self.config.GUTACHTEN_SEARCH_URL,
                    data=search_data,
                    timeout=self.config.REQUEST_TIMEOUT
                )
                
                if response.status_code != 200:
                    self.logger.warning(f"Form-Search {search_context} Seite {page} fehlgeschlagen: {response.status_code}")
                    break
                
                # Parse Response für Gutachten-Links
                soup = BeautifulSoup(response.content, 'html.parser')
                page_gutachten = self._extract_gutachten_from_results(soup, search_context, page)
                
                if page_gutachten:
                    found_gutachten.extend(page_gutachten)
                    self.logger.debug(f"{search_context} Seite {page}: {len(page_gutachten)} Gutachten gefunden")
                    
                    # Speichere Debug-HTML für erste Seite
                    if page == 1:
                        self._save_debug_html(response.content, f"{search_context}_page_{page}")
                else:
                    # Keine Ergebnisse mehr, stoppe Pagination
                    self.logger.debug(f"{search_context}: Keine weiteren Ergebnisse auf Seite {page}")
                    break
                
                time.sleep(self.config.REQUEST_DELAY_SECONDS * 0.5)  # Kurze Pause zwischen Seiten
            
            return found_gutachten
            
        except Exception as e:
            self.logger.error(f"Form-Search {search_context} fehlgeschlagen: {e}")
            return []
    
    def _extract_gutachten_from_results(self, soup: BeautifulSoup, search_context: str, page: int) -> List[Dict]:
        """Extrahiere Gutachten-Links aus Suchergebnissen"""
        try:
            found_gutachten = []
            
            # Verschiedene Selektoren für Ergebnis-Links probieren
            result_selectors = [
                'a[href*="nodeid"]',
                'a[href*="tx_dnotionlineplusapi_expertises"]',
                'a[href*="/details/"]',
                '.result-item a',
                '.expertise-item a',
                '.gutachten-item a',
                '.list-item a',
                'article a',
                '.content-element a'
            ]
            
            for selector in result_selectors:
                links = soup.select(selector)
                
                for link in links:
                    href = link.get('href')
                    text = link.get_text(strip=True)
                    
                    if href and self._is_valid_gutachten_link(href):
                        full_url = urljoin(self.config.BASE_URL, href)
                        
                        # Extrahiere zusätzliche Metadaten vom Link
                        metadata = self._extract_link_metadata(link, soup)
                        
                        gutachten_info = {
                            'url': full_url,
                            'title': text or "Gutachten",
                            'search_context': search_context,
                            'page': page,
                            'selector': selector,
                            'metadata': metadata,
                            'found_at': datetime.now().isoformat()
                        }
                        
                        found_gutachten.append(gutachten_info)
            
            # Dedupliziere innerhalb dieser Seite
            unique_gutachten = []
            seen_urls = set()
            
            for gutachten in found_gutachten:
                url_normalized = gutachten['url'].split('?')[0].split('#')[0]
                if url_normalized not in seen_urls:
                    seen_urls.add(url_normalized)
                    unique_gutachten.append(gutachten)
            
            return unique_gutachten
            
        except Exception as e:
            self.logger.error(f"Extraktion aus Suchergebnissen fehlgeschlagen: {e}")
            return []
    
    def _extract_link_metadata(self, link_element, soup: BeautifulSoup) -> Dict:
        """Extrahiere Metadaten aus Link-Kontext"""
        metadata = {}
        
        try:
            # Suche Parent-Container für zusätzliche Informationen
            parent = link_element.parent
            if parent:
                # Datum suchen
                date_patterns = [
                    r'\b\d{1,2}\.\d{1,2}\.\d{4}\b',
                    r'\b\d{4}-\d{1,2}-\d{1,2}\b',
                    r'\b\d{1,2}/\d{1,2}/\d{4}\b'
                ]
                
                parent_text = parent.get_text()
                for pattern in date_patterns:
                    date_match = re.search(pattern, parent_text)
                    if date_match:
                        metadata['date_found'] = date_match.group()
                        break
                
                # Weitere Metadaten aus Parent-Text
                if len(parent_text.strip()) > 20:
                    metadata['context_text'] = parent_text.strip()[:200]
            
            # Node-ID extrahieren falls vorhanden
            href = link_element.get('href', '')
            node_match = re.search(r'nodeid[=%]([a-f0-9\-]{36})', href, re.IGNORECASE)
            if node_match:
                metadata['node_id'] = node_match.group(1)
            
        except Exception as e:
            self.logger.debug(f"Metadata-Extraktion fehlgeschlagen: {e}")
        
        return metadata
    
    def _is_valid_gutachten_link(self, href: str) -> bool:
        """Prüfe ob Link ein gültiger Gutachten-Link ist"""
        if not href:
            return False
        
        # Positive Patterns
        positive_patterns = [
            r'/gutachten/details/',
            r'tx_dnotionlineplusapi_expertises.*nodeid',
            r'nodeid=[\w\-]+',
            r'/expertise/',
            r'gutachten.*id=\d+',
            r'expertise.*id=\d+'
        ]
        
        # Negative Patterns
        negative_patterns = [
            r'javascript:',
            r'mailto:',
            r'#$',
            r'\.pdf$',
            r'\.doc$',
            r'/impressum',
            r'/datenschutz',
            r'/kontakt',
            r'/search',
            r'/suche'
        ]
        
        # Prüfe negative Patterns
        for pattern in negative_patterns:
            if re.search(pattern, href, re.IGNORECASE):
                return False
        
        # Prüfe positive Patterns
        for pattern in positive_patterns:
            if re.search(pattern, href, re.IGNORECASE):
                return True
        
        return False
    
    def _remove_duplicates(self, gutachten_list: List[Dict]) -> List[Dict]:
        """Entferne Duplikate basierend auf URL und Node-ID"""
        seen_urls = set()
        seen_node_ids = set()
        unique_gutachten = []
        
        for gutachten in gutachten_list:
            url = gutachten.get('url', '')
            metadata = gutachten.get('metadata', {})
            
            # Extrahiere Node-ID
            node_id = metadata.get('node_id')
            if not node_id and 'nodeid' in url:
                node_match = re.search(r'nodeid[=%]([a-f0-9\-]{36})', url, re.IGNORECASE)
                if node_match:
                    node_id = node_match.group(1)
            
            # Prüfe Duplikate
            url_normalized = url.split('?')[0].split('#')[0]
            
            if url_normalized in seen_urls:
                continue
            
            if node_id and node_id in seen_node_ids:
                continue
            
            # Füge zur eindeutigen Liste hinzu
            seen_urls.add(url_normalized)
            if node_id:
                seen_node_ids.add(node_id)
            
            unique_gutachten.append(gutachten)
        
        return unique_gutachten
    
    def extract_gutachten_content(self, gutachten_info: Dict) -> Optional[Dict]:
        """Extrahiere Inhalt eines Gutachtens"""
        try:
            url = gutachten_info['url']
            self.logger.debug(f"Extrahiere Inhalt von: {url}")
            
            response = self.session.get(url, timeout=self.config.REQUEST_TIMEOUT)
            
            if response.status_code != 200:
                self.logger.warning(f"Gutachten nicht abrufbar: {url} (Status: {response.status_code})")
                return None
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Extrahiere Metadaten und Inhalt
            title = self._extract_title(soup, gutachten_info.get('title', ''))
            content = self._extract_main_content(soup)
            metadata = self._extract_metadata(soup, url, gutachten_info)
            
            if not content or len(content.strip()) < 50:
                self.logger.warning(f"Kein ausreichender Inhalt extrahiert für: {url}")
                return None
            
            return {
                'url': url,
                'title': title,
                'content': content,
                'metadata': metadata,
                'extracted_at': datetime.now().isoformat(),
                'source_info': gutachten_info
            }
            
        except Exception as e:
            self.logger.error(f"Content-Extraktion fehlgeschlagen für {gutachten_info.get('url', 'N/A')}: {e}")
            return None
    
    def _extract_title(self, soup: BeautifulSoup, fallback_title: str) -> str:
        """Extrahiere Titel des Gutachtens"""
        title_selectors = [
            'h1.gutachten-title',
            'h1',
            '.content-title h1',
            '.main-title',
            '.page-title',
            'title'
        ]
        
        for selector in title_selectors:
            element = soup.select_one(selector)
            if element:
                title = element.get_text(strip=True)
                if title and len(title) > 5 and 'dnoti' not in title.lower():
                    return title
        
        return fallback_title or "DNOTI Gutachten"
    
    def _extract_main_content(self, soup: BeautifulSoup) -> str:
        """Extrahiere Hauptinhalt des Gutachtens"""
        content_selectors = [
            '.gutachten-content',
            '.expertise-content',
            '.main-content',
            '.content-body',
            'article',
            '.tx-dnotionlineplus-pi1',
            '.page-content'
        ]
        
        for selector in content_selectors:
            element = soup.select_one(selector)
            if element:
                # Entferne unerwünschte Elemente
                for unwanted in element.select('script, style, nav, footer, .navigation, .menu'):
                    unwanted.decompose()
                
                content = element.get_text(separator=' ', strip=True)
                if content and len(content) > 100:
                    return content
        
        # Fallback: body-Inhalt
        body = soup.find('body')
        if body:
            for unwanted in body.select('script, style, nav, footer, .navigation, .sidebar, .menu'):
                unwanted.decompose()
            
            content = body.get_text(separator=' ', strip=True)
            return content
        
        return ""
    
    def _extract_metadata(self, soup: BeautifulSoup, url: str, gutachten_info: Dict) -> Dict:
        """Extrahiere erweiterte Metadaten"""
        metadata = {
            'url': url,
            'extracted_at': datetime.now().isoformat(),
            'search_context': gutachten_info.get('search_context', ''),
            'original_metadata': gutachten_info.get('metadata', {})
        }
        
        # Node-ID
        node_match = re.search(r'nodeid[=%]([a-f0-9\-]{36})', url, re.IGNORECASE)
        if node_match:
            metadata['node_id'] = node_match.group(1)
        
        # Meta-Tags
        meta_tags = soup.find_all('meta')
        for meta in meta_tags:
            name = meta.get('name') or meta.get('property')
            content = meta.get('content')
            
            if name and content:
                if name.lower() in ['description', 'keywords', 'author', 'date', 'subject']:
                    metadata[f"meta_{name.lower()}"] = content
        
        return metadata
    
    def add_to_vectordb(self, gutachten_list: List[Dict]) -> bool:
        """Füge Gutachten zur ChromaDB hinzu"""
        if not gutachten_list:
            return True
        
        try:
            self.logger.info(f"Bereite {len(gutachten_list)} Gutachten für ChromaDB vor...")
            
            documents = []
            metadatas = []
            ids = []
            
            for gutachten in gutachten_list:
                # Generiere eindeutige ID
                doc_id = self._generate_document_id(gutachten)
                
                # Bereite Dokument vor
                document_text = f"{gutachten['title']}\n\n{gutachten['content']}"
                
                # Bereite Metadaten vor
                metadata = {
                    'title': gutachten['title'],
                    'url': gutachten['url'],
                    'source': gutachten.get('source_info', {}).get('search_context', 'form_search'),
                    'extracted_at': gutachten['extracted_at'],
                    'document_type': 'dnoti_gutachten',
                    'language': 'de',
                    'version': 'v4_advanced'
                }
                
                # Zusätzliche Metadaten
                if 'metadata' in gutachten:
                    for key, value in gutachten['metadata'].items():
                        if isinstance(value, (str, int, float, bool)) and key != 'original_metadata':
                            metadata[f"meta_{key}"] = str(value)[:100]  # Begrenzt Länge
                
                documents.append(document_text)
                metadatas.append(metadata)
                ids.append(doc_id)
            
            # Füge zur ChromaDB hinzu
            self.chroma_client.add_documents(
                collection_name=self.config.COLLECTION_NAME,
                documents=documents,
                metadatas=metadatas,
                ids=ids
            )
            
            self.logger.info(f"Erfolgreich {len(documents)} Gutachten zur ChromaDB hinzugefügt")
            return True
            
        except Exception as e:
            self.logger.error(f"Fehler beim Hinzufügen zur ChromaDB: {e}")
            self.stats['errors'] += 1
            return False
    
    def _generate_document_id(self, gutachten: Dict) -> str:
        """Generiere eindeutige Dokument-ID"""
        url = gutachten.get('url', '')
        title = gutachten.get('title', '')
        
        # Node-ID falls verfügbar
        metadata = gutachten.get('metadata', {})
        node_id = metadata.get('node_id')
        
        if not node_id:
            node_match = re.search(r'nodeid[=%]([a-f0-9\-]{36})', url, re.IGNORECASE)
            if node_match:
                node_id = node_match.group(1)
        
        if node_id:
            return f"dnoti_gutachten_v4_{node_id}"
        
        # Fallback: Hash aus URL und Titel
        content_hash = hashlib.md5(f"{url}_{title}".encode('utf-8')).hexdigest()
        return f"dnoti_gutachten_v4_{content_hash}"
    
    def _save_debug_html(self, content: bytes, filename: str):
        """Speichere Debug-HTML"""
        debug_dir = Path("debug_output")
        debug_dir.mkdir(exist_ok=True)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filepath = debug_dir / f"form_search_{filename}_{timestamp}.html"
        
        try:
            with open(filepath, 'wb') as f:
                f.write(content)
        except Exception as e:
            self.logger.debug(f"Debug-HTML konnte nicht gespeichert werden: {e}")
    
    def run_complete_update_cycle(self) -> Dict:
        """Führe kompletten Update-Zyklus durch"""
        start_time = time.time()
        
        try:
            self.logger.info("=== DNOTI Advanced Auto-Update Zyklus gestartet ===")
            
            # 1. Website-Zugänglichkeit prüfen
            website_ok = self.check_website_accessibility()
            if not website_ok:
                self.logger.error("Website nicht erreichbar - Update abgebrochen")
                self.stats['status'] = 'website_unavailable'
                return self.stats
            
            # 2. Form-basierte Suche nach Gutachten
            gutachten_list = self.search_for_new_gutachten()
            
            if not gutachten_list:
                self.logger.warning("Keine Gutachten gefunden")
                self.stats['status'] = 'no_gutachten_found'
                return self.stats
            
            # 3. Extrahiere Inhalte
            self.logger.info(f"Starte Content-Extraktion für {len(gutachten_list)} Gutachten...")
            extracted_gutachten = []
            
            for i, gutachten_info in enumerate(gutachten_list[:self.config.BATCH_SIZE]):
                self.logger.debug(f"Extrahiere Gutachten {i+1}/{min(len(gutachten_list), self.config.BATCH_SIZE)}")
                
                extracted = self.extract_gutachten_content(gutachten_info)
                if extracted:
                    extracted_gutachten.append(extracted)
                    self.stats['gutachten_processed'] += 1
                
                time.sleep(self.config.REQUEST_DELAY_SECONDS)
            
            # 4. Füge zur ChromaDB hinzu
            if extracted_gutachten:
                success = self.add_to_vectordb(extracted_gutachten)
                if success:
                    self.stats['gutachten_added'] = len(extracted_gutachten)
                    self.logger.info(f"✓ Update erfolgreich: {len(extracted_gutachten)} Gutachten hinzugefügt")
                    self.stats['status'] = 'success'
                else:
                    self.logger.error("ChromaDB-Integration fehlgeschlagen")
                    self.stats['status'] = 'chromadb_error'
            else:
                self.logger.warning("Keine Gutachten extrahiert")
                self.stats['status'] = 'extraction_failed'
            
        except Exception as e:
            self.logger.error(f"Update-Zyklus fehlgeschlagen: {e}")
            self.stats['status'] = 'error'
            self.stats['errors'] += 1
        
        finally:
            # Statistiken finalisieren
            end_time = time.time()
            self.stats['duration_seconds'] = end_time - start_time
            self.logger.info(f"Gesamtdauer: {self.stats['duration_seconds']:.2f} Sekunden")
        
        return self.stats


def print_advanced_report(stats: Dict):
    """Drucke erweiterten Abschlussbericht"""
    print("\n" + "="*60)
    print("DNOTI Advanced Auto-Update - Final Report v4.0")
    print("="*60)
    
    print(f"Status: {stats['status']}")
    print(f"Gestartet: {stats['started_at']}")
    print(f"Website erreichbar: {stats['website_accessible']}")
    print(f"Suchstrategien verwendet: {len(stats['search_strategies_used'])}")
    print(f"Suchanfragen durchgeführt: {stats['total_searches_performed']}")
    print(f"Gutachten gefunden: {stats['gutachten_found']}")
    print(f"Gutachten verarbeitet: {stats['gutachten_processed']}")
    print(f"Gutachten hinzugefügt: {stats['gutachten_added']}")
    print(f"Fehler: {stats['errors']}")
    print(f"Dauer: {stats['duration_seconds']:.2f} Sekunden")
    
    print("\n" + "-"*60)
    
    if stats['status'] == 'success':
        print("✓ STATUS: Update erfolgreich abgeschlossen!")
        efficiency = (stats['gutachten_added'] / stats['gutachten_found'] * 100) if stats['gutachten_found'] > 0 else 0
        print(f"✓ EFFIZIENZ: {efficiency:.1f}% der gefundenen Gutachten erfolgreich hinzugefügt")
    elif stats['status'] == 'no_gutachten_found':
        print("- STATUS: Keine neuen Gutachten gefunden")
    elif stats['status'] == 'website_unavailable':
        print("✗ STATUS: Website nicht erreichbar")
    else:
        print("✗ STATUS: Update mit Fehlern abgeschlossen")
    
    print("\nVerwendete Suchstrategien:")
    for strategy in stats['search_strategies_used']:
        print(f"  • {strategy}")
    
    print("\nNächste Schritte:")
    print("1. Log-Datei überprüfen: logs/dnoti_auto_update_advanced_v4.log")
    print("2. Debug-HTML-Dateien prüfen: debug_output/")
    print("3. ChromaDB-Integration im Frontend testen")
    print("4. Für Produktionseinsatz: Automatische Ausführung konfigurieren")
    print("="*60)


def main():
    """Hauptfunktion"""
    print("DNOTI Advanced Auto-Updater v4.0 - Form-Based Search")
    print("=" * 60)
    print("Erweiterte Lösung mit Form-basierter Gutachten-Suche")
    print("Basierend auf Deep Analysis Ergebnissen")
    print()
    
    try:
        # Konfiguration laden
        config = DNOTIAdvancedConfig()
        
        # Auto-Updater initialisieren
        updater = DNOTIAdvancedAutoUpdater(config)
        
        # Update-Zyklus starten
        stats = updater.run_complete_update_cycle()
        
        # Erweiterten Bericht drucken
        print_advanced_report(stats)
        
        # Exit-Code basierend auf Status
        if stats['status'] == 'success':
            return 0
        elif stats['status'] in ['no_gutachten_found', 'extraction_failed']:
            return 1
        else:
            return 2
            
    except KeyboardInterrupt:
        print("\nUpdate durch Benutzer abgebrochen")
        return 130
    except Exception as e:
        print(f"\nFATALER FEHLER: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
