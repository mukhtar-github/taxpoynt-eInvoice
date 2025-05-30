# TaxPoynt eInvoice APP Implementation - Phase 1 Technical Specification

## 1. Overview

This document provides a detailed technical specification for implementing Phase 1 of the Access Point Provider (APP) functionality in the TaxPoynt eInvoice system. It builds upon the existing Systems Integration (SI) foundation and aligns with the APP Implementation Addendum.

## 2. Architecture Components

### 2.1 Certificate Management System

The foundation for certificate management is already in place with:
- `Certificate` and `CertificateRevocation` models in `models/certificate.py`
- `EncryptionKey` and `EncryptionConfig` models in `models/encryption.py`
- Certificate routes in `routes/certificates.py`

#### 2.1.1 Enhancements Needed

1. **Certificate Lifecycle Monitoring**
   - Implement a background task to check certificate expiration
   - Add notification service for certificate status changes
   - Create renewal workflow for expiring certificates

2. **Certificate Request Workflow**
   - Create certificate signing request (CSR) generation functionality
   - Implement secure storage for CSRs with proper encryption
   - Add status tracking for certificate requests

3. **UI Integration**
   - Replace the placeholder `CertificateManagementCard` with functional component
   - Implement certificate detail view with validity visualization
   - Add certificate request and renewal forms

### 2.2 Cryptographic Stamping

#### 2.2.1 Components to Implement

1. **CSID Generation Service**
   - Define CSID format based on FIRS requirements
   - Implement generation algorithm with proper entropy
   - Create storage and retrieval mechanisms

2. **Invoice Signing Service**
   - Enhance existing `sign_document` function in `certificates.py`
   - Implement FIRS-compliant signature format
   - Add performance optimizations for batch signing

3. **Signature Verification**
   - Extend the existing verification function
   - Add detailed validation reporting
   - Implement signature visualization for invoices

### 2.3 Secure Transmission

#### 2.3.1 Components to Implement

1. **Encrypted Payload Packaging**
   - Create service for encrypting invoice payloads
   - Implement secure key management for transmission
   - Add integrity verification mechanisms

2. **Transmission Monitoring**
   - Implement transmission status tracking
   - Create retry mechanisms with exponential backoff
   - Add audit logging for all transmission events

3. **Webhook Handlers**
   - Enhance existing webhook infrastructure for transmission events
   - Implement status update processing
   - Add notification service integration

## 3. Database Schema Extensions

### 3.1 New Tables

1. **certificate_requests**
   ```sql
   CREATE TABLE certificate_requests (
     id UUID PRIMARY KEY,
     organization_id UUID NOT NULL REFERENCES organizations(id),
     request_type VARCHAR(50) NOT NULL,
     csr_data TEXT,
     is_encrypted BOOLEAN DEFAULT TRUE,
     encryption_key_id VARCHAR(100) REFERENCES encryption_keys(id),
     status VARCHAR(50) NOT NULL DEFAULT 'pending',
     created_at TIMESTAMP NOT NULL DEFAULT NOW(),
     updated_at TIMESTAMP NOT NULL DEFAULT NOW(),
     created_by UUID REFERENCES users(id),
     request_metadata JSONB
   );
   ```

2. **transmission_records**
   ```sql
   CREATE TABLE transmission_records (
     id UUID PRIMARY KEY,
     organization_id UUID NOT NULL REFERENCES organizations(id),
     certificate_id UUID REFERENCES certificates(id),
     submission_id UUID REFERENCES submissions(id),
     transmission_time TIMESTAMP NOT NULL DEFAULT NOW(),
     status VARCHAR(50) NOT NULL DEFAULT 'pending',
     encrypted_payload TEXT,
     encryption_metadata JSONB,
     response_data JSONB,
     retry_count INTEGER DEFAULT 0,
     last_retry_time TIMESTAMP,
     created_by UUID REFERENCES users(id),
     transmission_metadata JSONB
   );
   ```

3. **csid_registry**
   ```sql
   CREATE TABLE csid_registry (
     id UUID PRIMARY KEY,
     organization_id UUID NOT NULL REFERENCES organizations(id),
     csid VARCHAR(100) NOT NULL UNIQUE,
     certificate_id UUID REFERENCES certificates(id),
     creation_time TIMESTAMP NOT NULL DEFAULT NOW(),
     expiration_time TIMESTAMP,
     is_active BOOLEAN DEFAULT TRUE,
     revocation_time TIMESTAMP,
     revocation_reason VARCHAR(255),
     created_by UUID REFERENCES users(id),
     metadata JSONB
   );
   ```

### 3.2 Alembic Migration Strategy

Following the multi-step approach for database migrations mentioned in the system memory:

1. **Step 1: Check Dependencies**
   - Verify that the `certificates`, `organizations`, and `users` tables exist
   - Create minimal versions if they don't exist

2. **Step 2: Create Tables Without Constraints**
   - Create the three new tables without foreign key constraints

3. **Step 3: Add Constraints**
   - Add foreign key constraints in a separate migration

## 4. API Endpoints

### 4.1 Certificate Request Endpoints

