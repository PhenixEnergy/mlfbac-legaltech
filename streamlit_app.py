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
    }
    .result-card {
        padding: 1rem;
        border-left: 4px solid #3b82f6;
        background-color: #f8fafc;
        margin: 0.5rem 0;
        border-radius: 5px;
    }
    .metric-card {
        background-color: #ffffff;
        padding: 1rem;
        border-radius: 10px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
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
        params = {
            "query": query,
            "search_type": search_type,
            "limit": limit
        }
        response = requests.get(f"{API_BASE_URL}/api/v1/search", params=params, timeout=10)
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
        response = requests.post(f"{API_BASE_URL}/api/v1/qa/answer", json=data, timeout=15)
        if response.status_code == 200:
            return response.json()
        else:
            return {"error": f"API Error: {response.status_code}"}
    except Exception as e:
        return {"error": f"Connection Error: {str(e)}"}

def get_admin_stats() -> Dict:
    """Ruft Admin-Statistiken ab."""
    try:
        response = requests.get(f"{API_BASE_URL}/api/v1/admin/stats", timeout=10)
        if response.status_code == 200:
            return response.json()
        else:
            return {"error": f"API Error: {response.status_code}"}
    except Exception as e:
        return {"error": f"Connection Error: {str(e)}"}

def render_search_results(results: Dict):
    """Rendert Suchergebnisse."""
    if "error" in results:
        st.error(f"Fehler bei der Suche: {results['error']}")
        return
    
    if results.get("total_results", 0) == 0:
        st.warning("Keine Ergebnisse gefunden.")
        return
    
    st.success(f"**{results['total_results']} Ergebnisse** gefunden in {results.get('search_time_ms', 0):.0f}ms")
    
    # Ergebnisse anzeigen
    for i, result in enumerate(results.get("results", []), 1):
        with st.container():
            st.markdown(f"""
            <div class="result-card">
                <h4>📄 Ergebnis {i} (Relevanz: {result.get('similarity_score', 0):.2f})</h4>
                <p><strong>Gutachten:</strong> {result.get('gutachten_id', 'N/A')}</p>
                <p><strong>Sektion:</strong> {result.get('section_type', 'N/A')}</p>
            </div>
            """, unsafe_allow_html=True)
            
            # Text anzeigen
            text = result.get("text", "")
            if len(text) > 500:
                with st.expander(f"Text anzeigen ({len(text)} Zeichen)"):
                    st.write(text)
            else:
                st.write(text)
            
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
