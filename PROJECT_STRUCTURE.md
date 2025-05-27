# 📁 LegalTech NLP Pipeline - Projektstruktur

## 🎯 Übersicht
Dieser Überblick zeigt die konsolidierte und optimierte Projektstruktur nach den Dokumentations- und Dateioptimierungen.

## 📂 Hauptverzeichnisse

### `📁 Scripts/` - Kern-Pipeline
Die wichtigsten Ausführungsdateien für die optimierte NLP-Pipeline:

#### 🚀 Hauptmodule
- **`optimized_prompt_generation.py`** - Erweiterte Prompt-Generierung (100+ Templates)
- **`enhanced_segmentation.py`** - Hierarchische Segmentierung mit Qualitätsbewertung
- **`optimization_integration.py`** - Pipeline-Integration mit CLI-Interface
- **`advanced_pipeline_orchestrator.py`** - Enterprise Pipeline-Orchestrierung (NEU v4.0)
- **`quality_validation.py`** - Umfassende Qualitätsvalidierung (NEU)
- **`quick_start.py`** - Vereinfachtes Interface für häufige Anwendungsfälle

#### ⚙️ Konfiguration & Demo
- **`optimization_config.json`** - Zentrale Konfigurationsdatei
- **`optimization_demo.py`** - Demonstrations- und Test-Tools
- **`create_demo_file.py`** - Demo-Daten Generator

#### 🔧 Legacy Scripts (Backward Compatibility)
- **`segment_and_prepare_training_data.py`** - Original Segmentierung
- **`prepare_rag_training_data_fixed.py`** - Original RAG Vorbereitung
- **`semantic_segmentation.py`** - Basis semantische Segmentierung
- **`jsonl_converter.py`** - Format-Konvertierung

### `📁 Documentation/` - Konsolidierte Dokumentation
- **`index.html`** - Vollständige, konsolidierte HTML-Dokumentation
- **`index_old.html`** - Backup der ursprünglichen Dokumentation

### `📁 Database/` - Datensätze
Strukturiert in Unterverzeichnisse für verschiedene Anwendungsfälle:

#### `📁 Fine_Tuning/`
- `gutachten_alle_seiten_neu_50k_segmented_prepared.jsonl` (Entwicklung)
- `gutachten_alle_seiten_neu_200k_segmented_prepared.jsonl` (Training)
- `gutachten_alle_seiten_neu_1_5_Mio_segmented_prepared.jsonl` (Produktion)
- `gutachten_alle_seiten_neu_max_segmented_prepared.jsonl` (Vollständig)

#### `📁 RAG_Training/`
- RAG Knowledge Bases (strukturierte Wissensdatenbanken)
- RAG Training Data (Query-Response Paare)

#### `📁 Original_Data/`
- `gutachten_alle_seiten_neu.json` (Rohdaten)

## 🎮 Verwendung

### Schnellstart mit Enterprise Pipeline (NEU):
```bash
cd Scripts
python advanced_pipeline_orchestrator.py --input ../Database/Original_Data/gutachten_alle_seiten_neu.json --output enhanced_output.jsonl --mode auto --optimization-level maximum --workers 8 --enable-cache --monitor --report pipeline_report.json
```

### Schnellstart mit vereinfachtem Interface:
```bash
# Demo ausführen
python Scripts/quick_start.py demo

# Segmentierung
python Scripts/quick_start.py segment your_file.jsonl

# Komplette Pipeline
python Scripts/quick_start.py all your_file.json
```

### Erweiterte Pipeline-Nutzung:
```bash
# Segmentierungsmodus
python Scripts/optimization_integration.py --mode segmentation --input input.jsonl --output segments.jsonl

# RAG-Modus  
python Scripts/optimization_integration.py --mode rag --input segments.jsonl --output rag_data.jsonl

# Fine-Tuning Modus
python Scripts/optimization_integration.py --mode fine-tuning --input segments.jsonl --output training.jsonl
```

## 📖 Dokumentation öffnen

### Windows:
Doppelklick auf `open_documentation.bat`

### Manuell:
Öffnen Sie `Documentation/index.html` in Ihrem Browser

## 🗂️ Aufgeräumte Dateien

### ❌ Entfernte Dateien (konsolidiert):
- `dataset_structure_new.html` → in `index.html` integriert
- `mathematical_background_new.html` → in `index.html` integriert  
- `script_documentation_new.html` → in `index.html` integriert
- `segmentierung_visualisierung_new.html` → in `index.html` integriert
- `system_completion_report_new.html` → in `index.html` integriert
- `rag_fine_tuning_optimization.html` → in `index.html` integriert
- `simple_test.py` → durch `optimization_demo.py` ersetzt
- `test_file_loading.py` → durch `optimization_demo.py` ersetzt
- `debug_loading.py` → nicht mehr benötigt

### 📦 Backup-Dateien:
- `README_old.md` - Backup der ursprünglichen README
- `index_old.html` - Backup der ursprünglichen Dokumentation

## 🎯 Vorteile der Konsolidierung

### ✅ Weniger Dateien
- Von 7 HTML-Dateien → 1 konsolidierte Dokumentation
- Von mehreren Test-Dateien → 1 umfassendes Demo-System
- Klarere Projektstruktur

### ✅ Bessere Übersichtlichkeit  
- Moderne, responsive HTML-Dokumentation
- Einheitliches Design und Navigation
- Zentrale Anlaufstelle für alle Informationen

### ✅ Einfachere Nutzung
- `quick_start.py` für häufige Anwendungsfälle
- `open_documentation.bat` für sofortigen Dokumentationszugriff
- Klare Trennung zwischen Kern-Features und Legacy-Support

### ✅ Wartungsfreundlichkeit
- Weniger Duplikation von Informationen
- Einfachere Updates und Erweiterungen
- Bessere Versionskontrolle

## 🚀 Nächste Schritte

1. **Testen:** Verwenden Sie `python Scripts/quick_start.py demo`
2. **Dokumentation:** Öffnen Sie `open_documentation.bat` oder `Documentation/index.html`
3. **Eigene Daten:** Nutzen Sie `python Scripts/quick_start.py all your_data.jsonl`

---

*Konsolidierung abgeschlossen am: Mai 25, 2025*  
*Dokumentation und Dateien optimiert für bessere Übersichtlichkeit und Nutzung*
