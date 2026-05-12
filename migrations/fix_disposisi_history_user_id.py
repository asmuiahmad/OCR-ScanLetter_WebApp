"""
Migration script untuk memperbaiki disposisi_history table
Membuat user_id nullable untuk mengatasi error saat update status

Run dengan: python migrations/fix_disposisi_history_user_id.py
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
        print("🚀 Starting disposisi_history migration...")
        
        try:
            # Check if disposisi_history table exists
            result = db.session.execute(text("""
                SELECT name FROM sqlite_master 
                WHERE type='table' AND name='disposisi_history';
            """)).fetchone()
            
            if not result:
                print("📋 Creating disposisi_history table...")
                # Create table with correct schema
                create_table_sql = """
                CREATE TABLE IF NOT EXISTS disposisi_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    disposisi_id INTEGER NOT NULL,
                    status_lama VARCHAR(20),
                    status_baru VARCHAR(20) NOT NULL,
                    catatan TEXT,
                    user_id INTEGER,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (disposisi_id) REFERENCES disposisi(id),
                    FOREIGN KEY (user_id) REFERENCES user(id)
                );
                """
                db.session.execute(text(create_table_sql))
                print("✅ Created disposisi_history table")
            else:
                print("📋 Updating disposisi_history table...")
                # Make user_id nullable if it's not already
                try:
                    # SQLite doesn't support ALTER COLUMN, so we need to recreate table
                    db.session.execute(text("""
                        CREATE TABLE IF NOT EXISTS disposisi_history_new (
                            id INTEGER PRIMARY KEY AUTOINCREMENT,
                            disposisi_id INTEGER NOT NULL,
                            status_lama VARCHAR(20),
                            status_baru VARCHAR(20) NOT NULL,
                            catatan TEXT,
                            user_id INTEGER,
                            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                            FOREIGN KEY (disposisi_id) REFERENCES disposisi(id),
                            FOREIGN KEY (user_id) REFERENCES user(id)
                        );
                    """))
                    
                    # Copy existing data
                    db.session.execute(text("""
                        INSERT INTO disposisi_history_new 
                        (id, disposisi_id, status_lama, status_baru, catatan, user_id, timestamp)
                        SELECT id, disposisi_id, status_lama, status_baru, catatan, user_id, timestamp
                        FROM disposisi_history;
                    """))
                    
                    # Drop old table and rename new one
                    db.session.execute(text("DROP TABLE disposisi_history;"))
                    db.session.execute(text("ALTER TABLE disposisi_history_new RENAME TO disposisi_history;"))
                    
                    print("✅ Updated disposisi_history table schema")
                except Exception as e:
                    print(f"⚠️  Table may already have correct schema: {str(e)}")
            
            db.session.commit()
            print("🎉 Migration completed successfully!")
            
        except Exception as e:
            db.session.rollback()
            print(f"❌ Migration failed: {str(e)}")
            raise

if __name__ == "__main__":
    migrate()