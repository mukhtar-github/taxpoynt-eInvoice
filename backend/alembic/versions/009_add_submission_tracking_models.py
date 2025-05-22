"""Add submission tracking models

Revision ID: 009
Revises: 008_add_validation_rule_management
Create Date: 2025-05-22 05:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
from sqlalchemy.sql import text

# revision identifiers, used by Alembic.
revision = 'ea54c28af931'
down_revision = '008'
branch_labels = None
depends_on = None


def upgrade():
    # Create submission status enum type
    op.execute(
        """
        CREATE TYPE submission_status AS ENUM (
            'pending',
            'processing',
            'validated',
            'signed',
            'accepted',
            'rejected',
            'failed',
            'error',
            'cancelled'
        )
        """
    )
    
    # Create notification status enum type
    op.execute(
        """
        CREATE TYPE notification_status AS ENUM (
            'pending',
            'delivered',
            'failed',
            'retry'
        )
        """
    )
    
    # Create submission_records table
    op.create_table(
        'submission_records',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('submission_id', sa.String(100), nullable=False, unique=True, index=True),
        sa.Column('irn', sa.String(50), sa.ForeignKey('irn_records.irn'), nullable=False, index=True),
        sa.Column('integration_id', sa.String(36), sa.ForeignKey('integrations.id'), nullable=False),
        sa.Column('status', sa.Enum('pending', 'processing', 'validated', 'signed', 'accepted', 'rejected', 'failed', 'error', 'cancelled', name='submission_status'), nullable=False, server_default='pending'),
        sa.Column('status_message', sa.String(512), nullable=True),
        sa.Column('last_updated', sa.DateTime, nullable=False, server_default=sa.func.now()),
        sa.Column('created_at', sa.DateTime, nullable=False, server_default=sa.func.now()),
        sa.Column('request_data', postgresql.JSON, nullable=True),
        sa.Column('response_data', postgresql.JSON, nullable=True),
        sa.Column('source_type', sa.String(50), nullable=False),
        sa.Column('source_id', sa.String(100), nullable=True),
        sa.Column('submitted_by', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id'), nullable=True),
        sa.Column('webhook_enabled', sa.Boolean, nullable=False, server_default='false'),
        sa.Column('webhook_url', sa.String(512), nullable=True)
    )
    
    # Create submission_status_updates table
    op.create_table(
        'submission_status_updates',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('submission_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('submission_records.id'), nullable=False),
        sa.Column('status', sa.Enum('pending', 'processing', 'validated', 'signed', 'accepted', 'rejected', 'failed', 'error', 'cancelled', name='submission_status'), nullable=False),
        sa.Column('message', sa.String(512), nullable=True),
        sa.Column('response_data', postgresql.JSON, nullable=True),
        sa.Column('timestamp', sa.DateTime, nullable=False, server_default=sa.func.now())
    )
    
    # Create submission_notifications table
    op.create_table(
        'submission_notifications',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('submission_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('submission_records.id'), nullable=False),
        sa.Column('status_update_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('submission_status_updates.id'), nullable=False),
        sa.Column('webhook_url', sa.String(512), nullable=False),
        sa.Column('payload', postgresql.JSON, nullable=False),
        sa.Column('status', sa.Enum('pending', 'delivered', 'failed', 'retry', name='notification_status'), nullable=False, server_default='pending'),
        sa.Column('attempts', sa.Integer, nullable=False, server_default='0'),
        sa.Column('last_attempt', sa.DateTime, nullable=True),
        sa.Column('next_attempt', sa.DateTime, nullable=True),
        sa.Column('response_code', sa.Integer, nullable=True),
        sa.Column('response_body', sa.Text, nullable=True),
        sa.Column('error_message', sa.String(512), nullable=True),
        sa.Column('timestamp', sa.DateTime, nullable=False, server_default=sa.func.now())
    )
    
    # Create indexes for fast lookups
    op.create_index('ix_submission_records_submission_id', 'submission_records', ['submission_id'])
    op.create_index('ix_submission_records_irn', 'submission_records', ['irn'])
    op.create_index('ix_submission_records_status', 'submission_records', ['status'])
    op.create_index('ix_submission_status_updates_submission_id', 'submission_status_updates', ['submission_id'])
    op.create_index('ix_submission_status_updates_timestamp', 'submission_status_updates', ['timestamp'])
    op.create_index('ix_submission_notifications_submission_id', 'submission_notifications', ['submission_id'])
    op.create_index('ix_submission_notifications_status', 'submission_notifications', ['status'])
    op.create_index('ix_submission_notifications_next_attempt', 'submission_notifications', ['next_attempt'])


def downgrade():
    # Drop tables in reverse order of creation
    op.drop_table('submission_notifications')
    op.drop_table('submission_status_updates')
    op.drop_table('submission_records')
    
    # Drop enum types
    op.execute('DROP TYPE notification_status')
    op.execute('DROP TYPE submission_status')
