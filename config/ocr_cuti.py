import os
import re
import logging
import tempfile
from flask import Blueprint, render_template, request, flash, redirect, url_for, jsonify
from werkzeug.utils import secure_filename
from flask_login import login_required, current_user
from config.extensions import db
from config.models import SuratKeluar, Cuti
from datetime import datetime
import random
import string

# Import untuk PDF processing
try:
    import pdf2image
    PDF_SUPPORT = True
except ImportError:
    PDF_SUPPORT = False
    logging.warning("pdf2image not installed. PDF processing will be disabled.")

ocr_cuti_bp = Blueprint('ocr_cuti', __name__, template_folder='../templates/home')

UPLOAD_FOLDER = 'static/ocr/cuti'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

def extract_text_from_pdf(pdf_file):
    """
    Extract text from PDF file using OCR
    """
    if not PDF_SUPPORT:
        return None
    
    try:
        # Simpan file PDF sementara
        with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as tmp_pdf:
            pdf_file.save(tmp_pdf)
            tmp_pdf_path = tmp_pdf.name
        
        # Konversi PDF ke gambar
        images = pdf2image.convert_from_path(tmp_pdf_path)
        
        # Ekstrak teks dari setiap halaman
        full_text = ""
        for i, image in enumerate(images):
            import pytesseract
            page_text = pytesseract.image_to_string(image, lang='ind')
            full_text += page_text
            if len(images) > 1:
                full_text += f"\n\n--- PAGE {i+1} ---\n\n"
        
        # Hapus file sementara
        os.unlink(tmp_pdf_path)
        return full_text
    except Exception as e:
        logging.error(f"Error processing PDF: {str(e)}")
        return None

