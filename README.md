# LegalTech NLP Pipeline

Ein modulares und skalierbares System für die Verarbeitung, Segmentierung und Analyse von Rechtsdokumenten mit Unterstützung für RAG (Retrieval-Augmented Generation) und Fine-Tuning Workflows.

## 🚀 Quick Start

### Installation
```bash
# Abhängigkeiten installieren
pip install -r requirements.txt

# System testen
python main.py --help
```

### Grundlegende Verwendung
```bash
# Dokumentenkonvertierung
python main.py convert --input data.json --output data.jsonl

# Textsegmentierung
python main.py segment --input data.jsonl --strategy semantic

# RAG-Datenvorbereitung
python main.py rag-prepare --input segments.jsonl --output rag_data.jsonl

# Qualitätsvalidierung
python main.py validate --input processed_data.jsonl
```

## 📁 Projektstruktur

```
mlfbac-legaltech/
├── main.py                 # Unified entry point
├── requirements.txt        # Abhängigkeiten
├── config/                 # Konfigurationsdateien
│   └── optimization_config.json
├── core/                   # Kernmodule
│   ├── conversion/         # Datenkonvertierung
│   ├── segmentation/       # Textsegmentierung
│   ├── rag/               # RAG-Pipeline
│   ├── orchestration/     # Pipeline-Orchestrierung
│   └── validation/        # Qualitätssicherung
├── data/                  # Datensätze
│   ├── Fine_Tuning/
│   ├── Original_Data/
│   └── RAG_Training/
├── docs/                  # Dokumentation
├── examples/              # Anwendungsbeispiele
├── tests/                 # Tests
└── utils/                 # Hilfsfunktionen
```

## 🔧 Kernfunktionen

### 1. Dokumentenkonvertierung
- **JSONL-Konvertierung** für verschiedene Eingabeformate
- **Batch-Verarbeitung** großer Datensätze
- **Formatvalidierung** und Fehlerbehandlung

### 2. Intelligente Segmentierung
- **Semantische Segmentierung** mit Transformer-Modellen
- **Kontextbewusste Aufteilung** für optimale Trainingsqualität
- **Anpassbare Parameter** für verschiedene Dokumenttypen

### 3. RAG-Pipeline
- **Automatisierte Datenvorbereitung** für Retrieval-Augmented Generation
- **Optimierte Prompt-Generierung** 
- **Metadaten-Erhaltung** für Nachverfolgbarkeit

### 4. Qualitätssicherung
- **Automatisierte Validierung** der Datenqualität
- **Performance-Benchmarks** und Metriken
- **Konsistenzprüfungen** für Trainingsdaten

## 📖 Vollständige Dokumentation

Für detaillierte Informationen siehe:
- **[Vollständige Dokumentation](docs/COMPLETE_DOCUMENTATION.md)** - Umfassender Leitfaden
- **[API-Referenz](API_REFERENCE.md)** - Detaillierte API-Beschreibung
- **[Konfiguration](CONFIGURATION.md)** - Konfigurationsoptionen
- **[Entwicklerhandbuch](DEVELOPER_GUIDE.md)** - Entwicklungsrichtlinien
- **[Enterprise Guide](ENTERPRISE_USER_GUIDE.md)** - Enterprise-Features
- **[Fehlerbehebung](TROUBLESHOOTING.md)** - Lösungen für häufige Probleme

## 🎯 Anwendungsfälle

### 1. **Rechtsdokument-Analyse**
```python
# Vollständige Pipeline für Gerichtsurteile
python main.py segment --input court_decisions.jsonl --strategy legal-document

# RAG-Training für Rechtsfragen
python main.py rag-prepare --input legal_segments.jsonl --context-type legal
```

### 2. **Vertragsverarbeitung**
```python
# Vertragsklauseln segmentieren
python main.py segment --input contracts.jsonl --preserve-structure --overlap 20

# Fine-Tuning Daten für Vertragsanalyse
python main.py prepare-training --input contract_segments.jsonl --task contract-analysis
```

