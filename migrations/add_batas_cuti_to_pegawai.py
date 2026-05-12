"""Add batas_cuti column to pegawai table

Revision ID: add_batas_cuti
Revises: 
Create Date: 2026-04-06 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'add_batas_cuti'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # Add batas_cuti column to pegawai table
    op.add_column('pegawai', sa.Column('batas_cuti', sa.Integer(), nullable=False, server_default='12'))


def downgrade():
    # Remove batas_cuti column from pegawai table
    op.drop_column('pegawai', 'batas_cuti')
