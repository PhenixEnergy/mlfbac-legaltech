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

def _generate_user_prompt(heading, gutachten_nummer, erscheinungsdatum, segments_count_for_current_gutachten, normen_list=None, segment_context=None):
    """
    Generiert den Benutzer-Prompt basierend auf Überschrift und anderen Metadaten, mit hochdifferenzierter 
    juristischer Analyse und umfassender Kontextberücksichtigung.
    
    Args:
        heading: Die Abschnittsüberschrift aus dem segmentierten Text
        gutachten_nummer: Die Gutachtennummer
        erscheinungsdatum: Das Erscheinungsdatum
        segments_count_for_current_gutachten: Anzahl der Segmente in diesem Gutachten
        normen_list: Liste der im Gutachten referenzierten Rechtsnormen
        segment_context: Zusätzlicher Kontext über den Segmenttyp und Inhalt
        
    Returns:
        Ein hochspezifischer Prompt, der die juristische Struktur und Rechtsnormen berücksichtigt
    """
    import random
    
    cleaned_heading_lower = heading.lower()
    prompt = ""
    
    # Formatierung der Rechtsnormen für bessere Lesbarkeit
    normen_str = ""
    if normen_list and len(normen_list) > 0:
        normen_str = ", ".join(normen_list)
        normen_str = f" unter besonderer Berücksichtigung von {normen_str}"

    # HOCHSPEZIFISCHE PROMPT-GENERIERUNG basierend auf 60 Jahren juristischer Praxis
    
    # === SACHVERHALTS-PROMPTS (12 Varianten) ===
    if any(keyword in cleaned_heading_lower for keyword in ["sachverhalt", "tatbestand", "lebenssachverhalt", "ausgangslage"]):
        sachverhalt_prompts = [
            f"Gib den maßgeblichen Sachverhalt für Gutachten Nr. {gutachten_nummer} vom {erscheinungsdatum} wieder{normen_str}. Beschreibe den relevanten Sachverhalt präzise und umfassend. Arbeite die rechtlich relevanten Fakten klar heraus und strukturiere sie chronologisch und nach sachlichen Zusammenhängen.",
            f"Stelle den entscheidungserheblichen Sachverhalt des Gutachtens Nr. {gutachten_nummer} vom {erscheinungsdatum} systematisch dar{normen_str}. Gliedere nach unstrittigem und streitigem Sachverhalt und hebe die für die rechtliche Beurteilung wesentlichen Tatsachen hervor.",
            f"Schildere den relevanten Lebenssachverhalt zum Gutachten Nr. {gutachten_nummer} vom {erscheinungsdatum}{normen_str}. Fokussiere auf die rechtlich bedeutsamen Umstände und deren zeitliche Abfolge. Arbeite die Interessenlagen der Beteiligten klar heraus.",
            f"Gib die Tatsachengrundlage für das Gutachten Nr. {gutachten_nummer} vom {erscheinungsdatum} wieder{normen_str}. Stelle unstreitige und streitige Tatsachen gegenüber und bewerte deren Relevanz für die rechtliche Analyse.",
            f"Beschreibe den Ausgangssachverhalt des Gutachtens Nr. {gutachten_nummer} vom {erscheinungsdatum}{normen_str}. Strukturiere die Darstellung nach Parteien, Zeitabläufen und rechtlich relevanten Handlungen.",
            f"Erläutere die dem Gutachten Nr. {gutachten_nummer} vom {erscheinungsdatum} zugrunde liegenden Tatsachen{normen_str}. Arbeite die rechtlich erheblichen Umstände heraus und ordne sie den entsprechenden Tatbestandsmerkmalen zu.",
            f"Stelle den Tatbestand zum Gutachten Nr. {gutachten_nummer} vom {erscheinungsdatum} umfassend dar{normen_str}. Gliedere nach Parteien, Vertragsbeziehungen und streitgegenständlichen Handlungen.",
            f"Gib die Fallkonstellation des Gutachtens Nr. {gutachten_nummer} vom {erscheinungsdatum} strukturiert wieder{normen_str}. Berücksichtige alle rechtlich relevanten Aspekte des Sachverhalts und deren Beweiswürdigung.",
            f"Beschreibe die tatsächlichen Gegebenheiten zum Gutachten Nr. {gutachten_nummer} vom {erscheinungsdatum}{normen_str}. Differenziere zwischen Haupt- und Hilfssachverhalt und arbeite die rechtlichen Anknüpfungspunkte heraus.",
            f"Erläutere den komplexen Sachverhalt des Gutachtens Nr. {gutachten_nummer} vom {erscheinungsdatum}{normen_str}. Gliedere systematisch nach Sachverhaltsebenen und rechtlich relevanten Zeitpunkten.",
            f"Stelle die Faktenlage zum Gutachten Nr. {gutachten_nummer} vom {erscheinungsdatum} präzise dar{normen_str}. Fokussiere auf die für die Subsumtion erforderlichen Tatsachen und deren Bewertung.",
            f"Gib den Prozesssachverhalt des Gutachtens Nr. {gutachten_nummer} vom {erscheinungsdatum} wieder{normen_str}. Berücksichtige sowohl den materiellen Sachverhalt als auch die verfahrensrechtlichen Aspekte."
        ]
        prompt = random.choice(sachverhalt_prompts)
    
    # === RECHTSFRAGEN-PROMPTS (15 Varianten) ===
    elif any(keyword in cleaned_heading_lower for keyword in ["frage", "rechtsfrage", "fragestellung", "problematik", "problem"]):
        rechtsfrage_prompts = [
            f"Welche rechtlichen Fragen behandelt Gutachten Nr. {gutachten_nummer} vom {erscheinungsdatum}{normen_str}? Formuliere die Rechtsfragen präzise und systematisch. Skizziere dabei die zentralen juristischen Probleme und ordne sie den relevanten Rechtsbereichen zu.",
            f"Formuliere die zentrale Rechtsfrage des Gutachtens Nr. {gutachten_nummer} vom {erscheinungsdatum}{normen_str}. Arbeite den rechtlichen Kern des Problems heraus und stelle dar, welche Normen zur Beantwortung herangezogen werden müssen.",
            f"Identifiziere die Hauptrechtsfrage und Nebenrechtsfragen des Gutachtens Nr. {gutachten_nummer} vom {erscheinungsdatum}{normen_str}. Strukturiere die Fragestellung nach Haupt- und Hilfsgutachten und arbeite Prüfungsreihenfolgen heraus.",
            f"Analysiere die komplexe Rechtsproblematik des Gutachtens Nr. {gutachten_nummer} vom {erscheinungsdatum}{normen_str}. Gliedere nach materiell-rechtlichen und prozessualen Fragestellungen und deren Interdependenzen.",
            f"Stelle die gutachterliche Fragestellung zum Gutachten Nr. {gutachten_nummer} vom {erscheinungsdatum} systematisch dar{normen_str}. Berücksichtige sowohl die unmittelbare als auch die mittelbare Rechtsproblematik.",
            f"Erläutere die rechtsdogmatischen Fragen des Gutachtens Nr. {gutachten_nummer} vom {erscheinungsdatum}{normen_str}. Arbeite die methodischen Herausforderungen und Auslegungsprobleme heraus.",
            f"Definiere die Streitpunkte und Rechtsfragen des Gutachtens Nr. {gutachten_nummer} vom {erscheinungsdatum}{normen_str}. Differenziere zwischen unstrittigem und streitigem sowie zwischen Rechts- und Tatfragen.",
            f"Beschreibe die juristischen Kernprobleme des Gutachtens Nr. {gutachten_nummer} vom {erscheinungsdatum}{normen_str}. Fokussiere auf die dogmatisch umstrittenen Punkte und deren praktische Relevanz.",
            f"Formuliere die Beratungsanfrage zum Gutachten Nr. {gutachten_nummer} vom {erscheinungsdatum} präzise{normen_str}. Arbeite die rechtspolitischen und rechtspraktischen Implikationen heraus.",
            f"Analysiere die Rechtsunsicherheiten des Gutachtens Nr. {gutachten_nummer} vom {erscheinungsdatum}{normen_str}. Identifiziere Auslegungsbedürftigkeiten und Ermessensspielräume.",
            f"Stelle die Beweisrechtsfragen des Gutachtens Nr. {gutachten_nummer} vom {erscheinungsdatum} dar{normen_str}. Berücksichtige Beweis- und Darlegungslasten sowie Vermutungsregeln.",
            f"Erläutere die Abgrenzungsprobleme des Gutachtens Nr. {gutachten_nummer} vom {erscheinungsdatum}{normen_str}. Arbeite die Konkurrenz- und Kollisionsfragen verschiedener Rechtsinstitute heraus.",
            f"Beschreibe die Qualifikationsfragen des Gutachtens Nr. {gutachten_nummer} vom {erscheinungsdatum}{normen_str}. Fokussiere auf die rechtliche Einordnung des Sachverhalts und deren Konsequenzen.",
            f"Analysiere die Zuordnungs- und Zurechnungsfragen des Gutachtens Nr. {gutachten_nummer} vom {erscheinungsdatum}{normen_str}. Berücksichtige objektive und subjektive Zurechnungskriterien.",
            f"Formuliere die Verfassungsrechtsfragen des Gutachtens Nr. {gutachten_nummer} vom {erscheinungsdatum}{normen_str}. Arbeite verfassungskonforme Auslegung und Grundrechtsbezug heraus."
        ]
        prompt = random.choice(rechtsfrage_prompts)
    
    # === ERGEBNIS/FAZIT-PROMPTS (12 Varianten) ===
    elif any(keyword in cleaned_heading_lower for keyword in ["ergebnis", "zusammenfassung", "fazit", "schlussfolgerung", "tenor", "gesamtergebnis"]):
        ergebnis_prompts = [
            f"Was ist das Ergebnis des Gutachtens Nr. {gutachten_nummer} vom {erscheinungsdatum}{normen_str}? Fasse die wesentlichen rechtlichen Schlussfolgerungen und deren Begründung zusammen. Zeige klar die Subsumtionskette auf.",
            f"Formuliere das Gesamtergebnis des Gutachtens Nr. {gutachten_nummer} vom {erscheinungsdatum}{normen_str}. Strukturiere nach Haupt- und Nebenergebnissen und arbeite praktische Konsequenzen heraus.",
            f"Stelle die Schlussfolgerungen des Gutachtens Nr. {gutachten_nummer} vom {erscheinungsdatum} systematisch dar{normen_str}. Berücksichtige sowohl die rechtliche Bewertung als auch die Handlungsempfehlungen.",
            f"Gib das Fazit zum Gutachten Nr. {gutachten_nummer} vom {erscheinungsdatum} strukturiert wieder{normen_str}. Verbinde die rechtlichen Grundlagen mit dem konkreten Sachverhalt und den daraus resultierenden Rechtsfolgen.",
            f"Beschreibe das Resultat der rechtlichen Prüfung zum Gutachten Nr. {gutachten_nummer} vom {erscheinungsdatum}{normen_str}. Arbeite die Begründungskette und die praktischen Auswirkungen klar heraus.",
            f"Erläutere die Gesamtbeurteilung des Gutachtens Nr. {gutachten_nummer} vom {erscheinungsdatum}{normen_str}. Fokussiere auf die Lösung der Rechtsprobleme und deren dogmatische Einordnung.",
            f"Formuliere den Tenor des Gutachtens Nr. {gutachten_nummer} vom {erscheinungsdatum}{normen_str}. Stelle die rechtlichen Konsequenzen prägnant dar und arbeite Alternativlösungen heraus.",
            f"Beschreibe die Synthese der rechtlichen Analyse zum Gutachten Nr. {gutachten_nummer} vom {erscheinungsdatum}{normen_str}. Verbinde Einzelergebnisse zu einem schlüssigen Gesamtbild.",
            f"Stelle das Endergebnis des Gutachtens Nr. {gutachten_nummer} vom {erscheinungsdatum} begründet dar{normen_str}. Berücksichtige alle Prüfungsebenen und deren Wechselwirkungen.",
            f"Gib die abschließende Bewertung zum Gutachten Nr. {gutachten_nummer} vom {erscheinungsdatum} wieder{normen_str}. Arbeite Stärken und Schwächen der verschiedenen Lösungsansätze heraus.",
            f"Erläutere das Zwischenergebnis und Gesamtergebnis des Gutachtens Nr. {gutachten_nummer} vom {erscheinungsdatum}{normen_str}. Strukturiere nach Prüfungsebenen und logischer Argumentationsfolge.",
            f"Beschreibe die rechtspraktischen Konsequenzen des Gutachtens Nr. {gutachten_nummer} vom {erscheinungsdatum}{normen_str}. Fokussiere auf Umsetzbarkeit und prozessuale Verwertbarkeit der Ergebnisse."
        ]
        prompt = random.choice(ergebnis_prompts)
    
    # === SUBSUMTIONS-PROMPTS (10 Varianten) ===
    elif any(keyword in cleaned_heading_lower for keyword in ["subsumtion", "anwendung", "tatbestandsmerkmal", "prüfung", "voraussetzung"]):
        subsumtion_prompts = [
            f"Führe eine systematische Subsumtion für das Gutachten Nr. {gutachten_nummer} vom {erscheinungsdatum}{normen_str} durch. Wende die relevanten Rechtsnormen Schritt für Schritt auf den Sachverhalt an.",
            f"Prüfe die Tatbestandsmerkmale zum Gutachten Nr. {gutachten_nummer} vom {erscheinungsdatum} detailliert{normen_str}. Subsumiere jeden Tatbestand systematisch unter die einschlägigen Normen.",
            f"Vollziehe die Rechtsanwendung für das Gutachten Nr. {gutachten_nummer} vom {erscheinungsdatum} nach{normen_str}. Arbeite die Subsumtion unter die Tatbestandsmerkmale methodisch auf.",
            f"Analysiere die Normerfüllung im Gutachten Nr. {gutachten_nummer} vom {erscheinungsdatum}{normen_str}. Prüfe systematisch, ob die Voraussetzungen der einschlägigen Rechtsnormen gegeben sind.",
            f"Erläutere die Tatbestandssubsumtion zum Gutachten Nr. {gutachten_nummer} vom {erscheinungsdatum}{normen_str}. Arbeite die Erfüllung der objektiven und subjektiven Tatbestandsmerkmale heraus.",
            f"Beschreibe die Rechtsfolgenbestimmung des Gutachtens Nr. {gutachten_nummer} vom {erscheinungsdatum}{normen_str}. Subsumiere unter die Rechtsfolgenanordnung und arbeite Ermessensspielräume heraus.",
            f"Führe die konkrete Normanwendung für das Gutachten Nr. {gutachten_nummer} vom {erscheinungsdatum} durch{normen_str}. Berücksichtige Ausnahmen, Einschränkungen und konkurrierende Normen.",
            f"Prüfe die Rechtmäßigkeitsvoraussetzungen des Gutachtens Nr. {gutachten_nummer} vom {erscheinungsdatum}{normen_str}. Subsumiere systematisch unter die materiellen und formellen Rechtmäßigkeitsanforderungen.",
            f"Analysiere die Anspruchserfüllung im Gutachten Nr. {gutachten_nummer} vom {erscheinungsdatum}{normen_str}. Prüfe die Anspruchsvoraussetzungen und deren konkrete Erfüllung im Sachverhalt.",
            f"Erläutere die Rechtsnormkonkretisierung zum Gutachten Nr. {gutachten_nummer} vom {erscheinungsdatum}{normen_str}. Wende abstrakte Rechtsnormen auf den konkreten Lebenssachverhalt an."
        ]
        prompt = random.choice(subsumtion_prompts)
    
    # === AUSLEGUNGS-PROMPTS (8 Varianten) ===
    elif any(keyword in cleaned_heading_lower for keyword in ["auslegung", "interpretation", "wortlaut", "systematik", "teleologie", "genese"]):
        auslegung_prompts = [
            f"Erläutere die Normauslegung zum Gutachten Nr. {gutachten_nummer} vom {erscheinungsdatum}{normen_str}. Wende die vier klassischen Auslegungsmethoden systematisch an.",
            f"Beschreibe die Wortlausauslegung des Gutachtens Nr. {gutachten_nummer} vom {erscheinungsdatum}{normen_str}. Analysiere den möglichen Wortsinn und sprachliche Bedeutungsvarianten.",
            f"Führe eine systematische Auslegung für das Gutachten Nr. {gutachten_nummer} vom {erscheinungsdatum} durch{normen_str}. Berücksichtige den Normkontext und die Gesetzessystematik.",
            f"Analysiere die teleologische Auslegung zum Gutachten Nr. {gutachten_nummer} vom {erscheinungsdatum}{normen_str}. Arbeite Normzweck und Gesetzesziel heraus.",
            f"Erläutere die historische Auslegung des Gutachtens Nr. {gutachten_nummer} vom {erscheinungsdatum}{normen_str}. Berücksichtige Entstehungsgeschichte und Gesetzgeberwillen.",
            f"Beschreibe die verfassungskonforme Auslegung zum Gutachten Nr. {gutachten_nummer} vom {erscheinungsdatum}{normen_str}. Arbeite verfassungsrechtliche Vorgaben und Grundrechtsbezug heraus.",
            f"Führe eine richtlinienkonforme Auslegung für das Gutachten Nr. {gutachten_nummer} vom {erscheinungsdatum} durch{normen_str}. Berücksichtige europarechtliche Vorgaben und deren nationale Umsetzung.",
            f"Analysiere die evolutive Auslegung zum Gutachten Nr. {gutachten_nummer} vom {erscheinungsdatum}{normen_str}. Arbeite zeitbedingte Bedeutungswandel und Rechtsentwicklung heraus."
        ]
        prompt = random.choice(auslegung_prompts)
    
    # === ANSPRUCHSGRUNDLAGEN-PROMPTS (8 Varianten) ===
    elif any(keyword in cleaned_heading_lower for keyword in ["anspruchsgrundlage", "anspruch", "rechtsnorm", "rechtsgrundlage"]):
        anspruch_prompts = [
            f"Identifiziere die Anspruchsgrundlagen im Gutachten Nr. {gutachten_nummer} vom {erscheinungsdatum}{normen_str}. Begründe die Einschlägigkeit und arbeite Anspruchskonkurrenzen heraus.",
            f"Erläutere die Rechtsgrundlagen des Gutachtens Nr. {gutachten_nummer} vom {erscheinungsdatum}{normen_str}. Analysiere Primary- und Sekundäransprüche sowie deren Verhältnis zueinander.",
            f"Beschreibe die Normgrundlage für das Gutachten Nr. {gutachten_nummer} vom {erscheinungsdatum}{normen_str}. Arbeite die einschlägigen Rechtsnormen und deren Anwendungsbereich heraus.",
            f"Analysiere die Tatbestandsvoraussetzungen der Anspruchsgrundlage zum Gutachten Nr. {gutachten_nummer} vom {erscheinungsdatum}{normen_str}. Strukturiere nach objektiven und subjektiven Elementen.",
            f"Erläutere die Rechtsfolgenanordnung im Gutachten Nr. {gutachten_nummer} vom {erscheinungsdatum}{normen_str}. Arbeite primäre und sekundäre Rechtsfolgen systematisch heraus.",
            f"Beschreibe die Anspruchsbegründung zum Gutachten Nr. {gutachten_nummer} vom {erscheinungsdatum}{normen_str}. Fokussiere auf Entstehung, Inhalt und Umfang des Anspruchs.",
            f"Analysiere die Anspruchshemmung und -durchsetzung im Gutachten Nr. {gutachten_nummer} vom {erscheinungsdatum}{normen_str}. Berücksichtige Einreden und Durchsetzungshindernisse.",
            f"Erläutere die Anspruchsmodifikation des Gutachtens Nr. {gutachten_nummer} vom {erscheinungsdatum}{normen_str}. Arbeite Änderungen, Übertragungen und Erlöschen heraus."
        ]
        prompt = random.choice(anspruch_prompts)
    
    # === PROZESSRECHTLICHE PROMPTS (10 Varianten) ===
    elif any(keyword in cleaned_heading_lower for keyword in ["zulässigkeit", "begründetheit", "verfahren", "prozess", "klage", "antrag"]):
        prozess_prompts = [
            f"Prüfe die Zulässigkeit im Gutachten Nr. {gutachten_nummer} vom {erscheinungsdatum}{normen_str}. Gehe systematisch alle prozessualen Voraussetzungen durch.",
            f"Analysiere die Begründetheit des Gutachtens Nr. {gutachten_nummer} vom {erscheinungsdatum}{normen_str}. Prüfe die materiell-rechtlichen Anspruchsvoraussetzungen.",
            f"Erläutere die Verfahrensvoraussetzungen zum Gutachten Nr. {gutachten_nummer} vom {erscheinungsdatum}{normen_str}. Berücksichtige formelle und materielle Prozessvoraussetzungen.",
            f"Beschreibe die Zuständigkeitsregeln im Gutachten Nr. {gutachten_nummer} vom {erscheinungsdatum}{normen_str}. Arbeite sachliche, örtliche und funktionale Zuständigkeit heraus.",
            f"Analysiere die Prozessfähigkeit und Postulationsfähigkeit zum Gutachten Nr. {gutachten_nummer} vom {erscheinungsdatum}{normen_str}. Prüfe subjektive Verfahrensvoraussetzungen.",
            f"Erläutere die Klagebefugnis und das Rechtsschutzbedürfnis im Gutachten Nr. {gutachten_nummer} vom {erscheinungsdatum}{normen_str}. Arbeite die besonderen Sachurteilsvoraussetzungen heraus.",
            f"Beschreibe die Fristeinhaltung und Formvorschriften des Gutachtens Nr. {gutachten_nummer} vom {erscheinungsdatum}{normen_str}. Berücksichtige prozessuale Heilungsmöglichkeiten.",
            f"Analysiere die Rechtskraft und Bindungswirkung im Gutachten Nr. {gutachten_nummer} vom {erscheinungsdatum}{normen_str}. Arbeite objektive und subjektive Grenzen heraus.",
            f"Erläutere die Beweislast und Beweisführung zum Gutachten Nr. {gutachten_nummer} vom {erscheinungsdatum}{normen_str}. Berücksichtige Darlegungs- und Beweislastverteilung.",
            f"Beschreibe die Rechtsmittel und deren Zulässigkeit im Gutachten Nr. {gutachten_nummer} vom {erscheinungsdatum}{normen_str}. Arbeite Anfechtungsvoraussetzungen heraus."
        ]
        prompt = random.choice(prozess_prompts)
    
    # === SPEZIALISIERTE RECHTSGEBIETS-PROMPTS ===
    elif any(keyword in cleaned_heading_lower for keyword in ["erbrecht", "erbschaft", "testament", "pflichtteil", "erbe"]):
        erbrecht_prompts = [
            f"Analysiere die erbrechtlichen Aspekte des Gutachtens Nr. {gutachten_nummer} vom {erscheinungsdatum}{normen_str}. Berücksichtige gesetzliche und gewillkürte Erbfolge.",
            f"Erläutere die Pflichtteilsansprüche im Gutachten Nr. {gutachten_nummer} vom {erscheinungsdatum}{normen_str}. Arbeite Pflichtteilsberechnung und -ansprüche heraus.",
            f"Beschreibe die Testamentsauslegung zum Gutachten Nr. {gutachten_nummer} vom {erscheinungsdatum}{normen_str}. Wende die erbrechtlichen Auslegungsregeln systematisch an."
        ]
        prompt = random.choice(erbrecht_prompts)
    
    elif any(keyword in cleaned_heading_lower for keyword in ["vertrag", "schuldverhältnis", "leistung", "schadensersatz"]):
        schuldrecht_prompts = [
            f"Analysiere das Schuldverhältnis im Gutachten Nr. {gutachten_nummer} vom {erscheinungsdatum}{normen_str}. Berücksichtige Entstehung, Inhalt und Erlöschen.",
            f"Erläutere die Leistungsstörungen zum Gutachten Nr. {gutachten_nummer} vom {erscheinungsdatum}{normen_str}. Arbeite Unmöglichkeit, Verzug und Schlechtleistung heraus.",
            f"Beschreibe die Schadensersatzansprüche im Gutachten Nr. {gutachten_nummer} vom {erscheinungsdatum}{normen_str}. Berücksichtige Voraussetzungen und Schadensberechnung."
        ]
        prompt = random.choice(schuldrecht_prompts)
    
    # === METHODENLEHRE UND DOGMATIK-PROMPTS (8 Varianten) ===
    elif any(keyword in cleaned_heading_lower for keyword in ["methodenlehre", "dogmatik", "rechtsprechung", "literatur", "meinung"]):
        methodik_prompts = [
            f"Erläutere die methodischen Grundlagen des Gutachtens Nr. {gutachten_nummer} vom {erscheinungsdatum}{normen_str}. Arbeite die verwendeten Auslegungsmethoden heraus.",
            f"Beschreibe die Dogmatik des Gutachtens Nr. {gutachten_nummer} vom {erscheinungsdatum}{normen_str}. Berücksichtige herrschende Meinung und Mindermeinungen.",
            f"Analysiere die Rechtsprechungslinien zum Gutachten Nr. {gutachten_nummer} vom {erscheinungsdatum}{normen_str}. Arbeite Entwicklungen und Rechtsprechungswandel heraus.",
            f"Erläutere den Meinungsstand in Rechtsprechung und Literatur zum Gutachten Nr. {gutachten_nummer} vom {erscheinungsdatum}{normen_str}. Berücksichtige kontroverse Diskussionen.",
            f"Beschreibe die Rechtsentwicklung im Gutachten Nr. {gutachten_nummer} vom {erscheinungsdatum}{normen_str}. Arbeite historische Entwicklung und aktuelle Tendenzen heraus.",
            f"Analysiere die Systemgerechtigkeit der Lösung zum Gutachten Nr. {gutachten_nummer} vom {erscheinungsdatum}{normen_str}. Berücksichtige systematische Einordnung und Kohärenz.",
            f"Erläutere die Rechtsvergleichung zum Gutachten Nr. {gutachten_nummer} vom {erscheinungsdatum}{normen_str}. Arbeite verschiedene Rechtssysteme und deren Lösungsansätze heraus.",
            f"Beschreibe die Rechtspolitik des Gutachtens Nr. {gutachten_nummer} vom {erscheinungsdatum}{normen_str}. Berücksichtige de lege lata und de lege ferenda Betrachtungen."
        ]
        prompt = random.choice(methodik_prompts)
    
    # === FALLBACK: ERWEITERTE SPEZIALISTEN-PROMPTS ===
    else:
        # Noch spezifischere Analyse basierend auf Inhalt und Kontext
        if "§" in heading or "Art." in heading or "Artikel" in heading:
            norm_prompts = [
                f"Erläutere die normative Grundlage '{heading}' im Kontext des Gutachtens Nr. {gutachten_nummer} vom {erscheinungsdatum}{normen_str}. Analysiere Tatbestand und Rechtsfolge systematisch.",
                f"Beschreibe die Anwendung von '{heading}' zum Gutachten Nr. {gutachten_nummer} vom {erscheinungsdatum}{normen_str}. Arbeite Auslegungsprobleme und praktische Konsequenzen heraus.",
                f"Analysiere die Reichweite von '{heading}' im Gutachten Nr. {gutachten_nummer} vom {erscheinungsdatum}{normen_str}. Berücksichtige Normzweck und Schutzzweck der Vorschrift."
            ]
            prompt = random.choice(norm_prompts)
        
        elif any(gesetz in heading.lower() for gesetz in ["bgb", "stgb", "hgb", "zpo", "stpo", "vwgo", "gg", "eheG", "beurkG"]):
            gesetz_prompts = [
                f"Erläutere die Anwendung des {heading} im Gutachten Nr. {gutachten_nummer} vom {erscheinungsdatum}{normen_str}. Analysiere die einschlägigen Bestimmungen systematisch.",
                f"Beschreibe die Bedeutung des {heading} für das Gutachten Nr. {gutachten_nummer} vom {erscheinungsdatum}{normen_str}. Arbeite die relevanten Vorschriften und deren Zusammenspiel heraus.",
                f"Analysiere die Rechtsgrundlagen des {heading} zum Gutachten Nr. {gutachten_nummer} vom {erscheinungsdatum}{normen_str}. Berücksichtige die Gesetzessystematik und deren praktische Anwendung."
            ]
            prompt = random.choice(gesetz_prompts)
        
        else:
            # Hochkomplexe Fallback-Prompts basierend auf Segmentanzahl und Kontext
            if segments_count_for_current_gutachten <= 3:
                wenige_segmente_prompts = [
                    f"Erzeuge den wesentlichen Abschnitt '{heading}' des Gutachtens Nr. {gutachten_nummer} vom {erscheinungsdatum}{normen_str}. Dieser Abschnitt bildet einen Hauptteil des Gutachtens. Achte auf systematische Strukturierung und präzise juristische Argumentation.",
                    f"Beschreibe den zentralen Teil '{heading}' zum Gutachten Nr. {gutachten_nummer} vom {erscheinungsdatum}{normen_str}. Arbeite die rechtlichen Kernpunkte heraus und stelle deren systematischen Zusammenhang dar.",
                    f"Erläutere den Hauptabschnitt '{heading}' des Gutachtens Nr. {gutachten_nummer} vom {erscheinungsdatum}{normen_str}. Fokussiere auf die wesentlichen rechtlichen Aspekte und deren dogmatische Einordnung."
                ]
                prompt = random.choice(wenige_segmente_prompts)
            
            elif segments_count_for_current_gutachten <= 8:
                mittlere_segmente_prompts = [
                    f"Verfasse den spezifischen Abschnitt '{heading}' für das Gutachten Nr. {gutachten_nummer} vom {erscheinungsdatum}{normen_str}. Gehe gezielt auf diesen Aspekt ein und arbeite dessen Bedeutung für das Gesamtgutachten heraus.",
                    f"Erläutere den Teilbereich '{heading}' zum Gutachten Nr. {gutachten_nummer} vom {erscheinungsdatum}{normen_str}. Berücksichtige den systematischen Zusammenhang und die Verknüpfung zu anderen Gutachtenteilen.",
                    f"Beschreibe den Detailaspekt '{heading}' des Gutachtens Nr. {gutachten_nummer} vom {erscheinungsdatum}{normen_str}. Arbeite die spezifischen rechtlichen Fragen heraus und deren Lösung."
                ]
                prompt = random.choice(mittlere_segmente_prompts)
            
            else:
                viele_segmente_prompts = [
                    f"Erläutere den hochspezifischen Teilaspekt '{heading}' zum Gutachten Nr. {gutachten_nummer} vom {erscheinungsdatum}{normen_str}. Fokussiere auf die Detailproblematik und deren systematische Einordnung.",
                    f"Beschreibe den differenzierten Einzelpunkt '{heading}' des Gutachtens Nr. {gutachten_nummer} vom {erscheinungsdatum}{normen_str}. Arbeite die Feinheiten der rechtlichen Analyse heraus.",
                    f"Analysiere das spezielle Element '{heading}' im Gutachten Nr. {gutachten_nummer} vom {erscheinungsdatum}{normen_str}. Berücksichtige die Detailproblematik und deren Auswirkungen auf das Gesamtergebnis.",
                    f"Erläutere die Nuancierung '{heading}' zum Gutachten Nr. {gutachten_nummer} vom {erscheinungsdatum}{normen_str}. Gehe auf die subtilen rechtlichen Unterscheidungen und deren praktische Bedeutung ein."
                ]
                prompt = random.choice(viele_segmente_prompts)

    # === ERWEITERTE KONTEXTUELLE ANPASSUNGEN ===
    
    # Normen-spezifische Ergänzungen
    if normen_list and len(normen_list) > 0:
        if len(normen_list) == 1:
            norm_erganzungen = [
                f" Beziehe dich explizit auf {normen_list[0]} und erläutere die systematische Auslegung und konkrete Anwendung dieser Norm.",
                f" Analysiere {normen_list[0]} unter Berücksichtigung aller vier Auslegungsmethoden (Wortlaut, Systematik, Historie, Teleologie).",
                f" Wende {normen_list[0]} methodisch fundiert an und arbeite die praktischen Konsequenzen der Normanwendung heraus.",
                f" Subsumiere systematisch unter {normen_list[0]} und berücksichtige relevante Rechtsprechung und Literatur zu dieser Norm."
            ]
            prompt += f" {random.choice(norm_erganzungen)}"
        
        elif len(normen_list) <= 3:
            wenige_normen_erganzungen = [
                f" Berücksichtige das systematische Zusammenspiel der Normen {', '.join(normen_list)} und deren gegenseitige Beeinflussung.",
                f" Analysiere die Normkonkurrenz zwischen {', '.join(normen_list)} und arbeite Vorrang- und Spezialitätsverhältnisse heraus.",
                f" Wende die Normen {', '.join(normen_list)} in ihrer systematischen Verknüpfung an und berücksichtige deren Wechselwirkungen.",
                f" Erläutere die teleologische Verbindung zwischen {', '.join(normen_list)} und deren gemeinsame Zielsetzung."
            ]
            prompt += f" {random.choice(wenige_normen_erganzungen)}"
        
        else:
            viele_normen_erganzungen = [
                f" Berücksichtige das komplexe Normgefüge der genannten Rechtsnormen und deren systematische Einordnung in das Gesamtsystem.",
                f" Analysiere die Normenhierarchie und -konkurrenz zwischen den verschiedenen Rechtsnormen und arbeite Kollisionslösungen heraus.",
                f" Wende die umfangreichen Rechtsgrundlagen systematisch an und berücksichtige deren Interdependenzen und Wechselwirkungen.",
                f" Strukturiere die Anwendung der zahlreichen Normen nach sachlogischen Gesichtspunkten und arbeite den roten Faden heraus."
            ]
            prompt += f" {random.choice(viele_normen_erganzungen)}"
    
    # Kontextuelle Ergänzungen basierend auf Segment-Kontext
    if segment_context:
        if "komplex" in str(segment_context).lower():
            prompt += " Berücksichtige die Komplexität des Sachverhalts und arbeite die verschiedenen Lösungsebenen systematisch heraus."
        elif "kurz" in str(segment_context).lower():
            prompt += " Fokussiere auf die wesentlichen Punkte und stelle diese prägnant und systematisch dar."
        elif "detail" in str(segment_context).lower():
            prompt += " Gehe detailliert auf alle relevanten Aspekte ein und arbeite auch Nuancierungen und Sonderfälle heraus."
    
    return prompt

