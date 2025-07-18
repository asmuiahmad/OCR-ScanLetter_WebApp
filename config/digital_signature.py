import qrcode
import base64
import io
import os
from datetime import datetime
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
import hashlib
import secrets

class DigitalSignature:
    def __init__(self):
        self.signature_folder = 'static/signatures'
        self.pdf_folder = 'static/pdf_cuti'
        os.makedirs(self.signature_folder, exist_ok=True)
        os.makedirs(self.pdf_folder, exist_ok=True)
    
    def generate_signature_hash(self, cuti_data, approver_info):
        """Generate unique hash untuk digital signature"""
        signature_string = f"{cuti_data.id_cuti}_{cuti_data.nama}_{cuti_data.nip}_{approver_info['name']}_{datetime.now().isoformat()}"
        return hashlib.sha256(signature_string.encode()).hexdigest()[:16]
    
    def create_qr_code(self, cuti_data, approver_info):
        """Membuat QR code untuk digital signature"""
        try:
            # Generate signature hash
            signature_hash = self.generate_signature_hash(cuti_data, approver_info)
            
            # Data untuk QR code
            qr_data = {
                'id_cuti': cuti_data.id_cuti,
                'nama': cuti_data.nama,
                'nip': cuti_data.nip,
                'jenis_cuti': cuti_data.jenis_cuti,
                'tanggal_cuti': cuti_data.tanggal_cuti.strftime('%Y-%m-%d'),
                'sampai_cuti': cuti_data.sampai_cuti.strftime('%Y-%m-%d'),
                'approved_by': approver_info['name'],
                'approved_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'signature_hash': signature_hash,
                'verification_url': f"https://your-domain.com/verify/{signature_hash}"
            }
            
            # Convert to string
            qr_string = f"PERSETUJUAN CUTI\n"
            qr_string += f"ID: {qr_data['id_cuti']}\n"
            qr_string += f"Nama: {qr_data['nama']}\n"
            qr_string += f"NIP: {qr_data['nip']}\n"
            qr_string += f"Jenis: {qr_data['jenis_cuti']}\n"
            qr_string += f"Periode: {qr_data['tanggal_cuti']} s/d {qr_data['sampai_cuti']}\n"
            qr_string += f"Disetujui oleh: {qr_data['approved_by']}\n"
            qr_string += f"Tanggal Persetujuan: {qr_data['approved_at']}\n"
            qr_string += f"Hash: {qr_data['signature_hash']}\n"
            qr_string += f"Verifikasi: {qr_data['verification_url']}"
            
            # Generate QR code
            qr = qrcode.QRCode(
                version=1,
                error_correction=qrcode.constants.ERROR_CORRECT_L,
                box_size=10,
                border=4,
            )
            qr.add_data(qr_string)
            qr.make(fit=True)
            
            # Create QR code image
            qr_img = qr.make_image(fill_color="black", back_color="white")
            
            # Convert to base64 string
            buffer = io.BytesIO()
            qr_img.save(buffer, format='PNG')
            qr_base64 = base64.b64encode(buffer.getvalue()).decode()
            
            # Save QR code file
            qr_filename = f"qr_cuti_{cuti_data.id_cuti}_{signature_hash}.png"
            qr_path = os.path.join(self.signature_folder, qr_filename)
            qr_img.save(qr_path)
            
            return {
                'qr_base64': qr_base64,
                'qr_path': qr_path,
                'signature_hash': signature_hash,
                'qr_data': qr_data
            }
            
        except Exception as e:
            print(f"Error creating QR code: {str(e)}")
            return None
    
    def generate_pdf_surat_cuti(self, cuti_data, qr_info, approver_info):
        """Generate PDF surat persetujuan cuti dengan QR code"""
        try:
            # Create PDF filename
            pdf_filename = f"surat_cuti_{cuti_data.id_cuti}_{qr_info['signature_hash']}.pdf"
            pdf_path = os.path.join(self.pdf_folder, pdf_filename)
            
            # Create PDF document
            doc = SimpleDocTemplate(pdf_path, pagesize=A4)
            styles = getSampleStyleSheet()
            story = []
            
            # Custom styles
            title_style = ParagraphStyle(
                'CustomTitle',
                parent=styles['Heading1'],
                fontSize=16,
                spaceAfter=30,
                alignment=TA_CENTER,
                fontName='Helvetica-Bold'
            )
            
            header_style = ParagraphStyle(
                'CustomHeader',
                parent=styles['Normal'],
                fontSize=12,
                alignment=TA_CENTER,
                fontName='Helvetica-Bold'
            )
            
            normal_style = ParagraphStyle(
                'CustomNormal',
                parent=styles['Normal'],
                fontSize=10,
                spaceAfter=6,
                fontName='Helvetica'
            )
            
            # Header
            story.append(Paragraph("PENGADILAN AGAMA WATAMPONE", header_style))
            story.append(Paragraph("KELAS I A", header_style))
            story.append(Spacer(1, 20))
            
            # Title
            story.append(Paragraph("SURAT PERSETUJUAN CUTI", title_style))
            story.append(Paragraph(f"Nomor: {cuti_data.no_suratmasuk}", normal_style))
            story.append(Spacer(1, 20))
            
            # Data pegawai dalam tabel
            data_pegawai = [
                ['Nama', ':', cuti_data.nama],
                ['NIP', ':', cuti_data.nip],
                ['Jabatan', ':', cuti_data.jabatan],
                ['Golongan/Ruang', ':', cuti_data.gol_ruang],
                ['Unit Kerja', ':', cuti_data.unit_kerja],
                ['Masa Kerja', ':', cuti_data.masa_kerja],
                ['Alamat', ':', cuti_data.alamat],
                ['Telepon', ':', cuti_data.telp],
            ]
            
            table_pegawai = Table(data_pegawai, colWidths=[2*inch, 0.3*inch, 4*inch])
            table_pegawai.setStyle(TableStyle([
                ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
                ('FONTSIZE', (0, 0), (-1, -1), 10),
                ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                ('LEFTPADDING', (0, 0), (-1, -1), 0),
                ('RIGHTPADDING', (0, 0), (-1, -1), 0),
            ]))
            
            story.append(table_pegawai)
            story.append(Spacer(1, 20))
            
            # Data cuti
            data_cuti = [
                ['Jenis Cuti', ':', cuti_data.jenis_cuti],
                ['Alasan Cuti', ':', cuti_data.alasan_cuti],
                ['Lama Cuti', ':', cuti_data.lama_cuti],
                ['Tanggal Mulai', ':', cuti_data.tanggal_cuti.strftime('%d %B %Y')],
                ['Tanggal Selesai', ':', cuti_data.sampai_cuti.strftime('%d %B %Y')],
                ['Tanggal Pengajuan', ':', cuti_data.tgl_ajuan_cuti.strftime('%d %B %Y')],
            ]
            
            table_cuti = Table(data_cuti, colWidths=[2*inch, 0.3*inch, 4*inch])
            table_cuti.setStyle(TableStyle([
                ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
                ('FONTSIZE', (0, 0), (-1, -1), 10),
                ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                ('LEFTPADDING', (0, 0), (-1, -1), 0),
                ('RIGHTPADDING', (0, 0), (-1, -1), 0),
            ]))
            
            story.append(table_cuti)
            story.append(Spacer(1, 30))
            
            # Status persetujuan
            story.append(Paragraph(f"<b>STATUS: DISETUJUI</b>", normal_style))
            story.append(Paragraph(f"Disetujui oleh: {approver_info['name']}", normal_style))
            story.append(Paragraph(f"Tanggal Persetujuan: {datetime.now().strftime('%d %B %Y, %H:%M:%S')}", normal_style))
            story.append(Spacer(1, 30))
            
            # QR Code section
            story.append(Paragraph("TANDA TANGAN DIGITAL", header_style))
            story.append(Spacer(1, 10))
            
            # Add QR code image
            if os.path.exists(qr_info['qr_path']):
                qr_image = Image(qr_info['qr_path'], width=2*inch, height=2*inch)
                qr_table = Table([[qr_image]], colWidths=[2*inch])
                qr_table.setStyle(TableStyle([
                    ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ]))
                story.append(qr_table)
            
            story.append(Spacer(1, 10))
            story.append(Paragraph(f"Hash Signature: {qr_info['signature_hash']}", normal_style))
            story.append(Paragraph("Scan QR code untuk verifikasi digital signature", normal_style))
            
            # Footer
            story.append(Spacer(1, 50))
            footer_data = [
                ['', 'Watampone, ' + datetime.now().strftime('%d %B %Y')],
                ['', 'Ketua Pengadilan Agama Watampone'],
                ['', ''],
                ['', ''],
                ['', approver_info['name']],
                ['', f"NIP. {approver_info.get('nip', '-')}"]
            ]
            
            footer_table = Table(footer_data, colWidths=[3*inch, 3*inch])
            footer_table.setStyle(TableStyle([
                ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
                ('FONTSIZE', (0, 0), (-1, -1), 10),
                ('ALIGN', (1, 0), (1, -1), 'CENTER'),
            ]))
            
            story.append(footer_table)
            
            # Build PDF
            doc.build(story)
            
            return pdf_path
            
        except Exception as e:
            print(f"Error generating PDF: {str(e)}")
            return None
    
    def verify_signature(self, signature_hash):
        """Verifikasi digital signature berdasarkan hash"""
        try:
            from config.models import Cuti
            cuti = Cuti.query.filter_by(qr_code=signature_hash).first()
            if cuti and cuti.status_cuti == 'approved':
                return {
                    'valid': True,
                    'cuti_data': cuti,
                    'message': 'Digital signature valid'
                }
            else:
                return {
                    'valid': False,
                    'message': 'Digital signature tidak valid atau cuti belum disetujui'
                }
        except Exception as e:
            return {
                'valid': False,
                'message': f'Error verifying signature: {str(e)}'
            }