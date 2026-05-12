"""
Create disposisi_surat table for the new disposisi module.

Run:
python migrations/create_disposisi_surat_table.py
"""

from app import app
from config.extensions import db


def run():
    with app.app_context():
        db.create_all()
        print("OK: tabel disposisi_surat sudah dipastikan tersedia.")


if __name__ == "__main__":
    run()
