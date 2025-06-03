"""Add signature settings table

Revision ID: add_signature_settings
Revises: 
Create Date: 2025-06-03

NOTE: This migration is part of the signature management feature branch.
It can be safely applied to both production and development environments.
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'add_signature_settings'
down_revision = None  # Will be applied independently
branch_labels = ('signature_features',)  # Separate branch for signature features
depends_on = None


def upgrade():
    # Safely check if the table already exists before creating
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    tables = inspector.get_table_names()
    
    if 'signature_settings' not in tables:
        # Create signature_settings table
        op.create_table('signature_settings',
            sa.Column('id', sa.Integer(), nullable=False),
            sa.Column('version', sa.Integer(), nullable=True, default=1),
            sa.Column('is_active', sa.Boolean(), nullable=True, default=True),
            sa.Column('created_at', sa.DateTime(), nullable=True, server_default=sa.func.now()),
            sa.Column('updated_at', sa.DateTime(), nullable=True, server_default=sa.func.now(), onupdate=sa.func.now()),
            sa.Column('user_id', sa.Integer(), nullable=True),
            sa.Column('algorithm', sa.String(), nullable=True, default='RSA-PSS-SHA256'),
            sa.Column('csid_version', sa.String(), nullable=True, default='2.0'),
            sa.Column('enable_caching', sa.Boolean(), nullable=True, default=True),
            sa.Column('cache_size', sa.Integer(), nullable=True, default=1000),
            sa.Column('cache_ttl', sa.Integer(), nullable=True, default=3600),
            sa.Column('parallel_processing', sa.Boolean(), nullable=True, default=True),
            sa.Column('max_workers', sa.Integer(), nullable=True, default=4),
            sa.Column('extra_settings', sa.JSON(), nullable=True, default={}),
            sa.ForeignKeyConstraint(['user_id'], ['user.id'], ondelete='CASCADE'),
            sa.PrimaryKeyConstraint('id')
        )
        op.create_index(op.f('ix_signature_settings_id'), 'signature_settings', ['id'], unique=False)


def downgrade():
    # Safely check if the table exists before dropping
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    tables = inspector.get_table_names()
    
    if 'signature_settings' in tables:
        # Drop signature_settings table
        op.drop_index(op.f('ix_signature_settings_id'), table_name='signature_settings')
        op.drop_table('signature_settings')
