# Test Script - Form Pegawai

## Pre-requisites
- Aplikasi sudah running: `python app.py`
- Login sebagai admin atau pimpinan
- Browser dengan DevTools (F12)

## Test Case 1: Submit Form dengan Data Lengkap ✅

### Steps:
1. Akses `/pegawai`
2. Isi semua field:
   - Nama Lengkap: "John Doe"
   - Tanggal Lahir: "1990-01-15"
   - NIP: "1234567890"
   - Golongan: "III/b"
   - Jabatan: "Staff Administrasi"
   - Agama: "Islam"
   - Jenis Kelamin: Laki-laki (checked)
   - Nomor Telepon: "081234567890"
   - Riwayat Pendidikan: "S1 Hukum - Universitas Indonesia (2012)"
   - Riwayat Pekerjaan: "Staff - PT ABC (2013-2020)"
3. Klik "Simpan Data Pegawai"

### Expected Result:
- ✅ Button berubah menjadi "Menyimpan..." dengan spinner
- ✅ Button disabled saat proses
- ✅ Toast hijau muncul: "Pegawai John Doe berhasil ditambahkan"
- ✅ Form ter-reset (semua field kosong)
- ✅ Radio button kembali ke "Laki-laki"
- ✅ Button enabled kembali
- ✅ Console tidak ada error
- ✅ Network tab menunjukkan status 200

### Verify in Database:
```sql
sqlite3 instance/app.db
SELECT * FROM pegawai WHERE nip = '1234567890';
```

---

## Test Case 2: Submit Form Field Required Kosong ❌

### Steps:
1. Akses `/pegawai`
2. Hanya isi Nama: "Jane Doe"
3. Biarkan NIP, Tanggal Lahir kosong
4. Klik "Simpan Data Pegawai"

### Expected Result:
- ✅ Toast merah muncul: "Mohon lengkapi semua field yang wajib diisi"
- ✅ Form tidak submit
- ✅ Data tidak hilang dari field yang sudah diisi
- ✅ Button tidak disabled
- ✅ Console log: "Form data:", dengan field kosong

---

## Test Case 3: NIP Duplikat ❌

### Steps:
1. Submit form dengan NIP: "1234567890" (yang sudah ada dari Test 1)
2. Isi field required lainnya

### Expected Result:
- ✅ Toast merah muncul: "NIP 1234567890 sudah terdaftar"
- ✅ Form tidak ter-reset
- ✅ Data tetap ada di form
- ✅ Status code 400
- ✅ Console log menunjukkan response error

---

## Test Case 4: Format Tanggal Invalid ❌

### Steps:
1. Isi form dengan data valid
2. Manually change tanggal_lahir value di console:
   ```javascript
   document.getElementById('tanggal_lahir').value = '32-13-2024';
   ```
3. Submit form

### Expected Result:
- ✅ Toast merah: "Format tanggal lahir tidak valid"
- ✅ Status code 400

---

## Test Case 5: CSRF Token Validation ✅

### Steps:
1. Buka DevTools > Console
2. Cek apakah csrf_token ada:
   ```javascript
   console.log(document.querySelector('input[name="csrf_token"]').value);
   ```
3. Submit form normal

### Expected Result:
- ✅ CSRF token ditemukan
- ✅ Console log: "CSRF Token: Found"
- ✅ Tidak ada error CSRF
- ✅ Submit berhasil

### Test CSRF Error:
1. Hapus csrf_token dari form:
   ```javascript
   document.querySelector('input[name="csrf_token"]').remove();
   ```
2. Submit form

### Expected Result:
- ✅ Toast merah: "Sesi keamanan tidak valid..."
- ✅ Status code 400

---

## Test Case 6: Field Opsional Kosong ✅

### Steps:
1. Isi hanya field required:
   - Nama: "Test User"
   - NIP: "9876543210"
   - Tanggal Lahir: "1995-05-20"
   - Jenis Kelamin: Perempuan
2. Kosongkan field opsional
3. Submit

### Expected Result:
- ✅ Submit berhasil
- ✅ Toast hijau muncul
- ✅ Data tersimpan dengan field opsional NULL

### Verify:
```sql
SELECT * FROM pegawai WHERE nip = '9876543210';
-- golongan, jabatan, agama, dll should be NULL
```

---

## Test Case 7: Double Submit Prevention ✅

### Steps:
1. Isi form dengan data valid
2. Klik "Simpan Data Pegawai"
3. **Cepat klik lagi** sebelum response selesai

### Expected Result:
- ✅ Button disabled setelah klik pertama
- ✅ Klik kedua tidak berfungsi
- ✅ Hanya 1 request terkirim (cek Network tab)
- ✅ Tidak ada data duplikat di database

---

## Test Case 8: Network Error Handling ❌

### Steps:
1. Buka DevTools > Network
2. Set throttling ke "Offline"
3. Submit form

### Expected Result:
- ✅ Toast merah: "Terjadi kesalahan saat menyimpan data"
- ✅ Console log error network
- ✅ Button enabled kembali setelah error
- ✅ Form tidak reset
- ✅ Data tetap ada di form

---

## Test Case 9: Special Characters in Input ✅

### Steps:
1. Isi field dengan special characters:
   - Nama: "O'Connor & Smith Jr."
   - NIP: "ABC-123-456"
   - Riwayat: "Worked at "ABC Corp" (2015)"
