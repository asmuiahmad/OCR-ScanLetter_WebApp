import os
import re
import json
import logging
import traceback
from flask import (
    render_template, request, Blueprint, url_for, flash, redirect, 
    jsonify, send_file, session, current_app, send_from_directory, abort
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
    is_formulir_cuti, extract_formulir_cuti_data, extract_text_with_multiple_configs,
    extract_document_code, extract_roman_numeral, normalize_ocr_text, extract_tanggal,
    extract_nomor_surat
)
import io
from functools import wraps
from config.forms import OCRSuratMasukForm
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
        
        # Use new text extraction method
        ocr_output = extract_text_with_multiple_configs(file_path)
        
        if not ocr_output:
            logger.warning(f"No text extracted from {file_path}")
            return None
        
        cleaned_text = clean_text(ocr_output)
        normalized_text = normalize_ocr_text(cleaned_text)
        
        # Add more detailed logging for debugging
        logger.debug("===== RAW OCR OUTPUT =====")
        logger.debug(ocr_output)
        logger.debug("===== CLEANED OCR TEXT =====")
        logger.debug(cleaned_text)
        logger.debug("===== NORMALIZED TEXT =====")
        logger.debug(normalized_text)

        # Deteksi formulir cuti
        if is_formulir_cuti(cleaned_text):
            cuti_data = extract_formulir_cuti_data(cleaned_text)
            nomor_surat_cuti = extract_nomor_surat(cleaned_text)
            kode_dokumen = extract_document_code(cleaned_text)
            # Ambil tanggal dari hasil ekstraksi tanggal jika ada, jika tidak baru ambil dari cuti_data
            tanggal_ekstrak = extract_tanggal(cleaned_text)
            tanggal_final = tanggal_ekstrak if tanggal_ekstrak and tanggal_ekstrak != 'Not found' else cuti_data.get('tanggal', 'N/A')
            # Tentukan jenis surat dari kode dokumen
            if kode_dokumen and kode_dokumen.startswith('KP'):
                jenis_surat = 'Kepegawaian'
            elif kode_dokumen and kode_dokumen.startswith('HM'):
                jenis_surat = 'Umum'
            elif kode_dokumen and kode_dokumen.startswith('HK'):
                jenis_surat = 'Perkara'
            else:
                jenis_surat = 'Cuti'
            isi_cuti = f"Surat Permintaan Cuti oleh {cuti_data.get('nama', 'N/A')} (NIP: {cuti_data.get('nip', 'N/A')}) - {cuti_data.get('jenis_cuti', 'N/A')} pada {cuti_data.get('tanggal', 'N/A')}"
            return {
                'nomor_surat': nomor_surat_cuti if nomor_surat_cuti and nomor_surat_cuti != 'Not found' else 'Not found',
                'kodesurat2': kode_dokumen if kode_dokumen and kode_dokumen != 'Not found' else 'Cuti',
                'jenis_surat': jenis_surat,
                'tanggal': tanggal_final,
                'pengirim': cuti_data.get('nama', 'N/A'),
                'penerima': 'Ketua Pengadilan Agama',
                'isi': isi_cuti,
                'file_hash': calculate_file_hash(file_path)
            }

        # Use ORIGINAL cleaned text for document number extraction to preserve structure
        # This prevents over-normalization that changes PAN.PA.W15 to 4/KPA.W15
        text_for_nomor = cleaned_text  # Use original cleaned text, not normalized

        # Tambahkan berbagai pola pencarian untuk nomor surat dengan pola yang lebih fleksibel
        nomor_patterns = [
            # Pattern untuk format: 1931/PAN.PA.W15-A12/HM2.1.4/X/2024 (preserve original structure)
            r'(?:Nomor|No|Nomer|NOMOR)\s*[:.\-]?\s*(\d+)[/\s-]+([A-Za-z.]+)\.?(?:W15-A12|W15[-\s]*A12)[/\s-]+([A-Z0-9.]+)[/\s-]+(\d{0,1}[XIVxvi]+)[/\s-]+(\d{4})',
            # Pattern untuk format: 1931/PAN.PA.W15-A12/HK.2.6/X/2024 (preserve original structure)
            r'(?:Nomor|No|Nomer|NOMOR)\s*[:.\-]?\s*(\d+)[/\s-]+([A-Za-z.]+)\.?(?:W15-A12|W15[-\s]*A12)[/\s-]+([A-Z0-9.]+)[/\s-]+(\d{0,1}[XIVxvi]+)[/\s-]+(\d{4})',
            # More flexible patterns that preserve original structure
            r'(?:Nomor|No|Nomer|NOMOR)\s*[:.\-]?\s*(\d+).*?(?:W15-A12|W15[-\s]*A12).*?([A-Z0-9.]+).*?([IVX]+).*?(\d{4})',
            r'(?:Nomor|No|Nomer|NOMOR)\s*[:.\-]?\s*(\d+).*?(?:W15|W.*?15).*?([A-Z0-9.]+).*?([IVX0-9]+).*?(\d{4})',
        ]

        nomor_suratMasuk = 'Not found'
        kodesurat1 = 'Not found'
        kodePA = 'Not found'
        kodesurat2 = 'Not found'
        bulan = 'Not found'
        tahun = 'Not found'
        full_letter_number = 'Not found'

        # Try to match with the patterns using ORIGINAL text
        for i, pattern in enumerate(nomor_patterns):
            logger.debug(f"Trying pattern {i}: {pattern}")
            match = re.search(pattern, text_for_nomor, re.IGNORECASE)
            if match:
                logger.debug(f"Pattern {i} matched: {match.groups()}")
                
                if len(match.groups()) >= 5:  # Complete pattern
                    nomor_suratMasuk = match.group(1)
                    kodesurat1 = match.group(2)  # Preserve original like "PAN.PA"
                    kodePA = 'W15-A12'  # Standard code
                    kodesurat2 = match.group(3)  # Preserve original like "HK.2.6"
                    bulan = match.group(4).upper().replace('1X', 'IX')
                    tahun = match.group(5)
                    logger.debug(f"nomor_suratMasuk: {nomor_suratMasuk}")
                    logger.debug(f"kodesurat1: {kodesurat1}")
                    logger.debug(f"kodePA: {kodePA}")
                    logger.debug(f"kodesurat2: {kodesurat2}")
                    logger.debug(f"bulan: {bulan}")
                    logger.debug(f"tahun: {tahun}")
                elif len(match.groups()) == 4:  # Flexible pattern
                    nomor_suratMasuk = match.group(1)
                    kodesurat1 = 'PAN.PA'  # Default to original structure
                    kodePA = 'W15-A12'  # Standard code
                    kodesurat2 = match.group(2)
                    bulan = match.group(3)
                    tahun = match.group(4)
                
                # Construct the full letter number preserving original structure
                full_letter_number = f"{nomor_suratMasuk}/{kodesurat1.rstrip('.')}.{kodePA}/{kodesurat2}/{bulan}/{tahun}"
                logger.debug(f"Full letter number: {full_letter_number}")
                break

        # If no match found with the standard patterns, try to extract parts
        if full_letter_number == 'Not found':
            # Extract document code using original text
            hm_code = extract_document_code(text_for_nomor)
            
            # Extract Roman numeral for month using original text
            roman_numeral = extract_roman_numeral(text_for_nomor)
            
            # Extract basic number using original text
            nomor_match = re.search(r'(?:Nomor|No|Nomer|NOMOR)\s*[:.\-]?\s*(\d+)', text_for_nomor, re.IGNORECASE)
            if nomor_match:
                nomor_suratMasuk = nomor_match.group(1)
            
            # Extract year using original text
            year_match = re.search(r'\b(20\d{2})\b', text_for_nomor)
            if year_match:
                tahun = year_match.group(1)
            
            # If we have all the essential parts, construct the full letter number
            if nomor_suratMasuk != 'Not found' and hm_code != 'Not found' and roman_numeral != 'Not found' and tahun != 'Not found':
                full_letter_number = f"{nomor_suratMasuk}/PAN.PA.W15-A12/{hm_code}/{roman_numeral}/{tahun}"
                logger.debug(f"Constructed full letter number: {full_letter_number}")

        # Ensure kodesurat2 is always filled if possible
        if kodesurat2 == 'Not found':
            kodesurat2 = extract_document_code(text_for_nomor)

        # Extract other information using normalized text for better accuracy
        tanggal = extract_tanggal(normalized_text)
        pengirim = extract_pengirim(normalized_text)
        penerima = extract_penerima_surat_masuk(normalized_text)
        isi_surat = extract_isi_suratmasuk(normalized_text)
        
        # Log extracted tanggal for debugging
        logger.debug(f"Extracted tanggal: {tanggal}")
        logger.debug(f"Extracted pengirim: {pengirim}")
        logger.debug(f"Extracted penerima: {penerima}")
        logger.debug(f"Extracted isi_surat: {isi_surat}")
        
        # Calculate hash for file identification
        file_hash = calculate_file_hash(file_path)
        
        return {
            'nomor_surat': full_letter_number,
            'kodesurat2': kodesurat2,
            'jenis_surat': 'Umum' if kodesurat2.startswith('HM') else ('Perkara' if kodesurat2.startswith('HK') else ('Kepegawaian' if kodesurat2.startswith('KP') else 'Umum')),
            'tanggal': tanggal,
            'pengirim': pengirim,
            'penerima': penerima,
            'isi': isi_surat,
            'file_hash': file_hash
        }

    except Exception as e:
        logger.error(f"Error in extract_ocr_data: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        return None

def process_batch_ocr(folder_path, max_files=None):
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
                extracted_data = extract_ocr_data(file_path)
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

def save_batch_results_to_db(results):
    """
    Save batch OCR results to database
    """
    try:
        saved_count = 0
        for item in results:
            try:
                # Generate a kode_surat from the nomor_surat
                kode_surat = "SM-" + ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))
                
                # Buat objek SuratMasuk baru
                surat_masuk = SuratMasuk(
                    full_letter_number=item.get('nomor_surat', 'Not found'),
                    nomor_suratMasuk=item.get('nomor_surat', 'Not found'),
                    tanggal_suratMasuk=datetime.strptime(item.get('tanggal')[0], '%Y-%m-%d') if item.get('tanggal') and item.get('tanggal')[0] else datetime.utcnow(),
                    pengirim_suratMasuk=item.get('pengirim', 'Not found'),
                    penerima_suratMasuk=item.get('penerima', 'Not found'),
                    kode_suratMasuk=kode_surat,
                    jenis_suratMasuk='Umum',
                    isi_suratMasuk=item.get('isi', 'Not found'),
                    initial_full_letter_number=item.get('nomor_surat', 'Not found'),
                    initial_pengirim_suratMasuk=item.get('pengirim', 'Not found'),
                    initial_penerima_suratMasuk=item.get('penerima', 'Not found'),
                    initial_isi_suratMasuk=item.get('isi', 'Not found'),
                    initial_nomor_suratMasuk=item.get('nomor_surat', 'Not found'),
                    status_suratMasuk='pending'
                )
                
                # Simpan file path
                if 'filename' in item:
                    surat_masuk.file_path = item['filename']
                
                # Simpan ke database
                db.session.add(surat_masuk)
                db.session.commit()
                saved_count += 1
                logger.info(f"Saved document to database: {item.get('nomor_surat', 'Not found')}")
                
            except Exception as e:
                db.session.rollback()
                logger.error(f"Error saving document to database: {str(e)}")
                
        return saved_count
        
    except Exception as e:
        logger.error(f"Error in save_batch_results_to_db: {str(e)}")
        return 0