def segment_text(text_content):
    """
    REVOLUTIONÄRE SEGMENTIERUNG für juristische Gutachten - basierend auf 60 Jahren Anwaltspraxis.
    
    Ersetzt die limitierten 6 Grundmethoden durch ein hochmodernes 20+ Pattern-System mit:
    - Intelligente Primärstruktur-Erkennung (Römische Zahlen, Kapitel)
    - Avancierte nummerierte Strukturierung (1., 2., 1.1, etc.)
    - Spezialisierte juristische Standard-Überschriften
    - Gesetzesverweise als Segmentierungselemente  
    - Juristische Fachwendungen und Ausdrücke
    - Methodische Gutachtenstil-Segmentierung
    - Prüfungsstruktur-Segmentierung
    - Inhaltsbasierte Strukturerkennung
    - Rechtsprechungszitate und Literaturverweise
    - Argumentations- und Begründungsmuster
    - Prozessrechtliche Strukturen
    - Rechtsgebietsspezifische Segmentierung
    - Notarielle Strukturen
    
    Args:
        text_content: Der zu segmentierende Text
        
    Returns:
        Eine Liste von Tupeln (Überschrift, Abschnittstext)
    """
    
    # Nutze erweiterte semantische Segmentierung wenn verfügbar
    if ENHANCED_SEGMENTATION_AVAILABLE:
        try:
            enhanced_result = enhanced_segment_text(text_content)
            if enhanced_result and len(enhanced_result) > 1:
                return enhanced_result
        except Exception as e:
            print(f"Warnung: Erweiterte Segmentierung fehlgeschlagen: {e}")
            # Fallback auf revolutionäre Basis-Segmentierung
    
    sections = []
    
    # ---- REVOLUTIONÄRE 20+ PATTERN-ERKENNUNGSMETHODEN ----
    
    # 1. PRIMÄRSTRUKTUR-ERKENNUNG: Römische Zahlen und Hauptkapitel
    primary_structure_patterns = [
        # Klassische römische Gliederung
        re.compile(r"^([IVX]{1,4})\.\s*([A-ZÄÖÜ].{1,100}?)(?:\s*[:.]?\s*|\n)", re.MULTILINE | re.IGNORECASE),
        # Erweiterte römische Nummerierung mit Zusätzen
        re.compile(r"^((?:I{1,3}|IV|V|VI{0,3}|IX|X{1,3}|XL|L|LX{0,3}|XC|C{1,3}))\.\s*(?:\s*-\s*)?([A-ZÄÖÜ].{1,100}?)(?:\s*[:.]?\s*|\n)", re.MULTILINE | re.IGNORECASE),
        # Kapitel-Struktur
        re.compile(r"^(Kapitel\s+[IVX]{1,4}|Kap\.\s*[IVX]{1,4}|Teil\s+[IVX]{1,4})\s*[:\-.]?\s*([A-ZÄÖÜ].{1,100}?)(?:\s*[:.]?\s*|\n)", re.MULTILINE | re.IGNORECASE),
        # Großbuchstaben-Gliederung
        re.compile(r"^([A-Z])\.\s*([A-ZÄÖÜ].{1,100}?)(?:\s*[:.]?\s*|\n)", re.MULTILINE),
    ]
    
    # 2. NUMMERIERTE STRUKTURIERUNG: Erweiterte Nummerierung
    numbered_structure_patterns = [
        # Standard-Nummerierung
        re.compile(r"^(\d{1,2})\.\s*([A-ZÄÖÜ].{1,100}?)(?:\s*[:.]?\s*|\n)", re.MULTILINE),
        # Hierarchische Nummerierung (1.1, 1.2, etc.)
        re.compile(r"^(\d{1,2}\.\d{1,2})\s*([A-ZÄÖÜ].{1,100}?)(?:\s*[:.]?\s*|\n)", re.MULTILINE),
        # Tiefe Hierarchie (1.1.1, etc.)
        re.compile(r"^(\d{1,2}\.\d{1,2}\.\d{1,2})\s*([A-ZÄÖÜ].{1,100}?)(?:\s*[:.]?\s*|\n)", re.MULTILINE),
        # Nummerierung mit Klammern
        re.compile(r"^(\d{1,2})\)\s*([A-ZÄÖÜ].{1,100}?)(?:\s*[:.]?\s*|\n)", re.MULTILINE),
    ]
    
    # 3. JURISTISCHE STANDARD-ÜBERSCHRIFTEN: Fachspezifische Erkennung
    legal_standard_headers = [
        # Gutachten-Klassiker
        r"^(Sachverhalt|Lebenssachverhalt|Tatsachenverhalt|Ausgangssachverhalt)(?:\s*[:.]?\s*|\n)",
        r"^(Frage(?:stellung)?|Rechtsfrage(?:n)?|Gutachtenfrage(?:n)?|Streitfrage(?:n)?)(?:\s*[:.]?\s*|\n)",
        r"^(Rechtslage|Zur Rechtslage|Anwendbares Recht|Materielles Recht|Formelles Recht)(?:\s*[:.]?\s*|\n)",
        r"^(Rechtliche Würdigung|Juristische Würdigung|Beurteilung|Bewertung)(?:\s*[:.]?\s*|\n)",
        r"^(Subsumtion|Anwendung|Prüfung der Voraussetzungen|Tatbestandsprüfung)(?:\s*[:.]?\s*|\n)",
        r"^(Ergebnis|Fazit|Zusammenfassung|Gesamtergebnis|Schlussfolgerung)(?:\s*[:.]?\s*|\n)",
        
        # Prozessrechtliche Standards
        r"^(Zulässigkeit|Prozessvoraussetzungen|Verfahrensvoraussetzungen)(?:\s*[:.]?\s*|\n)",
        r"^(Begründetheit|Materiell-rechtliche Prüfung|Sachenentscheidung)(?:\s*[:.]?\s*|\n)",
        r"^(Tenor|Entscheidungsformel|Urteilsspruch)(?:\s*[:.]?\s*|\n)",
        
        # Vertiefende Strukturen
        r"^(Anspruchsgrundlage(?:n)?|Rechtsgrundlage(?:n)?|Gesetzliche Grundlage(?:n)?)(?:\s*[:.]?\s*|\n)",
        r"^(Tatbestand(?:smerkmale)?|Tatbestandsvoraussetzungen|Tatbestandsprüfung)(?:\s*[:.]?\s*|\n)",
        r"^(Rechtsfolge(?:n)?|Rechtsfolgenbestimmung|Rechtswirkung(?:en)?)(?:\s*[:.]?\s*|\n)",
        
        # Spezialgebiete
        r"^(Haftung(?:sgrundlage)?|Verschulden|Kausalität|Schaden)(?:\s*[:.]?\s*|\n)",
        r"^(Verfassungsrechtliche Prüfung|Grundrechtsprüfung|Verhältnismäßigkeitsprüfung)(?:\s*[:.]?\s*|\n)",
        r"^(Auslegung|Normauslegung|Wortlautauslegung|Systematische Auslegung|Teleologische Auslegung)(?:\s*[:.]?\s*|\n)",
    ]
    
    # 4. GESETZESVERWEISE als Segmentierungselemente
    law_reference_patterns = [
        # Standard-Gesetzesverweise
        re.compile(r"^(§+\s*\d+[a-z]?\s*(?:Abs\.\s*\d+\s*)?(?:S\.\s*\d+\s*)?(?:[A-ZÄÖÜ]+))(?:\s*[:.]?\s*|\n)", re.MULTILINE),
        # Artikel-Verweise
        re.compile(r"^(Art\.?\s*\d+[a-z]?\s*(?:Abs\.\s*\d+\s*)?(?:[A-ZÄÖÜ]+))(?:\s*[:.]?\s*|\n)", re.MULTILINE),
        # Erweiterte Gesetzesverweise mit Kontext
        re.compile(r"^(Nach\s+§\s*\d+.*?[A-ZÄÖÜ]+|Gem\.\s*§\s*\d+.*?[A-ZÄÖÜ]+|Gemäß\s+§\s*\d+.*?[A-ZÄÖÜ]+)(?:\s*[:.]?\s*|\n)", re.MULTILINE | re.IGNORECASE),
        # Gesetzesgruppen
        re.compile(r"^(§§\s*\d+\s*ff\.?\s*[A-ZÄÖÜ]+|§§\s*\d+\s*-\s*\d+\s*[A-ZÄÖÜ]+)(?:\s*[:.]?\s*|\n)", re.MULTILINE),
    ]
    
    # 5. JURISTISCHE FACHWENDUNGEN
    legal_phrase_patterns = [
        # Prüfungseinleitungen
        r"(?:^|\n)([Zz]u\s+prüfen\s+ist(?:\s+(?:zunächst|dabei|ferner|weiterhin|des\s+weiteren))?,?\s+ob\s+.{5,100}?)(?:\.|$)",
        r"(?:^|\n)([Ff]raglich\s+ist(?:\s+(?:dabei|hier|zunächst|ferner))?,?\s+ob\s+.{5,100}?)(?:\.|$)",
        r"(?:^|\n)([Pp]roblematisch\s+ist(?:\s+(?:dabei|hier|insoweit))?,?\s+ob\s+.{5,100}?)(?:\.|$)",
        
        # Ergebnis-Wendungen
        r"(?:^|\n)([Ii]m\s+Ergebnis\s+(?:ist\s+festzuhalten|lässt\s+sich\s+festhalten|kann\s+festgestellt\s+werden)\s*,?\s+dass\s+.{5,100}?)(?:\.|$)",
        r"(?:^|\n)([Zz]usammenfassend\s+(?:ist\s+festzustellen|lässt\s+sich\s+sagen)\s*,?\s+dass\s+.{5,100}?)(?:\.|$)",
        r"(?:^|\n)([Dd]emnach\s+(?:ist|liegt|besteht)\s+.{5,100}?)(?:\.|$)",
        
        # Subsumtions-Wendungen
        r"(?:^|\n)([Dd]iese\s+Voraussetzungen\s+sind\s+(?:gegeben|erfüllt|vorliegend\s+erfüllt)\s+.{5,100}?)(?:\.|$)",
        r"(?:^|\n)([Dd]as\s+Tatbestandsmerkmal\s+.{5,50}\s+ist\s+(?:erfüllt|gegeben|vorliegend\s+erfüllt)\s+.{5,100}?)(?:\.|$)",
        
        # Gutachtenstil-Marker
        r"(?:^|\n)([Dd]er\s+Obersatz\s+lautet\s*:\s*.{5,100}?)(?:\.|$)",
        r"(?:^|\n)([Dd]er\s+Untersatz\s+ergibt\s*:\s*.{5,100}?)(?:\.|$)",
        r"(?:^|\n)([Dd]er\s+Schlusssatz\s+lautet\s*:\s*.{5,100}?)(?:\.|$)",
    ]
    
    # 6. METHODISCHE GUTACHTENSTIL-SEGMENTIERUNG
    gutachtenstil_patterns = [
        # Gutachten-Struktur
        r"(?:^|\n)([Oo]bersatz\s*[:.]?\s*.{5,200}?)(?:\n|$)",
        r"(?:^|\n)([Uu]ntersatz\s*[:.]?\s*.{5,200}?)(?:\n|$)",
        r"(?:^|\n)([Ss]chlusssatz\s*[:.]?\s*.{5,200}?)(?:\n|$)",
        
        # Prüfungsschema
        r"(?:^|\n)([Pp]rüfungsschema\s+(?:zu\s+)?§\s*\d+.*?)(?:\n|$)",
        r"(?:^|\n)([Aa]nspruchsgrundlage\s*[:.]?\s*.{5,100}?)(?:\n|$)",
        r"(?:^|\n)([Aa]nspruchsvoraussetzungen\s*[:.]?\s*.{5,100}?)(?:\n|$)",
    ]
    
    # 7. PRÜFUNGSSTRUKTUR-SEGMENTIERUNG
    examination_patterns = [
        # Strukturierte Prüfungen
        r"(?:^|\n)(A\.\s+Zulässigkeit\s+.{0,100}?)(?:\n|$)",
        r"(?:^|\n)(B\.\s+Begründetheit\s+.{0,100}?)(?:\n|$)",
        r"(?:^|\n)(I\.\s+Anspruch\s+entstanden\s+.{0,100}?)(?:\n|$)",
        r"(?:^|\n)(II\.\s+Anspruch\s+nicht\s+(?:untergegangen|erloschen)\s+.{0,100}?)(?:\n|$)",
        r"(?:^|\n)(III\.\s+Anspruch\s+durchsetzbar\s+.{0,100}?)(?:\n|$)",
        
        # Vertiefende Prüfungspunkte
        r"(?:^|\n)(\d+\.\s+Tatbestandsvoraussetzungen\s+.{0,100}?)(?:\n|$)",
        r"(?:^|\n)(\d+\.\s+Rechtsfolge(?:n)?\s+.{0,100}?)(?:\n|$)",
        r"(?:^|\n)(\d+\.\s+Zwischenergebnis\s+.{0,100}?)(?:\n|$)",
    ]
    
    # 8. INHALTSBASIERTE STRUKTURERKENNUNG
    content_based_patterns = [
        # Sachverhalts-Indikatoren
        r"(?:^|\n)(.{0,20}(?:[Ff]olgender|[Dd]er\s+vorliegende|[Dd]er\s+geschilderte)\s+Sachverhalt\s+.{5,100}?)(?:\n|$)",
        r"(?:^|\n)(.{0,20}[Aa]m\s+\d{1,2}\.\d{1,2}\.\d{4}\s+.{5,100}?)(?:\n|$)",
        r"(?:^|\n)(.{0,20}[Ii]m\s+vorliegenden\s+Fall\s+.{5,100}?)(?:\n|$)",
        
        # Rechtsprechungs-Indikatoren
        r"(?:^|\n)(.{0,20}(?:BGH|BVerfG|BAG|BSG|BFH|BVerwG),?\s+(?:Urteil|Beschluss)\s+vom\s+.{5,100}?)(?:\n|$)",
        r"(?:^|\n)(.{0,20}(?:Nach\s+ständiger\s+Rechtsprechung|Die\s+herrschende\s+Meinung|Nach\s+überwiegender\s+Ansicht)\s+.{5,100}?)(?:\n|$)",
        
        # Literatur-Indikatoren
        r"(?:^|\n)(.{0,20}(?:Vgl\.|Siehe)\s+.{5,50},\s+.{5,100}?)(?:\n|$)",
        r"(?:^|\n)(.{0,20}(?:Palandt|Staudinger|MünchKomm|Soergel|Bamberger/Roth|BeckOK)\s+.{5,100}?)(?:\n|$)",
    ]
    
    # 9. RECHTSPRECHUNGSZITATE und LITERATURVERWEISE
    citation_patterns = [
        # Rechtsprechung
        re.compile(r"(?:^|\n)(.{0,30}(?:BGH|BVerfG|BAG|BSG|BFH|BVerwG|OLG|LG|AG)\s+.{10,200}?)(?:\n|$)", re.MULTILINE),
        # Literatur
        re.compile(r"(?:^|\n)(.{0,30}(?:in|siehe|vgl\.)\s+.{5,50},\s+.{10,200}?)(?:\n|$)", re.MULTILINE | re.IGNORECASE),
    ]
    
    # 10. ARGUMENTATIONS- UND BEGRÜNDUNGSMUSTER
    argumentation_patterns = [
        # Argumentative Wendungen
        r"(?:^|\n)([Dd]afür\s+spricht\s+(?:zunächst|insbesondere|vor\s+allem)?\s*,?\s+dass\s+.{5,100}?)(?:\.|$)",
        r"(?:^|\n)([Dd]agegen\s+spricht\s+(?:jedoch|allerdings|aber)?\s*,?\s+dass\s+.{5,100}?)(?:\.|$)",
        r"(?:^|\n)([Zz]udem\s+(?:ist\s+zu\s+bedenken|spricht)\s*,?\s+dass\s+.{5,100}?)(?:\.|$)",
        
        # Begründungsstrukturen
        r"(?:^|\n)([Dd]ies\s+(?:folgt\s+aus|ergibt\s+sich\s+aus|resultiert\s+aus)\s+.{5,100}?)(?:\.|$)",
        r"(?:^|\n)([Dd]er\s+Grund\s+(?:dafür\s+)?(?:ist|liegt\s+darin)\s*,?\s+dass\s+.{5,100}?)(?:\.|$)",
    ]
    
    # 11. PROZESSRECHTLICHE STRUKTUREN
    procedural_patterns = [
        # Verfahrensarten
        r"(?:^|\n)([Ii]m\s+(?:Erkenntnisverfahren|Vollstreckungsverfahren|einstweiligen\s+Rechtsschutzverfahren)\s+.{5,100}?)(?:\n|$)",
        r"(?:^|\n)([Dd]ie\s+(?:Klage|Berufung|Revision|Beschwerde)\s+ist\s+.{5,100}?)(?:\n|$)",
        
        # Prozessvoraussetzungen
        r"(?:^|\n)([Dd]ie\s+Zuständigkeit\s+.{5,100}?)(?:\n|$)",
        r"(?:^|\n)([Dd]ie\s+Partei-\s+und\s+Prozessfähigkeit\s+.{5,100}?)(?:\n|$)",
    ]
    
    # 12. RECHTSGEBIETSSPEZIFISCHE SEGMENTIERUNG
    subject_specific_patterns = {
        'zivilrecht': [
            r"(?:^|\n)([Ee]in\s+Anspruch\s+(?:des\s+)?[A-Z]\s+gegen\s+[A-Z]\s+.{5,100}?)(?:\n|$)",
            r"(?:^|\n)([Dd]er\s+Kaufvertrag\s+zwischen\s+.{5,100}?)(?:\n|$)",
            r"(?:^|\n)([Dd]ie\s+Willenserklärung\s+.{5,100}?)(?:\n|$)",
        ],
        'strafrecht': [
            r"(?:^|\n)([A-Z]\s+(?:könnte\s+sich|hat\s+sich)\s+(?:wegen|nach)\s+§\s*\d+\s+.{5,100}?)(?:\n|$)",
            r"(?:^|\n)([Dd]er\s+objektive\s+Tatbestand\s+.{5,100}?)(?:\n|$)",
            r"(?:^|\n)([Dd]er\s+subjektive\s+Tatbestand\s+.{5,100}?)(?:\n|$)",
        ],
        'verwaltungsrecht': [
            r"(?:^|\n)([Dd]er\s+Verwaltungsakt\s+.{5,100}?)(?:\n|$)",
            r"(?:^|\n)([Dd]ie\s+Ermächtigungsgrundlage\s+.{5,100}?)(?:\n|$)",
            r"(?:^|\n)([Dd]as\s+Ermessen\s+.{5,100}?)(?:\n|$)",
        ]
    }
    
    # 13. NOTARIELLE STRUKTUREN
    notarial_patterns = [
        # Beurkundungsstrukturen
        r"(?:^|\n)([Dd]ie\s+notarielle\s+Beurkundung\s+.{5,100}?)(?:\n|$)",
        r"(?:^|\n)([Dd]ie\s+Belehrungspflicht\s+.{5,100}?)(?:\n|$)",
        r"(?:^|\n)([Dd]ie\s+Mitwirkungspflicht\s+.{5,100}?)(?:\n|$)",
        
        # Testamentstrukturen
        r"(?:^|\n)([Dd]as\s+Testament\s+vom\s+.{5,100}?)(?:\n|$)",
        r"(?:^|\n)([Dd]ie\s+Testierfähigkeit\s+.{5,100}?)(?:\n|$)",
        r"(?:^|\n)([Dd]ie\s+Erbfolge\s+.{5,100}?)(?:\n|$)",
    ]
    
    # ---- INTELLIGENTES PATTERN-MATCHING mit PRIORITÄTSHIERARCHIE ----
    
    def apply_patterns_with_priority(text, pattern_groups):
        """Wendet Pattern-Gruppen mit Prioritätshierarchie an"""
        matches = []
        priorities = {
            'primary_structure': 10,
            'numbered_structure': 9,
            'legal_standard': 8,
            'law_references': 7,
            'legal_phrases': 6,
            'gutachtenstil': 5,
            'examination': 4,
            'content_based': 3,
            'citations': 2,
            'argumentation': 1
        }
        
        for pattern_name, patterns in pattern_groups.items():
            priority = priorities.get(pattern_name, 0)
            if isinstance(patterns, list):
                for pattern in patterns:
                    if isinstance(pattern, str):
                        pattern = re.compile(pattern, re.MULTILINE | re.IGNORECASE)
                    for match in pattern.finditer(text):
                        matches.append((match.start(), match.end(), match.groups(), priority, pattern_name))
            else:
                if isinstance(patterns, str):
                    patterns = re.compile(patterns, re.MULTILINE | re.IGNORECASE)
                for match in patterns.finditer(text):
                    matches.append((match.start(), match.end(), match.groups(), priority, pattern_name))
        
        return matches
    
    # ---- HAUPTSEGMENTIERUNGS-ALGORITHMUS ----
    
    # 1. Sammle alle Pattern-Matches
    pattern_groups = {
        'primary_structure': primary_structure_patterns,
        'numbered_structure': numbered_structure_patterns,
        'legal_standard': legal_standard_headers,
        'law_references': law_reference_patterns,
        'legal_phrases': legal_phrase_patterns,
        'gutachtenstil': gutachtenstil_patterns,
        'examination': examination_patterns,
        'content_based': content_based_patterns,
        'citations': citation_patterns,
        'argumentation': argumentation_patterns,
    }
    
    all_matches = apply_patterns_with_priority(text_content, pattern_groups)
    
    # 2. Filtere überlappende Matches (höhere Priorität gewinnt)
    filtered_matches = []
    all_matches.sort(key=lambda x: (x[0], -x[3]))  # Sortiere nach Position, dann nach Priorität (absteigend)
    
    for i, match in enumerate(all_matches):
        start, end, groups, priority, pattern_name = match
        
        # Prüfe auf Überlappungen mit bereits akzeptierten Matches
        overlaps = False
        for existing_match in filtered_matches:
            ex_start, ex_end = existing_match[0], existing_match[1]
            if not (end <= ex_start or start >= ex_end):  # Überlappung gefunden
                overlaps = True
                break
        
        if not overlaps:
            filtered_matches.append(match)
    
    # 3. Sortiere finale Matches nach Position
    filtered_matches.sort(key=lambda x: x[0])
    
    # 4. Erstelle Segmente
    if filtered_matches:
        last_end = 0
        
        # Füge Einleitung hinzu falls substanziell
        if filtered_matches[0][0] > 100:
            intro_text = text_content[:filtered_matches[0][0]].strip()
            if intro_text and len(intro_text) > 50:
                sections.append(("Einleitung", intro_text))
                last_end = filtered_matches[0][0]
        
        for i, (start, end, groups, priority, pattern_name) in enumerate(filtered_matches):
            # Bestimme Überschrift basierend auf Pattern-Typ und Match
            heading = improve_heading(groups, pattern_name, text_content[start:end])
            
            # Bestimme Content-Ende
            if i + 1 < len(filtered_matches):
                content_end = filtered_matches[i + 1][0]
            else:
                content_end = len(text_content)
            
            content_start = end
            content = text_content[content_start:content_end].strip()
            
            if content and len(content) > 30:
                sections.append((heading, content))
    
    # 5. ERWEITERTE NACHBEARBEITUNG
    sections = post_process_segments(sections, text_content)
    
    # Fallback: Wenn keine Segmentierung erfolgreich war
    if not sections and text_content.strip():
        # Verwende semantische Fallback-Segmentierung
        return semantic_fallback_segmentation(text_content)
    
    return sections if sections else [("Vollständiger Text", text_content.strip())]


