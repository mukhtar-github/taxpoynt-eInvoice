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