import os
import re
import json
import logging
import traceback
from flask import (
    render_template, request, Blueprint, url_for, flash, redirect, 
    jsonify, send_file, session, current_app, send_from_directory
)
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename
import pytesseract
from PIL import Image
import hashlib
from datetime import datetime
from sqlalchemy.exc import SQLAlchemyError
from config.extensions import db, load_metadata, save_metadata
from config.models import SuratMasuk
from config.ocr_utils import (
    clean_text, extract_dates, extract_penerima_surat_masuk, extract_pengirim,
    calculate_file_hash, extract_isi_suratmasuk, calculate_ocr_accuracy,
    is_formulir_cuti, extract_formulir_cuti_data  # Impor fungsi baru
)
import io
from functools import wraps

# Setup logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

ocr_surat_masuk_bp = Blueprint('ocr_surat_masuk', __name__)

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

target_code = "W15-A12"
METADATA_PATH = 'metadata.json'
UPLOAD_FOLDER = 'static/ocr/surat_masuk'

# Pastikan direktori upload ada
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

def save_metadata(metadata):
    try:
        with open(METADATA_PATH, 'w') as f:
            json.dump(metadata, f, indent=4)
    except Exception as e:
        logger.error(f"Error saving metadata: {str(e)}")

def load_metadata():
    if os.path.exists(METADATA_PATH):
        try:
            with open(METADATA_PATH, 'r') as f:
                metadata = json.load(f)
            if "surat_masuk" not in metadata:
                metadata["surat_masuk"] = {}
            return metadata
        except json.JSONDecodeError:
            logger.warning("Metadata file corrupted, creating new one")
            return {"surat_masuk": {}}
    else:
        return {"surat_masuk": {}}

