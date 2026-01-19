from flask import request, url_for, g
from flask_login import current_user

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
    @app.before_request
    def load_notification_data():
        """Load notification data for pimpinan only"""
        if current_user.is_authenticated and current_user.role == 'pimpinan':
            try:
                from config.models import SuratMasuk, SuratKeluar

                pending_masuk = SuratMasuk.query.filter_by(status_suratMasuk='pending').count()
                pending_keluar = SuratKeluar.query.filter_by(status_suratKeluar='pending').count()

                g.pending_surat_masuk_count = pending_masuk + pending_keluar
                g.pending_masuk_count = pending_masuk
                g.pending_keluar_count = pending_keluar

                recent_masuk = SuratMasuk.query.filter_by(status_suratMasuk='pending')\
                    .order_by(SuratMasuk.created_at.desc())\
                    .limit(15)\
                    .all()

                recent_keluar = SuratKeluar.query.filter_by(status_suratKeluar='pending')\
                    .order_by(SuratKeluar.created_at.desc())\
                    .limit(15)\
                    .all()

                notification_items = []

                for surat in recent_masuk:
                    notification_items.append({
                        'id': surat.id_suratMasuk,
                        'type': 'masuk',
                        'pengirim': surat.pengirim_suratMasuk or 'Pengirim tidak diketahui',
                        'penerima': surat.penerima_suratMasuk or 'Penerima tidak diketahui',
                        'nomor': surat.nomor_suratMasuk or 'Nomor tidak tersedia',
                        'tanggal_display': surat.tanggal_suratMasuk.strftime('%d %b %Y') if surat.tanggal_suratMasuk else 'Tanggal tidak diketahui',
                        'created_at_display': surat.created_at.strftime('%d %b %Y %H:%M') if surat.created_at else '',
                        'created_at_sort': surat.created_at.isoformat() if surat.created_at else '',
                        'ringkasan': (surat.isi_suratMasuk[:100] + '...') if surat.isi_suratMasuk and len(surat.isi_suratMasuk) > 100 else (surat.isi_suratMasuk or '')
                    })

                for surat in recent_keluar:
                    notification_items.append({
                        'id': surat.id_suratKeluar,
                        'type': 'keluar',
                        'pengirim': surat.pengirim_suratKeluar or 'Pengirim tidak diketahui',
                        'penerima': surat.penerima_suratKeluar or 'Penerima tidak diketahui',
                        'nomor': surat.nomor_suratKeluar or 'Nomor tidak tersedia',
                        'tanggal_display': surat.tanggal_suratKeluar.strftime('%d %b %Y') if surat.tanggal_suratKeluar else 'Tanggal tidak diketahui',
                        'created_at_display': surat.created_at.strftime('%d %b %Y %H:%M') if surat.created_at else '',
                        'created_at_sort': surat.created_at.isoformat() if surat.created_at else '',
                        'ringkasan': (surat.isi_suratKeluar[:100] + '...') if surat.isi_suratKeluar and len(surat.isi_suratKeluar) > 100 else (surat.isi_suratKeluar or '')
                    })

                notification_items.sort(key=lambda item: item.get('created_at_sort') or '', reverse=True)

                g.surat_masuk_list = recent_masuk
                g.notification_items = notification_items
            except Exception as e:
                app.logger.error(f"Error loading notification data: {str(e)}")
                g.pending_surat_masuk_count = 0
                g.pending_masuk_count = 0
                g.pending_keluar_count = 0
                g.surat_masuk_list = []
                g.notification_items = []
        else:
            # Non-pimpinan tidak mendapat data notifikasi
            g.pending_surat_masuk_count = 0
            g.pending_masuk_count = 0
            g.pending_keluar_count = 0
            g.surat_masuk_list = []
            g.notification_items = []

    @app.context_processor
    def inject_breadcrumbs():
        """Inject breadcrumbs into all templates"""
        endpoint = request.endpoint
        view_args = request.view_args or {}
        breadcrumbs = generate_breadcrumbs(endpoint, **view_args)
        return dict(breadcrumbs=breadcrumbs)
    
    @app.context_processor
    def inject_notifications():
        """Inject notification data into all templates"""
        return dict(
            surat_masuk_list=getattr(g, 'surat_masuk_list', []),
            pending_surat_masuk_count=getattr(g, 'pending_surat_masuk_count', 0),
            pending_masuk_count=getattr(g, 'pending_masuk_count', 0),
            pending_keluar_count=getattr(g, 'pending_keluar_count', 0),
            notification_items=getattr(g, 'notification_items', [])
        )
    
    # Add utilities to Jinja2
    app.jinja_env.globals['zip'] = zip
    app.jinja_env.globals.update(max=max, min=min) 