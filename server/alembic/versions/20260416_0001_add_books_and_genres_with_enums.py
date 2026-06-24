"""Add books and genres tables with fixed PostgreSQL enums.

Revision ID: 20260416_0001_add_books_and_genres_with_enums
Revises: 20260329_0001_replicate_integration
Create Date: 2026-04-16
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "20260416_0001_add_books_and_genres_with_enums"
down_revision: Union[str, None] = "20260329_0001_replicate_integration"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    bind = op.get_bind()

    book_type_enum = postgresql.ENUM(
        "story",
        "coloring",
        name="book_type_enum",
    )
    theme_enum = postgresql.ENUM(
        "human",
        name="theme_enum",
    )
    style_enum = postgresql.ENUM(
        "animation",
        "illustration",
        name="style_enum",
    )
    age_group_enum = postgresql.ENUM(
        "5-9",
        "10-14",
        name="age_group_enum",
    )
    language_enum = postgresql.ENUM(
        "english",
        name="language_enum",
    )

    book_type_enum.create(bind, checkfirst=True)
    theme_enum.create(bind, checkfirst=True)
    style_enum.create(bind, checkfirst=True)
    age_group_enum.create(bind, checkfirst=True)
    language_enum.create(bind, checkfirst=True)

    op.create_table(
        "genres",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("name", sa.String(length=100), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("name", name="uq_genres_name"),
    )
    op.create_index("ix_genres_name", "genres", ["name"], unique=True)

    op.execute(
        sa.text(
            """
            INSERT INTO genres (name) VALUES
            ('fantasy'),
            ('educational'),
            ('moral'),
            ('adventure'),
            ('comedy'),
            ('bedtime')
            ON CONFLICT (name) DO NOTHING
            """
        )
    )

    op.create_table(
        "books",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("book_name", sa.String(length=255), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("cover_image_url", sa.Text(), nullable=True),
        sa.Column("book_url", sa.Text(), nullable=True),
        sa.Column("total_pages", sa.Integer(), nullable=True),
        sa.Column("book_type", postgresql.ENUM(name="book_type_enum", create_type=False), nullable=True),
        sa.Column("theme", postgresql.ENUM(name="theme_enum", create_type=False), nullable=True),
        sa.Column("style", postgresql.ENUM(name="style_enum", create_type=False), nullable=True),
        sa.Column("age_group", postgresql.ENUM(name="age_group_enum", create_type=False), nullable=True),
        sa.Column("language", postgresql.ENUM(name="language_enum", create_type=False), nullable=True),
        sa.Column("genre_id", sa.Integer(), nullable=True),
        sa.Column("price", sa.Numeric(precision=10, scale=2), nullable=True),
        sa.Column("rating", sa.Float(), nullable=False, server_default="0"),
        sa.Column("total_ratings", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("download_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.ForeignKeyConstraint(["genre_id"], ["genres.id"]),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_index("ix_books_genre_id", "books", ["genre_id"], unique=False)


def downgrade() -> None:
    bind = op.get_bind()

    op.drop_index("ix_books_genre_id", table_name="books")
    op.drop_table("books")

    op.drop_index("ix_genres_name", table_name="genres")
    op.drop_table("genres")

    language_enum = postgresql.ENUM(name="language_enum")
    age_group_enum = postgresql.ENUM(name="age_group_enum")
    style_enum = postgresql.ENUM(name="style_enum")
    theme_enum = postgresql.ENUM(name="theme_enum")
    book_type_enum = postgresql.ENUM(name="book_type_enum")

    language_enum.drop(bind, checkfirst=True)
    age_group_enum.drop(bind, checkfirst=True)
    style_enum.drop(bind, checkfirst=True)
    theme_enum.drop(bind, checkfirst=True)
    book_type_enum.drop(bind, checkfirst=True)
