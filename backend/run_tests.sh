#!/bin/bash
# Test runner for TaxPoynt eInvoice
# Ensures correct environment setup for running tests

# Set Python path to include backend directory
export PYTHONPATH=$PYTHONPATH:$(pwd)

# Check if specific test file provided
if [ $# -eq 0 ]; then
    echo "Running all tests..."
    find tests -name "test_*.py" | while read test_file; do
        echo "===== Running $test_file ====="
        python -m unittest $test_file
    done
else
    # Run specific test file
    test_file=$1
    echo "Running test: $test_file"
    python -m unittest $test_file
fi