@ocr_surat_masuk_bp.route('/ocr_surat_masuk', methods=['GET', 'POST'])
@login_required
@role_required('admin', 'pimpinan')
def ocr_surat_masuk():
    # Extensive logging for debugging
    logger.info("=== OCR Surat Masuk Route Started ===")
    logger.info(f"Request method: {request.method}")
    logger.info(f"Request content type: {request.content_type}")
    logger.info(f"Request headers: {dict(request.headers)}")
    
    # Debug all form data
    logger.info("Form Data:")
    for key, value in request.form.items():
        logger.info(f"  {key}: {value}")
    
    # Debug all files in request
    logger.info("Request Files:")
    for key in request.files:
        files = request.files.getlist(key)
        logger.info(f"  Key '{key}' files: {[file.filename for file in files]}")
    
    extracted_data_list = []
    image_paths = []
    extracted_text = ""
    processed_files = 0
    
    if request.method == 'POST':
        # Comprehensive file input debugging
        files = (
            request.files.getlist('image') or
            request.files.getlist('file') or
            request.files.getlist('files') or
            request.files.getlist('uploaded_files')
        )

        logger.info(f"Total files found: {len(files)}")

        for i, file in enumerate(files, 1):
            logger.info(f"File {i} Details:")
            logger.info(f"  Filename: {file.filename}")
            logger.info(f"  Content Type: {file.content_type}")
            logger.info(f"  Size: {len(file.read())} bytes")
            file.seek(0)

        if not files or all(file.filename == '' for file in files):
            logger.warning("No files selected for upload")
            flash('Silakan pilih dokumen terlebih dahulu', 'warning')
            return render_template('home/ocr_surat_masuk.html',
                                   extracted_data_list=[],
                                   image_paths=[],
                                   extracted_text='',
                                   currentIndex=0)

        os.makedirs(UPLOAD_FOLDER, exist_ok=True)

        for file in files:
            if file.filename == '':
                continue
            try:
                filename = secure_filename(file.filename or '')
                file_path = os.path.join(UPLOAD_FOLDER, filename)
                file.save(file_path)
                logger.debug(f"File saved to: {file_path}")
                file_hash = calculate_file_hash(file_path)
                extracted_data = extract_ocr_data(file_path)
                
                if extracted_data:
                    extracted_data['filename'] = filename
                    extracted_data_list.append(extracted_data)
                    image_paths.append(filename)
                    processed_files += 1
                    
                    # Add extracted text
                    extracted_text += f"--- Dokumen: {filename} ---\n{extracted_data.get('isi', 'Tidak ada teks')}\n\n"
                else:
                    logger.warning(f"No data extracted from file: {filename}")
        
            except Exception as e:
                logger.error(f'Error processing file {file.filename}: {e}')
                flash(f'Gagal memproses dokumen {filename}: {str(e)}', 'error')

        # Log the final extracted data for debugging
        logger.info("Final extracted data list:")
        for i, data in enumerate(extracted_data_list):
            logger.info(f"Item {i}: {data}")
        
        # Render template with extracted data
        return render_template('home/ocr_surat_masuk.html',
                               extracted_data_list=extracted_data_list,
                               image_paths=image_paths,
                               extracted_text=extracted_text,
                               currentIndex=0)

    # GET request handling
    return render_template('home/ocr_surat_masuk.html',
                           extracted_data_list=[],
                           image_paths=[],
                           extracted_text='',
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
        # Validate CSRF token
        if not request.headers.get('X-CSRFToken'):
            return jsonify({"success": False, "error": "CSRF token is missing"}), 400

        data = request.get_json()
        if not data:
            return jsonify({"success": False, "error": "No data provided"}), 400

        # Debug: Log the received data
        logger.info("Received data from frontend:")
        for item in data:
            logger.info(f"Item: {item}")

        # Load existing metadata
        metadata = load_metadata()
        
        # Inisialisasi kunci jika belum ada
        if "surat_masuk" not in metadata:
            metadata["surat_masuk"] = {}

        # Proses setiap item data
        for item in data:
            try:
                # Debug: Log individual field values
                logger.info(f"Processing item with fields:")
                logger.info(f"  full_letter_number: {item.get('full_letter_number')}")
                logger.info(f"  pengirim_suratMasuk: {item.get('pengirim_suratMasuk')}")
                logger.info(f"  penerima_suratMasuk: {item.get('penerima_suratMasuk')}")
                logger.info(f"  isi_suratMasuk: {item.get('isi_suratMasuk')}")
                logger.info(f"  tanggal: {item.get('tanggal')}")
                logger.info(f"  kode_suratMasuk: {item.get('kode_suratMasuk')}")
                logger.info(f"  jenis_surat: {item.get('jenis_surat')}")
                logger.info(f"  kodesurat2: {item.get('kodesurat2')}")

                # Tentukan kode surat - perbaiki mapping field
                kode_surat = (
                    item.get('kodesurat2', 'Not found') if item.get('kodesurat2', 'Not found') != 'Not found'
                    else item.get('kode_suratMasuk', 'Not found')
                )

                # Perbaiki mapping field dari frontend modal
                # Frontend mengirim field dengan nama yang berbeda
                nomor_surat = item.get('full_letter_number') or item.get('nomor_surat', 'Not found')
                pengirim = item.get('pengirim_suratMasuk') or item.get('pengirim', 'Not found')
                penerima = item.get('penerima_suratMasuk') or item.get('penerima', 'Not found')
                isi = item.get('isi_suratMasuk') or item.get('isi', 'Not found')
                jenis_surat = item.get('jenis_surat', 'Umum')
                
                # Handle tanggal - bisa dari selected_date atau tanggal_suratMasuk
                tanggal_str = item.get('selected_date') or item.get('tanggal_suratMasuk') or item.get('tanggal')
                if tanggal_str:
                    try:
                        tanggal_surat = datetime.strptime(tanggal_str, '%Y-%m-%d')
                        logger.info(f"Successfully parsed tanggal: {tanggal_surat}")
                    except ValueError:
                        logger.warning(f"Failed to parse tanggal: {tanggal_str}, using current time")
                        tanggal_surat = datetime.utcnow()
                else:
                    logger.warning("No tanggal provided, using current time")
                    tanggal_surat = datetime.utcnow()

                # Ambil nilai initial dari data OCR asli (jika tersedia)
                # Ini penting untuk perhitungan akurasi OCR
                initial_nomor = item.get('initial_full_letter_number') or item.get('nomor_surat', 'Not found')
                initial_pengirim = item.get('initial_pengirim_suratMasuk') or item.get('pengirim', 'Not found')
                initial_penerima = item.get('initial_penerima_suratMasuk') or item.get('penerima', 'Not found')
                initial_isi = item.get('initial_isi_suratMasuk') or item.get('isi', 'Not found')

                # Debug: Log nilai initial untuk verifikasi
                logger.info(f"Initial values for OCR accuracy calculation:")
                logger.info(f"  initial_nomor: {initial_nomor}")
                logger.info(f"  initial_pengirim: {initial_pengirim}")
                logger.info(f"  initial_penerima: {initial_penerima}")
                logger.info(f"  initial_isi: {initial_isi}")
                logger.info(f"  edited_nomor: {nomor_surat}")
                logger.info(f"  edited_pengirim: {pengirim}")
                logger.info(f"  edited_penerima: {penerima}")
                logger.info(f"  edited_isi: {isi}")

                # Buat objek SuratMasuk baru dengan field yang benar
                surat_masuk = SuratMasuk(
                    full_letter_number=nomor_surat,
                    nomor_suratMasuk=nomor_surat,
                    tanggal_suratMasuk=tanggal_surat,
                    pengirim_suratMasuk=pengirim,
                    penerima_suratMasuk=penerima,
                    kode_suratMasuk=kode_surat,
                    jenis_suratMasuk=jenis_surat,
                    isi_suratMasuk=isi,
                    initial_full_letter_number=initial_nomor,
                    initial_nomor_suratMasuk=initial_nomor,
                    initial_pengirim_suratMasuk=initial_pengirim,
                    initial_penerima_suratMasuk=initial_penerima,
                    initial_isi_suratMasuk=initial_isi,
                    status_suratMasuk='pending'  # Set initial status to pending
                )

                # Simpan ke database terlebih dahulu
                db.session.add(surat_masuk)
                db.session.commit()

                # Hitung akurasi OCR setelah data tersimpan
                try:
                    from config.ocr_utils import calculate_overall_ocr_accuracy
                    ocr_accuracy = calculate_overall_ocr_accuracy(surat_masuk, 'suratMasuk')
                    surat_masuk.ocr_accuracy_suratMasuk = ocr_accuracy
                    db.session.commit()
                    logger.info(f"Calculated OCR accuracy: {ocr_accuracy}%")
                except Exception as e:
                    logger.error(f"Error calculating OCR accuracy: {str(e)}")
                    surat_masuk.ocr_accuracy_suratMasuk = 0.0
                db.session.commit()

                # Update metadata untuk file yang berhasil disimpan
                if item.get('filename'):
                    metadata['surat_masuk'][item['filename']] = {
                        'id': surat_masuk.id_suratMasuk,
                        'nomor_surat': surat_masuk.nomor_suratMasuk,
                        'kode_surat': kode_surat,
                        'saved_at': datetime.now().isoformat()
                    }

                logger.info(f"Successfully saved Surat Masuk: {nomor_surat}")

            except Exception as e:
                db.session.rollback()
                logger.error(f"Error saving Surat Masuk: {str(e)}")
                return jsonify({"success": False, "error": str(e)})

        # Simpan metadata yang diperbarui
        save_metadata(metadata)

        # Tambahkan flash message untuk sukses
        flash('Data surat masuk berhasil disimpan ke database', 'success')

        return jsonify({"success": True, "message": "Data berhasil disimpan ke database"})

    except Exception as e:
        logger.error(f"Error in save_extracted_data: {str(e)}")
        return jsonify({"success": False, "error": str(e)})