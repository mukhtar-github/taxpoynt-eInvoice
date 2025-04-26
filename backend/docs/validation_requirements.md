# FIRS Invoice Validation Requirements

This document outlines the validation requirements for invoices according to the Federal Inland Revenue Service (FIRS) e-invoicing system.

## 1. Schema Validation Requirements

### 1.1 Required Fields

The following fields are mandatory for all invoices:

| Field                     | Description                        | Validation Requirements                                                                        |
| ------------------------- | ---------------------------------- | ---------------------------------------------------------------------------------------------- |
| business_id               | Unique identifier for the business | Must be a valid UUID                                                                           |
| irn                       | Invoice Reference Number           | Must follow format: InvoiceNumber-ServiceID-YYYYMMDD                                           |
| issue_date                | Date of invoice issuance           | Must be in format YYYY-MM-DD                                                                   |
| invoice_type_code         | Code identifying invoice type      | Must be a valid FIRS invoice type code (e.g., 381)                                             |
| document_currency_code    | Currency code                      | Must be a valid ISO 4217 currency code (e.g., NGN)                                             |
| accounting_supplier_party | Seller information                 | Must include valid party name and postal address                                               |
| accounting_customer_party | Buyer information                  | Must include valid party name and postal address                                               |
| legal_monetary_total      | Financial totals                   | Must include line_extension_amount, tax_exclusive_amount, tax_inclusive_amount, payable_amount |
| invoice_line              | Array of items or services         | Must contain at least one invoice line                                                         |

### 1.2 Optional Fields

The following fields are optional for invoices:

| Field                         | Description                                | Validation Requirements                              |
| ----------------------------- | ------------------------------------------ | ---------------------------------------------------- |
| due_date                      | Payment due date                           | Must be in format YYYY-MM-DD, after issue_date       |
| issue_time                    | Issue time of the invoice                  | Must be in format HH:MM:SS                           |
| payment_status                | Invoice payment status                     | Default is "PENDING"                                 |
| note                          | Free-text note on the invoice              | No specific validation                               |
| tax_point_date                | Value-added tax point date                 | Must be in format YYYY-MM-DD                         |
| tax_currency_code             | VAT accounting currency code               | Must be a valid ISO 4217 currency code               |
| accounting_cost               | Buyer accounting reference                 | No specific validation                               |
| buyer_reference               | Identifier for internal routing            | No specific validation                               |
| invoice_delivery_period       | Delivery or invoice period                 | start_date must be before or equal to end_date       |
| order_reference               | Order and sales-order reference            | No specific validation                               |
| billing_reference             | Preceding invoice references               | Each reference must contain valid IRN and issue_date |
| dispatch_document_reference   | References to despatch advice documents    | Each reference must contain valid IRN and issue_date |
| receipt_document_reference    | References to receipt advice documents     | Each reference must contain valid IRN and issue_date |
| originator_document_reference | References to original initiating document | Each reference must contain valid IRN and issue_date |
| contract_document_reference   | References to governing contract           | Each reference must contain valid IRN and issue_date |
| additional_document_reference | General references to related documents    | Each reference must contain valid IRN and issue_date |
| actual_delivery_date          | Actual delivery date                       | Must be in format YYYY-MM-DD                         |
| payment_means                 | How and when payment is due                | Each payment means must have valid code and due date |
| payment_terms_note            | Terms and conditions of payment            | No specific validation                               |
| allowance_charge              | Discounts or extra charges                 | Each allowance/charge must indicate type and amount  |
| tax_total                     | Total tax charged                          | Tax calculations must be mathematically correct      |

### 1.3 Data Type Validation

| Field                                        | Data Type | Validation Requirements                    |
| -------------------------------------------- | --------- | ------------------------------------------ |
| business_id                                  | String    | Valid UUID format                          |
| irn                                          | String    | Alphanumeric with specific pattern         |
| issue_date                                   | String    | ISO date format (YYYY-MM-DD)               |
| invoice_type_code                            | String    | Numeric code from FIRS list                |
| document_currency_code                       | String    | 3-letter ISO currency code                 |
| accounting_supplier_party.postal_address.tin | String    | Valid TIN format (12345678-0001)           |
| accounting_customer_party.postal_address.tin | String    | Valid TIN format (12345678-0001)           |
| legal_monetary_total.*                       | Float     | Numeric values with up to 2 decimal places |
| invoice_line.*.invoiced_quantity             | Integer   | Positive integer                           |
| invoice_line.*.line_extension_amount         | Float     | Numeric value with up to 2 decimal places  |
| allowance_charge.*.charge_indicator          | Boolean   | True for charges, False for allowances     |
| allowance_charge.*.amount                    | Float     | Numeric value with up to 2 decimal places  |
| tax_total.*.tax_amount                       | Float     | Numeric value with up to 2 decimal places  |
| payment_means.*.payment_means_code           | Integer   | Valid payment means code                   |
| payment_means.*.payment_due_date             | String    | ISO date format (YYYY-MM-DD)               |
| invoice_delivery_period.start_date           | String    | ISO date format (YYYY-MM-DD)               |
| invoice_delivery_period.end_date             | String    | ISO date format (YYYY-MM-DD)               |

