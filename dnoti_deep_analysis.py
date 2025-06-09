#!/usr/bin/env python3
"""
DNOTI Deep Website Analysis Tool
Detaillierte Analyse der DNOTI-Website-Struktur für optimierte Gutachten-Extraktion

Entwickelt für den MLFBAC Legal Tech Semantic Search
"""

import requests
from bs4 import BeautifulSoup
import re
import json
import time
from urllib.parse import urljoin, urlparse, parse_qs
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Set, Optional

class DNOTIDeepAnalyzer:
    """Tiefgreifende Analyse der DNOTI-Website-Struktur"""
    
    def __init__(self):
        self.base_url = "https://www.dnoti.de"
        self.session = requests.Session()
        self.findings = {
            'analyzed_at': datetime.now().isoformat(),
            'pages_analyzed': [],
            'gutachten_patterns': [],
            'form_parameters': [],
            'navigation_structure': {},
            'content_types': [],
            'recommended_strategies': []
        }
        
        # Setup Session
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'de-DE,de;q=0.9,en;q=0.8',
            'Accept-Encoding': 'gzip, deflate, br',
            'DNT': '1',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1'
        })
    
    def analyze_complete_website(self):
        """Führe komplette Website-Analyse durch"""
        print("🔍 DNOTI Deep Analysis - Starte vollständige Website-Analyse")
        print("=" * 60)
        
        # 1. Hauptseite analysieren
        print("\n📋 1. Analysiere Hauptseite...")
        self.analyze_main_page()
        
        # 2. Gutachten-Sektion analysieren
        print("\n📋 2. Analysiere Gutachten-Sektion...")
        self.analyze_gutachten_section()
        
        # 3. Such-Formulare analysieren
        print("\n📋 3. Analysiere Such-Formulare...")
        self.analyze_search_forms()
        
        # 4. Sitemap und Navigation analysieren
        print("\n📋 4. Analysiere Sitemap und Navigation...")
        self.analyze_navigation()
        
        # 5. Spezifische Gutachten-Links finden
        print("\n📋 5. Suche spezifische Gutachten-Links...")
        self.find_specific_gutachten_links()
        
        # 6. Empfehlungen generieren
        print("\n📋 6. Generiere Optimierungsempfehlungen...")
        self.generate_recommendations()
        
        # 7. Ergebnisse speichern
        self.save_analysis_results()
        
        print("\n✅ Analyse abgeschlossen! Ergebnisse gespeichert.")
        return self.findings
    
    def analyze_main_page(self):
        """Analysiere DNOTI Hauptseite"""
        try:
            response = self.session.get(self.base_url, timeout=30)
            if response.status_code != 200:
                print(f"❌ Hauptseite nicht erreichbar: {response.status_code}")
                return
            
            soup = BeautifulSoup(response.content, 'html.parser')
            self.findings['pages_analyzed'].append({
                'url': self.base_url,
                'title': soup.title.string if soup.title else "N/A",
                'status': 'success'
            })
            
            # Analysiere Navigation
            nav_elements = soup.find_all(['nav', 'ul', 'div'], class_=re.compile(r'nav|menu|navigation', re.I))
            navigation_links = set()
            
            for nav in nav_elements:
                links = nav.find_all('a', href=True)
                for link in links:
                    href = link['href']
                    text = link.get_text(strip=True)
                    if href and text:
                        full_url = urljoin(self.base_url, href)
                        navigation_links.add((full_url, text))
            
            self.findings['navigation_structure']['main_page'] = list(navigation_links)
            
            # Suche Gutachten-bezogene Links
            gutachten_links = soup.find_all('a', href=re.compile(r'gutachten|expertise', re.I))
            for link in gutachten_links:
                href = link.get('href')
                text = link.get_text(strip=True)
                if href:
                    full_url = urljoin(self.base_url, href)
                    self.findings['gutachten_patterns'].append({
                        'url': full_url,
                        'text': text,
                        'context': 'main_page_link'
                    })
            
            print(f"   ✓ Hauptseite analysiert: {len(navigation_links)} Navigation-Links gefunden")
            
        except Exception as e:
            print(f"❌ Fehler bei Hauptseiten-Analyse: {e}")
    
    def analyze_gutachten_section(self):
        """Analysiere dedizierte Gutachten-Sektion"""
        gutachten_urls = [
            f"{self.base_url}/gutachten/",
            f"{self.base_url}/gutachten",
            f"{self.base_url}/expertisen/",
            f"{self.base_url}/expertisen",
        ]
        
        for url in gutachten_urls:
            try:
                print(f"   🔍 Prüfe: {url}")
                response = self.session.get(url, timeout=30)
                
                if response.status_code == 200:
                    soup = BeautifulSoup(response.content, 'html.parser')
                    
                    self.findings['pages_analyzed'].append({
                        'url': url,
                        'title': soup.title.string if soup.title else "N/A",
                        'status': 'success'
                    })
                    
                    # Analysiere Seitenstruktur
                    self.analyze_page_structure(soup, url, 'gutachten_section')
                    
                    # Suche spezifische Gutachten-Links
                    self.extract_gutachten_links_from_page(soup, url)
                    
                    print(f"   ✓ {url} erfolgreich analysiert")
                    
                    # Debug-HTML speichern
                    self.save_debug_html(response.content, f"gutachten_section_{url.split('/')[-2]}")
                    
                else:
                    print(f"   ⚠️ {url} nicht verfügbar (Status: {response.status_code})")
                    
            except Exception as e:
                print(f"   ❌ Fehler bei {url}: {e}")
            
            time.sleep(1)  # Rate limiting
    
    def analyze_search_forms(self):
        """Analysiere Such-Formulare auf der DNOTI-Website"""
        try:
            # Gutachten-Such-Seite
            search_url = f"{self.base_url}/gutachten/"
            response = self.session.get(search_url, timeout=30)
            
            if response.status_code == 200:
                soup = BeautifulSoup(response.content, 'html.parser')
                
                # Finde alle Formulare
                forms = soup.find_all('form')
                
                for i, form in enumerate(forms):
                    form_analysis = {
                        'form_index': i,
                        'action': form.get('action', ''),
                        'method': form.get('method', 'get').lower(),
                        'inputs': [],
                        'selects': [],
                        'textareas': []
                    }
                    
                    # Analysiere Input-Felder
                    inputs = form.find_all('input')
                    for inp in inputs:
                        input_info = {
                            'name': inp.get('name', ''),
                            'type': inp.get('type', 'text'),
                            'value': inp.get('value', ''),
                            'placeholder': inp.get('placeholder', ''),
                            'required': inp.has_attr('required')
                        }
                        form_analysis['inputs'].append(input_info)
                    
                    # Analysiere Select-Felder
                    selects = form.find_all('select')
                    for select in selects:
                        select_info = {
                            'name': select.get('name', ''),
                            'options': []
                        }
                        
                        options = select.find_all('option')
                        for option in options:
                            select_info['options'].append({
                                'value': option.get('value', ''),
                                'text': option.get_text(strip=True)
                            })
                        
                        form_analysis['selects'].append(select_info)
                    
                    # Analysiere Textarea-Felder
                    textareas = form.find_all('textarea')
                    for textarea in textareas:
                        textarea_info = {
                            'name': textarea.get('name', ''),
                            'placeholder': textarea.get('placeholder', ''),
                            'required': textarea.has_attr('required')
                        }
                        form_analysis['textareas'].append(textarea_info)
                    
                    self.findings['form_parameters'].append(form_analysis)
                
                print(f"   ✓ {len(forms)} Formulare analysiert")
                
        except Exception as e:
            print(f"❌ Fehler bei Formular-Analyse: {e}")
    
    def analyze_navigation(self):
        """Analysiere Website-Navigation und Sitemap"""
        # Versuche Sitemap zu finden
        sitemap_urls = [
            f"{self.base_url}/sitemap.xml",
            f"{self.base_url}/sitemap/",
            f"{self.base_url}/robots.txt"
        ]
        
        for url in sitemap_urls:
            try:
                response = self.session.get(url, timeout=30)
                if response.status_code == 200:
                    print(f"   ✓ Gefunden: {url}")
                    
                    if url.endswith('.xml'):
                        # XML Sitemap
                        self.analyze_xml_sitemap(response.content)
                    elif url.endswith('robots.txt'):
                        # Robots.txt nach Sitemap-Verweisen durchsuchen
                        robots_content = response.text
                        sitemap_lines = [line for line in robots_content.split('\n') if 'sitemap' in line.lower()]
                        if sitemap_lines:
                            self.findings['navigation_structure']['robots_sitemaps'] = sitemap_lines
                            
            except Exception as e:
                print(f"   ⚠️ {url} nicht erreichbar")
    
    def analyze_xml_sitemap(self, xml_content):
        """Analysiere XML-Sitemap"""
        try:
            soup = BeautifulSoup(xml_content, 'xml')
            urls = soup.find_all('url')
            
            sitemap_urls = []
            gutachten_urls = []
            
            for url_elem in urls:
                loc = url_elem.find('loc')
                if loc:
                    url = loc.text
                    sitemap_urls.append(url)
                    
                    # Prüfe auf Gutachten-URLs
                    if re.search(r'gutachten|expertise', url, re.I):
                        gutachten_urls.append(url)
            
            self.findings['navigation_structure']['sitemap_urls'] = sitemap_urls[:50]  # Begrenzt für Output
            self.findings['navigation_structure']['gutachten_from_sitemap'] = gutachten_urls
            
            print(f"   ✓ Sitemap analysiert: {len(sitemap_urls)} URLs, {len(gutachten_urls)} Gutachten-URLs")
            
        except Exception as e:
            print(f"   ❌ XML-Sitemap-Analyse fehlgeschlagen: {e}")
    
    def find_specific_gutachten_links(self):
        """Suche spezifische Gutachten-Links mit verschiedenen Strategien"""
        
        strategies = [
            {
                'name': 'TYPO3 Extension Search',
                'method': self.search_typo3_extension
            },
            {
                'name': 'Archive Browsing',
                'method': self.search_archive_pages
            },
            {
                'name': 'Recent Content Search',
                'method': self.search_recent_content
            },
            {
                'name': 'Direct URL Pattern Testing',
                'method': self.test_url_patterns
            }
        ]
        
        for strategy in strategies:
            print(f"   🔍 {strategy['name']}...")
            try:
                results = strategy['method']()
                if results:
                    print(f"   ✓ {len(results)} Ergebnisse gefunden")
                else:
                    print("   ⚠️ Keine Ergebnisse")
            except Exception as e:
                print(f"   ❌ Fehler: {e}")
            
            time.sleep(1)
    
    def search_typo3_extension(self):
        """Suche über TYPO3 Extension"""
        try:
            # Test verschiedene TYPO3-Parameter
            search_params = [
                {
                    'tx_dnotionlineplusapi_expertises[searchText]': '',
                    'tx_dnotionlineplusapi_expertises[expertisesType]': 'all'
                },
                {
                    'tx_dnotionlineplusapi_expertises[searchText]': 'Notar',
                    'tx_dnotionlineplusapi_expertises[expertisesType]': 'dnotiReport'
                },
                {
                    'tx_dnotionlineplusapi_expertises[searchText]': '',
                    'tx_dnotionlineplusapi_expertises[expertisesType]': 'dnotiReport',
                    'tx_dnotionlineplusapi_expertises[dateFrom]': '2024-01-01',
                    'tx_dnotionlineplusapi_expertises[dateTo]': '2025-12-31'
                }
            ]
            
            found_links = []
            
            for params in search_params:
                response = self.session.post(
                    f"{self.base_url}/gutachten/",
                    data=params,
                    timeout=30
                )
                
                if response.status_code == 200:
                    soup = BeautifulSoup(response.content, 'html.parser')
                    
                    # Suche verschiedene Link-Pattern
                    link_patterns = [
                        'a[href*="nodeid"]',
                        'a[href*="tx_dnotionlineplusapi_expertises"]',
                        'a[href*="/details/"]',
                        '.result-item a',
                        '.expertise-link a'
                    ]
                    
                    for pattern in link_patterns:
                        links = soup.select(pattern)
                        for link in links:
                            href = link.get('href')
                            text = link.get_text(strip=True)
                            if href and self.is_valid_gutachten_link(href):
                                full_url = urljoin(self.base_url, href)
                                found_links.append({
                                    'url': full_url,
                                    'text': text,
                                    'context': 'typo3_search',
                                    'params': str(params)
                                })
                    
                    # Debug speichern
                    self.save_debug_html(response.content, f"typo3_search_{len(params)}_params")
            
            # Deduplizieren
            unique_links = []
            seen_urls = set()
            for link in found_links:
                if link['url'] not in seen_urls:
                    seen_urls.add(link['url'])
                    unique_links.append(link)
            
            self.findings['gutachten_patterns'].extend(unique_links)
            return unique_links
            
        except Exception as e:
            print(f"   ❌ TYPO3-Suche fehlgeschlagen: {e}")
            return []
    
    def search_archive_pages(self):
        """Durchsuche Archiv-Seiten"""
        archive_urls = [
            f"{self.base_url}/archiv/",
            f"{self.base_url}/gutachten/archiv/",
            f"{self.base_url}/service/archiv/",
            f"{self.base_url}/publikationen/",
            f"{self.base_url}/veroeffentlichungen/"
        ]
        
        found_links = []
        
        for url in archive_urls:
            try:
                response = self.session.get(url, timeout=30)
                if response.status_code == 200:
                    soup = BeautifulSoup(response.content, 'html.parser')
                    
                    # Suche Gutachten-Links
                    links = soup.find_all('a', href=True)
                    for link in links:
                        href = link['href']
                        text = link.get_text(strip=True)
                        
                        if self.is_valid_gutachten_link(href):
                            full_url = urljoin(self.base_url, href)
                            found_links.append({
                                'url': full_url,
                                'text': text,
                                'context': 'archive_page',
                                'source_page': url
                            })
            
            except Exception as e:
                print(f"   ⚠️ Archiv-URL {url} nicht erreichbar: {e}")
        
        return found_links
    
    def search_recent_content(self):
        """Suche nach neuen Inhalten"""
        recent_urls = [
            f"{self.base_url}/aktuelles/",
            f"{self.base_url}/news/",
            f"{self.base_url}/neuigkeiten/",
            f"{self.base_url}/service/aktuelles/"
        ]
        
        found_links = []
        
        for url in recent_urls:
            try:
                response = self.session.get(url, timeout=30)
                if response.status_code == 200:
                    soup = BeautifulSoup(response.content, 'html.parser')
                    
                    # Suche Gutachten-Links
                    links = soup.find_all('a', href=True)
                    for link in links:
                        href = link['href']
                        text = link.get_text(strip=True)
                        
                        if self.is_valid_gutachten_link(href):
                            full_url = urljoin(self.base_url, href)
                            found_links.append({
                                'url': full_url,
                                'text': text,
                                'context': 'recent_content',
                                'source_page': url
                            })
            
            except Exception as e:
                print(f"   ⚠️ Recent-URL {url} nicht erreichbar: {e}")
        
        return found_links
    
    def test_url_patterns(self):
        """Teste verschiedene URL-Muster für Gutachten"""
        test_patterns = [
            f"{self.base_url}/gutachten/details/1/",
            f"{self.base_url}/gutachten/details/2/",
            f"{self.base_url}/gutachten/view/1/",
            f"{self.base_url}/expertise/1/",
            f"{self.base_url}/expertise/details/1/",
            # UUID-ähnliche IDs (Beispiele)
            f"{self.base_url}/gutachten/details/?tx_dnotionlineplusapi_expertises[nodeid]=1a83d34f-65d8-440d-911d-a90c88782a1c",
            f"{self.base_url}/gutachten/details/?nodeid=1a83d34f-65d8-440d-911d-a90c88782a1c"
        ]
        
        working_patterns = []
        
        for pattern in test_patterns:
            try:
                response = self.session.get(pattern, timeout=30)
                if response.status_code == 200:
                    # Prüfe ob es tatsächlich ein Gutachten ist
                    content = response.text.lower()
                    if any(keyword in content for keyword in ['gutachten', 'expertise', 'notar', 'beurkundung']):
                        working_patterns.append({
                            'url': pattern,
                            'status': response.status_code,
                            'context': 'url_pattern_test'
                        })
                        print(f"   ✓ Funktionierendes Muster: {pattern}")
            
            except Exception as e:
                print(f"   ⚠️ Pattern {pattern} fehlgeschlagen: {e}")
        
        return working_patterns
    
    def is_valid_gutachten_link(self, href: str) -> bool:
        """Prüfe ob Link ein gültiger Gutachten-Link ist"""
        if not href:
            return False
        
        # Positive Patterns
        positive_patterns = [
            r'/gutachten/details/',
            r'tx_dnotionlineplusapi_expertises.*nodeid',
            r'nodeid=[\w\-]+',
            r'/expertise/',
            r'/expertisen/',
            r'gutachten.*id=\d+',
            r'expertise.*id=\d+'
        ]
        
        # Negative Patterns
        negative_patterns = [
            r'javascript:',
            r'mailto:',
            r'#$',
            r'\.pdf$',
            r'\.doc$',
            r'/impressum',
            r'/datenschutz',
            r'/kontakt',
            r'/search',
            r'/archiv$'
        ]
        
        # Prüfe negative Patterns
        for pattern in negative_patterns:
            if re.search(pattern, href, re.IGNORECASE):
                return False
        
        # Prüfe positive Patterns
        for pattern in positive_patterns:
            if re.search(pattern, href, re.IGNORECASE):
                return True
        
        return False
    
    def analyze_page_structure(self, soup: BeautifulSoup, url: str, context: str):
        """Analysiere Seitenstruktur einer spezifischen Seite"""
        structure = {
            'url': url,
            'context': context,
            'title': soup.title.string if soup.title else "N/A",
            'main_content_selectors': [],
            'link_count': len(soup.find_all('a', href=True)),
            'form_count': len(soup.find_all('form')),
            'script_count': len(soup.find_all('script')),
            'css_classes': []
        }
        
        # Identifiziere Content-Bereiche
        content_selectors = [
            '.content', '.main-content', '.page-content',
            '.tx-dnotionlineplus-pi1', '.gutachten-list',
            '.expertise-list', '.result-list', '.search-results'
        ]
        
        for selector in content_selectors:
            elements = soup.select(selector)
            if elements:
                structure['main_content_selectors'].append({
                    'selector': selector,
                    'count': len(elements)
                })
        
        # Sammle CSS-Klassen
        all_elements = soup.find_all(class_=True)
        class_names = set()
        for elem in all_elements[:50]:  # Begrenzt für Performance
            if elem.get('class'):
                class_names.update(elem['class'])
        
        structure['css_classes'] = list(class_names)[:20]  # Top 20 Klassen
        
        self.findings['content_types'].append(structure)
    
    def extract_gutachten_links_from_page(self, soup: BeautifulSoup, source_url: str):
        """Extrahiere Gutachten-Links von einer spezifischen Seite"""
        # Verschiedene Selektoren für Gutachten-Links
        link_selectors = [
            'a[href*="nodeid"]',
            'a[href*="tx_dnotionlineplusapi_expertises"]',
            'a[href*="/details/"]',
            'a[href*="/gutachten/"]',
            'a[href*="/expertise/"]',
            '.result-item a',
            '.gutachten-item a',
            '.expertise-item a',
            '.list-item a'
        ]
        
        found_links = []
        
        for selector in link_selectors:
            links = soup.select(selector)
            for link in links:
                href = link.get('href')
                text = link.get_text(strip=True)
                
                if href and self.is_valid_gutachten_link(href):
                    full_url = urljoin(self.base_url, href)
                    found_links.append({
                        'url': full_url,
                        'text': text,
                        'selector': selector,
                        'source_page': source_url
                    })
        
        # Deduplizieren
        unique_links = []
        seen_urls = set()
        for link in found_links:
            if link['url'] not in seen_urls:
                seen_urls.add(link['url'])
                unique_links.append(link)
        
        self.findings['gutachten_patterns'].extend(unique_links)
        
        if unique_links:
            print(f"   ✓ {len(unique_links)} eindeutige Gutachten-Links gefunden")
    
    def generate_recommendations(self):
        """Generiere Optimierungsempfehlungen basierend auf der Analyse"""
        recommendations = []
        
        # Analyse der gefundenen Patterns
        total_gutachten_links = len(self.findings['gutachten_patterns'])
        
        if total_gutachten_links == 0:
            recommendations.append({
                'priority': 'HIGH',
                'category': 'Search Strategy',
                'recommendation': 'Keine direkten Gutachten-Links gefunden. Implementiere Scraping-Fallback-Strategien.',
                'implementation': 'Nutze TYPO3-Forms mit verschiedenen Parametern und parse HTML-Responses nach versteckten Links.'
            })
        else:
            recommendations.append({
                'priority': 'MEDIUM',
                'category': 'Link Extraction',
                'recommendation': f'{total_gutachten_links} potentielle Gutachten-Links gefunden. Optimiere Extraktion.',
                'implementation': 'Verwende gefundene Selektoren für zielgerichtete Link-Extraktion.'
            })
        
        # Formular-Analyse
        if self.findings['form_parameters']:
            form_count = len(self.findings['form_parameters'])
            recommendations.append({
                'priority': 'HIGH',
                'category': 'Form Submission',
                'recommendation': f'{form_count} Formulare gefunden. Nutze für automatisierte Suchen.',
                'implementation': 'Implementiere POST-Requests mit gefundenen Form-Parametern für systematische Suche.'
            })
        
        # Navigation-Analyse
        if 'sitemap_urls' in self.findings['navigation_structure']:
            sitemap_count = len(self.findings['navigation_structure']['sitemap_urls'])
            recommendations.append({
                'priority': 'MEDIUM',
                'category': 'Sitemap Utilization',
                'recommendation': f'Sitemap mit {sitemap_count} URLs gefunden. Nutze für systematisches Crawling.',
                'implementation': 'Parse XML-Sitemap für vollständige URL-Liste und filtere Gutachten-URLs.'
            })
        
        # Content-Struktur-Analyse
        if self.findings['content_types']:
            recommendations.append({
                'priority': 'MEDIUM',
                'category': 'Content Extraction',
                'recommendation': 'Seitenstrukturen analysiert. Optimiere Content-Selektoren.',
                'implementation': 'Verwende identifizierte CSS-Selektoren für präzise Content-Extraktion.'
            })
        
        self.findings['recommended_strategies'] = recommendations
        
        # Drucke Empfehlungen
        print("\n🎯 Optimierungsempfehlungen:")
        for i, rec in enumerate(recommendations, 1):
            print(f"\n{i}. [{rec['priority']}] {rec['category']}")
            print(f"   💡 {rec['recommendation']}")
            print(f"   🔧 {rec['implementation']}")
    
    def save_debug_html(self, content: bytes, filename: str):
        """Speichere HTML für Debug-Zwecke"""
        debug_dir = Path("debug_output")
        debug_dir.mkdir(exist_ok=True)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filepath = debug_dir / f"deep_analysis_{filename}_{timestamp}.html"
        
        try:
            with open(filepath, 'wb') as f:
                f.write(content)
        except Exception as e:
            print(f"   ⚠️ Debug-HTML konnte nicht gespeichert werden: {e}")
    
    def save_analysis_results(self):
        """Speichere Analyseergebnisse"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"dnoti_deep_analysis_{timestamp}.json"
        
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(self.findings, f, indent=2, ensure_ascii=False)
            
            print(f"\n📄 Analyseergebnisse gespeichert: {filename}")
            
            # Zusätzlich vereinfachten Report erstellen
            self.create_summary_report(timestamp)
            
        except Exception as e:
            print(f"❌ Fehler beim Speichern: {e}")
    
    def create_summary_report(self, timestamp: str):
        """Erstelle zusammenfassenden Report"""
        summary_filename = f"dnoti_analysis_summary_{timestamp}.txt"
        
        try:
            with open(summary_filename, 'w', encoding='utf-8') as f:
                f.write("DNOTI Deep Analysis - Summary Report\n")
                f.write("=" * 50 + "\n\n")
                
                f.write(f"Analyzed at: {self.findings['analyzed_at']}\n")
                f.write(f"Pages analyzed: {len(self.findings['pages_analyzed'])}\n")
                f.write(f"Gutachten links found: {len(self.findings['gutachten_patterns'])}\n")
                f.write(f"Forms found: {len(self.findings['form_parameters'])}\n\n")
                
                # Gutachten-Links
                if self.findings['gutachten_patterns']:
                    f.write("Found Gutachten Links:\n")
                    f.write("-" * 25 + "\n")
                    for i, link in enumerate(self.findings['gutachten_patterns'][:10], 1):
                        f.write(f"{i}. {link['url']}\n")
                        f.write(f"   Text: {link['text']}\n")
                        f.write(f"   Context: {link['context']}\n\n")
                
                # Empfehlungen
                f.write("\nRecommendations:\n")
                f.write("-" * 15 + "\n")
                for i, rec in enumerate(self.findings['recommended_strategies'], 1):
                    f.write(f"{i}. [{rec['priority']}] {rec['category']}\n")
                    f.write(f"   {rec['recommendation']}\n")
                    f.write(f"   Implementation: {rec['implementation']}\n\n")
            
            print(f"📄 Summary Report gespeichert: {summary_filename}")
            
        except Exception as e:
            print(f"❌ Fehler beim Summary-Report: {e}")


def main():
    """Hauptfunktion"""
    print("🔍 DNOTI Deep Website Analysis Tool")
    print("Detaillierte Analyse für optimierte Gutachten-Extraktion")
    print("=" * 60)
    
    try:
        analyzer = DNOTIDeepAnalyzer()
        results = analyzer.analyze_complete_website()
        
        print("\n🎉 Analyse erfolgreich abgeschlossen!")
        print(f"📊 Ergebnisse: {len(results['gutachten_patterns'])} Gutachten-Links gefunden")
        print(f"📋 {len(results['recommended_strategies'])} Optimierungsempfehlungen generiert")
        
        return 0
        
    except KeyboardInterrupt:
        print("\n⚠️ Analyse durch Benutzer abgebrochen")
        return 130
    except Exception as e:
        print(f"\n❌ FATALER FEHLER: {e}")
        return 1


if __name__ == "__main__":
    import sys
    sys.exit(main())
