# Troubleshooting Guide - Modal "Lihat Data Ekstraksi" Tidak Muncul

## Gejala
- Tombol "Lihat Data Ekstraksi" tidak bisa diklik
- Modal tidak muncul ketika tombol diklik
- Tidak ada response ketika mengklik tombol

---

## 🔍 Diagnosis Cepat

### Langkah 1: Buka Browser Console
1. Tekan `F12` atau `Ctrl+Shift+I` (Windows/Linux) atau `Cmd+Option+I` (Mac)
2. Buka tab **Console**
3. Klik tombol "Lihat Data Ekstraksi"
4. Lihat apakah ada error message

---

## ✅ Checklist Debug

### 1. Pastikan Ada Data Ekstraksi
**Problem:** Modal hanya akan muncul jika ada data yang diekstrak.

**Cara Cek:**
- Di browser console, ketik: `extractedData`
- Jika menampilkan `[]` (array kosong) atau `null`, berarti belum ada data
- Jika menampilkan array dengan object, data sudah ada

**Solusi:**
```
Jika data kosong:
1. Upload file PDF/JPG/PNG terlebih dahulu
2. Klik tombol "Proses Dokumen"
3. Tunggu sampai muncul "Hasil Ekstraksi Formulir Cuti"
4. Baru klik "Lihat Data Ekstraksi"
```

---

### 2. Cek Apakah Modal Element Ada
**Cara Cek di Console:**
```javascript
document.getElementById('extractedDataModal')
```

**Jika hasilnya `null`:**
- Modal element tidak ada di halaman
- Kemungkinan template error
- **Solusi:** Refresh halaman atau clear browser cache

**Jika hasilnya menampilkan HTML element:**
- Modal element ada, lanjut ke step berikut

---

### 3. Cek Apakah Tombol Ada
**Cara Cek di Console:**
```javascript
document.getElementById('toggleExtractedDataBtn')
```

**Jika hasilnya `null`:**
- Tombol tidak ada
- **Solusi:** Refresh halaman

---

### 4. Cek Apakah Function Ada
**Cara Cek di Console:**
```javascript
typeof window.toggleExtractedData
```

**Jika hasilnya `"undefined"`:**
- JavaScript tidak ter-load dengan benar
- **Solusi:** Hard refresh (`Ctrl+Shift+R` atau `Cmd+Shift+R`)

**Jika hasilnya `"function"`:**
- Function sudah ada, lanjut ke step berikut

---

### 5. Test Manual dari Console
**Coba buka modal manual:**
```javascript
window.toggleExtractedData()
```

**Jika modal muncul:**
- Problem ada di event binding
- **Solusi:** Event listener sudah otomatis ditambahkan saat page load

**Jika modal tidak muncul:**
- Check error message di console
- Lanjut ke troubleshooting advanced

---

## 🛠️ Solusi Berdasarkan Error Message

### Error: "Modal not found"
```
Error: Modal tidak ditemukan. Refresh halaman dan coba lagi.
```

**Solusi:**
1. Hard refresh halaman: `Ctrl+Shift+R` (Windows/Linux) atau `Cmd+Shift+R` (Mac)
2. Clear browser cache
3. Pastikan file `ocr_cuti_v2.html` ter-load dengan lengkap

---

### Error: "Tidak ada data ekstraksi"
```
Tidak ada data ekstraksi. Silakan upload dan proses dokumen terlebih dahulu.
```

**Solusi:**
1. Upload file formulir cuti (PDF/JPG/PNG)
2. Klik "Proses Dokumen"
3. Tunggu sampai proses selesai
4. Section "Hasil Ekstraksi Formulir Cuti" akan muncul
5. Baru klik "Lihat Data Ekstraksi"

---

### Error: JavaScript Disabled
**Gejala:** Tombol sama sekali tidak merespon

**Solusi:**
1. Pastikan JavaScript enabled di browser:
   - Chrome: Settings → Privacy and security → Site settings → JavaScript → Allowed
   - Firefox: about:config → javascript.enabled → true
   - Safari: Preferences → Security → Enable JavaScript
2. Refresh halaman

---

### Error: Modal Terbuka tapi Kosong
**Gejala:** Modal muncul tapi tidak ada data/form kosong

**Cara Debug:**
```javascript
// Di console
console.log(window.extractedData);
console.log(window.currentDataIndex);
```

**Solusi:**
- Jika extractedData kosong, upload dan proses ulang dokumen
- Jika extractedData ada tapi form kosong, ada masalah di `fillModalForm()`
- Coba: `window.fillModalForm(0)` di console

---

## 🔧 Advanced Troubleshooting

### Manual Open Modal
Jika tombol tidak berfungsi, buka modal secara manual via console:

```javascript
// 1. Cek data
console.log('Data:', window.extractedData);

// 2. Buka modal
const modal = document.getElementById('extractedDataModal');
modal.classList.remove('hidden');

// 3. Fill form dengan data pertama
window.fillModalForm(0);
```

### Force Reload JavaScript
```javascript
// Hard reload tanpa cache
location.reload(true);

// Atau dengan code
window.location.href = window.location.href + '?refresh=' + Date.now();
```

