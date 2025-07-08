from flask import request, url_for

class Breadcrumb:
    def __init__(self, text, url=None):
        self.text = text
        self.url = url

# Dictionary mapping route names to breadcrumb text
route_breadcrumbs = {
    'show_surat_masuk': 'Surat Masuk',
    'show_surat_keluar': 'Surat Keluar',
    'input_surat_masuk': 'Input Surat Masuk',
    'input_surat_keluar': 'Input Surat Keluar',
    'edit_surat_masuk': 'Edit Surat Masuk',
    'edit_surat_keluar': 'Edit Surat Keluar',
    'generate_cuti': 'Generate Cuti',
    'laporan_statistik': 'Laporan Statistik',
    'pegawai_list': 'List Pegawai',
    'pegawai': 'Kelola Pegawai',
    'ocr_surat_masuk.ocr_surat_masuk': 'OCR Surat Masuk',
    'ocr_surat_keluar.ocr_surat_keluar': 'OCR Surat Keluar',
    'edit_user_view': 'Manajemen User',
    'edit_user': 'Edit User',
}

# Dictionary defining parent-child relationships for routes
route_hierarchy = {
    'show_surat_masuk': [],
    'show_surat_keluar': [],
    'input_surat_masuk': [],
    'input_surat_keluar': [],
    'edit_surat_masuk': ['show_surat_masuk'],
    'edit_surat_keluar': ['show_surat_keluar'],
    'generate_cuti': [],
    'laporan_statistik': [],
    'pegawai_list': [],
    'pegawai': [],
    'ocr_surat_masuk.ocr_surat_masuk': [],
    'ocr_surat_keluar.ocr_surat_keluar': [],
    'edit_user_view': [],
    'edit_user': ['edit_user_view'],
}

def generate_breadcrumbs(endpoint, **kwargs):
    """Generate breadcrumbs based on endpoint"""
    breadcrumbs = []
    
    # Map endpoints to breadcrumb titles
    if endpoint == 'show_surat_masuk':
        breadcrumbs.append(('Surat Masuk', url_for('main.show_surat_masuk')))
    elif endpoint == 'show_surat_keluar':
        breadcrumbs.append(('Surat Keluar', url_for('main.show_surat_keluar')))
    elif endpoint == 'ocr_surat_masuk.ocr_surat_masuk':
        breadcrumbs.append(('OCR Surat Masuk', url_for('ocr_surat_masuk.ocr_surat_masuk')))
    elif endpoint == 'ocr_surat_keluar.ocr_surat_keluar':
        breadcrumbs.append(('OCR Surat Keluar', url_for('ocr_surat_keluar.ocr_surat_keluar')))
    elif endpoint == 'input_surat_masuk':
        breadcrumbs.append(('Input Surat Masuk', url_for('main.input_surat_masuk')))
    elif endpoint == 'input_surat_keluar':
        breadcrumbs.append(('Input Surat Keluar', url_for('main.input_surat_keluar')))
    elif endpoint == 'pegawai':
        breadcrumbs.append(('Kelola Pegawai', url_for('main.pegawai')))
    elif endpoint == 'pegawai_list':
        breadcrumbs.append(('List Pegawai', url_for('main.pegawai_list')))
    elif endpoint == 'auth.login':
        breadcrumbs = [('Login', url_for('auth.login'))]  # Only show login, not home
    elif endpoint == 'auth.register':
        breadcrumbs.append(('Register', url_for('auth.register')))
    
    return breadcrumbs

def register_breadcrumbs(app):
    @app.context_processor
    def inject_breadcrumbs():
        """Inject breadcrumbs into all templates"""
        endpoint = request.endpoint
        view_args = request.view_args or {}
        breadcrumbs = generate_breadcrumbs(endpoint, **view_args)
        return dict(breadcrumbs=breadcrumbs)
    
    # Add utilities to Jinja2
    app.jinja_env.globals['zip'] = zip
    app.jinja_env.globals.update(max=max, min=min) 