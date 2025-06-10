# 🧾 OCR Surat Masuk & Surat Keluar

This is a Flask-based web app that uses Tesseract OCR to extract and process text from incoming and outgoing letters. It supports keyword search, statistical charts, and form correction before saving data.

## 🚀 Features
- Image-to-text extraction using Tesseract
- Real-time dashboard with charts (daily/monthly)
- Manual review and edit before saving OCR results
- Keyword filtering and search
- Separate modules for Surat Masuk and Surat Keluar

## 📸 Screenshot
![Dashboard Preview](screenshots/dashboard.png)

## 🛠 Tech Stack
- Python, Flask, Tesseract OCR
- HTML, JavaScript (Chart.js)
- SQLite / MySQL (depending on config)

## 🔧 Installation
```bash
git clone https://github.com/your-username/your-project.git
cd your-project
pip install -r requirements.txt
python app.py
