import os
import re
import json
from flask import (
    render_template, request, Blueprint, url_for, flash, redirect, jsonify, send_file, send_from_directory
)
from flask_login import login_required
from werkzeug.utils import secure_filename
import pytesseract
from PIL import Image
import hashlib
from datetime import datetime
from config.extensions import db
from config.models import SuratMasuk
from config.ocr_utils import calculate_ocr_accuracy
from config.ocr_utils import (
    clean_text,
    extract_dates,
    extract_tanggal,
    extract_penerima_surat_masuk,
    extract_pengirim,
    calculate_file_hash,
    extract_isi
)
import io
from sqlalchemy import func, extract
from datetime import date, timedelta

ocr_surat_masuk_bp = Blueprint('ocr_surat_masuk', __name__)

# Load dictionary and other constants
target_code = "W15-A12"

# Define the path for metadata
METADATA_PATH = 'metadata.json'

def save_metadata(metadata):
    with open(METADATA_PATH, 'w') as f:
        json.dump(metadata, f, indent=4)

def load_metadata():
    if os.path.exists(METADATA_PATH):
        with open(METADATA_PATH, 'r') as f:
            metadata = json.load(f)
        # Ensure the 'surat_masuk' section exists
        if "surat_masuk" not in metadata:
            metadata["surat_masuk"] = {}
        return metadata
    else:
        # Initialize metadata with the correct structure
        metadata = {
            "surat_masuk": {}
        }
        save_metadata(metadata)
        return metadata

def extract_ocr_data(file_path):
    try:
        img = Image.open(file_path)
        ocr_output = pytesseract.image_to_string(img)
        cleaned_text = clean_text(ocr_output)
        
        extracted_data = {
            'nomor_surat': 'Not found',
            'kodePA': 'Not found',
            'kodesurat1': 'Not found',
            'kodesurat2': 'Not found',
            'bulan': 'Not found',
            'tahun': 'Not found',
            'dates': extract_dates(cleaned_text),
            'penerima': extract_penerima_surat_masuk(cleaned_text),
            'pengirim': extract_pengirim(cleaned_text),
            'jenis_surat': 'Umum',
            'isi': extract_isi(cleaned_text),
            'filename': os.path.basename(file_path),
            'id_suratMasuk': None  # Initialize id_suratMasuk
        }
        
        match_nomor_surat = re.search(r"(\d+)(?=\s*/)", cleaned_text)
        if match_nomor_surat:
            extracted_data['nomor_surat'] = match_nomor_surat.group(1).strip()
        
        if target_code in cleaned_text:
            extracted_data['kodePA'] = target_code
        
        match_kodesurat1 = re.search(r"/\s*([A-Za-z0-9\-.]+)\s*\." + re.escape(target_code), cleaned_text)
        if match_kodesurat1:
            extracted_data['kodesurat1'] = re.sub(r'\.{2,}', '.', match_kodesurat1.group(1))
        
        match_kodesurat2 = re.search(r"{}\s*/\s*([A-Za-z0-9\-.]+)\s*/".format(target_code), cleaned_text)
        if match_kodesurat2:
            extracted_data['kodesurat2'] = re.sub(r'\.{2,}', '.', match_kodesurat2.group(1))
            if extracted_data['kodesurat2'].startswith('HK'):
                extracted_data['jenis_surat'] = 'Perkara'
            elif extracted_data['kodesurat2'].startswith('KP'):
                extracted_data['jenis_surat'] = 'Kepegawaian'
        
        match_bulan = re.search(r"/\s*([A-Za-z0-9]+)\s*/", cleaned_text)
        if match_bulan:
            bulan = match_bulan.group(1)
            extracted_data['bulan'] = bulan
            extracted_data['bulan_display'] = bulan.replace('1', 'I')
        
        match_tahun = re.search(r"/\s*" + re.escape(extracted_data['bulan']) + r"\s*/\s*(\d{4})", cleaned_text)
        if match_tahun:
            extracted_data['tahun'] = match_tahun.group(1)
        
        extracted_data['isi'] = extract_isi(cleaned_text)
        
        extracted_data['full_letter_number'] = f"{extracted_data['nomor_surat']}/{extracted_data['kodesurat1']}.{extracted_data['kodePA']}/{extracted_data['kodesurat2']}/{extracted_data['bulan_display']}/{extracted_data['tahun']}"
        
        return extracted_data
    except Exception as e:
        flash(f"Error during OCR processing: {e}", 'danger')
        return None

