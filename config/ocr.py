import os
from flask import render_template, request, Blueprint
from flask_login import login_required
from werkzeug.utils import secure_filename
import pytesseract
from PIL import Image
import re

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
            file_path = os.path.join('static/uploads', filename)
            file.save(file_path)
            try:
                extracted_text = pytesseract.image_to_string(file_path)
            except Exception as e:
                extracted_text = f"Error during OCR processing: {e}"
    return render_template('home/ocr.html', extracted_text=extracted_text)


@ocr_bp.route('/ocr2', methods=['GET', 'POST'])
@login_required
def ocr2():
    extracted_text = ""
    image_paths = []
    extracted_data_list = []

    # Regular expression to capture relevant fields
    pattern = r"(\d+)\/([A-Za-z0-9\-]+)\.([A-Za-z0-9\-]+)\/([A-Za-z0-9\-\.]+)\/([A-Za-z0-9]+)\/(\d{4})"
    
    if request.method == 'POST':
        if 'image' not in request.files:
            return render_template('home/ocr2.html', extracted_text='No file part')
        
        files = request.files.getlist('image')
        
        if not files:
            return render_template('home/ocr2.html', extracted_text='No selected files')
        
        for file in files:
            if file.filename == '':
                continue
                
            filename = secure_filename(file.filename)
            file_path = os.path.join('static/uploads', filename)
            file.save(file_path)
            image_paths.append(file_path)

            try:
                img = Image.open(file_path)
                extracted_text_image = pytesseract.image_to_string(img)

                print("OCR Output:", extracted_text_image)

                match = re.search(pattern, extracted_text_image)
                extracted_data = {}

                if match:
                    extracted_data['nomorsurat'] = match.group(1)
                    extracted_data['kodesurat1'] = match.group(2)
                    extracted_data['kodePA'] = match.group(3)
                    extracted_data['kodesurat2'] = match.group(4)
                    extracted_data['bulan'] = match.group(5)
                    extracted_data['tahun'] = match.group(6)
                else:
                    extracted_data['nomorsurat'] = 'Not found'
                    extracted_data['kodesurat1'] = 'Not found'
                    extracted_data['kodePA'] = 'Not found'
                    extracted_data['kodesurat2'] = 'Not found'
                    extracted_data['bulan'] = 'Not found'
                    extracted_data['tahun'] = 'Not found'

                extracted_data_list.append(extracted_data)

            except Exception as e:
                extracted_text = f"Error during OCR processing: {e}"

    return render_template('home/ocr2.html', extracted_text=extracted_text, image_paths=image_paths, extracted_data_list=extracted_data_list)

def ocr_routes(app):
    app.register_blueprint(ocr_bp)
