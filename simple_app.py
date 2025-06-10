#!/usr/bin/env python3
"""
Einfache DNOTI Legal Tech Anwendung
Vereinfachte Version ohne komplexe Templates
"""

import streamlit as st
import json
import re
from datetime import datetime
from typing import Dict, List
import os

# Einfache Konfiguration
st.set_page_config(
    page_title="DNOTI Legal Tech",
    page_icon="⚖️",
    layout="wide"
)

def search_documents_direct(query: str, top_k: int = 10) -> List[Dict]:
    """Direkte Suche in ChromaDB ohne API."""
    try:
        import chromadb
        from chromadb.utils import embedding_functions
        
        client = chromadb.PersistentClient(path="./chroma_db")
        
        # Embedding-Funktion
        embedding_fn = embedding_functions.SentenceTransformerEmbeddingFunction(
            model_name="sentence-transformers/all-MiniLM-L6-v2"
        )
        
        collection = client.get_collection("legal_documents", embedding_function=embedding_fn)
        
        results = collection.query(
            query_texts=[query],
            n_results=top_k
        )
        
        # Formatiere Ergebnisse
        formatted_results = []
        if results['documents'] and results['documents'][0]:
            for i, doc in enumerate(results['documents'][0]):
                similarity = 1.0 - results['distances'][0][i] if results['distances'] and results['distances'][0] else 0.0
                
                formatted_results.append({
                    'content': doc,
                    'similarity': similarity,
                    'metadata': results['metadatas'][0][i] if results['metadatas'] and results['metadatas'][0] else {}
                })
        
        return formatted_results
        
    except Exception as e:
        st.error(f"Datenbankfehler: {str(e)}")
        return []

def main():
    """Hauptfunktion der Anwendung."""
    
    # Header
    st.title("⚖️ DNOTI Legal Tech")
    st.subheader("KI-gestützte semantische Suche für Rechtsgutachten")
    
    # Sidebar
    with st.sidebar:
        st.header("🔧 Einstellungen")
        
        # Anzahl Ergebnisse
        top_k = st.slider("Anzahl Ergebnisse", 1, 20, 10)
        
        # Datenbank-Info
        st.header("📊 Datenbank")
        try:
            import chromadb
            client = chromadb.PersistentClient(path="./chroma_db")
            collection = client.get_collection("legal_documents")
            doc_count = collection.count()
            st.metric("Dokumente", f"{doc_count:,}")
        except Exception as e:
            st.error(f"DB-Fehler: {str(e)}")
    
    # Hauptbereich
    st.header("🔍 Semantische Suche")
    
    # Sucheingabe
    query = st.text_input(
        "Geben Sie Ihre Suchanfrage ein:",
        placeholder="z.B. Pflichtteilsrecht bei Immobilienübertragung"
    )
    
    # Beispielanfragen
    with st.expander("💡 Beispielanfragen"):
        examples = [
            "Haftung des Notars bei fehlerhafter Beurkundung",
            "Pflichtteilsrecht bei Immobilienübertragung", 
            "Vollmacht bei Grundstücksgeschäften",
            "Eheverträge und Güterstandsregelung",
            "Erbvertrag und gesetzliche Erbfolge"
        ]
        
        for i, example in enumerate(examples):
            if st.button(f"📝 {example}", key=f"ex_{i}"):
                st.session_state.query = example
                st.rerun()
    
    # Handle example selection
    if 'query' in st.session_state:
        query = st.session_state.query
        del st.session_state.query
    
    # Suche durchführen
    if query:
        with st.spinner("🔍 Suche läuft..."):
            results = search_documents_direct(query, top_k)
        
        if results:
            st.success(f"📊 {len(results)} Ergebnisse gefunden")
            
            # Ergebnisse anzeigen
            for i, result in enumerate(results):
                with st.container():
                    st.markdown(f"### 📄 Ergebnis {i + 1}")
                    
                    # Ähnlichkeit
                    similarity = result.get('similarity', 0.0)
                    st.markdown(f"**Relevanz:** {similarity:.1%}")
                    
                    # Inhalt
                    content = result.get('content', '')
                    preview = content[:500] + "..." if len(content) > 500 else content
                    st.markdown("**Inhalt:**")
                    st.text_area("", preview, height=100, key=f"content_{i}", disabled=True)
                    
                    # Volltext
                    with st.expander("Vollständigen Text anzeigen"):
                        st.text(content)
                    
                    st.divider()
        else:
            st.warning("❌ Keine Ergebnisse gefunden")
            st.info("""
            **Tipps:**
            - Verwenden Sie juristische Fachbegriffe
            - Probieren Sie verschiedene Formulierungen
            - Nutzen Sie die Beispielanfragen
            """)
    
    # Footer
    st.markdown("---")
    st.markdown("🏛️ **DNOTI Legal Tech** | 🤖 KI-gestützte Rechtsdatenbank")

if __name__ == "__main__":
    main()
