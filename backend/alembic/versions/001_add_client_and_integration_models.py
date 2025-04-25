"""Add client and integration models

Revision ID: 001_add_client_int
Revises: 
Create Date: 2023-07-01T12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '001_add_client_int'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # Create clients table
    op.create_table(
        'clients',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('organization_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('name', sa.String(100), nullable=False),
        sa.Column('tax_id', sa.String(50), nullable=False),
        sa.Column('email', sa.String(100)),
        sa.Column('phone', sa.String(20)),
        sa.Column('address', sa.String(255)),
        sa.Column('industry', sa.String(50)),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.Column('status', sa.String(20), nullable=False, server_default=sa.text("'active'")),
        sa.ForeignKeyConstraint(['organization_id'], ['organizations.id'], ),
    )
    
    # Create integrations table
    op.create_table(
        'integrations',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('client_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('name', sa.String(100), nullable=False),
        sa.Column('description', sa.Text()),
        sa.Column('config', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.Column('created_by', postgresql.UUID(as_uuid=True)),
        sa.Column('last_tested', sa.DateTime()),
        sa.Column('status', sa.String(20), nullable=False, server_default=sa.text("'configured'")),
        sa.ForeignKeyConstraint(['client_id'], ['clients.id'], ),
        sa.ForeignKeyConstraint(['created_by'], ['users.id'], ),
    )
    
    # Create integration_history table
    op.create_table(
        'integration_history',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('integration_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('changed_by', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('previous_config', postgresql.JSONB(astext_type=sa.Text())),
        sa.Column('new_config', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column('changed_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.Column('change_reason', sa.String(255)),
        sa.ForeignKeyConstraint(['integration_id'], ['integrations.id'], ),
        sa.ForeignKeyConstraint(['changed_by'], ['users.id'], ),
    )
    
    # Create indexes
    op.create_index('ix_clients_id', 'clients', ['id'])
    op.create_index('ix_clients_organization_id', 'clients', ['organization_id'])
    op.create_index('ix_integrations_id', 'integrations', ['id'])
    op.create_index('ix_integrations_client_id', 'integrations', ['client_id'])
    op.create_index('ix_integration_history_id', 'integration_history', ['id'])
    op.create_index('ix_integration_history_integration_id', 'integration_history', ['integration_id'])


def downgrade():
    op.drop_table('integration_history')
    op.drop_table('integrations')
    op.drop_table('clients') 