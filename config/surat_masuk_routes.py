"""
Surat Masuk routes
Incoming document management functionality
"""

from datetime import datetime
from flask import Blueprint, render_template, request, redirect, url_for, flash, current_app, jsonify, send_file
from flask_login import login_required, current_user
from sqlalchemy import desc, asc, or_
import io

from config.extensions import db
from config.models import SuratMasuk, SuratKeluar
from config.forms import SuratMasukForm
from config.route_utils import role_required

surat_masuk_bp = Blueprint('surat_masuk', __name__)


@surat_masuk_bp.route('/show_surat_masuk', methods=['GET'])
@login_required
def show_surat_masuk():
    """Show surat masuk list"""
    try:
        search_query = request.args.get('search', '')
        
        sort = request.args.get('sort', 'created_at')
        order = request.args.get('order', 'desc')
        
        valid_sort_columns = [
            'tanggal_suratMasuk', 'pengirim_suratMasuk', 'penerima_suratMasuk', 
            'nomor_suratMasuk', 'isi_suratMasuk', 'created_at', 'status_suratMasuk'
        ]
        
        if sort not in valid_sort_columns:
            sort = 'created_at'
        
        order = 'desc' if order == 'desc' else 'asc'
        
        query = SuratMasuk.query

        if search_query:
            search_filter = f'%{search_query}%'
            query = query.filter(
                or_(
                    SuratMasuk.nomor_suratMasuk.ilike(search_filter),
                    SuratMasuk.pengirim_suratMasuk.ilike(search_filter),
                    SuratMasuk.penerima_suratMasuk.ilike(search_filter),
                    SuratMasuk.isi_suratMasuk.ilike(search_filter)
                )
            )
        
        if sort == 'tanggal_suratMasuk':
            query = query.order_by(SuratMasuk.tanggal_suratMasuk.desc() if order == 'desc' else SuratMasuk.tanggal_suratMasuk.asc())
        elif sort == 'pengirim_suratMasuk':
            query = query.order_by(SuratMasuk.pengirim_suratMasuk.desc() if order == 'desc' else SuratMasuk.pengirim_suratMasuk.asc())
        elif sort == 'penerima_suratMasuk':
            query = query.order_by(SuratMasuk.penerima_suratMasuk.desc() if order == 'desc' else SuratMasuk.penerima_suratMasuk.asc())
        elif sort == 'nomor_suratMasuk':
            query = query.order_by(SuratMasuk.nomor_suratMasuk.desc() if order == 'desc' else SuratMasuk.nomor_suratMasuk.asc())
        elif sort == 'isi_suratMasuk':
            query = query.order_by(SuratMasuk.isi_suratMasuk.desc() if order == 'desc' else SuratMasuk.isi_suratMasuk.asc())
        elif sort == 'status_suratMasuk':
            query = query.order_by(SuratMasuk.status_suratMasuk.desc() if order == 'desc' else SuratMasuk.status_suratMasuk.asc())
        else:
            query = query.order_by(SuratMasuk.created_at.desc() if order == 'desc' else SuratMasuk.created_at.asc())
        
        page = request.args.get('page', 1, type=int)
        per_page = 10
        entries = query.paginate(page=page, per_page=per_page, error_out=False)

        current_app.logger.info(f"Showing Surat Masuk - Page: {page}, Sort: {sort}, Order: {order}")

        return render_template('surat_masuk/show_surat_masuk.html',
                               entries=entries, 
                               sort=sort,
                               order=order)
    except Exception as e:
        current_app.logger.error(f"Error in show_surat_masuk: {str(e)}", exc_info=True)
        flash('An error occurred while retrieving Surat Masuk. Please try again later.', 'error')
        return redirect(url_for('main.index'))


