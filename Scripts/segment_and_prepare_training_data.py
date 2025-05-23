"""
Segmentiert und bereitet juristische Gutachtentexte für das Training eines Sprachmodells vor.

Version 2.0 - Mai 2025
- Erweiterte semantische Segmentierung
- Verbesserte Prompt-Generierung
- Parameter für unterschiedliche Trainingsformate (-c, -r, -a)
- Optimierte Ausgabeformatierung
- Detaillierte Statistikausgabe

Aufbau des Skripts (3-teilige Struktur):
1. SEGMENTIERUNG: Erkennung von logischen Abschnitten in den Gutachtentexten
   - Hauptfunktion: segment_text()
   - Nutzt pattern-matching und reguläre Ausdrücke
   - Kann durch semantic_segmentation.py erweitert werden

2. PROMPT-GENERIERUNG: Erstellung von kontextreichen Prompts für jeden Abschnitt
   - Hauptfunktion: _generate_user_prompt()
   - Berücksichtigt Überschriften, Rechtsnormen und Gutachtenkontexte

3. VERARBEITUNG: Hauptprozess zur Datenverarbeitung und JSON(L)-Ausgabe
   - Hauptfunktion: prepare_data_for_training()
   - Verwaltet Token-Limits, Segmentgrenzen und statistische Auswertung

Diese 3-teilige Struktur ermöglicht modulare Erweiterungen und bessere Wartbarkeit.

Author: LegalTech Team
"""

import json
import argparse
import os
import re
import sys
import traceback
import datetime
import math
from collections import defaultdict

# Importiere die erweiterte semantische Segmentierung
try:
    from semantic_segmentation import enhanced_segment_text
    ENHANCED_SEGMENTATION_AVAILABLE = True
except ImportError:
    ENHANCED_SEGMENTATION_AVAILABLE = False

# Attempt to enable ANSI escape sequence processing on Windows
if os.name == 'nt':
    os.system('')

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

def format_token_limit_for_filename(limit_in_millions):
    """Formats the token limit for inclusion in the output filename."""
    if limit_in_millions >= 1:
        if limit_in_millions == int(limit_in_millions):
            return f"_{int(limit_in_millions)}_Mio"
        else:
            # For cases like 1.5 Mio, format as _1_5_Mio
            return f"_{str(limit_in_millions).replace('.', '_')}_Mio"
    else:
        # For 0.2 (200k), format as _200k
        k_value = int(limit_in_millions * 1000)
        return f"_{k_value}k"

def _generate_user_prompt(heading, gutachten_nummer, erscheinungsdatum, segments_count_for_current_gutachten, normen_list=None):
    """
    Generiert den Benutzer-Prompt basierend auf Überschrift und anderen Metadaten, mit stärkerem Fokus auf Rechtsnormen.
    
    Args:
        heading: Die Abschnittsüberschrift aus dem segmentierten Text
        gutachten_nummer: Die Gutachtennummer
        erscheinungsdatum: Das Erscheinungsdatum
        segments_count_for_current_gutachten: Anzahl der Segmente in diesem Gutachten
        normen_list: Liste der im Gutachten referenzierten Rechtsnormen
        
    Returns:
        Ein Prompt, der die Rechtsnormen und den Kontext berücksichtigt
    """
    cleaned_heading_lower = heading.lower()
    prompt = ""
    
    # Formatierung der Rechtsnormen für bessere Lesbarkeit
    normen_str = ""
    if normen_list and len(normen_list) > 0:
        normen_str = ", ".join(normen_list)
        normen_str = f" unter besonderer Berücksichtigung von {normen_str}"

    # Hauptprompts basierend auf Abschnittstyp - erweiterte und verbesserte Prompts
    if "sachverhalt" in cleaned_heading_lower:
        prompt = f"Gib den Sachverhalt für Gutachten Nr. {gutachten_nummer} vom {erscheinungsdatum} wieder{normen_str}. Beschreibe den relevanten Sachverhalt präzise und umfassend. Arbeite die rechtlich relevanten Fakten klar heraus und strukturiere sie chronologisch und nach sachlichen Zusammenhängen."
    
    elif "frage" in cleaned_heading_lower: # Fängt "Frage" und "Fragen" ab
        prompt = f"Welche rechtlichen Fragen behandelt Gutachten Nr. {gutachten_nummer} vom {erscheinungsdatum}{normen_str}? Formuliere die Rechtsfragen präzise und systematisch. Skizziere dabei die zentralen juristischen Probleme und ordne sie den relevanten Rechtsbereichen zu."
    
    elif "rechtsfrage" in cleaned_heading_lower:
        prompt = f"Formuliere die zentrale Rechtsfrage des Gutachtens Nr. {gutachten_nummer} vom {erscheinungsdatum}{normen_str}. Arbeite den rechtlichen Kern des Problems heraus und stelle dar, welche Normen zur Beantwortung herangezogen werden müssen. Grenzen Sie die Fragestellung präzise ein."
    
    elif "ergebnis" in cleaned_heading_lower or "zusammenfassung" in cleaned_heading_lower or "fazit" in cleaned_heading_lower:
        prompt = f"Was ist das Ergebnis des Gutachtens Nr. {gutachten_nummer} vom {erscheinungsdatum}{normen_str}? Fasse die wesentlichen rechtlichen Schlussfolgerungen und deren Begründung zusammen. Zeige klar die Subsumtionskette auf und verbinde die rechtlichen Grundlagen mit dem konkreten Sachverhalt."
    
    elif "tatbestand" in cleaned_heading_lower:
        prompt = f"Stelle den Tatbestand im Gutachten Nr. {gutachten_nummer} vom {erscheinungsdatum}{normen_str} dar. Fokussiere auf die relevanten Fakten und Umstände. Differenziere zwischen unstrittigem und streitigem Sachverhalt und arbeite das Begehren der Parteien klar heraus."
    
    elif "entscheidungsgründe" in cleaned_heading_lower or "gründe" in cleaned_heading_lower:
        prompt = f"Erläutere die Entscheidungsgründe im Gutachten Nr. {gutachten_nummer} vom {erscheinungsdatum}{normen_str}. Gehe auf die rechtliche Begründung der Entscheidung ein, einschließlich der Auslegung der relevanten Normen, der Subsumtion und der daraus resultierenden Rechtsfolgen."
    
    elif "rechtslage" in cleaned_heading_lower or "rechtliche würdigung" in cleaned_heading_lower:
        prompt = f"Erörtere die Rechtslage zum Gutachten Nr. {gutachten_nummer} vom {erscheinungsdatum}{normen_str}. Stelle die einschlägigen Rechtsnormen dar und erläutere ihre Auslegung und Anwendung auf den konkreten Fall. Berücksichtige dabei relevante Rechtsprechung und Lehrmeinungen."
    
    elif "subsumtion" in cleaned_heading_lower:
        prompt = f"Führe eine Subsumtion für das Gutachten Nr. {gutachten_nummer} vom {erscheinungsdatum}{normen_str} durch. Wende die relevanten Rechtsnormen Schritt für Schritt auf den Sachverhalt an. Prüfe die einzelnen Tatbestandsmerkmale systematisch und erläutere, ob sie im vorliegenden Fall erfüllt sind."
    
    elif "einleitung" in cleaned_heading_lower:
        prompt = f"Verfasse eine Einleitung zum Gutachten Nr. {gutachten_nummer} vom {erscheinungsdatum}{normen_str}. Führe kurz in die Thematik ein und skizziere den rechtlichen Kontext sowie die Bedeutung des zu behandelnden Rechtsproblems."
    
    elif "anspruchsgrundlage" in cleaned_heading_lower:
        prompt = f"Identifiziere und erläutere die relevanten Anspruchsgrundlagen im Gutachten Nr. {gutachten_nummer} vom {erscheinungsdatum}{normen_str}. Begründe, warum diese Normen im vorliegenden Fall einschlägig sind und welche Voraussetzungen erfüllt sein müssen."
    
    elif "zulässigkeit" in cleaned_heading_lower:
        prompt = f"Prüfe die Zulässigkeit im Gutachten Nr. {gutachten_nummer} vom {erscheinungsdatum}{normen_str}. Gehe dabei auf alle relevanten prozessualen Voraussetzungen ein und begründe deine Einschätzung anhand der einschlägigen Verfahrensvorschriften."
    
    elif "begründetheit" in cleaned_heading_lower:
        prompt = f"Prüfe die Begründetheit im Gutachten Nr. {gutachten_nummer} vom {erscheinungsdatum}{normen_str}. Untersuche, ob der geltend gemachte Anspruch materiell-rechtlich besteht und alle Voraussetzungen der Anspruchsgrundlage erfüllt sind."
    
    elif "spezifikation" in cleaned_heading_lower:
        prompt = f"Erläutere die juristische Spezifikation im Gutachten Nr. {gutachten_nummer} vom {erscheinungsdatum}{normen_str}. Gehe detailliert auf die spezifischen rechtlichen Anforderungen ein und arbeite die Besonderheiten dieses Falles heraus."
    
    elif "rechtsfolge" in cleaned_heading_lower:
        prompt = f"Beschreibe die Rechtsfolgen im Gutachten Nr. {gutachten_nummer} vom {erscheinungsdatum}{normen_str}. Lege dar, welche rechtlichen Konsequenzen sich aus der juristischen Beurteilung des Falles ergeben und welche praktischen Auswirkungen diese haben."
    
    # Fallback für sonstige oder generische Überschriften
    else:
        # Versuche, aus der Überschrift oder enthaltenen Gesetzen einen spezifischeren Prompt zu generieren
        if "§" in heading or "Art." in heading or "Artikel" in heading:
            # Die Überschrift enthält einen Gesetzeshinweis
            prompt = f"Erläutere die Anwendung und Bedeutung von {heading} im Kontext des Gutachtens Nr. {gutachten_nummer} vom {erscheinungsdatum}{normen_str}. Zeige auf, wie diese Rechtsnorm im vorliegenden Fall auszulegen ist und welche Folgen sich daraus ergeben."
        elif any(gesetz in heading.lower() for gesetz in ["bgb", "stgb", "hgb", "zpo", "stpo", "vwgo", "gg"]):
            # Die Überschrift enthält ein spezifisches Gesetz
            prompt = f"Erläutere die Anwendung des {heading} im Gutachten Nr. {gutachten_nummer} vom {erscheinungsdatum}{normen_str}. Analysiere die relevanten Bestimmungen des Gesetzes und ihre Bedeutung für den vorliegenden Fall."
        else:
            # Generischer Prompt mit Berücksichtigung der Anzahl an Segmenten
            if segments_count_for_current_gutachten <= 3:
                # Bei wenigen Segmenten wahrscheinlich ein wichtiger Teil des Gutachtens
                prompt = f"Erzeuge den Abschnitt '{heading}' des Gutachtens Nr. {gutachten_nummer} vom {erscheinungsdatum}{normen_str}. Dieser Abschnitt stellt einen wesentlichen Teil des Gutachtens dar. Achte auf eine präzise juristische Sprache und klare Argumentationsführung."
            else:
                # Bei vielen Segmenten eher ein spezifischer Detailaspekt
                prompt = f"Verfasse den Teilaspekt '{heading}' für das Gutachten Nr. {gutachten_nummer} vom {erscheinungsdatum}{normen_str}. Gehe gezielt auf diesen spezifischen Punkt ein und stelle den Zusammenhang zum Gesamtgutachten her."

    # Finalisierung des Prompts mit kontextueller Anpassung basierend auf Rechtsnormen
    if normen_list and len(normen_list) > 0:
        # Spezifischere Aufforderung bei vorhandenen Rechtsnormen
        if len(normen_list) == 1:
            prompt += f" Beziehe dich explizit auf {normen_list[0]} und erläutere die korrekte Auslegung und Anwendung dieser Norm."
        else:
            prompt += f" Berücksichtige dabei besonders das Zusammenspiel der genannten Rechtsnormen und ihre gegenseitige Beeinflussung."
            
    return prompt

