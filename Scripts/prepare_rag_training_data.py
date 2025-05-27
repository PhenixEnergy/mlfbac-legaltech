"""
RAG (Retrieval-Augmented Generation) Training Data Preparation for Legal Texts
==============================================================================

KORRIGIERTE VERSION - Arbeitet mit ChatML-Struktur der segmentierten Daten

Dieses Skript bereitet juristische Gutachten speziell für RAG-Training vor, indem es:
1. Wissensbasis (Knowledge Base) für Retrieval erstellt
2. Training Queries mit Context-Passage Paaren generiert
3. RAG-spezifische Prompt-Strukturen entwickelt

Version 2.0 - Mai 2025
Speziell entwickelt für RAG-Training mit deutschen Rechtsgutachten

RAG-Architektur:
- Retriever: Findet relevante Dokumentenabschnitte
- Generator: Erzeugt Antworten basierend auf abgerufenen Kontexten
- Training: Query + Retrieved Context → Generated Answer
"""

import json
import os
import sys
import argparse
import datetime
import random
import re
from collections import defaultdict
import hashlib

# Color codes for console output
class Colors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'

def extract_metadata_from_user_message(user_message):
    """Extrahiert Metadaten aus der User-Message"""
    metadata = {}
    
    if not user_message:
        return metadata
    
    # Gutachten-Nummer extrahieren
    gutachten_match = re.search(r'Gutachten Nr\. (\d+)', user_message)
    if gutachten_match:
        metadata["gutachten_nummer"] = gutachten_match.group(1)
    
    # Datum extrahieren
    datum_match = re.search(r'vom (\d{2}\.\d{2}\.\d{4})', user_message)
    if datum_match:
        metadata["erscheinungsdatum"] = datum_match.group(1)
    
    # Normen extrahieren (verschiedene Muster)
    normen = []
    
    # Muster 1: EUErbVO Art. 70
    normen_pattern1 = r'([A-Za-zÄÖÜäöüß]+(?:VO|BGB|StGB|ZPO|GG)?)\s*Art\.\s*(\d+(?:\w*)?)'
    normen_matches1 = re.findall(normen_pattern1, user_message)
    for law, section in normen_matches1:
        normen.append(f"{law.strip()} Art. {section.strip()}")
    
    # Muster 2: § 133 BGB
    normen_pattern2 = r'§\s*(\d+(?:\w*)?)\s*([A-Za-zÄÖÜäöüß]+)'
    normen_matches2 = re.findall(normen_pattern2, user_message)
    for section, law in normen_matches2:
        normen.append(f"§ {section.strip()} {law.strip()}")
    
    if normen:
        metadata["normen"] = list(set(normen))  # Duplikate entfernen
    
    # Rechtsgebiet bestimmen
    content_lower = user_message.lower()
    if any(keyword in content_lower for keyword in ["erb", "nachl", "testament"]):
        metadata["rechtsgebiet"] = "Erbrecht"
    elif any(keyword in content_lower for keyword in ["vertrag", "kauf", "miet"]):
        metadata["rechtsgebiet"] = "Vertragsrecht"
    elif any(keyword in content_lower for keyword in ["straf", "delikt"]):
        metadata["rechtsgebiet"] = "Strafrecht"
    else:
        metadata["rechtsgebiet"] = "Zivilrecht"
    
    return metadata

def extract_heading_from_content(content):
    """Extrahiert oder generiert eine Überschrift aus dem Inhalt"""
    if not content:
        return "Rechtliche Analyse"
    
    lines = content.split('\n')
    
    # Suche nach einer kurzen ersten Zeile als Überschrift
    for line in lines[:3]:  # Prüfe die ersten 3 Zeilen
        line = line.strip()
        if line and len(line) < 150 and not line.endswith('.'):
            # Prüfe ob es ein Titel-Pattern ist
            if any(keyword in line for keyword in ['I.', 'II.', 'III.', '1.', '2.', '3.', 'a)', 'b)', 'c)']):
                return line
            if line.endswith(':'):
                return line[:-1]  # Entferne den Doppelpunkt
    
    # Fallback: Generiere Überschrift basierend auf Inhalt
    content_lower = content.lower()
    if "sachverhalt" in content_lower:
        return "Sachverhalt"
    elif "rechtliche würdigung" in content_lower or "rechtliche beurteilung" in content_lower:
        return "Rechtliche Würdigung"
    elif "subsumtion" in content_lower:
        return "Subsumtion"
    elif "ergebnis" in content_lower or "fazit" in content_lower:
        return "Ergebnis"
    elif "anspruchsgrundlage" in content_lower:
        return "Anspruchsgrundlage"
    else:
        # Nimm die ersten 50 Zeichen als Überschrift
        first_sentence = content.split('.')[0].strip()
        if len(first_sentence) > 100:
            first_sentence = first_sentence[:100] + "..."
        return first_sentence

