# Legal Tech PowerShell Startup Script
# Enhanced automation with better error handling and service management
# Updated: June 2025

param(
    [switch]$QuickSetup,
    [switch]$SkipLMStudio,
    [string]$Port = "8501",
    [string]$ApiPort = "8000"
)

# Set execution policy for current session
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope Process -Force

Write-Host "=========================================" -ForegroundColor Cyan
Write-Host "Legal Tech Semantic Search System" -ForegroundColor Green
Write-Host "PowerShell Startup Script v2.0" -ForegroundColor Green
Write-Host "=========================================" -ForegroundColor Cyan
Write-Host ""

# Get script directory
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $ScriptDir

Write-Host "[INFO] Project Directory: $ScriptDir" -ForegroundColor Yellow
Write-Host ""

# Function to check if command exists
function Test-Command {
    param($Command)
    try {
        Get-Command $Command -ErrorAction Stop | Out-Null
        return $true
    } catch {
        return $false
    }
}

# Function to check if port is available
function Test-Port {
    param($Port)
    try {
        $connection = New-Object System.Net.Sockets.TcpClient
        $connection.ConnectAsync("localhost", $Port).Wait(1000)
        $connection.Close()
        return $true  # Port is in use
    } catch {
        return $false  # Port is available
    }
}

# Function to wait for service
function Wait-ForService {
    param($Url, $ServiceName, $MaxWait = 30)
    
    Write-Host "[WAIT] Waiting for $ServiceName to start..." -ForegroundColor Yellow
    $timeout = $MaxWait
    
    do {
        try {
            $response = Invoke-WebRequest -Uri $Url -TimeoutSec 2 -UseBasicParsing -ErrorAction Stop
            if ($response.StatusCode -eq 200) {
                Write-Host "[SUCCESS] $ServiceName is running!" -ForegroundColor Green
                return $true
            }
        } catch {
            Start-Sleep -Seconds 1
            $timeout--
        }
    } while ($timeout -gt 0)
    
    Write-Host "[WARNING] $ServiceName may not be fully ready" -ForegroundColor Yellow
    return $false
}

# Check Python installation
if (-not (Test-Command "python")) {
    Write-Host "[ERROR] Python is not installed or not in PATH" -ForegroundColor Red
    Write-Host "Please install Python 3.9+ and add it to PATH" -ForegroundColor Red
    Read-Host "Press Enter to exit"
    exit 1
}

$pythonVersion = python --version 2>&1
Write-Host "[INFO] Found: $pythonVersion" -ForegroundColor Green

# Check/Create virtual environment
if (-not (Test-Path "venv")) {
    Write-Host "[SETUP] Creating virtual environment..." -ForegroundColor Cyan
    python -m venv venv
    if ($LASTEXITCODE -ne 0) {
        Write-Host "[ERROR] Failed to create virtual environment" -ForegroundColor Red
        Read-Host "Press Enter to exit"
        exit 1
    }
    Write-Host "[SUCCESS] Virtual environment created" -ForegroundColor Green
} else {
    Write-Host "[INFO] Virtual environment already exists" -ForegroundColor Green
}

# Activate virtual environment
Write-Host "[SETUP] Activating virtual environment..." -ForegroundColor Cyan
& ".\venv\Scripts\Activate.ps1"

# Upgrade pip
Write-Host "[SETUP] Upgrading pip..." -ForegroundColor Cyan
python -m pip install --upgrade pip --quiet

# Install/Update dependencies
Write-Host "[SETUP] Installing/updating dependencies..." -ForegroundColor Cyan
pip install -r requirements.txt --quiet
if ($LASTEXITCODE -ne 0) {
    Write-Host "[WARNING] Some dependencies failed to install" -ForegroundColor Yellow
    Write-Host "[SETUP] Installing core dependencies only..." -ForegroundColor Cyan
    pip install streamlit fastapi uvicorn pandas --quiet
}

# Create necessary directories
Write-Host "[SETUP] Creating directory structure..." -ForegroundColor Cyan
$directories = @("data\logs", "data\vectordb", "data\embeddings", "data\processed", "models")
foreach ($dir in $directories) {
    if (-not (Test-Path $dir)) {
        New-Item -ItemType Directory -Path $dir -Force | Out-Null
    }
}