@surat_masuk_bp.route('/input_surat_masuk', methods=['GET', 'POST'])
@login_required
@role_required('admin', 'pimpinan')
def input_surat_masuk():
    """Input new surat masuk"""
    form = SuratMasukForm()
    if form.validate_on_submit():
        try:
            new_surat_masuk = SuratMasuk(
                tanggal_suratMasuk=form.tanggal_suratMasuk.data,
                pengirim_suratMasuk=form.pengirim_suratMasuk.data,
                penerima_suratMasuk=form.penerima_suratMasuk.data,
                nomor_suratMasuk=form.nomor_suratMasuk.data,
                isi_suratMasuk=form.isi_suratMasuk.data,
                acara_suratMasuk=form.acara_suratMasuk.data,
                tempat_suratMasuk=form.tempat_suratMasuk.data,
                tanggal_acara_suratMasuk=form.tanggal_acara_suratMasuk.data,
                jam_suratMasuk=form.jam_suratMasuk.data,
                kode_suratMasuk='Not found',
                jenis_suratMasuk='Not found',
                status_suratMasuk='pending',
                created_at=datetime.utcnow()
            )
            db.session.add(new_surat_masuk)
            db.session.commit()
            
            return jsonify({
                'success': True,
                'message': 'Surat Masuk berhasil ditambahkan',
                'data': {
                    'id': new_surat_masuk.id_suratMasuk,
                    'nomor_surat': new_surat_masuk.nomor_suratMasuk,
                    'pengirim': new_surat_masuk.pengirim_suratMasuk,
                    'penerima': new_surat_masuk.penerima_suratMasuk
                }
            }), 200
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Error adding Surat Masuk: {str(e)}", exc_info=True)
            return jsonify({
                'success': False,
                'message': f'Gagal menambahkan Surat Masuk: {str(e)}'
            }), 500
    elif request.method == 'POST':
        # Jika form tidak valid, tampilkan error detail
        current_app.logger.error(f"Form validation errors: {form.errors}")
        flash(f'Form validation errors: {form.errors}', 'danger')
    return render_template('surat_masuk/input_surat_masuk.html', form=form)


@surat_masuk_bp.route('/edit_surat_masuk/<int:id>', methods=['GET', 'POST'])
@login_required
def edit_surat_masuk(id):
    """Edit surat masuk"""
    if not current_user.is_admin:
        flash('You do not have permission to access this page.', 'error')
        return redirect(url_for('main.index'))

    entry = SuratMasuk.query.get_or_404(id)
    
    if request.method == 'POST':
        try:
            # Update basic fields
            entry.tanggal_suratMasuk = datetime.strptime(request.form['tanggal_suratMasuk'], '%Y-%m-%d')
            entry.pengirim_suratMasuk = request.form['pengirim_suratMasuk']
            entry.penerima_suratMasuk = request.form['penerima_suratMasuk']
            entry.nomor_suratMasuk = request.form['nomor_suratMasuk']
            entry.isi_suratMasuk = request.form['isi_suratMasuk']
            
            # Handle optional fields
            entry.acara_suratMasuk = request.form.get('acara_suratMasuk', '')
            entry.tempat_suratMasuk = request.form.get('tempat_suratMasuk', '')
            entry.jam_suratMasuk = request.form.get('jam_suratMasuk', '')
            
            # Handle tanggal_acara_suratMasuk
            if request.form.get('tanggal_acara_suratMasuk'):
                try:
                    entry.tanggal_acara_suratMasuk = datetime.strptime(request.form['tanggal_acara_suratMasuk'], '%Y-%m-%d').date()
                except ValueError:
                    entry.tanggal_acara_suratMasuk = None
            else:
                entry.tanggal_acara_suratMasuk = None
            
            # Calculate OCR accuracy if function exists
            try:
                from config.ocr_utils import calculate_overall_ocr_accuracy
                entry.ocr_accuracy_suratMasuk = calculate_overall_ocr_accuracy(entry, 'suratMasuk')
            except ImportError:
                pass  # OCR utils not available
            
            db.session.commit()
            
            # Check if this is an AJAX request (check for XMLHttpRequest header)
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest' or 'application/json' in request.headers.get('Accept', ''):
                return jsonify({
                    'success': True,
                    'message': 'Surat Masuk berhasil diperbarui',
                    'data': {
                        'id': entry.id_suratMasuk,
                        'nomor_surat': entry.nomor_suratMasuk,
                        'pengirim': entry.pengirim_suratMasuk,
                        'penerima': entry.penerima_suratMasuk
                    }
                }), 200
            else:
                # Regular form submission
                flash('Surat Masuk berhasil diperbarui!', 'success')
                return redirect(url_for('surat_masuk.show_surat_masuk'))
                
        except Exception as e:
            db.session.rollback()
            error_msg = f'Error updating Surat Masuk: {str(e)}'
            
            # Check if this is an AJAX request
            if request.headers.get('Content-Type') == 'application/json' or request.is_json:
                return jsonify({
                    'success': False,
                    'message': error_msg
                }), 500
            else:
                flash(error_msg, 'error')
                return render_template('surat_masuk/edit_surat_masuk_simple.html', entry=entry)
    
    # GET request - show the form
    try:
        return render_template('surat_masuk/edit_surat_masuk_simple.html', entry=entry)
    except Exception as e:
        flash(f'Error loading edit form: {str(e)}', 'error')
        return redirect(url_for('surat_masuk.show_surat_masuk'))


