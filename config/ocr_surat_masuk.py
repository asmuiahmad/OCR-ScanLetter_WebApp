import os
import json
import re
import logging
import traceback
from flask import (
    render_template, request, Blueprint, url_for, flash, redirect, jsonify, send_file, session, abort, current_app
)
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename
import pytesseract
from PIL import Image
import hashlib
from datetime import datetime
from config.extensions import db, load_metadata, save_metadata
from config.ocr_utils import (
    clean_text, extract_dates, extract_penerima_surat_masuk, extract_pengirim,
    calculate_file_hash, extract_isi_suratkeluar, extract_acara, extract_tempat,
    extract_tanggal_acara, extract_jam, calculate_ocr_accuracy, extract_document_code,
    extract_roman_numeral, normalize_ocr_text, extract_text_with_multiple_configs
)
import io
from functools import wraps
from config.models import SuratMasuk
from sqlalchemy.exc import SQLAlchemyError
import random
import string

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

METADATA_PATH = 'metadata.json'

# Perbaiki UPLOAD_FOLDER
def get_upload_folder():
    return os.path.join(current_app.root_path, 'static', 'ocr', 'surat_masuk')

# Fungsi validasi file
def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in {'png', 'jpg', 'jpeg', 'webp', 'tiff', 'bmp'}

# Pastikan direktori upload ada
def ensure_upload_folder():
    upload_folder = get_upload_folder()
    os.makedirs(upload_folder, exist_ok=True)
    return upload_folder

def save_metadata(metadata):
    with open(METADATA_PATH, 'w') as f:
        json.dump(metadata, f, indent=4)

def load_metadata():
    if os.path.exists(METADATA_PATH):
        with open(METADATA_PATH, 'r') as f:
            return json.load(f)
    return {"surat_masuk": {}}

def robust_parse_date(date_str):
    if not date_str or not isinstance(date_str, str):
        return None
    for fmt in ("%Y-%m-%d", "%d/%m/%Y", "%d-%m-%Y", "%d %B %Y", "%d %b %Y"):
        try:
            return datetime.strptime(date_str, fmt).strftime("%Y-%m-%d")
        except Exception:
            continue
    return None

def parse_date_to_ddmmyyyy(date_str):
    if not date_str or not isinstance(date_str, str):
        return None
    # Cek jika sudah yyyy-mm-dd
    try:
        dt = datetime.strptime(date_str, '%Y-%m-%d')
        return dt.strftime('%d/%m/%Y')
    except Exception:
        pass
    # Cek jika format dd Month yyyy
    months = {
        'januari': '01', 'februari': '02', 'maret': '03', 'april': '04', 'mei': '05', 'juni': '06',
        'juli': '07', 'agustus': '08', 'september': '09', 'oktober': '10', 'november': '11', 'desember': '12',
        'January': '01', 'February': '02', 'March': '03', 'April': '04', 'May': '05', 'June': '06',
        'July': '07', 'August': '08', 'September': '09', 'October': '10', 'November': '11', 'December': '12'
    }
    match = re.match(r'(\d{1,2})\s+([A-Za-z]+)\s+(\d{4})', date_str)
    if match:
        day, month, year = match.groups()
        month_num = months.get(month.lower().capitalize()) or months.get(month.lower())
        if month_num:
            return f"{int(day):02d}/{month_num}/{year}"
    # Cek jika format dd/mm/yyyy
    match = re.match(r'(\d{1,2})/(\d{1,2})/(\d{4})', date_str)
    if match:
        return f"{int(match.group(1)):02d}/{int(match.group(2)):02d}/{match.group(3)}"
    return None

