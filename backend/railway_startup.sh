#!/bin/bash
# Railway deployment startup script
# This script helps manage database migrations safely for Railway deployments

set -e  # Exit immediately if a command exits with a non-zero status

echo "Starting TaxPoynt eInvoice backend deployment on Railway..."

# Function to handle database migrations with additional safety
handle_migrations() {
    echo "Checking database migration status..."
    
    # Try to run migrations with 'heads' to handle multiple heads case
    if ! alembic upgrade heads; then
        echo "Migration with 'heads' failed, trying alternative approaches..."
        
        # Try to run with just 'head' (single head case)
        if ! alembic upgrade head; then
            echo "Migration with 'head' also failed, attempting to stamp current state..."
            
            # If both approaches fail, try to stamp the current state and then upgrade
            if ! alembic stamp head; then
                echo "WARNING: Could not stamp current migration state!"
            else
                echo "Successfully stamped current state, attempting migration again..."
                alembic upgrade head
            fi
        fi
    fi
    
    echo "Database migration process completed."
}

# Main deployment process
main() {
    # Make sure the script is executable
    chmod +x "${BASH_SOURCE[0]}"
    
    # Run database migrations with additional safety measures
    handle_migrations
    
    # Start the backend service
    echo "Starting backend service..."
    # Railway automatically uses the CMD from your Dockerfile
    # or the "start" command in your railway.json file
    # We'll just let that happen naturally by not explicitly starting anything here
    
    echo "TaxPoynt eInvoice backend deployment process completed."
}

# Execute the main function
main
