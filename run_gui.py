#!/usr/bin/env python3
"""
Launcher per l'interfaccia grafica del sistema di trading

Usage:
    python run_gui.py
"""

import sys
import os

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from gui import main

if __name__ == "__main__":
    print("=" * 70)
    print("CRYPTO TRADING SYSTEM - GUI")
    print("=" * 70)
    print("\nAvvio interfaccia grafica...\n")

    try:
        main()
    except KeyboardInterrupt:
        print("\n\nChiusura GUI...")
    except Exception as e:
        print(f"\nERRORE: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
