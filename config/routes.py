# 🔹 Standard Library Imports
import os
import io
import tempfile
import subprocess
from collections import defaultdict
from calendar import monthrange
from datetime import datetime, timedelta
from functools import wraps

# 🔹 Third-Party Library Imports
import pytesseract
from flask import (
    render_template, request, send_file, redirect, url_for,
    flash, jsonify, session, Blueprint, g, current_app, send_from_directory
)
from flask_login import (
    login_user, login_required, logout_user, current_user
)
from werkzeug.security import check_password_hash, generate_password_hash
from werkzeug.utils import secure_filename
from sqlalchemy import desc, asc, extract, func, or_
from docx import Document
from mailmerge import MailMerge

# 🔹 Local Application Imports
from config.extensions import db
from config.ocr import ocr_bp
from config.ocr_utils import hitung_field_not_found
from config.models import User, SuratMasuk, SuratKeluar, Pegawai
from config.forms import LoginForm, RegistrationForm, SuratMasukForm
from config.ocr_cuti import ocr_cuti_bp

# Create main blueprint for routes
main_bp = Blueprint('main', __name__)

# Create auth blueprint
auth_bp = Blueprint('auth', __name__)

def role_required(*roles):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not current_user.is_authenticated or current_user.role not in roles:
                return jsonify({"error": "Unauthorized"}), 403
            return f(*args, **kwargs)
        return decorated_function
    return decorator

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user and form.password.data and check_password_hash(user.password, form.password.data):
            if not user.is_approved:
                flash('Your account is pending approval by an administrator.', 'warning')
                return render_template('auth/login.html', form=form)
            
            user.last_login = datetime.now()
            if user.login_count is None:
                user.login_count = 0
            user.login_count += 1
            db.session.commit()
            login_user(user)
            return redirect(url_for('main.index'))
        flash('Invalid email or password', 'error')
    return render_template('auth/login.html', form=form)

@auth_bp.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('auth.login'))

@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    form = RegistrationForm()
    if form.validate_on_submit():
        try:
            # Check if user already exists
            existing_user = User.query.filter_by(email=form.email.data).first()
            if existing_user:
                flash('Email already registered. Please use a different email or login.', 'error')
                return render_template('auth/register.html', form=form)
            
            # Create new user
            hashed_password = generate_password_hash(form.password.data, method='pbkdf2:sha256')
            new_user = User(
                email=form.email.data, 
                password=hashed_password,
                role=form.role.data,
                is_approved=False
            )
            
            # Set is_admin flag if role is admin
            if form.role.data == 'admin':
                new_user.is_admin = True
            
            db.session.add(new_user)
            db.session.commit()
            flash('Registration successful! Your account is pending approval by an administrator.', 'success')
            return redirect(url_for('auth.login'))
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f'Registration error: {str(e)}')
            flash(f'An error occurred during registration. Please try again.', 'error')
    elif form.errors:
        # Log form validation errors
        current_app.logger.warning(f'Registration form validation errors: {form.errors}')
        for field, errors in form.errors.items():
            for error in errors:
                flash(f'{field}: {error}', 'error')
    
    return render_template('auth/register.html', form=form)

@main_bp.before_app_request
def set_pending_surat_counts():
    # Initialize default values
    g.pending_surat_keluar_count = 0
    
    # Set counts for authenticated users who can see notifications
    try:
        if current_user.is_authenticated:
            # Show count for pimpinan and admin users
            if current_user.role in ['pimpinan', 'admin']:
                g.pending_surat_keluar_count = SuratKeluar.query.filter_by(status_suratKeluar='pending').count()
                current_app.logger.debug(f"Pending count for {current_user.email}: {g.pending_surat_keluar_count}")
    except Exception as e:
        # Log the error but don't break the application
        current_app.logger.warning(f"Error in set_pending_surat_counts: {str(e)}")
        g.pending_surat_keluar_count = 0

@main_bp.route('/')
@login_required
def index():
    # Total surat
    suratMasuk_count = SuratMasuk.query.count()
    suratKeluar_count = SuratKeluar.query.count()

    # Statistik tahunan
    today = datetime.now()
    year = today.year
    month = today.month
    week_start = today - timedelta(days=today.weekday())

    suratMasuk_this_year = SuratMasuk.query.filter(
        extract('year', SuratMasuk.tanggal_suratMasuk) == year
    ).count()
    suratKeluar_this_year = SuratKeluar.query.filter(
        extract('year', SuratKeluar.tanggal_suratKeluar) == year
    ).count()

    # Statistik bulanan
    suratMasuk_this_month = SuratMasuk.query.filter(
        extract('year', SuratMasuk.tanggal_suratMasuk) == year,
        extract('month', SuratMasuk.tanggal_suratMasuk) == month
    ).count()
    suratKeluar_this_month = SuratKeluar.query.filter(
        extract('year', SuratKeluar.tanggal_suratKeluar) == year,
        extract('month', SuratKeluar.tanggal_suratKeluar) == month
    ).count()

    # Statistik mingguan
    suratMasuk_this_week = SuratMasuk.query.filter(
        SuratMasuk.tanggal_suratMasuk >= week_start
    ).count()
    suratKeluar_this_week = SuratKeluar.query.filter(
        SuratKeluar.tanggal_suratKeluar >= week_start
    ).count()

    # Surat terbaru
    recent_surat_masuk = SuratMasuk.query.order_by(SuratMasuk.tanggal_suratMasuk.desc()).limit(5).all()
    recent_surat_keluar = SuratKeluar.query.order_by(SuratKeluar.tanggal_suratKeluar.desc()).limit(5).all()

    # Pengguna terbaru
    users = User.query.order_by(User.last_login.desc()).limit(5).all()

    return render_template(
        'home/index.html', 
        suratMasuk_count=suratMasuk_count,
        suratKeluar_count=suratKeluar_count,
        suratMasuk_this_year=suratMasuk_this_year,
        suratKeluar_this_year=suratKeluar_this_year,
        suratMasuk_this_month=suratMasuk_this_month,
        suratKeluar_this_month=suratKeluar_this_month,
        suratMasuk_this_week=suratMasuk_this_week,
        suratKeluar_this_week=suratKeluar_this_week,
        recent_surat_masuk=recent_surat_masuk,
        recent_surat_keluar=recent_surat_keluar,
        users=users
    )

@main_bp.route('/users', methods=['GET'])
@login_required
def user_list():
    users = User.query.all()
    return render_template('auth/user_list.html', users=users)

@main_bp.route('/last-logins', methods=['GET'])
def last_logins():
    users = User.query.order_by(User.last_login.desc()).limit(10).all()
    result = [{"username": user.email, "last_login": user.last_login.strftime('%Y-%m-%d %H:%M:%S') if user.last_login else 'Never'} for user in users]
    return jsonify(result)

@main_bp.route('/api/notifications/count', methods=['GET'])
@login_required
def get_notification_count():
    """API endpoint untuk mendapatkan jumlah notifikasi pending"""
    try:
        if current_user.role in ['pimpinan', 'admin']:
            pending_count = SuratKeluar.query.filter_by(status_suratKeluar='pending').count()
            return jsonify({
                'success': True,
                'pending_count': pending_count
            })
        else:
            return jsonify({
                'success': False,
                'message': 'Unauthorized'
            }), 403
    except Exception as e:
        current_app.logger.error(f"Error getting notification count: {str(e)}")
        return jsonify({
            'success': False,
            'message': 'Internal server error'
        }), 500

@main_bp.route('/api/test', methods=['GET'])
@login_required
def test_api():
    """Test endpoint untuk memeriksa apakah API berfungsi"""
    return jsonify({
        'success': True,
        'message': 'API berfungsi dengan baik',
        'user': current_user.email,
        'role': current_user.role
    })

