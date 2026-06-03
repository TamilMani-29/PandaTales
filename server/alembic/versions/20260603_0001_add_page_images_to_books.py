"""add page image urls to books

Revision ID: 20260603_0001
Revises: 20260530_0001
Create Date: 2026-06-03 10:00:00.000000
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "20260603_0001"
down_revision: str | Sequence[str] | None = "20260530_0001"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    columns = {col["name"] for col in inspector.get_columns("books")}

    additions = [
        "page_1_image_url",
        "page_2_image_url",
        "page_3_image_url",
        "page_4_image_url",
    ]

    for name in additions:
        if name not in columns:
            op.add_column("books", sa.Column(name, sa.Text(), nullable=True))


def downgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    columns = {col["name"] for col in inspector.get_columns("books")}

    removals = [
        "page_4_image_url",
        "page_3_image_url",
        "page_2_image_url",
        "page_1_image_url",
    ]

    for name in removals:
        if name in columns:
            op.drop_column("books", name)
