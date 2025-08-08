#!/bin/bash

# Script untuk menginstal dependencies PDF generation
# Untuk sistem macOS dan Linux

echo "🚀 Installing PDF generation dependencies..."

# Detect OS
if [[ "$OSTYPE" == "darwin"* ]]; then
    # macOS
    echo "📱 Detected macOS"
    
    # Install wkhtmltopdf using Homebrew
    if command -v brew &> /dev/null; then
        echo "🍺 Installing wkhtmltopdf via Homebrew..."
        brew install wkhtmltopdf
    else
        echo "❌ Homebrew not found. Please install Homebrew first or install wkhtmltopdf manually."
        echo "   Download from: https://wkhtmltopdf.org/downloads.html"
    fi
    
elif [[ "$OSTYPE" == "linux-gnu"* ]]; then
    # Linux
    echo "🐧 Detected Linux"
    
    # Detect Linux distribution
    if command -v apt-get &> /dev/null; then
        # Debian/Ubuntu
        echo "📦 Installing wkhtmltopdf via apt..."
        sudo apt-get update
        sudo apt-get install -y wkhtmltopdf
        
        # Install additional dependencies for WeasyPrint
        sudo apt-get install -y python3-dev python3-pip python3-cffi python3-brotli libpango-1.0-0 libharfbuzz0b libpangoft2-1.0-0
        
    elif command -v yum &> /dev/null; then
        # CentOS/RHEL
        echo "📦 Installing wkhtmltopdf via yum..."
        sudo yum install -y wkhtmltopdf
        
        # Install additional dependencies for WeasyPrint
        sudo yum install -y python3-devel python3-pip libffi-devel pango harfbuzz
        
    elif command -v dnf &> /dev/null; then
        # Fedora
        echo "📦 Installing wkhtmltopdf via dnf..."
        sudo dnf install -y wkhtmltopdf
        
        # Install additional dependencies for WeasyPrint
        sudo dnf install -y python3-devel python3-pip libffi-devel pango harfbuzz
        
    else
        echo "❌ Unsupported Linux distribution. Please install wkhtmltopdf manually."
        echo "   Download from: https://wkhtmltopdf.org/downloads.html"
    fi
    
else
    echo "❌ Unsupported operating system: $OSTYPE"
    echo "   Please install wkhtmltopdf manually from: https://wkhtmltopdf.org/downloads.html"
fi

# Install Python dependencies
echo "🐍 Installing Python dependencies..."
pip install -r requirements.txt

# Test installations
echo "🧪 Testing installations..."

# Test wkhtmltopdf
if command -v wkhtmltopdf &> /dev/null; then
    echo "✅ wkhtmltopdf installed successfully"
    wkhtmltopdf --version
else
    echo "❌ wkhtmltopdf installation failed"
fi

# Test Python packages
echo "🐍 Testing Python packages..."
python3 -c "
try:
    import pdfkit
    print('✅ pdfkit imported successfully')
except ImportError as e:
    print('❌ pdfkit import failed:', e)

try:
    import weasyprint
    print('✅ WeasyPrint imported successfully')
except ImportError as e:
    print('❌ WeasyPrint import failed:', e)

try:
    import qrcode
    print('✅ qrcode imported successfully')
except ImportError as e:
    print('❌ qrcode import failed:', e)
"

echo "🎉 Installation complete!"
echo ""
echo "📝 Notes:"
echo "   - If you encounter issues with WeasyPrint, you may need to install additional system fonts"
echo "   - For production use, consider using Docker for consistent environments"
echo "   - Test the HTML to PDF conversion with your templates"