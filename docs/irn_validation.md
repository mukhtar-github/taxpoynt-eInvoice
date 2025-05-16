# IRN Validation Implementation

## Overview

This document details the comprehensive IRN (Invoice Reference Number) validation implementation that ensures IRN integrity according to FIRS specifications. The validation system provides robust checks for format compliance, hash verification, and invoice content matching.

**Date:** May 16, 2025

## Validation Architecture

The IRN validation system is implemented as a separate module to provide comprehensive validation capabilities while ensuring compatibility with the existing IRN generation system and UBL mapping functionality.

### Core Components

1. **IRN Validator Module** (`app/utils/irn_validator.py`)
   - Provides dedicated validation functions
   - Supports in-depth integrity checks
   - Compatible with both regular invoices and UBL-mapped invoices
   - Includes test scenario capabilities

2. **Integration Points**
   - Works with IRN Generator (`app/utils/irn_generator.py`)
   - Compatible with IRN Service (`app/services/irn_service.py`) 
   - Supports Odoo to BIS Billing 3.0 UBL mapping system

## Key Validation Functions

### 1. Format Validation

The `validate_irn_format` function ensures IRNs comply with the FIRS format requirements:

```python
def validate_irn_format(irn: str) -> Tuple[bool, str]:
    """Validate that an IRN follows the format required by FIRS."""
    # Checks for InvoiceNumber-ServiceID-YYYYMMDD pattern
    pattern = re.compile(r'^[a-zA-Z0-9]+-[a-zA-Z0-9]{8}-\d{8}$')
    if not pattern.match(irn):
        return False, "Invalid IRN format"
    
    # Further validates each component
    invoice_number, service_id, timestamp = irn.split('-')
    
    if not validate_invoice_number(invoice_number):
        return False, "Invalid invoice number format"
    
    # Additional validations...
    
    return True, "IRN format is valid"
```

### 2. Invoice Content Validation

The `validate_irn_against_invoice` function verifies that an IRN matches the invoice data it claims to represent:

```python
def validate_irn_against_invoice(
    irn: str,
    invoice_data: Dict[str, Any],
    verify_hash: bool = True,
    stored_hash: Optional[str] = None,
    stored_verification_code: Optional[str] = None
) -> Tuple[bool, str, dict]:
    """Comprehensive validation of an IRN against invoice data."""
    # Validates format, components, invoice match, and hash
    # Returns detailed validation results
```

### 3. Cryptographic Integrity Verification

The `verify_irn_integrity` function performs cryptographic validation to ensure the IRN hasn't been tampered with:

```python
def verify_irn_integrity(
    irn: str, 
    verification_code: str,
    hash_value: str,
    invoice_data: Dict[str, Any]
) -> Tuple[bool, str]:
    """Verify the cryptographic integrity of an IRN."""
    # Verifies hash matches invoice data
    # Verifies verification code matches hash
    # Ensures all components are valid
```

### 4. Validation Reporting

The `generate_validation_report` function provides a comprehensive validation report:

```python
def generate_validation_report(
    irn: str,
    invoice_data: Dict[str, Any],
    hash_value: Optional[str] = None,
    verification_code: Optional[str] = None
) -> Dict[str, Any]:
    """Generate a comprehensive validation report for an IRN."""
    # Runs all validations
    # Produces detailed report with results
```

## Validation Scenarios

The validation system supports testing with various invoice scenarios through the `run_irn_validation_test` function:

1. **Valid IRN with matching data**: Tests standard happy path
2. **Mismatched invoice number**: Tests detection of invoice data mismatches
3. **Invalid IRN format**: Tests format validation
4. **Hash verification**: Tests cryptographic integrity checks
5. **Expired/revoked IRN**: Tests status validation

## Testing

A comprehensive test suite (`backend/tests/test_irn_validator.py`) validates all functionality:

```bash
# Run validation tests
python -m backend.tests.test_irn_validator
```

The test suite covers:
- Format validation
- Invoice content matching
- Hash verification
- Verification code validation
- Test scenario functionality
- Validation reporting

## Integration with UBL System

The validation system is designed to work seamlessly with the Odoo to BIS Billing 3.0 UBL mapping system. It can validate IRNs generated for UBL-formatted invoices by:

1. **Field Extraction**: Correctly extracting fields from UBL format
2. **Flexible Validation**: Supporting both standard and UBL invoice formats
3. **Consistent Results**: Providing the same validation quality for all invoice types

## Security Features

The validation implementation includes several security features:

1. **Comprehensive Format Checking**: Prevents injection attacks
2. **Cryptographic Validation**: Ensures data integrity
3. **Component Validation**: Validates all IRN components individually
4. **Detailed Error Messages**: Helps identify validation issues
5. **Logging**: Records validation attempts and results

## Usage Examples

### Basic IRN Validation

```python
from app.utils.irn_validator import validate_irn_format

# Simple format validation
is_valid, message = validate_irn_format("INV2025001-94ND90NR-20250516")
if is_valid:
    print("IRN format is valid")
else:
    print(f"Invalid format: {message}")
```

### Comprehensive IRN Validation

```python
from app.utils.irn_validator import validate_irn_against_invoice

# Invoice data
invoice_data = {
    'invoice_number': 'INV2025001',
    'invoice_date': '2025-05-16',
    # Other invoice fields...
}

# Validate IRN against invoice
is_valid, message, details = validate_irn_against_invoice(
    "INV2025001-94ND90NR-20250516",
    invoice_data,
    verify_hash=True,
    stored_hash="hash_from_database",
    stored_verification_code="verification_code_from_database"
)

print(f"Validation result: {'Valid' if is_valid else 'Invalid'}")
print(f"Message: {message}")
print(f"Details: {details}")
```

### Generating a Validation Report

```python
from app.utils.irn_validator import generate_validation_report

# Generate a comprehensive validation report
report = generate_validation_report(
    "INV2025001-94ND90NR-20250516",
    invoice_data,
    hash_value="hash_from_database",
    verification_code="verification_code_from_database"
)

print(f"Overall result: {report['overall_result']}")
for key, validation in report['validations'].items():
    print(f"{key}: {'✅ Valid' if validation.get('is_valid') else '❌ Invalid'}")
```

## Best Practices

1. **Always Validate Format First**: This is the quickest check and fails fast
2. **Use Appropriate Detail Level**: Basic format validation for quick checks, comprehensive validation for critical operations
3. **Store Hash and Verification Code**: Store both for complete integrity checks
4. **Generate Reports for Auditing**: Use validation reports for audit trails
5. **Test with Various Scenarios**: Regularly test with different invoice scenarios

---

## Appendix: Validation Status Codes

| Status | Description | Action |
|--------|-------------|--------|
| `VALID` | IRN passes all validation checks | Accept the IRN |
| `INVALID_FORMAT` | IRN format doesn't comply with FIRS | Reject the IRN |
| `INVALID_COMPONENT` | One or more IRN components are invalid | Reject the IRN |
| `INVOICE_MISMATCH` | IRN doesn't match invoice data | Investigate mismatch |
| `HASH_MISMATCH` | Hash verification failed | Potential tampering |
| `EXPIRED` | IRN has expired | Generate new IRN |
| `REVOKED` | IRN has been revoked | Investigate reason |
| `ERROR` | Validation error occurred | Check logs for details |
