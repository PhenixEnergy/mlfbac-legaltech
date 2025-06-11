#!/usr/bin/env python3
"""
LegalTech System Status and Search Quality Analysis
"""

import requests
import json
from datetime import datetime

def get_system_status():
    """Get the current system status"""
    
    status = {
        'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'backend_status': 'Unknown',
        'frontend_status': 'Unknown',
        'search_working': False,
        'configuration': {}
    }
    
    # Test backend
    try:
        response = requests.get("http://localhost:8000/health", timeout=5)
        if response.status_code == 200:
            status['backend_status'] = 'Running'
        else:
            status['backend_status'] = f'Error {response.status_code}'
    except:
        status['backend_status'] = 'Not reachable'
    
    # Test frontend (just check if port is responding)
    try:
        response = requests.get("http://localhost:8501", timeout=5)
        if response.status_code == 200:
            status['frontend_status'] = 'Running'
        else:
            status['frontend_status'] = 'Error'
    except:
        status['frontend_status'] = 'Not reachable'
    
    # Test search functionality
    try:
        search_query = {"query": "Kaufvertrag", "max_results": 3}
        response = requests.post("http://localhost:8000/search/semantic", json=search_query, timeout=10)
        if response.status_code == 200:
            result = response.json()
            status['search_working'] = len(result.get('results', [])) > 0
    except:
        status['search_working'] = False
    
    return status

def analyze_search_quality():
    """Analyze search quality with various test queries"""
    
    test_queries = [
        "Kaufvertrag Immobilie",
        "Schadensersatz",
        "Gesellschaftsrecht GmbH",
        "Erbrecht Testament",
        "Vertragsrecht"
    ]
    
    results = []
    
    for query in test_queries:
        try:
            search_query = {"query": query, "max_results": 5}
            response = requests.post("http://localhost:8000/search/semantic", json=search_query, timeout=15)
            
            if response.status_code == 200:
                result = response.json()
                results.append({
                    'query': query,
                    'found_results': len(result.get('results', [])),
                    'avg_similarity': sum(r.get('similarity_score', 0) for r in result.get('results', [])) / max(len(result.get('results', [])), 1),
                    'success': True
                })
            else:
                results.append({
                    'query': query,
                    'success': False,
                    'error': f"HTTP {response.status_code}"
                })
                
        except Exception as e:
            results.append({
                'query': query,
                'success': False,
                'error': str(e)
            })
    
    return results

def print_status_report():
    """Print comprehensive status report"""
    
    print("🔍 LEGALTECH SYSTEM STATUS REPORT")
    print("=" * 60)
    print(f"📅 Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # System status
    status = get_system_status()
    print(f"\n🖥️  SYSTEM STATUS:")
    print(f"   🔧 Backend API: {status['backend_status']}")
    print(f"   🎨 Frontend (Streamlit): {status['frontend_status']}")
    print(f"   🔍 Search Engine: {'✅ Working' if status['search_working'] else '❌ Not working'}")
    
    # Configuration
    print(f"\n⚙️  CURRENT CONFIGURATION:")
    print(f"   📦 Collection: dnoti_legal_documents")
    print(f"   🗂️  Documents: 930 Gutachten")
    print(f"   🤖 Embedding Model: paraphrase-multilingual-MiniLM-L12-v2")
    print(f"   📊 Dimensions: 384 (compatible)")
    
    # Search quality analysis
    if status['search_working']:
        print(f"\n🎯 SEARCH QUALITY ANALYSIS:")
        search_results = analyze_search_quality()
        
        successful_searches = [r for r in search_results if r.get('success', False)]
        
        if successful_searches:
            avg_results = sum(r['found_results'] for r in successful_searches) / len(successful_searches)
            avg_similarity = sum(r['avg_similarity'] for r in successful_searches) / len(successful_searches)
            
            print(f"   📊 Test Queries: {len(search_results)}")
            print(f"   ✅ Successful: {len(successful_searches)}")
            print(f"   📈 Avg Results per Query: {avg_results:.1f}")
            print(f"   🎯 Avg Similarity Score: {avg_similarity:.3f}")
            
            print(f"\n   📋 Individual Query Results:")
            for result in search_results:
                if result.get('success'):
                    print(f"      '{result['query']}': {result['found_results']} results (sim: {result['avg_similarity']:.3f})")
                else:
                    print(f"      '{result['query']}': ❌ {result.get('error', 'Unknown error')}")
        else:
            print(f"   ❌ No successful search queries")
    
    # Recommendations
    print(f"\n💡 RECOMMENDATIONS:")
    
    if status['backend_status'] == 'Running' and status['frontend_status'] == 'Running' and status['search_working']:
        print(f"   🎉 SYSTEM IS OPERATIONAL!")
        print(f"   🌐 Access the application at: http://localhost:8501")
        print(f"   📖 API documentation at: http://localhost:8000/docs")
        
        print(f"\n   🔄 NEXT STEPS FOR OPTIMIZATION:")
        print(f"   1. Consider using larger 'legal_documents' collection (3,936 docs)")
        print(f"      - Requires switching to 768-dim embedding model")
        print(f"      - Would provide better search coverage")
        
        print(f"   2. Fine-tune search parameters for better relevance")
        print(f"   3. Test with real user queries")
        
    else:
        print(f"   🔧 TROUBLESHOOTING NEEDED:")
        if status['backend_status'] != 'Running':
            print(f"      - Fix backend API issues")
        if status['frontend_status'] != 'Running':
            print(f"      - Restart Streamlit frontend")
        if not status['search_working']:
            print(f"      - Debug search engine functionality")

def main():
    """Main function"""
    print_status_report()
    
    # Save report to file
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    filename = f"system_status_report_{timestamp}.txt"
    
    # Could implement file saving here if needed
    print(f"\n📄 Report completed")

if __name__ == "__main__":
    main()