@surat_masuk_bp.route('/delete_surat_masuk/<int:id>', methods=['POST'])
@login_required
def delete_surat_masuk(id):
    """Delete surat masuk"""
    entry = SuratMasuk.query.get_or_404(id)
    db.session.delete(entry)
    db.session.commit()
    flash('Surat Masuk has been deleted successfully!', 'success')
    return redirect(url_for('surat_masuk.show_surat_masuk'))


@surat_masuk_bp.route('/list-pending-surat-masuk')
@login_required
@role_required('pimpinan')
def list_pending_surat_masuk():
    """List pending surat masuk"""
    try:
        pending_surat_masuk = SuratMasuk.query.filter_by(status_suratMasuk='pending').all()
        return render_template('surat_masuk/list_pending_surat_masuk.html', 
                               pending_surat_masuk=pending_surat_masuk)
    except Exception as e:
        current_app.logger.error(f"Error in list_pending_surat_masuk: {str(e)}")
        flash('Terjadi kesalahan saat memuat daftar surat pending.', 'error')
        return redirect(url_for('main.index'))


@surat_masuk_bp.route('/approve-surat/<int:surat_id>', methods=['POST'])
@login_required
@role_required('pimpinan')
def approve_surat(surat_id):
    """Approve surat - hanya pimpinan yang dapat menyetujui"""
    try:
        surat = SuratMasuk.query.get(surat_id)
        if not surat:
            return jsonify({
                "success": False, 
                "message": "Surat tidak ditemukan"
            }), 404
        
        if surat.status_suratMasuk != 'pending':
            return jsonify({
                "success": False, 
                "message": f"Surat sudah {surat.status_suratMasuk}. Tidak dapat diubah lagi."
            }), 400
        
        # Update status
        surat.status_suratMasuk = 'approved'
        
        db.session.commit()
        
        current_app.logger.info(f"Surat ID {surat_id} disetujui oleh {current_user.email}")
        
        return jsonify({
            "success": True, 
            "message": f"Surat dari {surat.pengirim_suratMasuk} berhasil disetujui",
            "surat_info": {
                "nomor": surat.nomor_suratMasuk,
                "pengirim": surat.pengirim_suratMasuk,
                "status": surat.status_suratMasuk
            }
        })
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error approving surat {surat_id}: {str(e)}")
        return jsonify({
            "success": False, 
            "message": "Terjadi kesalahan saat menyetujui surat"
        }), 500


@surat_masuk_bp.route('/reject-surat/<int:surat_id>', methods=['POST'])
@login_required
@role_required('pimpinan')
def reject_surat(surat_id):
    """Reject surat - hanya pimpinan yang dapat menolak"""
    try:
        surat = SuratMasuk.query.get(surat_id)
        if not surat:
            return jsonify({
                "success": False, 
                "message": "Surat tidak ditemukan"
            }), 404
        
        if surat.status_suratMasuk != 'pending':
            return jsonify({
                "success": False, 
                "message": f"Surat sudah {surat.status_suratMasuk}. Tidak dapat diubah lagi."
            }), 400
        
        # Update status
        surat.status_suratMasuk = 'rejected'
        
        db.session.commit()
        
        current_app.logger.info(f"Surat ID {surat_id} ditolak oleh {current_user.email}")
        
        return jsonify({
            "success": True, 
            "message": f"Surat dari {surat.pengirim_suratMasuk} berhasil ditolak",
            "surat_info": {
                "nomor": surat.nomor_suratMasuk,
                "pengirim": surat.pengirim_suratMasuk,
                "status": surat.status_suratMasuk
            }
        })
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error rejecting surat {surat_id}: {str(e)}")
        return jsonify({
            "success": False, 
            "message": "Terjadi kesalahan saat menolak surat"
        }), 500


