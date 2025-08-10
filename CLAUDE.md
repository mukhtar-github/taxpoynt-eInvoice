# TaxPoynt E-Invoice Platform - Development Guide

## Project Overview

TaxPoynt eInvoice is a comprehensive middleware service that facilitates integration between financial software (ERP, CRM, POS) and FIRS (Federal Inland Revenue Service) for electronic invoicing. The platform serves as an Access Point Provider (APP) for Nigerian e-invoicing compliance.

## Company Identity

- TaxPoynt is NOT a payment processor - we are a data collector and invoice generator for compliance purposes.
- **APP Roles and Responsibilities**:
  1. TaxPoynt is the APP (Access Point Provider) - the certified company
  2. APP users are businesses using TaxPoynt's APP service for secure invoice transmission
  3. FIRS Compliance is TaxPoynt's responsibility, not the user's responsibility
  4. Revenue is TaxPoynt's business data, only for admin consumption

## Fundamental Compliance Principle

**TaxPoynt Platform Compliance Focus**: TaxPoynt compliance monitoring focuses on our platform obligations as an Access Point Provider (APP), NOT on customer business compliance tracking.

### FIRS-Mandated Standards for Service Providers
As an APP, TaxPoynt must implement compliance with these 7 regulatory standards:

1. **UBL (Universal Business Language)** - Document format standards
2. **WCO Harmonized System (HS) Code** - World Customs Organization classification
3. **NITDA GDPR & NDPA** - Nigerian data protection requirements  
4. **ISO 20022** - Financial messaging standards
5. **ISO 27001** - Information security management
6. **LEI (Legal Entity Identifier)** - Global entity identification
7. **PEPPOL** - Pan-European Public Procurement Online standards

### Compliance Responsibility Separation

**TaxPoynt's Platform Compliance (Our Responsibility)**:
- APP certification and maintenance
- Secure transmission protocols
- Data integrity and security
- E-invoice format compliance
- Platform infrastructure security
- Audit trails and logging

**Customer's Pre-existing Obligations (Independent of TaxPoynt)**:
- Tax payments and VAT returns (they already know this)
- Company registration and annual filings
- Banking and financial obligations
- Industry-specific business regulations

### Implementation Guidelines

- **Admin-Only Visibility**: Compliance dashboards are visible only to TaxPoynt administrators
- **Customer-Facing Focus**: Customer interfaces focus on service functionality, not compliance monitoring
- **Platform Operations**: Compliance status affects platform operations, not customer operations
- **System-Wide Principle**: Apply this understanding across SI, APP, and Hybrid interfaces

## Development Instructions

When building any compliance-related features:
1. Focus on TaxPoynt's service provider obligations
2. Make compliance monitoring admin-facing
3. Help customers fulfill their existing obligations efficiently
4. Never position TaxPoynt as tracking customer compliance