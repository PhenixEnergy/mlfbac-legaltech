#!/usr/bin/env python3
"""
DNOTI Gutachten Updater - Verbesserte Version
Automatisches Scraping und Hinzufügen neuer Gutachten zur Vektordatenbank
"""

import requests
from bs4 import BeautifulSoup
import time
import hashlib
import os
import json
import logging
from urllib.parse import urljoin
from typing import Dict, List, Set, Optional
from dataclasses import dataclass

# ========== KONFIGURATION ==========
@dataclass
class Config:
    """Konfiguration für den Gutachten-Updater"""
    BASE_URL: str = "https://www.dnoti.de/gutachten/"
    INTERVAL: int = 3600  # Scan-Intervall in Sekunden
    DB_PATH: str = "database"  # Pfad zur Vektordatenbank
    STATE_FILE: str = "scanned_urls.json"  # Zustandsdatei
    MAX_PAGES: int = 5  # Anzahl zu scannender Seiten
    
    # ChromaDB Einstellungen (optional - für lokale Speicherung)
    COLLECTION_NAME: str = "dnoti_gutachten"
    EMBEDDING_MODEL: str = "all-MiniLM-L6-v2"
    
    # Request Einstellungen
    USER_AGENT: str = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
    ACCEPT_LANGUAGE: str = "de-DE,de;q=0.9,en;q=0.8"
    REQUEST_TIMEOUT: int = 15
    REQUEST_DELAY: float = 0.5
    
    # CSS Selektoren (müssen angepasst werden nach Website-Analyse)
    LINK_SELECTOR: str = "a[href*='/gutachten/']"
    TITLE_SELECTOR: str = "h1, .title, .headline"
    CONTENT_SELECTOR: str = ".content, .main-content, article"
    AKTENZEICHEN_SELECTOR: str = "*:contains('Aktenzeichen')"

config = Config()

