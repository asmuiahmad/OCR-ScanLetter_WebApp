import os
import json
import re
import logging
import traceback
from flask import (
    render_template, request, Blueprint, url_for, flash, redirect, jsonify, send_file, session, abort
)
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename
import pytesseract
from PIL import Image
import hashlib
from datetime import datetime
from config.extensions import db, load_metadata, save_metadata
from config.ocr_utils import (
    clean_text, extract_dates, extract_penerima_surat_keluar, extract_pengirim,
    calculate_file_hash, extract_isi_suratkeluar, extract_acara, extract_tempat,
    extract_tanggal_acara, extract_jam, calculate_ocr_accuracy
)
import io
from functools import wraps
from config.models import SuratKeluar
from sqlalchemy.exc import SQLAlchemyError

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

        # Log raw OCR text for debugging
        logger.info(f"Raw OCR Text for {file_path}:\n{cleaned_text}")

        # Log the full cleaned text for debugging kode surat
        logger.info(f"Full cleaned text for kode surat extraction:\n{cleaned_text}")

        # Coba ekstrak nomor surat dengan beberapa pola
        match_nomor_surat = re.search(r'(Nomor|NOMOR|Nomar)\s*:\s*(.*?)\n', cleaned_text, re.DOTALL)
        if match_nomor_surat:
            extracted_data['nomor_surat'] = match_nomor_surat.group(2).strip()
            logger.info(f"Extracted Nomor Surat: {extracted_data['nomor_surat']}")
        else:
            # Coba pola alternatif
            match_nomor_alt = re.search(r'Nomor\s+Surat\s*[:.]?\s*([A-Z0-9./-]+)', cleaned_text, re.IGNORECASE)
            if match_nomor_alt:
                extracted_data['nomor_surat'] = match_nomor_alt.group(1).strip()
                logger.info(f"Extracted Nomor Surat (Alt): {extracted_data['nomor_surat']}")

        # Ekstraksi data
        extracted_data['pengirim'] = extract_pengirim(cleaned_text)
        logger.info(f"Extracted Pengirim: {extracted_data['pengirim']}")

        extracted_data['penerima'] = extract_penerima_surat_keluar(cleaned_text)
        logger.info(f"Extracted Penerima: {extracted_data['penerima']}")

        extracted_data['isi'] = extract_isi_suratkeluar(cleaned_text)
        logger.info(f"Extracted Isi: {extracted_data['isi']}")

        extracted_data['acara'] = extract_acara(cleaned_text)
        logger.info(f"Extracted Acara: {extracted_data['acara']}")

        extracted_data['tempat'] = extract_tempat(cleaned_text)
        logger.info(f"Extracted Tempat: {extracted_data['tempat']}")

        extracted_data['tanggal_acara'] = extract_tanggal_acara(cleaned_text)
        logger.info(f"Extracted Tanggal Acara: {extracted_data['tanggal_acara']}")

        extracted_data['jam'] = extract_jam(cleaned_text)
        logger.info(f"Extracted Jam: {extracted_data['jam']}")

        # Tambahkan pola tambahan untuk ekstraksi kode surat
        match_kodesurat = re.search(r'(HK\d+\.\d+)', cleaned_text)
        if match_kodesurat:
            extracted_data['kodesurat2'] = match_kodesurat.group(1).strip()
            logger.info(f"Extracted kodesurat2 (direct HK match): {extracted_data['kodesurat2']}")
        
        # Fallback untuk kode surat jika belum terisi
        if extracted_data.get('kodesurat2', 'Not found') == 'Not found':
            # Coba pola lain untuk kode surat
            match_kodesurat_alt = re.search(r'/([A-Z]+\d+\.\d+)/', cleaned_text)
            if match_kodesurat_alt:
                extracted_data['kodesurat2'] = match_kodesurat_alt.group(1).strip()
                logger.info(f"Extracted kodesurat2 (alt match): {extracted_data['kodesurat2']}")
            else:
                logger.warning("No kodesurat2 found in the text")

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
    extracted_text = ""
    processed_files = 0
    
    if request.method == 'POST':
        # Log all available files in the request
        logger.info(f"Request files: {list(request.files.keys())}")
        
        metadata = load_metadata()
        
        # Tangani kasus tidak ada file yang dipilih
        files = request.files.getlist('image') or request.files.getlist('file')
        
        logger.info(f"Found {len(files)} files in upload")
        
        if not files or all(file.filename == '' for file in files):
            logger.warning("No files selected for upload")
            return render_template('home/ocr_surat_keluar.html',
                                   extracted_data_list=extracted_data_list,
                                   image_paths=image_paths,
                                   extracted_text=extracted_text,
                                   currentIndex=0)

        for file in files:
            if file.filename == '':
                continue
                
            filename = secure_filename(file.filename or '')
            file_path = os.path.join(UPLOAD_FOLDER, filename)
            
            try:
                file.save(file_path)
                logger.debug(f"File saved to: {file_path}")
                file_hash = calculate_file_hash(file_path)
                
                # Cek apakah file sudah diproses sebelumnya
                if filename in metadata.get("surat_keluar", {}) and metadata["surat_keluar"][filename] == file_hash:
                    logger.info(f"File '{filename}' already processed")
                    continue
                    
                extracted_data = extract_ocr_data(file_path)
                if extracted_data:
                    extracted_data_list.append(extracted_data)
                    metadata.setdefault("surat_keluar", {})[filename] = file_hash
                    image_paths.append(filename)
                    processed_files += 1
                    
                    # Tambahkan teks yang diekstrak ke extracted_text
                    extracted_text += f"--- Dokumen: {filename} ---\n{extracted_data.get('isi', 'Tidak ada teks')}\n\n"
                else:
                    logger.warning(f"No data extracted from file: {filename}")
            except Exception as e:
                logger.error(f"Error processing file {filename}: {str(e)}\n{traceback.format_exc()}")

        save_metadata(metadata)

        return render_template('home/ocr_surat_keluar.html',
                               extracted_data_list=extracted_data_list,
                               image_paths=image_paths,
                               extracted_text=extracted_text,
                               currentIndex=0)

    return render_template('home/ocr_surat_keluar.html',
                           extracted_data_list=extracted_data_list,
                           image_paths=image_paths,
                           extracted_text=extracted_text,
                           currentIndex=0)

