from flask import render_template, redirect, url_for, flash, request, jsonify, session
from flask_login import login_user, login_required, logout_user, current_user
from werkzeug.security import check_password_hash, generate_password_hash
from sqlalchemy import desc, asc, extract, func
from collections import defaultdict
from config.extensions import db
from config.ocr import ocr_bp
from config.ocr_utils import hitung_field_not_found
from config.models import User, SuratMasuk, SuratKeluar
from config.forms import LoginForm, RegistrationForm
from datetime import datetime, timedelta
from app import app
from werkzeug.utils import secure_filename
import os
import pytesseract
from calendar import monthrange

@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user and check_password_hash(user.password, form.password.data):
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
            hashed_password = generate_password_hash(form.password.data, method='pbkdf2:sha256')
            new_user = User(email=form.email.data, password=hashed_password)
            db.session.add(new_user)
            db.session.commit()
            flash('Registration successful! Please login.', 'success')
            return redirect(url_for('login'))
        except Exception as e:
            db.session.rollback()
            flash('An error occurred during registration. Please try again.', 'error')
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
        day = surat.tanggal_suratMasuk.day
        surat_masuk_per_day[day] += 1

    surat_keluar_records = SuratKeluar.query.filter(
        SuratKeluar.tanggal_suratKeluar >= datetime(year, month, 1),
        SuratKeluar.tanggal_suratKeluar < datetime(year, month, days_in_month) + timedelta(days=1)
    ).all()

    for surat in surat_keluar_records:
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

@app.route('/last-logins', methods=['GET'])
def last_logins():
    users = User.query.order_by(User.last_login.desc()).limit(10).all()
    result = [{"username": user.email, "last_login": user.last_login.strftime('%Y-%m-%d %H:%M:%S') if user.last_login else 'Never'} for user in users]
    return jsonify(result)

@app.route('/show_surat_keluar', methods=['GET'])
@login_required
def show_surat_keluar():
    if not current_user.is_admin:
        flash('You do not have permission to access this page.', 'error')
        return redirect(url_for('index'))

    sort = request.args.get('sort', 'tanggal_suratKeluar')
    order = request.args.get('order', 'asc')
    page = request.args.get('page', 1, type=int)

    sort_options = {
        'tanggal_suratKeluar': SuratKeluar.tanggal_suratKeluar,
        'pengirim_suratKeluar': SuratKeluar.pengirim_suratKeluar,
        'penerima_suratKeluar': SuratKeluar.penerima_suratKeluar,
        'nomor_suratKeluar': SuratKeluar.nomor_suratKeluar,
        'isi_suratKeluar': SuratKeluar.isi_suratKeluar
    }

    sort_column = sort_options.get(sort, SuratKeluar.tanggal_suratKeluar)
    order_by = asc(sort_column) if order == 'asc' else desc(sort_column)

    surat_keluar = SuratKeluar.query.order_by(order_by).paginate(page=page, per_page=10)

    return render_template('home/show_surat_keluar.html', entries=surat_keluar, sort=sort, order=order)

@app.route('/show_surat_masuk', methods=['GET'])
@login_required
def show_surat_masuk():
    if not current_user.is_admin:
        flash('You do not have permission to access this page.', 'error')
        return redirect(url_for('index'))

    sort = request.args.get('sort', 'tanggal_suratMasuk')
    order = request.args.get('order', 'asc')
    page = request.args.get('page', 1, type=int)

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

    surat_masuk_entries = SuratMasuk.query.order_by(order_by).paginate(page=page, per_page=20)

    return render_template('home/show_surat_masuk.html', entries=surat_masuk_entries, sort=sort, order=order)

@app.route('/input_surat_masuk', methods=['GET', 'POST'])
@login_required
def input_surat_masuk():
    if not current_user.is_admin:
        flash('You do not have permission to access this page.', 'error')
        return redirect(url_for('index'))

    if request.method == 'POST':
        tanggal_suratMasuk = request.form['tanggal_suratMasuk']
        pengirim_suratMasuk = request.form['pengirim_suratMasuk']
        penerima_suratMasuk = request.form['penerima_suratMasuk']
        nomor_suratMasuk = request.form['nomor_suratMasuk']
        kode_suratMasuk = request.form['kode_suratMasuk']
        jenis_suratMasuk = request.form['jenis_suratMasuk']
        isi_suratMasuk = request.form['isi_suratMasuk']

        new_surat = SuratMasuk(
            tanggal_suratMasuk=datetime.strptime(tanggal_suratMasuk, '%Y-%m-%d'),
            pengirim_suratMasuk=pengirim_suratMasuk,
            penerima_suratMasuk=penerima_suratMasuk,
            nomor_suratMasuk=nomor_suratMasuk,
            kode_suratMasuk=kode_suratMasuk,
            jenis_suratMasuk=jenis_suratMasuk,
            isi_suratMasuk=isi_suratMasuk
        )
        db.session.add(new_surat)
        db.session.commit()
        flash('Surat Masuk has been added successfully!', 'success')
        return redirect(url_for('show_surat_masuk'))

    return render_template('home/input_surat_masuk.html')

@app.route('/input_surat_keluar', methods=['GET', 'POST'])
@login_required
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

