"""make_parent_email_required

Revision ID: 20260321_0001_parent_email_required
Revises: c1d2e3f4a5b6
Create Date: 2026-03-21 00:00:00.000000

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "20260321_0001_parent_email_required"
down_revision: Union[str, None] = "c1d2e3f4a5b6"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Back-fill any existing NULL rows with a placeholder so the NOT NULL
    # constraint can be applied without violating existing data.
    op.execute(
        "UPDATE generated_books SET parent_email = 'unknown@pandorapages.in' WHERE parent_email IS NULL"
    )
    op.alter_column(
        "generated_books",
        "parent_email",
        existing_type=sa.String(length=255),
        nullable=False,
    )


def downgrade() -> None:
    op.alter_column(
        "generated_books",
        "parent_email",
        existing_type=sa.String(length=255),
        nullable=True,
    )
