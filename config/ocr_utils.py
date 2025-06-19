import os
import re
import json
import hashlib
from difflib import SequenceMatcher

def clean_text(text):
    return re.sub(r'\s*\.\s*', '.', re.sub(r'\s*/\s*', '/', text.strip("() ")))

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
    months_pattern = '|'.join(indonesian_months)
    return [
        f"{d.zfill(2)}/{str(indonesian_months.index(m) + 1).zfill(2)}/{y}"
        for d, m, y in re.findall(rf'(\d{{1,2}})\s+({months_pattern})\s+(\d{{4}})', text)
    ]

def extract_tanggal(text):
    dates = extract_dates(text)
    return dates[0] if dates else 'Not found'

def extract_penerima_surat_masuk(text):
    pattern = r'(?:Kepada[\s:]*)?(Yth\.?|YM\.?)\s*[.:]?\s*(Ketua[^\n]+)'
    match = re.search(pattern, text, re.IGNORECASE)
    if match:
        return match.group(2).strip()
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
    matches = list(re.finditer(r'\b(?:' + '|'.join(map(re.escape, pengirim_keywords)) + r')\b', text))
    return matches[-1].group(0).strip() if matches else 'Not found'

def extract_isi_suratmasuk(text):
    match_isi = re.search(
        r"(?:Perihal|Hal|HaI|Ha1|PERIHAL|HAL)\s*[:\-]?\s*(?:\n\s*)?(.*?)(?=\n\s*\n|$)",
        text,
        re.DOTALL
    )
    if match_isi:
        return match_isi.group(1).strip()

    if re.search(r'FORMULIR PERMINTAAN DAN PEMBERIAN CUTI', text, re.IGNORECASE):
        return "FORMULIR PERMINTAAN DAN PEMBERIAN CUTI"

    return "Not found"

def extract_isi_suratkeluar(text):
    pattern = r"perihal\s*[:\-]?\s*(.*)"
    lines = text.splitlines()

    for line in lines:
        match = re.search(pattern, line, flags=re.IGNORECASE)
        if match:
            isi = match.group(1).strip()
            return isi if isi else "Not found"
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
