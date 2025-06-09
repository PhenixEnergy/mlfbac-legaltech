#!/usr/bin/env python3
"""
DNOTI Auto-Update Service - Enhanced Debug Version
Erweiterte Suchfunktionen und detailliertes Debugging

Entwickelt für robuste Erkennung von DNOTI Gutachten
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

@dataclass
class DNOTIConfig:
    """Erweiterte Konfiguration für DNOTI Auto-Update mit Debug-Features"""
    
    # DNOTI Website-Konfiguration
    BASE_URL: str = "https://www.dnoti.de"
    GUTACHTEN_SEARCH_URL: str = "https://www.dnoti.de/gutachten/"
    
    # Formular-Parameter für TYPO3
    FORM_FIELD_PREFIX: str = "tx_dnotionlineplusapi_expertises"
    
    # Erweiterte Suchstrategien
    SEARCH_STRATEGIES: List[str] = None
    CHECK_INTERVAL_HOURS: int = 6
    BATCH_SIZE: int = 5
    MAX_PAGES_PER_RUN: int = 15
    
    # Request-Konfiguration
    REQUEST_TIMEOUT: int = 30
    REQUEST_DELAY_SECONDS: float = 1.5
    MAX_RETRIES: int = 3
    
    # ChromaDB-Konfiguration  
    COLLECTION_NAME: str = "dnoti_gutachten"
    
    # Debug-Konfiguration
    SAVE_DEBUG_HTML: bool = True
    DEBUG_DIR: str = "debug_output"
    
    # Logging
    LOG_FILE: str = "logs/dnoti_auto_update_enhanced.log"
    LOG_LEVEL: str = "INFO"
    
    def __post_init__(self):
        if self.SEARCH_STRATEGIES is None:
            self.SEARCH_STRATEGIES = [
                "all_recent",           # Alle ohne Filterung
                "by_year_range",        # Nach Jahresbereich
                "by_text_search",       # Mit Textsuche
                "by_expertise_ref"      # Nach Gutachten-Referenz
            ]

class DNOTIAutoUpdaterEnhanced:
    """Erweiterte Version des DNOTI Auto-Updaters mit verbesserter Suchlogik"""
    
    def __init__(self, config: DNOTIConfig = None):
        self.config = config or DNOTIConfig()
        self.session = requests.Session()
        self.chroma_client = None
        
        # Setup User-Agent für bessere Website-Kompatibilität
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
            'Accept-Language': 'de-DE,de;q=0.9,en;q=0.8',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'none',
            'Cache-Control': 'max-age=0'
        })
        
        # Setup Debug-Verzeichnis
        Path(self.config.DEBUG_DIR).mkdir(exist_ok=True)
        
        # Setup Logging
        self._setup_logging()
        
        # Initialisiere ChromaDB
        self._initialize_chromadb()
    
    def _setup_logging(self):
        """Konfiguriert erweitertes Logging"""
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
        self.logger.info("DNOTI Enhanced Auto-Updater initialisiert")
    
    def _initialize_chromadb(self):
        """Initialisiert ChromaDB-Verbindung"""
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
    
    def comprehensive_search(self) -> List[Dict]:
        """
        Führt eine umfassende Suche mit mehreren Strategien durch
        
        Returns:
            Liste von gefundenen Gutachten
        """
        all_gutachten = []
        
        try:
            self.logger.info("Starte umfassende Gutachten-Suche...")
            
            for strategy in self.config.SEARCH_STRATEGIES:
                self.logger.info(f"Verwende Suchstrategie: {strategy}")
                
                strategy_results = []
                
                if strategy == "all_recent":
                    strategy_results = self._search_all_recent()
                elif strategy == "by_year_range":
                    strategy_results = self._search_by_year_range()
                elif strategy == "by_text_search":
                    strategy_results = self._search_by_text()
                elif strategy == "by_expertise_ref":
                    strategy_results = self._search_by_expertise_ref()
                
                self.logger.info(f"Strategie '{strategy}': {len(strategy_results)} Gutachten gefunden")
                all_gutachten.extend(strategy_results)
                
                time.sleep(self.config.REQUEST_DELAY_SECONDS)
            
            # Dedupliziere basierend auf URL oder Node-ID
            unique_gutachten = self._deduplicate_gutachten(all_gutachten)
            
            self.logger.info(f"Gesamt gefunden: {len(all_gutachten)}, eindeutig: {len(unique_gutachten)}")
            return unique_gutachten
            
        except Exception as e:
            self.logger.error(f"Fehler bei umfassender Suche: {e}")
            return []
    
    def _search_all_recent(self) -> List[Dict]:
        """Sucht nach allen aktuellen Gutachten ohne Filterung"""
        return self._perform_search({
            f"{self.config.FORM_FIELD_PREFIX}[expertisesType]": "all",
            f"{self.config.FORM_FIELD_PREFIX}[searchTitle]": "",
            f"{self.config.FORM_FIELD_PREFIX}[searchText]": "",
        }, "all_recent")
    
    def _search_by_year_range(self) -> List[Dict]:
        """Sucht nach Gutachten der letzten 2 Jahre"""
        gutachten_list = []
        current_year = datetime.now().year
        
        for year in [current_year, current_year - 1]:
            year_results = self._perform_search({
                f"{self.config.FORM_FIELD_PREFIX}[expertisesType]": "dnotiReport",
                f"{self.config.FORM_FIELD_PREFIX}[reportYear]": str(year),
            }, f"year_{year}")
            
            gutachten_list.extend(year_results)
            time.sleep(self.config.REQUEST_DELAY_SECONDS)
        
        return gutachten_list
    
    def _search_by_text(self) -> List[Dict]:
        """Sucht nach Gutachten mit allgemeinen Rechtsbegriffen"""
        search_terms = [
            "Notar",
            "Beurkundung", 
            "Immobilie",
            "Gesellschaft",
            "Testament"
        ]
        
        gutachten_list = []
        
        for term in search_terms[:2]:  # Limitiere auf erste 2 Begriffe
            term_results = self._perform_search({
                f"{self.config.FORM_FIELD_PREFIX}[expertisesType]": "all",
                f"{self.config.FORM_FIELD_PREFIX}[searchText]": term,
            }, f"text_{term}")
            
            gutachten_list.extend(term_results)
            time.sleep(self.config.REQUEST_DELAY_SECONDS)
        
        return gutachten_list
    
    def _search_by_expertise_ref(self) -> List[Dict]:
        """Versucht Suche nach Gutachten-Referenzen"""
        # Da wir keine konkreten Referenzen haben, teste mit allgemeinen Mustern
        ref_patterns = ["2024", "2025"]
        
        gutachten_list = []
        
        for pattern in ref_patterns:
            ref_results = self._perform_search({
                f"{self.config.FORM_FIELD_PREFIX}[expertisesType]": "expertiseReference",
                f"{self.config.FORM_FIELD_PREFIX}[expertiseReference]": pattern,
            }, f"ref_{pattern}")
            
            gutachten_list.extend(ref_results)
            time.sleep(self.config.REQUEST_DELAY_SECONDS)
        
        return gutachten_list
    
    def _perform_search(self, base_params: Dict, search_type: str) -> List[Dict]:
        """
        Führt eine spezifische Suche durch
        
        Args:
            base_params: Basis-Suchparameter
            search_type: Typ der Suche für Debugging
            
        Returns:
            Liste von gefundenen Gutachten
        """
        gutachten_list = []
        
        try:
            page = 1
            max_pages = self.config.MAX_PAGES_PER_RUN
            
            while page <= max_pages:
                # Erstelle vollständige Form-Daten
                form_data = {
                    f"{self.config.FORM_FIELD_PREFIX}[page]": str(page),
                    **base_params
                }
                
                # Füge Standard-Parameter hinzu falls nicht gesetzt
                if f"{self.config.FORM_FIELD_PREFIX}[searchTitle]" not in form_data:
                    form_data[f"{self.config.FORM_FIELD_PREFIX}[searchTitle]"] = ""
                if f"{self.config.FORM_FIELD_PREFIX}[searchText]" not in form_data:
                    form_data[f"{self.config.FORM_FIELD_PREFIX}[searchText]"] = ""
                
                self.logger.debug(f"Suche {search_type}, Seite {page} mit Parametern: {form_data}")
                
                # Sende POST-Request
                response = self.session.post(
                    self.config.GUTACHTEN_SEARCH_URL,
                    data=form_data,
                    timeout=self.config.REQUEST_TIMEOUT
                )
                
                if response.status_code != 200:
                    self.logger.warning(f"HTTP {response.status_code} für {search_type}, Seite {page}")
                    break
                
                # Debug: Speichere HTML-Response
                if self.config.SAVE_DEBUG_HTML:
                    self._save_debug_html(response.text, f"{search_type}_page_{page}")
                
                # Parse Ergebnisse
                page_gutachten = self._parse_search_results_enhanced(response.text, search_type, page)
                
                if not page_gutachten:
                    self.logger.info(f"{search_type}, Seite {page}: Keine Ergebnisse gefunden")
                    break
                
                gutachten_list.extend(page_gutachten)
                self.logger.info(f"{search_type}, Seite {page}: {len(page_gutachten)} Gutachten gefunden")
                
                page += 1
                time.sleep(self.config.REQUEST_DELAY_SECONDS)
                
                # Stoppe wenn zu viele Seiten ohne neue Ergebnisse
                if page > 3 and len(page_gutachten) == 0:
                    break
            
        except Exception as e:
            self.logger.error(f"Fehler bei Suche {search_type}: {e}")
        
        return gutachten_list
    
    def _save_debug_html(self, html_content: str, filename_prefix: str):
        """Speichert HTML-Content für Debugging"""
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"{filename_prefix}_{timestamp}.html"
            filepath = Path(self.config.DEBUG_DIR) / filename
            
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(html_content)
            
            self.logger.debug(f"Debug HTML gespeichert: {filepath}")
            
        except Exception as e:
            self.logger.debug(f"Fehler beim Speichern von Debug HTML: {e}")
    
    def _parse_search_results_enhanced(self, html_content: str, search_type: str, page: int) -> List[Dict]:
        """Erweiterte Parsing-Logik für Suchergebnisse"""
        gutachten_list = []
        
        try:
            soup = BeautifulSoup(html_content, 'html.parser')
            
            # Mehrstufiges Parsing
            
            # 1. Suche nach direkten Gutachten-Detail-Links
            detail_links = self._find_detail_links(soup)
            if detail_links:
                self.logger.info(f"Gefunden {len(detail_links)} Detail-Links via direkter Suche")
                gutachten_list.extend(detail_links)
            
            # 2. Suche nach Ergebnis-Containern
            result_containers = self._find_result_containers(soup)
            if result_containers:
                self.logger.info(f"Gefunden {len(result_containers)} Ergebnis-Container")
                gutachten_list.extend(result_containers)
            
            # 3. Suche nach allgemeinen Links mit "gutachten"
            general_links = self._find_general_gutachten_links(soup)
            if general_links:
                self.logger.info(f"Gefunden {len(general_links)} allgemeine Gutachten-Links")
                gutachten_list.extend(general_links)
            
            # 4. Analysiere Seitenstruktur für besseres Debugging
            self._analyze_page_structure(soup, search_type, page)
            
        except Exception as e:
            self.logger.error(f"Fehler beim erweiterten Parsing: {e}")
        
        return gutachten_list
    
    def _find_detail_links(self, soup: BeautifulSoup) -> List[Dict]:
        """Findet direkte Gutachten-Detail-Links"""
        gutachten_list = []
        
        # Regex für Detail-URLs
        detail_pattern = re.compile(r'/gutachten/details/\?tx_dnotionlineplusapi_expertises%5Bnodeid%5D=([a-f0-9-]+)&cHash=([a-f0-9]+)')
        
        for link in soup.find_all('a', href=True):
            href = link.get('href', '')
            match = detail_pattern.search(href)
            
            if match:
                node_id = match.group(1)
                c_hash = match.group(2)
                full_url = urljoin(self.config.BASE_URL, href)
                title = link.get_text(strip=True) or f"Gutachten {node_id[:8]}"
                
                gutachten_info = {
                    'url': full_url,
                    'node_id': node_id,
                    'c_hash': c_hash,
                    'title': title,
                    'found_date': datetime.now().isoformat(),
                    'source': 'detail_link'
                }
                
                gutachten_list.append(gutachten_info)
        
        return gutachten_list
    
    def _find_result_containers(self, soup: BeautifulSoup) -> List[Dict]:
        """Findet Gutachten in Ergebnis-Containern"""
        gutachten_list = []
        
        # Suche nach typischen Ergebnis-Container-Selektoren
        container_selectors = [
            'div[class*="result"]',
            'div[class*="gutachten"]', 
            'div[class*="expertise"]',
            'div[class*="item"]',
            'article',
            'li[class*="result"]'
        ]
        
        for selector in container_selectors:
            containers = soup.select(selector)
            
            for container in containers:
                # Suche nach Links innerhalb des Containers
                links = container.find_all('a', href=True)
                
                for link in links:
                    href = link.get('href', '')
                    if 'gutachten' in href.lower() or 'expertise' in href.lower():
                        full_url = urljoin(self.config.BASE_URL, href)
                        title = link.get_text(strip=True) or container.get_text(strip=True)[:100]
                        
                        gutachten_info = {
                            'url': full_url,
                            'node_id': f"container_{hash(href)%100000}",
                            'c_hash': '',
                            'title': title,
                            'found_date': datetime.now().isoformat(),
                            'source': f'container_{selector}'
                        }
                        
                        gutachten_list.append(gutachten_info)
        
        return gutachten_list
    
    def _find_general_gutachten_links(self, soup: BeautifulSoup) -> List[Dict]:
        """Findet allgemeine Links die zu Gutachten führen könnten"""
        gutachten_list = []
        
        for link in soup.find_all('a', href=True):
            href = link.get('href', '')
            text = link.get_text(strip=True).lower()
            
            # Filter für wahrscheinliche Gutachten-Links
            if any(keyword in href.lower() for keyword in ['gutachten', 'expertise']) or \
               any(keyword in text for keyword in ['gutachten', 'expertise', 'dnoti']):
                
                full_url = urljoin(self.config.BASE_URL, href)
                title = link.get_text(strip=True) or "Unbekanntes Gutachten"
                
                gutachten_info = {
                    'url': full_url,
                    'node_id': f"general_{hash(href)%100000}",
                    'c_hash': '',
                    'title': title,
                    'found_date': datetime.now().isoformat(),
                    'source': 'general_link'
                }
                
                gutachten_list.append(gutachten_info)
        
        return gutachten_list
    
    def _analyze_page_structure(self, soup: BeautifulSoup, search_type: str, page: int):
        """Analysiert die Seitenstruktur für besseres Debugging"""
        try:
            # Zähle verschiedene Elemente
            total_links = len(soup.find_all('a', href=True))
            total_forms = len(soup.find_all('form'))
            total_divs = len(soup.find_all('div'))
            
            # Suche nach Paginierung oder "keine Ergebnisse" Hinweisen
            no_results_indicators = soup.find_all(string=re.compile(r'keine.*(ergebnis|treffer|gutachten)', re.I))
            pagination_links = soup.find_all('a', string=re.compile(r'(weiter|nächste|next|>)', re.I))
            
            self.logger.debug(f"Seitenanalyse {search_type} Seite {page}: "
                            f"{total_links} Links, {total_forms} Formulare, {total_divs} Divs, "
                            f"{len(no_results_indicators)} 'Keine Ergebnisse' Hinweise, "
                            f"{len(pagination_links)} Paginierungs-Links")
            
            # Wenn keine Ergebnisse gefunden, logge relevante Textpassagen
            if no_results_indicators:
                for indicator in no_results_indicators[:3]:
                    self.logger.debug(f"'Keine Ergebnisse' Text: {indicator.strip()}")
                    
        except Exception as e:
            self.logger.debug(f"Fehler bei Seitenstruktur-Analyse: {e}")
    
    def _deduplicate_gutachten(self, gutachten_list: List[Dict]) -> List[Dict]:
        """Entfernt Duplikate basierend auf URL oder Node-ID"""
        seen_urls = set()
        seen_node_ids = set()
        unique_gutachten = []
        
        for gutachten in gutachten_list:
            url = gutachten.get('url', '')
            node_id = gutachten.get('node_id', '')
            
            if url not in seen_urls and node_id not in seen_node_ids:
                seen_urls.add(url)
                seen_node_ids.add(node_id)
                unique_gutachten.append(gutachten)
        
        return unique_gutachten
    
    def run_enhanced_update_cycle(self) -> Dict:
        """
        Führt einen erweiterten Update-Zyklus durch
        
        Returns:
            Detaillierte Statistiken des Update-Zyklus
        """
        start_time = time.time()
        stats = {
            'started_at': datetime.now().isoformat(),
            'strategies_used': len(self.config.SEARCH_STRATEGIES),
            'gutachten_found': 0,
            'gutachten_fetched': 0,
            'gutachten_added': 0,
            'errors': 0,
            'duration_seconds': 0,
            'debug_files_created': 0
        }
        
        try:
            self.logger.info("=== DNOTI Enhanced Auto-Update Zyklus gestartet ===")
            
            # 1. Umfassende Suche nach Gutachten
            gutachten_metadata = self.comprehensive_search()
            stats['gutachten_found'] = len(gutachten_metadata)
            
            if not gutachten_metadata:
                self.logger.info("Keine Gutachten gefunden - möglicherweise sind andere Suchstrategien erforderlich")
                # Hier könnten wir weitere Debug-Informationen sammeln
                return stats
            
            self.logger.info(f"Gefunden {len(gutachten_metadata)} potentielle Gutachten")
            
            # 2. Lade erste Batch für Tests
            test_batch = gutachten_metadata[:self.config.BATCH_SIZE]
            
            for metadata in test_batch:
                self.logger.info(f"Teste Gutachten-Link: {metadata['url']}")
                # Hier würde der Content-Fetch stattfinden
                time.sleep(self.config.REQUEST_DELAY_SECONDS)
            
            stats['duration_seconds'] = time.time() - start_time
            
            self.logger.info(f"=== Enhanced Update-Zyklus abgeschlossen: {stats} ===")
            
        except Exception as e:
            self.logger.error(f"Fehler im Enhanced Update-Zyklus: {e}")
            stats['errors'] += 1
            stats['duration_seconds'] = time.time() - start_time
        
        return stats

def main():
    """Hauptfunktion zum Testen des erweiterten Auto-Updaters"""
    try:
        print("DNOTI Auto-Updater - Enhanced Debug Version")
        print("=" * 55)
        
        # Initialisiere erweiterten Auto-Updater
        config = DNOTIConfig()
        updater = DNOTIAutoUpdaterEnhanced(config)
        
        # Führe erweiterten Update-Zyklus durch
        stats = updater.run_enhanced_update_cycle()
        
        print("\nErweiterte Update-Statistiken:")
        for key, value in stats.items():
            print(f"  {key}: {value}")
        
        print(f"\nDebug-Dateien gespeichert in: {config.DEBUG_DIR}")
        print("Enhanced Update-Zyklus abgeschlossen!")
        
    except Exception as e:
        print(f"Fehler: {e}")
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
