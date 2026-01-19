#!/usr/bin/env python3
"""
Script untuk menambahkan kolom file_suratMasuk ke database
"""

from app import app
from config.extensions import db
import sqlite3

def add_file_column():
    with app.app_context():
        db_path = 'instance/app.db'
        
        try:
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            
            # Cek apakah kolom sudah ada
            cursor.execute("PRAGMA table_info(surat_masuk)")
            columns = [col[1] for col in cursor.fetchall()]
            
            if 'file_suratMasuk' in columns:
                print("✅ Kolom file_suratMasuk sudah ada")
                conn.close()
                return
            
            # Tambahkan kolom
            print("➕ Menambahkan kolom file_suratMasuk...")
            cursor.execute("""
                ALTER TABLE surat_masuk 
                ADD COLUMN file_suratMasuk BLOB
            """)
            
            conn.commit()
            conn.close()
            
            print("✅ Kolom file_suratMasuk berhasil ditambahkan!")
            
        except Exception as e:
            print(f"❌ Error: {str(e)}")
            import traceback
            traceback.print_exc()

if __name__ == '__main__':
    print("🔧 Menambahkan kolom file_suratMasuk ke database...")
    print("=" * 50)
    add_file_column()
    print("=" * 50)
    print("✅ Selesai!")
