import os
import json
import re
from flask import (
    render_template, request, Blueprint, url_for, flash, redirect, jsonify, send_file, session
)
from flask_login import login_required
from werkzeug.utils import secure_filename
import pytesseract
from PIL import Image
import hashlib
from datetime import datetime
from config.extensions import db
from config.ocr_utils import calculate_ocr_accuracy
from config.models import SuratKeluar
from config.ocr_utils import (
    clean_text,
    extract_dates,
    extract_tanggal,
    extract_penerima_surat_keluar,
    extract_pengirim,
    calculate_file_hash,
    extract_isi
)
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
        ocr_output = pytesseract.image_to_string(img)
        cleaned_text = clean_text(ocr_output)

        extracted_data = {
            'nomor_surat': 'Not found',
            'pengirim': 'Not found',
            'penerima': 'Not found',
            'isi': 'Not found',
            'dates': extract_dates(cleaned_text),
            'filename': os.path.basename(file_path),
            'id_suratKeluar': None
        }

        # Nomor Surat
        match_nomor_surat = re.search(r'(Nomor|NOMOR|Nomar)\s*:\s*(.*?)\n', cleaned_text, re.DOTALL)
        if match_nomor_surat:
            extracted_data['nomor_surat'] = match_nomor_surat.group(2).strip()

        # Field extraction
        extracted_data['pengirim'] = extract_pengirim(cleaned_text)
        extracted_data['penerima'] = extract_penerima_surat_keluar(cleaned_text)
        extracted_data['isi'] = extract_isi(cleaned_text)

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

            # ✅ Tambahan: Hitung statistik "Not found" sebelum tampil
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
                with open(os.path.join('static/ocr/surat_keluar', request.form['filename']), 'rb') as f:
                    gambar_suratKeluar = f.read()

                initial_nomor = request.form.get('nomor_surat', 'Not found')
                initial_pengirim = request.form.get('pengirim', 'Not found')
                initial_penerima = request.form.get('penerima', 'Not found')
                initial_isi = request.form.get('isi', 'Not found')

                new_surat = SuratKeluar(
                    tanggal_suratKeluar=datetime.strptime(request.form['selected_date'], '%d/%m/%Y'),
                    pengirim_suratKeluar=initial_pengirim,
                    penerima_suratKeluar=initial_penerima,
                    nomor_suratKeluar=initial_nomor,
                    isi_suratKeluar=initial_isi,
                    initial_nomor_suratKeluar=initial_nomor,
                    initial_pengirim_suratKeluar=initial_pengirim,
                    initial_penerima_suratKeluar=initial_penerima,
                    initial_isi_suratKeluar=initial_isi,
                    gambar_suratKeluar=gambar_suratKeluar,
                    created_at=datetime.utcnow()
                )
                db.session.add(new_surat)
                db.session.commit()

                flash('Data saved successfully!', 'success')

                for data in extracted_data_list:
                    if data['filename'] == request.form['filename']:
                        data['id_suratKeluar'] = new_surat.id_suratKeluar
                        break

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
