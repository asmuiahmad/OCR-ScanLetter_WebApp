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
    clean_text, extract_dates, extract_penerima_surat_keluar, extract_pengirim,
    calculate_file_hash, extract_isi_suratkeluar, extract_acara, extract_tempat,
    extract_tanggal_acara, extract_jam, calculate_ocr_accuracy, extract_document_code,
    extract_roman_numeral, normalize_ocr_text, extract_text_with_multiple_configs
)
import io
from functools import wraps
from config.models import SuratKeluar
from sqlalchemy.exc import SQLAlchemyError
import random
import string

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

# Perbaiki UPLOAD_FOLDER
def get_upload_folder():
    return os.path.join(current_app.root_path, 'static', 'ocr', 'surat_keluar')

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
    return {"surat_keluar": {}}

def robust_parse_date(date_str):
    """
    Try to parse a date string in various formats and return as 'YYYY-MM-DD'.
    Return None if parsing fails.
    """
    if not date_str or not isinstance(date_str, str):
        return None
    for fmt in ("%Y-%m-%d", "%d/%m/%Y", "%d-%m-%Y", "%d %B %Y", "%d %b %Y"):
        try:
            return datetime.strptime(date_str, fmt).strftime("%Y-%m-%d")
        except Exception:
            continue
    return None

def parse_date_to_ddmmyyyy(date_str):
    """
    Konversi tanggal seperti '17 September 2024' atau '07 Oktober 2024' ke 'dd/mm/yyyy'.
    Jika sudah dalam format yyyy-mm-dd, konversi ke dd/mm/yyyy.
    Jika tidak bisa diparse, return None.
    """
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

