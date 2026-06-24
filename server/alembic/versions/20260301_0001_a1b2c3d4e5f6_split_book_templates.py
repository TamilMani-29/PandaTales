"""Split book_templates into story_book_templates and coloring_book_templates

Revision ID: 20260301_0001
Revises: e960767bca8c
Create Date: 2026-03-01 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '20260301_0001'
down_revision: Union[str, None] = 'e960767bca8c'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Check if tables already exist
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    existing_tables = inspector.get_table_names()
    
    # Create story_book_templates table only if it doesn't exist
    if 'story_book_templates' not in existing_tables:
        op.create_table(
        'story_book_templates',
        sa.Column('title', sa.String(length=255), nullable=False),
        sa.Column('description', sa.Text(), nullable=False),
        sa.Column('long_description', sa.Text(), nullable=True),
        sa.Column('book_type', sa.String(length=20), nullable=True),
        sa.Column('series_id', sa.UUID(), nullable=True),
        sa.Column('book_number', sa.Integer(), nullable=True),
        sa.Column('genre', sa.String(length=50), nullable=False),
        sa.Column('age_group', sa.String(length=20), nullable=False),
        sa.Column('story_theme', sa.String(length=100), nullable=True),
        sa.Column('moral_lesson', sa.Text(), nullable=True),
        sa.Column('reading_level', sa.String(length=20), nullable=True),
        sa.Column('price', sa.Numeric(precision=10, scale=2), nullable=False),
        sa.Column('cover_image_url', sa.String(length=500), nullable=False),
        sa.Column('preview_images', postgresql.JSONB(astext_type=sa.Text()), server_default=sa.text("'[]'::jsonb"), nullable=False),
        sa.Column('total_pages', sa.Integer(), nullable=False),
        sa.Column('features', postgresql.JSONB(astext_type=sa.Text()), server_default=sa.text("'[]'::jsonb"), nullable=False),
        sa.Column('learning_outcomes', postgresql.JSONB(astext_type=sa.Text()), server_default=sa.text("'[]'::jsonb"), nullable=False),
        sa.Column('chapters', postgresql.JSONB(astext_type=sa.Text()), server_default=sa.text("'[]'::jsonb"), nullable=False),
        sa.Column('customization_options', postgresql.JSONB(astext_type=sa.Text()), server_default=sa.text("'{}'::jsonb"), nullable=False),
        sa.Column('tags', postgresql.JSONB(astext_type=sa.Text()), server_default=sa.text("'[]'::jsonb"), nullable=False),
        sa.Column('is_published', sa.Boolean(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=False),
        sa.CheckConstraint("book_type IN ('single', 'series') OR book_type IS NULL", name='check_story_book_type'),
        sa.CheckConstraint("age_group IN ('0-2', '3-5', '6-8', '9-12')", name='check_story_age_group'),
        sa.CheckConstraint("reading_level IN ('beginner', 'intermediate', 'advanced') OR reading_level IS NULL", name='check_reading_level'),
        sa.CheckConstraint('price >= 0', name='check_story_price_positive'),
        sa.CheckConstraint('total_pages > 0', name='check_story_total_pages_positive'),
        sa.PrimaryKeyConstraint('id')
    )
    
        # Create indexes for story_book_templates
        op.create_index('idx_story_templates_active_published', 'story_book_templates', ['is_active', 'is_published'], unique=False)
        op.create_index('idx_story_templates_genre', 'story_book_templates', ['genre'], unique=False)
        op.create_index('idx_story_templates_series', 'story_book_templates', ['series_id', 'book_number'], unique=False)
        op.create_index('idx_story_templates_search', 'story_book_templates', [sa.literal_column("to_tsvector('english', title || ' ' || description)")], unique=False, postgresql_using='gin')
        op.create_index('idx_story_templates_tags', 'story_book_templates', ['tags'], unique=False, postgresql_using='gin')
        op.create_index(op.f('ix_story_book_templates_age_group'), 'story_book_templates', ['age_group'], unique=False)
        op.create_index(op.f('ix_story_book_templates_genre'), 'story_book_templates', ['genre'], unique=False)
        op.create_index(op.f('ix_story_book_templates_is_active'), 'story_book_templates', ['is_active'], unique=False)
        op.create_index(op.f('ix_story_book_templates_is_published'), 'story_book_templates', ['is_published'], unique=False)
        op.create_index(op.f('ix_story_book_templates_price'), 'story_book_templates', ['price'], unique=False)
        op.create_index(op.f('ix_story_book_templates_series_id'), 'story_book_templates', ['series_id'], unique=False)
        op.create_index(op.f('ix_story_book_templates_title'), 'story_book_templates', ['title'], unique=False)

    # Create coloring_book_templates table only if it doesn't exist
    if 'coloring_book_templates' not in existing_tables:
        op.create_table(
        'coloring_book_templates',
        sa.Column('title', sa.String(length=255), nullable=False),
        sa.Column('description', sa.Text(), nullable=False),
        sa.Column('long_description', sa.Text(), nullable=True),
        sa.Column('theme', sa.String(length=50), nullable=False),
        sa.Column('age_group', sa.String(length=20), nullable=False),
        sa.Column('difficulty', sa.String(length=20), nullable=False),
        sa.Column('art_style', sa.String(length=50), nullable=True),
        sa.Column('complexity_level', sa.String(length=20), nullable=True),
        sa.Column('includes_activities', sa.Boolean(), nullable=False),
        sa.Column('price', sa.Numeric(precision=10, scale=2), nullable=False),
        sa.Column('cover_image_url', sa.String(length=500), nullable=False),
        sa.Column('preview_images', postgresql.JSONB(astext_type=sa.Text()), server_default=sa.text("'[]'::jsonb"), nullable=False),
        sa.Column('sample_pages', postgresql.JSONB(astext_type=sa.Text()), server_default=sa.text("'[]'::jsonb"), nullable=False),
        sa.Column('total_pages', sa.Integer(), nullable=False),
        sa.Column('features', postgresql.JSONB(astext_type=sa.Text()), server_default=sa.text("'[]'::jsonb"), nullable=False),
        sa.Column('learning_outcomes', postgresql.JSONB(astext_type=sa.Text()), server_default=sa.text("'[]'::jsonb"), nullable=False),
        sa.Column('page_types', postgresql.JSONB(astext_type=sa.Text()), server_default=sa.text("'[]'::jsonb"), nullable=False),
        sa.Column('customization_options', postgresql.JSONB(astext_type=sa.Text()), server_default=sa.text("'{}'::jsonb"), nullable=False),
        sa.Column('tags', postgresql.JSONB(astext_type=sa.Text()), server_default=sa.text("'[]'::jsonb"), nullable=False),
        sa.Column('is_published', sa.Boolean(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=False),
        sa.CheckConstraint("age_group IN ('0-2', '3-5', '6-8', '9-12')", name='check_coloring_age_group'),
        sa.CheckConstraint("difficulty IN ('easy', 'medium', 'hard')", name='check_coloring_difficulty'),
        sa.CheckConstraint("art_style IN ('cartoon', 'realistic', 'abstract', 'simple', 'detailed') OR art_style IS NULL", name='check_art_style'),
        sa.CheckConstraint("complexity_level IN ('simple', 'moderate', 'complex') OR complexity_level IS NULL", name='check_complexity_level'),
        sa.CheckConstraint('price >= 0', name='check_coloring_price_positive'),
        sa.CheckConstraint('total_pages > 0', name='check_coloring_total_pages_positive'),
        sa.PrimaryKeyConstraint('id')
    )
    
        # Create indexes for coloring_book_templates
        op.create_index('idx_coloring_templates_active_published', 'coloring_book_templates', ['is_active', 'is_published'], unique=False)
        op.create_index('idx_coloring_templates_theme', 'coloring_book_templates', ['theme'], unique=False)
        op.create_index('idx_coloring_templates_difficulty', 'coloring_book_templates', ['difficulty'], unique=False)
        op.create_index('idx_coloring_templates_search', 'coloring_book_templates', [sa.literal_column("to_tsvector('english', title || ' ' || description)")], unique=False, postgresql_using='gin')
        op.create_index('idx_coloring_templates_tags', 'coloring_book_templates', ['tags'], unique=False, postgresql_using='gin')
        op.create_index(op.f('ix_coloring_book_templates_age_group'), 'coloring_book_templates', ['age_group'], unique=False)
        op.create_index(op.f('ix_coloring_book_templates_difficulty'), 'coloring_book_templates', ['difficulty'], unique=False)
        op.create_index(op.f('ix_coloring_book_templates_is_active'), 'coloring_book_templates', ['is_active'], unique=False)
        op.create_index(op.f('ix_coloring_book_templates_is_published'), 'coloring_book_templates', ['is_published'], unique=False)
        op.create_index(op.f('ix_coloring_book_templates_price'), 'coloring_book_templates', ['price'], unique=False)
        op.create_index(op.f('ix_coloring_book_templates_theme'), 'coloring_book_templates', ['theme'], unique=False)
        op.create_index(op.f('ix_coloring_book_templates_title'), 'coloring_book_templates', ['title'], unique=False)

    # Migrate data from book_templates if it exists
    if 'book_templates' in existing_tables:
        # Migrate data from book_templates to story_book_templates
        op.execute("""
            INSERT INTO story_book_templates (
                id, title, description, long_description, book_type, series_id, book_number,
                genre, age_group, price, cover_image_url, preview_images, total_pages,
                features, learning_outcomes, customization_options, tags, is_published,
                is_active, created_at, updated_at
            )
            SELECT 
                id, title, description, long_description, book_type, series_id, book_number,
                genre, age_group, price, cover_image_url, preview_images, total_pages,
                features, learning_outcomes, customization_options, tags, is_published,
                is_active, created_at, updated_at
            FROM book_templates
            WHERE template_type = 'story_book'
        """)

        # Migrate data from book_templates to coloring_book_templates
        op.execute("""
            INSERT INTO coloring_book_templates (
                id, title, description, long_description, theme, age_group, difficulty,
                price, cover_image_url, preview_images, total_pages, features,
                learning_outcomes, customization_options, tags, is_published, is_active,
                created_at, updated_at, includes_activities
            )
            SELECT 
                id, title, description, long_description, 
                COALESCE(genre, 'general') as theme,
                age_group, 
                COALESCE(difficulty, 'medium') as difficulty,
                price, cover_image_url, preview_images, total_pages, features,
                learning_outcomes, customization_options, tags, is_published, is_active,
                created_at, updated_at, FALSE as includes_activities
            FROM book_templates
            WHERE template_type = 'coloring_book'
        """)

        # Drop the old generated_books table if it exists (will be recreated with new schema)
        op.execute("DROP TABLE IF EXISTS generated_books CASCADE")
        
        # Drop the old book_templates table
        op.execute("DROP TABLE IF EXISTS book_templates CASCADE")
    
    # Create new generated_books table only if it doesn't exist
    if 'generated_books' not in existing_tables:
        op.create_table(
        'generated_books',
        sa.Column('template_type', sa.String(length=20), nullable=False),
        sa.Column('template_id', sa.UUID(), nullable=False),
        sa.Column('child_name', sa.String(length=100), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('id', sa.UUID(), nullable=False),
        sa.CheckConstraint("template_type IN ('story_book', 'coloring_book')", name='check_template_type'),
        sa.PrimaryKeyConstraint('id')
    )
        op.create_index(op.f('ix_generated_books_template_id'), 'generated_books', ['template_id'], unique=False)
        op.create_index(op.f('ix_generated_books_template_type'), 'generated_books', ['template_type'], unique=False)
    op.drop_index(op.f('ix_coloring_book_templates_is_active'), table_name='coloring_book_templates')
    op.drop_index(op.f('ix_coloring_book_templates_difficulty'), table_name='coloring_book_templates')
    op.drop_index(op.f('ix_coloring_book_templates_age_group'), table_name='coloring_book_templates')
    op.drop_index('idx_coloring_templates_tags', table_name='coloring_book_templates', postgresql_using='gin')
    op.drop_index('idx_coloring_templates_search', table_name='coloring_book_templates', postgresql_using='gin')
    op.drop_index('idx_coloring_templates_difficulty', table_name='coloring_book_templates')
    op.drop_index('idx_coloring_templates_theme', table_name='coloring_book_templates')
    op.drop_index('idx_coloring_templates_active_published', table_name='coloring_book_templates')
    op.drop_table('coloring_book_templates')
    
    op.drop_index(op.f('ix_story_book_templates_title'), table_name='story_book_templates')
    op.drop_index(op.f('ix_story_book_templates_series_id'), table_name='story_book_templates')
    op.drop_index(op.f('ix_story_book_templates_price'), table_name='story_book_templates')
    op.drop_index(op.f('ix_story_book_templates_is_published'), table_name='story_book_templates')
    op.drop_index(op.f('ix_story_book_templates_is_active'), table_name='story_book_templates')
    op.drop_index(op.f('ix_story_book_templates_genre'), table_name='story_book_templates')
    op.drop_index(op.f('ix_story_book_templates_age_group'), table_name='story_book_templates')
    op.drop_index('idx_story_templates_tags', table_name='story_book_templates', postgresql_using='gin')
    op.drop_index('idx_story_templates_search', table_name='story_book_templates', postgresql_using='gin')
    op.drop_index('idx_story_templates_series', table_name='story_book_templates')
    op.drop_index('idx_story_templates_genre', table_name='story_book_templates')
    op.drop_index('idx_story_templates_active_published', table_name='story_book_templates')
    op.drop_table('story_book_templates')
