# Requirements Management - Legal Tech Project

## 📋 Übersicht der Requirements-Dateien (Updated June 2025)

### 1. `requirements.txt` - Produktions-Dependencies ✅ AKTUALISIERT
**Zweck:** Enthält alle Pakete, die für den **Betrieb** der Anwendung in Produktion benötigt werden.

**Verwendung:**
```bash
pip install -r requirements.txt --upgrade
```

**Wichtigste Updates:**
- 🔧 **FastAPI 0.115.4** (KRITISCH: JSON Serialization Fix)
- ✨ **Streamlit 1.39.0** (Neueste Features)
- 🚀 **ChromaDB 0.5.15** (Performance Verbesserungen)
- 🧠 **PyTorch 2.5.1** (Latest ML Optimizations)
- 📊 **NumPy 2.1.3** (Major Version Update)

### 2. `requirements-dev.txt` - Development-Dependencies ✅ AKTUALISIERT
**Zweck:** Enthält **zusätzliche** Tools für Entwickler - Debugging, Testing, Code Quality.

**Verwendung:**
```bash
pip install -r requirements-dev.txt --upgrade
```

**Neue Entwickler-Tools:**
- 🎨 **Ruff 0.8.4** (Moderne, schnelle Python Linting)
- 🧪 **Pytest-xdist 3.6.3** (Parallele Test-Ausführung)
- 📊 **Scalene 1.5.46** (Advanced CPU+Memory Profiler)
- 🔍 **Bandit & Safety** (Sicherheits-Scanning)
- 📚 **JupyterLab 4.3.3** (Moderne Notebook-Umgebung)

## 🚨 Kritisches Update: FastAPI Version

### ✅ Problem GELÖST:
```python
# VORHER (Problem):
fastapi>=0.104.1  # Verursachte JSON Serialization Errors

# NACHHER (Lösung):
fastapi>=0.115.4  # Behebt DateTime Serialization Issues komplett
```

### 🎯 Warum diese Updates kritisch sind:

#### 1. **JSON Serialization Bug Fix** (FastAPI)
- **Problem:** DateTime Objekte wurden nicht korrekt serialisiert
- **Lösung:** FastAPI 0.115.4+ hat verbesserte Pydantic Integration
- **Auswirkung:** Keine 500 Server Errors mehr bei API Calls

#### 2. **NumPy 2.x Kompatibilität**
- **Update:** NumPy 1.26 → 2.1.3
- **Vorteil:** Bessere Performance, moderne APIs
- **Kompatibilität:** Alle anderen Pakete sind NumPy 2.x ready

#### 3. **Pydantic 2.x Vollständige Integration**
- **Update:** Pydantic 2.10.2 mit optimierter Validierung
- **Vorteil:** Schnellere Serialization, bessere Type Safety

## 🏗️ Warum 2 Requirements-Dateien?

### Vorteile der Trennung:

#### 1. **Produktions-Optimierung**
- Schlankere Production Deployments (65 vs 85+ Pakete)
- Weniger Abhängigkeiten = weniger Sicherheitsrisiken
- Schnellere Installation in Docker Containern
- Reduzierte Attack Surface in Production

#### 2. **Entwickler-Effizienz** 
- Vollständige Tool-Suite für professionelle Entwicklung
- Code Quality Tools (Black, MyPy, Ruff)
- Erweiterte Testing Frameworks (pytest + parallel execution)
- Performance Profiling Tools (Scalene, py-spy)
- Moderne Debugging Tools (ipdb, enhanced IPython)
- Sicherheits-Scanning (Bandit, Safety, pip-audit)

#### 3. **Dependency Klarheit**
```bash
# Für Production Server:
pip install -r requirements.txt --upgrade

# Für Entwickler-Umgebung:
pip install -r requirements-dev.txt --upgrade  # Inkludiert automatisch requirements.txt
```

#### 4. **CI/CD Pipeline Optimierung**
- **Production:** 65 Pakete (minimal, sicher)
- **Testing:** 85+ Pakete (vollständige Test-Suite)
- **Documentation:** Sphinx + ReadTheDocs nur in Dev
- **Security:** Vulnerability Scanning nur in Dev

## 📦 Automatische Inklusion

**Wichtig:** `requirements-dev.txt` enthält diese Zeile:
```bash
-r requirements.txt
```

Das bedeutet: **Development-Requirements installieren automatisch auch Production-Requirements!**

