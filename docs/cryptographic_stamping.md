# FIRS Cryptographic Stamping Implementation

This document describes the implementation of FIRS cryptographic stamping in the TaxPoynt eInvoice system.

## Overview

The cryptographic stamping feature enables invoices to be digitally signed according to FIRS requirements. This ensures:
- Invoice authenticity and integrity
- Non-repudiation of invoice data
- Compliance with FIRS e-invoicing standards
- Secure transmission and verification of invoice data

## Architecture

The implementation follows a modular design with clear separation between APP and SI layers:

### Components

1. **Certificate Manager** (`app/utils/certificate_manager.py`)
   - Handles all certificate operations
   - Stores and loads certificates
   - Validates certificates and their chain of trust
   - Extracts public keys from certificates
   - Creates self-signed certificates for testing

2. **Cryptographic Stamping Service** (`app/services/cryptographic_stamping_service.py`)
   - High-level service that orchestrates the stamping process
   - Generates and verifies Cryptographic Stamp IDs (CSIDs)
   - Creates QR codes containing stamp data
   - Integrates with the certificate manager for certificate validation
   - Provides methods to stamp and verify invoices

3. **Crypto API Endpoints** (`app/routers/crypto.py`)
   - REST API endpoints for cryptographic operations
   - Certificate management endpoints
   - CSID generation and verification
   - Cryptographic stamping of invoices
   - Integration with authentication system

### Cryptographic Standards

- **RSA-PSS-SHA256**: Primary signature algorithm
- **X.509 Certificates**: For key and identity management
- **Base64 Encoding**: For data transmission
- **QR Code Generation**: For easy verification on printed/displayed invoices

## Usage

### API Endpoints

#### Certificate Management

```
GET /api/crypto/certificates
```
Lists all available certificates in the system.

```
POST /api/crypto/upload-keys
```
Upload FIRS crypto keys file.

#### Cryptographic Stamping

```
POST /api/crypto/generate-stamp
```
Apply a cryptographic stamp to an invoice.

Request body:
```json
{
  "invoice_data": {
    "invoice_number": "INV-2023-001",
    "date": "2023-10-15",
    "seller": {
      "name": "Test Company Ltd",
      "tax_id": "12345678901"
    },
    "buyer": {
      "name": "Test Customer",
      "tax_id": "98765432109"
    },
    "items": [
      {
        "description": "Test Product",
        "quantity": 2,
        "unit_price": 5000.00,
        "total": 10000.00,
        "tax_rate": 7.5
      }
    ],
    "total_amount": 10000.00,
    "total_tax": 750.00,
    "currency": "NGN"
  }
}
```

Response:
```json
{
  "stamped_invoice": {
    // Original invoice data with added cryptographic_stamp field
    "cryptographic_stamp": {
      "csid": "base64_encoded_signature",
      "timestamp": "2023-10-15T12:00:00Z",
      "algorithm": "RSA_PSS_SHA256",
      "qr_code": "base64_encoded_qr_code",
      "certificate_id": "cert_identifier"
    }
  },
  "stamp_info": {
    "csid": "base64_encoded_signature",
    "timestamp": "2023-10-15T12:00:00Z",
    "algorithm": "RSA_PSS_SHA256",
    "qr_code": "base64_encoded_qr_code",
    "certificate_id": "cert_identifier"
  }
}
```

```
POST /api/crypto/verify-stamp
```
Verify a cryptographic stamp on an invoice.

Request body:
```json
{
  "invoice_data": {
    // Original invoice data
  },
  "stamp_data": {
    "csid": "base64_encoded_signature",
    "timestamp": "2023-10-15T12:00:00Z",
    "algorithm": "RSA_PSS_SHA256",
    "certificate_id": "cert_identifier"
  }
}
```

Response:
```json
{
  "is_valid": true,
  "details": {
    "verified_at": "2023-10-15T12:30:00Z",
    "certificate_status": "valid"
  }
}
```

### Integration with ERP Systems

The cryptographic stamping functionality is designed to integrate with the existing ERP-first strategy:

1. When an invoice is created in an ERP system (e.g., Odoo), it's transmitted to TaxPoynt.
2. TaxPoynt applies the cryptographic stamp using the FIRS certificate.
3. The stamped invoice is stored and can be transmitted to FIRS.
4. The QR code can be included on the printed invoice for verification.

## Testing

Comprehensive testing is implemented at multiple levels:

1. **Unit Tests**:
   - `app/tests/utils/test_certificate_manager.py`: Tests for certificate operations
   - `app/tests/services/test_cryptographic_stamping_service.py`: Tests for stamping service

2. **API Tests**:
   - `app/tests/api/test_crypto_api.py`: Tests for API endpoints

3. **End-to-End Tests**:
   - `app/tests/e2e/test_crypto_stamping_e2e.py`: Complete workflow test

To run the tests:

```bash
# Run unit tests
pytest app/tests/utils/test_certificate_manager.py
pytest app/tests/services/test_cryptographic_stamping_service.py

# Run API tests
pytest app/tests/api/test_crypto_api.py

# Run E2E tests
pytest app/tests/e2e/test_crypto_stamping_e2e.py
```

## Security Considerations

1. **Certificate Storage**: Certificates are stored with appropriate file permissions.
2. **Key Protection**: Private keys can be password-protected.
3. **Authentication**: All API endpoints require authentication.
4. **Superuser Restriction**: Certificate management requires superuser privileges.
5. **TLS**: All API communications must use TLS (as per FIRS requirements).

## Future Improvements

1. **OCSP Integration**: Online Certificate Status Protocol for real-time certificate validation.
2. **HSM Support**: Hardware Security Module integration for enhanced key security.
3. **Audit Logging**: Comprehensive logging of all cryptographic operations.
4. **Certificate Rotation**: Automated certificate rotation and management.
5. **Multi-tenant Support**: Separate certificates for different organizations.
