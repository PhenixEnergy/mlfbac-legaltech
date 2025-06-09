#!/usr/bin/env python3
"""
DNOTI Auto-Update Service - Produktionsreife Version
Intelligente Aktualisierung der Rechtsgutachten-Datenbank

Entwickelt von einem erfahrenen Legal Tech Experten
Implementiert Best Practices für Web Scraping und Datenbankmanagement
"""

import asyncio
import logging
import time
import hashlib
import json
import sys
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
from src.search.semantic_search import SemanticSearchEngine

# ========== KONFIGURATION ==========

@dataclass
class UpdateConfig:
    """Zentrale Konfiguration für den Auto-Update Service"""
    
    # DNOTI Website Konfiguration
    BASE_URL: str = "https://www.dnoti.de/gutachten/"
    DETAIL_URL_PATTERN: str = "details/?tx_dnotionlineplusapi_expertises"
    
    # Update-Strategien
    CHECK_INTERVAL_HOURS: int = 12  # Alle 12 Stunden prüfen
    FULL_SCAN_INTERVAL_DAYS: int = 7  # Wöchentlicher Vollscan
    MAX_PAGES_PER_RUN: int = 3  # Begrenzte Seitenzahl pro Durchlauf
    
    # Qualitätssicherung
    MIN_CONTENT_LENGTH: int = 100  # Mindestlänge für validen Content
    MAX_RETRIES: int = 3  # Wiederholungsversuche bei Fehlern
    CONTENT_VALIDATION_KEYWORDS: List[str] = None
    
    # Performance & Rate Limiting
    REQUEST_DELAY_SECONDS: float = 1.0  # Verzögerung zwischen Anfragen
    REQUEST_TIMEOUT_SECONDS: int = 30  # Timeout für Einzelanfragen
    CONCURRENT_REQUESTS: int = 3  # Parallele Anfragen
    
    # Datenbank
    DB_CONFIG_PATH: str = "config/database.yaml"
    COLLECTION_NAME: str = "dnoti_legal_documents"
    BACKUP_ENABLED: bool = True
    
    # Monitoring & Logging
    LOG_LEVEL: str = "INFO"
    LOG_FILE: str = "logs/auto_update.log"
    METRICS_FILE: str = "logs/update_metrics.json"
    NOTIFICATION_WEBHOOK: Optional[str] = None
    
    # Headers für Web Requests
    USER_AGENT: str = "LegalTech-AutoUpdater/1.0 (Research Purpose)"
    ACCEPT_LANGUAGE: str = "de-DE,de;q=0.9,en;q=0.8"
    
    def __post_init__(self):
        if self.CONTENT_VALIDATION_KEYWORDS is None:
            self.CONTENT_VALIDATION_KEYWORDS = [
                "gutachten", "rechtsbezug", "aktenzeichen", "entscheidung",
                "rechtsgrundlage", "sachverhalt", "rechtsprechung"
            ]

# ========== DATENSTRUKTUREN ==========

@dataclass
class GutachtenRecord:
    """Struktur für ein DNOTI-Gutachten"""
    id: str
    url: str
    title: str
    gutachten_nummer: str
    erscheinungsdatum: str
    rechtsbezug: str
    normen: str
    content: str
    content_hash: str
    scraped_timestamp: str
    metadata: Dict = None
    
    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}
        if not self.content_hash:
            self.content_hash = self._calculate_content_hash()
    
    def _calculate_content_hash(self) -> str:
        """Berechnet SHA-256 Hash des Inhalts für Duplikaterkennung"""
        content_to_hash = f"{self.title}{self.content}{self.gutachten_nummer}"
        return hashlib.sha256(content_to_hash.encode('utf-8')).hexdigest()
    
    def to_chroma_format(self) -> Dict:
        """Konvertiert in ChromaDB Format"""
        return {
            'id': f"dnoti_{self.id}",
            'text': self._build_searchable_text(),
            'metadata': {
                'gutachten_nummer': self.gutachten_nummer,
                'erscheinungsdatum': self.erscheinungsdatum,
                'rechtsbezug': self.rechtsbezug,
                'normen': self.normen,
                'url': self.url,
                'source': 'dnoti',
                'doc_type': 'legal_opinion',
                'content_hash': self.content_hash,
                'scraped_timestamp': self.scraped_timestamp,
                **self.metadata
            }
        }
    
    def _build_searchable_text(self) -> str:
        """Erstellt optimierten Text für semantische Suche"""
        return f"""Gutachten Nr. {self.gutachten_nummer} vom {self.erscheinungsdatum}
Titel: {self.title}
Rechtsbezug: {self.rechtsbezug}
Normen: {self.normen}

{self.content}"""

