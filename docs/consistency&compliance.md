Maintaining consistency and compliance between the e-invoices generated from ERP systems (starting with Odoo) and the official FIRS requirements documented in E_Invoice_Collection.md is critical for successful certification and operation.

Let me expand on this important point:
1. **Single Source of Truth**: The FIRS specification (documented in E_Invoice_Collection.md) must be the authoritative reference for all invoice structures. Any invoice generated from any integrated ERP system needs to strictly adhere to these specifications.

2. **Data Mapping Layer**: What we've implemented with the Odoo integration templates (particularly the IRN field mappings) serves as a translation layer between:
- Odoo's native invoice data model
- FIRS's required e-invoice format

3. **Validation Before Submission**: Our validate_invoice method in the FIRS service acts as a pre-submission check to ensure that transformed invoices meet all FIRS requirements before attempting to sign them.

4. **Consistent Invoice Reference Numbers**: The IRN system we've implemented ensures that invoices across all ERP sources maintain consistent and unique identification, which is crucial for the FIRS reconciliation process.

5. **Centralized FIRS Integration**: By centralizing the FIRS API communication through our service, we can ensure that regardless of the source ERP system, all e-invoices follow the same validation, signing, and submission process.

This approach gives us several advantages:
- Reduces compliance risk across different ERP integrations
- Centralizes the validation logic in one place
- Makes it easier to adapt to FIRS specification changes
- Provides a single audit trail for all e-invoice submissions
