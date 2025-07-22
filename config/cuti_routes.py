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


@cuti_bp.route('/generate-cuti', methods=['GET', 'POST'])
@login_required
def generate_cuti():
    """Generate cuti form"""
    form = CutiForm()
    
    if form.validate_on_submit():
        try:
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
                lama_cuti=form.lama_cuti.data,
                status_cuti='pending'
            )
            
            db.session.add(new_cuti)
            db.session.commit()
            
            flash('Formulir cuti berhasil dibuat!', 'success')
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
                lama_cuti=form.lama_cuti.data,
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
        
        db.session.delete(cuti)
        db.session.commit()
        
        flash(f'Data cuti {nama_cuti} berhasil dihapus', 'success')
        return redirect(url_for('cuti.list_cuti'))
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error deleting cuti {cuti_id}: {str(e)}")
        flash('Error deleting cuti', 'error')
        return redirect(url_for('cuti.list_cuti'))