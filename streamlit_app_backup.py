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
    }    .result-card {
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
    }    .metric-card {
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

def search_documents(query: str, search_type: str = "semantic", limit: int = 10) -> Dict:
    """Führt Dokumentensuche über API durch."""
    try:
        data = {
            "query": query,
            "search_type": search_type,
            "limit": limit
        }
        response = requests.post(f"{API_BASE_URL}/search/semantic", json=data, timeout=10)
        if response.status_code == 200:
            return response.json()
        else:
            return {"error": f"API Error: {response.status_code}"}
    except Exception as e:
        return {"error": f"Connection Error: {str(e)}"}

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

def render_search_results(results: Dict):
    """Rendert Suchergebnisse."""
    import html  # HTML-Escaping für sichere Anzeige
    
    if "error" in results:
        st.error(f"Fehler bei der Suche: {results['error']}")
        return
    
    if results.get("total_results", 0) == 0:
        st.warning("Keine Ergebnisse gefunden.")
        return
    
    st.success(f"**{results['total_results']} Ergebnisse** gefunden in {results.get('search_time_ms', 0):.0f}ms")
    
    def extract_gutachten_info(content: str) -> Dict[str, str]:
        """Extrahiert Gutachten-Informationen aus dem Content-Text"""
        info = {}
        lines = content.split('\n')
        
        for line in lines[:5]:  # Erste 5 Zeilen für Metadaten
            if line.startswith('Gutachten Nr.'):
                info['gutachten_nummer'] = line.strip()
            elif line.startswith('Rechtsbezug:'):
                info['rechtsbezug'] = line.replace('Rechtsbezug:', '').strip()
            elif line.startswith('Normen:'):
                normen = line.replace('Normen:', '').strip()
                info['normen'] = normen if normen else 'Keine spezifischen Normen angegeben'
        
        return info
    
    # Ergebnisse anzeigen
    for i, result in enumerate(results.get("results", []), 1):
        with st.container():            # Content-Text extrahieren (API verwendet 'content', nicht 'text')
            content = result.get("content", result.get("text", ""))
            gutachten_info = extract_gutachten_info(content)
            
            st.markdown(f"""
            <div class="result-card">
                <h4 style="color: #1e293b !important;">📄 Ergebnis {i} (Relevanz: {result.get('similarity_score', 0):.2f})</h4>
                <p style="color: #374151 !important;"><strong style="color: #1f2937 !important;">Gutachten:</strong> {gutachten_info.get('gutachten_nummer', 'N/A')}</p>
                <p style="color: #374151 !important;"><strong style="color: #1f2937 !important;">Rechtsbezug:</strong> {gutachten_info.get('rechtsbezug', 'N/A')}</p>
                <p style="color: #374151 !important;"><strong style="color: #1f2937 !important;">Normen:</strong> {gutachten_info.get('normen', 'N/A')}</p>
            </div>
            """, unsafe_allow_html=True)            # Text anzeigen mit verbesserter Formatierung
            escaped_content = html.escape(content)
            
            # Verbessere die Textformatierung
            def format_gutachten_text(text: str) -> str:
                """Formatiert Gutachtentext für bessere Lesbarkeit"""
                lines = text.split('\n')
                formatted_lines = []
                
                for line in lines:
                    line = line.strip()
                    if not line:
                        formatted_lines.append('<br>')
                        continue
                    
                    # Erkenne Überschriften (beginnen oft mit Gutachten Nr., Rechtsbezug:, etc.)
                    if any(line.startswith(prefix) for prefix in ['Gutachten Nr.', 'Rechtsbezug:', 'Normen:', 'Sachverhalt:', 'Rechtliche Bewertung:', 'Fazit:']):
                        formatted_lines.append(f'<h5 style="color: #1e40af !important; margin: 1rem 0 0.5rem 0; font-weight: 600;">{line}</h5>')
                    # Erkenne Listen (beginnen mit Ziffern oder Buchstaben)
                    elif line.strip().startswith(('1.', '2.', '3.', '4.', '5.', 'a)', 'b)', 'c)', '- ', '• ')):
                        formatted_lines.append(f'<p style="color: #374151 !important; margin: 0.5rem 0 0.5rem 1rem; line-height: 1.6;">{line}</p>')                    # Normaler Absatz
                    else:
                        formatted_lines.append(f'<p style="color: #374151 !important; margin: 0.8rem 0; line-height: 1.6;">{line}</p>')
                
                return '\n'.join(formatted_lines)
            
            formatted_content = format_gutachten_text(escaped_content)
            
            if len(content) > 500:
                with st.expander(f"Text anzeigen ({len(content)} Zeichen)"):
                    st.markdown(f"""
                    <style>
                    .text-content {{
                        background-color: #ffffff !important;
                        padding: 1.5rem !important;
                        border-radius: 8px !important;
                        border: 2px solid #3b82f6 !important;
                        margin: 1rem 0 !important;
                        box-shadow: 0 2px 8px rgba(0,0,0,0.1) !important;
                        max-height: 60vh !important;
                        overflow-y: auto !important;
                    }}
                    .text-content h5 {{
                        color: #1e40af !important;
                        margin: 1rem 0 0.5rem 0 !important;
                        font-weight: 600 !important;
                        font-size: 16px !important;
                    }}
                    .text-content p {{
                        color: #374151 !important;
                        line-height: 1.6 !important;
                        margin: 0.8rem 0 !important;
                        font-size: 14px !important;
                        font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Roboto', sans-serif !important;
                    }}
                    </style>
                    <div class="text-content">
                        {formatted_content}
                    </div>
                    """, unsafe_allow_html=True)
            else:
                st.markdown(f"""
                <style>
                .text-content-short {{
                    background-color: #ffffff !important;
                    padding: 1.5rem !important;
                    border-radius: 8px !important;
                    border: 2px solid #3b82f6 !important;
                    margin: 1rem 0 !important;
                    box-shadow: 0 2px 8px rgba(0,0,0,0.1) !important;
                }}
                .text-content-short h5 {{
                    color: #1e40af !important;
                    margin: 1rem 0 0.5rem 0 !important;
                    font-weight: 600 !important;
                    font-size: 16px !important;
                }}
                .text-content-short p {{
                    color: #374151 !important;
                    line-height: 1.6 !important;
                    margin: 0.8rem 0 !important;
                    font-size: 14px !important;
                    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Roboto', sans-serif !important;
                }}
                </style>
                <div class="text-content-short">
                    {formatted_content}
                </div>
                """, unsafe_allow_html=True)
                with st.expander(f"Text anzeigen ({len(content)} Zeichen)"):
                    # Stärkeres CSS für bessere Sichtbarkeit im Expander
                    st.markdown(f"""
                    <style>
                    .text-content {{
                        background-color: #ffffff !important;
                        padding: 1.5rem !important;
                        border-radius: 8px !important;
                        border: 2px solid #3b82f6 !important;
                        margin: 1rem 0 !important;
                        box-shadow: 0 2px 8px rgba(0,0,0,0.1) !important;
                        max-height: 60vh !important;
                        overflow-y: auto !important;
                    }}
                    .text-content h5 {{
                        color: #1e40af !important;
                        margin: 1rem 0 0.5rem 0 !important;
                        font-weight: 600 !important;
                        font-size: 16px !important;
                    }}
                    .text-content p {{
                        color: #374151 !important;
                        line-height: 1.6 !important;
                        margin: 0.8rem 0 !important;
                        font-size: 14px !important;
                        font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Roboto', sans-serif !important;
                    }}
                    </style>
                    <div class="text-content">
                        {formatted_content}
                    </div>
                    """, unsafe_allow_html=True)
            else:
                st.markdown(f"""
                <style>
                .text-content-short {{
                    background-color: #ffffff !important;
                    padding: 1.5rem !important;
                    border-radius: 8px !important;
                    border: 2px solid #3b82f6 !important;
                    margin: 1rem 0 !important;
                    box-shadow: 0 2px 8px rgba(0,0,0,0.1) !important;
                }}
                .text-content-short h5 {{
                    color: #1e40af !important;
                    margin: 1rem 0 0.5rem 0 !important;
                    font-weight: 600 !important;
                    font-size: 16px !important;
                }}
                .text-content-short p {{
                    color: #374151 !important;
                    line-height: 1.6 !important;
                    margin: 0.8rem 0 !important;
                    font-size: 14px !important;
                    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Roboto', sans-serif !important;
                }}
                </style>
                <div class="text-content-short">
                    {formatted_content}
                </div>
                """, unsafe_allow_html=True)
            
            # Metadaten
            metadata = result.get("metadata", {})
            if metadata:
                with st.expander("Metadaten"):
                    st.json(metadata)
            
            st.divider()

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

def render_admin_dashboard():
    """Rendert Admin-Dashboard."""
    st.markdown("## 🛠️ System-Administration")
    
    # Stats abrufen
    with st.spinner("Lade Statistiken..."):
        stats = get_admin_stats()
    
    if "error" in stats:
        st.error(f"Fehler beim Laden der Statistiken: {stats['error']}")
        return
    
    # Metriken anzeigen
    col1, col2, col3, col4 = st.columns(4)
    
    db_stats = stats.get("database_stats", {})
    with col1:
        st.metric("Collections", db_stats.get("total_collections", 0))
    
    with col2:
        st.metric("Chunks", db_stats.get("total_chunks", 0))
    
    with col3:
        st.metric("DB Größe (MB)", f"{db_stats.get('database_size_mb', 0):.1f}")
    
    system_stats = stats.get("system_stats", {})
    with col4:
        st.metric("Speicher (MB)", f"{system_stats.get('memory_usage_mb', 0):.1f}")
    
    # Detaillierte Statistiken
    st.markdown("### 📊 Detaillierte Statistiken")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("**Datenbank-Metriken**")
        if db_stats:
            df_db = pd.DataFrame([
                {"Metrik": "Collections", "Wert": db_stats.get("total_collections", 0)},
                {"Metrik": "Chunks", "Wert": db_stats.get("total_chunks", 0)},
                {"Metrik": "Größe (MB)", "Wert": f"{db_stats.get('database_size_mb', 0):.1f}"}
            ])
            st.dataframe(df_db, use_container_width=True)
    
    with col2:
        st.markdown("**System-Metriken**")
        if system_stats:
            df_sys = pd.DataFrame([
                {"Metrik": "Speicher (MB)", "Wert": f"{system_stats.get('memory_usage_mb', 0):.1f}"},
                {"Metrik": "Speicher (%)", "Wert": f"{system_stats.get('memory_percent', 0):.1f}"},
                {"Metrik": "Status", "Wert": "Aktiv"}
            ])
            st.dataframe(df_sys, use_container_width=True)

def main():
    """Hauptfunktion der Streamlit-App."""
    init_streamlit()
    
    # Header
    st.markdown("""
    <div class="main-header">
        ⚖️ Legal Tech Semantic Search
        <p style="font-size: 1rem; margin-top: 0.5rem;">KI-gestützte Rechtsgutachten-Suche und -Analyse</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Sidebar
    st.sidebar.title("🔧 Konfiguration")
    
    # API-Status prüfen
    api_status = check_api_connection()
    if api_status:
        st.sidebar.success("✅ API verfügbar")
    else:
        st.sidebar.error("❌ API nicht erreichbar")
        st.error(f"API-Server nicht erreichbar unter {API_BASE_URL}")
        st.info("Bitte stellen Sie sicher, dass der API-Server läuft.")
        return
    
    # Navigation
    page = st.sidebar.selectbox(
        "Navigation",
        ["🔍 Semantische Suche", "❓ Frage & Antwort", "🛠️ Administration"]
    )
    
    # Seiten-spezifische Inhalte
    if page == "🔍 Semantische Suche":
        render_search_page()
    elif page == "❓ Frage & Antwort":
        render_qa_page()
    elif page == "🛠️ Administration":
        render_admin_dashboard()

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
            results = search_documents(query, search_type, limit)
            search_time = (time.time() - start_time) * 1000
            
            # Suchzeit hinzufügen
            if "error" not in results:
                results["search_time_ms"] = search_time
            
            render_search_results(results)
    
    elif query == "":
        st.info("👆 Geben Sie einen Suchbegriff ein, um zu starten.")

def render_qa_page():
    """Rendert die Q&A-Seite."""
    st.markdown("## ❓ Frage & Antwort")
    st.markdown("Stellen Sie Fragen zu Rechtsgutachten und erhalten Sie KI-gestützte Antworten.")
    
    # Frage eingeben
    question = st.text_area(
        "Ihre Frage",
        placeholder="z.B. Was sind die Voraussetzungen für Schadensersatz nach § 280 BGB?",
        height=100,
        help="Stellen Sie eine konkrete Rechtsfrage"
    )
    
    # Optionen
    col1, col2 = st.columns(2)
    
    with col1:
        context_limit = st.slider("Anzahl Quellen", 1, 10, 5)
    
    with col2:
        detail_level = st.selectbox(
            "Antwort-Detail",
            ["Kurz", "Mittel", "Ausführlich"]
        )
    
    # Frage stellen
    if st.button("❓ Frage stellen", type="primary", use_container_width=True) and question:
        with st.spinner("Antwort wird generiert..."):
            result = ask_question(question, context_limit)
            render_qa_result(result)
    
    elif question == "":
        st.info("👆 Geben Sie eine Frage ein, um zu starten.")
    
    # Beispielfragen
    st.markdown("### 💡 Beispielfragen")
    example_questions = [
        "Was sind die Voraussetzungen für Schadensersatz?",
        "Wie ist die Haftung bei Vertragsbruch geregelt?",
        "Welche Ansprüche haben Mieter bei Mängeln?",
        "Was regelt das Widerrufsrecht bei Verbraucherverträgen?"
    ]
    
    for i, example in enumerate(example_questions):
        if st.button(f"📝 {example}", key=f"example_{i}"):
            st.rerun()

if __name__ == "__main__":
    main()
