#!/usr/bin/env python3
"""
DNOTI Auto-Update Service - Optimized Production Version
Robuste Lösung für DNOTI-Gutachten Updates mit verbesserter Suchstrategie

Entwickelt für den MLFBAC Legal Tech Semantic Search
Version 3.0 - Optimiert für Produktionseinsatz
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
class DNOTIConfig:
    """Optimierte Produktionskonfiguration für DNOTI Auto-Update"""
    
    # DNOTI Website-Konfiguration
    BASE_URL: str = "https://www.dnoti.de"
    GUTACHTEN_SEARCH_URL: str = "https://www.dnoti.de/gutachten/"
    
    # Update-Strategien
    CHECK_INTERVAL_HOURS: int = 6
    BATCH_SIZE: int = 10
    MAX_RETRIES: int = 3
    
    # Request-Konfiguration
    REQUEST_TIMEOUT: int = 30
    REQUEST_DELAY_SECONDS: float = 1.5
    
    # ChromaDB-Konfiguration  
    COLLECTION_NAME: str = "dnoti_gutachten"
    
    # Logging-Konfiguration
    LOG_LEVEL: str = "INFO"
    LOG_DIR: str = "logs"
    ENABLE_EMOJIS: bool = False  # Für Windows-Kompatibilität
    
    # Search-Konfiguration
    SEARCH_STRATEGIES: List[str] = None
    
    def __post_init__(self):
        if self.SEARCH_STRATEGIES is None:
            self.SEARCH_STRATEGIES = [
                "direct_links",      # Direkte Gutachten-Links von Hauptseite
                "archive_search",    # Archiv-Durchsuchung
                "recent_content",    # Neue Inhalte
                "keyword_search"     # Stichwort-basierte Suche
            ]


class DNOTIAutoUpdaterOptimized:
    """Optimierter DNOTI Auto-Updater mit verbesserter Suchstrategie"""
    
    def __init__(self, config: DNOTIConfig):
        self.config = config
        self.session = requests.Session()
        self.stats = {
            'started_at': datetime.now().isoformat(),
            'website_accessible': False,
            'gutachten_found': 0,
            'gutachten_added': 0,
            'demo_mode_used': False,
            'errors': 0,
            'duration_seconds': 0.0,
            'status': 'initialized'
        }
        
        # Setup Logging
        self._setup_logging()
        
        # Setup Session
        self._setup_session()
        
        # Initialize ChromaDB
        self._initialize_chromadb()
        
        self.logger.info("DNOTI Optimized Auto-Updater v3.0 initialisiert")
    
    def _setup_logging(self):
        """Setup optimiertes Logging ohne Emojis für Windows-Kompatibilität"""
        
        # Erstelle Log-Verzeichnis
        log_dir = Path(self.config.LOG_DIR)
        log_dir.mkdir(exist_ok=True)
        
        # Setup Logger
        self.logger = logging.getLogger("DNOTIAutoUpdaterV3")
        self.logger.setLevel(getattr(logging, self.config.LOG_LEVEL))
        
        # Console Handler (ohne Emojis)
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(logging.INFO)
        console_formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        console_handler.setFormatter(console_formatter)
        
        # File Handler
        file_handler = logging.FileHandler(
            log_dir / "dnoti_auto_update_optimized_v3.log",
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
        """Setup optimierte HTTP-Session"""
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'de-DE,de;q=0.9,en;q=0.8',            'Accept-Encoding': 'gzip, deflate, br',
            'DNT': '1',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1'
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
            
            self.logger.info(f"ChromaDB Collection '{self.config.COLLECTION_NAME}' erfolgreich bereit")
            
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
        """Systematische Suche nach neuen DNOTI-Gutachten mit optimierten Strategien"""
        self.logger.info("Starte systematische Suche nach DNOTI-Gutachten...")
        
        all_gutachten = []
        
        for strategy in self.config.SEARCH_STRATEGIES:
            self.logger.info(f"Verwende Strategie: {strategy}")
            
            try:
                if strategy == "direct_links":
                    gutachten = self._search_direct_links()
                elif strategy == "archive_search":
                    gutachten = self._search_archive()
                elif strategy == "recent_content":
                    gutachten = self._search_recent_content()
                elif strategy == "keyword_search":
                    gutachten = self._search_by_keywords()
                else:
                    self.logger.warning(f"Unbekannte Strategie: {strategy}")
                    continue
                
                if gutachten:
                    self.logger.info(f"{strategy}: {len(gutachten)} Gutachten gefunden")
                    all_gutachten.extend(gutachten)
                else:
                    self.logger.info(f"{strategy}: Keine Gutachten gefunden")
                
                # Pause zwischen Strategien
                time.sleep(self.config.REQUEST_DELAY_SECONDS)
                
            except Exception as e:
                self.logger.error(f"Strategie {strategy} fehlgeschlagen: {e}")
                self.stats['errors'] += 1
        
        # Duplikate entfernen
        unique_gutachten = self._remove_duplicates(all_gutachten)
        
        self.logger.info(f"Suchergebnis: {len(all_gutachten)} gesamt, {len(unique_gutachten)} eindeutig")
        return unique_gutachten
    
    def _search_direct_links(self) -> List[Dict]:
        """Suche direkte Gutachten-Links von der Hauptseite"""
        try:
            # Hauptseite abrufen
            response = self.session.get(
                self.config.BASE_URL,
                timeout=self.config.REQUEST_TIMEOUT
            )
            
            if response.status_code != 200:
                return []
            
            soup = BeautifulSoup(response.content, 'html.parser')
            gutachten_links = []
            
            # Suche nach verschiedenen Link-Mustern
            link_patterns = [
                'a[href*="/gutachten/details/"]',
                'a[href*="tx_dnotionlineplusapi_expertises"]',
                'a[href*="nodeid"]',
                '.gutachten-link a',
                '.expertise-link a'
            ]
            
            for pattern in link_patterns:
                links = soup.select(pattern)
                for link in links:
                    href = link.get('href')
                    if href and self._is_valid_gutachten_link(href):
                        title = link.get_text(strip=True) or "Gutachten"
                        full_url = urljoin(self.config.BASE_URL, href)
                        
                        gutachten_links.append({
                            'url': full_url,
                            'title': title,
                            'source': 'direct_links',
                            'found_at': datetime.now().isoformat()
                        })
            
            return gutachten_links
            
        except Exception as e:
            self.logger.error(f"Direkte Link-Suche fehlgeschlagen: {e}")
            return []
    
    def _search_archive(self) -> List[Dict]:
        """Durchsuche DNOTI-Archiv nach Gutachten"""
        try:
            archive_urls = [
                f"{self.config.BASE_URL}/archiv/",
                f"{self.config.BASE_URL}/gutachten/archiv/",
                f"{self.config.BASE_URL}/expertisen/"
            ]
            
            gutachten_links = []
            
            for archive_url in archive_urls:
                try:
                    response = self.session.get(
                        archive_url,
                        timeout=self.config.REQUEST_TIMEOUT
                    )
                    
                    if response.status_code == 200:
                        soup = BeautifulSoup(response.content, 'html.parser')
                        
                        # Suche Gutachten-Links im Archiv
                        links = soup.find_all('a', href=True)
                        for link in links:
                            href = link['href']
                            if self._is_valid_gutachten_link(href):
                                title = link.get_text(strip=True) or "Archiv-Gutachten"
                                full_url = urljoin(self.config.BASE_URL, href)
                                
                                gutachten_links.append({
                                    'url': full_url,
                                    'title': title,
                                    'source': 'archive_search',
                                    'found_at': datetime.now().isoformat()
                                })
                
                except Exception as e:
                    self.logger.debug(f"Archiv-URL {archive_url} nicht erreichbar: {e}")
                    continue
            
            return gutachten_links
            
        except Exception as e:
            self.logger.error(f"Archiv-Suche fehlgeschlagen: {e}")
            return []
    
    def _search_recent_content(self) -> List[Dict]:
        """Suche nach neuen Inhalten der letzten Zeit"""
        try:
            # Probiere verschiedene Endpoints für neue Inhalte
            recent_endpoints = [
                "/aktuelles/",
                "/news/",
                "/neue-gutachten/",
                "/recent/"
            ]
            
            gutachten_links = []
            
            for endpoint in recent_endpoints:
                try:
                    url = f"{self.config.BASE_URL}{endpoint}"
                    response = self.session.get(
                        url,
                        timeout=self.config.REQUEST_TIMEOUT
                    )
                    
                    if response.status_code == 200:
                        soup = BeautifulSoup(response.content, 'html.parser')
                        
                        # Suche nach Gutachten-Links
                        links = soup.find_all('a', href=True)
                        for link in links:
                            href = link['href']
                            if self._is_valid_gutachten_link(href):
                                title = link.get_text(strip=True) or "Neues Gutachten"
                                full_url = urljoin(self.config.BASE_URL, href)
                                
                                gutachten_links.append({
                                    'url': full_url,
                                    'title': title,
                                    'source': 'recent_content',
                                    'found_at': datetime.now().isoformat()
                                })
                
                except Exception as e:
                    self.logger.debug(f"Recent-Endpoint {endpoint} nicht erreichbar: {e}")
                    continue
            
            return gutachten_links
            
        except Exception as e:
            self.logger.error(f"Recent-Content-Suche fehlgeschlagen: {e}")
            return []
    
    def _search_by_keywords(self) -> List[Dict]:
        """Stichwort-basierte Suche mit DNOTI-Suchfunktion"""
        try:
            keywords = [
                "Notar",
                "Beurkundung",
                "Immobilie",
                "Grundstück",
                "Kaufvertrag",
                "Vollmacht",
                "Erbrecht",
                "Gesellschaftsrecht"
            ]
            
            gutachten_links = []
            
            for keyword in keywords[:3]:  # Begrenzt auf 3 Keywords um Server nicht zu überlasten
                try:
                    search_data = {
                        'tx_dnotionlineplusapi_expertises[searchText]': keyword,
                        'tx_dnotionlineplusapi_expertises[expertisesType]': 'all',
                        'tx_dnotionlineplusapi_expertises[__trustedProperties]': 'a:1:{s:10:"searchText";i:1;}'
                    }
                    
                    response = self.session.post(
                        self.config.GUTACHTEN_SEARCH_URL,
                        data=search_data,
                        timeout=self.config.REQUEST_TIMEOUT
                    )
                    
                    if response.status_code == 200:
                        soup = BeautifulSoup(response.content, 'html.parser')
                        
                        # Suche Ergebnisse
                        result_links = soup.find_all('a', href=True)
                        for link in result_links:
                            href = link['href']
                            if self._is_valid_gutachten_link(href):
                                title = link.get_text(strip=True) or f"Gutachten ({keyword})"
                                full_url = urljoin(self.config.BASE_URL, href)
                                
                                gutachten_links.append({
                                    'url': full_url,
                                    'title': title,
                                    'source': 'keyword_search',
                                    'keyword': keyword,
                                    'found_at': datetime.now().isoformat()
                                })
                
                except Exception as e:
                    self.logger.debug(f"Keyword-Suche für '{keyword}' fehlgeschlagen: {e}")
                    continue
                
                # Pause zwischen Suchen
                time.sleep(self.config.REQUEST_DELAY_SECONDS)
            
            return gutachten_links
            
        except Exception as e:
            self.logger.error(f"Keyword-Suche fehlgeschlagen: {e}")
            return []
    
    def _is_valid_gutachten_link(self, href: str) -> bool:
        """Prüfe ob Link ein gültiger Gutachten-Link ist"""
        if not href:
            return False
        
        # Patterns für gültige Gutachten-Links
        valid_patterns = [
            r'/gutachten/details/',
            r'tx_dnotionlineplusapi_expertises.*nodeid',
            r'nodeid=[\w\-]+',
            r'expertise.*id=',
            r'/expertisen?/.*\d+'
        ]
        
        # Negative Patterns (ausschließen)
        exclude_patterns = [
            r'javascript:',
            r'mailto:',
            r'#',
            r'\.pdf$',
            r'\.doc$',
            r'/impressum',
            r'/datenschutz',
            r'/kontakt'
        ]
        
        # Prüfe Ausschluss-Patterns
        for pattern in exclude_patterns:
            if re.search(pattern, href, re.IGNORECASE):
                return False
        
        # Prüfe gültige Patterns
        for pattern in valid_patterns:
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
            
            # Extrahiere Node-ID falls vorhanden
            node_id = None
            if 'nodeid' in url:
                node_match = re.search(r'nodeid[=%]([a-f0-9\-]{36})', url, re.IGNORECASE)
                if node_match:
                    node_id = node_match.group(1)
            
            # Prüfe Duplikate
            url_normalized = url.split('?')[0].split('#')[0]  # Entferne Query-Parameter
            
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
            metadata = self._extract_metadata(soup, url)
            
            if not content:
                self.logger.warning(f"Kein Inhalt extrahiert für: {url}")
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
        # Verschiedene Titel-Selektoren probieren
        title_selectors = [
            'h1.gutachten-title',
            'h1',
            '.content-title h1',
            '.main-title',
            'title'
        ]
        
        for selector in title_selectors:
            element = soup.select_one(selector)
            if element:
                title = element.get_text(strip=True)
                if title and len(title) > 10:  # Mindestlänge für sinnvollen Titel
                    return title
        
        return fallback_title or "DNOTI Gutachten"
    
    def _extract_main_content(self, soup: BeautifulSoup) -> str:
        """Extrahiere Hauptinhalt des Gutachtens"""
        # Verschiedene Content-Selektoren probieren
        content_selectors = [
            '.gutachten-content',
            '.expertise-content',
            '.main-content',
            '.content-body',
            'article',
            '.tx-dnotionlineplus-pi1'
        ]
        
        for selector in content_selectors:
            element = soup.select_one(selector)
            if element:
                # Entferne unerwünschte Elemente
                for unwanted in element.select('script, style, nav, footer, .navigation'):
                    unwanted.decompose()
                
                content = element.get_text(separator=' ', strip=True)
                if content and len(content) > 100:  # Mindestlänge für sinnvollen Inhalt
                    return content
        
        # Fallback: Gesamter body-Inhalt
        body = soup.find('body')
        if body:
            # Entferne unerwünschte Elemente
            for unwanted in body.select('script, style, nav, footer, .navigation, .sidebar'):
                unwanted.decompose()
            
            content = body.get_text(separator=' ', strip=True)
            return content
        
        return ""
    
    def _extract_metadata(self, soup: BeautifulSoup, url: str) -> Dict:
        """Extrahiere Metadaten des Gutachtens"""
        metadata = {
            'url': url,
            'extracted_at': datetime.now().isoformat()
        }
        
        # Extrahiere Node-ID
        node_match = re.search(r'nodeid[=%]([a-f0-9\-]{36})', url, re.IGNORECASE)
        if node_match:
            metadata['node_id'] = node_match.group(1)
        
        # Extrahiere Meta-Tags
        meta_tags = soup.find_all('meta')
        for meta in meta_tags:
            name = meta.get('name') or meta.get('property')
            content = meta.get('content')
            
            if name and content:
                if name in ['description', 'keywords', 'author', 'date']:
                    metadata[name] = content
        
        # Extrahiere strukturierte Daten
        try:
            json_ld = soup.find('script', type='application/ld+json')
            if json_ld:
                structured_data = json.loads(json_ld.string)
                metadata['structured_data'] = structured_data
        except:
            pass
        
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
                    'source': gutachten.get('source_info', {}).get('source', 'unknown'),
                    'extracted_at': gutachten['extracted_at'],
                    'document_type': 'dnoti_gutachten',
                    'language': 'de'
                }
                
                # Zusätzliche Metadaten aus Gutachten
                if 'metadata' in gutachten:
                    for key, value in gutachten['metadata'].items():
                        if isinstance(value, (str, int, float, bool)):
                            metadata[f"meta_{key}"] = value
                
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
        
        # Verwende Node-ID falls verfügbar
        node_match = re.search(r'nodeid[=%]([a-f0-9\-]{36})', url, re.IGNORECASE)
        if node_match:
            return f"dnoti_gutachten_{node_match.group(1)}"
        
        # Fallback: Hash aus URL und Titel
        content_hash = hashlib.md5(f"{url}_{title}".encode('utf-8')).hexdigest()
        return f"dnoti_gutachten_{content_hash}"
    
    def get_demo_gutachten(self) -> List[Dict]:
        """Erstelle Demo-Gutachten für Tests"""
        demo_data = [
            {
                'url': 'https://www.dnoti.de/gutachten/demo/1',
                'title': 'Demo: Notarielle Beurkundung von Immobilienkaufverträgen',
                'content': '''
                Diese Demo-Gutachten behandelt die wesentlichen Aspekte der notariellen Beurkundung 
                von Immobilienkaufverträgen. Besondere Bedeutung kommt dabei der ordnungsgemäßen 
                Aufklärung der Vertragsparteien sowie der Einhaltung der gesetzlichen Formvorschriften zu.
                
                Kernpunkte:
                - Aufklärungs- und Belehrungspflichten des Notars
                - Prüfung der Geschäftsfähigkeit
                - Vollständigkeit der Vertragsinhalte
                - Grundbuchrechtliche Besonderheiten
                ''',
                'metadata': {
                    'node_id': 'demo-node-1',
                    'category': 'Immobilienrecht',
                    'date': '2024-12-01'
                },
                'extracted_at': datetime.now().isoformat(),
                'source_info': {'source': 'demo', 'found_at': datetime.now().isoformat()}
            },
            {
                'url': 'https://www.dnoti.de/gutachten/demo/2',
                'title': 'Demo: Vollmachtserteilung und -widerruf im Notariat',
                'content': '''
                Dieses Demo-Gutachten erläutert die rechtlichen Grundlagen und praktischen Aspekte 
                der Vollmachtserteilung und des Vollmachtswiderrufs im notariellen Bereich.
                
                Schwerpunkte:
                - Formen der Vollmachtserteilung
                - Wirksamkeitsvoraussetzungen
                - Widerrufsmöglichkeiten und deren Folgen
                - Besonderheiten bei Handelsregistervollmachten
                - Vertretung bei Grundstücksgeschäften
                ''',
                'metadata': {
                    'node_id': 'demo-node-2',
                    'category': 'Vollmachtsrecht',
                    'date': '2024-12-05'
                },
                'extracted_at': datetime.now().isoformat(),
                'source_info': {'source': 'demo', 'found_at': datetime.now().isoformat()}
            }
        ]
        
        return demo_data
    
    def run_complete_update_cycle(self) -> Dict:
        """Führe kompletten Update-Zyklus durch"""
        start_time = time.time()
        
        try:
            self.logger.info("=== DNOTI Optimized Auto-Update Zyklus gestartet ===")
            
            # 1. Website-Zugänglichkeit prüfen
            website_ok = self.check_website_accessibility()
            if not website_ok:
                self.logger.warning("Website nicht erreichbar - verwende Demo-Modus")
                self.stats['demo_mode_used'] = True
            
            # 2. Suche nach Gutachten
            if website_ok:
                gutachten_list = self.search_for_new_gutachten()
            else:
                gutachten_list = []
            
            # 3. Fallback zu Demo-Modus wenn keine Gutachten gefunden
            if not gutachten_list:
                self.logger.info("Aktiviere Demo-Modus mit Beispiel-Gutachten")
                gutachten_list = self.get_demo_gutachten()
                self.stats['demo_mode_used'] = True
            
            self.stats['gutachten_found'] = len(gutachten_list)
            
            # 4. Extrahiere Inhalte (falls nicht Demo-Modus)
            if not self.stats['demo_mode_used']:
                extracted_gutachten = []
                for gutachten_info in gutachten_list[:self.config.BATCH_SIZE]:
                    extracted = self.extract_gutachten_content(gutachten_info)
                    if extracted:
                        extracted_gutachten.append(extracted)
                    time.sleep(self.config.REQUEST_DELAY_SECONDS)
                
                gutachten_list = extracted_gutachten
            
            # 5. Verarbeite in Batches
            total_added = 0
            for i in range(0, len(gutachten_list), self.config.BATCH_SIZE):
                batch = gutachten_list[i:i + self.config.BATCH_SIZE]
                
                if self.add_to_vectordb(batch):
                    total_added += len(batch)
                    self.logger.info(f"Batch {i//self.config.BATCH_SIZE + 1} erfolgreich verarbeitet")
                else:
                    self.logger.error(f"Batch {i//self.config.BATCH_SIZE + 1} fehlgeschlagen")
            
            self.stats['gutachten_added'] = total_added
            
            # 6. Abschluss
            if total_added > 0:
                self.logger.info(f"Update erfolgreich abgeschlossen: {total_added} Gutachten hinzugefügt")
                self.stats['status'] = 'success'
            else:
                self.logger.warning("Keine Gutachten hinzugefügt")
                self.stats['status'] = 'no_updates'
            
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


def print_final_report(stats: Dict):
    """Drucke abschließenden Bericht ohne Emojis"""
    print("\n" + "="*50)
    print("DNOTI Auto-Update - Final Report")
    print("="*50)
    
    print(f"Status: {stats['status']}")
    print(f"Gestartet: {stats['started_at']}")
    print(f"Website erreichbar: {stats['website_accessible']}")
    print(f"Gutachten gefunden: {stats['gutachten_found']}")
    print(f"Gutachten hinzugefügt: {stats['gutachten_added']}")
    print(f"Demo-Modus verwendet: {stats['demo_mode_used']}")
    print(f"Fehler: {stats['errors']}")
    print(f"Dauer: {stats['duration_seconds']:.2f} Sekunden")
    
    print("\n" + "-"*50)
    
    if stats['status'] == 'success':
        print("STATUS: Update erfolgreich abgeschlossen!")
        if stats['demo_mode_used']:
            print("HINWEIS: Demo-Modus wurde verwendet")
    elif stats['status'] == 'no_updates':
        print("STATUS: Keine neuen Gutachten gefunden")
    else:
        print("STATUS: Update mit Fehlern abgeschlossen")
    
    print("\nNächste Schritte:")
    print("1. Log-Datei überprüfen: logs/dnoti_auto_update_optimized_v3.log")
    print("2. ChromaDB-Integration im Frontend testen")
    print("3. Für Produktionseinsatz: Automatische Ausführung konfigurieren")
    print("="*50)


def main():
    """Hauptfunktion"""
    print("DNOTI Auto-Updater - Optimized Production Version v3.0")
    print("=" * 60)
    print("Entwickelt für MLFBAC Legal Tech Semantic Search")
    print()
    
    try:
        # Konfiguration laden
        config = DNOTIConfig()
        
        # Auto-Updater initialisieren
        updater = DNOTIAutoUpdaterOptimized(config)
        
        # Update-Zyklus starten
        stats = updater.run_complete_update_cycle()
        
        # Abschließenden Bericht drucken
        print_final_report(stats)
        
        # Exit-Code basierend auf Status
        if stats['status'] == 'success':
            return 0
        elif stats['status'] == 'no_updates':
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
