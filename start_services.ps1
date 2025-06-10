# Legal Tech - Multi-Service Starter
# Startet alle benötigten Services für das Legal Tech System

Write-Host "=== Legal Tech Service Starter ===" -ForegroundColor Cyan
Write-Host "Starting all required services..." -ForegroundColor Yellow

# Wechsel ins Projektverzeichnis
$ProjectDir = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $ProjectDir

# Virtual Environment aktivieren
Write-Host "Activating virtual environment..." -ForegroundColor Green
& ".\venv\Scripts\Activate.ps1"

# Backend Service in separatem Fenster starten
Write-Host "Starting FastAPI Backend..." -ForegroundColor Green
Start-Process powershell -ArgumentList @(
    "-NoExit", 
    "-Command", 
    "cd '$ProjectDir'; .\venv\Scripts\Activate.ps1; python -m uvicorn src.api.main:app --host 127.0.0.1 --port 8000 --reload"
) -WindowStyle Normal

# Warte kurz, damit Backend startet
Start-Sleep -Seconds 3

# Frontend Service in separatem Fenster starten  
Write-Host "Starting Streamlit Frontend..." -ForegroundColor Green
Start-Process powershell -ArgumentList @(
    "-NoExit",
    "-Command", 
    "cd '$ProjectDir'; .\venv\Scripts\Activate.ps1; streamlit run streamlit_app.py --server.port 8501 --server.headless false"
) -WindowStyle Normal

# Warte kurz, damit Frontend startet
Start-Sleep -Seconds 5

# Browser öffnen
Write-Host "Opening browser..." -ForegroundColor Green
Start-Process "http://localhost:8501"

Write-Host "=== Services Started ===" -ForegroundColor Cyan
Write-Host "FastAPI Backend: http://localhost:8000" -ForegroundColor Yellow
Write-Host "Streamlit Frontend: http://localhost:8501" -ForegroundColor Yellow
Write-Host "" -ForegroundColor Yellow
Write-Host "Note: LM Studio must be started separately on port 1234 for full functionality" -ForegroundColor Red
Write-Host "Press any key to exit..." -ForegroundColor Gray
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
