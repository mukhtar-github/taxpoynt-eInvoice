### Deployment & Environment Setup Guide
This guide ensures smooth setup and deployment, critical for a small team. It includes:
- **System Requirements**: Lists Node.js, Python, PostgreSQL, Redis, and Git, ensuring compatibility with the tech stack.
- **Local Development Setup**: Step-by-step instructions for cloning, installing dependencies, and running frontend and backend, with .env configuration examples, facilitating local testing.
- **.env Configuration**: Details variables like DATABASE_URL and REDIS_URL, ensuring secure and correct setup, aligning with security rules.
- **Deployment Instructions**: Covers deploying frontend on Vercel and backend on Railway, with plans for AWS scaling, reflecting the deployment strategy in the thinking trace.

## System Requirements

### Development Environment
- **Node.js**: v16.x or higher
- **Python**: 3.9 or higher
- **PostgreSQL**: 13.x or higher
- **Redis**: 6.x or higher
- **Git**: 2.x or higher
- **Docker** (optional): For containerized development
- **npm**: 8.x or higher or **yarn**: 1.22.x or higher
- **pip**: 21.x or higher
- **Poetry** (recommended): For Python dependency management

### Production Environment
- **Railway** (Initial Backend Deployment)
  - Standard plan or higher
  - PostgreSQL add-on
  - Redis add-on
- **Vercel** (Frontend Deployment)
  - Pro plan recommended for team development
- **AWS** (Future Deployment)
  - EC2 or ECS for containers
  - RDS for PostgreSQL
  - ElastiCache for Redis
  - S3 for static assets
  - CloudFront for CDN

## Local Development Setup

### 1. Backend Setup

```bash
# Clone the repository
git clone https://github.com/your-org/taxpoynt-einvoice.git
cd taxpoynt-einvoice/backend

# Set up Python virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
# OR with Poetry
poetry install

# Set up environment variables
cp .env.example .env
# Edit .env with your local configuration

# Initialize the database
alembic upgrade head

# Run development server
uvicorn app.main:app --reload
```

### 2. Frontend Setup

```bash
# Navigate to frontend directory
cd ../frontend

# Install dependencies
npm install
# OR
yarn install

# Set up environment variables
cp .env.example .env.local
# Edit .env.local with your local configuration

# Run development server
npm run dev
# OR
yarn dev
```

### 3. Database Setup

```bash
# Create PostgreSQL database
createdb taxpoynt_einvoice_dev

# For a clean reset (if needed)
dropdb taxpoynt_einvoice_dev && createdb taxpoynt_einvoice_dev

# Run migrations
cd ../backend
alembic upgrade head

# Seed initial data (if available)
python scripts/seed_data.py
```

## Environment Configuration

### Backend (.env) Configuration

```
# Application
APP_ENV=development
DEBUG=true
SECRET_KEY=your-secret-key-at-least-32-chars
API_PREFIX=/api/v1
ALLOWED_ORIGINS=http://localhost:3000

# Database
DATABASE_URL=postgresql://postgres:password@localhost:5432/taxpoynt_einvoice_dev
DATABASE_POOL_SIZE=20
DATABASE_MAX_OVERFLOW=10

# Redis
REDIS_URL=redis://localhost:6379/0

# JWT Authentication
JWT_SECRET=your-jwt-secret-at-least-32-chars
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=60
JWT_REFRESH_TOKEN_EXPIRE_DAYS=7

# Email
SMTP_HOST=smtp.example.com
SMTP_PORT=587
SMTP_USER=your-smtp-user
SMTP_PASSWORD=your-smtp-password
EMAIL_FROM=noreply@example.com

# FIRS API (use sandbox for development)
FIRS_API_URL=https://api.sandbox.firs.gov.ng
FIRS_API_KEY=your-sandbox-api-key
FIRS_CLIENT_ID=your-sandbox-client-id
FIRS_CLIENT_SECRET=your-sandbox-client-secret

# Encryption
ENCRYPTION_KEY=your-encryption-key-at-least-32-chars
```

### Frontend (.env.local) Configuration

```
# API Configuration
NEXT_PUBLIC_API_URL=http://localhost:8000/api/v1

# Authentication
NEXT_PUBLIC_AUTH_DOMAIN=localhost
NEXT_PUBLIC_AUTH_STORAGE_PREFIX=taxpoynt_einvoice

# Feature Flags
NEXT_PUBLIC_ENABLE_TWO_FACTOR_AUTH=false
NEXT_PUBLIC_ENABLE_SOCIAL_LOGIN=false

# Analytics (optional)
NEXT_PUBLIC_ANALYTICS_ID=

# UI Configuration
NEXT_PUBLIC_DEFAULT_THEME=light
```

## Feature-Specific Deployment Requirements

### 1. Authentication and Authorization

#### Required Services
- PostgreSQL database for user storage
- Redis for token blacklisting and rate limiting
- SMTP server for email verification and password reset

#### Environment Variables
- `JWT_SECRET`: Secret key for JWT signing
- `JWT_ACCESS_TOKEN_EXPIRE_MINUTES`: Access token lifetime
- `JWT_REFRESH_TOKEN_EXPIRE_DAYS`: Refresh token lifetime
- `SMTP_*`: SMTP server configuration for emails
- `REDIS_URL`: Redis connection for token management

