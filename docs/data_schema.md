### Data Schema & Models Documentation
This details the database structure, ensuring data integrity and relationships. It includes:
- **Tables and Fields**: Detailed schema with organizations, users, clients, integrations, and logs, each with fields, types, and constraints like NOT NULL and FOREIGN KEY, reflecting the multi-tenant design.
- **Relationships**: Defines one-to-many relationships, e.g., organization to clients, ensuring data consistency, as per the FIRS system's per-client configurations.
- **Validations**: Includes database constraints like UNIQUE for email, ensuring data quality, crucial for compliance with FIRS standards.

## Database Tables

### Authentication and User Management

#### organizations
| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | UUID | PRIMARY KEY | Unique identifier for the organization |
| name | VARCHAR(100) | NOT NULL | Organization name |
| tax_id | VARCHAR(50) | UNIQUE | Tax identification number |
| address | VARCHAR(255) | | Physical address |
| phone | VARCHAR(20) | | Contact phone number |
| email | VARCHAR(100) | | Contact email address |
| website | VARCHAR(255) | | Organization website |
| created_at | TIMESTAMP | NOT NULL, DEFAULT now() | Creation timestamp |
| updated_at | TIMESTAMP | NOT NULL, DEFAULT now() | Last update timestamp |
| status | VARCHAR(20) | NOT NULL, DEFAULT 'active' | Organization status (active, inactive, suspended) |
| firs_service_id | VARCHAR(8) | | FIRS assigned Service ID for IRN generation |

#### users
| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | UUID | PRIMARY KEY | Unique identifier for the user |
| email | VARCHAR(100) | NOT NULL, UNIQUE | User email address |
| password_hash | VARCHAR(255) | NOT NULL | Hashed password |
| first_name | VARCHAR(50) | NOT NULL | User's first name |
| last_name | VARCHAR(50) | NOT NULL | User's last name |
| phone | VARCHAR(20) | | User's phone number |
| is_verified | BOOLEAN | NOT NULL, DEFAULT false | Email verification status |
| created_at | TIMESTAMP | NOT NULL, DEFAULT now() | Account creation timestamp |
| updated_at | TIMESTAMP | NOT NULL, DEFAULT now() | Last update timestamp |
| last_login | TIMESTAMP | | Last login timestamp |
| status | VARCHAR(20) | NOT NULL, DEFAULT 'active' | User status (active, inactive, suspended) |

#### organization_users
| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | UUID | PRIMARY KEY | Unique identifier for the association |
| organization_id | UUID | NOT NULL, FOREIGN KEY (organizations.id) | Organization reference |
| user_id | UUID | NOT NULL, FOREIGN KEY (users.id) | User reference |
| role | VARCHAR(20) | NOT NULL, DEFAULT 'member' | User role in organization (owner, admin, member) |
| created_at | TIMESTAMP | NOT NULL, DEFAULT now() | When user was added to organization |
| updated_at | TIMESTAMP | NOT NULL, DEFAULT now() | Last role update timestamp |

#### api_keys
| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | UUID | PRIMARY KEY | Unique identifier for the API key |
| user_id | UUID | NOT NULL, FOREIGN KEY (users.id) | User who owns the key |
| organization_id | UUID | NOT NULL, FOREIGN KEY (organizations.id) | Associated organization |
| name | VARCHAR(100) | NOT NULL | Description of key purpose |
| key | VARCHAR(100) | NOT NULL, UNIQUE | Hashed API key |
| prefix | VARCHAR(10) | NOT NULL, UNIQUE | Key prefix for display |
| created_at | TIMESTAMP | NOT NULL, DEFAULT now() | Creation timestamp |
| expires_at | TIMESTAMP | | Optional expiration timestamp |
| last_used | TIMESTAMP | | Last usage timestamp |
| status | VARCHAR(20) | NOT NULL, DEFAULT 'active' | Key status (active, revoked) |

