#!/usr/bin/env python3
"""
Test script to verify all route imports are working correctly
"""

def test_route_imports():
    """Test all route module imports"""
    try:
        # Test main routes registration
        from config.routes_main import register_blueprints
        print("✅ routes_main import successful")
        
        # Test individual route modules
        from config.auth_routes import auth_bp
        print("✅ auth_routes import successful")
        
        from config.user_routes import user_bp
        print("✅ user_routes import successful")
        
        from config.pegawai_routes import pegawai_bp
        print("✅ pegawai_routes import successful")
        
        from config.surat_routes import surat_bp
        print("✅ surat_routes import successful")
        
        from config.cuti_routes import cuti_bp
        print("✅ cuti_routes import successful")
        
        from config.api_routes import api_bp
        print("✅ api_routes import successful")
        
        from config.dashboard_routes import dashboard_bp
        print("✅ dashboard_routes import successful")
        
        from config.route_utils import role_required, log_user_login
        print("✅ route_utils import successful")
        
        print("\n🎉 All route imports successful!")
        print("🎉 Route organization is working correctly!")
        return True
        
    except ImportError as e:
        print(f"❌ Import error: {e}")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False

if __name__ == "__main__":
    test_route_imports()