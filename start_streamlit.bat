@echo off
echo === Legal Tech Streamlit Starter ===
echo.

:: Ins Projektverzeichnis wechseln
cd /d "c:\Users\rafael.schumm\LegalTech\mlfbac-legaltech"

:: Virtual Environment aktivieren
call venv\Scripts\activate.bat

:: Backend starten (separates Fenster)
echo Starte FastAPI Backend...
start "Legal Tech Backend" cmd /k "call venv\Scripts\activate.bat && python -m uvicorn src.api.main:app --host 127.0.0.1 --port 8000 --reload"

:: Kurz warten
timeout /t 5 /nobreak >nul

:: Streamlit Frontend starten (separates Fenster)
echo Starte Streamlit Frontend...
start "Legal Tech Frontend" cmd /k "call venv\Scripts\activate.bat && streamlit run streamlit_app.py --server.port 8501"

:: Warten bis Services gestartet sind
echo Warte auf Service-Start...
timeout /t 10 /nobreak >nul

:: Browser öffnen
echo Öffne Browser...
start http://localhost:8501

echo.
echo === Services gestartet ===
echo Backend:  http://localhost:8000
echo Frontend: http://localhost:8501
echo.
echo Drücken Sie eine beliebige Taste zum Beenden...
pause >nul