@main_bp.route('/api/surat-keluar/detail/<int:surat_id>', methods=['GET'])
@login_required
@role_required('pimpinan')
def get_surat_keluar_detail(surat_id):
    """API endpoint untuk mendapatkan detail surat keluar dalam format JSON"""
    try:
        # Check if surat exists
        surat = SuratKeluar.query.get(surat_id)
        if not surat:
            return jsonify({
                'success': False,
                'message': f'Surat dengan ID {surat_id} tidak ditemukan'
            }), 404
        
        # Safely format date
        try:
            tanggal_str = surat.tanggal_suratKeluar.strftime('%d/%m/%Y') if surat.tanggal_suratKeluar else ''
        except Exception as e:
            current_app.logger.error(f"Error formatting date: {str(e)}")
            tanggal_str = ''
        
        # Safely format created_at
        try:
            created_at_str = surat.created_at.strftime('%Y-%m-%d %H:%M') if surat.created_at else ''
        except Exception as e:
            current_app.logger.error(f"Error formatting created_at: {str(e)}")
            created_at_str = ''
        
        # Build surat data with safe string conversion
        surat_data = {
            'id_suratKeluar': surat.id_suratKeluar,
            'nomor_suratKeluar': str(surat.nomor_suratKeluar) if surat.nomor_suratKeluar else '',
            'tanggal_suratKeluar': tanggal_str,
            'pengirim_suratKeluar': str(surat.pengirim_suratKeluar) if surat.pengirim_suratKeluar else '',
            'penerima_suratKeluar': str(surat.penerima_suratKeluar) if surat.penerima_suratKeluar else '',
            'isi_suratKeluar': str(surat.isi_suratKeluar) if surat.isi_suratKeluar else '',
            'status_suratKeluar': str(surat.status_suratKeluar) if surat.status_suratKeluar else 'pending',
            'file_suratKeluar': bool(surat.file_suratKeluar),
            'has_gambar': bool(surat.gambar_suratKeluar),
            'created_at': created_at_str
        }
        
        current_app.logger.info(f"Successfully retrieved surat data for ID {surat_id}")
        
        return jsonify({
            'success': True,
            'surat': surat_data
        })
        
    except Exception as e:
        current_app.logger.error(f"Error getting surat keluar detail for ID {surat_id}: {str(e)}", exc_info=True)
        return jsonify({
            'success': False,
            'message': f'Gagal memuat detail surat: {str(e)}'
        }), 500

@main_bp.route('/show_surat_keluar', methods=['GET'])
@login_required
def show_surat_keluar():
    try:
        # Ambil parameter pencarian
        search_query = request.args.get('search', '')
        
        # Ambil parameter sorting
        sort = request.args.get('sort', 'created_at')
        order = request.args.get('order', 'desc')
        
        # Daftar kolom yang valid untuk sorting
        valid_sort_columns = [
            'tanggal_suratKeluar', 'pengirim_suratKeluar', 'penerima_suratKeluar', 
            'nomor_suratKeluar', 'isi_suratKeluar', 'created_at', 'status_suratKeluar'
        ]
        
        # Validasi kolom sorting
        if sort not in valid_sort_columns:
            sort = 'created_at'
        
        # Tentukan arah sorting
        order = 'desc' if order == 'desc' else 'asc'
        
        # Buat query dasar
        query = SuratKeluar.query

        # Tambahkan filter pencarian jika ada
        if search_query:
            search_filter = f'%{search_query}%'
            query = query.filter(
                or_(
                    SuratKeluar.nomor_suratKeluar.ilike(search_filter),
                    SuratKeluar.pengirim_suratKeluar.ilike(search_filter),
                    SuratKeluar.penerima_suratKeluar.ilike(search_filter),
                    SuratKeluar.isi_suratKeluar.ilike(search_filter)
                )
            )
        
        # Tambahkan sorting
        if sort == 'tanggal_suratKeluar':
            query = query.order_by(SuratKeluar.tanggal_suratKeluar.desc() if order == 'desc' else SuratKeluar.tanggal_suratKeluar.asc())
        elif sort == 'pengirim_suratKeluar':
            query = query.order_by(SuratKeluar.pengirim_suratKeluar.desc() if order == 'desc' else SuratKeluar.pengirim_suratKeluar.asc())
        elif sort == 'penerima_suratKeluar':
            query = query.order_by(SuratKeluar.penerima_suratKeluar.desc() if order == 'desc' else SuratKeluar.penerima_suratKeluar.asc())
        elif sort == 'nomor_suratKeluar':
            query = query.order_by(SuratKeluar.nomor_suratKeluar.desc() if order == 'desc' else SuratKeluar.nomor_suratKeluar.asc())
        elif sort == 'isi_suratKeluar':
            query = query.order_by(SuratKeluar.isi_suratKeluar.desc() if order == 'desc' else SuratKeluar.isi_suratKeluar.asc())
        elif sort == 'status_suratKeluar':
            query = query.order_by(SuratKeluar.status_suratKeluar.desc() if order == 'desc' else SuratKeluar.status_suratKeluar.asc())
        else:
            # Default sorting by created_at
            query = query.order_by(SuratKeluar.created_at.desc() if order == 'desc' else SuratKeluar.created_at.asc())
        
        # Lakukan paginasi
        page = request.args.get('page', 1, type=int)
        per_page = 10  # Jumlah item per halaman
        entries = query.paginate(page=page, per_page=per_page, error_out=False)

        # Debugging: Log query details
        current_app.logger.info(f"Showing Surat Keluar - Page: {page}, Sort: {sort}, Order: {order}")

        return render_template('home/show_surat_keluar.html',
                               entries=entries, 
                               sort=sort,
                               order=order)
    except Exception as e:
        # Log the full error details with traceback
        current_app.logger.error(f"Error in show_surat_keluar: {str(e)}", exc_info=True)
        
        # Flash a user-friendly error message
        flash('An error occurred while retrieving Surat Keluar. Please try again later.', 'error')
        
        # Redirect to a safe page
        return redirect(url_for('main.index'))

@main_bp.route('/show_surat_masuk', methods=['GET'])
@login_required
def show_surat_masuk():
    try:
        sort = request.args.get('sort', 'tanggal_suratMasuk')
        order = request.args.get('order', 'desc')
        page = request.args.get('page', 1, type=int)
        search = request.args.get('search', '').strip()
        
        sort_options = {
            'tanggal_suratMasuk': SuratMasuk.tanggal_suratMasuk,
            'pengirim_suratMasuk': SuratMasuk.pengirim_suratMasuk,
            'penerima_suratMasuk': SuratMasuk.penerima_suratMasuk,
            'nomor_suratMasuk': SuratMasuk.nomor_suratMasuk,
            'isi_suratMasuk': SuratMasuk.isi_suratMasuk,
            'created_at': SuratMasuk.created_at,
            'status_suratMasuk': SuratMasuk.status_suratMasuk
        }

        sort_column = sort_options.get(sort, SuratMasuk.tanggal_suratMasuk)
        order_by = asc(sort_column) if order == 'asc' else desc(sort_column)

        query = SuratMasuk.query

        if search:
            like_pattern = f"%{search}%"
            query = query.filter(
                (SuratMasuk.pengirim_suratMasuk.ilike(like_pattern)) |
                (SuratMasuk.penerima_suratMasuk.ilike(like_pattern)) |
                (SuratMasuk.nomor_suratMasuk.ilike(like_pattern)) |
                (SuratMasuk.isi_suratMasuk.ilike(like_pattern))
            )

        surat_masuk_entries = query.order_by(order_by).paginate(page=page, per_page=20)

        return render_template(
            'home/show_surat_masuk.html',
            entries=surat_masuk_entries,
            sort=sort,
            order=order,
            search=search
        )
    except Exception as e:
        flash(f'Error: {str(e)}', 'error')
        return redirect(url_for('show_surat_masuk'))

