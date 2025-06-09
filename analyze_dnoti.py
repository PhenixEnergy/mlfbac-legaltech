import requests
from bs4 import BeautifulSoup

def analyze_website():
    """Analysiert die DNOTI Website Struktur"""
    try:
        r = requests.get('https://www.dnoti.de/gutachten/')
        r.raise_for_status()
        soup = BeautifulSoup(r.text, 'html.parser')
        
        print("=== DNOTI Website Analyse ===")
        print(f"Status: {r.status_code}")
        print(f"Title: {soup.title.string if soup.title else 'Kein Titel'}")
        
        print("\nLinks gefunden:")
        links = soup.find_all('a', href=True)
        for i, link in enumerate(links[:15]):
            href = link.get('href')
            text = link.get_text(strip=True)[:50]
            print(f"  {i+1:2d}. {href} -> {text}")
        
        print(f"\nGesamt Links: {len(links)}")
        
        # Suche nach gutachten-spezifischen Links
        gutachten_links = [l for l in links if 'gutachten' in l.get('href', '').lower()]
        print(f"Gutachten Links: {len(gutachten_links)}")
        
        print("\nMögliche CSS-Selektoren:")
        print("  Links: a[href*='gutachten']")
        print("  Titel: h1, .headline, .title")
        print("  Content: .content, article, main")
        
    except Exception as e:
        print(f"Fehler: {e}")

if __name__ == "__main__":
    analyze_website()