def extract_ocr_data(file_path):
    try:
        logger.debug(f"Processing file: {file_path}")
        img = Image.open(file_path)
        
        # Konfigurasi Tesseract
        custom_config = r'--oem 3 --psm 6'
        ocr_output = pytesseract.image_to_string(img, config=custom_config)
        cleaned_text = clean_text(ocr_output)
        logger.debug(f"Cleaned OCR Text:\n{cleaned_text}")

        # Deteksi formulir cuti
        if is_formulir_cuti(cleaned_text):
            cuti_data = extract_formulir_cuti_data(cleaned_text)
            return {
                'jenis_dokumen': 'FORMULIR_CUTI',
                'nomor_suratMasuk': 'N/A',
                'kodePA': 'N/A',
                'kodesurat1': 'N/A',
                'kodesurat2': 'CUTI',
                'bulan': 'N/A',
                'tahun': 'N/A',
                'dates': [cuti_data['tanggal']] if cuti_data['tanggal'] != 'N/A' else [],
                'penerima_suratMasuk': 'Bagian Kepegawaian',
                'pengirim_suratMasuk': cuti_data['nama'],
                'jenis_surat': 'Permohonan Cuti',
                'isi_suratMasuk': f"Permohonan cuti: {cuti_data['jenis_cuti']}",
                'filename': os.path.basename(file_path),
                'id_suratMasuk': None,
                'full_letter_number': 'FORMULIR CUTI'
            }

        # Ekstraksi normal untuk surat masuk
        extracted_data = {
            'jenis_dokumen': 'SURAT_MASUK',
            'nomor_suratMasuk': 'Not found',
            'kodePA': 'Not found',
            'kodesurat1': 'Not found',
            'kodesurat2': 'Not found',
            'bulan': 'Not found',
            'tahun': 'Not found',
            'dates': extract_dates(cleaned_text),
            'penerima_suratMasuk': extract_penerima_surat_masuk(cleaned_text),
            'pengirim_suratMasuk': extract_pengirim(cleaned_text),
            'jenis_surat': 'Umum',
            'isi_suratMasuk': extract_isi_suratmasuk(cleaned_text),
            'filename': os.path.basename(file_path),
            'id_suratMasuk': None,
            'full_letter_number': 'Not found'
        }

        cleaned_text = re.sub(r"W\s*1\s*5\s*[-\s]*A\s*1\s*2", target_code, cleaned_text, flags=re.IGNORECASE)

        pattern_full = rf"(\d+)[/\s-]+([\w.\-]+?)\.?{re.escape(target_code)}[/\s-]+([\w.\-]+)[/\s-]+([A-Za-z0-9]+)[/\s-]+(\d{{4}})"
        match = re.search(pattern_full, cleaned_text, re.IGNORECASE)

        if match:
            extracted_data['nomor_suratMasuk'] = match.group(1).strip()
            extracted_data['kodesurat1'] = match.group(2).strip()
            extracted_data['kodePA'] = target_code
            extracted_data['kodesurat2'] = match.group(3).strip()
            extracted_data['bulan'] = match.group(4).strip().replace('1', 'I')
            extracted_data['tahun'] = match.group(5).strip()

            # Tentukan jenis surat berdasarkan awalan kode surat 2
            if extracted_data['kodesurat2'].startswith('HK'):
                extracted_data['jenis_surat'] = 'Perkara'
            elif extracted_data['kodesurat2'].startswith('KP'):
                extracted_data['jenis_surat'] = 'Kepegawaian'
                
            # Bangun full_letter_number dengan format yang benar
            extracted_data['full_letter_number'] = (
                f"{extracted_data['nomor_suratMasuk']}/"
                f"{extracted_data['kodesurat1']}."
                f"{extracted_data['kodePA']}/"
                f"{extracted_data['kodesurat2']}/"
                f"{extracted_data['bulan']}/"
                f"{extracted_data['tahun']}"
            )
        else:
            # Fallback jika regex utama gagal
            if target_code in cleaned_text:
                extracted_data['kodePA'] = target_code

            match_nomor = re.search(r"(\d+)(?=\s*/)", cleaned_text)
            if match_nomor:
                extracted_data['nomor_suratMasuk'] = match_nomor.group(1)

            match_kodesurat1 = re.search(r"/\s*([\w\-.]+)\s*(?:\.|\s)" + re.escape(target_code), cleaned_text)
            if match_kodesurat1:
                extracted_data['kodesurat1'] = match_kodesurat1.group(1).strip()

            # Log the full cleaned text for debugging kode surat
            logger.info(f"Full cleaned text for kode surat extraction:\n{cleaned_text}")

            # Tambahkan pola tambahan untuk ekstraksi kode surat
            match_kodesurat = re.search(r'(HK\d+\.\d+)', cleaned_text)
            if match_kodesurat:
                extracted_data['kodesurat2'] = match_kodesurat.group(1).strip()
                logger.info(f"Extracted kodesurat2 (direct HK match): {extracted_data['kodesurat2']}")
                if extracted_data['kodesurat2'].startswith('HK'):
                    extracted_data['jenis_surat'] = 'Perkara'
            
            # Fallback untuk kode surat jika belum terisi
            if extracted_data.get('kodesurat2', 'Not found') == 'Not found':
                # Coba pola lain untuk kode surat
                match_kodesurat_alt = re.search(r'/([A-Z]+\d+\.\d+)/', cleaned_text)
                if match_kodesurat_alt:
                    extracted_data['kodesurat2'] = match_kodesurat_alt.group(1).strip()
                    logger.info(f"Extracted kodesurat2 (alt match): {extracted_data['kodesurat2']}")
                    if extracted_data['kodesurat2'].startswith('HK'):
                        extracted_data['jenis_surat'] = 'Perkara'
                else:
                    logger.warning("No kodesurat2 found in the text")

            match_bulan = re.search(r"/\s*([A-Za-z0-9]+)\s*/", cleaned_text)
            if match_bulan:
                extracted_data['bulan'] = match_bulan.group(1).strip().replace('1', 'I')

            match_tahun = re.search(r"/\s*" + re.escape(extracted_data.get('bulan', '')) + r"\s*/\s*(\d{4})", cleaned_text)
            if match_tahun:
                extracted_data['tahun'] = match_tahun.group(1)

            # Bangun full_letter_number jika komponen tersedia
            if all(extracted_data[k] != 'Not found' for k in ['nomor_suratMasuk', 'kodesurat1', 'kodePA', 'kodesurat2', 'bulan', 'tahun']):
                extracted_data['full_letter_number'] = (
                    f"{extracted_data['nomor_suratMasuk']}/"
                    f"{extracted_data['kodesurat1']}."
                    f"{extracted_data['kodePA']}/"
                    f"{extracted_data['kodesurat2']}/"
                    f"{extracted_data['bulan']}/"
                    f"{extracted_data['tahun']}"
                )

        logger.debug(f"Extracted data: {json.dumps(extracted_data, indent=2, ensure_ascii=False)}")
        return extracted_data

    except Exception as e:
        logger.error(f"Error during OCR processing: {str(e)}\n{traceback.format_exc()}")
        return None

