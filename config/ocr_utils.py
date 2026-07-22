import os
import re
import json
import hashlib
from difflib import SequenceMatcher
import logging
import pytesseract
from PIL import Image, ImageEnhance, ImageFilter
from datetime import datetime

# Setup logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

def normalize_ocr_text(text):
    """
    Normalize OCR text with minimal changes:
    - Only collapse multiple spaces to a single space
    - Preserve all original characters, punctuation, and structure
    - Do NOT replace I/O/l or apapun dalam konteks apapun
    """
    if not text:
        return text
    # Collapse multiple spaces only
    return re.sub(r' {2,}', ' ', text)

def clean_text(text):
    """
    Clean up OCR output text for better pattern matching
    - Only collapse multiple spaces, trim each line
    - Preserve all punctuation, symbols, and original structure
    """
    if text is None:
        return ""
    lines = text.split('\n')
    cleaned_lines = []
    for line in lines:
        cleaned_line = re.sub(r' {2,}', ' ', line).strip()
        cleaned_lines.append(cleaned_line)
    return '\n'.join(cleaned_lines)

def calculate_file_hash(file_path):
    hasher = hashlib.md5()
    with open(file_path, 'rb') as f:
        for buf in iter(lambda: f.read(65536), b""):
            hasher.update(buf)
    return hasher.hexdigest()

def load_dictionary():
    json_path = os.path.join('static', 'assets', 'js', 'utils', 'dictionary.json')
    with open(json_path, 'r') as f:
        return json.load(f)

dictionary = load_dictionary()
indonesian_months = dictionary.get('indonesian_months', [])
pengirim_keywords = dictionary.get('pengirim_keywords', [])

def parse_date_to_ddmmyyyy(date_str):
    """
    Konversi tanggal seperti '17 September 2024', '26Mei2024', '26 Mei 2024', '26-Mei-2024', '26/Mei/2024' ke 'dd/mm/yyyy'.
    Jika sudah dalam format yyyy-mm-dd, konversi ke dd/mm/yyyy.
    Jika tidak bisa diparse, return None.
    """
    if not date_str or not isinstance(date_str, str):
        return None
    # Cek jika sudah yyyy-mm-dd
    try:
        dt = datetime.strptime(date_str, '%Y-%m-%d')
        return dt.strftime('%d/%m/%Y')
    except Exception:
        pass
    # Cek jika format dd Month yyyy (spasi, strip, atau tanpa spasi)
    months = {
        'januari': '01', 'februari': '02', 'maret': '03', 'april': '04', 'mei': '05', 'juni': '06',
        'juli': '07', 'agustus': '08', 'september': '09', 'oktober': '10', 'november': '11', 'desember': '12',
    }
    # Pola: 26Mei2024, 26 Mei 2024, 26-Mei-2024, 26/Mei/2024
    match = re.search(r'(\d{1,2})[\s\-/]*([JjFfMmAaSsOoNnDd][a-zA-Z]+)[\s\-/]*(\d{4})', date_str)
    if match:
        day, month, year = match.groups()
        month_lc = month.lower()
        month_num = months.get(month_lc)
        if month_num:
            return f"{int(day):02d}/{month_num}/{year}"
    # Cek jika format dd/mm/yyyy
    match = re.match(r'(\d{1,2})/(\d{1,2})/(\d{4})', date_str)
    if match:
        return f"{int(match.group(1)):02d}/{int(match.group(2)):02d}/{match.group(3)}"
    return None

def extract_dates(text):
    """
    Ekstrak semua tanggal yang mengandung nama bulan Indonesia dan konversi ke dd/mm/yyyy jika bisa.
    Sekarang mencari tanggal di mana saja dalam baris, termasuk setelah koma, titik dua, atau strip.
    """
    months = [
        'Januari', 'Februari', 'Maret', 'April', 'Mei', 'Juni', 'Juli', 'Agustus', 'September', 'Oktober', 'November', 'Desember',
        'januari', 'februari', 'maret', 'april', 'mei', 'juni', 'juli', 'agustus', 'september', 'oktober', 'november', 'desember'
    ]
    results = []
    for line in text.splitlines():
        # Split baris dengan koma, titik dua, atau strip
        for part in re.split(r'[,:\-]', line):
            # Cari tanggal dengan nama bulan Indonesia di mana saja dalam part
            match = re.search(r'(\d{1,2})[\s\-/]*([A-Za-z]+)[\s\-/]*(\d{4})', part)
            if match:
                day, month, year = match.groups()
                month_lc = month.lower()
                month_map = {
                    'januari': '01', 'februari': '02', 'maret': '03', 'april': '04', 'mei': '05', 'juni': '06',
                    'juli': '07', 'agustus': '08', 'september': '09', 'oktober': '10', 'november': '11', 'desember': '12',
                }
                month_num = month_map.get(month_lc)
                if month_num:
                    results.append(f"{int(day):02d}/{month_num}/{year}")
    # Fallback: cari tanggal lain yang sudah dd/mm/yyyy
    for match in re.finditer(r'(\d{1,2})/(\d{1,2})/(\d{4})', text):
        results.append(f"{int(match.group(1)):02d}/{int(match.group(2)):02d}/{match.group(3)}")
    return results if results else None

