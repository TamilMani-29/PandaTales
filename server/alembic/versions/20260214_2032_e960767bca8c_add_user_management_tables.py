# Alembic Migration Script Template
# This is the default template for new migrations

"""add_user_management_tables

Revision ID: e960767bca8c
Revises: a727bdd5f897
Create Date: 2026-02-14 20:32:27.496655

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = 'e960767bca8c'
down_revision: Union[str, None] = 'a727bdd5f897'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Check if users table already exists
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    existing_tables = inspector.get_table_names()
    
    # Create users table only if it doesn't exist
    if 'users' not in existing_tables:
        op.create_table(
            'users',
            sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
            sa.Column('email', sa.String(length=255), nullable=False),
            sa.Column('password_hash', sa.String(length=255), nullable=True),
            sa.Column('first_name', sa.String(length=100), nullable=False),
            sa.Column('last_name', sa.String(length=100), nullable=False),
            sa.Column('phone', sa.String(length=20), nullable=True),
            sa.Column('avatar_url', sa.String(length=500), nullable=True),
            sa.Column('email_verified', sa.Boolean(), nullable=False, server_default='false'),
            sa.Column('phone_verified', sa.Boolean(), nullable=False, server_default='false'),
            sa.Column('oauth_provider', sa.String(length=50), nullable=True),
            sa.Column('oauth_provider_id', sa.String(length=255), nullable=True),
            sa.Column('role', sa.String(length=20), nullable=False, server_default='user'),
            sa.Column('last_login_at', sa.DateTime(timezone=True), nullable=True),
            sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
            sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
            sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
            sa.CheckConstraint("role IN ('user', 'admin')", name='check_user_role'),
            sa.CheckConstraint("oauth_provider IN ('google', 'facebook', 'apple')", name='check_oauth_provider'),
            sa.UniqueConstraint('email', name='uq_users_email'),
        )
        
        # Create indexes for users
        op.create_index('idx_users_email', 'users', ['email'])
        op.create_index('idx_users_oauth', 'users', ['oauth_provider', 'oauth_provider_id'])
        op.create_index('idx_users_created_at', 'users', ['created_at'])
        op.create_index('idx_users_is_active', 'users', ['is_active'])
    
    # Create child_profiles table only if it doesn't exist
    if 'child_profiles' not in existing_tables:
        op.create_table(
            'child_profiles',
            sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
            sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
            sa.Column('name', sa.String(length=100), nullable=False),
            sa.Column('age', sa.Integer(), nullable=False),
            sa.Column('gender', sa.String(length=20), nullable=False),
            sa.Column('birth_date', sa.Date(), nullable=True),
            sa.Column('photo_url', sa.String(length=500), nullable=True),
            sa.Column('books_created_count', sa.Integer(), nullable=False, server_default='0'),
            sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
            sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
            sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
            sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
            sa.CheckConstraint('age >= 0 AND age <= 18', name='check_child_age_range'),
            sa.CheckConstraint("gender IN ('male', 'female', 'other')", name='check_child_gender'),
        )
        
        # Create indexes for child_profiles
        op.create_index('idx_child_profiles_user_id', 'child_profiles', ['user_id'])
        op.create_index('idx_child_profiles_user_active', 'child_profiles', ['user_id', 'is_active'])
    
    # Create addresses table only if it doesn't exist
    if 'addresses' not in existing_tables:
        op.create_table(
            'addresses',
            sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
            sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
            sa.Column('first_name', sa.String(length=100), nullable=False),
            sa.Column('last_name', sa.String(length=100), nullable=False),
            sa.Column('address_line1', sa.String(length=255), nullable=False),
            sa.Column('address_line2', sa.String(length=255), nullable=True),
            sa.Column('city', sa.String(length=100), nullable=False),
            sa.Column('state', sa.String(length=100), nullable=False),
            sa.Column('postal_code', sa.String(length=20), nullable=False),
            sa.Column('country', sa.String(length=2), nullable=False),
            sa.Column('phone', sa.String(length=20), nullable=False),
            sa.Column('is_default', sa.Boolean(), nullable=False, server_default='false'),
            sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
            sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
            sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
            sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
            sa.CheckConstraint('length(country) = 2', name='check_country_code_length'),
        )
        
        # Create indexes for addresses
        op.create_index('idx_addresses_user_id', 'addresses', ['user_id'])
        op.create_index('idx_addresses_user_default', 'addresses', ['user_id', 'is_default'])
        op.create_index(
            'idx_addresses_user_default_unique',
            'addresses',
            ['user_id'],
            unique=True,
            postgresql_where=sa.text('is_default = TRUE AND is_active = TRUE')
        )


def downgrade() -> None:
    # Drop tables in reverse order (children first due to foreign keys)
    op.drop_table('addresses')
    op.drop_table('child_profiles')
    op.drop_table('users')
