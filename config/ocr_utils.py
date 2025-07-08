import os
import re
import json
import hashlib
from difflib import SequenceMatcher
import logging
import pytesseract
from PIL import Image

# Setup logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

def clean_text(text):
    """
    Enhanced text cleaning function
    """
    if not text:
        return ''
    
    # Remove extra whitespaces
    text = re.sub(r'\s+', ' ', text)
    
    # Remove non-printable characters
    text = re.sub(r'[^\x20-\x7E\n\u00A0-\uD7FF\uF900-\uFDCF\uFDF0-\uFFEF]', '', text)
    
    # Normalize common OCR mistakes
    text = text.replace('1', 'I').replace('0', 'O')
    
    # Remove leading/trailing whitespaces
    text = text.strip()
    
    return text

def calculate_file_hash(file_path):
    hasher = hashlib.md5()
    with open(file_path, 'rb') as f:
        for buf in iter(lambda: f.read(65536), b""):
            hasher.update(buf)
    return hasher.hexdigest()

def load_dictionary():
    json_path = os.path.join('static', 'assets', 'js', 'dictionary.json')
    with open(json_path, 'r') as f:
        return json.load(f)

dictionary = load_dictionary()
indonesian_months = dictionary.get('indonesian_months', [])
pengirim_keywords = dictionary.get('pengirim_keywords', [])

def extract_dates(text):
    """
    More robust date extraction
    """
    # Multiple date formats
    date_patterns = [
        r'\d{1,2}\s*(?:Jan|Feb|Mar|Apr|Mei|Jun|Jul|Agu|Sep|Okt|Nov|Des)[a-z]*\s*\d{4}',
        r'\d{1,2}[-/]\d{1,2}[-/]\d{4}',
        r'\d{4}[-/]\d{1,2}[-/]\d{1,2}'
    ]
    
    dates = []
    for pattern in date_patterns:
        matches = re.findall(pattern, text, re.IGNORECASE)
        dates.extend(matches)
    
    return dates if dates else ['Not found']

def extract_tanggal(text):
    dates = extract_dates(text)
    return dates[0] if dates else 'Not found'

def extract_penerima_surat_masuk(text):
    """
    Enhanced penerima extraction with multiple patterns and improved matching
    """
    # Pola pencarian yang lebih komprehensif
    patterns = [
        r'(?:Kepada[\s:]*)?(Yth\.?|YM\.?)\s*[.:]?\s*(Ketua[^\n]+)',
        r'Kepada\s*:\s*([^\n]+)',
        r'Ditujukan\s*[Kk]epada\s*:\s*([^\n]+)',
        r'(?:Kepada|Yang\s*Mulia)\s*(?:Yth\.?|YM\.?)\s*[.:]?\s*([^\n]+)',
        r'(?:Penerima|Alamat)\s*:\s*([^\n]+)'
    ]
    
    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE | re.MULTILINE)
        if match:
            # Bersihkan dan saring teks penerima
            penerima = match.group(1).strip()
            
            # Filter untuk menghindara salam atau kata kunci yang tidak relevan
            if not any(irrelevant in penerima.lower() for irrelevant in ['assalamu', 'dengan', 'hormat']):
                return penerima
    
    return 'Not found'

def extract_penerima_surat_keluar(text):
    pattern = r'(?:Kepada\s*(?:Yth\.?|YM\.?)\s*:\s*\n)([^\n]+)'
    match = re.search(pattern, text, re.IGNORECASE)
    if match:
        return match.group(1).strip()
    
    pattern = r'(?:Kepada\s*(?:Yth\.?|YM\.?)\s*:\s*)([^\n]+)'
    match = re.search(pattern, text, re.IGNORECASE)
    return match.group(1).strip() if match else 'Not found'

