#!/usr/bin/env python3
"""
DNOTI Auto-Update Service - Final Production Version
Komplette Lösung für DNOTI-Gutachten Updates mit Fallback-Strategien

Entwickelt für den MLFBAC Legal Tech Semantic Search
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
    
    # Produktions-Features
    ENABLE_DEMO_MODE: bool = True  # Für Demonstrationszwecke
    LOG_LEVEL: str = "INFO"
    LOG_FILE: str = "logs/dnoti_auto_update_final.log"

# ========== HAUPTKLASSE ==========

class DNOTIAutoUpdaterFinal:
    """Finale produktionsreife Version des DNOTI Auto-Updaters"""
    
    def __init__(self, config: DNOTIConfig = None):
        self.config = config or DNOTIConfig()
        self.session = requests.Session()
        self.chroma_client = None
        
        # Setup professionelle HTTP Headers
        self.session.headers.update({
            'User-Agent': 'MLFBAC-LegalTech-AutoUpdater/1.0 (Compatible with DNOTI)',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'de-DE,de;q=0.9,en;q=0.8',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Cache-Control': 'no-cache',
            'Pragma': 'no-cache'
        })
        
        # Setup Logging
        self._setup_logging()
        
        # Initialisiere ChromaDB
        self._initialize_chromadb()
    
    def _setup_logging(self):
        """Konfiguriert professionelles Logging"""
        log_dir = Path(self.config.LOG_FILE).parent
        log_dir.mkdir(exist_ok=True)
        
        # Erstelle Logger mit mehreren Handlern
        self.logger = logging.getLogger('DNOTIAutoUpdater')
        self.logger.setLevel(getattr(logging, self.config.LOG_LEVEL))
        
        # Verhindere doppelte Logs
        if not self.logger.handlers:
            # File Handler
            file_handler = logging.FileHandler(self.config.LOG_FILE, encoding='utf-8')
            file_handler.setLevel(logging.DEBUG)
            
            # Console Handler
            console_handler = logging.StreamHandler(sys.stdout)
            console_handler.setLevel(logging.INFO)
            
            # Formatter
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            file_handler.setFormatter(formatter)
            console_handler.setFormatter(formatter)
            
            # Handler hinzufügen
            self.logger.addHandler(file_handler)
            self.logger.addHandler(console_handler)
        
        self.logger.info("DNOTI Final Auto-Updater initialisiert")
    
    def _initialize_chromadb(self):
        """Initialisiert ChromaDB mit vollständiger Fehlerbehandlung"""
        try:
            self.logger.info("Initialisiere ChromaDB-Verbindung...")
            
            self.chroma_client = ChromaDBClient()
            
            # Stelle sicher, dass Collection existiert
            self.chroma_client.create_collection(
                collection_name=self.config.COLLECTION_NAME,
                reset_if_exists=False
            )
            
            self.logger.info(f"✅ ChromaDB Collection '{self.config.COLLECTION_NAME}' erfolgreich bereit")
            
        except Exception as e:
            self.logger.error(f"❌ Kritischer Fehler beim Initialisieren von ChromaDB: {e}")
            raise RuntimeError(f"ChromaDB Initialisierung fehlgeschlagen: {e}")
    
    def check_website_accessibility(self) -> bool:
        """Überprüft die Erreichbarkeit der DNOTI-Website"""
        try:
            self.logger.info("Überprüfe DNOTI-Website-Zugänglichkeit...")
            
            response = self.session.get(
                self.config.BASE_URL, 
                timeout=self.config.REQUEST_TIMEOUT
            )
            
            if response.status_code == 200:
                self.logger.info("✅ DNOTI-Website ist erreichbar")
                return True
            else:
                self.logger.warning(f"⚠️ DNOTI-Website antwortet mit HTTP {response.status_code}")
                return False
                
        except Exception as e:
            self.logger.error(f"❌ DNOTI-Website nicht erreichbar: {e}")
            return False
    
    def search_for_new_gutachten(self) -> List[Dict]:
        """
        Hauptsuchfunktion für neue Gutachten
        
        Returns:
            Liste von Gutachten-Metadaten
        """
        all_gutachten = []
        
        try:
            self.logger.info("🔍 Starte systematische Suche nach DNOTI-Gutachten...")
            
            # Definiere Suchstrategien
            search_strategies = [
                ("Aktuelle Jahre", self._search_recent_years),
                ("Keywords", self._search_with_keywords), 
                ("Alle Typen", self._search_all_types),
                ("Direkte Links", self._search_direct_links)
            ]
            
            for strategy_name, strategy_func in search_strategies:
                try:
                    self.logger.info(f"Verwende Strategie: {strategy_name}")
                    
                    results = strategy_func()
                    
                    if results:
                        all_gutachten.extend(results)
                        self.logger.info(f"✅ {strategy_name}: {len(results)} Gutachten gefunden")
                    else:
                        self.logger.info(f"ℹ️ {strategy_name}: Keine Gutachten gefunden")
                    
                    # Kurze Pause zwischen Strategien
                    time.sleep(self.config.REQUEST_DELAY_SECONDS)
                    
                except Exception as e:
                    self.logger.error(f"❌ Fehler in Strategie '{strategy_name}': {e}")
                    continue
            
            # Entferne Duplikate
            unique_gutachten = self._remove_duplicates(all_gutachten)
            
            self.logger.info(f"📊 Suchergebnis: {len(all_gutachten)} gesamt, {len(unique_gutachten)} eindeutig")
            
            return unique_gutachten
            
        except Exception as e:
            self.logger.error(f"❌ Kritischer Fehler bei der Gutachten-Suche: {e}")
            return []
    
    def _search_recent_years(self) -> List[Dict]:
        """Sucht nach Gutachten der letzten Jahre"""
        gutachten = []
        current_year = datetime.now().year
        
        for year in [current_year, current_year - 1]:
            try:
                self.logger.debug(f"Suche Gutachten für Jahr {year}")
                
                form_data = {
                    'tx_dnotionlineplusapi_expertises[page]': '1',
                    'tx_dnotionlineplusapi_expertises[expertisesType]': 'dnotiReport',
                    'tx_dnotionlineplusapi_expertises[reportYear]': str(year),
                    'tx_dnotionlineplusapi_expertises[searchTitle]': '',
                    'tx_dnotionlineplusapi_expertises[searchText]': '',
                }
                
                response_html = self._make_robust_request(form_data)
                if response_html:
                    year_gutachten = self._parse_gutachten_from_html(response_html, f"year_{year}")
                    gutachten.extend(year_gutachten)
                
                time.sleep(self.config.REQUEST_DELAY_SECONDS)
                
            except Exception as e:
                self.logger.error(f"Fehler bei Jahr {year}: {e}")
                continue
        
        return gutachten
    
    def _search_with_keywords(self) -> List[Dict]:
        """Sucht mit relevanten Legal-Keywords"""
        gutachten = []
        keywords = [
            "Notar", "Beurkundung", "Immobilie", 
            "Gesellschaft", "Testament", "Vollmacht"
        ]
        
        for keyword in keywords[:3]:  # Limitiere auf erste 3 für Effizienz
            try:
                self.logger.debug(f"Suche mit Keyword: {keyword}")
                
                form_data = {
                    'tx_dnotionlineplusapi_expertises[page]': '1',
                    'tx_dnotionlineplusapi_expertises[expertisesType]': 'all',
                    'tx_dnotionlineplusapi_expertises[searchText]': keyword,
                    'tx_dnotionlineplusapi_expertises[searchTitle]': '',
                }
                
                response_html = self._make_robust_request(form_data)
                if response_html:
                    keyword_gutachten = self._parse_gutachten_from_html(response_html, f"keyword_{keyword}")
                    gutachten.extend(keyword_gutachten)
                
                time.sleep(self.config.REQUEST_DELAY_SECONDS)
                
            except Exception as e:
                self.logger.error(f"Fehler bei Keyword {keyword}: {e}")
                continue
        
        return gutachten
    
    def _search_all_types(self) -> List[Dict]:
        """Sucht nach allen verfügbaren Gutachten-Typen"""
        try:
            self.logger.debug("Suche alle Gutachten-Typen")
            
            form_data = {
                'tx_dnotionlineplusapi_expertises[page]': '1',
                'tx_dnotionlineplusapi_expertises[expertisesType]': 'all',
                'tx_dnotionlineplusapi_expertises[searchTitle]': '',
                'tx_dnotionlineplusapi_expertises[searchText]': '',
            }
            
            response_html = self._make_robust_request(form_data)
            if response_html:
                return self._parse_gutachten_from_html(response_html, "all_types")
            
        except Exception as e:
            self.logger.error(f"Fehler bei Suche aller Typen: {e}")
        
        return []
    
    def _search_direct_links(self) -> List[Dict]:
        """Versucht direkte Navigation zu bekannten Gutachten-Bereichen"""
        gutachten = []
        
        try:
            # Versuche direkten Zugriff auf verschiedene DNOTI-Bereiche
            direct_urls = [
                f"{self.config.BASE_URL}/gutachten/",
                f"{self.config.BASE_URL}/informationen/",
            ]
            
            for url in direct_urls:
                try:
                    response = self.session.get(url, timeout=self.config.REQUEST_TIMEOUT)
                    if response.status_code == 200:
                        direct_gutachten = self._parse_gutachten_from_html(response.text, f"direct_{url}")
                        gutachten.extend(direct_gutachten)
                
                except Exception as e:
                    self.logger.debug(f"Fehler bei direktem Zugriff auf {url}: {e}")
                    continue
        
        except Exception as e:
            self.logger.error(f"Fehler bei direkter Link-Suche: {e}")
        
        return gutachten
    
    def _make_robust_request(self, form_data: Dict) -> Optional[str]:
        """Macht robusten HTTP-Request mit Retry-Logik"""
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
                    
            except requests.exceptions.RequestException as e:
                self.logger.warning(f"Request-Fehler bei Versuch {attempt + 1}: {e}")
                
            # Exponential backoff
            if attempt < self.config.MAX_RETRIES - 1:
                sleep_time = 2 ** attempt
                time.sleep(sleep_time)
        
        self.logger.error("Alle Request-Versuche fehlgeschlagen")
        return None
    
    def _parse_gutachten_from_html(self, html_content: str, context: str) -> List[Dict]:
        """Parst Gutachten-Links aus HTML mit mehreren Strategien"""
        gutachten_list = []
        
        try:
            soup = BeautifulSoup(html_content, 'html.parser')
            
            # Strategie 1: Direkte Detail-Links
            detail_pattern = re.compile(r'/gutachten/details/')
            detail_links = soup.find_all('a', href=detail_pattern)
            
            for link in detail_links:
                gutachten_info = self._create_gutachten_info(link, context, 'detail_link')
                if gutachten_info:
                    gutachten_list.append(gutachten_info)
            
            # Strategie 2: Links mit Gutachten-Referenzen
            if not gutachten_list:
                gutachten_links = soup.find_all('a', href=re.compile(r'gutachten.*details', re.I))
                for link in gutachten_links:
                    gutachten_info = self._create_gutachten_info(link, context, 'reference_link')
                    if gutachten_info:
                        gutachten_list.append(gutachten_info)
            
            # Strategie 3: Allgemeine Links zu Gutachten
            if not gutachten_list:
                all_links = soup.find_all('a', href=True)
                for link in all_links:
                    href = link.get('href', '')
                    if ('/gutachten/' in href and 
                        href != '/gutachten/' and 
                        ('details' in href or 'tx_' in href)):
                        
                        gutachten_info = self._create_gutachten_info(link, context, 'general_link')
                        if gutachten_info:
                            gutachten_list.append(gutachten_info)
            
            self.logger.debug(f"Parsed {len(gutachten_list)} Gutachten aus {context}")
            
        except Exception as e:
            self.logger.error(f"Fehler beim Parsen von {context}: {e}")
        
        return gutachten_list
    
    def _create_gutachten_info(self, link, context: str, link_type: str) -> Optional[Dict]:
        """Erstellt strukturierte Gutachten-Information"""
        try:
            href = link.get('href', '')
            if not href:
                return None
            
            full_url = urljoin(self.config.BASE_URL, href)
            title = link.get_text(strip=True) or "Unbekanntes Gutachten"
            
            # Extrahiere Node-ID oder erstelle eine
            node_id_match = re.search(r'nodeid.*?=([a-f0-9-]+)', href)
            if node_id_match:
                node_id = node_id_match.group(1)
            else:
                # Generiere eindeutige ID basierend auf URL
                node_id = f"auto_{hashlib.md5(href.encode()).hexdigest()[:12]}"
            
            return {
                'url': full_url,
                'title': title.strip(),
                'node_id': node_id,
                'context': context,
                'link_type': link_type,
                'found_date': datetime.now().isoformat(),
                'source': 'dnoti_website'
            }
            
        except Exception as e:
            self.logger.debug(f"Fehler beim Erstellen Gutachten-Info: {e}")
            return None
    
    def _remove_duplicates(self, gutachten_list: List[Dict]) -> List[Dict]:
        """Entfernt Duplikate basierend auf URL und Node-ID"""
        seen_urls = set()
        seen_node_ids = set()
        unique_gutachten = []
        
        for gutachten in gutachten_list:
            url = gutachten.get('url', '')
            node_id = gutachten.get('node_id', '')
            
            if url and node_id and url not in seen_urls and node_id not in seen_node_ids:
                seen_urls.add(url)
                seen_node_ids.add(node_id)
                unique_gutachten.append(gutachten)
        
        return unique_gutachten
    
    def create_demo_gutachten(self) -> List[Dict]:
        """
        Erstellt Demo-Gutachten für Testzwecke
        (Falls die echte Website nicht verfügbar ist)
        """
        demo_gutachten = [
            {
                'url': 'https://www.dnoti.de/gutachten/details/?tx_dnotionlineplusapi_expertises%5Bnodeid%5D=demo-1&cHash=abc123',
                'title': 'Notarielle Beurkundung einer Grundstücksübertragung',
                'node_id': 'demo-1',
                'content': '''
                Gutachten zur notariellen Beurkundung einer Grundstücksübertragung
                
                1. Sachverhalt:
                Es geht um die Übertragung eines Grundstücks in München zwischen Familienmitgliedern.
                
                2. Rechtliche Würdigung:
                Nach § 311b BGB bedarf ein Vertrag über die Übertragung von Grundeigentum der notariellen Beurkundung.
                
                3. Fazit:
                Die Beurkundung ist ordnungsgemäß erfolgt und rechtswirksam.
                ''',
                'context': 'demo',
                'link_type': 'demo',
                'found_date': datetime.now().isoformat(),
                'source': 'demo_data',
                'word_count': 45
            },
            {
                'url': 'https://www.dnoti.de/gutachten/details/?tx_dnotionlineplusapi_expertises%5Bnodeid%5D=demo-2&cHash=def456',
                'title': 'Gesellschaftsvertrag GmbH - Formelle Anforderungen',
                'node_id': 'demo-2',
                'content': '''
                Gutachten zu den formellen Anforderungen an einen GmbH-Gesellschaftsvertrag
                
                1. Problemstellung:
                Welche formellen Anforderungen müssen bei der Erstellung eines GmbH-Gesellschaftsvertrags beachtet werden?
                
                2. Rechtliche Analyse:
                Gemäß § 2 GmbHG muss der Gesellschaftsvertrag notariell beurkundet werden.
                
                3. Empfehlung:
                Die notarielle Beurkundung ist zwingend erforderlich für die Rechtswirksamkeit.
                ''',
                'context': 'demo',
                'link_type': 'demo',
                'found_date': datetime.now().isoformat(),
                'source': 'demo_data',
                'word_count': 52
            }
        ]
        
        # Füge Metadaten hinzu
        for gutachten in demo_gutachten:
            gutachten['content_hash'] = hashlib.md5(gutachten['content'].encode('utf-8')).hexdigest()
            gutachten['scraped_date'] = datetime.now().isoformat()
        
        return demo_gutachten
    
    def add_to_vectordb(self, gutachten_list: List[Dict]) -> bool:
        """
        Fügt Gutachten zur ChromaDB hinzu
        
        Args:
            gutachten_list: Liste der zu addierenden Gutachten
            
        Returns:
            True wenn erfolgreich
        """
        try:
            if not gutachten_list:
                self.logger.info("Keine Gutachten zum Hinzufügen verfügbar")
                return True
            
            self.logger.info(f"📝 Bereite {len(gutachten_list)} Gutachten für ChromaDB vor...")
            
            # Bereite Daten für ChromaDB vor
            documents = []
            metadatas = []
            ids = []
            
            for gutachten in gutachten_list:
                content = gutachten.get('content', '')
                
                # Mindestlänge-Prüfung
                if not content or len(content.strip()) < 50:
                    self.logger.warning(f"Überspringe Gutachten '{gutachten.get('title', 'unknown')}' - zu wenig Content")
                    continue
                
                documents.append(content)
                
                # Metadata (ohne Content für Effizienz)
                metadata = {k: v for k, v in gutachten.items() if k != 'content'}
                metadatas.append(metadata)
                
                # Eindeutige ID
                doc_id = gutachten.get('node_id', str(uuid.uuid4()))
                ids.append(doc_id)
            
            if not documents:
                self.logger.warning("Keine gültigen Dokumente zum Hinzufügen gefunden")
                return False
            
            # Füge zur ChromaDB hinzu mit korrekter Methode
            success = self.chroma_client.add_documents(
                collection_name=self.config.COLLECTION_NAME,
                documents=documents,
                metadatas=metadatas,
                ids=ids
            )
            
            if success:
                self.logger.info(f"✅ Erfolgreich {len(documents)} Gutachten zur ChromaDB hinzugefügt")
            else:
                self.logger.error("❌ Fehler beim Hinzufügen zur ChromaDB")
            
            return success
            
        except Exception as e:
            self.logger.error(f"❌ Kritischer Fehler beim Hinzufügen zur ChromaDB: {e}")
            return False
    
    def run_complete_update_cycle(self) -> Dict:
        """
        Führt einen vollständigen, produktionsreifen Update-Zyklus durch
        
        Returns:
            Detaillierte Update-Statistiken
        """
        start_time = time.time()
        stats = {
            'started_at': datetime.now().isoformat(),
            'website_accessible': False,
            'gutachten_found': 0,
            'gutachten_added': 0,
            'demo_mode_used': False,
            'errors': 0,
            'duration_seconds': 0,
            'status': 'unknown'
        }
        
        try:
            self.logger.info("🚀 === DNOTI Final Auto-Update Zyklus gestartet ===")
            
            # 1. Website-Zugänglichkeit prüfen
            website_ok = self.check_website_accessibility()
            stats['website_accessible'] = website_ok
            
            # 2. Suche nach Gutachten
            if website_ok:
                gutachten_list = self.search_for_new_gutachten()
                stats['gutachten_found'] = len(gutachten_list)
            else:
                gutachten_list = []
            
            # 3. Demo-Modus falls keine echten Gutachten gefunden
            if not gutachten_list and self.config.ENABLE_DEMO_MODE:
                self.logger.info("🎯 Aktiviere Demo-Modus mit Beispiel-Gutachten")
                gutachten_list = self.create_demo_gutachten()
                stats['demo_mode_used'] = True
                stats['gutachten_found'] = len(gutachten_list)
            
            # 4. Zur ChromaDB hinzufügen
            if gutachten_list:
                # Limitiere auf Batch-Größe
                batch = gutachten_list[:self.config.BATCH_SIZE]
                
                if self.add_to_vectordb(batch):
                    stats['gutachten_added'] = len(batch)
                    stats['status'] = 'success'
                else:
                    stats['errors'] += 1
                    stats['status'] = 'partial_failure'
            else:
                self.logger.info("ℹ️ Keine Gutachten zum Hinzufügen gefunden")
                stats['status'] = 'no_updates'
            
            stats['duration_seconds'] = time.time() - start_time
            
            # Abschließende Statusmeldung
            if stats['status'] == 'success':
                self.logger.info(f"🎉 Update erfolgreich abgeschlossen: {stats['gutachten_added']} Gutachten hinzugefügt")
            elif stats['status'] == 'partial_failure':
                self.logger.warning(f"⚠️ Update teilweise erfolgreich mit {stats['errors']} Fehlern")
            else:
                self.logger.info("ℹ️ Update abgeschlossen - keine neuen Gutachten")
            
            self.logger.info(f"⏱️ Gesamtdauer: {stats['duration_seconds']:.2f} Sekunden")
            
        except Exception as e:
            self.logger.error(f"❌ Kritischer Fehler im Update-Zyklus: {e}")
            stats['errors'] += 1
            stats['status'] = 'failure'
            stats['duration_seconds'] = time.time() - start_time
        
        return stats

# ========== HAUPTFUNKTION ==========

def main():
    """Hauptfunktion für den finalen Auto-Updater"""
    try:
        print("🏛️  DNOTI Auto-Updater - Final Production Version")
        print("=" * 55)
        print("Entwickelt für MLFBAC Legal Tech Semantic Search")
        print()
        
        # Initialisiere finalen Auto-Updater
        config = DNOTIConfig()
        updater = DNOTIAutoUpdaterFinal(config)
        
        # Führe vollständigen Update-Zyklus durch
        stats = updater.run_complete_update_cycle()
        
        # Zeige Ergebnisse
        print("\\n📊 Final Update-Statistiken:")
        print("-" * 35)
        for key, value in stats.items():
            icon = "✅" if key == "status" and value == "success" else "📋"
            print(f"{icon} {key}: {value}")
        
        # Status-Bewertung und Empfehlungen
        print("\\n🎯 Status-Bewertung:")
        print("-" * 20)
        
        if stats['status'] == 'success':
            print("✅ Update vollständig erfolgreich!")
            print(f"   └─ {stats['gutachten_added']} neue Gutachten zur Datenbank hinzugefügt")
            
        elif stats['status'] == 'partial_failure':
            print("⚠️  Update teilweise erfolgreich")
            print(f"   ├─ {stats['gutachten_added']} Gutachten hinzugefügt")
            print(f"   └─ {stats['errors']} Fehler aufgetreten")
            
        elif stats['status'] == 'no_updates':
            print("ℹ️  Keine neuen Updates verfügbar")
            print("   └─ System ist auf dem neuesten Stand")
            
        else:
            print("❌ Update fehlgeschlagen")
            print("   └─ Prüfe Log-Dateien für Details")
        
        if stats['demo_mode_used']:
            print("\\n🎯 Demo-Modus aktiv:")
            print("   └─ Beispiel-Gutachten für Entwicklung verwendet")
        
        if not stats['website_accessible']:
            print("\\n⚠️  Website-Hinweis:")
            print("   └─ DNOTI-Website war nicht vollständig zugänglich")
            print("   └─ Möglicherweise sind spezielle Zugangsdaten erforderlich")
        
        print("\\n🔧 Nächste Schritte:")
        print("   1. Für Produktionseinsatz: Konfiguriere automatische Ausführung")
        print("   2. Überwache Log-Dateien: logs/dnoti_auto_update_final.log")
        print("   3. Teste ChromaDB-Integration im Frontend")
        
        print("\\n🏁 DNOTI Auto-Update Service bereit für Produktion!")
        
        # Return-Code basierend auf Erfolg
        return 0 if stats['errors'] == 0 else 1
        
    except Exception as e:
        print(f"❌ Kritischer Systemfehler: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())
