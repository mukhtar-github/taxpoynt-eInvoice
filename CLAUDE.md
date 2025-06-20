# TaxPoynt E-Invoice Platform - Development Guide

## Project Overview

TaxPoynt eInvoice is a comprehensive middleware service that facilitates integration between financial software (ERP, CRM, POS) and FIRS (Federal Inland Revenue Service) for electronic invoicing. The platform serves as an Access Point Provider (APP) for Nigerian e-invoicing compliance.

## Architecture

### High-Level Architecture
- **Backend**: FastAPI-based Python application with PostgreSQL database
- **Frontend**: Next.js React application with TypeScript
- **Integration Layer**: Pluggable connector system for ERP/CRM/POS systems
- **Authentication**: JWT-based with role-based access control (RBAC)
- **Deployment**: Railway (backend) + Vercel (frontend)

### Core Components
- **Authentication & Authorization**: Multi-tenant RBAC system
- **Integration Framework**: Base connector classes for ERP/CRM/POS
- **Invoice Processing**: IRN generation, validation, and FIRS submission
- **Cryptographic Services**: Digital signing and certificate management
- **Transmission System**: Secure transmission with retry mechanisms
- **Monitoring & Analytics**: Real-time dashboard and metrics

## Development Setup

### Prerequisites
- Python 3.8+
- Node.js 18+
- PostgreSQL (or SQLite for development)
- Redis (optional, for caching)

### Backend Setup

```bash
cd backend

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Set up environment variables
cp railway.env.template .env
# Edit .env with your configuration

# Initialize database
python scripts/init_db.py

# Run database migrations
alembic upgrade head

# Start development server
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
# Alternative: bash run.sh
```

### Frontend Setup

```bash
cd frontend

# Install dependencies
npm install --legacy-peer-deps
# Alternative: npm install

# Set up environment variables
cp vercel.env.template .env.local
# Edit .env.local with your configuration

# Start development server
npm run dev

# Build for production
npm run build
```

### Environment Setup Script
```bash
# Automated environment setup
./scripts/setup_env.sh
```

## Development Commands

### Backend Commands

#### Server Management
```bash
# Start development server
cd backend && uvicorn app.main:app --reload

# Start with custom configuration
cd backend && python start_backend.py

# Using the provided script
cd backend && bash run.sh
```

#### Database Management
```bash
# Initialize database
cd backend && python scripts/init_db.py

# Run migrations
cd backend && alembic upgrade head

# Create new migration
cd backend && alembic revision --autogenerate -m "description"

# Check migration status
cd backend && python scripts/check_migrations.py
```

#### Testing
```bash
# Run all tests
cd backend && pytest

# Run specific test file
cd backend && pytest tests/api/test_auth_endpoints.py -v

# Run tests with coverage
cd backend && pytest --cov=app tests/

# Run integration tests
cd backend && bash run_integration_tests.sh

# Using the test script
cd backend && bash run_tests.sh
```

#### Code Quality
```bash
# Format code (use your preferred formatter)
cd backend && black app/
cd backend && isort app/

# Type checking (if mypy is installed)
cd backend && mypy app/
```

### Frontend Commands

#### Development
```bash
# Start development server
cd frontend && npm run dev

# Build for production  
cd frontend && npm run build

# Start production server
cd frontend && npm start

# Lint code
cd frontend && npm run lint
```

#### Testing
```bash
# Run unit tests
cd frontend && npm test

# Run tests in watch mode
cd frontend && npm run test:watch

# Run E2E tests with Cypress
cd frontend && npm run cypress:open
cd frontend && npm run cypress:run

# Run all E2E tests
cd frontend && npm run test:e2e
```

### Deployment Commands

#### Development Deployment
```bash
# Full development deployment
./scripts/deploy_dev.sh

# Simple development deployment
./scripts/deploy_dev_simple.sh
```

#### Production Deployment
```bash
# Deploy backend to Railway
./scripts/deploy_railway.sh

# Deploy frontend to Vercel
./scripts/deploy_vercel.sh

# Deploy backend only
./scripts/deploy_backend.sh

# Deploy frontend only
./scripts/deploy_frontend.sh
```

