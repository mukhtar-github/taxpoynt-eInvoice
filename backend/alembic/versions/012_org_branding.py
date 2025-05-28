"""Add logo_url and branding_settings to Organization

Revision ID: 012_org_branding
Revises: 999_dev_sqlite_schema
Create Date: 2025-05-28 14:07:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '012_org_branding'
down_revision = '999_dev_sqlite_schema'
branch_labels = None
depends_on = None


def upgrade():
    # First, check if the organization table exists
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    tables = inspector.get_table_names()
    
    if 'organization' in tables:
        # Get the dialect
        dialect = inspector.dialect.name
        
        if dialect == 'sqlite':
            # SQLite doesn't support JSON natively, use TEXT
            with op.batch_alter_table('organization') as batch_op:
                batch_op.add_column(sa.Column('logo_url', sa.String(255), nullable=True))
                batch_op.add_column(sa.Column('branding_settings', sa.Text(), nullable=True))
        else:
            # PostgreSQL supports JSON natively
            op.add_column('organization', sa.Column('logo_url', sa.String(255), nullable=True))
            op.add_column('organization', sa.Column('branding_settings', postgresql.JSONB(astext_type=sa.Text()), nullable=True))


def downgrade():
    # First, check if the organization table exists
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    tables = inspector.get_table_names()
    
    if 'organization' in tables:
        op.drop_column('organization', 'branding_settings')
        op.drop_column('organization', 'logo_url')
