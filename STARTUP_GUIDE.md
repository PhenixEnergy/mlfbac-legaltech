# Legal Tech Startup System 🚀

Automatisierte Setup- und Start-Scripts für das Legal Tech Semantic Search System.

## 📁 Verfügbare Scripts

### 1. **run_legal_tech.bat** (Empfohlen)
**Komplettes All-in-One Script für Windows**
- ✅ Automatisches Setup (Virtual Environment, Dependencies, Database)
- ✅ Service-Start (FastAPI + Streamlit)
- ✅ Port-Konflikt-Erkennung
- ✅ Interaktive Service-Verwaltung
- ✅ Fallback für fehlende Komponenten

```cmd
# Einfacher Start:
run_legal_tech.bat

# Script startet automatisch:
# 1. Virtual Environment Setup
# 2. Dependency Installation  
# 3. Database Initialization
# 4. FastAPI Backend (Port 8000)
# 5. Streamlit Frontend (Port 8501)
```

### 2. **start_legal_tech.bat**
**Erweiterte Batch-Version mit detaillierter Kontrolle**
- ✅ Ausführliches Setup und Logging
- ✅ LM Studio Integration Check
- ✅ Database Setup mit dnoti Daten
- ✅ Service Health Monitoring

### 3. **start_legal_tech.ps1**
**PowerShell-Version mit fortgeschrittenen Features**
- ✅ Bessere Windows-Integration
- ✅ Job-Management für Background Services
- ✅ Erweiterte Port-Verwaltung
- ✅ Interaktive Service-Kontrolle

```powershell
# PowerShell ausführen:
.\start_legal_tech.ps1

# Mit Optionen:
.\start_legal_tech.ps1 -QuickSetup -SkipLMStudio -Port 8502
```

### 4. **scripts/service_manager.py**
**Python-basierter Service Manager**
- ✅ Cross-Platform Service Management
- ✅ Health Monitoring
- ✅ Automatic Restart bei Fehlern
- ✅ JSON-basierte Konfiguration

```python
# Service Manager verwenden:
python scripts/service_manager.py start
python scripts/service_manager.py status
python scripts/service_manager.py stop
```

## 🎯 Schnellstart (Neue Installation)

### Option A: Einfachster Start
```cmd
# 1. Repository klonen
git clone <repository-url>

# 2. In Verzeichnis wechseln
cd mlfbac-legaltech

# 3. Script ausführen
run_legal_tech.bat
```

### Option B: Mit PowerShell
```powershell
# 1. PowerShell als Administrator öffnen
# 2. Execution Policy setzen (einmalig)
Set-ExecutionPolicy RemoteSigned -Scope CurrentUser

# 3. Script ausführen
.\start_legal_tech.ps1 -QuickSetup
```

## 📋 System-Anforderungen

### Minimal-Anforderungen
- **OS:** Windows 10/11
- **Python:** 3.9+
- **RAM:** 4 GB
- **Disk:** 2 GB freier Speicher

### Optimal für AI-Features
- **RAM:** 16 GB+
- **GPU:** 8 GB VRAM (für lokale LLMs)
- **LM Studio:** Installiert und konfiguriert

## 🔧 Service-Konfiguration

### Automatische Port-Konfiguration
```
Services:
├── FastAPI Backend     → Port 8000 (Auto: 8001 bei Konflikt)
├── Streamlit Frontend  → Port 8501 (Auto: 8502 bei Konflikt)  
└── LM Studio (Optional)→ Port 1234
```

### Service-Status prüfen
Nach dem Start sind folgende URLs verfügbar:
- **Frontend:** http://localhost:8501
- **API Docs:** http://localhost:8000/docs
- **API Health:** http://localhost:8000/health

## 🗂️ Automatische Directory-Struktur

Die Scripts erstellen automatisch:
```
data/
├── logs/           # System-Logs
├── vectordb/       # ChromaDB Dateien
├── embeddings/     # Embedding-Cache
└── processed/      # Verarbeitete Daten

config/
├── services.json   # Service-Konfiguration
├── models.yaml     # Model-Settings
└── database.yaml   # DB-Konfiguration
```

## 🚨 Problembehandlung

### Script startet nicht
```cmd
# Python-Version prüfen
python --version

# Virtual Environment manuell erstellen
python -m venv venv
venv\Scripts\activate.bat
pip install streamlit fastapi uvicorn
```

### Port-Konflikte
```cmd
# Verwendete Ports anzeigen
netstat -an | find ":8000"
netstat -an | find ":8501"

# Alternative Ports verwenden
.\start_legal_tech.ps1 -Port 8502 -ApiPort 8001
```

### Dependencies fehlen
```cmd
# Core-Dependencies installieren
pip install streamlit fastapi uvicorn pandas requests

# Oder requirements.txt reparieren
pip install -r requirements.txt --force-reinstall
```

### Database-Probleme
```cmd
# Database neu initialisieren
del data\vectordb\chroma.sqlite3
python scripts\setup_database.py --quick-setup
```

## 📊 Script-Features im Detail

### run_legal_tech.bat Features:
- 🔍 **Auto-Detection:** Python, Virtual Environment, Dependencies
- 🛠️ **Auto-Setup:** Erstellt fehlende Komponenten automatisch
- 🎯 **Smart Ports:** Erkennt Port-Konflikte und weicht aus
- 📱 **Interactive:** Einfache Bedienung mit Menü-System
- 🔄 **Fallback:** Erstellt minimale Apps wenn Hauptkomponenten fehlen
- 📋 **Status:** Live-Anzeige der Service-Stati

### PowerShell Script Zusatz-Features:
- 👥 **Job Management:** Background-Prozess-Kontrolle
- 🔒 **Security:** Execution Policy Management
- 📈 **Monitoring:** Erweiterte Service-Überwachung
- ⚡ **Performance:** Bessere Resource-Verwaltung

## 🎛️ Erweiterte Konfiguration

### Service-Konfiguration anpassen
Bearbeiten Sie `config/services.json`:
```json
{
  "fastapi": {
    "name": "FastAPI Backend",
    "port": 8000,
    "health_endpoint": "/health"
  },
  "streamlit": {
    "name": "Streamlit Frontend", 
    "port": 8501
  }
}
```

### Logging-Level anpassen
```python
# In scripts/service_manager.py
logging.basicConfig(level=logging.DEBUG)  # Für mehr Details
```

## 🔄 Service-Management

### Services einzeln starten/stoppen:
```python
# Einzelne Services verwalten
python scripts/service_manager.py start --service fastapi
python scripts/service_manager.py stop --service streamlit
python scripts/service_manager.py restart --service fastapi
```

### Monitoring aktivieren:
```python
# Dauerhaftes Monitoring starten
python scripts/service_manager.py monitor
```

## 💡 Tipps & Best Practices

1. **Erste Installation:** Verwenden Sie `run_legal_tech.bat` für einfachsten Start
2. **Development:** Nutzen Sie PowerShell-Script für bessere Kontrolle
3. **Production:** Service Manager für stabilen Betrieb
4. **Debugging:** Aktivieren Sie verbose Logging in service_manager.py
5. **Performance:** LM Studio für beste AI-Ergebnisse installieren

## 📞 Support

Bei Problemen:
1. Prüfen Sie `data/logs/legaltech.log` 
2. Testen Sie Services einzeln: `python scripts/service_manager.py status`
3. Neustart mit: `run_legal_tech.bat` (Clean Setup)

Das Startup-System ist darauf ausgelegt, auch bei partiellen Installationen oder fehlenden Komponenten zu funktionieren und bietet Fallback-Lösungen für alle kritischen Services.
