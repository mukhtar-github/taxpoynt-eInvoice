"""Add logo_url and branding_settings to Organization

Revision ID: 012_add_organization_branding_fields
Revises: 999_dev_sqlite_schema
Create Date: 2025-05-26 17:22:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '012_add_organization_branding_fields'
down_revision = '999_dev_sqlite_schema'
branch_labels = None
depends_on = None


def upgrade():
    # First, check if the organization table exists
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    tables = inspector.get_table_names()
    
    if 'organization' not in tables:
        return
    
    # For PostgreSQL (Railway production)
    if conn.dialect.name == 'postgresql':
        # Add logo_url
        op.add_column('organization', sa.Column('logo_url', sa.String(), nullable=True))
        
        # Add branding_settings as JSONB
        op.add_column('organization', sa.Column('branding_settings', postgresql.JSONB(), nullable=True))
    
    # For SQLite (local development)
    elif conn.dialect.name == 'sqlite':
        # Add logo_url
        op.add_column('organization', sa.Column('logo_url', sa.String(), nullable=True))
        
        # Add branding_settings as JSON string for SQLite
        op.add_column('organization', sa.Column('branding_settings', sa.Text(), nullable=True))


def downgrade():
    # Check if the organization table exists
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    tables = inspector.get_table_names()
    
    if 'organization' not in tables:
        return
    
    # Remove the added columns
    op.drop_column('organization', 'branding_settings')
    op.drop_column('organization', 'logo_url')