def classify_heading_type(heading):
    """Klassifiziert den Typ der Überschrift für bessere Retrieval-Performance"""
    heading_lower = heading.lower()
    
    if any(keyword in heading_lower for keyword in ["sachverhalt", "tatbestand", "fall"]):
        return "sachverhalt"
    elif any(keyword in heading_lower for keyword in ["rechtliche würdigung", "rechtliche beurteilung", "prüfung"]):
        return "rechtliche_analyse"
    elif any(keyword in heading_lower for keyword in ["subsumtion", "anwendung", "erfüllung"]):
        return "subsumtion"
    elif any(keyword in heading_lower for keyword in ["ergebnis", "fazit", "schluss"]):
        return "ergebnis"
    elif any(keyword in heading_lower for keyword in ["anspruchsgrundlage", "rechtsnorm", "gesetz"]):
        return "rechtsgrundlage"
    elif any(keyword in heading_lower for keyword in ["auslegung", "interpretation"]):
        return "auslegung"
    else:
        return "allgemein"

def create_knowledge_base_entry(segment_id, heading, content, metadata):
    """
    Erstellt einen Eintrag für die RAG Knowledge Base.
    
    Args:
        segment_id: Eindeutige ID für das Segment
        heading: Überschrift des Segments
        content: Textinhalt des Segments
        metadata: Zusätzliche Metadaten (Gutachten-Nr., Datum, Normen, etc.)
    
    Returns:
        Dictionary mit Knowledge Base Eintrag
    """
    return {
        "id": segment_id,
        "title": heading,
        "content": content,
        "metadata": {
            "gutachten_nummer": metadata.get("gutachten_nummer", ""),
            "erscheinungsdatum": metadata.get("erscheinungsdatum", ""),
            "rechtsbezug": metadata.get("rechtsbezug", ""),
            "normen": metadata.get("normen", []),
            "rechtsgebiet": metadata.get("rechtsgebiet", ""),
            "content_length": len(content),
            "heading_type": classify_heading_type(heading)
        }
    }

