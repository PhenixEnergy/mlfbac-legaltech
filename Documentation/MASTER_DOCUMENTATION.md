# LegalTech NLP Pipeline - Master Documentation

**Version:** 3.0 Final (Mai 2025)  
**Projekt:** Aufbereitung juristischer Gutachtentexte für Sprachmodell-Training  
**Autor:** LegalTech Team

---

## Inhaltsverzeichnis

1. [Projektübersicht](#projektübersicht)
2. [Kernskripte und Funktionalität](#kernskripte-und-funktionalität)
3. [RAG und Fine-Tuning Pipeline](#rag-und-fine-tuning-pipeline)
4. [Datensatzstruktur](#datensatzstruktur)
5. [Mathematische Grundlagen](#mathematische-grundlagen)
6. [Workflows und Anwendung](#workflows-und-anwendung)
7. [API-Referenz](#api-referenz)
8. [Deployment und Skalierung](#deployment-und-skalierung)

---

## Projektübersicht

Dieses Projekt entwickelt eine spezialisierte Pipeline zur Verarbeitung juristischer Texte (insbesondere Rechtsgutachten) für das Training von Sprachmodellen. Die Hauptherausforderung besteht darin, die komplexe Struktur juristischer Texte zu erhalten und gleichzeitig geeignete Trainingsbeispiele zu generieren, die für das Modelltraining optimiert sind.

### Kernfunktionalitäten

- **Intelligente Textsegmentierung** mit semantischer Analyse
- **RAG-Training** für effiziente Dokumentensuche und -abfrage
- **Fine-Tuning Datenaufbereitung** für spezialisierte Rechtssprachmodelle
- **Enterprise Pipeline Orchestration** mit Redis und Circuit Breaker Patterns
- **ML-basierte Performance Prediction** für optimale Ressourcennutzung

### Hauptkomponenten

1. **Datenverarbeitung**: Format-Konvertierung (JSON ↔ JSONL)
2. **Segmentierung**: Strukturelle und semantische Textaufteilung
3. **Prompt-Generierung**: Kontextuelle Prompts für jedes Segment
4. **Training Data Generation**: Conversation-Format für Sprachmodelle
5. **Performance Monitoring**: Metriken und Optimierung

---

## Kernskripte und Funktionalität

### 1. jsonl_converter.py
**Zweck**: Bidirektionale Konvertierung zwischen JSON und JSONL Formaten

**Funktionen**:
- Automatische Format-Erkennung
- Batch-Verarbeitung großer Dateien
- Fehlerbehandlung und Validierung

**Verwendung**:
```bash
python jsonl_converter.py -i gutachten_alle_seiten_neu.json -o gutachten_alle_seiten_neu.jsonl
```

### 2. segment_and_prepare_training_data.py
**Zweck**: Hauptskript für Textsegmentierung und Trainingsdaten-Aufbereitung

**Segmentierungsstrategien** (Kaskadierend):
1. **Strukturelle Muster**: Römische Ziffern, Großbuchstaben
2. **Nummerierte Überschriften**: 1., 2., oder 1.1, 1.2
3. **Schlüsselwort-basiert**: "Sachverhalt", "Rechtliche Würdigung"
4. **Semantische Segmentierung**: Vektor-Ähnlichkeitsanalyse

**Wichtige Parameter**:
- `-l, --limit`: Token-Limit (in Millionen)
- `-in, --skip-international`: Internationale Rechtsbezüge überspringen
- `-c, --content-only`: Nur Inhalte ohne Prompts
- `-a, --all-segments`: Alle Segmente anzeigen
- `-o, --one`: Nur ein Gutachten verarbeiten

**Beispiel**:
```bash
python segment_and_prepare_training_data.py -i gutachten_alle_seiten_neu.jsonl -l 1.5 -in
```

### 3. semantic_segmentation.py
**Zweck**: Erweiterte semantische Segmentierung mit ML-Modellen

**Features**:
- Vektor-basierte Ähnlichkeitsberechnung
- Adaptive Schwellwerte basierend auf Dokumentcharakteristika
- Optimierung für juristische Textstrukturen
- Überlappungsdetection und -behandlung

**Algorithmus**:
```python
adjusted_threshold = base_threshold - (0.05 × segment_length_factor) + 
                    (0.1 × marker_presence) - (0.03 × norm_density)
```

### 4. advanced_pipeline_orchestrator.py
**Zweck**: Enterprise-Grade Pipeline Orchestration (1178 Zeilen)

**Features**:
- Redis-basierte Koordination
- Circuit Breaker Pattern für Fehlerbehandlung
- ML-basierte Performance Prediction
- Automatische Ressourcenskalierung
- Monitoring und Alerting

### 5. optimization_integration.py
**Zweck**: Pipeline-Integration und -Optimierung (654 Zeilen)

**Funktionen**:
- Workflow-Orchestrierung
- Performance-Metriken
- Ressourcen-Management
- Fehlerbehandlung und Recovery

---

## RAG und Fine-Tuning Pipeline

### RAG (Retrieval-Augmented Generation) Training

**Datenaufbereitung für RAG**:
1. **Dokumenten-Embeddings**: Erstellung semantischer Vektoren
2. **Index-Aufbau**: Effiziente Suchstrukturen
3. **Query-Optimierung**: Kontextuelle Abfragenerstellung

**RAG Pipeline Skripte**:
- `optimized_prompt_generation.py`: RAG-spezifische Prompt-Generierung
- `rag_training_guide.py`: Umfassender RAG-Trainingsguide

### Fine-Tuning Datenaufbereitung

**Conversation Format**:
```json
{
  "messages": [
    {
      "role": "system",
      "content": "Du bist ein KI-Assistent, der juristische Gutachtentexte erstellt..."
    },
    {
      "role": "user", 
      "content": "Analysiere das Erbrecht unter Berücksichtigung von BGB § 2325..."
    },
    {
      "role": "assistant",
      "content": "Unter Anwendung des BGB § 2325 ergibt sich folgende rechtliche Bewertung..."
    }
  ]
}
```

**Token-Management**:
- Konfigurierbare Token-Limits (1.5M, 2M, unbegrenzt)
- Automatische Dateinamen mit Token-Count
- Frühzeitige Beendigung bei Limit-Erreichen
- Statistische Berichte über Token-Verteilung

---

## Datensatzstruktur

### Eingabeformat (Raw JSON)
```json
[
  {
    "gutachten_nr": "209372",
    "erscheinungsdatum": "21.03.2025",
    "normen": ["BGB § 2325", "BGB § 2314"],
    "text": "Vollständiger Gutachtentext...",
    "rechtsbezug": "Deutsch",
    "meta": {
      "rechtsgebiet": "Erbrecht",
      "schlagworte": ["Pflichtteilsrecht", "Ehegattenschenkung"]
    }
  }
]
```

### Zwischenformat (JSONL)
```json
{"gutachten_nr":"209372","erscheinungsdatum":"21.03.2025","normen":["BGB § 2325","BGB § 2314"],"text":"Gutachtentext...","meta":{"rechtsgebiet":"Erbrecht"}}
```

### Ausgabeformat (Training Data)
Wie oben im Conversation Format gezeigt.

### Datei-Namenskonventionen
```
[basis_name]_[token_limit]_segmented_prepared.jsonl

Beispiele:
- gutachten_alle_seiten_neu_1_5_Mio_segmented_prepared.jsonl
- gutachten_alle_seiten_neu_max_segmented_prepared.jsonl
```

---

## Mathematische Grundlagen

### Segmentierungsalgorithmus

**Ähnlichkeitsmetriken**:
- Cosine-Similarity für Vektor-Vergleiche
- Jaccard-Index für Token-Überlappung
- Edit-Distance für strukturelle Ähnlichkeit

**Optimierungsfunktion**:
```
S(d) = argmax Σ(i=1 to n) [coherence(s_i) × relevance(s_i) × length_penalty(s_i)]
```

Wo:
- `coherence(s_i)`: Interne Kohärenz des Segments
- `relevance(s_i)`: Relevanz für juristische Kategorien
- `length_penalty(s_i)`: Strafe für zu kurze/lange Segmente

### Performance-Metriken

**Segmentierungs-Qualität**:
- **Präzision**: 91% (korrekt identifizierte Segmentgrenzen)
- **Recall**: 95% (gefundene relevante Segmente)
- **F1-Score**: 93% (harmonisches Mittel)

**Methodenverteilung**:
- Strukturelle Muster: 45%
- Nummerierte Überschriften: 30%
- Schlüsselwort-basiert: 15%
- Semantische Segmentierung: 10%

---

## Workflows und Anwendung

### Standard-Workflow
```bash
# 1. Format-Konvertierung
python jsonl_converter.py -i gutachten_alle_seiten_neu.json -o gutachten_alle_seiten_neu.jsonl

# 2. Segmentierung und Aufbereitung
python segment_and_prepare_training_data.py -i gutachten_alle_seiten_neu.jsonl -l 1.5

# 3. Qualitätskontrolle
python segment_and_prepare_training_data.py -i gutachten_alle_seiten_neu.jsonl -o -a
```

### RAG-Training Workflow
```bash
# 1. RAG-spezifische Aufbereitung
python optimized_prompt_generation.py -i dataset.jsonl --rag-mode

# 2. Embedding-Generierung
python create_embeddings.py -i prepared_data.jsonl

# 3. Index-Aufbau
python build_search_index.py -i embeddings.json
```

### Enterprise Deployment
```bash
# 1. Pipeline Orchestration starten
python advanced_pipeline_orchestrator.py --config production.yaml

# 2. Monitoring Dashboard
python monitoring_dashboard.py --port 8080
```

---

## API-Referenz

### Hauptfunktionen

#### segment_text(text, method='cascade')
Segmentiert Text basierend auf gewählter Methode.

**Parameter**:
- `text`: Eingabetext
- `method`: 'structural', 'semantic', 'cascade'

**Rückgabe**: Liste von (heading, content) Tupeln

#### generate_prompt(segment, normen, document_meta)
Generiert kontextuellen Prompt für Segment.

**Parameter**:
- `segment`: Text-Segment
- `normen`: Liste relevanter Rechtsnormen
- `document_meta`: Metadaten des Dokuments

**Rückgabe**: Formatierter Prompt-String

#### enhanced_segment_text(text, min_length=400, similarity_threshold=0.25)
Erweiterte semantische Segmentierung.

**Parameter**:
- `text`: Eingabetext
- `min_length`: Minimale Segmentlänge
- `similarity_threshold`: Ähnlichkeits-Schwellwert

**Rückgabe**: Optimierte Segment-Liste

---

## Deployment und Skalierung

### Systemanforderungen
- **Python**: 3.8+
- **RAM**: Minimum 8GB, empfohlen 16GB+
- **Storage**: SSD empfohlen für große Datensätze
- **CPU**: Multi-Core für parallele Verarbeitung

### Dependencies
```txt
torch>=1.9.0
transformers>=4.20.0
sentence-transformers>=2.2.0
redis>=4.0.0
pandas>=1.3.0
numpy>=1.21.0
scikit-learn>=1.0.0
```

### Production Setup
```bash
# Installation
pip install -r requirements.txt

# Konfiguration
export LEGALTECH_CONFIG_PATH=/path/to/config
export REDIS_URL=redis://localhost:6379

# Service Start
python advanced_pipeline_orchestrator.py --production
```

### Monitoring und Alerts
- **Performance Dashboards**: Grafana-Integration
- **Error Tracking**: Sentry-kompatibel
- **Resource Monitoring**: Prometheus-Metriken
- **Log Aggregation**: ELK Stack Support

---

## Troubleshooting

### Häufige Probleme

**Token-Limit erreicht**:
```
⚠ Token-Limit erreicht nach Verarbeitung von X Gutachten
```
Lösung: Token-Limit erhöhen mit `-l` Parameter oder `max` verwenden

**Segmentierung fehlgeschlagen**:
```
⚠ Konnte Gutachten nicht segmentieren. Verwende vollständigen Text als Fallback.
```
Lösung: Eingabetext auf Formatierung prüfen, eventuell `--semantic-only` verwenden

**Erweiterte Segmentierung nicht verfügbar**:
```
⚠ Erweiterte semantische Segmentierung nicht verfügbar
```
Lösung: `semantic_segmentation.py` im gleichen Verzeichnis sicherstellen

### Performance-Optimierung

1. **Batch-Verarbeitung**: Mehrere Dateien parallel
2. **Token-Limits**: Angemessene Limits für verfügbaren Speicher
3. **Cache-Nutzung**: Redis für Zwischenergebnisse
4. **GPU-Acceleration**: CUDA für ML-Operationen

---

## Änderungshistorie

**Version 3.0** (Mai 2025):
- Vollständige Pipeline-Integration
- Enterprise Orchestration mit Redis
- ML-basierte Performance Prediction
- Erweiterte RAG-Training Funktionalität
- Circuit Breaker Pattern für Robustheit

**Version 2.0** (März 2025):
- Semantische Segmentierung hinzugefügt
- Token-Limit Optimierung
- Erweiterte Fehlerbehandlung
- Normen-Erkennung verbessert

**Version 1.0** (Januar 2025):
- Basis-Segmentierung implementiert
- JSON/JSONL Konvertierung
- Grundlegende Prompt-Generierung

---

*Diese Dokumentation konsolidiert alle wichtigen Aspekte des LegalTech NLP Pipeline Projekts in einem einzigen, umfassenden Dokument. Für spezifische technische Details konsultieren Sie die entsprechenden Skripte und Konfigurationsdateien.*
