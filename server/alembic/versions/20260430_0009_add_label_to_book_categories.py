"""add label column to book_categories

Revision ID: 20260430_0009_add_label_to_book_categories
Revises: 20260430_0008_rename_tag_to_personalized_tag
Create Date: 2026-04-30
"""

from alembic import op
import sqlalchemy as sa

revision: str = "20260430_0009_add_label_to_book_categories"
down_revision: str = "20260430_0008_rename_tag_to_personalized_tag"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("book_categories", sa.Column("label", sa.String(80), nullable=True))


def downgrade() -> None:
    op.drop_column("book_categories", "label")
