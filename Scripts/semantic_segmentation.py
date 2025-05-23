"""
Dieses Modul enthält erweiterte Funktionen zur semantischen Segmentierung von juristischen Texten.
Es wird vom segment_and_prepare_training_data.py verwendet, um intelligentere Segmentierung durchzuführen.
"""

import re
from collections import defaultdict

def get_semantic_embeddings(text_segment):
    """
    Erstellt eine verbesserte semantische Repräsentation eines juristischen Textsegments
    basierend auf Fachterminologie, Gesetzen und strukturellen Elementen.
    
    In einer produktiven Umgebung könnte hier ein fortschrittliches Embedding-Modell verwendet werden.
    
    Args:
        text_segment: Der Textabschnitt, für den eine semantische Repräsentation erstellt werden soll.
        
    Returns:
        Ein Dictionary mit Schlüsselwörtern und deren Gewichtung
    """
    # Stelle sicher, dass ein Textstring übergeben wurde
    if not isinstance(text_segment, str) or not text_segment.strip():
        return {}
        
    # Verbesserte Keyword-basierte Analyse
    semantic_vector = defaultdict(float)
    
    # Juristische Terminologie und deren Gewichtung - erweitert und kategorisiert
    keywords = {
        # Sachverhalt-Terminologie
        'sachverhalt': 6.0, 'tatbestand': 6.0, 'lebenssachverhalt': 6.0, 'fall': 3.0,
        'geschehen': 2.0, 'vorgang': 2.0, 'situation': 2.0, 'ausgangslage': 2.5,
        'umstände': 2.0, 'tatsachen': 2.5, 'ereignis': 2.0, 
        
        # Hauptkategorien juristischer Gutachten
        'frage': 5.0, 'rechtsfrage': 5.5, 'fragestellung': 5.0, 'problematik': 4.5,
        'lösung': 4.5, 'ergebnis': 5.0, 'bewertung': 4.0, 'beurteilung': 4.0,
        'lösungsansatz': 4.0, 'fazit': 5.0, 'schlussfolgerung': 5.0, 'zusammenfassung': 4.5,
        
        # Prozessuale Begriffe
        'klage': 4.5, 'antrag': 4.5, 'verfahren': 4.5, 'instanz': 3.5, 'revision': 4.5,
        'berufung': 4.5, 'beschwerde': 4.5, 'einspruch': 4.5, 'widerspruch': 4.5,
        'kläger': 3.5, 'beklagte': 3.5, 'gericht': 3.5, 'entscheidung': 4.0,
        'zuständigkeit': 4.0, 'frist': 3.5, 'zulässigkeit': 4.5, 'begründetheit': 4.5,
        
        # Normen-Terminologie
        'gesetz': 3.5, 'paragraph': 4.0, 'artikel': 3.5, 'vorschrift': 3.5, 'bestimmung': 3.5,
        'regelung': 3.0, 'norm': 4.0, 'richtlinie': 3.5, 'verordnung': 3.5, 'kodifikation': 3.0,
        'gesetzbuch': 3.5, 'bgb': 4.5, 'stgb': 4.5, 'hgb': 4.5, 'zpo': 4.5, 'stvo': 4.5,
        'erbrecht': 4.0, 'familienrecht': 4.0, 'schuldrecht': 4.0, 'sachenrecht': 4.0,
        
        # Auslegungsmethoden
        'auslegung': 5.0, 'wortlaut': 4.5, 'systematik': 4.5, 'teleologie': 4.5, 'telos': 4.0,
        'historisch': 4.0, 'genese': 4.0, 'zweck': 4.0, 'sinn': 3.5, 'gesetzgebung': 3.5,
        'materialien': 3.5, 'gesetzgeber': 4.0, 'interpretation': 4.0, 'wörtlich': 4.0,
        'grammatikalisch': 4.0, 'systematische': 4.0, 'teleologische': 4.0, 'historische': 4.0,
        
        # Subsumtion
        'subsumtion': 6.0, 'erfüllt': 4.0, 'tatbestandsmerkmal': 5.0, 'voraussetzung': 4.5,
        'merkmal': 3.5, 'prüfung': 4.5, 'anwendung': 4.0, 'tatbestand': 5.0, 'rechtsfolge': 5.0,
        'gegeben': 3.5, 'vorliegend': 4.0, 'einschlägig': 4.0, 'passend': 3.0, 
        'tatbestandlich': 4.5, 'erforderlich': 3.5, 'hinreichend': 3.5,
        
        # Argumentationstechnik und Dogmatik
        'argument': 3.0, 'begründung': 4.0, 'wertung': 3.5, 'abwägung': 4.0, 'dogmatik': 4.5,
        'ansicht': 3.0, 'meinung': 3.0, 'auffassung': 3.0, 'vertretbar': 3.0, 'herrschend': 3.5,
        'minderheit': 3.0, 'streit': 3.5, 'umstritten': 4.0, 'streitig': 4.0, 'eindeutig': 3.5,
        'unstreitig': 3.5, 'unklar': 3.0, 'fraglich': 4.0, 'problematisch': 4.0,
        
        # Rechtsprechung und Literatur
        'rechtsprechung': 4.5, 'bgh': 4.5, 'bundesgerichtshof': 4.5, 'olg': 4.0, 
        'oberlandesgericht': 4.0, 'lg': 3.5, 'ag': 3.5, 'bverfg': 4.5, 'bundesverfassungsgericht': 4.5,
        'literatur': 3.5, 'lehre': 3.5, 'kommentar': 3.5, 'monographie': 3.0, 'aufsatz': 3.0,
        'palandt': 4.0, 'münchener': 4.0, 'staudinger': 4.0, 'larenz': 3.5, 'canaris': 3.5,
        
        # Rechtsfolgen und Rechtsinstitute
        'rechtsfolge': 5.0, 'folge': 3.0, 'konsequenz': 3.5, 'rechtsverhältnis': 4.0,
        'wirkung': 3.0, 'geltung': 3.0, 'rechtswirkung': 4.0, 'rechtsnatur': 4.0,
        'anspruch': 4.5, 'einrede': 4.0, 'einwendung': 4.0, 'schuldverhältnis': 4.0,
        'vertrag': 3.5, 'eigentum': 3.5, 'besitz': 3.5, 'haftung': 4.0, 'schadenersatz': 4.0,
        
        # Gutachtenstruktur
        'gutachten': 5.0, 'stellungnahme': 4.0, 'zwischenergebnis': 4.0, 'gesamtergebnis': 4.5,
        'definitionen': 3.5, 'obersatz': 4.0, 'voraussetzungen': 4.0, 'aufbau': 3.0,
        'gliederung': 3.0, 'struktur': 3.0, 'darstellung': 3.0, 'rechtsschema': 4.0,
        
        # Erweiterte juristische Termini für Gutachten
        'gutachtenstil': 5.0, 'aufbauschema': 4.5, 'syllogismus': 4.0, 'obersatz': 4.5, 
        'untersatz': 4.5, 'schlusssatz': 4.5, 'hauptteil': 4.0, 'hilfsgutachten': 5.0,
        'nebenprüfung': 4.0, 'inzidentprüfung': 4.5, 'exkurs': 3.5, 'prüfungsschema': 4.5,
        'prüfungsreihenfolge': 4.0, 'anspruchsgrundlage': 5.0, 'anspruchsaufbau': 4.5,
        'fallbearbeitung': 4.0, 'fallanalyse': 4.0, 'fallgestaltung': 4.0,
        
        # Abstrakte juristische Bewertungsbegriffe
        'verhältnismäßigkeit': 4.5, 'zumutbar': 4.0, 'angemessen': 4.0, 'erforderlich': 4.0,
        'geeignet': 3.5, 'abwehrrecht': 4.0, 'leistungsrecht': 4.0, 'schutzpflicht': 4.0, 
        'schutzbereich': 4.0, 'kernbereich': 4.0, 'einzelfall': 3.5, 'rechtsgut': 4.0,
        
        # Methodenlehre und juristische Argumentation
        'methodenlehre': 4.5, 'auslegungsmethode': 4.5, 'normenhierarchie': 4.5, 
        'verfassungskonforme': 4.5, 'analogie': 4.5, 'rechtsfortbildung': 4.5, 'lückenfüllung': 4.0,
        'teleologische': 4.0, 'reduktion': 3.5, 'größenschluss': 4.0, 'erst-recht-schluss': 4.0,
        'umkehrschluss': 4.0, 'derogation': 4.0, 'generalklausel': 4.0
    }
    
    # Zähle Vorkommen der Keywords mit Kontextgewichtung
    text_lower = text_segment.lower()
    
    # Normalisiere Leerzeichen und entferne Sonderzeichen für bessere Erkennung
    normalized_text = re.sub(r'\s+', ' ', text_lower)
    
    for keyword, weight in keywords.items():
        # Zähle exakte Wortvorkommnisse (mit Wortgrenzenerkennung)
        exact_matches = len(re.findall(r'\b' + re.escape(keyword) + r'\b', normalized_text))
        
        # Betrachte Komposita zusätzlich mit geringerem Gewicht
        partial_matches = len(re.findall(r'\b\w*' + re.escape(keyword) + r'\w*\b', normalized_text)) - exact_matches
        
        # Gewichte exakte Übereinstimmungen stärker
        if exact_matches > 0:
            semantic_vector[keyword] = exact_matches * weight
        if partial_matches > 0:
            semantic_vector[keyword] += partial_matches * (weight * 0.4)  # Reduktion für Teilübereinstimmungen
    
    # Berücksichtige Positionsgewichtung (Begriffe am Anfang sind oft wichtiger)
    first_paragraph = text_segment.split('\n\n', 1)[0] if '\n\n' in text_segment else text_segment[:500]
    first_paragraph_lower = first_paragraph.lower()
    
    for keyword, weight in keywords.items():
        if keyword in first_paragraph_lower:
            # Verstärke Gewichtung für Schlüsselwörter im ersten Absatz
            semantic_vector[keyword] *= 1.5
    
    # Spezifischere Erkennung von Gesetzesverweisen
    # Reguläre §-Verweise
    bgb_references = len(re.findall(r'§\s*\d+\s*(?:bgb|bürgerliches\s+gesetzbuch)', text_lower))
    if bgb_references > 0:
        semantic_vector['bgb'] = bgb_references * 5.0
    
    stgb_references = len(re.findall(r'§\s*\d+\s*(?:stgb|strafgesetzbuch)', text_lower))
    if stgb_references > 0:
        semantic_vector['stgb'] = stgb_references * 5.0
    
    hgb_references = len(re.findall(r'§\s*\d+\s*(?:hgb|handelsgesetzbuch)', text_lower))
    if hgb_references > 0:
        semantic_vector['hgb'] = hgb_references * 5.0
    
    zpo_references = len(re.findall(r'§\s*\d+\s*(?:zpo|zivilprozessordnung)', text_lower))
    if zpo_references > 0:
        semantic_vector['zpo'] = zpo_references * 5.0
    
    # Allgemeine §-Verweise
    general_norm_references = len(re.findall(r'§\s*\d+', text_segment))
    semantic_vector['gesetzesreferenz'] = general_norm_references * 4.5
    
    # Artikelverweise
    artikel_references = len(re.findall(r'Art(?:ikel)?\.\s*\d+', text_segment))
    semantic_vector['artikelreferenz'] = artikel_references * 4.5
    
    # Erkennung von Strukturelementen
    # Zwischenüberschriften - verschiedene Formate
    roman_numerals = len(re.findall(r'^[IVX]+\.\s+', text_segment, re.MULTILINE))
    semantic_vector['gliederung_römisch'] = roman_numerals * 4.0
    
    numeric_headings = len(re.findall(r'^\d+\.\s+', text_segment, re.MULTILINE))
    semantic_vector['gliederung_numerisch'] = numeric_headings * 3.5
    
    alphabetic_headings = len(re.findall(r'^[A-Z]\.\s+', text_segment, re.MULTILINE))
    semantic_vector['gliederung_alphabetisch'] = alphabetic_headings * 3.5
    
    # Wichtige Wörter in Großbuchstaben (oft Überschriften oder Betonungen)
    capitalized_words = len(re.findall(r'\b[A-Z]{3,}\b', text_segment))
    semantic_vector['betonung'] = capitalized_words * 2.5
    
    # Gutachtenspezifische Erkennungsmerkmale
    legal_opinion_markers = [
        r'(?:im folgenden|im weiteren) ist zu prüfen', 
        r'(?:im ergebnis|zusammenfassend) (?:ist|lässt sich) festzuhalten',
        r'dem ist zu entgegnen', 
        r'fraglich ist, ob', 
        r'zu prüfen ist',
        r'folgende rechtsfragen'
    ]
    
    for marker in legal_opinion_markers:
        if re.search(marker, text_lower):
            semantic_vector['gutachtenstil'] = semantic_vector.get('gutachtenstil', 0) + 4.0
    
    return semantic_vector