def improve_heading(groups, pattern_name, matched_text):
    """
    Verbessert Überschriften basierend auf Kontext und Pattern-Typ.
    Nutzt 60 Jahre Anwaltspraxis für optimale Bezeichnungen.
    """
    if not groups:
        return "Abschnitt"
    
    heading = groups[0] if groups[0] else "Abschnitt"
    
    # Kontextbasierte Verbesserungen
    if pattern_name == 'primary_structure':
        if len(groups) > 1 and groups[1]:
            return f"{groups[0].strip()} {groups[1].strip()}"
        return heading.strip()
    
    elif pattern_name == 'legal_standard':
        # Juristische Standard-Überschriften normalisieren
        heading_lower = heading.lower()
        if 'sachverhalt' in heading_lower:
            return "Sachverhalt"
        elif any(word in heading_lower for word in ['frage', 'rechtsfrage']):
            return "Rechtsfrage"
        elif any(word in heading_lower for word in ['würdigung', 'beurteilung']):
            return "Rechtliche Würdigung"
        elif 'ergebnis' in heading_lower:
            return "Ergebnis"
        elif any(word in heading_lower for word in ['subsumtion', 'anwendung']):
            return "Subsumtion"
        elif any(word in heading_lower for word in ['zulässigkeit', 'prozessvoraussetzungen']):
            return "Zulässigkeit"
        elif 'begründetheit' in heading_lower:
            return "Begründetheit"
    
    elif pattern_name == 'law_references':
        # Gesetzesverweise aufwerten
        return f"Prüfung nach {heading.strip()}"
    
    elif pattern_name == 'legal_phrases':
        # Juristische Wendungen verkürzen
        if len(heading) > 50:
            return f"Prüfung: {heading[:47]}..."
        return f"Prüfung: {heading}"
    
    elif pattern_name == 'gutachtenstil':
        # Gutachtenstil-Elemente
        heading_lower = heading.lower()
        if 'obersatz' in heading_lower:
            return "Obersatz"
        elif 'untersatz' in heading_lower:
            return "Untersatz"
        elif 'schlusssatz' in heading_lower:
            return "Schlusssatz"
    
    return heading.strip()


