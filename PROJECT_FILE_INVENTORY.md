# LegalTech Projekt - Bereinigte Dateiübersicht
================================================

**Aktualisiert am:** 26. Mai 2025  
**Projektstatus:** Bereinigt - Nur essentielle Dateien für Fine-Tuning & RAG Training

---

## 📁 Bereinigte Repository-Struktur

### 🔧 **Scripts/** - Essentielle Skripte
Nur die Kern-Skripte für Fine-Tuning und RAG Training.

| Datei | Beschreibung | Status | Zweck |
|-------|-------------|--------|--------|
| `segment_and_prepare_training_data.py` | **HAUPTSKRIPT** - Segmentiert Gutachten für Fine-Tuning | ✅ BEHALTEN | Fine-Tuning Datenvorbereitung |
| `prepare_rag_training_data.py` | **RAG-SYSTEM** - Erstellt RAG-Trainingsdaten | ✅ BEHALTEN | RAG Training Datenvorbereitung |
| `jsonl_converter.py` | Konvertiert JSON ↔ JSONL Formate | ✅ BEHALTEN | Datenformat-Konvertierung |
| `optimized_prompt_generation.py` | Erweiterte Prompt-Generierung | ✅ BEHALTEN | Optimierte Prompt-Erstellung |
| `enhanced_segmentation.py` | Erweiterte Segmentierung mit ML | ✅ BEHALTEN | Advanced Text Processing |

### 🗑️ **Scripts/** - Zu löschende Dateien
Alle anderen Dateien im Scripts-Ordner können entfernt werden.

| Dateien/Ordner | Grund | Aktion |
|----------------|-------|--------|
| `advanced_pipeline_orchestrator.py` | Enterprise-Features nicht benötigt | ❌ LÖSCHEN |
| `enhanced_quality_validation.py` | Enterprise-Features nicht benötigt | ❌ LÖSCHEN |
| `optimization_integration.py` | Komplex, nicht essenziell | ❌ LÖSCHEN |
| `quality_validation.py` | Ersetzt durch andere Validierung | ❌ LÖSCHEN |
| `semantic_segmentation.py` | Ersetzt durch enhanced_segmentation | ❌ LÖSCHEN |
| `prepare_rag_training_data_fixed.py` | Backup-Version | ❌ LÖSCHEN |
| `quick_start.py` | Demo-Script | ❌ LÖSCHEN |
| `test_optimization.py` | Test-Dateien | ❌ LÖSCHEN |
| `optimization_demo.py` | Demo-Script | ❌ LÖSCHEN |
| `enterprise_integration_tests.py` | Enterprise-Tests | ❌ LÖSCHEN |
| `debug_*.py` | Debug-Scripts | ❌ LÖSCHEN |
| `test_*.py` | Test-Dateien | ❌ LÖSCHEN |
| `minimal_*.py` | Test-Scripts | ❌ LÖSCHEN |
| `__pycache__/` | Python Cache | ❌ LÖSCHEN |
| `optimization_cache/` | Cache-Verzeichnis | ❌ LÖSCHEN |
| `*.log` | Log-Dateien | ❌ LÖSCHEN |
| `*.json` | Test-Konfigurationen | ❌ LÖSCHEN |
| `*.jsonl` | Test-Outputs | ❌ LÖSCHEN |

### 📊 **Database/** - Kern-Datenbank

#### 📂 **Database/Original_Data/** (BEHALTEN)
| Datei | Beschreibung | Status | Größe/Wichtigkeit |
|-------|-------------|--------|-------------------|
| `gutachten_alle_seiten_neu.json` | **QUELLDATEI** - Originale Gutachten-Sammlung | ✅ BEHALTEN | Basis aller Daten |

#### 📂 **Database/Fine_Tuning/** (SELEKTIV BEHALTEN)
Nur die wichtigsten Fine-Tuning Dateien behalten.

| Datei | Beschreibung | Status | Begründung |
|-------|-------------|--------|------------|
| `gutachten_alle_seiten_neu_200k_segmented_prepared.jsonl` | 200k Token Training Set | ✅ BEHALTEN | Optimal für Training |
| `gutachten_alle_seiten_neu_max_segmented_prepared.jsonl` | Vollständiges Training Set | ✅ BEHALTEN | Maximale Datenmenge |
| `gutachten_alle_seiten_neu_50k_*` | Kleine Test-Sets | ❌ LÖSCHEN | Nicht produktiv nötig |
| `gutachten_alle_seiten_neu_100k_*` | Mittlere Test-Sets | ❌ LÖSCHEN | Nicht produktiv nötig |
| `gutachten_alle_seiten_neu_1_5_Mio_*` | 1.5M Token Sets | ❌ LÖSCHEN | Redundant zu max |
| `gutachten_alle_seiten_neu_2_Mio_*` | 2M Token Sets | ❌ LÖSCHEN | Redundant zu max |

#### 📂 **Database/RAG_Training/** (SELEKTIV BEHALTEN)
Nur die produktiven RAG-Dateien behalten.

| Datei | Beschreibung | Status | Begründung |
|-------|-------------|--------|------------|
| `gutachten_alle_seiten_neu_200k_segmented_prepared_rag_knowledge_base.jsonl` | 200k Knowledge Base | ✅ BEHALTEN | Produktive KB |
| `gutachten_alle_seiten_neu_200k_segmented_prepared_rag_training.jsonl` | 200k RAG Training | ✅ BEHALTEN | Produktives Training |
| `*50k*` | Kleine Test-Datasets | ❌ LÖSCHEN | Nicht produktiv nötig |
| `*100k*` (außer 200k) | Mittlere Test-Sets | ❌ LÖSCHEN | Nicht produktiv nötig |

