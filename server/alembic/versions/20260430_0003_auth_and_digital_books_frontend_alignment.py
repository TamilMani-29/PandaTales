"""auth and digital books frontend alignment

Revision ID: 20260430_0003_auth_and_digital_books_frontend_alignment
Revises: 20260424_0002_add_book_tag_to_books
Create Date: 2026-04-30
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "20260430_0003_auth_and_digital_books_frontend_alignment"
down_revision: Union[str, None] = "20260424_0002_add_book_tag_to_books"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("users", sa.Column("full_name", sa.String(length=200), nullable=True))
    op.add_column("users", sa.Column("referral_code", sa.String(length=20), nullable=True))
    op.add_column(
        "users",
        sa.Column("referral_count", sa.Integer(), nullable=False, server_default="0"),
    )

    op.execute(
        sa.text(
            """
            UPDATE users
            SET full_name = TRIM(COALESCE(first_name, '') || ' ' || COALESCE(last_name, ''))
            WHERE full_name IS NULL
            """
        )
    )

    op.execute(
        sa.text(
            """
            UPDATE users
            SET referral_code = CONCAT('PP', UPPER(SUBSTRING(MD5(id::text) FROM 1 FOR 6)))
            WHERE referral_code IS NULL
            """
        )
    )

    op.alter_column("users", "referral_code", nullable=False)
    op.create_unique_constraint("uq_users_referral_code", "users", ["referral_code"])
    op.create_index("ix_users_referral_code", "users", ["referral_code"], unique=False)

    op.add_column("books", sa.Column("collection_id", sa.String(length=80), nullable=True))
    op.add_column("books", sa.Column("emoji", sa.String(length=16), nullable=True))

    op.create_table(
        "digital_book_orders",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("book_id", sa.Integer(), nullable=False),
        sa.Column("delivery_method", sa.String(length=20), nullable=False),
        sa.Column("delivery_contact", sa.String(length=120), nullable=False),
        sa.Column("status", sa.String(length=30), nullable=False, server_default="paid"),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("CURRENT_TIMESTAMP"),
        ),
        sa.ForeignKeyConstraint(["book_id"], ["books.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_digital_book_orders_user_id", "digital_book_orders", ["user_id"], unique=False)
    op.create_index("ix_digital_book_orders_book_id", "digital_book_orders", ["book_id"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_digital_book_orders_book_id", table_name="digital_book_orders")
    op.drop_index("ix_digital_book_orders_user_id", table_name="digital_book_orders")
    op.drop_table("digital_book_orders")

    op.drop_column("books", "emoji")
    op.drop_column("books", "collection_id")

    op.drop_index("ix_users_referral_code", table_name="users")
    op.drop_constraint("uq_users_referral_code", "users", type_="unique")
    op.drop_column("users", "referral_count")
    op.drop_column("users", "referral_code")
    op.drop_column("users", "full_name")
