#!/usr/bin/env python3
"""
Requirements Installation Script
===============================

This script helps install Python requirements for the OCR application
with different installation options and environment detection.

Usage:
    python install_requirements.py [options]

Options:
    --env <env>         Install for specific environment (dev/prod/minimal)
    --upgrade           Upgrade existing packages
    --force             Force reinstall all packages
    --dry-run           Show what would be installed without installing
    --system-deps       Install system dependencies (requires sudo)
    --help              Show this help message

Examples:
    python install_requirements.py --env dev
    python install_requirements.py --env prod --upgrade
    python install_requirements.py --system-deps
"""

import os
import sys
import subprocess
import platform
import argparse
from pathlib import Path

class RequirementsInstaller:
    def __init__(self):
        self.root_dir = Path(__file__).parent
        self.system = platform.system().lower()
        self.requirements_files = {
            'base': 'requirements.txt',
            'dev': 'requirements-dev.txt',
            'prod': 'requirements-prod.txt',
            'minimal': 'requirements-minimal.txt'
        }
        
    def check_python_version(self):
        """Check if Python version is compatible"""
        version = sys.version_info
        if version.major < 3 or (version.major == 3 and version.minor < 9):
            print("❌ Python 3.9+ is required")
            print(f"   Current version: {version.major}.{version.minor}.{version.micro}")
            return False
        print(f"✓ Python version: {version.major}.{version.minor}.{version.micro}")
        return True
        
    def check_pip(self):
        """Check if pip is available and up to date"""
        try:
            result = subprocess.run([sys.executable, '-m', 'pip', '--version'], 
                                  capture_output=True, text=True)
            if result.returncode == 0:
                print(f"✓ pip is available: {result.stdout.strip()}")
                return True
            else:
                print("❌ pip is not available")
                return False
        except Exception as e:
            print(f"❌ Error checking pip: {e}")
            return False
            
    def upgrade_pip(self):
        """Upgrade pip to latest version"""
        print("📦 Upgrading pip...")
        try:
            subprocess.run([sys.executable, '-m', 'pip', 'install', '--upgrade', 'pip'], 
                          check=True)
            print("✓ pip upgraded successfully")
            return True
        except subprocess.CalledProcessError as e:
            print(f"❌ Failed to upgrade pip: {e}")
            return False
            
    def install_system_dependencies(self):
        """Install system dependencies for OCR"""
        print("🔧 Installing system dependencies...")
        
        if self.system == 'linux':
            # Ubuntu/Debian
            commands = [
                ['sudo', 'apt-get', 'update'],
                ['sudo', 'apt-get', 'install', '-y', 
                 'tesseract-ocr', 'tesseract-ocr-ind', 'tesseract-ocr-eng',
                 'libtesseract-dev', 'libleptonica-dev', 'pkg-config',
                 'libpoppler-cpp-dev', 'libcairo2-dev', 'libpango1.0-dev',
                 'libgdk-pixbuf2.0-dev', 'libffi-dev', 'shared-mime-info']
            ]
            
        elif self.system == 'darwin':  # macOS
            commands = [
                ['brew', 'install', 'tesseract', 'tesseract-lang'],
                ['brew', 'install', 'poppler', 'cairo', 'pango', 'gdk-pixbuf', 'libffi']
            ]
            
        elif self.system == 'windows':
            print("⚠️  Windows system dependencies:")
            print("   1. Download Tesseract from: https://github.com/UB-Mannheim/tesseract/wiki")
            print("   2. Install and add to PATH")
            print("   3. Download language packs for Indonesian and English")
            return True
            
        else:
            print(f"❌ Unsupported system: {self.system}")
            return False
            
        # Execute commands
        for cmd in commands:
            try:
                print(f"   Running: {' '.join(cmd)}")
                subprocess.run(cmd, check=True)
            except subprocess.CalledProcessError as e:
                print(f"❌ Failed to run: {' '.join(cmd)}")
                print(f"   Error: {e}")
                return False
            except FileNotFoundError:
                if cmd[0] == 'brew':
                    print("❌ Homebrew not found. Please install Homebrew first:")
                    print("   /bin/bash -c \"$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)\"")
                elif cmd[0] == 'sudo':
                    print("❌ This script requires sudo access for system packages")
                return False
                
        print("✓ System dependencies installed successfully")
        return True
        
    def install_requirements(self, env='base', upgrade=False, force=False, dry_run=False):
        """Install Python requirements"""
        req_file = self.requirements_files.get(env, 'requirements.txt')
        req_path = self.root_dir / req_file
        
        if not req_path.exists():
            print(f"❌ Requirements file not found: {req_file}")
            return False
            
        print(f"📦 Installing requirements from: {req_file}")
        
        # Build pip command
        cmd = [sys.executable, '-m', 'pip', 'install']
        
        if upgrade:
            cmd.append('--upgrade')
        if force:
            cmd.extend(['--force-reinstall', '--no-deps'])
        if dry_run:
            cmd.append('--dry-run')
            
        cmd.extend(['-r', str(req_path)])
        
        try:
            if dry_run:
                print(f"🔍 Dry run - would execute: {' '.join(cmd)}")
            else:
                print(f"   Executing: {' '.join(cmd)}")
                
            result = subprocess.run(cmd, check=True, capture_output=True, text=True)
            
            if dry_run:
                print("📋 Packages that would be installed:")
                print(result.stdout)
            else:
                print("✓ Requirements installed successfully")
                
            return True
            
        except subprocess.CalledProcessError as e:
            print(f"❌ Failed to install requirements: {e}")
            if e.stderr:
                print(f"   Error details: {e.stderr}")
            return False
            
    def check_installation(self):
        """Verify that key packages are installed correctly"""
        print("🔍 Verifying installation...")
        
        key_packages = [
            'flask',
            'pytesseract', 
            'PIL',
            'sqlalchemy',
            'wtforms'
        ]
        
        failed_imports = []
        
        for package in key_packages:
            try:
                if package == 'PIL':
                    import PIL
                else:
                    __import__(package)
                print(f"✓ {package}")
            except ImportError:
                print(f"❌ {package}")
                failed_imports.append(package)
                
        if failed_imports:
            print(f"\n❌ Failed to import: {', '.join(failed_imports)}")
            return False
        else:
            print("\n✓ All key packages imported successfully")
            return True
            
    def show_next_steps(self, env):
        """Show next steps after installation"""
        print("\n" + "="*50)
        print("🎉 Installation completed!")
        print("="*50)
        print("\n📋 Next steps:")
        print("1. Set up your environment:")
        print(f"   ./switch_env.sh {env}")
        print("\n2. Initialize the database:")
        print("   python -c \"from app import app, db; app.app_context().push(); db.create_all()\"")
        print("\n3. Run the application:")
        print("   python app.py")
        print("\n4. Open your browser:")
        print("   http://localhost:5000")
        
        if env == 'dev':
            print("\n🔧 Development tools available:")
            print("   - Flask Debug Toolbar")
            print("   - IPython shell")
            print("   - Testing framework")
            
        print("\n📚 Documentation:")
        print("   - README.md for setup instructions")
        print("   - .env.example for configuration options")

