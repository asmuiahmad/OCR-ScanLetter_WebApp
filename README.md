# OCR Scan Letter WebApp

A Flask-based web application for managing incoming and outgoing letters with OCR (Optical Character Recognition) features to extract text from scanned letter images.

## Main Features

- **OCR Processing**: Extract text from scanned letter images
- **Incoming Letter Management**: Input, edit, and view incoming letters
- **Outgoing Letter Management**: Input, edit, and view outgoing letters with supervisor approval
- **Authentication System**: Login with admin and supervisor roles
- **Dashboard**: Statistics and letter reports
- **Document Generation**: Automatic leave letter generation

## System Requirements

### Required Software
- Python 3.8 or newer
- pip (Python package installer)
- Tesseract OCR Engine

### Installing Tesseract OCR

#### macOS (using Homebrew)
```bash
brew install tesseract
brew install tesseract-lang  # For Indonesian language
```

#### Ubuntu/Debian
```bash
sudo apt update
sudo apt install tesseract-ocr
sudo apt install tesseract-ocr-ind  # For Indonesian language
```

#### Windows
1. Download installer from [GitHub Tesseract](https://github.com/UB-Mannheim/tesseract/wiki)
2. Install and ensure it's added to PATH
3. Download Indonesian language data from [tessdata](https://github.com/tesseract-ocr/tessdata)

## Application Installation

### 1. Clone Repository
```bash
git clone <repository-url>
cd OCR-ScanLetter_WebApp
```

### 2. Create Virtual Environment
```bash
# Create virtual environment
python -m venv venv

# Activate virtual environment
# macOS/Linux:
source venv/bin/activate
# Windows:
venv\Scripts\activate
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Setup Environment Variables (Optional)
Create a `.env` file in the root directory:
```env
FLASK_APP=app.py
FLASK_ENV=development
SECRET_KEY=your-secret-key-here
DATABASE_URL=sqlite:///instance/app.db
```

### 5. Initialize Database
```bash
# Run the application to create database
python app.py
```

### 6. Run Application
```bash
python app.py
```

The application will run at `http://localhost:5001`

## Database Structure

### User Table
- `id`: Primary key
- `username`: Username for login
- `email`: User email
- `password_hash`: Hashed password
- `role`: User role (admin/supervisor)
- `is_approved`: User approval status
- `created_at`: Creation timestamp

### IncomingLetter Table
- `id_suratKeluar`: Primary key
- `tanggal_suratKeluar`: Letter date
- `pengirim_suratKeluar`: Letter sender
- `penerima_suratKeluar`: Letter recipient
- `nomor_suratKeluar`: Letter number
- `kode_suratKeluar`: Letter code
- `jenis_suratKeluar`: Letter type
- `isi_suratKeluar`: Letter content
- `gambar_suratKeluar`: Letter image file
- `status_suratKeluar`: Letter status (approved)
- `created_at`: Creation timestamp

### OutgoingLetter Table
- `id_suratMasuk`: Primary key
- `tanggal_suratMasuk`: Letter date
- `pengirim_suratMasuk`: Letter sender
- `penerima_suratMasuk`: Letter recipient
- `nomor_suratMasuk`: Letter number
- `kode_suratMasuk`: Letter code
- `jenis_suratMasuk`: Letter type
- `isi_suratMasuk`: Letter content
- `file_suratMasuk`: Letter file
- `status_suratMasuk`: Letter status (pending/approved/rejected)
- `created_at`: Creation timestamp

## Usage

### 1. Login
- Access `http://localhost:5001`
- Login with username and password
- Roles: admin or supervisor

### 2. Input Incoming Letter
- Menu: "Input Surat Masuk"
- Upload letter image
- Fill letter data form
- Letter automatically gets "Approved" status

### 3. Input Outgoing Letter
- Menu: "Input Surat Keluar"
- Upload letter file
- Fill letter data form
- Letter gets "Pending" status awaiting supervisor approval

### 4. Letter Approval (Supervisor Role)
- Menu: "Persetujuan Surat" → "Surat Keluar Pending"
- View list of pending outgoing letters
- Click "Approve" or "Reject"

### 5. OCR Processing
- Menu: "OCR Surat Masuk" or "OCR Surat Keluar"
- Upload letter image
- System will automatically extract text
- Edit extraction results if needed

### 6. Reports and Statistics
- Menu: "Laporan Statistik"
- View charts and letter statistics

## Troubleshooting

### Error "No module named 'cv2'"
- Application uses PIL (Pillow) instead of OpenCV
- Ensure Pillow is installed: `pip install Pillow`

### Error Tesseract not found
- Ensure Tesseract OCR is installed
- Set environment variable `TESSDATA_PREFIX` if needed
- For Windows, ensure Tesseract is in PATH

### Database Error
- Delete `instance/app.db` file if exists
- Restart application to create new database

### Permission Error
- Ensure `static/ocr/uploads` folder has write permission
- Create folder if it doesn't exist

## Main Dependencies

### Flask Framework
- `Flask==3.1.0`: Web framework
- `Flask-Login==0.6.3`: User session management
- `Flask-SQLAlchemy==3.1.1`: Database ORM
- `Flask-WTF==1.2.2`: Form handling

### OCR and Image Processing
- `Pillow==11.1.0`: Image processing
- `pytesseract==0.3.13`: OCR engine wrapper

### Document Processing
- `python-docx==1.2.0`: Word document processing
- `docx-mailmerge2==0.9.0`: Mail merge functionality

### Database
- `SQLAlchemy==2.0.37`: Database ORM
- `alembic==1.14.1`: Database migrations

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## License

Distributed under the MIT License. See `LICENSE` for more information.

## Contact

Project Link: [https://github.com/asmuiahmad/OCR-ScanLetter_WebApp.git](https://github.com/asmuiahmad/OCR-ScanLetter_WebApp.git)
