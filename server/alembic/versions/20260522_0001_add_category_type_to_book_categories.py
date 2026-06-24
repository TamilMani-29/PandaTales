"""add category_type to book_categories

Revision ID: 20260522_0001
Revises: 20260517_0002_fix_personalized_flag_on_book_categories
Create Date: 2026-05-22 00:01:00.000000
"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '20260522_0001'
down_revision = '20260517_0002_fix_personalized_flag_on_book_categories'
branch_labels = None
depends_on = None

def upgrade():
    op.add_column('book_categories', sa.Column('category_type', sa.String(length=50), nullable=True))

def downgrade():
    op.drop_column('book_categories', 'category_type')
