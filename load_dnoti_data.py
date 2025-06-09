#!/usr/bin/env python3
"""
Simple script to load DNOTI legal documents into ChromaDB
"""

import json
import logging
import sys
from pathlib import Path
from typing import List, Dict, Any

# Add src to path
sys.path.append(str(Path(__file__).parent / "src"))

from src.vectordb.chroma_client import ChromaDBClient

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def load_dnoti_documents(json_file_path: str, limit: int = None) -> List[Dict[str, Any]]:
    """Load DNOTI documents from JSON file"""
    logger.info(f"Loading documents from {json_file_path}")
    
    with open(json_file_path, 'r', encoding='utf-8') as f:
        documents = json.load(f)
    
    if limit:
        documents = documents[:limit]
        logger.info(f"Limited to {limit} documents")
    
    logger.info(f"Loaded {len(documents)} documents")
    return documents

def process_document_for_embedding(doc: Dict[str, Any]) -> Dict[str, Any]:
    """Process a document for ChromaDB storage"""
    # Extract key information
    doc_id = str(doc.get('id', ''))
    gutachten_nr = doc.get('gutachten_nummer', '')
    erscheinungsdatum = doc.get('erscheinungsdatum', '')
    rechtsbezug = doc.get('rechtsbezug', '')
    normen = doc.get('normen', '') or ''
    text = doc.get('text', '')
    url = doc.get('url', '')
    
    # Create a comprehensive text for embedding that includes metadata
    full_text = f"""Gutachten Nr. {gutachten_nr} vom {erscheinungsdatum}
Rechtsbezug: {rechtsbezug}
Normen: {normen}

{text}"""
    
    # Metadata for filtering and display
    metadata = {
        'gutachten_nummer': gutachten_nr,
        'erscheinungsdatum': erscheinungsdatum,
        'rechtsbezug': rechtsbezug,
        'normen': normen,
        'url': url,
        'source': 'dnoti',
        'doc_type': 'legal_opinion'
    }
    
    return {
        'id': f"dnoti_{doc_id}",
        'text': full_text,
        'metadata': metadata
    }

def main():
    try:
        # Paths
        json_file = Path("Database/Original/dnoti_all.json")
        config_file = Path("config/database.yaml")
        
        # Check if files exist
        if not json_file.exists():
            logger.error(f"DNOTI data file not found: {json_file}")
            return
        
        # Initialize ChromaDB client
        logger.info("Initializing ChromaDB client...")
        chroma_client = ChromaDBClient(config_file)
        
        # Create collection (reset if exists)
        collection_name = "dnoti_legal_documents"
        logger.info(f"Creating collection: {collection_name}")
        collection = chroma_client.create_collection(collection_name, reset_if_exists=True)
          # Load documents (load 1000 for better testing)
        documents = load_dnoti_documents(str(json_file), limit=1000)
        
        # Process documents for embedding
        logger.info("Processing documents for embedding...")
        processed_docs = []
        for doc in documents:
            try:
                processed_doc = process_document_for_embedding(doc)
                processed_docs.append(processed_doc)
            except Exception as e:
                logger.error(f"Error processing document {doc.get('id', 'unknown')}: {e}")
                continue
        
        logger.info(f"Processed {len(processed_docs)} documents")
        
        # Add documents to collection in batches
        batch_size = 10
        total_added = 0
        
        for i in range(0, len(processed_docs), batch_size):
            batch = processed_docs[i:i + batch_size]
            
            # Prepare data for ChromaDB
            ids = [doc['id'] for doc in batch]
            documents_text = [doc['text'] for doc in batch]
            metadatas = [doc['metadata'] for doc in batch]
            
            logger.info(f"Adding batch {i//batch_size + 1} ({len(batch)} documents)")
            
            try:
                collection.add(
                    ids=ids,
                    documents=documents_text,
                    metadatas=metadatas
                )
                total_added += len(batch)
                logger.info(f"Successfully added {len(batch)} documents to collection")
            except Exception as e:
                logger.error(f"Error adding batch to collection: {e}")
                continue
        
        logger.info(f"Successfully loaded {total_added} documents into ChromaDB collection '{collection_name}'")
        
        # Test the collection
        logger.info("Testing collection with a sample query...")
        try:
            results = collection.query(
                query_texts=["Erbrecht Pflichtteil"],
                n_results=3
            )
            logger.info(f"Sample query returned {len(results['ids'][0])} results")
            for i, doc_id in enumerate(results['ids'][0]):
                metadata = results['metadatas'][0][i]
                logger.info(f"  - {doc_id}: {metadata.get('gutachten_nummer', 'N/A')} ({metadata.get('rechtsbezug', 'N/A')})")
        except Exception as e:
            logger.error(f"Error testing collection: {e}")
        
    except Exception as e:
        logger.error(f"Error in main: {e}")
        raise

if __name__ == "__main__":
    main()
