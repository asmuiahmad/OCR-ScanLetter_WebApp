# Troubleshooting Guide - OCR PDF Processing Errors

## Error: "Gagal memproses PDF"

Jika Anda mendapatkan error **"Error! Gagal memproses PDF: [filename]"**, ikuti langkah-langkah berikut:

---

## 🔍 Diagnosis Cepat

### Langkah 1: Cek Status Dependencies

1. Buka halaman OCR Cuti V2: `/cuti-v2/ocr`
2. Klik tombol **"Cek Dependencies"** (tombol oranye)
3. Lihat status semua dependencies

**Atau** jalankan script test dari terminal:

```bash
cd OCR-ScanLetter_WebApp
python test_pdf_dependencies.py
```

---

## 🛠️ Solusi Berdasarkan Error

### Error 1: pdf2image Not Installed

**Gejala:**
```
PDF processing will be disabled. Error: No module named 'pdf2image'
```

**Solusi:**
```bash
pip install pdf2image
```

---

### Error 2: Poppler Not Found

**Gejala:**
```
PDFInfoNotInstalledError: Unable to get page count. Is poppler installed and in PATH?
```

**Solusi:**

#### macOS:
```bash
brew install poppler
```

#### Ubuntu/Debian/Linux:
```bash
sudo apt-get update
sudo apt-get install poppler-utils
```

#### Windows:
1. Download Poppler dari: https://github.com/oschwartz10612/poppler-windows/releases/
2. Extract ke folder (misal: `C:\Program Files\poppler`)
3. Tambahkan ke PATH:
   - Buka "Environment Variables"
   - Edit "Path" di System Variables
   - Tambahkan: `C:\Program Files\poppler\Library\bin`
4. Restart terminal/IDE

#### Windows WSL:
```bash
sudo apt-get install poppler-utils
```

---

### Error 3: Tesseract Not Found

**Gejala:**
```
TesseractNotFoundError: tesseract is not installed or it's not in your PATH
```

**Solusi:**

#### macOS:
```bash
brew install tesseract
# Install bahasa Indonesia
brew install tesseract-lang
```

#### Ubuntu/Debian:
```bash
sudo apt-get install tesseract-ocr tesseract-ocr-ind
```

#### Windows:
1. Download installer: https://github.com/UB-Mannheim/tesseract/wiki
2. Install ke folder default: `C:\Program Files\Tesseract-OCR`
3. Tambahkan ke PATH atau set di script:
   ```python
   import pytesseract
   pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'
   ```

---

### Error 4: Permission Denied

**Gejala:**
```
PermissionError: [Errno 13] Permission denied: 'static/ocr/cuti/...'
```

**Solusi:**
```bash
# Pastikan folder writable
chmod -R 755 static/ocr/cuti

# Atau buat folder jika belum ada
mkdir -p static/ocr/cuti
chmod 755 static/ocr/cuti
```

---

### Error 5: File Too Large

**Gejala:**
- Upload gagal tanpa error message
- Request timeout

**Solusi:**
1. Kompres PDF terlebih dahulu
2. Atau tingkatkan limit di Flask config:
   ```python
   app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB
   ```

---

## ✅ Verifikasi Instalasi

Setelah install dependencies, test dengan:

```bash
# Test pdf2image
python -c "import pdf2image; print('pdf2image OK')"

# Test poppler
pdftoppm -v

# Test pytesseract
python -c "import pytesseract; print('pytesseract OK')"

# Test tesseract binary
tesseract --version

# Test PIL/Pillow
python -c "from PIL import Image; print('Pillow OK')"
```

**Semua command di atas harus berhasil!**

---

## 🔧 Install Semua Dependencies Sekaligus

### macOS:
```bash
# Python packages
pip install pdf2image pytesseract Pillow

# System dependencies
brew install poppler tesseract tesseract-lang
```

### Ubuntu/Debian:
```bash
# Python packages
pip install pdf2image pytesseract Pillow

# System dependencies
sudo apt-get update
sudo apt-get install poppler-utils tesseract-ocr tesseract-ocr-ind
```

### Windows:
```bash
# Python packages
pip install pdf2image pytesseract Pillow

# System dependencies:
# 1. Install Poppler (see Error 2 above)
# 2. Install Tesseract (see Error 3 above)
```

---

## 📊 Cek Logs untuk Debug

Logs tersimpan di console/terminal tempat Flask berjalan. Cari:

```
ERROR - Error processing PDF: ...
INFO - Processing PDF file: ...
INFO - Successfully extracted X characters from PDF
```

Jika Anda melihat error tertentu, search error message di dokumentasi ini.

---

## 🧪 Test dengan Sample File

1. Siapkan sample PDF formulir cuti
2. Upload via OCR Cuti V2
3. Perhatikan log di terminal
4. Jika berhasil, Anda akan melihat:
   - "Successfully extracted X characters from PDF"
   - Preview dokumen muncul di modal

---

## 🆘 Masih Error?

### Debug Mode

Edit `config/ocr_cuti_v2.py` dan uncomment logging:

```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

### Cek File yang Diupload

```bash
# Lihat file yang tersimpan
ls -lah static/ocr/cuti/

# Test manual dengan file yang diupload
python -c "
from pdf2image import convert_from_path
images = convert_from_path('static/ocr/cuti/cuti_xxx.pdf')
print(f'Pages: {len(images)}')
print(f'Size: {images[0].size}')
"
```

### Test OCR Manual

```python
from PIL import Image
import pytesseract
from pdf2image import convert_from_path

# Convert PDF
images = convert_from_path('path/to/your.pdf', first_page=1, last_page=1)

# OCR
text = pytesseract.image_to_string(images[0], lang='ind')
print(text)
```

---

## 📝 Checklist Lengkap

- [ ] Python 3.7+ terinstall
- [ ] pip packages terinstall (pdf2image, pytesseract, Pillow)
- [ ] Poppler terinstall dan di PATH
- [ ] Tesseract terinstall dan di PATH
- [ ] Tesseract bahasa Indonesia terinstall
- [ ] Folder `static/ocr/cuti/` ada dan writable
- [ ] Flask app running tanpa error
- [ ] Test dependencies menunjukkan semua ✓
- [ ] Sample PDF berhasil diupload dan diproses

---

## 📚 Resources

- **pdf2image**: https://github.com/Belval/pdf2image
- **Poppler**: https://poppler.freedesktop.org/
- **Tesseract**: https://github.com/tesseract-ocr/tesseract
- **pytesseract**: https://github.com/madmaze/pytesseract

---

## 💡 Tips

1. **Restart Terminal/IDE** setelah install dependencies sistem
2. **Activate virtual environment** jika menggunakan venv
3. **Check Python version**: Gunakan Python 3.7 atau lebih baru
4. **Test step by step**: Jangan install semuanya sekaligus, test satu per satu
5. **Read error messages**: Error message biasanya menunjukkan komponen yang hilang

---

**Jika masalah masih berlanjut, hubungi tim development dengan informasi:**
- Output dari `python test_pdf_dependencies.py`
- Screenshot error message
- OS dan versi (macOS, Windows, Linux)
- Python version