# Initialize logging
$logFile = "data\logs\legaltech.log"
if (-not (Test-Path $logFile)) {
    "$(Get-Date) - Legal Tech System Started" | Out-File -FilePath $logFile -Encoding UTF8
}

# Database setup
Write-Host "[SETUP] Checking database status..." -ForegroundColor Cyan
if (-not (Test-Path "data\vectordb\chroma.sqlite3")) {
    if (Test-Path "Database\Original\dnoti_all.json") {
        if ($QuickSetup) {
            Write-Host "[SETUP] Running quick database setup..." -ForegroundColor Cyan
            python scripts\setup_database.py --quick-setup
        } else {
            Write-Host "[SETUP] Full database setup required" -ForegroundColor Yellow
            $response = Read-Host "Run full database setup? (y/N)"
            if ($response -eq 'y' -or $response -eq 'Y') {
                python scripts\setup_database.py
            } else {
                Write-Host "[INFO] Skipping database setup - using empty database" -ForegroundColor Yellow
            }
        }
    } else {
        Write-Host "[WARNING] No source data found - starting with empty database" -ForegroundColor Yellow
    }
} else {
    Write-Host "[INFO] Database already exists" -ForegroundColor Green
}

# Check for port conflicts
if (Test-Port $Port) {
    Write-Host "[WARNING] Port $Port is already in use" -ForegroundColor Yellow
    $Port = [string]([int]$Port + 1)
    Write-Host "[INFO] Using alternative port: $Port" -ForegroundColor Yellow
}

