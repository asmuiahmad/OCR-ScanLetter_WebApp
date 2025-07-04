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
from config.extensions import db
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

            match_kodesurat2 = re.search(re.escape(target_code) + r"\s*/\s*([\w.\-]+)\s*/", cleaned_text)
            if match_kodesurat2:
                extracted_data['kodesurat2'] = match_kodesurat2.group(1).strip()
                if extracted_data['kodesurat2'].startswith('HK'):
                    extracted_data['jenis_surat'] = 'Perkara'
                elif extracted_data['kodesurat2'].startswith('KP'):
                    extracted_data['jenis_surat'] = 'Kepegawaian'

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
    # Jika ini adalah permintaan AJAX untuk menyimpan data (dari modal)
    if request.method == 'POST' and 'filename' in request.form:
        try:
            # Ambil data dari form
            filename = request.form['filename']
            full_letter_number = request.form.get('full_letter_number', 'Not found')
            pengirim_suratMasuk = request.form.get('pengirim_suratMasuk', 'Not found')
            penerima_suratMasuk = request.form.get('penerima_suratMasuk', 'Not found')
            isi_suratMasuk = request.form.get('isi_suratMasuk', 'Not found')
            kodesurat2 = request.form.get('kodesurat2', 'Not found')
            jenis_surat = request.form.get('jenis_surat', 'Not found')
            selected_date = request.form.get('selected_date', '')
            
            # Ambil nilai awal untuk perhitungan akurasi
            initial_full_letter_number = request.form.get('initial_full_letter_number', 'Not found')
            initial_pengirim = request.form.get('initial_pengirim_suratMasuk', 'Not found')
            initial_penerima = request.form.get('initial_penerima_suratMasuk', 'Not found')
            initial_isi = request.form.get('initial_isi_suratMasuk', 'Not found')

            # Validasi field penting
            if not full_letter_number or full_letter_number == 'Not found':
                return jsonify(success=False, error="Nomor surat lengkap wajib diisi")
            if not pengirim_suratMasuk or pengirim_suratMasuk == 'Not found':
                return jsonify(success=False, error="Pengirim surat wajib diisi")
            if not penerima_suratMasuk or penerima_suratMasuk == 'Not found':
                return jsonify(success=False, error="Penerima surat wajib diisi")
            if not selected_date:
                return jsonify(success=False, error="Tanggal surat wajib dipilih")

            # Hitung akurasi OCR
            ocr_accuracy = (
                calculate_ocr_accuracy(initial_full_letter_number, full_letter_number) +
                calculate_ocr_accuracy(initial_pengirim, pengirim_suratMasuk) +
                calculate_ocr_accuracy(initial_penerima, penerima_suratMasuk) +
                calculate_ocr_accuracy(initial_isi, isi_suratMasuk)
            ) / 4

            # Tangani tanggal
            try:
                # Format tanggal: DD/MM/YYYY
                tanggal_surat = datetime.strptime(selected_date, '%d/%m/%Y')
            except ValueError:
                return jsonify(success=False, error="Format tanggal tidak valid. Gunakan format DD/MM/YYYY.")

            # Baca file gambar
            file_path = os.path.join(UPLOAD_FOLDER, filename)
            if not os.path.exists(file_path):
                return jsonify(success=False, error="File gambar tidak ditemukan")
            
            with open(file_path, 'rb') as f:
                gambar_suratMasuk = f.read()

            # Periksa ukuran gambar (maks 10MB)
            MAX_IMAGE_SIZE = 10 * 1024 * 1024  # 10MB
            if len(gambar_suratMasuk) > MAX_IMAGE_SIZE:
                return jsonify(success=False, error="Ukuran gambar terlalu besar (maks 10MB)")

            # Buat objek SuratMasuk
            new_surat = SuratMasuk(
                full_letter_number=full_letter_number,
                tanggal_suratMasuk=tanggal_surat,
                pengirim_suratMasuk=pengirim_suratMasuk,
                penerima_suratMasuk=penerima_suratMasuk,
                kode_suratMasuk=kodesurat2,
                jenis_suratMasuk=jenis_surat,
                isi_suratMasuk=isi_suratMasuk,
                gambar_suratMasuk=gambar_suratMasuk,
                created_at=datetime.utcnow(),
                
                # Simpan hasil OCR mentah
                initial_full_letter_number=initial_full_letter_number,
                initial_pengirim_suratMasuk=initial_pengirim,
                initial_penerima_suratMasuk=initial_penerima,
                initial_isi_suratMasuk=initial_isi,
                ocr_accuracy_suratMasuk=ocr_accuracy
            )

            db.session.add(new_surat)
            db.session.commit()

            return jsonify(success=True)
            
        except SQLAlchemyError as e:
            db.session.rollback()
            logger.error(f"Database error: {str(e)}\n{traceback.format_exc()}")
            return jsonify(success=False, error="Gagal menyimpan ke database: " + str(e))
        except Exception as e:
            logger.error(f"Error saving data: {str(e)}\n{traceback.format_exc()}")
            return jsonify(success=False, error="Kesalahan server: " + str(e))
    
    # Jika ini adalah permintaan upload gambar
    elif request.method == 'POST':
        extracted_data_list = []
        image_paths = []
        metadata = load_metadata()
        
        # Tangani kasus tidak ada file yang dipilih
        if 'image' not in request.files:
            flash('Tidak ada file yang dipilih', 'warning')
            return redirect(url_for('ocr_surat_masuk.ocr_surat_masuk'))
            
        files = request.files.getlist('image')
        if not files or all(file.filename == '' for file in files):
            flash('Tidak ada file yang dipilih', 'warning')
            return redirect(url_for('ocr_surat_masuk.ocr_surat_masuk'))

        processed_files = 0
        not_found_counts = {
            'full_letter_number': 0,
            'pengirim_suratMasuk': 0,
            'penerima_suratMasuk': 0,
            'isi_suratMasuk': 0,
        }
        
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
                if filename in metadata.get("surat_masuk", {}) and metadata["surat_masuk"][filename] == file_hash:
                    flash(f"File '{filename}' sudah diproses sebelumnya.", 'info')
                    continue
                    
                extracted_data = extract_ocr_data(file_path)
                if extracted_data:
                    # Hitung field yang tidak ditemukan
                    if extracted_data['full_letter_number'] == 'Not found':
                        not_found_counts['full_letter_number'] += 1
                    if extracted_data['pengirim_suratMasuk'] == 'Not found':
                        not_found_counts['pengirim_suratMasuk'] += 1
                    if extracted_data['penerima_suratMasuk'] == 'Not found':
                        not_found_counts['penerima_suratMasuk'] += 1
                    if extracted_data['isi_suratMasuk'] == 'Not found':
                        not_found_counts['isi_suratMasuk'] += 1
                    
                    extracted_data_list.append(extracted_data)
                    metadata.setdefault("surat_masuk", {})[filename] = file_hash
                    image_paths.append(filename)
                    processed_files += 1
            except Exception as e:
                logger.error(f"Error processing file {filename}: {str(e)}\n{traceback.format_exc()}")
                flash(f"Error processing file {filename}: {e}", 'danger')

        save_metadata(metadata)
        
        if processed_files == 0:
            flash("Tidak ada file baru yang diproses", 'info')
        else:
            session['not_found_masuk'] = not_found_counts
            flash(f"Berhasil memproses {processed_files} file", 'success')

        return render_template('home/ocr_surat_masuk.html',
                               extracted_data_list=extracted_data_list,
                               image_paths=image_paths,
                               currentIndex=0)

    # GET request
    return render_template('home/ocr_surat_masuk.html',
                           extracted_data_list=[],
                           image_paths=[],
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