## Project Structure

### Backend Structure (`/backend`)
```
app/
├── main.py                 # FastAPI application entry point
├── core/
│   ├── config.py          # Configuration management
│   ├── security.py        # Security utilities
│   └── permissions.py     # Permission definitions
├── models/                 # SQLAlchemy models
│   ├── user.py
│   ├── organization.py
│   ├── integration.py
│   └── ...
├── routes/                 # API route handlers
│   ├── auth.py
│   ├── organization.py
│   ├── integrations.py
│   └── ...
├── services/              # Business logic services
│   ├── auth_service.py
│   ├── integration_service.py
│   ├── firs_service.py
│   └── ...
├── integrations/          # Integration framework
│   ├── base/              # Base connector classes
│   ├── crm/               # CRM integrations (HubSpot, etc.)
│   ├── erp/               # ERP integrations (Odoo, etc.)
│   └── pos/               # POS integrations
├── utils/                 # Utility functions
├── tests/                 # Test files
└── alembic/              # Database migrations
```

### Frontend Structure (`/frontend`)
```
pages/                     # Next.js pages
├── _app.tsx              # App wrapper
├── index.tsx             # Home page
├── auth/                 # Authentication pages
├── dashboard/            # Dashboard pages
└── ...
components/               # React components
├── ui/                   # Base UI components
├── dashboard/            # Dashboard components
├── integrations/         # Integration components
└── platform/            # Platform features
services/                 # API services
utils/                    # Utility functions
types/                    # TypeScript type definitions
styles/                   # CSS styles
```

## Key Features & Integration Points

### Authentication System
- **JWT Token Authentication**: Stateless with refresh tokens
- **Role-Based Access Control**: OWNER, ADMIN, MEMBER, SI_USER roles
- **Multi-tenant Architecture**: Organization-based data isolation
- **API Key Authentication**: For system integrations

### Integration Framework
- **Base Connector Pattern**: Standardized integration interface
- **Supported Systems**:
  - **ERP**: Odoo (implemented)
  - **CRM**: HubSpot (in development)
  - **POS**: Square, Toast (planned)
- **OAuth2 Support**: For third-party authentication
- **Webhook Support**: Real-time data synchronization

### FIRS Integration
- **IRN Generation**: Automatic invoice reference number generation
- **Digital Signing**: Cryptographic signing with certificates
- **Batch Processing**: Bulk invoice submission
- **Retry Mechanism**: Automatic retry for failed submissions
- **Sandbox Support**: Testing environment integration

### Security Features
- **TLS 1.2+ Enforcement**: Secure communications
- **Data Encryption**: At-rest and in-transit encryption
- **Certificate Management**: Digital certificate lifecycle
- **Rate Limiting**: API protection against abuse
- **CORS Configuration**: Cross-origin resource sharing

## Database Schema

### Core Tables
- `users` - User accounts and authentication
- `organizations` - Business entities/tenants
- `organization_users` - User-organization relationships with roles
- `integrations` - ERP/CRM/POS connection configurations
- `irn_records` - Invoice reference number records
- `submissions` - FIRS submission tracking
- `certificates` - Digital certificates for signing
- `transmissions` - Secure data transmission logs

### Integration Tables
- `crm_connections` - CRM system connections
- `pos_connections` - POS system connections
- `api_credentials` - Third-party API credentials
- `integration_history` - Configuration change tracking

## Environment Variables

### Backend Environment (.env)
```bash
# Application
APP_ENV=development
SECRET_KEY=your_secret_key
API_V1_STR=/api/v1

# Database
DATABASE_URL=postgresql://user:pass@host:port/db
# Or for development: sqlite:///./dev.db

# FIRS API
FIRS_SANDBOX_API_URL=https://eivc-k6z6d.ondigitalocean.app
FIRS_SANDBOX_API_KEY=your_sandbox_key
FIRS_SANDBOX_API_SECRET=your_sandbox_secret
FIRS_USE_SANDBOX=true

# Encryption
ENCRYPTION_KEY=your_32_char_encryption_key

# Redis (optional)
REDIS_URL=redis://localhost:6379
```