#### firs_credentials
| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | UUID | PRIMARY KEY | Unique identifier for the credentials |
| organization_id | UUID | NOT NULL, FOREIGN KEY (organizations.id) | Associated organization |
| api_key | VARCHAR(100) | NOT NULL | FIRS assigned API key (encrypted) |
| secret_key | VARCHAR(100) | NOT NULL | FIRS assigned secret key (encrypted) |
| service_id | VARCHAR(8) | NOT NULL | FIRS assigned Service ID for IRN generation |
| public_key | TEXT | | FIRS provided public key for encryption |
| certificate | TEXT | | FIRS provided certificate for signing |
| created_at | TIMESTAMP | NOT NULL, DEFAULT now() | Creation timestamp |
| updated_at | TIMESTAMP | NOT NULL, DEFAULT now() | Last update timestamp |
| status | VARCHAR(20) | NOT NULL, DEFAULT 'active' | Credentials status |

### Integration Management

#### clients
| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | UUID | PRIMARY KEY | Unique identifier for the client |
| organization_id | UUID | NOT NULL, FOREIGN KEY (organizations.id) | Organization that owns this client |
| name | VARCHAR(100) | NOT NULL | Client business name |
| tax_id | VARCHAR(50) | NOT NULL | Client tax identification number |
| email | VARCHAR(100) | | Client contact email |
| phone | VARCHAR(20) | | Client contact phone |
| address | VARCHAR(255) | | Client business address |
| industry | VARCHAR(50) | | Client industry type |
| created_at | TIMESTAMP | NOT NULL, DEFAULT now() | Creation timestamp |
| updated_at | TIMESTAMP | NOT NULL, DEFAULT now() | Last update timestamp |
| status | VARCHAR(20) | NOT NULL, DEFAULT 'active' | Client status |

#### integrations
| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | UUID | PRIMARY KEY | Unique identifier for the integration |
| client_id | UUID | NOT NULL, FOREIGN KEY (clients.id) | Associated client |
| name | VARCHAR(100) | NOT NULL | Integration name |
| description | TEXT | | Integration description |
| config | JSONB | NOT NULL | Integration configuration (API URLs, auth settings, etc.) |
| created_at | TIMESTAMP | NOT NULL, DEFAULT now() | Creation timestamp |
| updated_at | TIMESTAMP | NOT NULL, DEFAULT now() | Last update timestamp |
| created_by | UUID | FOREIGN KEY (users.id) | User who created the integration |
| last_tested | TIMESTAMP | | Last successful test timestamp |
| status | VARCHAR(20) | NOT NULL, DEFAULT 'configured' | Integration status (configured, active, failed, paused) |

#### integration_history
| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | UUID | PRIMARY KEY | Unique identifier for the history record |
| integration_id | UUID | NOT NULL, FOREIGN KEY (integrations.id) | Integration reference |
| changed_by | UUID | NOT NULL, FOREIGN KEY (users.id) | User who made the change |
| previous_config | JSONB | | Previous configuration |
| new_config | JSONB | NOT NULL | New configuration |
| changed_at | TIMESTAMP | NOT NULL, DEFAULT now() | When change was made |
| change_reason | VARCHAR(255) | | Reason for configuration change |

### Invoice Reference Number Management

#### irn_records
| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| irn | VARCHAR(50) | PRIMARY KEY | Invoice Reference Number (format: InvoiceNumber-ServiceID-YYYYMMDD) |
| integration_id | UUID | NOT NULL, FOREIGN KEY (integrations.id) | Integration that generated the IRN |
| invoice_number | VARCHAR(50) | NOT NULL | Original invoice number from accounting system |
| service_id | VARCHAR(8) | NOT NULL | FIRS assigned Service ID |
| timestamp | VARCHAR(8) | NOT NULL | Date in YYYYMMDD format |
| generated_at | TIMESTAMP | NOT NULL, DEFAULT now() | Generation timestamp |
| valid_until | TIMESTAMP | NOT NULL | Expiration timestamp |
| metadata | JSONB | | Associated invoice metadata |
| status | VARCHAR(20) | NOT NULL, DEFAULT 'unused' | IRN status (unused, used, expired, invalid) |
| used_at | TIMESTAMP | | When the IRN was used |
| invoice_id | VARCHAR(50) | | External invoice ID that used this IRN |