def segment_text(text_content):
    """
    Segmentiert einen Gutachtentext in logische Abschnitte durch Erkennung von Überschriften
    und strukturellen Merkmalen. Verbesserte Version mit intelligigerer Segmenterkennung.
    
    Args:
        text_content: Der zu segmentierende Text
        
    Returns:
        Eine Liste von Tupeln (Überschrift, Abschnittstext)
    """
    sections = []
    
    # ---- ERWEITERTE HEURISTISCHE PATTERN-ERKENNUNG ----
    
    # Hauptüberschriften (römische Zahlen, Abschnittsmuster)
    major_heading_pattern = re.compile(
        r"^((?:[A-Z]\.|[IVX]+\.|[0-9]+\.)\s+.{1,80}|"
        r"I\. Sachverhalt|II\. Rechtliche Würdigung|III\.|IV\.)\s*[:.]?\s*$",
        re.MULTILINE | re.IGNORECASE
    )
    
    # Nummerierte Überschriften (1., 2., etc. oder 1.1, 1.2, etc.)
    numbered_heading_pattern = re.compile(r"^(?:\d+)\.(?:\d+)?(?:\d+)?\s+", re.MULTILINE)
    
    # Gesetzesverweise als potenzielle Abschnittsgrenzen
    law_reference_pattern = re.compile(r"^(?:§|Art\.?|Artikel)\s*\d+.*?$", re.MULTILINE)
    
    # Erweiterte Erkennung von juristischen Spezifikationen 
    specification_pattern = re.compile(r"^(Im Sinne von|In Anwendung von|Nach|Gemäß|Laut|Entsprechend)\s+(?:§|Art\.?|Artikel)\s*\d+.*?$", re.MULTILINE | re.IGNORECASE)
    
    # Schlüsselwörter wie "Sachverhalt", "Frage", etc. - erweiterte Liste
    keyword_heading_pattern = re.compile(
        r"^(Sachverhalt|Frage(?:n)?|Zur Rechtslage|Rechtslage|Ergebnis|Lösung|Beurteilung|"
        r"Tenor|Einleitung|Zusammenfassung|Fazit|Gutachten|Begründung|Stellungnahme|"
        r"Gründe|Entscheidungsgründe|Tatbestand|Anmerkung|Anwendbares Recht|Auslegung|"
        r"Subsumtion|Voraussetzungen|Rechtsgrundlage|Materielles Recht|Formelles Recht|"
        r"Prozessvoraussetzungen|Zulässigkeit|Begründetheit|Anspruchsgrundlage|Prüfung|"
        r"Rechtliche Grundlagen|Gutachterlicher Teil|Erläuterung|Rechtsfolge(?:n)?|"
        r"Antragsstellung|Verhältnismäßigkeit|Schadensersatzanspruch|"
        r"Gesetzliche Grundlage|Haftung|Streitgegenstand|Problematik|"
        r"Normzweck|Normauslegung|Art und Weise|Analyse|Kurzes Fazit|Beweiserhebung"
        r")[\s:.]",
        re.MULTILINE | re.IGNORECASE
    )
    
    # Juristische Wendungen, die typischerweise Abschnitte einleiten
    legal_phrase_pattern = re.compile(
        r"^(Hiermit erstatte ich folgendes Rechtsgutachten|"
        r"In der vorliegenden Rechtssache|"
        r"Das vorliegende Gutachten behandelt die Frage|"
        r"Ich wurde gebeten, zu folgender Rechtsfrage|"
        r"In der Angelegenheit|"
        r"Folgender Sachverhalt liegt vor|"
        r"Zunächst ist festzustellen|"
        r"Der Senat hat hierzu folgendes entschieden|"
        r"Anders als im Urteil des|"
        r"Es gilt zu prüfen|"
        r"Im Ergebnis ist festzuhalten|"
        r"In der Entscheidung vom)"
    )
    
    # Strukturierte Entscheidungsmuster
    decision_pattern = re.compile(
        r"^(Die Kammer|Der Senat|Das Gericht|Im Ergebnis|Zusammenfassend|"
        r"Im Tenor|Gemäß ständiger Rechtsprechung|Die herrschende Meinung|"
        r"Abweichend hiervon|Im Unterschied zu|Im Gegensatz zur Auffassung|"
        r"Dem Antrag folgend|Im Sinne des Gesetzgebers)")

    # Suche zunächst nach Hauptüberschriften (römische Zahlen, Buchstaben)
    parts = major_heading_pattern.split(text_content)
    headings_markers = major_heading_pattern.findall(text_content)

    if len(parts) > 1:
        # Es wurden Hauptüberschriften gefunden
        if parts[0].strip() and len(parts[0].strip()) > 50:  # Füge Einleitung nur hinzu, wenn substantiell
            sections.append(("Einleitung", parts[0].strip()))
        
        for i, marker_text in enumerate(headings_markers):
            section_content_full = parts[i+1] 
            potential_title_line = section_content_full.lstrip().split('\n', 1)[0].strip()
            current_heading_text = marker_text.strip()
            
            if potential_title_line and len(potential_title_line) < 100 and not potential_title_line.endswith('.'):
                current_heading_text = f"{marker_text.strip()} {potential_title_line}"
                if section_content_full.lstrip().startswith(potential_title_line):
                    section_content_full = section_content_full.lstrip()[len(potential_title_line):]
            
            final_section_content = section_content_full.strip()
            if final_section_content:
                sections.append((current_heading_text, final_section_content))
    
    # Wenn keine Hauptüberschriften gefunden wurden, versuche nummerierte Überschriften
    elif not sections:
        parts = numbered_heading_pattern.split(text_content)
        headings_markers = numbered_heading_pattern.findall(text_content)
        
        if len(parts) > 1:
            # Es wurden nummerierte Überschriften gefunden
            if parts[0].strip() and len(parts[0].strip()) > 50:
                sections.append(("Einleitung", parts[0].strip()))
            
            for i, marker_text in enumerate(headings_markers):
                section_content_full = parts[i+1]
                potential_title_line = section_content_full.lstrip().split('\n', 1)[0].strip()
                current_heading_text = marker_text.strip()
                
                if potential_title_line and len(potential_title_line) < 100 and not potential_title_line.endswith('.'):
                    current_heading_text = f"{marker_text.strip()} {potential_title_line}"
                    if section_content_full.lstrip().startswith(potential_title_line):
                        section_content_full = section_content_full.lstrip()[len(potential_title_line):]
                
                final_section_content = section_content_full.strip()
                if final_section_content:
                    sections.append((current_heading_text, final_section_content))

        # Wenn keine nummerierten Überschriften gefunden wurden, versuche Schlüsselwörter
        if not sections:
            kw_matches = list(keyword_heading_pattern.finditer(text_content))
            
            if kw_matches:
                # Es wurden Schlüsselwörter gefunden
                current_pos = 0
                if kw_matches[0].start() > 0:
                    intro_text = text_content[current_pos:kw_matches[0].start()].strip()
                    if intro_text and len(intro_text) > 50:
                        sections.append(("Einleitung", intro_text))
                
                for i, match in enumerate(kw_matches):
                    heading_text_kw = match.group(1).strip() 
                    content_start_kw = match.end()
                    if i + 1 < len(kw_matches):
                        content_end_kw = kw_matches[i+1].start()
                    else:
                        content_end_kw = len(text_content)
                    section_content_kw = text_content[content_start_kw:content_end_kw].strip()
                    
                    # Verbesserte Intelligente Validierung: Prüft, ob der Abschnitt sinnvoll ist
                    # indem Mindestlänge, Satzmuster und unvollständige Abschnittsübergänge geprüft werden
                    is_valid_section = (
                        len(section_content_kw) > 50 and  # Mindestlänge
                        section_content_kw.count('. ') > 2 and  # Enthält vollständige Sätze
                        not (section_content_kw.strip().startswith('§') and len(section_content_kw.split('\n', 1)[0]) < 100)  # Kein Gesetzestext-Beginn
                    )
                    
                    if section_content_kw and is_valid_section: 
                        # Inhaltlich passendere Überschrift wählen
                        section_content_lower = section_content_kw.lower()
                        if heading_text_kw.lower() == "beurteilung" and "rechtliche würdigung" in section_content_lower:
                            heading_text_kw = "Rechtliche Würdigung"
                        elif heading_text_kw.lower() == "frage" and "rechtsfrage" in section_content_lower:
                            heading_text_kw = "Rechtsfrage"
                            
                        sections.append((heading_text_kw, section_content_kw))
            
            # Suche nach juristischen Spezifikationsmustern
            if not sections:
                spec_matches = list(specification_pattern.finditer(text_content))
                
                if spec_matches and len(spec_matches) >= 1:
                    current_pos = 0
                    if spec_matches[0].start() > 0:
                        intro_text = text_content[current_pos:spec_matches[0].start()].strip()
                        if intro_text and len(intro_text) > 50:
                            sections.append(("Einleitung", intro_text))
                    
                    for i, match in enumerate(spec_matches):
                        spec_text = match.group(0).strip()
                        spec_prefix = match.group(1).strip()
                        content_start = match.start()
                        
                        # Finde das Ende dieses Abschnitts
                        if i + 1 < len(spec_matches):
                            content_end = spec_matches[i+1].start()
                        else:
                            content_end = len(text_content)
                            
                        paragraph_text = text_content[content_start:content_end].strip()
                        
                        if paragraph_text and len(paragraph_text) > 50:
                            heading = f"Spezifikation: {spec_text[:50]}..." if len(spec_text) > 50 else f"Spezifikation: {spec_text}"
                            sections.append((heading, paragraph_text))
                            
            # Als letzten Versuch: Überprüfe auf Gesetzesverweise
            if not sections:
                law_refs = list(law_reference_pattern.finditer(text_content))
                
                if law_refs and len(law_refs) >= 2:  # Mindestens 2 Verweise, damit eine sinnvolle Aufteilung möglich ist
                    current_pos = 0
                    if law_refs[0].start() > 50:  # Einleitung ist substantiell
                        intro_text = text_content[current_pos:law_refs[0].start()].strip()
                        if intro_text:
                            sections.append(("Einleitung", intro_text))
                    
                    for i, match in enumerate(law_refs):
                        law_ref = match.group(0).strip()
                        content_start = match.start()
                        
                        # Finde das Ende dieses Abschnitts (nächster Verweis oder Ende des Textes)
                        if i + 1 < len(law_refs):
                            content_end = law_refs[i+1].start()
                        else:
                            content_end = len(text_content)
                            
                        # Extrahiere den vollständigen Absatz, der mit dem Gesetzesverweis beginnt
                        paragraph_text = text_content[content_start:content_end].strip()
                        
                        if paragraph_text and len(paragraph_text) > 50:  # Nur sinnvolle Absätze hinzufügen
                            heading = f"Abschnitt zu {law_ref}"
                            sections.append((heading, paragraph_text))
    
    # Nachbearbeitung: Entferne leere Abschnitte und führe kleinere zusammen
    sections = [(h, c) for h, c in sections if c.strip()]
    
    # Wenn sehr kurze Abschnitte (< 200 Zeichen) vorhanden sind, versuche diese mit benachbarten zu verbinden
    if sections and any(len(c) < 200 for _, c in sections):
        merged_sections = []
        i = 0
        while i < len(sections):
            heading, content = sections[i]
            
            # Wenn der Abschnitt kurz ist und nicht der letzte, versuche ihn mit dem nächsten zu verbinden
            if len(content) < 200 and i < len(sections) - 1:
                next_heading, next_content = sections[i+1]
                merged_heading = f"{heading} + {next_heading}"
                merged_content = f"{content}\n\n{next_content}"
                merged_sections.append((merged_heading, merged_content))
                i += 2  # Überspringe den nächsten Abschnitt, da er bereits zusammengeführt wurde
            else:
                merged_sections.append((heading, content))
                i += 1
        
        sections = merged_sections
    
    # Optimierung: Wenn wir viele kurze Abschnitte (> 5 Abschnitte mit < 300 Zeichen),
    # versuche, eine intelligentere Zusammenführung basierend auf thematischer Ähnlichkeit
    short_sections = [(i, (h, c)) for i, (h, c) in enumerate(sections) if len(c) < 300]
    if len(short_sections) > 5 and len(short_sections) > len(sections) * 0.4:  # Wenn > 40% der Abschnitte kurz sind
        temp_sections = sections.copy()
        merged = set()  # Halte bereits zusammengeführte Indizes
        
        for i, (h1, c1) in short_sections:
            if i in merged:
                continue
                
            # Suche nach dem nächsten thematisch ähnlichen Abschnitt
            for j, (h2, c2) in short_sections:
                if i != j and j not in merged and j > i:
                    # Einfache Heuristik für thematische Ähnlichkeit: Gemeinsame Wörter in Überschriften
                    h1_words = set(h1.lower().split())
                    h2_words = set(h2.lower().split())
                    common_words = h1_words.intersection(h2_words)
                    
                    if common_words or (len(h1_words) > 0 and len(h2_words) > 0 and 
                                      (h1_words.issubset(h2_words) or h2_words.issubset(h1_words))):
                        merged_heading = f"{h1} + {h2}"
                        merged_content = f"{c1}\n\n{c2}"
                        temp_sections[i] = (merged_heading, merged_content)
                        merged.add(j)
                        break
        
        # Erstelle die endgültige Liste ohne die zusammengeführten Abschnitte
        final_sections = [section for i, section in enumerate(temp_sections) if i not in merged]
        if len(final_sections) < len(sections):  # Nur wenn wir tatsächlich Zusammenführungen vorgenommen haben
            sections = final_sections
    
    # Verbesserte Inhaltserkennung: Identifiziere juristische Inhaltsmuster für genauere Überschriften
    for i, (heading, content) in enumerate(sections):
        content_lower = content.lower()
        if "sachverhalt" in heading.lower():
            # Typ bleibt "Sachverhalt"
            pass
        elif ("rechtsfrage" in content_lower or "gutachtenfrage" in content_lower) and "frage" in heading.lower():
            sections[i] = ("Rechtsfrage", content)
        elif "rechtslage" in content_lower and not "rechtslage" in heading.lower():
            sections[i] = ("Rechtslage", content)
        elif ("subsumtion" in content_lower or "tatbestandsmerkmal" in content_lower) and not any(x in heading.lower() for x in ["subsumtion", "tatbestand"]):
            sections[i] = ("Subsumtion", content)
        elif "ergebnis" in content_lower[:300] and not "ergebnis" in heading.lower() and len(content) < 1000:
            sections[i] = ("Ergebnis", content)
        elif "gutachten" in heading.lower() and ("sachverhalt" in content_lower[:500] or "rechtsfrage" in content_lower[:500]):
            sections[i] = ("Gutachten (mit Sachverhalt)", content)
    
    return sections

