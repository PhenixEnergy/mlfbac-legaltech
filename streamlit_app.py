#!/usr/bin/env python3
"""
Streamlit Frontend für Legal Tech Semantic Search
Benutzerfreundliche Oberfläche für Rechtsgutachten-Suche und -Analyse
"""

import streamlit as st

# Fallback imports für bessere Fehlerbehandlung
try:
    import requests
except ImportError:
    st.error("requests library not installed. Please run: pip install requests")
    st.stop()

try:
    import pandas as pd
except ImportError:
    st.warning("pandas not available - some features may be limited")
    pd = None

from datetime import datetime
from typing import Dict, List, Optional
import time
import html
import json

# Konfiguration
API_BASE_URL = "http://localhost:8000"
PAGE_CONFIG = {
    "page_title": "Legal Tech Semantic Search",
    "page_icon": "⚖️",
    "layout": "wide",
    "initial_sidebar_state": "expanded"
}

def init_streamlit():
    """Initialisiert Streamlit-Konfiguration."""
    st.set_page_config(**PAGE_CONFIG)
    
    # Custom CSS
    st.markdown("""
    <style>
    .main-header {
        font-size: 2.5rem;
        color: #1e3a8a;
        text-align: center;
        margin-bottom: 2rem;
        padding: 1rem;
        background: linear-gradient(90deg, #f0f9ff 0%, #dbeafe 100%);
        border-radius: 10px;
    }
    .search-box {
        padding: 1rem;
        border-radius: 10px;
        background-color: #f8fafc;
        margin: 1rem 0;
    }
    .result-card {
        padding: 1rem;
        border-left: 4px solid #3b82f6;
        background-color: #ffffff;
        border: 1px solid #e2e8f0;
        margin: 0.5rem 0;
        border-radius: 5px;
        box-shadow: 0 1px 3px rgba(0,0,0,0.1);
    }
    .result-card h4 {
        color: #1e293b !important;
        margin-bottom: 0.5rem;
    }
    .result-card p {
        color: #374151 !important;
        margin: 0.25rem 0;
    }
    .result-card strong {
        color: #1f2937 !important;
    }
    .metric-card {
        background-color: #ffffff;
        padding: 1rem;
        border-radius: 10px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        border: 1px solid #e2e8f0;
    }
    
    /* Stelle sicher, dass alle Texte gut lesbar sind */
    .stMarkdown, .stText {
        color: #1f2937 !important;
    }
    
    /* Fix für Streamlit Container */
    div[data-testid="stContainer"] {
        background-color: transparent;
    }
    
    /* Bessere Kontraste für alle Textelemente */
    h1, h2, h3, h4, h5, h6 {
        color: #1e293b !important;
    }
    
    p {
        color: #374151 !important;
    }
    
    /* Expander Styling */
    .streamlit-expander {
        background-color: #ffffff !important;
        border: 1px solid #e2e8f0 !important;
    }
    
    .streamlit-expander > div > div {
        color: #1f2937 !important;
        background-color: #ffffff !important;
    }
    
    /* Überschreibe alle Streamlit Text-Farben in Expandern */
    .streamlit-expander * {
        color: #1f2937 !important;
    }
    
    /* JSON Display Styling */
    .stJson {
        background-color: #ffffff !important;
        color: #1f2937 !important;
    }
    
    /* Starke Regeln für alle Text-Container */
    div[data-testid="stExpander"] * {
        color: #1f2937 !important;
        background-color: #ffffff !important;
    }
    </style>
    """, unsafe_allow_html=True)

def check_api_connection() -> bool:
    """Prüft Verbindung zur API."""
    try:
        response = requests.get(f"{API_BASE_URL}/admin/health", timeout=5)
        return response.status_code == 200
    except:
        return False

def search_documents(query: str, search_type: str = "semantic", limit: int = 10, 
                    similarity_threshold: float = 0.1, filters: str = None) -> Dict:
    """Führt Dokumentensuche über API durch."""
    try:
        data = {
            "query": query,
            "search_type": search_type,
            "limit": limit,
            "similarity_threshold": similarity_threshold
        }
        
        # Filter hinzufügen falls vorhanden
        if filters:
            try:
                filter_dict = json.loads(filters)
                data.update(filter_dict)
            except json.JSONDecodeError:
                pass  # Ignoriere ungültige JSON-Filter
        
        response = requests.post(f"{API_BASE_URL}/search/semantic", json=data, timeout=10)
        if response.status_code == 200:
            return response.json()
        else:
            return {"error": f"API Error: {response.status_code}"}
    except Exception as e:
        return {"error": f"Connection Error: {str(e)}"}

