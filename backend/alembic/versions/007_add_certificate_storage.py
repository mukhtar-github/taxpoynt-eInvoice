"""Add certificate storage models

Revision ID: 007_add_certificate_storage
Revises: 006_add_api_credentials_sqlite
Create Date: 2025-05-08 02:55:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '007_add_certificate_storage'
down_revision = '006_add_api_credentials_sqlite'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create certificates table
    op.create_table(
        'certificates',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('organization_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('description', sa.String(500)),
        sa.Column('certificate_type', sa.String(20), nullable=False),
        
        # Metadata fields
        sa.Column('issuer', sa.String(255)),
        sa.Column('subject', sa.String(255)),
        sa.Column('serial_number', sa.String(100)),
        sa.Column('fingerprint', sa.String(100)),
        sa.Column('valid_from', sa.DateTime),
        sa.Column('valid_to', sa.DateTime),
        sa.Column('status', sa.String(20)),
        
        # Certificate content - stored encrypted
        sa.Column('certificate_data', sa.Text),
        sa.Column('is_encrypted', sa.Boolean, default=True, nullable=False),
        sa.Column('encryption_key_id', sa.String(100)),
        
        # Private key - stored encrypted separately for additional security
        sa.Column('private_key_data', sa.Text),
        sa.Column('has_private_key', sa.Boolean, default=False),
        
        # Additional metadata
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), onupdate=sa.func.now()),
        sa.Column('created_by', postgresql.UUID(as_uuid=True)),
        sa.Column('last_used_at', sa.DateTime),
        sa.Column('tags', postgresql.JSONB),
        
        # Constraints
        sa.ForeignKeyConstraint(['organization_id'], ['organizations.id']),
        sa.ForeignKeyConstraint(['encryption_key_id'], ['encryption_keys.id']),
        sa.ForeignKeyConstraint(['created_by'], ['users.id'])
    )
    
    # Create certificate revocations table
    op.create_table(
        'certificate_revocations',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('certificate_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('revoked_at', sa.DateTime, server_default=sa.func.now(), nullable=False),
        sa.Column('revoked_by', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('reason', sa.String(255)),
        
        # Constraints
        sa.ForeignKeyConstraint(['certificate_id'], ['certificates.id']),
        sa.ForeignKeyConstraint(['revoked_by'], ['users.id'])
    )
    
    # Create indexes
    op.create_index('ix_certificates_id', 'certificates', ['id'])
    op.create_index('ix_certificates_organization_id', 'certificates', ['organization_id'])
    op.create_index('ix_certificate_revocations_certificate_id', 'certificate_revocations', ['certificate_id'])


def downgrade() -> None:
    # Drop tables and indexes
    op.drop_index('ix_certificate_revocations_certificate_id', table_name='certificate_revocations')
    op.drop_index('ix_certificates_organization_id', table_name='certificates')
    op.drop_index('ix_certificates_id', table_name='certificates')
    
    op.drop_table('certificate_revocations')
    op.drop_table('certificates')
