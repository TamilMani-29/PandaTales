"""book attribute options and dynamic fields

Revision ID: 20260508_0001_book_attribute_options_and_dynamic_fields
Revises: 20260501_0003_add_payment_status_to_generated_books
Create Date: 2026-05-08 12:00:00

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op


revision: str = "20260508_0001_book_attribute_options_and_dynamic_fields"
down_revision: Union[str, None] = "20260501_0003_add_payment_status_to_generated_books"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _table_exists(bind, table_name: str) -> bool:
    return sa.inspect(bind).has_table(table_name)


def _column_exists(bind, table_name: str, column_name: str) -> bool:
    cols = [c["name"] for c in sa.inspect(bind).get_columns(table_name)]
    return column_name in cols


def upgrade() -> None:
    bind = op.get_bind()

    # 1. Create book_attribute_options table (skip if already exists)
    if not _table_exists(bind, "book_attribute_options"):
        op.create_table(
            "book_attribute_options",
            sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
            sa.Column("option_type", sa.String(length=30), nullable=False),
            sa.Column("value", sa.String(length=100), nullable=False),
            sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
            sa.PrimaryKeyConstraint("id"),
            sa.UniqueConstraint("option_type", "value", name="uq_book_attribute_options_type_value"),
        )

    existing_indexes = [idx["name"] for idx in sa.inspect(bind).get_indexes("book_attribute_options")]
    if "ix_book_attribute_options_option_type" not in existing_indexes:
        op.create_index("ix_book_attribute_options_option_type", "book_attribute_options", ["option_type"], unique=False)

    # 2. Seed default options
    op.execute(
        sa.text(
            """
            INSERT INTO book_attribute_options (option_type, value, is_active) VALUES
                ('book_type', 'story', true),
                ('book_type', 'coloring', true),
                ('book_type', 'activity', true),
                ('book_type', 'workbook', true),
                ('book_type', 'comic', true),
                ('book_type', 'poetry', true),
                ('theme', 'human', true),
                ('theme', 'animal', true),
                ('theme', 'fantasy', true),
                ('theme', 'nature', true),
                ('theme', 'space', true),
                ('theme', 'ocean', true),
                ('theme', 'jungle', true),
                ('theme', 'mythology', true),
                ('theme', 'sports', true),
                ('theme', 'technology', true),
                ('language', 'english', true),
                ('language', 'hindi', true),
                ('language', 'tamil', true),
                ('language', 'telugu', true),
                ('language', 'kannada', true),
                ('language', 'malayalam', true),
                ('language', 'marathi', true),
                ('language', 'bengali', true),
                ('language', 'gujarati', true),
                ('language', 'punjabi', true)
            ON CONFLICT (option_type, value) DO NOTHING
            """
        )
    )

    # 3. Convert existing enum columns to text (only if they are still enum types)
    books_cols = {c["name"]: c for c in sa.inspect(bind).get_columns("books")}
    for col_name in ("book_type", "theme", "language"):
        col = books_cols.get(col_name)
        if col is not None and hasattr(col["type"], "enums"):
            op.execute(sa.text(f"ALTER TABLE books ALTER COLUMN {col_name} TYPE VARCHAR(50) USING {col_name}::text"))

    # 4. Add new FK integer columns (skip if already present)
    books_cols = {c["name"] for c in sa.inspect(bind).get_columns("books")}
    if "book_type_id" not in books_cols:
        op.add_column("books", sa.Column("book_type_id", sa.Integer(), nullable=True))
    if "theme_id" not in books_cols:
        op.add_column("books", sa.Column("theme_id", sa.Integer(), nullable=True))
    if "language_id" not in books_cols:
        op.add_column("books", sa.Column("language_id", sa.Integer(), nullable=True))

    existing_fks = {fk["name"] for fk in sa.inspect(bind).get_foreign_keys("books")}
    if "fk_books_book_type_id" not in existing_fks:
        op.create_foreign_key("fk_books_book_type_id", "books", "book_attribute_options", ["book_type_id"], ["id"])
    if "fk_books_theme_id" not in existing_fks:
        op.create_foreign_key("fk_books_theme_id", "books", "book_attribute_options", ["theme_id"], ["id"])
    if "fk_books_language_id" not in existing_fks:
        op.create_foreign_key("fk_books_language_id", "books", "book_attribute_options", ["language_id"], ["id"])

    # 5. Migrate existing string data to FK IDs
    op.execute(sa.text("""
        UPDATE books SET book_type_id = bao.id
        FROM book_attribute_options bao
        WHERE bao.option_type = 'book_type' AND bao.value = books.book_type
    """))
    op.execute(sa.text("""
        UPDATE books SET theme_id = bao.id
        FROM book_attribute_options bao
        WHERE bao.option_type = 'theme' AND bao.value = books.theme
    """))
    op.execute(sa.text("""
        UPDATE books SET language_id = bao.id
        FROM book_attribute_options bao
        WHERE bao.option_type = 'language' AND bao.value = books.language
    """))

    # 6. Drop old string columns (only if they still exist)
    remaining_cols = {c["name"] for c in sa.inspect(bind).get_columns("books")}
    for col_name in ("book_type", "theme", "language"):
        if col_name in remaining_cols:
            op.drop_column("books", col_name)

    # 7. Drop old enum types
    op.execute(sa.text("DROP TYPE IF EXISTS book_type_enum"))
    op.execute(sa.text("DROP TYPE IF EXISTS theme_enum"))
    op.execute(sa.text("DROP TYPE IF EXISTS language_enum"))


def downgrade() -> None:
    # Restore string columns from FK IDs
    op.add_column("books", sa.Column("book_type", sa.String(50), nullable=True))
    op.add_column("books", sa.Column("theme", sa.String(50), nullable=True))
    op.add_column("books", sa.Column("language", sa.String(50), nullable=True))

    op.execute(sa.text("""
        UPDATE books SET book_type = bao.value
        FROM book_attribute_options bao WHERE bao.id = books.book_type_id
    """))
    op.execute(sa.text("""
        UPDATE books SET theme = bao.value
        FROM book_attribute_options bao WHERE bao.id = books.theme_id
    """))
    op.execute(sa.text("""
        UPDATE books SET language = bao.value
        FROM book_attribute_options bao WHERE bao.id = books.language_id
    """))

    op.drop_constraint("fk_books_book_type_id", "books", type_="foreignkey")
    op.drop_constraint("fk_books_theme_id", "books", type_="foreignkey")
    op.drop_constraint("fk_books_language_id", "books", type_="foreignkey")
    op.drop_column("books", "book_type_id")
    op.drop_column("books", "theme_id")
    op.drop_column("books", "language_id")

    op.drop_index("ix_book_attribute_options_option_type", table_name="book_attribute_options")
    op.drop_table("book_attribute_options")

    # Placeholder to satisfy original downgrade structure
    op.execute(
        sa.text(
            """
            ALTER TABLE books
            ALTER COLUMN book_type TYPE book_type_enum
            USING (
                CASE
                    WHEN book_type IN ('story', 'coloring') THEN book_type::book_type_enum
                    ELSE NULL
                END
            )
            """
        )
    )
    op.execute(
        sa.text(
            """
            ALTER TABLE books
            ALTER COLUMN theme TYPE theme_enum
            USING (
                CASE
                    WHEN theme IN ('human') THEN theme::theme_enum
                    ELSE NULL
                END
            )
            """
        )
    )
    op.execute(
        sa.text(
            """
            ALTER TABLE books
            ALTER COLUMN language TYPE language_enum
            USING (
                CASE
                    WHEN language IN ('english') THEN language::language_enum
                    ELSE NULL
                END
            )
            """
        )
    )

    op.drop_index("ix_book_attribute_options_option_type", table_name="book_attribute_options")
    op.drop_table("book_attribute_options")
