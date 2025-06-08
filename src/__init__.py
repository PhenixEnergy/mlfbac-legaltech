"""
DNOTI Legal Tech - Hauptpaket für semantische Suche

Dieses Paket stellt eine KI-gestützte semantische Suchmaschine für 
Rechtsgutachten des Deutschen Notarinstituts bereit.

Hauptkomponenten:
- Datenverarbeitung und Chunking
- Vektordatenbank (ChromaDB) Integration
- Semantische Suche
- LLM-Integration für Antwortgenerierung
- API-Schnittstellen (FastAPI + Streamlit)
"""

__version__ = "0.1.0-alpha"
__author__ = "MLFB-AC Legal Tech Team"
__email__ = "legaltech@example.com"

from pathlib import Path

# Projektverzeichnisse
PROJECT_ROOT = Path(__file__).parent.parent
CONFIG_DIR = PROJECT_ROOT / "config"
DATA_DIR = PROJECT_ROOT / "data"
DATABASE_DIR = PROJECT_ROOT / "Database"

# Logging Setup
import logging
from pathlib import Path

def setup_logging(log_level: str = "INFO") -> None:
    """Setup grundlegendes Logging für das Projekt."""
    log_dir = DATA_DIR / "logs"
    log_dir.mkdir(exist_ok=True)
    
    logging.basicConfig(
        level=getattr(logging, log_level.upper()),
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[
            logging.FileHandler(log_dir / "legaltech.log"),
            logging.StreamHandler()
        ]
    )

# Setup beim Import
setup_logging()