@main_bp.route('/test_surat_masuk', methods=['GET'])
def test_surat_masuk():
    # Test route without login requirement
    try:
        surat_masuk_entries = SuratMasuk.query.paginate(page=1, per_page=20)
        return render_template(
            'home/show_surat_masuk.html',
            entries=surat_masuk_entries,
            sort='tanggal_suratMasuk',
            order='asc',
            search=''
        )
    except Exception as e:
        return f"Error: {str(e)}", 500

@main_bp.route('/input_surat_masuk', methods=['GET', 'POST'])
@login_required
@role_required('admin', 'pimpinan')
def input_surat_masuk():
    form = SuratMasukForm()
    if form.validate_on_submit():
        try:
            # Get file data
            file_data = None
            if form.image.data:
                file_data = form.image.data.read()

            # Create new SuratMasuk object
            new_surat = SuratMasuk(
                tanggal_suratMasuk=form.tanggal_suratMasuk.data,
                pengirim_suratMasuk=form.pengirim_suratMasuk.data,
                penerima_suratMasuk=form.penerima_suratMasuk.data,
                nomor_suratMasuk=form.nomor_suratMasuk.data,
                kode_suratMasuk=form.kode_suratMasuk.data,
                jenis_suratMasuk=form.jenis_suratMasuk.data,
                isi_suratMasuk=form.isi_suratMasuk.data,
                full_letter_number=form.nomor_suratMasuk.data,
                gambar_suratMasuk=file_data,
                status_suratMasuk='approved'
            )

            db.session.add(new_surat)
            db.session.commit()
            flash('Surat Masuk has been added successfully!', 'success')
            return redirect(url_for('show_surat_masuk'))

        except Exception as e:
            db.session.rollback()
            flash(f'Error adding Surat Masuk: {str(e)}', 'danger')

    return render_template('home/input_surat_masuk.html', form=form)

@main_bp.route('/input_surat_keluar', methods=['GET', 'POST'])
@login_required
@role_required('admin', 'pimpinan')
def input_surat_keluar():
    # 🔒 Ensure access for admin and pimpinan
    if request.method == 'POST':
        try:
            tanggal_suratKeluar = request.form['tanggal_suratKeluar']
            pengirim_suratKeluar = request.form['pengirim_suratKeluar']
            penerima_suratKeluar = request.form['penerima_suratKeluar']
            nomor_suratKeluar = request.form['nomor_suratKeluar']
            isi_suratKeluar = request.form['isi_suratKeluar']
            
            # Field acara (opsional)
            acara_suratKeluar = request.form.get('acara_suratKeluar', '')
            tempat_suratKeluar = request.form.get('tempat_suratKeluar', '')
            jam_suratKeluar = request.form.get('jam_suratKeluar', '')
            
            # Tanggal acara (opsional)
            tanggal_acara_suratKeluar = None
            if request.form.get('tanggal_acara_suratKeluar'):
                try:
                    tanggal_acara_suratKeluar = datetime.strptime(request.form['tanggal_acara_suratKeluar'], '%Y-%m-%d').date()
                except ValueError:
                    tanggal_acara_suratKeluar = None

            new_surat_keluar = SuratKeluar(
                tanggal_suratKeluar=datetime.strptime(tanggal_suratKeluar, '%Y-%m-%d'),
                pengirim_suratKeluar=pengirim_suratKeluar,
                penerima_suratKeluar=penerima_suratKeluar,
                nomor_suratKeluar=nomor_suratKeluar,
                isi_suratKeluar=isi_suratKeluar,
                acara_suratKeluar=acara_suratKeluar,
                tempat_suratKeluar=tempat_suratKeluar,
                tanggal_acara_suratKeluar=tanggal_acara_suratKeluar,
                jam_suratKeluar=jam_suratKeluar,
                status_suratKeluar='pending'  # Set default status
            )
            db.session.add(new_surat_keluar)
            db.session.commit()
            flash('Surat Keluar has been added successfully!', 'success')
            return redirect(url_for('show_surat_keluar'))
        except Exception as e:
            db.session.rollback()
            flash(f'Error adding Surat Keluar: {str(e)}', 'danger')
            return render_template('home/input_surat_keluar.html')

    return render_template('home/input_surat_keluar.html')

@main_bp.route('/edit_surat_keluar/<int:id>', methods=['GET', 'POST'])
@login_required
def edit_surat_keluar(id):
    if not current_user.is_admin:
        flash('You do not have permission to access this page.', 'error')
        return redirect(url_for('main.index'))

    entry = SuratKeluar.query.get_or_404(id)
    if request.method == 'POST':
        try:
            # Update fields
            entry.tanggal_suratKeluar = datetime.strptime(request.form['tanggal_suratKeluar'], '%Y-%m-%d')
            entry.pengirim_suratKeluar = request.form['pengirim_suratKeluar']
            entry.penerima_suratKeluar = request.form['penerima_suratKeluar']
            entry.nomor_suratKeluar = request.form['nomor_suratKeluar']
            entry.isi_suratKeluar = request.form['isi_suratKeluar']
            
            # Update field acara (opsional)
            entry.acara_suratKeluar = request.form.get('acara_suratKeluar', '')
            entry.tempat_suratKeluar = request.form.get('tempat_suratKeluar', '')
            entry.jam_suratKeluar = request.form.get('jam_suratKeluar', '')
            
            # Update tanggal acara (opsional)
            if request.form.get('tanggal_acara_suratKeluar'):
                try:
                    entry.tanggal_acara_suratKeluar = datetime.strptime(request.form['tanggal_acara_suratKeluar'], '%Y-%m-%d').date()
                except ValueError:
                    entry.tanggal_acara_suratKeluar = None
            else:
                entry.tanggal_acara_suratKeluar = None
            
            # Calculate OCR accuracy
            from config.ocr_utils import calculate_overall_ocr_accuracy
            entry.ocr_accuracy_suratKeluar = calculate_overall_ocr_accuracy(entry, 'suratKeluar')
            
            db.session.commit()
            flash('Surat Keluar has been updated successfully!', 'success')
            return redirect(url_for('show_surat_keluar'))
        except Exception as e:
            db.session.rollback()
            flash(f'Error updating Surat Keluar: {str(e)}', 'error')
            return render_template('home/edit_surat_keluar.html', entry=entry)
    
    return render_template('home/edit_surat_keluar.html', entry=entry)

@main_bp.route('/delete_surat_keluar/<int:id>', methods=['POST'])
@login_required
def delete_surat_keluar(id):
    entry = SuratKeluar.query.get_or_404(id)
    db.session.delete(entry)
    db.session.commit()
    flash('Surat Keluar has been deleted successfully!', 'success')
    return redirect(url_for('show_surat_keluar'))

@main_bp.route('/edit_surat_masuk/<int:id_suratMasuk>', methods=['GET', 'POST'])
@login_required
def edit_surat_masuk(id_suratMasuk):
    surat_masuk = SuratMasuk.query.get_or_404(id_suratMasuk)
    
    if request.method == 'POST':
        try:
            # Update fields from form
            surat_masuk.nomor_suratMasuk = request.form.get('nomor_suratMasuk')
            surat_masuk.pengirim_suratMasuk = request.form.get('pengirim_suratMasuk')
            surat_masuk.penerima_suratMasuk = request.form.get('penerima_suratMasuk')
            surat_masuk.isi_suratMasuk = request.form.get('isi_suratMasuk')
            
            # Calculate OCR accuracy
            from config.ocr_utils import calculate_overall_ocr_accuracy
            surat_masuk.ocr_accuracy_suratMasuk = calculate_overall_ocr_accuracy(surat_masuk, 'suratMasuk')
            
            # Handle file upload if present
            if 'gambar_suratMasuk' in request.files:
                file = request.files['gambar_suratMasuk']
                if file and file.filename != '':
                    # Save file logic here
                    pass
            
            db.session.commit()
            flash('Surat masuk berhasil diperbarui.', 'success')
            return redirect(url_for('show_surat_masuk'))
        except Exception as e:
            db.session.rollback()
            flash(f'Gagal memperbarui surat masuk: {str(e)}', 'error')
    
    return render_template('home/edit_surat_masuk.html', surat=surat_masuk)