@ocr_surat_masuk_bp.route('/ocr_surat_masuk', methods=['GET', 'POST'])
@login_required
def ocr_surat_masuk():
    extracted_data_list = []
    image_paths = []
    if request.method == 'POST':
        metadata = load_metadata()
        if 'image' in request.files:
            files = request.files.getlist('image')
            if not files:
                flash('No selected files', 'warning')
                return redirect(url_for('ocr_surat_masuk.ocr_surat_masuk'))
            for file in files:
                if file.filename == '':
                    continue
                filename = secure_filename(file.filename)
                file_path = os.path.join('static/ocr/surat_masuk', filename)
                file.save(file_path)
                file_hash = calculate_file_hash(file_path)
                if metadata['surat_masuk'].get(filename) == file_hash:
                    flash(f"File '{filename}' already processed.", 'info')
                    continue
                extracted_data = extract_ocr_data(file_path)
                if extracted_data:
                    extracted_data_list.append(extracted_data)
                    metadata['surat_masuk'][filename] = file_hash
                    image_paths.append(filename)
            save_metadata(metadata)
            return render_template('home/ocr_surat_masuk.html', 
                                extracted_data_list=extracted_data_list,
                                image_paths=image_paths,
                                currentIndex=0)
        elif 'filename' in request.form:
            try:
                with open(os.path.join('static/ocr/surat_masuk', request.form['filename']), 'rb') as f:
                    gambar_suratMasuk = f.read()
                
                new_surat = SuratMasuk(
                    tanggal_suratMasuk=datetime.strptime(request.form['selected_date'], '%d/%m/%Y'),
                    pengirim_suratMasuk=request.form['pengirim'],
                    penerima_suratMasuk=request.form['penerima'],
                    nomor_suratMasuk=request.form['full_letter_number'],
                    kode_suratMasuk=request.form['kodesurat2'],
                    jenis_suratMasuk=request.form['jenis_surat'],
                    isi_suratMasuk=request.form['isi'],
                    gambar_suratMasuk=gambar_suratMasuk,
                    created_at=datetime.now()
                )
                db.session.add(new_surat)
                db.session.commit()

                now = datetime.utcnow()
                start_of_year = datetime(now.year, 1, 1)
                start_of_month = datetime(now.year, now.month, 1)
                start_of_week = now - timedelta(days=now.weekday())
                start_of_week = datetime.combine(start_of_week.date(), datetime.min.time())

                return jsonify(success=True, counts={
                    "total": SuratMasuk.query.count(),
                    "this_year": SuratMasuk.query.filter(SuratMasuk.created_at >= start_of_year).count(),
                    "this_month": SuratMasuk.query.filter(SuratMasuk.created_at >= start_of_month).count(),
                    "this_week": SuratMasuk.query.filter(SuratMasuk.created_at >= start_of_week).count()
                })

            except Exception as e:
                db.session.rollback()
                return jsonify(success=False, error=str(e))
            
    return render_template('home/ocr_surat_masuk.html', extracted_data_list=extracted_data_list, image_paths=image_paths, currentIndex=0)

@ocr_surat_masuk_bp.route('/surat_masuk_image/<int:id>')
@login_required
def surat_masuk_image(id):
    surat = SuratMasuk.query.get_or_404(id)
    return send_file(io.BytesIO(surat.gambar_suratMasuk), mimetype='image/png')

@ocr_surat_masuk_bp.route('/static/ocr/surat_masuk/<filename>')
@login_required
def uploaded_file_surat_masuk(filename):
    return send_from_directory('static/ocr/surat_masuk', filename)