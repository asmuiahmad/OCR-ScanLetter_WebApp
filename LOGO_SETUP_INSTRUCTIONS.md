# Logo Setup Instructions

## Adding the Official Pengadilan Agama Logo

The PDF template has been configured to use the official Pengadilan Agama logo. Follow these steps to add the logo:

### Step 1: Save the Logo File

1. **Save the logo image** you provided as `logo-pengadilan-agama.png`
2. **Place it in the directory**: `static/assets/images/`
3. **Full path should be**: `static/assets/images/logo-pengadilan-agama.png`

### Step 2: Logo Specifications

The template is optimized for:
- **Size**: 90x90 pixels (automatically resized)
- **Format**: PNG (recommended) or JPG
- **Background**: Transparent (PNG) or white background
- **Quality**: High resolution for clear PDF output

### Step 3: Verify Setup

After adding the logo file:

1. **Generate a cuti form** through the web interface
2. **Check the PDF output** - the official logo should appear in the header
3. **If logo doesn't appear**: The template will automatically show a fallback placeholder

### Current Template Configuration

✅ **Logo is active** in the template  
✅ **Automatic fallback** if logo file is missing  
✅ **Proper sizing** (90x90px with drop shadow)  
✅ **Centered positioning** in header  

### Template Features with Logo

- **Professional header** with official Pengadilan Agama logo
- **Centered layout** with logo above institution name
- **Drop shadow effect** for visual depth
- **Responsive design** that works on all devices
- **Print-optimized** for PDF generation

### Troubleshooting

If the logo doesn't appear:

1. **Check file path**: Ensure the file is at `static/assets/images/logo-pengadilan-agama.png`
2. **Check file size**: Make sure the file is not empty (should be > 0 bytes)
3. **Check file format**: Use PNG or JPG format
4. **Check permissions**: Ensure the web server can read the file

### Alternative Logo Path

If you need to use a different path, update this line in `static/assets/templates/form_cuti_simple.html`:

```html
<img src="/static/assets/images/logo-pengadilan-agama.png" 
     alt="Logo Pengadilan Agama" 
     class="logo-image">
```

Change the `src` attribute to your preferred path.

---

**Note**: The template includes automatic fallback functionality. If the logo file is not found, it will display a placeholder instead of breaking the layout.