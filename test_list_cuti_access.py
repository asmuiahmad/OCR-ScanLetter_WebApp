"""
Test script to debug list_cuti access issue
"""

from flask import url_for

from app import app
from config.models import Cuti, User


def test_list_cuti_access():
    """Test accessing list_cuti_v2 endpoint"""
    print("=" * 80)
    print("Testing List Cuti Access")
    print("=" * 80)

    with app.app_context():
        # Check if route exists
        print("\n1. Checking route registration...")
        with app.test_request_context():
            try:
                url = url_for("ocr_cuti_v2.list_cuti_v2")
                print(f"   ✓ Route exists: {url}")
            except Exception as e:
                print(f"   ✗ Route not found: {e}")
                return

        # Check database
        print("\n2. Checking database...")
        try:
            cuti_count = Cuti.query.count()
            print(f"   ✓ Total cuti records: {cuti_count}")

            if cuti_count > 0:
                sample = Cuti.query.first()
                print(
                    f"   ✓ Sample record: ID={sample.id_cuti}, Nama={sample.nama}, Status={sample.status_cuti}"
                )
        except Exception as e:
            print(f"   ✗ Database error: {e}")
            return

        # Check users
        print("\n3. Checking users...")
        try:
            users = User.query.all()
            print(f"   ✓ Total users: {len(users)}")
            for user in users:
                print(f"      - {user.email} (role: {user.role})")
        except Exception as e:
            print(f"   ✗ User query error: {e}")
            return

        # Test with admin user
        print("\n4. Testing access with admin user...")
        admin = User.query.filter_by(role="admin").first()
        if not admin:
            print("   ✗ No admin user found")
            return

        print(f"   Using user: {admin.email}")

        with app.test_client() as client:
            # Test login
            print("\n5. Testing login...")
            login_response = client.post(
                "/login",
                data={
                    "email": admin.email,
                    "password": "admin123",  # Default password
                    "remember": False,
                },
                follow_redirects=False,
            )

            print(f"   Login status: {login_response.status_code}")

            # Test access to list_cuti_v2
            print("\n6. Testing access to /cuti-v2/list...")
            response = client.get("/cuti-v2/list", follow_redirects=False)
            print(f"   Status code: {response.status_code}")

            if response.status_code == 302:
                print(f"   Redirect to: {response.location}")
                print("   ✗ Access denied - redirected to login")

                # Try following redirect
                print("\n7. Following redirect chain...")
                response2 = client.get("/cuti-v2/list", follow_redirects=True)
                print(f"   Final status: {response2.status_code}")
                print(f"   Final URL: {response2.request.path}")

            elif response.status_code == 200:
                print("   ✓ Access granted!")
                print(f"   Response length: {len(response.data)} bytes")

                # Check if template rendered correctly
                if b"Daftar Permohonan Cuti" in response.data:
                    print("   ✓ Template rendered correctly")
                else:
                    print("   ⚠ Template may have issues")

            else:
                print(f"   ✗ Unexpected status code: {response.status_code}")
                print(f"   Response: {response.data[:500]}")

        # Test direct function call
        print("\n8. Testing direct function call...")
        try:
            from unittest.mock import Mock

            from flask import Flask

            from config.ocr_cuti_v2 import list_cuti_v2

            with app.test_request_context("/cuti-v2/list"):
                # Mock current_user
                from flask_login import current_user

                print(f"   Current user authenticated: {current_user.is_authenticated}")

        except Exception as e:
            print(f"   Error in direct call: {e}")
            import traceback

            traceback.print_exc()

        print("\n" + "=" * 80)
        print("Test completed!")
        print("=" * 80)


if __name__ == "__main__":
    test_list_cuti_access()
