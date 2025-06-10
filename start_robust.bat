@echo off
:: Legal Tech - Robuster Service Starter
:: Startet alle Services mit verbesserter Fehlerbehandlung

setlocal enabledelayedexpansion

title Legal Tech - Service Manager

:: Farbcodes
set "GREEN=[32m"
set "YELLOW=[33m"
set "RED=[31m"
set "CYAN=[36m"
set "RESET=[0m"

echo %CYAN%=========================================%RESET%
echo %GREEN%Legal Tech - Service Manager%RESET%
echo %CYAN%=========================================%RESET%
echo.

:: Ins Projektverzeichnis wechseln
cd /d "%~dp0"

:: Python Virtual Environment prüfen
if not exist "venv\Scripts\python.exe" (
    echo %RED%[ERROR] Virtual Environment nicht gefunden!%RESET%
    echo %YELLOW%Erstelle Virtual Environment...%RESET%
    python -m venv venv
    if errorlevel 1 (
        echo %RED%[ERROR] Konnte Virtual Environment nicht erstellen%RESET%
        pause
        exit /b 1
    )
)

:: Service Manager starten
echo %YELLOW%[INFO] Starte Service Manager...%RESET%
venv\Scripts\python.exe service_manager.py

if errorlevel 1 (
    echo %RED%[ERROR] Service Manager ist fehlgeschlagen%RESET%
    echo %YELLOW%Versuche alternative Methode...%RESET%
    goto :fallback_start
)

goto :end

:fallback_start
echo %YELLOW%[INFO] Fallback: Starte Services manuell...%RESET%

:: Virtual Environment aktivieren
call venv\Scripts\activate.bat

:: Backend in separatem Fenster starten
echo %YELLOW%[INFO] Starte Backend...%RESET%
start "Legal Tech Backend" cmd /k "call venv\Scripts\activate.bat && python -m uvicorn src.api.main:app --host 127.0.0.1 --port 8000 --reload"

:: Kurz warten
timeout /t 5 /nobreak >nul

:: Frontend in separatem Fenster starten
echo %YELLOW%[INFO] Starte Frontend...%RESET%
start "Legal Tech Frontend" cmd /k "call venv\Scripts\activate.bat && streamlit run streamlit_app.py --server.port 8501"

:: Browser öffnen
timeout /t 10 /nobreak >nul
start http://localhost:8501

echo %GREEN%[SUCCESS] Services gestartet!%RESET%
echo %CYAN%Backend: http://localhost:8000%RESET%
echo %CYAN%Frontend: http://localhost:8501%RESET%

:end
echo.
echo %YELLOW%Drücken Sie eine beliebige Taste zum Beenden...%RESET%
pause >nul