def generate_rag_query_variations(heading, content, metadata, max_queries=6):
    """
    Generiert verschiedene Query-Variationen für RAG-Training.
    
    Für jedes Segment werden mehrere Arten von Queries erstellt:
    1. Direkte Fragen zum Inhalt
    2. Vergleichsfragen 
    3. Anwendungsfragen
    4. Analysefragen
    """
    
    gutachten_nr = metadata.get("gutachten_nummer", "")
    erscheinungsdatum = metadata.get("erscheinungsdatum", "")
    normen = metadata.get("normen", [])
    
    normen_str = ""
    if normen:
        if len(normen) == 1:
            normen_str = f" bezüglich {normen[0]}"
        else:
            normen_str = f" bezüglich {', '.join(normen[:-1])} und {normen[-1]}"
    
    heading_type = classify_heading_type(heading)
    queries = []
    
    # Typ-spezifische Query-Generierung
    if heading_type == "sachverhalt":
        queries.extend([
            f"Was sind die wesentlichen Tatsachen des Falls aus Gutachten {gutachten_nr}?",
            f"Welche rechtlich relevanten Umstände liegen dem Gutachten {gutachten_nr} zugrunde?",
            f"Schildern Sie den Sachverhalt aus Gutachten {gutachten_nr}.",
            f"Welche Parteien und Interessenkonflikte zeigt der Fall in Gutachten {gutachten_nr}?",
        ])
        
    elif heading_type == "rechtliche_analyse":
        queries.extend([
            f"Wie ist die rechtliche Situation in Gutachten {gutachten_nr} zu bewerten{normen_str}?",
            f"Welche rechtlichen Probleme werden in Gutachten {gutachten_nr} behandelt?",
            f"Wie lautet die juristische Analyse zu Gutachten {gutachten_nr}?",
            f"Welche Rechtsnormen sind in Gutachten {gutachten_nr} einschlägig?",
        ])
        
    elif heading_type == "subsumtion":
        queries.extend([
            f"Wie erfolgt die Subsumtion unter die relevanten Tatbestandsmerkmale in Gutachten {gutachten_nr}{normen_str}?",
            f"Sind die Voraussetzungen der einschlägigen Normen in Gutachten {gutachten_nr} erfüllt?",
            f"Wie werden die Tatbestandsmerkmale in Gutachten {gutachten_nr} geprüft?",
            f"Welche Subsumtionsergebnisse zeigt Gutachten {gutachten_nr}?",
        ])
        
    elif heading_type == "ergebnis":
        queries.extend([
            f"Zu welchem Ergebnis kommt Gutachten {gutachten_nr}?",
            f"Wie lautet das Fazit des rechtlichen Gutachtens {gutachten_nr}?",
            f"Welche Schlussfolgerungen zieht Gutachten {gutachten_nr}?",
            f"Was ist das Endergebnis der rechtlichen Prüfung in Gutachten {gutachten_nr}?",
        ])
        
    elif heading_type == "rechtsgrundlage":
        queries.extend([
            f"Welche Anspruchsgrundlagen werden in Gutachten {gutachten_nr} geprüft{normen_str}?",
            f"Auf welche Rechtsnormen stützt sich Gutachten {gutachten_nr}?",
            f"Welche gesetzlichen Grundlagen sind für Gutachten {gutachten_nr} relevant?",
            f"Welche Rechtsquellen werden in Gutachten {gutachten_nr} herangezogen?",
        ])
        
    elif heading_type == "auslegung":
        queries.extend([
            f"Wie werden die einschlägigen Normen in Gutachten {gutachten_nr} ausgelegt{normen_str}?",
            f"Welche Auslegungsmethoden verwendet Gutachten {gutachten_nr}?",
            f"Wie interpretiert Gutachten {gutachten_nr} die relevanten Rechtsnormen?",
            f"Welche Bedeutung haben die Normen nach Gutachten {gutachten_nr}?",
        ])
    
    # Allgemeine Queries für alle Typen
    queries.extend([
        f"Erläutern Sie den Abschnitt '{heading}' aus Gutachten {gutachten_nr}.",
        f"Was behandelt der Teil '{heading}' in Gutachten {gutachten_nr}?",
        f"Fassen Sie den Inhalt von '{heading}' aus Gutachten {gutachten_nr} zusammen.",
    ])
    
    # Begrenze auf max_queries und entferne Duplikate
    unique_queries = list(dict.fromkeys(queries))  # Entfernt Duplikate
    return unique_queries[:max_queries]

def calculate_content_similarity(segment1, segment2):
    """
    Berechnet einfache inhaltliche Ähnlichkeit zwischen zwei Segmenten.
    In einer produktiven RAG-Implementierung würde hier ein Embedding-Model verwendet.
    """
    # Einfache keyword-basierte Ähnlichkeit
    words1 = set(segment1["content"].lower().split())
    words2 = set(segment2["content"].lower().split())
    
    intersection = words1.intersection(words2)
    union = words1.union(words2)
    
    if len(union) == 0:
        return 0.0
    
    jaccard_similarity = len(intersection) / len(union)
    
    # Bonus für gleiche Rechtsnormen
    normen1 = set(segment1["metadata"].get("normen", []))
    normen2 = set(segment2["metadata"].get("normen", []))
    normen_overlap = len(normen1.intersection(normen2)) > 0
    
    if normen_overlap:
        jaccard_similarity += 0.2
    
    # Bonus für gleiches Rechtsgebiet
    rechtsgebiet1 = segment1["metadata"].get("rechtsgebiet", "")
    rechtsgebiet2 = segment2["metadata"].get("rechtsgebiet", "")
    if rechtsgebiet1 and rechtsgebiet1 == rechtsgebiet2:
        jaccard_similarity += 0.1
    
    return min(jaccard_similarity, 1.0)

