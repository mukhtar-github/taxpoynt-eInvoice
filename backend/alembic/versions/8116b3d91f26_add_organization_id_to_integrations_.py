"""Add organization_id to integrations table

Revision ID: 8116b3d91f26
Revises: 435408565c9f
Create Date: 2025-06-24 16:04:07.619547

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision = '8116b3d91f26'
down_revision = '435408565c9f'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add organization_id column to integrations table
    op.add_column('integrations', 
        sa.Column('organization_id', postgresql.UUID(as_uuid=True), nullable=True)
    )
    
    # Add foreign key constraint
    op.create_foreign_key(
        'fk_integrations_organization_id',
        'integrations', 'organizations',
        ['organization_id'], ['id'],
        ondelete='CASCADE'
    )
    
    # Create index for better query performance
    op.create_index('idx_integrations_organization_id', 'integrations', ['organization_id'])


def downgrade() -> None:
    # Remove index
    op.drop_index('idx_integrations_organization_id', 'integrations')
    
    # Remove foreign key constraint
    op.drop_constraint('fk_integrations_organization_id', 'integrations', type_='foreignkey')
    
    # Remove column
    op.drop_column('integrations', 'organization_id')
