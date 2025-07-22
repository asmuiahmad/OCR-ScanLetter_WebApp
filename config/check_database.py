#!/usr/bin/env python3
"""
Database check and fix script
"""
import os
import sqlite3
from config.extensions import db
from config.models import User, SuratKeluar, SuratMasuk, Pegawai, Cuti, UserLoginLog

def check_database():
    """Check database and add missing columns if needed"""
    basedir = os.path.abspath(os.path.dirname(__file__))
    instance_path = os.path.join(os.path.dirname(basedir), 'instance')
    db_path = os.path.join(instance_path, 'app.db')
    
    print(f"Checking database at: {db_path}")
    
    if not os.path.exists(db_path):
        print("Database file not found. Creating new database...")
        return False
    
    # Connect to SQLite database
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # Check if file_suratMasuk column exists
        cursor.execute("PRAGMA table_info(surat_masuk)")
        columns = [column[1] for column in cursor.fetchall()]
        
        if 'file_suratMasuk' not in columns:
            print("Adding file_suratMasuk column...")
            cursor.execute("ALTER TABLE surat_masuk ADD COLUMN file_suratMasuk BLOB")
            conn.commit()
            print("Column added successfully!")
        else:
            print("file_suratMasuk column already exists.")
        
        # Check if status columns exist
        if 'status_suratMasuk' not in columns:
            print("Adding status_suratMasuk column...")
            cursor.execute("ALTER TABLE surat_masuk ADD COLUMN status_suratMasuk VARCHAR(20) DEFAULT 'pending'")
            conn.commit()
            print("status_suratMasuk column added successfully!")
        else:
            print("status_suratMasuk column already exists.")
        
        # Check SuratKeluar table
        cursor.execute("PRAGMA table_info(surat_keluar)")
        surat_keluar_columns = [column[1] for column in cursor.fetchall()]
        
        if 'status_suratKeluar' not in surat_keluar_columns:
            print("Adding status_suratKeluar column...")
            cursor.execute("ALTER TABLE surat_keluar ADD COLUMN status_suratKeluar VARCHAR(20) DEFAULT 'approved'")
            conn.commit()
            print("status_suratKeluar column added successfully!")
        else:
            print("status_suratKeluar column already exists.")
        
        # Check UserLoginLog table
        cursor.execute("PRAGMA table_info(user_login_logs)")
        user_login_logs_columns = [column[1] for column in cursor.fetchall()]
        
        if not user_login_logs_columns:
            print("UserLoginLog table doesn't exist. It will be created when the app starts.")
        else:
            print("UserLoginLog table exists with columns:", user_login_logs_columns)
        
        print("Database check completed successfully!")
        return True
        
    except Exception as e:
        print(f"Error checking database: {e}")
        return False
    finally:
        conn.close()

def create_tables():
    """Create all tables if they don't exist"""
    from flask import Flask
    from config.extensions import db
    
    basedir = os.path.abspath(os.path.dirname(__file__))
    instance_path = os.path.join(os.path.dirname(basedir), 'instance')
    
    app = Flask(__name__)
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(instance_path, 'app.db')
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    
    db.init_app(app)
    
    with app.app_context():
        db.create_all()
        print("All tables created successfully!")

if __name__ == "__main__":
    print("Checking and fixing database...")
    
    # First try to check and fix existing database
    if not check_database():
        print("Creating new database with all tables...")
        create_tables()
    
    print("Database setup completed!")