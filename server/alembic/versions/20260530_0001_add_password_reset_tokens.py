"""add password reset tokens table

Revision ID: 20260530_0001
Revises: 20260522_0002
Create Date: 2026-05-30 10:00:00.000000
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = "20260530_0001"
down_revision: str | Sequence[str] | None = "20260522_0002"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    table_name = "password_reset_tokens"

    if table_name not in inspector.get_table_names():
        op.create_table(
            table_name,
            sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
            sa.Column("token_hash", sa.String(length=128), nullable=False),
            sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
            sa.Column("used_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("requested_ip", sa.String(length=64), nullable=True),
            sa.Column("user_agent", sa.String(length=255), nullable=True),
            sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
            sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
            sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
            sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
            sa.PrimaryKeyConstraint("id"),
        )

    existing_indexes = {idx["name"] for idx in inspector.get_indexes(table_name)}
    index_specs = [
        (op.f("ix_password_reset_tokens_expires_at"), ["expires_at"], False),
        (op.f("ix_password_reset_tokens_token_hash"), ["token_hash"], True),
        (op.f("ix_password_reset_tokens_user_id"), ["user_id"], False),
        ("idx_password_reset_tokens_user_expires", ["user_id", "expires_at"], False),
    ]
    for index_name, columns, unique in index_specs:
        if index_name not in existing_indexes:
            op.create_index(index_name, table_name, columns, unique=unique)


def downgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    table_name = "password_reset_tokens"

    if table_name not in inspector.get_table_names():
        return

    existing_indexes = {idx["name"] for idx in inspector.get_indexes(table_name)}
    index_names = [
        "idx_password_reset_tokens_user_expires",
        op.f("ix_password_reset_tokens_user_id"),
        op.f("ix_password_reset_tokens_token_hash"),
        op.f("ix_password_reset_tokens_expires_at"),
    ]
    for index_name in index_names:
        if index_name in existing_indexes:
            op.drop_index(index_name, table_name=table_name)

    op.drop_table(table_name)