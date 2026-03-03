"""add_generation_configs_table

Revision ID: f3b2c1a8e7d6
Revises: e960767bca8c
Create Date: 2026-03-01 00:03:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = 'f3b2c1a8e7d6'
down_revision: Union[str, None] = '20260301_0002_b2c3d4e5f6g7'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create generation_configs table for admin-managed configurations"""
    
    # Check if table exists
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    existing_tables = inspector.get_table_names()
    
    # Create generation_configs table only if it doesn't exist
    if 'generation_configs' not in existing_tables:
        op.create_table(
            'generation_configs',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column('name', sa.String(length=100), nullable=False),
        sa.Column('display_name', sa.String(length=200), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('config_type', sa.String(length=50), nullable=False),
        sa.Column('config_data', postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default='{}'),
        sa.Column('category', sa.String(length=100), nullable=True),
        sa.Column('tags', postgresql.ARRAY(sa.String()), nullable=True),
        sa.Column('applies_to', sa.String(length=50), nullable=True),
        sa.Column('max_photos', sa.Integer(), nullable=True),
        sa.Column('min_photos', sa.Integer(), nullable=True),
        sa.Column('preview_image_url', sa.String(length=500), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('is_premium', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('is_default', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('sort_order', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('usage_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        
        # Constraints
        sa.CheckConstraint(
            "config_type IN ('theme', 'prompt_template', 'style_preset', 'generation_parameter')",
            name='check_generation_config_type'
        ),
        sa.CheckConstraint(
            "applies_to IN ('photo_to_coloring', 'theme_based', 'both')",
            name='check_generation_config_applies_to'
        ),
        sa.CheckConstraint(
            'max_photos IS NULL OR max_photos >= 1',
            name='check_max_photos_positive'
        ),
        sa.CheckConstraint(
            'min_photos IS NULL OR min_photos >= 1',
            name='check_min_photos_positive'
        ),
        sa.CheckConstraint(
            '(min_photos IS NULL AND max_photos IS NULL) OR (min_photos <= max_photos)',
            name='check_min_max_photos_range'
        ),
        sa.UniqueConstraint('name', name='uq_generation_configs_name'),
    )
    
    # Create indexes for generation_configs only if table was just created
    if 'generation_configs' not in existing_tables:
        op.create_index('idx_generation_configs_config_type', 'generation_configs', ['config_type'])
        op.create_index('idx_generation_configs_category', 'generation_configs', ['category'])
        op.create_index('idx_generation_configs_applies_to', 'generation_configs', ['applies_to'])
        op.create_index('idx_generation_configs_is_active', 'generation_configs', ['is_active'])
        op.create_index('idx_generation_configs_is_premium', 'generation_configs', ['is_premium'])
        op.create_index('idx_generation_configs_is_default', 'generation_configs', ['is_default'])
        op.create_index('idx_generation_configs_sort_order', 'generation_configs', ['sort_order'])
        op.create_index('idx_generation_configs_usage_count', 'generation_configs', ['usage_count'])
        op.create_index('idx_generation_configs_created_at', 'generation_configs', ['created_at'])
        
        # Create GIN index for JSONB config_data for faster queries
        op.create_index(
            'idx_generation_configs_config_data_gin',
            'generation_configs',
            ['config_data'],
            postgresql_using='gin'
        )


def downgrade() -> None:
    """Drop generation_configs table"""
    op.drop_table('generation_configs')
