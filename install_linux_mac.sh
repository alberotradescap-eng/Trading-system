#!/bin/bash

# Linux/macOS Installation Script for Crypto Trading System
# This script automates the installation of dependencies including TA-Lib

set -e

echo "========================================"
echo "Crypto Trading System - Linux/macOS Installer"
echo "========================================"
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
PYTHON_VERSION=$(python3 --version 2>&1 | awk '{print $2}')
PYTHON_MAJOR=$(echo $PYTHON_VERSION | cut -d. -f1)
PYTHON_MINOR=$(echo $PYTHON_VERSION | cut -d. -f2)

echo "Found: Python $PYTHON_VERSION"

if [ "$PYTHON_MAJOR" -lt 3 ] || ([ "$PYTHON_MAJOR" -eq 3 ] && [ "$PYTHON_MINOR" -lt 9 ]); then
    echo "Error: Python 3.9 or higher is required. You have Python $PYTHON_VERSION"
    exit 1
fi

# Install TA-Lib C library
echo ""
echo "Installing TA-Lib C library..."

if [ "$MACHINE" = "Mac" ]; then
    # macOS installation
    if command -v brew &> /dev/null; then
        echo "Using Homebrew to install TA-Lib..."
        brew install ta-lib
    else
        echo "Homebrew not found. Installing from source..."
        cd /tmp
        wget http://prdownloads.sourceforge.net/ta-lib/ta-lib-0.4.0-src.tar.gz
        tar -xzf ta-lib-0.4.0-src.tar.gz
        cd ta-lib/
        ./configure --prefix=/usr/local
        make
        sudo make install
        cd -
        rm -rf /tmp/ta-lib*
    fi
elif [ "$MACHINE" = "Linux" ]; then
    # Linux installation
    if command -v apt-get &> /dev/null; then
        # Debian/Ubuntu
        echo "Using apt-get to install build dependencies..."
        sudo apt-get update
        sudo apt-get install -y build-essential wget
    elif command -v yum &> /dev/null; then
        # CentOS/RHEL/Fedora
        echo "Using yum to install build dependencies..."
        sudo yum groupinstall -y "Development Tools"
        sudo yum install -y wget
    fi

    echo "Building TA-Lib from source..."
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
else
    echo "Unsupported operating system: $MACHINE"
    exit 1
fi

echo "TA-Lib C library installed successfully!"

# Create virtual environment
echo ""
echo "Creating virtual environment..."
if [ -d "venv" ]; then
    echo "Virtual environment already exists. Skipping creation."
else
    python3 -m venv venv
    echo "Virtual environment created successfully!"
fi

# Activate virtual environment
echo ""
echo "Activating virtual environment..."
source venv/bin/activate

# Upgrade pip
echo ""
echo "Upgrading pip..."
python -m pip install --upgrade pip

# Install TA-Lib Python wrapper
echo ""
echo "Installing TA-Lib Python wrapper..."
pip install ta-lib==0.4.28

if [ $? -eq 0 ]; then
    echo "TA-Lib Python wrapper installed successfully!"
else
    echo "Error: TA-Lib Python wrapper installation failed"
    echo "Please see INSTALL.md for troubleshooting"
    exit 1
fi

# Install other dependencies
echo ""
echo "Installing other dependencies from requirements.txt..."
echo "This may take several minutes..."

# Install packages
pip install python-binance==1.0.19 \
    ccxt==4.5.12 \
    pandas==2.1.4 \
    numpy==1.26.2 \
    ta==0.11.0 \
    pyarrow==14.0.1 \
    backtrader==1.9.78.123 \
    vectorbt==0.26.0 \
    anthropic==0.18.1 \
    openai==1.12.0 \
    python-telegram-bot==20.7 \
    pygame==2.5.2 \
    matplotlib==3.8.2 \
    plotly==5.18.0 \
    seaborn==0.13.0 \
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
    echo "Next steps:"
    echo "1. Create a .env file with your API keys (see README.md)"
    echo "2. Configure trading settings in config/ directory"
    echo "3. Run: python main.py --mode live"
    echo ""
    echo "To activate the virtual environment in future sessions:"
    echo "source venv/bin/activate"
else
    echo "Error: Verification failed"
    echo "Some imports are not working correctly"
    echo "Please check the error messages above"
    exit 1
fi