# Logging konfigurieren
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('gutachten_updater.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# ========== DATENSTRUKTUREN ==========
@dataclass
class GutachtenData:
    """Datenstruktur für ein Gutachten"""
    title: str
    aktenzeichen: str
    content: str
    url: str
    scraped_date: str

class URLTracker:
    """Verwaltet bereits gescannte URLs"""
    
    def __init__(self, state_file: str):
        self.state_file = state_file
        self._urls: Set[str] = self._load_urls()
    
    def _load_urls(self) -> Set[str]:
        """Lädt URLs aus der Zustandsdatei"""
        if not os.path.exists(self.state_file):
            return set()
        
        try:
            with open(self.state_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                return set(data.get("urls", []))
        except (json.JSONDecodeError, KeyError, IOError) as e:
            logger.warning(f"Fehler beim Laden der URLs: {e}")
            return set()
    
    def is_scanned(self, url: str) -> bool:
        """Prüft ob URL bereits gescannt wurde"""
        return url in self._urls
    
    def add_url(self, url: str) -> None:
        """Fügt URL hinzu und speichert"""
        self._urls.add(url)
        self._save_urls()
    
    def _save_urls(self) -> None:
        """Speichert URLs in Datei"""
        try:
            os.makedirs(os.path.dirname(self.state_file) if os.path.dirname(self.state_file) else '.', exist_ok=True)
            with open(self.state_file, 'w', encoding='utf-8') as f:
                json.dump({
                    "urls": list(self._urls),
                    "last_updated": time.strftime('%Y-%m-%d %H:%M:%S')
                }, f, indent=2, ensure_ascii=False)
        except IOError as e:
            logger.error(f"Fehler beim Speichern der URLs: {e}")

class DNotiScraper:
    """Web Scraper für DNOTI Gutachten"""
    
    def __init__(self, config: Config):
        self.config = config
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': config.USER_AGENT,
            'Accept-Language': config.ACCEPT_LANGUAGE,
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8'
        })
        self.url_tracker = URLTracker(config.STATE_FILE)
    
    def get_page_urls(self, page: int) -> List[str]:
        """Extrahiert Gutachten-URLs von einer Listenseite"""
        params = {"tx_dnotionlineplusapi_expertises[page]": page}
        
        try:
            response = self.session.get(
                self.config.BASE_URL, 
                params=params, 
                timeout=self.config.REQUEST_TIMEOUT
            )
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'html.parser')
            links = soup.select(self.config.LINK_SELECTOR)
            
            urls = []
            for link in links:
                href = link.get('href')
                if href:
                    full_url = urljoin(self.config.BASE_URL, href)
                    urls.append(full_url)
            
            logger.info(f"Seite {page}: {len(urls)} URLs gefunden")
            return urls
            
        except requests.RequestException as e:
            logger.error(f"Fehler beim Laden von Seite {page}: {e}")
            return []
    
    def extract_gutachten(self, url: str) -> Optional[GutachtenData]:
        """Extrahiert Gutachten-Daten von einer Detail-URL"""
        try:
            response = self.session.get(url, timeout=self.config.REQUEST_TIMEOUT)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Titel extrahieren
            title_elem = soup.select_one(self.config.TITLE_SELECTOR)
            title = title_elem.get_text(strip=True) if title_elem else "Ohne Titel"
            
            # Aktenzeichen extrahieren
            aktenzeichen = self._extract_aktenzeichen(soup)
            
            # Hauptinhalt extrahieren
            content = self._extract_content(soup)
            
            if not content.strip():
                logger.warning(f"Kein Inhalt gefunden: {url}")
                return None
            
            return GutachtenData(
                title=title,
                aktenzeichen=aktenzeichen,
                content=content,
                url=url,
                scraped_date=time.strftime('%Y-%m-%d %H:%M:%S')
            )
            
        except requests.RequestException as e:
            logger.error(f"Fehler beim Scrapen von {url}: {e}")
            return None
    
    def _extract_aktenzeichen(self, soup: BeautifulSoup) -> str:
        """Extrahiert Aktenzeichen"""
        # Suche nach Text der "Aktenzeichen" enthält
        for elem in soup.find_all(text=lambda text: text and 'Aktenzeichen' in text):
            parent = elem.parent
            if parent:
                text = parent.get_text(strip=True)
                # Extrahiere Text nach "Aktenzeichen:"
                if ':' in text:
                    return text.split(':', 1)[1].strip()
        return ""
    
    def _extract_content(self, soup: BeautifulSoup) -> str:
        """Extrahiert Hauptinhalt"""
        content_div = soup.select_one(self.config.CONTENT_SELECTOR)
        if not content_div:
            # Fallback: Versuche alle Paragraphen zu finden
            paragraphs = soup.find_all('p')
            return '\n'.join([p.get_text(strip=True) for p in paragraphs if p.get_text(strip=True)])
        
        # Entferne Navigation, Werbung etc.
        for unwanted in content_div(['nav', 'aside', '.advertisement', '.navigation']):
            unwanted.decompose()
        
        # Extrahiere Text von Paragraphen
        paragraphs = content_div.find_all(['p', 'div'])
        content_parts = []
        for p in paragraphs:
            text = p.get_text(strip=True)
            if text and len(text) > 20:  # Filtere sehr kurze Texte
                content_parts.append(text)
        
        return '\n'.join(content_parts)

