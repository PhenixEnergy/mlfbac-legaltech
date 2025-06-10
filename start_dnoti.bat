@echo off
echo.
echo ===============================================
echo   DNOTI Legal Tech - Production System
echo ===============================================
echo.

rem Change to script directory
cd /d "%~dp0"

rem Check if virtual environment exists
if exist ".venv\Scripts\activate.bat" (
    echo Activating virtual environment...
    call .venv\Scripts\activate.bat
) else (
    echo Virtual environment not found. Using system Python...
)

rem Check if Python is available
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python not found in PATH
    echo Please install Python 3.8+ and add it to PATH
    pause
    exit /b 1
)

echo.
echo Checking database status...
python -c "import chromadb; client = chromadb.PersistentClient(path='./chroma_db'); collection = client.get_collection('dnoti_gutachten'); print(f'✅ Database ready: {collection.count():,} documents')" 2>nul

if errorlevel 1 (
    echo ⚠️  Database not found. Loading documents...
    python load_all_gutachten.py
    if errorlevel 1 (
        echo ❌ Database setup failed!
        pause
        exit /b 1
    )
)

echo.
echo Starting FastAPI backend on port 8000...
start "DNOTI Backend" /min python -m uvicorn src.api.main:app --reload --host 0.0.0.0 --port 8000

echo Waiting for backend to start...
timeout /t 10 /nobreak >nul

echo.
echo Starting Streamlit frontend on port 8501...
start "DNOTI Frontend" python -m streamlit run streamlit_app_production.py --server.port 8501 --server.address 0.0.0.0 --browser.gatherUsageStats false

echo.
echo Waiting for frontend to start...
timeout /t 5 /nobreak >nul

echo.
echo ===============================================
echo   🎉 DNOTI Legal Tech is starting!
echo.
echo   🖥️  Frontend: http://localhost:8501
echo   🔧 Backend:  http://localhost:8000
echo   📚 API Docs: http://localhost:8000/docs
echo.
echo   Close this window to stop both services
echo ===============================================
echo.

rem Open browser
start http://localhost:8501

echo Press any key to stop all services...
pause >nul

echo.
echo Stopping services...
taskkill /f /im "python.exe" 2>nul
echo ✅ All services stopped.
pause
