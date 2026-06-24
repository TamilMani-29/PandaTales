"""Add is_bestseller boolean column to books table.

Revision ID: 20260430_0004_add_is_bestseller_to_books
Revises: 20260430_0003_auth_and_digital_books_frontend_alignment
Create Date: 2026-04-30
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "20260430_0004_add_is_bestseller_to_books"
down_revision: Union[str, None] = "20260430_0003_auth_and_digital_books_frontend_alignment"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "books",
        sa.Column(
            "is_bestseller",
            sa.Boolean(),
            nullable=False,
            server_default="false",
        ),
    )
    # Auto-mark existing books as bestseller if they already have a BESTSELLER tag
    op.execute(
        sa.text(
            """
            UPDATE books
            SET is_bestseller = true
            WHERE LOWER(book_tag) = 'bestseller'
            """
        )
    )


def downgrade() -> None:
    op.drop_column("books", "is_bestseller")
