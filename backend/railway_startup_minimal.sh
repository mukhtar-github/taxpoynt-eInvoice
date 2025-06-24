#!/bin/bash
# Minimal Railway deployment startup script for debugging
# This script helps identify where deployment is failing

echo "=== Starting Minimal TaxPoynt eInvoice Backend ==="
echo "Date: $(date)"
echo "Environment: ${RAILWAY_ENVIRONMENT:-unknown}"
echo "Working Directory: $(pwd)"
echo "Python Version: $(python3 --version)"
echo "PATH: $PATH"

# Check critical environment variables
echo "=== Environment Check ==="
echo "DATABASE_URL: ${DATABASE_URL:0:30}..." # Show first 30 chars only
echo "SECRET_KEY exists: $([ -n "$SECRET_KEY" ] && echo "YES" || echo "NO")"
echo "PORT: ${PORT:-8000}"

# Check if we can import the simple app
echo "=== Python Import Test ==="
python3 -c "
import sys
print(f'Python executable: {sys.executable}')
print(f'Python path: {sys.path}')

try:
    from app.simple_main import app
    print('SUCCESS: Simple app imported successfully')
except Exception as e:
    print(f'ERROR: Could not import simple app: {e}')
    import traceback
    traceback.print_exc()
    
    # Try the full app as fallback
    try:
        from app.main import app
        print('SUCCESS: Full app imported successfully')
    except Exception as e2:
        print(f'ERROR: Could not import full app either: {e2}')
        traceback.print_exc()
        exit(1)
"

if [ $? -ne 0 ]; then
    echo "FATAL: Python import failed, exiting"
    exit 1
fi

# Start the application with minimal configuration
echo "=== Starting Application ==="
exec uvicorn app.simple_main:app \
    --host 0.0.0.0 \
    --port ${PORT:-8000} \
    --log-level debug \
    --access-log