def extract_cuti_fields(text):
    print("=== DEBUG OCR CUTI ===")
    print(f"Raw OCR text: {text[:500]}...")  # Print first 500 chars
    
    # Pola yang lebih baik untuk mencocokkan format PDF
    nomor_patterns = [
        # Pattern untuk format: 1931/PAN.PA.W15-A12/HM2.1.4/X/2024 (preserve original structure)
        r'(?:Nomor|No|Nomer|NOMOR|Nomnor)\s*[:.\-]?\s*(\d+)[/\s-]+([A-Za-z.]+)\.?(?:W15-A12|W15[-\s]*A12)[/\s-]+([A-Z0-9.]+)[/\s-]+(\d{0,1}[XIVxvi]+)[/\s-]+(\d{4})',
        # Pattern untuk format: 1931/PAN.PA.W15-A12/HK.2.6/X/2024 (preserve original structure)
        r'(?:Nomor|No|Nomer|NOMOR|Nomnor)\s*[:.\-]?\s*(\d+)[/\s-]+([A-Za-z.]+)\.?(?:W15-A12|W15[-\s]*A12)[/\s-]+([A-Z0-9.]+)[/\s-]+(\d{0,1}[XIVxvi]+)[/\s-]+(\d{4})',
        # More flexible patterns that preserve original structure
        r'(?:Nomor|No|Nomer|NOMOR|Nomnor)\s*[:.\-]?\s*(\d+).*?(?:W15-A12|W15[-\s]*A12).*?([A-Z0-9.]+).*?([IVX]+).*?(\d{4})',
        r'(?:Nomor|No|Nomer|NOMOR|Nomnor)\s*[:.\-]?\s*(\d+).*?(?:W15|W.*?15).*?([A-Z0-9.]+).*?([IVX0-9]+).*?(\d{4})',
        # Pattern untuk menangani format dengan karakter khusus dan spasi
        r'(?:Nomor|No|Nomer|NOMOR|Nomnor)\s*[:.\-]?\s*\(?(\d+)\s*[/\s-]+\s*([A-Za-z.]+)\s*\.?\s*(?:W15-A12|W15[-\s]*A12)\s*[/\s-]+\s*([A-Z0-9.]+)\s*[/\s-]+\s*([IVX]+)\s*[/\s-]+\s*(\d{4})\)?',
        # Pattern yang lebih fleksibel untuk format yang tidak standar
        r'(?:Nomor|No|Nomer|NOMOR|Nomnor)\s*[:.\-]?\s*\(?(\d+)\s*[/\s-]+\s*([A-Za-z.]+)\s*\.?\s*(?:W15[-\s]*A12)\s*[/\s-]+\s*([A-Z0-9.]+)\s*[/\s-]+\s*([IVX]+)\s*[/\s-]+\s*(\d{4})\)?',
        # Pola alternatif untuk format yang berbeda
        r'(\d{4})\s*[/-]\s*(\w+)\s*[/-]\s*(\w+)\s*[/-]\s*(\w+)\s*[/-]\s*(\d{4})',
        r'NOMOR\s*:\s*(\d+)\s*[/-]\s*(\w+)[.\s]*W15-A12\s*[/-]\s*(\w+[.\d]+)\s*[/-]\s*([IVX]+)\s*[/-]\s*(\d{4})'
    ]

    nomor_surat = 'Not found'
    kodesurat1 = 'Not found'
    kodePA = 'Not found'
    kodesurat2 = 'Not found'
    bulan = 'Not found'
    tahun = 'Not found'
    full_letter_number = 'Not found'

    # Try to match with the patterns
    for i, pattern in enumerate(nomor_patterns):
        print(f"Trying pattern {i}: {pattern}")
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            print(f"Pattern {i} matched: {match.groups()}")
            if len(match.groups()) >= 5:  # Complete pattern
                nomor_surat = match.group(1)
                kodesurat1 = match.group(2)  # Preserve original like "PAN.PA"
                kodePA = 'W15-A12'  # Standard code
                kodesurat2 = match.group(3)  # Preserve original like "HK.2.6"
                bulan = match.group(4).upper().replace('1X', 'IX')
                tahun = match.group(5)
            elif len(match.groups()) == 4:  # Flexible pattern
                nomor_surat = match.group(1)
                kodesurat1 = 'PAN.PA'  # Default to original structure
                kodePA = 'W15-A12'  # Standard code
                kodesurat2 = match.group(2)
                bulan = match.group(3)
                tahun = match.group(4)
            
            # Construct the full letter number preserving original structure
            full_letter_number = f"{nomor_surat}/{kodesurat1.rstrip('.')}.{kodePA}/{kodesurat2}/{bulan}/{tahun}"
            print(f"Full letter number: {full_letter_number}")
            break
        else:
            print(f"Pattern {i} did not match")

    # Jika tidak ada match, coba pattern yang lebih sederhana
    if full_letter_number == 'Not found':
        print("Trying simpler patterns...")
        # Coba cari hanya nomor setelah Nomnor
        simple_match = re.search(r'Nomnor\s*[:.\-]?\s*([^/\n]+)', text, re.IGNORECASE)
        if simple_match:
            print(f"Simple match found: {simple_match.group(1)}")
            full_letter_number = simple_match.group(1).strip()
        else:
            print("No simple match found either")

    print(f"Final nomor_surat: {full_letter_number}")

    # Nama (setelah kata NAMA atau di baris dengan NIP)
    nama = None
    nama_match = re.search(r'NAMA\s*[:：]?\s*([A-Za-z .,-]+)', text, re.IGNORECASE)
    if not nama_match:
        # Coba cari baris sebelum NIP
        nip_match = re.search(r'NIP[.:\s]*([\d ]+)', text)
        if nip_match:
            before_nip = text[:nip_match.start()]
            lines = before_nip.strip().split('\n')
            if lines:
                nama = lines[-1].strip()
    else:
        nama = nama_match.group(1).strip()

    # NIP (ambil semua NIP yang ditemukan) - perbaikan untuk format dengan/tanpa spasi
    nips = re.findall(r'NIP[.:\s]*([\d\s]{10,})', text)
    nip = nips[0].replace(' ', '') if nips else None

    # Jenis cuti (cari baris "JENIS CUTI YANG DIAMBIL" atau daftar cuti dengan centang)
    jenis_cuti = None
    jenis_match = re.search(r'JENIS CUTI YANG DIAMBIL[""]*\s*([A-Za-z .,-]+)', text, re.IGNORECASE)
    if jenis_match:
        jenis_cuti = jenis_match.group(1).strip()
    else:
        # Coba cari baris yang mengandung kata CUTI dan centang (V/✓/✔)
        jenis_match2 = re.search(r'(CUTI [A-Z ]+)[^\n]*[V✓✔]', text)
        if jenis_match2:
            jenis_cuti = jenis_match2.group(1).strip()
        else:
            # Coba cari jenis cuti dengan pola yang lebih fleksibel
            cuti_types = ['Cuti Tahunan', 'Cuti Sakit', 'Cuti Melahirkan', 'Cuti Besar', 'Cuti Alasan Penting']
            for cuti_type in cuti_types:
                if cuti_type.lower() in text.lower():
                    jenis_cuti = cuti_type
                    break

    # Tanggal cuti (cari pola tanggal setelah kata Tanggal)
    tanggal_cuti = None
    tanggal_match = re.search(r'Tanggal\s*[:：]?\s*([\d]{1,2}\s*[A-Za-z]+\s*[\d]{4})', text)
    if tanggal_match:
        tanggal_cuti = tanggal_match.group(1).strip()
    else:
        # Coba cari tanggal lain
        tanggal_match2 = re.search(r'(\d{1,2}\s*[A-Za-z]+\s*\d{4})', text)
        if tanggal_match2:
            tanggal_cuti = tanggal_match2.group(1).strip()

    # Alamat selama cuti (setelah kata ALAMAT)
    alamat = None
    alamat_match = re.search(r'ALAMAT[\s\S]{0,50}?([A-Za-z0-9, .\-\n]+)', text, re.IGNORECASE)
    if alamat_match:
        alamat = alamat_match.group(1).strip().split('\n')[0]

    # Data tambahan khusus cuti
    jabatan = re.search(r'JABATAN\s*[:：]?\s*([A-Za-z .,-]+)', text, re.IGNORECASE)
    gol_ruang = re.search(r'GOL\.\s*RUANG\s*[:：]?\s*([A-Za-z0-9 .,-]+)', text, re.IGNORECASE)
    unit_kerja = re.search(r'UNIT\s*KERJA\s*[:：]?\s*([A-Za-z .,-]+)', text, re.IGNORECASE)
    masa_kerja = re.search(r'MASA\s*KERJA\s*[:：]?\s*([A-Za-z0-9 .,-]+)', text, re.IGNORECASE)
    alasan_cuti = re.search(r'ALASAN\s*CUTI\s*[:：]?\s*([A-Za-z .,-]+)', text, re.IGNORECASE)
    lama_cuti = re.search(r'SELAMA\s*[:：]?\s*([A-Za-z0-9 .,-]+)', text, re.IGNORECASE)
    telp = re.search(r'TELP\.\s*[:：]?\s*([A-Za-z0-9 .,-]+)', text, re.IGNORECASE)

    # Tanggal periode cuti
    tanggal_periode = None
    tgl_match = re.search(r'TANGGAL\s*[:：]?\s*([\d-]+)\s*SAMPAI\s*([\d-]+)', text)
    if tgl_match:
        tanggal_periode = f"{tgl_match.group(1)} sampai {tgl_match.group(2)}"

    return {
        'nomor_surat': full_letter_number,
        'nama': nama,
        'nip': nip,
        'jenis_cuti': jenis_cuti,
        'tanggal_cuti': tanggal_periode or tanggal_cuti,
        'alamat': alamat,
        'jenis_surat': 'Cuti',
        'pengirim': nama,
        'penerima': 'Ketua Pengadilan Agama',
        'isi': f"Surat Permintaan Cuti oleh {nama or 'N/A'} (NIP: {nip or 'N/A'}) - {jenis_cuti or 'N/A'}",
        
        # Data tambahan khusus cuti
        'jabatan': jabatan.group(1).strip() if jabatan else 'Tidak terbaca',
        'gol_ruang': gol_ruang.group(1).strip() if gol_ruang else 'Tidak terbaca',
        'unit_kerja': unit_kerja.group(1).strip() if unit_kerja else 'Tidak terbaca',
        'masa_kerja': masa_kerja.group(1).strip() if masa_kerja else 'Tidak terbaca',
        'alasan_cuti': alasan_cuti.group(1).strip() if alasan_cuti else 'Tidak terbaca',
        'lama_cuti': lama_cuti.group(1).strip() if lama_cuti else 'Tidak terbaca',
        'telp': telp.group(1).strip() if telp else 'Tidak terbaca'
    }

