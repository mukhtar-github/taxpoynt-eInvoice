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

# Function to run pre-startup health checks
pre_startup_checks() {
    log_message "Running pre-startup health checks..."
    
    # Check database connectivity
    log_message "Testing database connectivity..."
    python -c "
from app.db.session import SessionLocal
try:
    with SessionLocal() as db:
        result = db.execute('SELECT 1').scalar()
        if result == 1:
            print('Database connection: OK')
        else:
            print('Database connection: FAILED')
            exit(1)
except Exception as e:
    print(f'Database connection: FAILED - {str(e)}')
    exit(1)
"
    
    if [ $? -ne 0 ]; then
        log_message "ERROR: Database connectivity check failed"
        exit 1
    fi
    
    # Check Redis connectivity
    log_message "Testing Redis connectivity..."
    python -c "
from app.db.redis import get_redis_client
try:
    redis_client = get_redis_client()
    pong = redis_client.ping()
    if pong:
        print('Redis connection: OK')
    else:
        print('Redis connection: FAILED')
        exit(1)
except Exception as e:
    print(f'Redis connection: FAILED - {str(e)}')
    exit(1)
"
    
    if [ $? -ne 0 ]; then
        log_message "WARNING: Redis connectivity check failed - some features may not work"
        # Don't exit for Redis failure as it's not critical for basic operation
    fi
    
    # Check critical environment variables
    log_message "Checking critical environment variables..."
    
    if [ -z "$DATABASE_URL" ]; then
        log_message "ERROR: DATABASE_URL is not set"
        exit 1
    fi
    
    if [ -z "$SECRET_KEY" ]; then
        log_message "ERROR: SECRET_KEY is not set"
        exit 1
    fi
    
    log_message "Pre-startup health checks completed successfully"
}

# Function to wait for dependencies
wait_for_dependencies() {
    log_message "Waiting for dependencies to be ready..."
    
    # Wait for database to be ready (with timeout)
    local db_timeout=60
    local db_elapsed=0
    local db_interval=5
    
    while [ $db_elapsed -lt $db_timeout ]; do
        if python -c "
from app.db.session import SessionLocal
try:
    with SessionLocal() as db:
        db.execute('SELECT 1').scalar()
        exit(0)
except:
    exit(1)
" > /dev/null 2>&1; then
            log_message "Database is ready"
            break
        fi
        
        log_message "Waiting for database... (${db_elapsed}s/${db_timeout}s)"
        sleep $db_interval
        db_elapsed=$((db_elapsed + db_interval))
    done
    
    if [ $db_elapsed -ge $db_timeout ]; then
        log_message "ERROR: Database not ready after ${db_timeout} seconds"
        exit 1
    fi
}

# Function to start application with health monitoring
start_application() {
    log_message "Starting application with health monitoring..."
    
    # Start deployment monitoring in background
    python -c "
import asyncio
import logging
from app.services.deployment_monitor import get_deployment_monitor
import os

# Setup basic logging for monitoring
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger('deployment_monitor')

async def start_monitoring():
    try:
        monitor = get_deployment_monitor()
        deployment_id = os.environ.get('RAILWAY_DEPLOYMENT_ID', f'railway-{int(__import__('time').time())}')
        logger.info(f'Starting deployment monitoring for: {deployment_id}')
        await monitor.start_monitoring(deployment_id)
        logger.info('Deployment monitoring started successfully')
    except Exception as e:
        logger.error(f'Failed to start deployment monitoring: {str(e)}')
        # Don't fail startup for monitoring issues
        pass

# Don't block startup for monitoring
try:
    asyncio.run(start_monitoring())
except Exception as e:
    print(f'Monitoring startup failed: {e}')
    pass
" &
    
    # Start the application
    log_message "Starting uvicorn server..."
    exec uvicorn app.main:app \
        --host 0.0.0.0 \
        --port ${PORT:-8000} \
        --timeout-keep-alive 65 \
        --access-log \
        --use-colors
}

# Main deployment process
main() {
    # Make sure the script is executable
    chmod +x "${BASH_SOURCE[0]}"
    
    # Wait for dependencies
    wait_for_dependencies
    
    # Run database migrations with additional safety measures
    handle_migrations
    
    # Run pre-startup health checks
    pre_startup_checks
    
    # Start the application with monitoring
    start_application
}

# Execute the main function
main
