"""
Migration script to swap surat_keluar and surat_masuk tables and their columns.
"""
from alembic import op
import sqlalchemy as sa

def upgrade():
    # Rename surat_keluar to surat_masuk_temp
    op.rename_table('surat_keluar', 'surat_masuk_temp')
    # Rename surat_masuk to surat_keluar
    op.rename_table('surat_masuk', 'surat_keluar')
    # Rename surat_masuk_temp to surat_masuk
    op.rename_table('surat_masuk_temp', 'surat_masuk')

    # SuratKeluar (sekarang surat_masuk): ganti kolom *_suratKeluar menjadi *_suratMasuk
    with op.batch_alter_table('surat_masuk') as batch_op:
        batch_op.alter_column('nomor_suratKeluar', new_column_name='nomor_suratMasuk')
        batch_op.alter_column('tanggal_suratKeluar', new_column_name='tanggal_suratMasuk')
        batch_op.alter_column('pengirim_suratKeluar', new_column_name='pengirim_suratMasuk')
        batch_op.alter_column('penerima_suratKeluar', new_column_name='penerima_suratMasuk')
        batch_op.alter_column('kode_suratKeluar', new_column_name='kode_suratMasuk')
        batch_op.alter_column('jenis_suratKeluar', new_column_name='jenis_suratMasuk')
        batch_op.alter_column('isi_suratKeluar', new_column_name='isi_suratMasuk')
        batch_op.alter_column('gambar_suratKeluar', new_column_name='gambar_suratMasuk')
        batch_op.alter_column('ocr_accuracy_suratKeluar', new_column_name='ocr_accuracy_suratMasuk')
        batch_op.alter_column('initial_full_letter_number', new_column_name='initial_full_letter_number')
        batch_op.alter_column('initial_pengirim_suratKeluar', new_column_name='initial_pengirim_suratMasuk')
        batch_op.alter_column('initial_penerima_suratKeluar', new_column_name='initial_penerima_suratMasuk')
        batch_op.alter_column('initial_isi_suratKeluar', new_column_name='initial_isi_suratMasuk')
        batch_op.alter_column('initial_nomor_suratKeluar', new_column_name='initial_nomor_suratMasuk')
        batch_op.alter_column('status_suratKeluar', new_column_name='status_suratMasuk')

    # SuratMasuk (sekarang surat_keluar): ganti kolom *_suratMasuk menjadi *_suratKeluar
    with op.batch_alter_table('surat_keluar') as batch_op:
        batch_op.alter_column('nomor_suratMasuk', new_column_name='nomor_suratKeluar')
        batch_op.alter_column('tanggal_suratMasuk', new_column_name='tanggal_suratKeluar')
        batch_op.alter_column('pengirim_suratMasuk', new_column_name='pengirim_suratKeluar')
        batch_op.alter_column('penerima_suratMasuk', new_column_name='penerima_suratKeluar')
        batch_op.alter_column('isi_suratMasuk', new_column_name='isi_suratKeluar')
        batch_op.alter_column('gambar_suratMasuk', new_column_name='gambar_suratKeluar')
        batch_op.alter_column('file_suratMasuk', new_column_name='file_suratKeluar')
        batch_op.alter_column('ocr_accuracy_suratMasuk', new_column_name='ocr_accuracy_suratKeluar')
        batch_op.alter_column('initial_nomor_suratMasuk', new_column_name='initial_nomor_suratKeluar')
        batch_op.alter_column('initial_pengirim_suratMasuk', new_column_name='initial_pengirim_suratKeluar')
        batch_op.alter_column('initial_penerima_suratMasuk', new_column_name='initial_penerima_suratKeluar')
        batch_op.alter_column('initial_isi_suratMasuk', new_column_name='initial_isi_suratKeluar')
        batch_op.alter_column('acara_suratMasuk', new_column_name='acara_suratKeluar')
        batch_op.alter_column('tempat_suratMasuk', new_column_name='tempat_suratKeluar')
        batch_op.alter_column('tanggal_acara_suratMasuk', new_column_name='tanggal_acara_suratKeluar')
        batch_op.alter_column('jam_suratMasuk', new_column_name='jam_suratKeluar')
        batch_op.alter_column('status_suratMasuk', new_column_name='status_suratKeluar')

