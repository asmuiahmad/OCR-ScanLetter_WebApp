# Debug Guide - Form Pegawai

## 🐛 Masalah: "Terjadi kesalahan saat mengirim data"

Jika Anda mendapat error ini saat menyimpan data pegawai, ikuti langkah debugging berikut:

---

## Langkah 1: Akses Halaman Debug

1. Login sebagai admin atau pimpinan
2. Akses: **`http://localhost:5000/pegawai/debug`**
3. Halaman debug akan menampilkan form test dengan console logging

---

## Langkah 2: Test dengan Form Debug

### Cara Menggunakan:
1. Form sudah terisi otomatis dengan data test
2. Klik tombol **"Test Submit"**
3. Lihat **Debug Console** di bawah form
4. Console akan menampilkan semua detail request dan response

### Yang Harus Dicek:

#### ✅ CSRF Token
```
CSRF token found: IjM5N2Y4ZmE3ZWI5OT...
```
Jika muncul: **"⚠️ CSRF token NOT found!"** → masalah di CSRF token

#### ✅ Form Data
```
Form data collected:
  nama: Test User Debug
  nip: DEBUG1234567890
  tanggal_lahir: 1990-01-01
  jenis_kelamin: Laki-laki
  csrf_token: IjM5N2Y4ZmE3ZWI5OT...
```
Pastikan semua field terkirim

#### ✅ Response Status
```
Response status: 200 OK
```
- **200 OK** = berhasil
- **400 Bad Request** = validasi gagal atau CSRF error
- **500 Internal Server Error** = error di server

#### ✅ Response Body
```json
{
  "success": true,
  "message": "Validasi berhasil! (Debug mode - data tidak disimpan)",
  "debug": {
    "request_received": true,
    "has_csrf_token": true,
    "is_ajax": true,
    ...
  }
}
```

---

## Langkah 3: Cek Browser Console (F12)

### Buka DevTools:
1. Tekan **F12** atau klik kanan → Inspect
2. Buka tab **Console**
3. Submit form di `/pegawai` (bukan debug)
4. Lihat log yang muncul

### Log yang Diharapkan:
```
Form submit triggered
Form data: {nama: "...", nip: "...", ...}
CSRF Token: Found
Response status: 200
Response statusText: OK
Response ok: true
Response type: cors
Response text: {"success":true,...}
Parsed JSON: {success: true, message: "..."}
Success response: {success: true, message: "..."}
```

### Jika Ada Error:
```
❌ Response status: 400 Bad Request
❌ JSON parse error: Unexpected token < in JSON at position 0
❌ Network error: Failed to fetch
```

---

## Langkah 4: Cek Network Tab

### Di DevTools:
1. Buka tab **Network**
2. Submit form
3. Cari request ke `/pegawai`
4. Klik untuk melihat detail

### Cek Request:
```
Method: POST
URL: http://localhost:5000/pegawai
Status: 200 (atau error code)

Headers:
  Content-Type: multipart/form-data; boundary=...
  X-Requested-With: XMLHttpRequest

Form Data:
  csrf_token: IjM5N2Y4...
  nama: Test User
  nip: 1234567890
  tanggal_lahir: 1990-01-01
  jenis_kelamin: Laki-laki
  (other fields...)
```

### Cek Response:
```json
{
  "success": true,
  "message": "Pegawai Test User berhasil ditambahkan"
}
```

---

## Penyebab Umum & Solusi

### 1. CSRF Token Missing ❌
**Error:**
```
400 Bad Request
The CSRF token is missing.
```

**Solusi:**
1. Cek apakah ada `<input type="hidden" name="csrf_token" ...>` di form
2. Refresh halaman untuk generate token baru
3. Pastikan meta tag csrf-token ada di `<head>`
4. Cek session tidak expired

**Fix:**
```html
<!-- Pastikan ada di form -->
<input type="hidden" name="csrf_token" value="{{ csrf_token() }}" />
```

---

### 2. Response Bukan JSON ❌
**Error:**
```
JSON parse error: Unexpected token < in JSON at position 0
```

**Penyebab:**
- Server mengembalikan HTML error page bukan JSON
- Ada error 500 di server
- Redirect terjadi

**Solusi:**
1. Cek server logs: `tail -f logs/app.log` (jika ada)
2. Atau lihat terminal output saat jalankan `python app.py`
3. Cek apakah ada error di route `/pegawai`

---

### 3. Validasi Gagal ❌
**Error:**
```json
{
  "success": false,
  "message": "Nama, NIP, tanggal lahir, dan jenis kelamin wajib diisi"
}
```

**Solusi:**
- Pastikan semua field required terisi
- Cek format tanggal: YYYY-MM-DD
- Pilih salah satu radio button jenis kelamin

