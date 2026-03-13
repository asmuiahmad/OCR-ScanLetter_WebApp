#!/usr/bin/env python
"""
Quick Diagnosis Script for List Cuti Access Issues
Run this script to quickly identify why the list_cuti page is not accessible
"""

import sys
from datetime import datetime


def print_header(title):
    """Print formatted header"""
    print("\n" + "=" * 80)
    print(f" {title}")
    print("=" * 80)


def print_status(message, status="info"):
    """Print colored status message"""
    symbols = {"success": "✓", "error": "✗", "warning": "⚠", "info": "ℹ"}
    print(f"{symbols.get(status, 'ℹ')} {message}")


def check_imports():
    """Check if all required imports are available"""
    print_header("1. Checking Imports")

    required_modules = [
        ("flask", "Flask"),
        ("flask_login", "Flask-Login"),
        ("flask_sqlalchemy", "Flask-SQLAlchemy"),
        ("config.models", "Models"),
        ("config.ocr_cuti_v2", "OCR Cuti V2 Blueprint"),
    ]

    all_ok = True
    for module, name in required_modules:
        try:
            __import__(module)
            print_status(f"{name} - OK", "success")
        except ImportError as e:
            print_status(f"{name} - FAILED: {e}", "error")
            all_ok = False

    return all_ok


def check_database():
    """Check database connectivity and data"""
    print_header("2. Checking Database")

    try:
        from app import app
        from config.models import Cuti, User

        with app.app_context():
            # Check Cuti table
            try:
                cuti_count = Cuti.query.count()
                print_status(f"Cuti table accessible - {cuti_count} records", "success")

                if cuti_count > 0:
                    sample = Cuti.query.first()
                    print_status(
                        f"Sample record: ID={sample.id_cuti}, Nama={sample.nama}, Status={sample.status_cuti}",
                        "info",
                    )
                else:
                    print_status("No cuti records in database", "warning")

            except Exception as e:
                print_status(f"Cuti table error: {e}", "error")
                return False

            # Check User table
            try:
                user_count = User.query.count()
                print_status(f"User table accessible - {user_count} users", "success")

                if user_count > 0:
                    for user in User.query.all():
                        print_status(f"  • {user.email} (role: {user.role})", "info")
                else:
                    print_status("No users in database - cannot login!", "error")
                    return False

            except Exception as e:
                print_status(f"User table error: {e}", "error")
                return False

        return True

    except Exception as e:
        print_status(f"Database connection failed: {e}", "error")
        return False


def check_routes():
    """Check if routes are properly registered"""
    print_header("3. Checking Routes")

    try:
        from flask import url_for

        from app import app

        with app.app_context():
            with app.test_request_context():
                # Check main routes
                routes_to_check = [
                    ("ocr_cuti_v2.list_cuti_v2", "/cuti-v2/list"),
                    ("ocr_cuti_v2.ocr_cuti_v2", "/cuti-v2/"),
                    ("auth.login", "/login"),
                ]

                all_ok = True
                for route_name, expected_path in routes_to_check:
                    try:
                        url = url_for(route_name)
                        if url == expected_path:
                            print_status(f"{route_name} -> {url}", "success")
                        else:
                            print_status(
                                f"{route_name} -> {url} (expected: {expected_path})",
                                "warning",
                            )
                    except Exception as e:
                        print_status(f"{route_name} - NOT FOUND: {e}", "error")
                        all_ok = False

                return all_ok

    except Exception as e:
        print_status(f"Route check failed: {e}", "error")
        return False


def check_templates():
    """Check if template files exist"""
    print_header("4. Checking Templates")

    import os

    templates = [
        "templates/cuti/list_cuti.html",
        "templates/cuti/ocr_cuti_v2.html",
        "templates/layouts/base.html",
    ]

    all_ok = True
    for template in templates:
        if os.path.exists(template):
            size = os.path.getsize(template)
            print_status(f"{template} - OK ({size} bytes)", "success")
        else:
            print_status(f"{template} - NOT FOUND", "error")
            all_ok = False

    return all_ok


def check_static_files():
    """Check if static files exist"""
    print_header("5. Checking Static Files")

    import os

    static_files = [
        "static/assets/css/cuti.css",
        "static/assets/css/ocr_cuti.css",
    ]

    all_ok = True
    for file in static_files:
        if os.path.exists(file):
            size = os.path.getsize(file)
            print_status(f"{file} - OK ({size} bytes)", "success")
        else:
            print_status(f"{file} - NOT FOUND", "warning")

    return all_ok


