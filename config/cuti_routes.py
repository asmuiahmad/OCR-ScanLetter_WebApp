"""
Cuti routes
Leave/vacation management functionality
"""

import os
import qrcode
import tempfile
from io import BytesIO
from datetime import datetime

from flask import Blueprint, render_template, request, redirect, url_for, flash, send_file, current_app, Response
from flask_login import login_required, current_user
from docx import Document
from mailmerge import MailMerge

from config.extensions import db
from config.models import Cuti, Pegawai
from config.forms import CutiForm, InputCutiForm
from config.route_utils import role_required

cuti_bp = Blueprint('cuti', __name__)


def create_download_response(file_path, filename, mimetype='application/pdf'):
    """
    Create a proper download response that forces download to Downloads folder
    """
    try:
        # Ensure file exists
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"File not found: {file_path}")
        
        # Create response with proper headers for forced download
        response = send_file(
            file_path,
            as_attachment=True,
            download_name=filename,
            mimetype=mimetype
        )
        
        # Enhanced headers to force download to Downloads folder
        response.headers['Content-Type'] = mimetype
        response.headers['Content-Disposition'] = f'attachment; filename="{filename}"'
        response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
        response.headers['Pragma'] = 'no-cache'
        response.headers['Expires'] = '0'
        
        # Additional headers to ensure proper download behavior
        response.headers['X-Content-Type-Options'] = 'nosniff'
        response.headers['Content-Transfer-Encoding'] = 'binary'
        
        return response
        
    except Exception as e:
        current_app.logger.error(f"Error creating download response: {str(e)}")
        raise


def generate_cuti_filename(nama, tanggal_dibuat, file_type="surat_cuti"):
    """
    Generate standardized filename for cuti documents
    Format: surat_cuti_[nama]_[YYYY-MM-DD].pdf
    
    Args:
        nama (str): Employee name
        tanggal_dibuat (datetime/date): Date when the document was created
        file_type (str): Type of document (default: "surat_cuti")
    
    Returns:
        str: Formatted filename
    """
    try:
        # Clean the name - remove spaces, special characters, and convert to lowercase
        clean_nama = nama.replace(' ', '_').replace('-', '_').replace('.', '').replace(',', '')
        clean_nama = ''.join(c for c in clean_nama if c.isalnum() or c == '_').lower()
        
        # Format date as YYYY-MM-DD
        if hasattr(tanggal_dibuat, 'strftime'):
            date_str = tanggal_dibuat.strftime('%Y-%m-%d')
        else:
            # If it's already a string, try to parse it
            date_str = str(tanggal_dibuat)
        
        # Generate filename
        filename = f"{file_type}_{clean_nama}_{date_str}.pdf"
        
        return filename
        
    except Exception as e:
        # Fallback to simple format if there's an error
        clean_nama = str(nama).replace(' ', '_')
        return f"{file_type}_{clean_nama}.pdf"


