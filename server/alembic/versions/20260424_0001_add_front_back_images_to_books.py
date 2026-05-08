"""Add front and back image URL columns to books.

Revision ID: 20260424_0001_add_front_back_images_to_books
Revises: 20260416_0001_add_books_and_genres_with_enums
Create Date: 2026-04-24
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "20260424_0001_add_front_back_images_to_books"
down_revision: Union[str, None] = "20260416_0001_add_books_and_genres_with_enums"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("books", sa.Column("front_image_url", sa.Text(), nullable=True))
    op.add_column("books", sa.Column("back_image_url", sa.Text(), nullable=True))
    op.execute(
        sa.text(
            """
            UPDATE books
            SET front_image_url = cover_image_url,
                back_image_url = cover_image_url
            WHERE cover_image_url IS NOT NULL
            """
        )
    )


def downgrade() -> None:
    op.drop_column("books", "back_image_url")
    op.drop_column("books", "front_image_url")
