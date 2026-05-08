"""add is_personalized to books

Revision ID: 20260501_0002_add_is_personalized_to_books
Revises: 20260501_0001_rename_collection_id_to_category_id
Create Date: 2026-05-01
"""

import sqlalchemy as sa
from alembic import op

revision: str = "20260501_0002_add_is_personalized_to_books"
down_revision: str = "20260501_0001_rename_collection_id_to_category_id"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "books",
        sa.Column(
            "is_personalized",
            sa.Boolean(),
            nullable=False,
            server_default="false",
        ),
    )


def downgrade() -> None:
    op.drop_column("books", "is_personalized")