def extract_relevant_context_passages(all_segments, current_segment_idx, max_contexts=3):
    """
    Extrahiert relevante Kontextpassagen für das aktuelle Segment.
    Simuliert Retrieval-Ergebnisse für Training.
    """
    contexts = []
    current_segment = all_segments[current_segment_idx]
    
    # Immer das aktuelle Segment als primären Kontext
    contexts.append({
        "passage": current_segment["content"][:1000] + "..." if len(current_segment["content"]) > 1000 else current_segment["content"],
        "title": current_segment["heading"],
        "relevance_score": 1.0,
        "source": f"Gutachten {current_segment['metadata'].get('gutachten_nummer', 'N/A')}"
    })
    
    # Suche nach thematisch verwandten Segmenten
    similarity_scores = []
    for idx, segment in enumerate(all_segments):
        if idx != current_segment_idx:
            similarity = calculate_content_similarity(current_segment, segment)
            similarity_scores.append((idx, similarity))
    
    # Sortiere nach Ähnlichkeit
    similarity_scores.sort(key=lambda x: x[1], reverse=True)
    
    # Füge die ähnlichsten Segmente hinzu
    for idx, similarity in similarity_scores[:max_contexts-1]:
        if similarity > 0.15:  # Threshold für Relevanz
            segment = all_segments[idx]
            contexts.append({
                "passage": segment["content"][:800] + "..." if len(segment["content"]) > 800 else segment["content"],
                "title": segment["heading"],
                "relevance_score": similarity,
                "source": f"Gutachten {segment['metadata'].get('gutachten_nummer', 'N/A')}"
            })
    
    return contexts[:max_contexts]

def format_rag_prompt(query, contexts):
    """
    Formatiert den RAG-Prompt mit Query und Kontexten.
    """
    context_text = ""
    for idx, context in enumerate(contexts, 1):
        context_text += f"\n--- Kontext {idx} (Quelle: {context['source']}) ---\nTitel: {context['title']}\nInhalt: {context['passage']}\n"
    
    prompt = f"""Basierend auf den folgenden Kontextinformationen aus juristischen Gutachten, beantworte die gestellte Frage präzise und vollständig. Verwende nur Informationen aus den bereitgestellten Kontexten und zitiere die relevanten Quellen.

KONTEXTINFORMATIONEN:{context_text}

FRAGE: {query}

Bitte beantworte die Frage basierend ausschließlich auf den obigen Kontextinformationen:"""
    
    return prompt

def create_rag_training_example(query, context_passages, target_answer, metadata):
    """
    Erstellt ein RAG-Training-Beispiel im Format:
    Query + Retrieved Contexts → Generated Answer
    """
    return {
        "query": query,
        "contexts": context_passages,
        "target_answer": target_answer,
        "metadata": metadata
    }

