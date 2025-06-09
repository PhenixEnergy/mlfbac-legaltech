#!/usr/bin/env python3
"""
Erweiterte DNOTI Website Analyse
Analysiert die tatsächliche Struktur der Website
"""

import requests
from bs4 import BeautifulSoup
import json
import time
from urllib.parse import urljoin, urlparse

def deep_analyze_dnoti():
    """Tiefere Analyse der DNOTI Website"""
    
    base_url = "https://www.dnoti.de/gutachten/"
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'de-DE,de;q=0.9,en;q=0.8',
        'Accept-Encoding': 'gzip, deflate, br',
        'Cache-Control': 'no-cache',
        'Upgrade-Insecure-Requests': '1'
    }
    
    try:
        print("🔍 Erweiterte DNOTI Analyse...")
        response = requests.get(base_url, headers=headers, timeout=30)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Speichere HTML für Analyse
        with open('dnoti_page_analysis.html', 'w', encoding='utf-8') as f:
            f.write(soup.prettify())
        print("📄 HTML-Struktur gespeichert in: dnoti_page_analysis.html")
        
        # Analysiere Formulare (könnte für Suche/Navigation verwendet werden)
        forms = soup.find_all('form')
        print(f"\n📝 Gefundene Formulare: {len(forms)}")
        for i, form in enumerate(forms):
            action = form.get('action', 'Keine Action')
            method = form.get('method', 'GET')
            inputs = form.find_all('input')
            selects = form.find_all('select')
            print(f"  Form {i+1}: {method} -> {action}")
            print(f"    Inputs: {len(inputs)}, Selects: {len(selects)}")
            
            # Zeige wichtige Input-Felder
            for inp in inputs[:5]:  # Erste 5 Inputs
                name = inp.get('name', 'unnamed')
                input_type = inp.get('type', 'text')
                value = inp.get('value', '')
                print(f"      {input_type}: {name} = {value}")
        
        # Analysiere JavaScript/AJAX Calls
        scripts = soup.find_all('script')
        print(f"\n🔧 JavaScript Blöcke: {len(scripts)}")
        
        ajax_keywords = ['ajax', 'xhr', 'fetch', 'api', 'json']
        for i, script in enumerate(scripts):
            if script.string:
                script_content = script.string.lower()
                found_keywords = [kw for kw in ajax_keywords if kw in script_content]
                if found_keywords:
                    print(f"  Script {i+1} enthält: {found_keywords}")
                    # Zeige relevante Zeilen
                    lines = script.string.split('\n')
                    for line_num, line in enumerate(lines):
                        if any(kw in line.lower() for kw in ajax_keywords):
                            print(f"    Zeile {line_num}: {line.strip()[:100]}")
        
        # Suche nach versteckten/dynamischen Content-Bereichen
        content_divs = soup.find_all('div', class_=True)
        print(f"\n📦 Content DIVs mit Klassen: {len(content_divs)}")
        
        interesting_classes = []
        for div in content_divs:
            classes = div.get('class', [])
            for cls in classes:
                if any(keyword in cls.lower() for keyword in ['content', 'list', 'item', 'result', 'data']):
                    interesting_classes.append(cls)
        
        unique_classes = list(set(interesting_classes))
        print(f"  Interessante Klassen: {unique_classes[:10]}")  # Erste 10
        
        # Suche nach Meta-Tags und anderen Hinweisen
        meta_tags = soup.find_all('meta')
        print(f"\n🏷️  Meta Tags: {len(meta_tags)}")
        for meta in meta_tags:
            name = meta.get('name', '')
            content = meta.get('content', '')
            if name and any(keyword in name.lower() for keyword in ['description', 'keywords', 'title']):
                print(f"  {name}: {content[:100]}")
        
        # Analysiere Navigationsstruktur
        nav_elements = soup.find_all(['nav', 'ul', 'ol'])
        print(f"\n🧭 Navigationselemente: {len(nav_elements)}")
        
        for i, nav in enumerate(nav_elements[:3]):  # Erste 3
            links = nav.find_all('a')
            if links:
                print(f"  Navigation {i+1}: {len(links)} Links")
                for link in links[:3]:  # Erste 3 Links
                    href = link.get('href', '')
                    text = link.get_text().strip()
                    print(f"    {href} - {text}")
        
        # Teste verschiedene URL-Parameter für Gutachten-Suche
        test_params = [
            "?search=",
            "?query=",
            "?q=",
            "?filter=",
            "?page=1",
            "?limit=10"
        ]
        
        print(f"\n🔍 Teste URL-Parameter...")
        for param in test_params[:3]:  # Teste nur erste 3
            test_url = base_url + param
            try:
                time.sleep(1)  # Rate limiting
                test_response = requests.get(test_url, headers=headers, timeout=15)
                print(f"  {param}: Status {test_response.status_code}")
                if test_response.status_code == 200:
                    test_soup = BeautifulSoup(test_response.content, 'html.parser')
                    # Suche nach Inhaltsänderungen
                    content_length = len(test_soup.get_text())
                    print(f"    Content-Länge: {content_length}")
            except Exception as e:
                print(f"  {param}: Fehler - {e}")
        
        return True
        
    except Exception as e:
        print(f"❌ Fehler bei der Analyse: {e}")
        return False

def analyze_potential_api_endpoints():
    """Analysiere mögliche API-Endpunkte"""
    
    print("\n" + "="*60)
    print("🔌 API ENDPUNKT ANALYSE")
    print("="*60)
    
    base_domain = "https://www.dnoti.de"
    potential_endpoints = [
        "/api/gutachten",
        "/api/search",
        "/ajax/gutachten",
        "/ajax/search", 
        "/gutachten/api",
        "/gutachten/search",
        "/typo3/",
        "/index.php?eID=",
        "/fileadmin/"
    ]
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
        'Accept': 'application/json, text/plain, */*',
        'Accept-Language': 'de-DE,de;q=0.9',
        'X-Requested-With': 'XMLHttpRequest'
    }
    
    for endpoint in potential_endpoints:
        url = base_domain + endpoint
        try:
            response = requests.get(url, headers=headers, timeout=10)
            print(f"  {endpoint}: Status {response.status_code}")
            
            if response.status_code == 200:
                content_type = response.headers.get('content-type', '')
                print(f"    Content-Type: {content_type}")
                
                if 'json' in content_type:
                    try:
                        json_data = response.json()
                        print(f"    JSON-Struktur erkannt: {len(str(json_data))} Zeichen")
                    except:
                        pass
                
            time.sleep(0.5)  # Rate limiting
            
        except Exception as e:
            print(f"  {endpoint}: {type(e).__name__}")

if __name__ == "__main__":
    print("🚀 ERWEITERTE DNOTI WEBSITE ANALYSE")
    print("="*50)
    
    success = deep_analyze_dnoti()
    
    if success:
        analyze_potential_api_endpoints()
        print("\n✅ Erweiterte Analyse abgeschlossen.")
        print("📄 Prüfen Sie die gespeicherte HTML-Datei für weitere Details.")
    else:
        print("\n❌ Analyse fehlgeschlagen.")
