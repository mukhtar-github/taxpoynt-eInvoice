"""Add IRN tables

Revision ID: 002_add_irn_tables
Revises: 001_add_client_int
Create Date: 2024-05-11 14:30:00.000000

"""
from alembic import op # type: ignore
import sqlalchemy as sa # type: ignore
from sqlalchemy.dialects import postgresql # type: ignore

# revision identifiers, used by Alembic.
revision = '002_add_irn_tables'
down_revision = '001_add_client_int'
branch_labels = None
depends_on = None


def upgrade():
    # Make SQLite compatible by replacing JSONB with JSON when using SQLite
    import re
    from sqlalchemy import text
    from sqlalchemy.engine import reflection
    
    conn = op.get_bind()
    inspector = reflection.Inspector.from_engine(conn)
    dialect_name = conn.dialect.name
    
    # For SQLite, we'll use the JSON type instead of JSONB
    json_type = "JSON" if dialect_name == "sqlite" else "JSONB"

    # Create irn_records table
    op.create_table(
        'irn_records',
        sa.Column('irn', sa.String(50), primary_key=True, index=True),
        sa.Column('integration_id', sa.String(36), sa.ForeignKey('integrations.id'), nullable=False),
        sa.Column('invoice_number', sa.String(50), nullable=False, index=True),
        sa.Column('service_id', sa.String(8), nullable=False),
        sa.Column('timestamp', sa.String(8), nullable=False),
        sa.Column('generated_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column('valid_until', sa.DateTime(), nullable=False),
        sa.Column('metadata', getattr(postgresql, json_type)(astext_type=sa.Text()), nullable=True),
        sa.Column('status', sa.String(20), nullable=False, server_default='unused'),
        sa.Column('used_at', sa.DateTime(), nullable=True),
        sa.Column('invoice_id', sa.String(50), nullable=True),
    )
    
    # Add indexes for better performance
    op.create_index('idx_irn_integration_id', 'irn_records', ['integration_id'])
    op.create_index('idx_irn_status', 'irn_records', ['status'])
    op.create_index('idx_irn_timestamp', 'irn_records', ['timestamp'])


def downgrade():
    # Drop indexes first
    op.drop_index('idx_irn_timestamp', table_name='irn_records')
    op.drop_index('idx_irn_status', table_name='irn_records')
    op.drop_index('idx_irn_integration_id', table_name='irn_records')
    
    # Drop tables
    op.drop_table('irn_records') 