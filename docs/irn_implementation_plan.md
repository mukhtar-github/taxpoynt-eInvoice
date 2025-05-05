# TaxPoynt eInvoice - IRN Implementation Plan

This document outlines the comprehensive plan for implementing the Invoice Reference Number (IRN) system that integrates with our OdooRPC integration.

## 1. Comprehensive IRN Implementation Plan

### Phase 1: Core IRN System Design
- **IRN Generation Logic**: Design algorithms for generating unique, secure, and verifiable IRNs
- **OdooRPC Integration Layer**: Create a service that fetches invoice data from Odoo and prepares it for IRN generation
- **IRN Validation Rules**: Define validation rules for invoices before IRN issuance
- **IRN Lifecycle Management**: Implement status tracking (issued, validated, expired, revoked)

### Phase 2: API Development
- **IRN API Endpoints**: Create RESTful endpoints for generating, validating, and querying IRNs
- **Authentication & Authorization**: Implement security controls for API access
- **Rate Limiting & Throttling**: Prevent abuse and ensure system stability

### Phase 3: Testing & Deployment
- **Unit & Integration Tests**: Ensure all components work correctly in isolation and together
- **Performance Testing**: Verify the system can handle expected load
- **Security Testing**: Validate that the system is secure

## 2. Database Schema for IRN Data

We should design models that include:

```python
class InvoiceReferenceNumber(BaseModel):
    id: UUID
    irn_value: str              # The actual IRN string
    invoice_id: int             # Reference to Odoo invoice ID
    odoo_invoice_number: str    # Odoo's invoice number for cross-reference
    status: IRNStatus           # Enum: ACTIVE, EXPIRED, REVOKED
    created_at: datetime
    expires_at: datetime
    issued_by: str              # User who generated the IRN
    verification_code: str      # For validation purposes
    hash_value: str             # Hash of invoice data for verification
    
    # Relationships
    invoice_data: InvoiceData   # Related invoice details
    validation_history: List[IRNValidationRecord]
    
class InvoiceData(BaseModel):
    id: UUID
    irn_id: UUID                # Foreign key to InvoiceReferenceNumber
    invoice_number: str
    invoice_date: date
    customer_name: str
    customer_tax_id: str
    total_amount: Decimal
    currency_code: str
    line_items_hash: str        # Hash of line items for verification
    
class IRNValidationRecord(BaseModel):
    id: UUID
    irn_id: UUID                # Foreign key to InvoiceReferenceNumber
    validation_date: datetime
    validation_status: bool     # True if valid, False if invalid
    validation_message: str     # Details about validation results
    validated_by: str           # User or system that performed validation
```

## 3. Mapping Odoo Invoices to IRN Requirements

We'll need to define how Odoo invoice fields map to IRN requirements:

| IRN Field | Odoo Field | Notes |
|-----------|------------|-------|
| invoice_id | id | Direct mapping |
| odoo_invoice_number | name | For posted invoices only |
| customer_name | partner_id.name | Retrieved via relationship |
| customer_tax_id | partner_id.vat | Tax ID from partner record |
| total_amount | amount_total | Direct mapping |
| currency_code | currency_id.name | Retrieved via relationship |
| invoice_date | invoice_date | Direct mapping |
| line_items | invoice_line_ids | Will need processing to extract details |

## 4. Implementation Considerations

### Technical Considerations
1. **Error Handling**: Robust error handling for Odoo connection issues and data validation
2. **Performance Optimization**: Caching of frequently accessed data
3. **Security**: Ensuring data is secured in transit and at rest
4. **Compliance**: Meeting tax authority requirements for electronic invoicing

### Integration with Existing System
1. **Add the IRN router to the main API router in app.main.py**
2. **Run the tests to verify functionality**
3. **Integrate with the frontend to allow users to generate and manage IRNs**
4. **Add scheduled tasks to automatically expire outdated IRNs**
5. **Create documentation for API endpoints**

### Potential Challenges
1. **Handling Odoo Version Differences**: Ensuring compatibility with different Odoo versions
2. **Tax Configuration Compatibility**: Addressing issues with tax configurations in Odoo
3. **Data Synchronization**: Keeping IRN status in sync with invoice status in Odoo
4. **Performance under Load**: Ensuring the system can handle high volumes of invoice processing

## 5. Next Steps

1. Develop the database models for IRN storage
2. Implement the core IRN generation service
3. Create the OdooRPC integration service for fetching invoice data
4. Develop API endpoints for IRN management
5. Add authentication and authorization mechanisms
6. Implement scheduled tasks for IRN expiration
7. Create comprehensive tests
8. Document the API endpoints and system architecture

## 6. Timeline and Resources

To be determined based on project priorities and available resources.
