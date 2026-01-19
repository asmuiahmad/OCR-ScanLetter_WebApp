# Quick Test Guide - Modal "Lihat Data Ekstraksi" Fix

## ✅ Perubahan yang Dilakukan

Saya telah membuat **versi simplified** dari OCR Cuti V2 dengan struktur yang lebih clean:

### File Baru:
1. **`static/assets/js/cuti/ocr-cuti-v2-modal.js`** - JavaScript eksternal untuk modal
2. **`templates/cuti/ocr_cuti_v2_simple.html`** - Template HTML yang lebih sederhana
3. **`config/ocr_cuti_v2.py`** - Updated untuk menggunakan template baru

### Perubahan Utama:
- ✅ JavaScript dipindah ke file eksternal (lebih mudah di-maintain)
- ✅ Struktur HTML lebih sederhana dan jelas
- ✅ Event listeners dikelola dengan lebih baik
- ✅ Debugging console.log ditambahkan
- ✅ Tombol menggunakan event listener (bukan onclick inline)

---

## 🧪 Cara Test

### Step 1: Restart Flask Server
```bash
# Stop server (Ctrl+C)
# Start lagi
python app.py
```

### Step 2: Buka Browser
```
http://localhost:5000/cuti-v2/ocr
```

### Step 3: Buka Browser Console (PENTING!)
```
Tekan F12 (atau Cmd+Option+I di Mac)
Buka tab "Console"
```

### Step 4: Upload & Proses Dokumen
1. Upload file PDF atau JPG formulir cuti
2. Klik "Proses Dokumen"
3. Tunggu sampai muncul section "Hasil Ekstraksi Formulir Cuti"

### Step 5: Lihat Console Output
Seharusnya muncul di console:
```
DOM Content Loaded - OCR Cuti V2 Modal
Initializing modal event listeners...
Toggle button listener added
Modal event listeners initialized
Data initialized: 1 items
```

### Step 6: Klik "Lihat Data Ekstraksi"
**Tombol warna BIRU** di bagian bawah section hasil.

Console seharusnya menampilkan:
```
toggleExtractedData called
extractedData: [Object]
extractedData length: 1
Modal found, current state: hidden
Showing modal...
fillModalForm called with index: 0
Filling form with data: Object { ... }
Form filled successfully
```

### Step 7: Verifikasi Modal Muncul
Modal harus muncul dengan:
- ✅ Preview dokumen (PDF/Image) di sebelah kiri
- ✅ Form data ekstraksi di sebelah kanan
- ✅ Tombol Previous/Next/Close di bawah

---

## 🔍 Debug Jika Masih Bermasalah

### Test 1: Cek JavaScript File Ter-load
Di console, ketik:
```javascript
typeof toggleExtractedData
```
**Expected:** `"function"`
**Jika `"undefined"`:** JavaScript file tidak ter-load, hard refresh (`Ctrl+Shift+R`)

### Test 2: Cek Data Ada
```javascript
window.extractedData
```
**Expected:** Array dengan object data
**Jika `undefined` atau `[]`:** Upload dan proses dokumen dulu

### Test 3: Cek Modal Element
```javascript
document.getElementById('extractedDataModal')
```
**Expected:** HTML element object
**Jika `null`:** Template tidak ter-load dengan benar, refresh halaman

### Test 4: Cek Tombol Element
```javascript
document.getElementById('toggleExtractedDataBtn')
```
**Expected:** Button element object
**Jika `null`:** Template error, refresh halaman

### Test 5: Force Open Modal (Manual)
```javascript
// Init data (replace with your actual data)
window.initExtractedData([{
    nama: "Test",
    nip: "123",
    file_path: "ocr/cuti/test.pdf",
    file_type: "pdf"
}]);

// Open modal
window.toggleExtractedData();
```

---

## 📊 Expected Console Output (Success)

