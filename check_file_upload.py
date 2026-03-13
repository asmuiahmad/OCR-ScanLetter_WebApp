#!/usr/bin/env python3
"""
Script untuk memeriksa file yang tersimpan di database
Digunakan untuk debugging upload file pada Surat Masuk
"""

import os
import sys
from datetime import datetime

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from app import create_app
from config.extensions import db
from config.models import SuratMasuk


def check_files_in_database():
    """Check all files stored in database"""
    app = create_app()

    with app.app_context():
        print("=" * 80)
        print("CHECKING FILES IN DATABASE")
        print("=" * 80)

        # Get all surat masuk
        surat_list = SuratMasuk.query.order_by(SuratMasuk.created_at.desc()).all()

        if not surat_list:
            print("\n❌ No Surat Masuk found in database")
            return

        print(f"\n✅ Found {len(surat_list)} Surat Masuk entries\n")

        files_count = 0
        no_files_count = 0

        for surat in surat_list:
            print(f"\n{'─' * 80}")
            print(f"ID: {surat.id_suratMasuk}")
            print(f"Nomor Surat: {surat.nomor_suratMasuk}")
            print(f"Pengirim: {surat.pengirim_suratMasuk}")
            print(
                f"Tanggal: {surat.tanggal_suratMasuk.strftime('%Y-%m-%d') if surat.tanggal_suratMasuk else 'N/A'}"
            )
            print(
                f"Created: {surat.created_at.strftime('%Y-%m-%d %H:%M:%S') if surat.created_at else 'N/A'}"
            )

            # Check file_suratMasuk
            if surat.file_suratMasuk:
                file_size = len(surat.file_suratMasuk)
                file_size_kb = file_size / 1024
                file_size_mb = file_size_kb / 1024

                print(f"📎 File Lampiran: ✅ ADA")
                print(
                    f"   Size: {file_size:,} bytes ({file_size_kb:.2f} KB / {file_size_mb:.2f} MB)"
                )

                # Try to detect file type from first few bytes
                magic_bytes = surat.file_suratMasuk[:8]
                if magic_bytes[:4] == b"\x89PNG":
                    print(f"   Type: PNG Image")
                elif magic_bytes[:2] == b"\xff\xd8":
                    print(f"   Type: JPEG Image")
                elif magic_bytes[:4] == b"%PDF":
                    print(f"   Type: PDF Document")
                else:
                    print(f"   Type: Unknown (magic bytes: {magic_bytes.hex()})")

                files_count += 1
            else:
                print(f"📎 File Lampiran: ❌ TIDAK ADA")
                no_files_count += 1

            # Check gambar_suratMasuk (OCR image)
            if surat.gambar_suratMasuk:
                gambar_size = len(surat.gambar_suratMasuk)
                gambar_size_kb = gambar_size / 1024
                print(f"🖼️  Gambar OCR: ✅ ADA ({gambar_size_kb:.2f} KB)")
            else:
                print(f"🖼️  Gambar OCR: ❌ TIDAK ADA")

        print(f"\n{'=' * 80}")
        print(f"SUMMARY")
        print(f"{'=' * 80}")
        print(f"Total Surat: {len(surat_list)}")
        print(f"With Files: {files_count} ({files_count / len(surat_list) * 100:.1f}%)")
        print(
            f"Without Files: {no_files_count} ({no_files_count / len(surat_list) * 100:.1f}%)"
        )
        print(f"{'=' * 80}\n")


