# TaxPoynt eInvoice Project Analysis

## Project Overview
TaxPoynt eInvoice is a middleware service designed to facilitate integration between financial software systems and the Federal Inland Revenue Service (FIRS) for electronic invoicing in Nigeria. The system acts as an intermediary that handles the generation, validation, and management of electronic invoices and their corresponding Invoice Reference Numbers (IRNs).

## Technical Stack
- **Backend**: FastAPI (Python) with SQLAlchemy ORM
- **Database**: PostgreSQL (with SQLite used in development)
- **Authentication**: JWT-based authentication system
- **Security**: TLS encryption, API key authentication, and rate limiting

## Core Components

### 1. Authentication System
- Role-based access control with user roles: Owner, Admin, Member, and SI_User (System Integrator)
- Email verification workflow
- Password reset functionality
- Organization-based user management

### 2. IRN (Invoice Reference Number) System
- Core functionality for generating, validating, and managing electronic invoice reference numbers
- Support for different statuses: Unused, Active, Expired, Revoked, and Invalid
- Tracking of invoice data linked to IRNs
- Validation records for tracking IRN verification

### 3. Integration System
- Support for multiple integrations with financial software
- API credential management for third-party systems
- Certificate management for secure communications

### 4. API Endpoints
The application exposes several API endpoints grouped into categories:
- Authentication
- API Keys management
- IRN operations (generation, validation)
- FIRS interactions
- Integrations management
- Crypto operations for security
- Dashboard metrics

### 5. Security Features
- Strong TLS configuration (minimum TLS 1.2)
- Encryption utilities for securing sensitive data
- API rate limiting to prevent abuse
- Comprehensive error handling

## Project Structure
The project follows a well-organized structure with clear separation of concerns:
- API routes and controllers
- Database models
- Service layers
- Utility functions
- Authentication middleware
- Schema definitions

## Current Status
Based on the README, the project appears to be in a Proof of Concept (POC) phase with basic functionality implemented, including:
- User registration and login
- JWT token generation and validation
- Role-based access control

## Integration Components
The system seems designed to integrate with various financial software systems, with specific adaptations for Odoo (as seen in the IRN model with Odoo-specific fields).
