# Encryption Implementation for FIRS e-Invoice System

This document describes the encryption implementation for the TaxPoynt e-Invoice system, focusing on how we secure sensitive data and implement FIRS requirements for IRN generation and signing.

## Overview

The encryption implementation consists of several components:

1. **TLS for API Communication** - All API endpoints use HTTPS to encrypt data in transit
2. **IRN Generation & Validation** - Secure generation and validation of Invoice Reference Numbers
3. **IRN Signing & QR Code Generation** - Encrypting IRNs with FIRS public key and generating QR codes
4. **Sensitive Data Encryption** - Encrypting sensitive values like API keys and secrets before storing in the database

## TLS Implementation

All API communication is secured using Transport Layer Security (TLS):

- In production, HTTPS is enforced using Starlette's `HTTPSRedirectMiddleware`
- SSL certificates can be configured via environment variables (`SSL_KEYFILE`, `SSL_CERTFILE`)
- When deployed on platforms like Railway or AWS, TLS termination is typically handled by the platform

## IRN Generation & Validation

Invoice Reference Numbers (IRNs) are generated according to FIRS requirements:

- Format: `InvoiceNumber-ServiceID-YYYYMMDD`
- Example: `INV001-94ND90NR-20240611`
- Strict validation of all components to prevent tampering or errors

## IRN Signing & QR Code Generation

IRNs are signed using the FIRS public key:

1. The FIRS crypto_keys.txt file contains the public key and certificate
2. The IRN and certificate are packaged as JSON and encrypted with the public key
3. The encrypted data is Base64 encoded and embedded in a QR code
4. The QR code can be verified by FIRS using their private key

## Sensitive Data Encryption

Sensitive data like API keys and secrets are encrypted before storage:

- AES-256-GCM encryption is used for sensitive values
- Encryption keys are managed securely and not stored with the encrypted data
- Environment variables are used for key management in production

## Key Management

- **Application Encryption Key**: Stored as an environment variable (`ENCRYPTION_KEY`)
- **FIRS Public Key**: Downloaded from FIRS or provided by the organization
- **Key Rotation**: Support for key rotation is built into the design

## Security Considerations

- All encryption uses industry-standard algorithms and libraries (cryptography, PyJWT)
- Proper error handling to avoid leaking sensitive information
- Comprehensive testing of encryption functionality
- Input validation to prevent injection attacks
- Sensitive data masking in logs

## Code Structure

The encryption functionality is organized into several modules:

- `app/utils/encryption.py` - Core encryption utilities
- `app/utils/irn.py` - IRN generation and validation
- `app/utils/qr_code.py` - QR code generation utilities
- `app/routers/crypto.py` - API endpoints for crypto operations

## API Endpoints

The following endpoints are available for crypto operations:

- `GET /crypto/keys` - Download cryptographic keys
- `POST /crypto/upload-keys` - Upload a crypto_keys.txt file
- `POST /crypto/sign-irn` - Sign an IRN with the FIRS public key
- `POST /crypto/generate-irn` - Generate an IRN according to FIRS requirements
- `GET /crypto/qr-code/{irn}` - Generate a QR code for an IRN

## Testing

Comprehensive tests are included for all encryption functionality:

- Unit tests for encryption utilities
- Unit tests for IRN generation and validation
- API tests for crypto endpoints
- Integration tests for end-to-end encryption flows

## Environment Variables

The following environment variables are used for encryption configuration:

- `ENCRYPTION_KEY` - Base64 encoded 32-byte key for application encryption
- `SSL_KEYFILE` - Path to SSL key file (for direct TLS termination)
- `SSL_CERTFILE` - Path to SSL certificate file (for direct TLS termination)
- `ENVIRONMENT` - Application environment (development, staging, production) 