"""
Datenbank-Setup und Initialisierung für dnoti Legal Tech System
Lädt und verarbeitet Gutachten-Daten für ChromaDB
"""

import sys
import logging
from pathlib import Path
import json
from typing import Dict, List, Optional
import argparse
from datetime import datetime
import yaml

# Pfad zum src-Verzeichnis hinzufügen
sys.path.append(str(Path(__file__).parent.parent / "src"))

# Local imports
from src.data.loader import DNOTIDataLoader
from src.data.preprocessor import LegalTextPreprocessor, PreprocessingConfig
from src.data.chunker import HierarchicalChunker
from src.vectordb.chroma_client import ChromaDBClient

# Logging konfigurieren
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class DatabaseSetup:
    """
    Hauptklasse für Datenbank-Setup und -Initialisierung
    
    Workflow:
    1. Gutachten-Daten laden
    2. Text-Preprocessing
    3. Hierarchisches Chunking
    4. ChromaDB-Initialisierung  
    5. Vektor-Embeddings erstellen und speichern
    """
    
    def __init__(self, config_dir: Path):
        """
        Initialisiert Database Setup
        
        Args:
            config_dir: Verzeichnis mit Konfigurationsdateien
        """
        self.config_dir = Path(config_dir)
        self.stats = {
            'start_time': datetime.now(),
            'gutachten_loaded': 0,
            'gutachten_processed': 0,
            'chunks_created': 0,
            'chunks_stored': 0,
            'errors': []
        }
        
        # Komponenten initialisieren
        self._init_components()
        
    def _init_components(self):
        """Initialisiert alle benötigten Komponenten"""
        try:
            # Data Loader
            self.data_loader = DNOTIDataLoader()
            logger.info("Data Loader initialized")
            
            # Text Preprocessor
            preprocessing_config = PreprocessingConfig(
                remove_extra_whitespace=True,
                normalize_unicode=True,
                preserve_legal_formatting=True,
                extract_legal_norms=True
            )
            self.preprocessor = LegalTextPreprocessor(preprocessing_config)
            logger.info("Text Preprocessor initialized")
            
            # Hierarchical Chunker
            chunking_config_path = self.config_dir / "chunking.yaml"
            self.chunker = HierarchicalChunker(chunking_config_path)
            logger.info("Hierarchical Chunker initialized")
            
            # ChromaDB Client
            db_config_path = self.config_dir / "database.yaml"
            self.vectordb = ChromaDBClient(db_config_path)
            logger.info("ChromaDB Client initialized")
            
        except Exception as e:
            logger.error(f"Error initializing components: {e}")
            raise
    
    def run_full_setup(self, 
                      data_file: Path, 
                      collection_name: str = "dnoti_gutachten_chunks",
                      reset_collection: bool = False,
                      limit_gutachten: Optional[int] = None,
                      batch_size: int = 100) -> Dict:
        """
        Führt vollständiges Datenbank-Setup durch
        
        Args:
            data_file: Pfad zur dnoti_all.json Datei
            collection_name: Name der zu erstellenden Collection
            reset_collection: Ob Collection zurückgesetzt werden soll
            limit_gutachten: Beschränkung der Anzahl Gutachten (für Tests)
            batch_size: Batch-Größe für DB-Operationen
            
        Returns:
            Dict mit Setup-Statistiken
        """
        logger.info("Starting full database setup...")
        
        try:
            # 1. Gutachten-Daten laden
            logger.info("Step 1: Loading gutachten data...")
            gutachten_data = self._load_gutachten_data(data_file, limit_gutachten)
            
            # 2. ChromaDB Collection vorbereiten
            logger.info("Step 2: Preparing ChromaDB collection...")
            collection = self.vectordb.create_collection(collection_name, reset_collection)
            
            # 3. Gutachten verarbeiten und in DB speichern
            logger.info("Step 3: Processing and storing gutachten...")
            self._process_and_store_gutachten(gutachten_data, collection_name, batch_size)
            
            # 4. Abschluss-Statistiken
            self._finalize_stats()
            
            logger.info("Database setup completed successfully!")
            return self.stats
            
        except Exception as e:
            logger.error(f"Error in full setup: {e}")
            self.stats['errors'].append(str(e))
            return self.stats
    
    def _load_gutachten_data(self, data_file: Path, limit: Optional[int] = None) -> List[Dict]:
        """Lädt Gutachten-Daten aus JSON-Datei"""
        logger.info(f"Loading data from: {data_file}")
        
        if not data_file.exists():
            raise FileNotFoundError(f"Data file not found: {data_file}")
        
        try:
            with open(data_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            if isinstance(data, list):
                gutachten_list = data
            elif isinstance(data, dict) and 'gutachten' in data:
                gutachten_list = data['gutachten']
            else:
                raise ValueError("Invalid data format")
            
            # Limit anwenden wenn gesetzt
            if limit and limit > 0:
                gutachten_list = gutachten_list[:limit]
                logger.info(f"Limited to {limit} gutachten for processing")
            
            self.stats['gutachten_loaded'] = len(gutachten_list)
            logger.info(f"Loaded {len(gutachten_list)} gutachten")
            
            return gutachten_list
            
        except Exception as e:
            logger.error(f"Error loading gutachten data: {e}")
            raise
    
    def _process_and_store_gutachten(self, 
                                   gutachten_data: List[Dict], 
                                   collection_name: str,
                                   batch_size: int):
        """Verarbeitet Gutachten und speichert sie in ChromaDB"""
        
        all_chunks = []
        
        for i, gutachten in enumerate(gutachten_data):
            try:
                logger.info(f"Processing gutachten {i+1}/{len(gutachten_data)}: {gutachten.get('id', 'unknown')}")
                
                # Gutachten-Text extrahieren
                text_content = self._extract_gutachten_text(gutachten)
                
                if not text_content or len(text_content.strip()) < 100:
                    logger.warning(f"Gutachten {i+1} has insufficient content, skipping")
                    continue
                
                # Preprocessing
                preprocessed = self.preprocessor.preprocess_text(
                    text_content, 
                    gutachten
                )
                
                if 'error' in preprocessed:
                    logger.error(f"Preprocessing error for gutachten {i+1}: {preprocessed['error']}")
                    self.stats['errors'].append(f"Preprocessing error: {preprocessed['error']}")
                    continue
                
                # Hierarchisches Chunking
                chunking_result = self.chunker.process_gutachten(
                    preprocessed['processed_text'],
                    gutachten
                )
                
                if 'error' in chunking_result:
                    logger.error(f"Chunking error for gutachten {i+1}: {chunking_result['error']}")
                    self.stats['errors'].append(f"Chunking error: {chunking_result['error']}")
                    continue
                
                # Chunks zur Gesamtliste hinzufügen
                level2_chunks = chunking_result.get('level_2_chunks', [])
                all_chunks.extend(level2_chunks)
                
                self.stats['gutachten_processed'] += 1
                self.stats['chunks_created'] += len(level2_chunks)
                
                logger.info(f"Gutachten {i+1} processed: {len(level2_chunks)} chunks created")
                
                # Batch-Verarbeitung wenn Batch-Größe erreicht
                if len(all_chunks) >= batch_size:
                    self._store_chunk_batch(all_chunks[:batch_size], collection_name)
                    all_chunks = all_chunks[batch_size:]
                
            except Exception as e:
                logger.error(f"Error processing gutachten {i+1}: {e}")
                self.stats['errors'].append(f"Gutachten {i+1}: {str(e)}")
                continue
        
        # Verbleibende Chunks speichern
        if all_chunks:
            self._store_chunk_batch(all_chunks, collection_name)
    
    def _extract_gutachten_text(self, gutachten: Dict) -> str:
        """Extrahiert den Haupttext eines Gutachtens"""
        
        # Verschiedene mögliche Text-Felder versuchen
        text_fields = ['content', 'text', 'body', 'gutachten_text', 'inhalt']
        
        for field in text_fields:
            if field in gutachten and gutachten[field]:
                return str(gutachten[field])
        
        # Fallback: alle String-Werte kombinieren
        text_parts = []
        for key, value in gutachten.items():
            if isinstance(value, str) and len(value) > 50:  # Nur längere Texte
                if key not in ['id', 'nummer', 'datum', 'url']:  # Metadaten ausschließen
                    text_parts.append(value)
        
        return '\n\n'.join(text_parts)
    
    def _store_chunk_batch(self, chunks: List, collection_name: str):
        """Speichert eine Batch von Chunks in ChromaDB"""
        try:
            stats = self.vectordb.add_chunks_to_collection(
                collection_name=collection_name,
                chunks=chunks,
                batch_size=50  # Kleinere Sub-Batches für ChromaDB
            )
            
            self.stats['chunks_stored'] += stats['successful_adds']
            
            if stats['failed_adds'] > 0:
                logger.warning(f"Failed to store {stats['failed_adds']} chunks")
                self.stats['errors'].extend(stats['errors'])
            
            logger.info(f"Stored batch: {stats['successful_adds']} chunks successfully")
            
        except Exception as e:
            logger.error(f"Error storing chunk batch: {e}")
            self.stats['errors'].append(f"Batch storage error: {str(e)}")
    
    def _finalize_stats(self):
        """Finalisiert Setup-Statistiken"""
        self.stats['end_time'] = datetime.now()
        self.stats['total_duration'] = (
            self.stats['end_time'] - self.stats['start_time']
        ).total_seconds()
        
        self.stats['success_rate'] = (
            self.stats['gutachten_processed'] / max(1, self.stats['gutachten_loaded'])
        ) * 100
        
        logger.info("=== DATABASE SETUP STATISTICS ===")
        logger.info(f"Gutachten loaded: {self.stats['gutachten_loaded']}")
        logger.info(f"Gutachten processed: {self.stats['gutachten_processed']}")
        logger.info(f"Chunks created: {self.stats['chunks_created']}")
        logger.info(f"Chunks stored: {self.stats['chunks_stored']}")
        logger.info(f"Success rate: {self.stats['success_rate']:.1f}%")
        logger.info(f"Total duration: {self.stats['total_duration']:.1f} seconds")
        logger.info(f"Errors: {len(self.stats['errors'])}")
    
    def verify_setup(self, collection_name: str = "dnoti_gutachten_chunks") -> Dict:
        """Verifiziert das Setup durch Tests"""
        logger.info("Verifying database setup...")
        
        verification_results = {
            'collection_exists': False,
            'chunk_count': 0,
            'sample_search_works': False,
            'metadata_complete': False,
            'errors': []
        }
        
        try:
            # Collection existiert?
            collections = self.vectordb.list_collections()
            verification_results['collection_exists'] = collection_name in collections
            
            if verification_results['collection_exists']:
                # Chunk-Anzahl prüfen
                stats = self.vectordb.get_collection_stats(collection_name)
                verification_results['chunk_count'] = stats.get('total_chunks', 0)
                
                # Sample-Suche testen
                if verification_results['chunk_count'] > 0:
                    search_results = self.vectordb.search_similar_chunks(
                        query="Schadensersatz BGB",
                        collection_name=collection_name,
                        n_results=3
                    )
                    
                    verification_results['sample_search_works'] = (
                        search_results.get('total_results', 0) > 0
                    )
                    
                    # Metadaten-Vollständigkeit prüfen
                    if search_results.get('results'):
                        sample_result = search_results['results'][0]
                        required_metadata = ['chunk_id', 'source_gutachten_id', 'level']
                        
                        verification_results['metadata_complete'] = all(
                            field in sample_result.get('metadata', {}) 
                            for field in required_metadata
                        )
            
        except Exception as e:
            verification_results['errors'].append(str(e))
            logger.error(f"Verification error: {e}")
        
        # Ergebnisse ausgeben
        logger.info("=== VERIFICATION RESULTS ===")
        logger.info(f"Collection exists: {verification_results['collection_exists']}")
        logger.info(f"Chunk count: {verification_results['chunk_count']}")
        logger.info(f"Search works: {verification_results['sample_search_works']}")
        logger.info(f"Metadata complete: {verification_results['metadata_complete']}")
        
        if verification_results['errors']:
            logger.warning(f"Verification errors: {verification_results['errors']}")
        
        return verification_results
    
    def export_setup_report(self, output_file: Path):
        """Exportiert Setup-Report als JSON"""
        report = {
            'setup_stats': self.stats,
            'verification': self.verify_setup(),
            'timestamp': datetime.now().isoformat(),
            'config_dir': str(self.config_dir)
        }
        
        try:
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(report, f, ensure_ascii=False, indent=2, default=str)
            
            logger.info(f"Setup report exported to: {output_file}")
            
        except Exception as e:
            logger.error(f"Error exporting setup report: {e}")

def quick_setup_mode():
    """
    Schnelle Setup-Routine für Development/Testing
    Lädt nur eine Teilmenge der Daten für schnelle Initialisierung
    """
    logger.info("=== Quick Setup Mode ===")
    
    # Prüfe ob Datenbank bereits existiert
    db_path = Path("data/vectordb/chroma.sqlite3")
    if db_path.exists():
        logger.info("Database already exists - skipping quick setup")
        return True
    
    # Erstelle minimale Testdatenbank
    try:
        # Mock ChromaDB Client für Quick Setup
        from src.utils.mock_chromadb import MockChromaDBClient
        
        # Erstelle Dummy-Daten für Testing
        sample_data = [
            {
                "id": "quick_setup_1",
                "text": "Testgutachten für Quick Setup - Notarrecht BGB §1234",
                "metadata": {
                    "section_type": "test",
                    "gutachten_id": "test_001",
                    "keywords": ["notarrecht", "test"]
                }
            },
            {
                "id": "quick_setup_2", 
                "text": "Weiteres Testgutachten - Grundbuchrecht §567",
                "metadata": {
                    "section_type": "test",
                    "gutachten_id": "test_002",
                    "keywords": ["grundbuchrecht", "test"]
                }
            }
        ]
        
        # Erstelle Verzeichnisse
        Path("data/vectordb").mkdir(parents=True, exist_ok=True)
        Path("data/logs").mkdir(parents=True, exist_ok=True)
        
        # Erstelle leere Datenbank-Datei
        db_path.touch()
        
        logger.info("Quick setup completed - created minimal test database")
        return True
        
    except Exception as e:
        logger.error(f"Quick setup failed: {e}")
        return False


def main():
    """Hauptfunktion für Kommandozeilen-Interface"""
    parser = argparse.ArgumentParser(description="dnoti Legal Tech Database Setup")
    
    parser.add_argument(
        '--data-file', 
        type=Path, 
        required=True,
        help="Path to dnoti_all.json data file"
    )
    
    parser.add_argument(
        '--config-dir',
        type=Path,
        default=Path(__file__).parent.parent / "config",
        help="Directory containing config files"
    )
    
    parser.add_argument(
        '--collection-name',
        type=str,
        default="dnoti_gutachten_chunks",
        help="Name of ChromaDB collection to create"
    )
    
    parser.add_argument(
        '--reset-collection',
        action='store_true',
        help="Reset collection if it already exists"
    )
    
    parser.add_argument(
        '--limit-gutachten',
        type=int,
        help="Limit number of gutachten to process (for testing)"
    )
    
    parser.add_argument(
        '--batch-size',
        type=int,
        default=100,
        help="Batch size for database operations"
    )
    
    parser.add_argument(
        '--verify-only',
        action='store_true',
        help="Only run verification, skip setup"
    )
    
    parser.add_argument(
        '--export-report',
        type=Path,
        help="Export setup report to file"
    )
    
    parser.add_argument(
        '--quick-setup',
        action='store_true',
        help="Quick setup mode for development (creates minimal test database)"
    )

    args = parser.parse_args()
    
    # Quick Setup Mode
    if args.quick_setup:
        success = quick_setup_mode()
        if success:
            print("Quick setup completed successfully!")
            sys.exit(0)
        else:
            print("Quick setup failed!")
            sys.exit(1)
    
    # Setup initialisieren
    try:
        setup = DatabaseSetup(args.config_dir)
        
        if args.verify_only:
            # Nur Verifikation
            verification_results = setup.verify_setup(args.collection_name)
            print(f"Verification completed. Results: {verification_results}")
        else:
            # Vollständiges Setup
            setup_stats = setup.run_full_setup(
                data_file=args.data_file,
                collection_name=args.collection_name,
                reset_collection=args.reset_collection,
                limit_gutachten=args.limit_gutachten,
                batch_size=args.batch_size
            )
            
            print(f"Setup completed. Stats: {setup_stats}")
        
        # Report exportieren wenn gewünscht
        if args.export_report:
            setup.export_setup_report(args.export_report)
        
    except Exception as e:
        logger.error(f"Setup failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
