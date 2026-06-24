"""Add optional book_tag column to books.

Revision ID: 20260424_0002_add_book_tag_to_books
Revises: 20260424_0001_add_front_back_images_to_books
Create Date: 2026-04-24
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "20260424_0002_add_book_tag_to_books"
down_revision: Union[str, None] = "20260424_0001_add_front_back_images_to_books"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("books", sa.Column("book_tag", sa.String(length=80), nullable=True))
    op.execute(
        sa.text(
            """
            UPDATE books
            SET book_tag = 'BESTSELLER'
            WHERE total_ratings >= 80
            """
        )
    )


def downgrade() -> None:
    op.drop_column("books", "book_tag")
