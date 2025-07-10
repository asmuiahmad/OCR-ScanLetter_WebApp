import os
import sys

# Add the project root to the Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from config.extensions import db
from config.models import User
from app import create_app

def create_admin():
    """Create an admin user in the database."""
    # Create app context
    app = create_app()
    
    with app.app_context():
        # Check if admin already exists
        admin = User.query.filter_by(email='admin@admin.com').first()
        if admin:
            print("Admin user already exists!")
            return
        
        # Create new admin user
        admin = User(
            email='admin@admin.com',
            role='admin',
            is_admin=True,
            is_approved=True
        )
        admin.set_password('admin123')
        
        # Add to database
        db.session.add(admin)
        db.session.commit()
        
        print("Admin user created successfully!")
        print("Email: admin@admin.com")
        print("Password: admin123")

if __name__ == '__main__':
    create_admin() 