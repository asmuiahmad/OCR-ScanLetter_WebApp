"""
Migration script untuk membuat tabel user_login_logs
Mengatasi error 500 saat login karena tabel tidak ada

Run dengan: python migrations/create_user_login_logs_table.py
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from flask import Flask
from config.extensions import db
from sqlalchemy import text

def create_minimal_app():
    """Create minimal Flask app for migration"""
    app = Flask(__name__)
    
    # Basic config
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///app.db'  # Adjust as needed
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    
    db.init_app(app)
    return app

def migrate():
    app = create_minimal_app()
    with app.app_context():
        print("🚀 Starting user_login_logs table migration...")
        
        try:
            # Check if user_login_logs table exists
            result = db.session.execute(text("""
                SELECT name FROM sqlite_master 
                WHERE type='table' AND name='user_login_logs';
            """)).fetchone()
            
            if not result:
                print("📋 Creating user_login_logs table...")
                # Create table with correct schema
                create_table_sql = """
                CREATE TABLE user_login_logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER,
                    user_email VARCHAR(255) NOT NULL,
                    login_time DATETIME DEFAULT CURRENT_TIMESTAMP,
                    logout_time DATETIME,
                    ip_address VARCHAR(45),
                    user_agent TEXT,
                    status VARCHAR(20) DEFAULT 'success',
                    session_duration INTEGER,
                    browser_info VARCHAR(255),
                    device_type VARCHAR(50),
                    location VARCHAR(255),
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES user(id) ON DELETE CASCADE
                );
                """
                db.session.execute(text(create_table_sql))
                print("✅ Created user_login_logs table")
            else:
                print("✅ user_login_logs table already exists")
            
            # Check if user table exists
            result = db.session.execute(text("""
                SELECT name FROM sqlite_master 
                WHERE type='table' AND name='user';
            """)).fetchone()
            
            if not result:
                print("📋 Creating user table...")
                create_user_table_sql = """
                CREATE TABLE user (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    email VARCHAR(100) UNIQUE NOT NULL,
                    password VARCHAR(100) NOT NULL,
                    last_login DATETIME,
                    login_count INTEGER DEFAULT 0,
                    is_admin BOOLEAN DEFAULT 0,
                    role VARCHAR(20) NOT NULL DEFAULT 'karyawan',
                    is_approved BOOLEAN NOT NULL DEFAULT 0
                );
                """
                db.session.execute(text(create_user_table_sql))
                print("✅ Created user table")
                
                # Create default admin user
                from werkzeug.security import generate_password_hash
                admin_password = generate_password_hash('admin123')
                
                insert_admin_sql = """
                INSERT INTO user (email, password, role, is_admin, is_approved, login_count)
                VALUES ('admin@example.com', ?, 'admin', 1, 1, 0);
                """
                db.session.execute(text(insert_admin_sql), (admin_password,))
                print("✅ Created default admin user (admin@example.com / admin123)")
            else:
                print("✅ user table already exists")
            
            db.session.commit()
            print("🎉 Migration completed successfully!")
            
        except Exception as e:
            db.session.rollback()
            print(f"❌ Migration failed: {str(e)}")
            raise

if __name__ == "__main__":
    migrate()