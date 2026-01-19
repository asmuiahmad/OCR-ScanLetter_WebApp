# PDF Template Documentation

## Form Cuti Simple Template

The `form_cuti_simple.html` template has been redesigned with professional government document styling for Pengadilan Agama with a **centered header layout**.

### Features

✅ **Professional Centered Design**
- Official government document styling with centered header
- Logo and institution name prominently displayed in center
- Green color scheme (#2c5530) matching Pengadilan Agama branding
- Modern typography with Times New Roman font
- Structured sections with borders and backgrounds

✅ **Enhanced Header Layout**
- **Centered logo placeholder** (100x100px with shadow effect)
- **Centered institution name** "Pengadilan Agama [Unit Kerja]"
- **Centered Mahkamah Agung** subtitle
- **Centered address and contact** information
- Professional double-line border separator

✅ **Complete Form Sections**
- Employee data section (Data Pegawai)
- Leave type selection with checkboxes (Jenis Cuti)
- Leave details (Detail Permohonan Cuti)
- Signature sections for employee and supervisor
- Decision section for approval/rejection
- QR code for digital verification

✅ **Responsive & Print-Ready**
- A4 page size with proper margins
- Print-optimized CSS
- Mobile-responsive design
- Watermark background

### Header Structure

The header now features a **fully centered layout**:

```
        [LOGO]
    
PENGADILAN AGAMA [UNIT KERJA]
Mahkamah Agung Republik Indonesia

Jl. Alamat No. 123, Kota, Provinsi
Telp: (021) 1234-5678 | Email: info@pa.go.id
```

### Adding Official Logo

To replace the logo placeholder with the actual Pengadilan Agama logo:

1. **Add logo file** to `static/assets/images/` (e.g., `logo-pa.png`)

2. **Update template** in `form_cuti_simple.html`:
   ```html
   <!-- Comment out placeholder -->
   <!-- <div class="logo-placeholder">...</div> -->
   
   <!-- Uncomment and update logo image -->
   <img src="/static/assets/images/logo-pa.png" alt="Logo Pengadilan Agama" class="logo-image">
   ```

3. **Recommended logo specifications**:
   - Format: PNG or SVG
   - Size: 100x100 pixels (square)
   - Background: Transparent
   - Colors: Official Pengadilan Agama colors

### Template Variables

The template uses the following placeholder variables:

**Employee Data:**
- `«nama»` - Full name
- `«nip»` - Employee ID number
- `«jabatan»` - Position/job title
- `«gol_ruang»` - Grade/rank
- `«unit_kerja»` - Work unit (also used in header)
- `«masa_kerja»` - Years of service
- `«alamat»` - Address
- `«telp»` - Phone number

**Leave Data:**
- `«jenis_cuti»` - Leave type (used for checkboxes)
- `«alasan_cuti»` - Reason for leave
- `«lama_cuti»` - Duration of leave
- `«tanggal_cuti»` - Start date
- `«sampai_cuti»` - End date
- `«tgl_lengkap_ajuan_cuti»` - Application date
- `«no_suratmasuk»` - Incoming letter number

**Leave Type Checkboxes:**
- `«c_tahun»` - Annual leave
- `«c_besar»` - Long leave
- `«c_sakit»` - Sick leave
- `«c_lahir»` - Maternity leave
- `«c_penting»` - Important reason leave
- `«c_luarnegara»` - Overseas leave

### Testing

To test the template:

1. **Generate a cuti form** through the web interface
2. **Check the PDF output** in `static/pdf_cuti/`
3. **Verify styling** by opening the HTML preview

### Customization

The template can be customized by modifying:

- **Colors**: Change `#2c5530` to your preferred color scheme
- **Fonts**: Update font-family in CSS
- **Layout**: Adjust margins, padding, and spacing
- **Header alignment**: Modify `.official-header` and `.logo-section` CSS
- **Sections**: Add or remove form sections as needed

### Browser Compatibility

The template is optimized for:
- Chrome/Chromium (best PDF rendering)
- Firefox
- Safari
- Edge

For best PDF generation results, ensure WeasyPrint or Playwright is installed.