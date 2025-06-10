import requests
import json

def test_api():
    try:
        print("Testing API response structure...")
        response = requests.post('http://localhost:8000/search/documents', 
                               json={'query': 'Schadensersatz', 'limit': 1}, 
                               timeout=5)
        
        if response.status_code == 200:
            data = response.json()
            print(f"Success! Status: {response.status_code}")
            
            if 'results' in data and len(data['results']) > 0:
                result = data['results'][0]
                print("\n=== RESULT KEYS ===")
                print(list(result.keys()))
                
                print("\n=== METADATA ===")
                metadata = result.get('metadata', {})
                print("Metadata keys:", list(metadata.keys()) if metadata else "No metadata")
                if metadata:
                    print(json.dumps(metadata, indent=2, ensure_ascii=False))
                
                print("\n=== CONTENT SAMPLE ===")
                content = result.get('content', '')
                print(f"Content length: {len(content)}")
                print("First 200 chars:", repr(content[:200]))
                
            else:
                print("No results in response")
        else:
            print(f"API Error: {response.status_code}")
            print(response.text)
            
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    test_api()
