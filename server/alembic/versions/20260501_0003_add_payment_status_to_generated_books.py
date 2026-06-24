"""add payment_status to generated_books

Revision ID: 20260501_0003_add_payment_status_to_generated_books
Revises: 20260501_0002_add_is_personalized_to_books
Create Date: 2026-05-01 00:03:00

"""

import sqlalchemy as sa
from alembic import op

revision = "20260501_0003_add_payment_status_to_generated_books"
down_revision = "20260501_0002_add_is_personalized_to_books"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "generated_books",
        sa.Column(
            "payment_status",
            sa.String(20),
            nullable=False,
            server_default="pending",
        ),
    )


def downgrade() -> None:
    op.drop_column("generated_books", "payment_status")
