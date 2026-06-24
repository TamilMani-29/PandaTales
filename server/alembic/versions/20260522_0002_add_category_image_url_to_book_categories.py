"""add category_image_url to book_categories

Revision ID: 20260522_0002
Revises: 20260522_0001
Create Date: 2026-05-22 18:20:00.000000
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "20260522_0002"
down_revision: str | Sequence[str] | None = "20260522_0001"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("book_categories", sa.Column("category_image_url", sa.Text(), nullable=True))


def downgrade() -> None:
    op.drop_column("book_categories", "category_image_url")
