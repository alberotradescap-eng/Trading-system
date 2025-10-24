#!/bin/bash

# Linux/macOS Installation Script for Crypto Trading System with Anaconda
# Prerequisites: Activate your conda environment BEFORE running this script
# Example: conda activate myenv

set -e

echo "========================================"
echo "Crypto Trading System - Conda Installer (Linux/macOS)"
echo "========================================"
echo ""

# Check if conda is available
echo "Checking for conda..."
if ! command -v conda &> /dev/null; then
    echo "Error: conda is not found in PATH"
    echo "Please make sure Anaconda/Miniconda is installed and in PATH"
    echo "You can add conda to PATH by running:"
    echo "  conda init"
    exit 1
fi

# Check if a conda environment is activated
echo "Checking if conda environment is active..."
if [ -z "$CONDA_DEFAULT_ENV" ]; then
    echo "Error: No conda environment is activated!"
    echo ""
    echo "Please activate your conda environment first:"
    echo "  conda activate your_env_name"
    echo ""
    echo "Or create a new environment:"
    echo "  conda create -n trading-system python=3.11"
    echo "  conda activate trading-system"
    echo ""
    exit 1
fi

echo "Active environment: $CONDA_DEFAULT_ENV"
echo ""

# Detect OS
OS="$(uname -s)"
case "${OS}" in
    Linux*)     MACHINE=Linux;;
    Darwin*)    MACHINE=Mac;;
    *)          MACHINE="UNKNOWN:${OS}"
esac

echo "Detected OS: ${MACHINE}"

# Check Python version
echo ""
echo "Checking Python version..."
PYTHON_VERSION=$(python --version 2>&1 | awk '{print $2}')
PYTHON_MAJOR=$(echo $PYTHON_VERSION | cut -d. -f1)
PYTHON_MINOR=$(echo $PYTHON_VERSION | cut -d. -f2)

echo "Found: Python $PYTHON_VERSION"

if [ "$PYTHON_MAJOR" -lt 3 ] || ([ "$PYTHON_MAJOR" -eq 3 ] && [ "$PYTHON_MINOR" -lt 9 ]); then
    echo "Error: Python 3.9 or higher is required. You have Python $PYTHON_VERSION"
    exit 1
fi

# Upgrade pip
echo ""
echo "Upgrading pip..."
python -m pip install --upgrade pip

# Install essential packages with conda (faster and better for scientific computing)
echo ""
echo "Installing essential packages with conda..."
echo "This may take several minutes..."
echo ""

conda install -y numpy pandas matplotlib seaborn || echo "Warning: Some conda packages failed to install, continuing with pip..."

# Install TA-Lib
echo ""
echo "Installing TA-Lib..."

# Check if TA-Lib C library is already installed
if [ "$MACHINE" = "Mac" ]; then
    # Try to install with conda first (easiest)
    echo "Attempting to install TA-Lib with conda..."
    conda install -y -c conda-forge ta-lib && TALIB_INSTALLED=true || TALIB_INSTALLED=false

    if [ "$TALIB_INSTALLED" = false ]; then
        echo "Conda installation failed, trying Homebrew..."
        if command -v brew &> /dev/null; then
            brew install ta-lib || echo "Homebrew installation failed"
        else
            echo "Warning: Homebrew not found. You may need to install TA-Lib manually."
        fi
    fi
elif [ "$MACHINE" = "Linux" ]; then
    # Try to install with conda first
    echo "Attempting to install TA-Lib with conda..."
    conda install -y -c conda-forge ta-lib && TALIB_INSTALLED=true || TALIB_INSTALLED=false

    if [ "$TALIB_INSTALLED" = false ]; then
        echo "Conda installation failed, building from source..."

        # Install build dependencies if needed
        if command -v apt-get &> /dev/null; then
            echo "Using apt-get to install build dependencies..."
            sudo apt-get update
            sudo apt-get install -y build-essential wget
        elif command -v yum &> /dev/null; then
            echo "Using yum to install build dependencies..."
            sudo yum groupinstall -y "Development Tools"
            sudo yum install -y wget
        fi

        # Build from source
        cd /tmp
        wget http://prdownloads.sourceforge.net/ta-lib/ta-lib-0.4.0-src.tar.gz
        tar -xzf ta-lib-0.4.0-src.tar.gz
        cd ta-lib/
        ./configure --prefix=/usr
        make
        sudo make install
        sudo ldconfig
        cd -
        rm -rf /tmp/ta-lib*
    fi
fi

# Install TA-Lib Python wrapper
echo ""
echo "Installing TA-Lib Python wrapper..."
pip install ta-lib==0.4.28

if [ $? -eq 0 ]; then
    echo "TA-Lib Python wrapper installed successfully!"
else
    echo "Warning: TA-Lib Python wrapper installation failed"
    echo "The system will continue, but TA-Lib features may not work"
fi

# Install all other dependencies with pip
echo ""
echo "Installing remaining dependencies with pip..."
echo "This may take several minutes..."
echo ""

pip install \
    python-binance==1.0.19 \
    ccxt==4.5.12 \
    ta==0.11.0 \
    pyarrow==14.0.1 \
    backtrader==1.9.78.123 \
    vectorbt==0.26.0 \
    anthropic==0.18.1 \
    openai==1.12.0 \
    python-telegram-bot==20.7 \
    pygame==2.5.2 \
    plotly==5.18.0 \
    mplfinance==0.12.10b0 \
    pyyaml==6.0.1 \
    python-dotenv==1.0.0 \
    schedule==1.2.0 \
    "aiohttp>=3.10.11" \
    websockets==12.0 \
    loguru==0.7.2 \
    pytest==7.4.3 \
    pytest-asyncio==0.21.1

# Verify installation
echo ""
echo "Verifying installation..."
python -c "import talib; import ccxt; import pandas; import numpy; print('All critical imports successful!')"

if [ $? -eq 0 ]; then
    echo ""
    echo "========================================"
    echo "Installation completed successfully!"
    echo "========================================"
    echo ""
    echo "Environment: $CONDA_DEFAULT_ENV"
    echo ""
    echo "Next steps:"
    echo "1. Create a .env file with your API keys (see README.md)"
    echo "2. Configure trading settings in config/ directory"
    echo "3. Run: python main.py --mode live"
    echo ""
else
    echo "Warning: Verification had some issues"
    echo "Please check the error messages above"
    echo "Some imports may not be working correctly"
fi