#### Deployment Steps
1. Set up database tables for users and organizations
2. Configure JWT secret and token expiration times
3. Set up SMTP for email verification
4. Configure CORS settings for frontend domain
5. Test authentication flow end-to-end

### 2. Integration Configuration

#### Required Services
- PostgreSQL database for integration storage
- Redis for configuration caching (optional)

#### Environment Variables
- `ENCRYPTION_KEY`: For encrypting sensitive configuration data
- `FIRS_API_URL`: FIRS API endpoint for integration testing

#### Deployment Steps
1. Set up database tables for clients and integrations
2. Configure encryption for sensitive configuration data
3. Deploy templates for common integration patterns
4. Test connection to FIRS sandbox environment

### 3. IRN Generation

#### Required Services
- PostgreSQL database for IRN storage
- Redis for IRN caching and rate limiting

#### Environment Variables
- `FIRS_API_*`: FIRS API credentials for IRN generation
- `IRN_CACHE_TTL`: Time-to-live for cached IRNs (seconds)
- `IRN_BATCH_SIZE`: Maximum IRNs per batch request

#### Deployment Steps
1. Set up database tables for IRN records
2. Configure Redis for IRN caching
3. Set up connection to FIRS IRN generation API
4. Configure rate limiting for IRN requests
5. Test IRN generation and validation

### 4. Invoice Validation

#### Required Services
- PostgreSQL database for validation rules and results

#### Environment Variables
- `VALIDATION_RULE_PATH`: Path to validation rule definitions
- `FIRS_SCHEMA_VERSION`: FIRS schema version to validate against

#### Deployment Steps
1. Set up database tables for validation rules and records
2. Deploy validation rule definitions
3. Configure validation pipeline
4. Test validation against sample invoices

### 5. Data Encryption

#### Required Services
- Key management system (KMS) for production

#### Environment Variables
- `ENCRYPTION_KEY`: Master encryption key
- `KEY_ROTATION_INTERVAL_DAYS`: Interval for key rotation

#### Deployment Steps
1. Generate secure encryption keys
2. Configure field-level encryption
3. Set up secure key storage
4. Test encryption/decryption process

### 6. Monitoring Dashboard

#### Required Services
- Time-series database for metrics (optional)
- WebSocket server for real-time updates

#### Environment Variables
- `METRICS_RETENTION_DAYS`: How long to keep detailed metrics
- `WEBSOCKET_MAX_CONNECTIONS`: Limit for concurrent dashboard connections

#### Deployment Steps
1. Deploy WebSocket server for real-time updates
2. Configure metrics collection
3. Set up dashboard components
4. Test dashboard with sample data

## Deployment Process

### Railway Deployment (Backend)

1. **Connect Repository**:
   ```bash
   # Install Railway CLI
   npm install -g @railway/cli
   
   # Login to Railway
   railway login
   
   # Link project
   railway link
   ```

2. **Configure Environment**:
   - Add all required environment variables in Railway dashboard
   - Set up PostgreSQL and Redis plugins

3. **Deploy**:
   ```bash
   railway up
   ```

4. **Run Migrations**:
   ```bash
   railway run alembic upgrade head
   ```

### Vercel Deployment (Frontend)

1. **Connect Repository**:
   - Link GitHub repository in Vercel dashboard
   - Select frontend directory as root

2. **Configure Environment**:
   - Add all required environment variables in Vercel dashboard
   - Set build command: `npm run build` or `yarn build`
   - Set output directory: `out` or `.next`

3. **Deploy**:
   - Trigger deployment from dashboard or via git push

### Containerized Deployment (Future AWS)

1. **Build Docker Images**:
   ```bash
   # Backend
   docker build -t taxpoynt-einvoice-api ./backend
   
   # Frontend
   docker build -t taxpoynt-einvoice-frontend ./frontend
   ```

2. **Test Containers Locally**:
   ```bash
   docker-compose up
   ```

3. **Push to Container Registry**:
   ```bash
   # Tag images
   docker tag taxpoynt-einvoice-api:latest ${ECR_REPO}/taxpoynt-einvoice-api:latest
   docker tag taxpoynt-einvoice-frontend:latest ${ECR_REPO}/taxpoynt-einvoice-frontend:latest
   
   # Push images
   docker push ${ECR_REPO}/taxpoynt-einvoice-api:latest
   docker push ${ECR_REPO}/taxpoynt-einvoice-frontend:latest
   ```

4. **Deploy to ECS/EKS**:
   - Use AWS CLI or Terraform to deploy containers
   - Configure auto-scaling and load balancing

## Environment Promotion Process

1. **Development**:
   - Local development and testing
   - Automated tests on pull requests

2. **Staging**:
   - Automated deployment from main branch
   - Connected to FIRS sandbox environment
   - Used for integration testing
   - Data can be reset as needed

3. **Production**:
   - Manual promotion from staging
   - Connected to FIRS production API
   - Requires approval process
   - Contains real client data

## Monitoring and Logging

### Required Services
- CloudWatch or similar for logs aggregation
- Prometheus + Grafana for metrics (optional)
- Sentry for error tracking

### Setup Steps
1. Configure structured logging in application
2. Set up log aggregation service
3. Create dashboards for key metrics
4. Configure alerting for critical failures

## Backup and Recovery

### Database Backups
- Automated daily backups
- Point-in-time recovery enabled
- Test restoration process monthly

### Recovery Procedure
1. Identify backup to restore
2. Restore database from backup
3. Verify application functionality
4. Confirm data integrity