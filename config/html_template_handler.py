import os
import tempfile
import shutil
from datetime import datetime
import qrcode
from io import BytesIO
import base64

class HtmlTemplateHandler:
    def __init__(self):
        # Try simple template first, fallback to complex one
        self.template_path = 'static/assets/templates/form_cuti_simple.html'
        if not os.path.exists(self.template_path):
            self.template_path = 'static/assets/templates/form_permintaan_cuti copy.html'
        
        self.output_folder = 'static/pdf_cuti'
        self.signatures_folder = 'static/signatures'
        
        # Create output directories
        os.makedirs(self.output_folder, exist_ok=True)
        os.makedirs(self.signatures_folder, exist_ok=True)
    
    def create_qr_code(self, cuti_data, signature_hash):
        """Create QR code for digital signature"""
        try:
            # Data untuk QR code
            qr_data = f"PERSETUJUAN CUTI\n"
            qr_data += f"ID: {cuti_data.id_cuti}\n"
            qr_data += f"Nama: {cuti_data.nama}\n"
            qr_data += f"NIP: {cuti_data.nip}\n"
            qr_data += f"Jenis: {cuti_data.jenis_cuti}\n"
            qr_data += f"Periode: {cuti_data.tanggal_cuti.strftime('%Y-%m-%d')} s/d {cuti_data.sampai_cuti.strftime('%Y-%m-%d')}\n"
            qr_data += f"Tanggal: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
            qr_data += f"Hash: {signature_hash}\n"
            qr_data += f"Verifikasi: https://your-domain.com/verify/{signature_hash}"
            
            # Generate QR code
            qr = qrcode.QRCode(
                version=1,
                error_correction=qrcode.constants.ERROR_CORRECT_L,
                box_size=10,
                border=4,
            )
            qr.add_data(qr_data)
            qr.make(fit=True)
            
            # Create QR code image
            qr_img = qr.make_image(fill_color="black", back_color="white")
            
            # Save QR code file
            qr_filename = f"qr_cuti_{cuti_data.id_cuti}_{signature_hash}.png"
            qr_path = os.path.join(self.signatures_folder, qr_filename)
            qr_img.save(qr_path)
            
            return qr_path
            
        except Exception as e:
            print(f"Error creating QR code: {str(e)}")
            return None
    
    def generate_signature_hash(self, cuti_data):
        """Generate unique hash for digital signature"""
        import hashlib
        signature_string = f"{cuti_data.id_cuti}_{cuti_data.nama}_{cuti_data.nip}_{datetime.now().isoformat()}"
        return hashlib.sha256(signature_string.encode()).hexdigest()[:16]
    
    def format_jenis_cuti(self, jenis_cuti):
        """Convert jenis_cuti code to readable format"""
        jenis_map = {
            'c_tahun': 'Cuti Tahunan',
            'c_besar': 'Cuti Besar',
            'c_sakit': 'Cuti Sakit',
            'c_lahir': 'Cuti Melahirkan',
            'c_penting': 'Cuti Alasan Penting',
            'c_luarnegara': 'Cuti Luar Negara'
        }
        return jenis_map.get(jenis_cuti, jenis_cuti)
    
    def format_date_indonesian(self, date_obj):
        """Format date to Indonesian format"""
        if not date_obj:
            return ""
        
        months = [
            'Januari', 'Februari', 'Maret', 'April', 'Mei', 'Juni',
            'Juli', 'Agustus', 'September', 'Oktober', 'November', 'Desember'
        ]
        
        return f"{date_obj.day} {months[date_obj.month - 1]} {date_obj.year}"
    
    def replace_placeholders_in_html(self, html_content, cuti_data, signature_hash):
        """Replace placeholders in HTML content with actual data"""
        try:
            # Create replacement dictionary with the format used in template
            replacements = {
                '«nama»': cuti_data.nama,
                '«nip»': cuti_data.nip,
                '«jabatan»': cuti_data.jabatan,
                '«gol_ruang»': cuti_data.gol_ruang,
                '«unit_kerja»': cuti_data.unit_kerja,
                '«masa_kerja»': cuti_data.masa_kerja,
                '«alamat»': cuti_data.alamat,
                '«telp»': cuti_data.telp,
                '«no_suratmasuk»': cuti_data.no_suratmasuk,
                '«tgl_lengkap_ajuan_cuti»': self.format_date_indonesian(cuti_data.tgl_ajuan_cuti),
                '«bulan_ajuan_cuti»': str(cuti_data.tgl_ajuan_cuti.month).zfill(2),
                '«tahun_ajuan_cuti»': str(cuti_data.tgl_ajuan_cuti.year),
                '«alasan_cuti»': cuti_data.alasan_cuti,
                '«lama_cuti»': cuti_data.lama_cuti.replace(' hari', ''),  # Remove 'hari' as template has it
                '«tanggal_cuti»': self.format_date_indonesian(cuti_data.tanggal_cuti),
                '«sampai_cuti»': self.format_date_indonesian(cuti_data.sampai_cuti),
                # Jenis cuti checkboxes - mark the selected one
                '«c_tahun»': '✓' if cuti_data.jenis_cuti == 'c_tahun' else '',
                '«c_besar»': '✓' if cuti_data.jenis_cuti == 'c_besar' else '',
                '«c_sakit»': '✓' if cuti_data.jenis_cuti == 'c_sakit' else '',
                '«c_lahir»': '✓' if cuti_data.jenis_cuti == 'c_lahir' else '',
                '«c_penting»': '✓' if cuti_data.jenis_cuti == 'c_penting' else '',
                '«c_luarnegara»': '✓' if cuti_data.jenis_cuti == 'c_luarnegara' else '',
            }
            
            # Replace all placeholders in HTML content
            for placeholder, value in replacements.items():
                html_content = html_content.replace(placeholder, str(value))
            
            # Handle logo embedding for PDF generation
            html_content = self.embed_logo_in_html(html_content)
            
            return html_content
            
        except Exception as e:
            print(f"Error replacing placeholders: {str(e)}")
            return html_content
    
    def embed_logo_in_html(self, html_content):
        """Embed logo as base64 data for reliable PDF generation"""
        try:
            logo_path = 'static/assets/images/logo-pengadilan-agama.png'
            
            if os.path.exists(logo_path):
                with open(logo_path, 'rb') as logo_file:
                    logo_data = logo_file.read()
                    logo_base64 = base64.b64encode(logo_data).decode('utf-8')
                    
                    # Replace the logo src with base64 data
                    old_src = 'src="/static/assets/images/logo-pengadilan-agama.png"'
                    new_src = f'src="data:image/png;base64,{logo_base64}"'
                    html_content = html_content.replace(old_src, new_src)
                    
                    print("✅ Logo embedded as base64 data for PDF generation")
            else:
                print(f"⚠️ Logo file not found at: {logo_path}")
                
        except Exception as e:
            print(f"Error embedding logo: {str(e)}")
            
        return html_content
    
    def html_to_pdf_weasyprint(self, html_content, pdf_path):
        """Convert HTML to PDF using WeasyPrint"""
        try:
            from weasyprint import HTML, CSS
            from weasyprint.text.fonts import FontConfiguration
            
            # Create font configuration
            font_config = FontConfiguration()
            
            # Create PDF from HTML with proper configuration
            HTML(string=html_content).write_pdf(
                pdf_path,
                font_config=font_config
            )
            
            print(f"✅ PDF generated successfully with WeasyPrint: {pdf_path}")
            return True
            
        except ImportError as e:
            print(f"WeasyPrint not available: {str(e)}")
            return False
        except Exception as e:
            print(f"Error converting HTML to PDF with WeasyPrint: {str(e)}")
            import traceback
            traceback.print_exc()
            return False
    
    def html_to_pdf_playwright(self, html_content, pdf_path):
        """Convert HTML to PDF using Playwright"""
        try:
            from playwright.sync_api import sync_playwright
            
            with sync_playwright() as p:
                browser = p.chromium.launch()
                page = browser.new_page()
                page.set_content(html_content)
                page.pdf(path=pdf_path, format='A4', margin={'top': '2cm', 'right': '2cm', 'bottom': '2cm', 'left': '2cm'})
                browser.close()
            
            return True
            
        except ImportError:
            print("Playwright not available")
            return False
        except Exception as e:
            print(f"Error converting HTML to PDF with Playwright: {str(e)}")
            return False
    
    def html_to_pdf_reportlab(self, html_content, pdf_path):
        """Convert HTML to PDF using ReportLab (basic HTML parsing)"""
        try:
            from reportlab.lib.pagesizes import A4
            from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
            from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
            from reportlab.lib.units import inch, cm
            from reportlab.lib import colors
            from reportlab.lib.enums import TA_CENTER, TA_LEFT
            from bs4 import BeautifulSoup
            
            # Parse HTML content
            soup = BeautifulSoup(html_content, 'html.parser')
            
            # Create PDF
            doc = SimpleDocTemplate(
                pdf_path, 
                pagesize=A4,
                rightMargin=2*cm,
                leftMargin=2*cm,
                topMargin=2*cm,
                bottomMargin=2*cm
            )
            
            styles = getSampleStyleSheet()
            
            # Custom styles
            title_style = ParagraphStyle(
                'CustomTitle',
                parent=styles['Heading1'],
                fontSize=14,
                textColor=colors.black,
                spaceAfter=12,
                alignment=TA_CENTER,
                fontName='Helvetica-Bold'
            )
            
            normal_style = ParagraphStyle(
                'CustomNormal',
                parent=styles['Normal'],
                fontSize=10,
                textColor=colors.black,
                spaceAfter=6,
                alignment=TA_LEFT
            )
            
            story = []
            
            # Add title
            story.append(Paragraph("FORMULIR PERMINTAAN CUTI", title_style))
            story.append(Spacer(1, 0.5*cm))
            
            # Extract text content and convert to PDF
            for element in soup.find_all(['p', 'div', 'h1', 'h2', 'h3', 'td', 'th']):
                text = element.get_text().strip()
                if text and len(text) > 2:  # Skip very short texts
                    if element.name in ['h1', 'h2', 'h3']:
                        story.append(Paragraph(text, title_style))
                    else:
                        story.append(Paragraph(text, normal_style))
                    story.append(Spacer(1, 0.2*cm))
            
            # Build PDF
            doc.build(story)
            print(f"✅ PDF generated successfully with ReportLab: {pdf_path}")
            return True
            
        except ImportError as e:
            print(f"ReportLab or BeautifulSoup not available: {str(e)}")
            return False
        except Exception as e:
            print(f"Error converting HTML to PDF with ReportLab: {str(e)}")
            import traceback
            traceback.print_exc()
            return False
    
    def generate_pdf_direct_reportlab(self, cuti_data, pdf_path):
        """Generate PDF directly using ReportLab without HTML template"""
        try:
            from reportlab.lib.pagesizes import A4
            from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
            from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
            from reportlab.lib.units import cm
            from reportlab.lib import colors
            from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_JUSTIFY
            
            # Create PDF
            doc = SimpleDocTemplate(
                pdf_path,
                pagesize=A4,
                rightMargin=2*cm,
                leftMargin=2*cm,
                topMargin=2*cm,
                bottomMargin=2*cm
            )
            
            styles = getSampleStyleSheet()
            
            # Custom styles
            title_style = ParagraphStyle(
                'Title',
                parent=styles['Heading1'],
                fontSize=16,
                textColor=colors.black,
                spaceAfter=20,
                alignment=TA_CENTER,
                fontName='Helvetica-Bold'
            )
            
            heading_style = ParagraphStyle(
                'Heading',
                parent=styles['Heading2'],
                fontSize=12,
                textColor=colors.black,
                spaceAfter=10,
                fontName='Helvetica-Bold'
            )
            
            normal_style = ParagraphStyle(
                'Normal',
                parent=styles['Normal'],
                fontSize=10,
                textColor=colors.black,
                spaceAfter=6,
                alignment=TA_LEFT
            )
            
            story = []
            
            # Title
            story.append(Paragraph("FORMULIR PERMINTAAN CUTI", title_style))
            story.append(Spacer(1, 0.5*cm))
            
            # Data Pegawai
            story.append(Paragraph("I. DATA PEGAWAI", heading_style))
            
            data_pegawai = [
                ['Nama', ':', cuti_data.nama],
                ['NIP', ':', cuti_data.nip],
                ['Jabatan', ':', cuti_data.jabatan],
                ['Golongan/Ruang', ':', cuti_data.gol_ruang],
                ['Unit Kerja', ':', cuti_data.unit_kerja],
                ['Masa Kerja', ':', cuti_data.masa_kerja],
                ['Alamat', ':', cuti_data.alamat],
                ['Nomor Telepon', ':', cuti_data.telp],
            ]
            
            table = Table(data_pegawai, colWidths=[4*cm, 0.5*cm, 11*cm])
            table.setStyle(TableStyle([
                ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
                ('FONTSIZE', (0, 0), (-1, -1), 10),
                ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                ('LEFTPADDING', (0, 0), (-1, -1), 0),
                ('RIGHTPADDING', (0, 0), (-1, -1), 0),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
            ]))
            story.append(table)
            story.append(Spacer(1, 0.5*cm))
            
            # Data Cuti
            story.append(Paragraph("II. JENIS CUTI YANG DIMOHONKAN", heading_style))
            story.append(Paragraph(f"Jenis Cuti: {self.format_jenis_cuti(cuti_data.jenis_cuti)}", normal_style))
            story.append(Spacer(1, 0.3*cm))
            
            data_cuti = [
                ['Alasan Cuti', ':', cuti_data.alasan_cuti],
                ['Lama Cuti', ':', cuti_data.lama_cuti],
                ['Tanggal Mulai', ':', self.format_date_indonesian(cuti_data.tanggal_cuti)],
                ['Tanggal Selesai', ':', self.format_date_indonesian(cuti_data.sampai_cuti)],
                ['Tanggal Ajuan', ':', self.format_date_indonesian(cuti_data.tgl_ajuan_cuti)],
                ['No. Surat Masuk', ':', cuti_data.no_suratmasuk],
            ]
            
            table2 = Table(data_cuti, colWidths=[4*cm, 0.5*cm, 11*cm])
            table2.setStyle(TableStyle([
                ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
                ('FONTSIZE', (0, 0), (-1, -1), 10),
                ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                ('LEFTPADDING', (0, 0), (-1, -1), 0),
                ('RIGHTPADDING', (0, 0), (-1, -1), 0),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
            ]))
            story.append(table2)
            story.append(Spacer(1, 1*cm))
            
            # Signature section
            story.append(Paragraph("Pemohon,", normal_style))
            story.append(Spacer(1, 1.5*cm))
            story.append(Paragraph(f"({cuti_data.nama})", normal_style))
            story.append(Paragraph(f"NIP. {cuti_data.nip}", normal_style))
            
            # Build PDF
            doc.build(story)
            print(f"✅ PDF generated successfully with direct ReportLab: {pdf_path}")
            return True
            
        except Exception as e:
            print(f"Error generating PDF with direct ReportLab: {str(e)}")
            import traceback
            traceback.print_exc()
            return False
    
    def fill_template_and_generate_pdf(self, cuti_data):
        """Main function to fill HTML template and generate PDF"""
        try:
            # Check if template exists
            if not os.path.exists(self.template_path):
                raise FileNotFoundError(f"Template not found: {self.template_path}")
            
            # Generate signature hash
            signature_hash = self.generate_signature_hash(cuti_data)
            
            # Create QR code
            qr_path = self.create_qr_code(cuti_data, signature_hash)
            
            # Read HTML template
            with open(self.template_path, 'r', encoding='utf-8') as file:
                html_content = file.read()
            
            # Replace placeholders
            html_content = self.replace_placeholders_in_html(html_content, cuti_data, signature_hash)
            
            # Add QR code to HTML if created
            if qr_path and os.path.exists(qr_path):
                # Convert QR code to base64 for embedding
                with open(qr_path, 'rb') as qr_file:
                    qr_base64 = base64.b64encode(qr_file.read()).decode('utf-8')
                    qr_img_tag = f'<img src="data:image/png;base64,{qr_base64}" style="width: 100px; height: 100px;" />'
                    
                    # Replace QR placeholder or add at the end
                    if '{{QR_CODE}}' in html_content:
                        html_content = html_content.replace('{{QR_CODE}}', qr_img_tag)
                    else:
                        # Add QR code before closing body tag
                        html_content = html_content.replace('</body>', f'{qr_img_tag}</body>')
            
            # Generate PDF filename
            pdf_filename = f"surat_cuti_{cuti_data.id_cuti}_{signature_hash}.pdf"
            pdf_path = os.path.join(self.output_folder, pdf_filename)
            
            # Try multiple PDF conversion methods
            pdf_success = False
            
            # Method 1: Try WeasyPrint first (best HTML rendering)
            if not pdf_success:
                print("Trying WeasyPrint...")
                pdf_success = self.html_to_pdf_weasyprint(html_content, pdf_path)
            
            # Method 2: Try Playwright as fallback
            if not pdf_success:
                print("Trying Playwright...")
                pdf_success = self.html_to_pdf_playwright(html_content, pdf_path)
            
            # Method 3: Try ReportLab with HTML parsing
            if not pdf_success:
                print("Trying ReportLab with HTML...")
                pdf_success = self.html_to_pdf_reportlab(html_content, pdf_path)
            
            # Method 4: Direct PDF generation with ReportLab (no HTML)
            if not pdf_success:
                print("Trying direct ReportLab generation...")
                pdf_success = self.generate_pdf_direct_reportlab(cuti_data, pdf_path)
            
            if pdf_success:
                return {
                    'success': True,
                    'pdf_path': pdf_path,
                    'qr_path': qr_path,
                    'signature_hash': signature_hash
                }
            else:
                raise Exception("Failed to convert HTML to PDF - no PDF library available")
                
        except Exception as e:
            print(f"Error in fill_template_and_generate_pdf: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }