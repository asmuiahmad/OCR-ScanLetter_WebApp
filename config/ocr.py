import os
import json
from flask import render_template, request, Blueprint
from flask_login import login_required
from werkzeug.utils import secure_filename
import pytesseract
from PIL import Image
from .ocr_utils import (
    clean_text,
    extract_dates,
    extract_tanggal,
    extract_penerima_surat_masuk,
    extract_penerima_surat_keluar,
    extract_pengirim,
    calculate_file_hash
)
# Define Blueprint
ocr_bp = Blueprint('ocr', __name__)

@ocr_bp.route('/ocr', methods=['GET', 'POST'])
@login_required
def ocr():
    extracted_text = ""
    if request.method == 'POST':
        if 'image' not in request.files:
            return render_template('home/ocr.html', extracted_text='No file part')
        file = request.files['image']
        if file.filename == '':
            return render_template('home/ocr.html', extracted_text='No selected file')
        if file:
            filename = secure_filename(file.filename)
            file_path = os.path.join('static/ocr/uploads', filename)
            file.save(file_path)
            try:
                extracted_text = pytesseract.image_to_string(Image.open(file_path))
                extracted_text = clean_text(extracted_text)  # Clean OCR output
            except Exception as e:
                extracted_text = f"Error during OCR processing: {e}"
    return render_template('home/ocr.html', extracted_text=extracted_text)