def prepare_rag_training_data(input_file_path, output_options=None):
    """
    Hauptfunktion zur Vorbereitung von RAG-Trainingsdaten.
    
    Args:
        input_file_path: Pfad zur segmentierten JSONL-Datei
        output_options: Optionen für die Ausgabe
    
    Returns:
        Tuple (knowledge_base_path, training_data_path)
    """
    if output_options is None:
        output_options = {}
    
    knowledge_base_entries = []
    rag_training_examples = []
    all_segments = []
    
    processed_segments = 0
    generated_queries = 0
    errors = 0
    
    print(f"{Colors.HEADER}🔍 RAG Training Data Preparation{Colors.ENDC}")
    print(f"{Colors.OKBLUE}📂 Lade Daten von: {input_file_path}{Colors.ENDC}")
    
    # Lade und verarbeite segmentierte Daten
    try:
        with open(input_file_path, 'r', encoding='utf-8') as f:
            for line_num, line in enumerate(f, 1):
                if not line.strip():
                    continue
                
                try:
                    data = json.loads(line)
                    
                    # ChatML-Struktur erwarten
                    if "messages" not in data:
                        print(f"{Colors.WARNING}⚠ Keine messages in Zeile {line_num}{Colors.ENDC}")
                        continue
                    
                    user_message = ""
                    assistant_message = ""
                    
                    # Extrahiere User und Assistant Messages
                    for msg in data["messages"]:
                        role = msg.get("role", "")
                        if role == "user":
                            user_message = msg.get("content", "")
                        elif role == "assistant":
                            assistant_message = msg.get("content", "")
                    
                    if not assistant_message:
                        continue
                    
                    # Extrahiere Metadaten aus der User-Message
                    metadata = extract_metadata_from_user_message(user_message)
                    heading = extract_heading_from_content(assistant_message)
                    
                    # Erstelle Segment-ID
                    segment_id = f"seg_{hashlib.md5(assistant_message.encode()).hexdigest()[:8]}"
                    
                    # Erstelle Knowledge Base Entry
                    kb_entry = create_knowledge_base_entry(
                        segment_id, heading, assistant_message, metadata
                    )
                    knowledge_base_entries.append(kb_entry)
                    
                    # Sammle alle Segmente für Kontext-Extraktion
                    all_segments.append({
                        "id": segment_id,
                        "heading": heading,
                        "content": assistant_message,
                        "metadata": metadata,
                        "original_user_query": user_message
                    })
                    
                    processed_segments += 1
                    
                    # Progress Update
                    if processed_segments % 1000 == 0:
                        print(f"{Colors.OKCYAN}📊 Verarbeitet: {processed_segments} Segmente{Colors.ENDC}")
                    
                except json.JSONDecodeError as e:
                    print(f"{Colors.WARNING}⚠ JSON-Fehler in Zeile {line_num}: {e}{Colors.ENDC}")
                    errors += 1
                    continue
                except Exception as e:
                    print(f"{Colors.WARNING}⚠ Fehler in Zeile {line_num}: {e}{Colors.ENDC}")
                    errors += 1
                    continue
        
        print(f"{Colors.OKGREEN}✓ {processed_segments} Segmente erfolgreich geladen{Colors.ENDC}")
        if errors > 0:
            print(f"{Colors.WARNING}⚠ {errors} Fehler beim Laden{Colors.ENDC}")
        
        if processed_segments == 0:
            print(f"{Colors.FAIL}❌ Keine gültigen Segmente gefunden!{Colors.ENDC}")
            return None, None
        
        # Generiere RAG Training Examples (falls nicht nur Knowledge Base)
        if not output_options.get("knowledge_base_only", False):
            print(f"{Colors.OKBLUE}ℹ Generiere RAG-Trainingsbeispiele...{Colors.ENDC}")
            
            queries_per_segment = output_options.get("queries_per_segment", 6)
            
            for idx, segment in enumerate(all_segments):
                try:
                    # Generiere verschiedene Queries für dieses Segment
                    queries = generate_rag_query_variations(
                        segment["heading"], 
                        segment["content"], 
                        segment["metadata"],
                        max_queries=queries_per_segment
                    )
                    
                    for query in queries:
                        # Extrahiere relevante Kontexte
                        contexts = extract_relevant_context_passages(all_segments, idx)
                        
                        # Erstelle RAG-Training-Beispiel
                        rag_example = create_rag_training_example(
                            query=query,
                            context_passages=contexts,
                            target_answer=segment["content"],
                            metadata=segment["metadata"]
                        )
                        
                        rag_training_examples.append(rag_example)
                        generated_queries += 1
                    
                    # Progress Update
                    if (idx + 1) % 500 == 0:
                        print(f"{Colors.OKCYAN}📊 RAG-Beispiele für {idx + 1}/{len(all_segments)} Segmente generiert{Colors.ENDC}")
                        
                except Exception as e:
                    print(f"{Colors.WARNING}⚠ Fehler bei Segment {idx}: {e}{Colors.ENDC}")
                    continue
            
            print(f"{Colors.OKGREEN}✓ {generated_queries} RAG-Trainingsbeispiele generiert{Colors.ENDC}")
        
        # Schreibe Ausgabedateien in organisierte Ordnerstruktur
        base_filename = os.path.splitext(os.path.basename(input_file_path))[0]
        database_dir = os.path.dirname(os.path.dirname(input_file_path))  # Gehe vom Fine_Tuning-Ordner zum Database-Ordner
        rag_training_dir = os.path.join(database_dir, "RAG_Training")
        
        # Stelle sicher, dass der RAG_Training Ordner existiert
        os.makedirs(rag_training_dir, exist_ok=True)
        
        # Knowledge Base
        kb_output_path = os.path.join(rag_training_dir, f"{base_filename}_rag_knowledge_base.jsonl")
        print(f"{Colors.OKBLUE}💾 Schreibe Knowledge Base nach: {kb_output_path}{Colors.ENDC}")
        
        with open(kb_output_path, 'w', encoding='utf-8') as f:
            for entry in knowledge_base_entries:
                f.write(json.dumps(entry, ensure_ascii=False) + '\n')
        
        training_output_path = None
        
        # RAG Training Data (falls nicht nur Knowledge Base)
        if not output_options.get("knowledge_base_only", False):
            training_output_path = os.path.join(rag_training_dir, f"{base_filename}_rag_training.jsonl")
            print(f"{Colors.OKBLUE}💾 Schreibe RAG Training Data nach: {training_output_path}{Colors.ENDC}")
            
            with open(training_output_path, 'w', encoding='utf-8') as f:
                for example in rag_training_examples:
                    # Formatiere als Training-Example
                    rag_prompt = format_rag_prompt(example["query"], example["contexts"])
                    
                    training_data = {
                        "messages": [
                            {
                                "role": "system",
                                "content": "Du bist ein RAG-basierter KI-Assistent für juristische Fragen. Beantworte Fragen basierend auf den bereitgestellten Kontextinformationen aus Rechtsgutachten. Zitiere relevante Quellen und bleibe bei den gegebenen Informationen."
                            },
                            {
                                "role": "user", 
                                "content": rag_prompt
                            },
                            {
                                "role": "assistant",
                                "content": example["target_answer"]
                            }
                        ],
                        "metadata": {
                            "query_type": "rag_retrieval",
                            "num_contexts": len(example["contexts"]),
                            "source_gutachten": example["metadata"].get("gutachten_nummer", ""),
                            "heading_type": example["metadata"].get("heading_type", "")
                        }
                    }
                    
                    f.write(json.dumps(training_data, ensure_ascii=False) + '\n')
        
        # Statistiken
        print(f"\n{Colors.HEADER}📊 RAG-Vorbereitung Statistiken{Colors.ENDC}")
        print(f"{Colors.OKGREEN}✓ Knowledge Base Einträge: {len(knowledge_base_entries)}{Colors.ENDC}")
        print(f"{Colors.OKGREEN}✓ RAG Training Beispiele: {len(rag_training_examples)}{Colors.ENDC}")
        if len(all_segments) > 0:
            print(f"{Colors.OKGREEN}✓ Durchschnittliche Queries pro Segment: {generated_queries/len(all_segments):.1f}{Colors.ENDC}")
        print(f"{Colors.OKGREEN}✓ Knowledge Base Datei: {os.path.basename(kb_output_path)}{Colors.ENDC}")
        if training_output_path:
            print(f"{Colors.OKGREEN}✓ Training Data Datei: {os.path.basename(training_output_path)}{Colors.ENDC}")
        
        return kb_output_path, training_output_path
        
    except FileNotFoundError:
        print(f"{Colors.FAIL}❌ Datei nicht gefunden: {input_file_path}{Colors.ENDC}")
        return None, None
    except Exception as e:
        print(f"{Colors.FAIL}❌ Unerwarteter Fehler: {e}{Colors.ENDC}")
        import traceback
        traceback.print_exc()
        return None, None

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Bereitet segmentierte juristische Gutachten für RAG-Training vor"
    )
    
    parser.add_argument(
        "input_file",
        help="Pfad zur segmentierten JSONL-Datei (Output von segment_and_prepare_training_data.py)"
    )
    
    parser.add_argument(
        "-kb", "--knowledge-base-only",
        action="store_true",
        help="Erstelle nur Knowledge Base, keine Trainingsbeispiele"
    )
    
    parser.add_argument(
        "-q", "--queries-per-segment",
        type=int,
        default=6,
        help="Anzahl der Queries pro Segment (Standard: 6)"
    )
    
    args = parser.parse_args()
    
    output_options = {
        "knowledge_base_only": args.knowledge_base_only,
        "queries_per_segment": args.queries_per_segment
    }
    
    kb_path, training_path = prepare_rag_training_data(args.input_file, output_options)
    
    if kb_path:
        print(f"\n{Colors.OKGREEN}🎉 RAG-Vorbereitung erfolgreich abgeschlossen!{Colors.ENDC}")
        print(f"{Colors.OKCYAN}📚 Knowledge Base: {kb_path}{Colors.ENDC}")
        if training_path:
            print(f"{Colors.OKCYAN}🎯 Training Data: {training_path}{Colors.ENDC}")
    else:
        print(f"\n{Colors.FAIL}❌ RAG-Vorbereitung fehlgeschlagen.{Colors.ENDC}")
        sys.exit(1)