if (Test-Port $ApiPort) {
    Write-Host "[WARNING] API Port $ApiPort is already in use" -ForegroundColor Yellow
    $ApiPort = [string]([int]$ApiPort + 1)
    Write-Host "[INFO] Using alternative API port: $ApiPort" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "=========================================" -ForegroundColor Cyan
Write-Host "Starting Services" -ForegroundColor Green
Write-Host "=========================================" -ForegroundColor Cyan

# Start FastAPI backend
Write-Host "[START] Starting FastAPI backend server..." -ForegroundColor Cyan
$apiJob = Start-Job -ScriptBlock {
    param($dir, $port)
    Set-Location $dir
    & ".\venv\Scripts\Activate.ps1"
    python -m uvicorn src.api.main:app --reload --port $port --host 0.0.0.0
} -ArgumentList $ScriptDir, $ApiPort

Start-Sleep -Seconds 3

# Check LM Studio (if not skipped)
if (-not $SkipLMStudio) {
    Write-Host "[CHECK] Checking LM Studio connection..." -ForegroundColor Cyan
    try {
        $lmResponse = Invoke-WebRequest -Uri "http://localhost:1234/v1/models" -TimeoutSec 5 -UseBasicParsing -ErrorAction Stop
        Write-Host "[SUCCESS] LM Studio is running and accessible" -ForegroundColor Green
    } catch {
        Write-Host ""
        Write-Host "=========================================" -ForegroundColor Yellow
        Write-Host "LM Studio Setup Required" -ForegroundColor Yellow
        Write-Host "=========================================" -ForegroundColor Yellow
        Write-Host "LM Studio is not running on port 1234" -ForegroundColor Yellow
        Write-Host ""
        Write-Host "Please:" -ForegroundColor White
        Write-Host "1. Start LM Studio" -ForegroundColor White
        Write-Host "2. Load a model (recommended: deepseek-coder-v2-lite-16b-q8)" -ForegroundColor White
        Write-Host "3. Start the local server on port 1234" -ForegroundColor White
        Write-Host ""
        Write-Host "The system will work with basic search, but AI generation" -ForegroundColor Yellow
        Write-Host "will be limited without LM Studio." -ForegroundColor Yellow
        Write-Host ""
        Read-Host "Press Enter to continue"
    }
}

# Start Streamlit frontend
Write-Host "[START] Starting Streamlit frontend..." -ForegroundColor Cyan
$streamlitJob = Start-Job -ScriptBlock {
    param($dir, $port)
    Set-Location $dir
    & ".\venv\Scripts\Activate.ps1"
    streamlit run streamlit_app.py --server.port $port --server.address 0.0.0.0
} -ArgumentList $ScriptDir, $Port

# Wait for services to start
Write-Host ""
Write-Host "[INFO] Waiting for services to initialize..." -ForegroundColor Yellow
Start-Sleep -Seconds 5

# Check service status
Write-Host ""
Write-Host "=========================================" -ForegroundColor Cyan
Write-Host "Service Status" -ForegroundColor Green
Write-Host "=========================================" -ForegroundColor Cyan

$frontendReady = Wait-ForService "http://localhost:$Port" "Streamlit Frontend" 15
$backendReady = Wait-ForService "http://localhost:$ApiPort/health" "FastAPI Backend" 15

# Display URLs
Write-Host ""
Write-Host "=========================================" -ForegroundColor Cyan
Write-Host "Services Available" -ForegroundColor Green
Write-Host "=========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Frontend (Streamlit): http://localhost:$Port" -ForegroundColor White
Write-Host "Backend API:          http://localhost:$ApiPort" -ForegroundColor White
Write-Host "API Documentation:    http://localhost:$ApiPort/docs" -ForegroundColor White
Write-Host "LM Studio:           http://localhost:1234" -ForegroundColor White
Write-Host ""

# Final status check
if ($frontendReady) {
    Write-Host "[✓] Streamlit Frontend: RUNNING" -ForegroundColor Green
} else {
    Write-Host "[✗] Streamlit Frontend: STARTING..." -ForegroundColor Yellow
}

if ($backendReady) {
    Write-Host "[✓] FastAPI Backend:    RUNNING" -ForegroundColor Green
} else {
    Write-Host "[✗] FastAPI Backend:    STARTING..." -ForegroundColor Yellow
}

try {
    $lmCheck = Invoke-WebRequest -Uri "http://localhost:1234/v1/models" -TimeoutSec 2 -UseBasicParsing -ErrorAction Stop
    Write-Host "[✓] LM Studio:          RUNNING" -ForegroundColor Green
} catch {
    Write-Host "[✗] LM Studio:          NOT CONNECTED" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "=========================================" -ForegroundColor Cyan
Write-Host "Quick Actions" -ForegroundColor Green
Write-Host "=========================================" -ForegroundColor Cyan
Write-Host "1. Press 'O' to open the web interface" -ForegroundColor White
Write-Host "2. Press 'S' to show service status" -ForegroundColor White
Write-Host "3. Press 'L' to show logs" -ForegroundColor White
Write-Host "4. Press 'Q' to quit (stops all services)" -ForegroundColor White
Write-Host ""

# Interactive loop
do {
    Write-Host "Enter command (O/S/L/Q): " -NoNewline -ForegroundColor Cyan
    $key = Read-Host
    
    switch ($key.ToUpper()) {
        'O' {
            Write-Host "[INFO] Opening web interface..." -ForegroundColor Yellow
            Start-Process "http://localhost:$Port"
        }
        'S' {
            Write-Host "[INFO] Checking service status..." -ForegroundColor Yellow
            Write-Host "Streamlit Job State: $($streamlitJob.State)" -ForegroundColor White
            Write-Host "FastAPI Job State: $($apiJob.State)" -ForegroundColor White
        }
        'L' {
            Write-Host "[INFO] Showing recent logs..." -ForegroundColor Yellow
            if (Test-Path $logFile) {
                Get-Content $logFile -Tail 10
            } else {
                Write-Host "No log file found" -ForegroundColor Yellow
            }
        }
        'Q' {
            Write-Host "[INFO] Stopping services..." -ForegroundColor Yellow
            Stop-Job $streamlitJob -ErrorAction SilentlyContinue
            Stop-Job $apiJob -ErrorAction SilentlyContinue
            Remove-Job $streamlitJob -ErrorAction SilentlyContinue
            Remove-Job $apiJob -ErrorAction SilentlyContinue
            Write-Host "[INFO] All services stopped" -ForegroundColor Green
            break
        }
        default {
            Write-Host "[INFO] Invalid option. Use O/S/L/Q" -ForegroundColor Yellow
        }
    }
} while ($true)

Write-Host ""
Write-Host "Legal Tech System stopped. Goodbye!" -ForegroundColor Green
