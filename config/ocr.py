import os
import json
from flask import render_template, request, Blueprint, url_for, flash, redirect
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename
import pytesseract
from PIL import Image
from functools import wraps
from .ocr_utils import (
    clean_text,
    extract_dates,
    extract_tanggal,
    extract_penerima_surat_keluar,
    extract_penerima_surat_masuk,
    extract_pengirim,
    calculate_file_hash
)
from config.ocr_surat_keluar import extract_ocr_data as extract_ocr_data_surat_keluar
from config.ocr_surat_masuk import extract_ocr_data_surat_masuk
from config.route_utils import role_required  # Import from route_utils

ocr_bp = Blueprint('ocr', __name__)

@ocr_bp.route('/ocr', methods=['GET', 'POST'])
@login_required
@role_required('admin', 'pimpinan')
def ocr():
    extracted_text = ""
    if request.method == 'POST':
        if 'image' not in request.files:
            return render_template('ocr/ocr.html', extracted_text='No file part')
        file = request.files['image']
        if file.filename == '':
            return render_template('ocr/ocr.html', extracted_text='No selected file')
        if file:
            filename = secure_filename(file.filename)
            file_path = os.path.join('static/ocr/uploads', filename)
            file.save(file_path)
            try:
                extracted_text = pytesseract.image_to_string(Image.open(file_path))
                extracted_text = clean_text(extracted_text)  # Clean OCR output
            except Exception as e:
                extracted_text = f"Error during OCR processing: {e}"
    return render_template('ocr/ocr.html', extracted_text=extracted_text)

def process_ocr_surat_keluar(file_path):
    """
    Process OCR for incoming letter (surat masuk)
    Returns structured data from OCR
    """
    return extract_ocr_data_surat_keluar(file_path)

def process_ocr_surat_masuk(file_path):
    """
    Process OCR for outgoing letter (surat keluar)
    Returns structured data from OCR
    """
    return extract_ocr_data_surat_masuk(file_path)
