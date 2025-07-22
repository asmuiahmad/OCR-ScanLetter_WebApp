"""
OCR routes
OCR testing and processing functionality
"""

import os
import tempfile

import pytesseract
from flask import Blueprint, render_template, request, flash, current_app, send_from_directory
from flask_login import login_required
from werkzeug.utils import secure_filename

ocr_routes_bp = Blueprint('ocr_routes', __name__)


@ocr_routes_bp.route('/ocr-test', methods=['GET', 'POST'])
@login_required
def ocr_test():
    """OCR test functionality"""
    extracted_text = ""
    
    if request.method == 'POST':
        try:
            if 'file' not in request.files:
                flash('No file selected', 'error')
                return render_template('ocr/ocr_test.html', extracted_text=extracted_text, has_error=True, has_success=False)
            
            file = request.files['file']
            if file.filename == '':
                flash('No file selected', 'error')
                return render_template('ocr/ocr_test.html', extracted_text=extracted_text, has_error=True, has_success=False)
            
            if file and file.filename.lower().endswith(('.png', '.jpg', '.jpeg', '.gif', '.bmp', '.tiff')):
                try:
                    # Save uploaded file temporarily
                    filename = secure_filename(file.filename)
                    temp_path = os.path.join(tempfile.gettempdir(), filename)
                    file.save(temp_path)
                    
                    # Perform OCR
                    extracted_text = pytesseract.image_to_string(temp_path, lang='ind+eng')
                    
                    # Clean up
                    os.remove(temp_path)
                    
                    if extracted_text.strip():
                        flash('OCR extraction successful!', 'success')
                        return render_template('ocr/ocr_test.html', extracted_text=extracted_text, has_error=False, has_success=True)
                    else:
                        flash('No text could be extracted from the image', 'warning')
                        return render_template('ocr/ocr_test.html', extracted_text="No text found", has_error=False, has_success=False)
                        
                except Exception as ocr_error:
                    current_app.logger.error(f"OCR processing error: {str(ocr_error)}")
                    flash(f'Error processing image: {str(ocr_error)}', 'error')
                    return render_template('ocr/ocr_test.html', extracted_text=extracted_text, has_error=True, has_success=False)
            else:
                flash('Please upload a valid image file (PNG, JPG, JPEG, GIF, BMP, TIFF)', 'error')
                return render_template('ocr/ocr_test.html', extracted_text=extracted_text, has_error=True, has_success=False)
                
        except Exception as e:
            current_app.logger.error(f"OCR test error: {str(e)}")
            flash(f'An error occurred: {str(e)}', 'error')
            return render_template('ocr/ocr_test.html', extracted_text=extracted_text, has_error=True, has_success=False)
    
    return render_template('ocr/ocr_test.html', extracted_text=extracted_text, has_error=False, has_success=False)


@ocr_routes_bp.route('/favicon.ico')
def favicon():
    """Serve favicon"""
    return send_from_directory(
        os.path.join(current_app.root_path, 'static'),
        'favicon.ico',
        mimetype='image/vnd.microsoft.icon'
    )