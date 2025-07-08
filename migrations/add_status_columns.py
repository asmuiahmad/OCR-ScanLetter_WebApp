from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import Column, String

def upgrade(migrate_engine):
    """Add status columns to surat_masuk and surat_keluar tables."""
    from sqlalchemy import MetaData, Table, Column, String
    
    # Reflect the existing database
    meta = MetaData()
    meta.bind = migrate_engine
    
    # Surat Masuk table
    surat_masuk = Table('surat_masuk', meta, autoload_with=migrate_engine)
    
    # Check if column exists before adding
    if 'status_suratMasuk' not in surat_masuk.columns:
        status_suratMasuk = Column('status_suratMasuk', String(20), nullable=False, server_default='pending')
        status_suratMasuk.create(surat_masuk)
    
    # Surat Keluar table
    surat_keluar = Table('surat_keluar', meta, autoload_with=migrate_engine)
    
    # Check if column exists before adding
    if 'status_suratKeluar' not in surat_keluar.columns:
        status_suratKeluar = Column('status_suratKeluar', String(20), nullable=False, server_default='pending')
        status_suratKeluar.create(surat_keluar)

def downgrade(migrate_engine):
    """Remove status columns from surat_masuk and surat_keluar tables."""
    from sqlalchemy import MetaData, Table
    
    meta = MetaData()
    meta.bind = migrate_engine
    
    # Surat Masuk table
    surat_masuk = Table('surat_masuk', meta, autoload_with=migrate_engine)
    
    # Drop column if it exists
    if 'status_suratMasuk' in surat_masuk.columns:
        surat_masuk.drop_column('status_suratMasuk')
    
    # Surat Keluar table
    surat_keluar = Table('surat_keluar', meta, autoload_with=migrate_engine)
    
    # Drop column if it exists
    if 'status_suratKeluar' in surat_keluar.columns:
        surat_keluar.drop_column('status_suratKeluar') 