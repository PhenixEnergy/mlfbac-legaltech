@echo off
title DNOTI Legal Tech - Streamlit App
echo ==========================================
echo DNOTI Legal Tech - Streamlit Anwendung
echo ==========================================
echo.
echo Starte Streamlit-Anwendung...
echo.

REM Aktiviere virtuelle Umgebung falls vorhanden
if exist "venv\Scripts\activate.bat" (
    echo Aktiviere virtuelle Umgebung...
    call venv\Scripts\activate.bat
)

REM Starte Streamlit-Anwendung
echo Starte die Anwendung auf http://localhost:8505
echo.
streamlit run simple_app.py --server.port 8505

pause
