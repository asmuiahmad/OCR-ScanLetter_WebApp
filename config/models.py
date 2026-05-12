from datetime import datetime

from flask_login import UserMixin
from werkzeug.security import check_password_hash, generate_password_hash

from config.extensions import db


class User(db.Model, UserMixin):
    __tablename__ = "user"
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(100), unique=True, nullable=False)
    password = db.Column(db.String(100), nullable=False)
    last_login = db.Column(db.DateTime, nullable=True)
    login_count = db.Column(db.Integer, default=0)
    is_admin = db.Column(db.Boolean, default=False)
    role = db.Column(db.String(20), nullable=False, default="karyawan")
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
    status_suratMasuk = db.Column(db.String(20), default="pending", nullable=False)
    acara_suratMasuk = db.Column(db.Text, nullable=True)
    tempat_suratMasuk = db.Column(db.Text, nullable=True)
    tanggal_acara_suratMasuk = db.Column(db.Date, nullable=True)
    jam_suratMasuk = db.Column(db.String(10), nullable=True)
    approved_by = db.Column(db.String(100), nullable=True)
    approved_at = db.Column(db.DateTime, nullable=True)
    approval_notes = db.Column(db.Text, nullable=True)
    rejected_reason = db.Column(db.Text, nullable=True)


class SuratKeluar(db.Model):
    id_suratKeluar = db.Column(db.Integer, primary_key=True)
    tanggal_suratKeluar = db.Column(
        db.DateTime, nullable=False, default=datetime.utcnow
    )
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
    status_suratKeluar = db.Column(db.String(20), default="pending", nullable=False)
    kode_suratKeluar = db.Column(db.String(100), nullable=False)
    jenis_suratKeluar = db.Column(db.String(100), nullable=False)
    approved_by = db.Column(db.String(100), nullable=True)
    approved_at = db.Column(db.DateTime, nullable=True)
    approval_notes = db.Column(db.Text, nullable=True)
    rejected_reason = db.Column(db.Text, nullable=True)


