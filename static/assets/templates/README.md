# HTML Template untuk Surat Cuti

## Overview
Sistem ini mendukung dua jenis template untuk generate surat cuti:
1. **HTML Template** - Template HTML yang mudah diedit dan di-maintain
2. **DOCX Template** - Template Microsoft Word (fallback)

## Template HTML yang Tersedia

### 1. form_cuti_simple.html
Template HTML yang sederhana dan mudah digunakan dengan fitur:
- Layout responsive untuk print A4
- Styling CSS yang clean dan professional
- Placeholder yang mudah dipahami (format: `«field_name»`)
- Support untuk QR Code digital signature
- Format tanggal Indonesia
- Checkbox untuk jenis cuti

### 2. form_permintaan_cuti copy.html
Template HTML yang dikonversi dari Word document dengan:
- Format yang kompleks sesuai dokumen asli
- Styling Microsoft Word yang dipertahankan
- Kompatibilitas tinggi dengan format dokumen resmi

## Cara Menggunakan

### 1. Melalui Web Interface
1. Buka form "Formulir Permintaan Cuti"
2. Isi semua data yang diperlukan
3. Pilih tombol "Generate dengan HTML Template" untuk menggunakan HTML template
4. Atau pilih "Generate Surat Cuti (DOCX)" untuk menggunakan template Word

### 2. Preview HTML
- Di halaman "Daftar Permohonan Cuti", klik tombol "Preview HTML" untuk melihat hasil template sebelum generate PDF
- Preview akan membuka di tab baru dengan tampilan seperti hasil akhir

## Placeholder yang Tersedia

Template HTML menggunakan placeholder dengan format `«field_name»`:

### Data Pegawai
- `«nama»` - Nama lengkap pegawai
- `«nip»` - Nomor Induk Pegawai
- `«jabatan»` - Jabatan pegawai
- `«gol_ruang»` - Golongan/Ruang
- `«unit_kerja»` - Unit kerja
- `«masa_kerja»` - Masa kerja
- `«alamat»` - Alamat lengkap
- `«telp»` - Nomor telepon

### Data Cuti
- `«jenis_cuti»` - Jenis cuti yang dipilih
- `«alasan_cuti»` - Alasan mengajukan cuti
- `«lama_cuti»` - Lama cuti (dalam hari)
- `«tanggal_cuti»` - Tanggal mulai cuti
- `«sampai_cuti»` - Tanggal selesai cuti
- `«tgl_lengkap_ajuan_cuti»` - Tanggal pengajuan (format Indonesia)
- `«no_suratmasuk»` - Nomor surat masuk

### Checkbox Jenis Cuti
- `«c_tahun»` - Cuti Tahunan
- `«c_besar»` - Cuti Besar
- `«c_sakit»` - Cuti Sakit
- `«c_lahir»` - Cuti Melahirkan
- `«c_penting»` - Cuti Alasan Penting
- `«c_luarnegara»` - Cuti Luar Negara

### QR Code
- `{{QR_CODE}}` - Placeholder untuk QR Code digital signature

## Kustomisasi Template

### 1. Mengedit Template HTML
1. Buka file template di `static/assets/templates/`
2. Edit HTML dan CSS sesuai kebutuhan
3. Pastikan placeholder tetap menggunakan format `«field_name»`
4. Test dengan preview sebelum digunakan untuk generate PDF

### 2. Menambah Template Baru
1. Buat file HTML baru di folder `static/assets/templates/`
2. Gunakan placeholder yang sama dengan template existing
3. Update `html_template_handler.py` untuk menggunakan template baru
4. Test fungsionalitas

### 3. Styling CSS
Template menggunakan CSS untuk:
- Layout print A4 (`@page` rules)
- Typography yang professional
- Table styling untuk data terstruktur
- Responsive design untuk preview web

## Dependencies

### Python Packages
```bash
pip install WeasyPrint pdfkit qrcode python-docx
```

### System Dependencies
- **wkhtmltopdf** - Untuk konversi HTML ke PDF
- **System fonts** - Untuk rendering font yang baik

### Instalasi Otomatis
Jalankan script instalasi:
```bash
./install_pdf_dependencies.sh
```

## Troubleshooting

### 1. PDF Generation Gagal
- Pastikan wkhtmltopdf terinstal dengan benar
- Check log error di console aplikasi
- Coba gunakan template DOCX sebagai fallback

### 2. Template Tidak Ditemukan
- Pastikan file template ada di `static/assets/templates/`
- Check permission file (readable)
- Verify path di `html_template_handler.py`

### 3. Placeholder Tidak Ter-replace
- Pastikan format placeholder benar: `«field_name»`
- Check mapping di fungsi `replace_placeholders_in_html()`
- Verify data yang dikirim ke template handler

### 4. QR Code Tidak Muncul
- Check apakah QR code berhasil di-generate
- Verify placeholder `{{QR_CODE}}` ada di template
- Check permission folder `static/signatures/`

## Best Practices

1. **Backup Template** - Selalu backup template sebelum mengedit
2. **Test Preview** - Gunakan preview sebelum generate PDF final
3. **Consistent Styling** - Gunakan CSS yang konsisten untuk semua template
4. **Error Handling** - Template handler memiliki fallback ke DOCX jika HTML gagal
5. **Performance** - Template HTML lebih cepat daripada DOCX untuk generate PDF

## Support

Jika mengalami masalah:
1. Check log aplikasi untuk error details
2. Test dengan template sederhana terlebih dahulu
3. Verify semua dependencies terinstal dengan benar
4. Gunakan fallback DOCX template jika diperlukan