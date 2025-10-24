@echo off
REM Windows Installation Script for Crypto Trading System (Batch Version)
REM This script can run without PowerShell execution policy restrictions

echo ========================================
echo Crypto Trading System - Windows Installer
echo ========================================
echo.

REM Check if Python is available
echo Checking Python version...
python --version >nul 2>&1
if errorlevel 1 (
    echo Error: Python is not installed or not in PATH
    echo Please install Python 3.9 or higher from https://www.python.org
    pause
    exit /b 1
)

REM Get Python version
for /f "tokens=2" %%i in ('python --version 2^>^&1') do set PYTHON_VERSION=%%i
echo Found: Python %PYTHON_VERSION%

REM Extract major.minor version
for /f "tokens=1,2 delims=." %%a in ("%PYTHON_VERSION%") do (
    set MAJOR=%%a
    set MINOR=%%b
    set VERSION_SHORT=%%a%%b
)

echo Python version: %MAJOR%.%MINOR% (cp%VERSION_SHORT%)

REM Check if Python version is supported
if %MAJOR% LSS 3 (
    echo Error: Python 3.9 or higher is required
    pause
    exit /b 1
)
if %MAJOR% EQU 3 (
    if %MINOR% LSS 9 (
        echo Error: Python 3.9 or higher is required. You have Python %MAJOR%.%MINOR%
        pause
        exit /b 1
    )
)

REM Create virtual environment
echo.
echo Creating virtual environment...
if exist "venv\" (
    echo Virtual environment already exists. Skipping creation.
) else (
    python -m venv venv
    if errorlevel 1 (
        echo Error: Failed to create virtual environment
        pause
        exit /b 1
    )
    echo Virtual environment created successfully!
)

REM Activate virtual environment
echo.
echo Activating virtual environment...
call venv\Scripts\activate.bat
if errorlevel 1 (
    echo Error: Failed to activate virtual environment
    pause
    exit /b 1
)

REM Upgrade pip
echo.
echo Upgrading pip...
python -m pip install --upgrade pip
if errorlevel 1 (
    echo Warning: Failed to upgrade pip, continuing anyway...
)

REM Determine TA-Lib wheel URL based on Python version
set TALIB_URL=
if "%VERSION_SHORT%"=="39" set TALIB_URL=https://github.com/cgohlke/talib-build/releases/download/v0.4.28/TA_Lib-0.4.28-cp39-cp39-win_amd64.whl
if "%VERSION_SHORT%"=="310" set TALIB_URL=https://github.com/cgohlke/talib-build/releases/download/v0.4.28/TA_Lib-0.4.28-cp310-cp310-win_amd64.whl
if "%VERSION_SHORT%"=="311" set TALIB_URL=https://github.com/cgohlke/talib-build/releases/download/v0.4.28/TA_Lib-0.4.28-cp311-cp311-win_amd64.whl
if "%VERSION_SHORT%"=="312" set TALIB_URL=https://github.com/cgohlke/talib-build/releases/download/v0.4.28/TA_Lib-0.4.28-cp312-cp312-win_amd64.whl
if "%VERSION_SHORT%"=="313" set TALIB_URL=https://github.com/cgohlke/talib-build/releases/download/v0.4.28/TA_Lib-0.4.28-cp313-cp313-win_amd64.whl

if "%TALIB_URL%"=="" (
    echo Error: Python version %MAJOR%.%MINOR% is not supported for pre-built TA-Lib wheels
    echo Supported versions: 3.9, 3.10, 3.11, 3.12, 3.13
    echo Please see INSTALL.md for manual installation instructions
    pause
    exit /b 1
)

REM Install TA-Lib
echo.
echo Installing TA-Lib from pre-built wheel...
echo URL: %TALIB_URL%
pip install %TALIB_URL%
if errorlevel 1 (
    echo Error: TA-Lib installation failed
    echo Please see INSTALL.md for troubleshooting
    pause
    exit /b 1
)
echo TA-Lib installed successfully!

REM Install other dependencies
echo.
echo Installing other dependencies from requirements.txt...
echo This may take several minutes...
echo.

REM Install packages individually to avoid conflicts
echo Installing python-binance==1.0.19...
pip install python-binance==1.0.19 --no-deps

echo Installing ccxt==4.5.12...
pip install ccxt==4.5.12 --no-deps

echo Installing pandas==2.1.4...
pip install pandas==2.1.4 --no-deps

echo Installing numpy==1.26.2...
pip install numpy==1.26.2 --no-deps

echo Installing ta==0.11.0...
pip install ta==0.11.0 --no-deps

echo Installing pyarrow==14.0.1...
pip install pyarrow==14.0.1 --no-deps

echo Installing backtrader==1.9.78.123...
pip install backtrader==1.9.78.123 --no-deps

echo Installing vectorbt==0.26.0...
pip install vectorbt==0.26.0 --no-deps

echo Installing anthropic==0.18.1...
pip install anthropic==0.18.1 --no-deps

echo Installing openai==1.12.0...
pip install openai==1.12.0 --no-deps

echo Installing python-telegram-bot==20.7...
pip install python-telegram-bot==20.7 --no-deps

echo Installing pygame==2.5.2...
pip install pygame==2.5.2 --no-deps

echo Installing matplotlib==3.8.2...
pip install matplotlib==3.8.2 --no-deps

echo Installing plotly==5.18.0...
pip install plotly==5.18.0 --no-deps

echo Installing seaborn==0.13.0...
pip install seaborn==0.13.0 --no-deps

echo Installing mplfinance==0.12.10b0...
pip install mplfinance==0.12.10b0 --no-deps

echo Installing pyyaml==6.0.1...
pip install pyyaml==6.0.1 --no-deps

echo Installing python-dotenv==1.0.0...
pip install python-dotenv==1.0.0 --no-deps

echo Installing schedule==1.2.0...
pip install schedule==1.2.0 --no-deps

echo Installing aiohttp>=3.10.11...
pip install "aiohttp>=3.10.11" --no-deps

echo Installing websockets==12.0...
pip install websockets==12.0 --no-deps

echo Installing loguru==0.7.2...
pip install loguru==0.7.2 --no-deps

echo Installing pytest==7.4.3...
pip install pytest==7.4.3 --no-deps

echo Installing pytest-asyncio==0.21.1...
pip install pytest-asyncio==0.21.1 --no-deps

REM Install missing dependencies
echo.
echo Installing any missing dependencies...
pip install python-binance ccxt pandas numpy ta pyarrow backtrader vectorbt anthropic openai python-telegram-bot pygame matplotlib plotly seaborn mplfinance pyyaml python-dotenv schedule aiohttp websockets loguru pytest pytest-asyncio

REM Verify installation
echo.
echo Verifying installation...
python -c "import talib; import ccxt; import pandas; import numpy; print('All critical imports successful!')" 2>&1
if errorlevel 1 (
    echo Error: Verification failed
    echo Some imports are not working correctly
    echo Please check the error messages above
    pause
    exit /b 1
)

echo.
echo ========================================
echo Installation completed successfully!
echo ========================================
echo.
echo Next steps:
echo 1. Create a .env file with your API keys (see README.md)
echo 2. Configure trading settings in config/ directory
echo 3. Run: python main.py --mode live
echo.
echo To activate the virtual environment in future sessions:
echo venv\Scripts\activate.bat
echo.
pause
