# Troubleshooting File Upload - Surat Masuk

## 🔍 Masalah: File tidak tersimpan ke database

Jika file PDF/JPG/PNG tidak tersimpan setelah submit form Input Surat Masuk, ikuti langkah-langkah berikut:

---

## ✅ Langkah 1: Cek Form HTML

Pastikan form memiliki atribut `enctype="multipart/form-data"`:

```html
<form method="POST" enctype="multipart/form-data">
```

**File:** `templates/surat_masuk/input_surat_masuk.html`

✅ **Sudah diperbaiki** - Form sudah memiliki enctype yang benar.

---

## ✅ Langkah 2: Cek JavaScript

Pastikan JavaScript tidak menggunakan AJAX/fetch yang tidak mengirim FormData dengan benar.

**File:** `templates/surat_masuk/input_surat_masuk.html` (inline script)

**Yang Harus Dihindari:**
```javascript
// ❌ JANGAN GUNAKAN fetch dengan JSON
fetch('/input_surat_masuk', {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify(data) // File tidak bisa di-stringify
});
```

**Yang Benar:**
```javascript
// ✅ GUNAKAN form submit biasa (sudah diperbaiki)
// Atau gunakan FormData jika pakai AJAX
const formData = new FormData(form);
fetch('/input_surat_masuk', {
    method: 'POST',
    body: formData // Jangan set Content-Type, biarkan browser yang set
});
```

✅ **Sudah diperbaiki** - Form menggunakan submit biasa, tidak pakai AJAX.

---

## ✅ Langkah 3: Cek Backend Handler

File: `config/surat_masuk_routes.py`

Pastikan route handler membaca dan menyimpan file:

```python
if form.lampiran_suratMasuk.data:
    file = form.lampiran_suratMasuk.data
    file_data = file.read()  # Baca file
    
new_surat_masuk = SuratMasuk(
    # ... field lainnya
    file_suratMasuk=file_data,  # Simpan ke database
)
```

✅ **Sudah diperbaiki** - Backend sudah menangani upload file dengan logging detail.

---

## 🧪 Langkah 4: Test Upload

### Test Manual:

1. **Jalankan aplikasi:**
   ```bash
   python app.py
   ```

2. **Buka halaman Input Surat Masuk:**
   ```
   http://127.0.0.1:5000/surat-masuk/input_surat_masuk
   ```

3. **Upload file dengan cara:**
   - **Drag & Drop:** Drag file dari file explorer ke area upload
   - **Click:** Klik area "Drag & Drop atau Klik untuk Upload"

4. **Perhatikan:**
   - ✅ Nama file muncul setelah dipilih?
   - ✅ Ukuran file ditampilkan?
   - ✅ Icon check circle hijau muncul?

5. **Submit form dan cek:**
   - ✅ Flash message muncul?
   - ✅ Redirect ke halaman show_surat_masuk?

---

## 🔎 Langkah 5: Cek Database

### Menggunakan Script Python:

```bash
# Cek surat masuk terakhir
python check_file_upload.py

# Cek semua surat masuk
python check_file_upload.py --all

# Export file dari database (surat ID 5)
python check_file_upload.py --export 5
```

### Menggunakan SQLite Browser:

