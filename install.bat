@echo off
setlocal enabledelayedexpansion

echo OCR Scan Letter WebApp - Installation Script for Windows
echo ======================================================

:: Check if Python is installed
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ERROR: Python is not installed or not in PATH
    echo Please install Python 3.8 or higher from https://python.org
    pause
    exit /b 1
)

echo ✓ Python found

:: Check if pip is installed
pip --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ERROR: pip is not installed
    echo Please install pip
    pause
    exit /b 1
)

echo ✓ pip found

:: Check if Tesseract is installed
tesseract --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ⚠ Tesseract OCR not found
    echo Please install Tesseract OCR:
    echo 1. Download from: https://github.com/UB-Mannheim/tesseract/wiki
    echo 2. Install and add to PATH
    echo 3. Download Indonesian language data from: https://github.com/tesseract-ocr/tessdata
    echo.
    echo After installing Tesseract, run this script again.
    pause
    exit /b 1
)

echo ✓ Tesseract OCR found

:: Create virtual environment
if exist venv (
    echo ⚠ Virtual environment already exists
    set /p recreate="Do you want to recreate it? (y/N): "
    if /i "!recreate!"=="y" (
        rmdir /s /q venv
        echo ✓ Removed existing virtual environment
    ) else (
        echo ✓ Using existing virtual environment
        goto :install_deps
    )
)

echo Creating virtual environment...
python -m venv venv
echo ✓ Virtual environment created

:install_deps
:: Activate virtual environment and install dependencies
echo Activating virtual environment...
call venv\Scripts\activate.bat

echo Upgrading pip...
python -m pip install --upgrade pip

echo Installing Python dependencies...
pip install -r requirements.txt
echo ✓ Dependencies installed successfully

:: Create necessary directories
echo Creating necessary directories...
if not exist instance mkdir instance
if not exist static\ocr\uploads mkdir static\ocr\uploads
if not exist static\ocr\surat_masuk mkdir static\ocr\surat_masuk
if not exist static\ocr\surat_keluar mkdir static\ocr\surat_keluar
if not exist generated mkdir generated
echo ✓ Directories created

:: Create .env file
if not exist .env (
    echo Creating .env file...
    echo FLASK_APP=app.py > .env
    echo FLASK_ENV=development >> .env
    echo SECRET_KEY=your-secret-key-here >> .env
    echo DATABASE_URL=sqlite:///instance/app.db >> .env
    echo ✓ .env file created
) else (
    echo ⚠ .env file already exists
)

echo.
echo ======================================================
echo ✓ Installation completed successfully!
echo.
echo To run the application:
echo 1. Activate virtual environment: venv\Scripts\activate.bat
echo 2. Run the app: python app.py
echo 3. Open browser: http://localhost:5001
echo.
echo To deactivate virtual environment later: deactivate
echo.
pause 