@ocr_cuti_bp.route('/', methods=['GET', 'POST'])
@login_required
def ocr_cuti():
    if request.method == 'GET':
        return render_template('cuti/ocr_cuti.html')
    
    # Handle POST request for OCR processing
    if 'image' not in request.files:
        flash('Tidak ada file yang diunggah.', 'error')
        return render_template('cuti/ocr_cuti.html')

    files = request.files.getlist('image')
    if not files or files[0].filename == '':
        flash('Tidak ada file yang dipilih.', 'error')
        return render_template('cuti/ocr_cuti.html')

    extracted_data_list = []
    
    for file in files:
        if file.filename == '':
            continue
            
        # Check file type - tambahkan dukungan PDF
        allowed_extensions = {'png', 'jpg', 'jpeg', 'webp', 'pdf'}
        if not file.filename or '.' not in file.filename or file.filename.rsplit('.', 1)[1].lower() not in allowed_extensions:
            flash(f'Format file {file.filename} tidak didukung. Gunakan PNG, JPG, JPEG, WEBP, atau PDF.', 'error')
            continue

        try:
            extracted_text = ""
            file_ext = file.filename.rsplit('.', 1)[1].lower()
            
            if file_ext == 'pdf':
                # Proses file PDF
                if not PDF_SUPPORT:
                    flash(f'Dukungan PDF tidak tersedia. Install pdf2image: pip install pdf2image', 'error')
                    continue
                
                extracted_text = extract_text_from_pdf(file)
                if not extracted_text:
                    flash(f'Gagal memproses PDF: {file.filename}', 'error')
                    continue
            else:
                # Proses file gambar seperti biasa
                from PIL import Image
                import pytesseract
                
                # Convert file to image using PIL
                image = Image.open(file.stream)
                
                # Extract text using pytesseract
                extracted_text = pytesseract.image_to_string(image, lang='ind')
            
            if not extracted_text.strip():
                flash(f'Tidak ada teks yang dapat diekstrak dari {file.filename}.', 'error')
                continue
            
            # Extract specific fields for cuti form
            extracted_data = extract_cuti_fields(extracted_text)
            extracted_data['filename'] = file.filename
            extracted_data_list.append(extracted_data)
            
        except Exception as e:
            flash(f'Error saat memproses {file.filename}: {str(e)}', 'error')
            continue
    
    if extracted_data_list:
        flash(f'{len(extracted_data_list)} dokumen berhasil diproses.', 'success')
    
    return render_template('cuti/ocr_cuti.html', extracted_data_list=extracted_data_list) 

