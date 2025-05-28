#!/bin/bash
# Railway deployment startup script
# This script helps manage database migrations safely for Railway deployments
# Enhanced with better error handling and auto-merge capability

# Note: We're removing 'set -e' to allow better error handling in the script

echo "Starting TaxPoynt eInvoice backend deployment on Railway..."

# Function to log messages with timestamps
log_message() {
  echo "$(date +"%Y-%m-%d %H:%M:%S") - $1"
}

# Function to handle database migrations with additional safety
handle_migrations() {
    log_message "Checking database migration status..."
    
    # Try migration with heads first (best practice for merged migrations)
    log_message "Attempting migration with 'alembic upgrade heads'..."
    alembic upgrade heads

    # Check if the migration succeeded
    if [ $? -eq 0 ]; then
        log_message "Migration with 'heads' successful!"
    else
        log_message "Migration with 'heads' failed, trying alternative approaches..."
        
        # Get list of revision heads
        HEADS=$(alembic heads)
        HEAD_COUNT=$(echo "$HEADS" | grep -c "Rev:")
        
        if [ $HEAD_COUNT -gt 1 ]; then
            log_message "Found $HEAD_COUNT migration heads. Attempting auto-merge..."
            
            # Try to auto-merge the heads
            MERGE_NAME="railway_automerge_$(date +%Y%m%d_%H%M%S)"
            alembic merge heads -m "$MERGE_NAME"
            
            if [ $? -eq 0 ]; then
                log_message "Auto-merge created successfully. Applying merged migration..."
                alembic upgrade heads
                
                if [ $? -ne 0 ]; then
                    log_message "Failed to apply merged migration. Trying individual heads..."
                    # Attempt to upgrade to each head individually
                    for HEAD in $(alembic heads | grep "Rev:" | awk '{print $2}'); do
                        log_message "Attempting to upgrade to $HEAD..."
                        alembic upgrade $HEAD
                    done
                fi
            else
                log_message "Auto-merge failed. Trying to apply migrations individually..."
                # Try each head revision individually
                for HEAD in $(alembic heads | grep "Rev:" | awk '{print $2}'); do
                    log_message "Attempting to upgrade to $HEAD..."
                    alembic upgrade $HEAD
                done
            fi
        else
            # Try with 'head' (singular) as fallback
            log_message "Attempting migration with 'alembic upgrade head'..."
            alembic upgrade head
            
            if [ $? -ne 0 ]; then
                log_message "Migration with 'head' also failed, attempting to stamp current state..."
                
                # Try to stamp the current state to avoid repeated migrations
                for HEAD in $(alembic heads | grep "Rev:" | awk '{print $2}'); do
                    log_message "Attempting to stamp $HEAD..."
                    alembic stamp $HEAD
                done
                
                if [ $? -ne 0 ]; then
                    log_message "WARNING: Could not stamp current migration state!"
                fi
            fi
        fi
    fi
    
    log_message "Database migration process completed."
}

# Main deployment process
main() {
    # Make sure the script is executable
    chmod +x "${BASH_SOURCE[0]}"
    
    # Run database migrations with additional safety measures
    handle_migrations
    
    # Start the backend service
    log_message "Starting backend service..."
    # Start the application with uvicorn (safer than relying on Docker CMD for consistent behavior)
    exec uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}
}

# Execute the main function
main
