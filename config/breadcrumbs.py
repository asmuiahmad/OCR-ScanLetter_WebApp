from flask import request, url_for

class Breadcrumb:
    def __init__(self, text, url=None):
        self.text = text
        self.url = url

# Dictionary mapping route names to breadcrumb text
route_breadcrumbs = {
    'index': 'Home',
    'show_surat_keluar': 'Surat Keluar',
    'show_surat_masuk': 'Surat Masuk',
    'input_surat_keluar': 'Input Surat Keluar',
    'input_surat_masuk': 'Input Surat Masuk',
    'edit_surat_keluar': 'Edit Surat Keluar',
    'edit_surat_masuk': 'Edit Surat Masuk',
    'generate_cuti': 'Generate Cuti',
    'laporan_statistik': 'Laporan Statistik',
    'pegawai_list': 'List Pegawai',
    'pegawai': 'Kelola Pegawai',
    'ocr_surat_keluar.ocr_surat_keluar': 'OCR Surat Keluar',
    'ocr_surat_masuk.ocr_surat_masuk': 'OCR Surat Masuk',
    'edit_user_view': 'Manajemen User',
    'edit_user': 'Edit User',
    'ocr_test': 'OCR Test',
    'login': 'Login',
    'logout': 'Logout',
    'register': 'Register',
    'ocr_cuti': 'OCR Cuti',
    'favicon': 'Favicon',
}

def get_breadcrumb_title(endpoint):
    """Get the breadcrumb title for a given endpoint"""
    if '.' in endpoint:
        endpoint = endpoint.split('.')[-1]
    return route_breadcrumbs.get(endpoint, endpoint.replace('_', ' ').title())

def generate_breadcrumbs(endpoint, **view_args):
    breadcrumbs = []
    if endpoint != 'main.index':
        breadcrumbs.append(('Home', url_for('main.index')))
    if not endpoint:
        return breadcrumbs
    clean_endpoint = endpoint.split('.')[-1] if '.' in endpoint else endpoint
    # Add current page breadcrumb
    if clean_endpoint in route_breadcrumbs:
        # Special handling for edit pages
        if clean_endpoint.startswith('edit_'):
            parent_endpoint = clean_endpoint.replace('edit_', 'show_')
            if parent_endpoint in route_breadcrumbs:
                breadcrumbs.append((route_breadcrumbs[parent_endpoint], url_for(f'main.{parent_endpoint}')))
        current_url = url_for(endpoint, **view_args) if endpoint != 'main.index' else None
        breadcrumbs.append((route_breadcrumbs[clean_endpoint], current_url))
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