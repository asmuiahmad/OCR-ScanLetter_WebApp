#!/usr/bin/env python3
"""
Script to update OCR accuracy for all existing documents in the database
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app import app, db
from config.models import SuratKeluar, SuratMasuk
from config.ocr_utils import calculate_overall_ocr_accuracy

def update_all_ocr_accuracy():
    """
    Update OCR accuracy for all existing documents
    """
    with app.app_context():
        try:
            print("🔄 Updating OCR accuracy for all documents...")
            
            # Update Surat Masuk
            surat_keluar_list = SuratKeluar.query.all()
            print(f"📥 Found {len(surat_keluar_list)} Surat Masuk documents")
            
            for i, surat in enumerate(surat_keluar_list, 1):
                try:
                    accuracy = calculate_overall_ocr_accuracy(surat, 'suratKeluar')
                    surat.ocr_accuracy_suratKeluar = accuracy
                    print(f"  [{i}/{len(surat_keluar_list)}] Surat Masuk ID {surat.id_suratKeluar}: {accuracy}%")
                except Exception as e:
                    print(f"  ❌ Error updating Surat Masuk ID {surat.id_suratKeluar}: {str(e)}")
            
            # Update Surat Keluar
            surat_masuk_list = SuratMasuk.query.all()
            print(f"📤 Found {len(surat_masuk_list)} Surat Keluar documents")
            
            for i, surat in enumerate(surat_masuk_list, 1):
                try:
                    accuracy = calculate_overall_ocr_accuracy(surat, 'suratMasuk')
                    surat.ocr_accuracy_suratMasuk = accuracy
                    print(f"  [{i}/{len(surat_masuk_list)}] Surat Keluar ID {surat.id_suratMasuk}: {accuracy}%")
                except Exception as e:
                    print(f"  ❌ Error updating Surat Keluar ID {surat.id_suratMasuk}: {str(e)}")
            
            # Commit all changes
            db.session.commit()
            print("✅ Successfully updated OCR accuracy for all documents!")
            
            # Print summary statistics
            accuracy_masuk = [s.ocr_accuracy_suratKeluar for s in surat_keluar_list if s.ocr_accuracy_suratKeluar is not None]
            accuracy_keluar = [s.ocr_accuracy_suratMasuk for s in surat_masuk_list if s.ocr_accuracy_suratMasuk is not None]
            
            if accuracy_masuk:
                avg_masuk = sum(accuracy_masuk) / len(accuracy_masuk)
                print(f"📊 Average OCR accuracy Surat Masuk: {avg_masuk:.2f}%")
            
            if accuracy_keluar:
                avg_keluar = sum(accuracy_keluar) / len(accuracy_keluar)
                print(f"📊 Average OCR accuracy Surat Keluar: {avg_keluar:.2f}%")
            
        except Exception as e:
            db.session.rollback()
            print(f"❌ Error updating OCR accuracy: {str(e)}")
            return False
    
    return True

if __name__ == "__main__":
    print("🚀 Starting OCR accuracy update...")
    success = update_all_ocr_accuracy()
    
    if success:
        print("🎉 OCR accuracy update completed successfully!")
    else:
        print("💥 OCR accuracy update failed!")
        sys.exit(1) 