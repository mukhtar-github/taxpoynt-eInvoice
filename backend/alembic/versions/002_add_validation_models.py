"""Add validation models

Revision ID: 002
Revises: 001
Create Date: 2024-07-13 10:00:00.000000

"""
from alembic import op
import sqlalchemy as sa # type: ignore
from sqlalchemy.dialects import postgresql # type: ignore

# revision identifiers, used by Alembic.
revision = '002'
down_revision = '001'
branch_labels = None
depends_on = None


def upgrade():
    # Create validation_rules table
    op.create_table(
        'validation_rules',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('name', sa.String(100), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('rule_type', sa.String(50), nullable=False),
        sa.Column('field_path', sa.String(255), nullable=True),
        sa.Column('validation_logic', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column('error_message', sa.Text(), nullable=False),
        sa.Column('severity', sa.String(20), nullable=False, server_default='error'),
        sa.Column('created_at', sa.TIMESTAMP(), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.TIMESTAMP(), server_default=sa.text('now()'), nullable=False),
        sa.Column('active', sa.Boolean(), nullable=False, server_default='true'),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create validation_records table
    op.create_table(
        'validation_records',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('integration_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('irn', sa.String(50), nullable=True),
        sa.Column('invoice_data', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column('is_valid', sa.Boolean(), nullable=False),
        sa.Column('validation_time', sa.TIMESTAMP(), server_default=sa.text('now()'), nullable=False),
        sa.Column('issues', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('external_id', sa.String(100), nullable=True),
        sa.ForeignKeyConstraint(['integration_id'], ['integrations.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['irn'], ['irn_records.irn'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create indexes
    op.create_index(op.f('ix_validation_records_integration_id'), 'validation_records', ['integration_id'], unique=False)
    op.create_index(op.f('ix_validation_records_irn'), 'validation_records', ['irn'], unique=False)
    op.create_index(op.f('ix_validation_records_validation_time'), 'validation_records', ['validation_time'], unique=False)
    op.create_index(op.f('ix_validation_rules_rule_type'), 'validation_rules', ['rule_type'], unique=False)
    op.create_index(op.f('ix_validation_rules_active'), 'validation_rules', ['active'], unique=False)


def downgrade():
    # Drop indexes
    op.drop_index(op.f('ix_validation_rules_active'), table_name='validation_rules')
    op.drop_index(op.f('ix_validation_rules_rule_type'), table_name='validation_rules')
    op.drop_index(op.f('ix_validation_records_validation_time'), table_name='validation_records')
    op.drop_index(op.f('ix_validation_records_irn'), table_name='validation_records')
    op.drop_index(op.f('ix_validation_records_integration_id'), table_name='validation_records')
    
    # Drop tables
    op.drop_table('validation_records')
    op.drop_table('validation_rules') 