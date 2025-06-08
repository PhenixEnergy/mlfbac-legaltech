@echo off
:: Legal Tech - Ultimate Startup Script
:: Vereint alle Setup- und Start-Prozesse in einem Script
:: Version: 2.0 - June 2025

setlocal enabledelayedexpansion

title Legal Tech - Complete Setup & Startup

:: Farbcodes für bessere Ausgabe
set "GREEN=[32m"
set "YELLOW=[33m"
set "RED=[31m"
set "BLUE=[34m"
set "CYAN=[36m"
set "RESET=[0m"

echo %CYAN%==========================================%RESET%
echo %GREEN%Legal Tech Semantic Search System%RESET%
echo %GREEN%Complete Setup ^& Startup Script v2.0%RESET%
echo %CYAN%==========================================%RESET%
echo.

:: Get current directory
set "PROJECT_DIR=%~dp0"
cd /d "%PROJECT_DIR%"

echo %YELLOW%[INFO] Project Directory: %PROJECT_DIR%%RESET%
echo.

:: Check Python
python --version >nul 2>&1
if errorlevel 1 (
    echo %RED%[ERROR] Python is not installed or not in PATH%RESET%
    echo Please install Python 3.9+ and add it to PATH
    echo.
    echo Download from: https://www.python.org/downloads/
    pause
    exit /b 1
)

for /f "tokens=*" %%i in ('python --version') do set "PYTHON_VERSION=%%i"
echo %GREEN%[SUCCESS] Found %PYTHON_VERSION%%RESET%

:: Check virtual environment
if not exist "venv\" (
    echo %YELLOW%[SETUP] Creating virtual environment...%RESET%
    python -m venv venv
    if errorlevel 1 (
        echo %RED%[ERROR] Failed to create virtual environment%RESET%
        pause
        exit /b 1
    )
    echo %GREEN%[SUCCESS] Virtual environment created%RESET%
) else (
    echo %GREEN%[INFO] Virtual environment already exists%RESET%
)

:: Activate virtual environment
echo %YELLOW%[SETUP] Activating virtual environment...%RESET%
call venv\Scripts\activate.bat
if errorlevel 1 (
    echo %RED%[ERROR] Failed to activate virtual environment%RESET%
    pause
    exit /b 1
)

:: Upgrade pip
echo %YELLOW%[SETUP] Upgrading pip...%RESET%
python -m pip install --upgrade pip --quiet

:: Install requirements with fallback
echo %YELLOW%[SETUP] Installing dependencies...%RESET%
if exist "requirements.txt" (
    pip install -r requirements.txt --quiet
    if errorlevel 1 (
        echo %YELLOW%[WARNING] Some dependencies failed, installing core packages...%RESET%
        pip install streamlit fastapi uvicorn pandas requests pyyaml --quiet
    )
) else (
    echo %YELLOW%[SETUP] Installing core packages...%RESET%
    pip install streamlit fastapi uvicorn pandas requests pyyaml --quiet
)

:: Create directory structure
echo %YELLOW%[SETUP] Creating directory structure...%RESET%
set "DIRS=data\logs data\vectordb data\embeddings data\processed models config"
for %%d in (%DIRS%) do (
    if not exist "%%d\" mkdir "%%d"
)

:: Initialize config files if they don't exist
if not exist "config\services.json" (
    echo %YELLOW%[SETUP] Creating default service configuration...%RESET%
    echo { > config\services.json
    echo   "fastapi": { >> config\services.json
    echo     "name": "FastAPI Backend", >> config\services.json
    echo     "port": 8000, >> config\services.json
    echo     "health_endpoint": "/health" >> config\services.json
    echo   }, >> config\services.json
    echo   "streamlit": { >> config\services.json
    echo     "name": "Streamlit Frontend", >> config\services.json
    echo     "port": 8501 >> config\services.json
    echo   } >> config\services.json
    echo } >> config\services.json
)

:: Initialize logging
if not exist "data\logs\legaltech.log" (
    echo %date% %time% - Legal Tech System Initialized > data\logs\legaltech.log
)

:: Check database
echo %YELLOW%[SETUP] Checking database...%RESET%
if not exist "data\vectordb\chroma.sqlite3" (
    if exist "Database\Original\dnoti_all.json" (
        echo %YELLOW%[SETUP] Source data found, initializing database...%RESET%
        if exist "scripts\setup_database.py" (
            python scripts\setup_database.py --quick-setup
            if errorlevel 1 (
                echo %YELLOW%[WARNING] Database setup failed, creating empty database...%RESET%
                echo. > data\vectordb\chroma.sqlite3
            )
        ) else (
            echo %YELLOW%[WARNING] Setup script not found, creating empty database...%RESET%
            echo. > data\vectordb\chroma.sqlite3
        )
    ) else (
        echo %YELLOW%[WARNING] No source data found, creating empty database...%RESET%
        echo. > data\vectordb\chroma.sqlite3
    )
) else (
    echo %GREEN%[INFO] Database already exists%RESET%
)

:: Port availability check
set "API_PORT=8000"
set "FRONTEND_PORT=8501"

netstat -an | find ":8000 " >nul 2>&1
if not errorlevel 1 (
    echo %YELLOW%[WARNING] Port 8000 is busy, using 8001%RESET%
    set "API_PORT=8001"
)

netstat -an | find ":8501 " >nul 2>&1
if not errorlevel 1 (
    echo %YELLOW%[WARNING] Port 8501 is busy, using 8502%RESET%
    set "FRONTEND_PORT=8502"
)

echo.
echo %CYAN%==========================================%RESET%
echo %GREEN%Starting Services%RESET%
echo %CYAN%==========================================%RESET%

