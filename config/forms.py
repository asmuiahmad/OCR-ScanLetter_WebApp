from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, SelectField, DateField, TextAreaField, BooleanField, RadioField
from wtforms.validators import DataRequired, Email, Length, EqualTo
from flask_wtf.file import FileField, FileAllowed

class RegistrationForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired(), Length(min=6, message='Password must be at least 6 characters long')])
    confirm_password = PasswordField('Confirm Password', validators=[DataRequired(), EqualTo('password', message='Passwords must match')])
    role = SelectField('Role', choices=[('karyawan', 'Karyawan'), ('pimpinan', 'Pimpinan'), ('admin', 'Admin')], validators=[DataRequired()])
    submit = SubmitField('Register')

class LoginForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired()])
    submit = SubmitField('Login')

class SuratKeluarForm(FlaskForm):
    tanggal_suratKeluar = DateField('Tanggal Surat', validators=[DataRequired()], format='%Y-%m-%d')
    pengirim_suratKeluar = StringField('Pengirim', validators=[DataRequired()])
    penerima_suratKeluar = StringField('Penerima', validators=[DataRequired()])
    nomor_suratKeluar = StringField('Nomor Surat', validators=[DataRequired()])
    kode_suratKeluar = StringField('Kode Surat', validators=[DataRequired()])
    jenis_suratKeluar = StringField('Jenis Surat', validators=[DataRequired()])
    isi_suratKeluar = TextAreaField('Isi Surat', validators=[DataRequired()])
    image = FileField('Gambar Surat', validators=[FileAllowed(['jpg', 'png', 'jpeg', 'gif'], 'Image only!')])
    submit = SubmitField('Simpan Surat Masuk')

class OCRSuratKeluarForm(FlaskForm):
    image = FileField('Upload Image', validators=[
        FileAllowed(['jpg', 'png', 'jpeg', 'webp'], 'Images only!')
    ])
    preprocess = BooleanField('Preprocessing')
    enhance_contrast = BooleanField('Enhance Contrast')
    submit = SubmitField('Process OCR')

class CutiForm(FlaskForm):
    nama = StringField('Nama', validators=[DataRequired()])
    nip = StringField('NIP', validators=[DataRequired()])
    jabatan = StringField('Jabatan', validators=[DataRequired()])
    gol_ruang = StringField('Gol. Ruang', validators=[DataRequired()])
    unit_kerja = StringField('Unit Kerja', validators=[DataRequired()])
    masa_kerja = StringField('Masa Kerja', validators=[DataRequired()])
    alamat = TextAreaField('Alamat', validators=[DataRequired()])
    no_suratmasuk = StringField('Nomor Surat Masuk', validators=[DataRequired()])
    tgl_ajuan_cuti = DateField('Tanggal Ajuan Cuti', validators=[DataRequired()])
    tanggal_cuti = DateField('Tanggal Mulai Cuti', validators=[DataRequired()])
    sampai_cuti = DateField('Tanggal Selesai Cuti', validators=[DataRequired()])
    telp = StringField('Nomor Telepon', validators=[DataRequired()])
    jenis_cuti = RadioField('Jenis Cuti', choices=[
        ('c_tahun', 'Tahun'),
        ('c_besar', 'Besar'),
        ('c_sakit', 'Sakit'),
        ('c_lahir', 'Lahir'),
        ('c_penting', 'Penting'),
        ('c_luarnegara', 'Luar Negara')
    ], validators=[DataRequired()])
    alasan_cuti = TextAreaField('Alasan Cuti', validators=[DataRequired()])

class InputCutiForm(FlaskForm):
    nama = StringField('Nama', validators=[DataRequired()])
    nip = StringField('NIP', validators=[DataRequired()])
    jabatan = StringField('Jabatan', validators=[DataRequired()])
    gol_ruang = StringField('Gol. Ruang', validators=[DataRequired()])
    unit_kerja = StringField('Unit Kerja', validators=[DataRequired()])
    masa_kerja = StringField('Masa Kerja', validators=[DataRequired()])
    alamat = TextAreaField('Alamat', validators=[DataRequired()])
    no_suratmasuk = StringField('Nomor Surat Masuk', validators=[DataRequired()])
    tgl_ajuan_cuti = DateField('Tanggal Ajuan Cuti', validators=[DataRequired()])
    tanggal_cuti = DateField('Tanggal Mulai Cuti', validators=[DataRequired()])
    sampai_cuti = DateField('Tanggal Selesai Cuti', validators=[DataRequired()])
    telp = StringField('Nomor Telepon', validators=[DataRequired()])
    jenis_cuti = SelectField('Jenis Cuti', choices=[
        ('c_tahun', 'Tahun'),
        ('c_besar', 'Besar'),
        ('c_sakit', 'Sakit'),
        ('c_lahir', 'Lahir'),
        ('c_penting', 'Penting'),
        ('c_luarnegara', 'Luar Negara')
    ], validators=[DataRequired()])
    alasan_cuti = TextAreaField('Alasan Cuti', validators=[DataRequired()])
    submit = SubmitField('Simpan Cuti')

class SuratMasukForm(FlaskForm):
    tanggal_suratMasuk = DateField('Tanggal Surat', validators=[DataRequired()], format='%Y-%m-%d')
    pengirim_suratMasuk = StringField('Pengirim', validators=[DataRequired()])
    penerima_suratMasuk = StringField('Penerima', validators=[DataRequired()])
    nomor_suratMasuk = StringField('Nomor Surat', validators=[DataRequired()])
    isi_suratMasuk = TextAreaField('Isi Surat', validators=[DataRequired()])
    acara_suratMasuk = StringField('Acara', validators=[])
    tempat_suratMasuk = StringField('Tempat', validators=[])
    tanggal_acara_suratMasuk = DateField('Tanggal Acara', format='%Y-%m-%d', validators=[], default=None)
    jam_suratMasuk = StringField('Jam', validators=[])
    lampiran_suratMasuk = FileField('Lampiran Surat', validators=[FileAllowed(['jpg', 'png', 'jpeg', 'gif', 'pdf'], 'Image/PDF only!')])
    submit = SubmitField('Simpan Surat Masuk')