@cuti_bp.route('/generate-cuti-direct', methods=['GET', 'POST'])
@login_required
def generate_cuti_direct():
    """Generate cuti form directly using HTML template - prioritas utama"""
    form = CutiForm()
    
    if form.validate_on_submit():
        try:
            # Calculate lama_cuti automatically
            tanggal_mulai = form.tanggal_cuti.data
            tanggal_selesai = form.sampai_cuti.data
            lama_cuti_days = (tanggal_selesai - tanggal_mulai).days + 1
            lama_cuti_str = f"{lama_cuti_days} hari"
            
            # Create new cuti record
            new_cuti = Cuti(
                nama=form.nama.data,
                nip=form.nip.data,
                jabatan=form.jabatan.data,
                gol_ruang=form.gol_ruang.data,
                unit_kerja=form.unit_kerja.data,
                masa_kerja=form.masa_kerja.data,
                alamat=form.alamat.data,
                no_suratmasuk=form.no_suratmasuk.data,
                tgl_ajuan_cuti=form.tgl_ajuan_cuti.data,
                tanggal_cuti=form.tanggal_cuti.data,
                sampai_cuti=form.sampai_cuti.data,
                telp=form.telp.data,
                jenis_cuti=form.jenis_cuti.data,
                alasan_cuti=form.alasan_cuti.data,
                lama_cuti=lama_cuti_str,
                status_cuti='approved'  # Auto-approve for PDF generation
            )
            
            db.session.add(new_cuti)
            db.session.commit()
            
            # Generate PDF using HTML template (prioritas utama)
            from config.html_template_handler import HtmlTemplateHandler
            
            template_handler = HtmlTemplateHandler()
            
            # Generate PDF from HTML template
            result = template_handler.fill_template_and_generate_pdf(new_cuti)
            
            if result['success']:
                # Update cuti record with generated files info
                new_cuti.qr_code = result['signature_hash']
                new_cuti.pdf_path = result['pdf_path']
                db.session.commit()
                
                # Return PDF file for download
                return send_file(
                    result['pdf_path'],
                    as_attachment=True,
                    download_name=f"surat_cuti_{new_cuti.nama.replace(' ', '_')}_{new_cuti.id_cuti}.pdf",
                    mimetype='application/pdf'
                )
            else:
                flash(f'Error: Tidak dapat menghasilkan PDF - {result["error"]}', 'error')
                current_app.logger.error(f"PDF generation failed for cuti ID: {new_cuti.id_cuti} - {result['error']}")
                
                # Still commit the cuti record but redirect to list
                db.session.commit()
                flash('Data cuti berhasil disimpan, namun terjadi error saat generate PDF', 'warning')
                return redirect(url_for('cuti.list_cuti'))
            
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Error creating cuti: {str(e)}")
            flash(f'Error creating cuti form: {str(e)}', 'error')
    
    return render_template('cuti/generate_cuti_form.html', form=form)


@cuti_bp.route('/generate-cuti-html', methods=['GET', 'POST'])
@login_required
def generate_cuti_html():
    """Generate cuti form using HTML template and PDF"""
    form = CutiForm()
    
    if form.validate_on_submit():
        try:
            # Calculate lama_cuti automatically
            tanggal_mulai = form.tanggal_cuti.data
            tanggal_selesai = form.sampai_cuti.data
            lama_cuti_days = (tanggal_selesai - tanggal_mulai).days + 1
            lama_cuti_str = f"{lama_cuti_days} hari"
            
            # Create new cuti record
            new_cuti = Cuti(
                nama=form.nama.data,
                nip=form.nip.data,
                jabatan=form.jabatan.data,
                gol_ruang=form.gol_ruang.data,
                unit_kerja=form.unit_kerja.data,
                masa_kerja=form.masa_kerja.data,
                alamat=form.alamat.data,
                no_suratmasuk=form.no_suratmasuk.data,
                tgl_ajuan_cuti=form.tgl_ajuan_cuti.data,
                tanggal_cuti=form.tanggal_cuti.data,
                sampai_cuti=form.sampai_cuti.data,
                telp=form.telp.data,
                jenis_cuti=form.jenis_cuti.data,
                alasan_cuti=form.alasan_cuti.data,
                lama_cuti=lama_cuti_str,
                status_cuti='approved'  # Auto-approve for PDF generation
            )
            
            db.session.add(new_cuti)
            db.session.commit()
            
            # Generate PDF using HTML template
            from config.html_template_handler import HtmlTemplateHandler
            
            template_handler = HtmlTemplateHandler()
            
            # Generate PDF from HTML template
            result = template_handler.fill_template_and_generate_pdf(new_cuti)
            
            if result['success']:
                # Update cuti record with generated files info
                new_cuti.qr_code = result['signature_hash']
                new_cuti.pdf_path = result['pdf_path']
                db.session.commit()
                
                # Return PDF file for download
                return send_file(
                    result['pdf_path'],
                    as_attachment=True,
                    download_name=f"surat_cuti_{new_cuti.nama.replace(' ', '_')}_{new_cuti.id_cuti}.pdf",
                    mimetype='application/pdf'
                )
            else:
                flash(f'Error: Tidak dapat menghasilkan PDF - {result["error"]}', 'error')
                current_app.logger.error(f"PDF generation failed for cuti ID: {new_cuti.id_cuti} - {result['error']}")
                
                # Still commit the cuti record but redirect to list
                db.session.commit()
                flash('Data cuti berhasil disimpan, namun terjadi error saat generate PDF', 'warning')
                return redirect(url_for('cuti.list_cuti'))
            
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Error creating cuti: {str(e)}")
            flash(f'Error creating cuti form: {str(e)}', 'error')
    
    return render_template('cuti/generate_cuti_form.html', form=form)


