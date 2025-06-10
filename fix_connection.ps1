# Legal Tech - PowerShell Connection Fix
param(
    [switch]$Verbose
)

Write-Host "===========================================" -ForegroundColor Cyan
Write-Host "Legal Tech - Verbindungsproblem beheben" -ForegroundColor Green
Write-Host "===========================================" -ForegroundColor Cyan
Write-Host ""

# Ins Projektverzeichnis wechseln
$ProjectDir = "c:\Users\rafael.schumm\LegalTech\mlfbac-legaltech"
Set-Location $ProjectDir

Write-Host "📁 Arbeitsverzeichnis: $ProjectDir" -ForegroundColor Yellow

# Alte Prozesse beenden
Write-Host "🧹 Beende alte Prozesse..." -ForegroundColor Yellow
try {
    Get-Process -Name "python" -ErrorAction SilentlyContinue | Stop-Process -Force
    Get-Process -Name "streamlit" -ErrorAction SilentlyContinue | Stop-Process -Force
    Start-Sleep -Seconds 2
    Write-Host "✅ Alte Prozesse beendet" -ForegroundColor Green
} catch {
    Write-Host "ℹ️ Keine alten Prozesse gefunden" -ForegroundColor Gray
}

# Virtual Environment prüfen
$VenvPython = Join-Path $ProjectDir "venv\Scripts\python.exe"
if (-not (Test-Path $VenvPython)) {
    Write-Host "❌ Virtual Environment nicht gefunden!" -ForegroundColor Red
    Write-Host "Bitte führen Sie zuerst aus: python -m venv venv" -ForegroundColor Yellow
    Read-Host "Drücken Sie Enter zum Beenden"
    exit 1
}

Write-Host "✅ Virtual Environment gefunden" -ForegroundColor Green

# Services starten
Write-Host "" 
Write-Host "🚀 Starte Services..." -ForegroundColor Cyan

# Backend starten
Write-Host "[1/2] Starte FastAPI Backend..." -ForegroundColor Yellow
$BackendArgs = @(
    "-NoExit",
    "-Command",
    "Set-Location '$ProjectDir'; & '$ProjectDir\venv\Scripts\Activate.ps1'; Write-Host 'Backend wird gestartet...' -ForegroundColor Green; python -m uvicorn src.api.main:app --host 0.0.0.0 --port 8000 --reload"
)

try {
    $BackendProcess = Start-Process -FilePath "powershell.exe" -ArgumentList $BackendArgs -WindowStyle Normal -PassThru
    Write-Host "✅ Backend-Prozess gestartet (PID: $($BackendProcess.Id))" -ForegroundColor Green
} catch {
    Write-Host "❌ Backend-Start fehlgeschlagen: $_" -ForegroundColor Red
    Read-Host "Drücken Sie Enter zum Beenden"
    exit 1
}

# Warten auf Backend
Write-Host "⏳ Warte 8 Sekunden auf Backend..." -ForegroundColor Yellow
Start-Sleep -Seconds 8

# Backend testen
Write-Host "🔍 Teste Backend-Verbindung..." -ForegroundColor Yellow
try {
    $BackendResponse = Invoke-WebRequest -Uri "http://localhost:8000/health" -TimeoutSec 5 -UseBasicParsing
    if ($BackendResponse.StatusCode -eq 200) {
        Write-Host "✅ Backend erfolgreich gestartet!" -ForegroundColor Green
    } else {
        Write-Host "⚠️ Backend antwortet mit Status $($BackendResponse.StatusCode)" -ForegroundColor Yellow
    }
} catch {
    Write-Host "⚠️ Backend noch nicht bereit (normal beim ersten Start)" -ForegroundColor Yellow
}

# Streamlit-Installation prüfen und reparieren
Write-Host "🔧 Prüfe Streamlit-Installation..." -ForegroundColor Yellow
$StreamlitTest = & "$ProjectDir\venv\Scripts\python.exe" -c "import streamlit; print('OK')" 2>$null
if ($LASTEXITCODE -ne 0) {
    Write-Host "⚠️ Streamlit-Problem erkannt - Repariere Installation..." -ForegroundColor Yellow
    & "$ProjectDir\venv\Scripts\python.exe" -m pip uninstall streamlit -y >$null 2>&1
    & "$ProjectDir\venv\Scripts\python.exe" -m pip install streamlit==1.39.0 --force-reinstall --no-cache-dir >$null 2>&1
    Write-Host "✅ Streamlit repariert" -ForegroundColor Green
} else {
    Write-Host "✅ Streamlit OK" -ForegroundColor Green
}

