import os
import json
import re
import logging
import traceback
from flask import (
    render_template, request, Blueprint, url_for, flash, redirect, jsonify, send_file, session
)
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename
import pytesseract
from PIL import Image
import hashlib
from datetime import datetime
from config.extensions import db
from config.ocr_utils import (
    clean_text, extract_dates, extract_penerima_surat_keluar, extract_pengirim,
    calculate_file_hash, extract_isi_suratkeluar, extract_acara, extract_tempat,
    extract_tanggal_acara, extract_jam, calculate_ocr_accuracy
)
import io
from functools import wraps

# Setup logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

ocr_surat_keluar_bp = Blueprint('ocr_surat_keluar', __name__)

# Role required decorator for blueprints
def role_required(*roles):
    def wrapper(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if current_user.role not in roles:
                flash('You do not have permission to access this page.', 'error')
                return redirect(url_for('index'))
            return f(*args, **kwargs)
        return decorated_function
    return wrapper

METADATA_PATH = 'metadata.json'
UPLOAD_FOLDER = 'static/ocr/surat_keluar'

# Pastikan direktori upload ada
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

def save_metadata(metadata):
    with open(METADATA_PATH, 'w') as f:
        json.dump(metadata, f, indent=4)

def load_metadata():
    if os.path.exists(METADATA_PATH):
        with open(METADATA_PATH, 'r') as f:
            return json.load(f)
    return {"surat_keluar": {}}

def extract_ocr_data(file_path):
    try:
        logger.debug(f"Processing file: {file_path}")
        img = Image.open(file_path)

        custom_config = r'--oem 3 --psm 6'
        ocr_output = pytesseract.image_to_string(img, config=custom_config)
        cleaned_text = clean_text(ocr_output)
        logger.debug(f"Cleaned OCR Text:\n{cleaned_text}")

        extracted_data = {
            'nomor_surat': 'Not found',
            'pengirim': 'Not found',
            'penerima': 'Not found',
            'isi': 'Not found',
            'dates': extract_dates(cleaned_text),
            'filename': os.path.basename(file_path),
            'id_suratKeluar': None,
            'ocr_raw_text': cleaned_text,
            'acara': 'Not found',
            'tempat': 'Not found',
            'tanggal_acara': 'Not found',
            'jam': 'Not found'
        }

        # Coba ekstrak nomor surat dengan beberapa pola
        match_nomor_surat = re.search(r'(Nomor|NOMOR|Nomar)\s*:\s*(.*?)\n', cleaned_text, re.DOTALL)
        if match_nomor_surat:
            extracted_data['nomor_surat'] = match_nomor_surat.group(2).strip()
        else:
            # Coba pola alternatif
            match_nomor_alt = re.search(r'Nomor\s+Surat\s*[:.]?\s*([A-Z0-9./-]+)', cleaned_text, re.IGNORECASE)
            if match_nomor_alt:
                extracted_data['nomor_surat'] = match_nomor_alt.group(1).strip()

        extracted_data['pengirim'] = extract_pengirim(cleaned_text)
        extracted_data['penerima'] = extract_penerima_surat_keluar(cleaned_text)
        extracted_data['isi'] = extract_isi_suratkeluar(cleaned_text)
        extracted_data['acara'] = extract_acara(cleaned_text)
        extracted_data['tempat'] = extract_tempat(cleaned_text)
        extracted_data['tanggal_acara'] = extract_tanggal_acara(cleaned_text)
        extracted_data['jam'] = extract_jam(cleaned_text)

        logger.debug(f"Extracted data: {json.dumps(extracted_data, indent=2, ensure_ascii=False)}")
        return extracted_data
    except Exception as e:
        logger.error(f"Error during OCR processing: {str(e)}\n{traceback.format_exc()}")
        flash(f"Error during OCR processing: {e}", 'danger')
        return None

@ocr_surat_keluar_bp.route('/ocr_surat_keluar', methods=['GET', 'POST'])
@login_required
@role_required('admin', 'pimpinan')
def ocr_surat_keluar():
    extracted_data_list = []
    image_paths = []
    
    if request.method == 'POST':
        metadata = load_metadata()
        
        # Tangani kasus tidak ada file yang dipilih
        if 'image' not in request.files:
            flash('No selected files', 'warning')
            return redirect(url_for('ocr_surat_keluar.ocr_surat_keluar'))
            
        files = request.files.getlist('image')
        if not files or all(file.filename == '' for file in files):
            flash('No selected files', 'warning')
            return redirect(url_for('ocr_surat_keluar.ocr_surat_keluar'))

        processed_files = 0
        
        for file in files:
            if file.filename == '':
                continue
                
            filename = secure_filename(file.filename)
            file_path = os.path.join(UPLOAD_FOLDER, filename)
            
            try:
                file.save(file_path)
                logger.debug(f"File saved to: {file_path}")
                file_hash = calculate_file_hash(file_path)
                
                # Cek apakah file sudah diproses sebelumnya
                if filename in metadata.get("surat_keluar", {}) and metadata["surat_keluar"][filename] == file_hash:
                    flash(f"File '{filename}' already processed.", 'info')
                    continue
                    
                extracted_data = extract_ocr_data(file_path)
                if extracted_data:
                    extracted_data_list.append(extracted_data)
                    metadata.setdefault("surat_keluar", {})[filename] = file_hash
                    image_paths.append(filename)
                    processed_files += 1
            except Exception as e:
                logger.error(f"Error processing file {filename}: {str(e)}\n{traceback.format_exc()}")
                flash(f"Error processing file {filename}: {e}", 'danger')

        save_metadata(metadata)
        
        if processed_files == 0:
            flash("No new files processed", 'info')
        else:
            # Hitung field yang tidak ditemukan
            not_found_counts = {
                'nomor_suratKeluar': 0,
                'pengirim_suratKeluar': 0,
                'penerima_suratKeluar': 0,
                'isi_suratKeluar': 0,
            }
            
            for data in extracted_data_list:
                if data.get('nomor_surat') == 'Not found':
                    not_found_counts['nomor_suratKeluar'] += 1
                if data.get('pengirim') == 'Not found':
                    not_found_counts['pengirim_suratKeluar'] += 1
                if data.get('penerima') == 'Not found':
                    not_found_counts['penerima_suratKeluar'] += 1
                if data.get('isi') == 'Not found':
                    not_found_counts['isi_suratKeluar'] += 1
            
            session['not_found_keluar'] = not_found_counts
            flash(f"Successfully processed {processed_files} files", 'success')

        return render_template('home/ocr_surat_keluar.html',
                               extracted_data_list=extracted_data_list,
                               image_paths=image_paths,
                               currentIndex=0)

    return render_template('home/ocr_surat_keluar.html',
                           extracted_data_list=extracted_data_list,
                           image_paths=image_paths,
                           currentIndex=0)

@ocr_surat_keluar_bp.route('/surat_keluar_image/<int:id>')
@login_required
def surat_keluar_image(id):
    surat = SuratKeluar.query.get_or_404(id)
    return send_file(io.BytesIO(surat.gambar_suratKeluar), mimetype='image/png')