@ocr_surat_masuk_bp.route('/ocr_surat_masuk', methods=['GET', 'POST'])
@login_required
@role_required('admin', 'pimpinan')
def ocr_surat_masuk():
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
            return render_template('home/ocr_surat_masuk.html',
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
                if filename in metadata.get("surat_masuk", {}) and metadata["surat_masuk"][filename] == file_hash:
                    logger.info(f"File '{filename}' already processed")
                    continue
                    
                extracted_data = extract_ocr_data(file_path)
                if extracted_data:
                    extracted_data_list.append(extracted_data)
                    metadata.setdefault("surat_masuk", {})[filename] = file_hash
                    image_paths.append(filename)
                    processed_files += 1
                    
                    # Tambahkan teks yang diekstrak ke extracted_text
                    extracted_text += f"--- Dokumen: {filename} ---\n{extracted_data.get('isi_suratMasuk', 'Tidak ada teks')}\n\n"
                else:
                    logger.warning(f"No data extracted from file: {filename}")
            except Exception as e:
                logger.error(f"Error processing file {filename}: {str(e)}\n{traceback.format_exc()}")

        save_metadata(metadata)

        return render_template('home/ocr_surat_masuk.html',
                               extracted_data_list=extracted_data_list,
                               image_paths=image_paths,
                               extracted_text=extracted_text,
                               currentIndex=0)

    return render_template('home/ocr_surat_masuk.html',
                           extracted_data_list=extracted_data_list,
                           image_paths=image_paths,
                           extracted_text=extracted_text,
                           currentIndex=0)

@ocr_surat_masuk_bp.route('/surat_masuk_image/<int:id>')
@login_required
def surat_masuk_image(id):
    surat = SuratMasuk.query.get_or_404(id)
    return send_file(io.BytesIO(surat.gambar_suratMasuk), mimetype='image/png')

@ocr_surat_masuk_bp.route('/static/ocr/surat_masuk/<filename>')
@login_required
def uploaded_file_surat_masuk(filename):
    return send_from_directory('static/ocr/surat_masuk', filename)

@ocr_surat_masuk_bp.route('/save_extracted_data', methods=['POST'])
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
        if "surat_masuk" not in metadata:
            metadata["surat_masuk"] = {}

        # Proses setiap item data
        for item in data:
            try:
                # Tentukan kode surat
                kode_surat = (
                    item.get('kodesurat2', 'Not found') if item.get('kodesurat2', 'Not found') != 'Not found'
                    else item.get('kode_suratMasuk', 'Not found')
                )

                # Buat objek SuratMasuk baru
                surat_masuk = SuratMasuk(
                    full_letter_number=item.get('full_letter_number', 'Not found'),
                    nomor_suratMasuk=item.get('full_letter_number', 'Not found'),
                    pengirim_suratMasuk=item.get('pengirim_suratMasuk', 'Not found'),
                    penerima_suratMasuk=item.get('penerima_suratMasuk', 'Not found'),
                    kode_suratMasuk=kode_surat,
                    jenis_suratMasuk=item.get('jenis_surat', 'Umum'),
                    isi_suratMasuk=item.get('isi_suratMasuk', 'Not found'),
                    tanggal_suratMasuk=datetime.strptime(item.get('tanggal_suratMasuk'), '%Y-%m-%d') if item.get('tanggal_suratMasuk') else datetime.utcnow(),
                    initial_full_letter_number=item.get('full_letter_number', 'Not found'),
                    initial_nomor_suratMasuk=item.get('full_letter_number', 'Not found'),
                    initial_pengirim_suratMasuk=item.get('pengirim_suratMasuk', 'Not found'),
                    initial_penerima_suratMasuk=item.get('penerima_suratMasuk', 'Not found'),
                    initial_isi_suratMasuk=item.get('isi_suratMasuk', 'Not found'),
                    status_suratMasuk='pending'  # Set initial status to pending
                )

                # Simpan ke database
                db.session.add(surat_masuk)
                db.session.commit()

                # Update metadata untuk file yang berhasil disimpan
                if item.get('filename'):
                    metadata['surat_masuk'][item['filename']] = {
                        'id': surat_masuk.id_suratMasuk,
                        'nomor_surat': surat_masuk.nomor_suratMasuk,
                        'kode_surat': kode_surat,
                        'saved_at': datetime.now().isoformat()
                    }

            except Exception as e:
                db.session.rollback()
                logger.error(f"Error saving Surat Masuk: {str(e)}")
                return jsonify({"success": False, "error": str(e)})

        # Simpan metadata yang diperbarui
        save_metadata(metadata)

        return jsonify({"success": True})

    except Exception as e:
        logger.error(f"Error in save_extracted_data: {str(e)}")
        return jsonify({"success": False, "error": str(e)})