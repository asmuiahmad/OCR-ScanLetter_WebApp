"""
Surat Keluar routes
Outgoing document management functionality
"""

from flask import Blueprint, render_template, request, redirect, url_for, flash, current_app, jsonify
from flask_login import login_required
from sqlalchemy import desc, asc, func
from datetime import datetime

from config.extensions import db
from config.models import SuratKeluar
from config.forms import SuratKeluarForm
from config.route_utils import role_required

surat_keluar_bp = Blueprint('surat_keluar', __name__)


@surat_keluar_bp.route('/show_surat_keluar', methods=['GET'])
@login_required
def show_surat_keluar():
    """Show surat keluar list"""
    try:
        sort = request.args.get('sort', 'tanggal_suratKeluar')
        order = request.args.get('order', 'desc')
        page = request.args.get('page', 1, type=int)
        search = request.args.get('search', '').strip()
        
        sort_options = {
            'tanggal_suratKeluar': SuratKeluar.tanggal_suratKeluar,
            'pengirim_suratKeluar': SuratKeluar.pengirim_suratKeluar,
            'penerima_suratKeluar': SuratKeluar.penerima_suratKeluar,
            'nomor_suratKeluar': SuratKeluar.nomor_suratKeluar,
            'isi_suratKeluar': SuratKeluar.isi_suratKeluar,
            'created_at': SuratKeluar.created_at,
            'status_suratKeluar': SuratKeluar.status_suratKeluar
        }

        sort_column = sort_options.get(sort, SuratKeluar.tanggal_suratKeluar)
        order_by = asc(sort_column) if order == 'asc' else desc(sort_column)

        query = SuratKeluar.query

        if search:
            like_pattern = f"%{search}%"
            query = query.filter(
                (SuratKeluar.pengirim_suratKeluar.ilike(like_pattern)) |
                (SuratKeluar.penerima_suratKeluar.ilike(like_pattern)) |
                (SuratKeluar.nomor_suratKeluar.ilike(like_pattern)) |
                (SuratKeluar.isi_suratKeluar.ilike(like_pattern))
            )

        surat_keluar_entries = query.order_by(order_by).paginate(page=page, per_page=20)

        return render_template(
            'surat_keluar/show_surat_keluar.html',
            entries=surat_keluar_entries,
            sort=sort,
            order=order,
            search=search
        )
    except Exception as e:
        flash(f'Error: {str(e)}', 'error')
        return redirect(url_for('main.index'))


@surat_keluar_bp.route('/input_surat_keluar', methods=['GET', 'POST'])
@login_required
@role_required('admin', 'pimpinan')
def input_surat_keluar():
    """Input new surat keluar"""
    form = SuratKeluarForm()
    import logging
    logging.info(f"Form data received: {request.form}")
    logging.info(f"Files received: {request.files}")
    if form.validate_on_submit():
        try:
            new_surat_keluar = SuratKeluar(
                tanggal_suratKeluar=form.tanggal_suratKeluar.data,
                pengirim_suratKeluar=form.pengirim_suratKeluar.data,
                penerima_suratKeluar=form.penerima_suratKeluar.data,
                nomor_suratKeluar=form.nomor_suratKeluar.data,
                kode_suratKeluar=form.kode_suratKeluar.data,
                jenis_suratKeluar=form.jenis_suratKeluar.data,
                isi_suratKeluar=form.isi_suratKeluar.data,
                status_suratKeluar='pending',
                created_at=datetime.utcnow()
            )
            db.session.add(new_surat_keluar)
            db.session.commit()
            flash('Surat Keluar has been added successfully!', 'success')
            # Tetap di laman input, tidak redirect
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Error adding Surat Keluar: {str(e)}", exc_info=True)
            flash(f'Error adding Surat Keluar: {str(e)}', 'danger')
    elif request.method == 'POST':
        # Jika form tidak valid, tampilkan error detail
        current_app.logger.error(f"Form validation errors: {form.errors}")
        flash(f'Form validation errors: {form.errors}', 'danger')
    return render_template('surat_keluar/input_surat_keluar.html', form=form)


@surat_keluar_bp.route('/edit_surat_keluar/<int:id_suratKeluar>', methods=['GET', 'POST'])
@login_required
def edit_surat_keluar(id_suratKeluar):
    """Edit surat keluar"""
    surat_keluar = SuratKeluar.query.get_or_404(id_suratKeluar)
    
    if request.method == 'POST':
        try:
            # Update surat keluar fields
            surat_keluar.nomor_suratKeluar = request.form.get('nomor_suratKeluar', surat_keluar.nomor_suratKeluar)
            surat_keluar.pengirim_suratKeluar = request.form.get('pengirim_suratKeluar', surat_keluar.pengirim_suratKeluar)
            surat_keluar.penerima_suratKeluar = request.form.get('penerima_suratKeluar', surat_keluar.penerima_suratKeluar)
            surat_keluar.isi_suratKeluar = request.form.get('isi_suratKeluar', surat_keluar.isi_suratKeluar)
            
            from config.ocr_utils import calculate_overall_ocr_accuracy
            surat_keluar.ocr_accuracy_suratKeluar = calculate_overall_ocr_accuracy(surat_keluar, 'suratKeluar')
            
            if 'gambar_suratKeluar' in request.files:
                file = request.files['gambar_suratKeluar']
                if file and file.filename != '':
                    # Handle file upload if needed
                    pass
            
            db.session.commit()
            flash('Surat keluar berhasil diperbarui.', 'success')
            return redirect(url_for('surat_keluar.show_surat_keluar'))
        except Exception as e:
            db.session.rollback()
            flash(f'Gagal memperbarui surat keluar: {str(e)}', 'error')
    
    return render_template('surat_keluar/edit_surat_keluar.html', surat=surat_keluar)


