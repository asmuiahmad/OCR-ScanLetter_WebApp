# Troubleshooting: Daftar Permohonan Cuti Tidak Bisa Diakses

## Deskripsi Masalah
Halaman "Daftar Permohonan Cuti" tidak dapat diakses oleh pengguna yang sudah login.

## URL yang Bermasalah
- `/cuti-v2/list` - Halaman daftar permohonan cuti

## Penyebab Umum dan Solusi

### 1. User Belum Login
**Gejala:**
- Redirect otomatis ke halaman login
- URL berubah menjadi `/login?next=http://localhost:5000/cuti-v2/list`

**Solusi:**
1. Pastikan Anda sudah login dengan akun yang valid
2. Gunakan salah satu akun berikut:
   - Email: `admin@admin.com`, Password: `admin123`
   - Email: `pimpinan@suratapp.com`, Password: `pimpinan123`

**Cara Verifikasi:**
```bash
# Cek status login di browser console
console.log(document.cookie);
```

---

### 2. Session Timeout
**Gejala:**
- Sudah login sebelumnya, tapi sekarang tidak bisa akses
- Redirect ke login meskipun merasa masih login

**Solusi:**
1. Session default expire setelah 30 menit tidak aktif
2. Login ulang untuk mendapatkan session baru
3. Centang "Remember Me" saat login untuk session lebih lama

**Cara Memperpanjang Session:**
Edit `app.py` baris 40:
```python
app.config["PERMANENT_SESSION_LIFETIME"] = timedelta(hours=2)  # Ubah dari 30 menit ke 2 jam
```

---

### 3. CSRF Token Error
**Gejala:**
- Error 400 Bad Request
- Pesan: "The CSRF token is missing"

**Solusi:**
1. Clear browser cookies dan cache
2. Reload halaman dengan Ctrl+F5 (force refresh)
3. Pastikan JavaScript enabled di browser

**Cara Verifikasi CSRF Token:**
```bash
# Jalankan di terminal
python -c "
from app import app
with app.test_client() as client:
    response = client.get('/')
    print('CSRF Token in cookies:', response.headers.get('Set-Cookie'))
"
```

---

### 4. Database Connection Error
**Gejala:**
- Error 500 Internal Server Error
- Log error: "Database connection failed" atau "No such table: cuti"

**Solusi:**
1. Cek apakah database ada:
```bash
ls -la instance/app.db
```

2. Jika tidak ada, inisialisasi database:
```bash
python -c "from app import app, db; app.app_context().push(); db.create_all()"
```

3. Cek struktur tabel:
```bash
sqlite3 instance/app.db ".schema cuti"
```

---

### 5. Template Rendering Error
**Gejala:**
- Halaman blank/kosong
- Error di browser console
- Status code 200 tapi tidak ada konten

**Solusi:**
1. Cek apakah template file ada:
```bash
ls -la templates/cuti/list_cuti.html
```

2. Cek CSS file:
```bash
ls -la static/assets/css/cuti.css
```

3. Cek error di browser console (F12 -> Console tab)

4. Cek server log untuk error rendering:
```bash
# Di terminal tempat Flask running
# Lihat output untuk "Error in list_cuti_v2"
```

---

### 6. Route Tidak Terdaftar
**Gejala:**
- Error 404 Not Found
- "The requested URL was not found on the server"

**Solusi:**
1. Verifikasi route terdaftar:
```bash
python -c "
from app import app
with app.app_context():
    with app.test_request_context():
        from flask import url_for
        print(url_for('ocr_cuti_v2.list_cuti_v2'))
"
```

2. Jika route tidak ada, pastikan blueprint terdaftar di `app.py`:
```python
app.register_blueprint(ocr_cuti_v2_bp, url_prefix="/cuti-v2")
```

3. Restart Flask server setelah perubahan kode

---

### 7. Permission/Role Issue
**Gejala:**
- Redirect ke login meskipun sudah login
- Error "Unauthorized" atau "Forbidden"

**Catatan Penting:**
- Route `/cuti-v2/list` **TIDAK** memerlukan role khusus
- Semua user yang login (admin, pimpinan, staff) bisa akses
- Jika tetap tidak bisa akses, cek role user:

```bash
python -c "
from app import app
from config.models import User
with app.app_context():
    user = User.query.filter_by(email='EMAIL_ANDA').first()
    if user:
        print(f'Email: {user.email}')
        print(f'Role: {user.role}')
        print(f'Active: {user.is_active}')
    else:
        print('User tidak ditemukan')
"
```

---

## Testing & Debugging

### Test 1: Cek Route Availability
```bash
cd /path/to/OCR-ScanLetter_WebApp
python test_list_cuti_access.py
```

### Test 2: Cek Data Cuti
```bash
python -c "
from app import app
from config.models import Cuti
with app.app_context():
    count = Cuti.query.count()
    print(f'Total cuti records: {count}')
    if count > 0:
        sample = Cuti.query.first()
        print(f'Sample: {sample.nama} - {sample.status_cuti}')
"
```