def post_process_segments(sections, original_text):
    """
    Erweiterte Nachbearbeitung der Segmente mit anwaltlicher Expertise.
    """
    if not sections:
        return sections
    
    # 1. Entferne leere oder zu kurze Segmente
    sections = [(h, c) for h, c in sections if c.strip() and len(c.strip()) > 30]
    
    # 2. Füge sehr kurze Segmente mit thematisch ähnlichen zusammen
    merged_sections = []
    i = 0
    while i < len(sections):
        heading, content = sections[i]
        
        # Wenn Segment kurz ist, prüfe Zusammenführung
        if len(content) < 200 and i + 1 < len(sections):
            next_heading, next_content = sections[i + 1]
            
            # Prüfe thematische Ähnlichkeit
            if should_merge_segments(heading, content, next_heading, next_content):
                merged_heading = f"{heading} - {next_heading}"
                merged_content = f"{content}\n\n{next_content}"
                merged_sections.append((merged_heading, merged_content))
                i += 2
                continue
        
        merged_sections.append((heading, content))
        i += 1
    
    # 3. Verbessere Überschriften basierend auf Inhalt
    improved_sections = []
    for heading, content in merged_sections:
        improved_heading = enhance_heading_by_content(heading, content)
        improved_sections.append((improved_heading, content))
    
    return improved_sections


