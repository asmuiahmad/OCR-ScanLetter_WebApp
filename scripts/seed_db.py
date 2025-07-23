import sys
import os
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__) + '/../'))
from config.extensions import db
from config.models import User, SuratMasuk, SuratKeluar
from werkzeug.security import generate_password_hash
from datetime import datetime, timedelta
from app import app

with app.app_context():
    # Buat user admin
    if not User.query.filter_by(email='admin@admin.com').first():
        admin = User(
            email='admin@admin.com',
            password=generate_password_hash('admin123'),
            is_admin=True,
            role='admin',
            is_approved=True,
            last_login=datetime.now(),
            login_count=1
        )
        db.session.add(admin)
        print('Admin user created.')
    else:
        print('Admin user already exists.')

    # Dummy Surat Masuk
    for i in range(1, 6):
        surat = SuratMasuk(
            full_letter_number=f'SM-{i:03d}',
            nomor_suratMasuk=f'SM-{i:03d}',
            tanggal_suratMasuk=datetime.now() - timedelta(days=i*2),
            pengirim_suratMasuk=f'Pengirim {i}',
            penerima_suratMasuk=f'Penerima {i}',
            kode_suratMasuk=f'KODE{i}',
            jenis_suratMasuk='Umum',
            isi_suratMasuk=f'Isi surat masuk ke-{i}',
            status_suratMasuk='pending',
            created_at=datetime.now() - timedelta(days=i*2)
        )
        db.session.add(surat)
    print('Dummy Surat Masuk created.')

    # Dummy Surat Keluar
    for i in range(1, 6):
        surat = SuratKeluar(
            nomor_suratKeluar=f'SK-{i:03d}',
            tanggal_suratKeluar=datetime.now() - timedelta(days=i*3),
            pengirim_suratKeluar=f'Pengirim Keluar {i}',
            penerima_suratKeluar=f'Penerima Keluar {i}',
            isi_suratKeluar=f'Isi surat keluar ke-{i}',
            status_suratKeluar='pending',
            created_at=datetime.now() - timedelta(days=i*3)
        )
        db.session.add(surat)
    print('Dummy Surat Keluar created.')

    db.session.commit()
    print('Database seeded successfully.') 