@ocr_cuti_bp.route('/list', methods=['GET'])
@login_required
def list_cuti():
    """Menampilkan daftar data cuti yang tersimpan di database"""
    try:
        # Ambil data cuti dari database
        cuti_list = Cuti.query.order_by(Cuti.created_at.desc()).all()
        return render_template('cuti/list_cuti.html', cuti_list=cuti_list)
    except Exception as e:
        flash(f'Error saat mengambil data cuti: {str(e)}', 'error')
        return render_template('cuti/list_cuti.html', cuti_list=[])

@ocr_cuti_bp.route('/detail/<int:cuti_id>', methods=['GET'])
@login_required
def detail_cuti(cuti_id):
    """API endpoint untuk mendapatkan detail cuti"""
    try:
        cuti = Cuti.query.get_or_404(cuti_id)
        
        cuti_data = {
            'id_cuti': cuti.id_cuti,
            'nama': cuti.nama,
            'nip': cuti.nip,
            'jabatan': cuti.jabatan,
            'gol_ruang': cuti.gol_ruang,
            'unit_kerja': cuti.unit_kerja,
            'masa_kerja': cuti.masa_kerja,
            'alamat': cuti.alamat,
            'telp': cuti.telp,
            'jenis_cuti': cuti.jenis_cuti,
            'alasan_cuti': cuti.alasan_cuti,
            'lama_cuti': cuti.lama_cuti,
            'tanggal_cuti': cuti.tanggal_cuti.strftime('%d/%m/%Y'),
            'sampai_cuti': cuti.sampai_cuti.strftime('%d/%m/%Y'),
            'tgl_ajuan_cuti': cuti.tgl_ajuan_cuti.strftime('%d/%m/%Y'),
            'status_cuti': cuti.status_cuti,
            'approved_by': cuti.approved_by,
            'approved_at': cuti.approved_at.strftime('%d/%m/%Y %H:%M:%S') if cuti.approved_at else None,
            'notes': cuti.notes,
            'qr_code': cuti.qr_code,
            'pdf_path': cuti.pdf_path
        }
        
        return jsonify({
            'success': True,
            'cuti': cuti_data
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Error: {str(e)}'
        }), 500

