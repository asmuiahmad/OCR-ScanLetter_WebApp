"""
Advanced DOCX Template Handler
Uses docxtpl for better template filling and multiple PDF conversion methods
"""

import os
import tempfile
import shutil
from datetime import datetime
import qrcode
from io import BytesIO
import base64
from docxtpl import DocxTemplate

class AdvancedDocxTemplateHandler:
    def __init__(self):
        # Try to find the best template
        self.template_path = 'static/assets/templates/form_permintaan_cuti.docx'
        if not os.path.exists(self.template_path):
            # Fallback to any docx template in the folder
            template_folder = 'static/assets/templates'
            for file in os.listdir(template_folder):
                if file.endswith('.docx'):
                    self.template_path = os.path.join(template_folder, file)
                    break
        
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
    
    def prepare_template_data(self, cuti_data, signature_hash):
        """Prepare data dictionary for template filling"""
        try:
            # Create data dictionary with all possible placeholders
            template_data = {
                # Basic employee data
                'nama': cuti_data.nama,
                'nip': cuti_data.nip,
                'jabatan': cuti_data.jabatan,
                'gol_ruang': cuti_data.gol_ruang,
                'unit_kerja': cuti_data.unit_kerja,
                'masa_kerja': cuti_data.masa_kerja,
                'alamat': cuti_data.alamat,
                'telp': cuti_data.telp,
                'no_suratmasuk': cuti_data.no_suratmasuk,
                
                # Date formatting
                'tgl_lengkap_ajuan_cuti': self.format_date_indonesian(cuti_data.tgl_ajuan_cuti),
                'bulan_ajuan_cuti': str(cuti_data.tgl_ajuan_cuti.month).zfill(2),
                'tahun_ajuan_cuti': str(cuti_data.tgl_ajuan_cuti.year),
                'tanggal_cuti': self.format_date_indonesian(cuti_data.tanggal_cuti),
                'sampai_cuti': self.format_date_indonesian(cuti_data.sampai_cuti),
                
                # Leave data
                'alasan_cuti': cuti_data.alasan_cuti,
                'lama_cuti': cuti_data.lama_cuti.replace(' hari', ''),  # Remove 'hari' as template might have it
                'jenis_cuti': self.format_jenis_cuti(cuti_data.jenis_cuti),
                
                # Checkbox values for different leave types
                'c_tahun': '✓' if cuti_data.jenis_cuti == 'c_tahun' else '☐',
                'c_besar': '✓' if cuti_data.jenis_cuti == 'c_besar' else '☐',
                'c_sakit': '✓' if cuti_data.jenis_cuti == 'c_sakit' else '☐',
                'c_lahir': '✓' if cuti_data.jenis_cuti == 'c_lahir' else '☐',
                'c_penting': '✓' if cuti_data.jenis_cuti == 'c_penting' else '☐',
                'c_luarnegara': '✓' if cuti_data.jenis_cuti == 'c_luarnegara' else '☐',
                
                # Additional data
                'signature_hash': signature_hash,
                'generated_date': datetime.now().strftime('%d %B %Y'),
                'generated_time': datetime.now().strftime('%H:%M:%S'),
            }
            
            return template_data
            
        except Exception as e:
            print(f"Error preparing template data: {str(e)}")
            return {}
    
    def docx_to_pdf_libreoffice(self, docx_path, pdf_path):
        """Convert DOCX to PDF using LibreOffice"""
        try:
            import subprocess
            
            # Get the directory of the docx file
            docx_dir = os.path.dirname(docx_path)
            
            # Run LibreOffice conversion
            result = subprocess.run([
                'libreoffice', '--headless', '--convert-to', 'pdf',
                '--outdir', docx_dir, docx_path
            ], capture_output=True, text=True, timeout=30)
            
            if result.returncode == 0:
                # LibreOffice creates PDF with same name as DOCX
                docx_filename = os.path.basename(docx_path)
                pdf_filename = docx_filename.replace('.docx', '.pdf')
                generated_pdf = os.path.join(docx_dir, pdf_filename)
                
                if os.path.exists(generated_pdf):
                    # Move to desired location
                    shutil.move(generated_pdf, pdf_path)
                    return True
            
            print(f"LibreOffice conversion failed: {result.stderr}")
            return False
            
        except subprocess.TimeoutExpired:
            print("LibreOffice conversion timed out")
            return False
        except FileNotFoundError:
            print("LibreOffice not found")
            return False
        except Exception as e:
            print(f"Error converting DOCX to PDF with LibreOffice: {str(e)}")
            return False
    
    def docx_to_pdf_docx2pdf(self, docx_path, pdf_path):
        """Convert DOCX to PDF using docx2pdf"""
        try:
            from docx2pdf import convert
            
            # Convert directly to the desired path
            convert(docx_path, pdf_path)
            
            return os.path.exists(pdf_path)
            
        except ImportError:
            print("docx2pdf not available")
            return False
        except Exception as e:
            print(f"Error converting DOCX to PDF with docx2pdf: {str(e)}")
            return False
    
    def docx_to_pdf_pypandoc(self, docx_path, pdf_path):
        """Convert DOCX to PDF using pypandoc"""
        try:
            import pypandoc
            
            # Convert using pandoc
            pypandoc.convert_file(docx_path, 'pdf', outputfile=pdf_path)
            
            return os.path.exists(pdf_path)
            
        except ImportError:
            print("pypandoc not available")
            return False
        except Exception as e:
            print(f"Error converting DOCX to PDF with pypandoc: {str(e)}")
            return False
    
    def fill_template_and_generate_pdf(self, cuti_data):
        """Main function to fill DOCX template and generate PDF"""
        try:
            # Check if template exists
            if not os.path.exists(self.template_path):
                raise FileNotFoundError(f"Template not found: {self.template_path}")
            
            # Generate signature hash
            signature_hash = self.generate_signature_hash(cuti_data)
            
            # Create QR code
            qr_path = self.create_qr_code(cuti_data, signature_hash)
            
            # Load template using docxtpl
            doc = DocxTemplate(self.template_path)
            
            # Prepare data for template
            template_data = self.prepare_template_data(cuti_data, signature_hash)
            
            # Add QR code to template data if available
            if qr_path and os.path.exists(qr_path):
                # For docxtpl, we can embed images directly
                from docxtpl import InlineImage
                from docx.shared import Mm
                
                try:
                    qr_image = InlineImage(doc, qr_path, width=Mm(25))
                    template_data['qr_code'] = qr_image
                except Exception as e:
                    print(f"Could not embed QR code: {e}")
                    template_data['qr_code'] = '[QR CODE]'
            else:
                template_data['qr_code'] = '[QR CODE]'
            
            # Fill template with data
            doc.render(template_data)
            
            # Save filled DOCX
            filled_docx = os.path.join(self.output_folder, f"filled_cuti_{cuti_data.id_cuti}_{signature_hash}.docx")
            doc.save(filled_docx)
            
            # Generate PDF filename
            pdf_filename = f"surat_cuti_{cuti_data.id_cuti}_{signature_hash}.pdf"
            pdf_path = os.path.join(self.output_folder, pdf_filename)
            
            # Try multiple PDF conversion methods
            pdf_success = False
            
            # Try docx2pdf first (works on Windows/Mac with MS Office)
            if not pdf_success:
                pdf_success = self.docx_to_pdf_docx2pdf(filled_docx, pdf_path)
            
            # Try LibreOffice as fallback
            if not pdf_success:
                pdf_success = self.docx_to_pdf_libreoffice(filled_docx, pdf_path)
            
            # Try pypandoc as last resort
            if not pdf_success:
                pdf_success = self.docx_to_pdf_pypandoc(filled_docx, pdf_path)
            
            if pdf_success:
                # Clean up temporary DOCX file
                try:
                    os.remove(filled_docx)
                except:
                    pass
                
                return {
                    'success': True,
                    'pdf_path': pdf_path,
                    'qr_path': qr_path,
                    'signature_hash': signature_hash
                }
            else:
                # If PDF conversion fails, clean up and return failure
                # This allows the system to fall back to HTML template handler
                try:
                    os.remove(filled_docx)
                except:
                    pass
                
                return {
                    'success': False,
                    'error': 'PDF conversion failed - no PDF converter available (docx2pdf, LibreOffice, or pypandoc)'
                }
                
        except Exception as e:
            print(f"Error in fill_template_and_generate_pdf: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }