"""Drop obsolete book_tag column from books.

Revision ID: 20260517_0001_drop_book_tag_from_books
Revises: 20260508_0001_book_attribute_options_and_dynamic_fields
Create Date: 2026-05-17
"""

from typing import Union

import sqlalchemy as sa
from alembic import op


# revision identifiers, used by Alembic.
revision: str = "20260517_0001_drop_book_tag_from_books"
down_revision: Union[str, None] = "20260508_0001_book_attribute_options_and_dynamic_fields"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.drop_column("books", "book_tag")


def downgrade() -> None:
    op.add_column("books", sa.Column("book_tag", sa.String(length=80), nullable=True))