def format_gutachten_text(text: str) -> str:
    """Formatiert Gutachtentext für bessere Lesbarkeit mit erhaltener Struktur."""
    lines = text.split('\n')
    formatted_lines = []
    
    for line in lines:
        line_stripped = line.strip()
        
        # Leere Zeilen werden zu Absätzen
        if not line_stripped:
            formatted_lines.append('<br>')
            continue
        
        # Erkenne verschiedene Arten von Überschriften
        if any(line_stripped.startswith(prefix) for prefix in [
            'Gutachten Nr.', 'Rechtsbezug:', 'Normen:', 'Sachverhalt:', 
            'Rechtliche Bewertung:', 'Fazit:', 'I.', 'II.', 'III.', 'IV.',
            'A.', 'B.', 'C.', 'D.', '1.', '2.', '3.', '4.', '5.'
        ]):
            formatted_lines.append(f'<h5 style="color: #1e40af !important; margin: 1.5rem 0 0.5rem 0; font-weight: 600; font-size: 16px !important;">{html.escape(line_stripped)}</h5>')
        
        # Erkenne Listen und Aufzählungen
        elif line_stripped.startswith(('a)', 'b)', 'c)', 'd)', 'e)', '- ', '• ', '*')):
            formatted_lines.append(f'<p style="color: #374151 !important; margin: 0.3rem 0 0.3rem 1.5rem; line-height: 1.6; font-size: 14px;">{html.escape(line_stripped)}</p>')
        
        # Erkenne eingerückte Texte (oft wichtige Punkte)
        elif line.startswith('    ') or line.startswith('\t'):
            formatted_lines.append(f'<p style="color: #374151 !important; margin: 0.3rem 0 0.3rem 2rem; line-height: 1.6; font-size: 14px; font-style: italic;">{html.escape(line_stripped)}</p>')
        
        # Normaler Absatz
        else:
            formatted_lines.append(f'<p style="color: #374151 !important; margin: 0.8rem 0; line-height: 1.6; font-size: 14px;">{html.escape(line_stripped)}</p>')
    
    return '\n'.join(formatted_lines)

