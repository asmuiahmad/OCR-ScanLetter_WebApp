#!/bin/bash

# =============================================================================
# OCR SCANLETTER WEB APPLICATION - INSTALLATION SCRIPT
# =============================================================================
# Quick installation script for the OCR application
# Usage: ./install.sh [dev|prod|minimal]
# =============================================================================

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
NC='\033[0m' # No Color

# Function to print colored output
print_header() {
    echo -e "${PURPLE}🚀 $1${NC}"
    echo "=============================================="
}

print_success() {
    echo -e "${GREEN}✓${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}⚠${NC} $1"
}

print_error() {
    echo -e "${RED}✗${NC} $1"
}

print_info() {
    echo -e "${BLUE}ℹ${NC} $1"
}

# Function to check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Function to detect OS
detect_os() {
    if [[ "$OSTYPE" == "linux-gnu"* ]]; then
        echo "linux"
    elif [[ "$OSTYPE" == "darwin"* ]]; then
        echo "macos"
    elif [[ "$OSTYPE" == "msys" ]] || [[ "$OSTYPE" == "cygwin" ]]; then
        echo "windows"
    else
        echo "unknown"
    fi
}

# Function to install system dependencies
install_system_deps() {
    local os=$(detect_os)
    
    print_header "Installing System Dependencies"
    
    case $os in
        "linux")
            print_info "Detected Linux system"
            if command_exists apt-get; then
                print_info "Using apt-get package manager"
                sudo apt-get update
                sudo apt-get install -y \
                    tesseract-ocr \
                    tesseract-ocr-ind \
                    tesseract-ocr-eng \
                    libtesseract-dev \
                    libleptonica-dev \
                    pkg-config \
                    libpoppler-cpp-dev \
                    libcairo2-dev \
                    libpango1.0-dev \
                    libgdk-pixbuf2.0-dev \
                    libffi-dev \
                    shared-mime-info \
                    python3-dev \
                    python3-pip \
                    python3-venv
                print_success "System dependencies installed"
            elif command_exists yum; then
                print_info "Using yum package manager"
                sudo yum install -y \
                    tesseract \
                    tesseract-langpack-ind \
                    tesseract-langpack-eng \
                    tesseract-devel \
                    leptonica-devel \
                    pkgconfig \
                    poppler-cpp-devel \
                    cairo-devel \
                    pango-devel \
                    gdk-pixbuf2-devel \
                    libffi-devel \
                    python3-devel \
                    python3-pip
                print_success "System dependencies installed"
            else
                print_error "Unsupported Linux distribution"
                return 1
            fi
            ;;
        "macos")
            print_info "Detected macOS system"
            if command_exists brew; then
                brew install tesseract tesseract-lang
                brew install poppler cairo pango gdk-pixbuf libffi
                print_success "System dependencies installed"
            else
                print_error "Homebrew not found. Please install Homebrew first:"
                print_info "Run: /bin/bash -c \"\$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)\""
                return 1
            fi
            ;;
        "windows")
            print_warning "Windows detected. Please install manually:"
            print_info "1. Download Tesseract: https://github.com/UB-Mannheim/tesseract/wiki"
            print_info "2. Install and add to PATH"
            print_info "3. Download Indonesian and English language packs"
            ;;
        *)
            print_error "Unsupported operating system: $os"
            return 1
            ;;
    esac
}

# Function to check Python version
check_python() {
    print_header "Checking Python Installation"
    
    if command_exists python3; then
        local version=$(python3 --version 2>&1 | cut -d' ' -f2)
        local major=$(echo $version | cut -d'.' -f1)
        local minor=$(echo $version | cut -d'.' -f2)
        
        print_success "Python $version found"
        
        if [ "$major" -ge 3 ] && [ "$minor" -ge 9 ]; then
            print_success "Python version is compatible"
            return 0
        else
            print_error "Python 3.9+ is required (found $version)"
            return 1
        fi
    else
        print_error "Python 3 not found"
        return 1
    fi
}

# Function to create virtual environment
create_venv() {
    print_header "Setting Up Virtual Environment"
    
    if [ ! -d "venv" ]; then
        print_info "Creating virtual environment..."
        python3 -m venv venv
        print_success "Virtual environment created"
    else
        print_info "Virtual environment already exists"
    fi
    
    print_info "Activating virtual environment..."
    source venv/bin/activate
    
    print_info "Upgrading pip..."
    pip install --upgrade pip
    
    print_success "Virtual environment ready"
}

