#!/usr/bin/env python3
"""
DNOTI Hybrid Auto-Updater v5.0
===============================
Hybride Lösung mit Fallback-Strategien:
1. Form-basierte Suche (primary)
2. URL-Pattern-Discovery (fallback)
3. Database-URL-Validation (maintenance)
"""

import requests
from bs4 import BeautifulSoup
import re
import json
from datetime import datetime, timedelta
import time
import logging
from pathlib import Path
from typing import List, Dict, Optional, Set
from dataclasses import dataclass, field
import uuid
import os

# Import der bestehenden ChromaDB Komponenten
from src.vectordb.chroma_client import ChromaDBClient

@dataclass
class DNOTIHybridConfig:
    """Konfiguration für DNOTI Hybrid Auto-Updater"""
    
    # URLs
    BASE_URL: str = "https://www.dnoti.de"
    GUTACHTEN_SEARCH_URL: str = "https://www.dnoti.de/gutachten/"
    
    # Request-Konfiguration
    REQUEST_TIMEOUT: int = 30
    REQUEST_DELAY_SECONDS: float = 2.0
    MAX_RETRIES: int = 3
    
    # ChromaDB-Konfiguration  
    COLLECTION_NAME: str = "dnoti_gutachten"
    
    # Logging-Konfiguration
    LOG_LEVEL: str = "INFO"
    LOG_DIR: str = "logs"
    
    # Hybrid-Strategien
    STRATEGIES: List[str] = field(default_factory=lambda: [
        "form_search",       # Versuche Form-basierte Suche
        "url_discovery",     # URL-Pattern-Discovery
        "database_validation" # Validiere bestehende URLs
    ])
    
    # Discovery-Konfiguration
    KNOWN_GUTACHTEN_FILE: str = "Database/Original/dnoti_all.json"
    MAX_DISCOVERY_ATTEMPTS: int = 50
    DISCOVERY_YEARS: List[int] = field(default_factory=lambda: [2024, 2025])
    
    def __post_init__(self):
        # Erstelle Log-Verzeichnis
        Path(self.LOG_DIR).mkdir(exist_ok=True)