@main_bp.route('/delete_surat_masuk/<int:id_suratMasuk>', methods=['POST'])
@login_required
def delete_surat_masuk(id_suratMasuk):
    surat_masuk = SuratMasuk.query.get_or_404(id_suratMasuk)
    
    try:
        db.session.delete(surat_masuk)
        db.session.commit()
        flash('Surat masuk berhasil dihapus.', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Gagal menghapus surat masuk: {str(e)}', 'error')
    
    return redirect(url_for('show_surat_masuk'))

from sqlalchemy import or_

@main_bp.route("/laporan-statistik")
@login_required
@role_required('admin', 'pimpinan')
def laporan_statistik():
    semua_surat_keluar = SuratKeluar.query.all()
    semua_surat_masuk = SuratMasuk.query.all()

    total_masuk = len(semua_surat_masuk)
    total_keluar = len(semua_surat_keluar)

    berhasil_masuk = len([s for s in semua_surat_masuk if 'Not found' not in s.isi_suratMasuk])
    berhasil_keluar = len([s for s in semua_surat_keluar if 'Not found' not in s.isi_suratKeluar])

    persentase_berhasil_masuk = round((berhasil_masuk / total_masuk * 100), 2) if total_masuk else 0
    persentase_berhasil_keluar = round((berhasil_keluar / total_keluar * 100), 2) if total_keluar else 0

    field_stats_masuk = {
        'nomor_suratMasuk': 0,
        'pengirim_suratMasuk': 0,
        'penerima_suratMasuk': 0,
        'isi_suratMasuk': 0,
    }

    for surat in semua_surat_masuk:
        if surat.initial_nomor_suratMasuk == 'Not found':
            field_stats_masuk['nomor_suratMasuk'] += 1
        if surat.initial_pengirim_suratMasuk == 'Not found':
            field_stats_masuk['pengirim_suratMasuk'] += 1
        if surat.initial_penerima_suratMasuk == 'Not found':
            field_stats_masuk['penerima_suratMasuk'] += 1
        if surat.initial_isi_suratMasuk == 'Not found':
            field_stats_masuk['isi_suratMasuk'] += 1

    field_stats_keluar = {
        'nomor_suratKeluar': 0,
        'pengirim_suratKeluar': 0,
        'penerima_suratKeluar': 0,
        'isi_suratKeluar': 0,
    }

    for surat in semua_surat_keluar:
        if surat.initial_nomor_suratKeluar == 'Not found':
            field_stats_keluar['nomor_suratKeluar'] += 1
        if surat.initial_pengirim_suratKeluar == 'Not found':
            field_stats_keluar['pengirim_suratKeluar'] += 1
        if surat.initial_penerima_suratKeluar == 'Not found':
            field_stats_keluar['penerima_suratKeluar'] += 1
        if surat.initial_isi_suratKeluar == 'Not found':
            field_stats_keluar['isi_suratKeluar'] += 1

    full_letter_components_masuk = ['initial_nomor_suratMasuk']
    full_letter_components_keluar = ['nomor_suratKeluar']

    full_letter_not_found_masuk = sum(
        sum(1 for surat in semua_surat_masuk if getattr(surat, field) == 'Not found')
        for field in full_letter_components_masuk
    )
    full_letter_not_found_keluar = sum(
        sum(1 for surat in semua_surat_keluar if getattr(surat, field) == 'Not found')
        for field in full_letter_components_keluar
    )

    field_stats_masuk['full_letter_number_not_found'] = full_letter_not_found_masuk
    field_stats_keluar['full_letter_number_not_found'] = full_letter_not_found_keluar

    akurasi_masuk = [s.ocr_accuracy_suratMasuk for s in semua_surat_masuk if s.ocr_accuracy_suratMasuk is not None]
    akurasi_keluar = [s.ocr_accuracy_suratKeluar for s in semua_surat_keluar if s.ocr_accuracy_suratKeluar is not None]

    rata2_akurasi_masuk = round(sum(akurasi_masuk) / len(akurasi_masuk), 2) if akurasi_masuk else 0
    rata2_akurasi_keluar = round(sum(akurasi_keluar) / len(akurasi_keluar), 2) if akurasi_keluar else 0

    # Calculate accuracy distribution
    akurasi_tinggi_masuk = len([a for a in akurasi_masuk if a >= 90])
    akurasi_sedang_masuk = len([a for a in akurasi_masuk if 70 <= a < 90])
    akurasi_rendah_masuk = len([a for a in akurasi_masuk if a < 70])

    akurasi_tinggi_keluar = len([a for a in akurasi_keluar if a >= 90])
    akurasi_sedang_keluar = len([a for a in akurasi_keluar if 70 <= a < 90])
    akurasi_rendah_keluar = len([a for a in akurasi_keluar if a < 70])

    gagal_ekstraksi_suratKeluar = [
        s for s in semua_surat_keluar if s.ocr_accuracy_suratKeluar and s.ocr_accuracy_suratKeluar < 100
    ]

    gagal_ekstraksi_suratMasuk = SuratMasuk.query.filter(
        or_(
            SuratMasuk.initial_nomor_suratMasuk == 'Not found',
            SuratMasuk.initial_pengirim_suratMasuk == 'Not found',
            SuratMasuk.initial_penerima_suratMasuk == 'Not found',
            SuratMasuk.initial_isi_suratMasuk == 'Not found'
        )
    ).all()

    keyword = request.args.get('keyword', '')
    surat_keyword = []
    if keyword:
        surat_keyword = SuratKeluar.query.filter(SuratKeluar.isi_suratKeluar.ilike(f'%{keyword}%')).all()

    return render_template(
        "home/laporan_statistik.html",
            persentase_berhasil_masuk=persentase_berhasil_masuk,
            persentase_berhasil_keluar=persentase_berhasil_keluar,
            gagal_ekstraksi_suratMasuk=gagal_ekstraksi_suratMasuk,
            gagal_ekstraksi_suratKeluar=gagal_ekstraksi_suratKeluar,
            keyword=keyword,
            surat_keyword=surat_keyword,
            rata2_akurasi_masuk=rata2_akurasi_masuk,
            rata2_akurasi_keluar=rata2_akurasi_keluar,
            field_stats_keluar=field_stats_keluar,
            field_stats_masuk=field_stats_masuk,
            total_masuk=total_masuk,
            total_keluar=total_keluar,
            akurasi_tinggi_masuk=akurasi_tinggi_masuk,
            akurasi_sedang_masuk=akurasi_sedang_masuk,
            akurasi_rendah_masuk=akurasi_rendah_masuk,
            akurasi_tinggi_keluar=akurasi_tinggi_keluar,
            akurasi_sedang_keluar=akurasi_sedang_keluar,
            akurasi_rendah_keluar=akurasi_rendah_keluar
    )

@main_bp.route('/edit-user/<int:user_id>', methods=['GET', 'POST'])
@login_required
def edit_user(user_id):
    # Check if current user is admin or editing their own profile
    if not current_user.is_admin and current_user.id != user_id:
        flash('You do not have permission to edit this user.', 'error')
        return redirect(url_for('main.index'))
    
    user = User.query.get_or_404(user_id)

    if request.method == 'POST':
        user.email = request.form['email']
        new_password = request.form['password']
        if new_password:
            user.password = generate_password_hash(new_password)
        db.session.commit()
        flash('User updated successfully!')
        return redirect(url_for('main.index'))

    return render_template('auth/edit_users.html', users=[user], single_user=True)

@main_bp.route('/edit-user', methods=['GET', 'POST'])
@login_required
def edit_user_view():
    try:
        # Check if current user is admin
        if not current_user.is_admin:
            flash('You do not have permission to edit users.', 'error')
            return redirect(url_for('main.index'))
        
        users = User.query.all()

        if request.method == 'POST':
            user_id = request.form.get('user_id')
            email = request.form.get('email')
            password = request.form.get('password')
            role = request.form.get('role')
            is_approved = 'is_approved' in request.form

            if not user_id:
                flash('Please select a user to edit.', 'error')
                return redirect(url_for('main.edit_user_view'))

            user = User.query.get(user_id)
            if user:
                user.email = email
                user.role = role
                user.is_approved = is_approved
                
                # Set is_admin flag based on role
                user.is_admin = (role == 'admin')
                
                if password:
                    user.set_password(password)
                
                db.session.commit()
                current_app.logger.info(f"User {user.email} updated by {current_user.email}")
                flash('User updated successfully!', 'success')
            else:
                flash('User not found.', 'error')

            return redirect(url_for('main.edit_user_view'))

        return render_template('auth/edit_users.html', users=users, single_user=False)
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error in edit_user_view: {str(e)}")
        flash(f'Error updating user: {str(e)}', 'error')
        return redirect(url_for('main.edit_user_view'))

@main_bp.route('/get-user-data/<int:user_id>')
@login_required
def get_user_data(user_id):
    user = User.query.get(user_id)
    if user:
        return jsonify({
            "success": True,
            "email": user.email,
            "role": user.role,
            "is_approved": user.is_approved
        })
    else:
        return jsonify({"success": False}), 404

@main_bp.route('/approve-user/<int:user_id>', methods=['POST'])
@login_required
def approve_user(user_id):
    try:
        # Check if current user is admin
        if not current_user.is_admin:
            return jsonify({"success": False, "message": "You do not have permission to approve users."}), 403
        
        user = User.query.get_or_404(user_id)
        user.is_approved = True
        db.session.commit()
        
        current_app.logger.info(f"User {user.email} approved by {current_user.email}")
        return jsonify({"success": True, "message": f"User {user.email} has been approved."})
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error approving user {user_id}: {str(e)}")
        return jsonify({"success": False, "message": f"Error approving user: {str(e)}"}), 500

@main_bp.route('/delete-user/<int:user_id>', methods=['POST'])
@login_required
def delete_user(user_id):
    try:
        # Check if current user is admin
        if not current_user.is_admin:
            flash('You do not have permission to delete users.', 'error')
            return redirect(url_for('main.edit_user_view'))
        
        # Prevent deleting yourself
        if user_id == current_user.id:
            flash('You cannot delete your own account.', 'error')
            return redirect(url_for('main.edit_user_view'))
        
        user = User.query.get_or_404(user_id)
        user_email = user.email
        db.session.delete(user)
        db.session.commit()
        
        current_app.logger.info(f"User {user_email} deleted by {current_user.email}")
        flash(f'User {user_email} has been deleted.', 'success')
        return redirect(url_for('main.edit_user_view'))
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error deleting user {user_id}: {str(e)}")
        flash(f'Error deleting user: {str(e)}', 'error')
        return redirect(url_for('main.edit_user_view'))

@main_bp.route('/chart-data')
@login_required
def chart_data():

    masuk = db.session.query(
        func.date(SuratMasuk.tanggal_suratMasuk).label('tanggal'),
        func.count().label('jumlah')
    ).group_by(func.date(SuratMasuk.tanggal_suratMasuk)).all()

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
        "surat_masuk": [data_masuk_dict.get(t, 0) for t in tanggal_sorted],
        "surat_keluar": [data_keluar_dict.get(t, 0) for t in tanggal_sorted],
    }

    return jsonify(data)

