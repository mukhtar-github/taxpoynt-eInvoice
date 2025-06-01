# Secure Transmission Module for FIRS API Integration

## Overview

The Secure Transmission module provides encrypted, reliable transmission of invoice data to the Federal Inland Revenue Service (FIRS) API. This document describes the architecture, components, and usage of the secure transmission feature.

## Features

- **Encrypted Payload Packaging**: RSA-OAEP for key encryption and AES-256-GCM for payload encryption
- **Secure Transmission Protocol**: OAuth2 authentication with FIRS API endpoints
- **Automatic Retry Logic**: Exponential backoff for failed transmissions
- **Transmission Receipt Storage**: Verification and storage of transmission receipts
- **Platform-SI Separation**: Clean architectural boundaries between Platform and SI functionality

## Architecture

### Backend Components

1. **Encryption Utility** (`firs_encryption.py`)
   - Implements FIRS-specific encryption requirements
   - Handles AES-256-GCM encryption of payloads
   - Manages RSA-OAEP encryption of AES keys
   - Creates secure headers for transmission

2. **FIRS Transmission Service** (`firs_transmission_service.py`)
   - Handles authentication with FIRS API
   - Manages secure transmission with retry logic
   - Creates and stores transmission receipts
   - Provides status checking functionality

3. **Transmission Receipt Model** (`receipt.py`)
   - Stores transmission receipts with verification status
   - Links to transmission records

4. **Transmission Retry Worker** (`transmission_retry_worker.py`)
   - Background process for retrying failed transmissions
   - Implements exponential backoff strategy
   - Updates retry metadata and history

5. **Secure Transmission API Routes** (`secure_transmission.py`)
   - FastAPI routes for transmission operations
   - Authentication and authorization checks
   - Background task handling

### Frontend Components

1. **Secure Transmission Manager** (`SecureTransmissionManager.tsx`)
   - Lists and manages transmission records
   - Displays transmission status and details
   - Provides retry functionality for failed transmissions
   - Shows transmission receipts for completed transmissions

2. **New Transmission** (`NewTransmission.tsx`)
   - Creates new secure transmissions
   - Supports JSON and file uploads
   - Allows selection of digital certificates for signing

3. **Invoice Transmit Button** (`InvoiceTransmitButton.tsx`)
   - Component for direct invoice transmission
   - Integrates with invoice details page
   - Shows transmission status and receipts

4. **Transmission Details** (`TransmissionDetails.tsx`) and **Transmission Receipt** (`TransmissionReceipt.tsx`)
   - Reusable components for displaying transmission information
   - Support download and verification of receipts

## User Guide

### Transmitting Data to FIRS

1. Navigate to the Secure Transmission page from the dashboard sidebar
2. Use the "New Transmission" tab to create a new transmission
3. Enter JSON payload or upload a file
4. Optionally select a digital certificate for signing
5. Click "Transmit Securely"

### Managing Transmissions

1. View all transmissions in the "Manage Transmissions" tab
2. Check transmission status and details
3. Retry failed transmissions
4. View and download receipts for completed transmissions

### Transmitting Invoices Directly

1. Open the invoice details page
2. Click the "Transmit to FIRS" button
3. Optionally select a digital certificate for signing
4. Complete the transmission process

## Configuration

The secure transmission feature requires the following environment variables:

```
FIRS_PUBLIC_KEY_PATH=path/to/firs/public/key.pem
FIRS_API_BASE_URL=https://api.firs.gov.ng/v1
FIRS_CLIENT_ID=your_client_id
FIRS_CLIENT_SECRET=your_client_secret
```

## Security Considerations

- All sensitive cryptographic operations are handled in the backend
- Payloads are encrypted before transmission
- OAuth2 token-based authentication is used for API calls
- Digital signatures provide non-repudiation and integrity verification
- Transmission receipts are stored for audit purposes

## Troubleshooting

### Common Issues

1. **Failed Transmissions**: Check network connectivity and FIRS API status
2. **Authentication Errors**: Verify client credentials in environment variables
3. **Encryption Errors**: Ensure FIRS public key is correctly configured
4. **Receipt Verification Failures**: Contact FIRS support for assistance

## API Reference

See the FastAPI documentation at `/docs` endpoint for detailed API specifications.