@dataclass
class UpdateMetrics:
    """Metriken für Update-Durchläufe"""
    run_id: str
    start_time: datetime
    end_time: Optional[datetime] = None
    pages_scanned: int = 0
    urls_discovered: int = 0
    new_documents: int = 0
    updated_documents: int = 0
    failed_extractions: int = 0
    duplicate_count: int = 0
    errors: List[str] = None
    
    def __post_init__(self):
        if self.errors is None:
            self.errors = []
    
    def duration_seconds(self) -> float:
        """Berechnet Laufzeit in Sekunden"""
        if self.end_time:
            return (self.end_time - self.start_time).total_seconds()
        return 0.0
    
    def success_rate(self) -> float:
        """Berechnet Erfolgsrate"""
        total = self.urls_discovered
        if total == 0:
            return 100.0
        successful = total - self.failed_extractions
        return (successful / total) * 100.0

# ========== URL & CONTENT TRACKING ==========

class UrlStateManager:
    """Verwaltet bearbeitete URLs und Content-Hashes"""
    
    def __init__(self, state_file: str = "data/processed/url_state.json"):
        self.state_file = Path(state_file)
        self.state_file.parent.mkdir(parents=True, exist_ok=True)
        self.processed_urls: Set[str] = set()
        self.content_hashes: Set[str] = set()
        self.url_metadata: Dict[str, Dict] = {}
        self.load_state()
    
    def load_state(self):
        """Lädt gespeicherten Zustand"""
        if self.state_file.exists():
            try:
                with open(self.state_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.processed_urls = set(data.get('processed_urls', []))
                    self.content_hashes = set(data.get('content_hashes', []))
                    self.url_metadata = data.get('url_metadata', {})
            except Exception as e:
                logging.warning(f"Fehler beim Laden des URL-Zustands: {e}")
    
    def save_state(self):
        """Speichert aktuellen Zustand"""
        try:
            data = {
                'processed_urls': list(self.processed_urls),
                'content_hashes': list(self.content_hashes),
                'url_metadata': self.url_metadata,
                'last_updated': datetime.now().isoformat()
            }
            with open(self.state_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
        except Exception as e:
            logging.error(f"Fehler beim Speichern des URL-Zustands: {e}")
    
    def is_url_processed(self, url: str) -> bool:
        """Prüft ob URL bereits bearbeitet wurde"""
        return url in self.processed_urls
    
    def is_content_duplicate(self, content_hash: str) -> bool:
        """Prüft ob Inhalt bereits existiert"""
        return content_hash in self.content_hashes
    
    def mark_url_processed(self, url: str, metadata: Dict = None):
        """Markiert URL als bearbeitet"""
        self.processed_urls.add(url)
        if metadata:
            self.url_metadata[url] = {
                **metadata,
                'processed_timestamp': datetime.now().isoformat()
            }
    
    def mark_content_hash(self, content_hash: str):
        """Speichert Content-Hash"""
        self.content_hashes.add(content_hash)
    
    def get_stats(self) -> Dict:
        """Liefert Statistiken"""
        return {
            'total_processed_urls': len(self.processed_urls),
            'total_content_hashes': len(self.content_hashes),
            'last_state_save': self.state_file.stat().st_mtime if self.state_file.exists() else None
        }

# ========== INTELLIGENT WEB SCRAPER ==========

class IntelligentDNOTIScraper:
    """Intelligenter Web Scraper für DNOTI mit Qualitätssicherung"""
    
    def __init__(self, config: UpdateConfig):
        self.config = config
        self.session = self._setup_session()
        self.logger = logging.getLogger(self.__class__.__name__)
        
        # CSS Selektoren (müssen ggf. angepasst werden nach Website-Analyse)
        self.selectors = {
            'gutachten_links': 'a[href*="details/?tx_dnotionlineplusapi_expertises"]',
            'title': 'h1, .content-header h1, .page-title',
            'content_main': '.content-main, .main-content, article, .content',
            'gutachten_nummer': '*:contains("Gutachten Nr.")',
            'erscheinungsdatum': '*:contains("Erscheinungsdatum")',
            'rechtsbezug': '*:contains("Rechtsbezug")',
            'normen': '*:contains("Normen")'
        }
    
    def _setup_session(self) -> requests.Session:
        """Konfiguriert HTTP Session mit optimalen Einstellungen"""
        session = requests.Session()
        session.headers.update({
            'User-Agent': self.config.USER_AGENT,
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': self.config.ACCEPT_LANGUAGE,
            'Accept-Encoding': 'gzip, deflate',
            'DNT': '1',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1'
        })
        
        # Request-Adapter mit Retry-Logik
        from requests.adapters import HTTPAdapter
        from requests.packages.urllib3.util.retry import Retry
        
        retry_strategy = Retry(
            total=self.config.MAX_RETRIES,
            backoff_factor=1,
            status_forcelist=[429, 500, 502, 503, 504],
        )
        adapter = HTTPAdapter(max_retries=retry_strategy)
        session.mount("http://", adapter)
        session.mount("https://", adapter)
        
        return session
    
    async def discover_gutachten_urls(self, max_pages: int = None) -> List[str]:
        """Entdeckt neue Gutachten-URLs von Listenseiten"""
        if max_pages is None:
            max_pages = self.config.MAX_PAGES_PER_RUN
        
        discovered_urls = []
        
        for page in range(1, max_pages + 1):
            self.logger.info(f"📄 Scanne Seite {page} nach neuen Gutachten...")
            
            try:
                page_urls = await self._extract_urls_from_page(page)
                discovered_urls.extend(page_urls)
                
                # Rate Limiting
                await asyncio.sleep(self.config.REQUEST_DELAY_SECONDS)
                
            except Exception as e:
                self.logger.error(f"Fehler beim Scannen von Seite {page}: {e}")
                continue
        
        self.logger.info(f"🔍 Insgesamt {len(discovered_urls)} URLs entdeckt")
        return list(set(discovered_urls))  # Duplikate entfernen
    
    async def _extract_urls_from_page(self, page: int) -> List[str]:
        """Extrahiert Gutachten-URLs von einer Listenseite"""
        params = {"tx_dnotionlineplusapi_expertises[page]": page}
        
        response = await self._make_request(self.config.BASE_URL, params=params)
        if not response:
            return []
        
        soup = BeautifulSoup(response.text, 'html.parser')
        links = soup.select(self.selectors['gutachten_links'])
        
        urls = []
        for link in links:
            href = link.get('href')
            if href and self.config.DETAIL_URL_PATTERN in href:
                full_url = urljoin(self.config.BASE_URL, href)
                urls.append(full_url)
        
        self.logger.debug(f"Seite {page}: {len(urls)} URLs gefunden")
        return urls
    
    async def extract_gutachten(self, url: str) -> Optional[GutachtenRecord]:
        """Extrahiert vollständige Gutachten-Daten von Detail-URL"""
        self.logger.debug(f"📖 Extrahiere Gutachten von: {url}")
        
        response = await self._make_request(url)
        if not response:
            return None
        
        soup = BeautifulSoup(response.text, 'html.parser')
        
        try:
            # Basis-Daten extrahieren
            title = self._extract_title(soup)
            content = self._extract_content(soup)
            
            # Validierung
            if not self._validate_content(content):
                self.logger.warning(f"Content-Validierung fehlgeschlagen für: {url}")
                return None
            
            # Metadaten extrahieren
            gutachten_nummer = self._extract_metadata_field(soup, "Gutachten Nr.")
            erscheinungsdatum = self._extract_metadata_field(soup, "Erscheinungsdatum")
            rechtsbezug = self._extract_metadata_field(soup, "Rechtsbezug")
            normen = self._extract_metadata_field(soup, "Normen")
            
            # Unique ID generieren
            doc_id = self._generate_document_id(url, gutachten_nummer)
            
            return GutachtenRecord(
                id=doc_id,
                url=url,
                title=title,
                gutachten_nummer=gutachten_nummer,
                erscheinungsdatum=erscheinungsdatum,
                rechtsbezug=rechtsbezug,
                normen=normen,
                content=content,
                content_hash="",  # Wird automatisch berechnet
                scraped_timestamp=datetime.now().isoformat()
            )
            
        except Exception as e:
            self.logger.error(f"Fehler beim Extrahieren von {url}: {e}")
            return None
    
    def _extract_title(self, soup: BeautifulSoup) -> str:
        """Extrahiert Titel mit Fallback-Strategien"""
        for selector in self.selectors['title'].split(', '):
            element = soup.select_one(selector)
            if element:
                title = element.get_text(strip=True)
                if title and len(title) > 10:
                    return title
        
        # Fallback: Verwende page title
        title_tag = soup.find('title')
        if title_tag:
            return title_tag.get_text(strip=True)
        
        return "Ohne Titel"
    
    def _extract_content(self, soup: BeautifulSoup) -> str:
        """Extrahiert Hauptinhalt mit intelligenter Filterung"""
        content_parts = []
        
        # Versuche verschiedene Content-Selektoren
        for selector in self.selectors['content_main'].split(', '):
            content_div = soup.select_one(selector)
            if content_div:
                # Entferne unwünschte Elemente
                for unwanted in content_div(['nav', 'aside', 'header', 'footer', 
                                           '.navigation', '.sidebar', '.ads']):
                    unwanted.decompose()
                
                # Extrahiere Textinhalt
                paragraphs = content_div.find_all(['p', 'div', 'section'])
                for p in paragraphs:
                    text = p.get_text(strip=True)
                    if text and len(text) > 20:  # Filtere sehr kurze Texte
                        content_parts.append(text)
                
                if content_parts:
                    break
        
        # Fallback: Alle Paragraphen der Seite
        if not content_parts:
            paragraphs = soup.find_all('p')
            content_parts = [p.get_text(strip=True) for p in paragraphs 
                            if p.get_text(strip=True) and len(p.get_text(strip=True)) > 20]
        
        return '\n\n'.join(content_parts)
    
    def _extract_metadata_field(self, soup: BeautifulSoup, field_name: str) -> str:
        """Extrahiert spezifische Metadatenfelder"""
        # Suche nach Text der das Feld enthält
        for element in soup.find_all(text=lambda text: text and field_name.lower() in text.lower()):
            parent = element.parent
            if parent:
                text = parent.get_text(strip=True)
                # Extrahiere Wert nach dem Feldnamen
                if ':' in text:
                    parts = text.split(':', 1)
                    if len(parts) > 1:
                        return parts[1].strip()
                
                # Alternative: Suche im nächsten Geschwister-Element
                next_sibling = parent.find_next_sibling()
                if next_sibling:
                    sibling_text = next_sibling.get_text(strip=True)
                    if sibling_text:
                        return sibling_text
        
        return ""
    
    def _validate_content(self, content: str) -> bool:
        """Validiert extrahierten Content"""
        if len(content) < self.config.MIN_CONTENT_LENGTH:
            return False
        
        # Prüfe auf relevante Keywords
        content_lower = content.lower()
        keyword_found = any(keyword in content_lower 
                          for keyword in self.config.CONTENT_VALIDATION_KEYWORDS)
        
        return keyword_found
    
    def _generate_document_id(self, url: str, gutachten_nummer: str) -> str:
        """Generiert eindeutige Dokument-ID"""
        if gutachten_nummer:
            return f"gutachten_{gutachten_nummer}"
        else:
            # Fallback: URL-basierte ID
            url_hash = hashlib.md5(url.encode()).hexdigest()[:8]
            return f"gutachten_{url_hash}"
    
    async def _make_request(self, url: str, **kwargs) -> Optional[requests.Response]:
        """Macht HTTP-Request mit Error Handling"""
        try:
            loop = asyncio.get_event_loop()
            response = await loop.run_in_executor(
                None, 
                lambda: self.session.get(url, timeout=self.config.REQUEST_TIMEOUT_SECONDS, **kwargs)
            )
            response.raise_for_status()
            return response
            
        except requests.RequestException as e:
            self.logger.error(f"HTTP-Fehler für {url}: {e}")
            return None
        except Exception as e:
            self.logger.error(f"Unerwarteter Fehler für {url}: {e}")
            return None

# ========== AUTO-UPDATE SERVICE ==========

class DNOTIAutoUpdateService:
    """Hauptservice für automatische DNOTI-Updates"""
    
    def __init__(self, config: UpdateConfig):
        self.config = config
        self.logger = self._setup_logging()
        self.scraper = IntelligentDNOTIScraper(config)
        self.url_manager = UrlStateManager()
        self.db_client = None
        self.search_engine = None
        
        # Initialisiere Datenbankverbindung
        self._initialize_database()
    
    def _setup_logging(self) -> logging.Logger:
        """Konfiguriert Logging"""
        # Erstelle Log-Verzeichnis
        log_file = Path(self.config.LOG_FILE)
        log_file.parent.mkdir(parents=True, exist_ok=True)
        
        # Konfiguriere Logger
        logger = logging.getLogger('DNOTIAutoUpdate')
        logger.setLevel(getattr(logging, self.config.LOG_LEVEL))
        
        # File Handler
        file_handler = logging.FileHandler(log_file, encoding='utf-8')
        file_handler.setLevel(logging.DEBUG)
        
        # Console Handler
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        
        # Formatter
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        file_handler.setFormatter(formatter)
        console_handler.setFormatter(formatter)
        
        logger.addHandler(file_handler)
        logger.addHandler(console_handler)
        
        return logger
    
    def _initialize_database(self):
        """Initialisiert Datenbankverbindung"""
        try:
            config_path = Path(self.config.DB_CONFIG_PATH)
            if not config_path.exists():
                raise FileNotFoundError(f"Datenbank-Konfiguration nicht gefunden: {config_path}")
            
            self.db_client = ChromaDBClient(config_path)
            self.search_engine = SemanticSearchEngine(config_path)
            
            # Stelle sicher, dass Collection existiert
            self._ensure_collection_exists()
            
            self.logger.info("✅ Datenbankverbindung erfolgreich initialisiert")
            
        except Exception as e:
            self.logger.error(f"❌ Fehler bei Datenbankinitialisierung: {e}")
            raise
    
    def _ensure_collection_exists(self):
        """Stellt sicher, dass die Gutachten-Collection existiert"""
        try:
            # Versuche Collection zu laden
            collection = self.db_client.get_collection(self.config.COLLECTION_NAME)
            self.logger.info(f"Collection '{self.config.COLLECTION_NAME}' gefunden")
        except:
            # Collection existiert nicht, erstelle sie
            collection = self.db_client.create_collection(self.config.COLLECTION_NAME)
            self.logger.info(f"Collection '{self.config.COLLECTION_NAME}' erstellt")
    
    async def run_update_cycle(self) -> UpdateMetrics:
        """Führt einen vollständigen Update-Zyklus durch"""
        run_id = str(uuid.uuid4())[:8]
        metrics = UpdateMetrics(run_id=run_id, start_time=datetime.now())
        
        self.logger.info(f"🚀 Starte Update-Zyklus {run_id}")
        
        try:
            # 1. URL Discovery
            self.logger.info("🔍 Phase 1: URL Discovery")
            discovered_urls = await self.scraper.discover_gutachten_urls()
            metrics.urls_discovered = len(discovered_urls)
            
            # 2. Filtere bereits bearbeitete URLs
            new_urls = [url for url in discovered_urls 
                       if not self.url_manager.is_url_processed(url)]
            
            self.logger.info(f"📊 {len(new_urls)} neue URLs von {len(discovered_urls)} entdeckten")
            
            # 3. Extrahiere und verarbeite neue Gutachten
            if new_urls:
                self.logger.info("📖 Phase 2: Content Extraction")
                await self._process_new_gutachten(new_urls, metrics)
            
            # 4. Speichere Zustand
            self.url_manager.save_state()
            
            # 5. Update-Metriken finalisieren
            metrics.end_time = datetime.now()
            self._save_metrics(metrics)
            
            self.logger.info(f"✅ Update-Zyklus {run_id} abgeschlossen:")
            self.logger.info(f"   📄 Seiten gescannt: {metrics.pages_scanned}")
            self.logger.info(f"   🔗 URLs entdeckt: {metrics.urls_discovered}")
            self.logger.info(f"   ➕ Neue Dokumente: {metrics.new_documents}")
            self.logger.info(f"   🔄 Aktualisiert: {metrics.updated_documents}")
            self.logger.info(f"   ❌ Fehler: {metrics.failed_extractions}")
            self.logger.info(f"   ⏱️  Laufzeit: {metrics.duration_seconds():.1f}s")
            self.logger.info(f"   ✓ Erfolgsrate: {metrics.success_rate():.1f}%")
            
            return metrics
            
        except Exception as e:
            self.logger.error(f"❌ Kritischer Fehler in Update-Zyklus {run_id}: {e}")
            metrics.errors.append(str(e))
            metrics.end_time = datetime.now()
            raise
    
    async def _process_new_gutachten(self, urls: List[str], metrics: UpdateMetrics):
        """Verarbeitet neue Gutachten-URLs"""
        
        for i, url in enumerate(urls):
            self.logger.info(f"📖 Verarbeite {i+1}/{len(urls)}: {url}")
            
            try:
                # Extrahiere Gutachten
                gutachten = await self.scraper.extract_gutachten(url)
                
                if not gutachten:
                    metrics.failed_extractions += 1
                    continue
                
                # Prüfe auf Duplikate
                if self.url_manager.is_content_duplicate(gutachten.content_hash):
                    self.logger.info(f"⚠️ Duplikat erkannt (Content-Hash): {url}")
                    metrics.duplicate_count += 1
                    self.url_manager.mark_url_processed(url, {'status': 'duplicate'})
                    continue
                
                # Speichere in Datenbank
                success = await self._store_gutachten(gutachten)
                
                if success:
                    metrics.new_documents += 1
                    self.url_manager.mark_url_processed(url, {'status': 'success'})
                    self.url_manager.mark_content_hash(gutachten.content_hash)
                    self.logger.info(f"✅ Gutachten gespeichert: {gutachten.gutachten_nummer}")
                else:
                    metrics.failed_extractions += 1
                    self.url_manager.mark_url_processed(url, {'status': 'failed'})
                
                # Rate Limiting
                await asyncio.sleep(self.config.REQUEST_DELAY_SECONDS)
                
            except Exception as e:
                self.logger.error(f"Fehler beim Verarbeiten von {url}: {e}")
                metrics.failed_extractions += 1
                metrics.errors.append(f"{url}: {str(e)}")
    
    async def _store_gutachten(self, gutachten: GutachtenRecord) -> bool:
        """Speichert Gutachten in ChromaDB"""
        try:
            # Konvertiere zu ChromaDB Format
            chroma_doc = gutachten.to_chroma_format()
            
            # Füge zur Datenbank hinzu
            collection = self.db_client.get_collection(self.config.COLLECTION_NAME)
            
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(
                None,
                lambda: collection.add(
                    documents=[chroma_doc['text']],
                    ids=[chroma_doc['id']],
                    metadatas=[chroma_doc['metadata']]
                )
            )
            
            return True
            
        except Exception as e:
            self.logger.error(f"Fehler beim Speichern in ChromaDB: {e}")
            return False
    
    def _save_metrics(self, metrics: UpdateMetrics):
        """Speichert Update-Metriken"""
        try:
            metrics_file = Path(self.config.METRICS_FILE)
            metrics_file.parent.mkdir(parents=True, exist_ok=True)
            
            # Lade existierende Metriken
            all_metrics = []
            if metrics_file.exists():
                with open(metrics_file, 'r', encoding='utf-8') as f:
                    all_metrics = json.load(f)
            
            # Füge neue Metriken hinzu
            metrics_dict = asdict(metrics)
            metrics_dict['start_time'] = metrics.start_time.isoformat()
            if metrics.end_time:
                metrics_dict['end_time'] = metrics.end_time.isoformat()
            
            all_metrics.append(metrics_dict)
            
            # Behalte nur die letzten 100 Einträge
            all_metrics = all_metrics[-100:]
            
            # Speichere
            with open(metrics_file, 'w', encoding='utf-8') as f:
                json.dump(all_metrics, f, indent=2, ensure_ascii=False)
                
        except Exception as e:
            self.logger.error(f"Fehler beim Speichern der Metriken: {e}")
    
    async def run_scheduled_updates(self):
        """Führt geplante Updates durch"""
        self.logger.info("📅 Starte geplante Updates...")
        
        while True:
            try:
                # Führe Update-Zyklus durch
                await self.run_update_cycle()
                
                # Warte bis zum nächsten Zyklus
                self.logger.info(f"⏰ Nächster Update in {self.config.CHECK_INTERVAL_HOURS} Stunden")
                await asyncio.sleep(self.config.CHECK_INTERVAL_HOURS * 3600)
                
            except KeyboardInterrupt:
                self.logger.info("🛑 Update-Service gestoppt")
                break
            except Exception as e:
                self.logger.error(f"Fehler im geplanten Update: {e}")
                # Warte kurz vor erneutem Versuch
                await asyncio.sleep(300)  # 5 Minuten


# ========== COMMAND LINE INTERFACE ==========

async def main():
    """Hauptfunktion für CLI"""
    import argparse
    
    parser = argparse.ArgumentParser(description="DNOTI Auto-Update Service")
    parser.add_argument('--mode', choices=['single', 'scheduled'], default='single',
                       help='Update-Modus: single (einmalig) oder scheduled (dauerhaft)')
    parser.add_argument('--config', help='Pfad zur Konfigurationsdatei')
    parser.add_argument('--max-pages', type=int, help='Maximale Anzahl zu scannender Seiten')
    parser.add_argument('--log-level', choices=['DEBUG', 'INFO', 'WARNING', 'ERROR'], 
                       default='INFO', help='Log-Level')
    
    args = parser.parse_args()
    
    # Konfiguration erstellen
    config = UpdateConfig()
    if args.max_pages:
        config.MAX_PAGES_PER_RUN = args.max_pages
    if args.log_level:
        config.LOG_LEVEL = args.log_level
    
    # Service initialisieren
    service = DNOTIAutoUpdateService(config)
    
    if args.mode == 'single':
        # Einmaliger Update-Lauf
        print("🚀 Starte einmaligen Update-Lauf...")
        metrics = await service.run_update_cycle()
        print(f"✅ Update abgeschlossen. {metrics.new_documents} neue Dokumente hinzugefügt.")
        
    elif args.mode == 'scheduled':
        # Geplante Updates
        print("📅 Starte geplante Updates...")
        await service.run_scheduled_updates()

if __name__ == "__main__":
    asyncio.run(main())
