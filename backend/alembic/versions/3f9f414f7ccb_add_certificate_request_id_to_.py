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
    # Check if certificates table exists before modifying it
    from sqlalchemy import inspect
    
    bind = op.get_bind()
    inspector = inspect(bind)
    tables = inspector.get_table_names()
    
    if 'certificates' not in tables:
        print("Warning: certificates table does not exist. Skipping certificate_request_id column addition.")
        print("This migration will be automatically applied when the certificates table is created.")
        return
    
    # Check if column already exists
    columns = [col['name'] for col in inspector.get_columns('certificates')]
    if 'certificate_request_id' in columns:
        print("certificate_request_id column already exists in certificates table. Skipping.")
        return
        
    # Add certificate_request_id column to certificates table
    op.add_column('certificates', 
        sa.Column('certificate_request_id', postgresql.UUID(as_uuid=True), nullable=True)
    )
    
    # Check if certificate_requests table exists before creating foreign key
    if 'certificate_requests' in tables:
        # Add foreign key constraint
        op.create_foreign_key(
            'fk_certificates_certificate_request_id',
            'certificates', 'certificate_requests',
            ['certificate_request_id'], ['id'],
            ondelete='SET NULL'
        )
    else:
        print("Warning: certificate_requests table does not exist. Skipping foreign key constraint.")
    
    # Create index for better query performance
    op.create_index('idx_certificates_certificate_request_id', 'certificates', ['certificate_request_id'])


def downgrade() -> None:
    # Check if certificates table exists before modifying it
    from sqlalchemy import inspect
    
    bind = op.get_bind()
    inspector = inspect(bind)
    tables = inspector.get_table_names()
    
    if 'certificates' not in tables:
        print("Warning: certificates table does not exist. Nothing to downgrade.")
        return
    
    # Check if column exists before removing it
    columns = [col['name'] for col in inspector.get_columns('certificates')]
    if 'certificate_request_id' not in columns:
        print("certificate_request_id column does not exist in certificates table. Nothing to downgrade.")
        return
    
    # Remove index (if exists)
    indexes = inspector.get_indexes('certificates')
    index_names = [idx['name'] for idx in indexes]
    if 'idx_certificates_certificate_request_id' in index_names:
        op.drop_index('idx_certificates_certificate_request_id', 'certificates')
    
    # Remove foreign key constraint (if exists)
    foreign_keys = inspector.get_foreign_keys('certificates')
    fk_names = [fk['name'] for fk in foreign_keys]
    if 'fk_certificates_certificate_request_id' in fk_names:
        op.drop_constraint('fk_certificates_certificate_request_id', 'certificates', type_='foreignkey')
    
    # Remove column
    op.drop_column('certificates', 'certificate_request_id')