@cuti_bp.route('/generate-cuti', methods=['GET', 'POST'])
@login_required
def generate_cuti():
    """Generate cuti form and PDF"""
    form = CutiForm()
    
    # Handle POST request - let Flask-WTF handle CSRF automatically
    if request.method == 'POST':
        # Check if form is valid (this includes CSRF validation)
        if not form.validate():
            # Log validation errors
            current_app.logger.warning(f"Form validation failed: {form.errors}")
            # Check if it's a CSRF error
            if 'csrf_token' in form.errors:
                flash('Token keamanan tidak valid atau telah kedaluwarsa. Silakan refresh halaman dan coba lagi.', 'error')
            else:
                # Log other validation errors
                for field, errors in form.errors.items():
                    for error in errors:
                        flash(f'{field}: {error}', 'error')
            return render_template('cuti/generate_cuti_form.html', form=form)
    
    if form.validate_on_submit():
        try:
            # Calculate lama_cuti automatically
            tanggal_mulai = form.tanggal_cuti.data
            tanggal_selesai = form.sampai_cuti.data
            lama_cuti_days = (tanggal_selesai - tanggal_mulai).days + 1
            lama_cuti_str = f"{lama_cuti_days} hari"
            
            # Create new cuti record
            new_cuti = Cuti(
                nama=form.nama.data,
                nip=form.nip.data,
                jabatan=form.jabatan.data,
                gol_ruang=form.gol_ruang.data,
                unit_kerja=form.unit_kerja.data,
                masa_kerja=form.masa_kerja.data,
                alamat=form.alamat.data,
                no_suratmasuk=form.no_suratmasuk.data,
                tgl_ajuan_cuti=form.tgl_ajuan_cuti.data,
                tanggal_cuti=form.tanggal_cuti.data,
                sampai_cuti=form.sampai_cuti.data,
                telp=form.telp.data,
                jenis_cuti=form.jenis_cuti.data,
                alasan_cuti=form.alasan_cuti.data,
                lama_cuti=lama_cuti_str,
                status_cuti='approved'  # Auto-approve for PDF generation
            )
            
            db.session.add(new_cuti)
            db.session.commit()
            
            # Prioritize HTML template first (most reliable for PDF generation)
            result = None
            
            # Method 1: HTML Template (prioritas utama - selalu menghasilkan PDF)
            try:
                from config.html_template_handler import HtmlTemplateHandler
                template_handler = HtmlTemplateHandler()
                current_app.logger.info(f"Attempting PDF generation for cuti ID: {new_cuti.id_cuti}")
                result = template_handler.fill_template_and_generate_pdf(new_cuti)
                if result and result.get('success'):
                    current_app.logger.info(f"✅ HTML template successful - PDF at: {result.get('pdf_path')}")
                    print("✅ HTML template successful")
                else:
                    current_app.logger.warning(f"HTML template returned failure: {result.get('error', 'Unknown error') if result else 'No result'}")
            except Exception as html_error:
                current_app.logger.error(f"HTML template failed: {str(html_error)}")
                import traceback
                current_app.logger.error(traceback.format_exc())
                print(f"HTML template failed: {html_error}")
            
            # Method 2: Advanced DOCX Template (fallback - hanya jika berhasil convert ke PDF)
            if not result or not result['success']:
                try:
                    from config.docx_template_advanced import AdvancedDocxTemplateHandler
                    template_handler = AdvancedDocxTemplateHandler()
                    result = template_handler.fill_template_and_generate_pdf(new_cuti)
                    if result['success']:
                        # Verify that the result is actually a PDF file
                        pdf_path = result.get('pdf_path', '')
                        if pdf_path and pdf_path.endswith('.pdf') and os.path.exists(pdf_path):
                            print("✅ Advanced DOCX template successful")
                        else:
                            # If not PDF, mark as failed and try next method
                            result = None
                            print("⚠️ Advanced DOCX template returned non-PDF file")
                except Exception as advanced_error:
                    print(f"Advanced DOCX template failed: {advanced_error}")
            
            # Method 3: Basic DOCX Template (last resort - hanya jika berhasil convert ke PDF)
            if not result or not result['success']:
                try:
                    from config.docx_template_handler import DocxTemplateHandler
                    template_handler = DocxTemplateHandler()
                    result = template_handler.fill_template_and_generate_pdf(new_cuti)
                    if result['success']:
                        # Verify that the result is actually a PDF file
                        pdf_path = result.get('pdf_path', '')
                        if pdf_path and pdf_path.endswith('.pdf') and os.path.exists(pdf_path):
                            print("✅ Basic DOCX template successful")
                        else:
                            result = {'success': False, 'error': 'PDF conversion failed'}
                            print("⚠️ Basic DOCX template returned non-PDF file")
                except Exception as docx_error:
                    print(f"Basic DOCX template failed: {docx_error}")
                    result = {'success': False, 'error': 'All template methods failed'}
            
            if result and result.get('success'):
                pdf_path = result.get('pdf_path', '')
                
                # Verify file is actually a PDF
                if not pdf_path or not pdf_path.endswith('.pdf'):
                    flash('Error: File yang dihasilkan bukan PDF', 'error')
                    current_app.logger.error(f"Generated file is not PDF: {pdf_path}")
                    db.session.commit()
                    return redirect(url_for('cuti.list_cuti'))
                
                if not os.path.exists(pdf_path):
                    flash('Error: File PDF tidak ditemukan', 'error')
                    current_app.logger.error(f"PDF file not found: {pdf_path}")
                    db.session.commit()
                    return redirect(url_for('cuti.list_cuti'))
                
                # Update cuti record with generated files info
                new_cuti.qr_code = result.get('signature_hash', '')
                new_cuti.pdf_path = pdf_path
                db.session.commit()
                
                # Convert to absolute path for send_file
                if not os.path.isabs(pdf_path):
                    # Try relative to app root first
                    abs_path1 = os.path.join(current_app.root_path, pdf_path)
                    # Try relative to project root
                    abs_path2 = os.path.abspath(pdf_path)
                    # Use whichever exists
                    if os.path.exists(abs_path1):
                        pdf_path = abs_path1
                    elif os.path.exists(abs_path2):
                        pdf_path = abs_path2
                    else:
                        # Fallback to absolute path
                        pdf_path = os.path.abspath(pdf_path)
                
                # Return PDF file for download with enhanced headers
                try:
                    current_app.logger.info(f"Sending PDF file: {pdf_path}")
                    filename = generate_cuti_filename(new_cuti.nama, new_cuti.tgl_ajuan_cuti)
                    return create_download_response(pdf_path, filename)
                except Exception as send_error:
                    current_app.logger.error(f"Error sending PDF file: {str(send_error)}")
                    import traceback
                    current_app.logger.error(traceback.format_exc())
                    flash('Error: Gagal mengirim file PDF', 'error')
                    return redirect(url_for('cuti.list_cuti'))
            else:
                error_msg = result.get('error', 'Unknown error') if result else 'PDF generation failed - no result returned'
                flash(f'Error: Tidak dapat menghasilkan PDF - {error_msg}', 'error')
                current_app.logger.error(f"PDF generation failed for cuti ID: {new_cuti.id_cuti} - {error_msg}")
                
                # Still commit the cuti record but redirect to list
                db.session.commit()
                flash('Data cuti berhasil disimpan, namun terjadi error saat generate PDF', 'warning')
                return redirect(url_for('cuti.list_cuti'))
            
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Error creating cuti: {str(e)}")
            import traceback
            current_app.logger.error(traceback.format_exc())
            flash(f'Error creating cuti form: {str(e)}', 'error')
            return redirect(url_for('cuti.list_cuti'))
    
    return render_template('cuti/generate_cuti_form.html', form=form)


