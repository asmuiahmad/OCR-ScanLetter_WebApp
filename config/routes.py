# 🔹 Standard Library Imports
import os
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
    flash, jsonify, session, Blueprint
)
from flask_login import (
    login_user, login_required, logout_user, current_user
)
from werkzeug.security import check_password_hash, generate_password_hash
from werkzeug.utils import secure_filename
from sqlalchemy import desc, asc, extract, func
from mailmerge import MailMerge
from docx import Document

# 🔹 Local Application Imports
from app import app
from config.extensions import db
from config.ocr import ocr_bp
from config.ocr_utils import hitung_field_not_found
from config.models import User, SuratMasuk, SuratKeluar, Pegawai
from config.forms import LoginForm, RegistrationForm

def role_required(*roles):
    def wrapper(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if current_user.role not in roles:
                flash('You do not have permission to access this page.', 'error')
                return redirect(url_for('index'))
            return f(*args, **kwargs)
        return decorated_function
    return wrapper

@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user and check_password_hash(user.password, form.password.data):
            if not user.is_approved:
                flash('Your account is pending approval by an administrator.', 'warning')
                return render_template('auth/login.html', form=form)
            
            user.last_login = datetime.utcnow()
            if user.login_count is None:
                user.login_count = 0
            user.login_count += 1
            db.session.commit()
            login_user(user)
            return redirect(url_for('index'))
        flash('Invalid email or password', 'error')
    return render_template('auth/login.html', form=form)

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

@app.route('/register', methods=['GET', 'POST'])
def register():
    form = RegistrationForm()
    if form.validate_on_submit():
        try:
            if form.email.data and form.password.data:
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
            else:
                flash('Email and password are required', 'error')
                return render_template('auth/register.html', form=form)
            db.session.add(new_user)
            db.session.commit()
            flash('Registration successful! Your account is pending approval by an administrator.', 'success')
            return redirect(url_for('login'))
        except Exception as e:
            db.session.rollback()
            flash(f'An error occurred during registration: {str(e)}', 'error')
    return render_template('auth/register.html', form=form)

@app.route('/')
@login_required
def index():
    today = datetime.today()
    year = today.year
    month = today.month
    days_in_month = monthrange(year, month)[1]

    chart_labels = list(range(1, days_in_month + 1))

    surat_masuk_per_day = {day: 0 for day in chart_labels}
    surat_keluar_per_day = {day: 0 for day in chart_labels}

    surat_masuk_records = SuratMasuk.query.filter(
        SuratMasuk.tanggal_suratMasuk >= datetime(year, month, 1),
        SuratMasuk.tanggal_suratMasuk < datetime(year, month, days_in_month) + timedelta(days=1)
    ).all()

    for surat in surat_masuk_records:
        if surat.tanggal_suratMasuk:
            day = surat.tanggal_suratMasuk.day
            surat_masuk_per_day[day] += 1

    surat_keluar_records = SuratKeluar.query.filter(
        SuratKeluar.tanggal_suratKeluar >= datetime(year, month, 1),
        SuratKeluar.tanggal_suratKeluar < datetime(year, month, days_in_month) + timedelta(days=1)
    ).all()

    for surat in surat_keluar_records:
        if surat.tanggal_suratKeluar:
            day = surat.tanggal_suratKeluar.day
            surat_keluar_per_day[day] += 1

    chart_data_masuk = [surat_masuk_per_day[day] for day in chart_labels]
    chart_data_keluar = [surat_keluar_per_day[day] for day in chart_labels]

    return render_template('home/index.html',
        suratMasuk_count=SuratMasuk.query.count(),
        suratKeluar_count=SuratKeluar.query.count(),
        suratMasuk_this_month = SuratMasuk.query.filter(SuratMasuk.created_at >= datetime(year, month, 1)).count(),
        suratMasuk_this_year = SuratMasuk.query.filter(SuratMasuk.created_at >= datetime(year, 1, 1)).count(),
        suratMasuk_this_week = SuratMasuk.query.filter(SuratMasuk.created_at >= (datetime.today() - timedelta(days=datetime.today().weekday()))).count(),
        suratKeluar_this_month = SuratKeluar.query.filter(SuratKeluar.created_at >= datetime(year, month, 1)).count(),
        suratKeluar_this_year = SuratKeluar.query.filter(SuratKeluar.created_at >= datetime(year, 1, 1)).count(),
        suratKeluar_this_week = SuratKeluar.query.filter(SuratKeluar.created_at >= (datetime.today() - timedelta(days=datetime.today().weekday()))).count(),
        recent_surat_masuk = SuratMasuk.query.order_by(SuratMasuk.created_at.desc()).limit(5).all(),
        recent_surat_keluar = SuratKeluar.query.order_by(SuratKeluar.created_at.desc()).limit(5).all(),
        users=User.query.order_by(User.last_login.desc()).limit(5).all(),

        chart_labels=chart_labels,
        chart_data_masuk=chart_data_masuk,
        chart_data_keluar=chart_data_keluar
    )

@app.route('/users', methods=['GET'])
@login_required
def user_list():
    users = User.query.all()
    return render_template('auth/user_list.html', users=users)

@app.route('/last-logins', methods=['GET'])
def last_logins():
    users = User.query.order_by(User.last_login.desc()).limit(10).all()
    result = [{"username": user.email, "last_login": user.last_login.strftime('%Y-%m-%d %H:%M:%S') if user.last_login else 'Never'} for user in users]
    return jsonify(result)

@app.route('/show_surat_keluar', methods=['GET'])
@login_required
def show_surat_keluar():
    sort = request.args.get('sort', 'tanggal_suratKeluar')
    order = request.args.get('order', 'asc')
    page = request.args.get('page', 1, type=int)
    search = request.args.get('search', '', type=str).strip()

    sort_options = {
        'tanggal_suratKeluar': SuratKeluar.tanggal_suratKeluar,
        'pengirim_suratKeluar': SuratKeluar.pengirim_suratKeluar,
        'penerima_suratKeluar': SuratKeluar.penerima_suratKeluar,
        'nomor_suratKeluar': SuratKeluar.nomor_suratKeluar,
        'isi_suratKeluar': SuratKeluar.isi_suratKeluar,
        'created_at': SuratKeluar.created_at
    }

    sort_column = sort_options.get(sort, SuratKeluar.tanggal_suratKeluar)
    order_by = asc(sort_column) if order == 'asc' else desc(sort_column)

    query = SuratKeluar.query

    if search:
        query = query.filter(
            SuratKeluar.pengirim_suratKeluar.ilike(f'%{search}%') |
            SuratKeluar.penerima_suratKeluar.ilike(f'%{search}%') |
            SuratKeluar.nomor_suratKeluar.ilike(f'%{search}%') |
            SuratKeluar.isi_suratKeluar.ilike(f'%{search}%')
        )

    surat_keluar = query.order_by(order_by).paginate(page=page, per_page=10)

    return render_template('home/show_surat_keluar.html',
                           entries=surat_keluar,
                           sort=sort,
                           order=order,
                           search=search)

@app.route('/show_surat_masuk', methods=['GET'])
@login_required
def show_surat_masuk():
    sort = request.args.get('sort', 'tanggal_suratMasuk')
    order = request.args.get('order', 'asc')
    page = request.args.get('page', 1, type=int)
    search = request.args.get('search', '').strip()
    sort_options = {
        'tanggal_suratMasuk': SuratMasuk.tanggal_suratMasuk,
        'pengirim_suratMasuk': SuratMasuk.pengirim_suratMasuk,
        'penerima_suratMasuk': SuratMasuk.penerima_suratMasuk,
        'nomor_suratMasuk': SuratMasuk.nomor_suratMasuk,
        'kode_suratMasuk': SuratMasuk.kode_suratMasuk,
        'jenis_suratMasuk': SuratMasuk.jenis_suratMasuk,
        'isi_suratMasuk': SuratMasuk.isi_suratMasuk
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
            (SuratMasuk.kode_suratMasuk.ilike(like_pattern)) |
            (SuratMasuk.jenis_suratMasuk.ilike(like_pattern)) |
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

@app.route('/input_surat_masuk', methods=['GET', 'POST'])
@login_required
@role_required('admin', 'pimpinan')
def input_surat_masuk():
    # 🔒 Batasi akses hanya untuk admin
    if not current_user.is_admin:
        flash('You do not have permission to access this page.', 'error')
        return redirect(url_for('index'))

    if request.method == 'POST':
        try:
            # ✅ Ambil dan validasi input dari form
            tanggal_str = request.form.get('tanggal_suratMasuk')
            pengirim = request.form.get('pengirim_suratMasuk')
            penerima = request.form.get('penerima_suratMasuk')
            nomor = request.form.get('nomor_suratMasuk')
            kode = request.form.get('kode_suratMasuk')
            jenis = request.form.get('jenis_suratMasuk')
            isi = request.form.get('isi_suratMasuk')
            file = request.files.get('image')

            if not all([tanggal_str, pengirim, penerima, nomor, kode, jenis, isi]):
                flash("All fields are required.", 'warning')
                return redirect(request.url)

            tanggal_obj = datetime.strptime(tanggal_str, '%Y-%m-%d')

            full_letter_number = nomor  # Kamu bisa tambahkan format lain jika perlu
            file_data = file.read() if file and file.filename else None

            new_surat = SuratMasuk(
                tanggal_suratMasuk=tanggal_obj,
                pengirim_suratMasuk=pengirim,
                penerima_suratMasuk=penerima,
                nomor_suratMasuk=nomor,
                kode_suratMasuk=kode,
                jenis_suratMasuk=jenis,
                isi_suratMasuk=isi,
                full_letter_number=full_letter_number,
                gambar_suratMasuk=file_data
            )

            db.session.add(new_surat)
            db.session.commit()
            flash('Surat Masuk has been added successfully!', 'success')
            return redirect(url_for('show_surat_masuk'))

        except ValueError:
            flash('Invalid date format. Please use YYYY-MM-DD.', 'danger')
        except Exception as e:
            db.session.rollback()
            flash(f'Error adding Surat Masuk: {str(e)}', 'danger')

    return render_template('home/input_surat_masuk.html')


@app.route('/input_surat_keluar', methods=['GET', 'POST'])
@login_required
@role_required('admin', 'pimpinan')
def input_surat_keluar():
    if not current_user.is_admin:
        flash('You do not have permission to access this page.', 'error')
        return redirect(url_for('index'))

    if request.method == 'POST':
        tanggal_suratKeluar = request.form['tanggal_suratKeluar']
        pengirim_suratKeluar = request.form['pengirim_suratKeluar']
        penerima_suratKeluar = request.form['penerima_suratKeluar']
        nomor_suratKeluar = request.form['nomor_suratKeluar']
        isi_suratKeluar = request.form['isi_suratKeluar']

        new_surat_keluar = SuratKeluar(
            tanggal_suratKeluar=datetime.strptime(tanggal_suratKeluar, '%Y-%m-%d'),
            pengirim_suratKeluar=pengirim_suratKeluar,
            penerima_suratKeluar=penerima_suratKeluar,
            nomor_suratKeluar=nomor_suratKeluar,
            isi_suratKeluar=isi_suratKeluar
        )
        db.session.add(new_surat_keluar)
        db.session.commit()
        flash('Surat Keluar has been added successfully!', 'success')
        return redirect(url_for('show_surat_keluar'))

    return render_template('home/input_surat_keluar.html')

@app.route('/edit_surat_keluar/<int:id>', methods=['GET', 'POST'])
@login_required
def edit_surat_keluar(id):
    if not current_user.is_admin:
        flash('You do not have permission to access this page.', 'error')
        return redirect(url_for('index'))

    entry = SuratKeluar.query.get_or_404(id)
    if request.method == 'POST':
        entry.tanggal_suratKeluar = datetime.strptime(request.form['tanggal_suratKeluar'], '%Y-%m-%d')
        entry.pengirim_suratKeluar = request.form['pengirim_suratKeluar']
        entry.penerima_suratKeluar = request.form['penerima_suratKeluar']
        entry.nomor_suratKeluar = request.form['nomor_suratKeluar']
        entry.isi_suratKeluar = request.form['isi_suratKeluar']
        db.session.commit()
        flash('Surat Keluar has been updated successfully!', 'success')
        return redirect(url_for('show_surat_keluar'))
    return render_template('home/edit_surat_keluar.html', entry=entry)

@app.route('/delete_surat_keluar/<int:id>', methods=['POST'])
@login_required
def delete_surat_keluar(id):
    entry = SuratKeluar.query.get_or_404(id)
    db.session.delete(entry)
    db.session.commit()
    flash('Surat Keluar has been deleted successfully!', 'success')
    return redirect(url_for('show_surat_keluar'))

@app.route('/edit_surat_masuk/<int:id>', methods=['GET', 'POST'])
@login_required
def edit_surat_masuk(id):
    if not current_user.is_admin:
        flash('You do not have permission to access this page.', 'error')
        return redirect(url_for('index'))

    entry = SuratMasuk.query.get_or_404(id)
    if request.method == 'POST':
        entry.tanggal_suratMasuk = datetime.strptime(request.form['tanggal_suratMasuk'], '%Y-%m-%d')
        entry.pengirim_suratMasuk = request.form['pengirim_suratMasuk']
        entry.penerima_suratMasuk = request.form['penerima_suratMasuk']
        entry.nomor_suratMasuk = request.form['nomor_suratMasuk']
        entry.kode_suratMasuk = request.form['kode_suratMasuk']
        entry.jenis_suratMasuk = request.form['jenis_suratMasuk']
        entry.isi_suratMasuk = request.form['isi_suratMasuk']
        db.session.commit()
        flash('Surat Masuk has been updated successfully!', 'success')
        return redirect(url_for('show_surat_masuk'))
    return render_template('home/edit_surat_masuk.html', entry=entry)

@app.route('/delete_surat_masuk/<int:id>', methods=['POST'])
@login_required
def delete_surat_masuk(id):
    entry = SuratMasuk.query.get_or_404(id)
    db.session.delete(entry)
    db.session.commit()
    flash('Surat Masuk has been deleted successfully!', 'success')
    return redirect(url_for('show_surat_masuk'))

from sqlalchemy import or_

@app.route("/laporan-statistik")
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
            total_keluar=total_keluar
    )

@app.route('/edit-user/<int:user_id>', methods=['GET', 'POST'])
@login_required
def edit_user(user_id):
    user = User.query.get_or_404(user_id)

    if request.method == 'POST':
        user.username = request.form['username']
        new_password = request.form['password']
        if new_password:
            user.password = generate_password_hash(new_password)
        db.session.commit()
        flash('User updated successfully!')
        return redirect(url_for('index'))

    return render_template('auth/edit_users.html', user=user)

@app.route('/edit-user', methods=['GET', 'POST'])
@login_required
def edit_user_view():
    # Check if current user is admin
    if not current_user.is_admin:
        flash('You do not have permission to edit users.', 'error')
        return redirect(url_for('index'))
    
    users = User.query.all()

    if request.method == 'POST':
        user_id = request.form.get('user_id')
        email = request.form.get('email')
        password = request.form.get('password')
        role = request.form.get('role')
        is_approved = 'is_approved' in request.form

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
            flash('User updated successfully!', 'success')
        else:
            flash('User not found.', 'error')

        return redirect(url_for('edit_user_view'))

    return render_template('auth/edit_users.html', users=users)

@app.route('/get-user-data/<int:user_id>')
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

@app.route('/approve-user/<int:user_id>', methods=['POST'])
@login_required
def approve_user(user_id):
    # Check if current user is admin
    if not current_user.is_admin:
        flash('You do not have permission to approve users.', 'error')
        return redirect(url_for('index'))
    
    user = User.query.get_or_404(user_id)
    user.is_approved = True
    db.session.commit()
    flash(f'User {user.email} has been approved.', 'success')
    return redirect(url_for('edit_user_view'))

@app.route('/delete-user/<int:user_id>', methods=['POST'])
@login_required
def delete_user(user_id):
    # Check if current user is admin
    if not current_user.is_admin:
        flash('You do not have permission to delete users.', 'error')
        return redirect(url_for('index'))
    
    # Prevent deleting yourself
    if user_id == current_user.id:
        flash('You cannot delete your own account.', 'error')
        return redirect(url_for('edit_user_view'))
    
    user = User.query.get_or_404(user_id)
    db.session.delete(user)
    db.session.commit()
    flash(f'User {user.email} has been deleted.', 'success')
    return redirect(url_for('edit_user_view'))

@app.route('/chart-data')
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

@app.route('/generate-cuti', methods=['GET', 'POST'])
@login_required
def generate_cuti():
    if request.method == 'GET':
        return render_template('home/generate_cuti_form.html')

    def romawi_bulan(bulan):
        romawi = {
            1: 'I', 2: 'II', 3: 'III', 4: 'IV', 5: 'V', 6: 'VI',
            7: 'VII', 8: 'VIII', 9: 'IX', 10: 'X', 11: 'XI', 12: 'XII'
        }
        return romawi.get(bulan, '')

    # Ambil semua data dari form
    context = {
        "nama": request.form.get("nama"),
        "nip": request.form.get("nip"),
        "jabatan": request.form.get("jabatan"),
        "gol_ruang": request.form.get("gol_ruang"),
        "unit_kerja": request.form.get("unit_kerja"),
        "masa_kerja": request.form.get("masa_kerja"),
        "c_tahun": "✓" if request.form.get("jenis_cuti") == "c_tahun" else "",
        "c_besar": "✓" if request.form.get("jenis_cuti") == "c_besar" else "",
        "c_sakit": "✓" if request.form.get("jenis_cuti") == "c_sakit" else "",
        "c_lahir": "✓" if request.form.get("jenis_cuti") == "c_lahir" else "",
        "c_penting": "✓" if request.form.get("jenis_cuti") == "c_penting" else "",
        "c_luarnegara": "✓" if request.form.get("jenis_cuti") == "c_luarnegara" else "",
        "alasan_cuti": request.form.get("alasan_cuti"),
        "lama_cuti": request.form.get("lama_cuti"),
        "tanggal_cuti": request.form.get("tanggal_cuti"),
        "sampai_cuti": request.form.get("sampai_cuti"),
        "telp": request.form.get("telp"),
        "alamat": request.form.get("alamat"),
        "no_suratmasuk": request.form.get("no_suratmasuk"),
    }

    try:
        tgl_obj = datetime.strptime(request.form.get("tgl_ajuan_cuti"), "%Y-%m-%d")
        context["tgl_ajuan_cuti"] = tgl_obj.strftime("%d")
        context["bulan_ajuan_cuti"] = romawi_bulan(tgl_obj.month)
        context["tahun_ajuan_cuti"] = str(tgl_obj.year)
        context["tgl_lengkap_ajuan_cuti"] = tgl_obj.strftime("%d %B %Y")
    except Exception:
        context["tgl_ajuan_cuti"] = ""
        context["bulan_ajuan_cuti"] = ""
        context["tahun_ajuan_cuti"] = ""
        context["tgl_lengkap_ajuan_cuti"] = ""

    template_path = 'static/assets/templates/form_permintaan_cuti.docx'
    document = MailMerge(template_path)
    document.merge(**context)

    temp_dir = tempfile.gettempdir()
    docx_filename = f"Cuti_{context['nama'].replace(' ', '_')}_{datetime.now().strftime('%Y%m%d%H%M%S')}.docx"
    docx_path = os.path.join(temp_dir, docx_filename)
    document.write(docx_path)
    document.close()

    try:
        subprocess.run([
            "/Applications/LibreOffice.app/Contents/MacOS/soffice",
            "--headless", "--convert-to", "pdf",
            "--outdir", temp_dir,
            docx_path
        ], check=True)

        if os.path.exists(docx_path):
            os.remove(docx_path)

        pdf_filename = docx_filename.replace('.docx', '.pdf')
        pdf_path = os.path.join(temp_dir, pdf_filename)
        return send_file(pdf_path, as_attachment=True)

    except Exception as e:
        return f"Error during PDF generation: {str(e)}", 500

@app.route('/surat_masuk')
@login_required
def surat_masuk():
    # Ambil semua surat masuk dari database, termasuk field full_letter_number
    daftar_surat = SuratMasuk.query.order_by(SuratMasuk.tanggal_suratMasuk.desc()).all()
    
    # Kirim data ke template
    return render_template('home/surat_masuk.html', daftar_surat=daftar_surat)


@app.route('/pegawai', methods=['GET', 'POST'])
@login_required
@role_required('admin', 'pimpinan')
def kelola_pegawai():
    if request.method == 'POST':
        try:
            pegawai_baru = Pegawai(
                nama=request.form['nama'],
                tanggal_lahir=datetime.strptime(request.form['tanggal_lahir'], '%Y-%m-%d'),
                nip=request.form['nip'],
                golongan=request.form['golongan'],
                jabatan=request.form['jabatan'],
                agama=request.form['agama'],
                jenis_kelamin=request.form['jenis_kelamin'],
                riwayat_pendidikan=request.form['riwayat_pendidikan'],
                riwayat_pekerjaan=request.form['riwayat_pekerjaan'],
                nomor_telpon=request.form['nomor_telpon']
            )
            db.session.add(pegawai_baru)
            db.session.commit()
            flash('Pegawai berhasil ditambahkan!', 'success')
            return redirect(url_for('pegawai_list'))
        except Exception as e:
            db.session.rollback()
            flash(f'Gagal menambahkan pegawai: {str(e)}', 'danger')

    daftar_pegawai = Pegawai.query.all()
    return render_template('home/pegawai.html', pegawais=daftar_pegawai)

@app.route('/pegawai/list', methods=['GET'])
@login_required
@role_required('admin', 'pimpinan')
def pegawai_list():
    pegawais = Pegawai.query.all()
    return render_template('home/list_pegawai.html', daftar_pegawai=pegawais)

@app.route('/pegawai/edit/<int:id>', methods=['POST'])
@login_required
@role_required('admin', 'pimpinan')
def edit_pegawai(id):
    pegawai = Pegawai.query.get_or_404(id)
    try:
        pegawai.nama = request.form['nama']
        pegawai.nip = request.form['nip']
        pegawai.tanggal_lahir = datetime.strptime(request.form['tanggal_lahir'], '%Y-%m-%d')
        pegawai.golongan = request.form['golongan']
        pegawai.jabatan = request.form['jabatan']
        pegawai.agama = request.form['agama']
        pegawai.jenis_kelamin = request.form['jenis_kelamin']
        pegawai.nomor_telpon = request.form['nomor_telpon']
        pegawai.riwayat_pendidikan = request.form['riwayat_pendidikan']
        pegawai.riwayat_pekerjaan = request.form['riwayat_pekerjaan']
        db.session.commit()
        flash('Data pegawai berhasil diperbarui!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Gagal memperbarui data: {str(e)}', 'danger')
    return redirect(url_for('pegawai_list'))

@app.route('/pegawai/hapus/<int:id>', methods=['POST'])
@login_required
@role_required('admin', 'pimpinan')
def hapus_pegawai(id):
    pegawai = Pegawai.query.get_or_404(id)
    try:
        db.session.delete(pegawai)
        db.session.commit()
        flash('Data pegawai berhasil dihapus.', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Gagal menghapus data: {str(e)}', 'danger')
    return redirect(url_for('pegawai_list'))