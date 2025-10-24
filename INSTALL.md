# Installation Guide

This guide provides detailed installation instructions for the Crypto Trading System across different platforms.

## Table of Contents
- [System Requirements](#system-requirements)
- [Windows Installation](#windows-installation)
- [Linux Installation](#linux-installation)
- [macOS Installation](#macos-installation)
- [Troubleshooting](#troubleshooting)

## System Requirements

- **Python**: 3.9+ (3.10 or 3.11 recommended)
- **Pip**: Latest version
- **Git**: For cloning the repository
- **TA-Lib**: C library for technical analysis (platform-specific installation)

## Windows Installation

### Method 1: Anaconda/Miniconda (RECOMMENDED)

If you use Anaconda or Miniconda, this is the easiest method:

#### Step 1: Create and activate a conda environment

```cmd
conda create -n trading-system python=3.11
conda activate trading-system
```

#### Step 2: Run the automated conda installation script

```cmd
install_conda_windows.bat
```

This script:
- Verifies that a conda environment is activated
- Installs essential packages with conda (numpy, pandas, matplotlib, seaborn)
- Installs TA-Lib from pre-built wheels
- Installs all other dependencies with pip
- Verifies the installation

**Note**: You MUST activate your conda environment before running this script!

### Method 2: Automated Installation with venv (EASIEST for non-conda users)

We provide two automated installation scripts that handle everything for you:

#### Option A: Batch File (No Execution Policy Issues)

If you encounter PowerShell execution policy errors, use the batch file:

```cmd
install_windows.bat
```

This script:
- Works without PowerShell execution policy restrictions
- Automatically detects your Python version
- Creates a virtual environment
- Installs TA-Lib from pre-built wheels
- Installs all other dependencies
- Verifies the installation

**Simply double-click `install_windows.bat` or run it from Command Prompt.**

#### Option B: PowerShell Script

If you have PowerShell execution permissions:

```powershell
.\install_windows.ps1
```

**Note:** If you get an execution policy error like "execution of scripts is disabled", use Option A (batch file) instead, or temporarily bypass the policy:
```powershell
Set-ExecutionPolicy -ExecutionPolicy Bypass -Scope Process
.\install_windows.ps1
```

### Method 3: Using Pre-built Wheels (MANUAL)

If you prefer to install manually, this method avoids the need for Visual C++ Build Tools.

#### Step 1: Install Python Dependencies (except ta-lib)

```powershell
# Create and activate virtual environment
python -m venv provaLLMTrading
.\provaLLMTrading\Scripts\activate

# Upgrade pip
python -m pip install --upgrade pip

# Install dependencies except ta-lib
pip install -r requirements.txt --no-deps
pip install python-binance ccxt pandas numpy ta pyarrow backtrader vectorbt anthropic openai python-telegram-bot pygame matplotlib plotly seaborn mplfinance pyyaml python-dotenv schedule aiohttp websockets loguru pytest pytest-asyncio
```

#### Step 2: Install TA-Lib Using Pre-built Wheel

Download the appropriate pre-built wheel for your Python version from the unofficial repository:

**For Python 3.9:**
```powershell
pip install https://github.com/cgohlke/talib-build/releases/download/v0.4.28/TA_Lib-0.4.28-cp39-cp39-win_amd64.whl
```

**For Python 3.10:**
```powershell
pip install https://github.com/cgohlke/talib-build/releases/download/v0.4.28/TA_Lib-0.4.28-cp310-cp310-win_amd64.whl
```

**For Python 3.11:**
```powershell
pip install https://github.com/cgohlke/talib-build/releases/download/v0.4.28/TA_Lib-0.4.28-cp311-cp311-win_amd64.whl
```

**For Python 3.12:**
```powershell
pip install https://github.com/cgohlke/talib-build/releases/download/v0.4.28/TA_Lib-0.4.28-cp312-cp312-win_amd64.whl
```

#### Step 3: Verify Installation

```powershell
python -c "import talib; print(talib.__version__)"
```

If this prints the version (e.g., `0.4.28`), you're all set!

### Method 4: Install from Source (Advanced)

If you need to build from source, follow these steps:

#### Step 1: Install Visual C++ Build Tools

1. Download **Microsoft C++ Build Tools** from:
   https://visualstudio.microsoft.com/visual-cpp-build-tools/

2. Run the installer and select:
   - **Desktop development with C++**
   - Ensure "MSVC v142+" and "Windows 10/11 SDK" are checked

3. Restart your computer after installation

#### Step 2: Install TA-Lib C Library

1. Download TA-Lib C library (0.4.0) from:
   https://sourceforge.net/projects/ta-lib/files/ta-lib/0.4.0/ta-lib-0.4.0-msvc.zip

2. Extract to `C:\ta-lib`

3. The directory structure should be:
   ```
   C:\ta-lib\
   ├── c\
   │   ├── bin\
   │   ├── include\
   │   └── lib\
   ```

#### Step 3: Set Environment Variables

Add to your system PATH:
```
C:\ta-lib\c\bin
C:\ta-lib\c\include
C:\ta-lib\c\lib
```

Or set in PowerShell:
```powershell
$env:TA_LIBRARY_PATH = "C:\ta-lib\c\lib"
$env:TA_INCLUDE_PATH = "C:\ta-lib\c\include"
```

#### Step 4: Install Python Wrapper

```powershell
pip install ta-lib
```

## Linux Installation

### Method 1: Anaconda/Miniconda (RECOMMENDED)

If you use Anaconda or Miniconda, this is the easiest method:

#### Step 1: Create and activate a conda environment

```bash
conda create -n trading-system python=3.11
conda activate trading-system
```

#### Step 2: Run the automated conda installation script

```bash
./install_conda_linux_mac.sh
```

This script:
- Verifies that a conda environment is activated
- Installs essential packages with conda (numpy, pandas, matplotlib, seaborn)
- Attempts to install TA-Lib with conda
- Falls back to building from source if needed
- Installs all other dependencies with pip
- Verifies the installation

**Note**: You MUST activate your conda environment before running this script!

### Method 2: Automated Installation with venv

#### Automated Script

```bash
./install_linux_mac.sh
```

This script:
- Automatically detects your Linux distribution
- Installs TA-Lib C library
- Creates a virtual environment
- Installs all dependencies
- Verifies the installation

### Method 3: Manual Installation

### Ubuntu/Debian

```bash
# Install TA-Lib C library
sudo apt-get update
sudo apt-get install -y build-essential wget
cd /tmp
wget http://prdownloads.sourceforge.net/ta-lib/ta-lib-0.4.0-src.tar.gz
tar -xzf ta-lib-0.4.0-src.tar.gz
cd ta-lib/
./configure --prefix=/usr
make
sudo make install
sudo ldconfig

# Install Python dependencies
cd /path/to/Trading-system
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
```

### CentOS/RHEL/Fedora

```bash
# Install TA-Lib C library
sudo yum groupinstall "Development Tools"
sudo yum install wget
cd /tmp
wget http://prdownloads.sourceforge.net/ta-lib/ta-lib-0.4.0-src.tar.gz
tar -xzf ta-lib-0.4.0-src.tar.gz
cd ta-lib/
./configure --prefix=/usr
make
sudo make install
sudo ldconfig

# Install Python dependencies
cd /path/to/Trading-system
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
```

## macOS Installation

### Method 1: Anaconda/Miniconda (RECOMMENDED)

If you use Anaconda or Miniconda, this is the easiest method:

#### Step 1: Create and activate a conda environment

```bash
conda create -n trading-system python=3.11
conda activate trading-system
```

#### Step 2: Run the automated conda installation script

```bash
./install_conda_linux_mac.sh
```

This script:
- Verifies that a conda environment is activated
- Installs essential packages with conda (numpy, pandas, matplotlib, seaborn)
- Attempts to install TA-Lib with conda
- Falls back to Homebrew or building from source if needed
- Installs all other dependencies with pip
- Verifies the installation

**Note**: You MUST activate your conda environment before running this script!

### Method 2: Automated Installation with venv

#### Automated Script

```bash
./install_linux_mac.sh
```

This script:
- Installs TA-Lib using Homebrew or builds from source
- Creates a virtual environment
- Installs all dependencies
- Verifies the installation

### Method 3: Using Homebrew (Manual)

```bash
# Install TA-Lib C library
brew install ta-lib

# Install Python dependencies
cd /path/to/Trading-system
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
```

### Method 4: Building from Source

```bash
# Install TA-Lib C library
cd /tmp
wget http://prdownloads.sourceforge.net/ta-lib/ta-lib-0.4.0-src.tar.gz
tar -xzf ta-lib-0.4.0-src.tar.gz
cd ta-lib/
./configure --prefix=/usr/local
make
sudo make install

# Install Python dependencies
cd /path/to/Trading-system
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
```

## Docker Installation (All Platforms)

Create a `Dockerfile` in the project root:

```dockerfile
FROM python:3.11-slim

# Install TA-Lib C library
RUN apt-get update && apt-get install -y \
    build-essential \
    wget \
    && cd /tmp \
    && wget http://prdownloads.sourceforge.net/ta-lib/ta-lib-0.4.0-src.tar.gz \
    && tar -xzf ta-lib-0.4.0-src.tar.gz \
    && cd ta-lib \
    && ./configure --prefix=/usr \
    && make \
    && make install \
    && ldconfig \
    && rm -rf /tmp/ta-lib*

# Set working directory
WORKDIR /app

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

CMD ["python", "main.py", "--mode", "live"]
```

Build and run:
```bash
docker build -t crypto-trading-system .
docker run -it --env-file .env crypto-trading-system
```

## Post-Installation Setup

After installing dependencies, configure your environment:

### 1. Create Environment File

Create a `.env` file in the project root:

```env
# Binance API
BINANCE_API_KEY=your_api_key_here
BINANCE_API_SECRET=your_api_secret_here

# LLM Provider (choose one)
# Anthropic (Claude)
ANTHROPIC_API_KEY=your_anthropic_key_here
# OpenAI (GPT)
# OPENAI_API_KEY=your_openai_key_here
# OpenRouter (multiple models)
# OPENROUTER_API_KEY=your_openrouter_key_here

# Telegram Notifications
TELEGRAM_BOT_TOKEN=your_bot_token_here
TELEGRAM_CHAT_ID=your_chat_id_here
```

### 2. Configure Trading Settings

Edit the configuration files in the `config/` directory:
- `symbols.yaml`: Trading pairs
- `schedule.yaml`: Trading hours
- `trading_rules.py`: Entry/exit rules
- `settings.py`: General settings

### 3. Verify Installation

```bash
# Test imports
python -c "import talib, ccxt, pandas, numpy; print('All imports successful!')"

# Check Python version
python --version

# List installed packages
pip list
```

## Troubleshooting

### Windows Issues

#### Error: "execution of scripts is disabled" or "UnauthorizedAccess" (PowerShell)
- **Solution 1**: Use the batch file instead: `install_windows.bat`
- **Solution 2**: Temporarily bypass execution policy for the current session:
  ```powershell
  Set-ExecutionPolicy -ExecutionPolicy Bypass -Scope Process
  .\install_windows.ps1
  ```
- **Solution 3**: Enable scripts permanently (requires admin):
  ```powershell
  Set-ExecutionPolicy RemoteSigned
  ```

#### Error: "Microsoft Visual C++ 14.0 or greater is required"
- **Solution**: Use Method 1 (automated installation) or Method 2 (pre-built wheels) instead of building from source
- Alternatively, install Visual C++ Build Tools (see Method 3)

#### Error: "Cannot find ta-lib library"
- **Solution**: Ensure you've installed the C library to `C:\ta-lib`
- Check that environment variables are set correctly
- Use the pre-built wheel method to avoid this issue

#### Error: "ImportError: DLL load failed"
- **Solution**: Add `C:\ta-lib\c\bin` to your PATH
- Restart your terminal/PowerShell after adding to PATH
- Ensure you have the correct architecture (64-bit vs 32-bit)

### Linux Issues

#### Error: "ta-lib/func.h: No such file or directory"
- **Solution**: Install the TA-Lib C library first:
  ```bash
  sudo apt-get install libta-lib-dev
  ```

#### Error: "command 'gcc' failed"
- **Solution**: Install build tools:
  ```bash
  sudo apt-get install build-essential
  ```

### macOS Issues

#### Error: "ta_libc.h not found"
- **Solution**: Install TA-Lib with Homebrew:
  ```bash
  brew install ta-lib
  ```

#### Error: "clang: error: linker command failed"
- **Solution**: Install Xcode Command Line Tools:
  ```bash
  xcode-select --install
  ```

### General Issues

#### ImportError after installation
- Ensure virtual environment is activated
- Try uninstalling and reinstalling:
  ```bash
  pip uninstall ta-lib
  pip install ta-lib
  ```

#### Version conflicts
- Create a fresh virtual environment:
  ```bash
  python -m venv fresh_env
  source fresh_env/bin/activate  # or .\fresh_env\Scripts\activate on Windows
  pip install -r requirements.txt
  ```

## Alternative: Using `ta` Library Instead of `ta-lib`

If you continue to have issues with TA-Lib, you can modify the code to use the `ta` library, which is pure Python and doesn't require compilation:

```python
# Instead of:
import talib

# Use:
import ta

# The 'ta' library is already in requirements.txt
```

Note: You'll need to update the indicator calculation code to use the `ta` library's API, which is different from `talib`.

## Getting Help

If you encounter issues not covered here:

1. Check the [GitHub Issues](https://github.com/your-repo/issues)
2. Search for your specific error message
3. Open a new issue with:
   - Your operating system and version
   - Python version (`python --version`)
   - Complete error message
   - Steps you've already tried

---

**Installation Support**: For platform-specific help, please open an issue on GitHub with your system details.
