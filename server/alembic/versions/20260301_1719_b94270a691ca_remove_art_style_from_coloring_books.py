# Alembic Migration Script Template
# This is the default template for new migrations

"""remove_art_style_from_coloring_books

Revision ID: b94270a691ca
Revises: 20260301_1345
Create Date: 2026-03-01 17:19:43.437699

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'b94270a691ca'
down_revision: Union[str, None] = '20260301_1345'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Remove art_style column from coloring_book_templates table"""
    
    # Check if table and column exist
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    existing_tables = inspector.get_table_names()
    
    if 'coloring_book_templates' in existing_tables:
        existing_columns = [col['name'] for col in inspector.get_columns('coloring_book_templates')]
        
        if 'art_style' in existing_columns:
            # Try to drop the constraint first (may not exist)
            try:
                op.drop_constraint('check_art_style', 'coloring_book_templates', type_='check')
            except Exception:
                pass  # Constraint might not exist
            
            # Drop the column
            op.drop_column('coloring_book_templates', 'art_style')


def downgrade() -> None:
    """Re-add art_style column to coloring_book_templates table"""
    
    # Add back the art_style column
    op.add_column(
        'coloring_book_templates',
        sa.Column('art_style', sa.String(length=50), nullable=True)
    )
    
    # Recreate the art_style check constraint
    op.create_check_constraint(
        'check_art_style',
        'coloring_book_templates',
        "art_style IN ('cartoon', 'realistic', 'abstract', 'simple', 'detailed') OR art_style IS NULL"
    )