def prepare_data_for_training(input_file_path, token_limit_millions):
    """
    Bereitet Trainingsdaten für ein LLM vor, indem es Gutachtentexte in sinnvolle Segmente aufteilt
    und formatierte Prompts generiert, die für das Training verwendet werden können.
    
    Args:
        input_file_path: Pfad zur JSON-Datei mit den Gutachtendaten
        token_limit_millions: Maximale Anzahl von Tokens in Millionen für die Ausgabedatei oder 
                             Dictionary mit Optionen (limit, skip_international, content_only, no_role, all_segments)
    """
    # Unpack the token limit and flags from dictionary
    if isinstance(token_limit_millions, dict):
        skip_international = token_limit_millions.get('skip_international', False)
        content_only = token_limit_millions.get('content_only', False)
        no_role = token_limit_millions.get('no_role', False)
        all_segments = token_limit_millions.get('all_segments', False)
        process_one = token_limit_millions.get('process_one', False)  # New flag for one at a time
        token_limit_millions = token_limit_millions.get('limit', 2.0)
    else:
        skip_international = False  # Default is to not skip international entries
        content_only = False  # Default is to include prompts
        no_role = False  # Default is to include role information
        all_segments = False  # Default is to only show segments included in output file
        process_one = False  # Default is to process all Gutachten

    base, ext = os.path.splitext(input_file_path)
    if "_prepared" in base or "_segmented" in base:
        print(f"{Colors.WARNING}Warning: Input file '{input_file_path}' seems to be an already processed file. {Colors.ENDC}")
        print("This script should ideally run on the output of 'jsonl_converter.py'.")
        base = base.replace("_prepared", "").replace("_segmented", "")

    # Handle token limit - for "max" (infinity), use a special suffix
    is_unlimited = math.isinf(token_limit_millions)
    if is_unlimited:
        token_suffix_for_filename = "_max"
        actual_max_tokens = float('inf')  # Set to infinity - will be completely ignored
    else:
        token_suffix_for_filename = format_token_limit_for_filename(token_limit_millions)
        actual_max_tokens = int(token_limit_millions * 1_000_000)
        
    output_file_path = base + token_suffix_for_filename + "_segmented_prepared.jsonl"

    # Counters and flags initialization
    processed_gutachten_count = 0
    total_segments_generated = 0
    skipped_due_to_json_decode_error = 0 # For line-by-line errors in JSONL
    skipped_due_to_missing_fields_total = 0
    missing_field_counts = {"erscheinungsdatum": 0, "gutachten_nummer": 0, "text": 0}
    skipped_international_rechtsbezug_count = 0
    current_total_tokens = 0
    token_limit_reached_flag = False
    skipped_gutachten_due_to_token_limit = 0
    skipped_tokens_due_to_token_limit = 0
    missing_normen_count = 0  # Neue Zählung für Gutachten ohne Normen
    total_potential_tokens = 0  # Zähler für alle potenziellen Tokens (wenn -a verwendet wird)
    total_potential_segments = 0  # Zähler für alle potenziellen Segmente (wenn -a verwendet wird)
    
    # Zeitmessung starten
    start_time = datetime.datetime.now()
    
    items_to_process = []
    all_segmented_gutachten = []  # Neue Liste für alle segmentierten Gutachten
    initial_input_item_count = 0
    line_number_for_messages = 0 # Used for messages, distinct from loop iterator if from JSON list

    try:
        if ext.lower() == ".json":
            print(f"{Colors.OKBLUE}ℹ Info: Versuche '{input_file_path}' als JSON-Datei zu laden.{Colors.ENDC}")
            try:
                with open(input_file_path, 'r', encoding='utf-8') as f:
                    loaded_data = json.load(f)
                if not isinstance(loaded_data, list):
                    print(f"{Colors.FAIL}✖ Fehler: Eingabe-JSON-Datei '{input_file_path}' enthält keine Liste von Gutachten.{Colors.ENDC}")
                    return
                items_to_process = loaded_data
                initial_input_item_count = len(items_to_process)
                print(f"{Colors.OKGREEN}✓ Info: Erfolgreich {initial_input_item_count} Elemente aus JSON-Datei '{input_file_path}' geladen.{Colors.ENDC}")
            except json.JSONDecodeError as e:
                print(f"{Colors.FAIL}✖ Fehler: Konnte JSON-Datei '{input_file_path}' nicht decodieren: {e}{Colors.ENDC}")
                return # Cannot proceed if the whole JSON file is bad
            except FileNotFoundError:
                print(f"{Colors.FAIL}✖ Fehler: Eingabedatei '{input_file_path}' nicht gefunden.{Colors.ENDC}")
                return
        
        else: # Process as JSONL or try as best guess for other extensions
            if ext.lower() == ".jsonl":
                print(f"{Colors.OKBLUE}ℹ Info: Versuche '{input_file_path}' als JSONL-Datei zu laden.{Colors.ENDC}")
            else:
                print(f"{Colors.WARNING}⚠ Warnung: Eingabedatei '{input_file_path}' hat die Erweiterung '{ext}'. Versuche, als JSONL zu verarbeiten.{Colors.ENDC}")
            
            temp_items = []
            raw_lines_count = 0
            try:
                with open(input_file_path, 'r', encoding='utf-8') as infile:
                    for i, line_content in enumerate(infile, 1):
                        raw_lines_count = i
                        line_content_stripped = line_content.strip()
                        if not line_content_stripped: # Skip empty lines
                            continue
                        try:
                            item = json.loads(line_content_stripped)
                            temp_items.append(item)
                        except json.JSONDecodeError as e:
                            print(f"{Colors.WARNING}⚠ Warnung: Überspringe Zeile {i} in Eingabedatei '{input_file_path}' wegen JSON-Decodierungsfehler: {e}.{Colors.ENDC}")
                            skipped_due_to_json_decode_error += 1
                items_to_process = temp_items
                initial_input_item_count = len(temp_items) + skipped_due_to_json_decode_error  # Total valid items + skipped items
                print(f"{Colors.OKGREEN}✓ Info: {raw_lines_count} Zeilen aus Datei '{input_file_path}' verarbeitet, {len(items_to_process)} gültige Elemente geladen.{Colors.ENDC}")
            except FileNotFoundError:
                print(f"{Colors.FAIL}✖ Fehler: Eingabedatei '{input_file_path}' nicht gefunden.{Colors.ENDC}")
                return

        # Main processing loop using items_to_process
        print(f"\n{Colors.HEADER}{Colors.BOLD}❯❯❯ Starte Verarbeitung von {len(items_to_process)} Elementen...{Colors.ENDC}")
        total_items = len(items_to_process)
        progress_step = max(1, min(10, total_items // 10))  # Show progress every 10% or at least every item
        progress_next = progress_step
        
        # Create file and open for writing immediately if not using -a flag
        # With -a flag, we'll process all items first, then write the file up to the token limit
        file_created = False
        outfile = None
        
        if not all_segments:
            file_created = True
            outfile = open(output_file_path, 'w', encoding='utf-8')
        else:
            # For the -a flag, we'll collect all items first, then write to the file later
            all_segmented_gutachten = []
        
        for current_item_idx, item in enumerate(items_to_process, 1):
            line_number_for_messages = current_item_idx # For user messages, refers to item index
            
            # Show progress indicator
            if current_item_idx >= progress_next or current_item_idx == total_items:
                progress_percent = (current_item_idx / total_items) * 100
                print(f"{Colors.OKBLUE}ℹ Verarbeite Element {current_item_idx}/{total_items} ({progress_percent:.1f}%)...{Colors.ENDC}")
                progress_next = min(total_items, current_item_idx + progress_step)

            rechtsbezug = item.get("rechtsbezug")
            # Make skipping international entries optional based on command-line flag
            if skip_international and rechtsbezug == "International":
                print(f"{Colors.OKCYAN}ℹ Überspringe Element {line_number_for_messages} weil 'rechtsbezug' ist 'International' und -in Flag wurde verwendet.{Colors.ENDC}")
                skipped_international_rechtsbezug_count += 1
                continue

            # Get required fields
                        # Get required fields
            erscheinungsdatum = item.get("erscheinungsdatum")
            gutachten_nummer = item.get("gutachten_nummer")
            text_content = item.get("text")
            normen = item.get("normen", "")
            
            # Process normen field to make it more useful
            normen_list = []
            if normen:
                # Debug info to help diagnose issues with normen field
                print(f"{Colors.OKCYAN}  ℹ Rohwert des normen-Felds: {Colors.BOLD}{normen}{Colors.ENDC}")
                
                # First, simply try to split by common separators
                raw_normen = normen.replace(';', ',')
                primary_list = [norm.strip() for norm in raw_normen.split(',') if norm.strip()]
                
                if primary_list:
                    # If we have entries after simple splitting, use them directly
                    normen_list = primary_list
                else:
                    # Try more advanced pattern matching if simple splitting didn't work
                    # Handle patterns like "StGB § 123" or "EUErbVO Art. 70"
                    norm_pattern = re.compile(r'([A-Za-zÄÖÜäöüß]+(?:\s*\d*)?)\s*(?:§|Art\.?|Artikel)?\s*(\d+(?:\w*)?)', re.IGNORECASE)
                    
                    # Try to find structured patterns
                    matches = norm_pattern.findall(raw_normen)
                    if matches:
                        for law, section in matches:
                            norm = f"{law.strip()} § {section.strip()}"
                            if norm.strip():
                                normen_list.append(norm.strip())
                    else:
                        # Last resort: just add the whole string as one norm if it's not empty
                        if normen.strip():
                            normen_list = [normen.strip()]
            
            # Remove duplicates while preserving order
            if normen_list:
                seen = set()
                normen_list = [x for x in normen_list if not (x in seen or seen.add(x))]
                # Zeige die erkannten Normen für dieses Gutachten an
                normen_str = ", ".join(normen_list)
                print(f"{Colors.OKGREEN}  ✓ Normen erkannt: {Colors.BOLD}{normen_str}{Colors.ENDC}")
            else:
                missing_normen_count += 1  # Zähle Gutachten ohne Normen
                print(f"{Colors.WARNING}  ⚠ Keine Normen erkannt oder angegeben {Colors.BOLD}(Feld 'normen' leer oder nicht vorhanden){Colors.ENDC}")
                print(f"{Colors.OKCYAN}    ℹ Hinweis: Die Qualität der Segmentierung und Prompt-Generierung kann durch Rechtsnormen verbessert werden{Colors.ENDC}")
                
            if not all([erscheinungsdatum, gutachten_nummer, text_content]):
                print(f"{Colors.WARNING}⚠ Warnung: Überspringe Element {line_number_for_messages} wegen fehlender Pflichtfelder.{Colors.ENDC}")
                skipped_due_to_missing_fields_total +=1
                if not erscheinungsdatum: missing_field_counts["erscheinungsdatum"] += 1
                if not gutachten_nummer: missing_field_counts["gutachten_nummer"] += 1
                if not text_content: missing_field_counts["text"] += 1
                # Detailed print of missing fields already happens in the original code if needed, or can be added here
                continue
            
            # Segmentiere den Text immer, unabhängig vom Token-Limit
            processed_gutachten_count += 1 
            
            # Verwende die erweiterte semantische Segmentierung, wenn verfügbar
            if ENHANCED_SEGMENTATION_AVAILABLE:
                try:
                    segments = enhanced_segment_text(text_content)
                    if segments:
                        print(f"{Colors.OKGREEN}  ✓ Gutachten mit erweiterter semantischer Analyse in {len(segments)} Segmente unterteilt:{Colors.ENDC}")
                    else:
                        segments = segment_text(text_content)  # Fallback zur regulären Segmentierung
                        print(f"{Colors.WARNING}  ⚠ Erweiterte semantische Segmentierung ergab keine Ergebnisse, Fallback zur regulären Segmentierung ({len(segments)} Segmente):{Colors.ENDC}")
                except Exception as e:
                    print(f"{Colors.WARNING}  ⚠ Fehler bei erweiterter semantischer Segmentierung: {str(e)}, Fallback zur regulären Segmentierung{Colors.ENDC}")
                    import traceback
                    tb_lines = traceback.format_exc().splitlines()
                    print(f"{Colors.WARNING}  Details: {tb_lines[-3:] if len(tb_lines) >= 3 else tb_lines}{Colors.ENDC}")
                    
                    # Detaillierte Diagnose für häufige Fehlerquellen
                    if "not subscriptable" in str(e):
                        print(f"{Colors.WARNING}  Diagnose: Wahrscheinlich ein Problem mit Vektordaten oder Ähnlichkeitsberechnungen{Colors.ENDC}")
                    elif "object has no attribute" in str(e):
                        print(f"{Colors.WARNING}  Diagnose: Wahrscheinlich ein Problem mit fehlenden Attributen oder Funktionen{Colors.ENDC}")
                    elif "list index out of range" in str(e) or "index out of range" in str(e):
                        print(f"{Colors.WARNING}  Diagnose: Liste oder Array-Index-Problem, möglicherweise fehlerhafte Segmentgrenzen{Colors.ENDC}")
                    
                    segments = segment_text(text_content)  # Fallback zur regulären Segmentierung
            else:
                segments = segment_text(text_content)
            
            if not segments: 
                print(f"{Colors.WARNING}⚠ Warnung: Konnte Gutachten Nr. {gutachten_nummer} (Element {line_number_for_messages}) nicht segmentieren. Verwende vollständigen Text als Fallback.{Colors.ENDC}")
                segments = [("Gesamter Text", text_content.strip())]
            
            # Zähle potentielle Tokens für dieses Gutachten (für -a Statistik)
            potential_tokens_in_gutachten = 0
            segment_data = []
            
            for heading, segment_text in segments:
                if not segment_text.strip():
                    continue
                    
                # Create the actual data we'll write to the output file
                if content_only:
                    # Nur Content ohne Prompt (-c Parameter)
                    output_data = {
                        "messages": [
                            {
                                "role": "assistant" if not no_role else "",
                                "content": segment_text 
                            }
                        ]
                    }
                else:
                    # Mit Prompt (Standardverhalten)
                    user_prompt = _generate_user_prompt(heading, gutachten_nummer, erscheinungsdatum, len(segments), normen_list)
                    output_data = {
                        "messages": [
                            {
                                "role": "system" if not no_role else "", 
                                "content": "Du bist ein KI-Assistent, der juristische Gutachtentexte erstellt. Deine Aufgabe ist es, präzise rechtliche Analysen zu erstellen, die die relevanten Rechtsnormen korrekt anwenden und erläutern. Achte besonders auf die genaue Interpretation und Anwendung der genannten Normen im jeweiligen rechtlichen Kontext. Folge der juristischen Gutachtentechnik mit klarer Trennung von Sachverhalt, rechtlicher Prüfung und Ergebnis. Halte dich streng an die Methodenlehre der juristischen Auslegung und Subsumtion. Deine Aufgabe ist die dogmatisch fundierte und praktisch anwendbare Analyse rechtlicher Probleme unter Berücksichtigung von Rechtsprechung, Literatur und Gesetzgebung. Führe den Leser durch juristische Probleme mit strukturierter Argumentationsführung und klarer Gedankenführung."
                            },
                            {
                                "role": "user" if not no_role else "", 
                                "content": user_prompt
                            },
                            {
                                "role": "assistant" if not no_role else "", 
                                "content": segment_text 
                            }
                        ]
                    }
                
                # Convert to JSON and get token count
                line_to_write = json.dumps(output_data, ensure_ascii=False)
                tokens_for_this_segment = len(line_to_write)
                potential_tokens_in_gutachten += tokens_for_this_segment
                
                # Save segment data for potential writing
                segment_data.append((heading, segment_text, line_to_write, tokens_for_this_segment))
            
            total_potential_segments += len(segment_data)
            total_potential_tokens += potential_tokens_in_gutachten
            
            # Check token limit - skip completely if is_unlimited (i.e., -t max parameter)
            if is_unlimited:
                # If using "max" token limit, always include this gutachten regardless of size
                if all_segments:
                    # Just collect for later - we'll count all segments for statistics
                    all_segmented_gutachten.append((gutachten_nummer, erscheinungsdatum, segment_data, normen_list, potential_tokens_in_gutachten))
                else:
                    # Direct write mode with unlimited token limit
                    for heading, _, line_to_write, tokens_for_this_segment in segment_data:
                        outfile.write(line_to_write + '\n')
                        current_total_tokens += tokens_for_this_segment
                        total_segments_generated += 1
            # Normal token limit checking for other cases
            elif all_segments or (current_total_tokens + potential_tokens_in_gutachten <= actual_max_tokens):
                # We can include this gutachten - either unlimited tokens, all segments mode, or within limit
                if all_segments:
                    # Just collect for later - we'll write as much as possible at the end
                    all_segmented_gutachten.append((gutachten_nummer, erscheinungsdatum, segment_data, normen_list, potential_tokens_in_gutachten))
                else:
                    # Direct write mode - write each segment immediately
                    for heading, _, line_to_write, tokens_for_this_segment in segment_data:
                        outfile.write(line_to_write + '\n')
                        current_total_tokens += tokens_for_this_segment
                        total_segments_generated += 1
                        
                # If process_one flag and we've processed one Gutachten, exit the loop
                if process_one and processed_gutachten_count == 1:
                    print(f"{Colors.OKGREEN}✓ Process-one mode: Erfolgreich 1 Gutachten verarbeitet wie mit dem -o Parameter angefordert.{Colors.ENDC}")
                    break
            else:
                # Token limit would be exceeded
                if not token_limit_reached_flag:
                    token_limit_reached_flag = True
                    print(f"{Colors.WARNING}⚠ Token-Limit erreicht nach Verarbeitung von {processed_gutachten_count} Gutachten. Weitere Gutachten werden übersprungen.{Colors.ENDC}")
                    print(f"{Colors.WARNING}  Übersprungenes Gutachten enthält ca. {potential_tokens_in_gutachten} Tokens.{Colors.ENDC}")
                
                skipped_gutachten_due_to_token_limit += 1
                skipped_tokens_due_to_token_limit += potential_tokens_in_gutachten
                
                # Zeige die erkannten Segmente an
                print(f"{Colors.OKGREEN}  ✓ Gutachten in {len(segments)} Segmente unterteilt:{Colors.ENDC}")
                for idx, (heading, _) in enumerate(segments, 1):
                    print(f"{Colors.OKCYAN}    • Segment {idx}: {heading}{Colors.ENDC}")
                
                # For JSON files, we can break the loop as we've already reached the token limit
                # This optimization prevents unnecessary processing of remaining items
                if ext.lower() == ".json" and not all_segments:
                    print(f"{Colors.OKCYAN}  ℹ Optimierung: Verarbeitung weiterer Einträge gestoppt, da Token-Limit erreicht wurde und JSON-Datei als Eingabe verwendet wird.{Colors.ENDC}")
                    break
                
        # If we're using all_segments mode, now write as many segments as we can until token limit
        if all_segments:
            print(f"\n{Colors.HEADER}{Colors.BOLD}❯❯❯ Verarbeite {len(all_segmented_gutachten)} segmentierte Gutachten...{Colors.ENDC}")
            
            # Zurücksetzen der Token-Zählung für die Ausgabe
            current_total_tokens = 0
            token_limit_reached_flag = False
            
            # Zähle die Häufigkeit von Überschriften (für Prompt-Verbesserung)
            heading_counter = defaultdict(int)
            for _, _, segment_data, _, _ in all_segmented_gutachten:
                for heading, _, _, _ in segment_data:
                    normalized_heading = heading.lower().strip()
                    heading_counter[normalized_heading] += 1
            
            # Finde die häufigsten Überschriften
            common_headings = sorted(heading_counter.items(), key=lambda x: x[1], reverse=True)[:10]
            print(f"{Colors.OKBLUE}ℹ Die häufigsten Überschriften in den Gutachten:{Colors.ENDC}")
            for heading, count in common_headings:
                print(f"{Colors.OKCYAN}  • '{heading}': {count} mal{Colors.ENDC}")
            
            # Now write to the file
            with open(output_file_path, 'w', encoding='utf-8') as outfile:
                for gutachten_nummer, erscheinungsdatum, segment_data, normen_list, _ in all_segmented_gutachten:
                    for heading, _, line_to_write, tokens_for_this_segment in segment_data:
                        # With -a flag, write all segments when using -t max, otherwise respect token limit
                        if is_unlimited:
                            # Unlimited mode (-t max) - write all segments regardless of size
                            outfile.write(line_to_write + '\n')
                            current_total_tokens += tokens_for_this_segment
                            total_segments_generated += 1
                        elif current_total_tokens + tokens_for_this_segment <= actual_max_tokens:
                            # Normal token limit mode - write until limit reached
                            outfile.write(line_to_write + '\n')
                            current_total_tokens += tokens_for_this_segment
                            total_segments_generated += 1
                        else:
                            # Token limit reached - continue collecting stats but don't write
                            if not token_limit_reached_flag:
                                print(f"\n{Colors.WARNING}⚠ Token-Limit ({actual_max_tokens:,} Zeichen als Proxy) erreicht. "
                                      f"Stoppe Ausgabe aber fahre mit Statistikerfassung fort. Aktuelles Segment '{heading}' von Gutachten Nr. {gutachten_nummer} nicht geschrieben.{Colors.ENDC}")
                                token_limit_reached_flag = True
                            # Don't break - continue processing for stats but don't write to file
                            continue
        
        # If we opened the file directly (not -a mode), close it
        if file_created and not all_segments:
            outfile.close()

        # --- Summary Printing with improved formatting --- 
        print(f"\n{Colors.HEADER}{Colors.BOLD}┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓{Colors.ENDC}")
        print(f"{Colors.HEADER}{Colors.BOLD}┃             VERARBEITUNGSZUSAMMENFASSUNG            ┃{Colors.ENDC}")
        print(f"{Colors.HEADER}{Colors.BOLD}┗━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┛{Colors.ENDC}")
        print(f"{Colors.OKBLUE}➤ Ausgabedatei: {Colors.BOLD}'{output_file_path}'{Colors.ENDC}")
        print(f"{Colors.OKBLUE}➤ Anzahl der Elemente/Zeilen aus Eingabedatei '{input_file_path}': {Colors.BOLD}{initial_input_item_count}{Colors.ENDC}")
        print(f"{Colors.OKBLUE}➤ Verarbeitungsdatum: {Colors.BOLD}{datetime.datetime.now().strftime('%d.%m.%Y %H:%M:%S')}{Colors.ENDC}")
        
        # Zeige verwendete Parameter an mit verbessertem Highlighting
        print(f"\n{Colors.HEADER}{Colors.BOLD}❯❯❯ Verwendete Parameter:{Colors.ENDC}")
        if is_unlimited:
            print(f"{Colors.OKGREEN}  ✓ Token-Limit: {Colors.BOLD}max (unbegrenzter Token Speicher){Colors.ENDC}")
        else:
            print(f"{Colors.OKGREEN}  ✓ Token-Limit: {Colors.BOLD}{token_limit_millions}{Colors.ENDC}{Colors.OKGREEN} Millionen (≈ {Colors.BOLD}{actual_max_tokens:,}{Colors.ENDC}{Colors.OKGREEN} Zeichen){Colors.ENDC}")
        
        if skip_international:
            print(f"{Colors.OKGREEN}  ✓ Internationale Rechtsbezüge überspringen: {Colors.BOLD}Ja{Colors.ENDC}")
        else:
            print(f"{Colors.OKGREEN}  ✓ Internationale Rechtsbezüge überspringen: {Colors.BOLD}Nein{Colors.ENDC}")
        
        if content_only:
            print(f"{Colors.OKGREEN}  ✓ Nur Inhalte ohne Prompts verwenden: {Colors.BOLD}Ja{Colors.ENDC}")
        else:
            print(f"{Colors.OKGREEN}  ✓ Nur Inhalte ohne Prompts verwenden: {Colors.BOLD}Nein{Colors.ENDC}")
            
        if no_role:
            print(f"{Colors.OKGREEN}  ✓ Keine Rollenfelder verwenden: {Colors.BOLD}Ja{Colors.ENDC}")
        else:
            print(f"{Colors.OKGREEN}  ✓ Keine Rollenfelder verwenden: {Colors.BOLD}Nein{Colors.ENDC}")
            
        if all_segments:
            print(f"{Colors.OKGREEN}  ✓ Alle potentiellen Segmente anzeigen: {Colors.BOLD}Ja{Colors.ENDC}")
        else:
            print(f"{Colors.OKGREEN}  ✓ Alle potentiellen Segmente anzeigen: {Colors.BOLD}Nein{Colors.ENDC}")
        
        # Anzeige der UI-Parameter
        if process_one:
            print(f"{Colors.OKGREEN}  ✓ Verarbeite nur ein Gutachten (-o): {Colors.BOLD}Ja{Colors.ENDC}")
        else:
            print(f"{Colors.OKGREEN}  ✓ Verarbeite nur ein Gutachten (-o): {Colors.BOLD}Nein{Colors.ENDC}")
            
        print(f"{Colors.OKGREEN}  ✓ Erweiterte Segmentierung verfügbar: {Colors.BOLD}{'Ja' if ENHANCED_SEGMENTATION_AVAILABLE else 'Nein'}{Colors.ENDC}")

        print(f"\n{Colors.HEADER}{Colors.BOLD}❯❯❯ Übersprungene Einträge:{Colors.ENDC}")
        # This section for skipped_international_rechtsbezug_count is confirmed to be present
        if skipped_international_rechtsbezug_count > 0:
            print(f"{Colors.OKCYAN}  ℹ Gutachten mit 'rechtsbezug: International': {skipped_international_rechtsbezug_count} ({(skipped_international_rechtsbezug_count/initial_input_item_count*100):.1f}%){Colors.ENDC}")
        else:
            print(f"{Colors.OKGREEN}  ✓ Gutachten mit 'rechtsbezug: International': 0{Colors.ENDC}")

        if skipped_due_to_json_decode_error > 0: # This applies to JSONL line errors
            print(f"{Colors.WARNING}  ⚠ Zeilen in JSONL wegen JSON-Decodierungsfehlern übersprungen: {skipped_due_to_json_decode_error} ({(skipped_due_to_json_decode_error/initial_input_item_count*100):.1f}%){Colors.ENDC}")
        else:
            print(f"{Colors.OKGREEN}  ✓ Zeilen in JSONL wegen JSON-Decodierungsfehlern übersprungen: 0{Colors.ENDC}")
        
        # Verbesserte Ausgabe für fehlende Felder mit detaillierteren Informationen
        if skipped_due_to_missing_fields_total > 0:
            print(f"{Colors.WARNING}  ⚠ Elemente wegen fehlender Pflichtfelder übersprungen: {Colors.BOLD}{skipped_due_to_missing_fields_total}{Colors.ENDC}{Colors.WARNING} ({(skipped_due_to_missing_fields_total/initial_input_item_count*100):.1f}%){Colors.ENDC}")
            for field, count in missing_field_counts.items():
                if count > 0:
                    print(f"{Colors.WARNING}    • Fehlendes Feld '{Colors.UNDERLINE}{field}{Colors.ENDC}{Colors.WARNING}': {Colors.BOLD}{count}{Colors.ENDC}{Colors.WARNING} mal{Colors.ENDC}")
        else:
            print(f"{Colors.OKGREEN}  ✓ Elemente wegen fehlender Pflichtfelder übersprungen: {Colors.BOLD}0{Colors.ENDC}{Colors.OKGREEN}{Colors.ENDC}")
        
        # ... (rest of the summary print statements - existing logic) ...
        print(f"\n{Colors.HEADER}{Colors.BOLD}❯❯❯ Verarbeitete & Geschriebene Einträge:{Colors.ENDC}")
        if initial_input_item_count > 0:
            print(f"{Colors.OKGREEN}  ✓ Gutachten, aus denen Segmente erstellt wurden: {Colors.BOLD}{processed_gutachten_count}{Colors.ENDC}{Colors.OKGREEN} ({(processed_gutachten_count/initial_input_item_count*100):.1f}% der Eingabe){Colors.ENDC}")
        else:
            print(f"{Colors.OKGREEN}  ✓ Gutachten, aus denen Segmente erstellt wurden: {Colors.BOLD}{processed_gutachten_count}{Colors.ENDC}")
        
        # Anzeige der Normen-Statistik
        if processed_gutachten_count > 0:
            normen_percentage = (missing_normen_count / processed_gutachten_count) * 100
            print(f"{Colors.WARNING if missing_normen_count > 0 else Colors.OKGREEN}  ✓ Gutachten ohne erkannte Rechtsnormen: {Colors.BOLD}{missing_normen_count}{Colors.ENDC}{Colors.WARNING if missing_normen_count > 0 else Colors.OKGREEN} ({normen_percentage:.1f}% der verarbeiteten Gutachten){Colors.ENDC}")
        
        print(f"{Colors.OKGREEN}  ✓ Insgesamt generierte und geschriebene Trainingssegmente: {Colors.BOLD}{total_segments_generated}{Colors.ENDC}")
        
        if processed_gutachten_count > 0:
            avg_segments = total_segments_generated/processed_gutachten_count
            print(f"{Colors.OKGREEN}  ✓ Durchschnittliche Segmente pro Gutachten: {Colors.BOLD}{avg_segments:.2f}{Colors.ENDC}{Colors.OKGREEN} ({processed_gutachten_count} Gutachten){Colors.ENDC}")
        else:
            print(f"{Colors.WARNING}  ⚠ Keine Gutachten verarbeitet{Colors.ENDC}")
        
        print(f"{Colors.OKGREEN}  ✓ Insgesamt geschriebene Zeichen (Proxy für Tokens): {Colors.BOLD}{current_total_tokens:,}{Colors.ENDC}{Colors.OKGREEN} (Limit: {Colors.BOLD}{actual_max_tokens:,}{Colors.ENDC}{Colors.OKGREEN}){Colors.ENDC}")
        
        # Wenn -a verwendet wird, zeige auch potentielle Gesamt-Tokens/Segmente an
        if all_segments:
            print(f"\n{Colors.HEADER}{Colors.BOLD}❯❯❯ Erweiterte Statistik (--all-segments):{Colors.ENDC}")
            print(f"{Colors.OKCYAN}  ℹ Gesamtzahl potentieller Segmente: {Colors.BOLD}{total_potential_segments:,}{Colors.ENDC}")
            print(f"{Colors.OKCYAN}  ℹ Gesamtzahl potentieller Tokens: {Colors.BOLD}{total_potential_tokens:,}{Colors.ENDC}")
            
            if token_limit_reached_flag:
                not_included_segments = total_potential_segments - total_segments_generated
                not_included_tokens = total_potential_tokens - current_total_tokens
                print(f"{Colors.OKCYAN}  ℹ Nicht berücksichtigte Segmente wegen Token-Limit: {Colors.BOLD}{not_included_segments:,}{Colors.ENDC}")
                print(f"{Colors.OKCYAN}  ℹ Nicht berücksichtigte Tokens wegen Token-Limit: {Colors.BOLD}{not_included_tokens:,}{Colors.ENDC}")
                
                # Berechne Token-Nutzungs-Prozentsatz
                token_usage_percentage = (current_total_tokens/actual_max_tokens*100) if actual_max_tokens > 0 else 0
                print(f"{Colors.OKCYAN}  ℹ Aufgrund von --all-segments wurden Daten vollständig analysiert, aber nur {Colors.BOLD}{token_usage_percentage:.1f}%{Colors.ENDC}{Colors.OKCYAN} des Token-Limits in die Ausgabedatei geschrieben.{Colors.ENDC}")
            
            # Zeige die Verarbeitungszeit an
            end_time = datetime.datetime.now()
            processing_time = end_time - start_time
            print(f"{Colors.OKCYAN}  ℹ Gesamte Verarbeitungszeit: {Colors.BOLD}{processing_time}{Colors.ENDC}")
        
        if actual_max_tokens > 0:
            token_usage = (current_total_tokens/actual_max_tokens*100)
            print(f"{Colors.OKGREEN}  ✓ Auslastung des Token-Limits: {Colors.BOLD}{token_usage:.1f}%{Colors.ENDC}")
        else:
            print(f"{Colors.WARNING}  ⚠ Token-Limit ist 0 oder nicht definiert{Colors.ENDC}")

        if token_limit_reached_flag:
            print(f"\n{Colors.HEADER}{Colors.BOLD}❯❯❯ Token-Limit-Informationen:{Colors.ENDC}")
            if total_segments_generated == 0 and processed_gutachten_count > 0:
                print(f"{Colors.WARNING}  ⚠ Keine Segmente geschrieben. Das erste verarbeitete Gutachten hat möglicherweise das Token-Limit überschritten.{Colors.ENDC}")
            elif total_segments_generated > 0:
                if all_segments:
                    print(f"{Colors.OKCYAN}  ℹ Token-Limit wurde erreicht, aber alle Segmente wurden wegen --all-segments analysiert.{Colors.ENDC}")
                else:
                    print(f"{Colors.OKCYAN}  ℹ Token-Limit wurde erreicht. Ausgabe-Schreiben wurde gestoppt.{Colors.ENDC}")
            
            # Berechne, wie viel Prozent der Elemente nicht verarbeitet wurden
            valid_elements = initial_input_item_count - skipped_international_rechtsbezug_count - skipped_due_to_json_decode_error - skipped_due_to_missing_fields_total
            unprocessed_percentage = (skipped_gutachten_due_to_token_limit / valid_elements) * 100 if valid_elements > 0 else 0
            
            print(f"{Colors.WARNING}  ⚠ Gutachten vollständig übersprungen, nachdem Token-Limit erreicht wurde: {skipped_gutachten_due_to_token_limit} ({unprocessed_percentage:.1f}% der verarbeitbaren Gutachten){Colors.ENDC}")
            if skipped_gutachten_due_to_token_limit > 0:
                print(f"{Colors.WARNING}    • Potenzielle Zeichen aus diesen übersprungenen Gutachten: {skipped_tokens_due_to_token_limit:,}{Colors.ENDC}")
                print(f"{Colors.WARNING}    • Geschätztes zusätzliches Token-Limit benötigt: {(skipped_tokens_due_to_token_limit/1_000_000):.2f} Millionen{Colors.ENDC}")
        
        # Berechne und zeige die Erfolgsrate an
        success_rate = (processed_gutachten_count / initial_input_item_count) * 100 if initial_input_item_count > 0 else 0
        print(f"\n{Colors.HEADER}{Colors.BOLD}❯❯❯ Erfolgsstatistik:{Colors.ENDC}")
        if initial_input_item_count > 0:
            print(f"{Colors.OKGREEN}  ✓ Verarbeitungserfolgsrate: {success_rate:.1f}% ({processed_gutachten_count} von {initial_input_item_count} Gutachten erfolgreich verarbeitet){Colors.ENDC}")
        else:
            print(f"{Colors.WARNING}  ⚠ Keine Eingabe-Elemente gefunden, daher keine Erfolgsstatistik verfügbar.{Colors.ENDC}")
            
        # Segment- und Gutachtenstatistik
        print(f"\n{Colors.HEADER}{Colors.BOLD}❯❯❯ Segment- und Gutachtenstatistik:{Colors.ENDC}")
        print(f"{Colors.OKGREEN}  ✓ Verarbeitete Gutachten: {Colors.BOLD}{processed_gutachten_count}{Colors.ENDC}")
        print(f"{Colors.OKGREEN}  ✓ Erstellte Segmente insgesamt: {Colors.BOLD}{total_segments_generated}{Colors.ENDC}")
        if processed_gutachten_count > 0:
            avg_segments_per_gutachten = total_segments_generated/processed_gutachten_count
            print(f"{Colors.OKGREEN}  ✓ Durchschnittliche Anzahl Segmente pro Gutachten: {Colors.BOLD}{avg_segments_per_gutachten:.1f}{Colors.ENDC}")
        if processed_gutachten_count > 0 and total_potential_segments > 0:
            used_segments_percentage = (total_segments_generated/total_potential_segments*100)
            print(f"{Colors.OKGREEN}  ✓ Prozentsatz der verwendeten Segmente: {Colors.BOLD}{used_segments_percentage:.1f}%{Colors.ENDC} ({total_segments_generated} von {total_potential_segments})")
        
        # Zeige auch die Normen-Statistik an, wenn sie noch nicht angezeigt wurde
        if processed_gutachten_count > 0 and (processed_gutachten_count - missing_normen_count) > 0:
            print(f"{Colors.OKGREEN}  ✓ Gutachten mit erkannten Normen: {Colors.BOLD}{processed_gutachten_count - missing_normen_count}{Colors.ENDC} ({(processed_gutachten_count - missing_normen_count)/processed_gutachten_count*100:.1f}% der verarbeiteten Gutachten)")
            print(f"{Colors.OKGREEN}  ✓ Gutachten ohne erkennbare Normen: {Colors.BOLD}{missing_normen_count}{Colors.ENDC} ({missing_normen_count/processed_gutachten_count*100:.1f}% der verarbeiteten Gutachten)")
        
        if current_total_tokens == 0 and (skipped_international_rechtsbezug_count + skipped_due_to_json_decode_error + skipped_due_to_missing_fields_total) < initial_input_item_count and initial_input_item_count > 0:
             print(f"\n{Colors.WARNING}⚠ Keine Segmente wurden geschrieben. Dies könnte daran liegen, dass alle verarbeitbaren Gutachten nach der Segmentierung leer waren oder das erste gültige Element ein sehr kleines Token-Limit überschritten hat.{Colors.ENDC}")
        elif (skipped_international_rechtsbezug_count + skipped_due_to_json_decode_error + skipped_due_to_missing_fields_total) == initial_input_item_count and initial_input_item_count > 0 and len(items_to_process) == 0 : # Check if all items were skipped before main loop
             print(f"\n{Colors.FAIL}✖ Kein gültiges Gutachten in der Eingabedatei gefunden oder verarbeitet. Alle Elemente wurden basierend auf den Anfangskriterien übersprungen (z.B. International, JSON-Fehler, fehlende Felder).{Colors.ENDC}")
        elif initial_input_item_count == 0 and not (ext.lower() == ".json" and items_to_process == []): # Avoid this if JSON was empty list from start
            print(f"\n{Colors.WARNING}⚠ Eingabedatei '{input_file_path}' war leer oder es wurden keine verarbeitbaren Elemente gefunden.{Colors.ENDC}")
        elif len(items_to_process) > 0 and total_segments_generated == 0 and processed_gutachten_count == 0 and not token_limit_reached_flag:
            # This case handles when items were loaded, but none resulted in segments (e.g. all skipped for other reasons not yet counted, or all text content was empty)
            print(f"\n{Colors.WARNING}⚠ Keine Segmente wurden aus den verarbeiteten Elementen generiert. Prüfen Sie, ob Elemente übersprungen wurden oder ob der Textinhalt leer war.{Colors.ENDC}")
        else:
            if total_segments_generated > 0 or (processed_gutachten_count == 0 and token_limit_reached_flag and total_segments_generated == 0) or initial_input_item_count == 0:
                 print(f"\n{Colors.OKGREEN}✓ Verarbeitung abgeschlossen. Ausgabedatei: '{output_file_path}'{Colors.ENDC}") # Enhanced completion message
            else:
                 print(f"\n{Colors.WARNING}⚠ Verarbeitung abgeschlossen, aber keine Segmente wurden geschrieben. Überprüfen Sie die übersprungenen Anzahlen und Eingabedaten.{Colors.ENDC}")

    except Exception as e: # General catch-all for unexpected errors during processing stages
        print(f"\n{Colors.FAIL}✖ Ein unerwarteter Fehler ist während der Verarbeitung aufgetreten: {e}{Colors.ENDC}")
        import traceback
        print(f"{Colors.FAIL}{traceback.format_exc()}{Colors.ENDC}")
        print(f"\n{Colors.WARNING}⚠ Bitte melden Sie diesen Fehler mit der Beispieldatei, die das Problem verursacht hat.{Colors.ENDC}")

if __name__ == "__main__":
    # Check for help flag first before using argparse
    if "--help" in sys.argv or "-h" in sys.argv:
        print(f"\n{Colors.BOLD}{Colors.HEADER}╔══════════════════════════════════════════════════════════╗{Colors.ENDC}")
        print(f"{Colors.BOLD}{Colors.HEADER}║  GUTACHTEN SEGMENTIERUNG UND TRAINING DATEN VORBEREITUNG  ║{Colors.ENDC}")
        print(f"{Colors.BOLD}{Colors.HEADER}╚══════════════════════════════════════════════════════════╝{Colors.ENDC}\n")
        
        print(f"{Colors.BOLD}{Colors.OKBLUE}📝 Beschreibung:{Colors.ENDC}")
        print(f"  {Colors.OKCYAN}•{Colors.ENDC} Dieses Skript segmentiert juristische Gutachten aus einer JSON/JSONL-Datei")
        print(f"    und bereitet diese für das Training eines Sprachmodells vor.")
        print(f"  {Colors.OKCYAN}•{Colors.ENDC} Es nutzt die Zeichenanzahl der JSON-Ausgabezeilen als Näherung für Token-Anzahl.")
        print(f"  {Colors.OKCYAN}•{Colors.ENDC} Der Fokus liegt auf der Erstellung sinnvoller Trainingssegmente mit")
        print(f"    besonderem Schwerpunkt auf die rechtlichen Normen ({Colors.OKGREEN}normen-Feld{Colors.ENDC}).\n")
        
        print(f"{Colors.BOLD}{Colors.OKBLUE}⌨️ Verwendung:{Colors.ENDC}")
        print(f"  python segment_and_prepare_training_data.py {Colors.HEADER}[input_file_path]{Colors.ENDC} [{Colors.OKGREEN}-t TOKENS{Colors.ENDC}] [{Colors.OKGREEN}-in{Colors.ENDC}]\n")
        
        print(f"{Colors.BOLD}{Colors.OKBLUE}📄 Argumente:{Colors.ENDC}")
        print(f"  {Colors.HEADER}input_file_path{Colors.ENDC}")
        print(f"    Pfad zur Eingabe-JSON/JSONL-Datei mit den Gutachtendaten.\n")
        
        print(f"{Colors.BOLD}{Colors.OKBLUE}⚙️ Optionen:{Colors.ENDC}")
        print(f"  {Colors.OKGREEN}-h, --help{Colors.ENDC}")
        print(f"    Zeige diese Hilfemeldung an und beende das Programm.\n")
        
        print(f"  {Colors.OKGREEN}-t TOKENS, --tokens TOKENS{Colors.ENDC}")
        print(f"    Maximale Anzahl an 'Tokens' (Näherung durch Zeichenanzahl) für die Ausgabedatei,")
        print(f"    angegeben in Millionen (z.B. {Colors.OKCYAN}2.0{Colors.ENDC} für 2 Millionen, {Colors.OKCYAN}0.2{Colors.ENDC} für 200k).")
        print(f"    Standard ist {Colors.OKCYAN}2.0{Colors.ENDC} (2 Millionen).\n")
        
        print(f"  {Colors.OKGREEN}-in, --skip-international{Colors.ENDC}")
        print(f"    Überspringe Einträge mit 'rechtsbezug' gleich 'International'.\n")
        
        print(f"  {Colors.OKGREEN}-c, --content-only{Colors.ENDC}")
        print(f"    Erstellt Trainingsdaten ohne Prompt, nur mit den reinen Dokumentinhalten.")
        print(f"    Verwendet nur die 'assistant'-Nachricht ohne 'system'- oder 'user'-Prompts.\n")
        
        print(f"  {Colors.OKGREEN}-r, --no-role{Colors.ENDC}")
        print(f"    Lässt die Rollenfelder ('role'-Attribut) der Nachrichten leer.\n")
        
        print(f"  {Colors.OKGREEN}-a, --all-segments{Colors.ENDC}")
        print(f"    Zeigt alle potentiellen validen Segmente aus sämtlichen Datensätzen an,")
        print(f"    inklusive derer, die nicht in die Ausgabedatei geschrieben werden.\n")
        
        print(f"  {Colors.OKGREEN}-o, --one{Colors.ENDC}")
        print(f"    Verarbeitet nur ein einzelnes Gutachten und beendet dann das Programm.")
        print(f"    Nützlich für Tests und schnelle Validierung der Verarbeitung.\n")
        
        print(f"{Colors.BOLD}{Colors.OKBLUE}📋 Beispiele:{Colors.ENDC}")
        print(f"  {Colors.OKCYAN}»{Colors.ENDC} python segment_and_prepare_training_data.py {Colors.HEADER}gutachten.json{Colors.ENDC}")
        print(f"    Verarbeitet die JSON-Datei mit einem Standardlimit von 2 Millionen Tokens.\n")
        
        print(f"  {Colors.OKCYAN}»{Colors.ENDC} python segment_and_prepare_training_data.py {Colors.HEADER}gutachten.jsonl{Colors.ENDC} {Colors.OKGREEN}-t{Colors.ENDC} {Colors.OKCYAN}0.5{Colors.ENDC}")
        print(f"    Verarbeitet die JSONL-Datei mit einem Limit von 500.000 Tokens.\n")
        
        print(f"  {Colors.OKCYAN}»{Colors.ENDC} python segment_and_prepare_training_data.py {Colors.HEADER}gutachten.json{Colors.ENDC} {Colors.OKGREEN}-in{Colors.ENDC}")
        print(f"    Verarbeitet die JSON-Datei und überspringt alle Einträge mit dem Rechtsbezug 'International'.\n")
        
        print(f"  {Colors.OKCYAN}»{Colors.ENDC} python segment_and_prepare_training_data.py {Colors.HEADER}gutachten.json{Colors.ENDC} {Colors.OKGREEN}-c{Colors.ENDC}")
        print(f"    Erstellt Trainingsdaten mit nur dem Dokumentinhalt, ohne Prompts.\n")
        
        print(f"  {Colors.OKCYAN}»{Colors.ENDC} python segment_and_prepare_training_data.py {Colors.HEADER}gutachten.json{Colors.ENDC} {Colors.OKGREEN}-r{Colors.ENDC}")
        print(f"    Erstellt Trainingsdaten ohne Rollenfelder in den Nachrichten.\n")
        
        print(f"  {Colors.OKCYAN}»{Colors.ENDC} python segment_and_prepare_training_data.py {Colors.HEADER}gutachten.json{Colors.ENDC} {Colors.OKGREEN}-c -r -t{Colors.ENDC} {Colors.OKCYAN}1.0{Colors.ENDC}")
        print(f"    Erstellt Trainingsdaten ohne Prompts und Rollen mit einem Limit von 1 Million Tokens.\n")
        
        print(f"  {Colors.OKCYAN}»{Colors.ENDC} python segment_and_prepare_training_data.py {Colors.HEADER}gutachten.json{Colors.ENDC} {Colors.OKGREEN}-a{Colors.ENDC}")
        print(f"    Zeigt alle potentiellen Segmente an, auch wenn sie nicht in die Ausgabedatei geschrieben werden.\n")
        
        print(f"  {Colors.OKCYAN}»{Colors.ENDC} python segment_and_prepare_training_data.py {Colors.HEADER}gutachten.json{Colors.ENDC} {Colors.OKGREEN}-o{Colors.ENDC}")
        print(f"    Verarbeitet nur ein einzelnes Gutachten und beendet dann das Programm.\n")
        sys.exit(0)
    
    # Regular argparse setup for normal command-line parsing
    parser = argparse.ArgumentParser(
        description=f"Segmentiert juristische Gutachten aus einer JSON/JSONL-Datei und bereitet sie für das Training eines Sprachmodells vor."
    )
    
    parser.add_argument(
        "input_file_path",
        type=str,
        help="Pfad zur Eingabe-JSON/JSONL-Datei mit den Gutachtendaten."
    )
    
    parser.add_argument(
        "-t", "--tokens",
        type=str,
        default="2.0",
        help="Maximale Anzahl an Tokens (in Millionen) für die Ausgabe. Standard: 2.0 (2 Millionen). Verwende 'max' für kein Limit."
    )
    
    parser.add_argument(
        "-in", "--skip-international",
        action="store_true",
        help="Überspringe Einträge mit 'rechtsbezug' gleich 'International'."
    )
    
    parser.add_argument(
        "-c", "--content-only",
        action="store_true",
        help="Erstelle nur die Message-Inhalte ohne Prompt, nur die Gutachtentexte werden als Trainingsdaten verwendet."
    )
    
    parser.add_argument(
        "-r", "--no-role",
        action="store_true",
        help="Fülle die Rolle nicht aus, lasse das Role-Feld leer."
    )
    
    parser.add_argument(
        "-a", "--all-segments",
        action="store_true",
        help="Zeige alle potentiellen validen Segmente aus sämtlichen Datensätzen an, auch wenn sie nicht in die Ausgabedatei geschrieben werden."
    )
    
    parser.add_argument(
        "-o", "--one",
        action="store_true",
        help="Verarbeite nur ein einzelnes Gutachten und beende dann das Programm. Nützlich für Tests."
    )

    args = parser.parse_args()
    
    # Process token limit - handle "max" as a special case
    token_limit = args.tokens
    if token_limit.lower() == "max":
        token_limit = float('inf')  # Infinity for no limit
    else:
        try:
            token_limit = float(token_limit)
        except ValueError:
            print(f"{Colors.FAIL}✖ Fehler: Token-Limit '{token_limit}' ist keine gültige Zahl oder 'max'.{Colors.ENDC}")
            sys.exit(1)
    
    # Package the token limit and other flags together
    token_limit_millions_info = {
        'limit': token_limit,
        'skip_international': args.skip_international,
        'content_only': args.content_only,
        'no_role': args.no_role,
        'all_segments': args.all_segments,
        'process_one': args.one  # Nutze den neuen dedicated Parameter
    }
    
    prepare_data_for_training(args.input_file_path, token_limit_millions_info)
