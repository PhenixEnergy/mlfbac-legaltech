#!/usr/bin/env python3
"""
Final System Demonstration
Shows the complete Legal Tech Semantic Search pipeline in action
"""

import requests
import json
from datetime import datetime

def demonstrate_search():
    """Demonstrate the semantic search with a real legal query"""
    
    print("🎯 LEGAL TECH SEMANTIC SEARCH DEMONSTRATION")
    print("=" * 60)
    print(f"⏰ Demo Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    # Test query about rental law
    query = "Mietrecht Kaution Rückzahlung"
    
    data = {
        "query": query,
        "collection_name": "legal_documents",
        "n_results": 5,
        "threshold": 0.5
    }
    
    print(f"🔍 Search Query: '{query}'")
    print(f"📚 Collection: {data['collection_name']}")
    print(f"📊 Max Results: {data['n_results']}")
    print()
    
    try:
        response = requests.post("http://localhost:8000/search/semantic", json=data, timeout=15)
        
        if response.status_code == 200:
            result = response.json()
            
            print("✅ SEARCH SUCCESSFUL!")
            print(f"⚡ Query Time: {result.get('query_time', 0):.3f} seconds")
            print(f"📋 Found Results: {len(result.get('results', []))}")
            print()
            
            # Display top 3 results
            for i, res in enumerate(result.get('results', [])[:3], 1):
                metadata = res.get('metadata', {})
                semantic_score = metadata.get('semantic_score', 0)
                relevance_score = metadata.get('relevance_score', 0)
                
                print(f"📄 Result #{i}")
                print(f"   🎯 Semantic Score: {semantic_score:.4f}")
                print(f"   📈 Relevance Score: {relevance_score:.4f}")
                
                content = res.get('content', '')
                # Extract gutachten number if available
                if 'Gutachten Nr.' in content:
                    gutachten_line = content.split('\n')[0]
                    print(f"   📋 {gutachten_line}")
                
                # Show content preview
                preview = content[:200].replace('\n', ' ').strip()
                print(f"   📝 Preview: {preview}...")
                print()
                
            print("🎉 DEMONSTRATION COMPLETE!")
            print("✅ The Legal Tech Semantic Search system is fully operational!")
            print()
            print("🌐 Access Points:")
            print("   • Frontend (Streamlit): http://localhost:8501")
            print("   • API Documentation: http://localhost:8000/docs")
            print("   • API Health Check: http://localhost:8000/health")
            
        else:
            print(f"❌ Search failed with status {response.status_code}")
            print(response.text)
            
    except Exception as e:
        print(f"❌ Error during search: {e}")

if __name__ == "__main__":
    demonstrate_search()
