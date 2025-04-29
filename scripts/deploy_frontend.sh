#!/bin/bash

# Exit on error
set -e

echo "🚀 Deploying frontend to Vercel..."

# Check if Vercel CLI is installed
if ! command -v vercel &> /dev/null; then
    echo "❌ Vercel CLI is not installed. Please install it first."
    exit 1
fi

# Navigate to frontend directory
cd frontend

# Login to Vercel if not already logged in
if ! vercel whoami &> /dev/null; then
    echo "🔑 Logging in to Vercel..."
    vercel login
fi

# Deploy to Vercel
echo "📦 Deploying to Vercel..."
vercel --prod

echo "✅ Frontend deployment completed successfully!"