def render_search_results(results: Dict):
    """Rendert Suchergebnisse mit verbesserter Textformatierung."""
    
    if "error" in results:
        st.error(f"Fehler bei der Suche: {results['error']}")
        return
    
    if results.get("total_results", 0) == 0:
        st.warning("Keine Ergebnisse gefunden.")
        return
    
    st.success(f"**{results['total_results']} Ergebnisse** gefunden in {results.get('search_time_ms', 0):.0f}ms")
      def extract_gutachten_info(result: Dict) -> Dict[str, str]:
        """Extrahiert Gutachten-Informationen aus API-Result"""
        info = {}
        
        # Versuche Metadaten aus der API-Antwort zu extrahieren
        metadata = result.get("metadata", {})
        
        # 1. Gutachten-Nummer aus source_gutachten_id
        source_id = metadata.get("source_gutachten_id", "")
        if source_id:
            info['gutachten_nummer'] = f"Gutachten Nr. {source_id}"
        else:
            info['gutachten_nummer'] = "N/A"
        
        # 2. Rechtsbezug - meist "National" bei DNOTI-Gutachten
        info['rechtsbezug'] = "National"  # Default für DNOTI
        
        # 3. Normen aus legal_norms
        legal_norms = metadata.get("legal_norms", [])
        if legal_norms and isinstance(legal_norms, list) and len(legal_norms) > 0:
            info['normen'] = "; ".join(legal_norms[:5])  # Max 5 Normen anzeigen
        else:
            # Fallback: Versuche aus Content zu extrahieren (für alte Daten)
            content = result.get("content", "")
            lines = content.split('\n')
            for line in lines[:10]:  # Erste 10 Zeilen durchsuchen
                if line.startswith('Normen:'):
                    normen = line.replace('Normen:', '').strip()
                    info['normen'] = normen if normen else 'Keine spezifischen Normen angegeben'
                    break
            else:
                info['normen'] = 'Keine spezifischen Normen angegeben'
        
        return info
      # Ergebnisse anzeigen
    for i, result in enumerate(results.get("results", []), 1):
        with st.container():
            # Metadaten direkt aus API-Result extrahieren
            gutachten_info = extract_gutachten_info(result)
            
            # Metadaten-Card
            st.markdown(f"""
            <div class="result-card">
                <h4 style="color: #1e293b !important;">📄 Ergebnis {i} (Relevanz: {result.get('similarity_score', 0):.2f})</h4>
                <p style="color: #374151 !important;"><strong style="color: #1f2937 !important;">Gutachten:</strong> {gutachten_info.get('gutachten_nummer', 'N/A')}</p>
                <p style="color: #374151 !important;"><strong style="color: #1f2937 !important;">Rechtsbezug:</strong> {gutachten_info.get('rechtsbezug', 'N/A')}</p>
                <p style="color: #374151 !important;"><strong style="color: #1f2937 !important;">Normen:</strong> {gutachten_info.get('normen', 'N/A')}</p>
            </div>
            """, unsafe_allow_html=True)
              # Content-Text für Anzeige extrahieren
            content = result.get("content", result.get("text", ""))
            
            # Formatierter Text anzeigen
            formatted_content = format_gutachten_text(content)
            
            if len(content) > 500:
                with st.expander(f"📄 Text anzeigen ({len(content)} Zeichen)"):
                    st.markdown(f"""
                    <div style="
                        background-color: #ffffff; 
                        padding: 2rem; 
                        border-radius: 8px; 
                        border: 2px solid #3b82f6; 
                        margin: 1rem 0; 
                        box-shadow: 0 4px 12px rgba(0,0,0,0.1);
                        max-height: 70vh; 
                        overflow-y: auto;
                        font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Roboto', sans-serif;
                    ">
                        {formatted_content}
                    </div>
                    """, unsafe_allow_html=True)
            else:
                st.markdown(f"""
                <div style="
                    background-color: #ffffff; 
                    padding: 2rem; 
                    border-radius: 8px; 
                    border: 2px solid #3b82f6; 
                    margin: 1rem 0; 
                    box-shadow: 0 4px 12px rgba(0,0,0,0.1);
                    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Roboto', sans-serif;
                ">
                    {formatted_content}
                </div>
                """, unsafe_allow_html=True)
              # Metadaten anzeigen
            api_metadata = result.get("metadata", {})
            if api_metadata:
                with st.expander("🔍 Detaillierte Metadaten"):
                    # Strukturierte Anzeige der wichtigsten Metadaten
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        st.write("**Chunk-Informationen:**")
                        st.write(f"• Chunk-ID: `{api_metadata.get('chunk_id', 'N/A')}`")
                        st.write(f"• Abschnittstyp: {api_metadata.get('section_type', 'N/A')}")
                        st.write(f"• Token-Anzahl: {api_metadata.get('token_count', 'N/A')}")
                        
                    with col2:
                        st.write("**Bewertungen:**")
                        st.write(f"• Ähnlichkeit: {api_metadata.get('semantic_score', result.get('similarity_score', 0)):.3f}")
                        st.write(f"• Relevanz: {api_metadata.get('relevance_score', 0):.3f}")
                    
                    # Keywords anzeigen
                    keywords = api_metadata.get('keywords', [])
                    if keywords:
                        st.write("**Schlüsselwörter:**")
                        st.write(", ".join(keywords[:10]))  # Erste 10 Keywords
                    
                    # Legal Norms anzeigen
                    legal_norms = api_metadata.get('legal_norms', [])
                    if legal_norms:
                        st.write("**Rechtsnormen:**")
                        st.write(", ".join(legal_norms))
                    
                    # Vollständige Metadaten als JSON (für Debugging)
                    with st.expander("🔧 Vollständige Metadaten (JSON)"):
                        st.json(api_metadata)
            
            st.divider()

def ask_question(question: str, context_limit: int = 5) -> Dict:
    """Stellt Frage über QA-System."""
    try:
        data = {
            "question": question,
            "context_limit": context_limit
        }
        response = requests.post(f"{API_BASE_URL}/qa/answer", json=data, timeout=15)
        if response.status_code == 200:
            return response.json()
        else:
            return {"error": f"API Error: {response.status_code}"}
    except Exception as e:
        return {"error": f"Connection Error: {str(e)}"}

def render_qa_result(result: Dict):
    """Rendert QA-Ergebnis."""
    if "error" in result:
        st.error(f"Fehler bei der Frage: {result['error']}")
        return
    
    # Antwort anzeigen
    st.markdown("### 🤖 Antwort")
    answer = result.get("answer", "Keine Antwort verfügbar.")
    st.write(answer)
    
    # Kontext anzeigen
    context_chunks = result.get("context_chunks", [])
    if context_chunks:
        st.markdown("### 📚 Verwendete Quellen")
        for i, chunk in enumerate(context_chunks, 1):
            with st.expander(f"Quelle {i} - {chunk.get('gutachten_id', 'N/A')}"):
                st.write(chunk.get("text", ""))
                if "metadata" in chunk:
                    st.caption(f"Relevanz: {chunk.get('similarity_score', 0):.2f}")

def get_admin_stats() -> Dict:
    """Ruft Admin-Statistiken ab."""
    try:
        response = requests.get(f"{API_BASE_URL}/admin/stats", timeout=10)
        if response.status_code == 200:
            return response.json()
        else:
            return {"error": f"API Error: {response.status_code}"}
    except Exception as e:
        return {"error": f"Connection Error: {str(e)}"}

