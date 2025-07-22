# Final Route Structure

## 📁 Complete Route Organization

```
config/
├── auth_routes.py          # Authentication & authorization
├── user_routes.py          # User management & administration  
├── pegawai_routes.py       # Employee management
├── surat_routes.py         # Common document functionality
├── surat_masuk_routes.py   # Incoming document management
├── surat_keluar_routes.py  # Outgoing document management
├── cuti_routes.py          # Leave/vacation management
├── ocr_routes.py           # OCR testing and utilities
├── laporan_routes.py       # Statistical reports and analytics
├── api_routes.py           # RESTful API endpoints
├── dashboard_routes.py     # Dashboard & overview
├── routes_user_login_logs.py # User login tracking
├── remaining_routes.py     # Miscellaneous routes (to be organized)
├── routes_main.py          # Blueprint registration
└── route_utils.py          # Shared utilities & decorators
```

## 🔄 Blueprint Registration

All blueprints are registered in `routes_main.py`:

```python
def register_blueprints(app):
    app.register_blueprint(auth_bp)
    app.register_blueprint(dashboard_bp)
    app.register_blueprint(api_bp)
    app.register_blueprint(surat_bp)
    app.register_blueprint(surat_masuk_bp)
    app.register_blueprint(surat_keluar_bp)
    app.register_blueprint(pegawai_bp)
    app.register_blueprint(user_bp)
    app.register_blueprint(cuti_bp)
    app.register_blueprint(ocr_routes_bp)
    app.register_blueprint(laporan_bp)
    app.register_blueprint(remaining_bp)
```

## 📊 Route Distribution

| Module | Routes | Functionality |
|--------|--------|---------------|
| auth_routes.py | 3 | Login, logout, register |
| user_routes.py | 6 | User CRUD, approval, management |
| pegawai_routes.py | 4 | Employee CRUD operations |
| surat_routes.py | 2 | Common document functionality |
| surat_masuk_routes.py | 7 | Incoming document management |
| surat_keluar_routes.py | 6 | Outgoing document management |
| cuti_routes.py | 6 | Leave management system |
| ocr_routes.py | 2 | OCR testing and utilities |
| laporan_routes.py | 1 | Statistical reports and analytics |
| api_routes.py | 5 | REST API endpoints |
| dashboard_routes.py | 3 | Dashboard & statistics |
| remaining_routes.py | 4 | Misc routes (needs cleanup) |

## 🔗 Route Mapping

### Authentication Routes (`auth_routes.py`)
```
GET/POST /login          - Login page and processing
GET      /logout         - Logout user
GET/POST /register       - Registration page and processing
```

### User Management Routes (`user_routes.py`)
```
GET/POST /edit-user                - User management interface
GET/POST /edit-user/<id>           - Edit specific user
GET      /get-user-data/<id>       - Get user data (JSON)
POST     /approve-user/<id>        - Approve user account
POST     /delete-user/<id>         - Delete user account
```

### Employee Routes (`pegawai_routes.py`)
```
GET/POST /pegawai                  - Add employee form/Create employee
GET      /pegawai/list             - List all employees
POST     /pegawai/edit/<id>        - Update employee
POST     /pegawai/hapus/<id>       - Delete employee
```

### Surat Masuk Routes (`surat_masuk_routes.py`)
```
GET      /show_surat_masuk         - List incoming documents
GET/POST /input_surat_masuk        - Add new incoming document
GET/POST /edit_surat_masuk/<id>    - Edit incoming document
POST     /delete_surat_masuk/<id>  - Delete incoming document
GET      /list-pending-surat-masuk - List pending documents
POST     /approve-surat/<id>       - Approve document
POST     /reject-surat/<id>        - Reject document
```

### Surat Keluar Routes (`surat_keluar_routes.py`)
```
GET      /show_surat_keluar        - List outgoing documents
GET/POST /input_surat_keluar       - Add new outgoing document
GET/POST /edit_surat_keluar/<id>   - Edit outgoing document
POST     /delete_surat_keluar/<id> - Delete outgoing document
GET      /surat_keluar             - Legacy route
GET      /test_surat_keluar        - Test route
```

### Leave Management Routes (`cuti_routes.py`)
```
GET/POST /generate-cuti            - Generate leave form
GET/POST /input-cuti               - Admin leave input form
GET      /list-cuti                - List all leave applications
POST     /approve-cuti/<id>        - Approve leave application
POST     /reject-cuti/<id>         - Reject leave application
POST     /delete-cuti/<id>         - Delete leave record
```

### OCR Routes (`ocr_routes.py`)
```
GET/POST /ocr-test                 - Test OCR functionality
GET      /favicon.ico              - Serve favicon
```

### Report Routes (`laporan_routes.py`)
```
GET      /laporan-statistik        - Statistical reports
```

### API Routes (`api_routes.py`)
```
GET      /api/notifications/count  - Get notification count
GET      /api/test                 - API test endpoint
GET      /api/surat-keluar/detail/<id> - Get document details
GET      /api/chart-data           - Dashboard chart data
GET      /api/debug/surat/<id>     - Debug document info
```

### Dashboard Routes (`dashboard_routes.py`)
```
GET      /                         - Main dashboard
GET      /users                    - User list
GET      /last-logins              - Last login info (JSON)
```

## 🔐 Access Control

### Role-Based Access
- **Admin**: Full access to all routes
- **Pimpinan**: Management access (approval, viewing)
- **Karyawan**: Limited access (own data, basic functions)

### Protected Routes
All routes require `@login_required` decorator. Additional role restrictions:
- User management: Admin only
- Employee management: Admin + Pimpinan
- Leave approval: Pimpinan only
- Document approval: Pimpinan only

## 🛠 Utility Functions

### Decorators (`route_utils.py`)
```python
@role_required('admin', 'pimpinan')  # Require specific roles
@login_required                       # Require authentication
```

### Logging Functions
```python
log_user_login(user_id, email, status, request)
log_user_logout(user_id)
```

## 🚀 Testing Routes

To verify all route imports are working correctly:

```bash
python test_route_imports.py
```

This structure provides excellent maintainability, scalability, and follows Flask best practices!