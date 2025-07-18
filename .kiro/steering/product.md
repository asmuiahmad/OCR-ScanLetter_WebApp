# Product Overview

## OCR Scan Letter WebApp

A Flask-based document management system for Indonesian government offices (specifically Pengadilan Agama Watampone) that handles incoming/outgoing letters and leave applications with OCR capabilities.

### Core Features
- **Document OCR Processing**: Extract text from scanned letter images using Tesseract OCR
- **Letter Management**: Handle incoming (surat masuk) and outgoing (surat keluar) letters with approval workflows
- **Leave Management**: Process leave applications (cuti) with digital signature verification via QR codes
- **User Authentication**: Role-based access (admin, supervisor, karyawan/employee)
- **Document Generation**: Auto-generate PDF documents with digital signatures

### Target Users
- Government office employees submitting letters and leave requests
- Supervisors approving outgoing letters and leave applications
- Administrators managing the system and users

### Key Workflows
1. **Letter Processing**: Upload → OCR extraction → Manual verification → Database storage
2. **Approval Process**: Submit → Pending → Supervisor review → Approve/Reject
3. **Digital Signatures**: Generate QR codes for approved documents with verification URLs