from config.extensions import db
from flask_login import UserMixin
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash

class User(db.Model, UserMixin):
    __tablename__ = 'user'
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(150), unique=True, nullable=False)
    password = db.Column(db.String(150), nullable=False)
    last_login = db.Column(db.DateTime, nullable=True)
    login_count = db.Column(db.Integer, default=0)
    is_admin = db.Column(db.Boolean, default=False)

    def set_password(self, password):
        self.password = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password, password)

class SuratMasuk(db.Model):
    id_suratMasuk = db.Column(db.Integer, primary_key=True)
    full_letter_number = db.Column(db.String(255))
    tanggal_suratMasuk = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    pengirim_suratMasuk = db.Column(db.Text, nullable=False)
    penerima_suratMasuk = db.Column(db.Text, nullable=False)
    nomor_suratMasuk = db.Column(db.Text, nullable=False)
    kode_suratMasuk = db.Column(db.Text, nullable=False)
    jenis_suratMasuk = db.Column(db.Text, nullable=False)
    isi_suratMasuk = db.Column(db.Text, nullable=False)
    gambar_suratMasuk = db.Column(db.LargeBinary, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    ocr_accuracy_suratMasuk = db.Column(db.Float)
    initial_nomor_suratMasuk = db.Column(db.String(120))
    initial_pengirim_suratMasuk = db.Column(db.String(120))
    initial_penerima_suratMasuk = db.Column(db.String(120))
    initial_isi_suratMasuk = db.Column(db.Text)     

class SuratKeluar(db.Model):
    id_suratKeluar = db.Column(db.Integer, primary_key=True)
    tanggal_suratKeluar = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    pengirim_suratKeluar = db.Column(db.Text, nullable=False)
    penerima_suratKeluar = db.Column(db.Text, nullable=False)
    nomor_suratKeluar = db.Column(db.Text, nullable=False)
    isi_suratKeluar = db.Column(db.Text, nullable=False)
    gambar_suratKeluar = db.Column(db.LargeBinary, nullable=True) 
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    ocr_accuracy_suratKeluar = db.Column(db.Float)
    initial_nomor_suratKeluar = db.Column(db.String(120))
    initial_pengirim_suratKeluar = db.Column(db.String(120))
    initial_penerima_suratKeluar = db.Column(db.String(120))
    initial_isi_suratKeluar = db.Column(db.Text)
