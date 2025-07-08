#!/usr/bin/env python3
"""
Setup script for OCR Scan Letter WebApp
"""

import os
import sys
import subprocess
from setuptools import setup, find_packages

def check_python_version():
    """Check if Python version is compatible"""
    if sys.version_info < (3, 8):
        print("Error: Python 3.8 or higher is required")
        sys.exit(1)

def check_tesseract():
    """Check if Tesseract is installed"""
    try:
        subprocess.run(['tesseract', '--version'], 
                      capture_output=True, check=True)
        print("✓ Tesseract OCR is installed")
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("✗ Tesseract OCR is not installed")
        print("Please install Tesseract OCR:")
        print("  macOS: brew install tesseract tesseract-lang")
        print("  Ubuntu: sudo apt install tesseract-ocr tesseract-ocr-ind")
        print("  Windows: Download from https://github.com/UB-Mannheim/tesseract/wiki")
        return False

def create_directories():
    """Create necessary directories"""
    directories = [
        'instance',
        'static/ocr/uploads',
        'static/ocr/surat_masuk',
        'static/ocr/surat_keluar',
        'generated'
    ]
    
    for directory in directories:
        os.makedirs(directory, exist_ok=True)
        print(f"✓ Created directory: {directory}")

def main():
    """Main setup function"""
    print("OCR Scan Letter WebApp Setup")
    print("=" * 40)
    
    # Check Python version
    check_python_version()
    print("✓ Python version is compatible")
    
    # Check Tesseract
    if not check_tesseract():
        print("\nPlease install Tesseract OCR first, then run this setup again.")
        sys.exit(1)
    
    # Create directories
    print("\nCreating directories...")
    create_directories()
    
    print("\nSetup completed successfully!")
    print("\nNext steps:")
    print("1. Install dependencies: pip install -r requirements.txt")
    print("2. Run the application: python app.py")
    print("3. Access the app at: http://localhost:5001")

if __name__ == "__main__":
    main() 