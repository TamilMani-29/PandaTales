"""rename tag to personalized_tag in book_categories

Revision ID: 20260430_0008
Revises: 20260430_0007_add_payment_tracking_to_digital_book_orders
Create Date: 2026-04-30
"""

from alembic import op

revision = "20260430_0008_rename_tag_to_personalized_tag"
down_revision = "20260430_0007_add_payment_tracking_to_digital_book_orders"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.alter_column("book_categories", "tag", new_column_name="personalized_tag")


def downgrade() -> None:
    op.alter_column("book_categories", "personalized_tag", new_column_name="tag")
