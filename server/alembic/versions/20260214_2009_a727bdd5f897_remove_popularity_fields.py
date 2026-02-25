# Alembic Migration Script Template
# This is the default template for new migrations

"""remove_popularity_fields

Revision ID: a727bdd5f897
Revises: 6605ff3f90bc
Create Date: 2026-02-14 20:09:52.513306

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'a727bdd5f897'
down_revision: Union[str, None] = '6605ff3f90bc'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Remove popularity-related columns
    op.drop_column('book_templates', 'is_popular')
    op.drop_column('book_templates', 'total_generated')


def downgrade() -> None:
    # Restore popularity-related columns
    op.add_column('book_templates', sa.Column('total_generated', sa.Integer(), nullable=False, server_default='0'))
    op.add_column('book_templates', sa.Column('is_popular', sa.Boolean(), nullable=False, server_default='false'))
