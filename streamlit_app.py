#!/usr/bin/env python3
"""
Legal Tech Semantic Search - Final Version
Professionelle Version mit Dark/Light Mode und verbesserter UX
"""

import streamlit as st

# Konfiguration importieren
try:
    from src.config import config
    # Use localhost for client connections even if server binds to 0.0.0.0
    host = "localhost" if config.API_HOST == "0.0.0.0" else config.API_HOST
    API_BASE_URL = f"http://{host}:{config.API_PORT}"
except ImportError:
    # Fallback wenn Konfiguration nicht verfügbar
    API_BASE_URL = "http://localhost:8000"

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
import re

# Initialize session state
if 'search_query' not in st.session_state:
    st.session_state.search_query = ""
if 'search_results' not in st.session_state:
    st.session_state.search_results = None
if 'show_advanced' not in st.session_state:
    st.session_state.show_advanced = False
if 'search_count' not in st.session_state:
    st.session_state.search_count = 0
if 'dark_mode' not in st.session_state:
    st.session_state.dark_mode = True

# Konfiguration
PAGE_CONFIG = {
    "page_title": "Legal Tech AI Search",
    "page_icon": "",
    "layout": "wide",
    "initial_sidebar_state": "collapsed"  # Sidebar eingeklappt starten
}