def convert_indonesian_date_to_datetime(date_str):
    """
    Convert Indonesian date string to datetime object
    Example: "01 Oktober 2024" -> datetime object
    """
    try:
        # Indonesian month mapping
        month_mapping = {
            'januari': 1, 'februari': 2, 'maret': 3, 'april': 4,
            'mei': 5, 'juni': 6, 'juli': 7, 'agustus': 8,
            'september': 9, 'oktober': 10, 'november': 11, 'desember': 12,
            'jan': 1, 'feb': 2, 'mar': 3, 'apr': 4,
            'jun': 6, 'jul': 7, 'agu': 8, 'sep': 9,
            'okt': 10, 'nov': 11, 'des': 12
        }
        
        # Clean the date string
        date_str = date_str.strip()
        
        # Try to parse Indonesian date format
        for pattern in [
            r'(\d{1,2})\s+([A-Za-z]+)\s+(\d{4})',  # 01 Oktober 2024
            r'(\d{1,2})[-/](\d{1,2})[-/](\d{4})',  # 01/10/2024
            r'(\d{4})[-/](\d{1,2})[-/](\d{1,2})',  # 2024/10/01
        ]:
            match = re.match(pattern, date_str, re.IGNORECASE)
            if match:
                if len(match.groups()) == 3:
                    if match.group(2).isalpha():  # Indonesian month name
                        day = int(match.group(1))
                        month_name = match.group(2).lower()
                        year = int(match.group(3))
                        
                        if month_name in month_mapping:
                            month = month_mapping[month_name]
                            return datetime(year, month, day)
                    else:  # Numeric format
                        if len(match.group(1)) == 4:  # YYYY/MM/DD
                            year = int(match.group(1))
                            month = int(match.group(2))
                            day = int(match.group(3))
                        else:  # DD/MM/YYYY
                            day = int(match.group(1))
                            month = int(match.group(2))
                            year = int(match.group(3))
                        
                        return datetime(year, month, day)
        
        return None
    except Exception as e:
        print(f"Error converting date: {e}")
        return None

def extract_tanggal(text):
    dates = extract_dates(text)
    if dates and dates[0] != 'Not found':
        # Try to convert the first date found
        date_obj = convert_indonesian_date_to_datetime(dates[0])
        if date_obj:
            return date_obj.strftime('%Y-%m-%d')
    return 'Not found'

def normalize_case(text):
    """
    Normalize text case: capitalize first letter of each word, keep proper nouns in title case.
    Perbaikan: Jangan memecah kata secara berlebihan, hanya hapus spasi ganda, bukan menambah spasi di tengah kata.
    """
    if not text or text == "Not found" or text == "N/A":
        return text

    # Hapus spasi ganda, tapi jangan menambah spasi di tengah kata
    cleaned_text = re.sub(r'\s+', ' ', text).strip()

    # Normalisasi case: kapitalisasi awal kata
    words = cleaned_text.split(' ')
    normalized_words = []
    for word in words:
        # Keep specific abbreviations in uppercase
        if word.upper() in ['UNISKA', 'FTI', 'HM']:
            normalized_words.append(word.upper())
        # Keep common titles and proper nouns in title case
        elif word.lower() in ['ketua', 'pengadilan', 'panitera', 'sekretaris', 'kepala', 'bagian', 'staf', 'petugas', 'administrasi', 'keuangan', 'layanan', 'pelayanan', 'publik', 'humas', 'teknis', 'it', 'keamanan', 'umum', 'perencanaan', 'teknologi', 'informasi', 'muda', 'pendaftaran', 'perlengkapan', 'penyimpanan', 'pengganti']:
            normalized_words.append(word.title())
        else:
            # Capitalize first letter, lowercase the rest
            normalized_words.append(word.capitalize())

    return ' '.join(normalized_words)

