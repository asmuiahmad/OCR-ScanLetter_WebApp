# Technology Stack

## Backend Framework
- **Flask 3.1.0**: Main web framework
- **Flask-SQLAlchemy 3.1.1**: Database ORM
- **Flask-Login 0.6.3**: User session management
- **Flask-WTF 1.2.2**: Form handling and CSRF protection
- **Flask-Migrate 4.1.0**: Database migrations

## Database
- **SQLite**: Default database (instance/app.db)
- **SQLAlchemy 2.0.37**: ORM layer
- **Alembic 1.14.1**: Database migration tool

## OCR & Document Processing
- **Tesseract OCR**: Text extraction engine (external dependency)
- **pytesseract 0.3.13**: Python wrapper for Tesseract
- **Pillow 11.1.0**: Image processing
- **python-docx 1.2.0**: Word document generation
- **docx-mailmerge2 0.9.0**: Mail merge functionality

## Digital Signatures & PDF
- **qrcode 8.0**: QR code generation for digital signatures
- **reportlab 4.2.5**: PDF generation
- **pdf2image 1.17.0**: PDF processing

## Frontend
- **Jinja2 templates**: Server-side rendering
- **Bootstrap CSS framework**: UI components
- **Custom CSS/SCSS**: Additional styling
- **Vanilla JavaScript**: Client-side interactions

## Development Tools
- **Docker**: Containerization support
- **Make**: Build automation (Makefile)
- **Virtual environments**: Python dependency isolation

## Common Commands

### Development Setup
```bash
# Initial setup
make setup
# or manually:
python -m venv venv
source venv/bin/activate  # Linux/macOS
pip install -r requirements.txt

# Run application
make run
# or:
python app.py
```

### Database Operations
```bash
# Create/update database
python app.py  # Auto-creates tables on first run

# Reset database
python reset_database.py

# Check database
python check_database.py
```

### Docker Deployment
```bash
# Build and run with Docker
make docker-build
make docker-run

# Stop containers
make docker-stop
```

### Code Quality
```bash
# Format code
make format

# Lint code
make lint

# Clean temporary files
make clean
```

## External Dependencies
- **Tesseract OCR**: Must be installed system-wide
  - macOS: `brew install tesseract tesseract-lang`
  - Ubuntu: `sudo apt install tesseract-ocr tesseract-ocr-ind`
  - Windows: Download from GitHub releases