def extract_pengirim(text):
    """
    Enhanced pengirim extraction with multiple patterns and improved matching
    """
    patterns = [
        r'Dari\s*:\s*([^\n]+)',
        r'Pengirim\s*:\s*([^\n]+)',
        r'Yang\s*[Bb]ersangkutan\s*:\s*([^\n]+)',
        r'(?:Nama|Penulis)\s*[:\-]?\s*([A-Z\s]+)',
        r'Perihal\s*[:\-]?\s*([^\n]+)'
    ]
    
    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE | re.MULTILINE)
        if match:
            # Bersihkan dan saring teks pengirim
            pengirim = match.group(1).strip()
            
            # Filter untuk menghindari kata kunci yang tidak relevan
            if not any(irrelevant in pengirim.lower() for irrelevant in ['assalamu', 'dengan', 'hormat']):
                return pengirim
    
    return 'Not found'

def extract_isi_suratmasuk(text):
    """
    More comprehensive isi surat extraction with multiple patterns
    """
    # Prioritized patterns for extracting content
    patterns = [
        r"(?:Perihal|Hal|HaI|Ha1|PERIHAL|HAL)\s*[:\-]?\s*(.*?)\n",
        r"(?:Isi\s*[Ss]urat|Maksud)\s*[:\-]?\s*(.*?)\n",
        r"Tentang\s*[:\-]?\s*(.*?)\n",
        r"(?:Di-|Tempat)\s*\n(.*?)\n"
    ]
    
    for pattern in patterns:
        match = re.search(pattern, text, re.DOTALL | re.IGNORECASE)
        if match:
            isi = match.group(1).strip()
            
            # Bersihkan dan filter isi surat
            if '\n' in isi:
                isi = isi.split('\n')[0].strip()
            
            # Filter untuk menghindari salam atau header
            if not any(irrelevant in isi.lower() for irrelevant in ['assalamu', 'yth', 'dengan', 'hormat']):
                return isi
    
    # Fallback: Find first meaningful line
    lines = text.split('\n')
    for line in lines:
        line = line.strip()
        if (len(line.split()) > 3 and 
            not any(word in line.lower() for word in ["assalamu", "wr.wb", "yth"])):
            return line
    
    return "Not found"

def extract_isi_suratkeluar(text):
    # Pola untuk mencari perihal atau isi surat
    patterns = [
        r"perihal\s*[:\-]?\s*(.*)",
        r"hal\s*[:\-]?\s*(.*)",
        r"tentang\s*[:\-]?\s*(.*)",
        r"maksud\s*[:\-]?\s*(.*)"
    ]

    # Coba setiap pola
    for pattern in patterns:
        lines = text.splitlines()
        for line in lines:
            match = re.search(pattern, line, flags=re.IGNORECASE)
            if match:
                isi = match.group(1).strip()
                if isi and len(isi) > 3:
                    return isi

    # Jika pola spesifik tidak ditemukan, cari paragraf pertama yang cukup panjang
    lines = text.splitlines()
    for line in lines:
        line = line.strip()
        # Cari baris yang memiliki lebih dari 10 kata dan bukan salam/header
        if (len(line.split()) > 10 and 
            not any(word in line.lower() for word in ['assalamu', 'yth', 'kepada', 'dengan', 'hormat'])):
            return line

    return "Not found"

def calculate_ocr_completeness(data):
    total_fields = 4
    not_found = sum(
        1 for key in ['nomor_surat', 'pengirim', 'penerima', 'isi']
        if data.get(key) == 'Not found'
    )
    return round(((total_fields - not_found) / total_fields) * 100, 2)

def calculate_ocr_accuracy(original_text, edited_text):
    if not original_text and not edited_text:
        return 100.0
    if not original_text or not edited_text:
        return 0.0
    return round(SequenceMatcher(None, original_text, edited_text).ratio() * 100, 2)

def hitung_field_not_found(surat, prefix):
    field_not_found = {
        f"nomor_{prefix}": 0,
        f"pengirim_{prefix}": 0,
        f"penerima_{prefix}": 0,
        f"isi_{prefix}": 0,
        "full_letter_number_not_found": 0
    }

    nomor_field = getattr(surat, f"nomor_{prefix}", "")
    pengirim_field = getattr(surat, f"pengirim_{prefix}", "")
    penerima_field = getattr(surat, f"penerima_{prefix}", "")
    isi_field = getattr(surat, f"isi_{prefix}", "")

    if not nomor_field or "not found" in nomor_field.lower():
        field_not_found[f"nomor_{prefix}"] += 1
        field_not_found["full_letter_number_not_found"] += 1

    if not pengirim_field or "not found" in pengirim_field.lower():
        field_not_found[f"pengirim_{prefix}"] += 1

    if not penerima_field or "not found" in penerima_field.lower():
        field_not_found[f"penerima_{prefix}"] += 1

    if not isi_field or "not found" in isi_field.lower():
        field_not_found[f"isi_{prefix}"] += 1

    return field_not_found

