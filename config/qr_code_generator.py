"""
QR Code Generator untuk Surat Cuti
===================================
Module ini menangani pembuatan QR code yang lebih advanced dengan:
- QR code berwarna
- Logo di tengah QR code
- Informasi lengkap untuk verifikasi
- Preview QR code sebelum generate PDF
"""

import qrcode
from qrcode.image.styledpil import StyledPilImage
from qrcode.image.styles.moduledrawers import RoundedModuleDrawer, CircleModuleDrawer, GappedSquareModuleDrawer
from qrcode.image.styles.colormasks import SolidFillColorMask
import base64
import io
import os
from datetime import datetime
from PIL import Image, ImageDraw, ImageFont
import hashlib
import json

class QRCodeGenerator:
    def __init__(self):
        self.qr_folder = 'static/qr_codes'
        self.logo_path = 'static/assets/img/logo.png'  # Path ke logo instansi
        os.makedirs(self.qr_folder, exist_ok=True)
    
    def generate_signature_hash(self, cuti_data):
        """Generate unique hash untuk digital signature"""
        timestamp = datetime.now().isoformat()
        signature_string = f"{cuti_data.id_cuti}_{cuti_data.nama}_{cuti_data.nip}_{timestamp}"
        return hashlib.sha256(signature_string.encode()).hexdigest()[:16]
    
    def create_verification_url(self, signature_hash):
        """Buat URL verifikasi untuk QR code"""
        # Ganti dengan domain production Anda
        base_url = "https://your-domain.com"
        return f"{base_url}/verify-cuti/{signature_hash}"
    
    def create_qr_data(self, cuti_data, approver_info=None):
        """Buat data untuk QR code"""
        signature_hash = self.generate_signature_hash(cuti_data)
        verification_url = self.create_verification_url(signature_hash)
        
        qr_data = {
            'type': 'SURAT_CUTI',
            'id': cuti_data.id_cuti,
            'nama': cuti_data.nama,
            'nip': cuti_data.nip,
            'jenis_cuti': cuti_data.jenis_cuti,
            'tanggal_mulai': cuti_data.tanggal_cuti.strftime('%Y-%m-%d'),
            'tanggal_selesai': cuti_data.sampai_cuti.strftime('%Y-%m-%d'),
            'lama_cuti': cuti_data.lama_cuti,
            'status': cuti_data.status_cuti,
            'signature_hash': signature_hash,
            'verification_url': verification_url,
            'generated_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }
        
        if approver_info:
            qr_data['approved_by'] = approver_info.get('name', '')
            qr_data['approved_at'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        return qr_data, signature_hash
    
    def generate_qr_code_basic(self, cuti_data, approver_info=None):
        """Generate QR code basic (hitam putih)"""
        try:
            qr_data, signature_hash = self.create_qr_data(cuti_data, approver_info)
            
            # Convert data to JSON string
            qr_string = json.dumps(qr_data, ensure_ascii=False, indent=2)
            
            # Create QR code
            qr = qrcode.QRCode(
                version=None,  # Auto-determine version
                error_correction=qrcode.constants.ERROR_CORRECT_H,  # High error correction
                box_size=10,
                border=4,
            )
            qr.add_data(qr_string)
            qr.make(fit=True)
            
            # Create image
            qr_img = qr.make_image(fill_color="black", back_color="white")
            
            # Save to file
            qr_filename = f"qr_cuti_{cuti_data.id_cuti}_{signature_hash}.png"
            qr_path = os.path.join(self.qr_folder, qr_filename)
            qr_img.save(qr_path)
            
            # Convert to base64
            buffer = io.BytesIO()
            qr_img.save(buffer, format='PNG')
            qr_base64 = base64.b64encode(buffer.getvalue()).decode()
            
            return {
                'qr_path': qr_path,
                'qr_base64': qr_base64,
                'signature_hash': signature_hash,
                'qr_data': qr_data,
                'verification_url': qr_data['verification_url']
            }
            
        except Exception as e:
            print(f"Error generating basic QR code: {str(e)}")
            return None
    
    def generate_qr_code_styled(self, cuti_data, approver_info=None, style='rounded'):
        """Generate QR code dengan style (rounded, circle, gapped)"""
        try:
            qr_data, signature_hash = self.create_qr_data(cuti_data, approver_info)
            
            # Convert data to JSON string
            qr_string = json.dumps(qr_data, ensure_ascii=False, indent=2)
            
            # Create QR code
            qr = qrcode.QRCode(
                version=None,
                error_correction=qrcode.constants.ERROR_CORRECT_H,
                box_size=10,
                border=4,
            )
            qr.add_data(qr_string)
            qr.make(fit=True)
            
            # Choose style
            module_drawer = RoundedModuleDrawer()
            if style == 'circle':
                module_drawer = CircleModuleDrawer()
            elif style == 'gapped':
                module_drawer = GappedSquareModuleDrawer()
            
            # Create styled image
            qr_img = qr.make_image(
                image_factory=StyledPilImage,
                module_drawer=module_drawer,
                color_mask=SolidFillColorMask(
                    back_color=(255, 255, 255),  # White background
                    front_color=(0, 51, 102)     # Dark blue
                )
            )
            
            # Save to file
            qr_filename = f"qr_cuti_{cuti_data.id_cuti}_{signature_hash}_styled.png"
            qr_path = os.path.join(self.qr_folder, qr_filename)
            qr_img.save(qr_path)
            
            # Convert to base64
            buffer = io.BytesIO()
            qr_img.save(buffer, format='PNG')
            qr_base64 = base64.b64encode(buffer.getvalue()).decode()
            
            return {
                'qr_path': qr_path,
                'qr_base64': qr_base64,
                'signature_hash': signature_hash,
                'qr_data': qr_data,
                'verification_url': qr_data['verification_url']
            }
            
        except Exception as e:
            print(f"Error generating styled QR code: {str(e)}")
            # Fallback to basic QR code
            return self.generate_qr_code_basic(cuti_data, approver_info)
    
    def generate_qr_code_with_logo(self, cuti_data, approver_info=None):
        """Generate QR code dengan logo di tengah"""
        try:
            # Generate basic QR code first
            result = self.generate_qr_code_basic(cuti_data, approver_info)
            if not result:
                return None
            
            # Open QR code image
            qr_img = Image.open(result['qr_path'])
            
            # Check if logo exists
            if os.path.exists(self.logo_path):
                # Open logo
                logo = Image.open(self.logo_path)
                
                # Calculate logo size (should be about 1/5 of QR code size)
                qr_width, qr_height = qr_img.size
                logo_size = min(qr_width, qr_height) // 5
                
                # Resize logo
                logo = logo.resize((logo_size, logo_size), Image.Resampling.LANCZOS)
                
                # Create white background for logo
                logo_bg = Image.new('RGB', (logo_size + 20, logo_size + 20), 'white')
                logo_bg_pos = ((logo_bg.size[0] - logo_size) // 2, (logo_bg.size[1] - logo_size) // 2)
                logo_bg.paste(logo, logo_bg_pos)
                
                # Calculate position to paste logo (center of QR code)
                logo_pos = ((qr_width - logo_bg.size[0]) // 2, (qr_height - logo_bg.size[1]) // 2)
                
                # Paste logo onto QR code
                qr_img.paste(logo_bg, logo_pos)
            
            # Save QR code with logo
            qr_filename = f"qr_cuti_{cuti_data.id_cuti}_{result['signature_hash']}_logo.png"
            qr_path = os.path.join(self.qr_folder, qr_filename)
            qr_img.save(qr_path)
            
            # Convert to base64
            buffer = io.BytesIO()
            qr_img.save(buffer, format='PNG')
            qr_base64 = base64.b64encode(buffer.getvalue()).decode()
            
            result['qr_path'] = qr_path
            result['qr_base64'] = qr_base64
            
            return result
            
        except Exception as e:
            print(f"Error generating QR code with logo: {str(e)}")
            # Fallback to basic QR code
            return self.generate_qr_code_basic(cuti_data, approver_info)
    
    def generate_qr_code_with_text(self, cuti_data, approver_info=None):
        """Generate QR code dengan text di bawahnya"""
        try:
            # Generate QR code with logo
            result = self.generate_qr_code_with_logo(cuti_data, approver_info)
            if not result:
                return None
            
            # Open QR code image
            qr_img = Image.open(result['qr_path'])
            
            # Create new image with space for text
            text_height = 100
            new_img = Image.new('RGB', (qr_img.size[0], qr_img.size[1] + text_height), 'white')
            new_img.paste(qr_img, (0, 0))
            
            # Add text
            draw = ImageDraw.Draw(new_img)
            
            # Try to use a nice font, fallback to default if not available
            try:
                font_title = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", 16)
                font_text = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", 12)
            except:
                font_title = ImageFont.load_default()
                font_text = ImageFont.load_default()
            
            # Add title
            title = "VERIFIKASI DIGITAL"
            title_bbox = draw.textbbox((0, 0), title, font=font_title)
            title_width = title_bbox[2] - title_bbox[0]
            title_x = (new_img.size[0] - title_width) // 2
            draw.text((title_x, qr_img.size[1] + 10), title, fill='black', font=font_title)
            
            # Add hash
            hash_text = f"Hash: {result['signature_hash']}"
            hash_bbox = draw.textbbox((0, 0), hash_text, font=font_text)
            hash_width = hash_bbox[2] - hash_bbox[0]
            hash_x = (new_img.size[0] - hash_width) // 2
            draw.text((hash_x, qr_img.size[1] + 35), hash_text, fill='gray', font=font_text)
            
            # Add instruction
            instruction = "Scan untuk verifikasi"
            inst_bbox = draw.textbbox((0, 0), instruction, font=font_text)
            inst_width = inst_bbox[2] - inst_bbox[0]
            inst_x = (new_img.size[0] - inst_width) // 2
            draw.text((inst_x, qr_img.size[1] + 60), instruction, fill='gray', font=font_text)
            
            # Save final image
            qr_filename = f"qr_cuti_{cuti_data.id_cuti}_{result['signature_hash']}_final.png"
            qr_path = os.path.join(self.qr_folder, qr_filename)
            new_img.save(qr_path)
            
            # Convert to base64
            buffer = io.BytesIO()
            new_img.save(buffer, format='PNG')
            qr_base64 = base64.b64encode(buffer.getvalue()).decode()
            
            result['qr_path'] = qr_path
            result['qr_base64'] = qr_base64
            
            return result
            
        except Exception as e:
            print(f"Error generating QR code with text: {str(e)}")
            # Fallback to QR code with logo
            return self.generate_qr_code_with_logo(cuti_data, approver_info)
    
    def verify_qr_code(self, signature_hash):
        """Verifikasi QR code berdasarkan signature hash"""
        try:
            from config.models import Cuti
            from flask import current_app
            
            cuti = Cuti.query.filter_by(qr_code=signature_hash).first()
            
            if not cuti:
                return {
                    'valid': False,
                    'message': 'QR Code tidak ditemukan dalam sistem',
                    'data': None
                }
            
            # Check if cuti is approved
            if cuti.status_cuti != 'approved':
                return {
                    'valid': False,
                    'message': f'Surat cuti belum disetujui. Status: {cuti.status_cuti}',
                    'data': {
                        'id_cuti': cuti.id_cuti,
                        'nama': cuti.nama,
                        'status': cuti.status_cuti
                    }
                }
            
            # Return verification result
            return {
                'valid': True,
                'message': 'QR Code valid dan surat cuti telah disetujui',
                'data': {
                    'id_cuti': cuti.id_cuti,
                    'nama': cuti.nama,
                    'nip': cuti.nip,
                    'jenis_cuti': cuti.jenis_cuti,
                    'tanggal_mulai': cuti.tanggal_cuti.strftime('%d %B %Y'),
                    'tanggal_selesai': cuti.sampai_cuti.strftime('%d %B %Y'),
                    'lama_cuti': cuti.lama_cuti,
                    'alasan_cuti': cuti.alasan_cuti,
                    'status': cuti.status_cuti,
                    'tanggal_pengajuan': cuti.tgl_ajuan_cuti.strftime('%d %B %Y'),
                    'signature_hash': signature_hash
                }
            }
            
        except Exception as e:
            return {
                'valid': False,
                'message': f'Error verifikasi: {str(e)}',
                'data': None
            }