@ocr_cuti_bp.route('/approve/<int:cuti_id>', methods=['POST'])
@login_required
def approve_cuti(cuti_id):
    """Approve cuti dan generate digital signature dengan QR code"""
    try:
        # Cek apakah user adalah pimpinan atau admin
        if current_user.role not in ['pimpinan', 'admin']:
            return jsonify({
                'success': False,
                'message': 'Anda tidak memiliki wewenang untuk menyetujui cuti'
            }), 403
        
        # Ambil data cuti
        cuti = Cuti.query.get_or_404(cuti_id)
        
        if cuti.status_cuti == 'approved':
            return jsonify({
                'success': False,
                'message': 'Cuti sudah disetujui sebelumnya'
            }), 400
        
        # Update status cuti
        cuti.status_cuti = 'approved'
        cuti.approved_by = current_user.email
        cuti.approved_at = datetime.now()
        
        # Generate digital signature dengan QR code
        from config.digital_signature import DigitalSignature
        digital_sig = DigitalSignature()
        
        # Info approver
        approver_info = {
            'name': current_user.email,
            'role': current_user.role,
            'nip': getattr(current_user, 'nip', '-')
        }
        
        # Create QR code
        qr_info = digital_sig.create_qr_code(cuti, approver_info)
        if not qr_info:
            return jsonify({
                'success': False,
                'message': 'Gagal membuat QR code digital signature'
            }), 500
        
        # Generate PDF
        pdf_path = digital_sig.generate_pdf_surat_cuti(cuti, qr_info, approver_info)
        if not pdf_path:
            return jsonify({
                'success': False,
                'message': 'Gagal membuat PDF surat persetujuan'
            }), 500
        
        # Update cuti dengan QR code dan path PDF
        cuti.qr_code = qr_info['signature_hash']
        cuti.pdf_path = pdf_path
        cuti.notes = request.json.get('notes', '')
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Cuti berhasil disetujui dengan tanda tangan digital',
            'qr_code': qr_info['qr_base64'],
            'signature_hash': qr_info['signature_hash'],
            'pdf_url': f'/cuti/download_pdf/{cuti_id}'
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'message': f'Error: {str(e)}'
        }), 500