class Cuti(db.Model):
    __tablename__ = "cuti"
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
    status_cuti = db.Column(db.String(20), default="pending", nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    approved_by = db.Column(db.String(100), nullable=True)
    approved_at = db.Column(db.DateTime, nullable=True)
    notes = db.Column(db.Text, nullable=True)
    qr_code = db.Column(db.Text, nullable=True)
    pdf_path = db.Column(db.Text, nullable=True)
    docx_path = db.Column(db.Text, nullable=True)


class Pegawai(db.Model):
    __tablename__ = "pegawai"
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
    batas_cuti = db.Column(db.Integer, default=12, nullable=False)
    unit_kerja = db.Column(db.String(100), nullable=True, default="")
    masa_kerja = db.Column(db.String(50), nullable=True, default="")


class UserLoginLog(db.Model):
    __tablename__ = "user_login_logs"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(
        db.Integer, db.ForeignKey("user.id", ondelete="CASCADE"), nullable=True
    )
    user_email = db.Column(db.String(255), nullable=False)
    login_time = db.Column(db.DateTime, default=datetime.utcnow)
    logout_time = db.Column(db.DateTime, nullable=True)
    ip_address = db.Column(db.String(45), nullable=True)
    user_agent = db.Column(db.Text, nullable=True)
    status = db.Column(db.String(20), default="success")
    session_duration = db.Column(db.Integer, nullable=True)
    browser_info = db.Column(db.String(255), nullable=True)
    device_type = db.Column(db.String(50), nullable=True)
    location = db.Column(db.String(255), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(
        db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    user = db.relationship("User", backref="login_logs")

    def to_dict(self):
        from datetime import timedelta, timezone

        indonesia_tz = timezone(timedelta(hours=7))

        def convert_to_indonesia_time(dt):
            if dt:
                return (
                    dt.replace(tzinfo=timezone.utc).astimezone(indonesia_tz).isoformat()
                )
            return None

        return {
            "id": self.id,
            "user_id": self.user_id,
            "user_email": self.user_email,
            "login_time": convert_to_indonesia_time(self.login_time),
            "logout_time": convert_to_indonesia_time(self.logout_time),
            "ip_address": self.ip_address,
            "user_agent": self.user_agent,
            "status": self.status,
            "session_duration": self.session_duration,
            "browser_info": self.browser_info,
            "device_type": self.device_type,
            "location": self.location,
            "created_at": convert_to_indonesia_time(self.created_at),
            "updated_at": convert_to_indonesia_time(self.updated_at),
        }


class AuditLog(db.Model):
    __tablename__ = "audit_logs"

    id = db.Column(db.Integer, primary_key=True)
    entity_type = db.Column(db.String(50), nullable=False)
    entity_id = db.Column(db.Integer, nullable=False)
    action = db.Column(db.String(50), nullable=False)
    performed_by = db.Column(db.String(255), nullable=True)
    notes = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            "id": self.id,
            "entity_type": self.entity_type,
            "entity_id": self.entity_id,
            "action": self.action,
            "performed_by": self.performed_by,
            "notes": self.notes,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


class DisposisiSurat(db.Model):
    __tablename__ = "disposisi_surat"

    id = db.Column(db.Integer, primary_key=True)
    surat_tipe = db.Column(db.String(10), nullable=False)  # masuk | keluar
    surat_masuk_id = db.Column(
        db.Integer, db.ForeignKey("surat_masuk.id_suratMasuk"), nullable=True
    )
    surat_keluar_id = db.Column(
        db.Integer, db.ForeignKey("surat_keluar.id_suratKeluar"), nullable=True
    )
    dari_user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    kepada_user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    perihal = db.Column(db.String(255), nullable=True)
    instruksi = db.Column(db.Text, nullable=False)
    prioritas = db.Column(db.String(20), default="normal", nullable=False)
    status = db.Column(db.String(20), default="draft", nullable=False)
    batas_waktu = db.Column(db.Date, nullable=True)
    catatan_tindak_lanjut = db.Column(db.Text, nullable=True)
    tanggal_disposisi = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    tanggal_selesai = db.Column(db.DateTime, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    surat_masuk = db.relationship("SuratMasuk", backref="disposisi_surat_masuk")
    surat_keluar = db.relationship("SuratKeluar", backref="disposisi_surat_keluar")
    dari_user = db.relationship("User", foreign_keys=[dari_user_id], backref="disposisi_pengirim")
    kepada_user = db.relationship("User", foreign_keys=[kepada_user_id], backref="disposisi_penerima")

    def get_nomor_surat(self):
        if self.surat_tipe == "masuk" and self.surat_masuk:
            return self.surat_masuk.nomor_suratMasuk
        if self.surat_tipe == "keluar" and self.surat_keluar:
            return self.surat_keluar.nomor_suratKeluar
        return "-"


def load_user(user_id):
    return User.query.get(int(user_id))


class Disposisi(db.Model):
    __tablename__ = 'disposisi'
    
    id = db.Column(db.Integer, primary_key=True)
    
    # Surat reference - support both masuk and keluar
    surat_tipe = db.Column(db.String(10), nullable=False)  # 'masuk' or 'keluar'
    surat_masuk_id = db.Column(db.Integer, db.ForeignKey('surat_masuk.id_suratMasuk'), nullable=True)
    surat_keluar_id = db.Column(db.Integer, db.ForeignKey('surat_keluar.id_suratKeluar'), nullable=True)
    
    # Users
    dari_user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    kepada_user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    
    # Content
    perihal = db.Column(db.String(200), nullable=True)
    instruksi = db.Column(db.Text, nullable=False)
    catatan_tindak_lanjut = db.Column(db.Text, nullable=True)
    
    # Status tracking
    status = db.Column(db.String(20), default='draft')  # draft, dikirim, diproses, selesai, ditolak
    status_surat_sebelum = db.Column(db.String(50), nullable=True)  # Backup status surat sebelum disposisi
    alasan_penolakan = db.Column(db.Text, nullable=True)  # Alasan jika ditolak
    
    # Priority and deadline
    prioritas = db.Column(db.String(20), default='normal')  # rendah, normal, tinggi, urgent
    batas_waktu = db.Column(db.Date, nullable=True)  # deadline disposisi
    
    # Timestamps
    tanggal_disposisi = db.Column(db.DateTime, default=datetime.utcnow)
    tanggal_dikirim = db.Column(db.DateTime, nullable=True)  # Kapan disposisi dikirim
    tanggal_diproses = db.Column(db.DateTime, nullable=True)  # Kapan mulai diproses
    tanggal_selesai = db.Column(db.DateTime, nullable=True)  # Kapan selesai
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relasi
    surat_masuk = db.relationship('SuratMasuk', backref='disposisi_surat_v2', foreign_keys=[surat_masuk_id])
    surat_keluar = db.relationship('SuratKeluar', backref='disposisi_surat_keluar_v2', foreign_keys=[surat_keluar_id])
    dari_user = db.relationship('User', foreign_keys=[dari_user_id], backref='disposisi_dari')
    kepada_user = db.relationship('User', foreign_keys=[kepada_user_id], backref='disposisi_kepada')
    
    def get_surat(self):
        """Get the related surat (masuk or keluar)"""
        if self.surat_tipe == 'masuk':
            return self.surat_masuk
        elif self.surat_tipe == 'keluar':
            return self.surat_keluar
        return None
    
    def get_nomor_surat(self):
        """Get nomor surat from related surat"""
        surat = self.get_surat()
        if not surat:
            return None
        if self.surat_tipe == 'masuk':
            return surat.nomor_suratMasuk
        elif self.surat_tipe == 'keluar':
            return surat.nomor_suratKeluar
        return None
    
    def is_overdue(self):
        """Check if disposisi is overdue"""
        if not self.batas_waktu:
            return False
        if self.status in ['selesai', 'ditolak']:
            return False
        from datetime import date
        return date.today() > self.batas_waktu
    
    def days_until_deadline(self):
        """Calculate days until deadline"""
        if not self.batas_waktu:
            return None
        from datetime import date
        delta = self.batas_waktu - date.today()
        return delta.days
    
    def to_dict(self):
        return {
            'id': self.id,
            'surat_tipe': self.surat_tipe,
            'surat_masuk_id': self.surat_masuk_id,
            'surat_keluar_id': self.surat_keluar_id,
            'dari_user_id': self.dari_user_id,
            'kepada_user_id': self.kepada_user_id,
            'perihal': self.perihal,
            'instruksi': self.instruksi,
            'catatan_tindak_lanjut': self.catatan_tindak_lanjut,
            'status': self.status,
            'alasan_penolakan': self.alasan_penolakan,
            'prioritas': self.prioritas,
            'batas_waktu': self.batas_waktu.isoformat() if self.batas_waktu else None,
            'tanggal_disposisi': self.tanggal_disposisi.isoformat() if self.tanggal_disposisi else None,
            'tanggal_dikirim': self.tanggal_dikirim.isoformat() if self.tanggal_dikirim else None,
            'tanggal_diproses': self.tanggal_diproses.isoformat() if self.tanggal_diproses else None,
            'tanggal_selesai': self.tanggal_selesai.isoformat() if self.tanggal_selesai else None,
            'is_overdue': self.is_overdue(),
            'days_until_deadline': self.days_until_deadline(),
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }


class DisposisiHistory(db.Model):
    """Track history of disposisi status changes"""
    __tablename__ = 'disposisi_history'
    
    id = db.Column(db.Integer, primary_key=True)
    disposisi_id = db.Column(db.Integer, db.ForeignKey('disposisi.id'), nullable=False)
    status_lama = db.Column(db.String(20), nullable=True)
    status_baru = db.Column(db.String(20), nullable=False)
    catatan = db.Column(db.Text, nullable=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)  # Make nullable
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relasi
    disposisi = db.relationship('Disposisi', backref='history')
    user = db.relationship('User', backref='disposisi_history')
    
    def to_dict(self):
        return {
            'id': self.id,
            'disposisi_id': self.disposisi_id,
            'status_lama': self.status_lama,
            'status_baru': self.status_baru,
            'catatan': self.catatan,
            'user_id': self.user_id,
            'user_email': self.user.email if self.user else 'System',
            'timestamp': self.timestamp.isoformat() if self.timestamp else None
        }