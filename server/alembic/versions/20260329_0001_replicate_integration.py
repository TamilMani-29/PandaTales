"""Add replicate_prediction_ids to generated_books and prompts_config to story_book_templates

Revision ID: 20260329_0001_replicate_integration
Revises: 20260321_0002_add_whatsapp_number
Create Date: 2026-03-29
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB

# revision identifiers
revision = "20260329_0001_replicate_integration"
down_revision = "20260321_0002_add_whatsapp_number"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add Replicate prediction tracking column to generated_books
    op.add_column(
        "generated_books",
        sa.Column(
            "replicate_prediction_ids",
            JSONB(),
            nullable=True,
            comment="Per-page Replicate prediction tracking: {page_0: {prediction_id, status, image_object}}",
        ),
    )

    # Add AI generation prompts config to story_book_templates
    op.add_column(
        "story_book_templates",
        sa.Column(
            "prompts_config",
            JSONB(),
            nullable=True,
            comment="AI generation prompts configuration: story_lines, scenes, backgrounds, pages[]",
        ),
    )


def downgrade() -> None:
    op.drop_column("generated_books", "replicate_prediction_ids")
    op.drop_column("story_book_templates", "prompts_config")