### Test 3: Manual Access Test
1. Buka browser
2. Buka Developer Tools (F12)
3. Login ke aplikasi
4. Buka tab Network
5. Akses `http://localhost:5000/cuti-v2/list`
6. Cek response:
   - Status 200 = OK
   - Status 302 = Redirect (cek Location header)
   - Status 403 = Permission denied
   - Status 500 = Server error

### Test 4: Cek Log Server
Tambahkan logging di `config/ocr_cuti_v2.py` sudah ditingkatkan. Untuk melihat log:

```bash
# Saat menjalankan Flask
python app.py

# Output log akan muncul seperti:
INFO:config.ocr_cuti_v2:list_cuti_v2 accessed by user: admin@admin.com (role: admin)
INFO:config.ocr_cuti_v2:Retrieved 161 cuti records
INFO:config.ocr_cuti_v2:Rendering list_cuti.html template
```

---

## Quick Fix Checklist

Jika halaman tidak bisa diakses, coba langkah-langkah berikut secara berurutan:

- [ ] **Langkah 1:** Logout dan login ulang
- [ ] **Langkah 2:** Clear browser cache (Ctrl+Shift+Del)
- [ ] **Langkah 3:** Coba browser lain atau mode incognito
- [ ] **Langkah 4:** Restart Flask server (Ctrl+C, lalu `python app.py`)
- [ ] **Langkah 5:** Cek log server untuk error message
- [ ] **Langkah 6:** Verifikasi database dengan query manual
- [ ] **Langkah 7:** Test dengan script `test_list_cuti_access.py`
- [ ] **Langkah 8:** Cek file permissions untuk templates dan static files

---

## Solusi Darurat

Jika semua cara di atas gagal, gunakan route alternatif:

### Route Alternatif 1: `/cuti/list-cuti`
Route lama dari `cuti_routes.py` yang masih aktif:
```
http://localhost:5000/cuti/list-cuti
```

### Route Alternatif 2: Direct Database Query
Buat endpoint debug temporary di `config/ocr_cuti_v2.py`:

```python
@ocr_cuti_v2_bp.route("/debug-list", methods=["GET"])
@login_required
def debug_list_cuti():
    """Endpoint debug untuk troubleshooting"""
    from flask import jsonify
    cuti_list = Cuti.query.all()
    return jsonify({
        'total': len(cuti_list),
        'sample': [
            {
                'id': c.id_cuti,
                'nama': c.nama,
                'status': c.status_cuti
            } for c in cuti_list[:5]
        ]
    })
```

Akses via: `http://localhost:5000/cuti-v2/debug-list`

---

## Kontak Support

Jika masalah masih berlanjut setelah mencoba semua solusi di atas:

1. **Kumpulkan informasi berikut:**
   - Browser dan versi (Chrome 120, Firefox 121, dll)
   - Error message lengkap dari browser console
   - Error message dari Flask log
   - Screenshot halaman error
   - Output dari `test_list_cuti_access.py`

2. **Buat issue report dengan format:**
   ```
   **Environment:**
   - OS: [macOS/Windows/Linux]
   - Python version: [3.x.x]
   - Flask version: [x.x.x]
   
   **Steps to reproduce:**
   1. Login sebagai [role]
   2. Akses URL [URL]
   3. Error muncul: [deskripsi]
   
   **Expected behavior:**
   Halaman daftar cuti muncul dengan data
   
   **Actual behavior:**
   [Apa yang terjadi]
   
   **Logs/Screenshots:**
   [Paste log atau attach screenshot]
   ```

---

## Perubahan Terbaru

### Update 2024-01-22
- ✅ Menambahkan logging lebih detail di `list_cuti_v2()`
- ✅ Memperbaiki error handling untuk kasus edge case
- ✅ Menambahkan fallback rendering saat error
- ✅ Membuat script test `test_list_cuti_access.py`

### Known Issues
- Test client Flask-Login session tidak persist (normal behavior untuk test)
- CSRF token warning saat POST tanpa token (by design)

---

## Best Practices

### Untuk Development:
1. Selalu cek log saat ada error
2. Gunakan mode debug: `app.run(debug=True)`
3. Enable verbose logging di `app.py`:
   ```python
   logging.basicConfig(level=logging.DEBUG)
   ```

### Untuk Production:
1. Set `debug=False`
2. Set `SECRET_KEY` yang kuat
3. Gunakan HTTPS untuk session security
4. Set session timeout sesuai kebutuhan
5. Monitor log file secara berkala

---

## Related Documentation
- `README.md` - Setup instruksi umum
- `TROUBLESHOOTING_FILE_UPLOAD.md` - File upload issues
- `TROUBLESHOOTING_MODAL.md` - Modal/UI issues
- `USER_MANAGEMENT_UI_IMPROVEMENTS.md` - User management

---

**Last Updated:** 2024-01-22  
**Version:** 1.0  
**Maintainer:** Development Team