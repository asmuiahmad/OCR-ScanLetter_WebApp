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
    pattern_perihal = r"(?:Perihal|Hal|HaI|Ha1|PERIHAL|HAL)\s*[:\-]?\s*(.*?)\n"
    match_perihal = re.search(pattern_perihal, text, re.DOTALL | re.IGNORECASE)
    
    if match_perihal:
        isi = match_perihal.group(1).strip()
        if '\n' in isi:
            isi = isi.split('\n')[0].strip()
        return isi
    
    pattern_awal = r"(?:Di-|Tempat)\s*\n(.*?)\n"
    match_awal = re.search(pattern_awal, text, re.DOTALL | re.IGNORECASE)
    
    if match_awal:
        isi = match_awal.group(1).strip()
        if '\n' in isi:
            isi = isi.split('\n')[0].strip()
        return isi
    
    lines = text.split('\n')
    for i, line in enumerate(lines):
        line = line.strip()
        if len(line.split()) > 3 and not any(word in line for word in ["Assalamu", "Wr.Wb", "Yth"]):
            return line
    
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