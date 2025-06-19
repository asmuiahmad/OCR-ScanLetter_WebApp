import os
import json
import re
from flask import (
    render_template, request, Blueprint, url_for, flash, redirect, jsonify, send_file, session)
from flask_login import login_required
from werkzeug.utils import secure_filename
import pytesseract
from PIL import Image
import hashlib
from datetime import datetime
from config.extensions import db
from config.ocr_utils import calculate_ocr_accuracy
from config.models import SuratKeluar
from config.ocr_utils import (clean_text, extract_dates, extract_tanggal, extract_penerima_surat_keluar, extract_pengirim, calculate_file_hash, extract_isi_suratkeluar)
import io

ocr_surat_keluar_bp = Blueprint('ocr_surat_keluar', __name__)

METADATA_PATH = 'metadata.json'

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
        img = Image.open(file_path)
        custom_config = r'--oem 3 --psm 6'
        ocr_output = pytesseract.image_to_string(img, config=custom_config)
        cleaned_text = clean_text(ocr_output)

        extracted_data = {
            'nomor_surat': 'Not found',
            'pengirim': 'Not found',
            'penerima': 'Not found',
            'isi': 'Not found',
            'dates': extract_dates(cleaned_text),
            'filename': os.path.basename(file_path),
            'id_suratKeluar': None,
            'ocr_raw_text': cleaned_text
        }

        match_nomor_surat = re.search(r'(Nomor|NOMOR|Nomar)\s*:\s*(.*?)\n', cleaned_text, re.DOTALL)
        if match_nomor_surat:
            extracted_data['nomor_surat'] = match_nomor_surat.group(2).strip()

        extracted_data['pengirim'] = extract_pengirim(cleaned_text)
        extracted_data['penerima'] = extract_penerima_surat_keluar(cleaned_text)
        extracted_data['isi'] = extract_isi_suratkeluar(cleaned_text)

        return extracted_data
    except Exception as e:
        flash(f"Error during OCR processing: {e}", 'danger')
        return None

@ocr_surat_keluar_bp.route('/ocr_surat_keluar', methods=['GET', 'POST'])
@login_required
def ocr_surat_keluar():
    extracted_data_list = []
    image_paths = []
    if request.method == 'POST':
        metadata = load_metadata()
        if 'image' in request.files:
            files = request.files.getlist('image')
            if not files:
                flash('No selected files', 'warning')
                return redirect(url_for('ocr_surat_keluar.ocr_surat_keluar'))

            for file in files:
                if file.filename == '':
                    continue
                filename = secure_filename(file.filename)
                file_path = os.path.join('static/ocr/surat_keluar', filename)
                file.save(file_path)
                file_hash = calculate_file_hash(file_path)
                if metadata["surat_keluar"].get(filename) == file_hash:
                    flash(f"File '{filename}' already processed.", 'info')
                    continue
                extracted_data = extract_ocr_data(file_path)
                if extracted_data:
                    extracted_data_list.append(extracted_data)
                    metadata["surat_keluar"][filename] = file_hash
                    image_paths.append(filename)
            save_metadata(metadata)

            session['not_found_keluar'] = {
                'nomor_suratKeluar': 0,
                'pengirim_suratKeluar': 0,
                'penerima_suratKeluar': 0,
                'isi_suratKeluar': 0,
            }
            for data in extracted_data_list:
                if data.get('nomor_surat') == 'Not found':
                    session['not_found_keluar']['nomor_suratKeluar'] += 1
                if data.get('pengirim') == 'Not found':
                    session['not_found_keluar']['pengirim_suratKeluar'] += 1
                if data.get('penerima') == 'Not found':
                    session['not_found_keluar']['penerima_suratKeluar'] += 1
                if data.get('isi') == 'Not found':
                    session['not_found_keluar']['isi_suratKeluar'] += 1

            return render_template('home/ocr_surat_keluar.html',
                                   extracted_data_list=extracted_data_list,
                                   image_paths=image_paths,
                                   currentIndex=0)

        elif 'filename' in request.form:
            try:
                filename = request.form['filename']
                with open(os.path.join('static/ocr/surat_keluar', filename), 'rb') as f:
                    image_data = f.read()

                # Ambil hasil OCR mentah dari hidden inputs
                initial_nomor = request.form.get('initial_nomor_surat', 'Not found')
                initial_pengirim = request.form.get('initial_pengirim', 'Not found')
                initial_penerima = request.form.get('initial_penerima', 'Not found')
                initial_isi = request.form.get('initial_isi', 'Not found')

                edited_nomor = request.form.get('nomor_surat', initial_nomor)
                edited_pengirim = request.form.get('pengirim', initial_pengirim)
                edited_penerima = request.form.get('penerima', initial_penerima)
                edited_isi = request.form.get('isi', initial_isi)

                ocr_accuracy = (
                    calculate_ocr_accuracy(initial_nomor, edited_nomor) +
                    calculate_ocr_accuracy(initial_pengirim, edited_pengirim) +
                    calculate_ocr_accuracy(initial_penerima, edited_penerima) +
                    calculate_ocr_accuracy(initial_isi, edited_isi)
                ) / 4

                surat = SuratKeluar(
                    nomor_suratKeluar=edited_nomor,
                    pengirim_suratKeluar=edited_pengirim,
                    penerima_suratKeluar=edited_penerima,
                    isi_suratKeluar=edited_isi,
                    initial_nomor_suratKeluar=initial_nomor,
                    initial_pengirim_suratKeluar=initial_pengirim,
                    initial_penerima_suratKeluar=initial_penerima,
                    initial_isi_suratKeluar=initial_isi,
                    ocr_accuracy_suratKeluar=ocr_accuracy,
                    gambar_suratKeluar=image_data,
                    tanggal_suratKeluar=datetime.utcnow(),
                    created_at=datetime.utcnow()
                )
                db.session.add(surat)
                db.session.commit()

                flash('Data saved successfully!', 'success')
                return jsonify(success=True)
            except Exception as e:
                db.session.rollback()
                flash(f"Error saving data: {e}", 'danger')
                return jsonify(success=False, error=str(e))

    return render_template('home/ocr_surat_keluar.html',
                           extracted_data_list=extracted_data_list,
                           image_paths=image_paths,
                           currentIndex=0)

@ocr_surat_keluar_bp.route('/surat_keluar_image/<int:id>')
@login_required
def surat_keluar_image(id):
    surat = SuratKeluar.query.get_or_404(id)
    return send_file(io.BytesIO(surat.gambar_suratKeluar), mimetype='image/png')