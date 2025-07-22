"""
Remaining routes
Routes that haven't been categorized yet or are miscellaneous
TODO: Move these routes to appropriate modules
"""

import os
import io
import tempfile
import subprocess
from collections import defaultdict
from calendar import monthrange
from datetime import datetime

import pytesseract
from flask import (
    Blueprint, render_template, request, send_file, redirect, url_for,
    flash, jsonify, current_app, send_from_directory
)
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename
from sqlalchemy import desc, asc, extract, func, or_
from docx import Document
from mailmerge import MailMerge

from config.extensions import db
from config.models import SuratKeluar, SuratMasuk, Pegawai
from config.route_utils import role_required
from config.ocr_utils import hitung_field_not_found

remaining_bp = Blueprint('remaining', __name__)


@remaining_bp.route("/laporan-statistik")
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
        if surat.initial_nomor_suratKeluar == 'Not found':
            field_stats_masuk['nomor_suratKeluar'] += 1
        if surat.initial_pengirim_suratKeluar == 'Not found':
            field_stats_masuk['pengirim_suratKeluar'] += 1
        if surat.initial_penerima_suratKeluar == 'Not found':
            field_stats_masuk['penerima_suratKeluar'] += 1
        if surat.initial_isi_suratKeluar == 'Not found':
            field_stats_masuk['isi_suratKeluar'] += 1

    field_stats_keluar = {
        'nomor_suratMasuk': 0,
        'pengirim_suratMasuk': 0,
        'penerima_suratMasuk': 0,
        'isi_suratMasuk': 0,
    }

    for surat in semua_surat_masuk:
        if surat.initial_nomor_suratMasuk == 'Not found':
            field_stats_keluar['nomor_suratMasuk'] += 1
        if surat.initial_pengirim_suratMasuk == 'Not found':
            field_stats_keluar['pengirim_suratMasuk'] += 1
        if surat.initial_penerima_suratMasuk == 'Not found':
            field_stats_keluar['penerima_suratMasuk'] += 1
        if surat.initial_isi_suratMasuk == 'Not found':
            field_stats_keluar['isi_suratMasuk'] += 1

    full_letter_components_masuk = ['initial_nomor_suratKeluar']
    full_letter_components_keluar = ['nomor_suratMasuk']

    full_letter_not_found_masuk = sum(
        sum(1 for surat in semua_surat_keluar if getattr(surat, field) == 'Not found')
        for field in full_letter_components_masuk
    )
    full_letter_not_found_keluar = sum(
        sum(1 for surat in semua_surat_masuk if getattr(surat, field) == 'Not found')
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


# generate_cuti route moved to config/cuti_routes.py


@remaining_bp.route('/surat_keluar')
@login_required
def surat_keluar():
    """Surat keluar list"""
    daftar_surat = SuratKeluar.query.all()
    return render_template('surat_keluar/surat_keluar.html', daftar_surat=daftar_surat)


@remaining_bp.route('/test_surat_keluar', methods=['GET'])
def test_surat_keluar():
    """Test surat keluar"""
    try:
        surat_keluar_entries = SuratKeluar.query.paginate(page=1, per_page=20)
        return render_template(
            'surat_keluar/show_surat_keluar.html',
            entries=surat_keluar_entries,
            sort='tanggal_suratKeluar',
            order='asc',
            search=''
        )
    except Exception as e:
        return f"Error: {str(e)}", 500


@remaining_bp.route('/surat-keluar/list', methods=['GET'])
@login_required
@role_required('pimpinan', 'admin')
def list_surat_keluar():
    """List surat keluar for approval"""
    try:
        pending_surat_masuk = SuratMasuk.query.filter_by(status_suratMasuk='pending').all()
        pending_surat_masuk_count = len(pending_surat_masuk)
        
        return render_template('surat_keluar/list_surat_keluar.html',
                               pending_surat_masuk=pending_surat_masuk,
                               pending_surat_masuk_count=pending_surat_masuk_count)
    except Exception as e:
        current_app.logger.error(f"Error in list_surat_keluar: {str(e)}")
        flash('Terjadi kesalahan saat memuat daftar surat.', 'error')
        return redirect(url_for('main.index'))


@remaining_bp.route('/surat-keluar/approve/<int:surat_id>', methods=['POST'])
@login_required
@role_required('pimpinan')
def approve_surat(surat_id):
    """Approve surat"""
    try:
        surat = SuratMasuk.query.get(surat_id)
        if surat:
            surat.status_suratMasuk = 'approved'
            db.session.commit()
            return jsonify({"success": True, "message": "Surat berhasil disetujui"})
        else:
            return jsonify({"success": False, "error": "Surat tidak ditemukan"}), 404
    except Exception as e:
        db.session.rollback()
        return jsonify({"success": False, "error": str(e)}), 500


@remaining_bp.route('/surat-keluar/reject/<int:surat_id>', methods=['POST'])
@login_required
@role_required('pimpinan')
def reject_surat(surat_id):
    """Reject surat"""
    try:
        surat = SuratMasuk.query.get(surat_id)
        if surat:
            surat.status_suratMasuk = 'rejected'
            db.session.commit()
            return jsonify({"success": True, "message": "Surat berhasil ditolak"})
        else:
            return jsonify({"success": False, "error": "Surat tidak ditemukan"}), 404
    except Exception as e:
        db.session.rollback()
        return jsonify({"success": False, "error": str(e)}), 500


@remaining_bp.route('/list-pending-surat-masuk')
@login_required
@role_required('pimpinan')
def list_pending_surat_masuk():
    """List pending surat masuk"""
    try:
        pending_surat_masuk = SuratMasuk.query.filter_by(status_suratMasuk='pending').all()
        return render_template('surat_masuk/list_pending_surat_masuk.html', 
                               pending_surat_masuk=pending_surat_masuk)
    except Exception as e:
        current_app.logger.error(f"Error in list_pending_surat_masuk: {str(e)}")
        flash('Terjadi kesalahan saat memuat daftar surat pending.', 'error')
        return redirect(url_for('main.index'))


@remaining_bp.route('/ocr-test', methods=['GET', 'POST'])
@login_required
def ocr_test():
    """OCR test functionality"""
    extracted_text = ""
    
    if request.method == 'POST':
        try:
            if 'file' not in request.files:
                flash('No file selected', 'error')
                return render_template('ocr/ocr_test.html', extracted_text=extracted_text, has_error=True, has_success=False)
            
            file = request.files['file']
            if file.filename == '':
                flash('No file selected', 'error')
                return render_template('ocr/ocr_test.html', extracted_text=extracted_text, has_error=True, has_success=False)
            
            if file and file.filename.lower().endswith(('.png', '.jpg', '.jpeg', '.gif', '.bmp', '.tiff')):
                try:
                    # Save uploaded file temporarily
                    filename = secure_filename(file.filename)
                    temp_path = os.path.join(tempfile.gettempdir(), filename)
                    file.save(temp_path)
                    
                    # Perform OCR
                    extracted_text = pytesseract.image_to_string(temp_path, lang='ind+eng')
                    
                    # Clean up
                    os.remove(temp_path)
                    
                    if extracted_text.strip():
                        flash('OCR extraction successful!', 'success')
                        return render_template('ocr/ocr_test.html', extracted_text=extracted_text, has_error=False, has_success=True)
                    else:
                        flash('No text could be extracted from the image', 'warning')
                        return render_template('ocr/ocr_test.html', extracted_text="No text found", has_error=False, has_success=False)
                        
                except Exception as ocr_error:
                    current_app.logger.error(f"OCR processing error: {str(ocr_error)}")
                    flash(f'Error processing image: {str(ocr_error)}', 'error')
                    return render_template('ocr/ocr_test.html', extracted_text=extracted_text, has_error=True, has_success=False)
            else:
                flash('Please upload a valid image file (PNG, JPG, JPEG, GIF, BMP, TIFF)', 'error')
                return render_template('ocr/ocr_test.html', extracted_text=extracted_text, has_error=True, has_success=False)
                
        except Exception as e:
            current_app.logger.error(f"OCR test error: {str(e)}")
            flash(f'An error occurred: {str(e)}', 'error')
            return render_template('ocr/ocr_test.html', extracted_text=extracted_text, has_error=True, has_success=False)
    
    return render_template('ocr/ocr_test.html', extracted_text=extracted_text, has_error=False, has_success=False)


@remaining_bp.route('/favicon.ico')
def favicon():
    """Serve favicon"""
    return send_from_directory(
        os.path.join(current_app.root_path, 'static'),
        'favicon.ico',
        mimetype='image/vnd.microsoft.icon'
    )