#### irn_quotas
| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | UUID | PRIMARY KEY | Unique identifier for the quota record |
| integration_id | UUID | NOT NULL, FOREIGN KEY (integrations.id) | Associated integration |
| monthly_limit | INTEGER | NOT NULL, DEFAULT 1000 | IRN generation monthly limit |
| current_usage | INTEGER | NOT NULL, DEFAULT 0 | Current month usage count |
| reset_date | DATE | NOT NULL | Next quota reset date |
| created_at | TIMESTAMP | NOT NULL, DEFAULT now() | Creation timestamp |
| updated_at | TIMESTAMP | NOT NULL, DEFAULT now() | Last update timestamp |

### Invoice Validation

#### invoice_records
| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | UUID | PRIMARY KEY | Unique identifier for the invoice |
| organization_id | UUID | NOT NULL, FOREIGN KEY (organizations.id) | Associated organization |
| irn | VARCHAR(50) | NOT NULL, FOREIGN KEY (irn_records.irn) | Invoice Reference Number |
| business_id | UUID | NOT NULL | Business ID from FIRS |
| issue_date | DATE | NOT NULL | Invoice issue date |
| due_date | DATE | | Invoice due date |
| issue_time | TIME | | Invoice issue time |
| invoice_type_code | VARCHAR(10) | NOT NULL | Invoice type code |
| payment_status | VARCHAR(20) | NOT NULL, DEFAULT 'PENDING' | Payment status |
| document_currency_code | VARCHAR(3) | NOT NULL | Currency code |
| tax_currency_code | VARCHAR(3) | | Tax currency code |
| accounting_supplier_party | JSONB | NOT NULL | Supplier information |
| accounting_customer_party | JSONB | NOT NULL | Customer information |
| legal_monetary_total | JSONB | NOT NULL | Invoice monetary totals |
| invoice_lines | JSONB | NOT NULL | Invoice line items |
| note | TEXT | | Invoice note |
| created_at | TIMESTAMP | NOT NULL, DEFAULT now() | Creation timestamp |
| updated_at | TIMESTAMP | NOT NULL, DEFAULT now() | Last update timestamp |
| qr_code | TEXT | | QR code for invoice verification |
| signed_data | TEXT | | Cryptographically signed invoice data |
| status | VARCHAR(20) | NOT NULL, DEFAULT 'created' | Invoice status |

#### validation_rules
| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | UUID | PRIMARY KEY | Unique identifier for the rule |
| name | VARCHAR(100) | NOT NULL | Rule name |
| description | TEXT | | Rule description |
| rule_type | VARCHAR(50) | NOT NULL | Rule type (schema, business_logic, format) |
| field_path | VARCHAR(255) | | JSON path to field being validated (if applicable) |
| validation_logic | JSONB | NOT NULL | Validation logic definition |
| error_message | TEXT | NOT NULL | Error message to display on failure |
| severity | VARCHAR(20) | NOT NULL, DEFAULT 'error' | Rule severity (error, warning, info) |
| created_at | TIMESTAMP | NOT NULL, DEFAULT now() | Creation timestamp |
| updated_at | TIMESTAMP | NOT NULL, DEFAULT now() | Last update timestamp |
| active | BOOLEAN | NOT NULL, DEFAULT true | Whether rule is active |

