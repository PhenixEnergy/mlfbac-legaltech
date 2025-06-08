@echo off
:: Legal Tech Startup Script
:: Automated project initialization and service startup
:: Updated: June 2025

title Legal Tech - Automated Startup

echo =========================================
echo Legal Tech Semantic Search System
echo Automated Startup Script v2.0
echo =========================================
echo.

:: Check if Python is available
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python is not installed or not in PATH
    echo Please install Python 3.9+ and add it to PATH
    pause
    exit /b 1
)

:: Get current directory
set PROJECT_DIR=%~dp0
cd /d "%PROJECT_DIR%"

echo [INFO] Project Directory: %PROJECT_DIR%
echo.

:: Check for virtual environment
if not exist "venv\" (
    echo [SETUP] Creating virtual environment...
    python -m venv venv
    if errorlevel 1 (
        echo ERROR: Failed to create virtual environment
        pause
        exit /b 1
    )
    echo [SUCCESS] Virtual environment created
) else (
    echo [INFO] Virtual environment already exists
)

:: Activate virtual environment
echo [SETUP] Activating virtual environment...
call venv\Scripts\activate.bat
if errorlevel 1 (
    echo ERROR: Failed to activate virtual environment
    pause
    exit /b 1
)

:: Upgrade pip
echo [SETUP] Upgrading pip...
python -m pip install --upgrade pip --quiet

:: Install/Update dependencies
echo [SETUP] Installing/updating dependencies...
pip install -r requirements.txt --quiet
if errorlevel 1 (
    echo ERROR: Failed to install dependencies
    echo Trying to install core dependencies only...
    pip install streamlit fastapi uvicorn chromadb sentence-transformers --quiet
)

:: Create necessary directories
echo [SETUP] Creating directory structure...
if not exist "data\logs\" mkdir data\logs
if not exist "data\vectordb\" mkdir data\vectordb
if not exist "data\embeddings\" mkdir data\embeddings
if not exist "data\processed\" mkdir data\processed
if not exist "models\" mkdir models

:: Initialize logging
echo [SETUP] Initializing logging...
if not exist "data\logs\legaltech.log" (
    echo %date% %time% - Legal Tech System Started > data\logs\legaltech.log
)

:: Check if database exists and initialize if needed
echo [SETUP] Checking database status...
if not exist "data\vectordb\chroma.sqlite3" (
    if exist "Database\Original\dnoti_all.json" (
        echo [SETUP] Initializing database from source data...
        python scripts\setup_database.py --quick-setup
        if errorlevel 1 (
            echo WARNING: Database initialization failed - continuing with empty DB
        )
    ) else (
        echo WARNING: No source data found - starting with empty database
    )
) else (
    echo [INFO] Database already exists
)

:: Start services in background
echo.
echo =========================================
echo Starting Services
echo =========================================

:: Start FastAPI backend
echo [START] Starting FastAPI backend server...
start "Legal Tech API" cmd /k "cd /d "%PROJECT_DIR%" && venv\Scripts\activate.bat && python -m uvicorn src.api.main:app --reload --port 8000"

:: Wait a moment for API to start
timeout /t 3 /nobreak >nul

:: Check if LM Studio is running
echo [CHECK] Checking LM Studio connection...
curl -s http://localhost:1234/v1/models >nul 2>&1
if errorlevel 1 (
    echo.
    echo =========================================
    echo LM Studio Setup Required
    echo =========================================
    echo LM Studio is not running on port 1234
    echo.
    echo Please:
    echo 1. Start LM Studio
    echo 2. Load a model (recommended: deepseek-coder-v2-lite-16b-q8)
    echo 3. Start the local server on port 1234
    echo.
    echo The system will work with basic search, but AI generation
    echo will be limited without LM Studio.
    echo.
    pause
) else (
    echo [SUCCESS] LM Studio is running and accessible
)

:: Start Streamlit frontend
echo [START] Starting Streamlit frontend...
start "Legal Tech Frontend" cmd /k "cd /d "%PROJECT_DIR%" && venv\Scripts\activate.bat && streamlit run streamlit_app.py --server.port 8501"

:: Wait for services to start
echo.
echo [INFO] Waiting for services to initialize...
timeout /t 5 /nobreak >nul

:: Display service URLs
echo.
echo =========================================
echo Services Started Successfully!
echo =========================================
echo.
echo Frontend (Streamlit): http://localhost:8501
echo Backend API:          http://localhost:8000
echo API Documentation:    http://localhost:8000/docs
echo LM Studio:           http://localhost:1234
echo.
echo =========================================
echo System Status
echo =========================================

:: Check service status
curl -s http://localhost:8501 >nul 2>&1
if not errorlevel 1 (
    echo [✓] Streamlit Frontend: RUNNING
) else (
    echo [✗] Streamlit Frontend: STARTING...
)

curl -s http://localhost:8000/health >nul 2>&1
if not errorlevel 1 (
    echo [✓] FastAPI Backend:    RUNNING
) else (
    echo [✗] FastAPI Backend:    STARTING...
)

curl -s http://localhost:1234/v1/models >nul 2>&1
if not errorlevel 1 (
    echo [✓] LM Studio:          RUNNING
) else (
    echo [✗] LM Studio:          NOT CONNECTED
)

echo.
echo =========================================
echo Quick Actions
echo =========================================
echo 1. Press any key to open the web interface
echo 2. Close this window to stop monitoring
echo 3. Use Ctrl+C in service windows to stop individual services
echo.

pause

:: Open web interface
echo [INFO] Opening web interface...
start http://localhost:8501

echo.
echo [INFO] System is running. Monitor the service windows for logs.
echo [INFO] Press any key to exit this script (services will continue running)
pause >nul
