from config.extensions import db
from flask_login import UserMixin
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash

class User(db.Model, UserMixin):
    __tablename__ = 'user'
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(100), unique=True, nullable=False)
    password = db.Column(db.String(100), nullable=False)
    last_login = db.Column(db.DateTime, nullable=True)
    login_count = db.Column(db.Integer, default=0)
    is_admin = db.Column(db.Boolean, default=False)
    role = db.Column(db.String(20), nullable=False, default='karyawan')
    is_approved = db.Column(db.Boolean, nullable=False, default=False)

    def set_password(self, password):
        self.password = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password, password)

class SuratMasuk(db.Model):
    id_suratMasuk = db.Column(db.Integer, primary_key=True)
    full_letter_number = db.Column(db.String(255))
    nomor_suratMasuk = db.Column(db.String(255))
    tanggal_suratMasuk = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    pengirim_suratMasuk = db.Column(db.Text, nullable=False)
    penerima_suratMasuk = db.Column(db.Text, nullable=False)
    kode_suratMasuk = db.Column(db.Text, nullable=False)
    jenis_suratMasuk = db.Column(db.Text, nullable=False)
    isi_suratMasuk = db.Column(db.Text, nullable=False)
    gambar_suratMasuk = db.Column(db.LargeBinary, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    ocr_accuracy_suratMasuk = db.Column(db.Float)
    initial_full_letter_number = db.Column(db.String(255))
    initial_pengirim_suratMasuk = db.Column(db.String(255))
    initial_penerima_suratMasuk = db.Column(db.String(255))
    initial_isi_suratMasuk = db.Column(db.Text)
    initial_nomor_suratMasuk = db.Column(db.String(255))

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
    initial_nomor_suratKeluar = db.Column(db.String(255))
    initial_pengirim_suratKeluar = db.Column(db.String(255))
    initial_penerima_suratKeluar = db.Column(db.String(255))
    initial_isi_suratKeluar = db.Column(db.Text)

class Pegawai(db.Model):
    __tablename__ = 'pegawai'
    id = db.Column(db.Integer, primary_key=True)
    nama = db.Column(db.String(100), nullable=False)
    tanggal_lahir = db.Column(db.Date, nullable=False)
    nip = db.Column(db.String(50), unique=True, nullable=False)
    golongan = db.Column(db.String(50), nullable=True)
    agama = db.Column(db.String(30), nullable=True)
    jenis_kelamin = db.Column(db.String(10), nullable=False)
    riwayat_pendidikan = db.Column(db.Text, nullable=True)
    riwayat_pekerjaan = db.Column(db.Text, nullable=True)
    nomor_telpon = db.Column(db.String(20), nullable=True)
    jabatan = db.Column(db.String(100), nullable=True)

def load_user(user_id):
    return User.query.with_entities(User.id, User.email, User.password).get(int(user_id))