def init_streamlit():
    """Initialisiert Streamlit-Konfiguration."""
    st.set_page_config(**PAGE_CONFIG)
    
    # Verstecke Streamlit-Branding
    st.markdown("""
    <style>
        /* Entferne ALLE Streamlit-Branding-Elemente */
        #MainMenu {visibility: hidden;}
        footer {visibility: hidden;}
        header {visibility: hidden;}
        .viewerBadge_container__1QSob {display: none;}
        .styles_viewerBadge__1yB5_ {display: none;}
        .viewerBadge_link__1S137 {display: none;}
        .viewerBadge_text__1JaDK {display: none;}
        [data-testid="stToolbar"] {display: none;}
        [data-testid="stDecoration"] {display: none;}
        [data-testid="stStatusWidget"] {display: none;}
        .st-emotion-cache-1y4p8pa {padding-top: 0rem;}
        .block-container {padding-top: 1rem;}
    </style>
    """, unsafe_allow_html=True)
    
    # Dynamic CSS based on theme
    if st.session_state.dark_mode:
        # Dark Mode CSS
        st.markdown("""
        <style>
        /* FAU RW Farbschema - Dark Mode */
        :root {
            --rw-hell: #F2DED1;
            --rw-vitale: #C60F3C;
            --rw-aktiv: #97182F;
            --rw-dunkel: #662938;
            --text-primary: #e2e8f0;
            --text-secondary: #cbd5e1;
            --bg-primary: #1a1a1a;
            --bg-secondary: #2d2d2d;
            --bg-tertiary: #3a3a3a;
            --border-color: rgba(151, 24, 47, 0.2);
            --shadow-color: rgba(0,0,0,0.3);
        }
        
        /* Base Theme */
        .stApp {
            background-color: var(--bg-primary);
            color: var(--text-primary);
        }
        
        /* Select Box Improvement */
        .stSelectbox > div > div {
            background: var(--bg-tertiary) !important;
            border: 2px solid var(--rw-aktiv) !important;
            color: var(--text-primary) !important;
        }
        
        .stSelectbox label {
            color: var(--text-primary) !important;
        }
        
        [data-baseweb="select"] {
            background-color: var(--bg-tertiary) !important;
        }
        
        [data-baseweb="select"] > div {
            background-color: var(--bg-tertiary) !important;
            color: var(--text-primary) !important;
        }
        
        /* Dropdown menu */
        [data-baseweb="popover"] {
            background-color: var(--bg-secondary) !important;
        }
        
        [role="option"] {
            background-color: var(--bg-secondary) !important;
            color: var(--text-primary) !important;
        }
        
        [role="option"]:hover {
            background-color: var(--rw-aktiv) !important;
        }
        </style>
        """, unsafe_allow_html=True)
    else:
        # Light Mode CSS
        st.markdown("""
        <style>
        /* FAU RW Farbschema - Light Mode */
        :root {
            --rw-hell: #F2DED1;
            --rw-vitale: #C60F3C;
            --rw-aktiv: #97182F;
            --rw-dunkel: #662938;
            --text-primary: #1f2937;
            --text-secondary: #4b5563;
            --bg-primary: #ffffff;
            --bg-secondary: #f9fafb;
            --bg-tertiary: #f3f4f6;
            --border-color: #e5e7eb;
            --shadow-color: rgba(0,0,0,0.05);
        }
        
        /* Base Theme */
        .stApp {
            background-color: var(--bg-primary);
            color: var(--text-primary);
        }
        
        /* Hero Section - Light Mode angepasst */
        .hero-container {
            background: linear-gradient(135deg, var(--rw-aktiv) 0%, var(--rw-vitale) 100%);
            padding: 3rem;
            border-radius: 20px;
            text-align: center;
            margin-bottom: 3rem;
            box-shadow: 0 10px 30px rgba(151, 24, 47, 0.15);
        }
        
        /* Input Fields - Light Mode */
        .stTextInput > div > div > input, .stTextArea > div > div > textarea {
            background: #ffffff;
            border: 2px solid #e5e7eb;
            color: var(--text-primary);
            font-size: 1rem;
            padding: 0.75rem 1rem;
            border-radius: 8px;
            transition: all 0.2s ease;
            box-shadow: 0 1px 2px rgba(0, 0, 0, 0.05);
        }
        
        .stTextInput > div > div > input:focus, .stTextArea > div > div > textarea:focus {
            border-color: var(--rw-aktiv);
            box-shadow: 0 0 0 3px rgba(151, 24, 47, 0.1);
            outline: none;
        }
        
        /* Buttons - Light Mode */
        .stButton > button {
            background: var(--rw-aktiv);
            color: white;
            border: none;
            padding: 0.75rem 2rem;
            font-weight: 600;
            border-radius: 8px;
            font-size: 1rem;
            transition: all 0.2s ease;
            width: 100%;
            box-shadow: 0 2px 4px rgba(151, 24, 47, 0.2);
        }
        
        .stButton > button:hover {
            background: var(--rw-dunkel);
            transform: translateY(-1px);
            box-shadow: 0 4px 12px rgba(151, 24, 47, 0.3);
        }
        
        /* Select Box - Light Mode */
        .stSelectbox > div > div {
            background: #ffffff !important;
            border: 2px solid #e5e7eb !important;
            color: var(--text-primary) !important;
            border-radius: 8px !important;
            box-shadow: 0 1px 2px rgba(0, 0, 0, 0.05) !important;
        }
        
        .stSelectbox label {
            color: var(--text-primary) !important;
            font-weight: 500 !important;
        }
        
        [data-baseweb="select"] {
            background-color: #ffffff !important;
        }
        
        [data-baseweb="select"] > div {
            background-color: #ffffff !important;
            color: var(--text-primary) !important;
        }
        
        /* Dropdown menu */
        [data-baseweb="popover"] {
            background-color: #ffffff !important;
            box-shadow: 0 10px 25px rgba(0, 0, 0, 0.1) !important;
        }
        
        [role="option"] {
            background-color: #ffffff !important;
            color: var(--text-primary) !important;
        }
        
        [role="option"]:hover {
            background-color: var(--rw-hell) !important;
        }
        
        /* Sidebar - Light Mode komplett überarbeitet */
        .css-1d391kg, [data-testid="stSidebar"] {
            background: #ffffff !important;
            border-right: 1px solid #e5e7eb;
        }
        
        [data-testid="stSidebar"] * {
            color: var(--text-primary) !important;
        }
        
        [data-testid="stSidebar"] .stMarkdown {
            color: var(--text-primary) !important;
        }
        
        [data-testid="stSidebar"] p, 
        [data-testid="stSidebar"] span,
        [data-testid="stSidebar"] div {
            color: var(--text-primary) !important;
        }
        
        /* Radio Buttons in Sidebar - Light Mode */
        [data-testid="stSidebar"] .stRadio > div > label {
            color: var(--text-primary) !important;
            background-color: transparent !important;
        }
        
        [data-testid="stSidebar"] .stRadio > div > label > div {
            color: var(--text-primary) !important;
        }
        
        /* Success/Error in Sidebar */
        [data-testid="stSidebar"] .stSuccess {
            background-color: #f0fdf4 !important;
            color: #166534 !important;
            border: 1px solid #86efac !important;
            padding: 0.5rem !important;
            border-radius: 4px !important;
        }
        
        [data-testid="stSidebar"] .stError {
            background-color: #fef2f2 !important;
            color: #991b1b !important;
            border: 1px solid #fca5a5 !important;
            padding: 0.5rem !important;
            border-radius: 4px !important;
        }
        
        /* Sidebar Headers */
        [data-testid="stSidebar"] h1,
        [data-testid="stSidebar"] h2,
        [data-testid="stSidebar"] h3,
        [data-testid="stSidebar"] h4,
        [data-testid="stSidebar"] h5,
        [data-testid="stSidebar"] h6 {
            color: var(--text-primary) !important;
        }
        
        /* Captions in Sidebar */
        [data-testid="stSidebar"] .stCaption {
            color: var(--text-secondary) !important;
        }
        
        /* Divider in Sidebar */
        [data-testid="stSidebar"] hr {
            border-color: #e5e7eb !important;
        }
        
        /* Sidebar Stats - Light Mode */
        .sidebar-stats {
            background: white;
            border: 2px solid var(--rw-aktiv);
            padding: 1.5rem;
            margin-bottom: 1.5rem;
            border-radius: 12px;
            text-align: center;
            box-shadow: 0 4px 12px rgba(0, 0, 0, 0.05);
        }
        
        .sidebar-stats-value {
            font-size: 2.5rem;
            font-weight: 800;
            color: var(--rw-aktiv);
            margin-bottom: 0.25rem;
        }
        
        .sidebar-stats-label {
            font-size: 0.875rem;
            color: var(--text-secondary);
            text-transform: uppercase;
            letter-spacing: 0.1em;
        }
        
        /* Success/Error Messages - Light Mode */
        .stSuccess {
            background-color: #f0fdf4 !important;
            color: #166534 !important;
            border: 1px solid #86efac !important;
        }
        
        .stError {
            background-color: #fef2f2 !important;
            color: #991b1b !important;
            border: 1px solid #fca5a5 !important;
        }
        
        /* Info Messages - Light Mode with better contrast */
        .stInfo {
            background-color: #f0f9ff !important;
            color: #0c4a6e !important;
            border: 1px solid #0284c7 !important;
            padding: 1rem !important;
            border-radius: 8px !important;
        }
        
        .stInfo * {
            color: #0c4a6e !important;
        }
        
        /* Result Cards - Light Mode */
        .result-card {
            background: #ffffff;
            padding: 1.5rem;
            border: 1px solid #e5e7eb;
            border-left: 4px solid var(--rw-aktiv);
            margin: 1rem 0;
            border-radius: 8px;
            box-shadow: 0 1px 3px rgba(0, 0, 0, 0.05);
            transition: all 0.2s ease;
        }
        
        .result-card:hover {
            box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
            transform: translateY(-2px);
        }
        
        /* Stats Cards - Light Mode */
        .stat-card {
            background: #ffffff;
            border: 1px solid #e5e7eb;
            padding: 1.5rem;
            border-radius: 8px;
            text-align: center;
            transition: all 0.2s ease;
            box-shadow: 0 1px 3px rgba(0, 0, 0, 0.05);
        }
        
        .stat-card:hover {
            box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
            transform: translateY(-2px);
        }
        
        /* Expander - Light Mode - FIXED */
        .streamlit-expanderHeader {
            background: #f9fafb !important;
            border: 2px solid #e5e7eb !important;
            border-radius: 8px !important;
            color: var(--text-primary) !important;
            font-weight: 500 !important;
            padding: 0.75rem 1rem !important;
        }
        
        .streamlit-expanderHeader:hover {
            background: #f3f4f6 !important;
            border-color: #d1d5db !important;
        }
        
        .streamlit-expanderContent {
            border: 2px solid #e5e7eb !important;
            border-top: none !important;
            background: #fafafa !important;
        }
        
        /* Info Messages - Light Mode ENHANCED */
        .stInfo {
            background-color: #f0f9ff !important;
            color: #075985 !important;
            border: 2px solid #0284c7 !important;
            padding: 1rem !important;
            border-radius: 8px !important;
            font-weight: 500 !important;
        }
        
        .stInfo * {
            color: #075985 !important;
        }
        
        /* Success Messages - Light Mode */
        .stSuccess {
            background-color: #f0fdf4 !important;
            color: #14532d !important;
            border: 2px solid #16a34a !important;
            padding: 1rem !important;
            border-radius: 8px !important;
            font-weight: 500 !important;
        }
        
        .stSuccess * {
            color: #14532d !important;
        }
        
        /* Error Messages - Light Mode */
        .stError {
            background-color: #fef2f2 !important;
            color: #7f1d1d !important;
            border: 2px solid #dc2626 !important;
            padding: 1rem !important;
            border-radius: 8px !important;
            font-weight: 500 !important;
        }
        
        .stError * {
            color: #7f1d1d !important;
        }
        
        /* Sidebar Toggle Button - Light Mode */
        [data-testid="collapsedControl"] {
            color: var(--text-primary) !important;
        }
        
        [data-testid="collapsedControl"] svg {
            fill: var(--text-primary) !important;
            stroke: var(--text-primary) !important;
        }
        
        /* Radio Buttons - Light Mode */
        .stRadio > div {
            background-color: transparent;
        }
        
        .stRadio label {
            color: var(--text-primary) !important;
        }
        
        /* Links - Light Mode */
        .sidebar-link {
            color: var(--rw-aktiv);
            text-decoration: none;
            transition: all 0.2s ease;
            font-weight: 500;
        }
        
        .sidebar-link:hover {
            color: var(--rw-dunkel);
            text-decoration: underline;
        }
        
        /* Caption Text */
        .stCaption {
            color: var(--text-secondary) !important;
        }
        
        /* Formatted Text Container - Light Mode */
        .formatted-text-container {
            background-color: #ffffff;
            padding: 2rem;
            border-radius: 8px;
            border: 1px solid #e5e7eb;
            margin: 1rem 0;
            box-shadow: 0 1px 3px rgba(0, 0, 0, 0.05);
        }
        
        .formatted-text-container h5 {
            color: var(--rw-aktiv) !important;
            margin: 1.5rem 0 0.5rem 0;
            font-weight: 600;
            font-size: 16px !important;
        }
        
        .formatted-text-container p {
            color: var(--text-primary) !important;
            margin: 0.8rem 0;
            line-height: 1.6;
            font-size: 14px;
        }
        </style>
        """, unsafe_allow_html=True)
    
    # Common CSS for both themes
    st.markdown("""
    <style>
    /* Force text color in all modes */
    .stMarkdown, .stMarkdown p, .stMarkdown span {
        color: var(--text-primary) !important;
    }
    
    /* Headers */
    h1, h2, h3, h4, h5, h6 {
        color: var(--text-primary) !important;
    }
    
    /* Labels */
    label {
        color: var(--text-primary) !important;
    }
    /* Container Styling */
    .block-container {
        padding-top: 1rem;
        padding-bottom: 2rem;
        max-width: 1200px;
    }
    
    /* Hero Section */
    .hero-container {
        background: linear-gradient(135deg, var(--rw-aktiv) 0%, var(--rw-vitale) 100%);
        padding: 3rem;
        border-radius: 24px;
        text-align: center;
        margin-bottom: 3rem;
        box-shadow: 0 20px 40px rgba(151, 24, 47, 0.3);
    }
    
    .hero-title {
        color: white;
        font-size: 3.5rem;
        font-weight: 800;
        margin-bottom: 0.5rem;
        text-shadow: 0 2px 10px rgba(0,0,0,0.2);
    }
    
    .hero-subtitle {
        color: rgba(255,255,255,0.9);
        font-size: 1.25rem;
        font-weight: 300;
    }
    
    /* Search Box Container - removed */
    
    /* Input Field Styling */
    .stTextInput > div > div > input, .stTextArea > div > div > textarea {
        background: var(--bg-primary);
        border: 2px solid rgba(151, 24, 47, 0.3);
        color: var(--text-primary);
        font-size: 1.1rem;
        padding: 1rem;
        border-radius: 12px;
        transition: all 0.3s ease;
    }
    
    .stTextInput > div > div > input::placeholder, .stTextArea > div > div > textarea::placeholder {
        color: var(--text-secondary);
        opacity: 0.7;
    }
    
    .stTextInput > div > div > input:focus, .stTextArea > div > div > textarea:focus {
        border-color: var(--rw-vitale);
        box-shadow: 0 0 0 4px rgba(198, 15, 60, 0.15);
        outline: none;
    }
    
    /* Button Styling */
    .stButton > button {
        background: linear-gradient(135deg, var(--rw-aktiv) 0%, var(--rw-vitale) 100%);
        color: white;
        border: none;
        padding: 0.75rem 2rem;
        font-weight: 600;
        border-radius: 12px;
        font-size: 1rem;
        transition: all 0.3s ease;
        width: 100%;
        box-shadow: 0 4px 15px rgba(151, 24, 47, 0.4);
        transform: translateY(0);
    }
    
    .stButton > button:hover {
        transform: translateY(-4px) scale(1.02);
        box-shadow: 0 8px 30px rgba(198, 15, 60, 0.6);
        background: linear-gradient(135deg, var(--rw-vitale) 0%, var(--rw-dunkel) 100%);
    }
    
    .stButton > button:active {
        transform: translateY(-2px) scale(1.01);
    }
    
    /* Result Card Styling */
    .result-card {
        background: var(--bg-secondary);
        padding: 1.5rem;
        border-left: 4px solid var(--rw-vitale);
        border: 1px solid var(--border-color);
        margin: 1rem 0;
        border-radius: 16px;
        box-shadow: 0 4px 12px var(--shadow-color);
        transition: all 0.3s ease;
        position: relative;
        overflow: hidden;
    }
    
    .result-card:hover {
        border-color: var(--rw-vitale);
        transform: translateY(-3px);
        box-shadow: 0 12px 30px var(--shadow-color);
    }
    
    .result-card::before {
        content: '';
        position: absolute;
        left: 0;
        top: 0;
        bottom: 0;
        width: 4px;
        background: linear-gradient(180deg, var(--rw-aktiv) 0%, var(--rw-vitale) 100%);
    }
    
    .result-card h4 {
        color: var(--text-primary) !important;
        margin-bottom: 0.5rem;
    }
    
    .result-card p {
        color: var(--text-secondary) !important;
        margin: 0.25rem 0;
    }
    
    .result-card strong {
        color: var(--text-primary) !important;
    }
    
    /* Formatted Text Display */
    .formatted-text-container {
        background-color: var(--bg-primary);
        padding: 2rem;
        border-radius: 8px;
        border: 2px solid var(--rw-vitale);
        margin: 1rem 0;
        box-shadow: 0 4px 12px var(--shadow-color);
        max-height: 70vh;
        overflow-y: auto;
        font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Roboto', sans-serif;
    }
    
    .formatted-text-container h5 {
        color: var(--rw-vitale) !important;
        margin: 1.5rem 0 0.5rem 0;
        font-weight: 600;
        font-size: 16px !important;
    }
    
    .formatted-text-container p {
        color: var(--text-primary) !important;
        margin: 0.8rem 0;
        line-height: 1.6;
        font-size: 14px;
    }
    
    /* Stats Cards */
    .stats-grid {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
        gap: 1rem;
        margin-bottom: 2rem;
    }
    
    .stat-card, .metric-card {
        background: var(--bg-secondary);
        border: 1px solid var(--border-color);
        padding: 1.5rem;
        border-radius: 16px;
        text-align: center;
        transition: all 0.3s ease;
    }
    
    .stat-card:hover, .metric-card:hover {
        border-color: var(--rw-vitale);
        transform: translateY(-3px);
        box-shadow: 0 8px 20px rgba(198, 15, 60, 0.2);
    }
    
    .stat-value {
        font-size: 2rem;
        font-weight: 700;
        color: var(--rw-vitale);
        margin-bottom: 0.25rem;
    }
    
    .stat-label {
        font-size: 0.875rem;
        color: var(--text-secondary);
        text-transform: uppercase;
        letter-spacing: 0.05em;
    }
    
    /* Expander Styling */
    .streamlit-expanderHeader {
        background: var(--bg-tertiary) !important;
        border-radius: 8px;
        color: var(--text-primary) !important;
        font-weight: 600;
        transition: all 0.3s ease;
    }
    
    .streamlit-expanderHeader:hover {
        background: rgba(151, 24, 47, 0.1) !important;
    }
    
    .streamlit-expander {
        background-color: var(--bg-secondary) !important;
        border: 1px solid var(--border-color) !important;
    }
    
    .streamlit-expander > div > div {
        color: var(--text-primary) !important;
        background-color: transparent !important;
    }
    
    /* Sidebar */
    .css-1d391kg, [data-testid="stSidebar"] {
        background: var(--bg-secondary);
        border-right: 1px solid var(--border-color);
    }
    
    /* Sidebar Stats Box */
    .sidebar-stats {
        background: linear-gradient(135deg, var(--rw-aktiv) 0%, var(--rw-vitale) 100%);
        padding: 1.5rem;
        margin-bottom: 1.5rem;
        border-radius: 16px;
        text-align: center;
        box-shadow: 0 8px 20px rgba(151, 24, 47, 0.3);
    }
    
    .sidebar-stats-value {
        font-size: 2.5rem;
        font-weight: 800;
        color: white;
        margin-bottom: 0.25rem;
    }
    
    .sidebar-stats-label {
        font-size: 0.875rem;
        color: rgba(255, 255, 255, 0.9);
        text-transform: uppercase;
        letter-spacing: 0.1em;
    }
    
    /* Links in Sidebar */
    .sidebar-link {
        color: var(--rw-vitale);
        text-decoration: none;
        transition: all 0.3s ease;
    }
    
    .sidebar-link:hover {
        color: var(--rw-dunkel);
        text-decoration: underline;
    }
    
    /* JSON Display */
    .stJson {
        background-color: var(--bg-secondary) !important;
        color: var(--text-primary) !important;
    }
    
    /* Radio Buttons */
    .stRadio > div {
        background-color: transparent;
    }
    
    /* Slider */
    .stSlider > div > div {
        color: var(--rw-vitale);
    }
    
    /* Success/Error/Warning Messages */
    .stSuccess, .stError, .stWarning, .stInfo {
        background-color: var(--bg-secondary);
        border-radius: 8px;
        color: var(--text-primary);
    }
    
    /* Metric Values */
    [data-testid="metric-container"] {
        background-color: var(--bg-secondary);
        padding: 1rem;
        border-radius: 8px;
        border: 1px solid var(--border-color);
    }
    
    /* Loading Spinner */
    .stSpinner > div {
        border-color: var(--rw-vitale);
    }
    
    /* Theme Toggle */
    .theme-toggle {
        position: fixed;
        top: 1rem;
        right: 1rem;
        z-index: 999;
        background: var(--bg-secondary);
        padding: 0.5rem 1rem;
        border-radius: 20px;
        border: 1px solid var(--border-color);
        cursor: pointer;
        transition: all 0.3s ease;
    }
    
    .theme-toggle:hover {
        background: var(--bg-tertiary);
    }
    
    /* Responsive Design */
    @media (max-width: 768px) {
        .hero-title {
            font-size: 2.5rem;
        }
        
        .stats-grid {
            grid-template-columns: 1fr;
        }
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
            formatted_lines.append(f'<h5>{html.escape(line_stripped)}</h5>')
        
        # Erkenne Listen und Aufzählungen
        elif line_stripped.startswith(('a)', 'b)', 'c)', 'd)', 'e)', '- ', '• ', '*')):
            formatted_lines.append(f'<p style="margin: 0.3rem 0 0.3rem 1.5rem; line-height: 1.6; font-size: 14px;">{html.escape(line_stripped)}</p>')
        
        # Erkenne eingerückte Texte (oft wichtige Punkte)
        elif line.startswith('    ') or line.startswith('\t'):
            formatted_lines.append(f'<p style="margin: 0.3rem 0 0.3rem 2rem; line-height: 1.6; font-size: 14px; font-style: italic;">{html.escape(line_stripped)}</p>')
        
        # Normaler Absatz
        else:
            formatted_lines.append(f'<p style="margin: 0.8rem 0; line-height: 1.6; font-size: 14px;">{html.escape(line_stripped)}</p>')
    
    return '\n'.join(formatted_lines)

def render_search_results(results: Dict):
    """Rendert Suchergebnisse mit verbesserter Textformatierung."""
    
    if "error" in results:
        st.error(f"Fehler bei der Suche: {results['error']}")
        return
    
    total = results.get("total_results", 0)
    
    if total == 0:
        st.warning("Keine Ergebnisse gefunden. Versuchen Sie andere Suchbegriffe.")
        return
    
    # Stats display
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown(f"""
        <div class="stat-card">
            <div class="stat-value">{total}</div>
            <div class="stat-label">Ergebnisse</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        search_time = results.get("search_time_ms", 0)
        st.markdown(f"""
        <div class="stat-card">
            <div class="stat-value">{search_time:.0f}ms</div>
            <div class="stat-label">Suchzeit</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        avg_score = sum(r.get('similarity_score', 0) for r in results.get('results', [])) / max(len(results.get('results', [])), 1)
        st.markdown(f"""
        <div class="stat-card">
            <div class="stat-value">{avg_score:.1%}</div>
            <div class="stat-label">Ø Relevanz</div>
        </div>
        """, unsafe_allow_html=True)
    
    st.markdown("### Suchergebnisse")
    
    def extract_gutachten_info(result: Dict) -> Dict[str, str]:
        """Extrahiert Gutachten-Informationen aus API-Result mit verbesserter Fallback-Logik"""
        info = {}
        
        # Versuche Metadaten aus der API-Antwort zu extrahieren
        metadata = result.get("metadata", {})
        content = result.get("content", "")
        
        # 1. Gutachten-Nummer - Versuche verschiedene Quellen
        source_id = None
        
        # Primär: aus metadata
        if metadata:
            source_id = (metadata.get("source_gutachten_id") or 
                        metadata.get("gutachten_id") or 
                        metadata.get("document_id"))
        
        # Fallback: aus result direkt
        if not source_id:
            source_id = (result.get("source_gutachten_id") or 
                        result.get("gutachten_id") or 
                        result.get("document_id"))
        
        # Letzter Fallback: aus Content extrahieren
        if not source_id and content:
            lines = content.split('\n')
            for line in lines[:10]:  # Erste 10 Zeilen durchsuchen
                line_stripped = line.strip()
                if "Gutachten" in line_stripped and any(c.isdigit() for c in line_stripped):
                    # Versuche Nummer zu extrahieren
                    import re
                    match = re.search(r'(?:Gutachten|Nr\.?|#)\s*[:\-]?\s*(\d+)', line_stripped, re.IGNORECASE)
                    if match:
                        source_id = match.group(1)
                        break
        
        if source_id:
            info['gutachten_nummer'] = f"Gutachten Nr. {source_id}"
        else:
            info['gutachten_nummer'] = "Keine Gutachten-Nr. verfügbar"
        
        # 2. Rechtsbezug
        rechtsbezug = None
        if metadata:
            rechtsbezug = (metadata.get("rechtsbezug") or 
                          metadata.get("jurisdiction") or 
                          metadata.get("legal_jurisdiction"))
        
        if not rechtsbezug:
            rechtsbezug = result.get("rechtsbezug") or result.get("jurisdiction")
        
        info['rechtsbezug'] = rechtsbezug or "National (DNOTI)"
        
        # 3. Normen - Versuche verschiedene Quellen
        legal_norms = None
        
        # Primär: aus metadata
        if metadata:
            legal_norms = (metadata.get("legal_norms") or 
                          metadata.get("normen") or 
                          metadata.get("laws"))
        
        # Fallback: aus result direkt
        if not legal_norms:
            legal_norms = (result.get("legal_norms") or 
                          result.get("normen") or 
                          result.get("laws"))
        
        # Verarbeite legal_norms
        if legal_norms and isinstance(legal_norms, list) and len(legal_norms) > 0:
            # Filtere leere/ungültige Einträge
            valid_norms = [str(norm).strip() for norm in legal_norms if norm and str(norm).strip()]
            if valid_norms:
                info['normen'] = "; ".join(valid_norms[:5])  # Max 5 Normen
            else:
                info['normen'] = "Keine gültigen Normen in Metadaten"
        else:
            # Fallback: aus Content extrahieren
            if content:
                lines = content.split('\n')
                found_norms = []
                
                # Suche explizite Normen-Zeile
                for line in lines[:15]:
                    line_stripped = line.strip()
                    if line_stripped.startswith('Normen:'):
                        normen_text = line_stripped.replace('Normen:', '').strip()
                        if normen_text and normen_text not in ['', '-', 'N/A']:
                            found_norms.append(normen_text)
                        break
                
                # Suche nach Rechtsnormen im Text (§ 123 BGB, Art. 456 GG, etc.)
                if not found_norms:
                    import re
                    # Suche nach typischen deutschen Rechtsnormen
                    norm_patterns = re.findall(r'[§Art\.]*\s*\d+[a-z]*\s+[A-Z]{2,4}', content[:2000], re.IGNORECASE)
                    if norm_patterns:
                        # Bereinige und dedupliziere
                        cleaned_norms = list(set([norm.strip() for norm in norm_patterns if norm.strip()]))
                        found_norms.extend(cleaned_norms[:3])  # Max 3 aus Content
                
                if found_norms:
                    info['normen'] = "; ".join(found_norms)
                else:
                    info['normen'] = "Keine spezifischen Normen erkannt"
            else:
                info['normen'] = "Kein Content verfügbar"
        
        return info
    
    # Ergebnisse anzeigen
    for i, result in enumerate(results.get("results", []), 1):
        with st.container():
            # Metadaten direkt aus API-Result extrahieren
            gutachten_info = extract_gutachten_info(result)
            
            # Metadaten-Card
            st.markdown(f"""
            <div class="result-card">
                <h4>Ergebnis {i} (Relevanz: {result.get('similarity_score', 0):.2f})</h4>
                <p><strong>Gutachten:</strong> {gutachten_info.get('gutachten_nummer', 'N/A')}</p>
                <p><strong>Rechtsbezug:</strong> {gutachten_info.get('rechtsbezug', 'N/A')}</p>
                <p><strong>Normen:</strong> {gutachten_info.get('normen', 'N/A')}</p>
            </div>
            """, unsafe_allow_html=True)
            
            # Content-Text für Anzeige extrahieren
            content = result.get("content", result.get("text", ""))
            
            # Formatierter Text anzeigen
            formatted_content = format_gutachten_text(content)
            
            if len(content) > 500:
                with st.expander(f"Text anzeigen ({len(content)} Zeichen)"):
                    st.markdown(f"""
                    <div class="formatted-text-container">
                        {formatted_content}
                    </div>
                    """, unsafe_allow_html=True)
            else:
                st.markdown(f"""
                <div class="formatted-text-container">
                    {formatted_content}
                </div>
                """, unsafe_allow_html=True)
            
            # Metadaten anzeigen
            api_metadata = result.get("metadata", {})
            if api_metadata:
                with st.expander("Detaillierte Metadaten"):
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
                
                # Vollständige Metadaten als JSON (außerhalb des Expanders)
                if st.button(f"Vollständige Metadaten anzeigen", key=f"metadata_{result.get('id', hash(str(result)))}"):
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
    st.markdown("### Antwort")
    answer = result.get("answer", "Keine Antwort verfügbar.")
    st.write(answer)
    
    # Kontext anzeigen
    context_chunks = result.get("context_chunks", [])
    if context_chunks:
        st.markdown("### Verwendete Quellen")
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

def render_hero_section():
    """Rendert Hero Section."""
    st.markdown("""
    <div class="hero-container">
        <h1 class="hero-title">Legal Tech AI Search</h1>
        <p class="hero-subtitle">Intelligente Rechtsgutachten-Analyse mit modernster KI-Technologie</p>
    </div>
    """, unsafe_allow_html=True)

def render_search_page():
    """Rendert die Suchseite."""
    st.markdown("## Semantische Suche")
    st.markdown("Durchsuchen Sie Rechtsgutachten mit KI-gestützter semantischer Suche.")
    
    # Suchoptionen
    col1, col2 = st.columns([3, 1])
    
    with col1:
        query = st.text_input(
            "Suchbegriff",
            placeholder="z.B. Schadensersatz, Haftung, Vertragsrecht...",
            help="Geben Sie einen Suchbegriff oder eine Frage ein",
            value=st.session_state.search_query,
            key="search_input"
        )
    
    with col2:
        search_type = st.selectbox(
            "Suchtyp",
            ["semantic", "keyword", "hybrid"],
            help="Semantisch: KI-basiert, Keyword: Exakte Begriffe, Hybrid: Kombination",
            key="search_type_select"
        )
    
    # Erweiterte Optionen
    with st.expander("Erweiterte Suchoptionen"):
        col1, col2, col3 = st.columns(3)
        
        with col1:
            limit = st.slider("Max. Ergebnisse", 1, 50, 10)
        
        with col2:
            min_similarity = st.slider("Min. Ähnlichkeit", 0.0, 1.0, 0.5, 0.1)
        
        with col3:
            search_filters = st.text_input("Filter (JSON)", placeholder='{"legal_area": "civil"}')
    
    # Suche ausführen - mit Enter-Taste Support
    search_clicked = st.button("Suchen", type="primary", use_container_width=True)
    
    # Check if Enter was pressed (query changed and is not empty)
    enter_pressed = (query != st.session_state.search_query and query != "")
    
    if (search_clicked or enter_pressed) and query:
        st.session_state.search_query = query
        # Increment search counter immediately
        st.session_state.search_count += 1
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
            
            st.session_state.search_results = results
            # Force rerun to update the search query state
            if enter_pressed:
                st.rerun()
    
    # Ergebnisse anzeigen
    if st.session_state.search_results:
        render_search_results(st.session_state.search_results)
    elif query == "":
        st.info("Geben Sie einen Suchbegriff ein, um zu starten.")

def render_qa_page():
    """Rendert die Q&A-Seite."""
    st.markdown("## Fragen & Antworten")
    st.markdown("Stellen Sie Fragen zu Rechtsgutachten und erhalten Sie KI-gestützte Antworten.")
    
    question = st.text_area(
        "Ihre Frage",
        placeholder="z.B. Was sind die Voraussetzungen für Schadensersatz nach § 280 BGB?",
        help="Stellen Sie eine konkrete Rechtsfrage"
    )
    
    col1, col2 = st.columns([1, 4])
    with col1:
        context_limit = st.slider("Max. Quellen", 1, 10, 5)
    
    if st.button("Frage stellen", type="primary", use_container_width=True) and question:
        with st.spinner("KI arbeitet..."):
            result = ask_question(question, context_limit)
            render_qa_result(result)

def render_admin_page():
    """Rendert Admin-Dashboard."""
    st.markdown("## System-Administration")
    
    # API-Status prüfen
    if check_api_connection():
        st.success("API-Verbindung aktiv")
    else:
        st.error("API nicht erreichbar")
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
    
    # Theme Toggle in rechter oberer Ecke
    col1, col2 = st.columns([10, 1])
    with col2:
        if st.button("☀" if st.session_state.dark_mode else "🌙", key="theme_toggle", help="Theme wechseln"):
            st.session_state.dark_mode = not st.session_state.dark_mode
            st.rerun()
    
    # Hauptnavigation
    render_hero_section()
    
    # Sidebar Navigation
    with st.sidebar:
        st.markdown("### Legal Tech AI")
        
        # Search Statistics
        st.markdown(f"""
        <div class="sidebar-stats">
            <div class="sidebar-stats-value">{st.session_state.search_count}</div>
            <div class="sidebar-stats-label">Suchanfragen</div>
        </div>
        """, unsafe_allow_html=True)
        
        # API-Status
        if check_api_connection():
            st.success("API: Online")
        else:
            st.error("API: Offline")
        
        st.markdown("---")
        
        st.markdown("### Navigation")
        page = st.radio(
            "Wählen Sie eine Seite:",
            ["Suche", "Q&A", "Admin"],
            key="navigation"
        )
        
        st.markdown("---")
        st.markdown("### System-Info")
        
        st.caption(f"Version: 1.0.0")
        st.caption(f"Build: {datetime.now().strftime('%Y-%m-%d')}")
        
        st.markdown("---")
        st.markdown("### Links")
        st.markdown("""
        - <a href="https://github.com/PhenixEnergy/mlfbac-legaltech#" class="sidebar-link">Dokumentation</a>
        - <a href="mailto:support@legal.ai" class="sidebar-link">Support</a>
        """, unsafe_allow_html=True)
    
    # Seiten-Routing
    if page == "Suche":
        render_search_page()
    elif page == "Q&A":
        render_qa_page()
    elif page == "Admin":
        render_admin_page()

if __name__ == "__main__":
    main()