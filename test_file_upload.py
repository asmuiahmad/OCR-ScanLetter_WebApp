#!/usr/bin/env python3
"""
Script untuk test upload file pada Input Surat Masuk dan Surat Keluar
Verifikasi apakah file benar-benar tersimpan ke database
"""

import os
import sys
from io import BytesIO

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from datetime import datetime

from app import create_app
from config.extensions import db
from config.models import SuratKeluar, SuratMasuk


def create_test_image(format="JPEG"):
    """Create a simple test image in memory"""
    try:
        from PIL import Image, ImageDraw

        # Create a simple image
        img = Image.new("RGB", (200, 200), color="white")
        draw = ImageDraw.Draw(img)
        draw.rectangle([50, 50, 150, 150], fill="blue", outline="black", width=2)
        draw.text((70, 90), "TEST", fill="white")

        # Save to BytesIO
        output = BytesIO()
        img.save(output, format=format)
        output.seek(0)
        return output.read()
    except ImportError:
        print("⚠️  PIL/Pillow not installed. Using dummy data.")
        # Return dummy JPEG header + minimal data
        if format == "JPEG":
            return b"\xff\xd8\xff\xe0" + b"\x00" * 100 + b"\xff\xd9"
        elif format == "PNG":
            return b"\x89PNG\r\n\x1a\n" + b"\x00" * 100
        elif format == "PDF":
            return b"%PDF-1.4\n" + b"\x00" * 100 + b"%%EOF"
        else:
            return b"\x00" * 100


def test_surat_masuk_file_upload():
    """Test upload file untuk Surat Masuk"""
    print("\n" + "=" * 80)
    print("TEST: UPLOAD FILE - SURAT MASUK")
    print("=" * 80)

    app = create_app()

    with app.app_context():
        try:
            # Create test image data
            print("\n1. Creating test JPEG image...")
            test_file_data = create_test_image("JPEG")
            print(f"   ✅ Test image created: {len(test_file_data)} bytes")

            # Create new Surat Masuk with file
            print("\n2. Creating Surat Masuk with file...")
            new_surat = SuratMasuk(
                tanggal_suratMasuk=datetime.now(),
                pengirim_suratMasuk="Test Pengirim",
                penerima_suratMasuk="Test Penerima",
                nomor_suratMasuk="TEST/001/2024",
                isi_suratMasuk="Test isi surat untuk verifikasi upload file",
                kode_suratMasuk="TEST",
                jenis_suratMasuk="Test",
                status_suratMasuk="pending",
                file_suratMasuk=test_file_data,  # ✅ Upload file di sini
                created_at=datetime.utcnow(),
            )

            db.session.add(new_surat)
            db.session.commit()
            print(f"   ✅ Surat Masuk created with ID: {new_surat.id_suratMasuk}")

            # Verify file was saved
            print("\n3. Verifying file in database...")
            db.session.refresh(new_surat)

            if new_surat.file_suratMasuk:
                file_size = len(new_surat.file_suratMasuk)
                file_size_kb = file_size / 1024
                print(f"   ✅ File TERSIMPAN!")
                print(f"   📎 File Size: {file_size:,} bytes ({file_size_kb:.2f} KB)")

                # Check magic bytes
                magic_bytes = new_surat.file_suratMasuk[:4]
                if magic_bytes[:2] == b"\xff\xd8":
                    print(f"   📄 File Type: JPEG")
                elif magic_bytes == b"\x89PNG":
                    print(f"   📄 File Type: PNG")
                elif magic_bytes == b"%PDF":
                    print(f"   📄 File Type: PDF")
                else:
                    print(f"   📄 File Type: Unknown (magic: {magic_bytes.hex()})")

                print("\n" + "=" * 80)
                print("RESULT: ✅ SURAT MASUK FILE UPLOAD - SUCCESS")
                print("=" * 80)
                return True
            else:
                print(f"   ❌ File TIDAK TERSIMPAN!")
                print("\n" + "=" * 80)
                print("RESULT: ❌ SURAT MASUK FILE UPLOAD - FAILED")
                print("=" * 80)
                return False

        except Exception as e:
            print(f"\n❌ Error during test: {str(e)}")
            print(f"   Type: {type(e).__name__}")
            import traceback

            traceback.print_exc()
            return False


