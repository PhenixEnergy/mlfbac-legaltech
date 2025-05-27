# 🔧 LegalTech NLP Pipeline - Troubleshooting Guide

[![Troubleshooting](https://img.shields.io/badge/Troubleshooting-Complete-success)](./DEVELOPER_GUIDE.md)
[![Support](https://img.shields.io/badge/Support-Available-blue)](mailto:support@legaltech.example.com)

## 📋 Übersicht

Dieser Guide hilft bei der Diagnose und Lösung häufiger Probleme der LegalTech NLP Pipeline.

## 🚨 Häufige Probleme und Lösungen

### 🔄 Performance-Probleme

#### Problem: Langsame Verarbeitung
```
Symptom: Pipeline läuft sehr langsam
Ursache: Suboptimale Konfiguration oder Ressourcenmangel
```

**Lösungsansätze:**
1. **Batch-Größe anpassen**:
   ```json
   {
     "performance": {
       "batch_processing": {
         "batch_size": 50  // Reduzieren bei wenig RAM
       }
     }
   }
   ```

2. **Parallele Verarbeitung optimieren**:
   ```json
   {
     "parallel_processing": {
       "max_workers": 2  // An CPU-Kerne anpassen
     }
   }
   ```

3. **Caching aktivieren**:
   ```json
   {
     "caching": {
       "enabled": true,
       "cache_directory": "optimization_cache"
     }
   }
   ```

#### Problem: Speicher-Overflow
```
Symptom: "MemoryError" oder "Out of Memory"
Ursache: Zu große Dateien oder ineffiziente Speichernutzung
```

**Lösungsansätze:**
1. **Streaming aktivieren**:
   ```json
   {
     "memory_management": {
       "streaming_threshold_mb": 256,
       "garbage_collection_interval": 50
     }
   }
   ```

2. **Kleinere Batch-Größen**:
   ```bash
   export LEGALTECH_BATCH_SIZE=25
   export LEGALTECH_MAX_MEMORY=2048
   ```

### 📝 Datenverarbeitungsfehler

#### Problem: JSON Parsing Fehler
```
Symptom: "JSONDecodeError" oder "Invalid JSON"
Ursache: Beschädigte oder falsch formatierte Eingabedateien
```

**Lösungsansätze:**
1. **Eingabedatei validieren**:
   ```python
   import json
   
   def validate_json_file(filepath):
       try:
           with open(filepath, 'r', encoding='utf-8') as f:
               json.load(f)
           print("✅ JSON ist gültig")
       except json.JSONDecodeError as e:
           print(f"❌ JSON Fehler: {e}")
   ```

2. **Encoding-Probleme lösen**:
   ```python
   # In optimization_config.json
   {
     "validation": {
       "input_validation": {
         "encoding_validation": true,
         "remove_html_tags": true
       }
     }
   }
   ```

#### Problem: Segmentierungsfehler
```
Symptom: "No segments found" oder "Segmentation failed"
Ursache: Zu restriktive Qualitätsfilter oder ungeeignete Texte
```

**Lösungsansätze:**
1. **Qualitätsfilter lockern**:
   ```json
   {
     "segmentation": {
       "quality_filters": {
         "min_segment_length": 30,
         "min_coherence": 0.4,
         "min_completeness": 0.5
       }
     }
   }
   ```

2. **Debug-Modus aktivieren**:
   ```bash
   export LEGALTECH_DEBUG_MODE=true
   export LEGALTECH_VERBOSE_OUTPUT=true
   ```

### ⚙️ Konfigurationsprobleme

#### Problem: Konfigurationsdatei nicht gefunden
```
Symptom: "Config file not found" oder "FileNotFoundError"
Ursache: Fehlender oder falscher Pfad zur Konfigurationsdatei
```

**Lösungsansätze:**
1. **Konfigurationspfad prüfen**:
   ```bash
   # Aktuelles Verzeichnis prüfen
   ls -la optimization_config.json
   
   # Umgebungsvariable setzen
   export LEGALTECH_CONFIG_PATH=/pfad/zur/config.json
   ```

2. **Standard-Konfiguration erstellen**:
   ```python
   from optimized_prompt_generation import OptimizedPromptGenerator
   
   # Standard-Config generieren
   generator = OptimizedPromptGenerator()
   generator.save_default_config("optimization_config.json")
   ```

#### Problem: Ungültige Konfigurationswerte
```
Symptom: "ValidationError" oder "Invalid configuration"
Ursache: Falsche oder widersprüchliche Konfigurationswerte
```

**Lösungsansätze:**
1. **Konfiguration validieren**:
   ```python
   from optimized_prompt_generation import OptimizedPromptGenerator
   
   generator = OptimizedPromptGenerator()
   generator.validate_config("optimization_config.json")
   ```

2. **Häufige Validierungsfehler**:
   ```json
   {
     "segmentation": {
       "min_segment_length": 50,      // Muss < max_segment_length
       "max_segment_length": 2000,    // Muss > min_segment_length
       "quality_threshold": 0.7       // Muss zwischen 0.0 und 1.0
     }
   }
   ```

### 🔌 Importfehler

#### Problem: Modul nicht gefunden
```
Symptom: "ModuleNotFoundError" oder "ImportError"
Ursache: Fehlende Dependencies oder falsche Python-Pfade
```

**Lösungsansätze:**
1. **Dependencies installieren**:
   ```bash
   pip install -r requirements.txt
   
   # Oder einzeln:
   pip install numpy pandas transformers torch
   ```

2. **Python-Pfad prüfen**:
   ```python
   import sys
   print(sys.path)
   
   # Pfad hinzufügen falls nötig
   sys.path.append('/pfad/zum/Scripts')
   ```

### 🔍 Output-Qualitätsprobleme

#### Problem: Schlechte Prompt-Qualität
```
Symptom: Generierte Prompts sind unspezifisch oder repetitiv
Ursache: Suboptimale Template-Konfiguration
```

**Lösungsansätze:**
1. **Template-Vielfalt erhöhen**:
   ```json
   {
     "prompt_generation": {
       "max_templates_per_type": 15,
       "enable_domain_adaptation": true,
       "template_selection_strategy": "adaptive"
     }
   }
   ```

2. **Keyword-Extraktion optimieren**:
   ```json
   {
     "keyword_extraction": {
       "min_frequency": 1,
       "max_keywords": 25,
       "boost_legal_terms": true
     }
   }
   ```

#### Problem: Niedrige Segmentqualität
```
Symptom: Segmente sind unvollständig oder inkohärent
Ursache: Zu aggressive Segmentierung oder schlechte Texte
```

**Lösungsansätze:**
1. **Segmentierung verfeinern**:
   ```json
   {
     "segmentation": {
       "enhancement_features": {
         "cross_reference_detection": true,
         "legal_concept_extraction": true,
         "argument_structure_analysis": true
       }
     }
   }
   ```

2. **Qualitätsmetriken anpassen**:
   ```json
   {
     "quality_filters": {
       "min_coherence": 0.6,
       "min_completeness": 0.7,
       "require_legal_content": true
     }
   }
   ```

## 🔍 Debugging-Tools

### Log-Analyse

**Log-Level erhöhen**:
```bash
export LEGALTECH_LOG_LEVEL=DEBUG
export LEGALTECH_VERBOSE_OUTPUT=true
```

**Strukturierte Logs aktivieren**:
```json
{
  "logging": {
    "level": "DEBUG",
    "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    "include_performance_metrics": true
  }
}
```

### Performance-Profiling

**Memory-Tracking aktivieren**:
```bash
export LEGALTECH_MEMORY_TRACKING=true
export LEGALTECH_PROFILE_PERFORMANCE=true
```

**Performance-Report generieren**:
```python
from optimization_integration import OptimizedPipelineIntegrator

integrator = OptimizedPipelineIntegrator(
    config_path="optimization_config.json",
    enable_profiling=True
)

# Nach Verarbeitung:
integrator.generate_performance_report("performance_report.json")
```

### Validierung

**Input-Validierung**:
```python
def validate_input_file(filepath):
    """Validiert Eingabedatei auf häufige Probleme."""
    import json
    import os
    
    # Dateigröße prüfen
    size_mb = os.path.getsize(filepath) / (1024 * 1024)
    print(f"Dateigröße: {size_mb:.2f} MB")
    
    # JSON-Struktur prüfen
    with open(filepath, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    # Erforderliche Felder prüfen
    required_fields = ['gutachten_nr', 'text']
    for item in data[:5]:  # Erste 5 Einträge prüfen
        for field in required_fields:
            if field not in item:
                print(f"❌ Fehlendes Feld: {field}")
                return False
    
    print("✅ Input-Validierung erfolgreich")
    return True
```

**Output-Validierung**:
```python
def validate_output_quality(output_file):
    """Prüft Qualität der generierten Daten."""
    import json
    
    with open(output_file, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    total_lines = len(lines)
    valid_lines = 0
    
    for line in lines:
        try:
            data = json.loads(line)
            if 'messages' in data and len(data['messages']) >= 2:
                valid_lines += 1
        except json.JSONDecodeError:
            continue
    
    quality_ratio = valid_lines / total_lines
    print(f"Output-Qualität: {quality_ratio:.2%} ({valid_lines}/{total_lines})")
    
    return quality_ratio > 0.9
```

## 🛠️ Erweiterte Problembehandlung

### Speicher-Optimierung

**Für große Dateien (>1GB)**:
```json
{
  "performance": {
    "memory_management": {
      "streaming_threshold_mb": 100,
      "chunk_processing": true,
      "garbage_collection_interval": 25
    },
    "batch_processing": {
      "batch_size": 25,
      "max_concurrent_batches": 2
    }
  }
}
```

### Netzwerk-Probleme

**Für Remote-Ressourcen**:
```json
{
  "network": {
    "timeout_seconds": 30,
    "retry_attempts": 3,
    "backoff_factor": 2.0
  }
}
```

### Encoding-Probleme

**Unicode-Handling**:
```json
{
  "validation": {
    "input_validation": {
      "encoding_validation": true,
      "normalize_unicode": true,
      "remove_control_chars": true
    }
  }
}
```

## 📞 Support & Hilfe

### Community-Support
- **GitHub Issues**: Probleme und Feature-Requests
- **Discussions**: Allgemeine Fragen und Erfahrungsaustausch
- **Wiki**: Community-Dokumentation und Tutorials

### Professioneller Support
- **E-Mail**: support@legaltech.example.com
- **Enterprise Support**: Für kommerzielle Anwendungen
- **Consulting**: Individuelle Optimierungen und Anpassungen

### Hilfreiche Ressourcen
- **[DEVELOPER_GUIDE.md](./DEVELOPER_GUIDE.md)**: Umfassendes Entwicklerhandbuch
- **[API_REFERENCE.md](./API_REFERENCE.md)**: Detaillierte API-Dokumentation
- **[CONFIGURATION.md](./CONFIGURATION.md)**: Konfigurationsreferenz
- **[Documentation/index.html](./Documentation/index.html)**: Interaktive Web-Dokumentation

## 🔄 Häufige Workflows

### Schnelldiagnose
```bash
# 1. System prüfen
python -c "import sys; print(f'Python: {sys.version}')"

# 2. Dependencies prüfen
pip list | grep -E "(numpy|pandas|transformers)"

# 3. Konfiguration validieren
python -c "from optimized_prompt_generation import OptimizedPromptGenerator; OptimizedPromptGenerator().validate_config()"

# 4. Test-Lauf
python optimization_integration.py --mode test --input sample.jsonl --verbose
```

### Performance-Optimierung
```bash
# 1. Baseline messen
time python optimization_integration.py --mode segmentation --input test.jsonl

# 2. Optimierungen anwenden
export LEGALTECH_BATCH_SIZE=200
export LEGALTECH_PARALLEL_WORKERS=4

# 3. Erneut messen
time python optimization_integration.py --mode segmentation --input test.jsonl

# 4. Profiling aktivieren
export LEGALTECH_PROFILE_PERFORMANCE=true
```

---

*Zuletzt aktualisiert: 2025-01-26*  
*Version: 1.0.0*  
*Lizenz: MIT*
