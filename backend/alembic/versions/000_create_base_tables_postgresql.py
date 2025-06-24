"""Create base tables for PostgreSQL production

Revision ID: 000_create_base_tables_postgresql
Revises: 
Create Date: 2025-06-24 06:30:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '000_create_base_tables_postgresql'
down_revision = '012_org_branding'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Create base tables that other migrations depend on."""
    
    connection = op.get_bind()
    inspector = sa.inspect(connection)
    
    # Only run for PostgreSQL, skip for SQLite development
    if inspector.dialect.name != 'postgresql':
        print("Skipping PostgreSQL base tables creation - not running on PostgreSQL")
        return
    
    # Enable uuid-ossp extension
    try:
        connection.execute(sa.text('CREATE EXTENSION IF NOT EXISTS "uuid-ossp"'))
    except Exception as e:
        print(f"Warning: Could not create uuid-ossp extension: {e}")
    
    # Check existing tables
    existing_tables = inspector.get_table_names()
    
    # Create organizations table if it doesn't exist
    if 'organizations' not in existing_tables:
        op.create_table(
            'organizations',
            sa.Column('id', postgresql.UUID(as_uuid=True), server_default=sa.text('uuid_generate_v4()'), primary_key=True),
            sa.Column('name', sa.String(100), nullable=False),
            sa.Column('tax_id', sa.String(50), nullable=True),
            sa.Column('address', sa.String(255), nullable=True),
            sa.Column('phone', sa.String(20), nullable=True),
            sa.Column('email', sa.String(100), nullable=True),
            sa.Column('website', sa.String(255), nullable=True),
            sa.Column('status', sa.String(20), server_default=sa.text("'active'"), nullable=False),
            sa.Column('firs_service_id', sa.String(100), nullable=True),
            sa.Column('logo_url', sa.String(255), nullable=True),
            sa.Column('branding_settings', postgresql.JSONB, nullable=True),
            sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
            sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now(), nullable=True)
        )
        print("Created organizations table")
    else:
        print("Organizations table already exists")
    
    # Create users table if it doesn't exist
    if 'users' not in existing_tables:
        op.create_table(
            'users',
            sa.Column('id', postgresql.UUID(as_uuid=True), server_default=sa.text('uuid_generate_v4()'), primary_key=True),
            sa.Column('email', sa.String(100), nullable=False, unique=True),
            sa.Column('password_hash', sa.String(255), nullable=False),
            sa.Column('full_name', sa.String(100), nullable=False),
            sa.Column('is_active', sa.Boolean, server_default=sa.text('true'), nullable=False),
            sa.Column('is_superuser', sa.Boolean, server_default=sa.text('false'), nullable=False),
            sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
            sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now(), nullable=True)
        )
        
        # Create unique index on email
        op.create_index('ix_users_email', 'users', ['email'], unique=True)
        print("Created users table")
    else:
        print("Users table already exists")
    
    # Create organization_users junction table if it doesn't exist
    if 'organization_users' not in existing_tables:
        op.create_table(
            'organization_users',
            sa.Column('id', postgresql.UUID(as_uuid=True), server_default=sa.text('uuid_generate_v4()'), primary_key=True),
            sa.Column('organization_id', postgresql.UUID(as_uuid=True), nullable=False),
            sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
            sa.Column('role', sa.String(50), server_default=sa.text("'member'"), nullable=False),
            sa.Column('is_primary', sa.Boolean, server_default=sa.text('false'), nullable=False),
            sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
            sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now(), nullable=True)
        )
        
        # Add foreign key constraints if both tables exist
        if 'organizations' in existing_tables or 'organizations' not in existing_tables:
            op.create_foreign_key(
                'fk_organization_users_organization_id', 
                'organization_users', 
                'organizations',
                ['organization_id'], 
                ['id'],
                ondelete='CASCADE'
            )
        
        if 'users' in existing_tables or 'users' not in existing_tables:
            op.create_foreign_key(
                'fk_organization_users_user_id', 
                'organization_users', 
                'users',
                ['user_id'], 
                ['id'],
                ondelete='CASCADE'
            )
        
        # Create unique constraint to prevent duplicate user-organization pairs
        op.create_unique_constraint(
            'uq_organization_users_org_user', 
            'organization_users', 
            ['organization_id', 'user_id']
        )
        
        print("Created organization_users table")
    else:
        print("Organization_users table already exists")


def downgrade() -> None:
    """Drop base tables."""
    
    connection = op.get_bind()
    inspector = sa.inspect(connection)
    
    # Only run for PostgreSQL
    if inspector.dialect.name != 'postgresql':
        print("Skipping PostgreSQL base tables cleanup - not running on PostgreSQL")
        return
    
    existing_tables = inspector.get_table_names()
    
    # Drop tables in reverse order to handle foreign key dependencies
    if 'organization_users' in existing_tables:
        op.drop_table('organization_users')
        print("Dropped organization_users table")
    
    if 'users' in existing_tables:
        op.drop_table('users')
        print("Dropped users table")
    
    if 'organizations' in existing_tables:
        op.drop_table('organizations')
        print("Dropped organizations table")