class DNOTIHybridAutoUpdater:
    """DNOTI Hybrid Auto-Updater mit mehreren Fallback-Strategien"""
    
    def __init__(self, config: DNOTIHybridConfig):
        self.config = config
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })
        
        self.stats = {
            'strategies_attempted': 0,
            'strategies_successful': 0,
            'gutachten_found': 0,
            'gutachten_new': 0,
            'gutachten_updated': 0,
            'errors': 0
        }
        
        self.found_gutachten: List[Dict] = []
        self.known_urls: Set[str] = set()
        
        # Setup Logging
        self.setup_logging()
        
        # Initialize ChromaDB
        self.chroma_client = None
        self.collection = None
        
    def setup_logging(self):
        """Setup detailliertes Logging"""
        log_file = Path(self.config.LOG_DIR) / "dnoti_hybrid_v5.log"
        
        # Create formatters
        file_formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        console_formatter = logging.Formatter(
            '%(levelname)s - %(message)s'
        )
        
        # Setup logger
        self.logger = logging.getLogger('DNOTIHybridV5')
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
            
            self.logger.info(f"Geladen: {len(self.known_urls)} bekannte Gutachten-URLs")
            return True
            
        except Exception as e:
            self.logger.error(f"Fehler beim Laden bekannter Gutachten: {e}")
            return False
    
    def run_update_cycle(self):
        """Führe Hybrid-Update-Zyklus aus"""
        start_time = time.time()
        
        self.logger.info("=== DNOTI Hybrid Auto-Update Zyklus gestartet ===")
        self.logger.info(f"Strategien: {', '.join(self.config.STRATEGIES)}")
        
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
                if strategy == "form_search":
                    success = self.strategy_form_search()
                elif strategy == "url_discovery":
                    success = self.strategy_url_discovery()
                elif strategy == "database_validation":
                    success = self.strategy_database_validation()
                else:
                    self.logger.warning(f"Unbekannte Strategie: {strategy}")
                    continue
                
                if success:
                    self.stats['strategies_successful'] += 1
                    self.logger.info(f"Strategie {strategy} erfolgreich")
                    
                    # Wenn wir Gutachten gefunden haben, können wir hier entscheiden ob wir fortfahren
                    if len(self.found_gutachten) > 0:
                        self.logger.info(f"Strategie {strategy} lieferte {len(self.found_gutachten)} Gutachten")
                else:
                    self.logger.warning(f"Strategie {strategy} nicht erfolgreich")
                
            except Exception as e:
                self.logger.error(f"Fehler in Strategie {strategy}: {e}")
                self.stats['errors'] += 1
            
            # Kurze Pause zwischen Strategien
            time.sleep(self.config.REQUEST_DELAY_SECONDS)
        
        # Process found Gutachten
        self.process_found_gutachten()
        
        # Statistiken
        duration = time.time() - start_time
        self.log_final_stats(duration)
        
        return len(self.found_gutachten) > 0
    
    def strategy_form_search(self) -> bool:
        """Strategie 1: Form-basierte Suche (wie in v4)"""
        self.logger.info("Versuche Form-basierte Suche...")
        
        try:
            # Test verschiedene Form-Parameter
            test_searches = [
                {'tx_dnotionlineplusapi_expertises[expertisesType]': ''},
                {'tx_dnotionlineplusapi_expertises[expertisesType]': 'all'},
                {'tx_dnotionlineplusapi_expertises[expertisesType]': 'dnotiReport', 
                 'tx_dnotionlineplusapi_expertises[reportYear]': '2024'},
                {'tx_dnotionlineplusapi_expertises[searchText]': 'BGB'},
            ]
            
            for i, search_params in enumerate(test_searches):
                base_params = {
                    'tx_dnotionlineplusapi_expertises[page]': '1',
                    'tx_dnotionlineplusapi_expertises[searchTitle]': '',
                    'tx_dnotionlineplusapi_expertises[searchText]': '',
                }
                base_params.update(search_params)
                
                response = self.session.post(
                    self.config.GUTACHTEN_SEARCH_URL,
                    data=base_params,
                    timeout=self.config.REQUEST_TIMEOUT
                )
                
                if response.status_code == 200:
                    soup = BeautifulSoup(response.content, 'html.parser')
                    nodeid_links = soup.find_all('a', href=re.compile(r'nodeid'))
                    
                    if nodeid_links:
                        self.logger.info(f"Form-Suche {i+1}: {len(nodeid_links)} Gutachten gefunden!")
                        
                        for link in nodeid_links:
                            gutachten_info = self.extract_gutachten_from_link(link)
                            if gutachten_info:
                                self.found_gutachten.append(gutachten_info)
                        
                        return True
                    else:
                        self.logger.debug(f"Form-Suche {i+1}: Keine Ergebnisse")
                
                time.sleep(self.config.REQUEST_DELAY_SECONDS * 0.5)
            
            self.logger.info("Form-basierte Suche: Keine Ergebnisse gefunden")
            return False
            
        except Exception as e:
            self.logger.error(f"Form-Suche fehlgeschlagen: {e}")
            return False
    
    def strategy_url_discovery(self) -> bool:
        """Strategie 2: URL-Pattern-Discovery basierend auf bekannten URLs"""
        self.logger.info("Versuche URL-Pattern-Discovery...")
        
        if not self.known_urls:
            self.logger.warning("Keine bekannten URLs für Discovery verfügbar")
            return False
        
        try:
            # Extrahiere Node-IDs aus bekannten URLs
            known_node_ids = set()
            for url in list(self.known_urls)[:10]:  # Begrenzt für Test
                node_match = re.search(r'nodeid.*?([a-f0-9\-]{36})', url, re.IGNORECASE)
                if node_match:
                    known_node_ids.add(node_match.group(1))
            
            self.logger.info(f"Extrahiert: {len(known_node_ids)} bekannte Node-IDs")
            
            # Teste Variationen der Node-IDs oder schaue nach ähnlichen Patterns
            discovery_count = 0
            attempts = 0
            
            for node_id in list(known_node_ids)[:5]:  # Teste nur einige
                if attempts >= self.config.MAX_DISCOVERY_ATTEMPTS:
                    break
                
                # Versuche den direkten Zugriff auf bekannte URL
                test_url = f"{self.config.BASE_URL}/gutachten/details/?tx_dnotionlineplusapi_expertises%5Bnodeid%5D={node_id}&cHash=test"
                
                try:
                    response = self.session.get(test_url, timeout=self.config.REQUEST_TIMEOUT)
                    attempts += 1
                    
                    if response.status_code == 200:
                        # Prüfe ob es ein gültiges Gutachten ist
                        soup = BeautifulSoup(response.content, 'html.parser')
                        title_elem = soup.find('title')
                        
                        if title_elem and 'gutachten' not in title_elem.get_text().lower():
                            continue  # Möglicherweise Fehlerseite
                        
                        gutachten_info = {
                            'url': test_url,
                            'node_id': node_id,
                            'title': title_elem.get_text() if title_elem else 'Unbekannt',
                            'discovery_method': 'url_pattern',
                            'found_at': datetime.now().isoformat()
                        }
                        
                        self.found_gutachten.append(gutachten_info)
                        discovery_count += 1
                        
                        self.logger.info(f"URL-Discovery: Gutachten gefunden - {node_id}")
                    
                    time.sleep(self.config.REQUEST_DELAY_SECONDS)
                    
                except Exception as e:
                    self.logger.debug(f"URL-Test fehlgeschlagen für {node_id}: {e}")
                    attempts += 1
            
            self.logger.info(f"URL-Discovery: {discovery_count} neue Gutachten gefunden")
            return discovery_count > 0
            
        except Exception as e:
            self.logger.error(f"URL-Discovery fehlgeschlagen: {e}")
            return False
    
    def strategy_database_validation(self) -> bool:
        """Strategie 3: Validiere bestehende URLs aus Datenbank"""
        self.logger.info("Versuche Database-Validation...")
        
        if not self.known_urls:
            self.logger.warning("Keine bekannten URLs für Validation verfügbar")
            return False
        
        try:
            validation_count = 0
            
            # Teste eine Stichprobe der bekannten URLs
            sample_urls = list(self.known_urls)[:10]  # Teste nur einige
            
            for url in sample_urls:
                try:
                    response = self.session.get(url, timeout=self.config.REQUEST_TIMEOUT)
                    
                    if response.status_code == 200:
                        soup = BeautifulSoup(response.content, 'html.parser')
                        title_elem = soup.find('title')
                        
                        if title_elem and len(response.content) > 10000:  # Einfache Validierung
                            # URL ist noch gültig, könnte als "gefunden" gezählt werden
                            validation_count += 1
                            self.logger.debug(f"URL validiert: {url}")
                        else:
                            self.logger.debug(f"URL möglicherweise nicht mehr gültig: {url}")
                    else:
                        self.logger.debug(f"URL nicht erreichbar: {url} (Status: {response.status_code})")
                    
                    time.sleep(self.config.REQUEST_DELAY_SECONDS * 0.5)
                    
                except Exception as e:
                    self.logger.debug(f"Validation-Fehler für {url}: {e}")
            
            self.logger.info(f"Database-Validation: {validation_count}/{len(sample_urls)} URLs validiert")
            return validation_count > 0
            
        except Exception as e:
            self.logger.error(f"Database-Validation fehlgeschlagen: {e}")
            return False
    
    def extract_gutachten_from_link(self, link_element) -> Optional[Dict]:
        """Extrahiere Gutachten-Info aus Link-Element"""
        try:
            href = link_element.get('href', '')
            text = link_element.get_text(strip=True)
            
            if 'nodeid' not in href:
                return None
            
            # Extrahiere Node-ID
            node_match = re.search(r'nodeid.*?([a-f0-9\-]{36})', href, re.IGNORECASE)
            node_id = node_match.group(1) if node_match else None
            
            # Normalisiere URL
            if href.startswith('/'):
                full_url = self.config.BASE_URL + href
            elif not href.startswith('http'):
                full_url = self.config.BASE_URL + '/' + href
            else:
                full_url = href
            
            return {
                'url': full_url,
                'title': text or 'Unbekannt',
                'node_id': node_id,                'found_at': datetime.now().isoformat(),
                'discovery_method': 'form_search'
            }
            
        except Exception as e:
            self.logger.debug(f"Fehler beim Extrahieren von Link: {e}")
            return None
    
    def process_found_gutachten(self):
        """Verarbeite gefundene Gutachten"""
        if not self.found_gutachten:
            self.logger.info("Keine neuen Gutachten zu verarbeiten")
            return
        
        self.logger.info(f"Verarbeite {len(self.found_gutachten)} gefundene Gutachten...")
        
        for gutachten in self.found_gutachten:
            try:
                self.logger.info(f"Gutachten: {gutachten['title'][:80]} | {gutachten['url']}")
                self.stats['gutachten_found'] += 1
                
                if gutachten['url'] not in self.known_urls:
                    self.stats['gutachten_new'] += 1
                    self.logger.info(f"  -> NEU! Noch nicht in der Datenbank")
                    
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
                content_div = soup.find('div', class_='content-main') or soup.find('main') or soup.find('article')
                if content_div:
                    content = content_div.get_text(strip=True, separator=' ')
                else:
                    # Fallback: ganzer Body
                    body = soup.find('body')
                    content = body.get_text(strip=True, separator=' ') if body else soup.get_text(strip=True)
                
                # Bereinige Text
                content = re.sub(r'\s+', ' ', content)
                content = content.strip()
                
                if len(content) > 100:  # Mindestlänge prüfen
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
                'type': 'Gutachten'
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
        self.logger.info(f"=== DNOTI Hybrid Auto-Update Abgeschlossen ===")
        self.logger.info(f"Gesamtdauer: {duration:.2f} Sekunden")
        self.logger.info(f"Strategien versucht: {self.stats['strategies_attempted']}")
        self.logger.info(f"Strategien erfolgreich: {self.stats['strategies_successful']}")
        self.logger.info(f"Gutachten gefunden: {self.stats['gutachten_found']}")
        self.logger.info(f"Neue Gutachten: {self.stats['gutachten_new']}")
        self.logger.info(f"Fehler: {self.stats['errors']}")


def main():
    """Hauptfunktion"""
    print("DNOTI Hybrid Auto-Updater v5.0 - Multi-Strategy Approach")
    print("=" * 65)
    print("Hybride Lösung mit Form-Search, URL-Discovery und Database-Validation")
    
    config = DNOTIHybridConfig()
    updater = DNOTIHybridAutoUpdater(config)
    
    try:
        success = updater.run_update_cycle()
        
        if success:
            print("\\n✅ Update-Zyklus erfolgreich abgeschlossen")
        else:
            print("\\n⚠️ Update-Zyklus ohne neue Gutachten beendet")
            
    except KeyboardInterrupt:
        print("\\nUpdate durch Benutzer abgebrochen")
    except Exception as e:
        print(f"\\n❌ Unerwarteter Fehler: {e}")


if __name__ == "__main__":
    main()
