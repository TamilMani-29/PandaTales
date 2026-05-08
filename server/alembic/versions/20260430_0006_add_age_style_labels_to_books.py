"""Add age_label and style_label to books for frontend parity.

Revision ID: 20260430_0006_add_age_style_labels_to_books
Revises: 20260430_0005_create_book_categories_table
Create Date: 2026-04-30
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "20260430_0006_add_age_style_labels_to_books"
down_revision: Union[str, None] = "20260430_0005_create_book_categories_table"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("books", sa.Column("age_label", sa.String(length=32), nullable=True))
    op.add_column("books", sa.Column("style_label", sa.String(length=64), nullable=True))


def downgrade() -> None:
    op.drop_column("books", "style_label")
    op.drop_column("books", "age_label")
