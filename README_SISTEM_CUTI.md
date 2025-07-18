# Sistem Persetujuan Cuti dengan Tanda Tangan Digital

## 📋 Deskripsi
Sistem ini menambahkan fitur persetujuan cuti otomatis dengan tanda tangan digital menggunakan QR code. Setelah pimpinan menyetujui permohonan cuti, sistem akan otomatis:
- Membuat QR code digital signature
- Generate PDF surat persetujuan cuti
- Menyimpan hash signature untuk verifikasi

## 🚀 Instalasi

### 1. Install Dependencies
```bash
pip install qrcode==8.0 reportlab==4.2.5 pdf2image==1.17.0
```

### 2. Jalankan Script Instalasi
```bash
python install_cuti_system.py
```

### 3. Manual Installation (Alternatif)
```bash
# Install dependencies
pip install -r requirements.txt

# Buat direktori yang diperlukan
mkdir -p static/signatures static/pdf_cuti static/qr_codes

# Jalankan aplikasi
python app.py
```

## 🎯 Fitur Utama

### 1. Input Permohonan Cuti
- **URL**: `/cuti/`
- **Akses**: Semua user yang login
- **Fitur**:
  - Upload formulir cuti (JPG, PNG, PDF)
  - OCR otomatis untuk ekstraksi data
  - Input manual data cuti
  - Validasi form

### 2. Daftar Permohonan Cuti
- **URL**: `/cuti/list`
- **Akses**: Semua user yang login
- **Fitur**:
  - Lihat semua permohonan cuti
  - Filter berdasarkan status
  - Detail permohonan cuti

### 3. Persetujuan Cuti (Pimpinan/Admin)
- **URL**: `/cuti/approve/<id>`
- **Akses**: Pimpinan dan Admin
- **Fitur**:
  - Approve permohonan cuti
  - Reject permohonan cuti
  - Tambah catatan persetujuan
  - **Otomatis generate QR code dan PDF**

### 4. Download PDF Surat Persetujuan
- **URL**: `/cuti/download_pdf/<id>`
- **Akses**: User yang bersangkutan, Pimpinan, Admin
- **Fitur**:
  - Download PDF surat persetujuan
  - PDF berisi QR code digital signature
  - Format resmi dengan kop surat

### 5. Verifikasi Digital Signature
- **URL**: `/cuti/verify/<hash>`
- **Akses**: Public (tidak perlu login)
- **Fitur**:
  - Verifikasi keaslian surat persetujuan
  - Tampilkan detail cuti yang disetujui
  - Validasi hash signature

## 🔐 Sistem Tanda Tangan Digital

### Cara Kerja
1. **Generate Hash**: Sistem membuat hash unik berdasarkan data cuti + approver + timestamp
2. **Create QR Code**: QR code berisi informasi verifikasi dan URL verifikasi
3. **PDF Generation**: PDF dibuat dengan QR code tertanam
4. **Database Storage**: Hash signature disimpan di database untuk verifikasi

### Komponen QR Code
```
PERSETUJUAN CUTI
ID: [id_cuti]
Nama: [nama_pegawai]
NIP: [nip]
Jenis: [jenis_cuti]
Periode: [tanggal_mulai] s/d [tanggal_selesai]
Disetujui oleh: [nama_pimpinan]
Tanggal Persetujuan: [timestamp]
Hash: [signature_hash]
Verifikasi: [verification_url]
```

## 👥 Role dan Akses

### Karyawan
- ✅ Input permohonan cuti baru
- ✅ Lihat status permohonan cuti sendiri
- ✅ Download PDF jika sudah disetujui
- ❌ Tidak bisa approve/reject cuti

### Pimpinan/Admin
- ✅ Semua akses karyawan
- ✅ Lihat semua permohonan cuti
- ✅ Approve/reject permohonan cuti
- ✅ Generate tanda tangan digital otomatis
- ✅ Download semua PDF surat persetujuan

## 📱 Cara Penggunaan