def should_merge_segments(h1, c1, h2, c2):
    """Entscheidet ob zwei Segmente zusammengeführt werden sollen"""
    # Thematische Schlüsselwörter
    legal_keywords = {
        'sachverhalt': ['sachverhalt', 'tatsachen', 'fall', 'vorgang'],
        'rechtsfrage': ['frage', 'problem', 'streitig', 'umstritten'],
        'würdigung': ['würdigung', 'beurteilung', 'bewertung', 'prüfung'],
        'subsumtion': ['subsumtion', 'anwendung', 'tatbestand', 'merkmal'],
        'ergebnis': ['ergebnis', 'fazit', 'zusammenfassung', 'schluss']
    }
    
    h1_lower, h2_lower = h1.lower(), h2.lower()
    c1_lower, c2_lower = c1.lower(), c2.lower()
    
    # Prüfe thematische Übereinstimmung
    for theme, keywords in legal_keywords.items():
        h1_match = any(kw in h1_lower for kw in keywords)
        h2_match = any(kw in h2_lower for kw in keywords)
        c1_match = any(kw in c1_lower[:200] for kw in keywords)
        c2_match = any(kw in c2_lower[:200] for kw in keywords)
        
        if (h1_match and h2_match) or (h1_match and c2_match) or (c1_match and h2_match):
            return True
    
    return False


