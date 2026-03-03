"""Create generated_books table

Revision ID: 20260301_0002_b2c3d4e5f6g7
Revises: 20260301_0001_a1b2c3d4e5f6
Create Date: 2026-03-01 12:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '20260301_0002_b2c3d4e5f6g7'
down_revision: Union[str, None] = '20260301_0001'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Check if table exists
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    existing_tables = inspector.get_table_names()
    
    # Create generated_books table only if it doesn't exist
    if 'generated_books' not in existing_tables:
        op.create_table(
            'generated_books',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('template_type', sa.String(length=20), nullable=False),
        sa.Column('template_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('child_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('child_name', sa.String(length=100), nullable=False),
        sa.Column('child_age', sa.Integer(), nullable=False),
        sa.Column('child_gender', sa.String(length=20), nullable=False),
        sa.Column('status', sa.String(length=20), nullable=False),
        sa.Column('progress', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('current_step', sa.String(length=100), nullable=True),
        sa.Column('queue_position', sa.Integer(), nullable=True),
        sa.Column('estimated_completion_time', sa.Integer(), nullable=True),
        sa.Column('generation_steps', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('photos', postgresql.ARRAY(sa.String()), nullable=False, server_default='{}'),
        sa.Column('cover_image_url', sa.String(length=500), nullable=True),
        sa.Column('total_pages', sa.Integer(), nullable=True),
        sa.Column('preview_pages', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('is_purchased', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('purchased_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('generation_duration', sa.Integer(), nullable=True),
        sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('failed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('error_code', sa.String(length=50), nullable=True),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('error_details', sa.Text(), nullable=True),
        sa.Column('parent_email', sa.String(length=255), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['child_id'], ['child_profiles.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.CheckConstraint("template_type IN ('story_book', 'coloring_book')", name='check_template_type'),
        sa.CheckConstraint("status IN ('queued', 'processing', 'completed', 'failed', 'cancelled')", name='check_status'),
        sa.CheckConstraint('progress >= 0 AND progress <= 100', name='check_progress_range'),
        sa.CheckConstraint('child_age > 0 AND child_age <= 18', name='check_child_age'),
    )

    # Create indexes only if table was just created
    if 'generated_books' not in existing_tables:
        op.create_index('idx_generated_books_user_status', 'generated_books', ['user_id', 'status'])
        op.create_index('idx_generated_books_status_created', 'generated_books', ['status', 'created_at'])
        op.create_index(op.f('ix_generated_books_child_id'), 'generated_books', ['child_id'])
        op.create_index(op.f('ix_generated_books_completed_at'), 'generated_books', ['completed_at'])
        op.create_index(op.f('ix_generated_books_is_purchased'), 'generated_books', ['is_purchased'])
        op.create_index(op.f('ix_generated_books_status'), 'generated_books', ['status'])
        op.create_index(op.f('ix_generated_books_template_id'), 'generated_books', ['template_id'])
        op.create_index(op.f('ix_generated_books_template_type'), 'generated_books', ['template_type'])
        op.create_index(op.f('ix_generated_books_user_id'), 'generated_books', ['user_id'])


def downgrade() -> None:
    # Drop indexes
    op.drop_index(op.f('ix_generated_books_user_id'), table_name='generated_books')
    op.drop_index(op.f('ix_generated_books_template_type'), table_name='generated_books')
    op.drop_index(op.f('ix_generated_books_template_id'), table_name='generated_books')
    op.drop_index(op.f('ix_generated_books_status'), table_name='generated_books')
    op.drop_index(op.f('ix_generated_books_is_purchased'), table_name='generated_books')
    op.drop_index(op.f('ix_generated_books_completed_at'), table_name='generated_books')
    op.drop_index(op.f('ix_generated_books_child_id'), table_name='generated_books')
    op.drop_index('idx_generated_books_status_created', table_name='generated_books')
    op.drop_index('idx_generated_books_user_status', table_name='generated_books')

    # Drop table
    op.drop_table('generated_books')
