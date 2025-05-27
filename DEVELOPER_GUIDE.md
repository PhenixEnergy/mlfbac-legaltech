# 🛠️ LegalTech NLP Pipeline - Developer Guide

[![Development](https://img.shields.io/badge/Development-Active-brightgreen)](https://github.com/example/legaltech-nlp)
[![Python](https://img.shields.io/badge/Python-3.8+-blue)](https://python.org)
[![Documentation](https://img.shields.io/badge/Docs-Complete-success)](./Documentation/index.html)

## 📋 Übersicht

Dieser Developer Guide bietet detaillierte Informationen für Entwickler, die am LegalTech NLP Pipeline Projekt mitarbeiten oder es erweitern möchten.

## 🏗️ Architektur-Überblick

### Kern-Komponenten

```
📦 LegalTech NLP Pipeline
├── 🧠 Core Engines
│   ├── OptimizedPromptGenerator     # Intelligente Prompt-Erstellung
│   ├── EnhancedSegmentationEngine   # Semantische Segmentierung
│   └── OptimizedPipelineIntegrator  # Pipeline-Orchestrierung
├── 🔧 Processing Scripts
│   ├── optimized_prompt_generation.py
│   ├── enhanced_segmentation.py
│   ├── optimization_integration.py
│   └── quick_start.py
└── 📊 Data Management
    ├── Database/                    # Strukturierte Datensets
    └── Documentation/               # Umfassende Dokumentation
```

## 🚀 Entwicklungsumgebung Setup

### Voraussetzungen

- **Python 3.8+**
- **Moderne IDE** (VS Code, PyCharm empfohlen)
- **Git** für Versionskontrolle
- **Mindestens 8GB RAM** für große Datensätze

### Installation

```bash
# Repository klonen
git clone <repository-url>
cd legaltech-nlp-pipeline

# Virtuelle Umgebung erstellen
python -m venv venv
venv\Scripts\activate  # Windows
# source venv/bin/activate  # Linux/Mac

# Dependencies installieren
pip install -r requirements.txt
```

### Projekt-Struktur verstehen

```
Scripts/
├── Core Modules/
│   ├── optimized_prompt_generation.py    # Prompt-Optimierung
│   ├── enhanced_segmentation.py          # Erweiterte Segmentierung
│   └── optimization_integration.py       # Pipeline-Integration
├── Utilities/
│   ├── jsonl_converter.py                # Format-Konvertierung
│   ├── segment_and_prepare_training_data.py  # Legacy Segmentierung
│   └── semantic_segmentation.py          # Semantische Analyse
├── Data Processing/
│   ├── prepare_rag_training_data.py      # RAG-Datenaufbereitung
│   └── create_demo_file.py               # Demo-Datenerstellung
└── Testing/
    ├── test_optimization.py              # Optimierung Tests
    └── quick_start.py                     # Schnellstart-Tool
```

## 🔧 API-Referenz

### OptimizedPromptGenerator

```python
from optimized_prompt_generation import OptimizedPromptGenerator

# Initialisierung
generator = OptimizedPromptGenerator(
    config_path="optimization_config.json"
)

# Basis Prompt-Generierung
prompt = generator.generate_enhanced_prompt(
    content="Rechtlicher Text...",
    context={"gutachten_nr": "123456", "date": "2025-05-25"}
)

# RAG Query-Generierung
rag_queries = generator.generate_rag_queries(
    content="Rechtlicher Text...",
    num_queries=8,
    diversity_factor=0.8
)

# Adaptive Komplexitätserkennung
complexity = generator.detect_complexity(content)
```

### EnhancedSegmentationEngine

```python
from enhanced_segmentation import EnhancedSegmentationEngine

# Initialisierung
engine = EnhancedSegmentationEngine()

# Erweiterte Segmentierung
segments = engine.segment_with_enhancement(
    text="Vollständiger Rechtstext...",
    min_quality_score=0.7,
    max_segments=10
)

# Qualitätsbewertung
for segment in segments:
    print(f"Typ: {segment.segment_type}")
    print(f"Qualität: {segment.quality_score:.3f}")
    print(f"Komplexität: {segment.complexity_level}")
```

### OptimizedPipelineIntegrator

```python
from optimization_integration import OptimizedPipelineIntegrator

# Vollständige Pipeline
integrator = OptimizedPipelineIntegrator()

# End-to-End Verarbeitung
results = integrator.process_complete_pipeline(
    input_file="data.jsonl",
    output_modes=["fine_tuning", "rag_training"],
    optimization_level="advanced"
)

# Batch-Verarbeitung
batch_results = integrator.process_batch(
    file_list=["file1.json", "file2.json"],
    parallel_workers=4
)
```

## 📊 Konfiguration

### optimization_config.json

```json
{
  "prompt_generation": {
    "max_templates_per_type": 10,
    "complexity_levels": ["basic", "intermediate", "advanced", "expert"],
    "enable_domain_adaptation": true,
    "keyword_weights": {
      "sachverhalt": 1.0,
      "rechtsfrage": 1.2,
      "subsumtion": 1.1
    }
  },
  "segmentation": {
    "min_segment_length": 50,
    "max_segment_length": 2000,
    "quality_threshold": 0.7,
    "semantic_similarity_threshold": 0.25,
    "enable_hierarchical_classification": true
  },
  "rag_training": {
    "queries_per_segment": 8,
    "enable_multi_perspective": true,
    "diversity_factor": 0.8,
    "quality_filter_threshold": 0.6
  },
  "performance": {
    "batch_size": 100,
    "enable_caching": true,
    "parallel_processing": true,
    "memory_limit_mb": 4096
  }
}
```

## 🧪 Testing & Debugging

### Unit Tests ausführen

```bash
# Alle Tests
python -m pytest Scripts/test_*.py -v

# Spezifische Tests
python Scripts/test_optimization.py
python Scripts/test_segmentation.py
```

### Debugging-Modi

```python
# Debug-Modus aktivieren
import logging
logging.basicConfig(level=logging.DEBUG)

# Verbose Output
generator = OptimizedPromptGenerator(verbose=True)
segments = engine.segment_with_enhancement(text, debug=True)
```

### Performance-Profiling

```python
import time
import memory_profiler

@memory_profiler.profile
def profile_segmentation():
    start_time = time.time()
    
    # Ihr Code hier
    segments = engine.segment_with_enhancement(large_text)
    
    end_time = time.time()
    print(f"Verarbeitungszeit: {end_time - start_time:.2f}s")
```

## 📈 Performance-Optimierung

### Speicher-Effizienz

```python
# Streaming für große Dateien
def process_large_file(file_path):
    with open(file_path, 'r', encoding='utf-8') as f:
        for line in f:
            # Zeile für Zeile verarbeiten
            yield process_single_line(line)

# Memory-mapped Files
import mmap
with open('large_file.jsonl', 'r+b') as f:
    with mmap.mmap(f.fileno(), 0) as mm:
        # Effiziente Dateiverarbeitung
        pass
```

### Parallele Verarbeitung

```python
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor
import multiprocessing

def parallel_processing(file_list):
    max_workers = min(len(file_list), multiprocessing.cpu_count())
    
    with ProcessPoolExecutor(max_workers=max_workers) as executor:
        results = list(executor.map(process_file, file_list))
    
    return results
```

### Caching-Strategien

```python
from functools import lru_cache
import pickle
import os

class CacheManager:
    def __init__(self, cache_dir="optimization_cache"):
        self.cache_dir = cache_dir
        os.makedirs(cache_dir, exist_ok=True)
    
    @lru_cache(maxsize=1000)
    def get_cached_result(self, input_hash):
        cache_file = os.path.join(self.cache_dir, f"{input_hash}.pkl")
        if os.path.exists(cache_file):
            with open(cache_file, 'rb') as f:
                return pickle.load(f)
        return None
    
    def save_to_cache(self, input_hash, result):
        cache_file = os.path.join(self.cache_dir, f"{input_hash}.pkl")
        with open(cache_file, 'wb') as f:
            pickle.dump(result, f)
```

## 🔍 Erweiterte Features

### Custom Template-Entwicklung

```python
# Eigene Prompt-Templates definieren
custom_templates = {
    "custom_analysis": [
        "Analysiere {content} unter besonderer Berücksichtigung von {norms}.",
        "Prüfe die rechtlichen Aspekte von {content} bezüglich {norms}.",
        "Bewerte {content} im Kontext der Normen {norms}."
    ]
}

generator.add_custom_templates("custom_analysis", custom_templates)
```

### Plugin-System

```python
class SegmentationPlugin:
    def __init__(self, name):
        self.name = name
    
    def process_segment(self, segment):
        # Plugin-spezifische Verarbeitung
        return enhanced_segment
    
    def get_metadata(self):
        return {"plugin": self.name, "version": "1.0"}

# Plugin registrieren
engine.register_plugin(SegmentationPlugin("custom_legal_analyzer"))
```

## 📚 Erweiterte Dokumentation

### Code-Kommentierung Standards

```python
def generate_enhanced_prompt(self, content: str, context: dict = None) -> dict:
    """
    Generiert optimierte Prompts für Rechtstexte.
    
    Args:
        content (str): Der zu verarbeitende Rechtstext
        context (dict, optional): Zusätzlicher Kontext (Gutachten-Nr., Datum, etc.)
    
    Returns:
        dict: Dictionary mit generiertem Prompt und Metadaten
        
    Raises:
        ValueError: Wenn content leer ist
        TypeError: Wenn context nicht dict ist
        
    Example:
        >>> generator = OptimizedPromptGenerator()
        >>> result = generator.generate_enhanced_prompt(
        ...     content="Rechtlicher Text...",
        ...     context={"gutachten_nr": "123456"}
        ... )
        >>> print(result["prompt"])
    """
    # Implementation hier
```

### Type Hints

```python
from typing import List, Dict, Optional, Union, Tuple
from dataclasses import dataclass

@dataclass
class SegmentResult:
    content: str
    segment_type: str
    quality_score: float
    metadata: Dict[str, Union[str, int, float]]
    
def process_segments(
    segments: List[str], 
    config: Dict[str, any]
) -> Tuple[List[SegmentResult], Dict[str, any]]:
    """Type-safe Segmentverarbeitung."""
    # Implementation
```

## 🚨 Troubleshooting

### Häufige Probleme

#### 1. Memory Errors bei großen Dateien
```python
# Lösung: Streaming verwenden
def process_large_file_safely(file_path):
    chunk_size = 1000  # Zeilen pro Chunk
    with open(file_path, 'r') as f:
        while True:
            chunk = []
            for _ in range(chunk_size):
                line = f.readline()
                if not line:
                    break
                chunk.append(line)
            
            if not chunk:
                break
                
            # Chunk verarbeiten
            yield process_chunk(chunk)
```

#### 2. JSON Encoding Errors
```python
import json
import logging

def safe_json_load(file_path):
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except UnicodeDecodeError:
        # Fallback auf andere Encodings
        for encoding in ['latin1', 'cp1252', 'iso-8859-1']:
            try:
                with open(file_path, 'r', encoding=encoding) as f:
                    return json.load(f)
            except:
                continue
        
        logging.error(f"Konnte {file_path} nicht laden")
        return None
```

#### 3. Performance Issues
```python
import cProfile
import pstats

def profile_function(func, *args, **kwargs):
    """Profiling für Performance-Analyse."""
    profiler = cProfile.Profile()
    profiler.enable()
    
    result = func(*args, **kwargs)
    
    profiler.disable()
    stats = pstats.Stats(profiler)
    stats.sort_stats('cumulative')
    stats.print_stats(10)  # Top 10 langsamste Funktionen
    
    return result
```

## 🔄 Contribution Guidelines

### Pull Request Process

1. **Fork** das Repository
2. **Branch** erstellen: `git checkout -b feature/amazing-feature`
3. **Commit** Changes: `git commit -m 'Add amazing feature'`
4. **Push** Branch: `git push origin feature/amazing-feature`
5. **Pull Request** öffnen

### Code Standards

- **PEP 8** Coding Style befolgen
- **Type Hints** verwenden
- **Docstrings** für alle öffentlichen Funktionen
- **Unit Tests** für neue Features
- **Performance Tests** für kritische Pfade

### Review Checklist

- [ ] Code folgt PEP 8 Standards
- [ ] Alle Tests bestehen
- [ ] Dokumentation ist aktualisiert
- [ ] Performance Impact evaluiert
- [ ] Backward Compatibility gewährleistet

## 📞 Support & Community

### Entwickler-Ressourcen

- **📖 Vollständige Dokumentation**: [Documentation/index.html](./Documentation/index.html)
- **🔧 API-Referenz**: [API_REFERENCE.md](./API_REFERENCE.md)
- **📊 Performance Benchmarks**: [BENCHMARKS.md](./BENCHMARKS.md)
- **🐛 Issue Tracking**: GitHub Issues
- **💬 Diskussionen**: GitHub Discussions

### Quick Links

- [Installation Guide](./INSTALLATION.md)
- [Configuration Reference](./CONFIGURATION.md)
- [Troubleshooting Guide](./TROUBLESHOOTING.md)
- [Changelog](./CHANGELOG.md)

---

**📝 Letzte Aktualisierung**: 25. Mai 2025  
**👨‍💻 Entwickler**: LegalTech Team  
**📄 Version**: 2.0.0
