#!/usr/bin/env python3
"""
Test script untuk debugging route pegawai
Jalankan: python test_pegawai_route.py
"""

import os
import sys

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from datetime import datetime

from app import create_app
from config.extensions import db
from config.models import Pegawai, User


def test_pegawai_route():
    """Test route pegawai dengan berbagai skenario"""

    app = create_app()

    with app.test_client() as client:
        with app.app_context():
            print("\n=== Testing Pegawai Route ===\n")

            # Test 1: Check if route exists
            print("Test 1: Check if /pegawai route exists (GET)")
            response = client.get("/pegawai")
            print(f"Status: {response.status_code}")
            print(f"Expected: 302 (redirect to login) or 200 (if logged in)")

            # Create test user if not exists
            print("\n\nTest 2: Create test admin user")
            admin = User.query.filter_by(email="admin@test.com").first()
            if not admin:
                admin = User(
                    email="admin@test.com",
                    role="admin",
                    is_admin=True,
                    is_approved=True,
                )
                admin.set_password("admin123")
                db.session.add(admin)
                db.session.commit()
                print("✓ Admin user created")
            else:
                print("✓ Admin user already exists")

            # Test 3: Login
            print("\n\nTest 3: Login as admin")
            response = client.post(
                "/login",
                data={"email": "admin@test.com", "password": "admin123"},
                follow_redirects=True,
            )
            print(f"Login status: {response.status_code}")

            # Test 4: Access pegawai form
            print("\n\nTest 4: Access pegawai form (GET)")
            response = client.get("/pegawai")
            print(f"Status: {response.status_code}")
            print(f"Expected: 200")
            if response.status_code == 200:
                print("✓ Form accessible")
                # Check if CSRF token exists
                if b"csrf_token" in response.data:
                    print("✓ CSRF token found in form")
                else:
                    print("✗ CSRF token NOT found in form")

            # Test 5: Submit form data
            print("\n\nTest 5: Submit pegawai data (POST)")

            # Get CSRF token from session
            with client.session_transaction() as sess:
                # Flask-WTF stores CSRF token in session
                pass

            test_data = {
                "nama": "Test Pegawai",
                "nip": f"TEST{datetime.now().strftime('%Y%m%d%H%M%S')}",
                "tanggal_lahir": "1990-01-01",
                "jenis_kelamin": "Laki-laki",
                "golongan": "III/a",
                "jabatan": "Staff Test",
                "agama": "Islam",
                "nomor_telpon": "081234567890",
                "riwayat_pendidikan": "S1 Test",
                "riwayat_pekerjaan": "Test Job",
            }

            print(f"Submitting data: {test_data}")
            response = client.post(
                "/pegawai",
                data=test_data,
                headers={"X-Requested-With": "XMLHttpRequest"},
                content_type="application/x-www-form-urlencoded",
            )

            print(f"Response status: {response.status_code}")
            print(f"Response headers: {dict(response.headers)}")
            print(f"Response data: {response.data.decode('utf-8')[:500]}")

            if response.status_code == 200:
                print("✓ POST successful")
                try:
                    import json

                    data = json.loads(response.data)
                    print(f"JSON response: {data}")
                    if data.get("success"):
                        print("✓✓ Pegawai successfully added!")
                    else:
                        print(f"✗ Error: {data.get('message')}")
                except:
                    print("✗ Response is not JSON")
            else:
                print(f"✗ POST failed with status {response.status_code}")

            # Test 6: Check if data exists in database
            print("\n\nTest 6: Check database")
            pegawai = Pegawai.query.filter_by(nip=test_data["nip"]).first()
            if pegawai:
                print(f"✓ Pegawai found in database:")
                print(f"  - Nama: {pegawai.nama}")
                print(f"  - NIP: {pegawai.nip}")
                print(f"  - Tanggal Lahir: {pegawai.tanggal_lahir}")

                # Clean up test data
                print("\n\nCleaning up test data...")
                db.session.delete(pegawai)
                db.session.commit()
                print("✓ Test data deleted")
            else:
                print("✗ Pegawai NOT found in database")

            # Test 7: Test CSRF validation
            print("\n\nTest 7: Test CSRF validation (submit without CSRF)")
            response = client.post(
                "/pegawai",
                data={"nama": "Test"},
                headers={"X-Requested-With": "XMLHttpRequest"},
            )
            print(f"Status without CSRF: {response.status_code}")
            print(f"Expected: 400 (CSRF validation error)")

            print("\n\n=== All Tests Complete ===\n")


if __name__ == "__main__":
    try:
        test_pegawai_route()
    except Exception as e:
        print(f"\n✗✗✗ ERROR: {e}")
        import traceback

        traceback.print_exc()