@cuti_bp.route('/input-cuti', methods=['GET', 'POST'])
@login_required
@role_required('admin', 'pimpinan')
def input_cuti():
    """Input cuti form"""
    form = InputCutiForm()
    
    if form.validate_on_submit():
        try:
            # Calculate lama_cuti automatically
            tanggal_mulai = form.tanggal_cuti.data
            tanggal_selesai = form.sampai_cuti.data
            lama_cuti_days = (tanggal_selesai - tanggal_mulai).days + 1
            lama_cuti_str = f"{lama_cuti_days} hari"
            
            new_cuti = Cuti(
                nama=form.nama.data,
                nip=form.nip.data,
                jabatan=form.jabatan.data,
                gol_ruang=form.gol_ruang.data,
                unit_kerja=form.unit_kerja.data,
                masa_kerja=form.masa_kerja.data,
                alamat=form.alamat.data,
                no_suratmasuk=form.no_suratmasuk.data,
                tgl_ajuan_cuti=form.tgl_ajuan_cuti.data,
                tanggal_cuti=form.tanggal_cuti.data,
                sampai_cuti=form.sampai_cuti.data,
                telp=form.telp.data,
                jenis_cuti=form.jenis_cuti.data,
                alasan_cuti=form.alasan_cuti.data,
                lama_cuti=lama_cuti_str,
                status_cuti='pending'
            )
            
            db.session.add(new_cuti)
            db.session.commit()
            
            flash('Data cuti berhasil disimpan!', 'success')
            return redirect(url_for('cuti.list_cuti'))
            
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Error saving cuti: {str(e)}")
            flash(f'Error saving cuti: {str(e)}', 'error')
    
    return render_template('cuti/input_cuti.html', form=form)


