"""convert collection_id columns to integer in books and book_categories

Revision ID: 20260430_0010_convert_collection_id_to_integer
Revises: 20260430_0009_add_label_to_book_categories
Create Date: 2026-04-30
"""

from alembic import op
import sqlalchemy as sa

revision: str = "20260430_0010_convert_collection_id_to_integer"
down_revision: str = "20260430_0009_add_label_to_book_categories"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("book_categories", sa.Column("collection_id_int", sa.Integer(), nullable=True))
    op.execute(sa.text("UPDATE book_categories SET collection_id_int = id"))

    op.add_column("books", sa.Column("collection_id_int", sa.Integer(), nullable=True))
    op.execute(
        sa.text(
            """
            UPDATE books b
            SET collection_id_int = bc.id
            FROM book_categories bc
            WHERE b.collection_id = bc.collection_id
            """
        )
    )

    op.drop_column("books", "collection_id")
    op.drop_column("book_categories", "collection_id")

    op.alter_column("book_categories", "collection_id_int", new_column_name="collection_id")
    op.alter_column("books", "collection_id_int", new_column_name="collection_id")

    op.alter_column("book_categories", "collection_id", nullable=False)
    op.create_index("ix_book_categories_collection_id", "book_categories", ["collection_id"], unique=True)


def downgrade() -> None:
    op.add_column("book_categories", sa.Column("collection_id_str", sa.String(length=80), nullable=True))
    op.execute(sa.text("UPDATE book_categories SET collection_id_str = CAST(collection_id AS TEXT)"))

    op.add_column("books", sa.Column("collection_id_str", sa.String(length=80), nullable=True))
    op.execute(sa.text("UPDATE books SET collection_id_str = CAST(collection_id AS TEXT) WHERE collection_id IS NOT NULL"))

    op.drop_index("ix_book_categories_collection_id", table_name="book_categories")
    op.drop_column("books", "collection_id")
    op.drop_column("book_categories", "collection_id")

    op.alter_column("book_categories", "collection_id_str", new_column_name="collection_id")
    op.alter_column("books", "collection_id_str", new_column_name="collection_id")

    op.alter_column("book_categories", "collection_id", nullable=False)
    op.create_index("ix_book_categories_collection_id", "book_categories", ["collection_id"], unique=True)
