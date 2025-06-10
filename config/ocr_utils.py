import os
import re
import json
import hashlib

def clean_text(text):
    return re.sub(r'\s*\.\s*', '.', re.sub(r'\s*/\s*', '/', text.strip("() ")))

def calculate_file_hash(file_path):
    hasher = hashlib.md5()
    with open(file_path, 'rb') as f:
        for buf in iter(lambda: f.read(65536), b""):  # Read in chunks
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
    months_pattern = '|'.join(indonesian_months)
    return [
        f"{d.zfill(2)}/{str(indonesian_months.index(m) + 1).zfill(2)}/{y}"
        for d, m, y in re.findall(rf'(\d{{1,2}})\s+({months_pattern})\s+(\d{{4}})', text)
    ]

def extract_tanggal(text):
    dates = extract_dates(text)
    return dates[0] if dates else 'Not found'

def extract_penerima_surat_masuk(text):
    pattern = r'(?:Kepada[:\s]*(?:Yth\.?|YM\.?)|Yth\.?|YM\.?|Kepada[:\s]+)\s*(.*)' 
    match = re.search(pattern, text, re.IGNORECASE)
    return match.group(1).strip() if match else 'Not found'

def extract_penerima_surat_keluar(text):
    # Try matching when the marker is followed by a newline first.
    pattern = r'(?:Kepada\s*(?:Yth\.?|YM\.?)\s*:\s*\n)([^\n]+)'
    match = re.search(pattern, text, re.IGNORECASE)
    if match:
        return match.group(1).strip()
    
    # Fallback: marker and address on the same line.
    pattern = r'(?:Kepada\s*(?:Yth\.?|YM\.?)\s*:\s*)([^\n]+)'
    match = re.search(pattern, text, re.IGNORECASE)
    return match.group(1).strip() if match else 'Not found'

def extract_pengirim(text):
    matches = list(re.finditer(r'\b(?:' + '|'.join(map(re.escape, pengirim_keywords)) + r')\b', text))
    return matches[-1].group(0).strip() if matches else 'Not found'

def extract_isi(text):
    match_isi = re.search(
        r"(?:Perihal|Hal)\s*:\s*(?:\n\s*)?(.*?)(?=\n\s*\n|$)",
        text,
        re.DOTALL
    )
    return match_isi.group(1).strip() if match_isi else 'Not found'

def calculate_ocr_accuracy(data):
    total_fields = 4
    not_found = sum(
        1 for key in ['nomor_surat', 'pengirim', 'penerima', 'isi']
        if data.get(key) == 'Not found'
    )
    return round(((total_fields - not_found) / total_fields) * 100, 2)