## 2. Business Rule Validation

### 2.1 IRN Validation

- IRN must follow the format: InvoiceNumber-ServiceID-YYYYMMDD
- InvoiceNumber: Alphanumeric, no special characters
- ServiceID: 8-character alphanumeric assigned by FIRS
- YYYYMMDD: Date in specified format, must be a valid date

### 2.2 Monetary Total Validation

- tax_inclusive_amount must be greater than or equal to tax_exclusive_amount
- payable_amount must equal tax_inclusive_amount
- line_extension_amount must equal the sum of all invoice line amounts

### 2.3 Tax Calculation Validation

- tax_total.tax_amount must equal the sum of all tax_subtotal.tax_amount values
- Each tax_subtotal.tax_amount should approximately equal taxable_amount * (percent / 100)
- Small rounding differences (less than 0.01) are permitted

### 2.4 Tax Identification Number (TIN) Validation

- TIN must follow the format: 12345678-0001
- First part must be 8 digits
- Second part must be 4 digits
- Parts are separated by a hyphen

### 2.5 Date Validation

- All dates must be in format YYYY-MM-DD
- issue_date must not be in the future
- due_date (if provided) must be after issue_date
- In invoice_delivery_period, end_date must be on or after start_date

### 2.6 Document Reference Validation

- All document references must have valid IRN format
- All document references must have valid issue_date in YYYY-MM-DD format

### 2.7 Payment Means Validation

- payment_means_code must be a valid code from the FIRS list
- payment_due_date must be in format YYYY-MM-DD

## 3. FIRS Compliance Requirements

### 3.1 Invoice Type Codes

Common invoice type codes include:

- 380: Commercial Invoice
- 381: Credit Note
- 384: Corrected Invoice
- 389: Self-billed Invoice
- 396: Purchase Order

### 3.2 Currency Codes

- NGN: Nigerian Naira (default for domestic transactions)
- Currency must be one of the ISO 4217 standard codes

### 3.3 Tax Categories

Valid tax categories according to FIRS:

- S: Standard rate
- Z: Zero rated
- E: Exempt from tax
- O: Services outside scope of tax
- VAT: Value Added Tax

### 3.4 Payment Means Codes

Common payment means codes include:

- 10: Cash
- 20: Check
- 30: Credit transfer
- 42: Payment to bank account
- 48: Bank card
- 49: Direct debit
- 50: Payment by post
- 97: Other

## 4. Validation Process Flow

The validation process follows these steps:

1. **Schema Validation**: Verify all required fields are present and data types are correct
2. **Format Validation**: Check that string formats (dates, TIN, IRN) are valid
3. **Business Rule Validation**: Apply business logic rules for monetary totals, dates, tax calculations, etc.
4. **Compliance Validation**: Check against FIRS reference data (currency codes, invoice types, payment means, etc.)

## 5. Validation Response

The validation response includes:

- Overall validation result (valid or invalid)
- List of validation issues, each with:
  - Field path
  - Error message
  - Severity (error, warning, info)
  - Error code

## 6. Common Validation Errors

| Error Code                    | Description                                               | Severity |
| ----------------------------- | --------------------------------------------------------- | -------- |
| required_field                | A required field is missing                               | ERROR    |
| invalid_irn_format            | IRN format is invalid                                     | ERROR    |
| invalid_date_format           | Date format is invalid                                    | ERROR    |
| invalid_time_format           | Time format is invalid                                    | ERROR    |
| invalid_tin_format            | TIN format is invalid                                     | ERROR    |
| invalid_tax_calculation       | Tax calculations are incorrect                            | ERROR    |
| invalid_payable_amount        | Payable amount does not match tax inclusive amount        | ERROR    |
| invalid_line_sum              | Line extension amount does not match sum of invoice lines | ERROR    |
| invalid_tax_sum               | Tax amount does not match sum of subtotals                | ERROR    |
| tax_calculation_mismatch      | Tax amount does not match percentage calculation          | WARNING  |
| invalid_reference_irn_format  | Document reference IRN format is invalid                  | ERROR    |
| invalid_reference_date_format | Document reference date format is invalid                 | ERROR    |
| invalid_delivery_period       | Delivery period end date before start date                | ERROR    |
| invalid_payment_means_code    | Payment means code is not valid                           | ERROR    |
| invalid_payment_due_date      | Payment due date format is invalid                        | ERROR    |
| currency_mismatch             | Tax currency code doesn't match document currency code    | WARNING  |

## 7. Validation Best Practices

- Validate invoices early in the process, before submitting to FIRS
- Store validation results for audit purposes
- Use progressive validation to catch errors as early as possible
- Provide clear error messages to help users correct issues
- Allow warnings for non-critical issues that don't prevent submission
- Implement client-side validation for immediate feedback
- Maintain validation rules as configurable entities that can be updated 