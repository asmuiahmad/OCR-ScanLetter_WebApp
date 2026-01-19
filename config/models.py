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
    file_suratMasuk = db.Column(db.LargeBinary, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    ocr_accuracy_suratMasuk = db.Column(db.Float)
    initial_full_letter_number = db.Column(db.String(255))
    initial_pengirim_suratMasuk = db.Column(db.String(255))
    initial_penerima_suratMasuk = db.Column(db.String(255))
    initial_isi_suratMasuk = db.Column(db.Text)
    initial_nomor_suratMasuk = db.Column(db.String(255))
    status_suratMasuk = db.Column(db.String(20), default='pending', nullable=False)
    acara_suratMasuk = db.Column(db.Text, nullable=True)
    tempat_suratMasuk = db.Column(db.Text, nullable=True)
    tanggal_acara_suratMasuk = db.Column(db.Date, nullable=True)
    jam_suratMasuk = db.Column(db.String(10), nullable=True)

class SuratKeluar(db.Model):
    id_suratKeluar = db.Column(db.Integer, primary_key=True)
    tanggal_suratKeluar = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    pengirim_suratKeluar = db.Column(db.Text, nullable=False)
    penerima_suratKeluar = db.Column(db.Text, nullable=False)
    nomor_suratKeluar = db.Column(db.Text, nullable=False)
    isi_suratKeluar = db.Column(db.Text, nullable=False)
    gambar_suratKeluar = db.Column(db.LargeBinary, nullable=True)
    file_suratKeluar = db.Column(db.LargeBinary, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    ocr_accuracy_suratKeluar = db.Column(db.Float)
    initial_nomor_suratKeluar = db.Column(db.String(255))
    initial_pengirim_suratKeluar = db.Column(db.String(255))
    initial_penerima_suratKeluar = db.Column(db.String(255))
    initial_isi_suratKeluar = db.Column(db.Text)
    acara_suratKeluar = db.Column(db.Text, nullable=True)
    tempat_suratKeluar = db.Column(db.Text, nullable=True)
    tanggal_acara_suratKeluar = db.Column(db.Date, nullable=True)
    jam_suratKeluar = db.Column(db.String(10), nullable=True)
    status_suratKeluar = db.Column(db.String(20), default='pending', nullable=False)
    kode_suratKeluar = db.Column(db.String(100), nullable=False)
    jenis_suratKeluar = db.Column(db.String(100), nullable=False)

class Cuti(db.Model):
    __tablename__ = 'cuti'
    id_cuti = db.Column(db.Integer, primary_key=True)
    nama = db.Column(db.String(100), nullable=False)
    nip = db.Column(db.String(50), nullable=False)
    jabatan = db.Column(db.String(100), nullable=False)
    gol_ruang = db.Column(db.String(50), nullable=False)
    unit_kerja = db.Column(db.String(100), nullable=False)
    masa_kerja = db.Column(db.String(100), nullable=False)
    alamat = db.Column(db.Text, nullable=False)
    no_suratmasuk = db.Column(db.String(100), nullable=False)
    tgl_ajuan_cuti = db.Column(db.Date, nullable=False)
    tanggal_cuti = db.Column(db.Date, nullable=False)
    sampai_cuti = db.Column(db.Date, nullable=False)
    telp = db.Column(db.String(20), nullable=False)
    jenis_cuti = db.Column(db.String(50), nullable=False)
    alasan_cuti = db.Column(db.Text, nullable=False)
    lama_cuti = db.Column(db.String(50), nullable=False)
    status_cuti = db.Column(db.String(20), default='pending', nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    approved_by = db.Column(db.String(100), nullable=True)
    approved_at = db.Column(db.DateTime, nullable=True)
    notes = db.Column(db.Text, nullable=True)
    qr_code = db.Column(db.Text, nullable=True)
    pdf_path = db.Column(db.Text, nullable=True)
    docx_path = db.Column(db.Text, nullable=True)

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

class UserLoginLog(db.Model):
    __tablename__ = 'user_login_logs'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id', ondelete='CASCADE'), nullable=True)
    user_email = db.Column(db.String(255), nullable=False)
    login_time = db.Column(db.DateTime, default=datetime.utcnow)
    logout_time = db.Column(db.DateTime, nullable=True)
    ip_address = db.Column(db.String(45), nullable=True)
    user_agent = db.Column(db.Text, nullable=True)
    status = db.Column(db.String(20), default='success')
    session_duration = db.Column(db.Integer, nullable=True)
    browser_info = db.Column(db.String(255), nullable=True)
    device_type = db.Column(db.String(50), nullable=True)
    location = db.Column(db.String(255), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    user = db.relationship('User', backref='login_logs')
    
    def to_dict(self):
        from datetime import timezone, timedelta
        
        indonesia_tz = timezone(timedelta(hours=7))
        
        def convert_to_indonesia_time(dt):
            if dt:
                return dt.replace(tzinfo=timezone.utc).astimezone(indonesia_tz).isoformat()
            return None
        
        return {
            'id': self.id,
            'user_id': self.user_id,
            'user_email': self.user_email,
            'login_time': convert_to_indonesia_time(self.login_time),
            'logout_time': convert_to_indonesia_time(self.logout_time),
            'ip_address': self.ip_address,
            'user_agent': self.user_agent,
            'status': self.status,
            'session_duration': self.session_duration,
            'browser_info': self.browser_info,
            'device_type': self.device_type,
            'location': self.location,
            'created_at': convert_to_indonesia_time(self.created_at),
            'updated_at': convert_to_indonesia_time(self.updated_at)
        }

def load_user(user_id):
    return User.query.get(int(user_id))