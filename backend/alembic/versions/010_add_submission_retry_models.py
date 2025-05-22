"""Add submission retry models

Revision ID: 5a1928efb34d
Revises: ea54c28af931
Create Date: 2025-05-22 06:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
from sqlalchemy.sql import text

# revision identifiers, used by Alembic.
revision = '5a1928efb34d'
down_revision = 'ea54c28af931'
branch_labels = None
depends_on = None


def upgrade():
    # Create retry status enum type
    op.execute(
        """
        CREATE TYPE retry_status AS ENUM (
            'pending',
            'in_progress',
            'succeeded',
            'failed',
            'cancelled',
            'max_retries_exceeded'
        )
        """
    )
    
    # Create failure severity enum type
    op.execute(
        """
        CREATE TYPE failure_severity AS ENUM (
            'low',
            'medium',
            'high',
            'critical'
        )
        """
    )
    
    # Create submission_retries table
    op.create_table(
        'submission_retries',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('submission_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('submission_records.id'), nullable=False, index=True),
        sa.Column('attempt_number', sa.Integer, nullable=False, server_default='1'),
        sa.Column('max_attempts', sa.Integer, nullable=False, server_default='5'),
        sa.Column('next_attempt_at', sa.DateTime, nullable=True, index=True),
        sa.Column('last_attempt_at', sa.DateTime, nullable=True),
        sa.Column('backoff_factor', sa.Float, nullable=False, server_default='2.0'),
        sa.Column('base_delay', sa.Integer, nullable=False, server_default='60'),
        sa.Column('jitter', sa.Float, nullable=False, server_default='0.1'),
        sa.Column('status', sa.Enum('pending', 'in_progress', 'succeeded', 'failed', 'cancelled', 'max_retries_exceeded', name='retry_status'), nullable=False, server_default='pending'),
        sa.Column('created_at', sa.DateTime, nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime, nullable=False, server_default=sa.func.now(), onupdate=sa.func.now()),
        sa.Column('error_type', sa.String(100), nullable=True),
        sa.Column('error_message', sa.String(1000), nullable=True),
        sa.Column('error_details', postgresql.JSON, nullable=True),
        sa.Column('stack_trace', sa.Text, nullable=True),
        sa.Column('severity', sa.Enum('low', 'medium', 'high', 'critical', name='failure_severity'), nullable=False, server_default='medium'),
        sa.Column('alert_sent', sa.Boolean, nullable=False, server_default='false')
    )
    
    # Create indexes for fast lookups
    op.create_index('ix_submission_retries_submission_id', 'submission_retries', ['submission_id'])
    op.create_index('ix_submission_retries_next_attempt_at', 'submission_retries', ['next_attempt_at'])
    op.create_index('ix_submission_retries_status', 'submission_retries', ['status'])
    op.create_index('ix_submission_retries_severity', 'submission_retries', ['severity'])


def downgrade():
    # Drop tables in reverse order of creation
    op.drop_table('submission_retries')
    
    # Drop enum types
    op.execute('DROP TYPE failure_severity')
    op.execute('DROP TYPE retry_status')
