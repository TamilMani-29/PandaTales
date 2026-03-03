"""update_generated_books_for_coloring_types

Revision ID: a4c3d2e1f0b9
Revises: f3b2c1a8e7d6
Create Date: 2026-03-01 00:04:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = 'a4c3d2e1f0b9'
down_revision: Union[str, None] = 'f3b2c1a8e7d6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Update generated_books table for coloring book generation types"""
    
    # Check if generated_books table exists
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    existing_tables = inspector.get_table_names()
    
    if 'generated_books' not in existing_tables:
        # If table doesn't exist, create it with all fields
        op.create_table(
            'generated_books',
            sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
            sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
            sa.Column('template_type', sa.String(length=50), nullable=False),
            sa.Column('template_id', postgresql.UUID(as_uuid=True), nullable=False),
            sa.Column('generation_type', sa.String(length=50), nullable=True),
            sa.Column('theme_config_id', postgresql.UUID(as_uuid=True), nullable=True),
            sa.Column('selected_theme_name', sa.String(length=200), nullable=True),
            sa.Column('child_id', postgresql.UUID(as_uuid=True), nullable=True),
            sa.Column('child_name', sa.String(length=100), nullable=False),
            sa.Column('child_age', sa.Integer(), nullable=False),
            sa.Column('child_gender', sa.String(length=20), nullable=False),
            sa.Column('status', sa.String(length=20), nullable=False, server_default='queued'),
            sa.Column('progress', sa.Integer(), nullable=False, server_default='0'),
            sa.Column('queue_position', sa.Integer(), nullable=True),
            sa.Column('estimated_completion_time', sa.Integer(), nullable=True),
            sa.Column('started_at', sa.DateTime(timezone=True), nullable=True),
            sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True),
            sa.Column('total_pages', sa.Integer(), nullable=True),
            sa.Column('generated_title', sa.String(length=255), nullable=True),
            sa.Column('generated_content', sa.Text(), nullable=True),
            sa.Column('photos', postgresql.ARRAY(sa.String()), nullable=True),
            sa.Column('generated_images', postgresql.ARRAY(sa.String()), nullable=True),
            sa.Column('pdf_url', sa.String(length=500), nullable=True),
            sa.Column('preview_url', sa.String(length=500), nullable=True),
            sa.Column('parent_email', sa.String(length=255), nullable=True),
            sa.Column('error_message', sa.Text(), nullable=True),
            sa.Column('generation_steps', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
            sa.Column('metadata', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
            sa.Column('is_viewed', sa.Boolean(), nullable=False, server_default='false'),
            sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
            sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
            
            # Foreign keys
            sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
            sa.ForeignKeyConstraint(['child_id'], ['child_profiles.id'], ondelete='SET NULL'),
            sa.ForeignKeyConstraint(['theme_config_id'], ['generation_configs.id'], ondelete='SET NULL'),
            
            # Constraints
            sa.CheckConstraint(
                "template_type IN ('story_book', 'coloring_book')",
                name='check_generated_book_template_type'
            ),
            sa.CheckConstraint(
                "generation_type IN ('standard', 'photo_to_coloring', 'theme_based')",
                name='check_generated_book_generation_type'
            ),
            sa.CheckConstraint(
                "status IN ('queued', 'processing', 'completed', 'failed', 'cancelled')",
                name='check_generated_book_status'
            ),
            sa.CheckConstraint(
                "child_gender IN ('male', 'female', 'other')",
                name='check_generated_book_child_gender'
            ),
            sa.CheckConstraint(
                'progress >= 0 AND progress <= 100',
                name='check_generated_book_progress_range'
            ),
            sa.CheckConstraint(
                'child_age >= 0 AND child_age <= 18',
                name='check_generated_book_child_age'
            ),
        )
        
        # Create indexes
        op.create_index('idx_generated_books_user_id', 'generated_books', ['user_id'])
        op.create_index('idx_generated_books_child_id', 'generated_books', ['child_id'])
        op.create_index('idx_generated_books_theme_config_id', 'generated_books', ['theme_config_id'])
        op.create_index('idx_generated_books_template_type', 'generated_books', ['template_type'])
        op.create_index('idx_generated_books_generation_type', 'generated_books', ['generation_type'])
        op.create_index('idx_generated_books_status', 'generated_books', ['status'])
        op.create_index('idx_generated_books_created_at', 'generated_books', ['created_at'])
        op.create_index('idx_generated_books_queue_position', 'generated_books', ['queue_position'])
        
    else:
        # If table exists, add the new columns
        # Check if columns already exist before adding
        existing_columns = [col['name'] for col in inspector.get_columns('generated_books')]
        
        if 'generation_type' not in existing_columns:
            op.add_column('generated_books',
                sa.Column('generation_type', sa.String(length=50), nullable=True)
            )
            # Update existing records to have 'standard' generation_type
            op.execute(
                "UPDATE generated_books SET generation_type = 'standard' WHERE generation_type IS NULL"
            )
        
        if 'theme_config_id' not in existing_columns:
            op.add_column('generated_books',
                sa.Column('theme_config_id', postgresql.UUID(as_uuid=True), nullable=True)
            )
            try:
                op.create_foreign_key(
                    'fk_generated_books_theme_config_id',
                    'generated_books',
                    'generation_configs',
                    ['theme_config_id'],
                    ['id'],
                    ondelete='SET NULL'
                )
            except Exception:
                pass  # Foreign key might already exist
        
        if 'selected_theme_name' not in existing_columns:
            op.add_column('generated_books',
                sa.Column('selected_theme_name', sa.String(length=200), nullable=True)
            )
        
        # Add constraints if they don't exist
        try:
            op.create_check_constraint(
                'check_generated_book_generation_type',
                'generated_books',
                "generation_type IN ('standard', 'photo_to_coloring', 'theme_based')"
            )
        except Exception:
            pass  # Constraint might already exist
        
        # Add indexes if they don't exist
        try:
            op.create_index('idx_generated_books_theme_config_id', 'generated_books', ['theme_config_id'])
        except Exception:
            pass  # Index might already exist
        
        try:
            op.create_index('idx_generated_books_generation_type', 'generated_books', ['generation_type'])
        except Exception:
            pass  # Index might already exist


def downgrade() -> None:
    """Remove coloring book generation type fields from generated_books"""
    
    # Drop indexes
    try:
        op.drop_index('idx_generated_books_generation_type', table_name='generated_books')
    except Exception:
        pass
    
    try:
        op.drop_index('idx_generated_books_theme_config_id', table_name='generated_books')
    except Exception:
        pass
    
    # Drop foreign key and columns
    with op.batch_alter_table('generated_books', schema=None) as batch_op:
        try:
            batch_op.drop_constraint('fk_generated_books_theme_config_id', type_='foreignkey')
        except Exception:
            pass
        
        try:
            batch_op.drop_column('selected_theme_name')
        except Exception:
            pass
        
        try:
            batch_op.drop_column('theme_config_id')
        except Exception:
            pass
        
        try:
            batch_op.drop_column('generation_type')
        except Exception:
            pass
