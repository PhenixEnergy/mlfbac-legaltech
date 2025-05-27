# ⚙️ LegalTech NLP Pipeline - Konfigurationsreferenz

[![Configuration](https://img.shields.io/badge/Configuration-Complete-success)](./DEVELOPER_GUIDE.md)
[![JSON](https://img.shields.io/badge/Format-JSON-blue)](https://json.org)

## 📋 Übersicht

Vollständige Konfigurationsreferenz für die LegalTech NLP Pipeline mit allen verfügbaren Einstellungen, Standardwerten und Optimierungsoptionen.

## 🎯 Hauptkonfigurationsdatei

### optimization_config.json

```json
{
  "prompt_generation": {
    "max_templates_per_type": 10,
    "complexity_levels": ["basic", "intermediate", "advanced", "expert"],
    "enable_domain_adaptation": true,
    "auto_detect_complexity": true,
    "template_selection_strategy": "adaptive",
    "fallback_template": "generic_legal",
    "keyword_extraction": {
      "min_frequency": 2,
      "max_keywords": 20,
      "boost_legal_terms": true,
      "weight_factors": {
        "paragraph_position": 0.8,
        "legal_citations": 1.2,
        "structural_markers": 0.9
      }
    },
    "quality_filters": {
      "min_prompt_length": 50,
      "max_prompt_length": 1000,
      "require_context_integration": true,
      "validate_legal_relevance": true
    }
  },
  "segmentation": {
    "algorithms": {
      "structural": {
        "weight": 0.4,
        "enabled": true,
        "patterns": {
          "major_headings": true,
          "numbered_sections": true,
          "roman_numerals": true
        }
      },
      "semantic": {
        "weight": 0.4,
        "enabled": true,
        "similarity_threshold": 0.25,
        "vector_method": "tfidf",
        "legal_term_boost": 1.5
      },
      "keyword": {
        "weight": 0.2,
        "enabled": true,
        "keywords": [
          "Sachverhalt", "Rechtsfrage", "Anspruchsgrundlage",
          "Tatbestandsvoraussetzungen", "Subsumtion", "Rechtsfolge",
          "Ergebnis", "Literatur", "Rechtsprechung"
        ]
      }
    },
    "quality_filters": {
      "min_segment_length": 50,
      "max_segment_length": 2000,
      "min_coherence": 0.6,
      "min_completeness": 0.7,
      "min_relevance": 0.5,
      "require_legal_content": true
    },
    "segment_types": {
      "SACHVERHALT": {
        "priority": 5,
        "min_length": 100,
        "max_length": 1500,
        "quality_weight": 1.2
      },
      "RECHTSFRAGE": {
        "priority": 5,
        "min_length": 50,
        "max_length": 800,
        "quality_weight": 1.3
      },
      "ANSPRUCHSGRUNDLAGE": {
        "priority": 4,
        "min_length": 80,
        "max_length": 1200,
        "quality_weight": 1.1
      },
      "SUBSUMTION": {
        "priority": 4,
        "min_length": 100,
        "max_length": 2000,
        "quality_weight": 1.0
      },
      "ERGEBNIS": {
        "priority": 3,
        "min_length": 50,
        "max_length": 800,
        "quality_weight": 0.9
      }
    },
    "enhancement_features": {
      "cross_reference_detection": true,
      "legal_concept_extraction": true,
      "argument_structure_analysis": true,
      "citation_preservation": true
    }
  },
  "rag_training": {
    "queries_per_segment": 8,
    "enable_multi_perspective": true,
    "diversity_factor": 0.8,
    "quality_filter_threshold": 0.6,
    "query_strategies": [
      {
        "name": "factual_extraction",
        "weight": 1.0,
        "templates": [
          "Was sind die Fakten zu {topic}?",
          "Welche Tatsachen sind relevant für {topic}?",
          "Beschreibe den Sachverhalt bezüglich {topic}."
        ]
      },
      {
        "name": "analytical_reasoning",
        "weight": 1.2,
        "templates": [
          "Analysiere die rechtlichen Aspekte von {topic}.",
          "Welche rechtlichen Schlussfolgerungen ergeben sich aus {topic}?",
          "Prüfe die juristische Argumentation zu {topic}."
        ]
      },
      {
        "name": "comparative_analysis",
        "weight": 0.9,
        "templates": [
          "Vergleiche {topic} mit ähnlichen Fällen.",
          "Wie unterscheidet sich {topic} von Standardfällen?",
          "Welche Parallelen gibt es zu {topic}?"
        ]
      },
      {
        "name": "precedent_search",
        "weight": 1.1,
        "templates": [
          "Welche Präzedenzfälle gibt es zu {topic}?",
          "Finde relevante Rechtsprechung zu {topic}.",
          "Welche Urteile behandeln {topic}?"
        ]
      },
      {
        "name": "norm_application",
        "weight": 1.3,
        "templates": [
          "Wie wenden sich die Normen auf {topic} an?",
          "Welche Gesetze regeln {topic}?",
          "Prüfe die Normgrundlagen für {topic}."
        ]
      }
    ],
    "diversity_metrics": {
      "semantic_diversity": 0.8,
      "structural_diversity": 0.6,
      "perspective_diversity": 0.9,
      "lexical_diversity": 0.7
    }
  },
  "performance": {
    "batch_processing": {
      "enabled": true,
      "batch_size": 100,
      "max_concurrent_batches": 4,
      "memory_limit_mb": 4096
    },
    "caching": {
      "enabled": true,
      "cache_directory": "optimization_cache",
      "max_cache_size_mb": 1024,
      "cache_expiry_hours": 24,
      "cache_compression": true
    },
    "parallel_processing": {
      "enabled": true,
      "max_workers": 4,
      "chunk_size": "auto",
      "load_balancing": "dynamic"
    },
    "memory_management": {
      "streaming_threshold_mb": 512,
      "garbage_collection_interval": 100,
      "memory_monitoring": true
    }
  },
  "output_formats": {
    "fine_tuning": {
      "enabled": true,
      "format": "conversation",
      "system_message": "Du bist ein KI-Assistent, der juristische Gutachtentexte erstellt. Antworte präzise, strukturiert und rechtlich fundiert.",
      "include_metadata": false,
      "token_limit": null
    },
    "rag_training": {
      "enabled": true,
      "include_query_metadata": true,
      "format": "query_response_pairs",
      "quality_annotation": true
    },
    "rag_knowledge_base": {
      "enabled": true,
      "include_embeddings": false,
      "metadata_fields": [
        "gutachten_nr", "erscheinungsdatum", "normen",
        "segment_type", "quality_score", "legal_concepts"
      ],
      "indexing_strategy": "hierarchical"
    },
    "analysis_report": {
      "enabled": true,
      "include_statistics": true,
      "include_quality_metrics": true,
      "include_processing_log": true,
      "format": "detailed_json"
    }
  },
  "logging": {
    "level": "INFO",
    "file": "pipeline.log",
    "max_file_size_mb": 100,
    "backup_count": 5,
    "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    "include_performance_metrics": true
  },
  "validation": {
    "input_validation": {
      "required_fields": ["gutachten_nr", "text"],
      "min_text_length": 100,
      "max_text_length": 50000,
      "encoding_validation": true
    },
    "output_validation": {
      "validate_json_structure": true,
      "validate_prompt_quality": true,
      "validate_segment_coherence": true,
      "quality_threshold": 0.6
    }
  }
}
```

## 🔧 Umgebungsvariablen

### Performance-Konfiguration

```bash
# Speicher-Management
LEGALTECH_MAX_MEMORY=4096           # Maximaler RAM in MB
LEGALTECH_CACHE_SIZE=1000           # Cache-Größe (Einträge)
LEGALTECH_STREAMING_THRESHOLD=512   # Streaming ab X MB

# Parallele Verarbeitung
LEGALTECH_PARALLEL_WORKERS=4        # Anzahl Worker-Prozesse
LEGALTECH_BATCH_SIZE=100            # Batch-Größe
LEGALTECH_CHUNK_SIZE=auto           # Chunk-Größe (auto/fixed)

# I/O Optimierung
LEGALTECH_IO_BUFFER_SIZE=8192       # I/O Buffer in Bytes
LEGALTECH_ASYNC_IO=true             # Asynchrone I/O aktivieren
```

### Logging-Konfiguration

```bash
# Log-Level und Ausgabe
LEGALTECH_LOG_LEVEL=INFO            # DEBUG, INFO, WARNING, ERROR, CRITICAL
LEGALTECH_LOG_FILE=pipeline.log     # Log-Datei Pfad
LEGALTECH_CONSOLE_LOGGING=true      # Konsolen-Ausgabe
LEGALTECH_STRUCTURED_LOGGING=false  # JSON-formatierte Logs

# Performance-Logging
LEGALTECH_PROFILE_PERFORMANCE=false # Performance-Profiling
LEGALTECH_MEMORY_TRACKING=false     # Memory-Usage Tracking
LEGALTECH_TIME_OPERATIONS=false     # Zeitmessung für Operationen
```

### Pfad-Konfiguration

```bash
# Dateipfade
LEGALTECH_CONFIG_PATH=optimization_config.json
LEGALTECH_CACHE_DIR=optimization_cache
LEGALTECH_OUTPUT_DIR=output
LEGALTECH_TEMP_DIR=%TEMP%\legaltech

# Datenbank-Pfade
LEGALTECH_DATABASE_DIR=Database
LEGALTECH_TRAINING_DATA_DIR=Database\Fine_Tuning
LEGALTECH_RAG_DATA_DIR=Database\RAG_Training
```

### Debug und Entwicklung

```bash
# Debug-Modi
LEGALTECH_DEBUG_MODE=false          # Debug-Modus aktivieren
LEGALTECH_VERBOSE_OUTPUT=false      # Ausführliche Ausgaben
LEGALTECH_SAVE_INTERMEDIATE=false   # Zwischenergebnisse speichern

# Entwicklung
LEGALTECH_DEV_MODE=false            # Entwicklungsmodus
LEGALTECH_SKIP_VALIDATION=false     # Validierung überspringen
LEGALTECH_FORCE_REPROCESSING=false  # Cache ignorieren
```

## 📊 Spezialisierte Konfigurationen

### Entwicklungskonfiguration (dev_config.json)

```json
{
  "extends": "optimization_config.json",
  "overrides": {
    "performance": {
      "batch_processing": {
        "batch_size": 10
      },
      "caching": {
        "enabled": false
      }
    },
    "logging": {
      "level": "DEBUG",
      "include_performance_metrics": true
    },
    "validation": {
      "output_validation": {
        "quality_threshold": 0.3
      }
    }
  }
}
```

### Produktionskonfiguration (production_config.json)

```json
{
  "extends": "optimization_config.json",
  "overrides": {
    "performance": {
      "batch_processing": {
        "batch_size": 500,
        "max_concurrent_batches": 8
      },
      "parallel_processing": {
        "max_workers": 8
      },
      "memory_management": {
        "streaming_threshold_mb": 256
      }
    },
    "logging": {
      "level": "WARNING",
      "include_performance_metrics": false
    },
    "validation": {
      "output_validation": {
        "quality_threshold": 0.8
      }
    }
  }
}
```

### Test-Konfiguration (test_config.json)

```json
{
  "extends": "optimization_config.json",
  "overrides": {
    "segmentation": {
      "quality_filters": {
        "min_segment_length": 20,
        "min_coherence": 0.3
      }
    },
    "rag_training": {
      "queries_per_segment": 3,
      "quality_filter_threshold": 0.2
    },
    "performance": {
      "caching": {
        "enabled": false
      }
    }
  }
}
```

## 🎛️ Template-Konfiguration

### Prompt-Templates Struktur

```json
{
  "prompt_templates": {
    "sachverhalt": {
      "basic": [
        "Gib den Sachverhalt für Gutachten Nr. {gutachten_nr} wieder.",
        "Beschreibe die Fakten des Falls Nr. {gutachten_nr}.",
        "Stelle den Sachverhalt von Gutachten {gutachten_nr} dar."
      ],
      "intermediate": [
        "Gib den Sachverhalt für Gutachten Nr. {gutachten_nr} vom {erscheinungsdatum} systematisch wieder unter Berücksichtigung von {normen}.",
        "Beschreibe den entscheidungserheblichen Sachverhalt des Gutachtens Nr. {gutachten_nr} strukturiert."
      ],
      "advanced": [
        "Analysiere den komplexen Sachverhalt des Gutachtens Nr. {gutachten_nr} vom {erscheinungsdatum} unter besonderer Berücksichtigung von {normen}. Arbeite die rechtlich relevanten Fakten systematisch heraus."
      ],
      "expert": [
        "Rekonstruiere den vielschichtigen Sachverhalt des Gutachtens Nr. {gutachten_nr} vom {erscheinungsdatum} unter dogmatischer Würdigung der Normen {normen}. Strukturiere nach streitigem und unstreitigem Sachverhalt und arbeite die prozessual relevanten Tatsachen heraus."
      ]
    },
    "rechtsfrage": {
      "basic": [
        "Was ist die Rechtsfrage in Gutachten Nr. {gutachten_nr}?",
        "Identifiziere die Rechtsproblematik von Fall {gutachten_nr}."
      ],
      "intermediate": [
        "Formuliere die zentrale Rechtsfrage des Gutachtens Nr. {gutachten_nr} unter Bezugnahme auf {normen}.",
        "Analysiere die Rechtsproblematik von Gutachten {gutachten_nr} systematisch."
      ],
      "advanced": [
        "Identifiziere und strukturiere die komplexe Rechtsproblematik des Gutachtens Nr. {gutachten_nr} vom {erscheinungsdatum} unter Berücksichtigung der Normen {normen}."
      ],
      "expert": [
        "Entwickle die vielschichtige Rechtsproblematik des Gutachtens Nr. {gutachten_nr} dogmatisch und arbeite die Interdependenzen zwischen den Normen {normen} heraus."
      ]
    }
  }
}
```

## 🔍 Segment-Klassifizierung

### Erkennungsmuster

```json
{
  "segment_classification": {
    "patterns": {
      "SACHVERHALT": {
        "keywords": ["Sachverhalt", "Tatsachen", "Fall", "Geschehen"],
        "regex_patterns": [
          "I\\.|1\\.|A\\.|Sachverhalt",
          "Tatsächliche\\s+Feststellungen",
          "Der\\s+Fall"
        ],
        "position_hints": ["beginning", "after_heading"],
        "content_indicators": [
          "chronological_narrative",
          "factual_statements",
          "date_references"
        ]
      },
      "RECHTSFRAGE": {
        "keywords": ["Rechtsfrage", "Problem", "Streitpunkt", "Frage"],
        "regex_patterns": [
          "II\\.|2\\.|B\\.|Rechtsfrage",
          "Streitgegenstand",
          "Zu\\s+prüfen"
        ],
        "position_hints": ["after_sachverhalt", "early_section"],
        "content_indicators": [
          "question_formulation",
          "legal_uncertainty",
          "dispute_indication"
        ]
      },
      "SUBSUMTION": {
        "keywords": ["Prüfung", "Subsumtion", "Anwendung", "Würdigung"],
        "regex_patterns": [
          "III\\.|3\\.|C\\.|Rechtliche\\s+Würdigung",
          "Prüfung\\s+der",
          "Subsumtion"
        ],
        "position_hints": ["middle_section", "main_content"],
        "content_indicators": [
          "norm_application",
          "case_law_citation",
          "legal_reasoning"
        ]
      }
    }
  }
}
```

## 📈 Qualitätsmetriken

### Bewertungskriterien

```json
{
  "quality_metrics": {
    "coherence": {
      "weight": 0.3,
      "factors": {
        "logical_flow": 0.4,
        "topic_consistency": 0.3,
        "argument_structure": 0.3
      },
      "thresholds": {
        "excellent": 0.9,
        "good": 0.7,
        "acceptable": 0.5,
        "poor": 0.3
      }
    },
    "completeness": {
      "weight": 0.25,
      "factors": {
        "information_coverage": 0.5,
        "argument_depth": 0.3,
        "context_inclusion": 0.2
      }
    },
    "relevance": {
      "weight": 0.25,
      "factors": {
        "legal_relevance": 0.6,
        "topic_relevance": 0.4
      }
    },
    "complexity": {
      "weight": 0.2,
      "factors": {
        "legal_terminology": 0.4,
        "argument_sophistication": 0.3,
        "citation_quality": 0.3
      }
    }
  }
}
```

## 🚀 Performance-Tuning

### Optimierung für verschiedene Szenarien

#### Hohe Geschwindigkeit (High Throughput)

```json
{
  "performance_profile": "high_throughput",
  "settings": {
    "batch_size": 1000,
    "parallel_workers": 8,
    "caching": {
      "aggressive_caching": true,
      "cache_size_mb": 2048
    },
    "quality_filters": {
      "reduced_validation": true,
      "min_quality_threshold": 0.5
    },
    "algorithms": {
      "semantic_analysis": false,
      "structural_only": true
    }
  }
}
```

#### Hohe Qualität (High Quality)

```json
{
  "performance_profile": "high_quality",
  "settings": {
    "batch_size": 50,
    "parallel_workers": 2,
    "algorithms": {
      "semantic_analysis": true,
      "multiple_validation_passes": true
    },
    "quality_filters": {
      "strict_validation": true,
      "min_quality_threshold": 0.8
    },
    "rag_training": {
      "queries_per_segment": 12,
      "diversity_factor": 0.95
    }
  }
}
```

#### Ausgeglichen (Balanced)

```json
{
  "performance_profile": "balanced",
  "settings": {
    "batch_size": 200,
    "parallel_workers": 4,
    "caching": {
      "moderate_caching": true
    },
    "quality_filters": {
      "standard_validation": true,
      "min_quality_threshold": 0.7
    }
  }
}
```

## 🔒 Sicherheit und Validierung

### Input-Validierung

```json
{
  "security": {
    "input_sanitization": {
      "remove_html_tags": true,
      "validate_encoding": true,
      "max_input_size_mb": 100,
      "allowed_file_types": [".json", ".jsonl", ".txt"]
    },
    "path_validation": {
      "restrict_to_workspace": true,
      "prevent_directory_traversal": true,
      "validate_permissions": true
    },
    "resource_limits": {
      "max_memory_per_process_mb": 2048,
      "max_processing_time_minutes": 60,
      "max_concurrent_processes": 8
    }
  }
}
```

## 📝 Konfiguration laden

### Python-Code Beispiele

```python
import json
import os
from typing import Dict, Any

class ConfigManager:
    def __init__(self, config_path: str = "optimization_config.json"):
        self.config_path = config_path
        self.config = self.load_config()
    
    def load_config(self) -> Dict[str, Any]:
        """Lädt Konfiguration mit Environment Variable Überschreibung."""
        
        # Basis-Konfiguration laden
        with open(self.config_path, 'r', encoding='utf-8') as f:
            config = json.load(f)
        
        # Environment Variables überschreiben
        config = self._apply_env_overrides(config)
        
        # Validierung
        self._validate_config(config)
        
        return config
    
    def _apply_env_overrides(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """Wendet Environment Variable Überschreibungen an."""
        
        # Beispiel-Überschreibungen
        if os.getenv('LEGALTECH_MAX_MEMORY'):
            config['performance']['memory_limit_mb'] = int(os.getenv('LEGALTECH_MAX_MEMORY'))
        
        if os.getenv('LEGALTECH_LOG_LEVEL'):
            config['logging']['level'] = os.getenv('LEGALTECH_LOG_LEVEL')
        
        if os.getenv('LEGALTECH_PARALLEL_WORKERS'):
            config['performance']['parallel_processing']['max_workers'] = int(os.getenv('LEGALTECH_PARALLEL_WORKERS'))
        
        return config
    
    def _validate_config(self, config: Dict[str, Any]) -> None:
        """Validiert Konfiguration auf Konsistenz."""
        
        # Erforderliche Schlüssel prüfen
        required_keys = ['prompt_generation', 'segmentation', 'rag_training', 'performance']
        for key in required_keys:
            if key not in config:
                raise ValueError(f"Required config key missing: {key}")
        
        # Wertebereiche prüfen
        if config['segmentation']['quality_filters']['min_coherence'] < 0 or \
           config['segmentation']['quality_filters']['min_coherence'] > 1:
            raise ValueError("min_coherence must be between 0 and 1")
    
    def get(self, key_path: str, default: Any = None) -> Any:
        """Holt Konfigurationswert mit Dot-Notation."""
        keys = key_path.split('.')
        value = self.config
        
        for key in keys:
            if isinstance(value, dict) and key in value:
                value = value[key]
            else:
                return default
        
        return value
    
    def update(self, key_path: str, value: Any) -> None:
        """Aktualisiert Konfigurationswert."""
        keys = key_path.split('.')
        config_ref = self.config
        
        for key in keys[:-1]:
            if key not in config_ref:
                config_ref[key] = {}
            config_ref = config_ref[key]
        
        config_ref[keys[-1]] = value

# Verwendung
config_manager = ConfigManager()

# Werte abrufen
batch_size = config_manager.get('performance.batch_processing.batch_size', 100)
log_level = config_manager.get('logging.level', 'INFO')

# Werte aktualisieren
config_manager.update('performance.parallel_processing.max_workers', 8)
```

## 🎯 Konfiguration für spezielle Anwendungsfälle

### Große Datensätze (Big Data)

```json
{
  "name": "big_data_config",
  "description": "Optimiert für sehr große Datensätze (>10GB)",
  "settings": {
    "performance": {
      "streaming_mode": true,
      "chunk_processing": true,
      "memory_limit_mb": 1024,
      "disk_caching": true
    },
    "segmentation": {
      "simplified_analysis": true,
      "batch_segmentation": true
    }
  }
}
```

### Echtzeit-Verarbeitung (Real-time)

```json
{
  "name": "realtime_config",
  "description": "Optimiert für Echtzeit-Verarbeitung",
  "settings": {
    "performance": {
      "preload_models": true,
      "keep_alive_workers": true,
      "aggressive_caching": true
    },
    "quality_filters": {
      "fast_validation": true,
      "skip_heavy_analysis": true
    }
  }
}
```

### Höchste Qualität (Research)

```json
{
  "name": "research_config",
  "description": "Maximale Qualität für Forschungszwecke",
  "settings": {
    "segmentation": {
      "multiple_algorithm_consensus": true,
      "human_validation_integration": true
    },
    "rag_training": {
      "exhaustive_query_generation": true,
      "quality_scoring_detailed": true
    }
  }
}
```

---

**📝 Letzte Aktualisierung**: 25. Mai 2025  
**⚙️ Konfiguration Version**: 2.0.0  
**📄 Dokumentations-Version**: 1.0.0