---

### 4. NIP Duplikat ❌
**Error:**
```json
{
  "success": false,
  "message": "NIP 1234567890 sudah terdaftar"
}
```

**Solusi:**
- Gunakan NIP yang berbeda
- Atau edit pegawai yang sudah ada

**Cek di database:**
```sql
sqlite3 instance/app.db
SELECT * FROM pegawai WHERE nip = '1234567890';
```

---

### 5. Network Error ❌
**Error:**
```
Network error: Failed to fetch
```

**Penyebab:**
- Server tidak running
- CORS issue
- Browser blocking request

**Solusi:**
1. Pastikan aplikasi running: `python app.py`
2. Cek di browser: `http://localhost:5000`
3. Cek firewall/antivirus tidak block

---

### 6. Session Expired ❌
**Error:**
- Redirect ke login page
- 401 Unauthorized

**Solusi:**
- Login ulang
- Session timeout default: 30 menit

---

## Langkah 5: Cek Server Logs

### Jalankan aplikasi dengan logging:
```bash
python app.py
```

### Log yang diharapkan saat submit:
```
INFO: === POST /pegawai called ===
INFO: Request method: POST
INFO: Content-Type: multipart/form-data; boundary=...
INFO: Is AJAX: XMLHttpRequest
INFO: Form data keys: ['csrf_token', 'nama', 'nip', ...]
INFO: Received data - nama: Test User, nip: 1234567890, ...
INFO: Pegawai baru ditambahkan: Test User (NIP: 1234567890)
INFO: Returning success response
```

### Jika ada error:
```
ERROR: Error adding pegawai: ...
ERROR: Error type: ValueError
ERROR: Traceback: ...
```

---

## Langkah 6: Test dengan Script Python

Jalankan test script:
```bash
python test_pegawai_route.py
```

Output yang diharapkan:
```
=== Testing Pegawai Route ===

Test 1: Check if /pegawai route exists (GET)
Status: 302
✓ Route exists

Test 2: Create test admin user
✓ Admin user already exists

Test 3: Login as admin
Login status: 200

Test 4: Access pegawai form (GET)
Status: 200
✓ Form accessible
✓ CSRF token found in form

Test 5: Submit pegawai data (POST)
Response status: 200
✓ POST successful
✓✓ Pegawai successfully added!

Test 6: Check database
✓ Pegawai found in database
✓ Test data deleted

=== All Tests Complete ===
```

---

## Checklist Debugging

- [ ] CSRF token ada di form (`<input type="hidden" name="csrf_token">`)
- [ ] CSRF token terkirim dalam FormData
- [ ] Response status 200 OK
- [ ] Response body adalah JSON valid
- [ ] Server logs tidak ada error
- [ ] Field required semua terisi
- [ ] Format tanggal benar (YYYY-MM-DD)
- [ ] NIP belum ada di database
- [ ] Session masih aktif (tidak expired)
- [ ] Browser console tidak ada error JavaScript
- [ ] Network tab menunjukkan request terkirim

---

## Solusi Quick Fix

### Jika masih error setelah semua dicek:

1. **Clear browser cache dan cookies**
   ```
   Ctrl + Shift + Delete
   Clear cookies and site data
   ```

2. **Restart aplikasi**
   ```bash
   # Stop aplikasi (Ctrl+C)
   # Jalankan ulang
   python app.py
   ```

3. **Hard refresh halaman**
   ```
   Ctrl + Shift + R (Windows/Linux)
   Cmd + Shift + R (Mac)
   ```

4. **Coba di browser lain**
   - Chrome
   - Firefox
   - Edge

5. **Cek file database**
   ```bash
   ls -lh instance/app.db
   # Pastikan file ada dan bisa diakses
   ```

---

## Cara Report Bug

Jika masih ada masalah, kumpulkan informasi berikut:

1. **Screenshot error message**
2. **Browser console log** (copy semua text)
3. **Network tab** (screenshot request/response)
4. **Server logs** (copy dari terminal)
5. **Form data** yang disubmit
6. **Browser & OS** yang digunakan

Kirim ke developer dengan format:
```
Browser: Chrome 120.0.6099.130
OS: Windows 11
Error: "Terjadi kesalahan saat mengirim data"

Console log:
[paste console log here]

Network request:
[screenshot or paste request detail]

Server log:
[paste server log here]
```

---

## Kontak Support

Jika butuh bantuan lebih lanjut:
- Check documentation: `PERBAIKAN_FORM_PEGAWAI.md`
- Run debug form: `/pegawai/debug`
- Run test script: `python test_pegawai_route.py`

---

## Last Updated
2024 - After Form Pegawai Fix