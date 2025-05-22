#!/bin/bash
# Railway Deployment Script for TaxPoynt eInvoice Backend
# This script assists in deploying the backend to Railway

# Colors for better readability
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${YELLOW}===== TaxPoynt eInvoice Railway Deployment =====${NC}"
echo "This script will help you deploy the backend to Railway"

# Check if Railway CLI is installed
if ! command -v railway &> /dev/null; then
    echo -e "${RED}Railway CLI not found!${NC}"
    echo "Installing Railway CLI..."
    npm install -g @railway/cli
    
    if [ $? -ne 0 ]; then
        echo -e "${RED}Failed to install Railway CLI. Please install it manually:${NC}"
        echo "npm install -g @railway/cli"
        exit 1
    fi
fi

# Login to Railway if not already logged in
railway whoami &> /dev/null
if [ $? -ne 0 ]; then
    echo -e "${YELLOW}Logging in to Railway...${NC}"
    railway login
    
    if [ $? -ne 0 ]; then
        echo -e "${RED}Failed to login to Railway. Please try again.${NC}"
        exit 1
    fi
fi

# Navigate to backend directory
cd "$(dirname "$0")/../backend" || exit

# Check if a Railway project is already linked
railway project &> /dev/null
if [ $? -ne 0 ]; then
    echo -e "${YELLOW}No Railway project linked. Let's create or link one.${NC}"
    echo "Do you want to create a new project or link an existing one?"
    echo "1. Create new project"
    echo "2. Link existing project"
    read -p "Enter your choice (1/2): " project_choice
    
    if [ "$project_choice" == "1" ]; then
        echo -e "${YELLOW}Creating new Railway project...${NC}"
        railway project create
    else
        echo -e "${YELLOW}Linking existing Railway project...${NC}"
        railway link
    fi
fi

# Check if we need to set up the PostgreSQL plugin
echo -e "${YELLOW}Checking for PostgreSQL plugin...${NC}"
railway variables get DATABASE_URL &> /dev/null
if [ $? -ne 0 ]; then
    echo -e "${YELLOW}Setting up PostgreSQL plugin...${NC}"
    echo "Please go to the Railway dashboard and add the PostgreSQL plugin"
    echo "After adding the plugin, press Enter to continue..."
    read -p ""
fi

# Check if we need to set up the Redis plugin
echo -e "${YELLOW}Checking for Redis plugin...${NC}"
railway variables get REDIS_URL &> /dev/null
if [ $? -ne 0 ]; then
    echo -e "${YELLOW}Setting up Redis plugin...${NC}"
    echo "Please go to the Railway dashboard and add the Redis plugin"
    echo "After adding the plugin, press Enter to continue..."
    read -p ""
fi

# Set up environment variables
echo -e "${YELLOW}Setting up environment variables...${NC}"
echo "Would you like to set up environment variables now?"
echo "1. Yes, help me set up environment variables"
echo "2. No, I'll set them up manually in the Railway dashboard"
read -p "Enter your choice (1/2): " env_choice

if [ "$env_choice" == "1" ]; then
    echo -e "${YELLOW}Setting up essential environment variables...${NC}"
    
    # Generate secure random strings for secrets
    JWT_SECRET=$(openssl rand -hex 32)
    ENCRYPTION_KEY=$(openssl rand -hex 32)
    
    # Set essential environment variables
    railway variables set APP_ENV=production
    railway variables set DEBUG=false
    railway variables set API_V1_STR=/api/v1
    railway variables set JWT_SECRET="$JWT_SECRET"
    railway variables set JWT_ALGORITHM=HS256
    railway variables set JWT_ACCESS_TOKEN_EXPIRE_MINUTES=30
    railway variables set ENCRYPTION_KEY="$ENCRYPTION_KEY"
    railway variables set LOG_LEVEL=INFO
    
    # Odoo integration settings
    railway variables set ODOO_DEFAULT_TIMEOUT=30
    railway variables set ODOO_CONNECTION_POOL_SIZE=5
    
    echo -e "${GREEN}Essential environment variables set!${NC}"
    echo -e "${YELLOW}NOTE: You still need to set the following variables manually in the Railway dashboard:${NC}"
    echo "- FIRS_API_URL"
    echo "- FIRS_API_KEY"
    echo "- FIRS_API_SECRET"
    echo "- ALLOWED_ORIGINS (set to your frontend URL)"
else
    echo -e "${YELLOW}Please set up all required environment variables in the Railway dashboard.${NC}"
    echo "See railway.env.template for the list of required variables."
fi

# Deploy to Railway
echo -e "${YELLOW}Ready to deploy to Railway!${NC}"
echo "Would you like to deploy now?"
echo "1. Yes, deploy now"
echo "2. No, I'll deploy later"
read -p "Enter your choice (1/2): " deploy_choice

if [ "$deploy_choice" == "1" ]; then
    echo -e "${YELLOW}Deploying to Railway...${NC}"
    railway up
    
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}Deployment successful!${NC}"
        
        # Run migrations
        echo -e "${YELLOW}Running database migrations...${NC}"
        railway run alembic upgrade head
        
        if [ $? -eq 0 ]; then
            echo -e "${GREEN}Migrations successful!${NC}"
        else
            echo -e "${RED}Failed to run migrations. Please run them manually:${NC}"
            echo "railway run alembic upgrade head"
        fi
    else
        echo -e "${RED}Deployment failed. Please check the logs.${NC}"
    fi
else
    echo -e "${YELLOW}You can deploy later using:${NC}"
    echo "railway up"
    echo -e "${YELLOW}Don't forget to run migrations after deployment:${NC}"
    echo "railway run alembic upgrade head"
fi

echo -e "${GREEN}===== Deployment script completed! =====${NC}"
echo "Visit the Railway dashboard to monitor your deployment and set any remaining environment variables."
echo "Your API will be available at the URL provided in the Railway dashboard."
