#!/usr/bin/env python3
"""
Test script untuk memeriksa CSRF token functionality
"""

import requests
from bs4 import BeautifulSoup

def test_csrf_token():
    """Test CSRF token functionality"""
    base_url = "http://localhost:5001"
    
    # Create session to maintain cookies
    session = requests.Session()
    
    try:
        # Get login page
        print("1. Mengakses halaman login...")
        response = session.get(f"{base_url}/login")
        print(f"   Status: {response.status_code}")
        
        if response.status_code == 200:
            # Parse HTML to get CSRF token
            soup = BeautifulSoup(response.text, 'html.parser')
            csrf_token = soup.find('meta', {'name': 'csrf-token'})
            
            if csrf_token:
                token = csrf_token.get('content')
                print(f"   CSRF Token ditemukan: {token[:20]}...")
                
                # Test login (you'll need to provide valid credentials)
                login_data = {
                    'email': 'admin@example.com',
                    'password': 'admin123',
                    'csrf_token': token
                }
                
                print("2. Mencoba login...")
                login_response = session.post(f"{base_url}/login", data=login_data)
                print(f"   Login status: {login_response.status_code}")
                
                if login_response.status_code == 302:  # Redirect after successful login
                    print("   Login berhasil!")
                    
                    # Test accessing pegawai list page
                    print("3. Mengakses halaman list pegawai...")
                    pegawai_response = session.get(f"{base_url}/pegawai/list")
                    print(f"   Status: {pegawai_response.status_code}")
                    
                    if pegawai_response.status_code == 200:
                        # Parse to get CSRF token from pegawai page
                        soup = BeautifulSoup(pegawai_response.text, 'html.parser')
                        csrf_token = soup.find('meta', {'name': 'csrf-token'})
                        
                        if csrf_token:
                            token = csrf_token.get('content')
                            print(f"   CSRF Token di halaman pegawai: {token[:20]}...")
                            
                            # Test delete request (you'll need a valid pegawai ID)
                            print("4. Testing delete request...")
                            delete_data = {
                                'csrf_token': token
                            }
                            
                            # Note: You'll need to replace '1' with an actual pegawai ID
                            delete_response = session.post(f"{base_url}/pegawai/hapus/1", data=delete_data)
                            print(f"   Delete status: {delete_response.status_code}")
                            print(f"   Response: {delete_response.text[:200]}...")
                        else:
                            print("   CSRF token tidak ditemukan di halaman pegawai")
                    else:
                        print("   Gagal mengakses halaman pegawai")
                else:
                    print("   Login gagal")
            else:
                print("   CSRF token tidak ditemukan di halaman login")
        else:
            print("   Gagal mengakses halaman login")
            
    except requests.exceptions.ConnectionError:
        print("Error: Tidak dapat terhubung ke server. Pastikan aplikasi Flask berjalan.")
    except Exception as e:
        print(f"Error: {str(e)}")

if __name__ == "__main__":
    test_csrf_token() 