def extract_nomor_surat(text):
    match = re.search(
        r'(?:Nomor|Nornor|Nomor\s*>\s*|Nomo|NOMOR)?\s*[:>\-\[]?\s*([\[\(]?[A-Z0-9\-./\s@ ]+)',
        text,
        re.IGNORECASE
    )
    if match:
        raw_nomor = match.group(1)
        cleaned = clean_text(raw_nomor)
        return cleaned.strip("[]() ")
    return 'Not found'

def extract_acara(text):
    pattern = r"(?:Acara|acara)\s*[:\-]?\s*(.*?)(?=\n|tempat|tanggal|jam|pukul|$)"
    match = re.search(pattern, text, flags=re.IGNORECASE)
    return match.group(1).strip() if match else "Not found"

def extract_tempat(text):
    # Pola utama: Mencari "Tempat :" diikuti teks hingga akhir baris
    pattern_main = r"Tempat\s*:\s*(.*?)\n"
    match = re.search(pattern_main, text, flags=re.IGNORECASE)
    
    if match:
        tempat = match.group(1).strip()
        
        # Filter khusus untuk menghindari salam
        if not any(salam in tempat for salam in ["Assalamu", "Wassalamu", "Warahmatullahi"]):
            return tempat
    
    pattern_alt1 = r"Tempat\s*:?\s*(.*?)\n"
    match_alt1 = re.search(pattern_alt1, text, flags=re.IGNORECASE)
    if match_alt1:
        tempat = match_alt1.group(1).strip()
        if not any(salam in tempat for salam in ["Assalamu", "Wassalamu", "Warahmatullahi"]):
            return tempat
    
    pattern_alt2 = r"(?:Tempat|tempat|lokasi)\s*[:\-]?\s*(.*?)(?=\n|$|Hari|Tanggal|Pukul|Jam)"
    match_alt2 = re.search(pattern_alt2, text, flags=re.IGNORECASE)
    if match_alt2:
        tempat = match_alt2.group(1).strip()
        if not any(salam in tempat for salam in ["Assalamu", "Wassalamu", "Warahmatullahi"]):
            return tempat
    
    return "Not found"

def extract_tanggal_acara(text):
    pattern = r"(?:Tanggal Acara|Tanggal|tanggal acara|tgl)\s*[:\-]?\s*(.*?)(?=\n|jam|pukul|$)"
    match = re.search(pattern, text, flags=re.IGNORECASE)
    return match.group(1).strip() if match else "Not found"

def extract_jam(text):
    pattern = r"(?:Pukul|Jam|Waktu)\s*[:\-]?\s*(\d{1,2}[.:]\d{2})"
    match = re.search(pattern, text, flags=re.IGNORECASE)
    return match.group(1).strip() if match else "Not found"

# Fungsi baru untuk deteksi formulir cuti
def is_formulir_cuti(text):
    """Deteksi apakah teks mengandung formulir permintaan cuti"""
    pattern = r"FORMULIR\s+PERMINTAAN\s+DAN\s+PEMBERIAN\s+CUTI"
    return re.search(pattern, text, re.IGNORECASE) is not None

