#!/bin/bash
# Simplified development environment deployment script for TaxPoynt eInvoice
# This script deploys the application to a development environment without Docker

set -e  # Exit immediately if a command exits with a non-zero status

# Configuration
APP_NAME="taxpoynt-einvoice"
DEV_ENV_NAME="development"
BACKEND_DIR="backend"
FRONTEND_DIR="frontend"
DEPLOY_DIR="deploy"

# Colors for better visibility
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${GREEN}=== TaxPoynt eInvoice Development Deployment (Simple) ===${NC}"
echo -e "${YELLOW}Starting deployment to $DEV_ENV_NAME environment...${NC}"

# Create deployment directory if it doesn't exist
mkdir -p $DEPLOY_DIR

# Function to check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Check for required tools
echo -e "${YELLOW}Checking required tools...${NC}"
if ! command_exists python; then
    echo -e "${RED}Error: Python is not installed. Please install Python first.${NC}"
    exit 1
fi

# Back up database if it exists
echo -e "${YELLOW}Backing up database...${NC}"
if [ -f "$BACKEND_DIR/dev.db" ]; then
    cp "$BACKEND_DIR/dev.db" "$DEPLOY_DIR/dev.db.backup.$(date +%Y%m%d%H%M%S)"
    echo -e "${GREEN}Database backup created.${NC}"
else
    echo -e "${YELLOW}No database found to backup.${NC}"
fi

# Create or update .env file for development
echo -e "${YELLOW}Setting up environment variables...${NC}"
if [ ! -f "$BACKEND_DIR/.env.development" ]; then
    cat > "$BACKEND_DIR/.env.development" << EOF
# TaxPoynt eInvoice Development Environment Configuration
APP_ENV=development
DEBUG=true
SECRET_KEY=dev-secret-key-replace-in-production-environment
API_PREFIX=/api/v1
ALLOWED_ORIGINS=http://localhost:3000

# Database - Using SQLite for development
DATABASE_URL=sqlite:///dev.db

# FIRS API (Sandbox)
FIRS_API_URL=https://api.sandbox.firs.gov.ng
FIRS_CLIENT_ID=dev-client-id
FIRS_CLIENT_SECRET=dev-client-secret

# Encryption
ENCRYPTION_KEY=dev-encryption-key-32-chars-minimum
EOF
    echo -e "${GREEN}Created development environment file.${NC}"
else
    echo -e "${GREEN}Using existing development environment file.${NC}"
fi

# Deploy backend
echo -e "${YELLOW}Deploying backend...${NC}"
cd $BACKEND_DIR

# Create Python virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    echo -e "${YELLOW}Creating Python virtual environment...${NC}"
    python -m venv venv
fi

# Activate virtual environment and install dependencies
echo -e "${YELLOW}Installing backend dependencies...${NC}"
source venv/bin/activate
pip install -r requirements.txt

# Run database migrations
echo -e "${YELLOW}Running database migrations...${NC}"
export ENV_FILE=.env.development
alembic upgrade head

cd ..

# Deploy frontend (if npm is available)
if command_exists npm; then
    echo -e "${YELLOW}Deploying frontend...${NC}"
    cd $FRONTEND_DIR
    
    # Create or update .env.local file for development
    if [ ! -f ".env.local" ]; then
        cat > ".env.local" << EOF
# Frontend environment variables
NEXT_PUBLIC_API_URL=http://localhost:8000/api/v1
NEXT_PUBLIC_AUTH_DOMAIN=localhost
NEXT_PUBLIC_AUTH_STORAGE_PREFIX=taxpoynt_einvoice
NEXT_PUBLIC_ENABLE_TWO_FACTOR_AUTH=false
EOF
        echo -e "${GREEN}Created frontend environment file.${NC}"
    else
        echo -e "${GREEN}Using existing frontend environment file.${NC}"
    fi
    
    # Install dependencies and build
    echo -e "${YELLOW}Installing frontend dependencies...${NC}"
    npm install
    
    echo -e "${YELLOW}Building frontend...${NC}"
    npm run build
    
    cd ..
else
    echo -e "${YELLOW}Skipping frontend deployment (npm not found).${NC}"
fi

# Create deployment summary
echo -e "${YELLOW}Creating deployment summary...${NC}"
TIMESTAMP=$(date +"%Y-%m-%d %H:%M:%S")
cat > "$DEPLOY_DIR/deployment_summary.md" << EOF
# TaxPoynt eInvoice Deployment Summary

## Environment: $DEV_ENV_NAME
## Timestamp: $TIMESTAMP

### Backend
- Status: Deployed
- Environment: SQLite Development
- Configuration: .env.development
- Migrations: Applied

### Frontend
- Status: $(command_exists npm && echo "Deployed" || echo "Skipped (npm not found)")

### Week 2 POC Phase Implementation
- ✅ Integrated authentication with basic integration configuration
- ✅ End-to-end flow for simple integration setup implemented
- ✅ Deployed to development environment
- ✅ Created basic test cases for FIRS API interactions

### Next Steps
1. Start the backend server: \`cd backend && source venv/bin/activate && uvicorn app.main:app --reload\`
2. Start the frontend development server: \`cd frontend && npm run dev\`
3. Access the API at: http://localhost:8000/api/v1
4. Access the frontend at: http://localhost:3000
EOF

echo -e "${GREEN}=== Deployment completed successfully ===${NC}"
echo -e "${GREEN}See deployment summary at: $DEPLOY_DIR/deployment_summary.md${NC}"
echo -e "${YELLOW}To start the application:${NC}"
echo -e "  Backend: ${GREEN}cd backend && source venv/bin/activate && uvicorn app.main:app --reload${NC}"
echo -e "  Frontend: ${GREEN}cd frontend && npm run dev${NC}"

# Start the backend server for testing
cd $BACKEND_DIR
source venv/bin/activate
echo -e "${GREEN}Starting backend server for testing...${NC}"
echo -e "${YELLOW}Press Ctrl+C to stop the server when finished testing.${NC}"
uvicorn app.main:app --reload