2. Submit

### Expected Result:
- ✅ Submit berhasil
- ✅ Data tersimpan dengan benar (tidak corrupted)
- ✅ Special characters tidak menyebabkan SQL injection
- ✅ Data tetap utuh saat ditampilkan kembali

---

## Test Case 10: Long Text Input ✅

### Steps:
1. Isi Riwayat Pendidikan dengan text > 500 karakter
2. Isi Riwayat Pekerjaan dengan text > 500 karakter
3. Submit

### Expected Result:
- ✅ Submit berhasil
- ✅ Text lengkap tersimpan
- ✅ Tidak ada truncation
- ✅ Textarea scrollable untuk text panjang

---

## Test Case 11: Browser Back Button ✅

### Steps:
1. Isi form (jangan submit)
2. Klik link lain (misalnya Dashboard)
3. Klik browser back button
4. Cek form

### Expected Result:
- ✅ Form kembali dengan data yang sudah diisi (browser cache)
- ✅ CSRF token masih valid
- ✅ Form bisa disubmit

---

## Test Case 12: Session Timeout ❌

### Steps:
1. Buka form pegawai
2. Tunggu > 30 menit (session timeout)
3. Isi dan submit form

### Expected Result:
- ✅ Redirect ke login page
- ✅ Atau error message yang jelas
- ✅ Data form tidak hilang (optional)

---

## Console Checks

### Saat Page Load:
```javascript
// Cek element ada
console.log(document.getElementById('pegawaiForm')); // Should not be null
console.log(document.getElementById('submitBtn')); // Should not be null
console.log(document.getElementById('toast-container')); // Should not be null
console.log(document.querySelector('input[name="csrf_token"]')); // Should have value
```

### Saat Submit:
```javascript
// Log yang harus muncul:
// "Form submit triggered"
// "Form data: {nama: '...', nip: '...', ...}"
// "CSRF Token: Found"
// "Response status: 200"
// "Success response: {success: true, message: '...'}"
```

---

## Network Tab Checks

### Request:
- Method: POST
- URL: /pegawai
- Headers:
  - Content-Type: multipart/form-data
  - X-Requested-With: XMLHttpRequest
- Body (Form Data):
  - csrf_token: [token value]
  - nama: [value]
  - nip: [value]
  - tanggal_lahir: [value]
  - jenis_kelamin: [value]
  - (other fields)

### Response (Success):
- Status: 200 OK
- Content-Type: application/json
- Body:
  ```json
  {
    "success": true,
    "message": "Pegawai [nama] berhasil ditambahkan"
  }
  ```

### Response (Error):
- Status: 400 Bad Request / 500 Internal Server Error
- Content-Type: application/json
- Body:
  ```json
  {
    "success": false,
    "message": "[error message]"
  }
  ```

---

## Database Verification

### Check Data Inserted:
```sql
-- List all pegawai
SELECT * FROM pegawai ORDER BY id DESC LIMIT 5;

-- Count total
SELECT COUNT(*) FROM pegawai;

-- Check specific NIP
SELECT * FROM pegawai WHERE nip = '1234567890';

-- Check NULL fields
SELECT * FROM pegawai WHERE golongan IS NULL;
```

### Check Data Integrity:
```sql
-- Check for duplicates
SELECT nip, COUNT(*) as count 
FROM pegawai 
GROUP BY nip 
HAVING count > 1;

-- Check invalid dates
SELECT * FROM pegawai 
WHERE tanggal_lahir > DATE('now');
```

---

## Performance Test

### Measure Submit Time:
```javascript
const startTime = performance.now();

// Submit form

// In .finally():
const endTime = performance.now();
console.log(`Submit took ${endTime - startTime}ms`);
```

### Expected:
- ✅ < 500ms for local database
- ✅ < 2000ms for network database

---

## Accessibility Test

1. ✅ Tab navigation works
2. ✅ All fields accessible via keyboard
3. ✅ Labels associated with inputs
4. ✅ Error messages readable by screen reader
5. ✅ Required fields marked with *
6. ✅ Color contrast sufficient

---

## Mobile Responsive Test

1. ✅ Form usable on mobile (375px width)
2. ✅ Fields stack vertically on small screen
3. ✅ Date picker works on mobile
4. ✅ Toast notification visible
5. ✅ Submit button accessible

---

## Security Test

1. ✅ CSRF protection active
2. ✅ Login required
3. ✅ Role-based access (admin/pimpinan only)
4. ✅ SQL injection prevented
5. ✅ XSS prevented
6. ✅ Session validation

### Try SQL Injection:
```
Nama: ' OR '1'='1
NIP: '; DROP TABLE pegawai; --
```
**Expected:** Data tersimpan as-is, tidak execute SQL

---

## Summary Checklist

- [ ] All test cases passed
- [ ] No console errors
- [ ] No network errors
- [ ] Data integrity maintained
- [ ] CSRF protection working
- [ ] Toast notifications working
- [ ] Form validation working
- [ ] Button state management working
- [ ] Database queries correct
- [ ] Security measures active

---

## Rollback Test Data

```sql
-- Delete test data
DELETE FROM pegawai WHERE nip IN ('1234567890', '9876543210');

-- Verify
SELECT COUNT(*) FROM pegawai;
```

---

## Last Updated
2024 - After CSRF Token Fix