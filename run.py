import os
from flask import Flask, render_template, request, redirect, url_for, flash
from flask_migrate import Migrate
from flask_minify import Minify
from sys import exit

from apps.config import config_dict
from apps import create_app, db

class SuratKeluar(db.Model):
    __tablename__ = 'surat_keluar'
    id_surat = db.Column(db.Integer, primary_key=True)
    tanggal_surat = db.Column(db.Text, nullable=False)
    pengirim_surat = db.Column(db.Text, nullable=False)
    penerima_surat = db.Column(db.Text, nullable=False)
    nomor_surat = db.Column(db.Text, nullable=False)
    kode_surat = db.Column(db.Text, nullable=False)
    jenis_surat = db.Column(db.Text, nullable=False)
    isi_surat = db.Column(db.Text, nullable=False)

class SuratMasuk(db.Model):
    __tablename__ = 'surat_masuk'
    id_surat = db.Column(db.Integer, primary_key=True)
    tanggal_surat = db.Column(db.Text, nullable=False)
    pengirim_surat = db.Column(db.Text, nullable=False)
    penerima_surat = db.Column(db.Text, nullable=False)
    nomor_surat = db.Column(db.Text, nullable=False)
    kode_surat = db.Column(db.Text, nullable=False)
    jenis_surat = db.Column(db.Text, nullable=False)
    isi_surat = db.Column(db.Text, nullable=False)

# WARNING: Don't run with debug turned on in production!
DEBUG = (os.getenv('DEBUG', 'False') == 'True')

# The configuration
get_config_mode = 'Debug' if DEBUG else 'Production'

try:
    app_config = config_dict[get_config_mode.capitalize()]

except KeyError:
    exit('Error: Invalid <config_mode>. Expected values [Debug, Production] ')

app = create_app(app_config)
Migrate(app, db)

if not DEBUG:
    Minify(app=app, html=True, js=False, cssless=False)

@app.route('/')
def index():
    surat_list = db.session.execute('SELECT * FROM surat').fetchall()
    return render_template('index.html', surat_list=surat_list)

@app.route('/add_surat_keluar', methods=['POST'])
def add_surat_keluar():
    
    tanggal_surat = request.form['tanggal_surat']
    pengirim_surat = request.form['pengirim_surat']
    penerima_surat = request.form['penerima_surat']
    nomor_surat = request.form['nomor_surat']
    kode_surat1 = request.form['kode_surat1']
    kode_surat2 = request.form['kode_surat2']
    kode_surat = f"{kode_surat1}/KPA/W15-A12/{kode_surat2}"
    jenis_surat = request.form['jenis_surat']
    isi_surat = request.form['isi_surat']

    new_surat_keluar = SuratKeluar(
        tanggal_surat=tanggal_surat,
        pengirim_surat=pengirim_surat,
        penerima_surat=penerima_surat,
        nomor_surat=nomor_surat,
        kode_surat=kode_surat,
        jenis_surat=jenis_surat,
        isi_surat=isi_surat
    )
    db.session.add(new_surat_keluar)
    db.session.commit()

    flash('Surat Berhasil di Input!')
    return redirect(url_for('input_surat_keluar'))

@app.route('/input_surat_keluar')
def input_surat_keluar():
    return render_template('home/input_surat_keluar.html')

@app.route('/add_surat_masuk', methods=['POST'])
def add_surat_masuk():
    if request.method == 'POST':

        tanggal_surat = request.form['tanggal_surat']
        pengirim_surat = request.form['pengirim_surat']
        penerima_surat = request.form['penerima_surat']
        nomor_surat = request.form['nomor_surat']
        kode_surat1 = request.form['kode_surat1']
        kode_surat2 = request.form['kode_surat2']
        kode_surat = f"{kode_surat1}/KPA/W15-A12/{kode_surat2}"
        jenis_surat = request.form['jenis_surat']
        isi_surat = request.form['isi_surat']

        new_surat_masuk = SuratMasuk(
            tanggal_surat=tanggal_surat,
            pengirim_surat=pengirim_surat,
            penerima_surat=penerima_surat,
            nomor_surat=nomor_surat,
            kode_surat=kode_surat,
            jenis_surat=jenis_surat,
            isi_surat=isi_surat
        )

        db.session.add(new_surat_masuk)
        db.session.commit()

        flash('Surat Masuk Berhasil di Input!', 'success')
        return redirect(url_for('input_surat_masuk'))

@app.route('/input_surat_masuk')
def input_surat_masuk():
    return render_template('home/input_surat_masuk.html')

@app.route('/tbl_bootstrap')
def surat_list():
    surat_records = SuratKeluar.query.all()
    return render_template('home/tbl_bootstrap.html', surat_records=surat_records)
    
if DEBUG:
    app.logger.info('DEBUG            = ' + str(DEBUG)             )
    app.logger.info('Page Compression = ' + 'FALSE' if DEBUG else 'TRUE' )
    app.logger.info('DBMS             = ' + app_config.SQLALCHEMY_DATABASE_URI)
    app.logger.info('ASSETS_ROOT      = ' + app_config.ASSETS_ROOT )

if __name__ == "__main__":
    app.run()