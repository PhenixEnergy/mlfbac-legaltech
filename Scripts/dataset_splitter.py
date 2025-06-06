#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Dataset Splitter für LegalTech-Projekt
Teilt den Datensatz in supervised und unsupervised learning datasets auf.

Supervised: Rechtsbezug + Normen + nur Abschnitt I + II
Unsupervised: Komplette Texte
"""

import json
import argparse
import re
from pathlib import Path
from collections import defaultdict, Counter
import random
import math
from typing import List, Dict, Tuple, Any

def estimate_tokens(text: str) -> int:
    """
    Schätzt die Anzahl der Tokens in einem Text.
    Grobe Schätzung: ~0.75 Tokens pro Wort (basierend auf GPT-Tokenization)
    """
    words = len(text.split())
    return int(words * 0.75)

def extract_legal_references(text: str) -> List[str]:
    """
    Extrahiert Gesetzesverweise aus dem Text.
    """
    # Pattern für verschiedene Gesetzesverweise
    patterns = [
        r'§§?\s*\d+\w*(?:\s+Abs\.\s*\d+\w*)?(?:\s+S\.\s*\d+\w*)?\s+[A-Z]{2,10}',  # § 307 BGB
        r'Art\.\s*\d+\w*(?:\s+Abs\.\s*\d+\w*)?\s+[A-Z]{2,15}',  # Art. 66 EuErbVO
        r'[A-Z]{2,15}\s+Art\.\s*\d+\w*',  # EuErbVO Art. 63
    ]
    
    references = []
    for pattern in patterns:
        matches = re.findall(pattern, text, re.IGNORECASE)
        references.extend(matches)
    
    return list(set(references))  # Duplikate entfernen

def extract_legal_domain(text: str) -> str:
    """
    Bestimmt das Rechtsgebiet basierend auf Schlüsselwörtern im Text.
    """
    domains = {
        'Erbrecht': ['Nachlass', 'Erbe', 'Erbschaft', 'Testament', 'ENZ', 'Erbschein', 'Erblasser'],
        'Zivilrecht': ['BGB', 'Vertrag', 'Schadensersatz', 'Anspruch', 'Klage'],
        'Arbeitsrecht': ['Arbeitgeber', 'Arbeitnehmer', 'Kündigung', 'Arbeitsvertrag'],
        'Familienrecht': ['Ehe', 'Scheidung', 'Unterhalt', 'Sorgerecht', 'FamFG'],
        'Handelsrecht': ['HGB', 'Gesellschaft', 'Kaufmann', 'Handelsregister'],
        'Verwaltungsrecht': ['Verwaltungsakt', 'Behörde', 'VwGO', 'Widerspruch'],
        'Europarecht': ['EuGH', 'EU-Recht', 'Richtlinie', 'Verordnung', 'EuErbVO'],
        'Prozessrecht': ['ZPO', 'Verfahren', 'Gericht', 'Urteil', 'Beschluss']
    }
    
    text_lower = text.lower()
    domain_scores = {}
    
    for domain, keywords in domains.items():
        score = sum(text_lower.count(keyword.lower()) for keyword in keywords)
        if score > 0:
            domain_scores[domain] = score
    
    if domain_scores:
        return max(domain_scores, key=domain_scores.get)
    return 'Allgemeines Recht'

def extract_roman_sections(text: str) -> Tuple[str, str]:
    """
    Extrahiert nur die Abschnitte I. und II. aus dem Text.
    """
    # Einfachere Pattern für römische Ziffern
    # Suche nach "I. " gefolgt von Text bis zu "II. "
    pattern_i = r'I\.\s+(.*?)(?=\s+II\.|$)'
    # Suche nach "II. " gefolgt von Text bis zu "III. " oder Ende
    pattern_ii = r'II\.\s+(.*?)(?=\s+III\.|$)'
    
    # Suche Abschnitt I
    match_i = re.search(pattern_i, text, re.DOTALL)
    section_i = match_i.group(1).strip() if match_i else ""
    
    # Suche Abschnitt II  
    match_ii = re.search(pattern_ii, text, re.DOTALL)
    section_ii = match_ii.group(1).strip() if match_ii else ""
    
    # Füge Überschriften hinzu wenn Inhalt gefunden
    if section_i:
        section_i = "I. " + section_i
    if section_ii:
        section_ii = "II. " + section_ii
    
    return section_i, section_ii

def create_supervised_entry(text_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Erstellt einen Eintrag für supervised learning.
    """
    text = text_data['text']
    
    # Rechtsbezug extrahieren
    legal_domain = extract_legal_domain(text)
    
    # Normen extrahieren
    legal_references = extract_legal_references(text)
    
    # Nur Abschnitt I und II extrahieren
    section_i, section_ii = extract_roman_sections(text)
    
    return {
        'rechtsbezug': legal_domain,
        'normen': legal_references,
        'abschnitt_i': section_i,
        'abschnitt_ii': section_ii,
        'original_length': len(text),
        'processed_length': len(section_i) + len(section_ii),
        'token_count': estimate_tokens(section_i + " " + section_ii)
    }

