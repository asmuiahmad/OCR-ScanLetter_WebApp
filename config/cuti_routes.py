"""
Cuti routes
Leave/vacation management functionality
"""

import os
import qrcode
import tempfile
from io import BytesIO
from datetime import datetime

from flask import Blueprint, render_template, request, redirect, url_for, flash, send_file, current_app
from flask_login import login_required, current_user
from docx import Document
from mailmerge import MailMerge

from config.extensions import db
from config.models import Cuti, Pegawai
from config.forms import CutiForm, InputCutiForm
from config.route_utils import role_required

cuti_bp = Blueprint('cuti', __name__)


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
            
            # Try Advanced DOCX template first, then HTML, then basic DOCX
            result = None
            
            # Method 1: Advanced DOCX Template (docxtpl)
            try:
                from config.docx_template_advanced import AdvancedDocxTemplateHandler
                template_handler = AdvancedDocxTemplateHandler()
                result = template_handler.fill_template_and_generate_pdf(new_cuti)
                if result['success']:
                    print("✅ Advanced DOCX template successful")
            except Exception as advanced_error:
                print(f"Advanced DOCX template failed: {advanced_error}")
            
            # Method 2: HTML Template (fallback)
            if not result or not result['success']:
                try:
                    from config.html_template_handler import HtmlTemplateHandler
                    template_handler = HtmlTemplateHandler()
                    result = template_handler.fill_template_and_generate_pdf(new_cuti)
                    if result['success']:
                        print("✅ HTML template successful")
                except Exception as html_error:
                    print(f"HTML template failed: {html_error}")
            
            # Method 3: Basic DOCX Template (last resort)
            if not result or not result['success']:
                try:
                    from config.docx_template_handler import DocxTemplateHandler
                    template_handler = DocxTemplateHandler()
                    result = template_handler.fill_template_and_generate_pdf(new_cuti)
                    if result['success']:
                        print("✅ Basic DOCX template successful")
                except Exception as docx_error:
                    print(f"Basic DOCX template failed: {docx_error}")
                    result = {'success': False, 'error': 'All template methods failed'}
            
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
        
        return html_content
        
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
            return send_file(
                cuti.pdf_path,
                as_attachment=True,
                download_name=f"surat_cuti_{cuti.nama.replace(' ', '_')}_{cuti.id_cuti}.pdf",
                mimetype='application/pdf'
            )
        
        # If PDF doesn't exist, generate it using multiple template methods
        result = None
        
        # Method 1: Advanced DOCX Template (docxtpl) - prioritas utama
        try:
            from config.docx_template_advanced import AdvancedDocxTemplateHandler
            template_handler = AdvancedDocxTemplateHandler()
            result = template_handler.fill_template_and_generate_pdf(cuti)
            if result['success']:
                print("✅ Advanced DOCX template successful for download")
        except Exception as advanced_error:
            print(f"Advanced DOCX template failed: {advanced_error}")
        
        # Method 2: HTML Template (fallback)
        if not result or not result['success']:
            try:
                from config.html_template_handler import HtmlTemplateHandler
                template_handler = HtmlTemplateHandler()
                result = template_handler.fill_template_and_generate_pdf(cuti)
                if result['success']:
                    print("✅ HTML template successful for download")
            except Exception as html_error:
                print(f"HTML template failed: {html_error}")
        
        # Method 3: Basic DOCX Template (last resort)
        if not result or not result['success']:
            try:
                from config.docx_template_handler import DocxTemplateHandler
                template_handler = DocxTemplateHandler()
                result = template_handler.fill_template_and_generate_pdf(cuti)
                if result['success']:
                    print("✅ Basic DOCX template successful for download")
            except Exception as docx_error:
                print(f"Basic DOCX template failed: {docx_error}")
                result = {'success': False, 'error': 'All template methods failed'}
        
        if result['success']:
            # Update cuti record with generated files info
            cuti.qr_code = result['signature_hash']
            cuti.pdf_path = result['pdf_path']
            db.session.commit()
            
            return send_file(
                result['pdf_path'],
                as_attachment=True,
                download_name=f"surat_cuti_{cuti.nama.replace(' ', '_')}_{cuti.id_cuti}.pdf",
                mimetype='application/pdf'
            )
        
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
        
        # Return PDF file
        return send_file(
            pdf_path,
            as_attachment=True,
            download_name=f"formulir_cuti_{cuti.nama.replace(' ', '_')}_{cuti.id_cuti}.pdf",
            mimetype='application/pdf'
        )
        
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