@ocr_cuti_bp.route('/reject/<int:cuti_id>', methods=['POST'])
@login_required
def reject_cuti(cuti_id):
    """Reject cuti"""
    try:
        # Cek apakah user adalah pimpinan atau admin
        if current_user.role not in ['pimpinan', 'admin']:
            return jsonify({
                'success': False,
                'message': 'Anda tidak memiliki wewenang untuk menolak cuti'
            }), 403
        
        # Ambil data cuti
        cuti = Cuti.query.get_or_404(cuti_id)
        
        if cuti.status_cuti != 'pending':
            return jsonify({
                'success': False,
                'message': 'Cuti sudah diproses sebelumnya'
            }), 400
        
        # Update status cuti
        cuti.status_cuti = 'rejected'
        cuti.approved_by = current_user.email
        cuti.approved_at = datetime.now()
        cuti.notes = request.json.get('notes', 'Ditolak oleh pimpinan')
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Cuti berhasil ditolak'
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'message': f'Error: {str(e)}'
        }), 500

@ocr_cuti_bp.route('/download_pdf/<int:cuti_id>')
@login_required
def download_pdf(cuti_id):
    """Download PDF surat persetujuan cuti"""
    try:
        cuti = Cuti.query.get_or_404(cuti_id)
        
        if not cuti.pdf_path or not os.path.exists(cuti.pdf_path):
            flash('File PDF tidak ditemukan', 'error')
            return redirect(url_for('ocr_cuti.list_cuti'))
        
        from flask import send_file
        return send_file(
            cuti.pdf_path,
            as_attachment=True,
            download_name=f'surat_cuti_{cuti.nama}_{cuti.id_cuti}.pdf'
        )
        
    except Exception as e:
        flash(f'Error downloading PDF: {str(e)}', 'error')
        return redirect(url_for('ocr_cuti.list_cuti'))

@ocr_cuti_bp.route('/verify/<signature_hash>')
def verify_signature(signature_hash):
    """Verifikasi digital signature"""
    try:
        from config.digital_signature import DigitalSignature
        digital_sig = DigitalSignature()
        
        result = digital_sig.verify_signature(signature_hash)
        
        if result['valid']:
            cuti = result['cuti_data']
            return render_template('other/verify_signature.html', 
                                 cuti=cuti, 
                                 signature_hash=signature_hash,
                                 valid=True)
        else:
            return render_template('other/verify_signature.html', 
                                 message=result['message'],
                                 valid=False)
            
    except Exception as e:
        return render_template('other/verify_signature.html', 
                             message=f'Error: {str(e)}',
                             valid=False)

@ocr_cuti_bp.route('/save_extracted_data', methods=['POST'])
@login_required
def save_extracted_data():
    try:
        print("=== DEBUG SAVE EXTRACTED DATA ===")
        data = request.get_json()
        print(f"Received data: {data}")
        
        if not data:
            print("No data provided")
            return jsonify({"success": False, "error": "No data provided"}), 400

        saved_count = 0
        for item in data:
            print(f"Processing item: {item}")
            try:
                if item.get('jenis_surat') == 'Cuti':
                    print("Saving to Cuti table")
                    save_cuti_data(item)
                    saved_count += 1
                else:
                    print("Saving to SuratKeluar table")
                    save_surat_keluar(item)
                    saved_count += 1
            except Exception as e:
                print(f"Error saving item: {str(e)}")
                return jsonify({"success": False, "error": f"Error saving item: {str(e)}"}), 500
                
        print(f"Successfully saved {saved_count} items")
        return jsonify({"success": True, "message": f"Data saved successfully. {saved_count} items saved."}), 200

    except Exception as e:
        print(f"Server error: {str(e)}")
        return jsonify({"success": False, "error": f"Server error: {str(e)}"}), 500

