# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.0.0] - 2024-01-XX

### Added
- OCR processing untuk surat masuk dan surat keluar
- Sistem autentikasi dengan role admin dan pimpinan
- Manajemen surat masuk (input, edit, lihat)
- Manajemen surat keluar dengan sistem persetujuan
- Dashboard dengan statistik dan laporan
- Generate dokumen surat cuti otomatis
- Upload dan drag-and-drop interface
- Search dan pagination untuk daftar surat
- Toast notifications untuk feedback user
- OCR test page untuk testing ekstraksi teks

### Changed
- Menghapus fitur persetujuan untuk surat masuk
- Surat masuk langsung berstatus "Disetujui"
- Hanya surat keluar yang memerlukan persetujuan pimpinan
- Memperbaiki UI/UX untuk konsistensi antar halaman
- Mengganti OpenCV dengan PIL untuk image processing

### Fixed
- Error "No module named 'cv2'" dengan menggunakan PIL
- Masalah upload file yang memerlukan dua kali klik
- Tombol "Pilih Dokumen" yang tidak clickable
- IndentationError di routes.py
- Masalah sidebar navigation untuk halaman surat keluar
- Template yang tidak menampilkan data surat masuk

### Removed
- Fitur persetujuan surat masuk
- Route approve/reject surat masuk
- Menu pending surat masuk dari sidebar
- Template yang tidak diperlukan (list_pending_surat_keluar.html, detail_surat_keluar.html)
- Perhitungan pending count untuk surat masuk

## [Unreleased]

### Planned
- Export data ke Excel/PDF
- Backup dan restore database
- Multi-language support
- API endpoints untuk integrasi
- Advanced OCR dengan machine learning
- Mobile responsive design improvements 