```
DOM Content Loaded - OCR Cuti V2 Modal
Initializing modal event listeners...
Toggle button listener added
Modal event listeners initialized
Data initialized: 1 items
[User clicks button]
toggleExtractedData called
extractedData: Array(1) [ {…} ]
extractedData length: 1
Modal found, current state: hidden
Showing modal...
fillModalForm called with index: 0
Filling form with data: {nama: "Ahmad Asmui", nip: "21412321312231", ...}
Form filled successfully
```

---

## ❌ Common Errors & Solutions

### Error 1: "toggleExtractedData is not defined"
**Console:** `Uncaught ReferenceError: toggleExtractedData is not defined`

**Solution:**
```bash
# Hard refresh browser
Ctrl+Shift+R (Windows/Linux)
Cmd+Shift+R (Mac)
```

### Error 2: "Tidak ada data ekstraksi"
**Alert:** "Tidak ada data ekstraksi. Silakan upload dan proses dokumen terlebih dahulu."

**Solution:**
1. Pastikan sudah upload file
2. Pastikan sudah klik "Proses Dokumen"
3. Tunggu sampai muncul "Hasil Ekstraksi Formulir Cuti"

### Error 3: "Modal tidak ditemukan"
**Alert:** "Error: Modal tidak ditemukan. Refresh halaman dan coba lagi."

**Solution:**
```bash
# Clear browser cache
# Chrome: Ctrl+Shift+Delete
# Firefox: Ctrl+Shift+Delete
# Pilih "Cached images and files"
# Klik "Clear data"
```

### Error 4: Modal Muncul tapi Kosong
**Symptom:** Modal terbuka tapi form kosong

**Debug:**
```javascript
// Di console
console.log(window.extractedData);
console.log(window.currentDataIndex);

// Try fill manually
window.fillModalForm(0);
```

---

## 🎯 Quick Debug Commands

Copy-paste ke browser console:

```javascript
// Full diagnostic
const diagnostic = {
    hasData: !!window.extractedData && window.extractedData.length > 0,
    dataCount: window.extractedData ? window.extractedData.length : 0,
    hasModal: !!document.getElementById('extractedDataModal'),
    hasButton: !!document.getElementById('toggleExtractedDataBtn'),
    hasToggleFunction: typeof window.toggleExtractedData === 'function',
    hasInitFunction: typeof window.initExtractedData === 'function',
    hasFillFunction: typeof window.fillModalForm === 'function',
};

console.table(diagnostic);

// If all true, modal should work!
if (Object.values(diagnostic).every(v => v === true)) {
    console.log('✅ ALL CHECKS PASSED - Modal should work!');
    console.log('Try: window.toggleExtractedData()');
} else {
    console.error('❌ SOME CHECKS FAILED - See table above');
}
```

---

## 🔄 Rollback ke Versi Lama (Jika Perlu)

Jika versi baru tidak bekerja, rollback dengan:

1. Edit `config/ocr_cuti_v2.py`
2. Ubah semua `ocr_cuti_v2_simple.html` kembali ke `ocr_cuti_v2.html`
3. Restart Flask server

---

## 📝 Checklist

- [ ] Flask server sudah restart
- [ ] Browser console terbuka (F12)
- [ ] File sudah diupload
- [ ] Proses OCR sudah selesai
- [ ] Section "Hasil Ekstraksi" sudah muncul
- [ ] Console menampilkan "Data initialized: X items"
- [ ] Tombol "Lihat Data Ekstraksi" terlihat
- [ ] Klik tombol → Console log muncul
- [ ] Modal muncul dengan preview & form
- [ ] Data terisi di form

---

## 🆘 Jika Masih Tidak Bisa

Kirim info berikut ke tim development:

1. **Screenshot console** (semua log yang muncul)
2. **Screenshot halaman** (tunjukkan tombol dan section hasil)
3. **Output dari diagnostic command** (di atas)
4. **Browser & versi** (Chrome 120, Firefox 121, dll)
5. **OS** (Windows 10, macOS 14, Ubuntu 22.04, dll)

---

**Last Updated:** January 2024
**Version:** OCR Cuti V2 Simplified
**Status:** Ready for Testing ✅