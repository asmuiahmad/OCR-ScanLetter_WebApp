#!/usr/bin/env python3
"""
Test script to check if all imports work correctly
"""

try:
    print("Testing imports...")
    
    # Test basic Flask imports
    from flask import Flask
    print("✓ Flask import successful")
    
    # Test config imports
    from config.extensions import db
    print("✓ Extensions import successful")
    
    from config.models import SuratMasuk, SuratKeluar, Cuti
    print("✓ Models import successful")
    
    # Test route imports
    from config.surat_masuk_routes import surat_masuk_bp
    print("✓ Surat Masuk routes import successful")
    
    from config.cuti_routes import cuti_bp
    print("✓ Cuti routes import successful")
    
    # Test PDF generator
    from config.pdf_form_generator import CutiFormPDFGenerator
    print("✓ PDF Form Generator import successful")
    
    # Test app creation
    from app import create_app
    app = create_app()
    print("✓ App creation successful")
    
    print("\n🎉 All imports and app creation successful!")
    print("The application should now run without import errors.")
    
except ImportError as e:
    print(f"❌ Import Error: {e}")
except Exception as e:
    print(f"❌ General Error: {e}")