@main_bp.route('/generate-cuti', methods=['GET', 'POST'])
@login_required
def generate_cuti():  # Keep the function name as generate_cuti for url_for to work
    from config.forms import CutiForm
    form = CutiForm()
    
    if request.method == 'GET':
        return render_template('home/generate_cuti_form.html', form=form)

    if not form.validate_on_submit():
        for field, errors in form.errors.items():
            for error in errors:
                flash(f"{getattr(form, field).label.text}: {error}", "error")
                if 'csrf_token' in field:
                    flash("CSRF token validation failed. Please refresh the page and try again.", "error")
        return render_template('home/generate_cuti_form.html', form=form)

    def romawi_bulan(bulan):
        romawi = {
            1: 'I', 2: 'II', 3: 'III', 4: 'IV', 5: 'V', 6: 'VI',
            7: 'VII', 8: 'VIII', 9: 'IX', 10: 'X', 11: 'XI', 12: 'XII'
        }
        return romawi.get(bulan, '')

    try:
        # Ambil semua data dari form
        context = {
            "nama": form.nama.data,
            "nip": form.nip.data,
            "jabatan": form.jabatan.data,
            "gol_ruang": form.gol_ruang.data,
            "unit_kerja": form.unit_kerja.data,
            "masa_kerja": form.masa_kerja.data,
            "c_tahun": "✓" if form.jenis_cuti.data == "c_tahun" else "",
            "c_besar": "✓" if form.jenis_cuti.data == "c_besar" else "",
            "c_sakit": "✓" if form.jenis_cuti.data == "c_sakit" else "",
            "c_lahir": "✓" if form.jenis_cuti.data == "c_lahir" else "",
            "c_penting": "✓" if form.jenis_cuti.data == "c_penting" else "",
            "c_luarnegara": "✓" if form.jenis_cuti.data == "c_luarnegara" else "",
            "alasan_cuti": form.alasan_cuti.data,
            "lama_cuti": form.lama_cuti.data,
            "tanggal_cuti": form.tanggal_cuti.data.strftime("%Y-%m-%d"),
            "sampai_cuti": form.sampai_cuti.data.strftime("%Y-%m-%d"),
            "telp": form.telp.data,
            "alamat": form.alamat.data,
            "no_suratmasuk": form.no_suratmasuk.data,
        }

        try:
            tgl_obj = form.tgl_ajuan_cuti.data
            context["tgl_ajuan_cuti"] = tgl_obj.strftime("%d")
            context["bulan_ajuan_cuti"] = romawi_bulan(tgl_obj.month)
            context["tahun_ajuan_cuti"] = str(tgl_obj.year)
            context["tgl_lengkap_ajuan_cuti"] = tgl_obj.strftime("%d %B %Y")
        except Exception:
            flash("Invalid date format for tgl_ajuan_cuti", "error")
            return render_template('home/generate_cuti_form.html', form=form)

        # Get absolute path to template
        template_path = os.path.join(current_app.root_path, 'static/assets/templates/form_permintaan_cuti.docx')
        if not os.path.exists(template_path):
            flash("Template file not found. Please contact administrator.", "error")
            return render_template('home/generate_cuti_form.html', form=form)

        document = MailMerge(template_path)
        document.merge(**context)

        temp_dir = tempfile.gettempdir()
        docx_filename = f"Cuti_{context['nama'].replace(' ', '_')}_{datetime.now().strftime('%Y%m%d%H%M%S')}.docx"
        docx_path = os.path.join(temp_dir, docx_filename)
        document.write(docx_path)
        document.close()

        # Try different LibreOffice paths based on OS
        libreoffice_paths = [
            "/usr/bin/soffice",  # Linux
            "/usr/local/bin/soffice",  # Linux/macOS alternative
            "/Applications/LibreOffice.app/Contents/MacOS/soffice",  # macOS
            "C:\\Program Files\\LibreOffice\\program\\soffice.exe",  # Windows
            "/opt/homebrew/bin/soffice",  # macOS Homebrew
        ]

        conversion_successful = False
        conversion_error = None
        for libreoffice_path in libreoffice_paths:
            if os.path.exists(libreoffice_path):
                try:
                    subprocess.run([
                        libreoffice_path,
                        "--headless", "--convert-to", "pdf",
                        "--outdir", temp_dir,
                        docx_path
                    ], check=True, capture_output=True)
                    conversion_successful = True
                    break
                except subprocess.CalledProcessError as e:
                    conversion_error = f"LibreOffice error: {e.stderr.decode()}"
                    continue
                except Exception as e:
                    conversion_error = str(e)
                    continue

        if not conversion_successful:
            if os.path.exists(docx_path):
                os.remove(docx_path)
            flash(f"Could not convert document to PDF. Please ensure LibreOffice is installed. Error: {conversion_error}", "error")
            return render_template('home/generate_cuti_form.html', form=form)

        if os.path.exists(docx_path):
            os.remove(docx_path)

        pdf_filename = docx_filename.replace('.docx', '.pdf')
        pdf_path = os.path.join(temp_dir, pdf_filename)
        
        if not os.path.exists(pdf_path):
            flash("PDF file was not generated. Please try again.", "error")
            return render_template('home/generate_cuti_form.html', form=form)

        return send_file(pdf_path, as_attachment=True, download_name=pdf_filename)

    except Exception as e:
        flash(f"An error occurred: {str(e)}", "error")
        return render_template('home/generate_cuti_form.html', form=form)

