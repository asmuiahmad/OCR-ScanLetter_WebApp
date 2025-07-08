# Quick Start Guide - OCR Scan Letter WebApp

## 🚀 Instalasi Cepat

### Prerequisites
- Python 3.8+
- Tesseract OCR Engine
- pip (Python package installer)

### 1. Install Tesseract OCR

#### macOS
```bash
brew install tesseract tesseract-lang
```

#### Ubuntu/Debian
```bash
sudo apt update
sudo apt install tesseract-ocr tesseract-ocr-ind
```

#### Windows
1. Download dari [GitHub Tesseract](https://github.com/UB-Mannheim/tesseract/wiki)
2. Install dan tambahkan ke PATH
3. Download data bahasa Indonesia dari [tessdata](https://github.com/tesseract-ocr/tessdata)

### 2. Clone dan Setup

```bash
# Clone repository
git clone <repository-url>
cd OCR-ScanLetter_WebApp

# Buat virtual environment
python -m venv venv

# Aktifkan virtual environment
# macOS/Linux:
source venv/bin/activate
# Windows:
venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 3. Jalankan Aplikasi

```bash
python app.py
```

Aplikasi akan berjalan di `http://localhost:5001`

## 📋 Dependencies Lengkap

### Flask Framework
```
Flask==3.1.0
Flask-Login==0.6.3
Flask-Migrate==4.1.0
Flask-SQLAlchemy==3.1.1
Flask-WTF==1.2.2
Werkzeug==3.1.3
```

### Database
```
SQLAlchemy==2.0.37
alembic==1.14.1
greenlet==3.1.1
```

### OCR dan Image Processing
```
Pillow==11.1.0
pytesseract==0.3.13
```

### Document Processing
```
python-docx==1.2.0
docx-mailmerge2==0.9.0
lxml==6.0.0
```

### Utilities
```
click==8.1.8
dnspython==2.7.0
email_validator==2.2.0
python-dotenv==1.0.1
```

## 🔧 Script Instalasi Otomatis

### Linux/macOS
```bash
chmod +x install.sh
./install.sh
```

### Windows
```cmd
install.bat
```

## 🐛 Troubleshooting

### Error "No module named 'cv2'"
- Aplikasi menggunakan PIL (Pillow) bukan OpenCV
- Pastikan Pillow terinstall: `pip install Pillow`

### Error Tesseract tidak ditemukan
- Pastikan Tesseract OCR terinstall
- Set environment variable `TESSDATA_PREFIX` jika diperlukan
- Untuk Windows, pastikan Tesseract ada di PATH

### Error Database
- Hapus file `instance/app.db` jika ada
- Jalankan ulang aplikasi untuk membuat database baru

### Error Permission
- Pastikan folder `static/ocr/uploads` memiliki permission write
- Buat folder jika belum ada

## 📖 Dokumentasi Lengkap

Lihat [README.md](README.md) untuk dokumentasi lengkap aplikasi.

## 🆘 Bantuan

Jika mengalami masalah, periksa:
1. Versi Python (harus 3.8+)
2. Tesseract OCR terinstall dan ada di PATH
3. Semua dependencies terinstall dengan benar
4. Virtual environment aktif 