### 3. **Compliance-Monitoring**
```python
# Automatisierte Qualitätsprüfung
python main.py validate --input processed_docs.jsonl --compliance-check --threshold 0.9
```

## 🏗️ Architektur

### Modularer Aufbau
- **Conversion**: JSONL-Transformation und Formatvalidierung
- **Segmentation**: Intelligente Text- und Dokumentenaufteilung  
- **RAG**: Retrieval-Augmented Generation Pipeline
- **Orchestration**: Workflow-Management und Ressourcenoptimierung
- **Validation**: Qualitätssicherung und Performance-Monitoring

### Datenfluss
```
Rohdokumente → Konvertierung → Segmentierung → RAG/Fine-Tuning → Validierung → Trainingsfertige Daten
```

## ⚙️ Konfiguration

### Hauptkonfiguration (`config/optimization_config.json`)
```json
{
  "segmentation": {
    "max_length": 512,
    "overlap": 50,
    "strategy": "semantic"
  },
  "rag": {
    "embedding_model": "sentence-transformers/all-MiniLM-L6-v2",
    "chunk_size": 256
  }
}
```

### Erweiterte Optionen
- **Multi-Threading**: Parallele Verarbeitung für bessere Performance
- **GPU-Unterstützung**: CUDA-beschleunigte Inferenz
- **Batch-Processing**: Effiziente Verarbeitung großer Datensätze
- **Quality Metrics**: Automatisierte Qualitätsbewertung

## 🧪 Testing

```bash
# Alle Tests ausführen
python -m pytest tests/

# Spezifische Modultests
python -m pytest tests/unit/test_segmentation.py

# Performance-Benchmarks
python main.py benchmark --dataset data/test_corpus.jsonl
```

## 🚀 Deployment

### Docker
```bash
# Container erstellen
docker build -t legaltech-nlp .

# Pipeline ausführen
docker run -v /path/to/data:/data legaltech-nlp segment --input /data/input.jsonl
```

### Produktionsumgebung
```bash
# Enterprise-Konfiguration
python main.py configure --enterprise --multi-tenant

# API-Server starten
python main.py serve --host 0.0.0.0 --port 8000
```

## 💡 Best Practices

### Datenqualität
- **Vorverarbeitung**: Bereinigung und Normalisierung der Eingabedaten
- **Validierung**: Regelmäßige Qualitätsprüfungen durchführen  
- **Monitoring**: Performance-Metriken kontinuierlich überwachen

### Performance-Optimierung
- **Batch-Größe**: Anpassung je nach verfügbarem Speicher
- **Parallelisierung**: Nutzung aller verfügbaren CPU-Kerne
- **Caching**: Wiederverwendung berechneter Embeddings

### Sicherheit
- **Datenschutz**: GDPR-konforme Verarbeitung sensibler Rechtsdaten
- **Zugriffskontrolle**: Authentifizierung und Autorisierung
- **Audit-Logging**: Vollständige Nachverfolgung aller Operationen

## 🤝 Contributing

Beiträge sind willkommen! Bitte beachten Sie:

1. **Entwicklungsrichtlinien** im [Developer Guide](DEVELOPER_GUIDE.md)
2. **Code-Style**: PEP 8 und Type Hints verwenden
3. **Tests**: Neue Features mit Tests abdecken
4. **Dokumentation**: Änderungen dokumentieren

```bash
# Entwicklungsumgebung setup
git clone <repository-url>
cd mlfbac-legaltech
pip install -r requirements-dev.txt
pre-commit install
```

## 📄 Lizenz

MIT License - siehe [LICENSE](LICENSE) für Details.

## 📞 Support

