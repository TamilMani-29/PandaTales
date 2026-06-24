"""remove_features_learning_outcomes_from_coloring_books

Revision ID: c7d8e9f0a1b2
Revises: b5d6e7f8a9c0
Create Date: 2026-03-01 00:06:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = 'c7d8e9f0a1b2'
down_revision: Union[str, None] = 'b5d6e7f8a9c0'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Remove features and learning_outcomes columns from coloring_book_templates table"""
    
    # Check if table exists
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    existing_tables = inspector.get_table_names()
    
    if 'coloring_book_templates' in existing_tables:
        # Check which columns exist before trying to drop them
        existing_columns = [col['name'] for col in inspector.get_columns('coloring_book_templates')]
        
        if 'features' in existing_columns:
            op.drop_column('coloring_book_templates', 'features')
        
        if 'learning_outcomes' in existing_columns:
            op.drop_column('coloring_book_templates', 'learning_outcomes')


def downgrade() -> None:
    """Re-add features and learning_outcomes columns to coloring_book_templates table"""
    
    # Add the columns back
    op.add_column(
        'coloring_book_templates',
        sa.Column(
            'features',
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
            server_default=sa.text("'[]'::jsonb")
        )
    )
    
    op.add_column(
        'coloring_book_templates',
        sa.Column(
            'learning_outcomes',
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
            server_default=sa.text("'[]'::jsonb")
        )
    )
