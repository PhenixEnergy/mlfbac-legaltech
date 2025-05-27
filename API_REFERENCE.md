# 🔧 LegalTech NLP Pipeline - API Reference

[![API](https://img.shields.io/badge/API-Stable-brightgreen)](./DEVELOPER_GUIDE.md)
[![Python](https://img.shields.io/badge/Python-3.8+-blue)](https://python.org)

## 📋 Übersicht

Umfassende API-Dokumentation für alle Kernkomponenten der LegalTech NLP Pipeline.

## 🧠 OptimizedPromptGenerator

### Klassen-Übersicht

```python
class OptimizedPromptGenerator:
    """
    Erweiterte Prompt-Generierung mit 100+ spezialisierten Templates,
    automatischer Komplexitätserkennung und Domain-Adaptation.
    """
```

### Constructor

```python
def __init__(self, config_path: str = "optimization_config.json", 
             verbose: bool = False)
```

**Parameter:**
- `config_path` (str): Pfad zur Konfigurationsdatei
- `verbose` (bool): Aktiviert detaillierte Logging-Ausgaben

**Beispiel:**
```python
generator = OptimizedPromptGenerator(
    config_path="custom_config.json",
    verbose=True
)
```

### Kern-Methoden

#### generate_enhanced_prompt()

```python
def generate_enhanced_prompt(self, content: str, context: dict = None) -> dict
```

Generiert optimierte Prompts basierend auf Textinhalt und Kontext.

**Parameter:**
- `content` (str): Zu verarbeitender Rechtstext
- `context` (dict, optional): Zusätzlicher Kontext
  - `gutachten_nr` (str): Gutachten-Nummer
  - `erscheinungsdatum` (str): Erscheinungsdatum
  - `normen` (List[str]): Relevante Rechtsnormen
  - `segment_type` (str): Typ des Segments

**Rückgabe:**
```python
{
    "prompt": str,                    # Generierter Prompt
    "template_type": str,             # Verwendeter Template-Typ
    "complexity_level": str,          # Erkannte Komplexität
    "domain": str,                    # Erkannter Rechtsbereich
    "confidence": float,              # Confidence Score (0-1)
    "metadata": {
        "keywords": List[str],        # Extrahierte Keywords
        "norms_count": int,           # Anzahl erkannter Normen
        "template_id": str            # Template-Identifier
    }
}
```

**Beispiel:**
```python
result = generator.generate_enhanced_prompt(
    content="Im vorliegenden Fall geht es um eine Erbausschlagung...",
    context={
        "gutachten_nr": "123456",
        "erscheinungsdatum": "2025-05-25",
        "normen": ["BGB § 1942", "BGB § 1944"]
    }
)
print(f"Prompt: {result['prompt']}")
print(f"Komplexität: {result['complexity_level']}")
```

#### generate_rag_queries()

```python
def generate_rag_queries(self, content: str, num_queries: int = 8, 
                        diversity_factor: float = 0.8) -> List[dict]
```

Erstellt diverse RAG-Queries für optimale Retrieval-Performance.

**Parameter:**
- `content` (str): Basis-Text für Query-Generierung
- `num_queries` (int): Anzahl zu generierender Queries
- `diversity_factor` (float): Diversitätsfaktor (0-1)

**Rückgabe:**
```python
[
    {
        "query": str,                 # RAG Query
        "query_type": str,            # Typ (factual, analytical, etc.)
        "perspective": str,           # Rechtliche Perspektive
        "priority": int,              # Priorität (1-5)
        "expected_response_type": str # Erwarteter Antworttyp
    },
    # ... weitere Queries
]
```

#### detect_complexity()

```python
def detect_complexity(self, content: str) -> dict
```

Automatische Komplexitätserkennung für adaptive Prompt-Generierung.

**Rückgabe:**
```python
{
    "level": str,                     # basic, intermediate, advanced, expert
    "score": float,                   # Numerischer Score (0-1)
    "factors": {
        "legal_terms_density": float,
        "sentence_complexity": float,
        "citation_count": int,
        "argument_depth": float
    }
}
```

### Template-Management

#### add_custom_templates()

```python
def add_custom_templates(self, template_type: str, templates: List[str]) -> bool
```

Fügt benutzerdefinierte Templates hinzu.

#### get_available_templates()

```python
def get_available_templates(self) -> dict
```

Gibt alle verfügbaren Template-Typen zurück.

#### validate_template()

```python
def validate_template(self, template: str) -> dict
```

Validiert Template-Syntax und -Struktur.

---

## 🔧 EnhancedSegmentationEngine

### Klassen-Übersicht

```python
class EnhancedSegmentationEngine:
    """
    Erweiterte Segmentierung mit semantischer Analyse,
    hierarchischer Klassifizierung und Qualitätsbewertung.
    """
```

### Constructor

```python
def __init__(self, config: dict = None, enable_caching: bool = True)
```

### Kern-Methoden

#### segment_with_enhancement()

```python
def segment_with_enhancement(self, text: str, 
                           min_quality_score: float = 0.7,
                           max_segments: int = None) -> List[SegmentResult]
```

**Parameter:**
- `text` (str): Zu segmentierender Text
- `min_quality_score` (float): Mindest-Qualitätsscore
- `max_segments` (int, optional): Maximale Anzahl Segmente

**Rückgabe:**
```python
@dataclass
class SegmentResult:
    content: str                      # Segment-Inhalt
    heading: str                      # Erkannte Überschrift
    segment_type: str                 # Klassifizierter Typ
    quality_score: float              # Qualitätsbewertung
    complexity_level: str             # Komplexitätsstufe
    legal_concepts: List[str]         # Rechtliche Konzepte
    cross_references: List[str]       # Querverweise
    metadata: dict                    # Zusätzliche Metadaten
    
    # Qualitätsmetriken
    coherence_score: float            # Kohärenz-Score
    completeness_score: float        # Vollständigkeits-Score
    relevance_score: float           # Relevanz-Score
```

#### classify_segment_type()

```python
def classify_segment_type(self, content: str, heading: str = "") -> dict
```

Klassifiziert Segment-Typ mit Confidence-Score.

**Segment-Typen:**
- `SACHVERHALT` - Faktische Grundlagen
- `RECHTSFRAGE` - Zentrale Problemstellung  
- `ANSPRUCHSGRUNDLAGE` - Rechtliche Basis
- `TATBESTANDSVORAUSSETZUNGEN` - Voraussetzungen
- `SUBSUMTION` - Rechtliche Prüfung
- `RECHTSFOLGE` - Konsequenzen
- `ERGEBNIS` - Schlussfolgerung
- `LITERATUR` - Rechtsliteratur
- `RECHTSPRECHUNG` - Gerichtsentscheidungen
- `SONSTIGES` - Andere Inhalte

#### calculate_quality_metrics()

```python
def calculate_quality_metrics(self, segment: str) -> dict
```

Berechnet umfassende Qualitätsmetriken für Segmente.

### Konfiguration

```python
segmentation_config = {
    "min_segment_length": 50,
    "max_segment_length": 2000,
    "quality_threshold": 0.7,
    "semantic_similarity_threshold": 0.25,
    "segment_types": {
        "SACHVERHALT": {"priority": 5, "min_length": 100},
        "RECHTSFRAGE": {"priority": 5, "min_length": 50},
        # ... weitere Typen
    }
}
```

---

## ⚙️ OptimizedPipelineIntegrator

### Klassen-Übersicht

```python
class OptimizedPipelineIntegrator:
    """
    Orchestriert die komplette Pipeline mit optimierter
    Verarbeitung und Multi-Format-Output.
    """
```

### Kern-Methoden

#### process_complete_pipeline()

```python
def process_complete_pipeline(self, input_file: str,
                            output_modes: List[str] = None,
                            optimization_level: str = "standard") -> dict
```

**Output-Modi:**
- `fine_tuning` - JSONL für Model Fine-Tuning
- `rag_training` - Query-Response Paare für RAG
- `rag_knowledge_base` - Strukturierte Knowledge Base
- `analysis_report` - Detaillierter Analyse-Report

**Optimization-Level:**
- `basic` - Grundlegende Verarbeitung
- `standard` - Standard-Optimierung (empfohlen)
- `advanced` - Erweiterte Optimierung
- `maximum` - Maximale Qualität (langsamer)

#### process_batch()

```python
def process_batch(self, file_list: List[str],
                 parallel_workers: int = 4,
                 progress_callback: callable = None) -> List[dict]
```

Parallele Batch-Verarbeitung für große Datensätze.

#### generate_analysis_report()

```python
def generate_analysis_report(self, results: dict) -> dict
```

Erstellt detaillierten Analyse-Report mit Statistiken und Qualitätsmetriken.

---

## 🛠️ Utility Functions

### Datenformat-Konvertierung

```python
# jsonl_converter.py
def convert_json_to_jsonl(input_file: str, output_file: str) -> bool
def convert_jsonl_to_json(input_file: str, output_file: str) -> bool
def auto_detect_and_convert(input_file: str, output_file: str = None) -> str
```

### Qualitäts-Validierung

```python
def validate_training_data(file_path: str) -> dict:
    """
    Validiert generierte Trainingsdaten auf Konsistenz und Qualität.
    
    Returns:
        {
            "valid": bool,
            "total_entries": int,
            "valid_entries": int,
            "errors": List[dict],
            "quality_metrics": dict
        }
    """
```

### Performance-Monitoring

```python
def measure_performance(func: callable) -> dict:
    """
    Decorator für Performance-Messung.
    
    Returns:
        {
            "execution_time": float,
            "memory_usage": dict,
            "cpu_usage": float
        }
    """
```

---

## 🚀 AdvancedPipelineOrchestrator

### Klassen-Übersicht

```python
class AdvancedPipelineOrchestrator:
    """
    Enterprise-grade Pipeline-Orchestrierung mit erweiterten Features:
    - Multi-Format-Support (JSON, JSONL, XML, CSV)
    - Adaptive Performance-Optimierung mit ML-basierter Vorhersage
    - Real-time Qualitäts-Monitoring mit Alerting
    - Parallele Batch-Verarbeitung mit Auto-Scaling
    - Automatische Error-Recovery mit Circuit-Breaker Pattern
    - Plugin-System für benutzerdefinierte Erweiterungen
    - Memory Pool Management
    - Advanced Caching mit Redis-Support
    """
```

### Constructor

```python
def __init__(self, config: Dict = None)
```

**Parameter:**
- `config` (Dict): Erweiterte Konfiguration mit Enterprise-Features

**Beispiel:**
```python
config = {
    'optimization_level': 'maximum',
    'max_workers': 16,
    'use_redis_cache': True,
    'enable_monitoring': True,
    'auto_scaling': True,
    'circuit_breaker_threshold': 5,
    'alert_thresholds': {
        'error_rate': 0.05,
        'memory_usage': 0.9
    }
}

orchestrator = AdvancedPipelineOrchestrator(config)
```

### Asynchrone Verarbeitung

#### process_pipeline_async()

```python
async def process_pipeline_async(self, 
                               input_data: Union[str, List, Dict],
                               output_path: str = None,
                               processing_mode: str = "auto") -> ProcessingResult
```

**Parameter:**
- `input_data`: Eingabedaten (Dateipfad, Liste oder Dict)
- `output_path`: Ausgabepfad (optional)
- `processing_mode`: Verarbeitungsmodus ("auto", "fine_tuning", "rag", "validation")

**Rückgabe:**
```python
@dataclass
class ProcessingResult:
    success: bool
    data: Optional[Dict] = None
    error: Optional[str] = None
    processing_time: float = 0.0
    quality_score: float = 0.0
    metadata: Dict = field(default_factory=dict)
    warnings: List[str] = field(default_factory=list)
    stage: str = "unknown"
    worker_id: Optional[str] = None
    memory_usage: float = 0.0
    cache_hit: bool = False
```

**Beispiel:**
```python
import asyncio

async def main():
    orchestrator = AdvancedPipelineOrchestrator()
    
    result = await orchestrator.process_pipeline_async(
        input_data="data.jsonl",
        output_path="enhanced_output.jsonl",
        processing_mode="auto"
    )
    
    if result.success:
        print(f"Processed in {result.processing_time:.2f}s")
        print(f"Quality Score: {result.quality_score:.2%}")
        print(f"Cache Hit: {result.cache_hit}")
    else:
        print(f"Error: {result.error}")

asyncio.run(main())
```

### Performance Monitoring

#### generate_comprehensive_report()

```python
def generate_comprehensive_report(self, output_file: str = None) -> Dict
```

Generiert umfassenden Performance- und Qualitätsbericht.

**Rückgabe:**
```python
{
    'timestamp': '2025-05-26T...',
    'metrics': PipelineMetrics,
    'performance_analysis': {
        'baselines': {...},
        'recent_alerts': [...],
        'cache_performance': {...}
    },
    'system_info': {...},
    'configuration': {...},
    'recommendations': [...]
}
```

### CLI Interface

```python
def create_cli_interface(self) -> argparse.ArgumentParser
```

Erstellt erweiterte Kommandozeilen-Schnittstelle.

**CLI-Nutzung:**
```bash
python advanced_pipeline_orchestrator.py \
    --input data.jsonl \
    --output enhanced_output.jsonl \
    --mode auto \
    --optimization-level maximum \
    --workers 8 \
    --enable-cache \
    --use-redis \
    --monitor \
    --report pipeline_report.json
```

---

## 🔍 QualityValidator

### Klassen-Übersicht

```python
class QualityValidator:
    """
    Umfassende Qualitätsvalidierung für Pipeline-Outputs mit:
    - Multi-dimensionale Qualitätsmetriken
    - Legal Text Validation
    - Automated Content Analysis
    - Performance Benchmarking
    - Batch Processing Support
    """
```

### Constructor

```python
def __init__(self, custom_thresholds: Dict = None)
```

### Validierungs-Methoden

#### validate_prompt_quality()

```python
def validate_prompt_quality(self, prompt: str, context: dict = None) -> dict
```

**Parameter:**
- `prompt` (str): Zu validierender Prompt
- `context` (dict): Zusätzlicher Kontext für Validierung

**Rückgabe:**
```python
{
    "overall_score": 0.85,
    "passed": True,
    "details": {
        "length_valid": True,
        "legal_terms_ratio": 0.15,
        "legal_terms_valid": True,
        "has_question": True,
        "not_empty": True,
        "language_quality": True,
        "word_count": 42,
        "char_count": 287
    }
}
```

#### validate_segment_quality()

```python
def validate_segment_quality(self, segment: Any) -> dict
```

**Parameter:**
- `segment`: Segment-Objekt mit Attributen wie content, segment_type, quality_score

**Rückgabe:**
```python
{
    "overall_score": 0.92,
    "passed": True,
    "details": {
        "has_content": True,
        "has_type": True,
        "has_quality_score": True,
        "quality_score_valid": True,
        "content_length_valid": True,
        "type_valid": True,
        "segment_type": "SACHVERHALT",
        "quality_score": 0.87
    }
}
```

#### validate_rag_queries()

```python
def validate_rag_queries(self, queries: List[dict]) -> dict
```

**Parameter:**
- `queries`: Liste von RAG-Query-Objekten

**Rückgabe:**
```python
{
    "overall_score": 0.78,
    "passed": True,
    "details": {
        "diversity_score": 0.85,
        "avg_query_quality": 0.76,
        "metadata_complete": True,
        "query_count": 8,
        "unique_queries": 7
    }
}
```

### Batch-Validierung

#### validate_pipeline_output()

```python
def validate_pipeline_output(self, output_data: Union[List, Dict], 
                           validation_type: str = "comprehensive") -> dict
```

**Parameter:**
- `output_data`: Pipeline-Output-Daten
- `validation_type`: Art der Validierung ("comprehensive", "fast", "quality_only")

**Beispiel:**
```python
validator = QualityValidator()

# Comprehensive validation
result = validator.validate_pipeline_output(
    output_data=pipeline_results,
    validation_type="comprehensive"
)

print(f"Overall Quality: {result['overall_quality']:.2%}")
print(f"Issues Found: {len(result['issues_found'])}")
print(f"Recommendations: {result['recommendations']}")
```

---

## 🎯 Performance Classes

### PipelineMetrics

```python
@dataclass
class PipelineMetrics:
    total_documents: int = 0
    processed_documents: int = 0
    failed_documents: int = 0
    total_processing_time: float = 0.0
    average_processing_time: float = 0.0
    throughput_per_second: float = 0.0
    quality_scores: List[float] = field(default_factory=list)
    memory_usage_peak: float = 0.0
    memory_usage_current: float = 0.0
    cache_hit_rate: float = 0.0
    error_rate: float = 0.0
    worker_utilization: Dict[str, float] = field(default_factory=dict)
    stage_timings: Dict[str, List[float]] = field(default_factory=dict)
    bottlenecks: List[str] = field(default_factory=list)
```

### PerformanceMonitor

```python
class PerformanceMonitor:
    def record_metric(self, metric: str, value: float, timestamp: Optional[datetime] = None)
    def predict_performance(self, metric: str, lookahead_minutes: int = 10) -> Optional[float]
    def update_baselines(self)
```

### CircuitBreaker

```python
class CircuitBreaker:
    def __init__(self, failure_threshold: int = 5, timeout: int = 60)
    def call(self, func: Callable, *args, **kwargs)
```

### AdvancedCacheManager

```python
class AdvancedCacheManager:
    def __init__(self, use_redis: bool = False, redis_host: str = 'localhost')
    def get(self, key: str) -> Optional[Any]
    def set(self, key: str, value: Any, ttl: int = 3600)
    def get_hit_rate(self) -> float
```

---

## 📊 Configuration Schema

### Erweiterte Konfiguration

```json
{
    "optimization_level": "standard|advanced|maximum",
    "max_workers": 8,
    "batch_size": 100,
    "memory_limit_mb": 4096,
    "cache_enabled": true,
    "use_redis_cache": false,
    "quality_threshold": 0.7,
    "enable_monitoring": true,
    "auto_scaling": true,
    "max_auto_scale_workers": 16,
    "monitoring_interval": 30,
    "circuit_breaker_threshold": 5,
    "circuit_breaker_timeout": 60,
    "alert_thresholds": {
        "error_rate": 0.05,
        "memory_usage": 0.9,
        "processing_time": 300
    },
    "plugin_directory": "plugins/",
    "redis_config": {
        "host": "localhost",
        "port": 6379,
        "ttl": 3600
    }
}
```

---

## 🔌 Plugin System

### Plugin Development

```python
class CustomPlugin:
    def __init__(self):
        self.name = "custom_plugin"
        
    def process_data(self, data: Dict) -> Dict:
        # Custom processing logic
        return enhanced_data
    
    def on_alert(self, alert: Dict):
        # Custom alert handling
        pass

# Plugin Registration
orchestrator = AdvancedPipelineOrchestrator()
orchestrator.plugin_manager.register_plugin("custom", CustomPlugin)
orchestrator.plugin_manager.register_hook("alert_sent", custom_plugin.on_alert)
```

---

## 🚀 Advanced Usage Examples

### Complete Enterprise Pipeline

```python
import asyncio
from Scripts.advanced_pipeline_orchestrator import AdvancedPipelineOrchestrator

async def enterprise_pipeline():
    # Enterprise configuration
    config = {
        'optimization_level': 'maximum',
        'max_workers': 16,
        'use_redis_cache': True,
        'enable_monitoring': True,
        'auto_scaling': True,
        'alert_thresholds': {
            'error_rate': 0.02,
            'memory_usage': 0.85
        }
    }
    
    orchestrator = AdvancedPipelineOrchestrator(config)
    
    # Process multiple datasets
    datasets = ['dataset1.jsonl', 'dataset2.jsonl', 'dataset3.jsonl']
    
    results = []
    for dataset in datasets:
        result = await orchestrator.process_pipeline_async(
            input_data=dataset,
            processing_mode="auto"
        )
        results.append(result)
    
    # Generate comprehensive report
    report = orchestrator.generate_comprehensive_report("enterprise_report.json")
    
    # Performance analysis
    print(f"Total Documents: {orchestrator.metrics.total_documents}")
    print(f"Success Rate: {(1 - orchestrator.metrics.error_rate):.2%}")
    print(f"Average Processing Time: {orchestrator.metrics.average_processing_time:.2f}s")
    print(f"Cache Hit Rate: {orchestrator.cache_manager.get_hit_rate():.2%}")
    
    return results, report

# Run enterprise pipeline
results, report = asyncio.run(enterprise_pipeline())
```

---

**📝 Letzte Aktualisierung**: 26. Mai 2025  
**🔧 API Version**: 3.0.0 (Enhanced)  
**📄 Dokumentations-Version**: 2.0.0
