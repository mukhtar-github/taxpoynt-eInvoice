"""Add validation rule management tables

Revision ID: 008
Revises: 007_add_certificate_storage
Create Date: 2025-05-12

This migration adds the database tables needed for the enhanced validation rule management system,
particularly focused on FIRS e-Invoice validation requirements.
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
import uuid
from sqlalchemy.dialects.postgresql import UUID


# revision identifiers, used by Alembic
revision = '008'
down_revision = '007_add_certificate_storage'
branch_labels = None
depends_on = None


def upgrade():
    """Upgrade database to revision 008."""
    # Create enum types
    op.create_table(
        'validation_rules',
        sa.Column('id', UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
        sa.Column('name', sa.String(100), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('rule_type', sa.String(50), nullable=False),
        sa.Column('field_path', sa.String(255), nullable=True),
        sa.Column('validation_logic', sa.JSON(), nullable=False),
        sa.Column('error_message', sa.Text(), nullable=False),
        sa.Column('severity', sa.String(20), nullable=False),
        sa.Column('source', sa.String(20), nullable=False),
        sa.Column('status', sa.String(20), nullable=False),
        sa.Column('created_at', sa.TIMESTAMP(), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.Column('updated_at', sa.TIMESTAMP(), server_default=sa.text('CURRENT_TIMESTAMP'), onupdate=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.Column('created_by', UUID(as_uuid=True), nullable=True),
        sa.Column('updated_by', UUID(as_uuid=True), nullable=True),
        sa.Column('tags', sa.JSON(), nullable=True)
    )
    
    # Enhance the validation_records table with additional fields
    op.add_column('validation_records', sa.Column('validated_by', UUID(as_uuid=True), nullable=True))
    op.add_column('validation_records', sa.Column('source', sa.String(50), nullable=True))
    op.add_column('validation_records', sa.Column('duration_ms', sa.Integer(), nullable=True))
    
    # Create custom_validation_rules table
    op.create_table(
        'custom_validation_rules',
        sa.Column('id', UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
        sa.Column('original_rule_id', sa.String(100), nullable=True),
        sa.Column('name', sa.String(100), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('rule_type', sa.String(50), nullable=False),
        sa.Column('field_path', sa.String(255), nullable=True),
        sa.Column('validator_definition', sa.JSON(), nullable=False),
        sa.Column('error_message', sa.Text(), nullable=False),
        sa.Column('severity', sa.String(20), nullable=False),
        sa.Column('category', sa.String(50), nullable=True),
        sa.Column('status', sa.String(20), nullable=False),
        sa.Column('created_at', sa.TIMESTAMP(), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.Column('updated_at', sa.TIMESTAMP(), server_default=sa.text('CURRENT_TIMESTAMP'), onupdate=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.Column('created_by', UUID(as_uuid=True), nullable=True),
        sa.Column('updated_by', UUID(as_uuid=True), nullable=True)
    )
    
    # Create validation_rule_presets table
    op.create_table(
        'validation_rule_presets',
        sa.Column('id', UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
        sa.Column('name', sa.String(100), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('preset_type', sa.String(50), nullable=False),
        sa.Column('rules', sa.JSON(), nullable=False),
        sa.Column('is_default', sa.Boolean(), default=False),
        sa.Column('created_at', sa.TIMESTAMP(), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.Column('updated_at', sa.TIMESTAMP(), server_default=sa.text('CURRENT_TIMESTAMP'), onupdate=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.Column('created_by', UUID(as_uuid=True), nullable=True),
        sa.Column('updated_by', UUID(as_uuid=True), nullable=True)
    )
    
    # Create indices for better query performance
    op.create_index('ix_validation_rules_rule_type', 'validation_rules', ['rule_type'])
    op.create_index('ix_validation_rules_source', 'validation_rules', ['source'])
    op.create_index('ix_validation_rules_status', 'validation_rules', ['status'])
    op.create_index('ix_custom_validation_rules_rule_type', 'custom_validation_rules', ['rule_type'])
    op.create_index('ix_custom_validation_rules_status', 'custom_validation_rules', ['status'])
    op.create_index('ix_custom_validation_rules_category', 'custom_validation_rules', ['category'])
    op.create_index('ix_validation_rule_presets_preset_type', 'validation_rule_presets', ['preset_type'])
    op.create_index('ix_validation_rule_presets_is_default', 'validation_rule_presets', ['is_default'])


def downgrade():
    """Downgrade database to revision 007."""
    # Drop indices
    op.drop_index('ix_validation_rule_presets_is_default', 'validation_rule_presets')
    op.drop_index('ix_validation_rule_presets_preset_type', 'validation_rule_presets')
    op.drop_index('ix_custom_validation_rules_category', 'custom_validation_rules')
    op.drop_index('ix_custom_validation_rules_status', 'custom_validation_rules')
    op.drop_index('ix_custom_validation_rules_rule_type', 'custom_validation_rules')
    op.drop_index('ix_validation_rules_status', 'validation_rules')
    op.drop_index('ix_validation_rules_source', 'validation_rules')
    op.drop_index('ix_validation_rules_rule_type', 'validation_rules')
    
    # Drop tables
    op.drop_table('validation_rule_presets')
    op.drop_table('custom_validation_rules')
    op.drop_table('validation_rules')
    
    # Remove added columns from validation_records
    op.drop_column('validation_records', 'duration_ms')
    op.drop_column('validation_records', 'source')
    op.drop_column('validation_records', 'validated_by')