@main_bp.route('/surat_masuk')
@login_required
def surat_masuk():
    # Ambil semua surat masuk dari database, termasuk field full_letter_number
    daftar_surat = SuratMasuk.query.order_by(SuratMasuk.tanggal_suratMasuk.desc()).all()
    
    # Kirim data ke template
    return render_template('home/surat_masuk.html', daftar_surat=daftar_surat)


@main_bp.route('/pegawai', methods=['GET', 'POST'])
@login_required
@role_required('admin', 'pimpinan')
def pegawai():
    if request.method == 'POST':
        try:
            # Log request data for debugging
            current_app.logger.info(f"=== ADD PEGAWAI REQUEST ===")
            current_app.logger.info(f"User: {current_user.email}")
            current_app.logger.info(f"Form data: {dict(request.form)}")
            current_app.logger.info(f"Headers: {dict(request.headers)}")
            current_app.logger.info(f"Method: {request.method}")
            current_app.logger.info(f"URL: {request.url}")
            
            # Check if CSRF token exists in form
            csrf_token_in_form = request.form.get('csrf_token')
            current_app.logger.info(f"CSRF token in form: {'Yes' if csrf_token_in_form else 'No'}")
            
            # Check if CSRF token exists in headers
            csrf_token_in_headers = request.headers.get('X-CSRFToken') or request.headers.get('X-CSRF-Token')
            current_app.logger.info(f"CSRF token in headers: {'Yes' if csrf_token_in_headers else 'No'}")
            
            # Validate CSRF token
            if not csrf_token_in_form:
                current_app.logger.error("CSRF token missing in pegawai")
                current_app.logger.error(f"Available form fields: {list(request.form.keys())}")
                return jsonify({"success": False, "message": "Token keamanan tidak ditemukan. Silakan refresh halaman."}), 400
            
            # Validate required fields
            required_fields = ['nama', 'tanggal_lahir', 'nip', 'golongan', 'jabatan', 'agama', 'jenis_kelamin', 'riwayat_pendidikan', 'riwayat_pekerjaan', 'nomor_telpon']
            missing_fields = []
            
            for field in required_fields:
                if not request.form.get(field):
                    missing_fields.append(field)
            
            if missing_fields:
                error_msg = f"Field yang diperlukan tidak ditemukan: {', '.join(missing_fields)}"
                current_app.logger.error(error_msg)
                return jsonify({"success": False, "message": error_msg}), 400
            
            # Check if NIP already exists
            existing_pegawai = Pegawai.query.filter_by(nip=request.form['nip']).first()
            if existing_pegawai:
                return jsonify({"success": False, "message": f'NIP {request.form["nip"]} sudah terdaftar!'}), 400
            
            # Parse tanggal_lahir
            try:
                tanggal_lahir = datetime.strptime(request.form['tanggal_lahir'], '%Y-%m-%d')
                current_app.logger.info(f"Tanggal lahir parsed successfully: {tanggal_lahir}")
            except ValueError as e:
                current_app.logger.error(f"Invalid date format: {request.form['tanggal_lahir']}")
                return jsonify({"success": False, "message": "Format tanggal lahir tidak valid!"}), 400
            
            # Create new pegawai
            try:
                new_pegawai = Pegawai(
                    nama=request.form['nama'].strip(),
                    tanggal_lahir=tanggal_lahir,
                    nip=request.form['nip'].strip(),
                    golongan=request.form['golongan'].strip(),
                    jabatan=request.form['jabatan'].strip(),
                    agama=request.form['agama'].strip(),
                    jenis_kelamin=request.form['jenis_kelamin'].strip(),
                    nomor_telpon=request.form['nomor_telpon'].strip(),
                    riwayat_pendidikan=request.form['riwayat_pendidikan'].strip(),
                    riwayat_pekerjaan=request.form['riwayat_pekerjaan'].strip()
                )
                
                current_app.logger.info(f"Pegawai object created: {new_pegawai.nama}")
                
                db.session.add(new_pegawai)
                db.session.commit()
                
                current_app.logger.info(f"Pegawai berhasil ditambahkan: {new_pegawai.nama} (NIP: {new_pegawai.nip})")
                return jsonify({"success": True, "message": f"Pegawai {new_pegawai.nama} berhasil ditambahkan!"})
                
            except Exception as e:
                db.session.rollback()
                current_app.logger.error(f"Error creating pegawai object: {str(e)}")
                return jsonify({"success": False, "message": f"Gagal membuat data pegawai: {str(e)}"}), 500
            
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Unexpected error adding pegawai: {str(e)}", exc_info=True)
            return jsonify({"success": False, "message": f"Gagal menambahkan pegawai: {str(e)}"}), 500

    return render_template('home/pegawai.html')

@main_bp.route('/pegawai/list', methods=['GET'])
@login_required
@role_required('admin', 'pimpinan')
def pegawai_list():
    daftar_pegawai = Pegawai.query.all()
    return render_template('home/list_pegawai.html', daftar_pegawai=daftar_pegawai)

