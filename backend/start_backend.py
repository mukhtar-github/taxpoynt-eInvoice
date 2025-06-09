#!/usr/bin/env python
"""
Bootstrap script to start the TaxPoynt eInvoice backend
with proper environment variable handling for Pydantic V2.
"""
import os
import sys
import subprocess

# Define environment variables from .env file if it exists
def load_env():
    """Load environment variables from .env file"""
    env_file = os.path.join(os.path.dirname(__file__), ".env")
    if os.path.exists(env_file):
        with open(env_file, "r") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#"):
                    key, value = line.split("=", 1)
                    os.environ[key] = value.strip('"\'')

# Start the backend with modified environment
def start_backend():
    print("Starting TaxPoynt eInvoice backend...")
    # Set environment variable to control Pydantic behavior
    os.environ["PYDANTIC_STRICT_VALIDATION"] = "False"
    # Execute the main module directly
    subprocess.run([sys.executable, "-m", "app.main"], cwd=os.path.dirname(os.path.abspath(__file__)))

if __name__ == "__main__":
    load_env()
    start_backend()
