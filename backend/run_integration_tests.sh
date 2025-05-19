#!/bin/bash
# Integration test runner for FIRS submission API
# This script runs the integration tests against a running API instance

# Default API URL
API_URL="http://localhost:8000/api/v1"

# Check if custom API URL provided
if [ $# -eq 1 ]; then
  API_URL=$1
fi

# Check if credentials are provided via environment variables
if [ -z "$TEST_USER_EMAIL" ] || [ -z "$TEST_USER_PASSWORD" ]; then
  echo "⚠️  Warning: TEST_USER_EMAIL and TEST_USER_PASSWORD environment variables not set."
  echo "   Using default test credentials. This may fail in a real environment."
  echo ""
fi

# Ensure the requests package is installed
if ! ./venv/bin/python -c "import requests" 2>/dev/null; then
  echo "📦 Installing required packages..."
  ./venv/bin/pip install requests
fi

echo "🚀 Running FIRS submission integration tests against: $API_URL"
echo ""

# Run the integration tests
export PYTHONPATH=$PYTHONPATH:$(pwd)
./venv/bin/python backend/tests/integration/test_firs_submission_api.py $API_URL

# Check exit status
if [ $? -eq 0 ]; then
  echo "✅ Integration tests completed successfully!"
else
  echo "❌ Integration tests failed. Check output for details."
fi