@surat_masuk_bp.route('/api/surat-masuk/detail/<int:surat_id>', methods=['GET'])
@login_required
@role_required('pimpinan')
def get_surat_masuk_detail(surat_id):
    try:
        surat = SuratMasuk.query.get(surat_id)
        if not surat:
            return jsonify({
                'success': False,
                'message': f'Surat dengan ID {surat_id} tidak ditemukan'
            }), 404
        tanggal_str = surat.tanggal_suratMasuk.strftime('%d/%m/%Y') if surat.tanggal_suratMasuk else ''
        created_at_str = surat.created_at.strftime('%Y-%m-%d %H:%M') if surat.created_at else ''
        surat_data = {
            'id_suratMasuk': surat.id_suratMasuk,
            'nomor_suratMasuk': str(surat.nomor_suratMasuk) if surat.nomor_suratMasuk else '',
            'tanggal_suratMasuk': tanggal_str,
            'pengirim_suratMasuk': str(surat.pengirim_suratMasuk) if surat.pengirim_suratMasuk else '',
            'penerima_suratMasuk': str(surat.penerima_suratMasuk) if surat.penerima_suratMasuk else '',
            'isi_suratMasuk': str(surat.isi_suratMasuk) if surat.isi_suratMasuk else '',
            'status_suratMasuk': str(surat.status_suratMasuk) if surat.status_suratMasuk else 'pending',
            'file_suratMasuk': bool(surat.file_suratMasuk),
            'has_gambar': bool(surat.gambar_suratMasuk),
            'created_at': created_at_str
        }
        return jsonify({
            'success': True,
            'surat': surat_data
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Gagal memuat detail surat: {str(e)}'
        }), 500

@surat_masuk_bp.route('/surat-masuk/download/<int:id>')
@login_required
@role_required('pimpinan')
def download_surat_masuk(id):
    surat_masuk = SuratMasuk.query.get_or_404(id)
    if not surat_masuk.file_suratMasuk:
        flash('Dokumen tidak tersedia.', 'error')
        return redirect(url_for('surat_masuk.detail_surat_masuk', id=id))
    try:
        return send_file(
            surat_masuk.file_suratMasuk,
            as_attachment=True,
            download_name=f"Surat_Masuk_{surat_masuk.nomor_suratMasuk}.pdf"
        )
    except Exception as e:
        flash('Gagal mengunduh dokumen.', 'error')
        return redirect(url_for('surat_masuk.detail_surat_masuk', id=id))

@surat_masuk_bp.route('/surat-masuk/image/<int:id>')
@login_required
@role_required('pimpinan')
def view_surat_masuk_image(id):
    try:
        surat = SuratMasuk.query.get_or_404(id)
        if surat.gambar_suratMasuk:
            return send_file(
                io.BytesIO(surat.gambar_suratMasuk),
                mimetype='image/jpeg',
                as_attachment=False
            )
        else:
            return jsonify({'error': 'Gambar tidak ditemukan'}), 404
    except Exception as e:
        return jsonify({'error': 'Terjadi kesalahan saat memuat gambar'}), 500

@surat_masuk_bp.route('/test-ocr-enhancement', methods=['POST'])
@login_required
@role_required('admin', 'pimpinan')
def test_ocr_enhancement():
    """Test OCR text enhancement"""
    try:
        from config.ocr_text_processor import ocr_processor
        from config.ocr_surat_masuk_enhancer import surat_masuk_enhancer
        
        # Get test text from request
        test_text = request.json.get('text', '')
        field_type = request.json.get('field_type', 'isi_surat')
        
        if not test_text:
            return jsonify({
                'success': False,
                'message': 'No text provided for testing'
            }), 400
        
        # Process with OCR text processor
        cleaned_text = ocr_processor.clean_ocr_text(test_text)
        
        # Enhance with surat masuk enhancer
        enhanced_text = surat_masuk_enhancer.enhance_surat_masuk_text(cleaned_text, field_type)
        
        # Get quality score
        quality_score = ocr_processor.get_text_quality_score(enhanced_text)
        
        # Detect surat type if isi_surat
        surat_type = None
        if field_type == 'isi_surat':
            surat_type = surat_masuk_enhancer.detect_surat_type(enhanced_text)
        
        return jsonify({
            'success': True,
            'original': test_text,
            'cleaned': cleaned_text,
            'enhanced': enhanced_text,
            'quality_score': quality_score,
            'surat_type': surat_type,
            'improvements': {
                'length_change': len(enhanced_text) - len(test_text),
                'word_count_change': len(enhanced_text.split()) - len(test_text.split())
            }
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Error testing OCR enhancement: {str(e)}'
        }), 500

@surat_masuk_bp.route('/test-ocr-enhancement-page')
@login_required
@role_required('admin', 'pimpinan')
def test_ocr_enhancement_page():
    """Halaman untuk test OCR enhancement"""
    return render_template('surat_masuk/test_ocr_enhancement.html')