# Function to install Python requirements
install_requirements() {
    local env=${1:-"base"}
    
    print_header "Installing Python Requirements ($env)"
    
    case $env in
        "dev"|"development")
            req_file="requirements-dev.txt"
            ;;
        "prod"|"production")
            req_file="requirements-prod.txt"
            ;;
        "minimal")
            req_file="requirements-minimal.txt"
            ;;
        *)
            req_file="requirements.txt"
            ;;
    esac
    
    if [ -f "$req_file" ]; then
        print_info "Installing from $req_file..."
        pip install -r "$req_file"
        print_success "Requirements installed successfully"
    else
        print_error "Requirements file not found: $req_file"
        return 1
    fi
}

# Function to setup environment
setup_environment() {
    local env=${1:-"dev"}
    
    print_header "Setting Up Environment Configuration"
    
    if [ -f ".env.$env" ]; then
        if [ -f ".env" ]; then
            print_info "Backing up existing .env file..."
            cp .env .env.backup.$(date +%Y%m%d_%H%M%S)
        fi
        
        print_info "Copying .env.$env to .env..."
        cp ".env.$env" ".env"
        print_success "Environment configuration set to $env"
    else
        print_warning ".env.$env not found, using .env.example as template"
        if [ -f ".env.example" ]; then
            cp ".env.example" ".env"
            print_info "Please edit .env file with your configuration"
        fi
    fi
}

# Function to initialize database
init_database() {
    print_header "Initializing Database"
    
    print_info "Creating database tables..."
    python3 -c "
from app import app, db
with app.app_context():
    db.create_all()
    print('Database initialized successfully')
" 2>/dev/null || {
    print_warning "Could not initialize database automatically"
    print_info "You may need to run this manually after starting the app"
}
}

# Function to show completion message
show_completion() {
    local env=${1:-"dev"}
    
    print_header "Installation Complete! 🎉"
    
    echo ""
    print_success "OCR ScanLetter Web Application is ready!"
    echo ""
    print_info "Next steps:"
    echo "  1. Activate virtual environment: source venv/bin/activate"
    echo "  2. Edit .env file if needed: nano .env"
    echo "  3. Start the application: python app.py"
    echo "  4. Open browser: http://localhost:5000"
    echo ""
    
    if [ "$env" = "dev" ]; then
        print_info "Development features enabled:"
        echo "  - Debug mode"
        echo "  - Auto-reload"
        echo "  - Debug toolbar"
        echo ""
    fi
    
    print_info "Useful commands:"
    echo "  - Switch environment: ./switch_env.sh [dev|prod|test]"
    echo "  - Install more packages: pip install package_name"
    echo "  - Run tests: pytest (if in dev environment)"
    echo ""
}

# Main installation function
main() {
    local env=${1:-"dev"}
    local install_sys_deps=${2:-"yes"}
    
    print_header "OCR ScanLetter Web Application Installer"
    
    # Check if we're in the right directory
    if [ ! -f "app.py" ]; then
        print_error "app.py not found. Please run this script from the project root directory."
        exit 1
    fi
    
    # Check Python
    if ! check_python; then
        exit 1
    fi
    
    # Install system dependencies
    if [ "$install_sys_deps" = "yes" ]; then
        if ! install_system_deps; then
            print_warning "System dependencies installation failed, continuing anyway..."
        fi
    fi
    
    # Create virtual environment
    if ! create_venv; then
        exit 1
    fi
    
    # Install Python requirements
    if ! install_requirements "$env"; then
        exit 1
    fi
    
    # Setup environment
    setup_environment "$env"
    
    # Initialize database
    init_database
    
    # Show completion message
    show_completion "$env"
}

# Show usage if help requested
if [ "$1" = "--help" ] || [ "$1" = "-h" ]; then
    echo "OCR ScanLetter Web Application Installer"
    echo "========================================"
    echo ""
    echo "Usage: $0 [environment] [install_system_deps]"
    echo ""
    echo "Environments:"
    echo "  dev      - Development environment (default)"
    echo "  prod     - Production environment"
    echo "  minimal  - Minimal installation"
    echo ""
    echo "System Dependencies:"
    echo "  yes      - Install system dependencies (default)"
    echo "  no       - Skip system dependencies"
    echo ""
    echo "Examples:"
    echo "  $0                    # Install development environment"
    echo "  $0 dev               # Install development environment"
    echo "  $0 prod              # Install production environment"
    echo "  $0 dev no            # Install dev without system deps"
    echo ""
    exit 0
fi

# Run main installation
main "$@"