#### validation_records
| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | UUID | PRIMARY KEY | Unique identifier for validation record |
| integration_id | UUID | NOT NULL, FOREIGN KEY (integrations.id) | Integration reference |
| irn | VARCHAR(50) | FOREIGN KEY (irn_records.irn) | Associated IRN |
| invoice_data | JSONB | NOT NULL | Invoice data that was validated |
| is_valid | BOOLEAN | NOT NULL | Overall validation result |
| validation_time | TIMESTAMP | NOT NULL, DEFAULT now() | Validation timestamp |
| issues | JSONB | | Validation issues found |
| external_id | VARCHAR(100) | | External invoice ID |

### FIRS Reference Data

#### currencies
| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| code | VARCHAR(3) | PRIMARY KEY | Currency code (e.g., NGN) |
| symbol | VARCHAR(10) | NOT NULL | Currency symbol (e.g., ₦) |
| name | VARCHAR(100) | NOT NULL | Currency name (e.g., Nigerian Naira) |
| symbol_native | VARCHAR(10) | NOT NULL | Native currency symbol |
| decimal_digits | INTEGER | NOT NULL | Number of decimal digits |
| rounding | FLOAT | NOT NULL | Rounding precision |
| name_plural | VARCHAR(100) | NOT NULL | Plural name (e.g., Nigerian nairas) |
| last_updated | TIMESTAMP | NOT NULL, DEFAULT now() | Last updated timestamp |

#### invoice_types
| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| code | VARCHAR(10) | PRIMARY KEY | Invoice type code (e.g., 381) |
| value | VARCHAR(100) | NOT NULL | Invoice type name (e.g., Commercial Invoice) |
| description | TEXT | | Detailed description |
| last_updated | TIMESTAMP | NOT NULL, DEFAULT now() | Last updated timestamp |

#### payment_means
| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| code | VARCHAR(10) | PRIMARY KEY | Payment means code (e.g., 10) |
| value | VARCHAR(100) | NOT NULL | Payment method name (e.g., Cash) |
| description | TEXT | | Detailed description |
| last_updated | TIMESTAMP | NOT NULL, DEFAULT now() | Last updated timestamp |

#### product_codes
| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| hscode | VARCHAR(20) | PRIMARY KEY | Harmonized System code |
| description | TEXT | NOT NULL | Product description |
| last_updated | TIMESTAMP | NOT NULL, DEFAULT now() | Last updated timestamp |

#### service_codes
| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| code | VARCHAR(20) | PRIMARY KEY | Service code |
| description | TEXT | NOT NULL | Service description |
| last_updated | TIMESTAMP | NOT NULL, DEFAULT now() | Last updated timestamp |

#### tax_categories
| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| code | VARCHAR(50) | PRIMARY KEY | Tax category code |
| value | VARCHAR(100) | NOT NULL | Tax category name |
| description | TEXT | | Detailed description |
| last_updated | TIMESTAMP | NOT NULL, DEFAULT now() | Last updated timestamp |

#### vat_exemptions
| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | UUID | PRIMARY KEY | Unique identifier |
| heading_no | VARCHAR(20) | NOT NULL | Heading number |
| harmonized_system_code | VARCHAR(20) | NOT NULL | Harmonized System code |
| tariff_category | VARCHAR(100) | NOT NULL | Tariff category |
| tariff | TEXT | NOT NULL | Tariff description |
| description | TEXT | NOT NULL | Detailed description |
| last_updated | TIMESTAMP | NOT NULL, DEFAULT now() | Last updated timestamp |

### Monitoring and Logging

#### transactions
| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | UUID | PRIMARY KEY | Unique transaction identifier |
| integration_id | UUID | NOT NULL, FOREIGN KEY (integrations.id) | Associated integration |
| transaction_type | VARCHAR(50) | NOT NULL | Transaction type (irn_generation, validation, submission) |
| status | VARCHAR(20) | NOT NULL | Transaction status (success, failure, pending) |
| started_at | TIMESTAMP | NOT NULL, DEFAULT now() | Transaction start timestamp |
| completed_at | TIMESTAMP | | Transaction end timestamp |
| details | JSONB | | Transaction details |
| error | TEXT | | Error message if failed |

