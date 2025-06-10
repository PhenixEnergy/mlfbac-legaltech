@echo off
title Legal Tech - Streamlit Startup Fix
color 0A

echo ==========================================
echo    Legal Tech - Streamlit Reparatur
echo ==========================================
echo.

:: Ins Projektverzeichnis wechseln
cd /d "c:\Users\rafael.schumm\LegalTech\mlfbac-legaltech"

echo [INFO] Starte Streamlit-Reparatur...
echo.

:: Python-Reparatur-Skript ausführen
python fix_streamlit_startup.py

echo.
echo ==========================================
echo [INFO] Reparatur abgeschlossen
echo ==========================================
pause