@app.route("/laporan-statistik")
@login_required
def laporan_statistik():
    semua_surat_keluar = SuratKeluar.query.all()
    semua_surat_masuk = SuratMasuk.query.all()

    total_masuk = len(semua_surat_masuk)
    total_keluar = len(semua_surat_keluar)

    berhasil_masuk = SuratMasuk.query.filter(~SuratMasuk.isi_suratMasuk.contains("Not found")).count()
    berhasil_keluar = SuratKeluar.query.filter(~SuratKeluar.isi_suratKeluar.contains("Not found")).count()

    persen_berhasil_masuk = round((berhasil_masuk / total_masuk * 100), 2) if total_masuk else 0
    persen_berhasil_keluar = round((berhasil_keluar / total_keluar * 100), 2) if total_keluar else 0

    # Init field not found stats
    field_stats_masuk = {
        'nomor_suratMasuk': SuratMasuk.query.filter(SuratMasuk.initial_nomor_suratMasuk == 'Not found').count(),
        'pengirim_suratMasuk': SuratMasuk.query.filter(SuratMasuk.initial_pengirim_suratMasuk == 'Not found').count(),
        'penerima_suratMasuk': SuratMasuk.query.filter(SuratMasuk.initial_penerima_suratMasuk == 'Not found').count(),
        'isi_suratMasuk': SuratMasuk.query.filter(SuratMasuk.initial_isi_suratMasuk == 'Not found').count(),
    }
    field_stats_keluar = {
        'nomor_suratKeluar': SuratKeluar.query.filter(SuratKeluar.initial_nomor_suratKeluar == 'Not found').count(),
        'pengirim_suratKeluar': SuratKeluar.query.filter(SuratKeluar.initial_pengirim_suratKeluar == 'Not found').count(),
        'penerima_suratKeluar': SuratKeluar.query.filter(SuratKeluar.initial_penerima_suratKeluar == 'Not found').count(),
        'isi_suratKeluar': SuratKeluar.query.filter(SuratKeluar.initial_isi_suratKeluar == 'Not found').count(),
    }

    # Count 'Not found' per field in SuratMasuk
    for surat in semua_surat_masuk:
        if surat.nomor_suratMasuk == 'Not found':
            field_stats_masuk['nomor_suratMasuk'] += 1
        if surat.pengirim_suratMasuk == 'Not found':
            field_stats_masuk['pengirim_suratMasuk'] += 1
        if surat.penerima_suratMasuk == 'Not found':
            field_stats_masuk['penerima_suratMasuk'] += 1
        if surat.isi_suratMasuk == 'Not found':
            field_stats_masuk['isi_suratMasuk'] += 1

    # Count 'Not found' per field in SuratKeluar
    for surat in semua_surat_keluar:
        if surat.nomor_suratKeluar == 'Not found':
            field_stats_keluar['nomor_suratKeluar'] += 1
        if surat.pengirim_suratKeluar == 'Not found':
            field_stats_keluar['pengirim_suratKeluar'] += 1
        if surat.penerima_suratKeluar == 'Not found':
            field_stats_keluar['penerima_suratKeluar'] += 1
        if surat.isi_suratKeluar == 'Not found':
            field_stats_keluar['isi_suratKeluar'] += 1

    # Tambahan: full letter number components
    full_letter_components_masuk = ['nomor_suratMasuk', 'kode_suratMasuk']
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

    # Average OCR Accuracy
    akurasi_masuk = [s.ocr_accuracy_suratMasuk for s in semua_surat_masuk if s.ocr_accuracy_suratMasuk is not None]
    akurasi_keluar = [s.ocr_accuracy_suratKeluar for s in semua_surat_keluar if s.ocr_accuracy_suratKeluar is not None]

    rata2_akurasi_masuk = round(sum(akurasi_masuk) / len(akurasi_masuk), 2) if akurasi_masuk else 0
    rata2_akurasi_keluar = round(sum(akurasi_keluar) / len(akurasi_keluar), 2) if akurasi_keluar else 0

    # Failed extractions
    gagal_ekstraksi = [s for s in semua_surat_keluar if s.ocr_accuracy_suratKeluar and s.ocr_accuracy_suratKeluar < 100]
    berhasil_count = len([s for s in semua_surat_keluar if s.ocr_accuracy_suratKeluar == 100])
    persentase_berhasil = round((berhasil_count / total_keluar) * 100, 2) if total_keluar else 0

    # Optional keyword search
    keyword = request.args.get('keyword', '')
    surat_keyword = []
    if keyword:
        surat_keyword = SuratKeluar.query.filter(SuratKeluar.isi_suratKeluar.ilike(f'%{keyword}%')).all()

    return render_template(
        "home/laporan_statistik.html",
        persentase_berhasil=persentase_berhasil,
        gagal_ekstraksi=gagal_ekstraksi,
        keyword=keyword,
        surat_keyword=surat_keyword,
        rata2_akurasi_masuk=rata2_akurasi_masuk,
        rata2_akurasi_keluar=rata2_akurasi_keluar,
        field_stats_keluar=field_stats_keluar,
        field_stats_masuk=field_stats_masuk
    )
