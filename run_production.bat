@echo off
echo.
echo ===============================================
echo   DNOTI Legal Tech - Production Startup
echo ===============================================
echo.

rem Check if Python is available
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python not found in PATH
    echo Please install Python 3.8+ and add it to PATH
    pause
    exit /b 1
)

rem Change to script directory
cd /d "%~dp0"

rem Activate virtual environment if it exists
if exist ".venv\Scripts\activate.bat" (
    echo Activating virtual environment...
    call .venv\Scripts\activate.bat
)

rem Run production startup script
echo Starting DNOTI Legal Tech...
python start_production.py

pause
