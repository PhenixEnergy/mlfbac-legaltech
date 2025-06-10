# Legal Tech - Streamlit Test und Start
param(
    [switch]$TestOnly
)

Write-Host "===========================================" -ForegroundColor Cyan
Write-Host "Legal Tech - Streamlit Test und Start" -ForegroundColor Green
Write-Host "===========================================" -ForegroundColor Cyan
Write-Host ""

# Ins Projektverzeichnis wechseln
$ProjectDir = "c:\Users\rafael.schumm\LegalTech\mlfbac-legaltech"
Set-Location $ProjectDir

Write-Host "📁 Arbeitsverzeichnis: $ProjectDir" -ForegroundColor Yellow

# Virtual Environment aktivieren
Write-Host "🔧 Aktiviere Virtual Environment..." -ForegroundColor Yellow
& ".\venv\Scripts\Activate.ps1"

# Installation testen
Write-Host "🧪 Teste Streamlit-Installation..." -ForegroundColor Yellow
python test_streamlit_fix.py

if ($TestOnly) {
    Write-Host "✅ Test abgeschlossen (nur Test-Modus)" -ForegroundColor Green
    Read-Host "Drücken Sie Enter zum Beenden"
    exit 0
}

# Streamlit starten
Write-Host ""
Write-Host "🚀 Starte Streamlit..." -ForegroundColor Cyan

# Verfügbare Apps prüfen und beste auswählen
$AppsToTry = @("streamlit_test.py", "simple_app.py", "streamlit_app.py")
$AppToUse = $null

foreach ($App in $AppsToTry) {
    if (Test-Path $App) {
        Write-Host "✅ $App gefunden" -ForegroundColor Green
        $AppToUse = $App
        break
    }
}

if (-not $AppToUse) {
    Write-Host "❌ Keine Streamlit-App gefunden!" -ForegroundColor Red
    Read-Host "Drücken Sie Enter zum Beenden"
    exit 1
}

Write-Host "🎯 Verwende: $AppToUse" -ForegroundColor Green

# Streamlit in separatem Fenster starten
$StreamlitArgs = @(
    "-NoExit",
    "-Command",
    "Set-Location '$ProjectDir'; & '$ProjectDir\venv\Scripts\Activate.ps1'; Write-Host 'Starte $AppToUse...' -ForegroundColor Green; streamlit run $AppToUse --server.port 8501 --server.address 0.0.0.0"
)

try {
    $StreamlitProcess = Start-Process -FilePath "powershell.exe" -ArgumentList $StreamlitArgs -WindowStyle Normal -PassThru
    Write-Host "✅ Streamlit-Prozess gestartet (PID: $($StreamlitProcess.Id))" -ForegroundColor Green
} catch {
    Write-Host "❌ Streamlit-Start fehlgeschlagen: $_" -ForegroundColor Red
    Read-Host "Drücken Sie Enter zum Beenden"
    exit 1
}

# Warten auf Streamlit
Write-Host "⏳ Warte 8 Sekunden auf Streamlit..." -ForegroundColor Yellow
Start-Sleep -Seconds 8

# Streamlit testen
Write-Host "🔍 Teste Streamlit-Verbindung..." -ForegroundColor Yellow
try {
    $Response = Invoke-WebRequest -Uri "http://localhost:8501" -TimeoutSec 5 -UseBasicParsing
    if ($Response.StatusCode -eq 200) {
        Write-Host "✅ Streamlit erfolgreich gestartet!" -ForegroundColor Green
    } else {
        Write-Host "⚠️ Streamlit antwortet mit Status $($Response.StatusCode)" -ForegroundColor Yellow
    }
} catch {
    Write-Host "⚠️ Streamlit noch nicht bereit - wird noch geladen..." -ForegroundColor Yellow
}

# Browser öffnen
Write-Host "🌐 Öffne Browser..." -ForegroundColor Yellow
try {
    Start-Process "http://localhost:8501"
    Write-Host "✅ Browser geöffnet" -ForegroundColor Green
} catch {
    Write-Host "⚠️ Browser konnte nicht automatisch geöffnet werden" -ForegroundColor Yellow
}

# Status anzeigen
Write-Host ""
Write-Host "===========================================" -ForegroundColor Cyan
Write-Host "✅ Streamlit Status:" -ForegroundColor Green
Write-Host "===========================================" -ForegroundColor Cyan
Write-Host "🌐 Frontend: http://localhost:8501" -ForegroundColor White
Write-Host "📱 App:      $AppToUse" -ForegroundColor White
Write-Host "🆔 PID:      $($StreamlitProcess.Id)" -ForegroundColor White
Write-Host ""
Write-Host "📝 Hinweise:" -ForegroundColor Yellow
Write-Host "  • Streamlit läuft in separatem PowerShell-Fenster" -ForegroundColor Gray
Write-Host "  • Schließen Sie dieses Fenster NICHT!" -ForegroundColor Red
Write-Host "  • Bei Problemen prüfen Sie die Ausgabe im Streamlit-Fenster" -ForegroundColor Gray
Write-Host "===========================================" -ForegroundColor Cyan

Write-Host ""
Write-Host "🎉 Test und Start abgeschlossen!" -ForegroundColor Green
Read-Host "Drücken Sie Enter zum Beenden"
