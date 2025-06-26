"""add_service_based_permissions

Revision ID: 016_add_service_based_permissions
Revises: 015_add_nigerian_compliance_models
Create Date: 2025-06-26 16:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '016_add_service_based_permissions'
down_revision = '015_add_nigerian_compliance_models'
branch_labels = None
depends_on = None


def upgrade():
    # Create enum types for service access
    service_type_enum = postgresql.ENUM(
        'system_integration', 'access_point_provider', 'nigerian_compliance', 'organization_management',
        name='servicetype',
        create_type=False
    )
    access_level_enum = postgresql.ENUM(
        'read', 'write', 'admin', 'owner',
        name='accesslevel',
        create_type=False
    )
    
    # Create enum types if they don't exist
    op.execute("DO $$ BEGIN CREATE TYPE servicetype AS ENUM ('system_integration', 'access_point_provider', 'nigerian_compliance', 'organization_management'); EXCEPTION WHEN duplicate_object THEN null; END $$;")
    op.execute("DO $$ BEGIN CREATE TYPE accesslevel AS ENUM ('read', 'write', 'admin', 'owner'); EXCEPTION WHEN duplicate_object THEN null; END $$;")
    
    # ### Create User Service Access table ###
    op.create_table('user_service_access',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('service_type', service_type_enum, nullable=False),
        sa.Column('access_level', access_level_enum, nullable=False),
        sa.Column('granted_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('granted_at', sa.DateTime(), nullable=False),
        sa.Column('expires_at', sa.DateTime(), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False),
        sa.Column('notes', sa.String(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['granted_by'], ['users.id'], ),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_user_service_access_id'), 'user_service_access', ['id'], unique=False)
    op.create_index(op.f('ix_user_service_access_user_id'), 'user_service_access', ['user_id'], unique=False)
    op.create_index(op.f('ix_user_service_access_service_type'), 'user_service_access', ['service_type'], unique=False)
    op.create_index(op.f('ix_user_service_access_is_active'), 'user_service_access', ['is_active'], unique=False)
    
    # Create unique constraint for active service access per user
    op.create_index(
        'ix_user_service_access_unique_active',
        'user_service_access',
        ['user_id', 'service_type'],
        unique=True,
        postgresql_where=sa.text('is_active = true')
    )

    # ### Create Service Access Audit Log table ###
    op.create_table('service_access_audit_log',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('user_service_access_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('action', sa.String(length=50), nullable=False),
        sa.Column('changed_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('change_reason', sa.String(), nullable=True),
        sa.Column('old_values', sa.String(), nullable=True),
        sa.Column('new_values', sa.String(), nullable=True),
        sa.Column('timestamp', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['changed_by'], ['users.id'], ),
        sa.ForeignKeyConstraint(['user_service_access_id'], ['user_service_access.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_service_access_audit_log_id'), 'service_access_audit_log', ['id'], unique=False)
    op.create_index(op.f('ix_service_access_audit_log_timestamp'), 'service_access_audit_log', ['timestamp'], unique=False)
    op.create_index(op.f('ix_service_access_audit_log_action'), 'service_access_audit_log', ['action'], unique=False)


def downgrade():
    # ### Drop tables ###
    op.drop_index(op.f('ix_service_access_audit_log_action'), table_name='service_access_audit_log')
    op.drop_index(op.f('ix_service_access_audit_log_timestamp'), table_name='service_access_audit_log')
    op.drop_index(op.f('ix_service_access_audit_log_id'), table_name='service_access_audit_log')
    op.drop_table('service_access_audit_log')
    
    op.drop_index('ix_user_service_access_unique_active', table_name='user_service_access')
    op.drop_index(op.f('ix_user_service_access_is_active'), table_name='user_service_access')
    op.drop_index(op.f('ix_user_service_access_service_type'), table_name='user_service_access')
    op.drop_index(op.f('ix_user_service_access_user_id'), table_name='user_service_access')
    op.drop_index(op.f('ix_user_service_access_id'), table_name='user_service_access')
    op.drop_table('user_service_access')
    
    # ### Drop enum types ###
    op.execute("DROP TYPE IF EXISTS servicetype;")
    op.execute("DROP TYPE IF EXISTS accesslevel;")