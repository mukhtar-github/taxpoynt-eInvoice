# Odoo to BIS Billing 3.0 UBL Field Mapping Implementation

## Overview

This document summarizes the implementation of a mapping system between Odoo invoice data and the BIS Billing 3.0 UBL (Universal Business Language) format for the TaxPoynt eInvoice project. The implementation enables seamless conversion of Odoo invoice data to the UBL format required by the Federal Inland Revenue Service (FIRS) of Nigeria.

## Key Components

### 1. Field Mapping (odoo_ubl_mapper.py)

We implemented a comprehensive mapping schema that transforms Odoo invoice fields to their corresponding BIS Billing 3.0 UBL format. The mapping covers:

- **Invoice Headers**: Basic invoice information such as number, type, dates, and currency
- **Supplier Information**: Complete company details including name, tax ID, address, and contact info
- **Customer Information**: Partner details with full address and contact information
- **Line Items**: Product quantities, prices, descriptions, and identifiers
- **Tax Information**: Tax rates, categories, and amounts
- **Payment Terms**: Due dates and payment method information
- **Monetary Totals**: Invoice subtotals, tax totals, and payable amounts

Special attention was given to handling code mappings for various enumerated types:
- Invoice type codes (e.g., out_invoice → 380)
- Tax categories (e.g., VAT → S)
- Unit codes (e.g., kg → KGM)
- Payment methods (e.g., bank_transfer → 30)

### 2. Field Validation (odoo_ubl_validator.py)

A robust validation system ensures that mapped data complies with BIS Billing 3.0 requirements:

- Validates presence of all required fields defined in the UBL standard
- Performs business rule validations such as:
  - Line amounts consistency with quantities and prices
  - Tax calculations correctness
  - Date sequence validity
  - Total amounts reconciliation

The validator returns detailed error messages when validation fails, making it easier to identify and fix mapping issues.

### 3. XML Transformation (odoo_ubl_transformer.py)

A transformation service converts validated data objects to BIS Billing 3.0 UBL XML:

- Generates properly namespaced XML following UBL 2.1 specifications
- Applies appropriate XML structures for all invoice components
- Handles currency attributes and unit code attributes
- Preserves numeric precision for monetary values
- Formats dates according to ISO standards

## Implementation Details

- **Error Handling**: Comprehensive error handling throughout the mapping, validation, and transformation process
- **Reusable Components**: Modular design with singleton instances for easy reuse across the application
- **Extensibility**: Structured to allow for future extensions to support additional fields or UBL versions
- **Documentation**: Complete field mapping documentation for maintenance and reference

## Usage Example

```python
# Get invoice data from Odoo
odoo_invoice = odoo_connector.get_invoice("INV/2023/00123")
company_info = odoo_connector.get_company_info()

# Map and validate
ubl_invoice, validation_issues = odoo_ubl_transformer.odoo_to_ubl_object(
    odoo_invoice, company_info
)

# Generate UBL XML if valid
if not validation_issues:
    ubl_xml, conversion_issues = odoo_ubl_transformer.ubl_object_to_xml(ubl_invoice)
    
    if not conversion_issues:
        # Submit to FIRS or store in database
        firs_response = firs_service.submit_invoice(ubl_xml)
    else:
        logger.error(f"XML conversion issues: {conversion_issues}")
else:
    logger.error(f"Validation issues: {validation_issues}")
```

## Next Steps

1. Implement unit tests for the mapper, validator, and transformer components
2. Test with real Odoo invoice data to verify complete coverage of field mappings
3. Integrate with the existing IRN generation workflow in the TaxPoynt eInvoice system
4. Add support for additional Odoo fields and customizations as needed

## References

The implementation follows the BIS Billing 3.0 standard as referenced in:
- [Peppol BIS Billing 3.0 Documentation](https://docs.peppol.eu/poacc/billing/3.0/)
- FIRS e-Invoicing Guidelines and Technical Documentation