@cuti_bp.route('/list-cuti')
@login_required
@role_required('admin', 'pimpinan')
def list_cuti():
    """List all cuti applications"""
    try:
        cuti_list = Cuti.query.order_by(Cuti.created_at.desc()).all()
        return render_template('cuti/list_cuti.html', cuti_list=cuti_list)
    except Exception as e:
        current_app.logger.error(f"Error loading cuti list: {str(e)}")
        flash('Error loading cuti list', 'error')
        return redirect(url_for('main.index'))


@cuti_bp.route('/approve-cuti/<int:cuti_id>', methods=['POST'])
@login_required
@role_required('pimpinan')
def approve_cuti(cuti_id):
    """Approve cuti application"""
    try:
        cuti = Cuti.query.get_or_404(cuti_id)
        cuti.status_cuti = 'approved'
        cuti.approved_by = current_user.email
        cuti.approved_at = datetime.utcnow()
        
        db.session.commit()
        
        flash(f'Cuti untuk {cuti.nama} telah disetujui', 'success')
        return redirect(url_for('cuti.list_cuti'))
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error approving cuti {cuti_id}: {str(e)}")
        flash('Error approving cuti', 'error')
        return redirect(url_for('cuti.list_cuti'))


@cuti_bp.route('/reject-cuti/<int:cuti_id>', methods=['POST'])
@login_required
@role_required('pimpinan')
def reject_cuti(cuti_id):
    """Reject cuti application"""
    try:
        cuti = Cuti.query.get_or_404(cuti_id)
        cuti.status_cuti = 'rejected'
        cuti.notes = request.form.get('notes', '')
        
        db.session.commit()
        
        flash(f'Cuti untuk {cuti.nama} telah ditolak', 'info')
        return redirect(url_for('cuti.list_cuti'))
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error rejecting cuti {cuti_id}: {str(e)}")
        flash('Error rejecting cuti', 'error')
        return redirect(url_for('cuti.list_cuti'))


