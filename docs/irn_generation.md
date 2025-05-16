# IRN Generation Implementation

## Overview

This document describes the implementation of the Invoice Reference Number (IRN) generation algorithm according to FIRS (Federal Inland Revenue Service) specifications. The implementation provides a secure, reliable, and FIRS-compliant method for generating unique identifiers for invoices in the TaxPoynt eInvoice system.

**Date:** May 16, 2025

## FIRS IRN Format Requirements

The FIRS requires that each electronic invoice has a unique IRN with the following format:

```
InvoiceNumber-ServiceID-YYYYMMDD
```

Where:
- **InvoiceNumber**: Alphanumeric identifier from the taxpayer's accounting system (max 50 characters)
- **ServiceID**: 8-character alphanumeric identifier assigned by FIRS
- **Date**: YYYYMMDD format representing the invoice date

Example: `INV001-94ND90NR-20240611`

## Implementation Architecture

The IRN generation is implemented in the following components:

### 1. IRN Generator (`app/utils/irn_generator.py`)

This module provides the core functionality for IRN generation:

- **Validation Functions**:
  - `validate_invoice_number`: Validates invoice numbers according to FIRS requirements
  - `validate_service_id`: Validates 8-character alphanumeric service IDs
  - `validate_timestamp`: Validates date strings in YYYYMMDD format

- **IRN Generation**:
  - `generate_firs_irn`: Creates a complete IRN according to FIRS specifications
  - `calculate_invoice_hash`: Computes cryptographic hash of invoice data for verification
  - `generate_verification_code`: Creates HMAC-based verification codes

- **UBL Integration**:
  - `generate_irn_for_ubl_invoice`: Generates IRNs specifically for UBL-formatted invoices
  - Works with the Odoo to BIS Billing 3.0 UBL mapping system

### 2. IRN Service (`app/services/irn_service.py`)

This service provides business-level IRN functionality:

- Record management in the database
- IRN verification and validation
- Integration with other application services

## Key Features

1. **FIRS Compliance**: Implements the exact format required by FIRS guidelines
2. **Cryptographic Security**: Uses SHA-256 hashes and HMAC verification for security
3. **Validation**: Comprehensive input validation for all IRN components
4. **UBL Compatibility**: Integrates with the Odoo UBL mapping system
5. **Backward Compatibility**: Maintains compatibility with legacy IRN formats
6. **Error Handling**: Detailed error messages and logging for troubleshooting

## Usage Examples

### Basic IRN Generation

```python
from app.utils.irn_generator import generate_firs_irn

# Prepare invoice data
invoice_data = {
    'invoice_number': 'INV2025001',
    'invoice_date': '2025-05-16',
    'seller_tax_id': 'NG123456789',
    'buyer_tax_id': 'NG987654321',
    'total_amount': 1500.0,
    'currency_code': 'NGN',
}

# Generate IRN
irn_result = generate_firs_irn(invoice_data)

# Access the IRN and components
irn = irn_result['irn']  # e.g., 'INV2025001-94ND90NR-20250516'
verification_code = irn_result['verification_code']
hash_value = irn_result['hash_value']
```

### Generating IRN from UBL Invoice

```python
from app.utils.irn_generator import generate_irn_for_ubl_invoice

# UBL-formatted invoice data
ubl_invoice = {
    'ID': 'UBL2025001',
    'IssueDate': '2025-05-16',
    # Other UBL fields...
}

# Generate IRN with a specific service ID
service_id = 'UBLSVCID'
irn_result = generate_irn_for_ubl_invoice(ubl_invoice, service_id)
```

### Verifying an IRN

```python
from app.utils.irn_generator import verify_irn

# IRN to verify
irn = 'INV2025001-94ND90NR-20250516'

# Invoice data to verify against
invoice_data = {
    'invoice_number': 'INV2025001',
    # Other invoice fields...
}

# Verify the IRN
is_valid, message = verify_irn(irn, invoice_data)
if is_valid:
    print(f"IRN is valid: {message}")
else:
    print(f"Invalid IRN: {message}")
```

## Testing

A comprehensive test suite is provided in `backend/tests/test_irn_generator.py`. It covers:

- Field extraction and formatting
- Hash calculation and verification
- Service ID generation and validation
- IRN generation and parsing
- UBL integration

To run the tests:

```bash
cd /path/to/taxpoynt-eInvoice
python -m backend.tests.test_irn_generator
```

## Integration with Existing Systems

The IRN generation system integrates with the following components:

1. **Odoo UBL Mapping System**: Generates IRNs for invoices mapped from Odoo to BIS Billing 3.0
2. **Crypto Services**: Works with digital signing and encryption for secure transmission
3. **QR Code Generation**: IRNs can be embedded in QR codes for easy verification

## Security Considerations

1. **Hash Algorithms**: SHA-256 is used for all hash calculations
2. **Verification Codes**: HMAC-based verification with application secret key
3. **Non-Repudiation**: IRNs can be cryptographically verified against invoice data
4. **Timestamp Security**: Validation prevents future-dated invoices

## Future Enhancements

1. **Distributed Generation**: Support for high-throughput IRN generation across multiple nodes
2. **Caching Strategy**: Implement caching for frequently verified IRNs
3. **Blockchain Integration**: Option to register IRNs on a blockchain for immutable records

---

## Appendix: FIRS Compliance Checklist

| Requirement | Implementation | Status |
|-------------|---------------|--------|
| InvoiceNumber-ServiceID-YYYYMMDD format | `generate_firs_irn` function | ✅ |
| Invoice Number validation | `validate_invoice_number` function | ✅ |
| Service ID validation | `validate_service_id` function | ✅ |
| Date validation | `validate_timestamp` function | ✅ |
| No duplicate IRNs | Unique hash + timestamp combination | ✅ |
| Cryptographic security | SHA-256 + HMAC verification | ✅ |
