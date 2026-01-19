# Update OCR Cuti V2 - Fitur Preview Dokumen

## Ringkasan Update

Fitur baru telah ditambahkan ke OCR Cuti V2 untuk menampilkan preview dokumen (PDF/JPG/PNG) yang telah diupload, baik pada halaman ekstraksi maupun pada halaman detail data cuti yang tersimpan.

## Fitur yang Ditambahkan

### 1. Penyimpanan File Upload
- File yang diupload (PDF, JPG, PNG, WEBP) sekarang disimpan ke folder `static/ocr/cuti/`
- Setiap file diberi nama unik dengan format: `cuti_YYYYMMDD_HHMMSS_xxxxxx.ext`
- Path file disimpan ke database pada kolom `pdf_path` tabel `cuti`

### 2. Preview Dokumen di Modal Ekstraksi (OCR Cuti V2)
Pada halaman OCR Cuti V2 (`/cuti-v2/ocr`), modal "Detail Ekstraksi Formulir Cuti" sekarang menampilkan:

#### Untuk File PDF:
- Preview PDF menggunakan `<iframe>` yang dapat di-scroll
- Kontrol zoom disembunyikan (PDF memiliki kontrol zoom sendiri)
- Tombol untuk membuka di tab baru dan download

#### Untuk File Image (JPG/PNG/WEBP):
- Preview gambar dengan ukuran responsif
- Kontrol zoom dan pan interaktif:
  - **Zoom In/Out**: Tombol untuk memperbesar/memperkecil
  - **Mouse Wheel**: Scroll untuk zoom
  - **Drag**: Klik dan drag untuk menggeser gambar
  - **Reset**: Kembalikan ke ukuran awal
- Indikator level zoom (100%, 150%, dll)

### 3. Preview Dokumen di Halaman List Cuti
Pada halaman list cuti (`/cuti-v2/list`), ketika mengklik tombol "Detail":

#### Modal Detail Diperluas:
- Modal size diubah ke `modal-xl` (95% lebar layar)
- Menampilkan informasi pegawai dan cuti
- **Tambahan**: Preview dokumen yang diupload (jika ada)

#### Fitur Preview:
- Dokumen PDF ditampilkan dalam iframe 500px
- Gambar ditampilkan dengan max-height 500px
- Tombol "Buka di Tab Baru" dan "Download"

## File yang Dimodifikasi

### 1. Backend - `config/ocr_cuti_v2.py`

#### Fungsi `ocr_cuti_v2()`:
```python
# Perubahan utama:
- Menyimpan file upload ke folder UPLOAD_FOLDER
- Generate nama file unik dengan timestamp dan random string
- Menyimpan relative path untuk database dan URL
- Menambahkan field 'file_path' dan 'file_type' ke extracted_data
```

#### Fungsi `save_cuti_data()`:
```python
# Perubahan:
- Menyimpan pdf_path ke database
- Field: pdf_path=item.get("file_path", None)
```

### 2. Frontend - `templates/cuti/ocr_cuti_v2.html`

#### Modal "Detail Ekstraksi Formulir Cuti":
```html
<!-- Ditambahkan: -->
- <iframe id="pdfPreview"> untuk preview PDF
- Container height dinaikkan menjadi h-96
- Text placeholder "Tidak ada dokumen"
```

#### JavaScript Functions:
```javascript
// Fungsi baru:
- updateFilePreview(data): Menampilkan PDF atau image sesuai tipe file
- resetImageZoom(): Reset zoom gambar ke default

// Fungsi diupdate:
- fillModalForm(index): Memanggil updateFilePreview()
- setupZoomAndPan(): Variable scope dipindah ke global
```

### 3. Styles - `static/assets/css/ocr_cuti.css`

```css
/* Ditambahkan: */
- Style untuk #pdfPreview (iframe PDF)
- Style untuk #noImageText
- Transisi smooth untuk switching preview
- Container improvements untuk document viewer
```

### 4. List Cuti - `static/assets/js/cuti/list-cuti.js`

#### Fungsi `generateDetailContent()`:
```javascript
// Perubahan:
- Menambahkan logika untuk generate preview dokumen
- Support PDF preview dengan iframe
- Support image preview dengan responsive sizing
- Tombol "Buka di Tab Baru" dan "Download"
```

### 5. Template - `templates/cuti/list_cuti.html`

```html
<!-- Perubahan: -->
- Modal size: modal-lg → modal-xl
- Max-width: 95% untuk tampilan lebih luas
```

## Struktur Data

### Database - Tabel `cuti`
```sql
-- Field yang digunakan:
pdf_path VARCHAR(255) NULL  -- Path relatif file (e.g., "ocr/cuti/cuti_20240115_143022_abc123.pdf")
```

