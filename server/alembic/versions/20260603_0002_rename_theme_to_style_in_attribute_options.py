"""rename theme to style in book_attribute_options

Revision ID: 20260603_0002
Revises: 20260603_0001
Create Date: 2026-06-03 12:00:00.000000
"""

from collections.abc import Sequence

from alembic import op


# revision identifiers, used by Alembic.
revision: str = "20260603_0002"
down_revision: str | Sequence[str] | None = "20260603_0001"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.execute(
        "UPDATE book_attribute_options SET option_type = 'style' WHERE option_type = 'theme'"
    )


def downgrade() -> None:
    op.execute(
        "UPDATE book_attribute_options SET option_type = 'theme' WHERE option_type = 'style'"
    )
