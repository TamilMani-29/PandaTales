"""Create book_categories table for collection metadata.

Revision ID: 20260430_0005_create_book_categories_table
Revises: 20260430_0004_add_is_bestseller_to_books
Create Date: 2026-04-30
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "20260430_0005_create_book_categories_table"
down_revision: Union[str, None] = "20260430_0004_add_is_bestseller_to_books"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "book_categories",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("collection_id", sa.String(length=80), nullable=False),
        sa.Column("name", sa.String(length=120), nullable=False),
        sa.Column("tag", sa.String(length=160), nullable=True),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("emoji", sa.String(length=16), nullable=True),
        sa.Column("color", sa.String(length=32), nullable=True),
        sa.Column("grad", sa.Text(), nullable=True),
        sa.Column("personalized", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.UniqueConstraint("collection_id", name="uq_book_categories_collection_id"),
    )
    op.create_index("ix_book_categories_collection_id", "book_categories", ["collection_id"], unique=True)


def downgrade() -> None:
    op.drop_index("ix_book_categories_collection_id", table_name="book_categories")
    op.drop_table("book_categories")
