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
down_revision = '014_add_crm_pos_tables'  # Connect to main migration chain
branch_labels = ('signature_features',)  # Separate branch for signature features
depends_on = None


def upgrade():
    # Safely check if the table already exists before creating
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    tables = inspector.get_table_names()
    
    if 'signature_settings' not in tables:
        # Check if users table exists to determine if we can add foreign key
        has_users_table = 'users' in tables
        
        # Create signature_settings table
        table_args = [
            sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False, default=sa.text('gen_random_uuid()')),
            sa.Column('version', sa.Integer(), nullable=True, default=1),
            sa.Column('is_active', sa.Boolean(), nullable=True, default=True),
            sa.Column('created_at', sa.DateTime(), nullable=True, server_default=sa.func.now()),
            sa.Column('updated_at', sa.DateTime(), nullable=True, server_default=sa.func.now(), onupdate=sa.func.now()),
            sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=True),
            sa.Column('algorithm', sa.String(), nullable=True, default='RSA-PSS-SHA256'),
            sa.Column('csid_version', sa.String(), nullable=True, default='2.0'),
            sa.Column('enable_caching', sa.Boolean(), nullable=True, default=True),
            sa.Column('cache_size', sa.Integer(), nullable=True, default=1000),
            sa.Column('cache_ttl', sa.Integer(), nullable=True, default=3600),
            sa.Column('parallel_processing', sa.Boolean(), nullable=True, default=True),
            sa.Column('max_workers', sa.Integer(), nullable=True, default=4),
            sa.Column('extra_settings', sa.JSON(), nullable=True, default={}),
            sa.PrimaryKeyConstraint('id')
        ]
        
        # Only add foreign key if users table exists
        if has_users_table:
            table_args.append(sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'))
        else:
            print("Warning: users table not found, skipping foreign key constraint for signature_settings.user_id")
        
        op.create_table('signature_settings', *table_args)
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