def extract_ocr_data_surat_keluar(file_path):
    """
    Extract OCR data from surat keluar document
    """
    try:
        logger.info(f"Extracting OCR data from: {file_path}")
        
        # Extract text from image using the multiple configs approach
        ocr_output = extract_text_with_multiple_configs(file_path)
        
        if not ocr_output:
            logger.warning(f"No text extracted from {file_path}")
            return None
            
        # Gunakan raw OCR langsung tanpa cleaning/normalizing
        raw_text = ocr_output
        logger.info(f"Full raw text for kode surat extraction:\n{raw_text}")
        
        # Ambil nomor surat keluar: deteksi baris yang mengandung 'Nomor' (atau variasinya), ambil setelah ':' hingga newline
        nomor_suratKeluar = 'Not found'
        nomor_variants = [
            'Nomor', 'No', 'Nomer', 'NOMOR', 'NO', 'N0', 'Nomar', 'Nomur', 'Nomot', 'Nomoe',
            'nomor', 'no', 'nomer', 'nomar', 'nomur', 'nomot', 'nomoe'
        ]
        nomor_regex = r'(?:' + '|'.join(nomor_variants) + r')'
        lines = raw_text.splitlines()
        for line in lines:
            match = re.search(nomor_regex + r'.*[:：](.*)', line, re.IGNORECASE)
            if match:
                nomor_suratKeluar = match.group(1).strip()
                logger.info(f"Extracted nomor_surat: {nomor_suratKeluar}")
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
        penerima = extract_penerima_surat_keluar(raw_text)
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
        logger.info(f"  nomor_surat: {nomor_suratKeluar}")
        logger.info(f"  tanggal: {tanggal_final}")
        logger.info(f"  pengirim: {pengirim}")
        logger.info(f"  penerima: {penerima}")
        logger.info(f"  isi length: {len(isi_surat) if isi_surat else 0}")
        
        return {
            'nomor_surat': nomor_suratKeluar,
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
        logger.error(f"Error in extract_ocr_data_surat_keluar: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        return None

def process_batch_ocr_surat_keluar(folder_path, max_files=None):
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
                extracted_data = extract_ocr_data_surat_keluar(file_path)
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

def save_batch_results_to_db_surat_keluar(results):
    """
    Save batch OCR results to database for surat keluar
    """
    try:
        saved_count = 0
        for item in results:
            try:
                # Handle tanggal utama
                tgl = item.get('tanggal')
                tanggal_suratKeluar = datetime.utcnow()  # default value
                
                if tgl:
                    try:
                        # Coba parsing format YYYY-MM-DD
                        tanggal_suratKeluar = datetime.strptime(tgl, '%Y-%m-%d')
                    except ValueError:
                        try:
                            # Coba parsing format lain
                            for fmt in ("%d/%m/%Y", "%d-%m-%Y", "%d %B %Y", "%d %b %Y"):
                                try:
                                    tanggal_suratKeluar = datetime.strptime(tgl, fmt)
                                    break
                                except ValueError:
                                    continue
                        except Exception:
                            # Gunakan tanggal sekarang jika parsing gagal
                            tanggal_suratKeluar = datetime.utcnow()
                
                # Handle tanggal acara
                tgl_acara = item.get('tanggal_acara')
                tanggal_acara_suratKeluar = None
                
                if tgl_acara:
                    try:
                        # Coba parsing format yang mungkin
                        for fmt in ("%d/%m/%Y", "%d-%m-%Y", "%d %B %Y", "%d %b %Y"):
                            try:
                                dt = datetime.strptime(tgl_acara, fmt)
                                tanggal_acara_suratKeluar = dt.date()
                                break
                            except ValueError:
                                continue
                    except Exception:
                        tanggal_acara_suratKeluar = None
                
                # Buat dictionary untuk parameter SuratKeluar
                surat_keluar_data = {
                    'tanggal_suratKeluar': tanggal_suratKeluar,
                    'pengirim_suratKeluar': item.get('pengirim', 'Not found'),
                    'penerima_suratKeluar': item.get('penerima', 'Not found'),
                    'nomor_suratKeluar': item.get('nomor_surat', 'Not found'),
                    'isi_suratKeluar': item.get('isi', 'Not found'),
                    'acara_suratKeluar': item.get('acara', ''),
                    'tempat_suratKeluar': item.get('tempat', ''),
                    'tanggal_acara_suratKeluar': tanggal_acara_suratKeluar,
                    'jam_suratKeluar': item.get('jam', ''),
                    'status_suratKeluar': 'pending',
                    'initial_nomor_suratKeluar': item.get('nomor_surat', 'Not found'),
                    'initial_pengirim_suratKeluar': item.get('pengirim', 'Not found'),
                    'initial_penerima_suratKeluar': item.get('penerima', 'Not found'),
                    'initial_isi_suratKeluar': item.get('isi', 'Not found')
                }
                
                surat_keluar = SuratKeluar(**surat_keluar_data)
                
                # Simpan ke database
                db.session.add(surat_keluar)
                db.session.commit()
                saved_count += 1
                logger.info(f"Saved document to database: {item.get('nomor_surat', 'Not found')}")
                
            except Exception as e:
                db.session.rollback()
                logger.error(f"Error saving document to database: {str(e)}")
                logger.error(traceback.format_exc())
                
        return saved_count
        
    except Exception as e:
        logger.error(f"Error in save_batch_results_to_db_surat_keluar: {str(e)}")
        logger.error(traceback.format_exc())
        return 0

@ocr_surat_keluar_bp.route('/ocr_surat_keluar', methods=['GET', 'POST'])
@login_required
@role_required('admin', 'pimpinan')
def ocr_surat_keluar():
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
                return render_template('home/ocr_surat_keluar.html',
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
                    extracted_data = extract_ocr_data_surat_keluar(file_path)
                    
                    if extracted_data:
                        extracted_data['filename'] = filename
                        extracted_data_list.append(extracted_data)
                        image_paths.append(f'/static/ocr/surat_keluar/{filename}')
                        processed_files += 1
                    else:
                        flash(f"Tidak ada data yang diekstrak dari file: {filename}", 'warning')
                        
                except Exception as e:
                    logger.error(f"Error processing file {filename}: {str(e)}")
                    flash(f"Terjadi kesalahan saat memproses file {filename}", 'error')
            
            # Simpan batch results ke database
            if extracted_data_list:
                saved_count = save_batch_results_to_db_surat_keluar(extracted_data_list)
                if saved_count > 0:
                    flash(f"Berhasil memproses {saved_count} dokumen", 'success')
            
            return render_template('home/ocr_surat_keluar.html', 
                                   extracted_data_list=extracted_data_list, 
                                   image_paths=image_paths,
                                   currentIndex=0)
        
        # Untuk GET request, tampilkan halaman kosong
        return render_template('home/ocr_surat_keluar.html', 
                               extracted_data_list=[], 
                               image_paths=[],
                               currentIndex=0)
                               
    except Exception as e:
        logger.error(f"Error in ocr_surat_keluar: {str(e)}")
        flash("Terjadi kesalahan sistem", 'error')
        return render_template('home/ocr_surat_keluar.html', 
                               extracted_data_list=[], 
                               image_paths=[],
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
                tgl_acara = item.get('tanggal_acara_suratKeluar')
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

                # Hitung ocr_accuracy_suratKeluar
                initial_isi = item.get('isi_suratKeluar', '')
                edited_isi = item.get('isi_suratKeluar', '')
                ocr_accuracy = calculate_ocr_accuracy(initial_isi, edited_isi)

                surat_keluar = SuratKeluar(
                    tanggal_suratKeluar=tanggal_obj,
                    pengirim_suratKeluar=item.get('pengirim_suratKeluar', 'Not found'),
                    penerima_suratKeluar=item.get('penerima_suratKeluar', 'Not found'),
                    nomor_suratKeluar=item.get('full_letter_number', 'Not found'),
                    isi_suratKeluar=item.get('isi_suratKeluar', 'Not found'),
                    acara_suratKeluar=item.get('acara_suratKeluar', ''),
                    tempat_suratKeluar=item.get('tempat_suratKeluar', ''),
                    tanggal_acara_suratKeluar=tanggal_acara_obj,
                    jam_suratKeluar=item.get('jam_suratKeluar', ''),
                    status_suratKeluar='pending',
                    initial_nomor_suratKeluar=item.get('full_letter_number', 'Not found'),
                    initial_pengirim_suratKeluar=item.get('pengirim_suratKeluar', 'Not found'),
                    initial_penerima_suratKeluar=item.get('penerima_suratKeluar', 'Not found'),
                    initial_isi_suratKeluar=item.get('isi_suratKeluar', 'Not found'),
                    ocr_accuracy_suratKeluar=ocr_accuracy
                )

                # Simpan ke database
                db.session.add(surat_keluar)
                db.session.commit()

                # Update metadata untuk file yang berhasil disimpan
                if item.get('filename'):
                    metadata['surat_keluar'][item['filename']] = {
                        'id': surat_keluar.id_suratKeluar,
                        'nomor_surat': surat_keluar.nomor_suratKeluar,
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