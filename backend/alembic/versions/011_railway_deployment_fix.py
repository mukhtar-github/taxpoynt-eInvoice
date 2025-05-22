"""Railway deployment fix

Revision ID: 011_railway_fix
Revises: 5757be8e289c
Create Date: 2025-05-22

This migration adds safety measures for deploying to Railway by making
the migrations more robust when tables might already exist.
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.engine import reflection
from sqlalchemy import text
from sqlalchemy.exc import ProgrammingError, OperationalError

# revision identifiers, used by Alembic.
revision = '011_railway_fix'
down_revision = '5757be8e289c'
branch_labels = None
depends_on = None


def table_exists(table_name):
    """Check if a table exists in the database."""
    try:
        conn = op.get_bind()
        inspector = reflection.Inspector.from_engine(conn)
        return table_name in inspector.get_table_names()
    except Exception:
        # If we can't check for some reason, assume it might exist
        return True


def upgrade():
    """Apply database upgrades."""
    # Create an enum type for integration status if it doesn't exist
    # This is often a source of problems in PostgreSQL migrations
    conn = op.get_bind()
    
    # Workaround for existing enums - recreate them if needed
    try:
        conn.execute(text("""
            DO $$
            BEGIN
                IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'integrationstatus') THEN
                    CREATE TYPE integrationstatus AS ENUM ('active', 'inactive', 'error', 'pending');
                END IF;
                
                IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'submissionstatus') THEN
                    CREATE TYPE submissionstatus AS ENUM ('pending', 'processing', 'completed', 'failed', 'cancelled');
                END IF;
            END
            $$;
        """))
    except (ProgrammingError, OperationalError):
        # Ignore errors if it already exists or we're using SQLite
        pass
    
    # Add any other Railway-specific fixes here
    # For example, you might want to ensure certain tables have the right extensions
    # or that specific sequences are properly set up
    
    # Example: Ensure the uuid-ossp extension is available for UUID generation
    try:
        conn.execute(text('CREATE EXTENSION IF NOT EXISTS "uuid-ossp";'))
    except (ProgrammingError, OperationalError):
        # Ignore errors if it's already installed or not applicable
        pass
    
    # Example: Reset any sequence values if needed
    # This might be useful if you've had failed migrations that left sequences in a bad state
    try:
        # Check if clients table exists before trying to update its sequence
        if table_exists('clients'):
            conn.execute(text("""
                SELECT setval(pg_get_serial_sequence('clients', 'id'), 
                       COALESCE((SELECT MAX(id) FROM clients), 1), 
                       false);
            """))
    except (ProgrammingError, OperationalError):
        # Ignore errors if sequence doesn't exist or table uses UUIDs
        pass


def downgrade():
    """Revert database changes."""
    # No need to downgrade since these are just safety measures
    pass