def normalize_recipient_text(text):
    """
    Normalize recipient text by:
    1. Splitting camel case and ALLCAPS glued words
    2. Replacing runs of spaces with a single space
    3. Handling special cases like "UNISKA" that should remain uppercase
    """
    if not text or text == "Not found":
        return text
    # Handle specific abbreviations and special cases
    text = re.sub(r'(?i)uniska', 'UNISKA', text)
    text = re.sub(r'U\s*N\s*I\s*S\s*K\s*A', 'UNISKA', text)
    text = re.sub(r'(?i)fti', 'FTI', text)
    text = re.sub(r'(?i)\bhm\b', 'HM', text)
    
    # Pisahkan camel case: huruf kecil diikuti huruf besar
    text = re.sub(r'([a-z])([A-Z])', r'\1 \2', text)
    
    # Pisahkan ALLCAPS yang menempel dengan kata lain (UNISKAJ -> UNISKA J)
    text = re.sub(r'([A-Z]{2,})([A-Z][a-z])', r'\1 \2', text)
    text = re.sub(r'([a-z])([A-Z]{2,})', r'\1 \2', text)
    
    # Pisahkan kata yang menempel dengan huruf besar di tengah (PersetujuanPraktekKerja -> Persetujuan Praktek Kerja)
    text = re.sub(r'([A-Z][a-z]+)([A-Z][a-z]+)', r'\1 \2', text)
    
    # Pisahkan kata yang menempel dengan huruf besar di akhir (MahasiswaUniversitas -> Mahasiswa Universitas)
    text = re.sub(r'([a-z]+)([A-Z][a-z]+)', r'\1 \2', text)
    
    # Pisahkan kata yang menempel dengan huruf besar di awal (UNISKAJ -> UNISKA J)
    text = re.sub(r'([A-Z]+)([A-Z][a-z]+)', r'\1 \2', text)
    
    # Replace runs of spaces with a single space
    text = re.sub(r'\s+', ' ', text)
    
    # Use the new normalize_case function
    return normalize_case(text)

def extract_penerima_surat_keluar(text):
    """
    Extract recipient (penerima) from OCR text for incoming letters
    Only take up to the first newline or known stopwords after 'Yth.' or 'Kepada Yth.'
    """
    # Look for text after "Yth." up to newline, "di tempat", "Assalamualaikum", or "Dengan hormat"
    yth_patterns = [
        r'Yth\.?\s*(.*?)(?:\n|di\s+tempat|Assalamualaikum|Dengan hormat)',
        r'Kepada\s+Yth\.?\s*(.*?)(?:\n|di\s+tempat|Assalamualaikum|Dengan hormat)',
    ]
    
    for pattern in yth_patterns:
        match = re.search(pattern, text, re.IGNORECASE | re.DOTALL)
        if match:
            # Extract the full recipient text
            recipient_text = match.group(1).strip()
            # Only take up to the first newline if present
            recipient_text = recipient_text.split('\n')[0].strip()
            # Clean up any extra spaces and remove "di tempat" if it appears at the end
            recipient_text = re.sub(r'\s+', ' ', recipient_text)
            recipient_text = re.sub(r'di\s*tempat\s*$', '', recipient_text, flags=re.IGNORECASE).strip()
            # Normalize the recipient text
            recipient = normalize_recipient_text(recipient_text)
            return recipient
    return "Not found"

def extract_penerima_surat_masuk(text):
    """
    Extract recipient (penerima) from OCR text for outgoing letters
    """
    # Same logic as extract_penerima_surat_keluar
    return extract_penerima_surat_keluar(text)

def extract_pengirim(text):
    """
    Extract pengirim from text using dictionary keywords, searching from bottom to top
    """
    # Load dictionary
    dictionary = load_dictionary()
    pengirim_keywords = dictionary.get('pengirim_keywords', [])
    
    logger.debug(f"Extracting pengirim from text with {len(pengirim_keywords)} keywords")
    logger.debug(f"Keywords: {pengirim_keywords}")
    
    # Split text into lines and reverse to search from bottom to top
    lines = text.split('\n')
    lines.reverse()  # Search from bottom to top
    
    logger.debug(f"Searching through {len(lines)} lines from bottom to top")
    
    # First, try to find exact matches with keywords
    for i, line in enumerate(lines):
        line = line.strip()
        if not line:
            continue
            
        logger.debug(f"Checking line {len(lines) - i}: '{line}'")
        
        # Check if line contains any pengirim keyword
        for keyword in pengirim_keywords:
            if keyword.lower() in line.lower():
                # Clean up the line and normalize case
                cleaned_line = re.sub(r'[^\w\s]', ' ', line)  # Remove special characters
                cleaned_line = re.sub(r'\s+', ' ', cleaned_line).strip()  # Normalize spaces
                
                normalized_line = normalize_case(cleaned_line)
                logger.debug(f"Found pengirim keyword '{keyword}' in line: '{normalized_line}'")
                return normalized_line
    
    # If no exact keyword match found, try pattern matching
    logger.debug("No keyword match found, trying pattern matching")
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
                normalized_pengirim = normalize_case(pengirim)
                logger.debug(f"Found pengirim via pattern '{pattern}': '{normalized_pengirim}'")
                return normalized_pengirim
    
    logger.debug("No pengirim found, returning 'Not found'")
    return 'Not found'