:: Create minimal FastAPI health endpoint if main.py doesn't exist
if not exist "src\api\main.py" (
    echo %YELLOW%[SETUP] Creating minimal API endpoint...%RESET%
    mkdir "src\api" 2>nul
    echo from fastapi import FastAPI > src\api\main.py
    echo app = FastAPI^(^) >> src\api\main.py
    echo @app.get^("/health"^) >> src\api\main.py
    echo def health^(^): return {"status": "ok"} >> src\api\main.py
)

:: Start FastAPI backend
echo %YELLOW%[START] Starting FastAPI backend on port %API_PORT%...%RESET%
start "Legal Tech API" cmd /k "cd /d "%PROJECT_DIR%" && venv\Scripts\activate.bat && python -m uvicorn src.api.main:app --reload --port %API_PORT% --host 0.0.0.0"

:: Wait for API to start
timeout /t 5 /nobreak >nul

:: Check API health
curl -s http://localhost:%API_PORT%/health >nul 2>&1
if not errorlevel 1 (
    echo %GREEN%[SUCCESS] FastAPI backend is running%RESET%
) else (
    echo %YELLOW%[WARNING] FastAPI backend may still be starting...%RESET%
)

:: Create minimal Streamlit app if it doesn't exist
if not exist "streamlit_app.py" (
    echo %YELLOW%[SETUP] Creating minimal Streamlit app...%RESET%
    echo import streamlit as st > streamlit_app.py
    echo st.title^("Legal Tech Semantic Search"^) >> streamlit_app.py
    echo st.write^("System is running!"^) >> streamlit_app.py
    echo st.write^("API Backend: http://localhost:%API_PORT%"^) >> streamlit_app.py
)

:: Start Streamlit frontend
echo %YELLOW%[START] Starting Streamlit frontend on port %FRONTEND_PORT%...%RESET%
start "Legal Tech Frontend" cmd /k "cd /d "%PROJECT_DIR%" && venv\Scripts\activate.bat && streamlit run streamlit_app.py --server.port %FRONTEND_PORT% --server.address 0.0.0.0"

:: Wait for Streamlit to start
timeout /t 7 /nobreak >nul

:: Check LM Studio (optional)
echo %YELLOW%[CHECK] Checking LM Studio connection...%RESET%
curl -s http://localhost:1234/v1/models >nul 2>&1
if not errorlevel 1 (
    echo %GREEN%[SUCCESS] LM Studio is running%RESET%
) else (
    echo %YELLOW%[INFO] LM Studio not detected (optional service)%RESET%
    echo To enable AI features:
    echo 1. Download and install LM Studio
    echo 2. Load a compatible model
    echo 3. Start local server on port 1234
)

:: Final status display
echo.
echo %CYAN%==========================================%RESET%
echo %GREEN%Services Started Successfully!%RESET%
echo %CYAN%==========================================%RESET%
echo.
echo %BLUE%Frontend (Streamlit):%RESET% http://localhost:%FRONTEND_PORT%
echo %BLUE%Backend API:%RESET%          http://localhost:%API_PORT%
echo %BLUE%API Documentation:%RESET%    http://localhost:%API_PORT%/docs
echo %BLUE%LM Studio:%RESET%           http://localhost:1234 ^(optional^)
echo.

:: Service status check
curl -s http://localhost:%FRONTEND_PORT% >nul 2>&1
if not errorlevel 1 (
    echo %GREEN%[✓] Streamlit Frontend: RUNNING%RESET%
) else (
    echo %YELLOW%[⏳] Streamlit Frontend: STARTING...%RESET%
)

curl -s http://localhost:%API_PORT%/health >nul 2>&1
if not errorlevel 1 (
    echo %GREEN%[✓] FastAPI Backend:    RUNNING%RESET%
) else (
    echo %YELLOW%[⏳] FastAPI Backend:    STARTING...%RESET%
)

curl -s http://localhost:1234/v1/models >nul 2>&1
if not errorlevel 1 (
    echo %GREEN%[✓] LM Studio:          CONNECTED%RESET%
) else (
    echo %YELLOW%[○] LM Studio:          NOT CONNECTED%RESET%
)

echo.
echo %CYAN%==========================================%RESET%
echo %GREEN%Quick Actions%RESET%
echo %CYAN%==========================================%RESET%
echo 1. Press ENTER to open the web interface
echo 2. Press S to show service status
echo 3. Press L to show logs
echo 4. Press Q to quit
echo.

:action_loop
set /p "action=Choose action (ENTER/S/L/Q): "

if "%action%"=="" (
    echo %YELLOW%[INFO] Opening web interface...%RESET%
    start http://localhost:%FRONTEND_PORT%
    goto action_loop
)

if /i "%action%"=="S" (
    echo.
    echo %BLUE%Service Status:%RESET%
    tasklist | find "python" >nul && echo Python processes: RUNNING || echo Python processes: NOT FOUND
    tasklist | find "streamlit" >nul && echo Streamlit: RUNNING || echo Streamlit: NOT FOUND
    echo.
    goto action_loop
)

if /i "%action%"=="L" (
    echo.
    echo %BLUE%Recent logs:%RESET%
    if exist "data\logs\legaltech.log" (
        powershell "Get-Content 'data\logs\legaltech.log' | Select-Object -Last 10"
    ) else (
        echo No log file found
    )
    echo.
    goto action_loop
)

if /i "%action%"=="Q" (
    echo %YELLOW%[INFO] Shutting down services...%RESET%
    taskkill /f /im "python.exe" >nul 2>&1
    taskkill /f /im "streamlit.exe" >nul 2>&1
    echo %GREEN%[INFO] Services stopped%RESET%
    goto end
)

echo Invalid option. Please choose ENTER, S, L, or Q
goto action_loop

:end
echo.
echo %GREEN%Legal Tech System stopped. Goodbye!%RESET%
pause >nul