1. **POST /api/v1/certificate-requests**
   - Create a new certificate request
   - Generate CSR based on provided parameters
   - Return request ID and status

2. **GET /api/v1/certificate-requests**
   - List all certificate requests for an organization
   - Filter by status, type, and date range

3. **GET /api/v1/certificate-requests/{request_id}**
   - Get details for a specific certificate request
   - Include status and timeline information

4. **PUT /api/v1/certificate-requests/{request_id}/cancel**
   - Cancel a pending certificate request

### 4.2 CSID Management Endpoints

1. **POST /api/v1/csids**
   - Generate a new CSID for a certificate
   - Associate with certificate and organization

2. **GET /api/v1/csids**
   - List all CSIDs for an organization
   - Filter by status, certificate, and date range

3. **GET /api/v1/csids/{csid}**
   - Get details for a specific CSID
   - Include usage statistics

4. **PUT /api/v1/csids/{csid}/revoke**
   - Revoke an active CSID

### 4.3 Transmission Endpoints

1. **POST /api/v1/transmissions**
   - Create a new secure transmission
   - Encrypt payload and send to FIRS
   - Return transmission ID and status

2. **GET /api/v1/transmissions**
   - List all transmissions for an organization
   - Filter by status, date range, and certificate

3. **GET /api/v1/transmissions/{transmission_id}**
   - Get details for a specific transmission
   - Include retry history and response data

4. **POST /api/v1/transmissions/{transmission_id}/retry**
   - Manually retry a failed transmission

## 5. Frontend Components

### 5.1 Certificate Management UI

1. **Certificate Dashboard**
   - Overview of all certificates with status indicators
   - Quick actions for common operations
   - Filter and search functionality

2. **Certificate Detail View**
   - Full certificate information with timeline
   - Validity visualization with expiration warnings
   - Associated CSIDs and transmission records

3. **Certificate Request Wizard**
   - Step-by-step guide for requesting a new certificate
   - CSR generation with secure parameters
   - Status tracking for submitted requests

### 5.2 CSID Management UI

1. **CSID Dashboard**
   - List of all CSIDs with status and usage statistics
   - Quick actions for generation and revocation
   - Filter and search functionality

2. **CSID Detail View**
   - Full CSID information with timeline
   - Associated certificate and transmission records
   - Usage statistics and visualization

### 5.3 Transmission Monitoring UI

1. **Transmission Dashboard**
   - Overview of all transmissions with status indicators
   - Performance metrics and success rate
   - Filter and search functionality

2. **Transmission Detail View**
   - Full transmission information with timeline
   - Response data and error details
   - Retry history and manual retry action

## 6. Security Considerations

### 6.1 Certificate Data Protection

1. **Field-Level Encryption**
   - Continue using the existing encryption infrastructure
   - Ensure proper key rotation and management
   - Implement secure key storage with hardware security if possible

2. **Access Control**
   - Implement fine-grained permissions for certificate operations
   - Add audit logging for all sensitive operations
   - Enforce strong authentication for certificate management

### 6.2 Transmission Security

1. **Payload Encryption**
   - Implement end-to-end encryption for all transmissions
   - Use strong algorithms (AES-256-GCM) for payload protection
   - Implement secure key exchange mechanisms

2. **Transport Security**
   - Enforce TLS 1.3 for all API communications
   - Implement certificate pinning for FIRS API
   - Add additional integrity verification for transmitted data

## 7. Implementation Plan

### 7.1 Phase 1 (2 Weeks)

#### Week 1
- Implement database schema extensions
- Create basic certificate request workflow
- Implement CSID generation service
- Add transmission record infrastructure

#### Week 2
- Complete certificate management UI
- Implement secure transmission service
- Add signature generation and verification
- Create comprehensive test suite

### 7.2 Testing Strategy

1. **Unit Tests**
   - Test all cryptographic operations
   - Verify certificate parsing and validation
   - Test CSID generation and verification

2. **Integration Tests**
   - Test end-to-end certificate request workflow
   - Verify secure transmission to FIRS sandbox
   - Test certificate and CSID lifecycle management

3. **Security Tests**
   - Conduct encryption validation tests
   - Verify proper key management
   - Test access control enforcement

## 8. Future Considerations

Features to be implemented in subsequent phases:

1. **Hardware Security Module (HSM) Integration**
   - Secure key storage in dedicated hardware
   - Enhanced protection for certificate private keys
   - FIPS 140-2 compliance for cryptographic operations

2. **Advanced Certificate Rotation Strategies**
   - Automated certificate renewal process
   - Zero-downtime certificate rotation
   - Certificate delegation for multi-tenant scenarios

3. **Custom Transmission Scheduling**
   - Configurable transmission windows
   - Batch optimization for high-volume scenarios
   - Priority-based transmission queue

## 9. Conclusion

This technical specification provides a comprehensive roadmap for implementing Phase 1 of the APP functionality in the TaxPoynt eInvoice system. By building upon the existing certificate management foundation and following the multi-step migration approach, we can ensure a smooth integration of APP features while maintaining the core SI functionality.

The implementation approach follows a modular design that allows for gradual feature enablement through the feature flags system, ensuring that we can release functionality incrementally while maintaining system stability.
