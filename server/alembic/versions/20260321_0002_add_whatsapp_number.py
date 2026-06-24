"""add_whatsapp_number_to_orders_and_generated_books

Revision ID: 20260321_0002_add_whatsapp_number
Revises: 20260321_0001_parent_email_required
Create Date: 2026-03-21 00:00:00.000000

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "20260321_0002_add_whatsapp_number"
down_revision: Union[str, None] = "20260321_0001_parent_email_required"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "generated_books",
        sa.Column("whatsapp_number", sa.String(length=20), nullable=True),
    )
    op.add_column(
        "orders",
        sa.Column("whatsapp_number", sa.String(length=20), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("orders", "whatsapp_number")
    op.drop_column("generated_books", "whatsapp_number")