def extract_formulir_cuti_data(text):
    """Ekstrak data khusus dari formulir cuti dengan lebih akurat"""
    # Pola untuk ekstraksi data pegawai
    nama_pattern = r"(?:Nama\s*[:.]?\s*|Nama\s+Lengkap\s*[:.]?\s*)([A-Z\s]+)"
    nip_pattern = r"(?:NIP\s*[:.]?\s*|Nomor\s+Induk\s+Pegawai\s*[:.]?\s*)(\d+)"
    tanggal_pattern = r"(?:Tanggal\s*[:.]?\s*)(\d{1,2}[/-]\d{1,2}[/-]\d{4})"
    jenis_cuti_pattern = r"(?:Jenis\s*Cuti\s*[:.]?\s*|Macam\s+Cuti\s*[:.]?\s*)([A-Za-z\s]+)"
    
    nama = re.search(nama_pattern, text, re.IGNORECASE)
    nip = re.search(nip_pattern, text, re.IGNORECASE)
    tanggal = re.search(tanggal_pattern, text, re.IGNORECASE)
    jenis_cuti = re.search(jenis_cuti_pattern, text, re.IGNORECASE)
    
    return {
        'nama': nama.group(1).strip() if nama else 'N/A',
        'nip': nip.group(1) if nip else 'N/A',
        'tanggal': tanggal.group(1) if tanggal else 'N/A',
        'jenis_cuti': jenis_cuti.group(1).strip() if jenis_cuti else 'N/A'
    }

def preprocess_image(image_path):
    """
    Preprocess image to improve OCR accuracy
    """
    try:
        # Open the image
        img = Image.open(image_path)
        
        # Convert to grayscale
        img_gray = img.convert('L')
        
        # Optional: Enhance contrast
        from PIL import ImageEnhance
        enhancer = ImageEnhance.Contrast(img_gray)
        img_enhanced = enhancer.enhance(2.0)  # Increase contrast
        
        return img_enhanced
    except Exception as e:
        logger.error(f"Error preprocessing image {image_path}: {str(e)}")
        return None

def extract_text_with_multiple_configs(file_path):
    """
    Extract text from image using multiple Tesseract configurations
    with comprehensive logging and debugging
    """
    import pytesseract
    from PIL import Image
    import logging
    import re

    logger = logging.getLogger(__name__)
    logger.setLevel(logging.DEBUG)

    # Konfigurasi Tesseract yang berbeda
    configs = [
        r'--oem 3 --psm 6 -c tessedit_char_whitelist=ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789/.,:-',  # Default
        r'--oem 3 --psm 11',  # Sparse text. Find as much text as possible
        r'--oem 3 --psm 3',   # Fully automatic page segmentation
        r'--oem 3 --psm 1',   # Automatic page segmentation with OSD
    ]

    # Preprocessing untuk meningkatkan kualitas OCR
    def preprocess_image(image):
        # Convert to grayscale
        gray = image.convert('L')
        
        # Optional: Enhance contrast
        from PIL import ImageEnhance
        enhancer = ImageEnhance.Contrast(gray)
        gray = enhancer.enhance(2.5)  # Meningkatkan kontras lebih tinggi
        
        # Optional: Sharpen image
        from PIL import ImageFilter
        gray = gray.filter(ImageFilter.SHARPEN)
        
        return gray

    try:
        # Buka gambar
        img = Image.open(file_path)
        
        # Preprocessing gambar
        preprocessed_img = preprocess_image(img)
        
        # Simpan log detail gambar
        logger.info(f"Image Details:")
        logger.info(f"  Path: {file_path}")
        logger.info(f"  Format: {img.format}")
        logger.info(f"  Mode: {img.mode}")
        logger.info(f"  Size: {img.size}")

        # Ekstraksi teks dengan konfigurasi berbeda
        extracted_texts = []
        for config in configs:
            try:
                text = pytesseract.image_to_string(preprocessed_img, config=config, lang='ind')
                
                # Log detail ekstraksi
                logger.info(f"Extraction with config '{config}':")
                logger.info(f"  Text length: {len(text)}")
                
                if text.strip():
                    extracted_texts.append(text)
            except Exception as config_error:
                logger.error(f"Error with config {config}: {str(config_error)}")

        # Gabungkan teks dari berbagai konfigurasi
        combined_text = "\n".join(extracted_texts)
        
        # Log teks gabungan
        logger.info("Combined Extracted Text:")
        logger.info(combined_text)

        return combined_text if combined_text else None

    except Exception as e:
        logger.error(f"Error extracting text from {file_path}: {str(e)}")
        return None