### Frontend Environment (.env.local)
```bash
NEXT_PUBLIC_API_URL=http://localhost:8000/api/v1
NEXT_PUBLIC_AUTH_DOMAIN=localhost
NEXT_PUBLIC_FIRS_API_SANDBOX_MODE=true
```

## Testing Strategy

### Backend Testing (798 test files)
- **Unit Tests**: Individual component testing
- **Integration Tests**: API endpoint testing
- **Service Tests**: Business logic testing
- **Authentication Tests**: Security feature testing
- **FIRS Integration Tests**: External API testing

### Frontend Testing
- **Component Tests**: React component testing with Jest
- **E2E Tests**: Full workflow testing with Cypress
- **Integration Tests**: API integration testing

### Test Execution
```bash
# Backend: Run all tests
cd backend && pytest

# Backend: Run specific test category
cd backend && pytest tests/api/ -v
cd backend && pytest tests/services/ -v

# Frontend: Run all tests
cd frontend && npm test

# E2E: Run Cypress tests
cd frontend && npm run cypress:run
```

## Deployment Architecture

### Production Setup
- **Backend**: Railway hosting with PostgreSQL
- **Frontend**: Vercel hosting with Next.js
- **Domain**: taxpoynt.com with SSL/TLS
- **Monitoring**: Built-in health checks and metrics

### Development Setup
- **Backend**: Local uvicorn server (port 8000)
- **Frontend**: Local Next.js dev server (port 3000)
- **Database**: SQLite or PostgreSQL
- **FIRS**: Sandbox environment

## API Documentation

### Access Points
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc
- **Health Check**: http://localhost:8000/health

### Key API Endpoints
- `POST /api/v1/auth/login` - User authentication
- `GET /api/v1/organizations` - Organization management
- `POST /api/v1/integrations` - Create integrations
- `POST /api/v1/irn/generate` - Generate IRN
- `POST /api/v1/firs-submission/submit` - Submit to FIRS

## Troubleshooting

### Common Issues

#### Backend Issues
1. **Database Connection**: Check DATABASE_URL and database status
2. **Migration Errors**: Run `alembic upgrade head`
3. **Import Errors**: Ensure PYTHONPATH includes backend directory
4. **FIRS API Errors**: Verify sandbox credentials and network access

#### Frontend Issues
1. **API Connection**: Check NEXT_PUBLIC_API_URL configuration
2. **Build Errors**: Run `npm install --legacy-peer-deps`
3. **Authentication**: Verify JWT token handling
4. **CORS Issues**: Check backend CORS configuration

### Debug Mode
```bash
# Backend debug mode
cd backend && LOG_LEVEL=DEBUG uvicorn app.main:app --reload

# Frontend debug mode  
cd frontend && DEBUG=true npm run dev
```

## Contributing

### Development Workflow
1. Create feature branch from `master`
2. Implement changes with tests
3. Run full test suite
4. Create pull request
5. Deploy to staging for testing
6. Merge to master after approval

### Code Standards
- **Backend**: Follow PEP 8, use type hints
- **Frontend**: Follow ESLint rules, use TypeScript
- **Testing**: Maintain >85% code coverage
- **Documentation**: Update API docs and README files

## Support & Resources

### Documentation
- **Architecture Docs**: `/docs` directory
- **API Docs**: Available at `/docs` endpoint
- **Integration Guides**: Individual integration documentation
- **Testing Guide**: `TESTING.md`

### External Resources
- **FIRS API Documentation**: Official FIRS e-invoicing docs
- **FastAPI Docs**: https://fastapi.tiangolo.com/
- **Next.js Docs**: https://nextjs.org/docs
- **SQLAlchemy Docs**: https://docs.sqlalchemy.org/

This comprehensive guide covers all aspects of the TaxPoynt E-Invoice platform development. Refer to specific documentation files in the `/docs` directory for detailed implementation guides.