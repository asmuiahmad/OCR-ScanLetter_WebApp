#!/bin/bash

# OCR Scan Letter WebApp Installation Script
# This script will install all dependencies and setup the application

set -e  # Exit on any error

echo "OCR Scan Letter WebApp - Installation Script"
echo "============================================="

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${GREEN}✓${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}⚠${NC} $1"
}

print_error() {
    echo -e "${RED}✗${NC} $1"
}

# Check if Python is installed
check_python() {
    if command -v python3 &> /dev/null; then
        PYTHON_VERSION=$(python3 -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')")
        print_status "Python $PYTHON_VERSION found"
        return 0
    elif command -v python &> /dev/null; then
        PYTHON_VERSION=$(python -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')")
        print_status "Python $PYTHON_VERSION found"
        return 0
    else
        print_error "Python is not installed"
        echo "Please install Python 3.8 or higher"
        exit 1
    fi
}

# Check if pip is installed
check_pip() {
    if command -v pip3 &> /dev/null; then
        print_status "pip3 found"
        PIP_CMD="pip3"
    elif command -v pip &> /dev/null; then
        print_status "pip found"
        PIP_CMD="pip"
    else
        print_error "pip is not installed"
        echo "Please install pip"
        exit 1
    fi
}

# Check if virtualenv is installed
check_virtualenv() {
    if command -v virtualenv &> /dev/null; then
        print_status "virtualenv found"
        return 0
    else
        print_warning "virtualenv not found, installing..."
        $PIP_CMD install virtualenv
        print_status "virtualenv installed"
    fi
}

# Install Tesseract based on OS
install_tesseract() {
    if command -v tesseract &> /dev/null; then
        print_status "Tesseract OCR is already installed"
        return 0
    fi
    
    print_warning "Tesseract OCR not found, attempting to install..."
    
    # Detect OS
    if [[ "$OSTYPE" == "darwin"* ]]; then
        # macOS
        if command -v brew &> /dev/null; then
            print_status "Installing Tesseract via Homebrew..."
            brew install tesseract tesseract-lang
        else
            print_error "Homebrew not found. Please install Homebrew first:"
            echo "  /bin/bash -c \"\$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)\""
            exit 1
        fi
    elif [[ "$OSTYPE" == "linux-gnu"* ]]; then
        # Linux
        if command -v apt-get &> /dev/null; then
            print_status "Installing Tesseract via apt..."
            sudo apt-get update
            sudo apt-get install -y tesseract-ocr tesseract-ocr-ind
        elif command -v yum &> /dev/null; then
            print_status "Installing Tesseract via yum..."
            sudo yum install -y tesseract tesseract-langpack-ind
        else
            print_error "Package manager not supported. Please install Tesseract manually."
            exit 1
        fi
    else
        print_error "Unsupported OS. Please install Tesseract manually."
        exit 1
    fi
    
    print_status "Tesseract OCR installed successfully"
}

# Create virtual environment
create_venv() {
    if [ -d "venv" ]; then
        print_warning "Virtual environment already exists"
        read -p "Do you want to recreate it? (y/N): " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            rm -rf venv
            print_status "Removed existing virtual environment"
        else
            print_status "Using existing virtual environment"
            return 0
        fi
    fi
    
    print_status "Creating virtual environment..."
    virtualenv venv
    print_status "Virtual environment created"
}

# Activate virtual environment and install dependencies
install_dependencies() {
    print_status "Activating virtual environment..."
    source venv/bin/activate
    
    print_status "Upgrading pip..."
    pip install --upgrade pip
    
    print_status "Installing Python dependencies..."
    pip install -r requirements.txt
    
    print_status "Dependencies installed successfully"
}

# Create necessary directories
create_directories() {
    print_status "Creating necessary directories..."
    
    directories=(
        "instance"
        "static/ocr/uploads"
        "static/ocr/surat_masuk"
        "static/ocr/surat_keluar"
        "generated"
    )
    
    for dir in "${directories[@]}"; do
        mkdir -p "$dir"
        print_status "Created directory: $dir"
    done
}

# Create .env file
create_env_file() {
    if [ ! -f ".env" ]; then
        print_status "Creating .env file..."
        cat > .env << EOF
FLASK_APP=app.py
FLASK_ENV=development
SECRET_KEY=$(python -c "import secrets; print(secrets.token_hex(32))")
DATABASE_URL=sqlite:///instance/app.db
EOF
        print_status ".env file created"
    else
        print_warning ".env file already exists"
    fi
}

# Main installation process
main() {
    echo "Starting installation..."
    echo
    
    # Check prerequisites
    check_python
    check_pip
    check_virtualenv
    
    # Install Tesseract
    install_tesseract
    
    # Setup Python environment
    create_venv
    install_dependencies
    
    # Create directories
    create_directories
    
    # Create .env file
    create_env_file
    
    echo
    echo "============================================="
    print_status "Installation completed successfully!"
    echo
    echo "To run the application:"
    echo "1. Activate virtual environment: source venv/bin/activate"
    echo "2. Run the app: python app.py"
    echo "3. Open browser: http://localhost:5001"
    echo
    echo "To deactivate virtual environment later: deactivate"
    echo
}

# Run main function
main "$@" 