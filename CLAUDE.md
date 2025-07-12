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

## Performance Optimization Considerations

### What needs attention:
- Image optimization (Next.js Image component usage)
- Bundle size analysis for Framer Motion
- Core Web Vitals measurement and monitoring
- Code splitting for landing components

## Development Best Practices

### Python and Environment Management
- Always use python3: "Let me try with python3 instead,"
- Always use the virtual environment to run the commands: "I can see there's a virtual environment with alembic. Let me use the virtual environment to run the commands"

## Execution Principles
- Always think and analyze before execution.

## Service Restructuring Plan

### firs_si (System Integrator Services)
- irn_service.py - IRN & QR Code generation
- certificate_service.py - Digital certificate management
- odoo_service.py & ERP integration services - ERP system integration
- invoice_validation_service.py - Schema conformity validation
- Authentication services for invoice origin verification

### firs_app (Access Point Provider Services)
- firs_transmission_service.py - Secure transmission protocols
- validation_rule_service.py - Data validation before submission
- cryptographic_stamping_service.py - Authentication Seal management
- encryption_service.py - Cryptographic stamp validation
- TLS/OAuth 2.0 secure communication services

### firs_core (Shared FIRS Services)
- firs_service.py - Core FIRS API client
- audit_service.py - Audit logging
- Common models and utilities
- Configuration management

### firs_hybrid (SI+APP Hybrid Services)
- Cross-role validation services
- Unified compliance monitoring
- Shared workflow orchestration

### Key Corrections Made

#### SI Focus Areas (Backend processing):
- ERP integration and data extraction
- Certificate lifecycle management
- IRN generation and QR code creation
- Schema validation and conformity checks

#### APP Focus Areas (Secure transmission):
- Transmission security protocols
- Pre-submission data validation
- Authentication seal management
- Cryptographic operations for secure communication

## Import Guidelines (CRITICAL)

### **FIRS Service Migration Status**: ✅ COMPLETED
- **Total Services Migrated**: 22 services across 4 packages
- **Import Structure**: All core services now use firs_* package structure
- **Migration Document**: See `backend/IMPORT_MIGRATION_STRATEGY.md` for detailed plan

### **Mandatory Import Rules for All Development**
```python
# ✅ CORRECT - Use new structure
from app.services.firs_si.odoo_service import OdooService
from app.services.firs_app.transmission_service import TransmissionService
from app.services.firs_core.audit_service import AuditService
from app.services.firs_hybrid.certificate_manager import CertificateManager

# ❌ AVOID - Old structure (will be deprecated)
from app.services.odoo_service import OdooService
from app.services.transmission_service import TransmissionService
```

### **Package Structure Rules**
- **firs_si**: Backend processing, ERP integration, IRN generation, certificate management
- **firs_app**: Secure transmission, validation, crypto operations, document signing
- **firs_core**: Shared services, audit, configuration, core FIRS API client
- **firs_hybrid**: Cross-role validation, unified monitoring, shared workflows

### **Development Process Requirements**
- All new code MUST use firs_* package structure
- When modifying existing files, update imports to new structure
- Before adding new services, check if similar exists in packages
- Run import validation before committing (when available)

### **Import Migration Priority**
1. ✅ **Priority 1 (COMPLETED)**: Core services, API routes, main routers
2. 🔄 **Priority 2 (IN PROGRESS)**: Test files, workers, authentication modules
3. ⏳ **Priority 3 (PENDING)**: Utility scripts, development tools, legacy files

### **Ongoing Maintenance**
- Fix 5-10 import issues per development session
- Weekly import health checks
- Archive redundant files after migration
- Update documentation with any structural changes

## Import Migration Memory (CRITICAL)
- **Status**: Major import migration completed - 22 services restructured
- **Critical Rule**: Always use firs_* package structure for imports
- **Remaining Work**: ~80 files with minor import issues (tests, utilities)
- **Strategy**: Incremental cleanup, fix 5-10 issues per session
- **Tools Needed**: import_health_check.py script for validation
- **Migration Document**: `backend/IMPORT_MIGRATION_STRATEGY.md` contains full strategy