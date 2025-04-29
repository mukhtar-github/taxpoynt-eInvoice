#!/bin/bash

# Exit on error
set -e

echo "🔧 Setting up environment variables..."

# Create .env file if it doesn't exist
if [ ! -f ".env" ]; then
    echo "📝 Creating .env file..."
    touch .env
fi

# Function to set environment variable if not already set
set_env_var() {
    local key=$1
    local value=$2
    if ! grep -q "^${key}=" .env; then
        echo "${key}=${value}" >> .env
        echo "✅ Set ${key}"
    else
        echo "⚠️  ${key} already exists in .env"
    fi
}

# Set required environment variables
set_env_var "APP_ENV" "development"
set_env_var "SECRET_KEY" "$(openssl rand -hex 32)"
set_env_var "ENCRYPTION_KEY" "$(openssl rand -hex 32)"

# Database configuration
set_env_var "POSTGRES_SERVER" "localhost"
set_env_var "POSTGRES_USER" "postgres"
set_env_var "POSTGRES_PASSWORD" "postgres"
set_env_var "POSTGRES_DB" "taxpoynt"

# Redis configuration
set_env_var "REDIS_HOST" "localhost"
set_env_var "REDIS_PORT" "6379"
set_env_var "REDIS_PASSWORD" ""
set_env_var "REDIS_DB" "0"

# Email configuration
set_env_var "SMTP_HOST" ""
set_env_var "SMTP_PORT" "587"
set_env_var "SMTP_USER" ""
set_env_var "SMTP_PASSWORD" ""
set_env_var "EMAILS_FROM_EMAIL" "noreply@taxpoynt.com"
set_env_var "EMAILS_FROM_NAME" "TaxPoynt eInvoice"

echo "✅ Environment setup completed!"
echo "⚠️  Please review and update the .env file with your specific values."
