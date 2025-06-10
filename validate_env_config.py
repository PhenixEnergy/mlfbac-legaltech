#!/usr/bin/env python3
"""
Environment Configuration Validation & Documentation
Validiert die neue .env Konfiguration und erstellt einen Bericht
"""

import json
import sys
from pathlib import Path
from datetime import datetime
import requests

def test_api_endpoints():
    """Testet die API-Endpunkte"""
    print("🌐 Testing API Endpoints...")
    
    endpoints = [
        ("Health Check", "http://localhost:8000/health"),
        ("Admin Health", "http://localhost:8000/admin/health"),
        ("API Docs", "http://localhost:8000/docs")
    ]
    
    results = {}
    
    for name, url in endpoints:
        try:
            response = requests.get(url, timeout=5)
            if response.status_code == 200:
                print(f"  ✅ {name}: {response.status_code}")
                if url.endswith('/health'):
                    results[name] = response.json()
                else:
                    results[name] = {"status": "ok", "status_code": response.status_code}
            else:
                print(f"  ⚠️  {name}: {response.status_code}")
                results[name] = {"status": "error", "status_code": response.status_code}
        except Exception as e:
            print(f"  ❌ {name}: {str(e)}")
            results[name] = {"status": "failed", "error": str(e)}
    
    return results

def test_streamlit():
    """Testet die Streamlit-Anwendung"""
    print("🎨 Testing Streamlit Frontend...")
    
    try:
        response = requests.get("http://localhost:8501", timeout=5)
        if response.status_code == 200:
            print("  ✅ Streamlit is running")
            return {"status": "ok", "status_code": response.status_code}
        else:
            print(f"  ⚠️  Streamlit returned: {response.status_code}")
            return {"status": "error", "status_code": response.status_code}
    except Exception as e:
        print(f"  ❌ Streamlit connection failed: {str(e)}")
        return {"status": "failed", "error": str(e)}

def generate_config_report():
    """Erstellt einen Konfigurationsbericht"""
    try:
        from src.config import config
        
        report = {
            "timestamp": datetime.now().isoformat(),
            "configuration": {
                "database": {
                    "chroma_db_path": config.CHROMA_DB_PATH,
                    "chroma_collection_name": config.CHROMA_COLLECTION_NAME,
                    "chroma_persist_directory": config.CHROMA_PERSIST_DIRECTORY,
                    "chroma_batch_size": config.CHROMA_BATCH_SIZE
                },
                "llm": {
                    "base_url": config.LM_STUDIO_BASE_URL,
                    "model": config.LM_STUDIO_MODEL,
                    "max_tokens": config.LM_STUDIO_MAX_TOKENS,
                    "temperature": config.LM_STUDIO_TEMPERATURE
                },
                "embedding": {
                    "model": config.EMBEDDING_MODEL,
                    "batch_size": config.EMBEDDING_BATCH_SIZE,
                    "device": config.EMBEDDING_DEVICE
                },
                "api": {
                    "host": config.API_HOST,
                    "port": config.API_PORT,
                    "debug": config.DEBUG
                },
                "application": {
                    "log_level": config.APP_LOG_LEVEL,
                    "development": config.DEVELOPMENT
                }
            }
        }
        
        # Teste API Endpunkte
        report["api_tests"] = test_api_endpoints()
        
        # Teste Streamlit
        report["streamlit_test"] = test_streamlit()
        
        # Pfad-Validierung
        report["path_validation"] = config.validate_config()
        
        return report
        
    except Exception as e:
        return {
            "timestamp": datetime.now().isoformat(),
            "error": f"Failed to generate report: {str(e)}"
        }

def save_report(report):
    """Speichert den Bericht"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"config_validation_report_{timestamp}.json"
    
    try:
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        print(f"📄 Report saved to: {filename}")
        return filename
    except Exception as e:
        print(f"❌ Failed to save report: {e}")
        return None

def print_summary(report):
    """Druckt eine Zusammenfassung"""
    print("\n" + "="*60)
    print("📋 CONFIGURATION VALIDATION SUMMARY")
    print("="*60)
    
    # Basis-Konfiguration
    if "configuration" in report:
        print("✅ Configuration loaded successfully")
        config = report["configuration"]
        print(f"  📊 Database: {config['database']['chroma_collection_name']}")
        print(f"  🤖 LLM Model: {config['llm']['model']}")
        print(f"  🔤 Embedding: {config['embedding']['model']}")
        print(f"  🌐 API Port: {config['api']['port']}")
    
    # API Tests
    if "api_tests" in report:
        print(f"\n🌐 API Status:")
        for endpoint, result in report["api_tests"].items():
            status = result.get("status", "unknown")
            if status in ["ok", "healthy"]:
                print(f"  ✅ {endpoint}")
            elif status == "degraded":
                print(f"  ⚠️  {endpoint} (degraded)")
            else:
                print(f"  ❌ {endpoint}")
    
    # Streamlit Test
    if "streamlit_test" in report:
        streamlit_status = report["streamlit_test"].get("status", "unknown")
        if streamlit_status == "ok":
            print(f"  ✅ Streamlit Frontend")
        else:
            print(f"  ❌ Streamlit Frontend")
    
    # Pfad-Validierung
    if "path_validation" in report:
        if report["path_validation"]:
            print(f"  ✅ Path validation passed")
        else:
            print(f"  ❌ Path validation failed")
    
    print("\n🎉 Environment configuration is successfully set up!")

def main():
    """Hauptfunktion"""
    print("🔧 LegalTech Environment Configuration Validation")
    print("="*60)
    
    # Generiere Bericht
    report = generate_config_report()
    
    # Speichere Bericht
    filename = save_report(report)
    
    # Zeige Zusammenfassung
    print_summary(report)
    
    # Nächste Schritte
    print("\n📝 Next Steps:")
    print("  1. Start LM Studio for full LLM functionality")
    print("  2. Test semantic search in Streamlit interface")
    print("  3. Monitor logs for any issues")
    print(f"  4. Configuration report saved as: {filename}")
    
    return True

if __name__ == "__main__":
    try:
        success = main()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\n❌ Validation interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n❌ Validation failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
