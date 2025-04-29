#!/bin/bash

# Exit on error
set -e

echo "🚀 Deploying backend to Railway..."

# Check if Railway CLI is installed
if ! command -v railway &> /dev/null; then
    echo "❌ Railway CLI is not installed. Please install it first."
    exit 1
fi

# Login to Railway if not already logged in
if ! railway whoami &> /dev/null; then
    echo "🔑 Logging in to Railway..."
    railway login
fi

# Link to the project if not already linked
if [ ! -f ".railway/config.json" ]; then
    echo "🔗 Linking to Railway project..."
    railway link
fi

# Run database migrations
echo "🔄 Running database migrations..."
railway run alembic upgrade head

# Deploy the application
echo "📦 Deploying application..."
railway up

echo "✅ Backend deployment completed successfully!"
