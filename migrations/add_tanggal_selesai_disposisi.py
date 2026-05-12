"""
Migration script untuk menambahkan field tanggal_selesai ke tabel disposisi
Mengatasi error saat update status disposisi ke 'selesai'

Run dengan: python migrations/add_tanggal_selesai_disposisi.py
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app
from config.extensions import db
from sqlalchemy import text

def migrate():
    app = create_app()
    with app.app_context():
        print("🚀 Starting disposisi tanggal_selesai migration...")
        
        try:
            # Add tanggal_selesai column if not exists
            migration_sql = """
            ALTER TABLE disposisi 
            ADD COLUMN IF NOT EXISTS tanggal_selesai TIMESTAMP;
            """
            
            db.session.execute(text(migration_sql))
            db.session.commit()
            
            print("✅ Added tanggal_selesai column to disposisi table")
            print("🎉 Migration completed successfully!")
            
        except Exception as e:
            db.session.rollback()
            print(f"❌ Migration failed: {str(e)}")
            raise

if __name__ == "__main__":
    migrate()