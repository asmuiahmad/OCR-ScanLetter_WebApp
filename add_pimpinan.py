#!/usr/bin/env python3
"""
Simple script to add pimpinan account
Run this with: python add_pimpinan.py
"""

from app import create_app
from config.extensions import db
from config.models import User
from werkzeug.security import generate_password_hash

def add_pimpinan():
    app = create_app()
    
    with app.app_context():
        # Check if pimpinan already exists
        existing = User.query.filter_by(role='pimpinan').first()
        if existing:
            print(f"✅ Pimpinan account already exists: {existing.email}")
            if not existing.is_approved:
                existing.is_approved = True
                db.session.commit()
                print("✅ Account approved!")
            return existing.email
        
        # Create new pimpinan account
        pimpinan = User(
            email='pimpinan@suratapp.com',
            password=generate_password_hash('pimpinan123'),
            role='pimpinan',
            is_admin=False,
            is_approved=True
        )
        
        db.session.add(pimpinan)
        db.session.commit()
        
        print("✅ Pimpinan account created!")
        print("📧 Email: pimpinan@suratapp.com")
        print("🔑 Password: pimpinan123")
        print("⚠️  Please change password after first login!")
        
        return pimpinan.email

if __name__ == '__main__':
    add_pimpinan()