def create_unsupervised_entry(text_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Erstellt einen Eintrag für unsupervised learning.
    """
    text = text_data['text']
    
    return {
        'text': text,
        'token_count': estimate_tokens(text)
    }

def split_by_legal_domain(data: List[Dict], test_ratio: float = 0.5) -> Tuple[List[Dict], List[Dict]]:
    """
    Teilt den Datensatz nach Rechtsgebieten gleichmäßig auf.
    """
    # Gruppiere nach Rechtsgebieten
    domains = defaultdict(list)
    
    for item in data:
        domain = extract_legal_domain(item['text'])
        domains[domain].append(item)
    
    supervised_data = []
    unsupervised_data = []
    
    # Für jedes Rechtsgebiet gleichmäßig aufteilen
    for domain, items in domains.items():
        random.shuffle(items)  # Zufällige Reihenfolge
        
        split_point = int(len(items) * test_ratio)
        supervised_data.extend(items[:split_point])
        unsupervised_data.extend(items[split_point:])
    
    return supervised_data, unsupervised_data

def write_supervised_jsonl_with_token_limit(data: List[Dict], output_path: Path, token_limit: int):
    """
    Schreibt supervised JSONL-Datei mit Token-Limit.
    """
    current_tokens = 0
    written_entries = 0
    
    print(f"\nSchreibe supervised Datei: {output_path}")
    print(f"Token-Limit: {token_limit:,}")
    
    with open(output_path, 'w', encoding='utf-8') as f:
        for item in data:
            entry = create_supervised_entry(item)
            entry_tokens = entry['token_count']
            
            # Prüfe Token-Limit nur für supervised
            if current_tokens + entry_tokens > token_limit and written_entries > 0:
                print(f"Token-Limit erreicht bei {current_tokens:,} Tokens")
                break
            
            # Schreibe Eintrag
            json.dump(entry, f, ensure_ascii=False)
            f.write('\n')
            
            current_tokens += entry_tokens
            written_entries += 1
            
            if written_entries % 100 == 0:
                print(f"  Geschrieben: {written_entries} Einträge, {current_tokens:,} Tokens")
    
    print(f"Fertig: {written_entries} Einträge, {current_tokens:,} Tokens")
    return written_entries, current_tokens

def write_unsupervised_jsonl_fixed_count(data: List[Dict], output_path: Path, target_entries: int):
    """
    Schreibt unsupervised JSONL-Datei mit fester Anzahl Einträge (gleich wie supervised).
    """
    current_tokens = 0
    written_entries = 0
    
    print(f"\nSchreibe unsupervised Datei: {output_path}")
    print(f"Ziel-Einträge: {target_entries}")
    
    # Begrenze auf verfügbare Daten oder Ziel-Anzahl
    entries_to_write = min(len(data), target_entries)
    
    with open(output_path, 'w', encoding='utf-8') as f:
        for i, item in enumerate(data[:entries_to_write]):
            entry = create_unsupervised_entry(item)
            entry_tokens = entry['token_count']
            
            # Schreibe Eintrag
            json.dump(entry, f, ensure_ascii=False)
            f.write('\n')
            
            current_tokens += entry_tokens
            written_entries += 1
            
            if written_entries % 100 == 0:
                print(f"  Geschrieben: {written_entries} Einträge, {current_tokens:,} Tokens")
    
    print(f"Fertig: {written_entries} Einträge, {current_tokens:,} Tokens")
    return written_entries, current_tokens

def analyze_distribution(data: List[Dict], title: str):
    """
    Analysiert die Verteilung der Rechtsgebiete.
    """
    domains = [extract_legal_domain(item['text']) for item in data]
    domain_counts = Counter(domains)
    
    print(f"\n{title}:")
    print(f"Gesamt: {len(data)} Einträge")
    for domain, count in domain_counts.most_common():
        percentage = (count / len(data)) * 100
        print(f"  {domain}: {count} ({percentage:.1f}%)")

def main():
    parser = argparse.ArgumentParser(description='Teilt den Datensatz für supervised und unsupervised learning auf')
    parser.add_argument('input_file', help='Input JSON Datei')
    parser.add_argument('-t', '--tokens', type=float, default=1.0, 
                       help='Token-Limit in Millionen pro Datei (default: 1.0)')
    parser.add_argument('--seed', type=int, default=42, help='Random seed für Reproduzierbarkeit')
    parser.add_argument('--split-ratio', type=float, default=0.5, 
                       help='Anteil für supervised learning (default: 0.5)')
    
    args = parser.parse_args()
    
    # Random seed setzen
    random.seed(args.seed)
    
    # Token-Limit in absolute Zahlen umrechnen
    token_limit = int(args.tokens * 1_000_000)
    
    # Input-Datei laden
    input_path = Path(args.input_file)
    if not input_path.exists():
        print(f"Fehler: Datei {input_path} nicht gefunden!")
        return
    
    print(f"Lade Datensatz: {input_path}")
    with open(input_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    print(f"Geladene Einträge: {len(data)}")
    
    # Analysiere ursprüngliche Verteilung
    analyze_distribution(data, "Ursprüngliche Verteilung")
    
    # Aufteilen nach Rechtsgebieten
    print(f"\nTeile Datensatz auf (Ratio: {args.split_ratio})")
    supervised_data, unsupervised_data = split_by_legal_domain(data, args.split_ratio)
    
    # Analysiere Verteilungen nach Split
    analyze_distribution(supervised_data, "Supervised Learning Dataset")
    analyze_distribution(unsupervised_data, "Unsupervised Learning Dataset")
    
    # Output-Verzeichnis erstellen
    output_dir = input_path.parent / "Unsupervised Learning"
    output_dir.mkdir(exist_ok=True)
    
    # Dateinamen generieren
    base_name = input_path.stem
    supervised_file = output_dir / f"{base_name}_supervised_{args.tokens}M_tokens.jsonl"
    unsupervised_file = output_dir / f"{base_name}_unsupervised_{args.tokens}M_tokens.jsonl"
    
    # JSONL-Dateien schreiben
    print(f"\n{'='*60}")
    print("SUPERVISED LEARNING DATASET")
    print(f"{'='*60}")
    supervised_entries, supervised_tokens = write_supervised_jsonl_with_token_limit(
        supervised_data, supervised_file, token_limit
    )
    
    print(f"\n{'='*60}")
    print("UNSUPERVISED LEARNING DATASET")
    print(f"{'='*60}")
    # Für unsupervised: gleiche Anzahl Einträge wie supervised
    unsupervised_entries, unsupervised_tokens = write_unsupervised_jsonl_fixed_count(
        unsupervised_data, unsupervised_file, supervised_entries
    )
    
    # Zusammenfassung
    print(f"\n{'='*60}")
    print("ZUSAMMENFASSUNG")
    print(f"{'='*60}")
    print(f"Supervised Dataset:")
    print(f"  - Datei: {supervised_file}")
    print(f"  - Einträge: {supervised_entries}")
    print(f"  - Tokens: {supervised_tokens:,}")
    print(f"  - Inhalt: Rechtsbezug + Normen + Abschnitt I & II")
    
    print(f"\nUnsupervised Dataset:")
    print(f"  - Datei: {unsupervised_file}")
    print(f"  - Einträge: {unsupervised_entries}")
    print(f"  - Tokens: {unsupervised_tokens:,}")
    print(f"  - Inhalt: Komplette Texte")
    
    print(f"\nToken-Limit für supervised: {token_limit:,}")
    print(f"Einträge pro Dataset: {supervised_entries} (supervised) / {unsupervised_entries} (unsupervised)")
    print(f"Random Seed: {args.seed}")

if __name__ == "__main__":
    main()
