# Windows Installation Script for Crypto Trading System
# This script automates the installation of dependencies including TA-Lib

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Crypto Trading System - Windows Installer" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Check Python version
Write-Host "Checking Python version..." -ForegroundColor Yellow
$pythonVersion = python --version 2>&1
Write-Host "Found: $pythonVersion" -ForegroundColor Green

# Extract Python version number
$versionMatch = [regex]::Match($pythonVersion, "Python (\d+\.\d+)")
if ($versionMatch.Success) {
    $version = $versionMatch.Groups[1].Value
    $majorMinor = $version -replace '\.', ''
    Write-Host "Python version: $version (cp$majorMinor)" -ForegroundColor Green
} else {
    Write-Host "Error: Could not detect Python version" -ForegroundColor Red
    exit 1
}

# Check if Python version is supported
if ($version -lt "3.9") {
    Write-Host "Error: Python 3.9 or higher is required. You have Python $version" -ForegroundColor Red
    exit 1
}

# Create virtual environment
Write-Host ""
Write-Host "Creating virtual environment..." -ForegroundColor Yellow
if (Test-Path ".\venv") {
    Write-Host "Virtual environment already exists. Skipping creation." -ForegroundColor Yellow
} else {
    python -m venv venv
    Write-Host "Virtual environment created successfully!" -ForegroundColor Green
}

# Activate virtual environment
Write-Host ""
Write-Host "Activating virtual environment..." -ForegroundColor Yellow
& .\venv\Scripts\Activate.ps1

# Upgrade pip
Write-Host ""
Write-Host "Upgrading pip..." -ForegroundColor Yellow
python -m pip install --upgrade pip

# Determine TA-Lib wheel URL based on Python version
$talibUrl = ""
switch ($majorMinor) {
    "39" { $talibUrl = "https://github.com/cgohlke/talib-build/releases/download/v0.4.28/TA_Lib-0.4.28-cp39-cp39-win_amd64.whl" }
    "310" { $talibUrl = "https://github.com/cgohlke/talib-build/releases/download/v0.4.28/TA_Lib-0.4.28-cp310-cp310-win_amd64.whl" }
    "311" { $talibUrl = "https://github.com/cgohlke/talib-build/releases/download/v0.4.28/TA_Lib-0.4.28-cp311-cp311-win_amd64.whl" }
    "312" { $talibUrl = "https://github.com/cgohlke/talib-build/releases/download/v0.4.28/TA_Lib-0.4.28-cp312-cp312-win_amd64.whl" }
    default {
        Write-Host "Error: Python version $version is not supported for pre-built TA-Lib wheels" -ForegroundColor Red
        Write-Host "Supported versions: 3.9, 3.10, 3.11, 3.12" -ForegroundColor Yellow
        Write-Host "Please see INSTALL.md for manual installation instructions" -ForegroundColor Yellow
        exit 1
    }
}

# Install TA-Lib
Write-Host ""
Write-Host "Installing TA-Lib from pre-built wheel..." -ForegroundColor Yellow
Write-Host "URL: $talibUrl" -ForegroundColor Cyan
pip install $talibUrl

if ($LASTEXITCODE -eq 0) {
    Write-Host "TA-Lib installed successfully!" -ForegroundColor Green
} else {
    Write-Host "Error: TA-Lib installation failed" -ForegroundColor Red
    Write-Host "Please see INSTALL.md for troubleshooting" -ForegroundColor Yellow
    exit 1
}

# Install other dependencies
Write-Host ""
Write-Host "Installing other dependencies from requirements.txt..." -ForegroundColor Yellow
Write-Host "This may take several minutes..." -ForegroundColor Yellow

# Install packages individually to avoid conflicts
$packages = @(
    "python-binance==1.0.19",
    "ccxt==4.5.12",
    "pandas==2.1.4",
    "numpy==1.26.2",
    "ta==0.11.0",
    "pyarrow==14.0.1",
    "backtrader==1.9.78.123",
    "vectorbt==0.26.0",
    "anthropic==0.18.1",
    "openai==1.12.0",
    "python-telegram-bot==20.7",
    "pygame==2.5.2",
    "matplotlib==3.8.2",
    "plotly==5.18.0",
    "seaborn==0.13.0",
    "mplfinance==0.12.10b0",
    "pyyaml==6.0.1",
    "python-dotenv==1.0.0",
    "schedule==1.2.0",
    "aiohttp>=3.10.11",
    "websockets==12.0",
    "loguru==0.7.2",
    "pytest==7.4.3",
    "pytest-asyncio==0.21.1"
)

foreach ($package in $packages) {
    Write-Host "Installing $package..." -ForegroundColor Cyan
    pip install $package --no-deps
}

# Install missing dependencies
Write-Host ""
Write-Host "Installing any missing dependencies..." -ForegroundColor Yellow
pip install python-binance ccxt pandas numpy ta pyarrow backtrader vectorbt anthropic openai python-telegram-bot pygame matplotlib plotly seaborn mplfinance pyyaml python-dotenv schedule aiohttp websockets loguru pytest pytest-asyncio

# Verify installation
Write-Host ""
Write-Host "Verifying installation..." -ForegroundColor Yellow
$verification = python -c "import talib; import ccxt; import pandas; import numpy; print('All critical imports successful!')" 2>&1

if ($LASTEXITCODE -eq 0) {
    Write-Host $verification -ForegroundColor Green
    Write-Host ""
    Write-Host "========================================" -ForegroundColor Green
    Write-Host "Installation completed successfully!" -ForegroundColor Green
    Write-Host "========================================" -ForegroundColor Green
    Write-Host ""
    Write-Host "Next steps:" -ForegroundColor Cyan
    Write-Host "1. Create a .env file with your API keys (see README.md)" -ForegroundColor White
    Write-Host "2. Configure trading settings in config/ directory" -ForegroundColor White
    Write-Host "3. Run: python main.py --mode live" -ForegroundColor White
    Write-Host ""
    Write-Host "To activate the virtual environment in future sessions:" -ForegroundColor Yellow
    Write-Host ".\venv\Scripts\Activate.ps1" -ForegroundColor White
} else {
    Write-Host "Error: Verification failed" -ForegroundColor Red
    Write-Host "Some imports are not working correctly" -ForegroundColor Red
    Write-Host "Please check the error messages above" -ForegroundColor Yellow
    exit 1
}
