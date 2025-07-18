"""Add file_suratMasuk field to SuratMasuk table

Revision ID: add_file_surat_masuk_field
Revises: add_status_columns
Create Date: 2024-01-XX

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'add_file_surat_masuk_field'
down_revision = 'add_status_columns'
branch_labels = None
depends_on = None

def upgrade():
    # Add file_suratMasuk column to SuratMasuk table
    op.add_column('surat_masuk', sa.Column('file_suratMasuk', sa.LargeBinary(), nullable=True))

def downgrade():
    # Remove file_suratMasuk column from SuratMasuk table
    op.drop_column('surat_masuk', 'file_suratMasuk') 