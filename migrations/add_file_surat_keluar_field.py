"""Add file_suratKeluar field to SuratKeluar table

Revision ID: add_file_surat_keluar_field
Revises: add_status_columns
Create Date: 2024-01-XX

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'add_file_surat_keluar_field'
down_revision = 'add_status_columns'
branch_labels = None
depends_on = None

def upgrade():
    # Add file_suratKeluar column to SuratKeluar table
    op.add_column('surat_keluar', sa.Column('file_suratKeluar', sa.LargeBinary(), nullable=True))

def downgrade():
    # Remove file_suratKeluar column from SuratKeluar table
    op.drop_column('surat_keluar', 'file_suratKeluar') 