@main_bp.route('/pegawai/edit/<int:id>', methods=['POST'])
@login_required
@role_required('admin', 'pimpinan')
def edit_pegawai(id):
    try:
        # Log form data for debugging
        current_app.logger.info(f"=== EDIT PEGAWAI REQUEST ===")
        current_app.logger.info(f"User: {current_user.email}")
        current_app.logger.info(f"Pegawai ID: {id}")
        current_app.logger.info(f"Form data: {dict(request.form)}")
        current_app.logger.info(f"Headers: {dict(request.headers)}")
        current_app.logger.info(f"Method: {request.method}")
        current_app.logger.info(f"URL: {request.url}")
        
        # Check if CSRF token exists in form
        csrf_token_in_form = request.form.get('csrf_token')
        current_app.logger.info(f"CSRF token in form: {'Yes' if csrf_token_in_form else 'No'}")
        
        # Check if CSRF token exists in headers
        csrf_token_in_headers = request.headers.get('X-CSRFToken') or request.headers.get('X-CSRF-Token')
        current_app.logger.info(f"CSRF token in headers: {'Yes' if csrf_token_in_headers else 'No'}")
        
        # Validate CSRF token
        if not csrf_token_in_form:
            current_app.logger.error("CSRF token missing in edit_pegawai")
            current_app.logger.error(f"Available form fields: {list(request.form.keys())}")
            return jsonify({"success": False, "message": "Token keamanan tidak ditemukan. Silakan refresh halaman."}), 400

        # Validate required fields
        required_fields = ['nama', 'tanggal_lahir', 'nip', 'golongan', 'jabatan', 'agama', 'jenis_kelamin', 'riwayat_pendidikan', 'riwayat_pekerjaan', 'nomor_telpon']
        missing_fields = []
        
        for field in required_fields:
            if not request.form.get(field):
                missing_fields.append(field)
        
        if missing_fields:
            error_msg = f"Field yang diperlukan tidak ditemukan: {', '.join(missing_fields)}"
            current_app.logger.error(error_msg)
            return jsonify({"success": False, "message": error_msg}), 400
        
        # Try to get pegawai
        try:
            pegawai = Pegawai.query.get_or_404(id)
            current_app.logger.info(f"Pegawai found: {pegawai.nama} (NIP: {pegawai.nip})")
        except Exception as e:
            current_app.logger.error(f"Error getting pegawai {id}: {str(e)}")
            return jsonify({"success": False, "message": f"Pegawai dengan ID {id} tidak ditemukan."}), 404
        
        # Check if NIP already exists (excluding current pegawai)
        existing_pegawai = Pegawai.query.filter_by(nip=request.form['nip']).filter(Pegawai.id != id).first()
        if existing_pegawai:
            return jsonify({"success": False, "message": f'NIP {request.form["nip"]} sudah terdaftar!'}), 400
        
        # Parse tanggal_lahir
        try:
            tanggal_lahir = datetime.strptime(request.form['tanggal_lahir'], '%Y-%m-%d')
            current_app.logger.info(f"Tanggal lahir parsed successfully: {tanggal_lahir}")
        except ValueError as e:
            current_app.logger.error(f"Invalid date format: {request.form['tanggal_lahir']}")
            return jsonify({"success": False, "message": "Format tanggal lahir tidak valid!"}), 400
        
        # Try to update pegawai data
        try:
            pegawai.nama = request.form['nama'].strip()
            pegawai.tanggal_lahir = tanggal_lahir
            pegawai.nip = request.form['nip'].strip()
            pegawai.golongan = request.form['golongan'].strip()
            pegawai.jabatan = request.form['jabatan'].strip()
            pegawai.agama = request.form['agama'].strip()
            pegawai.jenis_kelamin = request.form['jenis_kelamin'].strip()
            pegawai.nomor_telpon = request.form['nomor_telpon'].strip()
            pegawai.riwayat_pendidikan = request.form['riwayat_pendidikan'].strip()
            pegawai.riwayat_pekerjaan = request.form['riwayat_pekerjaan'].strip()
            
            current_app.logger.info(f"Pegawai data updated in memory")
            
            db.session.commit()
            
            current_app.logger.info(f"Pegawai berhasil diupdate: {pegawai.nama} (NIP: {pegawai.nip})")
            return jsonify({"success": True, "message": f"Data pegawai {pegawai.nama} berhasil diupdate!"})
            
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Error updating pegawai in database: {str(e)}")
            return jsonify({"success": False, "message": f"Gagal mengupdate pegawai di database: {str(e)}"}), 500
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Unexpected error updating pegawai {id}: {str(e)}", exc_info=True)
        return jsonify({"success": False, "message": f"Gagal mengupdate pegawai: {str(e)}"}), 500

@main_bp.route('/pegawai/hapus/<int:id>', methods=['POST'])
@login_required
@role_required('admin')
def hapus_pegawai(id):
    try:
        # Log request data for debugging
        current_app.logger.info(f"=== DELETE PEGAWAI REQUEST ===")
        current_app.logger.info(f"User: {current_user.email}")
        current_app.logger.info(f"Pegawai ID: {id}")
        current_app.logger.info(f"Form data: {dict(request.form)}")
        current_app.logger.info(f"Headers: {dict(request.headers)}")
        current_app.logger.info(f"Method: {request.method}")
        current_app.logger.info(f"URL: {request.url}")
        
        # Check if CSRF token exists in form
        csrf_token_in_form = request.form.get('csrf_token')
        current_app.logger.info(f"CSRF token in form: {'Yes' if csrf_token_in_form else 'No'}")
        
        # Check if CSRF token exists in headers
        csrf_token_in_headers = request.headers.get('X-CSRFToken') or request.headers.get('X-CSRF-Token')
        current_app.logger.info(f"CSRF token in headers: {'Yes' if csrf_token_in_headers else 'No'}")
        
        # Validate CSRF token
        if not csrf_token_in_form:
            current_app.logger.error("CSRF token missing in hapus_pegawai")
            current_app.logger.error(f"Available form fields: {list(request.form.keys())}")
            return jsonify({"success": False, "message": "Token keamanan tidak ditemukan. Silakan refresh halaman."}), 400
        
        # Try to get pegawai
        try:
            pegawai = Pegawai.query.get_or_404(id)
            current_app.logger.info(f"Pegawai found: {pegawai.nama} (NIP: {pegawai.nip})")
        except Exception as e:
            current_app.logger.error(f"Error getting pegawai {id}: {str(e)}")
            return jsonify({"success": False, "message": f"Pegawai dengan ID {id} tidak ditemukan."}), 404
        
        nama_pegawai = pegawai.nama
        nip_pegawai = pegawai.nip
        
        # Try to delete pegawai
        try:
            db.session.delete(pegawai)
            db.session.commit()
            current_app.logger.info(f"Pegawai berhasil dihapus: {nama_pegawai} (NIP: {nip_pegawai})")
            return jsonify({"success": True, "message": f"Pegawai {nama_pegawai} berhasil dihapus!"})
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Error deleting pegawai from database: {str(e)}")
            return jsonify({"success": False, "message": f"Gagal menghapus pegawai dari database: {str(e)}"}), 500
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Unexpected error deleting pegawai {id}: {str(e)}", exc_info=True)
        return jsonify({"success": False, "message": f"Gagal menghapus pegawai: {str(e)}"}), 500



@main_bp.route('/surat-keluar/list', methods=['GET'])
@login_required
@role_required('pimpinan', 'admin')
def surat_keluar_list():
    # Ambil parameter halaman dan jumlah item per halaman
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 10, type=int)
    
    # Hitung jumlah surat keluar pending
    pending_surat_keluar_count = SuratKeluar.query.filter_by(status_suratKeluar='pending').count()
    
    # Filter untuk status pending jika pimpinan
    if current_user.role == 'pimpinan':
        query = SuratKeluar.query.filter_by(status_suratKeluar='pending')
    else:
        query = SuratKeluar.query
    
    # Lakukan paginasi
    pagination = query.order_by(SuratKeluar.created_at.desc()).paginate(page=page, per_page=per_page)
    
    # Konversi ke list dictionary untuk serialisasi
    surat_keluar_list = [{
        'id_suratKeluar': surat.id_suratKeluar,
        'nomor_surat': surat.nomor_suratKeluar,
        'pengirim': surat.pengirim_suratKeluar,
        'penerima': surat.penerima_suratKeluar,
        'tanggal': surat.tanggal_suratKeluar.strftime('%Y-%m-%d'),
        'status': surat.status_suratKeluar
    } for surat in pagination.items]
    
    return render_template('home/list_surat_keluar.html', 
                           surat_keluar_list=surat_keluar_list, 
                           pagination=pagination,
                           pending_surat_keluar_count=pending_surat_keluar_count)



@main_bp.route('/surat-keluar/approve/<int:surat_id>', methods=['POST'])
@login_required
@role_required('pimpinan')
def approve_surat_keluar(surat_id):
    try:
        surat = SuratKeluar.query.get_or_404(surat_id)
        surat.status_suratKeluar = 'approved'
        
        db.session.commit()
        current_app.logger.info(f"Surat keluar {surat_id} approved by {current_user.email}")
        return jsonify({"success": True, "message": "Surat keluar berhasil disetujui"})
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error approving surat keluar {surat_id}: {str(e)}")
        return jsonify({"success": False, "error": str(e)}), 500

