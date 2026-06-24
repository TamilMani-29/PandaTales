"""remove_complexity_level_from_coloring_books

Revision ID: b5d6e7f8a9c0
Revises: a4c3d2e1f0b9
Create Date: 2026-03-01 00:05:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = 'b5d6e7f8a9c0'
down_revision: Union[str, None] = 'a4c3d2e1f0b9'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Remove complexity_level column from coloring_book_templates table"""
    
    # Check if table exists
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    existing_tables = inspector.get_table_names()
    
    if 'coloring_book_templates' in existing_tables:
        # Check if column exists before trying to drop it
        existing_columns = [col['name'] for col in inspector.get_columns('coloring_book_templates')]
        
        if 'complexity_level' in existing_columns:
            # Drop the check constraint first
            try:
                op.drop_constraint(
                    'check_complexity_level',
                    'coloring_book_templates',
                    type_='check'
                )
            except Exception:
                pass  # Constraint might not exist
            
            # Drop the column
            op.drop_column('coloring_book_templates', 'complexity_level')


def downgrade() -> None:
    """Re-add complexity_level column to coloring_book_templates table"""
    
    # Add the column back
    op.add_column(
        'coloring_book_templates',
        sa.Column('complexity_level', sa.String(length=20), nullable=True)
    )
    
    # Re-add the check constraint
    op.create_check_constraint(
        'check_complexity_level',
        'coloring_book_templates',
        "complexity_level IN ('simple', 'moderate', 'complex') OR complexity_level IS NULL"
    )