class SimpleStorage:
    """Einfache JSON-basierte Speicherung als ChromaDB Alternative"""
    
    def __init__(self, db_path: str):
        self.db_path = db_path
        self.data_file = os.path.join(db_path, "gutachten_data.json")
        os.makedirs(db_path, exist_ok=True)
        self._data = self._load_data()
    
    def _load_data(self) -> Dict:
        """Lädt existierende Daten"""
        if os.path.exists(self.data_file):
            try:
                with open(self.data_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except (json.JSONDecodeError, IOError):
                return {"gutachten": [], "last_updated": ""}
        return {"gutachten": [], "last_updated": ""}
    
    def _save_data(self) -> None:
        """Speichert Daten"""
        try:
            with open(self.data_file, 'w', encoding='utf-8') as f:
                json.dump(self._data, f, indent=2, ensure_ascii=False)
        except IOError as e:
            logger.error(f"Fehler beim Speichern: {e}")
    
    def add_gutachten(self, gutachten: GutachtenData) -> bool:
        """Fügt Gutachten hinzu wenn noch nicht vorhanden"""
        # Generiere eindeutige ID
        unique_id = hashlib.sha256(
            f"{gutachten.url}_{gutachten.aktenzeichen}".encode()
        ).hexdigest()[:20]
        
        # Prüfe Duplikate
        for existing in self._data["gutachten"]:
            if existing.get("id") == unique_id:
                return False
        
        # Füge hinzu
        gutachten_dict = {
            "id": unique_id,
            "title": gutachten.title,
            "aktenzeichen": gutachten.aktenzeichen,
            "content": gutachten.content,
            "url": gutachten.url,
            "scraped_date": gutachten.scraped_date
        }
        
        self._data["gutachten"].append(gutachten_dict)
        self._data["last_updated"] = time.strftime('%Y-%m-%d %H:%M:%S')
        self._save_data()
        return True
    
    def get_existing_urls(self) -> Set[str]:
        """Gibt alle existierenden URLs zurück"""
        return {item["url"] for item in self._data["gutachten"]}
    
    def get_stats(self) -> Dict:
        """Gibt Statistiken zurück"""
        return {
            "total_gutachten": len(self._data["gutachten"]),
            "last_updated": self._data.get("last_updated", "Nie")
        }

def validate_config(config: Config) -> List[str]:
    """Validiert die Konfiguration"""
    errors = []
    
    if not config.BASE_URL:
        errors.append("BASE_URL ist nicht gesetzt")
    
    if not config.STATE_FILE:
        errors.append("STATE_FILE ist nicht gesetzt")
    
    if config.MAX_PAGES < 1:
        errors.append("MAX_PAGES muss mindestens 1 sein")
    
    return errors

def main():
    """Hauptfunktion"""
    logger.info("="*60)
    logger.info("DNOTI Gutachten Updater gestartet")
    
    # Konfiguration validieren
    config_errors = validate_config(config)
    if config_errors:
        logger.error("Konfigurationsfehler:")
        for error in config_errors:
            logger.error(f"  - {error}")
        return
    
    # Komponenten initialisieren
    scraper = DNotiScraper(config)
    storage = SimpleStorage(config.DB_PATH)
    
    logger.info(f"Datenbank: {config.DB_PATH}")
    logger.info(f"Scan-Intervall: {config.INTERVAL//60} Minuten")
    
    stats = storage.get_stats()
    logger.info(f"Aktuelle DB: {stats['total_gutachten']} Gutachten")
    
    try:
        while True:
            start_time = time.time()
            new_count = scan_for_updates(scraper, storage)
            
            if new_count > 0:
                logger.info(f"✅ {new_count} neue Gutachten hinzugefügt")
            else:
                logger.info("ℹ️  Keine neuen Gutachten gefunden")
            
            # Warte bis zum nächsten Scan
            elapsed = time.time() - start_time
            sleep_time = max(60, config.INTERVAL - elapsed)  # Mindestens 1 Minute warten
            
            logger.info(f"⏰ Nächster Scan in {sleep_time//60:.0f} Minuten")
            time.sleep(sleep_time)
            
    except KeyboardInterrupt:
        logger.info("👋 Updater gestoppt")
    except Exception as e:
        logger.error(f"❌ Unerwarteter Fehler: {e}")

def scan_for_updates(scraper: DNotiScraper, storage: SimpleStorage) -> int:
    """Führt einen Scan-Durchlauf durch"""
    logger.info("🔍 Starte Scan nach neuen Gutachten...")
    new_items_count = 0
    
    for page in range(1, config.MAX_PAGES + 1):
        logger.info(f"📄 Scanne Seite {page}...")
        
        # URLs von Listenseite holen
        page_urls = scraper.get_page_urls(page)
        if not page_urls:
            logger.warning(f"Keine URLs auf Seite {page} gefunden")
            continue
        
        # Jede URL verarbeiten
        for url in page_urls:
            if scraper.url_tracker.is_scanned(url):
                continue
            
            logger.info(f"📖 Verarbeite: {url}")
            
            # Gutachten extrahieren
            gutachten = scraper.extract_gutachten(url)
            if gutachten:
                # In Datenbank speichern
                if storage.add_gutachten(gutachten):
                    new_items_count += 1
                    logger.info(f"✅ Neu hinzugefügt: {gutachten.title[:50]}...")
                else:
                    logger.info(f"ℹ️  Bereits vorhanden: {gutachten.title[:50]}...")
            
            # URL als verarbeitet markieren
            scraper.url_tracker.add_url(url)
            
            # Rate limiting
            time.sleep(config.REQUEST_DELAY)
    
    logger.info(f"📊 Scan abgeschlossen. Neue Gutachten: {new_items_count}")
    return new_items_count

if __name__ == "__main__":
    main()