### Debug Modal State
```javascript
// Check current state
const modal = document.getElementById('extractedDataModal');
console.log('Modal classes:', modal.className);
console.log('Is hidden:', modal.classList.contains('hidden'));
console.log('Display style:', modal.style.display);
```

---

## 📱 Browser Compatibility Issues

### Safari
**Issue:** Modal mungkin tidak support z-index yang tinggi

**Solusi:**
```javascript
const modal = document.getElementById('extractedDataModal');
modal.style.zIndex = '99999';
modal.style.position = 'fixed';
```

### Internet Explorer
**Issue:** ES6 JavaScript tidak didukung

**Solusi:** Gunakan browser modern (Chrome, Firefox, Edge, Safari)

---

## 🎯 Quick Fix Checklist

Coba langkah-langkah ini secara berurutan:

1. **[ ]** Hard refresh halaman (`Ctrl+Shift+R`)
2. **[ ]** Clear browser cache
3. **[ ]** Pastikan sudah upload dan proses dokumen
4. **[ ]** Buka browser console (F12) dan cek error
5. **[ ]** Test: `window.extractedData` di console
6. **[ ]** Test: `window.toggleExtractedData()` di console
7. **[ ]** Coba browser lain (Chrome/Firefox)
8. **[ ]** Restart browser
9. **[ ]** Restart Flask server

---

## 📊 Verification Steps

Setelah fix, verifikasi dengan:

```javascript
// Di browser console:

// 1. Check data
console.log('Has data:', window.extractedData && window.extractedData.length > 0);

// 2. Check modal
console.log('Has modal:', !!document.getElementById('extractedDataModal'));

// 3. Check button
console.log('Has button:', !!document.getElementById('toggleExtractedDataBtn'));

// 4. Check function
console.log('Has function:', typeof window.toggleExtractedData === 'function');

// All should return true
```

---

## 🔄 Step-by-Step Expected Flow

### Normal Flow (yang seharusnya terjadi):

1. **Upload Dokumen** → Pilih PDF/JPG/PNG
2. **Klik "Proses Dokumen"** → OCR berjalan
3. **Section "Hasil Ekstraksi" muncul** → Data summary ditampilkan
4. **Klik "Lihat Data Ekstraksi"** → Modal muncul
5. **Modal menampilkan:**
   - Preview dokumen (PDF/Image) di kiri
   - Form data ekstraksi di kanan
   - Tombol navigasi (Previous/Next)
   - Tombol Simpan

### Debug di Setiap Step:

**After Step 1 (Upload):**
```javascript
console.log('File uploaded:', document.getElementById('fileInput').files.length > 0);
```

**After Step 2 (Process):**
- Lihat network tab, pastikan request POST ke `/cuti-v2/ocr` success
- Response should include extracted_data_list

**After Step 3 (Results shown):**
```javascript
console.log('Data loaded:', window.extractedData);
```

**After Step 4 (Click button):**
- Console should log: "toggleExtractedData called"
- Console should log: "Modal found, current state: hidden"
- Console should log: "Showing modal..."

---

## 💡 Common Mistakes

### Mistake 1: Klik tombol sebelum proses selesai
**Error:** Tidak ada yang terjadi atau error "Tidak ada data"

**Fix:** Tunggu sampai section "Hasil Ekstraksi" muncul

---

### Mistake 2: Multiple clicks
**Error:** Modal buka tutup atau tidak konsisten

**Fix:** Klik tombol hanya sekali, tunggu modal muncul

---

### Mistake 3: Browser cache lama
**Error:** JavaScript versi lama ter-load

**Fix:** Hard refresh atau clear cache

---

## 🆘 Masih Tidak Bisa?

### Langkah Terakhir:

1. **Screenshot error di console** (F12 → Console tab)
2. **Check file log server** (di terminal tempat Flask running)
3. **Copy-paste error message**
4. **Hubungi tim development** dengan info:
   - Browser dan versi (Chrome 120, Firefox 121, dll)
   - OS (Windows 10, macOS, Ubuntu, dll)
   - Screenshot error console
   - Screenshot halaman (show button dan results section)
   - Output dari: `window.extractedData`

### Generate Debug Report:

Jalankan di console dan kirim hasilnya:

```javascript
const debugReport = {
    timestamp: new Date().toISOString(),
    browser: navigator.userAgent,
    dataCount: window.extractedData ? window.extractedData.length : 0,
    hasModal: !!document.getElementById('extractedDataModal'),
    hasButton: !!document.getElementById('toggleExtractedDataBtn'),
    hasFunction: typeof window.toggleExtractedData === 'function',
    modalClasses: document.getElementById('extractedDataModal')?.className,
    sampleData: window.extractedData && window.extractedData[0] ? {
        nama: window.extractedData[0].nama,
        nip: window.extractedData[0].nip,
        hasFilePath: !!window.extractedData[0].file_path
    } : null
};
console.log('DEBUG REPORT:', JSON.stringify(debugReport, null, 2));
```

---

**Last Updated:** January 2024
**For:** OCR Cuti V2 - PA Banjarbaru