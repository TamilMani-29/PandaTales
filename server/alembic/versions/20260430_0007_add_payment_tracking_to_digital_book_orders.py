"""Add payment tracking fields to digital_book_orders.

Revision ID: 20260430_0007_add_payment_tracking_to_digital_book_orders
Revises: 20260430_0006_add_age_style_labels_to_books
Create Date: 2026-04-30
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "20260430_0007_add_payment_tracking_to_digital_book_orders"
down_revision: Union[str, None] = "20260430_0006_add_age_style_labels_to_books"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("digital_book_orders", sa.Column("amount", sa.Integer(), nullable=False, server_default="0"))
    op.add_column("digital_book_orders", sa.Column("currency", sa.String(length=10), nullable=False, server_default="INR"))
    op.add_column("digital_book_orders", sa.Column("razorpay_order_id", sa.String(length=100), nullable=True))
    op.add_column("digital_book_orders", sa.Column("razorpay_payment_id", sa.String(length=100), nullable=True))
    op.add_column("digital_book_orders", sa.Column("razorpay_signature", sa.String(length=256), nullable=True))
    op.add_column("digital_book_orders", sa.Column("payment_status", sa.String(length=20), nullable=False, server_default="created"))
    op.add_column("digital_book_orders", sa.Column("payment_error", sa.String(length=255), nullable=True))
    op.add_column("digital_book_orders", sa.Column("paid_at", sa.DateTime(timezone=True), nullable=True))
    op.add_column("digital_book_orders", sa.Column("delivery_status", sa.String(length=20), nullable=False, server_default="pending"))
    op.add_column("digital_book_orders", sa.Column("delivery_sent_at", sa.DateTime(timezone=True), nullable=True))

    op.create_index("ix_digital_book_orders_razorpay_order_id", "digital_book_orders", ["razorpay_order_id"], unique=True)
    op.create_index("ix_digital_book_orders_razorpay_payment_id", "digital_book_orders", ["razorpay_payment_id"], unique=False)
    op.create_index("ix_digital_book_orders_payment_status", "digital_book_orders", ["payment_status"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_digital_book_orders_payment_status", table_name="digital_book_orders")
    op.drop_index("ix_digital_book_orders_razorpay_payment_id", table_name="digital_book_orders")
    op.drop_index("ix_digital_book_orders_razorpay_order_id", table_name="digital_book_orders")

    op.drop_column("digital_book_orders", "delivery_sent_at")
    op.drop_column("digital_book_orders", "delivery_status")
    op.drop_column("digital_book_orders", "paid_at")
    op.drop_column("digital_book_orders", "payment_error")
    op.drop_column("digital_book_orders", "payment_status")
    op.drop_column("digital_book_orders", "razorpay_signature")
    op.drop_column("digital_book_orders", "razorpay_payment_id")
    op.drop_column("digital_book_orders", "razorpay_order_id")
    op.drop_column("digital_book_orders", "currency")
    op.drop_column("digital_book_orders", "amount")