def extract_ocr_data_surat_masuk(file_path):
    try:
        logger.info(f"Extracting OCR data from: {file_path}")
        
        # Extract text from image using the multiple configs approach
        ocr_output = extract_text_with_multiple_configs(file_path)
        
        if not ocr_output:
            logger.warning(f"No text extracted from {file_path}")
            return None
            
        raw_text = ocr_output
        logger.info(f"Full raw text for kode surat extraction:\n{raw_text}")
        
        nomor_suratMasuk = 'Not found'
        nomor_variants = [
            'Nomor', 'No', 'Nomer', 'NOMOR', 'NO', 'N0', 'Nomar', 'Nomur', 'Nomot', 'Nomoe',
            'nomor', 'no', 'nomer', 'nomar', 'nomur', 'nomot', 'nomoe'
        ]
        nomor_regex = r'(?:' + '|'.join(nomor_variants) + r')'
        lines = raw_text.splitlines()
        for line in lines:
            match = re.search(nomor_regex + r'.*[:：](.*)', line, re.IGNORECASE)
            if match:
                nomor_suratMasuk = match.group(1).strip()
                logger.info(f"Extracted nomor_surat: {nomor_suratMasuk}")
                break
        # Jika tidak ditemukan, tetap return 'Not found'
        
        # Field lain juga gunakan raw_text
        tanggal = extract_dates(raw_text)
        # --- FIX: Always output a single string in 'YYYY-MM-DD' format ---
        tanggal_str = ''
        if tanggal:
            if isinstance(tanggal, list):
                for t in tanggal:
                    parsed = robust_parse_date(t)
                    if parsed:
                        tanggal_str = parsed
                        break
                if not tanggal_str:
                    tanggal_str = tanggal[0]  # fallback to first raw
            else:
                parsed = robust_parse_date(tanggal)
                tanggal_str = parsed if parsed else tanggal
        
        # Pastikan format tanggal YYYY-MM-DD
        if tanggal_str and isinstance(tanggal_str, str) and re.match(r"\d{4}-\d{2}-\d{2}", tanggal_str):
            tanggal_final = tanggal_str
        else:
            tanggal_final = datetime.now().strftime("%Y-%m-%d")  # Default jika tidak valid
            logger.warning(f"Using current date as fallback: {tanggal_final}")
        
        pengirim = extract_pengirim(raw_text)
        penerima = extract_penerima_surat_masuk(raw_text)
        isi_surat = extract_isi_suratkeluar(raw_text)  # RAW, tanpa clean_text
        acara = extract_acara(raw_text)
        tempat = extract_tempat(raw_text)
        tanggal_acara = extract_tanggal_acara(raw_text)
        tanggal_acara = parse_date_to_ddmmyyyy(tanggal_acara) or tanggal_acara
        jam = extract_jam(raw_text)
        
        # Calculate hash for file identification
        file_hash = calculate_file_hash(file_path)
        
        # Log hasil ekstraksi untuk debugging
        logger.info(f"Extraction results for {file_path}:")
        logger.info(f"  nomor_surat: {nomor_suratMasuk}")
        logger.info(f"  tanggal: {tanggal_final}")
        logger.info(f"  pengirim: {pengirim}")
        logger.info(f"  penerima: {penerima}")
        logger.info(f"  isi length: {len(isi_surat) if isi_surat else 0}")
        
        return {
            'nomor_surat': nomor_suratMasuk,
            'tanggal': tanggal_final,  # <-- always a string
            'pengirim': pengirim,
            'penerima': penerima,
            'isi': isi_surat,
            'acara': acara,
            'tempat': tempat,
            'tanggal_acara': tanggal_acara,
            'jam': jam,
            'file_hash': file_hash,
            'raw_ocr': raw_text  # Tambahkan hasil raw OCR
        }
        
    except Exception as e:
        logger.error(f"Error in extract_ocr_data_surat_masuk: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        return None

def process_batch_ocr_surat_masuk(folder_path, max_files=None):
    """
    Process multiple files in a directory for OCR extraction
    """
    try:
        logger.info(f"Processing batch OCR from folder: {folder_path}")
        if not os.path.exists(folder_path):
            logger.error(f"Folder path does not exist: {folder_path}")
            return [], "Folder not found"
            
        # Get all image files in the folder
        image_files = [os.path.join(folder_path, f) for f in os.listdir(folder_path)
                     if os.path.isfile(os.path.join(folder_path, f)) and 
                     f.lower().endswith(('.png', '.jpg', '.jpeg', '.tif', '.tiff', '.bmp', '.webp'))]
        
        if max_files:
            image_files = image_files[:max_files]
            
        logger.info(f"Found {len(image_files)} image files to process")
        
        results = []
        extracted_text = ""
        
        for file_path in image_files:
            filename = os.path.basename(file_path)
            logger.info(f"Processing file: {filename}")
            
            try:
                extracted_data = extract_ocr_data_surat_masuk(file_path)
                if extracted_data:
                    extracted_data['filename'] = filename
                    results.append(extracted_data)
                    
                    # Add extracted text
                    extracted_text += f"--- Dokumen: {filename} ---\n{extracted_data.get('isi', 'Tidak ada teks')}\n\n"
                else:
                    logger.warning(f"No data extracted from file: {filename}")
            except Exception as e:
                logger.error(f"Error processing file {filename}: {str(e)}")
                
        return results, extracted_text
        
    except Exception as e:
        logger.error(f"Error in batch processing: {str(e)}")
        return [], f"Error: {str(e)}"

def save_batch_results_to_db_surat_masuk(results):
    """
    Save batch OCR results to database for surat keluar
    """
    try:
        saved_count = 0
        for item in results:
            try:
                # Handle tanggal utama
                tgl = item.get('tanggal')
                tanggal_suratMasuk = datetime.utcnow()  # default value
                
                if tgl:
                    try:
                        # Coba parsing format YYYY-MM-DD
                        tanggal_suratMasuk = datetime.strptime(tgl, '%Y-%m-%d')
                    except ValueError:
                        try:
                            # Coba parsing format lain
                            for fmt in ("%d/%m/%Y", "%d-%m-%Y", "%d %B %Y", "%d %b %Y"):
                                try:
                                    tanggal_suratMasuk = datetime.strptime(tgl, fmt)
                                    break
                                except ValueError:
                                    continue
                        except Exception:
                            # Gunakan tanggal sekarang jika parsing gagal
                            tanggal_suratMasuk = datetime.utcnow()
                
                # Handle tanggal acara
                tgl_acara = item.get('tanggal_acara')
                tanggal_acara_suratMasuk = None
                
                if tgl_acara:
                    try:
                        # Coba parsing format yang mungkin
                        for fmt in ("%d/%m/%Y", "%d-%m-%Y", "%d %B %Y", "%d %b %Y"):
                            try:
                                dt = datetime.strptime(tgl_acara, fmt)
                                tanggal_acara_suratMasuk = dt.date()
                                break
                            except ValueError:
                                continue
                    except Exception:
                        tanggal_acara_suratMasuk = None
                
                # Buat dictionary untuk parameter SuratMasuk
                surat_masuk_data = {
                    'tanggal_suratMasuk': tanggal_suratMasuk,
                    'pengirim_suratMasuk': item.get('pengirim', 'Not found'),
                    'penerima_suratMasuk': item.get('penerima', 'Not found'),
                    'nomor_suratMasuk': item.get('nomor_surat', 'Not found'),
                    'isi_suratMasuk': item.get('isi', 'Not found'),
                    'acara_suratMasuk': item.get('acara', ''),
                    'tempat_suratMasuk': item.get('tempat', ''),
                    'tanggal_acara_suratMasuk': tanggal_acara_suratMasuk,
                    'jam_suratMasuk': item.get('jam', ''),
                    'status_suratMasuk': 'pending',
                    'initial_nomor_suratMasuk': item.get('nomor_surat', 'Not found'),
                    'initial_pengirim_suratMasuk': item.get('pengirim', 'Not found'),
                    'initial_penerima_suratMasuk': item.get('penerima', 'Not found'),
                    'initial_isi_suratMasuk': item.get('isi', 'Not found')
                }
                
                surat_masuk = SuratMasuk(**surat_masuk_data)
                
                # Simpan ke database
                db.session.add(surat_masuk)
                db.session.commit()
                saved_count += 1
                logger.info(f"Saved document to database: {item.get('nomor_surat', 'Not found')}")
                
            except Exception as e:
                db.session.rollback()
                logger.error(f"Error saving document to database: {str(e)}")
                logger.error(traceback.format_exc())
                
        return saved_count
        
    except Exception as e:
        logger.error(f"Error in save_batch_results_to_db_surat_masuk: {str(e)}")
        logger.error(traceback.format_exc())
        return 0

@ocr_surat_masuk_bp.route('/ocr_surat_masuk', methods=['GET', 'POST'])
@login_required
@role_required('admin', 'pimpinan')
def ocr_surat_masuk():
    try:
        extracted_data_list = []
        image_paths = []
        processed_files = 0
        
        if request.method == 'POST':
            # Pastikan direktori upload ada
            UPLOAD_FOLDER = ensure_upload_folder()
            
            # Tangani kasus tidak ada file yang dipilih
            files = request.files.getlist('image')
            
            if not files or all(file.filename == '' for file in files):
                flash('Tidak ada file yang dipilih untuk diunggah.', 'error')
                return render_template('home/ocr_surat_masuk.html',
                                       extracted_data_list=[],
                                       image_paths=[],
                                       currentIndex=0)

            for file in files:
                if file.filename == '':
                    continue
                
                try:
                    filename = secure_filename(file.filename)
                    
                    # Validasi file
                    if not allowed_file(filename):
                        flash(f"File '{filename}' tidak diizinkan. Hanya file dengan ekstensi .png, .jpg, .jpeg, .webp, .tiff, .bmp yang diizinkan.", 'error')
                        continue
                    
                    file_path = os.path.join(UPLOAD_FOLDER, filename)
                    file.save(file_path)
                    
                    # Proses OCR
                    extracted_data = extract_ocr_data_surat_masuk(file_path)
                    
                    if extracted_data:
                        extracted_data['filename'] = filename
                        extracted_data_list.append(extracted_data)
                        image_paths.append(f'/static/ocr/surat_masuk/{filename}')
                        processed_files += 1
                    else:
                        flash(f"Tidak ada data yang diekstrak dari file: {filename}", 'warning')
                        
                except Exception as e:
                    logger.error(f"Error processing file {filename}: {str(e)}")
                    flash(f"Terjadi kesalahan saat memproses file {filename}", 'error')
            
            # Simpan batch results ke database
            if extracted_data_list:
                saved_count = save_batch_results_to_db_surat_masuk(extracted_data_list)
                if saved_count > 0:
                    flash(f"Berhasil memproses {saved_count} dokumen", 'success')
            
            return render_template('home/ocr_surat_masuk.html', 
                                   extracted_data_list=extracted_data_list, 
                                   image_paths=image_paths,
                                   currentIndex=0)
        
        # Untuk GET request, tampilkan halaman kosong
        return render_template('home/ocr_surat_masuk.html', 
                               extracted_data_list=[], 
                               image_paths=[],
                               currentIndex=0)
                               
    except Exception as e:
        logger.error(f"Error in ocr_surat_masuk: {str(e)}")
        flash("Terjadi kesalahan sistem", 'error')
        return render_template('home/ocr_surat_masuk.html', 
                               extracted_data_list=[], 
                               image_paths=[],
                               currentIndex=0)

@ocr_surat_masuk_bp.route('/surat_masuk_image/<int:id>')
@login_required
def surat_masuk_image(id):
    surat = SuratMasuk.query.get_or_404(id)
    return send_file(io.BytesIO(surat.gambar_suratMasuk), mimetype='image/png')

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
                # Ambil tanggal, bisa string atau list
                tgl = item.get('tanggal')
                if isinstance(tgl, list):
                    tgl = tgl[0] if tgl and len(tgl) > 0 else ''
                if tgl:
                    try:
                        tanggal_obj = datetime.strptime(tgl, '%Y-%m-%d')
                    except Exception:
                        try:
                            # Coba format lain (dd/mm/yyyy)
                            tanggal_obj = datetime.strptime(tgl, '%d/%m/%Y')
                        except Exception:
                            tanggal_obj = datetime.utcnow()
                else:
                    tanggal_obj = datetime.utcnow()

                # Tanggal acara (opsional)
                tgl_acara = item.get('tanggal_acara_suratMasuk')
                if tgl_acara:
                    try:
                        tanggal_acara_obj = datetime.strptime(tgl_acara, '%Y-%m-%d').date()
                    except Exception:
                        try:
                            tanggal_acara_obj = datetime.strptime(tgl_acara, '%d/%m/%Y').date()
                        except Exception:
                            tanggal_acara_obj = None
                else:
                    tanggal_acara_obj = None

                # Hitung ocr_accuracy_suratMasuk
                initial_isi = item.get('isi_suratMasuk', '')
                edited_isi = item.get('isi_suratMasuk', '')
                ocr_accuracy = calculate_ocr_accuracy(initial_isi, edited_isi)

                surat_masuk = SuratMasuk(
                    tanggal_suratMasuk=tanggal_obj,
                    pengirim_suratMasuk=item.get('pengirim_suratMasuk', 'Not found'),
                    penerima_suratMasuk=item.get('penerima_suratMasuk', 'Not found'),
                    nomor_suratMasuk=item.get('full_letter_number', 'Not found'),
                    isi_suratMasuk=item.get('isi_suratMasuk', 'Not found'),
                    acara_suratMasuk=item.get('acara_suratMasuk', ''),
                    tempat_suratMasuk=item.get('tempat_suratMasuk', ''),
                    tanggal_acara_suratMasuk=tanggal_acara_obj,
                    jam_suratMasuk=item.get('jam_suratMasuk', ''),
                    status_suratMasuk='pending',
                    initial_nomor_suratMasuk=item.get('full_letter_number', 'Not found'),
                    initial_pengirim_suratMasuk=item.get('pengirim_suratMasuk', 'Not found'),
                    initial_penerima_suratMasuk=item.get('penerima_suratMasuk', 'Not found'),
                    initial_isi_suratMasuk=item.get('isi_suratMasuk', 'Not found'),
                    ocr_accuracy_suratMasuk=ocr_accuracy
                )

                # Simpan ke database
                db.session.add(surat_masuk)
                db.session.commit()

                # Update metadata untuk file yang berhasil disimpan
                if item.get('filename'):
                    metadata['surat_masuk'][item['filename']] = {
                        'id': surat_masuk.id_suratMasuk,
                        'nomor_surat': surat_masuk.nomor_suratMasuk,
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