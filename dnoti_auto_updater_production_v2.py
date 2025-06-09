#!/usr/bin/env python3
"""
DNOTI Auto-Update Service - Production Ready Version
Finale Version für produktionsreife DNOTI-Gutachten Updates

Entwickelt für robuste, produktionsreife Updates der Legal Tech Datenbank
"""

import logging
import time
import hashlib
import json
import sys
import re
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple
from dataclasses import dataclass
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
    
    # DNOTI Website-Konfiguration
    BASE_URL: str = "https://www.dnoti.de"
    GUTACHTEN_SEARCH_URL: str = "https://www.dnoti.de/gutachten/"
    
    # Update-Strategien
    CHECK_INTERVAL_HOURS: int = 6
    BATCH_SIZE: int = 5
    MAX_RETRIES: int = 3
    
    # Request-Konfiguration
    REQUEST_TIMEOUT: int = 30
    REQUEST_DELAY_SECONDS: float = 2.0
    
    # ChromaDB-Konfiguration  
    COLLECTION_NAME: str = "dnoti_gutachten"
    
    # Logging
    LOG_FILE: str = "logs/dnoti_auto_update_production.log"
    LOG_LEVEL: str = "INFO"

# ========== HAUPTKLASSE ==========

class DNOTIAutoUpdaterProduction:
    """Produktionsreife Version des DNOTI Auto-Updaters"""
    
    def __init__(self, config: DNOTIConfig = None):
        self.config = config or DNOTIConfig()
        self.session = requests.Session()
        self.chroma_client = None
        
        # Setup robuste HTTP Headers
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
            'Accept-Language': 'de-DE,de;q=0.9,en;q=0.8',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
        })
        
        # Setup Logging
        self._setup_logging()
        
        # Initialisiere ChromaDB
        self._initialize_chromadb()
    
    def _setup_logging(self):
        """Konfiguriert robustes Logging"""
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
        self.logger.info("DNOTI Production Auto-Updater initialisiert")
    
    def _initialize_chromadb(self):
        """Initialisiert ChromaDB-Verbindung mit korrekten Methoden"""
        try:
            self.chroma_client = ChromaDBClient()
            
            # Stelle sicher, dass Collection existiert
            self.chroma_client.create_collection(
                collection_name=self.config.COLLECTION_NAME,
                reset_if_exists=False
            )
            
            self.logger.info(f"ChromaDB Collection '{self.config.COLLECTION_NAME}' bereit")
            
        except Exception as e:
            self.logger.error(f"Fehler beim Initialisieren von ChromaDB: {e}")
            raise
    
    def search_for_new_gutachten(self) -> List[Dict]:
        """
        Sucht nach neuen Gutachten mit robuster Strategie
        
        Returns:
            Liste von gefundenen Gutachten-Metadaten
        """
        all_gutachten = []
        
        try:
            self.logger.info("Starte Suche nach neuen DNOTI-Gutachten...")
            
            # Verwende bewährte Suchstrategien
            strategies = [
                self._search_recent_years,
                self._search_with_keywords,
                self._search_all_types
            ]
            
            for strategy in strategies:
                try:
                    strategy_name = strategy.__name__
                    self.logger.info(f"Verwende Strategie: {strategy_name}")
                    
                    results = strategy()
                    
                    if results:
                        all_gutachten.extend(results)
                        self.logger.info(f"{strategy_name}: {len(results)} Gutachten gefunden")
                    else:
                        self.logger.info(f"{strategy_name}: Keine Gutachten gefunden")
                    
                    time.sleep(self.config.REQUEST_DELAY_SECONDS)
                    
                except Exception as e:
                    self.logger.error(f"Fehler in Strategie {strategy.__name__}: {e}")
                    continue
            
            # Entferne Duplikate
            unique_gutachten = self._remove_duplicates(all_gutachten)
            
            self.logger.info(f"Insgesamt {len(all_gutachten)} gefunden, {len(unique_gutachten)} eindeutig")
            return unique_gutachten
            
        except Exception as e:
            self.logger.error(f"Fehler bei der Gutachten-Suche: {e}")
            return []
    
    def _search_recent_years(self) -> List[Dict]:
        """Sucht nach Gutachten der letzten Jahre"""
        gutachten = []
        current_year = datetime.now().year
        
        for year in [current_year, current_year - 1]:
            try:
                form_data = {
                    'tx_dnotionlineplusapi_expertises[page]': '1',
                    'tx_dnotionlineplusapi_expertises[expertisesType]': 'dnotiReport',
                    'tx_dnotionlineplusapi_expertises[reportYear]': str(year),
                    'tx_dnotionlineplusapi_expertises[searchTitle]': '',
                    'tx_dnotionlineplusapi_expertises[searchText]': '',
                }
                
                response = self._make_search_request(form_data)
                if response:
                    year_gutachten = self._extract_gutachten_from_response(response, f"year_{year}")
                    gutachten.extend(year_gutachten)
                
                time.sleep(self.config.REQUEST_DELAY_SECONDS)
                
            except Exception as e:
                self.logger.error(f"Fehler bei Jahr {year}: {e}")
                continue
        
        return gutachten
    
    def _search_with_keywords(self) -> List[Dict]:
        """Sucht mit relevanten Keywords"""
        gutachten = []
        keywords = ["Notar", "Beurkundung", "Immobilie"]
        
        for keyword in keywords:
            try:
                form_data = {
                    'tx_dnotionlineplusapi_expertises[page]': '1',
                    'tx_dnotionlineplusapi_expertises[expertisesType]': 'all',
                    'tx_dnotionlineplusapi_expertises[searchText]': keyword,
                    'tx_dnotionlineplusapi_expertises[searchTitle]': '',
                }
                
                response = self._make_search_request(form_data)
                if response:
                    keyword_gutachten = self._extract_gutachten_from_response(response, f"keyword_{keyword}")
                    gutachten.extend(keyword_gutachten)
                
                time.sleep(self.config.REQUEST_DELAY_SECONDS)
                
            except Exception as e:
                self.logger.error(f"Fehler bei Keyword {keyword}: {e}")
                continue
        
        return gutachten
    
    def _search_all_types(self) -> List[Dict]:
        """Sucht nach allen Gutachten-Typen"""
        gutachten = []
        
        try:
            form_data = {
                'tx_dnotionlineplusapi_expertises[page]': '1',
                'tx_dnotionlineplusapi_expertises[expertisesType]': 'all',
                'tx_dnotionlineplusapi_expertises[searchTitle]': '',
                'tx_dnotionlineplusapi_expertises[searchText]': '',
            }
            
            response = self._make_search_request(form_data)
            if response:
                all_gutachten = self._extract_gutachten_from_response(response, "all_types")
                gutachten.extend(all_gutachten)
            
        except Exception as e:
            self.logger.error(f"Fehler bei Suche nach allen Typen: {e}")
        
        return gutachten
    
    def _make_search_request(self, form_data: Dict) -> Optional[str]:
        """Macht einen robusten Such-Request"""
        for attempt in range(self.config.MAX_RETRIES):
            try:
                response = self.session.post(
                    self.config.GUTACHTEN_SEARCH_URL,
                    data=form_data,
                    timeout=self.config.REQUEST_TIMEOUT
                )
                
                if response.status_code == 200:
                    return response.text
                else:
                    self.logger.warning(f"HTTP {response.status_code} bei Versuch {attempt + 1}")
                    
            except Exception as e:
                self.logger.warning(f"Request-Fehler bei Versuch {attempt + 1}: {e}")
                
            if attempt < self.config.MAX_RETRIES - 1:
                time.sleep(1 * (attempt + 1))  # Exponential backoff
        
        return None
    
    def _extract_gutachten_from_response(self, html_content: str, search_context: str) -> List[Dict]:
        """Extrahiert Gutachten-Links aus der Response"""
        gutachten_list = []
        
        try:
            soup = BeautifulSoup(html_content, 'html.parser')
            
            # Mehrere Strategien zum Finden von Gutachten-Links
            
            # 1. Direkte Detail-Links
            detail_pattern = re.compile(r'/gutachten/details/.*nodeid.*')
            detail_links = soup.find_all('a', href=detail_pattern)
            
            for link in detail_links:
                gutachten_info = self._create_gutachten_info(link, search_context, 'detail_link')
                if gutachten_info:
                    gutachten_list.append(gutachten_info)
            
            # 2. Links in Ergebnis-Containern
            result_containers = soup.find_all(['div', 'article', 'li'], class_=re.compile(r'result|item|entry', re.I))
            
            for container in result_containers:
                links = container.find_all('a', href=True)
                for link in links:
                    href = link.get('href', '')
                    if 'gutachten' in href and href not in [l.get('url', '') for l in gutachten_list]:
                        gutachten_info = self._create_gutachten_info(link, search_context, 'container_link')
                        if gutachten_info:
                            gutachten_list.append(gutachten_info)
            
            # 3. Alle Links mit "gutachten" im Pfad (als Fallback)
            if not gutachten_list:
                all_links = soup.find_all('a', href=True)
                for link in all_links:
                    href = link.get('href', '')
                    if '/gutachten/' in href and href != '/gutachten/' and 'details' in href:
                        gutachten_info = self._create_gutachten_info(link, search_context, 'general_link')
                        if gutachten_info:
                            gutachten_list.append(gutachten_info)
            
            self.logger.debug(f"Extrahierte {len(gutachten_list)} Gutachten aus {search_context}")
            
        except Exception as e:
            self.logger.error(f"Fehler beim Extrahieren aus {search_context}: {e}")
        
        return gutachten_list
    
    def _create_gutachten_info(self, link, search_context: str, link_type: str) -> Optional[Dict]:
        """Erstellt Gutachten-Info aus einem Link"""
        try:
            href = link.get('href', '')
            if not href:
                return None
            
            full_url = urljoin(self.config.BASE_URL, href)
            title = link.get_text(strip=True) or "Unbekanntes Gutachten"
            
            # Extrahiere Node-ID falls verfügbar
            node_id_match = re.search(r'nodeid.*?=([a-f0-9-]+)', href)
            node_id = node_id_match.group(1) if node_id_match else f"auto_{hash(href)%100000}"
            
            return {
                'url': full_url,
                'title': title,
                'node_id': node_id,
                'search_context': search_context,
                'link_type': link_type,
                'found_date': datetime.now().isoformat()
            }
            
        except Exception as e:
            self.logger.debug(f"Fehler beim Erstellen der Gutachten-Info: {e}")
            return None
    
    def _remove_duplicates(self, gutachten_list: List[Dict]) -> List[Dict]:
        """Entfernt Duplikate basierend auf URL"""
        seen_urls = set()
        unique_gutachten = []
        
        for gutachten in gutachten_list:
            url = gutachten.get('url', '')
            if url and url not in seen_urls:
                seen_urls.add(url)
                unique_gutachten.append(gutachten)
        
        return unique_gutachten
    
    def fetch_gutachten_content(self, gutachten: Dict) -> Optional[Dict]:
        """
        Lädt den vollständigen Inhalt eines Gutachtens
        
        Args:
            gutachten: Gutachten-Metadaten
            
        Returns:
            Vollständiges Gutachten oder None
        """
        try:
            url = gutachten['url']
            self.logger.info(f"Lade Gutachten: {gutachten['title']}")
            
            for attempt in range(self.config.MAX_RETRIES):
                try:
                    response = self.session.get(url, timeout=self.config.REQUEST_TIMEOUT)
                    
                    if response.status_code == 200:
                        content = self._extract_content(response.text)
                        
                        if content and len(content.strip()) > 100:  # Mindestlänge
                            full_gutachten = {
                                **gutachten,
                                'content': content,
                                'content_hash': hashlib.md5(content.encode('utf-8')).hexdigest(),
                                'scraped_date': datetime.now().isoformat(),
                                'word_count': len(content.split())
                            }
                            
                            return full_gutachten
                        else:
                            self.logger.warning(f"Zu wenig Content in {url}")
                            return None
                    else:
                        self.logger.warning(f"HTTP {response.status_code} für {url}")
                        
                except Exception as e:
                    self.logger.warning(f"Fehler beim Laden {url}, Versuch {attempt + 1}: {e}")
                    
                if attempt < self.config.MAX_RETRIES - 1:
                    time.sleep(1 * (attempt + 1))
            
            return None
            
        except Exception as e:
            self.logger.error(f"Fehler beim Laden von Gutachten {gutachten.get('url', 'unknown')}: {e}")
            return None
    
    def _extract_content(self, html_content: str) -> str:
        """Extrahiert den Haupttext aus HTML"""
        try:
            soup = BeautifulSoup(html_content, 'html.parser')
            
            # Entferne Navigations- und Footer-Elemente
            for unwanted in soup.find_all(['nav', 'footer', 'header', 'aside', 'script', 'style']):
                unwanted.decompose()
            
            # Suche nach Content-Containern
            content_selectors = [
                'main',
                'article', 
                'div.content',
                'div.main-content',
                'div.gutachten-content',
                'div.container'
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
                text = content_element.get_text(separator=' ', strip=True)
                text = re.sub(r'\\s+', ' ', text)
                return text.strip()
            
        except Exception as e:
            self.logger.error(f"Fehler beim Extrahieren des Contents: {e}")
        
        return ""
    
    def add_to_vectordb(self, gutachten_list: List[Dict]) -> bool:
        """
        Fügt neue Gutachten zur ChromaDB hinzu
        
        Args:
            gutachten_list: Liste der Gutachten
            
        Returns:
            True wenn erfolgreich
        """
        try:
            if not gutachten_list:
                self.logger.info("Keine Gutachten zum Hinzufügen")
                return True
            
            # Bereite Daten vor
            documents = []
            metadatas = []
            ids = []
            
            for gutachten in gutachten_list:
                if 'content' not in gutachten or not gutachten['content']:
                    self.logger.warning(f"Kein Content für Gutachten {gutachten.get('title', 'unknown')}")
                    continue
                
                documents.append(gutachten['content'])
                
                # Metadata ohne Content
                metadata = {k: v for k, v in gutachten.items() if k != 'content'}
                metadatas.append(metadata)
                
                ids.append(gutachten.get('node_id', str(uuid.uuid4())))
            
            if not documents:
                self.logger.warning("Keine gültigen Dokumente zum Hinzufügen")
                return False
            
            # Verwende ChromaDBClient.add_documents Methode
            success = self.chroma_client.add_documents(
                collection_name=self.config.COLLECTION_NAME,
                documents=documents,
                metadatas=metadatas,
                ids=ids
            )
            
            if success:
                self.logger.info(f"Erfolgreich {len(documents)} Gutachten zur ChromaDB hinzugefügt")
            else:
                self.logger.error("Fehler beim Hinzufügen zur ChromaDB")
            
            return success
            
        except Exception as e:
            self.logger.error(f"Fehler beim Hinzufügen zur ChromaDB: {e}")
            return False
    
    def run_full_update_cycle(self) -> Dict:
        """
        Führt einen vollständigen Update-Zyklus durch
        
        Returns:
            Update-Statistiken
        """
        start_time = time.time()
        stats = {
            'started_at': datetime.now().isoformat(),
            'gutachten_found': 0,
            'gutachten_processed': 0,
            'gutachten_added': 0,
            'errors': 0,
            'duration_seconds': 0
        }
        
        try:
            self.logger.info("=== DNOTI Production Auto-Update gestartet ===")
            
            # 1. Suche nach Gutachten
            gutachten_metadata = self.search_for_new_gutachten()
            stats['gutachten_found'] = len(gutachten_metadata)
            
            if not gutachten_metadata:
                self.logger.info("Keine neuen Gutachten gefunden")
                stats['duration_seconds'] = time.time() - start_time
                return stats
            
            # 2. Verarbeite Batch der neuesten Gutachten
            batch = gutachten_metadata[:self.config.BATCH_SIZE]
            self.logger.info(f"Verarbeite {len(batch)} Gutachten...")
            
            processed_gutachten = []
            
            for gutachten in batch:
                full_gutachten = self.fetch_gutachten_content(gutachten)
                
                if full_gutachten:
                    processed_gutachten.append(full_gutachten)
                    stats['gutachten_processed'] += 1
                else:
                    stats['errors'] += 1
                
                time.sleep(self.config.REQUEST_DELAY_SECONDS)
            
            # 3. Zur ChromaDB hinzufügen
            if processed_gutachten:
                if self.add_to_vectordb(processed_gutachten):
                    stats['gutachten_added'] = len(processed_gutachten)
                else:
                    stats['errors'] += 1
            
            stats['duration_seconds'] = time.time() - start_time
            
            self.logger.info(f"=== Production Update abgeschlossen: {stats} ===")
            
        except Exception as e:
            self.logger.error(f"Fehler im Production Update-Zyklus: {e}")
            stats['errors'] += 1
            stats['duration_seconds'] = time.time() - start_time
        
        return stats

# ========== HAUPTFUNKTION ==========

def main():
    """Hauptfunktion für den produktionsreifen Auto-Updater"""
    try:
        print("DNOTI Auto-Updater - Production Version")
        print("=" * 45)
        
        # Initialisiere produktionsreifen Auto-Updater
        config = DNOTIConfig()
        updater = DNOTIAutoUpdaterProduction(config)
        
        # Führe vollständigen Update-Zyklus durch
        stats = updater.run_full_update_cycle()
        
        print("\\nProduction Update-Statistiken:")
        for key, value in stats.items():
            print(f"  {key}: {value}")
        
        # Status-Bewertung
        if stats['gutachten_added'] > 0:
            print("\\n✅ Update erfolgreich - Neue Gutachten hinzugefügt!")
        elif stats['gutachten_found'] > 0:
            print("\\n⚠️  Gutachten gefunden, aber nicht hinzugefügt - prüfe Logs")
        else:
            print("\\n ℹ️  Keine neuen Gutachten gefunden")
        
        print("\\nProduction Update abgeschlossen!")
        
        return 0 if stats['errors'] == 0 else 1
        
    except Exception as e:
        print(f"Kritischer Fehler: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())
