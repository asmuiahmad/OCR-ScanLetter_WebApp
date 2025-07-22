"""
Laporan routes
Statistical reports and analytics functionality
"""

from collections import defaultdict
from calendar import monthrange
from datetime import datetime

from flask import Blueprint, render_template, request, current_app
from flask_login import login_required
from sqlalchemy import or_

from config.extensions import db
from config.models import SuratKeluar, SuratMasuk
from config.route_utils import role_required

laporan_bp = Blueprint('laporan', __name__)


@laporan_bp.route("/laporan-statistik")
@login_required
@role_required('admin', 'pimpinan')
def laporan_statistik():
    """Statistical reports"""
    semua_surat_masuk = SuratMasuk.query.all()
    semua_surat_keluar = SuratKeluar.query.all()

    total_masuk = len(semua_surat_keluar)
    total_keluar = len(semua_surat_masuk)

    berhasil_masuk = len([s for s in semua_surat_keluar if 'Not found' not in s.isi_suratKeluar])
    berhasil_keluar = len([s for s in semua_surat_masuk if 'Not found' not in s.isi_suratMasuk])

    persentase_berhasil_masuk = round((berhasil_masuk / total_masuk * 100), 2) if total_masuk else 0
    persentase_berhasil_keluar = round((berhasil_keluar / total_keluar * 100), 2) if total_keluar else 0

    field_stats_masuk = {
        'nomor_suratKeluar': 0,
        'pengirim_suratKeluar': 0,
        'penerima_suratKeluar': 0,
        'isi_suratKeluar': 0,
    }

    for surat in semua_surat_keluar:
        if hasattr(surat, 'initial_nomor_suratKeluar') and surat.initial_nomor_suratKeluar == 'Not found':
            field_stats_masuk['nomor_suratKeluar'] += 1
        if hasattr(surat, 'initial_pengirim_suratKeluar') and surat.initial_pengirim_suratKeluar == 'Not found':
            field_stats_masuk['pengirim_suratKeluar'] += 1
        if hasattr(surat, 'initial_penerima_suratKeluar') and surat.initial_penerima_suratKeluar == 'Not found':
            field_stats_masuk['penerima_suratKeluar'] += 1
        if hasattr(surat, 'initial_isi_suratKeluar') and surat.initial_isi_suratKeluar == 'Not found':
            field_stats_masuk['isi_suratKeluar'] += 1

    field_stats_keluar = {
        'nomor_suratMasuk': 0,
        'pengirim_suratMasuk': 0,
        'penerima_suratMasuk': 0,
        'isi_suratMasuk': 0,
    }

    for surat in semua_surat_masuk:
        if hasattr(surat, 'initial_nomor_suratMasuk') and surat.initial_nomor_suratMasuk == 'Not found':
            field_stats_keluar['nomor_suratMasuk'] += 1
        if hasattr(surat, 'initial_pengirim_suratMasuk') and surat.initial_pengirim_suratMasuk == 'Not found':
            field_stats_keluar['pengirim_suratMasuk'] += 1
        if hasattr(surat, 'initial_penerima_suratMasuk') and surat.initial_penerima_suratMasuk == 'Not found':
            field_stats_keluar['penerima_suratMasuk'] += 1
        if hasattr(surat, 'initial_isi_suratMasuk') and surat.initial_isi_suratMasuk == 'Not found':
            field_stats_keluar['isi_suratMasuk'] += 1

    full_letter_components_masuk = ['initial_nomor_suratKeluar']
    full_letter_components_keluar = ['nomor_suratMasuk']

    full_letter_not_found_masuk = sum(
        sum(1 for surat in semua_surat_keluar if hasattr(surat, field) and getattr(surat, field) == 'Not found')
        for field in full_letter_components_masuk
    )
    full_letter_not_found_keluar = sum(
        sum(1 for surat in semua_surat_masuk if hasattr(surat, field) and getattr(surat, field) == 'Not found')
        for field in full_letter_components_keluar
    )

    field_stats_masuk['full_letter_number_not_found'] = full_letter_not_found_masuk
    field_stats_keluar['full_letter_number_not_found'] = full_letter_not_found_keluar

    akurasi_masuk = [s.ocr_accuracy_suratKeluar for s in semua_surat_keluar if s.ocr_accuracy_suratKeluar is not None]
    akurasi_keluar = [s.ocr_accuracy_suratMasuk for s in semua_surat_masuk if s.ocr_accuracy_suratMasuk is not None]

    rata2_akurasi_masuk = round(sum(akurasi_masuk) / len(akurasi_masuk), 2) if akurasi_masuk else 0
    rata2_akurasi_keluar = round(sum(akurasi_keluar) / len(akurasi_keluar), 2) if akurasi_keluar else 0

    akurasi_tinggi_masuk = len([a for a in akurasi_masuk if a >= 90])
    akurasi_sedang_masuk = len([a for a in akurasi_masuk if 70 <= a < 90])
    akurasi_rendah_masuk = len([a for a in akurasi_masuk if a < 70])

    akurasi_tinggi_keluar = len([a for a in akurasi_keluar if a >= 90])
    akurasi_sedang_keluar = len([a for a in akurasi_keluar if 70 <= a < 90])
    akurasi_rendah_keluar = len([a for a in akurasi_keluar if a < 70])

    gagal_ekstraksi_suratMasuk = [
        s for s in semua_surat_masuk if s.ocr_accuracy_suratMasuk and s.ocr_accuracy_suratMasuk < 100
    ]

    gagal_ekstraksi_suratKeluar = SuratKeluar.query.filter(
        or_(
            SuratKeluar.initial_nomor_suratKeluar == 'Not found',
            SuratKeluar.initial_pengirim_suratKeluar == 'Not found',
            SuratKeluar.initial_penerima_suratKeluar == 'Not found',
            SuratKeluar.initial_isi_suratKeluar == 'Not found'
        )
    ).all()

    keyword = request.args.get('keyword', '')
    surat_keyword = []
    if keyword:
        surat_keyword = SuratMasuk.query.filter(SuratMasuk.isi_suratMasuk.ilike(f'%{keyword}%')).all()

    return render_template(
        'statistik/laporan_statistik.html',
        persentase_berhasil_masuk=persentase_berhasil_masuk,
        persentase_berhasil_keluar=persentase_berhasil_keluar,
        gagal_ekstraksi_suratKeluar=gagal_ekstraksi_suratKeluar,
        gagal_ekstraksi_suratMasuk=gagal_ekstraksi_suratMasuk,
        keyword=keyword,
        surat_keyword=surat_keyword,
        rata2_akurasi_masuk=rata2_akurasi_masuk,
        rata2_akurasi_keluar=rata2_akurasi_keluar,
        field_stats_keluar=field_stats_keluar,
        field_stats_masuk=field_stats_masuk,
        total_masuk=total_masuk,
        total_keluar=total_keluar,
        akurasi_tinggi_masuk=akurasi_tinggi_masuk,
        akurasi_sedang_masuk=akurasi_sedang_masuk,
        akurasi_rendah_masuk=akurasi_rendah_masuk,
        akurasi_tinggi_keluar=akurasi_tinggi_keluar,
        akurasi_sedang_keluar=akurasi_sedang_keluar,
        akurasi_rendah_keluar=akurasi_rendah_keluar
    )