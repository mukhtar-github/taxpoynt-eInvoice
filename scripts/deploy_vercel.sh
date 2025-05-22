#!/bin/bash
# Vercel Deployment Script for TaxPoynt eInvoice Frontend
# This script assists in deploying the frontend to Vercel

# Colors for better readability
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${YELLOW}===== TaxPoynt eInvoice Vercel Deployment =====${NC}"
echo "This script will help you deploy the frontend to Vercel"

# Check if Vercel CLI is installed
if ! command -v vercel &> /dev/null; then
    echo -e "${RED}Vercel CLI not found!${NC}"
    echo "Installing Vercel CLI..."
    npm install -g vercel
    
    if [ $? -ne 0 ]; then
        echo -e "${RED}Failed to install Vercel CLI. Please install it manually:${NC}"
        echo "npm install -g vercel"
        exit 1
    fi
fi

# Navigate to frontend directory
cd "$(dirname "$0")/../frontend" || exit

# Login to Vercel if not already logged in
vercel whoami &> /dev/null
if [ $? -ne 0 ]; then
    echo -e "${YELLOW}Logging in to Vercel...${NC}"
    vercel login
    
    if [ $? -ne 0 ]; then
        echo -e "${RED}Failed to login to Vercel. Please try again.${NC}"
        exit 1
    fi
fi

# Check if project is already linked
vercel project ls &> /dev/null
if [ $? -ne 0 ]; then
    echo -e "${YELLOW}No Vercel project linked. Let's create or link one.${NC}"
    vercel link
    
    if [ $? -ne 0 ]; then
        echo -e "${RED}Failed to link Vercel project. Please try again.${NC}"
        exit 1
    fi
fi

# Environment variables setup
echo -e "${YELLOW}Do you want to set up environment variables now?${NC}"
echo "1. Yes, help me set up environment variables"
echo "2. No, I'll set them up manually in the Vercel dashboard"
read -p "Enter your choice (1/2): " env_choice

if [ "$env_choice" == "1" ]; then
    echo -e "${YELLOW}Setting up environment variables...${NC}"
    
    # Backend API URL
    read -p "Enter your backend API URL (e.g., https://your-railway-backend.up.railway.app/api/v1): " api_url
    vercel env add NEXT_PUBLIC_API_URL "$api_url"
    
    # Auth domain
    read -p "Enter your frontend domain (e.g., taxpoynt-einvoice.vercel.app): " auth_domain
    vercel env add NEXT_PUBLIC_AUTH_DOMAIN "$auth_domain"
    
    # Storage prefix
    vercel env add NEXT_PUBLIC_AUTH_STORAGE_PREFIX "taxpoynt_einvoice"
    
    # Default theme
    vercel env add NEXT_PUBLIC_DEFAULT_THEME "light"
    
    # FIRS API sandbox mode
    vercel env add NEXT_PUBLIC_FIRS_API_SANDBOX_MODE "true"
    
    # Default time range
    vercel env add NEXT_PUBLIC_DEFAULT_TIME_RANGE "24h"
    
    echo -e "${GREEN}Environment variables set!${NC}"
else
    echo -e "${YELLOW}Please set up environment variables in the Vercel dashboard.${NC}"
    echo "See frontend/vercel.env.template for the list of required variables."
fi

# Deploy options
echo -e "${YELLOW}Ready to deploy to Vercel!${NC}"
echo "Select your deployment environment:"
echo "1. Production"
echo "2. Preview (Staging)"
read -p "Enter your choice (1/2): " deploy_choice

if [ "$deploy_choice" == "1" ]; then
    echo -e "${YELLOW}Deploying to production...${NC}"
    vercel --prod
else
    echo -e "${YELLOW}Deploying to preview environment...${NC}"
    vercel
fi

if [ $? -eq 0 ]; then
    echo -e "${GREEN}Deployment successful!${NC}"
    echo -e "${YELLOW}Important next steps:${NC}"
    echo "1. Ensure your Railway backend has ALLOWED_ORIGINS set to your Vercel domain"
    echo "2. Test Odoo integration functionality on the deployed site"
    echo "3. Verify FIRS API connectivity in both sandbox and production modes"
    echo "4. Check the submission dashboard for proper data loading"
else
    echo -e "${RED}Deployment failed. Please check the error messages.${NC}"
fi

echo -e "${GREEN}===== Deployment script completed! =====${NC}"
