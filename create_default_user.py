#!/usr/bin/env python3
"""
Script to create a default admin user for testing purposes.
"""

import os
import sys

# Add the project root to the Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from config.extensions import db
from config.models import User
from app import create_app
from werkzeug.security import generate_password_hash

def create_default_user():
    """Create a default admin user for testing."""
    app = create_app()
    
    with app.app_context():
        # Check if admin user already exists
        admin_user = User.query.filter_by(email='admin@test.com').first()
        
        if admin_user:
            print("Admin user already exists!")
            print(f"Email: {admin_user.email}")
            print(f"Role: {admin_user.role}")
            print(f"Is Approved: {admin_user.is_approved}")
            return
        
        # Create default admin user
        admin_user = User(
            email='admin@test.com',
            password=generate_password_hash('admin123'),
            role='admin',
            is_admin=True,
            is_approved=True
        )
        
        try:
            db.session.add(admin_user)
            db.session.commit()
            print("Default admin user created successfully!")
            print("Email: admin@test.com")
            print("Password: admin123")
            print("Role: admin")
            print("Status: Approved")
        except Exception as e:
            db.session.rollback()
            print(f"Error creating admin user: {e}")

if __name__ == "__main__":
    create_default_user() 