---

### 📚 **Documentation/** - Kern-Dokumentation (BEHALTEN)

| Datei | Beschreibung | Status | Zweck |
|-------|-------------|--------|--------|
| `index.html` | **HAUPTDOKUMENTATION** | ✅ BEHALTEN | Projektreferenz |
| `script_documentation.html` | Skript-Dokumentation | ✅ BEHALTEN | Technische Referenz |
| `rag_training_guide.html` | RAG-Training Anleitung | ✅ BEHALTEN | RAG-System Dokumentation |
| Alle anderen `*.html` | Zusätzliche Dokumentation | ❌ LÖSCHEN | Nicht essenziell |

---

### 📝 **Stammdateien** (BEHALTEN)

| Datei | Beschreibung | Status | Zweck |
|-------|-------------|--------|--------|
| `README.md` | Projekt-Readme | ✅ BEHALTEN | Erste Anlaufstelle |
| `PROJECT_FILE_INVENTORY.md` | **DIESE DATEI** - Bereinigte Übersicht | ✅ BEHALTEN | Projektmanagement |

### 🗑️ **Stammdateien** (LÖSCHEN)

| Dateien | Grund | Aktion |
|---------|-------|--------|
| `API_REFERENCE.md` | Enterprise-Features | ❌ LÖSCHEN |
| `CONFIGURATION.md` | Erweiterte Konfiguration | ❌ LÖSCHEN |
| `DEVELOPER_GUIDE.md` | Entwickler-Features | ❌ LÖSCHEN |
| `ENTERPRISE_USER_GUIDE.md` | Enterprise-Features | ❌ LÖSCHEN |
| `PERFORMANCE_BENCHMARKS.md` | Performance-Tests | ❌ LÖSCHEN |
| `TROUBLESHOOTING.md` | Erweiterte Troubleshooting | ❌ LÖSCHEN |
| `PROJECT_STRUCTURE*.md` | Alte Strukturen | ❌ LÖSCHEN |
| `README_NEW.md` | Duplikate | ❌ LÖSCHEN |
| `DOCUMENTATION_*.md` | Erweiterte Docs | ❌ LÖSCHEN |
| `ENHANCEMENT_*.md` | Entwicklungsberichte | ❌ LÖSCHEN |
| `*.log` | Log-Dateien | ❌ LÖSCHEN |
| `*.py` (Stamm) | Test-Scripts | ❌ LÖSCHEN |
| `*.bat` | Batch-Dateien | ❌ LÖSCHEN |

---

### 📁 **Ordner** (LÖSCHEN)

| Ordner | Grund | Aktion |
|--------|-------|--------|
| `Examples/` | Demo-Code | ❌ LÖSCHEN |
| `Documentation/` (außer 3 essentiellen Dateien) | Überflüssige Docs | ❌ LÖSCHEN |

---

## 🎯 **Bereinigungsplan**

### **Phase 1: Scripts aufräumen**
```bash
# Im Scripts/ Ordner nur behalten:
- segment_and_prepare_training_data.py
- prepare_rag_training_data.py  
- jsonl_converter.py
- optimized_prompt_generation.py
- enhanced_segmentation.py

# Alles andere löschen
```

### **Phase 2: Database bereinigen**
```bash
# Original_Data/ - komplett behalten
# Fine_Tuning/ - nur 200k und max behalten
# RAG_Training/ - nur 200k Dateien behalten
```

### **Phase 3: Documentation bereinigen**
```bash
# Nur behalten:
- index.html
- script_documentation.html  
- rag_training_guide.html
```

### **Phase 4: Stammdateien bereinigen**
```bash
# Nur behalten:
- README.md
- PROJECT_FILE_INVENTORY.md
```

---

## ✅ **Nach der Bereinigung**

### **Finale Repository-Struktur:**
```
README.md
PROJECT_FILE_INVENTORY.md
Scripts/
  ├── segment_and_prepare_training_data.py
  ├── prepare_rag_training_data.py
  ├── jsonl_converter.py
  ├── optimized_prompt_generation.py
  └── enhanced_segmentation.py
Database/
  ├── Original_Data/
  │   └── gutachten_alle_seiten_neu.json
  ├── Fine_Tuning/
  │   ├── gutachten_alle_seiten_neu_200k_segmented_prepared.jsonl
  │   └── gutachten_alle_seiten_neu_max_segmented_prepared.jsonl
  └── RAG_Training/
      ├── gutachten_alle_seiten_neu_200k_segmented_prepared_rag_knowledge_base.jsonl
      └── gutachten_alle_seiten_neu_200k_segmented_prepared_rag_training.jsonl
Documentation/
  ├── index.html
  ├── script_documentation.html
  └── rag_training_guide.html
```

### **Geschätzte Platzeinsparung:** ~80-90%
### **Funktionalität:** 100% erhalten für Fine-Tuning & RAG Training

---

**🎯 ZWECK:** Sauberes, fokussiertes Repository nur mit den essentiellen Komponenten für Fine-Tuning und RAG Training von LegalTech NLP-Modellen.

---

**⚡ Status:** Bereinigungsplan erstellt - Ready für Repository Cleanup!
