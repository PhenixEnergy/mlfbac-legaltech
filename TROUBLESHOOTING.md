# Legal Tech - Diagnose und Fehlerbehebung

## Hauptprobleme warum das Projekt nicht startbar ist:

### 1. **LM Studio Abhängigkeit**
Das System versucht sich mit LM Studio auf Port 1234 zu verbinden, aber:
- LM Studio ist nicht installiert oder läuft nicht
- Ohne LM Studio funktioniert die KI-Funktionalität nicht vollständig

**Lösung:**
- LM Studio herunterladen und installieren
- Deepseek Coder Modell laden
- LM Studio auf Port 1234 starten

### 2. **Service Orchestrierung**
Das Projekt benötigt mehrere Services gleichzeitig:
- FastAPI Backend (Port 8000)
- Streamlit Frontend (Port 8501)
- ChromaDB Vektor-Datenbank
- LM Studio LLM Service (Port 1234)

**Problem:** Keine automatische Service-Orchestrierung

### 3. **Abhängigkeiten und Umgebung**
- Virtual Environment muss aktiviert sein
- Alle Requirements müssen installiert sein
- ChromaDB muss initialisiert sein

### 4. **Port-Konflikte**
Mögliche Konflikte mit bereits laufenden Services auf Ports 8000/8501

## Lösungsansätze:

### Sofortige Lösung (ohne LM Studio):
1. **Backend manuell starten:**
   ```bash
   cd "c:\Users\rafael.schumm\LegalTech\mlfbac-legaltech"
   .\venv\Scripts\Activate.ps1
   python -m uvicorn src.api.main:app --host 127.0.0.1 --port 8000
   ```

2. **Frontend in neuem Terminal starten:**
   ```bash
   cd "c:\Users\rafael.schumm\LegalTech\mlfbac-legaltech"
   .\venv\Scripts\Activate.ps1
   streamlit run streamlit_app.py --server.port 8501
   ```

### Vollständige Lösung:
1. **LM Studio installieren:**
   - Download: https://lmstudio.ai/
   - Deepseek Coder Modell laden
   - Server auf Port 1234 starten

2. **Robuste Scripts verwenden:**
   - `service_manager.py` - Python-basierter Service Manager
   - `start_robust.bat` - Batch-Script mit Fallback

### Mock-Modus für Tests:
Das System kann auch ohne LM Studio laufen mit eingeschränkter Funktionalität.

## Überprüfung der Services:

### Backend Test:
```bash
curl http://localhost:8000/health
```

### Frontend Test:
```bash
curl http://localhost:8501
```

### LM Studio Test:
```bash
curl http://localhost:1234/v1/models
```

## Empfohlene Startreihenfolge:
1. LM Studio starten (optional für Tests)
2. FastAPI Backend starten
3. Streamlit Frontend starten
4. Browser zu http://localhost:8501 öffnen