### Extracted Data Object
```javascript
{
    // Data form...
    "filename": "original_name.pdf",           // Nama file asli
    "file_path": "ocr/cuti/cuti_xxx.pdf",     // Path relatif untuk DB
    "file_type": "pdf",                        // Ekstensi file: pdf, jpg, png, webp
    // ... field lainnya
}
```

## Cara Penggunaan

### 1. Upload dan Ekstraksi (OCR Cuti V2)
1. Buka halaman `/cuti-v2/ocr`
2. Upload file PDF atau gambar formulir cuti
3. Klik "Proses OCR"
4. Setelah ekstraksi selesai, klik "Lihat Data Ekstraksi"
5. Modal akan menampilkan:
   - **Kiri**: Preview dokumen dengan kontrol zoom/pan
   - **Kanan**: Form data hasil ekstraksi
6. Gunakan tombol navigasi untuk melihat multiple dokumen
7. Klik "Simpan Semua Data" untuk menyimpan ke database

### 2. Melihat Detail Cuti yang Tersimpan
1. Buka halaman `/cuti-v2/list`
2. Klik tombol "Detail" pada baris cuti
3. Modal akan menampilkan:
   - Data pegawai (nama, NIP, jabatan, dll)
   - Data cuti (jenis, tanggal, lama, dll)
   - **Preview dokumen** (jika ada file yang diupload)
4. Gunakan tombol "Buka di Tab Baru" untuk melihat full-screen
5. Gunakan tombol "Download" untuk mengunduh file

## File Structure
```
OCR-ScanLetter_WebApp/
├── config/
│   ├── ocr_cuti_v2.py          # ✅ Updated
│   └── models.py               # (sudah ada kolom pdf_path)
├── templates/
│   └── cuti/
│       ├── ocr_cuti_v2.html    # ✅ Updated
│       └── list_cuti.html      # ✅ Updated
├── static/
│   ├── ocr/
│   │   └── cuti/               # 📁 Folder penyimpanan file
│   ├── assets/
│   │   ├── css/
│   │   │   └── ocr_cuti.css    # ✅ Updated
│   │   └── js/
│   │       └── cuti/
│   │           └── list-cuti.js # ✅ Updated
└── README_OCR_CUTI_V2_UPDATE.md # 📄 Dokumentasi ini
```

## Testing Checklist

- [ ] Upload PDF dan pastikan preview muncul di modal ekstraksi
- [ ] Upload JPG/PNG dan pastikan zoom/pan berfungsi
- [ ] Test multiple file upload (preview berganti saat navigasi)
- [ ] Simpan data ke database dan cek kolom pdf_path terisi
- [ ] Buka halaman list cuti dan klik Detail
- [ ] Pastikan preview dokumen muncul di modal detail
- [ ] Test tombol "Buka di Tab Baru" dan "Download"
- [ ] Test dengan berbagai ukuran file dan resolusi

## Troubleshooting

### Preview tidak muncul
- Pastikan file tersimpan di `static/ocr/cuti/`
- Cek kolom `pdf_path` di database berisi path yang benar
- Periksa console browser untuk error
- Pastikan file accessible (permissions)

### Zoom tidak berfungsi pada gambar
- Pastikan `setupZoomAndPan()` dipanggil saat DOM ready
- Cek apakah element `#imagePreview` ada di DOM
- Periksa CSS untuk `#imagePreview` dan `#imagePreviewContainer`

### PDF tidak tampil di iframe
- Beberapa browser memblokir iframe PDF
- Gunakan tombol "Buka di Tab Baru" sebagai alternatif
- Pertimbangkan menggunakan PDF.js untuk kompatibilitas lebih baik

## Future Improvements

1. **PDF.js Integration**: Gunakan PDF.js untuk render PDF yang lebih konsisten
2. **Thumbnail Generation**: Generate thumbnail untuk preview cepat
3. **Image Compression**: Kompres gambar untuk menghemat storage
4. **Multiple Pages**: Support preview multi-page PDF dengan navigasi halaman
5. **Fullscreen Mode**: Tambah mode fullscreen untuk preview
6. **Annotation**: Tambah fitur markup/annotation pada dokumen
7. **OCR Confidence**: Tampilkan confidence score untuk setiap field yang diekstrak

## Dependencies

- **Python**: Flask, Pillow, pytesseract, pdf2image
- **JavaScript**: Native ES6+ (no additional libraries needed)
- **CSS**: Tailwind CSS (untuk beberapa utility classes)

## Notes

- File upload disimpan dengan nama unik untuk menghindari conflict
- Path disimpan secara relatif (tanpa `/static/`) untuk fleksibilitas deployment
- Preview menggunakan native browser capabilities (iframe untuk PDF, img tag untuk images)
- Zoom/pan hanya untuk images, PDF menggunakan native PDF viewer controls

## Credits

- Developed for: PA Banjarbaru
- Feature: OCR Cuti V2 - Document Preview
- Date: 2024

---

**Untuk pertanyaan atau issue, silakan hubungi tim development.**