def main():
    parser = argparse.ArgumentParser(description='Install requirements for OCR application')
    parser.add_argument('--env', choices=['base', 'dev', 'prod', 'minimal'], 
                       default='base', help='Environment to install for')
    parser.add_argument('--upgrade', action='store_true', 
                       help='Upgrade existing packages')
    parser.add_argument('--force', action='store_true', 
                       help='Force reinstall all packages')
    parser.add_argument('--dry-run', action='store_true', 
                       help='Show what would be installed')
    parser.add_argument('--system-deps', action='store_true', 
                       help='Install system dependencies')
    parser.add_argument('--skip-checks', action='store_true', 
                       help='Skip pre-installation checks')
    
    args = parser.parse_args()
    
    installer = RequirementsInstaller()
    
    print("🚀 OCR Application Requirements Installer")
    print("=" * 50)
    
    # Pre-installation checks
    if not args.skip_checks:
        if not installer.check_python_version():
            sys.exit(1)
            
        if not installer.check_pip():
            sys.exit(1)
            
        # Upgrade pip
        installer.upgrade_pip()
    
    # Install system dependencies if requested
    if args.system_deps:
        if not installer.install_system_dependencies():
            print("⚠️  System dependencies installation failed, but continuing...")
    
    # Install Python requirements
    success = installer.install_requirements(
        env=args.env,
        upgrade=args.upgrade,
        force=args.force,
        dry_run=args.dry_run
    )
    
    if not success:
        sys.exit(1)
    
    # Verify installation (skip for dry run)
    if not args.dry_run:
        if not installer.check_installation():
            print("⚠️  Some packages failed to import, but installation may still work")
        
        installer.show_next_steps(args.env)

if __name__ == '__main__':
    main()