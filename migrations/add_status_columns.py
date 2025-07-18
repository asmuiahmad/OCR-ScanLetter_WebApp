from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import Column, String

def upgrade(migrate_engine):
    """Add status columns to surat_keluar and surat_masuk tables."""
    from sqlalchemy import MetaData, Table, Column, String
    
    # Reflect the existing database
    meta = MetaData()
    meta.bind = migrate_engine
    
    # Surat Masuk table
    surat_keluar = Table('surat_keluar', meta, autoload_with=migrate_engine)
    
    # Check if column exists before adding
    if 'status_suratKeluar' not in surat_keluar.columns:
        status_suratKeluar = Column('status_suratKeluar', String(20), nullable=False, server_default='pending')
        status_suratKeluar.create(surat_keluar)
    
    # Surat Keluar table
    surat_masuk = Table('surat_masuk', meta, autoload_with=migrate_engine)
    
    # Check if column exists before adding
    if 'status_suratMasuk' not in surat_masuk.columns:
        status_suratMasuk = Column('status_suratMasuk', String(20), nullable=False, server_default='pending')
        status_suratMasuk.create(surat_masuk)

    # Tambahan field untuk digital signature dan file cuti
    cuti = Table('cuti', meta, autoload_with=migrate_engine)
    if 'qr_code' not in cuti.columns:
        qr_code_col = Column('qr_code', String, nullable=True)
        qr_code_col.create(cuti)
    if 'pdf_path' not in cuti.columns:
        pdf_path_col = Column('pdf_path', String, nullable=True)
        pdf_path_col.create(cuti)
    if 'docx_path' not in cuti.columns:
        docx_path_col = Column('docx_path', String, nullable=True)
        docx_path_col.create(cuti)

def downgrade(migrate_engine):
    """Remove status columns from surat_keluar and surat_masuk tables."""
    from sqlalchemy import MetaData, Table
    
    meta = MetaData()
    meta.bind = migrate_engine
    
    # Surat Masuk table
    surat_keluar = Table('surat_keluar', meta, autoload_with=migrate_engine)
    
    # Drop column if it exists
    if 'status_suratKeluar' in surat_keluar.columns:
        surat_keluar.drop_column('status_suratKeluar')
    
    # Surat Keluar table
    surat_masuk = Table('surat_masuk', meta, autoload_with=migrate_engine)
    
    # Drop column if it exists
    if 'status_suratMasuk' in surat_masuk.columns:
        surat_masuk.drop_column('status_suratMasuk') 
    # Tambahan: drop field cuti
    cuti = Table('cuti', meta, autoload_with=migrate_engine)
    if 'qr_code' in cuti.columns:
        cuti.drop_column('qr_code')
    if 'pdf_path' in cuti.columns:
        cuti.drop_column('pdf_path')
    if 'docx_path' in cuti.columns:
        cuti.drop_column('docx_path') 