# FIRS e-Invoice Pre-submission Validation Guide

## Overview

This document outlines the comprehensive pre-submission validation system implemented for Nigerian FIRS e-Invoice requirements. The validation system ensures that invoices conform to both UBL (Universal Business Language) standards and specific FIRS regulations before submission, reducing the risk of rejection and ensuring compliance with Nigerian tax requirements.

## Key Components

The validation system consists of the following key components:

1. **Validation Rule Engine**: Core engine that applies validation rules to invoice data
2. **UBL Schema Validator**: Validates invoice structure against official UBL standards
3. **FIRS-Specific Validation Rules**: Custom rules based on Nigerian tax requirements
4. **Validation Rule Management System**: Interface for managing validation rules
5. **Error Reporting System**: Clear and actionable validation error messages

## Validation Rules

### FIRS-Specific Requirements

The following validation categories are specifically implemented for FIRS e-Invoice compliance:

#### Registration and Identity Validation

| Rule ID | Description | Severity |
|---------|-------------|----------|
| FIRS-REG-001 | Seller must have a valid Nigerian TIN (14 digits) | Error |
| FIRS-REG-002 | B2B invoices require buyer to have a valid Nigerian TIN | Error |

#### Format Validation

| Rule ID | Description | Severity |
|---------|-------------|----------|
| FIRS-FMT-001 | Invoice number must contain only alphanumeric characters (max 50 chars) | Error |
| FIRS-CUR-001 | Primary currency must be NGN for domestic transactions | Error |
| FIRS-ADR-001 | Seller must have valid Nigerian address with state and LGA for domestic invoices | Error |

#### Nigerian Tax Rules

| Rule ID | Description | Severity |
|---------|-------------|----------|
| FIRS-TAX-001 | VAT must be calculated correctly at 7.5% unless specifically exempt | Error |
| FIRS-TAX-002 | VAT exempt or zero-rated items must include valid exemption reason code | Error |
| FIRS-TAX-003 | Withholding Tax should be calculated correctly for applicable services | Warning |

### UBL Schema Validation

The system validates invoice structure against the official UBL 2.1 schema as required by the BIS Billing 3.0 standard and FIRS:

- Element structure and relationships
- Required fields presence
- Data type validation
- Code list validation

### Business Rule Validation

Beyond schema validation, the system includes business logic validation:

- Date consistency (e.g., due date after invoice date)
- Tax calculation correctness
- Monetary total consistency
- Line item validation

## Validation Rule Management

### Rule Administration

Administrators can:

1. View all validation rules with filtering options
2. Enable or disable specific rules
3. Create custom validation rules
4. Group rules into validation presets
5. Test rules with sample invoice data

### Custom Rule Creation

The system supports creating custom validation rules with:

- Different validation logic types (field presence, format, comparison, etc.)
- Configurable severity levels (error, warning, info)
- Field-specific validation paths
- Custom error messages

### Validation Presets

Presets allow grouping rules for different validation scenarios:

- FIRS Nigeria (comprehensive preset with all FIRS requirements)
- UBL Basic (core UBL schema validation)
- UBL Extended (advanced UBL requirements)
- Custom presets for specific business needs

## Error Reporting

Validation errors include:

- Clear error message explaining the issue
- Field path indicating where the error occurred
- Error code for reference
- Severity level (error, warning, info)
- Suggestions for resolution when applicable

## Integration with Odoo

The validation system includes special mapping for Odoo invoice data:

1. Odoo invoice fields are mapped to UBL structure
2. Validation occurs before IRN generation
3. Field-level validation errors are mapped back to Odoo fields
4. Comprehensive validation reports are provided for each invoice

## Using the Validation API

### Basic Invoice Validation

```python
POST /api/v1/validation/invoice
{
  "invoice_data": { ... }  // Invoice data in UBL format
}
```

### Batch Validation

```python
POST /api/v1/validation/batch
{
  "invoices": [
    { ... },  // Invoice 1
    { ... }   // Invoice 2
  ]
}
```

### Managing Validation Rules

```python
# List all rules
GET /api/v1/validation-management/validation-rules

# Create custom rule
POST /api/v1/validation-management/validation-rules

# Update rule
PUT /api/v1/validation-management/validation-rules/{rule_id}

# Disable rule
POST /api/v1/validation-management/validation-rules/{rule_id}/disable
```

## Implementation Considerations

### Performance Optimization

- Validation rules are cached for faster processing
- Batch validation to process multiple invoices efficiently
- Parallel validation for high throughput

### Security

- Rule management requires authentication
- Validation operations are logged for audit purposes
- Custom rules have controlled execution environments

### Extensibility

- Pluggable validation rule system
- Support for custom rule types
- API for integrating with other systems

## Testing and Verification

To verify the validation system:

1. Use the test endpoint with sample invoice data
2. Review validation results and error messages
3. Test with known invalid invoices to confirm error detection
4. Verify FIRS-specific rules with Nigerian tax documents

## Conclusion

This comprehensive validation system ensures invoices meet both UBL standards and specific FIRS requirements before submission, reducing rejection risk and ensuring compliance with Nigerian tax regulations. The flexible rule management system allows for adaptation to changing requirements and business needs.
