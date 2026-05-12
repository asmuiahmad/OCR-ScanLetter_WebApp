"""
Migration script untuk update schema Disposisi
Menambahkan field baru untuk improvement sistem disposisi

Run dengan: python migrations/update_disposisi_schema.py
"""

from app import create_app
from config.extensions import db
from sqlalchemy import text

app = create_app()

def migrate():
    with app.app_context():
        print("🚀 Starting Disposisi schema migration...")
        
        try:
            # Add new columns to disposisi table
            migrations = [
                # Surat reference
                "ALTER TABLE disposisi ADD COLUMN IF NOT EXISTS surat_tipe VARCHAR(10) DEFAULT 'masuk'",
                "ALTER TABLE disposisi ADD COLUMN IF NOT EXISTS surat_keluar_id INTEGER REFERENCES surat_keluar(id_suratKeluar)",
                
                # Content fields
                "ALTER TABLE disposisi ADD COLUMN IF NOT EXISTS perihal VARCHAR(200)",
                "ALTER TABLE disposisi ADD COLUMN IF NOT EXISTS instruksi TEXT",
                "ALTER TABLE disposisi ADD COLUMN IF NOT EXISTS catatan_tindak_lanjut TEXT",
                
                # Status tracking
                "ALTER TABLE disposisi ADD COLUMN IF NOT EXISTS status_surat_sebelum VARCHAR(50)",
                "ALTER TABLE disposisi ADD COLUMN IF NOT EXISTS alasan_penolakan TEXT",
                
                # Timestamps
                "ALTER TABLE disposisi ADD COLUMN IF NOT EXISTS tanggal_dikirim TIMESTAMP",
                "ALTER TABLE disposisi ADD COLUMN IF NOT EXISTS tanggal_diproses TIMESTAMP",
                
                # Update default status from 'pending' to 'draft'
                "UPDATE disposisi SET status = 'draft' WHERE status = 'pending'",
            ]
            
            for migration in migrations:
                try:
                    db.session.execute(text(migration))
                    print(f"✅ Executed: {migration[:80]}...")
                except Exception as e:
                    print(f"⚠️  Skipped (may already exist): {migration[:80]}...")
                    print(f"   Error: {str(e)[:100]}")
            
            # Create disposisi_history table
            create_history_table = """
            CREATE TABLE IF NOT EXISTS disposisi_history (
                id SERIAL PRIMARY KEY,
                disposisi_id INTEGER NOT NULL REFERENCES disposisi(id) ON DELETE CASCADE,
                status_lama VARCHAR(20),
                status_baru VARCHAR(20) NOT NULL,
                catatan TEXT,
                user_id INTEGER NOT NULL REFERENCES "user"(id),
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """
            
            try:
                db.session.execute(text(create_history_table))
                print("✅ Created disposisi_history table")
            except Exception as e:
                print(f"⚠️  disposisi_history table may already exist: {str(e)[:100]}")
            
            # Commit all changes
            db.session.commit()
            print("\n✅ Migration completed successfully!")
            print("\n📋 Summary:")
            print("   - Added surat_tipe and surat_keluar_id for supporting both surat types")
            print("   - Added perihal, instruksi, catatan_tindak_lanjut for better content management")
            print("   - Added status_surat_sebelum and alasan_penolakan for better tracking")
            print("   - Added tanggal_dikirim and tanggal_diproses for timeline tracking")
            print("   - Created disposisi_history table for audit trail")
            print("   - Updated status 'pending' to 'draft'")
            
        except Exception as e:
            db.session.rollback()
            print(f"\n❌ Migration failed: {str(e)}")
            raise

if __name__ == '__main__':
    migrate()