@surat_keluar_bp.route('/delete_surat_keluar/<int:id_suratKeluar>', methods=['POST'])
@login_required
def delete_surat_keluar(id_suratKeluar):
    """Delete surat keluar"""
    surat_keluar = SuratKeluar.query.get_or_404(id_suratKeluar)
    
    try:
        db.session.delete(surat_keluar)
        db.session.commit()
        flash('Surat keluar berhasil dihapus.', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Gagal menghapus surat keluar: {str(e)}', 'error')
    
    return redirect(url_for('surat_keluar.show_surat_keluar'))


@surat_keluar_bp.route('/surat_keluar')
@login_required
def surat_keluar():
    """Surat keluar list (legacy route)"""
    daftar_surat = SuratKeluar.query.all()
    return render_template('surat_keluar/surat_keluar.html', daftar_surat=daftar_surat)


@surat_keluar_bp.route('/test_surat_keluar', methods=['GET'])
def test_surat_keluar():
    """Test surat keluar"""
    try:
        surat_keluar_entries = SuratKeluar.query.paginate(page=1, per_page=20)
        return render_template(
            'surat_keluar/show_surat_keluar.html',
            entries=surat_keluar_entries,
            sort='tanggal_suratKeluar',
            order='asc',
            search=''
        )
    except Exception as e:
        return f"Error: {str(e)}", 500


# Tambahan chart-data dari routes_old.py
@surat_keluar_bp.route('/chart-data')
@login_required
def chart_data():
    masuk = db.session.query(
        func.date(SuratKeluar.tanggal_suratKeluar).label('tanggal'),
        func.count().label('jumlah')
    ).group_by(func.date(SuratKeluar.tanggal_suratKeluar)).all()

    keluar = db.session.query(
        func.date(SuratKeluar.tanggal_suratKeluar).label('tanggal'),
        func.count().label('jumlah')
    ).group_by(func.date(SuratKeluar.tanggal_suratKeluar)).all()

    tanggal_set = set([m[0] for m in masuk] + [k[0] for k in keluar])
    tanggal_sorted = sorted(tanggal_set)

    data_masuk_dict = {m[0]: m[1] for m in masuk}
    data_keluar_dict = {k[0]: k[1] for k in keluar}

    data = {
        "labels": tanggal_sorted,
        "surat_keluar": [data_masuk_dict.get(t, 0) for t in tanggal_sorted],
        "surat_masuk": [data_keluar_dict.get(t, 0) for t in tanggal_sorted],
    }
    return jsonify(data)


@surat_keluar_bp.route('/approve-surat/<int:surat_id>', methods=['POST'])
@login_required
@role_required('pimpinan')
def approve_surat_keluar(surat_id):
    """Approve surat keluar - hanya pimpinan yang dapat menyetujui"""
    try:
        surat = SuratKeluar.query.get(surat_id)
        if not surat:
            return jsonify({
                "success": False, 
                "message": "Surat tidak ditemukan"
            }), 404
        
        if surat.status_suratKeluar != 'pending':
            return jsonify({
                "success": False, 
                "message": f"Surat sudah {surat.status_suratKeluar}. Tidak dapat diubah lagi."
            }), 400
        
        # Update status
        surat.status_suratKeluar = 'approved'
        
        db.session.commit()
        
        current_app.logger.info(f"Surat Keluar ID {surat_id} disetujui oleh {current_user.email}")
        
        return jsonify({
            "success": True, 
            "message": f"Surat dari {surat.pengirim_suratKeluar} berhasil disetujui",
            "surat_info": {
                "nomor": surat.nomor_suratKeluar,
                "pengirim": surat.pengirim_suratKeluar,
                "status": surat.status_suratKeluar
            }
        })
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error approving surat keluar {surat_id}: {str(e)}")
        return jsonify({
            "success": False, 
            "message": "Terjadi kesalahan saat menyetujui surat"
        }), 500


@surat_keluar_bp.route('/reject-surat/<int:surat_id>', methods=['POST'])
@login_required
@role_required('pimpinan')
def reject_surat_keluar(surat_id):
    """Reject surat keluar - hanya pimpinan yang dapat menolak"""
    try:
        surat = SuratKeluar.query.get(surat_id)
        if not surat:
            return jsonify({
                "success": False, 
                "message": "Surat tidak ditemukan"
            }), 404
        
        if surat.status_suratKeluar != 'pending':
            return jsonify({
                "success": False, 
                "message": f"Surat sudah {surat.status_suratKeluar}. Tidak dapat diubah lagi."
            }), 400
        
        # Update status
        surat.status_suratKeluar = 'rejected'
        
        db.session.commit()
        
        current_app.logger.info(f"Surat Keluar ID {surat_id} ditolak oleh {current_user.email}")
        
        return jsonify({
            "success": True, 
            "message": f"Surat dari {surat.pengirim_suratKeluar} berhasil ditolak",
            "surat_info": {
                "nomor": surat.nomor_suratKeluar,
                "pengirim": surat.pengirim_suratKeluar,
                "status": surat.status_suratKeluar
            }
        })
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error rejecting surat keluar {surat_id}: {str(e)}")
        return jsonify({
            "success": False, 
            "message": "Terjadi kesalahan saat menolak surat"
        }), 500