@echo off
title Legal Tech - Connection Fix

echo ==========================================
echo Legal Tech - Verbindungsproblem beheben
echo ==========================================
echo.

:: Ins Projektverzeichnis wechseln
cd /d "c:\Users\rafael.schumm\LegalTech\mlfbac-legaltech"

:: Alte Prozesse beenden
echo Beende alte Prozesse...
taskkill /f /im python.exe >nul 2>&1
taskkill /f /im streamlit.exe >nul 2>&1
timeout /t 2 /nobreak >nul

:: Virtual Environment aktivieren
echo Aktiviere Virtual Environment...
call venv\Scripts\activate.bat

echo.
echo ===========================================
echo Starte Services einzeln zur Diagnose...
echo ===========================================
echo.

:: Backend in separatem Fenster starten
echo [1/3] Starte FastAPI Backend...
start "Legal Tech Backend" cmd /k "title Legal Tech Backend && cd /d "c:\Users\rafael.schumm\LegalTech\mlfbac-legaltech" && call venv\Scripts\activate.bat && echo Backend wird gestartet... && python -m uvicorn src.api.main:app --host 0.0.0.0 --port 8000 --reload"

:: Warten auf Backend
echo Warte 8 Sekunden auf Backend-Start...
timeout /t 8 /nobreak >nul

:: Backend testen
echo [2/3] Teste Backend-Verbindung...
curl -s http://localhost:8000/health >nul 2>&1
if %errorlevel% equ 0 (
    echo ✓ Backend erfolgreich gestartet!
) else (
    echo ✗ Backend nicht erreichbar - prüfen Sie das Backend-Fenster
)

:: Frontend in separatem Fenster starten  
echo [3/3] Starte Streamlit Frontend...
start "Legal Tech Frontend" cmd /k "title Legal Tech Frontend && cd /d "c:\Users\rafael.schumm\LegalTech\mlfbac-legaltech" && call venv\Scripts\activate.bat && echo Frontend wird gestartet... && streamlit run streamlit_app.py --server.port 8501 --server.address 0.0.0.0 --server.headless false"

:: Warten auf Frontend
echo Warte 10 Sekunden auf Frontend-Start...
timeout /t 10 /nobreak >nul

:: Frontend testen
echo Teste Frontend-Verbindung...
curl -s http://localhost:8501 >nul 2>&1
if %errorlevel% equ 0 (
    echo ✓ Frontend erfolgreich gestartet!
) else (
    echo ✗ Frontend nicht erreichbar - prüfen Sie das Frontend-Fenster
)

echo.
echo ===========================================
echo Services Status:
echo ===========================================
echo Backend:  http://localhost:8000
echo Frontend: http://localhost:8501
echo.
echo Hinweise:
echo - Beide Services laufen in separaten Fenstern
echo - Schließen Sie diese Fenster NICHT
echo - Falls Probleme auftreten, prüfen Sie die Fenster-Ausgaben
echo ===========================================

:: Browser öffnen
echo Öffne Browser...
start http://localhost:8501

echo.
echo Drücken Sie eine beliebige Taste zum Beenden...
pause >nul
