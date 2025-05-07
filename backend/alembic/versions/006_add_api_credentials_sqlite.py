"""Add API credentials table for SQLite

Revision ID: 006_add_api_credentials_sqlite
Revises: 999_dev_sqlite_schema
Create Date: 2025-05-07 11:30:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '006_add_api_credentials_sqlite'
down_revision = '999_dev_sqlite_schema'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create credential_type enum type equivalent in SQLite (using string)
    
    # Create api_credentials table
    op.create_table(
        'api_credentials',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('organization_id', sa.String(36), nullable=False),
        sa.Column('name', sa.String(100), nullable=False),
        sa.Column('description', sa.String(255), nullable=True),
        sa.Column('credential_type', sa.String(50), nullable=False),  # Using string for enum in SQLite
        sa.Column('client_id', sa.String(), nullable=True),
        sa.Column('client_secret', sa.String(), nullable=True),
        sa.Column('api_key', sa.String(), nullable=True),
        sa.Column('api_secret', sa.String(), nullable=True),
        sa.Column('additional_config', sa.String(), nullable=True),
        sa.Column('is_encrypted', sa.Boolean(), nullable=False, default=True),
        sa.Column('encryption_key_id', sa.String(100), nullable=True),
        sa.Column('created_by', sa.String(36), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), onupdate=sa.func.now()),
        sa.Column('last_used_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('expires_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False, default=True),
        sa.ForeignKeyConstraint(['organization_id'], ['organizations.id']),
        sa.ForeignKeyConstraint(['created_by'], ['users.id']),
        # SQLite doesn't enforce foreign keys by default, so we'll skip the encryption_key foreign key
        # since it might not exist in the simplified schema
    )
    
    # Create indexes - SQLite supports these
    op.create_index('ix_api_credentials_id', 'api_credentials', ['id'])
    op.create_index('ix_api_credentials_organization_id', 'api_credentials', ['organization_id'])


def downgrade() -> None:
    # Drop the api_credentials table
    op.drop_index('ix_api_credentials_organization_id', table_name='api_credentials')
    op.drop_index('ix_api_credentials_id', table_name='api_credentials')
    op.drop_table('api_credentials')
