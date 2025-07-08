from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, SelectField, DateField, TextAreaField, BooleanField
from wtforms.validators import DataRequired, Email
from flask_wtf.file import FileField, FileAllowed

class RegistrationForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired()])
    role = SelectField('Role', choices=[('karyawan', 'Karyawan'), ('pimpinan', 'Pimpinan'), ('admin', 'Admin')], validators=[DataRequired()])
    submit = SubmitField('Register')

class LoginForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired()])
    submit = SubmitField('Login')

class SuratMasukForm(FlaskForm):
    tanggal_suratMasuk = DateField('Tanggal Surat', validators=[DataRequired()], format='%Y-%m-%d')
    pengirim_suratMasuk = StringField('Pengirim', validators=[DataRequired()])
    penerima_suratMasuk = StringField('Penerima', validators=[DataRequired()])
    nomor_suratMasuk = StringField('Nomor Surat', validators=[DataRequired()])
    kode_suratMasuk = StringField('Kode Surat', validators=[DataRequired()])
    jenis_suratMasuk = StringField('Jenis Surat', validators=[DataRequired()])
    isi_suratMasuk = TextAreaField('Isi Surat', validators=[DataRequired()])
    image = FileField('Gambar Surat', validators=[FileAllowed(['jpg', 'png', 'jpeg', 'gif'], 'Image only!')])
    submit = SubmitField('Simpan Surat Masuk')

class OCRSuratMasukForm(FlaskForm):
    image = FileField('Upload Image', validators=[
        FileAllowed(['jpg', 'png', 'jpeg', 'webp'], 'Images only!')
    ])
    preprocess = BooleanField('Preprocessing')
    enhance_contrast = BooleanField('Enhance Contrast')
    submit = SubmitField('Process OCR')
