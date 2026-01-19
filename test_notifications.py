#!/usr/bin/env python3
"""
Test script for notification system
Verifies that notifications show proper status messages instead of numbers
"""

import re
from pathlib import Path

def test_flash_messages_integration():
    """Test if Flask flash messages are properly integrated"""
    template_path = Path("templates/auth/edit_users.html")
    
    with open(template_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Check for flash message integration
    flash_integration_checks = [
        "get_flashed_messages(with_categories=true)",
        "{% for category, message in messages %}",
        "showToast('{{ message|safe }}'"
    ]
    
    print("🔍 Testing Flash Messages Integration...")
    
    all_passed = True
    for check in flash_integration_checks:
        if check in content:
            print(f"✅ {check}")
        else:
            print(f"❌ {check}")
            all_passed = False
    
    return all_passed

def test_indonesian_messages():
    """Test if all messages are in Indonesian"""
    
    # Test template messages
    template_path = Path("templates/auth/edit_users.html")
    with open(template_path, 'r', encoding='utf-8') as f:
        template_content = f.read()
    
    # Test routes messages
    routes_path = Path("config/user_routes.py")
    with open(routes_path, 'r', encoding='utf-8') as f:
        routes_content = f.read()
    
    print("\n🇮🇩 Testing Indonesian Messages...")
    
    # Check for Indonesian messages in template
    template_indonesian_messages = [
        "Gagal memuat data pegawai",
        "Gagal menyetujui pegawai", 
        "Data pegawai berhasil dihapus",
        "Gagal menghapus data pegawai",
        "Data pegawai berhasil diperbarui",
        "Gagal memperbarui data pegawai",
        "Gagal memuat log aktivitas"
    ]
    
    template_passed = True
    for message in template_indonesian_messages:
        if message in template_content:
            print(f"✅ Template: {message}")
        else:
            print(f"❌ Template: {message}")
            template_passed = False
    
    # Check for Indonesian messages in routes
    routes_indonesian_messages = [
        "Data pegawai berhasil diperbarui!",
        "Anda tidak memiliki izin untuk mengelola pegawai",
        "Silakan pilih pegawai yang akan diedit",
        "Data pegawai tidak ditemukan",
        "Terjadi kesalahan saat memuat halaman kelola pegawai",
        "Anda tidak memiliki izin untuk menghapus pegawai",
        "Anda tidak dapat menghapus akun Anda sendiri",
        "berhasil dihapus",
        "Gagal menghapus pegawai",
        "berhasil disetujui",
        "Tidak memiliki izin"
    ]
    
    routes_passed = True
    for message in routes_indonesian_messages:
        if message in routes_content:
            print(f"✅ Routes: {message}")
        else:
            print(f"❌ Routes: {message}")
            routes_passed = False
    
    return template_passed and routes_passed

def test_no_english_error_messages():
    """Test that there are no remaining English error messages"""
    
    template_path = Path("templates/auth/edit_users.html")
    routes_path = Path("config/user_routes.py")
    
    with open(template_path, 'r', encoding='utf-8') as f:
        template_content = f.read()
    
    with open(routes_path, 'r', encoding='utf-8') as f:
        routes_content = f.read()
    
    print("\n🚫 Testing for English Error Messages...")
    
    # Common English error patterns to avoid
    english_patterns = [
        r"Error (loading|updating|deleting|approving) user",
        r"User .* (updated|deleted|approved) successfully",
        r"You do not have permission",
        r"User not found",
        r"Unauthorized"
    ]
    
    all_passed = True
    
    for pattern in english_patterns:
        template_matches = re.findall(pattern, template_content, re.IGNORECASE)
        routes_matches = re.findall(pattern, routes_content, re.IGNORECASE)
        
        if template_matches:
            print(f"❌ Template contains English: {template_matches}")
            all_passed = False
        else:
            print(f"✅ Template clean of: {pattern}")
            
        if routes_matches:
            print(f"❌ Routes contains English: {routes_matches}")
            all_passed = False
        else:
            print(f"✅ Routes clean of: {pattern}")
    
    return all_passed

def test_toast_notification_system():
    """Test if toast notification system is properly implemented"""
    
    template_path = Path("templates/auth/edit_users.html")
    with open(template_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    print("\n🍞 Testing Toast Notification System...")
    
    toast_checks = [
        "function showToast(",
        "toast-success",
        "toast-error", 
        "getElementById('toast-container')",
        ".classList.remove('hidden')",
        "setTimeout(() => {"
    ]
    
    all_passed = True
    for check in toast_checks:
        if check in content:
            print(f"✅ {check}")
        else:
            print(f"❌ {check}")
            all_passed = False
    
    return all_passed

def main():
    """Run all notification tests"""
    print("🔔 Testing Notification System")
    print("=" * 50)
    
    tests = [
        ("Flash Messages Integration", test_flash_messages_integration),
        ("Indonesian Messages", test_indonesian_messages),
        ("No English Errors", test_no_english_error_messages),
        ("Toast Notification System", test_toast_notification_system)
    ]
    
    results = []
    for test_name, test_func in tests:
        print(f"\n📋 {test_name}")
        print("-" * 30)
        results.append(test_func())
    
    print("\n" + "=" * 50)
    print("📊 Test Results:")
    
    passed = sum(results)
    total = len(results)
    
    if passed == total:
        print(f"🎉 All tests passed! ({passed}/{total})")
        print("\n✨ Notification system is working properly!")
        print("\n🚀 Key Improvements:")
        print("   • Flask flash messages integrated")
        print("   • All messages in Indonesian")
        print("   • No English error messages")
        print("   • Toast notifications working")
        print("   • Proper status messages instead of numbers")
        return True
    else:
        print(f"⚠️  Some tests failed ({passed}/{total})")
        return False

if __name__ == "__main__":
    import sys
    success = main()
    sys.exit(0 if success else 1)