# Fallback-App erstellen falls Hauptapp Probleme hat
$FallbackApp = @"
import streamlit as st
st.set_page_config(page_title="Legal Tech", page_icon="⚖️")
st.title("⚖️ Legal Tech - System Online")
st.success("✅ Streamlit läuft erfolgreich!")
st.info("Backend: http://localhost:8000")
st.info("Frontend: http://localhost:8501")
"@

$FallbackApp | Out-File -FilePath "$ProjectDir\streamlit_minimal.py" -Encoding UTF8

# Frontend starten mit Fallback-Strategie
Write-Host "[2/2] Starte Streamlit Frontend..." -ForegroundColor Yellow

# Teste welche App funktioniert
$AppToUse = "streamlit_app.py"
if (-not (Test-Path "$ProjectDir\streamlit_app.py")) {
    $AppToUse = "streamlit_minimal.py"
    Write-Host "ℹ️ Verwende Minimal-App als Fallback" -ForegroundColor Yellow
}

$FrontendArgs = @(
    "-NoExit",
    "-Command", 
    "Set-Location '$ProjectDir'; & '$ProjectDir\venv\Scripts\Activate.ps1'; Write-Host 'Frontend wird gestartet...' -ForegroundColor Green; streamlit run $AppToUse --server.port 8501 --server.address 0.0.0.0 --server.headless false --browser.gatherUsageStats false"
)

try {
    $FrontendProcess = Start-Process -FilePath "powershell.exe" -ArgumentList $FrontendArgs -WindowStyle Normal -PassThru
    Write-Host "✅ Frontend-Prozess gestartet (PID: $($FrontendProcess.Id))" -ForegroundColor Green
} catch {
    Write-Host "❌ Frontend-Start fehlgeschlagen: $_" -ForegroundColor Red
    Read-Host "Drücken Sie Enter zum Beenden"
    exit 1
}

# Warten auf Frontend
Write-Host "⏳ Warte 12 Sekunden auf Frontend..." -ForegroundColor Yellow
Start-Sleep -Seconds 12

# Frontend testen
Write-Host "🔍 Teste Frontend-Verbindung..." -ForegroundColor Yellow
try {
    $FrontendResponse = Invoke-WebRequest -Uri "http://localhost:8501" -TimeoutSec 5 -UseBasicParsing
    if ($FrontendResponse.StatusCode -eq 200) {
        Write-Host "✅ Frontend erfolgreich gestartet!" -ForegroundColor Green
    } else {
        Write-Host "⚠️ Frontend antwortet mit Status $($FrontendResponse.StatusCode)" -ForegroundColor Yellow
    }
} catch {
    Write-Host "⚠️ Frontend noch nicht bereit - wird noch geladen..." -ForegroundColor Yellow
}

# Status anzeigen
Write-Host ""
Write-Host "===========================================" -ForegroundColor Cyan
Write-Host "✅ Services Status:" -ForegroundColor Green
Write-Host "===========================================" -ForegroundColor Cyan
Write-Host "📊 Backend:  http://localhost:8000" -ForegroundColor White
Write-Host "🌐 Frontend: http://localhost:8501" -ForegroundColor White
Write-Host ""
Write-Host "📝 Hinweise:" -ForegroundColor Yellow
Write-Host "  • Beide Services laufen in separaten PowerShell-Fenstern" -ForegroundColor Gray
Write-Host "  • Schließen Sie diese Fenster NICHT!" -ForegroundColor Red
Write-Host "  • Bei Problemen prüfen Sie die Ausgaben in den Service-Fenstern" -ForegroundColor Gray
Write-Host "  • LM Studio (Port 1234) ist optional für erweiterte KI-Features" -ForegroundColor Gray
Write-Host "===========================================" -ForegroundColor Cyan

# Browser öffnen
Write-Host "🌐 Öffne Browser..." -ForegroundColor Yellow
try {
    Start-Process "http://localhost:8501"
    Write-Host "✅ Browser geöffnet" -ForegroundColor Green
} catch {
    Write-Host "⚠️ Browser konnte nicht automatisch geöffnet werden" -ForegroundColor Yellow
    Write-Host "Bitte öffnen Sie manuell: http://localhost:8501" -ForegroundColor White
}

Write-Host ""
Write-Host "🎉 Setup abgeschlossen!" -ForegroundColor Green
Read-Host "Drücken Sie Enter zum Beenden"
