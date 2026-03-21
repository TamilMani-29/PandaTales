"""create_orders_table

Revision ID: 20260315_0001_create_orders_table
Revises: b94270a691ca
Create Date: 2026-03-15 00:00:00.000000

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import UUID

# revision identifiers, used by Alembic.
revision: str = "c1d2e3f4a5b6"
down_revision: Union[str, None] = "b94270a691ca"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    if "orders" in inspector.get_table_names():
        return  # table already exists, nothing to do

    op.create_table(
        "orders",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "user_id",
            UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "book_id",
            UUID(as_uuid=True),
            sa.ForeignKey("generated_books.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("format", sa.String(20), nullable=False),
        sa.Column("amount", sa.Integer, nullable=False),
        sa.Column("currency", sa.String(10), nullable=False, server_default="INR"),
        sa.Column("razorpay_order_id", sa.String(100), nullable=False, unique=True),
        sa.Column("razorpay_payment_id", sa.String(100), nullable=True),
        sa.Column("razorpay_signature", sa.String(256), nullable=True),
        sa.Column("status", sa.String(20), nullable=False, server_default="created"),
        sa.Column("paid_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.CheckConstraint(
            "format IN ('digital', 'softcover', 'hardcover')",
            name="check_order_format",
        ),
        sa.CheckConstraint(
            "status IN ('created', 'paid', 'failed')",
            name="check_order_status",
        ),
    )

    op.create_index("ix_orders_user_id", "orders", ["user_id"])
    op.create_index("ix_orders_book_id", "orders", ["book_id"])
    op.create_index("ix_orders_razorpay_order_id", "orders", ["razorpay_order_id"])
    op.create_index("ix_orders_razorpay_payment_id", "orders", ["razorpay_payment_id"])
    op.create_index("ix_orders_status", "orders", ["status"])


def downgrade() -> None:
    op.drop_table("orders")