#### error_logs
| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | UUID | PRIMARY KEY | Unique error identifier |
| integration_id | UUID | FOREIGN KEY (integrations.id) | Associated integration |
| user_id | UUID | FOREIGN KEY (users.id) | Associated user |
| error_type | VARCHAR(50) | NOT NULL | Type of error |
| error_message | TEXT | NOT NULL | Error message |
| stack_trace | TEXT | | Error stack trace |
| occurred_at | TIMESTAMP | NOT NULL, DEFAULT now() | When error occurred |
| request_data | JSONB | | Request data that caused error |
| severity | VARCHAR(20) | NOT NULL, DEFAULT 'error' | Error severity |

#### audit_logs
| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | UUID | PRIMARY KEY | Unique log identifier |
| user_id | UUID | FOREIGN KEY (users.id) | User who performed action |
| organization_id | UUID | FOREIGN KEY (organizations.id) | Associated organization |
| action | VARCHAR(50) | NOT NULL | Action performed |
| entity_type | VARCHAR(50) | NOT NULL | Type of entity affected |
| entity_id | UUID | NOT NULL | ID of entity affected |
| occurred_at | TIMESTAMP | NOT NULL, DEFAULT now() | When action occurred |
| ip_address | VARCHAR(50) | | IP address of requester |
| user_agent | VARCHAR(255) | | User agent information |
| details | JSONB | | Additional details about action |

## Relationships Diagram

```
organizations 1──┐
                 │
                 ├──* organization_users *──1 users
                 │
                 ├──* clients
                 │
                 ├──* api_keys
                 │
                 └──1 firs_credentials
                      
clients 1──* integrations

integrations 1──┬──* integration_history
                │
                ├──* irn_records
                │
                ├──* validation_records
                │
                └──1 irn_quotas

irn_records 1──* invoice_records

validation_records *──1 irn_records

integrations 1──* transactions
```

## FIRS Invoice Schema Requirements

### Invoice Structure
The platform must support the Universal Business Language (UBL) standard for invoices with the following key components:

1. **Header Information**
   - business_id (mandatory): UUID identifier for the business
   - irn (mandatory): Invoice Reference Number in format InvoiceNumber-ServiceID-YYYYMMDD
   - issue_date (mandatory): Date of invoice issuance
   - invoice_type_code (mandatory): Code identifying invoice type (e.g., 381 for Commercial Invoice)
   - document_currency_code (mandatory): Currency code (e.g., NGN)

2. **Party Information**
   - accounting_supplier_party: Seller details including TIN, name, address, contact information
   - accounting_customer_party: Buyer details including TIN, name, address, contact information

3. **Monetary Information**
   - legal_monetary_total (mandatory): Financial totals including line_extension_amount, tax_exclusive_amount, tax_inclusive_amount, payable_amount

4. **Line Items**
   - invoice_line (mandatory): Array of items or services with details like quantity, price, description, and tax information

### IRN Generation Rules
The Invoice Reference Number must follow the format:
- InvoiceNumber-ServiceID-YYYYMMDD
- Example: INV001-94ND90NR-20240611

Where:
- InvoiceNumber: Alphanumeric, no special characters
- ServiceID: 8-character alphanumeric assigned by FIRS
- YYYYMMDD: Date in specified format

### QR Code Requirements
Each validated invoice must contain a QR code that:
- Contains the encrypted IRN and certificate
- Is generated using public key cryptography
- Follows the FIRS signing protocol

## Validation Rules

- Email addresses must be valid format and unique within the system
- Passwords must meet minimum security requirements (8+ chars, mixed case, numbers)
- Tax IDs must follow country-specific format validation
- Integration configurations must pass schema validation before saving
- API keys must be securely hashed before storage
- All sensitive data must be encrypted at rest and in transit
- Every table has a created_at timestamp and most have updated_at timestamps
- IRN numbers must follow the FIRS-specified format
- All actions affecting data are tracked in audit logs
- Invoice validation must check against FIRS schema requirements