### Untuk Karyawan:
1. Login ke sistem
2. Pilih menu **"Manajemen Cuti"** > **"Input Cuti Baru"**
3. Upload formulir cuti atau input manual
4. Klik **"Proses Dokumen"** untuk OCR (jika upload)
5. Periksa data hasil ekstraksi
6. Klik **"Simpan ke Database"**
7. Cek status di **"Daftar Permohonan Cuti"**

### Untuk Pimpinan:
1. Login sebagai pimpinan/admin
2. Pilih menu **"Manajemen Cuti"** > **"Daftar Permohonan Cuti"**
3. Klik **"Setujui"** atau **"Tolak"** pada permohonan
4. Tambahkan catatan jika diperlukan
5. **Sistem otomatis generate QR code dan PDF**
6. Download PDF dari tombol **"PDF"**

### Verifikasi Digital Signature:
1. Scan QR code pada surat persetujuan
2. Atau buka URL: `/cuti/verify/<hash>`
3. Sistem akan menampilkan status verifikasi
4. Jika valid, detail cuti akan ditampilkan

## 🗂️ Struktur File

```
├── config/
│   ├── digital_signature.py     # Sistem tanda tangan digital
│   ├── ocr_cuti.py             # Route dan logic cuti
│   └── models.py               # Model database (updated)
├── templates/home/
│   ├── list_cuti.html          # Daftar permohonan cuti
│   ├── verify_signature.html   # Halaman verifikasi
│   └── ocr_cuti.html          # Input cuti (existing)
├── static/
│   ├── signatures/             # QR code files
│   ├── pdf_cuti/              # PDF surat persetujuan
│   └── qr_codes/              # QR code backup
└── install_cuti_system.py      # Script instalasi
```

## 🔧 Konfigurasi

### Environment Variables (Opsional)
```bash
# .env
SIGNATURE_SECRET_KEY=your-secret-key-for-signature
PDF_TEMPLATE_PATH=templates/pdf/
QR_CODE_SIZE=200
```

### Database Schema
Tabel `cuti` ditambahkan kolom:
- `qr_code`: TEXT - Hash signature untuk QR code
- `pdf_path`: TEXT - Path file PDF surat persetujuan  
- `docx_path`: TEXT - Path file DOCX (future use)

## 🐛 Troubleshooting

### Error: "pdf2image not installed"
```bash
pip install pdf2image
# Untuk Ubuntu/Debian:
sudo apt-get install poppler-utils
# Untuk macOS:
brew install poppler
```

### Error: "QR code generation failed"
```bash
pip install qrcode[pil]
```

### Error: "Permission denied" saat create PDF
```bash
chmod 755 static/pdf_cuti/
chmod 755 static/signatures/
```

### Database Error
```bash
# Reset database jika perlu
python reset_database.py
python install_cuti_system.py
```

## 📊 Monitoring dan Log

### Log Files
- Approval actions logged ke console
- PDF generation status
- QR code creation status
- Verification attempts

### Metrics
- Total permohonan cuti per bulan
- Approval rate
- Average processing time
- Digital signature verification count

## 🔒 Keamanan

### Digital Signature Security
- Hash menggunakan SHA-256
- Timestamp untuk prevent replay attacks
- Unique hash per approval
- Database validation untuk verifikasi

### Access Control
- Role-based access control
- CSRF protection
- Session management
- File access validation

## 🚀 Future Enhancements

### Planned Features
- [ ] Email notification saat approval
- [ ] Mobile app untuk scan QR code
- [ ] Bulk approval untuk multiple cuti
- [ ] Integration dengan sistem payroll
- [ ] Advanced reporting dashboard
- [ ] API endpoints untuk integration

### Technical Improvements
- [ ] Async PDF generation
- [ ] Cloud storage untuk PDF files
- [ ] Advanced OCR dengan AI
- [ ] Multi-language support
- [ ] Audit trail lengkap

## 📞 Support

Jika mengalami masalah:
1. Cek log error di console
2. Pastikan semua dependencies terinstall
3. Verifikasi permission direktori
4. Cek database connection
5. Test dengan data sample

## 📄 License

Sistem ini menggunakan lisensi yang sama dengan aplikasi utama.

---

**Dibuat untuk Pengadilan Agama Watampone**  
*Sistem Manajemen Surat dengan Digital Signature*