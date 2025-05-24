"""create submission retries table for prod

Revision ID: 97d2d22910b1
Revises: 011_railway_fix
Create Date: 2025-05-24 11:49:25.576768

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '97d2d22910b1'
down_revision = '011_railway_fix'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create submission_retries table
    # First, check if submission_records table exists
    op.execute("""
    DO $$
    BEGIN
        IF NOT EXISTS (SELECT FROM pg_tables WHERE schemaname = 'public' AND tablename = 'submission_records') THEN
            -- Create a minimal submission_records table if it doesn't exist
            CREATE TABLE submission_records (
                id UUID PRIMARY KEY,
                created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
            );
        END IF;
    END
    $$;
    """);
    
    # Now create the submission_retries table
    op.execute("""
    CREATE TABLE IF NOT EXISTS submission_retries (
        id UUID PRIMARY KEY,
        submission_id UUID NOT NULL,
        
        -- Retry tracking
        attempt_number INTEGER NOT NULL DEFAULT 1,
        max_attempts INTEGER NOT NULL DEFAULT 5,
        next_attempt_at TIMESTAMP WITH TIME ZONE,
        last_attempt_at TIMESTAMP WITH TIME ZONE,
        backoff_factor FLOAT NOT NULL DEFAULT 2.0,
        base_delay INTEGER NOT NULL DEFAULT 60,
        jitter FLOAT NOT NULL DEFAULT 0.1,
        
        -- Status tracking
        status VARCHAR(20) NOT NULL DEFAULT 'pending',
        created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
        updated_at TIMESTAMP WITH TIME ZONE,
        
        -- Error information
        error_type VARCHAR(100),
        error_message TEXT,
        error_details JSONB,
        stack_trace TEXT,
        severity VARCHAR(20) DEFAULT 'low',
        alert_sent BOOLEAN DEFAULT FALSE
    );
    
    -- Create indexes for better performance
    CREATE INDEX IF NOT EXISTS idx_submission_retries_submission_id ON submission_retries(submission_id);
    CREATE INDEX IF NOT EXISTS idx_submission_retries_status ON submission_retries(status);
    CREATE INDEX IF NOT EXISTS idx_submission_retries_next_attempt_at ON submission_retries(next_attempt_at);
    
    -- Add foreign key constraint if both tables exist
    DO $$
    BEGIN
        IF EXISTS (SELECT FROM pg_tables WHERE schemaname = 'public' AND tablename = 'submission_records') AND 
           EXISTS (SELECT FROM pg_tables WHERE schemaname = 'public' AND tablename = 'submission_retries') THEN
            IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'fk_submission_retries_submission_id') THEN
                ALTER TABLE submission_retries
                ADD CONSTRAINT fk_submission_retries_submission_id
                FOREIGN KEY (submission_id) REFERENCES submission_records(id);
            END IF;
        END IF;
    END
    $$;
    """)


def downgrade() -> None:
    # Drop indexes first
    op.execute("DROP INDEX IF EXISTS idx_submission_retries_next_attempt_at;")
    op.execute("DROP INDEX IF EXISTS idx_submission_retries_status;")
    op.execute("DROP INDEX IF EXISTS idx_submission_retries_submission_id;")
    
    # Drop the table
    op.execute("DROP TABLE IF EXISTS submission_retries;")
    