def save_cuti_data(item):
    print(f"=== DEBUG SAVE CUTI DATA ===")
    print(f"Item to save: {item}")
    
    try:
        # Parse tanggal cuti
        tgl_mulai = tgl_selesai = None
        if item.get('tanggal_cuti'):
            try:
                if 'sampai' in item['tanggal_cuti']:
                    tgl_mulai_str, tgl_selesai_str = item['tanggal_cuti'].split(' sampai ')
                    tgl_mulai = datetime.strptime(tgl_mulai_str, '%Y-%m-%d').date()
                    tgl_selesai = datetime.strptime(tgl_selesai_str, '%Y-%m-%d').date()
                else:
                    tgl_mulai = datetime.strptime(item['tanggal_cuti'], '%Y-%m-%d').date()
                    tgl_selesai = tgl_mulai  # Jika hanya satu hari
            except Exception as e:
                print(f"Error parsing tanggal_cuti: {str(e)}")
                tgl_mulai = tgl_selesai = datetime.utcnow().date()

        # Buat objek Cuti
        cuti = Cuti(
            nama=item.get('nama', ''),
            nip=item.get('nip', ''),
            jabatan=item.get('jabatan', 'Tidak terbaca'),
            gol_ruang=item.get('gol_ruang', 'Tidak terbaca'),
            unit_kerja=item.get('unit_kerja', 'Tidak terbaca'),
            masa_kerja=item.get('masa_kerja', 'Tidak terbaca'),
            alamat=item.get('alamat', 'Tidak terbaca'),
            no_suratmasuk=item.get('nomor_surat', ''),
            tgl_ajuan_cuti=datetime.utcnow().date(),
            tanggal_cuti=tgl_mulai,
            sampai_cuti=tgl_selesai,
            telp=item.get('telp', ''),
            jenis_cuti=item.get('jenis_cuti', 'Tidak terbaca'),
            alasan_cuti=item.get('alasan_cuti', 'Tidak terbaca'),
            lama_cuti=item.get('lama_cuti', 'Tidak terbaca'),
            status_cuti='pending'
        )
        
        print(f"Cuti object created: {cuti}")
        db.session.add(cuti)
        db.session.commit()
        print("Cuti data saved successfully")
        
    except Exception as e:
        print(f"Error in save_cuti_data: {str(e)}")
        db.session.rollback()
        raise e

def save_surat_keluar(item):
    # Parse tanggal
    tanggal_obj = datetime.utcnow().date()
    if item.get('tanggal_cuti'):
        try:
            if '/' in item['tanggal_cuti']:
                tanggal_obj = datetime.strptime(item['tanggal_cuti'], '%d/%m/%Y').date()
            else:
                tanggal_obj = datetime.strptime(item['tanggal_cuti'], '%Y-%m-%d').date()
        except:
            tanggal_obj = datetime.utcnow().date()

    # Buat objek SuratKeluar
    surat_keluar = SuratKeluar(
        full_letter_number=item.get('nomor_surat', 'Not found'),
        nomor_suratKeluar=item.get('nomor_surat', 'Not found'),
        tanggal_suratKeluar=tanggal_obj,
        pengirim_suratKeluar=item.get('pengirim', 'Not found'),
        penerima_suratKeluar=item.get('penerima', 'Ketua Pengadilan Agama'),
        kode_suratKeluar="CUTI-" + ''.join(random.choices(string.ascii_uppercase + string.digits, k=6)),
        jenis_suratKeluar='Cuti' if item.get('jenis_surat') == 'Cuti' else 'Umum',
        isi_suratKeluar=item.get('isi', 'Not found'),
        initial_full_letter_number=item.get('nomor_surat', 'Not found'),
        initial_pengirim_suratKeluar=item.get('pengirim', 'Not found'),
        initial_penerima_suratKeluar=item.get('penerima', 'Ketua Pengadilan Agama'),
        initial_isi_suratKeluar=item.get('isi', 'Not found'),
        initial_nomor_suratKeluar=item.get('nomor_surat', 'Not found'),
        status_suratKeluar='pending'
    )
    
    db.session.add(surat_keluar)
    db.session.commit() 