def calculate_semantic_similarity(vector1, vector2):
    """
    Berechnet die semantische Ähnlichkeit zwischen zwei semantischen Vektoren
    mit verbesserter Berücksichtigung juristischer Fachbegriffe und Kategorien.
    
    Args:
        vector1: Der erste semantische Vektor (Dictionary)
        vector2: Der zweite semantische Vektor (Dictionary)
        
    Returns:
        Ein Wert zwischen 0 und 1, der die Ähnlichkeit angibt
    """
    # Robustheitsprüfung für die Eingabe
    if not vector1 or not vector2:
        return 0.0
        
    # Stelle sicher, dass beide Vektoren Dictionaries sind
    if not isinstance(vector1, dict) or not isinstance(vector2, dict):
        print(f"Warnung: Nicht-Dictionary-Vektor in calculate_semantic_similarity")
        if not isinstance(vector1, dict):
            vector1 = {}
        if not isinstance(vector2, dict):
            vector2 = {}
        return 0.0  # Keine Ähnlichkeit, wenn keine gültigen Vektoren
    
    # Prüfe, ob die Vektoren Daten enthalten
    if not vector1 or not vector2:
        return 0.0
    
    # Definiere Kategorien für juristische Konzepte, um ähnliche Konzepte zu gruppieren
    # Dies verbessert die Ähnlichkeitserkennung, selbst wenn nicht exakt dieselben Begriffe verwendet werden
    concept_categories = {
        'sachverhalt': ['sachverhalt', 'tatbestand', 'lebenssachverhalt', 'fall', 'geschehen', 'vorgang', 
                       'situation', 'ausgangslage', 'umstände', 'tatsachen', 'ereignis'],
        
        'normenbezug': ['gesetz', 'paragraph', 'artikel', 'vorschrift', 'bestimmung', 'regelung', 'norm', 
                        'richtlinie', 'verordnung', 'kodifikation', 'gesetzbuch', 'gesetzesreferenz', 
                        'artikelreferenz', 'bgb', 'stgb', 'hgb', 'zpo'],
        
        'auslegung': ['auslegung', 'wortlaut', 'systematik', 'teleologie', 'telos', 'historisch', 'genese', 
                     'zweck', 'sinn', 'gesetzgebung', 'materialien', 'gesetzgeber', 'interpretation', 
                     'wörtlich', 'grammatikalisch', 'systematische', 'teleologische', 'historische'],
        
        'subsumtion': ['subsumtion', 'erfüllt', 'tatbestandsmerkmal', 'voraussetzung', 'merkmal', 'prüfung', 
                      'anwendung', 'tatbestand', 'rechtsfolge', 'gegeben', 'vorliegend', 'einschlägig', 
                      'tatbestandlich', 'erforderlich', 'hinreichend'],
        
        'argumentation': ['argument', 'begründung', 'wertung', 'abwägung', 'dogmatik', 'ansicht', 'meinung', 
                         'auffassung', 'vertretbar', 'herrschend', 'minderheit', 'streit', 'umstritten', 
                         'streitig', 'eindeutig', 'unstreitig', 'unklar', 'fraglich', 'problematisch'],
        
        'struktur': ['gliederung', 'gliederung_römisch', 'gliederung_numerisch', 'gliederung_alphabetisch', 
                    'betonung', 'gutachtenstil', 'aufbau', 'struktur', 'darstellung'],
        
        'ergebnis': ['ergebnis', 'fazit', 'schlussfolgerung', 'zusammenfassung', 'zwischenergebnis', 
                    'gesamtergebnis', 'lösung', 'bewertung', 'beurteilung'],
                    
        'gutachtenstil': ['gutachtenstil', 'aufbauschema', 'syllogismus', 'obersatz', 'untersatz', 
                         'schlusssatz', 'hauptteil', 'hilfsgutachten', 'prüfungsschema'],
                         
        'methodenlehre': ['methodenlehre', 'auslegungsmethode', 'normenhierarchie', 'verfassungskonforme', 
                         'analogie', 'rechtsfortbildung', 'lückenfüllung', 'teleologische', 'reduktion']
    }
    
    # Erzeuge einen Kategorie-zu-Term-Mapping
    term_to_category = {}
    for category, terms in concept_categories.items():
        for term in terms:
            term_to_category[term] = category
    
    # Berechne kategoriebasierte Ähnlichkeit
    category_scores = {}
    
    # Aggregiere Termgewichte pro Kategorie mit verbesserter Fehlerbehandlung
    for vector, is_first in [(vector1, True), (vector2, False)]:
        for term, weight in vector.items():
            if not isinstance(weight, (int, float)):
                # Wenn weight kein numerischer Wert ist, setze einen Standardwert
                weight = 1.0
                
            category = term_to_category.get(term, 'other')
            
            # Robustere Initialisierung mit expliziter Fehlerbehandlung
            try:
                if is_first:
                    if category not in category_scores:
                        category_scores[category] = [0, 0]
                    category_scores[category][0] += weight
                else:
                    if category in category_scores:
                        category_scores[category][1] += weight
                    else:
                        category_scores[category] = [0, weight]
            except Exception as e:
                print(f"Fehler bei der Ähnlichkeitsberechnung für Term '{term}': {str(e)}")
                # Erstelle einen neuen Eintrag für diese Kategorie
                category_scores[category] = [weight if is_first else 0, 0 if is_first else weight]
    
    # Berechne die Ähnlichkeit basierend auf Kategoriescores
    category_min_sum = 0
    category_total_sum = 0
    
    for cat_scores in category_scores.values():
        # Sicherstellen, dass beide Vektoren Werte für diese Kategorie haben
        if cat_scores[0] > 0 and cat_scores[1] > 0:
            category_min_sum += min(cat_scores[0], cat_scores[1])
        category_total_sum += cat_scores[0] + cat_scores[1]
    
    # Berechne auch direkte Term-Übereinstimmungen für höhere Präzision
    common_keys = set(vector1.keys()) & set(vector2.keys())
    term_min_sum = 0
    
    # Fehlerbehandlung für die term_min_sum-Berechnung
    for key in common_keys:
        try:
            v1 = vector1[key]
            v2 = vector2[key]
            
            # Stelle sicher, dass wir numerische Werte haben
            if not isinstance(v1, (int, float)):
                v1 = 1.0
            if not isinstance(v2, (int, float)):
                v2 = 1.0
                
            term_min_sum += min(v1, v2)
        except Exception as e:
            print(f"Fehler bei direkter Termähnlichkeitsberechnung für '{key}': {str(e)}")
            # Überspringe diesen Term bei Fehlern
            continue
    
    term_total_sum = sum(vector1.values()) + sum(vector2.values())
    
    # Gewichtete Kombination aus kategoriebasierter und direkter Ähnlichkeit
    if category_total_sum == 0 or term_total_sum == 0:
        return 0.0
    
    category_similarity = (2 * category_min_sum) / category_total_sum if category_total_sum > 0 else 0
    term_similarity = (2 * term_min_sum) / term_total_sum if term_total_sum > 0 else 0
    
    # Kombiniere beide Ähnlichkeitsmaße mit Gewichtung
    # Erhöhe die Gewichtung der direkten Übereinstimmungen für höhere Präzision
    combined_similarity = (0.7 * term_similarity) + (0.3 * category_similarity)
    
    return combined_similarity

