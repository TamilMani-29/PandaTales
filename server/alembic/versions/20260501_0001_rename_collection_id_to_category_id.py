"""rename collection_id to category_id in books and book_categories

Revision ID: 20260501_0001_rename_collection_id_to_category_id
Revises: 20260430_0010_convert_collection_id_to_integer
Create Date: 2026-05-01
"""

from alembic import op

revision: str = "20260501_0001_rename_collection_id_to_category_id"
down_revision: str = "20260430_0010_convert_collection_id_to_integer"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Rename index before renaming column (PostgreSQL requires this)
    op.drop_index("ix_book_categories_collection_id", table_name="book_categories")
    op.alter_column("book_categories", "collection_id", new_column_name="category_id")
    op.create_index("ix_book_categories_category_id", "book_categories", ["category_id"], unique=True)

    op.alter_column("books", "collection_id", new_column_name="category_id")


def downgrade() -> None:
    op.alter_column("books", "category_id", new_column_name="collection_id")

    op.drop_index("ix_book_categories_category_id", table_name="book_categories")
    op.alter_column("book_categories", "category_id", new_column_name="collection_id")
    op.create_index("ix_book_categories_collection_id", "book_categories", ["collection_id"], unique=True)