def test_access():
    """Test actual access to the list_cuti endpoint"""
    print_header("6. Testing Endpoint Access")

    try:
        from app import app
        from config.models import User

        with app.app_context():
            # Get admin user
            admin = User.query.filter_by(role="admin").first()

            if not admin:
                print_status("No admin user found for testing", "error")
                return False

            print_status(f"Testing with user: {admin.email}", "info")

            with app.test_client() as client:
                # Test without login
                print_status("Testing access WITHOUT login...", "info")
                response = client.get("/cuti-v2/list", follow_redirects=False)

                if response.status_code == 302:
                    print_status(f"Redirected to: {response.location}", "info")
                    print_status(
                        "Redirect is expected for unauthenticated users", "success"
                    )
                elif response.status_code == 200:
                    print_status("Accessible without login (unexpected!)", "warning")
                else:
                    print_status(
                        f"Unexpected status code: {response.status_code}", "error"
                    )

                # Test the route function directly
                print_status("Testing route function...", "info")
                try:
                    from config.ocr_cuti_v2 import list_cuti_v2

                    print_status("list_cuti_v2 function is importable", "success")
                except Exception as e:
                    print_status(f"Cannot import list_cuti_v2: {e}", "error")
                    return False

        return True

    except Exception as e:
        print_status(f"Access test failed: {e}", "error")
        import traceback

        traceback.print_exc()
        return False


def check_permissions():
    """Check decorator and permission requirements"""
    print_header("7. Checking Permissions")

    try:
        import inspect

        from config.ocr_cuti_v2 import list_cuti_v2

        # Get function source
        source = inspect.getsource(list_cuti_v2)

        # Check for decorators
        if "@login_required" in source:
            print_status("@login_required decorator found - Login IS required", "info")
        else:
            print_status("No @login_required decorator - Login NOT required", "warning")

        if "@role_required" in source:
            print_status(
                "@role_required decorator found - Specific role required", "warning"
            )
        else:
            print_status(
                "No @role_required decorator - All authenticated users can access",
                "success",
            )

        return True

    except Exception as e:
        print_status(f"Permission check failed: {e}", "error")
        return False


def provide_recommendations():
    """Provide recommendations based on checks"""
    print_header("8. Recommendations")

    print("\nIf you cannot access /cuti-v2/list, try these steps:\n")

    recommendations = [
        "1. Make sure you are logged in as admin or pimpinan",
        "2. Clear browser cookies and cache (Ctrl+Shift+Del)",
        "3. Try accessing in incognito/private mode",
        "4. Check browser console (F12) for JavaScript errors",
        "5. Restart the Flask server: Ctrl+C then 'python app.py'",
        "6. Check server logs for error messages",
        "7. Try alternative route: http://localhost:5000/cuti/list-cuti",
    ]

    for rec in recommendations:
        print(f"   {rec}")

    print("\nLogin credentials for testing:")
    print("   • admin@admin.com / admin123")
    print("   • pimpinan@suratapp.com / pimpinan123")


def main():
    """Main diagnosis function"""
    print("\n")
    print("╔" + "=" * 78 + "╗")
    print("║" + " " * 20 + "LIST CUTI ACCESS DIAGNOSIS" + " " * 32 + "║")
    print("╚" + "=" * 78 + "╝")
    print(f"\nRunning diagnosis at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")

    results = {
        "imports": check_imports(),
        "database": check_database(),
        "routes": check_routes(),
        "templates": check_templates(),
        "static": check_static_files(),
        "access": test_access(),
        "permissions": check_permissions(),
    }

    # Summary
    print_header("DIAGNOSIS SUMMARY")

    passed = sum(1 for v in results.values() if v)
    total = len(results)

    print(f"\nTests passed: {passed}/{total}\n")

    for test_name, result in results.items():
        status = "PASS" if result else "FAIL"
        symbol = "✓" if result else "✗"
        print(f"  {symbol} {test_name.upper()}: {status}")

    # Overall status
    if passed == total:
        print("\n" + "=" * 80)
        print_status("All checks passed! The route should be accessible.", "success")
        print("=" * 80)
    else:
        print("\n" + "=" * 80)
        print_status(f"{total - passed} check(s) failed. See details above.", "error")
        print("=" * 80)

    provide_recommendations()

    print("\n" + "=" * 80)
    print("For more detailed troubleshooting, see TROUBLESHOOTING_LIST_CUTI.md")
    print("=" * 80 + "\n")

    return passed == total


if __name__ == "__main__":
    try:
        success = main()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\nDiagnosis interrupted by user.")
        sys.exit(1)
    except Exception as e:
        print(f"\n\nFatal error during diagnosis: {e}")
        import traceback

        traceback.print_exc()
        sys.exit(1)
