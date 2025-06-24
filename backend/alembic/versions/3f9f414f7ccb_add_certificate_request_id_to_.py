"""Add certificate_request_id to certificates table

Revision ID: 3f9f414f7ccb
Revises: 8116b3d91f26
Create Date: 2025-06-24 17:12:24.813324

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision = '3f9f414f7ccb'
down_revision = '8116b3d91f26'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add certificate_request_id column to certificates table
    op.add_column('certificates', 
        sa.Column('certificate_request_id', postgresql.UUID(as_uuid=True), nullable=True)
    )
    
    # Add foreign key constraint
    op.create_foreign_key(
        'fk_certificates_certificate_request_id',
        'certificates', 'certificate_requests',
        ['certificate_request_id'], ['id'],
        ondelete='SET NULL'
    )
    
    # Create index for better query performance
    op.create_index('idx_certificates_certificate_request_id', 'certificates', ['certificate_request_id'])


def downgrade() -> None:
    # Remove index
    op.drop_index('idx_certificates_certificate_request_id', 'certificates')
    
    # Remove foreign key constraint
    op.drop_constraint('fk_certificates_certificate_request_id', 'certificates', type_='foreignkey')
    
    # Remove column
    op.drop_column('certificates', 'certificate_request_id')