1. Install [DB Browser for SQLite](https://sqlitebrowser.org/)
2. Buka file: `instance/app.db`
3. Browse tabel `surat_masuk`
4. Cek kolom `file_suratMasuk`
   - Jika ada data BLOB → File tersimpan ✅
   - Jika NULL → File tidak tersimpan ❌

### Menggunakan Python Console:

```python
from app import create_app
from config.models import SuratMasuk

app = create_app()
with app.app_context():
    latest = SuratMasuk.query.order_by(SuratMasuk.created_at.desc()).first()
    
    if latest.file_suratMasuk:
        print(f"✅ File tersimpan: {len(latest.file_suratMasuk)} bytes")
    else:
        print("❌ File tidak tersimpan")
```

---

## 📋 Langkah 6: Cek Log Aplikasi

Cek terminal/console saat submit form. Cari log seperti:

```
=== POST REQUEST DEBUG ===
Form data keys: ['csrf_token', 'pengirim_suratMasuk', 'nomor_suratMasuk', ...]
Files in request: ['lampiran_suratMasuk']
File detected: contoh.pdf
File content type: application/pdf
File from form: contoh.pdf
File uploaded successfully: contoh.pdf, size: 245678 bytes
Surat Masuk saved with ID: 123
File saved to DB: True
Verified: File saved in DB (239.92 KB)
```

### Jika Tidak Ada File:

```
Files in request: []
No file found in request.files
No file uploaded (optional field)
File saved to DB: False
Verified: No file in DB
```

**Kemungkinan penyebab:**
- File tidak dipilih
- JavaScript error mencegah file masuk ke FormData
- Browser compatibility issue

---

## 🐛 Troubleshooting Common Issues

### Issue 1: File Input Tidak Muncul

**Gejala:** Input file tidak terlihat di form

**Solusi:**
```html
<!-- Pastikan input ada dan tidak hidden dengan CSS yang salah -->
<input type="file" 
       name="lampiran_suratMasuk" 
       id="lampiran_suratMasuk" 
       style="display:none;">  <!-- OK: disembunyikan karena pakai custom UI -->
```

---

### Issue 2: File Terlalu Besar

**Gejala:** Upload file besar gagal tanpa error

**Solusi:** Tambahkan config di `app.py`:

```python
# Maksimal 16 MB
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024
```

---

### Issue 3: Form Validation Error

**Gejala:** Form tidak submit, ada error validation

**Cek log:**
```
Form validation errors: {'lampiran_suratMasuk': ['Image/PDF only!']}
```

**Solusi:** Sudah diperbaiki - Validator `FileAllowed` sudah dihapus di `config/forms.py`.

Sekarang form menggunakan custom validation di route handler yang lebih fleksibel.

---

### Issue 4: CSRF Token Error

**Gejala:** Error "CSRF token missing or invalid"

**Solusi:**
```html
<!-- Pastikan CSRF token ada di form -->
{{ form.csrf_token()|safe }}
```

---

### Issue 5: JavaScript DataTransfer Error

**Gejala:** Drag & drop tidak work di beberapa browser

**Solusi:** Sudah diperbaiki dengan menggunakan `DataTransfer` API:

```javascript
const dataTransfer = new DataTransfer();
dataTransfer.items.add(files[0]);
fileInput.files = dataTransfer.files;
```

**Browser Support:**
- ✅ Chrome/Chromium 60+
- ✅ Firefox 52+
- ✅ Edge 79+
- ✅ Safari 14+

---

## 📊 Format File yang Didukung

| Format | Extension | MIME Type | Status |
|--------|-----------|-----------|--------|
| JPEG | .jpg, .jpeg | image/jpeg | ✅ Supported |
| PNG | .png | image/png | ✅ Supported |
| PDF | .pdf | application/pdf | ✅ Supported |

---

## 🔒 Security Notes

1. **Validasi Format:** Custom validation di backend memastikan hanya format yang diizinkan
2. **CSRF Protection:** Form dilindungi CSRF token
3. **Role-Based Access:** Hanya admin dan pimpinan bisa upload
4. **File Size:** Perhatikan ukuran maksimal (default: tidak dibatasi, bisa ditambahkan)

---

## 🎯 Quick Test Checklist

```
□ Form memiliki enctype="multipart/form-data"
□ Input file ada dan memiliki name="lampiran_suratMasuk"
□ JavaScript drag & drop berfungsi
□ Click to upload berfungsi
□ Nama file muncul setelah dipilih
□ Submit form berhasil
□ Flash message muncul
□ Redirect ke show_surat_masuk
□ File tersimpan di database (cek dengan script)
□ Log menunjukkan "File saved to DB: True"
```

---

## 🚀 Testing Script

Gunakan script berikut untuk test cepat:

```bash
# 1. Cek latest upload
python check_file_upload.py

# 2. Jika file ada, export untuk verifikasi
python check_file_upload.py --export <ID>

# 3. Buka file yang diexport untuk memastikan tidak corrupt
open exported_files/surat_*.pdf
```

---

## 📞 Debug Mode

Untuk debugging lebih detail, aktifkan debug mode di `app.py`:

```python
if __name__ == "__main__":
    app.run(debug=True, port=5000)
```

Ini akan menampilkan:
- Stack trace lengkap untuk error
- Auto-reload saat file berubah
- Debug toolbar (jika diinstall)

---

## ✅ Verification Steps

Setelah upload file, verifikasi dengan langkah berikut:

1. **Cek flash message:**
   ```
   "Surat Masuk berhasil ditambahkan dengan lampiran (XX.XX KB)!"
   ```

2. **Cek log:**
   ```
   File uploaded successfully: test.pdf, size: 245678 bytes
   Verified: File saved in DB (239.92 KB)
   ```

3. **Cek database:**
   ```bash
   python check_file_upload.py
   ```
   
   Output harus:
   ```
   📎 File Lampiran: ✅ TERSIMPAN
      Size: 245,678 bytes
      Size: 239.92 KB
      Detected Type: PDF Document
   ```

4. **Export dan buka file:**
   ```bash
   python check_file_upload.py --export 1
   open exported_files/surat_1_*.pdf
   ```

---

## 🎉 Jika Semua Sudah Benar

Jika semua langkah di atas sudah dilakukan dan file masih tidak tersimpan:

1. **Restart aplikasi:**
   ```bash
   # Stop aplikasi (Ctrl+C)
   python app.py
   ```

2. **Clear browser cache:**
   - Chrome: Ctrl+Shift+Delete
   - Firefox: Ctrl+Shift+Delete
   - Safari: Cmd+Option+E

3. **Test dengan browser berbeda:**
   - Chrome
   - Firefox
   - Edge

4. **Cek permission database:**
   ```bash
   ls -la instance/app.db
   # Pastikan file writable
   ```

5. **Backup dan recreate database:**
   ```bash
   cp instance/app.db instance/app.db.backup
   rm instance/app.db
   python app.py  # Database akan recreate otomatis
   ```

---

## 📝 Log File Locations

Default log locations:
- **Console/Terminal:** Stdout (langsung di terminal)
- **Flask Debug:** Enabled saat `debug=True`
- **Application Log:** Custom logger di setiap route

Untuk save log ke file, tambahkan di `app.py`:

```python
import logging

logging.basicConfig(
    filename='app.log',
    level=logging.DEBUG,
    format='%(asctime)s %(levelname)s: %(message)s'
)
```

---

## 🔗 Related Files

- `config/surat_masuk_routes.py` - Backend route handler
- `config/forms.py` - Form definition
- `config/models.py` - Database model
- `templates/surat_masuk/input_surat_masuk.html` - Frontend template
- `check_file_upload.py` - Database checking script
- `DRAG_DROP_UPLOAD_FIX.md` - Detailed fix documentation

---

## 📚 Additional Resources

- [Flask File Uploads](https://flask.palletsprojects.com/en/2.3.x/patterns/fileuploads/)
- [WTForms FileField](https://wtforms.readthedocs.io/en/3.0.x/fields/#wtforms.fields.FileField)
- [HTML5 Drag and Drop](https://developer.mozilla.org/en-US/docs/Web/API/HTML_Drag_and_Drop_API)
- [SQLAlchemy LargeBinary](https://docs.sqlalchemy.org/en/14/core/type_basics.html#sqlalchemy.types.LargeBinary)

---

**Last Updated:** 2024  
**Status:** ✅ RESOLVED - File upload berfungsi dengan baik