@surat_masuk_bp.route('/update-ocr-accuracy/<int:id>', methods=['POST'])
@login_required
@role_required('admin', 'pimpinan')
def update_ocr_accuracy(id):
    try:
        surat_type = request.form.get('type')  # 'masuk' or 'keluar'
        if surat_type == 'masuk':
            surat = SuratMasuk.query.get_or_404(id)
            try:
                from config.ocr_utils import calculate_overall_ocr_accuracy
                surat.ocr_accuracy_suratMasuk = calculate_overall_ocr_accuracy(surat, 'suratMasuk')
            except ImportError:
                surat.ocr_accuracy_suratMasuk = 0
        elif surat_type == 'keluar':
            surat = SuratKeluar.query.get_or_404(id)
            try:
                from config.ocr_utils import calculate_overall_ocr_accuracy
                surat.ocr_accuracy_suratKeluar = calculate_overall_ocr_accuracy(surat, 'suratKeluar')
            except ImportError:
                surat.ocr_accuracy_suratKeluar = 0
        else:
            return jsonify({"success": False, "error": "Invalid surat type"})
        
        db.session.commit()
        accuracy_field = f'ocr_accuracy_surat{surat_type.title()}'
        accuracy_value = getattr(surat, accuracy_field, 0)
        return jsonify({"success": True, "accuracy": accuracy_value})
        
    except Exception as e:
        db.session.rollback()
        return jsonify({"success": False, "error": str(e)})

@surat_masuk_bp.route('/api/debug/surat/<int:surat_id>', methods=['GET'])
@login_required
@role_required('pimpinan')
def debug_surat_detail(surat_id):
    try:
        surat = SuratMasuk.query.get(surat_id)
        if not surat:
            return jsonify({
                'success': False,
                'message': f'Surat dengan ID {surat_id} tidak ditemukan'
            }), 404
        return jsonify({
            'success': True,
            'surat_id': surat_id,
            'raw_data': {
                'id_suratMasuk': surat.id_suratMasuk,
                'nomor_suratMasuk': surat.nomor_suratMasuk,
                'tanggal_suratMasuk': str(surat.tanggal_suratMasuk) if surat.tanggal_suratMasuk else None,
                'pengirim_suratMasuk': surat.pengirim_suratMasuk,
                'penerima_suratMasuk': surat.penerima_suratMasuk,
                'perihal_suratMasuk': getattr(surat, 'perihal_suratMasuk', None),
                'isi_suratMasuk': surat.isi_suratMasuk,
                'status_suratMasuk': surat.status_suratMasuk,
                'file_suratMasuk': str(surat.file_suratMasuk),
                'created_at': str(surat.created_at) if surat.created_at else None
            }
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e),
            'error_type': type(e).__name__
        }), 500

@surat_masuk_bp.route('/api/surat-masuk/<int:id>')
@login_required
def get_surat_masuk_api(id):
    """API endpoint to get surat masuk data for editing"""
    try:
        entry = SuratMasuk.query.get_or_404(id)
        
        return jsonify({
            'success': True,
            'data': {
                'id_suratMasuk': entry.id_suratMasuk,
                'tanggal_suratMasuk': entry.tanggal_suratMasuk.strftime('%Y-%m-%d') if entry.tanggal_suratMasuk else '',
                'pengirim_suratMasuk': entry.pengirim_suratMasuk,
                'penerima_suratMasuk': entry.penerima_suratMasuk,
                'nomor_suratMasuk': entry.nomor_suratMasuk,
                'isi_suratMasuk': entry.isi_suratMasuk,
                'acara_suratMasuk': entry.acara_suratMasuk,
                'tempat_suratMasuk': entry.tempat_suratMasuk,
                'tanggal_acara_suratMasuk': entry.tanggal_acara_suratMasuk.strftime('%Y-%m-%d') if entry.tanggal_acara_suratMasuk else '',
                'jam_suratMasuk': entry.jam_suratMasuk,
                'status_suratMasuk': entry.status_suratMasuk
            }
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Error: {str(e)}'
        }), 500

@surat_masuk_bp.route('/surat_masuk/detail/<int:id>')
@login_required
@role_required('pimpinan')
def detail_surat_masuk(id):
    surat_masuk = SuratMasuk.query.get_or_404(id)
    return render_template('surat_masuk/detail_surat_masuk.html', surat=surat_masuk)