@main_bp.route('/surat-keluar/reject/<int:surat_id>', methods=['POST'])
@login_required
@role_required('pimpinan')
def reject_surat_keluar(surat_id):
    try:
        surat = SuratKeluar.query.get_or_404(surat_id)
        surat.status_suratKeluar = 'rejected'
        
        db.session.commit()
        current_app.logger.info(f"Surat keluar {surat_id} rejected by {current_user.email}")
        return jsonify({"success": True, "message": "Surat keluar berhasil ditolak"})
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error rejecting surat keluar {surat_id}: {str(e)}")
        return jsonify({"success": False, "error": str(e)}), 500



@main_bp.route('/list-pending-surat-keluar')
@login_required
@role_required('pimpinan')
def list_pending_surat_keluar():
    try:
        # Ambil daftar surat keluar yang masih pending
        pending_surat_keluar = SuratKeluar.query.filter_by(status_suratKeluar='pending').order_by(SuratKeluar.created_at.desc()).all()
        current_app.logger.info(f"Showing {len(pending_surat_keluar)} pending surat keluar for user {current_user.email}")
        return render_template('home/list_pending_surat_keluar.html', pending_surat_keluar=pending_surat_keluar)
    except Exception as e:
        current_app.logger.error(f"Error in list_pending_surat_keluar: {str(e)}")
        flash('Terjadi kesalahan saat memuat daftar surat keluar pending.', 'error')
        return redirect(url_for('main.index'))



@main_bp.route('/surat-keluar/detail/<int:id>')
@login_required
@role_required('pimpinan')
def detail_surat_keluar(id):
    surat_keluar = SuratKeluar.query.get_or_404(id)
    return render_template('home/detail_surat_keluar.html', surat=surat_keluar)



@main_bp.route('/update-ocr-accuracy/<int:id>', methods=['POST'])
@login_required
@role_required('admin', 'pimpinan')
def update_ocr_accuracy(id):
    """
    Update OCR accuracy for a specific document
    """
    try:
        surat_type = request.form.get('type')  # 'masuk' or 'keluar'
        
        if surat_type == 'masuk':
            surat = SuratMasuk.query.get_or_404(id)
            from config.ocr_utils import calculate_overall_ocr_accuracy
            surat.ocr_accuracy_suratMasuk = calculate_overall_ocr_accuracy(surat, 'suratMasuk')
        elif surat_type == 'keluar':
            surat = SuratKeluar.query.get_or_404(id)
            from config.ocr_utils import calculate_overall_ocr_accuracy
            surat.ocr_accuracy_suratKeluar = calculate_overall_ocr_accuracy(surat, 'suratKeluar')
        else:
            return jsonify({"success": False, "error": "Invalid surat type"})
        
        db.session.commit()
        return jsonify({"success": True, "accuracy": getattr(surat, f'ocr_accuracy_{surat_type}', 0)})
    except Exception as e:
        db.session.rollback()
        return jsonify({"success": False, "error": str(e)})

@main_bp.route('/surat-keluar/download/<int:id>')
@login_required
@role_required('pimpinan')
def download_surat_keluar(id):
    surat_keluar = SuratKeluar.query.get_or_404(id)
    
    if not surat_keluar.file_suratKeluar:
        flash('Dokumen tidak tersedia.', 'error')
        return redirect(url_for('detail_surat_keluar', id=id))
    
    try:
        return send_file(
            surat_keluar.file_suratKeluar, 
            as_attachment=True, 
            download_name=f"Surat_Keluar_{surat_keluar.nomor_suratKeluar}.pdf"
        )
    except Exception as e:
        flash('Gagal mengunduh dokumen.', 'error')
        return redirect(url_for('detail_surat_keluar', id=id))

@main_bp.route('/surat-keluar/image/<int:id>')
@login_required
@role_required('pimpinan')
def view_surat_keluar_image(id):
    """Endpoint untuk menampilkan gambar surat keluar"""
    try:
        surat = SuratKeluar.query.get_or_404(id)
        if surat.gambar_suratKeluar:
            return send_file(
                io.BytesIO(surat.gambar_suratKeluar),
                mimetype='image/jpeg',
                as_attachment=False
            )
        else:
            return jsonify({'error': 'Gambar tidak ditemukan'}), 404
    except Exception as e:
        current_app.logger.error(f"Error viewing surat keluar image {id}: {str(e)}")
        return jsonify({'error': 'Terjadi kesalahan saat memuat gambar'}), 500

@main_bp.route('/ocr-test', methods=['GET', 'POST'])
@login_required
def ocr_test():
    extracted_text = ""
    
    if request.method == 'POST':
        try:
            # Get uploaded file
            if 'image' not in request.files:
                return render_template('home/ocr_test.html', extracted_text=extracted_text, has_error=True, has_success=False)
            
            file = request.files['image']
            if file.filename == '':
                return render_template('home/ocr_test.html', extracted_text=extracted_text, has_error=True, has_success=False)
            
            # Check file type
            allowed_extensions = {'png', 'jpg', 'jpeg', 'webp'}
            if not file.filename or '.' not in file.filename or file.filename.rsplit('.', 1)[1].lower() not in allowed_extensions:
                return render_template('home/ocr_test.html', extracted_text=extracted_text, has_error=True, has_success=False)
            
            # Read image using PIL instead of cv2
            from PIL import Image
            import io
            
            # Convert file to image using PIL
            image = Image.open(file.stream)
            
            # Extract text using pytesseract
            import pytesseract
            try:
                extracted_text = pytesseract.image_to_string(image, lang='ind')
                if not extracted_text.strip():
                    extracted_text = "Tidak ada teks yang dapat diekstrak dari gambar ini."
            except Exception as e:
                extracted_text = "Error saat memproses gambar."
                return render_template('home/ocr_test.html', extracted_text=extracted_text, has_error=True, has_success=False)
            
            # Don't use flash message, we'll use toast instead
            return render_template('home/ocr_test.html', extracted_text=extracted_text, has_success=True, has_error=False)
            
        except Exception as e:
            return render_template('home/ocr_test.html', extracted_text=extracted_text, has_error=True, has_success=False)
    
    return render_template('home/ocr_test.html', extracted_text=extracted_text, has_error=False, has_success=False)

# OCR Cuti route removed - using blueprint instead

@main_bp.route('/favicon.ico')
def favicon():
    return send_from_directory(
        os.path.join(current_app.root_path, 'static/assets/images'),
        'favicon.ico',
        mimetype='image/vnd.microsoft.icon'
    )

@main_bp.route('/api/debug/surat/<int:surat_id>', methods=['GET'])
@login_required
@role_required('pimpinan')
def debug_surat_detail(surat_id):
    """Debug endpoint untuk memeriksa struktur data surat"""
    try:
        surat = SuratKeluar.query.get(surat_id)
        if not surat:
            return jsonify({
                'success': False,
                'message': f'Surat dengan ID {surat_id} tidak ditemukan'
            }), 404
        
        # Return raw surat data for debugging
        return jsonify({
            'success': True,
            'surat_id': surat_id,
            'raw_data': {
                'id_suratKeluar': surat.id_suratKeluar,
                'nomor_suratKeluar': surat.nomor_suratKeluar,
                'tanggal_suratKeluar': str(surat.tanggal_suratKeluar) if surat.tanggal_suratKeluar else None,
                'pengirim_suratKeluar': surat.pengirim_suratKeluar,
                'penerima_suratKeluar': surat.penerima_suratKeluar,
                'perihal_suratKeluar': surat.perihal_suratKeluar,
                'isi_suratKeluar': surat.isi_suratKeluar,
                'status_suratKeluar': surat.status_suratKeluar,
                'file_suratKeluar': str(surat.file_suratKeluar),
                'created_at': str(surat.created_at) if surat.created_at else None
            }
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e),
            'error_type': type(e).__name__
        }), 500