@cuti_bp.route('/delete-cuti/<int:cuti_id>', methods=['POST'])
@login_required
@role_required('admin')
def delete_cuti(cuti_id):
    """Delete cuti application"""
    try:
        cuti = Cuti.query.get_or_404(cuti_id)
        nama_cuti = cuti.nama
        
        # Delete associated files if they exist
        if cuti.pdf_path and os.path.exists(cuti.pdf_path):
            os.remove(cuti.pdf_path)
        
        db.session.delete(cuti)
        db.session.commit()
        
        flash(f'Data cuti {nama_cuti} berhasil dihapus', 'success')
        return redirect(url_for('cuti.list_cuti'))
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error deleting cuti {cuti_id}: {str(e)}")
        flash('Error deleting cuti', 'error')
        return redirect(url_for('cuti.list_cuti'))


@cuti_bp.route('/detail/<int:cuti_id>')
@login_required
def detail_cuti(cuti_id):
    """Get cuti detail as JSON"""
    try:
        cuti = Cuti.query.get_or_404(cuti_id)
        
        cuti_data = {
            'id_cuti': cuti.id_cuti,
            'nama': cuti.nama,
            'nip': cuti.nip,
            'jabatan': cuti.jabatan,
            'gol_ruang': cuti.gol_ruang,
            'unit_kerja': cuti.unit_kerja,
            'masa_kerja': cuti.masa_kerja,
            'alamat': cuti.alamat,
            'telp': cuti.telp,
            'jenis_cuti': cuti.jenis_cuti,
            'alasan_cuti': cuti.alasan_cuti,
            'lama_cuti': cuti.lama_cuti,
            'tanggal_cuti': cuti.tanggal_cuti.strftime('%d/%m/%Y'),
            'sampai_cuti': cuti.sampai_cuti.strftime('%d/%m/%Y'),
            'tgl_ajuan_cuti': cuti.tgl_ajuan_cuti.strftime('%d/%m/%Y'),
            'status_cuti': cuti.status_cuti,
            'approved_by': cuti.approved_by,
            'approved_at': cuti.approved_at.strftime('%d/%m/%Y %H:%M') if cuti.approved_at else None,
            'notes': cuti.notes
        }
        
        return {'success': True, 'cuti': cuti_data}
        
    except Exception as e:
        current_app.logger.error(f"Error getting cuti detail {cuti_id}: {str(e)}")
        return {'success': False, 'message': str(e)}


