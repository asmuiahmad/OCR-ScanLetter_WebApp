from flask import request, url_for

class Breadcrumb:
    def __init__(self, text, url=None):
        self.text = text
        self.url = url

# Dictionary mapping route names to breadcrumb text
route_breadcrumbs = {
    'index': 'Dashboard',
    'show_surat_masuk': 'Surat Masuk',
    'show_surat_keluar': 'Surat Keluar',
    'input_surat_masuk': 'Input Surat Masuk',
    'input_surat_keluar': 'Input Surat Keluar',
    'edit_surat_masuk': 'Edit Surat Masuk',
    'edit_surat_keluar': 'Edit Surat Keluar',
    'generate_cuti': 'Generate Cuti',
    'laporan_statistik': 'Laporan Statistik',
    'pegawai_list': 'List Pegawai',
    'kelola_pegawai': 'Kelola Pegawai',
    'ocr_surat_masuk.ocr_surat_masuk': 'OCR Surat Masuk',
    'ocr_surat_keluar.ocr_surat_keluar': 'OCR Surat Keluar',
    'edit_user_view': 'Manajemen User',
    'edit_user': 'Edit User',
}

# Dictionary defining parent-child relationships for routes
route_hierarchy = {
    'show_surat_masuk': ['index'],
    'show_surat_keluar': ['index'],
    'input_surat_masuk': ['index'],
    'input_surat_keluar': ['index'],
    'edit_surat_masuk': ['index', 'show_surat_masuk'],
    'edit_surat_keluar': ['index', 'show_surat_keluar'],
    'generate_cuti': ['index'],
    'laporan_statistik': ['index'],
    'pegawai_list': ['index'],
    'kelola_pegawai': ['index'],
    'ocr_surat_masuk.ocr_surat_masuk': ['index'],
    'ocr_surat_keluar.ocr_surat_keluar': ['index'],
    'edit_user_view': ['index'],
    'edit_user': ['index', 'edit_user_view'],
}

def generate_breadcrumbs(endpoint, **kwargs):
    """Generate breadcrumb navigation based on the current endpoint"""
    breadcrumbs = []
    
    # If the endpoint is not in our mapping, return empty breadcrumbs
    if endpoint not in route_breadcrumbs and endpoint not in route_hierarchy:
        return breadcrumbs
    
    # Add parent breadcrumbs if they exist
    if endpoint in route_hierarchy:
        for parent in route_hierarchy[endpoint]:
            breadcrumbs.append(
                Breadcrumb(
                    text=route_breadcrumbs.get(parent, parent),
                    url=url_for(parent, **{k: v for k, v in kwargs.items() if k in ['user_id', 'id']})
                )
            )
    
    # Add current page breadcrumb (without URL since it's the current page)
    breadcrumbs.append(
        Breadcrumb(
            text=route_breadcrumbs.get(endpoint, endpoint)
        )
    )
    
    return breadcrumbs 