# Simple Indonesian wordlist for demonstration (expand as needed)
INDO_WORDLIST = set([
    'penyampaian', 'amar', 'putusan', 'banding',
    'pengadilan', 'agama', 'banjarbaru', 'palangkaraya',
    'nomor', 'surat', 'kepada', 'yth', 'ketua', 'isi', 'keterangan', 'pengembalian', 'relas', 'dengan', 'hormat',
    'untuk', 'dapat', 'dipergunakan', 'sebagaimana', 'terima', 'kasih', 'panitera', 'tembusan', 'laporan', 'jalan',
    'telp', 'sg', 'pengantar', 'tanggal', 'lembar', 'disampaikan', 'johanes', 'kupabin', 'mestinya', 'banjarbaru',
    'oktober', 'putusan', 'g', 'plk', 'an', 'j', 'p', 'kupa', 'm', 'l', 'a', 'i', 'dan', 'di', 'sebagai', 'no', 'ke',
    'bisa', 'tidak', 'ada', 'dalam', 'kepada', 'untuk', 'dengan', 'oleh', 'pada', 'sebagai', 'dari', 'ke', 'dan', 'di',
    'terima', 'kasih', 'laporan', 'pengantar', 'nomor', 'surat', 'tanggal', 'pengadilan', 'agama', 'banjarbaru',
    'palangkaraya', 'putusan', 'banding', 'amar', 'isi', 'keterangan', 'pengembalian', 'relas', 'disampaikan',
    'hormat', 'tembusan', 'jalan', 'telp', 'sg', 'no', 'g', 'plk', 'an', 'j', 'p', 'kupa', 'mestinya', 'banjarbaru',
    'oktober', 'panitera', 'm', 'l', 'a', 'i', 'dan', 'di', 'sebagai', 'no', 'ke', 'pada', 'oleh', 'dari', 'atas',
    'adalah', 'yang', 'ini', 'itu', 'atau', 'juga', 'karena', 'sudah', 'belum', 'akan', 'bisa', 'tidak', 'ada', 'dalam'
])

# Tambahkan kata kunci ke INDO_WORDLIST
INDO_WORDLIST.update(['mohon', 'kesediaan', 'menerima', 'praktek', 'kerja'])

def word_breaker(text, wordlist=INDO_WORDLIST, min_word_len=4):
    """
    Breaks a long word into valid Indonesian words using a greedy approach.
    Only applies if the word is not in wordlist and is long.
    Only splits if ALL resulting parts are valid words, otherwise returns the original word.
    """
    def _break_word(s):
        s = s.lower()
        if s in wordlist or len(s) <= min_word_len:
            return [s]
        for i in range(len(s), min_word_len, -1):
            prefix = s[:i]
            suffix = s[i:]
            if prefix in wordlist and suffix in wordlist:
                return [prefix, suffix]
            if prefix in wordlist:
                rest = _break_word(suffix)
                if all(r in wordlist for r in rest):
                    return [prefix] + rest
        # If no valid split found, return the original word
        return [s]
    
    words = text.split()
    result = []
    for w in words:
        wl = w.lower()
        if wl not in wordlist and len(w) > min_word_len+2:
            # Coba pecah menjadi 2 bagian saja
            for i in range(min_word_len+1, len(w)-min_word_len):
                part1 = w[:i]
                part2 = w[i:]
                if part1.lower() in wordlist and part2.lower() in wordlist:
                    result.extend([part1, part2])
                    break
            else:
                result.append(w)
        else:
            result.append(w)
    return ' '.join(result)