def downgrade():
    # Reverse the process
    with op.batch_alter_table('surat_masuk') as batch_op:
        batch_op.alter_column('nomor_suratMasuk', new_column_name='nomor_suratKeluar')
        batch_op.alter_column('tanggal_suratMasuk', new_column_name='tanggal_suratKeluar')
        batch_op.alter_column('pengirim_suratMasuk', new_column_name='pengirim_suratKeluar')
        batch_op.alter_column('penerima_suratMasuk', new_column_name='penerima_suratKeluar')
        batch_op.alter_column('kode_suratMasuk', new_column_name='kode_suratKeluar')
        batch_op.alter_column('jenis_suratMasuk', new_column_name='jenis_suratKeluar')
        batch_op.alter_column('isi_suratMasuk', new_column_name='isi_suratKeluar')
        batch_op.alter_column('gambar_suratMasuk', new_column_name='gambar_suratKeluar')
        batch_op.alter_column('ocr_accuracy_suratMasuk', new_column_name='ocr_accuracy_suratKeluar')
        batch_op.alter_column('initial_full_letter_number', new_column_name='initial_full_letter_number')
        batch_op.alter_column('initial_pengirim_suratMasuk', new_column_name='initial_pengirim_suratKeluar')
        batch_op.alter_column('initial_penerima_suratMasuk', new_column_name='initial_penerima_suratKeluar')
        batch_op.alter_column('initial_isi_suratMasuk', new_column_name='initial_isi_suratKeluar')
        batch_op.alter_column('initial_nomor_suratMasuk', new_column_name='initial_nomor_suratKeluar')
        batch_op.alter_column('status_suratMasuk', new_column_name='status_suratKeluar')

    with op.batch_alter_table('surat_keluar') as batch_op:
        batch_op.alter_column('nomor_suratKeluar', new_column_name='nomor_suratMasuk')
        batch_op.alter_column('tanggal_suratKeluar', new_column_name='tanggal_suratMasuk')
        batch_op.alter_column('pengirim_suratKeluar', new_column_name='pengirim_suratMasuk')
        batch_op.alter_column('penerima_suratKeluar', new_column_name='penerima_suratMasuk')
        batch_op.alter_column('isi_suratKeluar', new_column_name='isi_suratMasuk')
        batch_op.alter_column('gambar_suratKeluar', new_column_name='gambar_suratMasuk')
        batch_op.alter_column('file_suratKeluar', new_column_name='file_suratMasuk')
        batch_op.alter_column('ocr_accuracy_suratKeluar', new_column_name='ocr_accuracy_suratMasuk')
        batch_op.alter_column('initial_nomor_suratKeluar', new_column_name='initial_nomor_suratMasuk')
        batch_op.alter_column('initial_pengirim_suratKeluar', new_column_name='initial_pengirim_suratMasuk')
        batch_op.alter_column('initial_penerima_suratKeluar', new_column_name='initial_penerima_suratMasuk')
        batch_op.alter_column('initial_isi_suratKeluar', new_column_name='initial_isi_suratMasuk')
        batch_op.alter_column('acara_suratKeluar', new_column_name='acara_suratMasuk')
        batch_op.alter_column('tempat_suratKeluar', new_column_name='tempat_suratMasuk')
        batch_op.alter_column('tanggal_acara_suratKeluar', new_column_name='tanggal_acara_suratMasuk')
        batch_op.alter_column('jam_suratKeluar', new_column_name='jam_suratMasuk')
        batch_op.alter_column('status_suratKeluar', new_column_name='status_suratMasuk')

    # Rename surat_masuk to surat_masuk_temp
    op.rename_table('surat_masuk', 'surat_masuk_temp')
    # Rename surat_keluar to surat_masuk
    op.rename_table('surat_keluar', 'surat_masuk')
    # Rename surat_masuk_temp to surat_keluar
    op.rename_table('surat_masuk_temp', 'surat_keluar') 