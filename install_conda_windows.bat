@echo off
REM Windows Installation Script for Crypto Trading System with Anaconda
REM Prerequisites: Activate your conda environment BEFORE running this script
REM Example: conda activate myenv

echo ========================================
echo Crypto Trading System - Conda Installer (Windows)
echo ========================================
echo.

REM Check if conda is available
echo Checking for conda...
where conda >nul 2>&1
if errorlevel 1 (
    echo Error: conda is not found in PATH
    echo Please make sure Anaconda/Miniconda is installed and in PATH
    echo You can add conda to PATH by running:
    echo   conda init
    pause
    exit /b 1
)

REM Check if a conda environment is activated
echo Checking if conda environment is active...
if "%CONDA_DEFAULT_ENV%"=="" (
    echo Error: No conda environment is activated!
    echo.
    echo Please activate your conda environment first:
    echo   conda activate your_env_name
    echo.
    echo Or create a new environment:
    echo   conda create -n trading-system python=3.11
    echo   conda activate trading-system
    echo.
    pause
    exit /b 1
)

echo Active environment: %CONDA_DEFAULT_ENV%
echo.

REM Check Python version
echo Checking Python version...
python --version >nul 2>&1
if errorlevel 1 (
    echo Error: Python is not available in this environment
    pause
    exit /b 1
)

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

REM Upgrade pip
echo.
echo Upgrading pip...
python -m pip install --upgrade pip
if errorlevel 1 (
    echo Warning: Failed to upgrade pip, continuing anyway...
)

REM Install essential packages with conda (faster and better for scientific computing)
echo.
echo Installing essential packages with conda...
echo This may take several minutes...
echo.

conda install -y numpy pandas matplotlib seaborn
if errorlevel 1 (
    echo Warning: Some conda packages failed to install, continuing with pip...
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

REM Install all other dependencies with pip
echo.
echo Installing remaining dependencies with pip...
echo This may take several minutes...
echo.

pip install ^
    python-binance==1.0.19 ^
    ccxt==4.5.12 ^
    ta==0.11.0 ^
    pyarrow==14.0.1 ^
    backtrader==1.9.78.123 ^
    vectorbt==0.26.0 ^
    anthropic==0.18.1 ^
    openai==1.12.0 ^
    python-telegram-bot==20.7 ^
    pygame==2.5.2 ^
    plotly==5.18.0 ^
    mplfinance==0.12.10b0 ^
    pyyaml==6.0.1 ^
    python-dotenv==1.0.0 ^
    schedule==1.2.0 ^
    "aiohttp>=3.10.11" ^
    websockets==12.0 ^
    loguru==0.7.2 ^
    pytest==7.4.3 ^
    pytest-asyncio==0.21.1

if errorlevel 1 (
    echo Warning: Some packages failed to install
    echo Please check the error messages above
)

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
echo Environment: %CONDA_DEFAULT_ENV%
echo.
echo Next steps:
echo 1. Create a .env file with your API keys (see README.md)
echo 2. Configure trading settings in config/ directory
echo 3. Run: python main.py --mode live
echo.
pause
