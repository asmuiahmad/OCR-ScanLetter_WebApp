#!/usr/bin/env python3
"""
Script untuk menginstall sistem persetujuan cuti dengan tanda tangan digital
"""

import os
import sys
import subprocess
from flask import Flask
from config.extensions import db
from config.models import Cuti

def install_dependencies():
    """Install dependencies yang diperlukan"""
    print("📦 Installing dependencies...")
    
    dependencies = [
        'qrcode==8.0',
        'reportlab==4.2.5', 
        'pdf2image==1.17.0'
    ]
    
    for dep in dependencies:
        try:
            print(f"Installing {dep}...")
            subprocess.check_call([sys.executable, '-m', 'pip', 'install', dep])
            print(f"✅ {dep} installed successfully")
        except subprocess.CalledProcessError as e:
            print(f"❌ Failed to install {dep}: {e}")
            return False
    
    return True

def create_directories():
    """Buat direktori yang diperlukan"""
    print("📁 Creating directories...")
    
    directories = [
        'static/signatures',
        'static/pdf_cuti',
        'static/qr_codes'
    ]
    
    for directory in directories:
        os.makedirs(directory, exist_ok=True)
        print(f"✅ Created directory: {directory}")

def run_database_migration():
    """Jalankan migrasi database"""
    print("🗄️ Running database migration...")
    
    try:
        # Import app untuk context
        from app import create_app
        app = create_app()
        
        with app.app_context():
            # Create all tables
            db.create_all()
            print("✅ Database tables created successfully")
            
            # Check if Cuti table exists and has required columns
            inspector = db.inspect(db.engine)
            if 'cuti' in inspector.get_table_names():
                columns = [col['name'] for col in inspector.get_columns('cuti')]
                required_columns = ['qr_code', 'pdf_path', 'docx_path']
                
                missing_columns = [col for col in required_columns if col not in columns]
                if missing_columns:
                    print(f"⚠️ Missing columns in cuti table: {missing_columns}")
                    print("Please run the following SQL commands manually:")
                    for col in missing_columns:
                        if col == 'qr_code':
                            print(f"ALTER TABLE cuti ADD COLUMN {col} TEXT;")
                        else:
                            print(f"ALTER TABLE cuti ADD COLUMN {col} TEXT;")
                else:
                    print("✅ All required columns exist in cuti table")
            else:
                print("✅ Cuti table created with all required columns")
                
    except Exception as e:
        print(f"❌ Database migration failed: {e}")
        return False
    
    return True

def test_system():
    """Test sistem tanda tangan digital"""
    print("🧪 Testing digital signature system...")
    
    try:
        from config.digital_signature import DigitalSignature
        
        # Test QR code generation
        digital_sig = DigitalSignature()
        print("✅ Digital signature system imported successfully")
        
        # Test directories
        if os.path.exists('static/signatures') and os.path.exists('static/pdf_cuti'):
            print("✅ Required directories exist")
        else:
            print("❌ Required directories missing")
            return False
            
        return True
        
    except ImportError as e:
        print(f"❌ Failed to import digital signature system: {e}")
        return False
    except Exception as e:
        print(f"❌ System test failed: {e}")
        return False

def main():
    """Main installation function"""
    print("🚀 Installing Sistem Persetujuan Cuti dengan Tanda Tangan Digital")
    print("=" * 60)
    
    # Step 1: Install dependencies
    if not install_dependencies():
        print("❌ Installation failed at dependency installation")
        return False
    
    # Step 2: Create directories
    create_directories()
    
    # Step 3: Run database migration
    if not run_database_migration():
        print("❌ Installation failed at database migration")
        return False
    
    # Step 4: Test system
    if not test_system():
        print("❌ Installation failed at system testing")
        return False
    
    print("\n" + "=" * 60)
    print("✅ INSTALLATION COMPLETED SUCCESSFULLY!")
    print("\n📋 Fitur yang telah diinstall:")
    print("   • Sistem persetujuan cuti dengan approval pimpinan")
    print("   • Tanda tangan digital otomatis dengan QR code")
    print("   • Export PDF surat persetujuan cuti")
    print("   • Verifikasi digital signature")
    print("   • Menu navigasi untuk manajemen cuti")
    
    print("\n🔗 URL yang tersedia:")
    print("   • Input Cuti Baru: /cuti/")
    print("   • Daftar Permohonan Cuti: /cuti/list")
    print("   • Approve Cuti: /cuti/approve/<id>")
    print("   • Download PDF: /cuti/download_pdf/<id>")
    print("   • Verifikasi Signature: /cuti/verify/<hash>")
    
    print("\n👥 Role yang dapat mengakses:")
    print("   • Karyawan: Input cuti, lihat status cuti sendiri")
    print("   • Pimpinan/Admin: Approve/reject cuti, download PDF")
    
    print("\n🎯 Cara menggunakan:")
    print("   1. Login sebagai karyawan")
    print("   2. Pilih menu 'Manajemen Cuti' > 'Input Cuti Baru'")
    print("   3. Upload formulir cuti atau input manual")
    print("   4. Login sebagai pimpinan untuk approve")
    print("   5. Setelah approve, QR code dan PDF otomatis dibuat")
    print("   6. Scan QR code untuk verifikasi digital signature")
    
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)