def extract_isi_suratmasuk(text):
    """
    More comprehensive isi surat extraction with multiple patterns
    Now applies word_breaker to split glued words.
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
                normalized_isi = normalize_case(isi)
                # Apply word breaker
                normalized_isi = word_breaker(normalized_isi)
                return normalized_isi
    # Fallback: Find first meaningful line
    lines = text.split('\n')
    for line in lines:
        line = line.strip()
        if (len(line.split()) > 3 and 
            not any(word in line.lower() for word in ["assalamu", "wr.wb", "yth"])):
            normalized_line = normalize_case(line)
            normalized_line = word_breaker(normalized_line)
            return normalized_line
    return "Not found"

def split_merged_words(text):
    """
    Pattern replacement untuk glued words umum pada surat keluar.
    Tambahkan pola sesuai kebutuhan.
    """
    patterns = {
        r'Mohonkesediaan': 'Mohon kesediaan',
        r'menerimapraktekkerja': 'menerima praktek kerja',
        r'PersetujuanPraktekKerja': 'Persetujuan Praktek Kerja',
    }
    for pattern, replacement in patterns.items():
        text = re.sub(pattern, replacement, text, flags=re.IGNORECASE)
    return text

def extract_isi_suratkeluar(text):
    # Pola untuk mencari perihal atau isi surat, hanya ambil satu baris setelah kata kunci
    patterns = [
        r"perihal\s*[:\-]?\s*(.*?)(?:\n|$)",
        r"hal\s*[:\-]?\s*(.*?)(?:\n|$)",
        r"tentang\s*[:\-]?\s*(.*?)(?:\n|$)",
        r"maksud\s*[:\-]?\s*(.*?)(?:\n|$)"
    ]
    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            isi = match.group(1).strip()
            if isi and len(isi) > 3:
                normalized_isi = normalize_case(isi)
                # Selalu apply word_breaker agar kata menempel dipisah
                normalized_isi = word_breaker(normalized_isi)
                normalized_isi = split_merged_words(normalized_isi)
                return normalized_isi

    # Jika pola spesifik tidak ditemukan, cari paragraf pertama yang cukup panjang
    lines = text.splitlines()
    for line in lines:
        line = line.strip()
        # Cari baris yang memiliki lebih dari 10 kata dan bukan salam/header
        if (len(line.split()) > 10 and 
            not any(word in line.lower() for word in ['assalamu', 'yth', 'kepada', 'dengan', 'hormat'])):
            normalized_line = normalize_case(line)
            normalized_line = word_breaker(normalized_line)
            normalized_line = split_merged_words(normalized_line)
            return normalized_line

    return "Not found"

def calculate_ocr_completeness(data):
    total_fields = 4
    not_found = sum(
        1 for key in ['nomor_surat', 'pengirim', 'penerima', 'isi']
        if data.get(key) == 'Not found'
    )
    return round(((total_fields - not_found) / total_fields) * 100, 2)

def calculate_ocr_accuracy(original_text, edited_text):
    """
    Calculate OCR accuracy by comparing original extracted text with edited text
    Returns percentage of accuracy
    """
    if not original_text and not edited_text:
        return 100.0
    if not original_text or not edited_text:
        return 0.0
    
    # Normalize texts for comparison
    original_normalized = normalize_case(original_text) if original_text else ""
    edited_normalized = normalize_case(edited_text) if edited_text else ""
    
    # Calculate similarity using SequenceMatcher
    similarity = SequenceMatcher(None, original_normalized, edited_normalized).ratio()
    
    # Calculate word-level accuracy
    original_words = original_normalized.split()
    edited_words = edited_normalized.split()
    
    if not original_words:
        return 100.0 if not edited_words else 0.0
    
    # Count matching words
    matching_words = 0
    for word in original_words:
        if word in edited_words:
            matching_words += 1
    
    word_accuracy = (matching_words / len(original_words)) * 100
    
    # Combine character-level and word-level accuracy
    final_accuracy = (similarity * 70 + word_accuracy * 30) / 100
    
    return round(final_accuracy, 2)

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

def calculate_field_accuracy(initial_text, edited_text):
    """
    Calculate accuracy for a specific field by comparing initial OCR text with edited text
    """
    if not initial_text or initial_text == 'Not found':
        return 0.0
    
    if not edited_text:
        return 0.0
    
    # Normalize texts for comparison
    initial_normalized = normalize_case(initial_text)
    edited_normalized = normalize_case(edited_text)
    
    # Calculate similarity
    similarity = SequenceMatcher(None, initial_normalized, edited_normalized).ratio()
    
    # Calculate word-level accuracy
    initial_words = initial_normalized.split()
    edited_words = edited_normalized.split()
    
    if not initial_words:
        return 100.0 if not edited_words else 0.0
    
    # Count matching words
    matching_words = 0
    for word in initial_words:
        if word in edited_words:
            matching_words += 1
    
    word_accuracy = (matching_words / len(initial_words)) * 100
    
    # Combine character-level and word-level accuracy
    final_accuracy = (similarity * 70 + word_accuracy * 30) / 100
    
    return round(final_accuracy, 2)

def calculate_overall_ocr_accuracy(surat, prefix):
    """
    Calculate overall OCR accuracy for a document by comparing all fields
    """
    fields = ['nomor', 'pengirim', 'penerima', 'isi']
    total_accuracy = 0
    valid_fields = 0
    
    for field in fields:
        initial_field = getattr(surat, f"initial_{field}_{prefix}", "")
        edited_field = getattr(surat, f"{field}_{prefix}", "")
        
        if initial_field and initial_field != 'Not found':
            field_accuracy = calculate_field_accuracy(initial_field, edited_field)
            total_accuracy += field_accuracy
            valid_fields += 1
    
    if valid_fields == 0:
        return 0.0
    
    return round(total_accuracy / valid_fields, 2)

def extract_nomor_surat(text):
    """
    Ekstrak nomor surat dengan regex yang lebih fleksibel.
    Menangkap format seperti:
    - Nomor: 123/ABC/2024
    - Nomor 123/ABC/2024
    - Nomor. 123/ABC/2024
    - Nomor 1.040/PR/A4/L191118/5/2024
    """
    patterns = [
        r'(?:Nomor|No|Nomer|NOMOR|NO|N0|Nomar|Nomur|Nomot|Nomoe)\s*[:：\.-]?\s*([\w\./-]+)',
        r'(?:Nomor|No|Nomer|NOMOR|NO|N0|Nomar|Nomur|Nomot|Nomoe)[^\w\d]{0,3}([\w\./-]+)',
        r'(\d{1,4}/[\w\./-]+/\d{4})',  # fallback: nomor surat umum
    ]
    lines = text.splitlines()
    for line in lines:
        for pattern in patterns:
            match = re.search(pattern, line, re.IGNORECASE)
            if match:
                return match.group(1).strip()
    return 'Not found'

def extract_document_code(text):
    """
    Extract document code patterns like HM2.1.4, HK.2.6, etc. from text
    """
    # Normalize the text for better pattern matching
    text = normalize_ocr_text(text)
    
    # Look for various document code patterns with flexible spacing
    code_patterns = [
        # HM patterns
        r'(?:\/|\.)([HM]{2}\d+\.\d+\.?\d*)(?:\/|\.)',        # Match HM2.1.4 between separators
        r'([HM]{2}[\s.-]*\d+[\s.-]*\d+[\s.-]*\d*)',          # Handle spaces or separators in HM code
        r'(?:\/|\.|\s)([HM]{2}\s*\d+[\s.]*\d+[\s.]*\d*)',    # Even more flexible with spaces
        
        # HK patterns (new)
        r'(?:\/|\.)([HK]{2}\d*\.\d+\.?\d*)(?:\/|\.)',        # Match HK.2.6 between separators
        r'([HK]{2}[\s.-]*\d*[\s.-]*\d+[\s.-]*\d*)',          # Handle spaces or separators in HK code
        r'(?:\/|\.|\s)([HK]{2}\s*\d*[\s.]*\d+[\s.]*\d*)',    # Even more flexible with spaces for HK
        
        # Generic patterns for any 2-letter code
        r'(?:\/|\.)([A-Z]{2}\d*\.\d+\.?\d*)(?:\/|\.)',       # Any 2-letter code with numbers
        r'([A-Z]{2}[\s.-]*\d*[\s.-]*\d+[\s.-]*\d*)',         # Any 2-letter code with flexible separators
        r'(?:\/|\.|\s)([A-Z]{2}\s*\d*[\s.]*\d+[\s.]*\d*)',   # Any 2-letter code with spaces
        
        # Specific patterns for this particular case
        r'W15-A12\/([A-Z]{2}[0-9.]+\.[0-9]+)',               # Extract after W15-A12/
        r'[\/\.](?:[A-Z]{2})[.\s-]*(\d*)[.\s-]*(\d+)[.\s-]*(\d*)[\/\.]',  # Extract code parts
    ]
    
    for i, pattern in enumerate(code_patterns):
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            # Clean up the extracted code
            code = match.group(1).strip()
            # Normalize the format (remove spaces, standardize separators)
            code = re.sub(r'\s+', '', code)
            
            # If it's a valid document code format, return it
            if re.match(r'^[A-Z]{2}\d*\.\d+', code, re.IGNORECASE):
                return code
    
    # Look for specific patterns in the text
    specific_patterns = [
        r'HK\.\s*(\d+)\.\s*(\d+)',  # HK.2.6 pattern
        r'HM\s*(\d+)\.\s*(\d+)\.\s*(\d+)',  # HM2.1.4 pattern
        r'([A-Z]{2})\s*(\d+)\.\s*(\d+)',  # Any 2-letter code with numbers
    ]
    
    for pattern in specific_patterns:
        match = re.search(pattern, text, re.IGNORECASE)
    if match:
            if len(match.groups()) == 2:  # HK.2.6 format
                return f"{match.group(1)}.{match.group(2)}"
            elif len(match.groups()) == 3:  # HM2.1.4 format
                return f"{match.group(1)}{match.group(2)}.{match.group(3)}"
    
    # Last resort: look for any pattern that could be a document code
    match = re.search(r'[A-Z]{2}\s*\d+', text, re.IGNORECASE)
    if match:
        code_text = match.group(0).upper().replace(' ', '')
        # Try to reconstruct a valid code
        if len(code_text) >= 4:  # At least 2 letters followed by 2 digits
            if '.' not in code_text:
                # Insert dot if missing: HK26 -> HK.2.6
                parts = re.findall(r'([A-Z]{2})(\d)(\d+)', code_text)
                if parts:
                    code_text = f"{parts[0][0]}.{parts[0][1]}.{parts[0][2]}"
            return code_text
    
    # Super-specific patterns for this particular case
    specific_patterns = [
        r'[\/\.](?:[A-Z]{2})[.\s-]*(\d*)[.\s-]*(\d+)[.\s-]*(\d*)[\/\.]',  # Extract code parts
        r'W15-A12\/([A-Z]{2}[0-9.]+\.[0-9]+)',  # Extract after W15-A12/
    ]
    for pattern in specific_patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match and len(match.groups()) > 0:
            if len(match.groups()) == 1:
                return match.groups()[0]
            elif len(match.groups()) >= 2:  # If we have multiple groups with digits
                return f"{match.group(1)}.{match.group(2)}.{match.group(3) if match.group(3) else ''}"
    
    return 'Not found'  # Return 'Not found' instead of default value

def extract_roman_numeral(text):
    """
    Extract roman numerals (I-XII) for months from text
    """
    roman_patterns = [
        r'\/\s*((?:IX|IV|V?I{1,3}|X{1,2}I{0,3}))\s*\/',  # Between slashes: /IX/
        r'[^A-Z]((?:IX|IV|V?I{1,3}|X{1,2}I{0,3}))[^A-Z]',  # Roman numeral surrounded by non-letters
        r'([IVX]+)[\s\/.-]*(\d{4})',  # Roman numeral followed by year
        r'(\d+)[\s\/.-]*([IVX]+)',  # Digits followed by Roman numeral (day and month)
    ]
    
    roman_months = {
        'I': 'I', 'II': 'II', 'III': 'III', 'IV': 'IV', 
        'V': 'V', 'VI': 'VI', 'VII': 'VII', 'VIII': 'VIII', 
        'IX': 'IX', 'X': 'X', 'XI': 'XI', 'XII': 'XII'
    }
    
    # Also handle arabic numerals converted to roman
    arabic_to_roman = {
        '1': 'I', '2': 'II', '3': 'III', '4': 'IV', 
        '5': 'V', '6': 'VI', '7': 'VII', '8': 'VIII', 
        '9': 'IX', '10': 'X', '11': 'XI', '12': 'XII'
    }
    
    for pattern in roman_patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            month = match.group(1).upper()
            # Check if it's a valid roman numeral for months 1-12
            if month in roman_months:
                return month
            # Check if it's a digit that should be converted to roman
            elif month in arabic_to_roman:
                return arabic_to_roman[month]
    
    # Look for 1X pattern which often gets misrecognized in OCR
    match = re.search(r'[/\s.:-](\d{0,1}X)[/\s.:-]', text)
    if match:
        value = match.group(1)
        if value == 'X':
            return 'X'  # October
        if value == '1X':
            return 'IX'  # September
    
    return 'Not found'

def extract_acara(text):
    pattern = r"(?:Acara|acara)\s*[:\-]?\s*(.*?)(?=\n|tempat|tanggal|jam|pukul|$)"
    match = re.search(pattern, text, flags=re.IGNORECASE)
    if match:
        acara = match.group(1).strip()
        normalized_acara = normalize_case(acara)
        return normalized_acara
    return "Not found"

def extract_tempat(text):
    # Pola utama: Mencari "Tempat :" diikuti teks hingga akhir baris
    pattern_main = r"Tempat\s*:\s*(.*?)\n"
    match = re.search(pattern_main, text, flags=re.IGNORECASE)
    
    if match:
        tempat = match.group(1).strip()
        
        # Filter khusus untuk menghindari salam
        if not any(salam in tempat for salam in ["Assalamu", "Wassalamu", "Warahmatullahi"]):
            normalized_tempat = normalize_case(tempat)
            return normalized_tempat
    
    pattern_alt1 = r"Tempat\s*:?\s*(.*?)\n"
    match_alt1 = re.search(pattern_alt1, text, flags=re.IGNORECASE)
    if match_alt1:
        tempat = match_alt1.group(1).strip()
        if not any(salam in tempat for salam in ["Assalamu", "Wassalamu", "Warahmatullahi"]):
            normalized_tempat = normalize_case(tempat)
            return normalized_tempat
    
    pattern_alt2 = r"(?:Tempat|tempat|lokasi)\s*[:\-]?\s*(.*?)(?=\n|$|Hari|Tanggal|Pukul|Jam)"
    match_alt2 = re.search(pattern_alt2, text, flags=re.IGNORECASE)
    if match_alt2:
        tempat = match_alt2.group(1).strip()
        if not any(salam in tempat for salam in ["Assalamu", "Wassalamu", "Warahmatullahi"]):
            normalized_tempat = normalize_case(tempat)
            return normalized_tempat
    
    return "Not found"

def extract_tanggal_acara(text):
    pattern = r"(?:Tanggal Acara|Tanggal|tanggal acara|tgl)\s*[:\-]?\s*(.*?)(?=\n|jam|pukul|$)"
    match = re.search(pattern, text, flags=re.IGNORECASE)
    if match:
        tanggal = match.group(1).strip()
        normalized_tanggal = normalize_case(tanggal)
        return normalized_tanggal
    return "Not found"

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
        'nama': normalize_case(nama.group(1).strip()) if nama else 'N/A',
        'nip': nip.group(1) if nip else 'N/A',
        'tanggal': tanggal.group(1) if tanggal else 'N/A',
        'jenis_cuti': normalize_case(jenis_cuti.group(1).strip()) if jenis_cuti else 'N/A'
    }

# Preprocessing gambar lebih agresif

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

# Update extract_ocr_data agar lebih robust

def determine_jenis_surat(kodesurat2):
    """
    Determine jenis surat based on kodesurat2
    HM -> Umum
    HK -> Perkara
    KP -> Kepegawaian
    """
    if not kodesurat2 or kodesurat2 == 'Not found':
        return 'Umum'
    
    kodesurat2_upper = kodesurat2.upper()
    
    if kodesurat2_upper.startswith('HM'):
        return 'Umum'
    elif kodesurat2_upper.startswith('HK'):
        return 'Perkara'
    elif kodesurat2_upper.startswith('KP'):
        return 'Kepegawaian'
    else:
        return 'Umum'  # Default fallback

def extract_ocr_data(file_path):
    try:
        ocr_output = extract_text_with_multiple_configs(file_path)
        if not ocr_output:
            return None
            
        cleaned_text = clean_text(ocr_output)
        normalized_text = normalize_ocr_text(cleaned_text)
        
        # Ekstraksi field dengan logging
        nomor_surat = extract_nomor_surat(normalized_text)
        tanggal = extract_tanggal(normalized_text)
        pengirim = extract_pengirim(normalized_text)
        penerima = extract_penerima_surat_keluar(normalized_text)
        isi_surat = extract_isi_suratmasuk(normalized_text)
        
        # Ekstraksi komponen nomor surat untuk kodesurat2
        kodesurat2 = 'Not found'
        if nomor_surat != 'Not found':
            # Coba ekstrak HM code dari nomor surat
            hm_code = extract_document_code(normalized_text)
            if hm_code != 'Not found':
                kodesurat2 = hm_code
        
        # Determine jenis surat based on kodesurat2
        jenis_surat = determine_jenis_surat(kodesurat2)
        
        # Debug logging
        import logging
        logger = logging.getLogger(__name__)
        logger.debug(f"OCR Output:\n{ocr_output}")
        logger.debug(f"Cleaned Text:\n{cleaned_text}")
        logger.debug(f"Nomor Surat: {nomor_surat}")
        logger.debug(f"Kode Surat 2: {kodesurat2}")
        logger.debug(f"Jenis Surat: {jenis_surat}")
        logger.debug(f"Tanggal: {tanggal}")
        logger.debug(f"Pengirim: {pengirim}")
        logger.debug(f"Penerima: {penerima}")
        logger.debug(f"Isi Surat: {isi_surat}")
        
        return {
            'nomor_surat': nomor_surat,
            'kodesurat2': kodesurat2,
            'jenis_surat': jenis_surat,
            'tanggal': tanggal,
            'pengirim': pengirim,
            'penerima': penerima,
            'isi': isi_surat,
        }
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Error in extract_ocr_data: {str(e)}")
        return None