@cuti_bp.route('/preview-cuti-html/<int:cuti_id>')
@login_required
def preview_cuti_html(cuti_id):
    """Preview HTML template with filled data"""
    try:
        cuti = Cuti.query.get_or_404(cuti_id)
        
        from config.html_template_handler import HtmlTemplateHandler
        template_handler = HtmlTemplateHandler()
        
        # Check if template exists
        if not os.path.exists(template_handler.template_path):
            flash('Template HTML tidak ditemukan', 'error')
            return redirect(url_for('cuti.list_cuti'))
        
        # Generate signature hash for preview
        signature_hash = template_handler.generate_signature_hash(cuti)
        
        # Read HTML template
        with open(template_handler.template_path, 'r', encoding='utf-8') as file:
            html_content = file.read()
        
        # Replace placeholders
        html_content = template_handler.replace_placeholders_in_html(html_content, cuti, signature_hash)
        
        # Add preview notice
        preview_notice = '''
        <div style="position: fixed; top: 0; left: 0; right: 0; background: #ff9800; color: white; padding: 10px; text-align: center; z-index: 1000;">
            <strong>PREVIEW MODE</strong> - Ini adalah preview template HTML. 
            <a href="javascript:window.close()" style="color: white; text-decoration: underline;">Tutup</a>
        </div>
        <div style="margin-top: 50px;">
        '''
        html_content = html_content.replace('<body>', f'<body>{preview_notice}')
        html_content = html_content.replace('</body>', '</div></body>')
        
        # Replace QR code placeholder with text for preview
        html_content = html_content.replace('{{QR_CODE}}', '<div style="border: 1px dashed #ccc; width: 100px; height: 100px; display: flex; align-items: center; justify-content: center; font-size: 10px;">QR CODE</div>')
        
        # Return HTML content with proper content type for preview
        from flask import Response
        return Response(html_content, mimetype='text/html')
        
    except Exception as e:
        current_app.logger.error(f"Error previewing HTML for cuti {cuti_id}: {str(e)}")
        flash('Error loading preview', 'error')
        return redirect(url_for('cuti.list_cuti'))


@cuti_bp.route('/download-cuti-pdf/<int:cuti_id>')
@login_required
def download_cuti_pdf(cuti_id):
    """Download PDF for existing cuti application"""
    try:
        cuti = Cuti.query.get_or_404(cuti_id)
        
        # Check if PDF already exists
        if cuti.pdf_path and os.path.exists(cuti.pdf_path):
            pdf_path = cuti.pdf_path
            # Convert to absolute path for send_file
            if not os.path.isabs(pdf_path):
                pdf_path = os.path.join(current_app.root_path, '..', pdf_path)
                pdf_path = os.path.abspath(pdf_path)
            
            try:
                filename = generate_cuti_filename(cuti.nama, cuti.tgl_ajuan_cuti)
                return create_download_response(pdf_path, filename)
            except Exception as send_error:
                current_app.logger.error(f"Error sending existing PDF file: {str(send_error)}")
                # If sending fails, regenerate PDF
                pass
        
        # If PDF doesn't exist, generate it using multiple template methods
        result = None
        
        # Method 1: HTML Template (prioritas utama - selalu menghasilkan PDF)
        try:
            from config.html_template_handler import HtmlTemplateHandler
            template_handler = HtmlTemplateHandler()
            result = template_handler.fill_template_and_generate_pdf(cuti)
            if result['success']:
                print("✅ HTML template successful for download")
        except Exception as html_error:
            print(f"HTML template failed: {html_error}")
        
        # Method 2: Advanced DOCX Template (fallback - hanya jika berhasil convert ke PDF)
        if not result or not result['success']:
            try:
                from config.docx_template_advanced import AdvancedDocxTemplateHandler
                template_handler = AdvancedDocxTemplateHandler()
                result = template_handler.fill_template_and_generate_pdf(cuti)
                if result['success']:
                    # Verify that the result is actually a PDF file
                    pdf_path = result.get('pdf_path', '')
                    if pdf_path and pdf_path.endswith('.pdf') and os.path.exists(pdf_path):
                        print("✅ Advanced DOCX template successful for download")
                    else:
                        result = None
                        print("⚠️ Advanced DOCX template returned non-PDF file")
            except Exception as advanced_error:
                print(f"Advanced DOCX template failed: {advanced_error}")
        
        # Method 3: Basic DOCX Template (last resort - hanya jika berhasil convert ke PDF)
        if not result or not result['success']:
            try:
                from config.docx_template_handler import DocxTemplateHandler
                template_handler = DocxTemplateHandler()
                result = template_handler.fill_template_and_generate_pdf(cuti)
                if result['success']:
                    # Verify that the result is actually a PDF file
                    pdf_path = result.get('pdf_path', '')
                    if pdf_path and pdf_path.endswith('.pdf') and os.path.exists(pdf_path):
                        print("✅ Basic DOCX template successful for download")
                    else:
                        result = {'success': False, 'error': 'PDF conversion failed'}
                        print("⚠️ Basic DOCX template returned non-PDF file")
            except Exception as docx_error:
                print(f"Basic DOCX template failed: {docx_error}")
                result = {'success': False, 'error': 'All template methods failed'}
        
        if result and result['success']:
            pdf_path = result['pdf_path']
            
            # Verify file is actually a PDF
            if not pdf_path.endswith('.pdf') or not os.path.exists(pdf_path):
                flash('Error: File PDF tidak dapat dihasilkan', 'error')
                current_app.logger.error(f"PDF file invalid or not found: {pdf_path}")
                return redirect(url_for('cuti.list_cuti'))
            
            # Convert to absolute path for send_file
            if not os.path.isabs(pdf_path):
                pdf_path = os.path.join(current_app.root_path, '..', pdf_path)
                pdf_path = os.path.abspath(pdf_path)
            
            # Update cuti record with generated files info
            cuti.qr_code = result['signature_hash']
            cuti.pdf_path = pdf_path
            db.session.commit()
            
            try:
                current_app.logger.info(f"Sending PDF file: {pdf_path}")
                filename = generate_cuti_filename(cuti.nama, cuti.tgl_ajuan_cuti)
                return create_download_response(pdf_path, filename)
            except Exception as send_error:
                current_app.logger.error(f"Error sending PDF file: {str(send_error)}")
                import traceback
                current_app.logger.error(traceback.format_exc())
                flash('Error: Gagal mengirim file PDF', 'error')
                return redirect(url_for('cuti.list_cuti'))
        
        flash('PDF tidak dapat dihasilkan. Pastikan cuti sudah disetujui.', 'error')
        return redirect(url_for('cuti.list_cuti'))
        
    except Exception as e:
        current_app.logger.error(f"Error downloading PDF for cuti {cuti_id}: {str(e)}")
        flash('Error downloading PDF', 'error')
        return redirect(url_for('cuti.list_cuti'))

