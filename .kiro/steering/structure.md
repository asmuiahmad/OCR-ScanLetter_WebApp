# Project Structure

## Architecture Pattern
- **Blueprint-based Flask application**: Modular route organization
- **MVC-like separation**: Models, routes (controllers), templates (views)
- **Factory pattern**: Application creation in `create_app()` function

## Directory Organization

### Core Application
```
app.py                    # Main application entry point
config/                   # Application configuration and modules
├── __init__.py
├── extensions.py         # Flask extensions initialization
├── models.py            # SQLAlchemy database models
├── routes.py            # Main routes and auth blueprint
├── forms.py             # WTForms form definitions
├── breadcrumbs.py       # Navigation breadcrumb logic
├── ocr.py               # General OCR blueprint
├── ocr_surat_masuk.py   # Incoming letters OCR
├── ocr_surat_keluar.py  # Outgoing letters OCR
├── ocr_cuti.py          # Leave applications OCR
├── ocr_utils.py         # OCR utility functions
└── digital_signature.py # Digital signature utilities
```

### Templates & Static Files
```
templates/               # Jinja2 templates
├── layouts/            # Base templates
├── includes/           # Reusable template components
├── auth/               # Authentication pages
├── home/               # Main application pages
└── error pages (404.html, 500.html)

static/                 # Static assets
├── assets/
│   ├── css/           # Stylesheets
│   ├── js/            # JavaScript files
│   ├── images/        # Images and icons
│   └── fonts/         # Font files
└── ocr/               # OCR-related uploads
    ├── uploads/       # General uploads
    ├── surat_masuk/   # Incoming letter images
    ├── surat_keluar/  # Outgoing letter images
    └── cuti/          # Leave application documents
```

### Database & Instance
```
instance/               # Instance-specific files
└── app.db             # SQLite database file

migrations/            # Database migration files
├── versions/          # Migration versions
└── alembic configuration files
```

## Code Organization Patterns

### Blueprint Structure
- Each major feature has its own blueprint (OCR modules, auth, main)
- Routes are organized by functionality, not by HTTP method
- URL prefixes separate different modules (`/cuti`, `/surat-masuk`, etc.)

### Model Conventions
- Models use descriptive Indonesian field names (e.g., `tanggal_suratMasuk`)
- Primary keys follow pattern: `id_[tableName]`
- Timestamps use `created_at` with UTC default
- Status fields use string enums ('pending', 'approved', 'rejected')

### File Upload Organization
- Separate directories for different document types
- Secure filename handling with `werkzeug.utils.secure_filename`
- Binary data stored in database for smaller files
- File paths stored for larger documents

### Template Hierarchy
```
base.html (layouts/)     # Main layout
├── includes/head.html   # HTML head section
├── auth templates       # Login, register
└── feature templates    # OCR, lists, forms
```

### Configuration Management
- Environment variables via `.env` file
- Metadata stored in `metadata.json`
- Extensions initialized in `config/extensions.py`
- CSRF protection enabled globally

## Naming Conventions
- **Files**: Snake_case for Python files, kebab-case for templates
- **Classes**: PascalCase (e.g., `SuratMasuk`, `User`)
- **Functions/Variables**: snake_case
- **Database fields**: Indonesian descriptive names with underscores
- **Routes**: Kebab-case URLs (`/surat-masuk`, `/list-cuti`)
- **Templates**: Descriptive names matching functionality

## Key Architectural Decisions
- **Single database file**: SQLite for simplicity in government environment
- **Server-side rendering**: Jinja2 templates, minimal JavaScript
- **File storage**: Mix of database binary storage and filesystem
- **OCR processing**: Synchronous processing with user feedback
- **Authentication**: Flask-Login with role-based access control
- **CSRF protection**: Enabled globally with token injection