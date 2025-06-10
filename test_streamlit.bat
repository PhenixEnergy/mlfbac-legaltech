@echo off
title Legal Tech - Streamlit Test
color 0A

echo ==========================================
echo    Legal Tech - Streamlit Fix Test
echo ==========================================
echo.

:: Ins Projektverzeichnis wechseln
cd /d "c:\Users\rafael.schumm\LegalTech\mlfbac-legaltech"

echo [INFO] Teste ob der Streamlit-Fix funktioniert hat...
echo.

:: Virtual Environment aktivieren
if exist "venv\Scripts\activate.bat" (
    echo [INFO] Aktiviere Virtual Environment...
    call venv\Scripts\activate.bat
) else (
    echo [ERROR] Virtual Environment nicht gefunden!
    pause
    exit /b 1
)

:: Test ausführen
echo [INFO] Führe Installation-Test aus...
python test_streamlit_fix.py

echo.
echo [INFO] Wenn der Test erfolgreich war, können Sie Streamlit starten:
echo   - streamlit run streamlit_test.py
echo   - streamlit run simple_app.py  
echo   - streamlit run streamlit_app.py
echo.
echo [INFO] URL: http://localhost:8501
echo.

pause