- **GitHub Issues**: [Repository Issues](https://github.com/company/legaltech-nlp/issues)
- **Dokumentation**: [docs/COMPLETE_DOCUMENTATION.md](docs/COMPLETE_DOCUMENTATION.md)
- **Enterprise Support**: enterprise@legaltech-company.com

---

**Version**: 2.0.0  
**Letzte Aktualisierung**: Juni 2025  
**Minimale Python-Version**: 3.8+

Diese Sektion beschreibt die im Projekt verwendeten Python-Skripte.

### Projektbeschreibung
<a name="projektbeschreibung"></a>
Das Projekt fokussiert sich auf die semantische Segmentierung von Rechtsdokumenten, um relevante Abschnitte automatisch zu identifizieren und zu extrahieren. Ziel ist es, die Effizienz bei der Analyse juristischer Texte zu steigern und die Grundlage für weiterführende Anwendungen wie Wissensextraktion oder automatisierte Zusammenfassungen zu schaffen.

### Projektkontext
<a name="projektkontext"></a>
Im LegalTech-Bereich ist die automatische Analyse von Dokumenten von entscheidender Bedeutung. Juristische Texte sind oft lang, komplex und enthalten spezifische Strukturen, deren manuelle Erfassung zeitaufwendig ist. Dieses Projekt adressiert diese Herausforderung durch den Einsatz von Natural Language Processing (NLP) und Machine Learning (ML) Techniken.

### Übersicht der Skripte
<a name="übersicht-der-skripte"></a>
Das Projekt umfasst mehrere Python-Skripte, die für verschiedene Phasen der Datenverarbeitung und -analyse zuständig sind:
*   `jsonl_converter.py`: Konvertiert JSON-Dateien in das JSONL-Format.
*   `segment_and_prepare_training_data.py`: Segmentiert Texte und bereitet sie für das Training von ML-Modellen vor.
*   `semantic_segmentation.py`: Führt die semantische Segmentierung auf den vorbereiteten Daten durch.

### `jsonl_converter.py`
<a name="jsonl_converterpy"></a>
*   **Zweck:** Konvertiert Standard-JSON-Dateien in das JSONL-Format (JSON Lines), bei dem jede Zeile ein gültiges JSON-Objekt darstellt. Dies ist oft nützlich für Streaming-Datenverarbeitung und große Datensätze.
*   **Funktionsweise:** Liest eine JSON-Datei, die typischerweise eine Liste von JSON-Objekten enthält, und schreibt jedes Objekt als separate Zeile in eine Ausgabedatei im JSONL-Format.
*   **Verwendung:**
    ```bash
    python Scripts/jsonl_converter.py <input_file.json> <output_file.jsonl>
    ```

### `segment_and_prepare_training_data.py`
<a name="segment_and_prepare_training_datapy"></a>
*   **Zweck:** Dieses Skript ist verantwortlich für die Segmentierung von Texten in kleinere Einheiten (z.B. Sätze oder Absätze) und die Vorbereitung dieser Daten für das Training von Machine Learning Modellen. Dies kann das Tokenisieren von Text, das Erstellen von numerischen Repräsentationen und das Anreichern mit Labels umfassen.
*   **Funktionsweise:** Nutzt NLP-Techniken und -Bibliotheken (z.B. spaCy, NLTK, oder Transformer-basierte Tokenizer) zur Textverarbeitung. Es kann Konfigurationsdateien verwenden, um den Segmentierungs- und Vorbereitungsprozess zu steuern.
*   **Verwendung:**
    ```bash
    python Scripts/segment_and_prepare_training_data.py --input_file <path_to_input.jsonl> --output_file <path_to_output.jsonl> --config <path_to_config.yaml>
    ```

### `semantic_segmentation.py`
<a name="semantic_segmentationpy"></a>
*   **Zweck:** Führt die eigentliche semantische Segmentierung auf vorbereiteten Daten durch. Es verwendet ein trainiertes Modell, um Textabschnitte basierend auf ihrer Bedeutung und ihrem Kontext in vordefinierte Kategorien einzuteilen.
*   **Funktionsweise:** Lädt ein vortrainiertes Segmentierungsmodell (z.B. ein Transformer-Modell, das für Token-Klassifizierung oder Sequenz-Labeling trainiert wurde) und wendet es auf die Eingabedaten an. Die Ergebnisse enthalten die identifizierten Segmente mit ihren Labels und Positionen.
*   **Verwendung:**
    ```bash
    python Scripts/semantic_segmentation.py --model_path <path_to_model> --input_data <path_to_data.jsonl> --output_results <path_to_results.jsonl>
    ```

### Setup und Abhängigkeiten
<a name="setup-und-abhängigkeiten"></a>
Stellen Sie sicher, dass Python 3.8+ installiert ist. Die notwendigen Python-Bibliotheken können über eine `requirements.txt`-Datei installiert werden:
```bash
pip install -r requirements.txt
```
(Hinweis: Eine `requirements.txt` sollte im Projektverzeichnis vorhanden sein und alle Abhängigkeiten wie `pandas`, `numpy`, `torch`, `transformers`, `scikit-learn` etc. auflisten.)

### Ausführung der Skripte
<a name="ausführung-der-skripte"></a>
Die Skripte werden über die Kommandozeile ausgeführt. Die genauen Befehle und Parameter sind oben bei jedem Skript beschrieben. Es wird empfohlen, die Skripte aus dem Hauptverzeichnis des Projekts auszuführen, um korrekte Pfadangaben zu gewährleisten.

### Datenformate (Skripte)
<a name="datenformate-skripte"></a>
Primär werden JSON und JSONL Formate verwendet. Eingabedaten für die Segmentierung sind typischerweise Texte im JSONL-Format, wobei jede Zeile ein Dokument oder einen Textabschnitt repräsentiert. Ausgabedaten enthalten die ursprünglichen Texte angereichert mit Segmentinformationen.

### Fehlerbehandlung
<a name="fehlerbehandlung"></a>
Grundlegende Fehlerbehandlung ist implementiert (z.B. Überprüfung von Dateipfaden, Umgang mit fehlenden Konfigurationen). Detaillierte Fehlermeldungen werden in der Konsole ausgegeben. Für produktive Einsätze sollte das Logging und die Fehlerrobustheit erweitert werden.

### Zukünftige Erweiterungen
<a name="zukünftige-erweiterungen"></a>
Mögliche Erweiterungen umfassen die Integration weiterer Modelle, Unterstützung zusätzlicher Datenformate, Verbesserung der Benutzeroberfläche (z.B. durch eine Web-App) und die Implementierung fortgeschrittener Evaluations- und Visualisierungsmethoden.

---

## 3. Workflows
<a name="workflows"></a>

Die typischen Arbeitsabläufe im Projekt umfassen:
1.  **Datenvorbereitung:** Konvertierung und Bereinigung der Rohdaten. Dies beinhaltet oft die Umwandlung von Formaten (z.B. PDF/DOCX zu Text, JSON zu JSONL) und das Entfernen irrelevanter Informationen.
2.  **Segmentierung:** Anwendung der semantischen Segmentierungsmodelle auf die vorbereiteten Texte. Hierbei werden die Texte in logische Einheiten unterteilt und mit entsprechenden Labels versehen.
3.  **Training:** (Falls zutreffend) Training neuer Modelle oder Feinabstimmung bestehender Modelle auf spezifischen Datensätzen, um die Segmentierungsgenauigkeit zu verbessern.
4.  **Analyse & Visualisierung:** Untersuchung der Segmentierungsergebnisse, Berechnung von Metriken und Darstellung der Segmente in einer verständlichen Form.

Weitere Details zu spezifischen Teilen der Workflows finden Sie in den jeweiligen Dokumentationsseiten (siehe [Vollständige HTML Dokumentation](#vollständige-html-dokumentation)).

---

## 4. Datensatz Struktur
<a name="datensatz-struktur"></a>

Diese Sektion beschreibt den Aufbau und die Struktur der im Projekt verwendeten Datensätze.

### Verwendete Dateiformate
<a name="verwendete-dateiformate"></a>
Die primären Dateiformate für die Datenspeicherung und -verarbeitung sind JSON und JSONL.
*   **JSON (JavaScript Object Notation):** Ein leichtgewichtiges Daten-Austauschformat, das einfach von Menschen gelesen und von Maschinen geparst und generiert werden kann. Gut geeignet für strukturierte Daten.
*   **JSONL (JSON Lines):** Ein Textformat, bei dem jede Zeile ein separates, gültiges JSON-Objekt ist. Dieses Format ist besonders nützlich für das Streaming von Daten oder die Verarbeitung sehr großer Datensätze, da jede Zeile unabhängig geparst werden kann.

### JSON Struktur (Beispiel für ein Dokument)
<a name="json-struktur-beispiel"></a>
Eine einzelne JSON-Datei kann eine Liste von Dokumenten oder ein einzelnes komplexes Dokumentobjekt enthalten.
```json
[
  {
    "id": "doc1",
    "text": "Dies ist der Inhalt des ersten Dokuments...",
    "segments": [
      {"label": "Einleitung", "start": 0, "end": 50},
      {"label": "Hauptteil", "start": 51, "end": 200}
    ],
    "metadata": {"source": "Quelle A"}
  },
  {
    "id": "doc2",
    "text": "Inhalt des zweiten Dokuments...",
    "segments": [],
    "metadata": {"source": "Quelle B"}
  }
]
```

### JSONL Struktur (Beispiel)
<a name="jsonl-struktur-beispiel"></a>
Jede Zeile in einer `.jsonl`-Datei repräsentiert ein Datenobjekt. Dies ist oft das bevorzugte Format für Trainingsdaten oder große Sammlungen von Dokumenten.

Beispiel für allgemeine Daten:
```json
{"id": "item1", "text": "Text des ersten Eintrags.", "label": "KategorieX"}
{"id": "item2", "text": "Text des zweiten Eintrags.", "label": "KategorieY"}
```

Beispiel für Trainingsdaten (z.B. für Token-Klassifizierung):
```json
{"text": "Der Kläger behauptet...", "tokens": ["Der", "Kläger", "behauptet"], "labels": ["O", "B-PERSON", "O"]}
{"text": "Die Beklagte erwidert...", "tokens": ["Die", "Beklagte", "erwidert"], "labels": ["O", "B-PERSON", "O"]}
```

### Wichtige Datenfelder
<a name="wichtige-datenfelder"></a>
Die genauen Felder können je nach Anwendungsfall variieren, aber typische Felder umfassen:
*   `id`: Eindeutiger Identifikator für ein Dokument oder einen Datensatz.
*   `text`: Der Rohtext des Dokuments oder Textabschnitts.
*   `segments`: Eine Liste von Objekten, die die erkannten semantischen Segmente definieren. Jedes Segmentobjekt enthält typischerweise:
    *   `label`: Die Kategorie des Segments (z.B. "Klageantrag", "Tatbestand").
    *   `start`: Startposition des Segments im Text (Zeichen- oder Token-Index).
    *   `end`: Endposition des Segments im Text.
*   `tokens`: (Optional, oft für Trainingsdaten) Eine Liste von Tokens (Wörtern/Subwörtern) des Textes.
*   `labels`: (Optional, oft für Trainingsdaten) Entsprechende Labels für jedes Token (z.B. im BIO-Format für Named Entity Recognition oder Segmentierung).
*   `metadata`: Zusätzliche Informationen wie Quelle, Erstellungsdatum, Autor, Fallnummer etc.

---

## 5. Technische Details
<a name="technische-details"></a>

### Mathematischer Hintergrund
<a name="mathematischer-hintergrund"></a>

Diese Sektion gibt einen Einblick in die mathematischen und algorithmischen Grundlagen des Projekts.

#### Grundlagen des Natural Language Processing (NLP)
<a name="grundlagen-des-natural-language-processing-nlp"></a>
Natural Language Processing (NLP) ist ein Teilgebiet der künstlichen Intelligenz, das sich mit der Interaktion zwischen Computern und menschlicher Sprache befasst. Ziel ist es, Computern die Fähigkeit zu verleihen, menschliche Sprache zu verstehen, zu interpretieren und zu generieren.

Wichtige Konzepte im NLP, die in diesem Projekt relevant sein können:
*   **Tokenisierung:** Aufteilung von Text in kleinere Einheiten (Tokens), wie Wörter oder Subwörter.
*   **Word Embeddings:** Numerische Vektorrepräsentationen von Wörtern, die ihre semantische Bedeutung erfassen (z.B. Word2Vec, GloVe, FastText). Moderne Ansätze verwenden kontextsensitive Embeddings aus Transformer-Modellen.
*   **Part-of-Speech (POS) Tagging:** Zuweisung von Wortarten (z.B. Nomen, Verb, Adjektiv) zu jedem Token.
*   **Named Entity Recognition (NER):** Identifizierung und Klassifizierung von benannten Entitäten im Text (z.B. Personen, Organisationen, Orte).

#### Transformer-Modelle und Attention-Mechanismus
<a name="transformer-modelle-und-attention-mechanismus"></a>
Transformer-Modelle (z.B. BERT, GPT, RoBERTa) haben die Verarbeitung von Sequenzdaten, insbesondere im NLP, revolutioniert. Sie basieren auf dem **Attention-Mechanismus**, der es dem Modell ermöglicht, die Wichtigkeit verschiedener Teile der Eingabesequenz bei der Verarbeitung jedes Elements zu gewichten.
*   **Self-Attention:** Ermöglicht es dem Modell, Abhängigkeiten zwischen verschiedenen Wörtern in einem Satz zu lernen, unabhängig von ihrer Distanz.
*   **Encoder-Decoder-Architektur:** Viele Transformer-Modelle verwenden eine Encoder-Struktur zur Repräsentation der Eingabe und/oder eine Decoder-Struktur zur Generierung der Ausgabe. Für Segmentierungsaufgaben sind oft Encoder-basierte Modelle ausreichend.

#### Evaluationsmetriken für Segmentierung
<a name="evaluationsmetriken-für-segmentierung"></a>
Zur Bewertung der Qualität der semantischen Segmentierung werden verschiedene Metriken verwendet:
*   **Precision, Recall, F1-Score:** Diese Metriken werden oft für jede Segmentklasse berechnet.
    *   *Precision:* Anteil der korrekt identifizierten Segmente an allen als positiv klassifizierten Segmenten.
    *   *Recall (Sensitivity):* Anteil der korrekt identifizierten Segmente an allen tatsächlich vorhandenen positiven Segmenten.
    *   *F1-Score:* Das harmonische Mittel von Precision und Recall.
*   **Intersection over Union (IoU) / Jaccard Index:** Misst die Überlappung zwischen den vorhergesagten Segmentgrenzen und den tatsächlichen Segmentgrenzen.
*   **Boundary Similarity / Boundary F1-Score:** Bewertet die Genauigkeit der erkannten Segmentgrenzen, oft mit einer gewissen Toleranz.

### Textsegmentierung und Visualisierung
<a name="textsegmentierung-und-visualisierung"></a>

Diese Sektion behandelt den Prozess der Textsegmentierung und Methoden zur Visualisierung der Ergebnisse.

#### Der Segmentierungsprozess
<a name="der-segmentierungsprozess"></a>
Die semantische Segmentierung von Texten zielt darauf ab, Textabschnitte, die zu einer bestimmten semantischen Kategorie gehören, automatisch zu identifizieren und abzugrenzen.

Typische Schritte im Segmentierungsprozess:
1.  **Vorverarbeitung der Texte:** Bereinigung des Rohmaterials, z.B. Entfernung von HTML-Tags, Normalisierung von Text, Aufteilung in kleinere Einheiten (Sätze, Absätze), falls erforderlich.
2.  **Anwendung des Segmentierungsmodells:** Ein trainiertes Machine-Learning-Modell (oft ein Transformer-basiertes Modell) klassifiziert Tokens oder Textspannen und weist ihnen Segmentlabels zu.
3.  **Nachverarbeitung der Ergebnisse:** Glättung von Segmentgrenzen, Zusammenführen kleiner Segmente, Behebung von Inkonsistenzen und Formatierung der Ausgabe.

#### Tools und Techniken zur Visualisierung
<a name="tools-und-techniken-zur-visualisierung"></a>
Für die Visualisierung der Segmentierungsergebnisse können verschiedene Tools und Techniken eingesetzt werden, um die Ergebnisse verständlich und interpretierbar zu machen:
*   **Farbliche Hervorhebung:** Unterschiedliche semantische Segmente werden im Originaltext farblich markiert. Dies ist eine einfache und intuitive Methode.
*   **Interaktive Dashboards:** Tools wie Plotly Dash, Streamlit oder spezialisierte Annotationswerkzeuge (z.B. INCEpTION, doccano) können verwendet werden, um interaktive Visualisierungen zu erstellen, die es Benutzern ermöglichen, die Ergebnisse zu explorieren und ggf. zu korrigieren.
*   **Diagramme und Statistiken:** Balkendiagramme zur Häufigkeit von Segmenttypen, Histogramme von Segmentlängen oder Konfusionsmatrizen zur Darstellung der Modellleistung.

#### Herausforderungen bei der Segmentierung und Visualisierung
<a name="herausforderungen-bei-der-segmentierung-und-visualisierung"></a>
*   **Segmentgrenzen:** Korrekte Identifizierung von exakten Segmentgrenzen, besonders bei fließenden Übergängen.
*   **Mehrdeutigkeit:** Texte können mehrdeutig sein, was die Zuordnung zu Segmentkategorien erschwert.
*   **Lange Dokumente:** Effiziente Verarbeitung und Visualisierung von sehr langen Dokumenten.
*   **Überlappende Segmente:** Umgang mit hierarchischen oder überlappenden Segmentstrukturen.
*   **Subjektivität:** Die Definition von "korrekten" Segmenten kann subjektiv sein und von der spezifischen Aufgabe abhängen.
*   **Skalierbarkeit der Visualisierung:** Darstellung großer Mengen an segmentierten Daten ohne Informationsverlust oder Überforderung des Nutzers.

---

## 6. Vollständige HTML Dokumentation
<a name="vollständige-html-dokumentation"></a>

Diese `README.md` Datei fasst die wichtigsten Informationen aus der Projektdokumentation zusammen.
Für eine detailliertere Ansicht, einschließlich interaktiver Elemente und der ursprünglichen Formatierung, können Sie die vollständige HTML-Dokumentation einsehen.

**So öffnen Sie die HTML-Dokumentation:**
1.  Navigieren Sie in Ihrem Dateiexplorer zum Projektverzeichnis `c:\Ab 20.05.2025\`.
2.  Führen Sie die Datei `open_documentation.bat` aus. Diese Batch-Datei öffnet die Hauptseite der HTML-Dokumentation (`Documentation/index.html`) in Ihrem Standard-Webbrowser.
3.  Alternativ können Sie die Datei `c:\Ab 20.05.2025\Documentation\index.html` direkt in einem Webbrowser öffnen.

Die HTML-Dokumentation ist in folgende Dateien unterteilt:
*   `Documentation/index.html`: Hauptübersichtsseite.
*   `Documentation/script_documentation.html`: Detaillierte Dokumentation der Python-Skripte.
*   `Documentation/mathematical_background.html`: Erläuterungen zu mathematischen Konzepten und Algorithmen.
*   `Documentation/segmentierung_visualisierung.html`: Informationen zur Textsegmentierung und Visualisierung.
*   `Documentation/dataset_structure.html`: Beschreibung der Datensatzstruktur.

---
*Letzte Aktualisierung der Quelldokumente: Mai 2025*
*README generiert am: 21. Mai 2025*
