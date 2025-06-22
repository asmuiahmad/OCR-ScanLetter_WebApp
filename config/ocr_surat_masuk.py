import os
import re
import json
from flask import (render_template, request, Blueprint, url_for, flash, redirect, jsonify, send_file, send_from_directory, session)
from flask_login import login_required
from werkzeug.utils import secure_filename
import pytesseract
from PIL import Image
import hashlib
from datetime import datetime
from config.extensions import db
from config.models import SuratMasuk
from config.ocr_utils import calculate_ocr_accuracy
from config.ocr_utils import (clean_text, extract_dates, extract_tanggal, extract_penerima_surat_masuk, extract_pengirim, calculate_file_hash,extract_isi_suratmasuk)
import io
from sqlalchemy import func, extract
from datetime import date, timedelta

ocr_surat_masuk_bp = Blueprint('ocr_surat_masuk', __name__)

target_code = "W15-A12"
METADATA_PATH = 'metadata.json'

def save_metadata(metadata):
    with open(METADATA_PATH, 'w') as f:
        json.dump(metadata, f, indent=4)

def load_metadata():
    if os.path.exists(METADATA_PATH):
        with open(METADATA_PATH, 'r') as f:
            metadata = json.load(f)
        if "surat_masuk" not in metadata:
            metadata["surat_masuk"] = {}
        return metadata
    else:
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
            'isi': extract_isi_suratmasuk(cleaned_text),
            'filename': os.path.basename(file_path),
            'id_suratMasuk': None
        }

        cleaned_text = re.sub(r"W\s*1\s*5\s*[-\s]*A\s*1\s*2", target_code, cleaned_text, flags=re.IGNORECASE)

        pattern_full = rf"(\d+)[/\s-]+([\w.\-]+)[/\s.-]+{re.escape(target_code)}[/\s-]+([\w.\-]+)[/\s-]+([A-ZIX0-9]{{1,4}})[/\s-]+(\d{{4}})"
        match = re.search(pattern_full, cleaned_text, re.IGNORECASE)

        if match:
            extracted_data['nomor_surat'] = match.group(1).strip()
            extracted_data['kodesurat1'] = match.group(2).strip()
            extracted_data['kodePA'] = target_code
            extracted_data['kodesurat2'] = match.group(3).strip()
            extracted_data['bulan'] = match.group(4).strip().replace('1', 'I')
            extracted_data['bulan_display'] = extracted_data['bulan']
            extracted_data['tahun'] = match.group(5).strip()

            # Tentukan jenis surat berdasarkan awalan kode surat 2
            if extracted_data['kodesurat2'].startswith('HK'):
                extracted_data['jenis_surat'] = 'Perkara'
            elif extracted_data['kodesurat2'].startswith('KP'):
                extracted_data['jenis_surat'] = 'Kepegawaian'
        else:
            # ⛔ Jika gagal match dengan regex utama, fallback manual
            if target_code in cleaned_text:
                extracted_data['kodePA'] = target_code

            match_nomor = re.search(r"(\d+)(?=\s*/)", cleaned_text)
            if match_nomor:
                extracted_data['nomor_surat'] = match_nomor.group(1)

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
                extracted_data['bulan_display'] = extracted_data['bulan']

            match_tahun = re.search(r"/\s*" + re.escape(extracted_data['bulan']) + r"\s*/\s*(\d{4})", cleaned_text)
            if match_tahun:
                extracted_data['tahun'] = match_tahun.group(1)

        # ✅ Bangun full_letter_number dari hasil ekstraksi
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
                    not_found_counts_masuk = {
                        'nomor_suratMasuk': 1 if re.search(r'\bNot\s*found\b', extracted_data.get('nomor_surat', ''), re.IGNORECASE) else 0,
                        'pengirim_suratMasuk': 1 if extracted_data.get('pengirim') == "Not found" else 0,
                        'penerima_suratMasuk': 1 if extracted_data.get('penerima') == "Not found" else 0,
                        'isi_suratMasuk': 1 if extracted_data.get('isi') == "Not found" else 0
                    }
                    session['not_found_masuk'] = not_found_counts_masuk

                    extracted_data_list.append(extracted_data)
                    metadata['surat_masuk'][filename] = file_hash
                    image_paths.append(filename)
            save_metadata(metadata)
            return render_template('home/ocr_surat_masuk.html', 
                                extracted_data_list=extracted_data_list,
                                image_paths=image_paths,
                                currentIndex=0,
                                field_stats_masuk=session.get('not_found_masuk'))
        elif 'filename' in request.form:
            try:
                initial_nomor = request.form.get('initial_nomor_suratMasuk', 'Not found')
                initial_pengirim = request.form.get('initial_pengirim_suratMasuk', 'Not found')
                initial_penerima = request.form.get('initial_penerima_suratMasuk', 'Not found')
                initial_isi = request.form.get('initial_isi_suratMasuk', 'Not found')
                edited_nomor = request.form.get("full_letter_number", "Not found")
                edited_pengirim = request.form.get('pengirim', initial_pengirim)
                edited_penerima = request.form.get('penerima', initial_penerima)
                edited_isi = request.form.get('isi', initial_isi)

                ocr_accuracy = (
                    calculate_ocr_accuracy(initial_nomor, edited_nomor) +
                    calculate_ocr_accuracy(initial_pengirim, edited_pengirim) +
                    calculate_ocr_accuracy(initial_penerima, edited_penerima) +
                    calculate_ocr_accuracy(initial_isi, edited_isi)
                ) / 4

                try:
                    tanggal_surat = datetime.strptime(request.form.get('selected_date', ''), '%d/%m/%Y')
                except ValueError:
                    return jsonify(success=False, error="Invalid date format.")

                with open(os.path.join('static/ocr/surat_masuk', request.form['filename']), 'rb') as f:
                    gambar_suratMasuk = f.read()

                new_surat = SuratMasuk(
                    tanggal_suratMasuk=datetime.utcnow(),
                    nomor_suratMasuk=edited_nomor,
                    pengirim_suratMasuk=edited_pengirim,
                    penerima_suratMasuk=edited_penerima,
                    kode_suratMasuk=request.form.get('kodesurat2', 'Not found'),
                    jenis_suratMasuk=request.form.get('jenis_surat', 'Not found'),
                    isi_suratMasuk=edited_isi,
                    gambar_suratMasuk=gambar_suratMasuk,
                    created_at=datetime.utcnow(),
                    initial_nomor_suratMasuk=initial_nomor,
                    initial_pengirim_suratMasuk=initial_pengirim,
                    initial_penerima_suratMasuk=initial_penerima,
                    initial_isi_suratMasuk=initial_isi,
                    ocr_accuracy_suratMasuk=ocr_accuracy
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

    return render_template('home/ocr_surat_masuk.html',         
                        extracted_data_list=extracted_data_list, 
                        image_paths=image_paths, 
                        currentIndex=0,
                        field_stats_masuk=session.get('not_found_masuk')
                        )

@ocr_surat_masuk_bp.route('/surat_masuk_image/<int:id>')
@login_required
def surat_masuk_image(id):
    surat = SuratMasuk.query.get_or_404(id)
    return send_file(io.BytesIO(surat.gambar_suratMasuk), mimetype='image/png')

@ocr_surat_masuk_bp.route('/static/ocr/surat_masuk/<filename>')
@login_required
def uploaded_file_surat_masuk(filename):
    return send_from_directory('static/ocr/surat_masuk', filename)
