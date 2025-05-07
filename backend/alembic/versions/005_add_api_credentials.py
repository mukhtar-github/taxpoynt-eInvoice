"""Add API credentials table

Revision ID: 005_add_api_credentials
Revises: 004_enhance_irn_system
Create Date: 2025-05-07 10:43:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '005_add_api_credentials'
down_revision = '004_enhance_irn_system'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create credential_type enum type
    credential_type_enum = sa.Enum('firs', 'odoo', 'other', name='credentialtype')
    credential_type_enum.create(op.get_bind())
    
    # Create api_credentials table
    op.create_table(
        'api_credentials',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('organization_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('name', sa.String(100), nullable=False),
        sa.Column('description', sa.String(255), nullable=True),
        sa.Column('credential_type', credential_type_enum, nullable=False),
        sa.Column('client_id', sa.String(), nullable=True),
        sa.Column('client_secret', sa.String(), nullable=True),
        sa.Column('api_key', sa.String(), nullable=True),
        sa.Column('api_secret', sa.String(), nullable=True),
        sa.Column('additional_config', sa.String(), nullable=True),
        sa.Column('is_encrypted', sa.Boolean(), nullable=False, default=True),
        sa.Column('encryption_key_id', sa.String(100), nullable=True),
        sa.Column('created_by', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), onupdate=sa.func.now()),
        sa.Column('last_used_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('expires_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False, default=True),
        sa.ForeignKeyConstraint(['organization_id'], ['organizations.id']),
        sa.ForeignKeyConstraint(['created_by'], ['users.id']),
        sa.ForeignKeyConstraint(['encryption_key_id'], ['encryption_keys.id']),
    )
    
    # Create indexes
    op.create_index('ix_api_credentials_id', 'api_credentials', ['id'])
    op.create_index('ix_api_credentials_organization_id', 'api_credentials', ['organization_id'])


def downgrade() -> None:
    # Drop the api_credentials table
    op.drop_index('ix_api_credentials_organization_id', table_name='api_credentials')
    op.drop_index('ix_api_credentials_id', table_name='api_credentials')
    op.drop_table('api_credentials')
    
    # Drop the credential_type enum
    sa.Enum(name='credentialtype').drop(op.get_bind())