def check_latest_surat():
    """Check only the latest surat masuk"""
    app = create_app()

    with app.app_context():
        print("=" * 80)
        print("LATEST SURAT MASUK")
        print("=" * 80)

        latest = SuratMasuk.query.order_by(SuratMasuk.created_at.desc()).first()

        if not latest:
            print("\n❌ No Surat Masuk found")
            return

        print(f"\nID: {latest.id_suratMasuk}")
        print(f"Nomor Surat: {latest.nomor_suratMasuk}")
        print(f"Pengirim: {latest.pengirim_suratMasuk}")
        print(f"Penerima: {latest.penerima_suratMasuk}")
        print(
            f"Tanggal: {latest.tanggal_suratMasuk.strftime('%Y-%m-%d') if latest.tanggal_suratMasuk else 'N/A'}"
        )
        print(
            f"Created: {latest.created_at.strftime('%Y-%m-%d %H:%M:%S') if latest.created_at else 'N/A'}"
        )
        print(f"Status: {latest.status_suratMasuk}")

        print(f"\n{'─' * 80}")
        print("FILE INFORMATION")
        print(f"{'─' * 80}")

        if latest.file_suratMasuk:
            file_size = len(latest.file_suratMasuk)
            file_size_kb = file_size / 1024
            file_size_mb = file_size_kb / 1024

            print(f"📎 File Lampiran: ✅ TERSIMPAN")
            print(f"   Size: {file_size:,} bytes")
            print(f"   Size: {file_size_kb:.2f} KB")
            print(f"   Size: {file_size_mb:.2f} MB")

            # Detect file type
            magic_bytes = latest.file_suratMasuk[:16]
            print(f"   Magic bytes: {magic_bytes.hex()}")

            if magic_bytes[:4] == b"\x89PNG":
                print(f"   Detected Type: PNG Image")
            if magic_bytes[:2] == b"\xff\xd8":
                print(f"   Detected Type: JPEG Image")
            elif magic_bytes[:4] == b"%PDF":
                print(f"   Detected Type: PDF Document")
            else:
                print(f"   Detected Type: Unknown")
        else:
            print(f"📎 File Lampiran: ❌ TIDAK TERSIMPAN")

        if latest.gambar_suratMasuk:
            gambar_size = len(latest.gambar_suratMasuk)
            gambar_size_kb = gambar_size / 1024
            print(f"\n🖼️  Gambar OCR: ✅ TERSIMPAN ({gambar_size_kb:.2f} KB)")
        else:
            print(f"\n🖼️  Gambar OCR: ❌ TIDAK TERSIMPAN")

        print(f"\n{'=' * 80}\n")


def export_file(surat_id, output_dir="exported_files"):
    """Export file from database to filesystem"""
    app = create_app()

    with app.app_context():
        surat = SuratMasuk.query.get(surat_id)

        if not surat:
            print(f"❌ Surat with ID {surat_id} not found")
            return

        if not surat.file_suratMasuk:
            print(f"❌ Surat ID {surat_id} has no file attached")
            return

        # Create output directory
        os.makedirs(output_dir, exist_ok=True)

        # Detect file extension
        magic_bytes = surat.file_suratMasuk[:4]
        if magic_bytes == b"\x89PNG":
            ext = "png"
        elif magic_bytes[:2] == b"\xff\xd8":
            ext = "jpg"
        elif magic_bytes == b"%PDF":
            ext = "pdf"
        else:
            ext = "bin"

        # Generate filename
        filename = f"surat_{surat_id}_{surat.nomor_suratMasuk.replace('/', '_')}.{ext}"
        filepath = os.path.join(output_dir, filename)

        # Write file
        with open(filepath, "wb") as f:
            f.write(surat.file_suratMasuk)

        print(f"✅ File exported successfully:")
        print(f"   Path: {filepath}")
        print(f"   Size: {len(surat.file_suratMasuk)} bytes")


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Check file uploads in database")
    parser.add_argument("--all", action="store_true", help="Check all surat masuk")
    parser.add_argument(
        "--latest", action="store_true", help="Check latest surat masuk"
    )
    parser.add_argument(
        "--export", type=int, metavar="ID", help="Export file from surat with given ID"
    )
    parser.add_argument(
        "--output",
        type=str,
        default="exported_files",
        help="Output directory for export",
    )

    args = parser.parse_args()

    if args.all:
        check_files_in_database()
    elif args.export:
        export_file(args.export, args.output)
    else:
        # Default: check latest
        check_latest_surat()

    print("\nUsage examples:")
    print("  python check_file_upload.py              # Check latest surat")
    print("  python check_file_upload.py --all        # Check all surat")
    print("  python check_file_upload.py --export 5   # Export file from surat ID 5")
