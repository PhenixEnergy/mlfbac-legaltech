#!/usr/bin/env python3
"""
DNOTI Production Auto-Updater v6.0
===================================
Production-ready version with enhanced discovery, monitoring, and integration
"""

import requests
from bs4 import BeautifulSoup
import re
import json
from datetime import datetime, timedelta
import time
import logging
from pathlib import Path
from typing import List, Dict, Optional, Set, Tuple
from dataclasses import dataclass, field
import uuid
import os
import random

# Import der bestehenden ChromaDB Komponenten
from src.vectordb.chroma_client import ChromaDBClient

@dataclass
class DNOTIProductionConfig:
    """Production-Konfiguration für DNOTI Auto-Updater"""
    
    # URLs
    BASE_URL: str = "https://www.dnoti.de"
    GUTACHTEN_SEARCH_URL: str = "https://www.dnoti.de/gutachten/"
    
    # Request-Konfiguration
    REQUEST_TIMEOUT: int = 30
    REQUEST_DELAY_SECONDS: float = 2.0
    MAX_RETRIES: int = 3
    USER_AGENTS: List[str] = field(default_factory=lambda: [
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:89.0) Gecko/20100101 Firefox/89.0',
        'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    ])
    
    # ChromaDB-Konfiguration  
    COLLECTION_NAME: str = "dnoti_gutachten"
    
    # Logging-Konfiguration
    LOG_LEVEL: str = "INFO"
    LOG_DIR: str = "logs"
    
    # Production-Strategien
    STRATEGIES: List[str] = field(default_factory=lambda: [
        "search_monitor",        # Monitor DNOTI search availability
        "enhanced_discovery",    # Enhanced URL pattern discovery
        "systematic_scan",       # Systematic scanning approach
        "database_maintenance"   # Database maintenance and validation
    ])
    
    # Discovery-Konfiguration
    KNOWN_GUTACHTEN_FILE: str = "Database/Original/dnoti_all.json"
    MAX_DISCOVERY_ATTEMPTS: int = 100
    DISCOVERY_YEARS: List[int] = field(default_factory=lambda: [2024, 2025])
    
    # Production-Einstellungen
    ENABLE_DATABASE_UPDATES: bool = True
    DRY_RUN_MODE: bool = False
    MAX_NEW_DOCUMENTS_PER_RUN: int = 10
    
    # Monitoring
    SEARCH_HEALTH_CHECK_INTERVAL: int = 300  # 5 Minuten
    LAST_SUCCESSFUL_SEARCH_FILE: str = "logs/last_successful_search.json"
    
    def __post_init__(self):
        # Erstelle Log-Verzeichnis
        Path(self.LOG_DIR).mkdir(exist_ok=True)


class DNOTIProductionUpdater:
    """Production DNOTI Auto-Updater mit erweiterten Funktionen"""
    
    def __init__(self, config: DNOTIProductionConfig):
        self.config = config
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': random.choice(config.USER_AGENTS)
        })
        
        self.stats = {
            'strategies_attempted': 0,
            'strategies_successful': 0,
            'gutachten_found': 0,
            'gutachten_new': 0,
            'gutachten_updated': 0,
            'gutachten_validated': 0,
            'errors': 0,
            'search_health_status': 'unknown'
        }
        
        self.found_gutachten: List[Dict] = []
        self.known_urls: Set[str] = set()
        self.known_node_ids: Set[str] = set()
        
        # Setup Logging
        self.setup_logging()
        
        # Initialize ChromaDB
        self.chroma_client = None
        self.collection = None
        
    def setup_logging(self):
        """Setup production logging"""
        log_file = Path(self.config.LOG_DIR) / f"dnoti_production_v6_{datetime.now().strftime('%Y%m%d')}.log"
        
        # Create formatters
        file_formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(funcName)s:%(lineno)d - %(message)s'
        )
        console_formatter = logging.Formatter(
            '%(levelname)s - %(message)s'
        )
        
        # Setup logger
        self.logger = logging.getLogger('DNOTIProductionV6')
        self.logger.setLevel(getattr(logging, self.config.LOG_LEVEL))
        
        # Clear existing handlers
        for handler in self.logger.handlers[:]:
            self.logger.removeHandler(handler)
        
        # File handler
        file_handler = logging.FileHandler(log_file, encoding='utf-8')
        file_handler.setFormatter(file_formatter)
        self.logger.addHandler(file_handler)
        
        # Console handler
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(console_formatter)
        self.logger.addHandler(console_handler)
    
    def initialize_chroma(self):
        """Initialisiere ChromaDB-Verbindung"""
        try:
            self.logger.info("Initialisiere ChromaDB-Verbindung...")
            self.chroma_client = ChromaDBClient()
            self.collection = self.chroma_client.create_collection(
                collection_name=self.config.COLLECTION_NAME,
                reset_if_exists=False
            )
            self.logger.info(f"ChromaDB Collection '{self.config.COLLECTION_NAME}' bereit")
            return True
            
        except Exception as e:
            self.logger.error(f"ChromaDB-Initialisierung fehlgeschlagen: {e}")
            return False
    
    def load_known_gutachten(self) -> bool:
        """Lade bekannte Gutachten aus bestehender Datenbank"""
        try:
            json_file = Path(self.config.KNOWN_GUTACHTEN_FILE)
            if not json_file.exists():
                self.logger.warning(f"Bekannte Gutachten-Datei nicht gefunden: {json_file}")
                return False
            
            with open(json_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            for item in data:
                if 'url' in item:
                    self.known_urls.add(item['url'])
                    # Extrahiere Node-ID
                    node_match = re.search(r'nodeid.*?([a-f0-9\-]{36})', item['url'], re.IGNORECASE)
                    if node_match:
                        self.known_node_ids.add(node_match.group(1))
            
            self.logger.info(f"Geladen: {len(self.known_urls)} bekannte URLs, {len(self.known_node_ids)} Node-IDs")
            return True
            
        except Exception as e:
            self.logger.error(f"Fehler beim Laden bekannter Gutachten: {e}")
            return False
    
    def run_production_cycle(self):
        """Führe Production-Update-Zyklus aus"""
        start_time = time.time()
        
        self.logger.info("=== DNOTI Production Auto-Update Zyklus gestartet ===")
        self.logger.info(f"Strategien: {', '.join(self.config.STRATEGIES)}")
        self.logger.info(f"Dry-Run Modus: {self.config.DRY_RUN_MODE}")
        
        # Initialize components
        if not self.initialize_chroma():
            self.logger.error("ChromaDB-Initialisierung fehlgeschlagen - Abbruch")
            return False
        
        if not self.load_known_gutachten():
            self.logger.warning("Konnte bekannte Gutachten nicht laden - fahre fort")
        
        # Execute strategies
        for strategy in self.config.STRATEGIES:
            self.logger.info(f"Führe Strategie aus: {strategy}")
            self.stats['strategies_attempted'] += 1
            
            try:
                if strategy == "search_monitor":
                    success = self.strategy_search_monitor()
                elif strategy == "enhanced_discovery":
                    success = self.strategy_enhanced_discovery()
                elif strategy == "systematic_scan":
                    success = self.strategy_systematic_scan()
                elif strategy == "database_maintenance":
                    success = self.strategy_database_maintenance()
                else:
                    self.logger.warning(f"Unbekannte Strategie: {strategy}")
                    continue
                
                if success:
                    self.stats['strategies_successful'] += 1
                    self.logger.info(f"Strategie {strategy} erfolgreich")
                else:
                    self.logger.warning(f"Strategie {strategy} nicht erfolgreich")
                
            except Exception as e:
                self.logger.error(f"Fehler in Strategie {strategy}: {e}")
                self.stats['errors'] += 1
            
            # Pause zwischen Strategien
            time.sleep(self.config.REQUEST_DELAY_SECONDS)
        
        # Process found Gutachten
        if self.found_gutachten:
            self.process_found_gutachten()
        
        # Statistiken
        duration = time.time() - start_time
        self.log_final_stats(duration)
        
        return len(self.found_gutachten) > 0
    
    def strategy_search_monitor(self) -> bool:
        """Strategie 1: Monitor DNOTI search health"""
        self.logger.info("Überwache DNOTI-Suchfunktionalität...")
        
        try:
            # Test basic search functionality
            test_params = {
                'tx_dnotionlineplusapi_expertises[page]': '1',
                'tx_dnotionlineplusapi_expertises[expertisesType]': '',
                'tx_dnotionlineplusapi_expertises[searchTitle]': '',
                'tx_dnotionlineplusapi_expertises[searchText]': 'BGB',
            }
            
            response = self.session.post(
                self.config.GUTACHTEN_SEARCH_URL,
                data=test_params,
                timeout=self.config.REQUEST_TIMEOUT
            )
            
            if response.status_code == 200:
                soup = BeautifulSoup(response.content, 'html.parser')
                nodeid_links = soup.find_all('a', href=re.compile(r'nodeid'))
                
                if len(nodeid_links) > 0:
                    self.stats['search_health_status'] = 'healthy'
                    self.logger.info(f"✅ DNOTI-Suche funktioniert! {len(nodeid_links)} Ergebnisse gefunden")
                    self.save_search_health_status(True)
                    
                    # Process found links
                    for link in nodeid_links[:5]:  # Begrenzt für Monitoring
                        gutachten_info = self.extract_gutachten_from_link(link)
                        if gutachten_info and gutachten_info['url'] not in self.known_urls:
                            self.found_gutachten.append(gutachten_info)
                    
                    return True
                else:
                    self.stats['search_health_status'] = 'empty_results'
                    self.logger.warning("⚠️ DNOTI-Suche antwortet, aber liefert keine Ergebnisse")
                    self.save_search_health_status(False)
                    return False
            else:
                self.stats['search_health_status'] = 'unreachable'
                self.logger.error(f"❌ DNOTI-Suche nicht erreichbar (Status: {response.status_code})")
                self.save_search_health_status(False)
                return False
                
        except Exception as e:
            self.stats['search_health_status'] = 'error'
            self.logger.error(f"❌ DNOTI-Suche-Monitor Fehler: {e}")
            self.save_search_health_status(False)
            return False
    
    def strategy_enhanced_discovery(self) -> bool:
        """Strategie 2: Enhanced URL pattern discovery"""
        self.logger.info("Starte erweiterte URL-Pattern-Discovery...")
        
        if not self.known_node_ids:
            self.logger.warning("Keine bekannten Node-IDs für Discovery verfügbar")
            return False
        
        try:
            discovery_count = 0
            max_attempts = min(self.config.MAX_DISCOVERY_ATTEMPTS, 20)
            
            # Strategy A: Test variations of known Node-IDs
            for node_id in list(self.known_node_ids)[:10]:
                if discovery_count >= max_attempts:
                    break
                
                # Try different cHash values
                for cHash_variant in ['test', 'preview', 'main', 'default']:
                    test_url = (f"{self.config.BASE_URL}/gutachten/details/"
                              f"?tx_dnotionlineplusapi_expertises%5Bnodeid%5D={node_id}"
                              f"&cHash={cHash_variant}")
                    
                    if self.test_url_for_content(test_url, node_id):
                        discovery_count += 1
                        break
                    
                    time.sleep(self.config.REQUEST_DELAY_SECONDS * 0.3)
            
            # Strategy B: Generate systematic Node-ID variations
            if discovery_count == 0:
                discovery_count += self.generate_systematic_node_ids()
            
            self.logger.info(f"Enhanced Discovery: {discovery_count} neue Gutachten gefunden")
            return discovery_count > 0
            
        except Exception as e:
            self.logger.error(f"Enhanced Discovery fehlgeschlagen: {e}")
            return False
    
    def strategy_systematic_scan(self) -> bool:
        """Strategie 3: Systematic scanning approach"""
        self.logger.info("Starte systematischen Scan...")
        
        try:
            scan_results = 0
            
            # Scan approach 1: Check recent patterns
            for year in self.config.DISCOVERY_YEARS:
                for month in range(1, 13):
                    if scan_results >= 5:  # Limit für Production
                        break
                    
                    # Simulate potential patterns based on date
                    potential_patterns = self.generate_date_based_patterns(year, month)
                    
                    for pattern in potential_patterns[:3]:  # Test nur wenige
                        test_url = f"{self.config.BASE_URL}/gutachten/details/?{pattern}"
                        
                        try:
                            response = self.session.get(test_url, timeout=self.config.REQUEST_TIMEOUT)
                            if response.status_code == 200 and len(response.content) > 5000:
                                # Potential valid Gutachten
                                gutachten_info = self.extract_gutachten_info_from_response(response, test_url)
                                if gutachten_info and gutachten_info['url'] not in self.known_urls:
                                    self.found_gutachten.append(gutachten_info)
                                    scan_results += 1
                                    self.logger.info(f"Systematic Scan: Gutachten gefunden")
                        
                        except Exception as e:
                            self.logger.debug(f"Scan-Test fehlgeschlagen: {e}")
                        
                        time.sleep(self.config.REQUEST_DELAY_SECONDS)
                    
                    if scan_results >= 5:
                        break
            
            self.logger.info(f"Systematic Scan: {scan_results} neue Gutachten gefunden")
            return scan_results > 0
            
        except Exception as e:
            self.logger.error(f"Systematic Scan fehlgeschlagen: {e}")
            return False
    
    def strategy_database_maintenance(self) -> bool:
        """Strategie 4: Database maintenance and validation"""
        self.logger.info("Starte Database-Maintenance...")
        
        try:
            validation_count = 0
            invalid_urls = []
            
            # Teste Stichprobe der bekannten URLs
            sample_size = min(20, len(self.known_urls))
            sample_urls = random.sample(list(self.known_urls), sample_size)
            
            for url in sample_urls:
                try:
                    response = self.session.get(url, timeout=self.config.REQUEST_TIMEOUT)
                    
                    if response.status_code == 200:
                        if len(response.content) > 5000:  # Mindestgröße für gültiges Gutachten
                            validation_count += 1
                            self.stats['gutachten_validated'] += 1
                        else:
                            invalid_urls.append(url)
                    else:
                        invalid_urls.append(url)
                    
                except Exception as e:
                    self.logger.debug(f"Validation-Fehler für {url}: {e}")
                    invalid_urls.append(url)
                
                time.sleep(self.config.REQUEST_DELAY_SECONDS * 0.5)
            
            # Log invalid URLs for potential cleanup
            if invalid_urls:
                self.logger.warning(f"Gefunden: {len(invalid_urls)} möglicherweise ungültige URLs")
                for url in invalid_urls[:5]:  # Log nur wenige
                    self.logger.debug(f"Ungültige URL: {url}")
            
            self.logger.info(f"Database-Maintenance: {validation_count}/{sample_size} URLs validiert")
            return True
            
        except Exception as e:
            self.logger.error(f"Database-Maintenance fehlgeschlagen: {e}")
            return False
    
    def test_url_for_content(self, url: str, node_id: str) -> bool:
        """Teste URL auf gültigen Gutachten-Inhalt"""
        try:
            response = self.session.get(url, timeout=self.config.REQUEST_TIMEOUT)
            
            if response.status_code == 200 and len(response.content) > 5000:
                soup = BeautifulSoup(response.content, 'html.parser')
                title_elem = soup.find('title')
                
                if title_elem and 'gutachten' in title_elem.get_text().lower():
                    gutachten_info = {
                        'url': url,
                        'node_id': node_id,
                        'title': title_elem.get_text().strip(),
                        'discovery_method': 'enhanced_pattern',
                        'found_at': datetime.now().isoformat()
                    }
                    
                    if url not in self.known_urls:
                        self.found_gutachten.append(gutachten_info)
                        self.logger.info(f"Enhanced Discovery: Neues Gutachten gefunden - {node_id}")
                        return True
            
            return False
            
        except Exception as e:
            self.logger.debug(f"URL-Test fehlgeschlagen für {url}: {e}")
            return False
    
    def generate_systematic_node_ids(self) -> int:
        """Generiere systematische Node-ID-Variationen"""
        # This would implement more sophisticated Node-ID generation
        # For now, return 0 as this is complex and would need more analysis
        return 0
    
    def generate_date_based_patterns(self, year: int, month: int) -> List[str]:
        """Generiere datumsbasierte URL-Patterns"""
        patterns = []
        
        # Beispiel-Patterns basierend auf Datum
        for day in [1, 15, 28]:  # Teste einige Tage
            # Simuliere mögliche Parameter-Patterns
            pattern = f"tx_dnotionlineplusapi_expertises%5Byear%5D={year}&tx_dnotionlineplusapi_expertises%5Bmonth%5D={month:02d}"
            patterns.append(pattern)
        
        return patterns
    
    def extract_gutachten_info_from_response(self, response, url: str) -> Optional[Dict]:
        """Extrahiere Gutachten-Info aus Response"""
        try:
            soup = BeautifulSoup(response.content, 'html.parser')
            title_elem = soup.find('title')
            
            if title_elem:
                # Extrahiere Node-ID aus URL
                node_match = re.search(r'nodeid.*?([a-f0-9\-]{36})', url, re.IGNORECASE)
                node_id = node_match.group(1) if node_match else str(uuid.uuid4())
                
                return {
                    'url': url,
                    'node_id': node_id,
                    'title': title_elem.get_text().strip(),
                    'discovery_method': 'systematic_scan',
                    'found_at': datetime.now().isoformat()
                }
        
        except Exception as e:
            self.logger.debug(f"Fehler beim Extrahieren aus Response: {e}")
        
        return None
    
    def extract_gutachten_from_link(self, link_element) -> Optional[Dict]:
        """Extrahiere Gutachten-Informationen aus Link-Element"""
        try:
            href = link_element.get('href', '')
            text = link_element.get_text(strip=True)
            
            if 'nodeid' in href:
                # Extrahiere Node-ID
                node_match = re.search(r'nodeid.*?([a-f0-9\-]{36})', href, re.IGNORECASE)
                node_id = node_match.group(1) if node_match else None
                
                if node_id:
                    # Erstelle vollständige URL
                    if href.startswith('http'):
                        full_url = href
                    else:
                        full_url = self.config.BASE_URL + href if href.startswith('/') else self.config.BASE_URL + '/' + href
                    
                    return {
                        'url': full_url,
                        'title': text or 'Unbekannt',
                        'node_id': node_id,
                        'found_at': datetime.now().isoformat(),
                        'discovery_method': 'search_monitor'
                    }
            
        except Exception as e:
            self.logger.debug(f"Fehler beim Extrahieren von Link: {e}")
        
        return None
    
    def save_search_health_status(self, is_healthy: bool):
        """Speichere Search-Health-Status"""
        try:
            status_file = Path(self.config.LAST_SUCCESSFUL_SEARCH_FILE)
            status_data = {
                'timestamp': datetime.now().isoformat(),
                'is_healthy': is_healthy,
                'status': self.stats['search_health_status']
            }
            
            with open(status_file, 'w', encoding='utf-8') as f:
                json.dump(status_data, f, indent=2)
                
        except Exception as e:
            self.logger.debug(f"Fehler beim Speichern des Health-Status: {e}")
    
    def process_found_gutachten(self):
        """Verarbeite gefundene Gutachten"""
        if not self.found_gutachten:
            self.logger.info("Keine neuen Gutachten zu verarbeiten")
            return
        
        # Limitiere auf Maximum pro Lauf
        gutachten_to_process = self.found_gutachten[:self.config.MAX_NEW_DOCUMENTS_PER_RUN]
        
        self.logger.info(f"Verarbeite {len(gutachten_to_process)} gefundene Gutachten...")
        
        for gutachten in gutachten_to_process:
            try:
                self.logger.info(f"Gutachten: {gutachten['title'][:80]} | {gutachten['url']}")
                self.stats['gutachten_found'] += 1
                
                if gutachten['url'] not in self.known_urls:
                    self.stats['gutachten_new'] += 1
                    self.logger.info(f"  -> NEU! Noch nicht in der Datenbank")
                    
                    if not self.config.DRY_RUN_MODE and self.config.ENABLE_DATABASE_UPDATES:
                        # Extrahiere vollständigen Inhalt
                        content = self.extract_gutachten_content(gutachten['url'])
                        if content:
                            # Füge zu ChromaDB hinzu
                            self.add_to_database(gutachten, content)
                            self.stats['gutachten_updated'] += 1
                            self.logger.info(f"  -> Erfolgreich zur Datenbank hinzugefügt")
                        else:
                            self.logger.warning(f"  -> Konnte Inhalt nicht extrahieren")
                    else:
                        self.logger.info(f"  -> DRY-RUN: Würde zur Datenbank hinzufügen")
                else:
                    self.logger.info(f"  -> Bereits in der Datenbank vorhanden")
                
            except Exception as e:
                self.logger.error(f"Fehler beim Verarbeiten von Gutachten: {e}")
                self.stats['errors'] += 1
    
    def extract_gutachten_content(self, url: str) -> Optional[str]:
        """Extrahiere vollständigen Inhalt eines Gutachtens"""
        try:
            response = self.session.get(url, timeout=self.config.REQUEST_TIMEOUT)
            if response.status_code == 200:
                soup = BeautifulSoup(response.content, 'html.parser')
                
                # Entferne Navigation, Header, Footer
                for element in soup(['nav', 'header', 'footer', 'script', 'style']):
                    element.decompose()
                
                # Extrahiere Hauptinhalt
                content_selectors = [
                    '.content-main',
                    '.gutachten-content',
                    '.main-content',
                    'main',
                    'article',
                    '.content'
                ]
                
                content_div = None
                for selector in content_selectors:
                    content_div = soup.select_one(selector)
                    if content_div:
                        break
                
                if content_div:
                    content = content_div.get_text(strip=True, separator=' ')
                else:
                    # Fallback: ganzer Body
                    body = soup.find('body')
                    content = body.get_text(strip=True, separator=' ') if body else soup.get_text(strip=True)
                
                # Bereinige Text
                content = re.sub(r'\s+', ' ', content)
                content = content.strip()
                
                if len(content) > 500:  # Erhöhte Mindestlänge
                    return content
                    
            return None
            
        except Exception as e:
            self.logger.error(f"Fehler beim Extrahieren von Inhalt von {url}: {e}")
            return None
    
    def add_to_database(self, gutachten: Dict, content: str):
        """Füge Gutachten zur ChromaDB hinzu"""
        try:
            # Erstelle Metadaten
            metadata = {
                'url': gutachten['url'],
                'title': gutachten['title'],
                'node_id': gutachten['node_id'],
                'discovery_method': gutachten['discovery_method'],
                'found_at': gutachten['found_at'],
                'source': 'DNOTI',
                'type': 'Gutachten',
                'auto_updated': True
            }
            
            # Erstelle eindeutige ID
            doc_id = f"dnoti_{gutachten['node_id']}"
            
            # Füge zu ChromaDB hinzu
            self.collection.add(
                documents=[content],
                metadatas=[metadata],
                ids=[doc_id]
            )
            
            self.logger.debug(f"Dokument {doc_id} zur Sammlung hinzugefügt")
            
        except Exception as e:
            self.logger.error(f"Fehler beim Hinzufügen zur Datenbank: {e}")
            raise
    
    def log_final_stats(self, duration: float):
        """Logge finale Statistiken"""
        self.logger.info(f"=== DNOTI Production Auto-Update Abgeschlossen ===")
        self.logger.info(f"Gesamtdauer: {duration:.2f} Sekunden")
        self.logger.info(f"Search Health Status: {self.stats['search_health_status']}")
        self.logger.info(f"Strategien versucht: {self.stats['strategies_attempted']}")
        self.logger.info(f"Strategien erfolgreich: {self.stats['strategies_successful']}")
        self.logger.info(f"Gutachten gefunden: {self.stats['gutachten_found']}")
        self.logger.info(f"Neue Gutachten: {self.stats['gutachten_new']}")
        self.logger.info(f"Gutachten aktualisiert: {self.stats['gutachten_updated']}")
        self.logger.info(f"URLs validiert: {self.stats['gutachten_validated']}")
        self.logger.info(f"Fehler: {self.stats['errors']}")


def main():
    """Hauptfunktion"""
    print("DNOTI Production Auto-Updater v6.0")
    print("=" * 50)
    print("Production-ready mit Enhanced Discovery & Monitoring")
    
    config = DNOTIProductionConfig()
    updater = DNOTIProductionUpdater(config)
    
    try:
        success = updater.run_production_cycle()
        
        if success:
            print("\\n✅ Production Update-Zyklus erfolgreich abgeschlossen")
        else:
            print("\\n⚠️ Production Update-Zyklus ohne neue Gutachten beendet")
            
    except KeyboardInterrupt:
        print("\\nUpdate durch Benutzer abgebrochen")
    except Exception as e:
        print(f"\\n❌ Unerwarteter Fehler: {e}")


if __name__ == "__main__":
    main()