def render_search_page():
    """Rendert die Suchseite."""
    st.markdown("## 🔍 Semantische Suche")
    st.markdown("Durchsuchen Sie Rechtsgutachten mit KI-gestützter semantischer Suche.")
    
    # Suchoptionen
    col1, col2 = st.columns([3, 1])
    
    with col1:
        query = st.text_input(
            "Suchbegriff",
            placeholder="z.B. Schadensersatz, Haftung, Vertragsrecht...",
            help="Geben Sie einen Suchbegriff oder eine Frage ein"
        )
    
    with col2:
        search_type = st.selectbox(
            "Suchtyp",
            ["semantic", "keyword", "hybrid"],
            help="Semantisch: KI-basiert, Keyword: Exakte Begriffe, Hybrid: Kombination"
        )
    
    # Erweiterte Optionen
    with st.expander("🔧 Erweiterte Suchoptionen"):
        col1, col2, col3 = st.columns(3)
        
        with col1:
            limit = st.slider("Max. Ergebnisse", 1, 50, 10)
        
        with col2:
            min_similarity = st.slider("Min. Ähnlichkeit", 0.0, 1.0, 0.5, 0.1)
        
        with col3:
            search_filters = st.text_input("Filter (JSON)", placeholder='{"legal_area": "civil"}')
      # Suche ausführen
    if st.button("🔍 Suchen", type="primary", use_container_width=True) and query:
        with st.spinner("Suche läuft..."):
            start_time = time.time()
            results = search_documents(
                query=query, 
                search_type=search_type, 
                limit=limit,
                similarity_threshold=min_similarity,
                filters=search_filters
            )
            search_time = (time.time() - start_time) * 1000
            
            # Suchzeit hinzufügen
            if "error" not in results:
                results["search_time_ms"] = search_time
            
            render_search_results(results)
    
    elif query == "":
        st.info("👆 Geben Sie einen Suchbegriff ein, um zu starten.")

def render_qa_page():
    """Rendert die Q&A-Seite."""
    st.markdown("## ❓ Fragen & Antworten")
    st.markdown("Stellen Sie Fragen zu Rechtsgutachten und erhalten Sie KI-gestützte Antworten.")
    
    question = st.text_area(
        "Ihre Frage",
        placeholder="z.B. Was sind die Voraussetzungen für Schadensersatz nach § 280 BGB?",
        help="Stellen Sie eine konkrete Rechtsfrage"
    )
    
    col1, col2 = st.columns([1, 4])
    with col1:
        context_limit = st.slider("Max. Quellen", 1, 10, 5)
    
    if st.button("❓ Frage stellen", type="primary", use_container_width=True) and question:
        with st.spinner("KI arbeitet..."):
            result = ask_question(question, context_limit)
            render_qa_result(result)

def render_admin_page():
    """Rendert Admin-Dashboard."""
    st.markdown("## 🛠️ System-Administration")
    
    # API-Status prüfen
    if check_api_connection():
        st.success("✅ API-Verbindung aktiv")
    else:
        st.error("❌ API nicht erreichbar")
        return
    
    # Statistiken abrufen
    with st.spinner("Lade Statistiken..."):
        stats = get_admin_stats()
        
        if "error" in stats:
            st.error(f"Fehler beim Laden der Statistiken: {stats['error']}")
            return
        
        # Metriken anzeigen
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Dokumente", stats.get("total_documents", "N/A"))
        
        with col2:
            st.metric("Textchunks", stats.get("total_chunks", "N/A"))
        
        with col3:
            st.metric("Vektordatenbank", f"{stats.get('vector_db_size_mb', 0):.1f} MB")
        
        with col4:
            st.metric("Letzte Aktualisierung", stats.get("last_updated", "N/A"))

def main():
    """Hauptfunktion der Streamlit-App."""
    init_streamlit()
    
    # Hauptnavigation
    st.markdown('<div class="main-header">⚖️ Legal Tech Semantic Search</div>', unsafe_allow_html=True)
    
    # Sidebar Navigation
    with st.sidebar:
        st.markdown("### 🧭 Navigation")
        page = st.radio(
            "Wählen Sie eine Seite:",
            ["🔍 Suche", "❓ Q&A", "🛠️ Admin"],
            key="navigation"
        )
        
        st.markdown("---")
        st.markdown("### ℹ️ System-Info")
        
        # API-Status in Sidebar
        if check_api_connection():
            st.success("API: Online")
        else:
            st.error("API: Offline")
        
        st.caption(f"Version: 1.0.0")
        st.caption(f"Build: {datetime.now().strftime('%Y-%m-%d')}")
    
    # Seiten-Routing
    if page == "🔍 Suche":
        render_search_page()
    elif page == "❓ Q&A":
        render_qa_page()
    elif page == "🛠️ Admin":
        render_admin_page()

if __name__ == "__main__":
    main()