def test_surat_keluar_image_upload():
    """Test upload gambar untuk Surat Keluar"""
    print("\n" + "=" * 80)
    print("TEST: UPLOAD IMAGE - SURAT KELUAR")
    print("=" * 80)

    app = create_app()

    with app.app_context():
        try:
            # Create test image data
            print("\n1. Creating test PNG image...")
            test_image_data = create_test_image("PNG")
            print(f"   ✅ Test image created: {len(test_image_data)} bytes")

            # Create new Surat Keluar with image
            print("\n2. Creating Surat Keluar with image...")
            new_surat = SuratKeluar(
                tanggal_suratKeluar=datetime.now(),
                pengirim_suratKeluar="Test Pengirim",
                penerima_suratKeluar="Test Penerima",
                nomor_suratKeluar="TEST/001/2024",
                kode_suratKeluar="TEST",
                jenis_suratKeluar="Test",
                isi_suratKeluar="Test isi surat untuk verifikasi upload gambar",
                gambar_suratKeluar=test_image_data,  # ✅ Upload gambar di sini
                status_suratKeluar="pending",
                created_at=datetime.utcnow(),
            )

            db.session.add(new_surat)
            db.session.commit()
            print(f"   ✅ Surat Keluar created with ID: {new_surat.id_suratKeluar}")

            # Verify image was saved
            print("\n3. Verifying image in database...")
            db.session.refresh(new_surat)

            if new_surat.gambar_suratKeluar:
                image_size = len(new_surat.gambar_suratKeluar)
                image_size_kb = image_size / 1024
                print(f"   ✅ Gambar TERSIMPAN!")
                print(
                    f"   🖼️  Image Size: {image_size:,} bytes ({image_size_kb:.2f} KB)"
                )

                # Check magic bytes
                magic_bytes = new_surat.gambar_suratKeluar[:4]
                if magic_bytes[:2] == b"\xff\xd8":
                    print(f"   📄 Image Type: JPEG")
                elif magic_bytes == b"\x89PNG":
                    print(f"   📄 Image Type: PNG")
                else:
                    print(f"   📄 Image Type: Unknown (magic: {magic_bytes.hex()})")

                print("\n" + "=" * 80)
                print("RESULT: ✅ SURAT KELUAR IMAGE UPLOAD - SUCCESS")
                print("=" * 80)
                return True
            else:
                print(f"   ❌ Gambar TIDAK TERSIMPAN!")
                print("\n" + "=" * 80)
                print("RESULT: ❌ SURAT KELUAR IMAGE UPLOAD - FAILED")
                print("=" * 80)
                return False

        except Exception as e:
            print(f"\n❌ Error during test: {str(e)}")
            print(f"   Type: {type(e).__name__}")
            import traceback

            traceback.print_exc()
            return False


def check_existing_files():
    """Check existing files in database"""
    print("\n" + "=" * 80)
    print("CHECKING EXISTING FILES IN DATABASE")
    print("=" * 80)

    app = create_app()

    with app.app_context():
        # Check Surat Masuk
        total_masuk = SuratMasuk.query.count()
        with_files = SuratMasuk.query.filter(
            SuratMasuk.file_suratMasuk.isnot(None)
        ).count()
        print(f"\n📥 SURAT MASUK:")
        print(f"   Total: {total_masuk}")
        print(f"   With Files: {with_files}")
        print(f"   Without Files: {total_masuk - with_files}")

        # Check Surat Keluar
        total_keluar = SuratKeluar.query.count()
        with_images = SuratKeluar.query.filter(
            SuratKeluar.gambar_suratKeluar.isnot(None)
        ).count()
        print(f"\n📤 SURAT KELUAR:")
        print(f"   Total: {total_keluar}")
        print(f"   With Images: {with_images}")
        print(f"   Without Images: {total_keluar - with_images}")


def main():
    """Main test function"""
    print("\n" + "🔬" + "=" * 78 + "🔬")
    print("FILE UPLOAD TEST SUITE")
    print("🔬" + "=" * 78 + "🔬")

    # Check existing files first
    check_existing_files()

    # Run tests
    results = []

    print("\n\n📋 RUNNING TESTS...")
    print("-" * 80)

    # Test 1: Surat Masuk
    result1 = test_surat_masuk_file_upload()
    results.append(("Surat Masuk File Upload", result1))

    # Test 2: Surat Keluar
    result2 = test_surat_keluar_image_upload()
    results.append(("Surat Keluar Image Upload", result2))

    # Summary
    print("\n\n" + "=" * 80)
    print("TEST SUMMARY")
    print("=" * 80)

    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} - {test_name}")

    passed = sum(1 for _, result in results if result)
    total = len(results)

    print("\n" + "-" * 80)
    print(f"Total: {passed}/{total} tests passed")

    if passed == total:
        print("\n🎉 ALL TESTS PASSED! File upload berfungsi dengan baik.")
    else:
        print("\n⚠️  SOME TESTS FAILED! Ada masalah dengan file upload.")

    print("=" * 80 + "\n")

    # Check files after test
    print("\nCHECKING FILES AFTER TEST:")
    check_existing_files()

    print("\n" + "=" * 80)
    print("VERIFICATION:")
    print("Run 'python check_file_upload.py --all' to see all files")
    print("=" * 80 + "\n")


if __name__ == "__main__":
    main()
