-- SQL script to create the submission_retries table in PostgreSQL
-- This is based on the SubmissionRetry model definition

CREATE TABLE IF NOT EXISTS submission_retries (
    id UUID PRIMARY KEY,
    submission_id UUID NOT NULL REFERENCES submission_records(id),
    
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
    alert_sent BOOLEAN DEFAULT FALSE,
    
    -- Indexes for query optimization
    CONSTRAINT submission_retry_unique_id UNIQUE (id),
    CONSTRAINT submission_retry_status_next_attempt_idx UNIQUE (status, next_attempt_at)
);

-- Create indexes for better performance
CREATE INDEX IF NOT EXISTS idx_submission_retries_submission_id ON submission_retries(submission_id);
CREATE INDEX IF NOT EXISTS idx_submission_retries_status ON submission_retries(status);
CREATE INDEX IF NOT EXISTS idx_submission_retries_next_attempt_at ON submission_retries(next_attempt_at);

-- Create sequence for ID generation (if using serial IDs)
-- CREATE SEQUENCE IF NOT EXISTS submission_retries_id_seq;
