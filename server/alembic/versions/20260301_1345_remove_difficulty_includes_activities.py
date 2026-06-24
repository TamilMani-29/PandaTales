"""remove difficulty and includes_activities from coloring_book_templates

Revision ID: 20260301_1345
Revises: 20260301_0006
Create Date: 2026-03-01 13:45:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '20260301_1345'
down_revision: Union[str, None] = 'c7d8e9f0a1b2'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Check if table and columns exist
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    existing_tables = inspector.get_table_names()
    
    if 'coloring_book_templates' in existing_tables:
        existing_columns = [col['name'] for col in inspector.get_columns('coloring_book_templates')]
        
        # Drop the difficulty column if it exists
        if 'difficulty' in existing_columns:
            # Try to drop the constraint first (may not exist)
            try:
                op.drop_constraint('check_coloring_difficulty', 'coloring_book_templates', type_='check')
            except:
                pass
            
            # Try to drop the index (may not exist)
            try:
                op.drop_index('idx_coloring_templates_difficulty', table_name='coloring_book_templates')
            except:
                pass
            
            op.drop_column('coloring_book_templates', 'difficulty')
        
        # Drop the includes_activities column if it exists
        if 'includes_activities' in existing_columns:
            op.drop_column('coloring_book_templates', 'includes_activities')


def downgrade() -> None:
    # Add back the includes_activities column
    op.add_column('coloring_book_templates', 
                  sa.Column('includes_activities', sa.Boolean(), nullable=False, server_default='false'))
    
    # Add back the difficulty column
    op.add_column('coloring_book_templates',
                  sa.Column('difficulty', sa.String(length=20), nullable=False, server_default='medium'))
    
    # Recreate the difficulty index
    op.create_index('idx_coloring_templates_difficulty', 'coloring_book_templates', ['difficulty'])
    
    # Recreate the difficulty check constraint
    op.create_check_constraint(
        'check_coloring_difficulty',
        'coloring_book_templates',
        "difficulty IN ('easy', 'medium', 'hard')"
    )