def detect_logical_segments(text, min_segment_length=400, similarity_threshold=0.25, max_segment_length=4000):
    """
    Teilt einen Text in logische Segmente basierend auf Absätzen und semantischer Ähnlichkeit.
    
    Args:
        text: Der zu segmentierende Text
        min_segment_length: Minimale Länge eines Segments in Zeichen
        similarity_threshold: Schwellenwert für die semantische Ähnlichkeit
        max_segment_length: Maximale Länge eines Segments in Zeichen
        
    Returns:
        Eine Liste von Textsegmenten
    """
    # Liste der Schlüsselwörter, die typischerweise einen neuen Abschnitt in juristischen Texten einleiten
    legal_section_markers = [
        # Allgemeine Übergangsmarker
        r"\b[Ii]m [Ff]olgenden\b", r"\b[Zz]unächst\b", r"\b[Ii]m [Ee]rgebnis\b", r"\b[Ff]erner\b",
        r"\b[Dd]es [Ww]eiteren\b", r"\b[Ii]m [Üü]brigen\b", r"\b[Dd]arüber hinaus\b",
        r"\b[Ss]chließlich\b", r"\b[Zz]usammenfassend\b", r"\b[Aa]bschließend\b",
        r"\b[Ee]ine andere [Ff]rage\b", r"\b[Zz]u [Bb]eachten ist\b", r"\b[Hh]iergegen\b",
        r"\b[Aa]nders als\b", r"\b[Ii]m [Gg]egensatz\b", r"\b[Zz]u [Pp]rüfen ist\b",
        r"\b[Ee]s bleibt [Ff]estzuhalten\b", r"\b[Ee]s ist noch [Aa]nzumerken\b",
        r"\b[Aa]us den genannten [Gg]ründen\b", r"\b[Mm]aßgeblich ist\b",
        
        # Ergänzte Marker für spezifische Strukturen in Rechtsgutachten
        r"\b[Dd]ie [Pp]rüfung ergibt\b", r"\b[Dd]ie [Bb]eurteilung\b", r"\b[Ii]n [Bb]ezug auf\b",
        r"\b[Nn]unmehr\b", r"\b[Dd]emnach\b", r"\b[Ff]olglich\b", r"\b[Dd]araus ergibt sich\b",
        r"\b[Ee]s ist davon auszugehen\b", r"\b[Ee]ine [Aa]usnahme\b", r"\b[Ii]m [Gg]rundsatz\b",
        r"\b[Gg]rundsätzlich\b", r"\b[Ww]eiterhin\b", r"\b[Aa]llerdings\b", r"\b[Jj]edoch\b",
        r"\b[Dd]emzufolge\b", r"\b[Dd]iesem [Gg]rundsatz folgend\b",
        r"\b[Uu]nter [Bb]erücksichtigung\b", r"\b[Ii]n [Aa]nbetracht\b",
        
        # Gutachtenspezifische strukturelle Marker
        r"\b[Dd]ie [Rr]echtsfolge\b", r"\b[Dd]er [Tt]atbestand\b", r"\b[Dd]ie [Tt]atbestandsmerkmale\b",
        r"\b[Ff]raglich ist [Ff]olgendes\b", r"\b[Ii]m [Mm]ittelpunkt steht\b", r"\b[Zz]entral ist\b",
        r"\b[Dd]abei ist zu beachten\b", r"\b[Aa]us rechtlicher [Ss]icht\b", r"\b[Dd]ies führt zu\b",
        r"\b[Ii]n der [Ss]ache gilt\b", r"\b[Rr]echtlich gesehen\b",
        
        # Fortgeschrittene normbasierte Marker
        r"\b[Dd]er Anwendungsbereich des\b", r"\b[Dd]ie [Vv]oraussetzungen des\b", 
        r"\b[Nn]ach ständiger [Rr]echtsprechung\b", r"\b[Dd]ie herrschende [Mm]einung\b",
        r"\b[Ii]m [Ss]chrifttum wird vertreten\b", r"\b[Nn]ach der [Gg]esetzesbegründung\b"
    ]

    # Teile Text in Absätze auf - verbesserte Methode, die Absatztrennungen besser erkennt
    paragraphs = [p.strip() for p in re.split(r'(\n\s*\n|\n\s{3,}\n)', text) if p.strip()]
    
    if not paragraphs:
        return [text] if text.strip() else []
    
    # Zu kurze Texte nicht weiter segmentieren
    if len(text) < min_segment_length * 2:
        return [text]
    
    # Berechne semantische Vektoren für jeden Absatz
    paragraph_vectors = []
    paragraph_text_lengths = []  # Speichere auch die Länge der Absätze für bessere Entscheidungen
    
    for p in paragraphs:
        try:
            # Versuche den semantischen Vektor zu berechnen, mit erweiterter Fehlerbehandlung
            vector = get_semantic_embeddings(p)
            if not isinstance(vector, dict):
                vector = {}  # Fallback falls kein Dictionary zurückkommt
                print(f"Warnung: get_semantic_embeddings gab keinen Dictionary für einen Absatz zurück")
            
            # Speichere Vektor und Textlänge
            paragraph_vectors.append(vector)
            paragraph_text_lengths.append(len(p))
        except Exception as e:
            # Bei Fehlern, leeres Dictionary als Fallback mit zusätzlicher Diagnose
            print(f"Fehler bei Vektorgenerierung: {str(e)}")
            paragraph_vectors.append({})
            paragraph_text_lengths.append(len(p))
            
    # Überprüfe jeden Absatz auf Übergangsmarker mit verbesserter Erkennung
    transition_markers = [False] * len(paragraphs)
    context_importance = [1.0] * len(paragraphs)  # Gewichtungsfaktor für die Wichtigkeit der Absätze
    
    for i, paragraph in enumerate(paragraphs):
        # Überprüfe, ob der Absatz mit einem juristischen Übergangsmarker beginnt
        if any(re.search(pattern, paragraph[:max(100, len(paragraph) // 3)]) for pattern in legal_section_markers):
            transition_markers[i] = True
            context_importance[i] = 1.5  # Erhöhe die Wichtigkeit von Übergangsparagraphen
        
        # Erkenne Überschriften oder besonders hervorgehobenen Text (z.B. durch Großbuchstaben)
        if i > 0 and len(paragraph) < 200 and (paragraph.isupper() or re.match(r'^[A-Z][a-z]*(\s+[A-Z][a-z]*)+$', paragraph)):
            transition_markers[i] = True
            context_importance[i] = 2.0  # Noch höheres Gewicht für potenzielle Überschriften
        
        # Erkenne Absätze mit vielen juristischen Schlüsselbegriffen
        legal_term_count = sum(1 for marker in ['§', 'gem.', 'gemäß', 'nach', 'laut', 'entsprechend', 'BGH', 'BVerfG'] 
                              if marker.lower() in paragraph.lower())
        if legal_term_count >= 3:
            context_importance[i] = min(2.0, context_importance[i] + 0.3)  # Erhöhe Wichtigkeit, aber maximal 2.0
    
    # Gruppiere Absätze in Segmente basierend auf semantischer Ähnlichkeit und Übergangsmarkern
    segments = []
    current_segment = [paragraphs[0]]
    current_vector = paragraph_vectors[0].copy()  # Wichtig: Kopiere den Vektor, um ihn zu isolieren
    current_segment_len = len(paragraphs[0])
    
    for i in range(1, len(paragraphs)):
        # Berechne die semantische Ähnlichkeit mit erhöhter Robustheit
        try:
            similarity = calculate_semantic_similarity(current_vector, paragraph_vectors[i])
        except Exception as e:
            print(f"Fehler bei Ähnlichkeitsberechnung: {str(e)}")
            similarity = 0.0  # Fallback: Betrachte als unähnlich bei Fehlern
        
        new_segment_len = current_segment_len + len(paragraphs[i])
        
        # Dynamischer Schwellenwert basierend auf Kontext
        dynamic_threshold = similarity_threshold
        if transition_markers[i]:
            dynamic_threshold *= 1.5  # Erhöhe Schwellenwert bei expliziten Übergangsmarkern
        
        # Berücksichtige die Länge der Absätze - kürzere Absätze können eher zusammengeführt werden
        if paragraph_text_lengths[i] < 200:
            dynamic_threshold *= 0.8  # Reduziere Schwellenwert für kurze Absätze
        
        # Beginne ein neues Segment, wenn:
        # 1. Ein Übergangsmarker gefunden wurde, oder
        # 2. Die Ähnlichkeit unter dem Schwellenwert liegt und das aktuelle Segment lang genug ist, oder
        # 3. Das aktuelle Segment würde zu lang werden
        if (transition_markers[i] or 
           (similarity < dynamic_threshold and current_segment_len >= min_segment_length) or
           (new_segment_len > max_segment_length and current_segment_len >= min_segment_length)):
            segments.append('\n\n'.join(current_segment))
            current_segment = [paragraphs[i]]
            current_vector = paragraph_vectors[i].copy()  # Isolierter Vektor für das neue Segment
            current_segment_len = len(paragraphs[i])
        else:
            # Füge Absatz zum aktuellen Segment hinzu
            current_segment.append(paragraphs[i])
            # Aktualisiere den semantischen Vektor des Segments mit Gewichtung und Wichtigkeit
            # Neue Absätze erhalten mehr Gewicht, um thematische Übergänge besser zu erkennen
            weight = 1.2 * context_importance[i]  # Gewichtung basierend auf Kontextwichtigkeit
            
            # Sichere Vektor-Kombination, die mit der neuen Sicherheitsebene robust ist
            if isinstance(paragraph_vectors[i], dict):
                for key, value in paragraph_vectors[i].items():
                    if key in current_vector:
                        current_vector[key] = current_vector[key] + (value * weight)
                    else:
                        current_vector[key] = value * weight
            
            current_segment_len += len(paragraphs[i])
    
    # Füge das letzte Segment hinzu
    if current_segment:
        segments.append('\n\n'.join(current_segment))
    
    # Verbesserte Strategie für das Zusammenführen kurzer Segmente
    final_segments = []
    i = 0
    
    # Erste Zusammenführung basierend auf Minimallänge
    while i < len(segments):
        if len(segments[i]) < min_segment_length and i + 1 < len(segments):
            # Prüfe thematische Ähnlichkeit für intelligentere Zusammenführung
            if i > 0:
                # Versuche die Ähnlichkeit mit dem vorherigen und dem nächsten Segment zu vergleichen
                prev_segment_vector = get_semantic_embeddings(segments[i-1][:1000])
                current_segment_vector = get_semantic_embeddings(segments[i][:1000])
                next_segment_vector = get_semantic_embeddings(segments[i+1][:1000])
                
                # Stelle sicher, dass alle Vektoren Dictionaries sind
                if not isinstance(prev_segment_vector, dict): prev_segment_vector = {}
                if not isinstance(current_segment_vector, dict): current_segment_vector = {}
                if not isinstance(next_segment_vector, dict): next_segment_vector = {}
                
                try:
                    similarity_with_prev = calculate_semantic_similarity(current_segment_vector, prev_segment_vector)
                    similarity_with_next = calculate_semantic_similarity(current_segment_vector, next_segment_vector)
                    
                    # Füge das Segment zum ähnlicheren Nachbarn hinzu
                    if similarity_with_prev > similarity_with_next:
                        # Mit vorherigem Segment zusammenführen
                        merged_segment = final_segments.pop() + '\n\n' + segments[i]
                        final_segments.append(merged_segment)
                        i += 1
                    else:
                        # Mit nächstem Segment zusammenführen
                        merged_segment = segments[i] + '\n\n' + segments[i+1]
                        final_segments.append(merged_segment)
                        i += 2
                except Exception as e:
                    # Bei Fehlern in der Ähnlichkeitsberechnung, führe mit dem nächsten zusammen als Fallback
                    print(f"Fehler bei semantischer Ähnlichkeitsberechnung für Segmentzusammenführung: {str(e)}")
                    merged_segment = segments[i] + '\n\n' + segments[i+1]
                    final_segments.append(merged_segment)
                    i += 2
            else:
                # Wenn es kein vorheriges Segment gibt, füge mit dem nächsten zusammen
                merged_segment = segments[i] + '\n\n' + segments[i+1]
                final_segments.append(merged_segment)
                i += 2
        else:
            final_segments.append(segments[i])
            i += 1
    
    # Zweite Phase: Optimierte Zusammenführung von überlappenden Inhalten in benachbarten Segmenten
    optimized_segments = []
    i = 0
    while i < len(final_segments):
        current_segment = final_segments[i]
        
        if i + 1 < len(final_segments):
            next_segment = final_segments[i+1]
            
            # Prüfe auf signifikante gemeinsame Phrasen (3-5 Wörter), die auf überlappende Inhalte hindeuten
            current_phrases = set([' '.join(current_segment.split()[j:j+4]) 
                                  for j in range(len(current_segment.split()) - 4)])
            next_phrases = set([' '.join(next_segment.split()[j:j+4]) 
                               for j in range(min(20, len(next_segment.split()) - 4))])  # Prüfe nur Anfang des nächsten Segments
            
            common_phrases = current_phrases.intersection(next_phrases)
            
            # Wenn signifikante Überlappungen gefunden werden und die Segmente nicht zu lang werden
            if len(common_phrases) > 2 and len(current_segment) + len(next_segment) < max_segment_length * 1.2:
                # Finde Position der ersten Überlappung im nächsten Segment
                for phrase in common_phrases:
                    if phrase in next_segment[:200]:  # Nur am Anfang suchen
                        pos = next_segment.find(phrase)
                        if pos > 0:
                            # Entferne überlappenden Teil aus dem nächsten Segment
                            merged = current_segment + '\n\n' + next_segment[pos + len(phrase):]
                            optimized_segments.append(merged)
                            i += 2
                            break
                else:
                    # Keine geeignete Überlappung gefunden
                    optimized_segments.append(current_segment)
                    i += 1
            else:
                optimized_segments.append(current_segment)
                i += 1
        else:
            # Letztes Segment
            optimized_segments.append(current_segment)
            i += 1
    
    # Final: Überprüfe auf zu lange Segmente und teile sie wenn nötig
    extra_long_segments = []
    for segment in optimized_segments:
        if len(segment) > max_segment_length * 1.5:  # Besonders lange Segmente
            # Teile das Segment an Satzgrenzen
            sentences = re.split(r'(?<=[.!?])\s+', segment)
            current_chunk = ""
            for sentence in sentences:
                if len(current_chunk) + len(sentence) <= max_segment_length:
                    current_chunk += sentence + " "
                else:
                    if current_chunk:
                        extra_long_segments.append(current_chunk.strip())
                    current_chunk = sentence + " "
            if current_chunk:
                extra_long_segments.append(current_chunk.strip())
        else:
            extra_long_segments.append(segment)
    
    return extra_long_segments

def detect_topic_transitions(text, transition_patterns=None):
    """
    Erkennt thematische Übergänge im Text basierend auf bestimmten Signalphrasen.
    
    Args:
        text: Der zu analysierende Text
        transition_patterns: Regex-Muster für Übergangssignale
        
    Returns:
        Eine Liste von Indizes, an denen Themenübergänge identifiziert wurden
    """
    if transition_patterns is None:
        transition_patterns = [
            # Allgemeine Übergangssignale
            r'Im Folgenden',
            r'Zunächst',
            r'Anschließend',
            r'Abschließend',
            r'Zusammenfassend',
            r'Es ist festzuhalten',
            r'Im Ergebnis',
            r'Daraus folgt',
            r'Anders als',
            r'Im Gegensatz dazu',
            r'Davon ausgehend',
            r'Hiervon ausgehend',
            r'Weiterhin ist zu beachten',
            r'Deshalb',
            r'Dennoch',
            r'Darüber hinaus',
            r'Was .* betrifft',
            r'In Bezug auf',
            
            # Juristische Fachsprache und Gliederungssignale
            r'Im Rahmen der Prüfung',
            r'Fraglich ist',
            r'Zu prüfen ist',
            r'Bei der Auslegung',
            r'Nach der Rechtsprechung',
            r'Nach h\.M\.',
            r'Nach herrschender Meinung',
            r'Umstritten ist',
            r'Die Subsumtion ergibt',
            r'Im vorliegenden Fall',
            r'Streitig ist',
            r'Aus rechtlicher Sicht',
            r'Materiell-rechtlich',
            r'Formell-rechtlich',
            r'Prozessual betrachtet',
            
            # Einleitung neuer Argumentationsketten
            r'Als Erstes',
            r'Als Zweites',
            r'Als Nächstes',
            r'Zum einen',
            r'Zum anderen',
            r'Einerseits',
            r'Andererseits',
            r'Vielmehr',
            r'Insbesondere',
            r'Problematisch ist',
            r'Demgegenüber',
            r'Somit gilt',
            r'Letztendlich',
            r'Schließlich',
            
            # Normspezifische Überleitungen
            r'Die Voraussetzungen des § \d+',
            r'Nach § \d+ (?:[A-Za-z]+)',
            r'Gemäß § \d+ (?:[A-Za-z]+)',
            r'Laut § \d+ (?:[A-Za-z]+)',
            r'Die Tatbestandsvoraussetzungen',
            r'Als Rechtsfolge ergibt sich',
            r'Die Anspruchsgrundlage',
            r'Die gesetzliche Grundlage',
        ]
    
    transitions = []
    for pattern in transition_patterns:
        for match in re.finditer(pattern, text, re.IGNORECASE):
            # Finde den Satzanfang für bessere Segmentierung
            sentence_start = text.rfind('.', 0, match.start())
            if sentence_start == -1:
                sentence_start = 0
            else:
                sentence_start += 1  # Überspringe den Punkt
            
            # Vermeide zu nah beieinander liegende Übergänge, aber berücksichtige wichtige juristische Marker
            is_important_marker = any(imp in pattern.lower() for imp in ['§', 'prüfung', 'fraglich', 'tatbestand', 'rechtsprechung'])
            min_distance = 30 if is_important_marker else 100
            
            if not any(abs(t - sentence_start) < min_distance for t in transitions):
                transitions.append(sentence_start)
                
                # Suche auch nach dem Ende des kompletten Satzes, um den Kontext besser zu erhalten
                sentence_end = text.find('.', match.end())
                if sentence_end != -1 and not any(abs(t - sentence_end) < min_distance for t in transitions):
                    transitions.append(sentence_end + 1)
    
    # Sortiere die Übergänge nach Position
    return sorted(transitions)

def enhanced_segment_text(text_content):
    """
    Erweiterte Segmentierung eines Gutachtentextes mit Kombination aus Struktur- und semantischer Analyse.
    Erkennt juristische Struktur und Schlüsselwörter, um bessere Segmente zu erzeugen.
    
    Args:
        text_content: Der zu segmentierende Gutachtentext
        
    Returns:
        Eine Liste von Tupeln (heading, segment_content)
    """
    if not text_content or not text_content.strip():
        return []
    
    # Importiere die bestehende Segmentierungsfunktion
    from segment_and_prepare_training_data import segment_text as basic_segment_text
    
    # Juristische Schlüsselwörter für die Klassifizierung von Segmenten
    legal_keywords = {
        'sachverhalt': ["sachverhalt", "tatbestand", "umstände", "ereignis", "vorliegend", "fakten", 
                      "ausgangssituation", "fallgeschehen", "tatsachenlage", "sachgegebenheiten",
                      "tatsachenverhalt", "tatsächliche lage", "gegebener sachverhalt", "sachlich"],
                      
        'rechtsfrage': ["frage", "fragestellung", "zu klären", "rechtsfrage", "umstritten", "fraglich", 
                       "problematisch", "zu prüfen", "problematik", "strittig", "unklar", 
                       "ungeklärt", "aufklärungsbedürftig", "streitpunkt", "central de facto", 
                       "im mittelpunkt der betrachtung", "zentrales problem", "zentrale frage", 
                       "hauptfrage", "kernproblematik"],
                       
        'rechtliche_wuerdigung': ["rechtslage", "rechtliche würdigung", "prüfung", "beurteilung", 
                                "nach auffassung", "rechtlich", "gutachterlich", "analyse", "dogmatisch", 
                                "im ergebnis", "im folgenden", "juristisch", "normativ",
                                "von rechts wegen", "rechtsansicht", "rechtsauffassung", 
                                "unter juristischen gesichtspunkten", "rechtliche beurteilung",
                                "juristische bewertung", "zu würdigen", "rechtlich zu bewerten"],
                                
        'subsumtion': ["subsumtion", "anwendung", "unter die norm", "tatbestandsmerkmal", "voraussetzungen", 
                     "erfüllt", "gegeben", "unterfallen", "entsprechen", "zutreffen", "angewendet",
                     "zuordnung", "einordnung", "überprüfung", "fall unter", "einordnung des falles",
                     "einschlägig", "anwendbar", "herangezogen", "unterfällt", "zu fassen unter"],
                     
        'ergebnis': ["ergebnis", "fazit", "zusammenfassend", "resultat", "schlussfolgerung", "im ergebnis", 
                   "abschließend", "schluss", "quintessenz", "endgültig", "schließlich", "abschließende betrachtung",
                   "zusammenfassende bewertung", "letztendlich", "somit", "demnach", "folglich", 
                   "daraus ergibt sich", "im endeffekt", "im gesamtergebnis", "abschließende beurteilung"],
                   
        'gesetzesnorm': ["nach §", "gemäß §", "im sinne des §", "anwendung des §", "paragraph", "gesetzgeber", 
                       "bgb", "stgb", "hgb", "zpo", "normierung", "vorschrift", "regelung", "verordnung",
                       "gesetzliche grundlage", "rechtsgrundlage", "nach der vorschrift", "gesetzesmaterialien",
                       "rechtsnorm", "normtext", "wortlaut der vorschrift", "gesetzestext"]
    }
    
    # Versuche zuerst, mit der vorhandenen Segmentierungslogik zu arbeiten
    basic_segments = basic_segment_text(text_content)
    
    # Prüfe, ob die grundlegende Segmentierung brauchbare Ergebnisse liefert
    if basic_segments and len(basic_segments) > 1:
        enhanced_segments = []
        
        for heading, content in basic_segments:
            heading_lower = heading.lower()
            
            # Spezielle Behandlung für bestimmte Arten von Segmenten
            if any(keyword in heading_lower for keyword in ["sachverhalt", "frage", "tenor", "leitsatz", "tenor"]):
                # Diese Segmente werden in der Regel nicht weiter unterteilt
                enhanced_segments.append((heading, content))
                continue
                
            # Für kurze Segmente oder solche mit präzisen Überschriften: keine weitere Aufteilung
            if len(content) < 1500 or heading_lower not in ["gesamter text", "rechtslage", "rechtliche würdigung", "gutachten"]:
                enhanced_segments.append((heading, content))
                continue
            
            # Für längere unspezifische Segmente: versuche semantische Segmentierung
            logical_subsegments = detect_logical_segments(content, min_segment_length=500, similarity_threshold=0.25, max_segment_length=4000)
            
            if len(logical_subsegments) <= 1:
                # Wenn keine weitere Aufteilung möglich ist, behalte das Originalsegment
                enhanced_segments.append((heading, content))
            else:
                # Erstelle aussagekräftigere Überschriften für die Untersegmente
                for i, subsegment in enumerate(logical_subsegments, 1):
                    # Analysiere den Inhalt des Segments für eine themenbezogene Überschrift
                    semantic_vector = get_semantic_embeddings(subsegment[:1000])  # Nutze nur den Anfang zur Analyse
                    
                    # Stelle sicher, dass semantic_vector ein Dictionary ist
                    if not isinstance(semantic_vector, dict):
                        semantic_vector = {}  # Fallback, wenn kein Dictionary
                    
                    # Kategorisiere das Subsegment anhand der juristischen Schlüsselwörter
                    segment_type = "Allgemein"
                    segment_score = 0
                    
                    for category, keywords in legal_keywords.items():
                        category_score = sum(semantic_vector.get(keyword, 0) for keyword in keywords)
                        if category_score > segment_score:
                            segment_score = category_score
                            if category == 'sachverhalt':
                                segment_type = "Sachverhalt"
                            elif category == 'rechtsfrage':
                                segment_type = "Rechtsfrage"
                            elif category == 'rechtliche_wuerdigung':
                                segment_type = "Rechtliche Würdigung"
                            elif category == 'subsumtion':
                                segment_type = "Subsumtion"
                            elif category == 'ergebnis':
                                segment_type = "Ergebnis"
                            elif category == 'gesetzesnorm':
                                segment_type = "Normprüfung"
                    
                    # Erweiterte Erkennung: Prüfe anhand spezifischer Muster im ersten Absatz
                    first_paragraph = subsegment.split('\n\n')[0] if '\n\n' in subsegment else subsegment[:500]
                    first_paragraph_lower = first_paragraph.lower()
                    
                    # Verfeinerte Erkennung durch kontextuelle Muster im ersten Absatz
                    if segment_type == "Allgemein":
                        if re.search(r'(?:im folgenden|zunächst|dabei) (?:ist|wird|soll|möchte ich) (?:zu )?(?:prüfen|untersuchen|klären|erörtern)', first_paragraph_lower):
                            segment_type = "Prüfungsbeginn"
                        elif re.search(r'(?:im ergebnis|zusammenfassend|abschließend|daher|somit|demnach) (?:ist|lässt sich|kann) (?:fest(?:zu)?halten|festzustellen|feststellen|sagen|konstatieren)', first_paragraph_lower):
                            segment_type = "Ergebnis"
                        elif re.search(r'(?:fraglich|problematisch|umstritten|zu klären) ist(?: (?:dabei|hier|nunmehr|also|jedoch|demnach))?, ob', first_paragraph_lower):
                            segment_type = "Rechtsfrage"
                        elif re.search(r'(?:es gilt|zu prüfen ist|zu untersuchen ist|geprüft werden muss|geklärt werden muss)', first_paragraph_lower):
                            segment_type = "Prüfungsschritt"
                    
                    # Füge einen Gesetzeskontext hinzu, wenn erkennbar
                    law_references = re.findall(r'§\s*\d+[a-z]?\s*(?:[A-Za-zäöüÄÖÜß]+)', subsegment[:500])
                    law_context = ""
                    if law_references:
                        unique_laws = set()
                        for law in law_references[:3]:  # Max. 3 Gesetze anzeigen
                            unique_laws.add(law.strip())
                        if unique_laws:
                            law_context = f" ({', '.join(unique_laws)})"
                    
                    # Erkenne Gutachtenkonstellationen durch bestimmte Indikatoren
                    constellation_indicators = {
                        "Vertrag": ["vertrag", "vertragsschluss", "vertragspartei", "vertragsrecht", "vertragsklausel"],
                        "Delikt": ["delikt", "schädigung", "schadensersatz", "unerlaubte handlung", "schaden"],
                        "Verfassungsrecht": ["grundrecht", "verfassung", "verfassungsmäßig", "grundgesetz", "staatsgewalt"],
                        "Strafrecht": ["strafbar", "täter", "tat", "vorsatz", "schuld", "qualifikation", "versuch"],
                        "Verwaltungsrecht": ["verwaltungsakt", "behörde", "ermessen", "verwaltungsverfahren"]
                    }
                    
                    constellation = ""
                    for const_name, indicators in constellation_indicators.items():
                        if any(ind in first_paragraph_lower for ind in indicators):
                            constellation = f" - {const_name}"
                            break
                    
                    # Erstelle die Überschrift
                    if segment_type != "Allgemein":
                        subheading = f"{heading} - {segment_type}{constellation}{law_context} [{i}/{len(logical_subsegments)}]"
                    else:
                        subheading = f"{heading} - Teil {i}/{len(logical_subsegments)}{constellation}{law_context}"
                    
                    enhanced_segments.append((subheading, subsegment))
        
        return enhanced_segments
    
    # Wenn keine strukturelle Segmentierung möglich war, versuche semantische Segmentierung
    logical_segments = detect_logical_segments(text_content, min_segment_length=800, similarity_threshold=0.3, max_segment_length=5000)
    
    if len(logical_segments) <= 1:
        # Wenn keine semantische Segmentierung möglich war, prüfe nochmal thematische Übergänge
        transitions = detect_topic_transitions(text_content)
        
        if transitions:
            # Erstelle Segmente an den thematischen Übergängen
            transition_segments = []
            last_pos = 0
            
            for pos in transitions:
                if pos - last_pos > 500:  # Vermeide zu kurze Segmente
                    segment_text = text_content[last_pos:pos].strip()
                    if segment_text:
                        transition_segments.append(segment_text)
                    last_pos = pos
            
            # Füge den letzten Teil hinzu
            if last_pos < len(text_content) and len(text_content) - last_pos > 500:
                segment_text = text_content[last_pos:].strip()
                if segment_text:
                    transition_segments.append(segment_text)
            
            if len(transition_segments) > 1:
                logical_segments = transition_segments
            else:
                # Keine brauchbaren Übergänge gefunden, gib den Gesamttext zurück
                return [("Gesamter Text", text_content.strip())]
        else:
            # Keine Segmentierung möglich, gib den Gesamttext zurück
            return [("Gesamter Text", text_content.strip())]
    
    # Benenne die semantischen Segmente mit juristisch sinnvollen Kategorien
    result_segments = []
    standard_parts = ["Sachverhalt", "Rechtliche Würdigung", "Ergebnis"]
    
    # Je nach Anzahl der Segmente wähle unterschiedliche Benennungsstrategien
    if len(logical_segments) <= 3:
        # Wenige Segmente: Verwende Standardbenennungen nach Gutachtenaufbau
        # Verbesserte Kategorisierung für die Standardteile
        segment_types = []
        
        for i, segment in enumerate(logical_segments):
            segment_start = segment[:min(len(segment), 1000)]
            semantic_vector = get_semantic_embeddings(segment_start)
            
            # Ermittle den Typ dieses Segments
            segment_score = {}
            for category, keywords in legal_keywords.items():
                segment_score[category] = sum(semantic_vector.get(keyword, 0) for keyword in keywords)
            
            # Finde die beste Kategorie
            best_category = max(segment_score.items(), key=lambda x: x[1]) if segment_score else ("unknown", 0)
            segment_types.append(best_category[0])
        
        # Sortierung entsprechend der typischen Gutachtenreihenfolge
        expected_order = ['sachverhalt', 'rechtsfrage', 'rechtliche_wuerdigung', 'subsumtion', 'ergebnis']
        
        # Bei 2 Segmenten: Vereinfachte Kategorisierung (Sachverhalt + Rest oder Rest + Ergebnis)
        if len(logical_segments) == 2:
            if 'sachverhalt' in segment_types:
                sachverhalt_idx = segment_types.index('sachverhalt')
                other_idx = 1 - sachverhalt_idx  # Der andere Index (0 oder 1)
                result_segments.append(("Sachverhalt", logical_segments[sachverhalt_idx]))
                result_segments.append(("Rechtliche Würdigung und Ergebnis", logical_segments[other_idx]))
            elif 'ergebnis' in segment_types:
                ergebnis_idx = segment_types.index('ergebnis')
                other_idx = 1 - ergebnis_idx  # Der andere Index (0 oder 1)
                result_segments.append(("Rechtsfrage und Rechtliche Würdigung", logical_segments[other_idx]))
                result_segments.append(("Ergebnis", logical_segments[ergebnis_idx]))
            else:
                # Fallback - Standard-Benennung
                for i, segment in enumerate(logical_segments):
                    result_segments.append((standard_parts[i], segment))
        
        # Bei 3 Segmenten: Versuch einer klassischen Gutachtenstruktur
        elif len(logical_segments) == 3:
            # Versuche die Segmente in eine logische Reihenfolge zu bringen
            ordered_indices = []
            remaining_indices = list(range(len(logical_segments)))
            
            # Finde für jede erwartete Kategorie den besten Match
            for expected_cat in expected_order:
                if not remaining_indices:
                    break
                    
                best_match_idx = None
                best_match_score = -1
                
                for idx in remaining_indices:
                    if segment_types[idx] == expected_cat:
                        # Direkte Übereinstimmung
                        best_match_idx = idx
                        break
                    elif best_match_score < segment_score[expected_cat]:
                        best_match_idx = idx
                        best_match_score = segment_score[expected_cat]
                
                if best_match_idx is not None:
                    ordered_indices.append(best_match_idx)
                    remaining_indices.remove(best_match_idx)
            
            # Füge verbleibende Indices hinzu
            ordered_indices.extend(remaining_indices)
            
            # Erstelle die sortierten Segmente
            labels = ["Sachverhalt", "Rechtsfrage", "Rechtliche Würdigung"]
            for i, idx in enumerate(ordered_indices[:3]):  # Max. 3 Segmente
                result_segments.append((labels[i], logical_segments[idx]))
        
        else:
            # Bei einem Segment: Gesamttext
            result_segments.append(("Vollständiges Gutachten", logical_segments[0]))
    
    else:
        # Mehrere Segmente: Verwende semantische Analyse für aussagekräftigere Bezeichnungen
        for i, segment in enumerate(logical_segments, 1):
            # Analysiere Segment zur Kategorisierung
            segment_start = segment[:min(len(segment), 1000)]  # Verwende den Anfang des Segments
            semantic_vector = get_semantic_embeddings(segment_start)
            
            # Bestimme Segmenttyp mit verbesserter Analyse
            segment_type = "Allgemein"
            segment_score = 0
            
            # Tiefere Analyse mit kontextueller Gewichtung
            for category, keywords in legal_keywords.items():
                # Gewichtete Punktzahl berechnen, die stärkere Gewichtung für die ersten 200 Zeichen gibt
                intro_text = segment_start[:200].lower()
                base_score = sum(semantic_vector.get(keyword, 0) for keyword in keywords)
                
                # Zusatzpunkte für Schlüsselwörter im Einleitungstext
                bonus_score = sum(3.0 for keyword in keywords if keyword in intro_text)
                
                category_score = base_score + bonus_score
                
                if category_score > segment_score:
                    segment_score = category_score
                    if category == 'sachverhalt':
                        segment_type = "Sachverhalt"
                    elif category == 'rechtsfrage':
                        segment_type = "Rechtsfrage"
                    elif category == 'rechtliche_wuerdigung':
                        segment_type = "Rechtliche Würdigung"
                    elif category == 'subsumtion':
                        segment_type = "Subsumtion"
                    elif category == 'ergebnis':
                        segment_type = "Ergebnis"
                    elif category == 'gesetzesnorm':
                        segment_type = "Normprüfung"
            
            # Überprüfe auf spezifische Muster im Segment-Anfang für genauere Klassifizierung
            first_paragraph = segment.split('\n\n')[0] if '\n\n' in segment else segment[:500]
            first_paragraph_lower = first_paragraph.lower()
            
            # Verfeinerte Erkennung spezifischer Abschnittstypen durch Textmuster
            if segment_type == "Allgemein" or segment_score < 4.0:  # Schwacher Score oder Allgemeine Klassifikation
                if re.search(r'(?:zu\s+)?(?:prüfen|untersuchen|beantworten)\s+(?:ist|sei|wäre)', first_paragraph_lower[:100]):
                    segment_type = "Prüfungsfragestellung"
                elif re.search(r'(?:im\s+ergebnis|zusammenfassend|abschließend|somit)(?:\s+ist|\s+lässt\s+sich|\s+kann\s+festgehalten\s+werden)', first_paragraph_lower[:100]):
                    segment_type = "Ergebnis"
                elif re.search(r'(?:nach|gemäß|laut|entsprechend)\s+§\s*\d+', first_paragraph_lower[:100]):
                    segment_type = "Normprüfung"
                elif re.search(r'(?:es\s+handelt\s+sich|vorliegend\s+geht\s+es|der\s+fall|im\s+vorliegenden\s+fall)', first_paragraph_lower[:100]):
                    segment_type = "Sachverhalt"
            
            # Überprüfe, ob das Segment Gesetzesreferenzen enthält
            law_references = re.findall(r'§\s*\d+[a-z]?\s*(?:[A-Za-zäöüÄÖÜß]+)', segment_start)
            law_context = ""
            
            if law_references:
                unique_laws = set()
                for law in law_references[:3]:  # Max. 3 Gesetze anzeigen
                    unique_laws.add(law.strip())
                if unique_laws:
                    law_context = f" ({', '.join(unique_laws)})"
            
            # Bestimme die Top-Keywords für aussagekräftige Überschriften
            # Stelle sicher, dass semantic_vector ein Dictionary ist
            if not isinstance(semantic_vector, dict):
                semantic_vector = {}  # Fallback, wenn kein Dictionary
                
            top_keywords = sorted(semantic_vector.items(), key=lambda x: x[1], reverse=True)[:5]
            legal_terms = [k for k, _ in top_keywords if k not in ["gliederung", "gesetzesreferenz", "artikelreferenz"] 
                          and len(k) > 3 and k not in ["werden", "diese", "nicht", "auch", "eine", "sein", "dass"]]
            
            keyword_str = ""
            if legal_terms:
                keyword_str = f": {', '.join(legal_terms[:2])}"
            
            # Erstelle aussagekräftige Überschrift mit verbesserter Formatierung
            if segment_type != "Allgemein":
                heading = f"{segment_type}{law_context} [{i}/{len(logical_segments)}]{keyword_str}"
            else:
                # Versuche einen beschreibenden Titel zu finden
                # Erkenne potenzielle Überschriften im Text
                potential_heading = re.search(r'^([A-Z][a-zäöüß]+(?: [A-Za-zÄÖÜäöüß]+){1,5})[\.\n]', segment[:200])
                if potential_heading:
                    custom_heading = potential_heading.group(1).strip()
                    heading = f"{custom_heading} [{i}/{len(logical_segments)}]{law_context}"
                else:
                    heading = f"Abschnitt {i}/{len(logical_segments)}{law_context}{keyword_str}"
            
            result_segments.append((heading, segment))
    
    return result_segments