@cuti_bp.route('/generate-form-pdf/<int:cuti_id>')
@login_required
def generate_form_pdf(cuti_id):
    """Generate PDF formulir cuti dengan format resmi Mahkamah Agung"""
    try:
        # Get cuti data
        cuti = Cuti.query.get_or_404(cuti_id)
        
        # Generate PDF
        pdf_generator = CutiFormPDFGenerator()
        pdf_path = pdf_generator.create_cuti_form_from_model(cuti)
        
        # Return PDF file with enhanced download headers
        filename = generate_cuti_filename(cuti.nama, cuti.tgl_ajuan_cuti, "formulir_cuti")
        return create_download_response(pdf_path, filename)
        
    except Exception as e:
        current_app.logger.error(f"Error generating PDF form for cuti {cuti_id}: {str(e)}")
        flash(f'Error generating PDF form: {str(e)}', 'error')
        return redirect(url_for('cuti.list_cuti'))

@cuti_bp.route('/preview-form-pdf/<int:cuti_id>')
@login_required
def preview_form_pdf(cuti_id):
    """Preview formulir cuti sebelum generate PDF"""
    try:
        # Get cuti data
        cuti = Cuti.query.get_or_404(cuti_id)
        
        return render_template('cuti/preview_form_pdf.html', cuti=cuti)
        
    except Exception as e:
        current_app.logger.error(f"Error previewing PDF form for cuti {cuti_id}: {str(e)}")
        flash(f'Error loading preview: {str(e)}', 'error')
        return redirect(url_for('cuti.list_cuti'))