#!/usr/bin/env python3
"""
Environment Manager Script
==========================

This script helps manage different environment configurations for the OCR application.

Usage:
    python env_manager.py [command] [environment]

Commands:
    switch <env>    - Switch to a specific environment (dev/prod/test)
    create <env>    - Create a new environment file
    backup          - Backup current .env file
    restore         - Restore .env from backup
    validate        - Validate current .env file
    list            - List available environment files
    help            - Show this help message

Examples:
    python env_manager.py switch dev
    python env_manager.py switch prod
    python env_manager.py backup
    python env_manager.py validate
"""

import os
import sys
import shutil
from datetime import datetime
from pathlib import Path

class EnvironmentManager:
    def __init__(self):
        self.root_dir = Path(__file__).parent
        self.env_files = {
            'dev': '.env.dev',
            'prod': '.env.prod', 
            'test': '.env.test',
            'example': '.env.example'
        }
        self.current_env = '.env'
        self.backup_dir = self.root_dir / 'env_backups'
        
    def ensure_backup_dir(self):
        """Create backup directory if it doesn't exist"""
        self.backup_dir.mkdir(exist_ok=True)
        
    def list_environments(self):
        """List available environment files"""
        print("Available environment files:")
        print("-" * 40)
        
        for env_name, env_file in self.env_files.items():
            file_path = self.root_dir / env_file
            status = "✓" if file_path.exists() else "✗"
            print(f"{status} {env_name:8} -> {env_file}")
            
        # Check current .env
        current_path = self.root_dir / self.current_env
        current_status = "✓" if current_path.exists() else "✗"
        print(f"{current_status} {'current':8} -> {self.current_env}")
        
    def switch_environment(self, env_name):
        """Switch to a specific environment"""
        if env_name not in self.env_files:
            print(f"Error: Unknown environment '{env_name}'")
            print(f"Available environments: {', '.join(self.env_files.keys())}")
            return False
            
        source_file = self.root_dir / self.env_files[env_name]
        target_file = self.root_dir / self.current_env
        
        if not source_file.exists():
            print(f"Error: Environment file '{source_file}' does not exist")
            return False
            
        # Backup current .env if it exists
        if target_file.exists():
            self.backup_current_env()
            
        # Copy the environment file
        try:
            shutil.copy2(source_file, target_file)
            print(f"✓ Switched to {env_name} environment")
            print(f"  Copied: {source_file} -> {target_file}")
            return True
        except Exception as e:
            print(f"Error switching environment: {e}")
            return False
            
    def backup_current_env(self):
        """Backup current .env file"""
        self.ensure_backup_dir()
        
        current_file = self.root_dir / self.current_env
        if not current_file.exists():
            print("No current .env file to backup")
            return False
            
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_file = self.backup_dir / f".env.backup.{timestamp}"
        
        try:
            shutil.copy2(current_file, backup_file)
            print(f"✓ Backed up current .env to: {backup_file}")
            return True
        except Exception as e:
            print(f"Error creating backup: {e}")
            return False
            
    def restore_from_backup(self, backup_name=None):
        """Restore .env from backup"""
        if not self.backup_dir.exists():
            print("No backup directory found")
            return False
            
        backups = list(self.backup_dir.glob(".env.backup.*"))
        if not backups:
            print("No backup files found")
            return False
            
        if backup_name:
            backup_file = self.backup_dir / backup_name
            if not backup_file.exists():
                print(f"Backup file '{backup_name}' not found")
                return False
        else:
            # Use the most recent backup
            backup_file = max(backups, key=os.path.getctime)
            
        target_file = self.root_dir / self.current_env
        
        try:
            shutil.copy2(backup_file, target_file)
            print(f"✓ Restored .env from: {backup_file}")
            return True
        except Exception as e:
            print(f"Error restoring backup: {e}")
            return False
            
    def validate_env(self):
        """Validate current .env file"""
        env_file = self.root_dir / self.current_env
        
        if not env_file.exists():
            print("❌ No .env file found")
            return False
            
        print("Validating .env file...")
        print("-" * 40)
        
        required_vars = [
            'FLASK_APP',
            'SECRET_KEY',
            'DEBUG'
        ]
        
        important_vars = [
            'DB_ENGINE',
            'OCR_ENGINE',
            'UPLOAD_FOLDER'
        ]
        
        try:
            with open(env_file, 'r') as f:
                content = f.read()
                
            # Parse environment variables
            env_vars = {}
            for line in content.split('\n'):
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    env_vars[key.strip()] = value.strip()
                    
            # Check required variables
            missing_required = []
            for var in required_vars:
                if var not in env_vars or not env_vars[var]:
                    missing_required.append(var)
                else:
                    print(f"✓ {var}: {env_vars[var]}")
                    
            # Check important variables
            missing_important = []
            for var in important_vars:
                if var not in env_vars or not env_vars[var]:
                    missing_important.append(var)
                else:
                    print(f"✓ {var}: {env_vars[var]}")
                    
            # Report results
            if missing_required:
                print(f"\n❌ Missing required variables: {', '.join(missing_required)}")
                return False
                
            if missing_important:
                print(f"\n⚠️  Missing important variables: {', '.join(missing_important)}")
                
            # Check for default values that should be changed
            warnings = []
            if env_vars.get('SECRET_KEY', '').find('change-this') != -1:
                warnings.append("SECRET_KEY contains default value")
                
            if env_vars.get('SECRET_KEY', '').find('dev-secret') != -1 and env_vars.get('DEBUG') == 'False':
                warnings.append("Using development SECRET_KEY in production mode")
                
            if warnings:
                print(f"\n⚠️  Warnings:")
                for warning in warnings:
                    print(f"   - {warning}")
                    
            print(f"\n✓ Environment file validation completed")
            return True
            
        except Exception as e:
            print(f"Error validating .env file: {e}")
            return False
            
    def create_environment(self, env_name):
        """Create a new environment file"""
        if env_name in self.env_files:
            print(f"Environment '{env_name}' already exists")
            return False
            
        # Create from example template
        example_file = self.root_dir / self.env_files['example']
        new_file = self.root_dir / f'.env.{env_name}'
        
        if not example_file.exists():
            print("Error: .env.example template not found")
            return False
            
        try:
            shutil.copy2(example_file, new_file)
            print(f"✓ Created new environment file: {new_file}")
            print(f"  Please edit {new_file} to configure your settings")
            return True
        except Exception as e:
            print(f"Error creating environment file: {e}")
            return False

def main():
    manager = EnvironmentManager()
    
    if len(sys.argv) < 2:
        print(__doc__)
        return
        
    command = sys.argv[1].lower()
    
    if command == 'list':
        manager.list_environments()
        
    elif command == 'switch':
        if len(sys.argv) < 3:
            print("Usage: python env_manager.py switch <environment>")
            return
        env_name = sys.argv[2]
        manager.switch_environment(env_name)
        
    elif command == 'backup':
        manager.backup_current_env()
        
    elif command == 'restore':
        backup_name = sys.argv[2] if len(sys.argv) > 2 else None
        manager.restore_from_backup(backup_name)
        
    elif command == 'validate':
        manager.validate_env()
        
    elif command == 'create':
        if len(sys.argv) < 3:
            print("Usage: python env_manager.py create <environment_name>")
            return
        env_name = sys.argv[2]
        manager.create_environment(env_name)
        
    elif command == 'help':
        print(__doc__)
        
    else:
        print(f"Unknown command: {command}")
        print(__doc__)

if __name__ == '__main__':
    main()