## 🔄 Update-Strategie (Juni 2025)

### Regel 1: Production First ✅
Neue Production-Dependencies → `requirements.txt`
- Alle kritischen Pakete auf neueste stabile Versionen
- Sicherheitsupdates priorisiert
- Backward Compatibility geprüft

### Regel 2: Development Enhancement ✅
Testing/Debugging Tools → `requirements-dev.txt`
- Moderne Linting Tools (Ruff zusätzlich zu flake8)
- Parallele Test-Execution (pytest-xdist)
- Advanced Profiling (Scalene)
- Security Scanning Suite

### Regel 3: Version Strategy ✅
- **Production:** Getestete, stabile Versionen mit `>=`
- **Development:** Neueste Tool-Versionen
- **Security:** Regelmäßige Vulnerability Scans

## 🚀 Installation Workflows

### Neues Projekt Setup:
```bash
# 1. Basis Installation
pip install -r requirements.txt

# 2. Development Setup (für Entwickler)
pip install -r requirements-dev.txt

# 3. Verifikation
python check_requirements_update.py
```

### Update Existing Environment:
```bash
# 1. Backup current environment
pip freeze > backup_environment.txt

# 2. Update to latest versions
pip install -r requirements.txt --upgrade
pip install -r requirements-dev.txt --upgrade

# 3. Verify installation
python check_requirements_update.py

# 4. Test system
python emergency_api.py  # Test API
streamlit run streamlit_app.py  # Test Frontend
```

## 📊 Requirements Comparison

| Aspekt | requirements.txt | requirements-dev.txt |
|--------|------------------|---------------------|
| **Anzahl Pakete** | ~65 | ~85+ |
| **Zielgruppe** | Production Server | Entwickler |
| **Installation Zeit** | ~2-3 Minuten | ~4-5 Minuten |
| **Disk Space** | ~2GB | ~3GB |
| **Update Frequenz** | Monatlich | Wöchentlich |
| **Sicherheit** | Minimal Surface | Vollständiger Scan |

## 🔧 Troubleshooting

### Häufige Probleme:

#### 1. **NumPy 2.x Kompatibilität**
```bash
# Falls Kompatibilitätsprobleme auftreten:
pip install numpy>=2.1.3 --force-reinstall
```

#### 2. **PyTorch Installation Issues**
```bash
# Für CPU-only Installation:
pip install torch>=2.5.1+cpu --index-url https://download.pytorch.org/whl/cpu
```

#### 3. **FastAPI + Pydantic Conflicts**
```bash
# Koordinierte Installation:
pip install fastapi>=0.115.4 pydantic>=2.10.2 --upgrade
```

## 📝 Changelog

### Juni 2025 Update:
- ✅ FastAPI 0.115.4 (kritischer JSON Serialization Fix)
- ✅ NumPy 2.1.3 (Major Version Upgrade)
- ✅ Streamlit 1.39.0 (neueste Features)
- ✅ ChromaDB 0.5.15 (Performance Verbesserungen)
- ✅ Ruff 0.8.4 (moderne Linting Alternative)
- ✅ Sicherheits-Scanning Tools hinzugefügt
- ✅ Parallele Test-Execution Support
- ✅ Advanced Profiling Tools (Scalene)

### Für End-User/Production:
```bash
pip install -r requirements.txt
python emergency_api.py
streamlit run streamlit_app.py
```

### Für Entwickler:
```bash
pip install -r requirements-dev.txt  # Installiert alles
pytest  # Testing
black .  # Code Formatting
mypy src/  # Type Checking
```

## 📈 Version Updates durchgeführt

### Kritische Updates:
- ✅ **FastAPI:** 0.104.1 → 0.115.3 (JSON Bug Fix)
- ✅ **Streamlit:** 1.28.1 → 1.30.0 (Stability)
- ✅ **ChromaDB:** 0.4.18 → 0.4.22 (Performance)
- ✅ **Pandas:** 2.1.0 → 2.2.0 (Security)

### Development Tools:
- ✅ **pytest:** 7.4.3 → 8.1.1 (New Features)
- ✅ **black:** 23.11.0 → 24.3.0 (Formatting)
- ✅ **mypy:** 1.7.0 → 1.9.0 (Type Checking)

---

**Fazit:** Die Trennung ermöglicht optimierte Deployments und produktive Entwicklung! 🎯
