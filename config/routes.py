from flask import render_template, redirect, url_for, flash, request, jsonify
from flask_login import login_user, login_required, logout_user, current_user
from werkzeug.security import check_password_hash, generate_password_hash
from sqlalchemy import desc, asc
from config.extensions import db
from config.ocr import ocr_routes
from config.models import User, SuratMasuk, SuratKeluar
from config.forms import LoginForm, RegistrationForm
from datetime import datetime, timedelta
from app import app
from werkzeug.utils import secure_filename
import os
import pytesseract

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
    suratMasuk_count = SuratMasuk.query.count()
    suratKeluar_count = SuratKeluar.query.count()

    start_of_month = datetime.now().replace(day=1)
    start_of_year = datetime.now().replace(month=1, day=1)
    start_of_week = datetime.now() - timedelta(days=datetime.now().weekday())

    suratMasuk_this_month = SuratMasuk.query.filter(SuratMasuk.tanggal_suratMasuk >= start_of_month).count()
    suratMasuk_this_year = SuratMasuk.query.filter(SuratMasuk.tanggal_suratMasuk >= start_of_year).count()
    suratMasuk_this_week = SuratMasuk.query.filter(SuratMasuk.tanggal_suratMasuk >= start_of_week).count()

    suratKeluar_this_month = SuratKeluar.query.filter(SuratKeluar.tanggal_suratKeluar >= start_of_month).count()
    suratKeluar_this_year = SuratKeluar.query.filter(SuratKeluar.tanggal_suratKeluar >= start_of_year).count()
    suratKeluar_this_week = SuratKeluar.query.filter(SuratKeluar.tanggal_suratKeluar >= start_of_week).count()

    recent_surat_masuk = SuratMasuk.query.order_by(SuratMasuk.tanggal_suratMasuk.desc()).limit(5).all()
    recent_surat_keluar = SuratKeluar.query.order_by(SuratKeluar.tanggal_suratKeluar.desc()).limit(5).all()

    last_login_time = current_user.last_login if current_user.is_authenticated else None
    users = User.query.order_by(User.last_login.desc()).limit(5).all()

    return render_template('home/index.html',
                        suratMasuk_count=suratMasuk_count, 
                        suratKeluar_count=suratKeluar_count,
                        suratMasuk_this_month=suratMasuk_this_month, 
                        suratMasuk_this_year=suratMasuk_this_year,
                        suratMasuk_this_week=suratMasuk_this_week, 
                        suratKeluar_this_month=suratKeluar_this_month,
                        suratKeluar_this_year=suratKeluar_this_year, 
                        suratKeluar_this_week=suratKeluar_this_week,
                        recent_surat_masuk=recent_surat_masuk, 
                        recent_surat_keluar=recent_surat_keluar,
                        last_login_time=last_login_time, 
                        users=users)

ocr_routes(app)

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
        'kode_suratKeluar': SuratKeluar.kode_suratKeluar,
        'jenis_suratKeluar': SuratKeluar.jenis_suratKeluar,
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
        kode_suratKeluar = request.form['kode_suratKeluar']
        jenis_suratKeluar = request.form['jenis_suratKeluar']
        isi_suratKeluar = request.form['isi_suratKeluar']

        new_surat_keluar = SuratKeluar(
            tanggal_suratKeluar=datetime.strptime(tanggal_suratKeluar, '%Y-%m-%d'),
            pengirim_suratKeluar=pengirim_suratKeluar,
            penerima_suratKeluar=penerima_suratKeluar,
            nomor_suratKeluar=nomor_suratKeluar,
            kode_suratKeluar=kode_suratKeluar,
            jenis_suratKeluar=jenis_suratKeluar,
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
        entry.tanggal_suratKeluar = datetime.strptime(request.form['tanggal_suratKeluar', '%Y-%m-%d'])
        entry.pengirim_suratKeluar = request.form['pengirim_suratKeluar']
        entry.penerima_suratKeluar = request.form['penerima_suratKeluar']
        entry.nomor_suratKeluar = request.form['nomor_suratKeluar']
        entry.kode_suratKeluar = request.form['kode_suratKeluar']
        entry.jenis_suratKeluar = request.form['jenis_suratKeluar']
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
        entry.tanggal_suratMasuk = datetime.strptime(request.form['tanggal_suratMasuk', '%Y-%m-%d'])
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