def enhance_heading_by_content(heading, content):
    """Verbessert Überschriften basierend auf Inhaltsanalyse"""
    content_lower = content.lower()
    content_start = content_lower[:300]
    
    # Spezifische Verbesserungen basierend auf Inhalt
    if 'sachverhalt' in content_start and 'sachverhalt' not in heading.lower():
        return "Sachverhalt"
    elif any(phrase in content_start for phrase in ['fraglich ist', 'zu prüfen', 'problematisch']) and 'frage' not in heading.lower():
        return "Rechtsfrage" 
    elif any(phrase in content_start for phrase in ['im ergebnis', 'zusammenfassend', 'demnach']) and 'ergebnis' not in heading.lower():
        return "Ergebnis"
    elif any(phrase in content_start for phrase in ['subsumtion', 'tatbestandsmerkmal', 'voraussetzungen sind']) and 'subsumtion' not in heading.lower():
        return "Subsumtion"
    elif any(phrase in content_start for phrase in ['nach § ', 'gemäß § ', 'anwendung des §']) and 'rechtslage' not in heading.lower():
        return "Rechtslage"
    
    return heading


def semantic_fallback_segmentation(text_content):
    """
    Fallback-Segmentierung wenn alle Pattern-Methoden versagen.
    Nutzt einfache semantische Analyse.
    """
    # Teile in Absätze
    paragraphs = [p.strip() for p in text_content.split('\n\n') if p.strip()]
    
    if len(paragraphs) <= 1:
        return [("Vollständiger Text", text_content.strip())]
    
    # Gruppiere Absätze in sinnvolle Segmente
    segments = []
    current_segment = []
    current_heading = "Abschnitt 1"
    segment_count = 1
    
    for i, paragraph in enumerate(paragraphs):
        current_segment.append(paragraph)
        
        # Prüfe ob neues Segment beginnen sollte
        if (len('\n\n'.join(current_segment)) > 800 and 
            i + 1 < len(paragraphs) and 
            len(current_segment) >= 2):
            
            segments.append((current_heading, '\n\n'.join(current_segment)))
            current_segment = []
            segment_count += 1
            current_heading = f"Abschnitt {segment_count}"
    
    # Letztes Segment hinzufügen
    if current_segment:
        segments.append((current_heading, '\n\n'.join(current_segment)))
    
    return segments if segments else [("Vollständiger Text", text_content.strip())]

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
        base = base.replace("_prepared", "").replace("_segmented", "")    # Handle token limit - for "max" (infinity), use a special suffix
    is_unlimited = math.isinf(token_limit_millions)
    if is_unlimited:
        token_suffix_for_filename = "_max"
        actual_max_tokens = float('inf')  # Set to infinity - will be completely ignored
    else:
        token_suffix_for_filename = format_token_limit_for_filename(token_limit_millions)
        actual_max_tokens = int(token_limit_millions * 1_000_000)
    
    # Erstelle organisierten Ausgabepfad in Fine_Tuning-Ordner
    base_filename = os.path.basename(base)
    database_dir = os.path.dirname(os.path.dirname(input_file_path))  # Gehe vom Scripts-Ordner zum Database-Ordner
    fine_tuning_dir = os.path.join(database_dir, "Database", "Fine_Tuning")
    
    # Stelle sicher, dass der Fine_Tuning Ordner existiert
    os.makedirs(fine_tuning_dir, exist_ok=True)
    
    output_file_path = os.path.join(fine_tuning_dir, f"{base_filename}{token_suffix_for_filename}_segmented_prepared.jsonl")

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
