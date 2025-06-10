# DNOTI Legal Tech - Production Version

## 🚀 Quick Start

### One-Command Startup
```cmd
run_production.bat
```

### Manual Startup
```cmd
python start_production.py
```

## 📊 System Overview

- **Frontend**: Streamlit at http://localhost:8501
- **Backend**: FastAPI at http://localhost:8000
- **Database**: ChromaDB with 3,936+ legal documents
- **AI Model**: IBM Granite Multilingual Embeddings

## 🔧 Features

✅ **Semantic Search** - Natural language search through legal documents  
✅ **Similarity Filtering** - Adjustable relevance threshold  
✅ **Metadata Extraction** - Gutachten numbers, legal norms, dates  
✅ **Export Functionality** - CSV download of search results  
✅ **Professional UI** - Clean, responsive interface  
✅ **Production Ready** - Optimized and debugged  

## 📋 Requirements

- Python 3.8+
- 4GB RAM minimum
- 2GB free disk space
- Windows 10/11

## 🛠️ Troubleshooting

If you encounter issues:

1. **Database not found**: Run `python load_all_gutachten.py`
2. **API not responding**: Check if port 8000 is available
3. **Frontend not loading**: Check if port 8501 is available
4. **Memory issues**: Close other applications

## 📞 Support

For technical support, check the main `README.md` file.