@ocr_surat_keluar_bp.route('/surat_keluar_image/<int:id>')
@login_required
def surat_keluar_image(id):
    surat = SuratKeluar.query.get_or_404(id)
    return send_file(io.BytesIO(surat.gambar_suratKeluar), mimetype='image/png')

@ocr_surat_keluar_bp.route('/save_extracted_data', methods=['POST'])
@login_required
@role_required('admin', 'pimpinan')
def save_extracted_data():
    try:
        data = request.get_json()
        if not data:
            return jsonify({"success": False, "error": "No data provided"})

        # Load existing metadata
        metadata = load_metadata()
        
        # Inisialisasi kunci jika belum ada
        if "surat_keluar" not in metadata:
            metadata["surat_keluar"] = {}

        # Proses setiap item data
        for item in data:
            try:
                # Tentukan kode surat
                kode_surat = (
                    item.get('kodesurat2', 'Not found') if item.get('kodesurat2', 'Not found') != 'Not found'
                    else 'Not found'
                )

                # Buat objek SuratKeluar baru
                surat_keluar = SuratKeluar(
                    nomor_suratKeluar=item.get('full_letter_number', 'Not found'),
                    pengirim_suratKeluar=item.get('pengirim_suratKeluar', 'Not found'),
                    penerima_suratKeluar=item.get('penerima_suratKeluar', 'Not found'),
                    isi_suratKeluar=item.get('isi_suratKeluar', 'Not found'),
                    tanggal_suratKeluar=datetime.strptime(item.get('tanggal_suratKeluar'), '%Y-%m-%d') if item.get('tanggal_suratKeluar') else datetime.utcnow(),
                    initial_nomor_suratKeluar=item.get('full_letter_number', 'Not found'),
                    initial_pengirim_suratKeluar=item.get('pengirim_suratKeluar', 'Not found'),
                    initial_penerima_suratKeluar=item.get('penerima_suratKeluar', 'Not found'),
                    initial_isi_suratKeluar=item.get('isi_suratKeluar', 'Not found'),
                    status_suratKeluar='pending'  # Set initial status to pending
                )

                # Simpan ke database
                db.session.add(surat_keluar)
                db.session.commit()

                # Update metadata untuk file yang berhasil disimpan
                if item.get('filename'):
                    metadata['surat_keluar'][item['filename']] = {
                        'id': surat_keluar.id_suratKeluar,
                        'nomor_surat': surat_keluar.nomor_suratKeluar,
                        'kode_surat': kode_surat,
                        'saved_at': datetime.now().isoformat()
                    }

            except Exception as e:
                db.session.rollback()
                logger.error(f"Error saving Surat Keluar: {str(e)}")
                return jsonify({"success": False, "error": str(e)})

        # Simpan metadata yang diperbarui
        save_metadata(metadata)

        return jsonify({"success": True})

    except Exception as e:
        logger.error(f"Error in save_extracted_data: {str(e)}")
        return jsonify({"success": False, "error": str(e)})