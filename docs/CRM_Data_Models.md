# TaxPoynt CRM Integration - Data Models Documentation

## Overview

This document provides comprehensive documentation for all data models used in the TaxPoynt CRM integration system. These models define the structure for CRM connections, deals, customer data, and invoice transformations.

## Table of Contents

1. [Core Models](#core-models)
2. [Database Schema](#database-schema)
3. [API Schema Models](#api-schema-models)
4. [Validation Rules](#validation-rules)
5. [Data Transformations](#data-transformations)
6. [Security Considerations](#security-considerations)

## Core Models

### CRMConnection Model

The main model representing a connection to a CRM system.

```python
class CRMConnection(Base):
    __tablename__ = "crm_connections"
    
    # Primary identification
    id = Column(String, primary_key=True, default=lambda: str(uuid4()))
    organization_id = Column(String, ForeignKey("organizations.id"), nullable=False)
    
    # Connection details
    crm_type = Column(Enum(CRMType), nullable=False)  # hubspot, salesforce, etc.
    connection_name = Column(String(100), nullable=False)
    
    # Authentication and configuration
    credentials = Column(EncryptedJSON, nullable=False)  # Encrypted JSON field
    connection_settings = Column(JSON, nullable=True)
    
    # Status and metadata
    status = Column(Enum(ConnectionStatus), default=ConnectionStatus.PENDING)
    webhook_url = Column(String(500), nullable=True)
    webhook_secret = Column(String(100), nullable=True)
    
    # Synchronization tracking
    last_sync = Column(DateTime, nullable=True)
    last_successful_sync = Column(DateTime, nullable=True)
    sync_frequency = Column(Enum(SyncFrequency), default=SyncFrequency.DAILY)
    
    # Statistics
    total_deals = Column(Integer, default=0)
    total_invoices = Column(Integer, default=0)
    sync_error_count = Column(Integer, default=0)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    organization = relationship("Organization", back_populates="crm_connections")
    deals = relationship("CRMDeal", back_populates="connection", cascade="all, delete-orphan")
```

#### Field Descriptions

| Field | Type | Description | Constraints |
|-------|------|-------------|-------------|
| `id` | String | Unique identifier | UUID format, Primary key |
| `organization_id` | String | Organization owner | Foreign key, Not null |
| `crm_type` | Enum | Type of CRM system | hubspot, salesforce, pipedrive, zoho |
| `connection_name` | String | Display name | Max 100 chars, Not null |
| `credentials` | EncryptedJSON | Authentication data | Encrypted at rest |
| `connection_settings` | JSON | Configuration options | Nullable |
| `status` | Enum | Connection status | pending, connected, failed, etc. |
| `webhook_url` | String | Webhook endpoint URL | Max 500 chars |
| `webhook_secret` | String | Webhook verification secret | Max 100 chars |
| `last_sync` | DateTime | Last sync attempt | Nullable |
| `total_deals` | Integer | Number of synced deals | Default 0 |

#### Credentials Structure

```json
{
  "client_id": "string",
  "client_secret": "encrypted_string",
  "refresh_token": "encrypted_string",
  "access_token": "encrypted_string",
  "expires_at": "datetime",
  "scope": "string"
}
```

#### Connection Settings Structure

```json
{
  "auto_sync": true,
  "sync_frequency": "daily",
  "deal_stage_mapping": {
    "closedwon": "generate_invoice",
    "proposal": "create_draft",
    "negotiation": "no_action"
  },
  "auto_generate_invoice_on_creation": false,
  "default_currency": "NGN",
  "webhook_events": ["deal.creation", "deal.propertyChange"],
  "filters": {
    "minimum_deal_amount": 1000,
    "excluded_stages": ["closedlost"],
    "date_range_days": 365
  },
  "invoice_settings": {
    "default_due_days": 30,
    "default_tax_rate": 7.5,
    "line_item_template": "{{deal_title}} - {{deal_stage}}"
  }
}
```

### CRMDeal Model

Represents a deal synchronized from a CRM system.

```python
class CRMDeal(Base):
    __tablename__ = "crm_deals"
    
    # Primary identification
    id = Column(String, primary_key=True, default=lambda: str(uuid4()))
    connection_id = Column(String, ForeignKey("crm_connections.id"), nullable=False)
    external_deal_id = Column(String(100), nullable=False)  # ID from CRM system
    
    # Deal information
    deal_title = Column(String(200), nullable=True)
    deal_amount = Column(String(50), nullable=True)  # Stored as string for precision
    deal_currency = Column(String(3), default="NGN")
    deal_stage = Column(String(100), nullable=True)
    deal_probability = Column(Float, nullable=True)
    
    # Customer information
    customer_data = Column(JSON, nullable=True)
    
    # Additional deal data
    deal_data = Column(JSON, nullable=True)  # Raw CRM data
    
    # Invoice tracking
    invoice_generated = Column(Boolean, default=False)
    invoice_data = Column(JSON, nullable=True)
    invoice_generation_attempts = Column(Integer, default=0)
    
    # Timestamps from CRM
    created_at_source = Column(DateTime, nullable=True)
    updated_at_source = Column(DateTime, nullable=True)
    closed_at_source = Column(DateTime, nullable=True)
    
    # Synchronization tracking
    last_sync = Column(DateTime, default=datetime.utcnow)
    sync_status = Column(Enum(SyncStatus), default=SyncStatus.SUCCESS)
    sync_error = Column(Text, nullable=True)
    
    # Local timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    connection = relationship("CRMConnection", back_populates="deals")
    
    # Constraints
    __table_args__ = (
        UniqueConstraint('connection_id', 'external_deal_id', name='unique_deal_per_connection'),
        Index('idx_deal_stage', 'deal_stage'),
        Index('idx_invoice_generated', 'invoice_generated'),
        Index('idx_last_sync', 'last_sync'),
    )
```

#### Customer Data Structure

```json
{
  "name": "John Doe",
  "email": "john.doe@example.com",
  "phone": "+2341234567890",
  "company": "Acme Corporation",
  "title": "CEO",
  "address": {
    "street": "123 Business Avenue",
    "city": "Lagos",
    "state": "Lagos",
    "country": "Nigeria",
    "postal_code": "100001"
  },
  "custom_fields": {
    "industry": "Technology",
    "company_size": "50-100",
    "lead_source": "Website"
  }
}
```

#### Deal Data Structure

```json
{
  "source": "website",
  "owner": {
    "id": "owner_123",
    "name": "Sales Rep Name",
    "email": "rep@company.com"
  },
  "pipeline": "sales-pipeline",
  "expected_close_date": "2023-12-31T00:00:00Z",
  "actual_close_date": "2023-12-25T10:30:00Z",
  "deal_type": "new_business",
  "products": [
    {
      "name": "Product A",
      "quantity": 2,
      "unit_price": 25000
    }
  ],
  "notes": "Important enterprise client",
  "tags": ["enterprise", "priority"],
  "custom_properties": {
    "lead_score": 95,
    "qualification_status": "qualified"
  }
}
```

#### Invoice Data Structure

```json
{
  "invoice_id": "uuid",
  "invoice_number": "HUB-123456789",
  "generated_at": "2023-12-20T15:30:00Z",
  "firs_submission_status": "pending",
  "irn": "IRN123456789",
  "validation_status": "passed",
  "submission_attempts": 1,
  "last_submission_error": null
}
```

## Database Schema

### Enums

```python
class CRMType(str, Enum):
    HUBSPOT = "hubspot"
    SALESFORCE = "salesforce"
    PIPEDRIVE = "pipedrive"
    ZOHO = "zoho"
    CUSTOM = "custom"

class ConnectionStatus(str, Enum):
    PENDING = "pending"
    CONNECTING = "connecting"
    CONNECTED = "connected"
    FAILED = "failed"
    DISCONNECTED = "disconnected"
    EXPIRED = "expired"

class SyncFrequency(str, Enum):
    HOURLY = "hourly"
    DAILY = "daily"
    WEEKLY = "weekly"
    MANUAL = "manual"

class SyncStatus(str, Enum):
    SUCCESS = "success"
    FAILED = "failed"
    PENDING = "pending"
    PARTIAL = "partial"
```

### Database Indexes

```sql
-- Performance indexes for common queries
CREATE INDEX idx_crm_connections_org_id ON crm_connections(organization_id);
CREATE INDEX idx_crm_connections_status ON crm_connections(status);
CREATE INDEX idx_crm_connections_last_sync ON crm_connections(last_sync);

CREATE INDEX idx_crm_deals_connection_id ON crm_deals(connection_id);
CREATE INDEX idx_crm_deals_external_id ON crm_deals(external_deal_id);
CREATE INDEX idx_crm_deals_stage ON crm_deals(deal_stage);
CREATE INDEX idx_crm_deals_invoice_generated ON crm_deals(invoice_generated);
CREATE INDEX idx_crm_deals_amount ON crm_deals(CAST(deal_amount AS DECIMAL));
CREATE INDEX idx_crm_deals_last_sync ON crm_deals(last_sync);

-- Composite indexes for common filter combinations
CREATE INDEX idx_deals_connection_stage ON crm_deals(connection_id, deal_stage);
CREATE INDEX idx_deals_connection_invoice ON crm_deals(connection_id, invoice_generated);
CREATE INDEX idx_deals_sync_status ON crm_deals(connection_id, sync_status, last_sync);
```

## API Schema Models

### Request Models

#### CRMConnectionCreate

```python
class CRMConnectionCreate(BaseModel):
    crm_type: CRMType
    connection_name: str = Field(..., min_length=1, max_length=100)
    credentials: Dict[str, Any]
    connection_settings: Optional[Dict[str, Any]] = None
    webhook_secret: Optional[str] = Field(None, max_length=100)
    
    class Config:
        json_encoders = {
            CRMType: lambda v: v.value
        }
```

#### CRMConnectionUpdate

```python
class CRMConnectionUpdate(BaseModel):
    connection_name: Optional[str] = Field(None, min_length=1, max_length=100)
    connection_settings: Optional[Dict[str, Any]] = None
    status: Optional[ConnectionStatus] = None
    webhook_secret: Optional[str] = Field(None, max_length=100)
```

#### DealProcessingRequest

```python
class DealProcessingRequest(BaseModel):
    action: str = Field(..., regex="^(generate_invoice|create_draft|validate_only)$")
    force_regenerate: bool = False
    invoice_settings: Optional[Dict[str, Any]] = None
    
    class Config:
        schema_extra = {
            "example": {
                "action": "generate_invoice",
                "force_regenerate": False,
                "invoice_settings": {
                    "currency": "NGN",
                    "due_days": 30,
                    "tax_rate": 7.5
                }
            }
        }
```

### Response Models

#### CRMConnectionResponse

```python
class CRMConnectionResponse(BaseModel):
    id: str
    organization_id: str
    crm_type: CRMType
    connection_name: str
    status: ConnectionStatus
    webhook_url: Optional[str]
    last_sync: Optional[datetime]
    total_deals: int
    total_invoices: int
    created_at: datetime
    updated_at: datetime
    
    # Exclude sensitive fields
    class Config:
        orm_mode = True
        exclude = {"credentials", "webhook_secret"}
```

#### CRMDealResponse

```python
class CRMDealResponse(BaseModel):
    id: str
    connection_id: str
    external_deal_id: str
    deal_title: Optional[str]
    deal_amount: Optional[str]
    deal_currency: str
    deal_stage: Optional[str]
    customer_data: Optional[Dict[str, Any]]
    invoice_generated: bool
    invoice_data: Optional[Dict[str, Any]]
    created_at_source: Optional[datetime]
    updated_at_source: Optional[datetime]
    last_sync: datetime
    sync_status: SyncStatus
    
    class Config:
        orm_mode = True
```

#### PaginatedDealsResponse

```python
class PaginatedDealsResponse(BaseModel):
    deals: List[CRMDealResponse]
    pagination: PaginationMetadata
    filters_applied: Optional[Dict[str, Any]]
    
    class Config:
        schema_extra = {
            "example": {
                "deals": [],
                "pagination": {
                    "page": 1,
                    "page_size": 20,
                    "total": 150,
                    "pages": 8,
                    "has_next": True,
                    "has_prev": False
                },
                "filters_applied": {
                    "deal_stage": "closedwon",
                    "invoice_generated": False
                }
            }
        }
```

## Validation Rules

### CRMConnection Validation

```python
def validate_crm_credentials(crm_type: CRMType, credentials: Dict[str, Any]) -> Dict[str, Any]:
    """Validate CRM credentials based on type."""
    
    validation_rules = {
        CRMType.HUBSPOT: {
            "required_fields": ["client_id", "client_secret"],
            "optional_fields": ["authorization_code", "refresh_token", "access_token"]
        },
        CRMType.SALESFORCE: {
            "required_fields": ["client_id", "client_secret", "username"],
            "optional_fields": ["security_token", "sandbox"]
        },
        CRMType.PIPEDRIVE: {
            "required_fields": ["api_token"],
            "optional_fields": ["company_domain"]
        }
    }
    
    rules = validation_rules.get(crm_type)
    if not rules:
        raise ValueError(f"Unsupported CRM type: {crm_type}")
    
    # Validate required fields
    for field in rules["required_fields"]:
        if field not in credentials or not credentials[field]:
            raise ValueError(f"Missing required credential: {field}")
    
    # Validate field formats
    if "client_id" in credentials and len(credentials["client_id"]) < 10:
        raise ValueError("Client ID must be at least 10 characters")
    
    if "email" in credentials:
        email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        if not re.match(email_pattern, credentials["email"]):
            raise ValueError("Invalid email format")
    
    return credentials

def validate_connection_settings(settings: Dict[str, Any]) -> Dict[str, Any]:
    """Validate connection settings."""
    
    if not isinstance(settings, dict):
        raise ValueError("Connection settings must be a dictionary")
    
    # Validate deal stage mapping
    if "deal_stage_mapping" in settings:
        mapping = settings["deal_stage_mapping"]
        if not isinstance(mapping, dict):
            raise ValueError("Deal stage mapping must be a dictionary")
        
        valid_actions = ["generate_invoice", "create_draft", "no_action"]
        for stage, action in mapping.items():
            if action not in valid_actions:
                raise ValueError(f"Invalid action '{action}' for stage '{stage}'")
    
    # Validate currency
    if "default_currency" in settings:
        valid_currencies = ["NGN", "USD", "EUR", "GBP"]
        if settings["default_currency"] not in valid_currencies:
            raise ValueError(f"Invalid currency: {settings['default_currency']}")
    
    # Validate sync frequency
    if "sync_frequency" in settings:
        valid_frequencies = ["hourly", "daily", "weekly", "manual"]
        if settings["sync_frequency"] not in valid_frequencies:
            raise ValueError(f"Invalid sync frequency: {settings['sync_frequency']}")
    
    return settings
```

### CRMDeal Validation

```python
def validate_deal_amount(amount: str) -> bool:
    """Validate deal amount format."""
    try:
        decimal_amount = Decimal(amount)
        return decimal_amount >= 0 and decimal_amount <= Decimal('999999999.99')
    except (ValueError, InvalidOperation):
        return False

def validate_customer_data(customer_data: Dict[str, Any]) -> Dict[str, Any]:
    """Validate customer data structure."""
    
    if not isinstance(customer_data, dict):
        raise ValueError("Customer data must be a dictionary")
    
    # Validate email if provided
    if "email" in customer_data and customer_data["email"]:
        email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        if not re.match(email_pattern, customer_data["email"]):
            raise ValueError("Invalid email format in customer data")
    
    # Validate phone if provided
    if "phone" in customer_data and customer_data["phone"]:
        phone = customer_data["phone"].replace(" ", "").replace("-", "").replace("(", "").replace(")", "")
        if not phone.startswith("+") or len(phone) < 10:
            raise ValueError("Invalid phone format in customer data")
    
    # Validate required name field
    if "name" not in customer_data or not customer_data["name"]:
        if "company" not in customer_data or not customer_data["company"]:
            raise ValueError("Customer data must include either 'name' or 'company'")
    
    return customer_data
```

## Data Transformations

### Deal to Invoice Transformation

```python
class DealToInvoiceTransformer:
    """Transforms CRM deal data into invoice format."""
    
    @staticmethod
    def transform_hubspot_deal(deal_data: Dict[str, Any], customer_data: Dict[str, Any]) -> Dict[str, Any]:
        """Transform HubSpot deal to invoice format."""
        
        properties = deal_data.get("properties", {})
        
        # Extract deal information
        deal_id = deal_data.get("id")
        deal_name = properties.get("dealname", "")
        deal_amount = properties.get("amount", "0")
        deal_stage = properties.get("dealstage", "")
        close_date = properties.get("closedate")
        
        # Parse amount
        try:
            amount = float(deal_amount) if deal_amount else 0.0
        except (ValueError, TypeError):
            amount = 0.0
        
        # Generate invoice number
        invoice_number = f"HUB-{deal_id}"
        
        # Create line items
        line_items = [
            {
                "description": deal_name or f"Service for Deal {deal_id}",
                "quantity": 1,
                "unit_price": amount,
                "total": amount,
                "tax_rate": 7.5,  # Default VAT rate
                "tax_amount": amount * 0.075
            }
        ]
        
        # Calculate totals
        subtotal = amount
        tax_total = subtotal * 0.075
        total = subtotal + tax_total
        
        # Transform customer data
        customer = {
            "name": customer_data.get("name") or customer_data.get("company", ""),
            "email": customer_data.get("email", ""),
            "phone": customer_data.get("phone", ""),
            "address": customer_data.get("address", {}),
            "tax_id": customer_data.get("tax_id", ""),
            "company": customer_data.get("company", "")
        }
        
        # Create invoice data
        invoice_data = {
            "invoice_number": invoice_number,
            "description": f"Invoice for {deal_name}",
            "currency": "NGN",
            "subtotal": subtotal,
            "tax_total": tax_total,
            "total": total,
            "due_date": close_date or (datetime.utcnow() + timedelta(days=30)).isoformat(),
            "customer": customer,
            "line_items": line_items,
            "metadata": {
                "source": "hubspot",
                "deal_id": deal_id,
                "deal_stage": deal_stage,
                "transformed_at": datetime.utcnow().isoformat()
            }
        }
        
        return invoice_data
    
    @staticmethod
    def transform_salesforce_opportunity(opportunity_data: Dict[str, Any]) -> Dict[str, Any]:
        """Transform Salesforce opportunity to invoice format."""
        # Similar transformation logic for Salesforce
        pass
```

### Data Sanitization

```python
class DataSanitizer:
    """Sanitizes data from external CRM systems."""
    
    @staticmethod
    def sanitize_string(value: str, max_length: int = None) -> str:
        """Sanitize string input."""
        if not isinstance(value, str):
            return ""
        
        # Remove potential XSS content
        value = value.replace("<script", "").replace("javascript:", "")
        
        # Remove SQL injection patterns
        dangerous_patterns = ["DROP TABLE", "DELETE FROM", "UPDATE SET", "--", "/*", "*/"]
        for pattern in dangerous_patterns:
            value = value.replace(pattern, "")
        
        # Trim whitespace
        value = value.strip()
        
        # Apply length limit
        if max_length and len(value) > max_length:
            value = value[:max_length]
        
        return value
    
    @staticmethod
    def sanitize_amount(value: Any) -> str:
        """Sanitize monetary amounts."""
        if value is None:
            return "0"
        
        # Convert to string and remove non-numeric characters except decimal point
        str_value = str(value).replace(",", "").replace("$", "").replace("€", "").replace("£", "")
        
        # Validate decimal format
        try:
            decimal_value = Decimal(str_value)
            return str(decimal_value)
        except (ValueError, InvalidOperation):
            return "0"
    
    @staticmethod
    def sanitize_email(email: str) -> str:
        """Sanitize email addresses."""
        if not email or not isinstance(email, str):
            return ""
        
        email = email.strip().lower()
        
        # Basic email format validation
        email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        if re.match(email_pattern, email):
            return email
        
        return ""
```

## Security Considerations

### Credential Encryption

```python
class CredentialEncryption:
    """Handles encryption of sensitive credential data."""
    
    @staticmethod
    def encrypt_credentials(credentials: Dict[str, Any]) -> Dict[str, Any]:
        """Encrypt sensitive credential fields."""
        
        sensitive_fields = [
            "client_secret",
            "refresh_token",
            "access_token",
            "api_token",
            "security_token",
            "private_key"
        ]
        
        encrypted_credentials = credentials.copy()
        
        for field in sensitive_fields:
            if field in encrypted_credentials and encrypted_credentials[field]:
                # Use your encryption service
                encrypted_value = encryption_service.encrypt(encrypted_credentials[field])
                encrypted_credentials[field] = encrypted_value
        
        return encrypted_credentials
    
    @staticmethod
    def decrypt_credentials(encrypted_credentials: Dict[str, Any]) -> Dict[str, Any]:
        """Decrypt sensitive credential fields."""
        
        sensitive_fields = [
            "client_secret",
            "refresh_token",
            "access_token",
            "api_token",
            "security_token",
            "private_key"
        ]
        
        decrypted_credentials = encrypted_credentials.copy()
        
        for field in sensitive_fields:
            if field in decrypted_credentials and decrypted_credentials[field]:
                # Use your encryption service
                decrypted_value = encryption_service.decrypt(decrypted_credentials[field])
                decrypted_credentials[field] = decrypted_value
        
        return decrypted_credentials
```

### Data Masking for Logs

```python
class DataMasker:
    """Masks sensitive data for logging and debugging."""
    
    @staticmethod
    def mask_credentials(credentials: Dict[str, Any]) -> Dict[str, Any]:
        """Mask credentials for safe logging."""
        
        sensitive_fields = [
            "client_secret",
            "refresh_token",
            "access_token",
            "api_token",
            "password",
            "webhook_secret"
        ]
        
        masked = credentials.copy()
        
        for field in sensitive_fields:
            if field in masked and masked[field]:
                value = masked[field]
                if len(value) > 8:
                    masked[field] = value[:4] + "*" * (len(value) - 8) + value[-4:]
                else:
                    masked[field] = "*" * len(value)
        
        return masked
    
    @staticmethod
    def mask_customer_data(customer_data: Dict[str, Any]) -> Dict[str, Any]:
        """Mask personal customer data for logging."""
        
        sensitive_fields = ["email", "phone", "tax_id"]
        
        masked = customer_data.copy()
        
        for field in sensitive_fields:
            if field in masked and masked[field]:
                value = masked[field]
                if field == "email" and "@" in value:
                    username, domain = value.split("@", 1)
                    masked_username = username[:2] + "*" * (len(username) - 2) if len(username) > 2 else "*" * len(username)
                    masked[field] = f"{masked_username}@{domain}"
                elif field == "phone":
                    masked[field] = value[:3] + "*" * (len(value) - 6) + value[-3:] if len(value) > 6 else "*" * len(value)
                else:
                    masked[field] = "*" * len(value)
        
        return masked
```

### Audit Trail

```python
class CRMAuditLogger:
    """Logs CRM operations for audit trail."""
    
    @staticmethod
    def log_connection_created(connection_id: str, organization_id: str, crm_type: str, user_id: str):
        """Log CRM connection creation."""
        audit_log.info(
            "CRM connection created",
            extra={
                "event_type": "crm_connection_created",
                "connection_id": connection_id,
                "organization_id": organization_id,
                "crm_type": crm_type,
                "user_id": user_id,
                "timestamp": datetime.utcnow().isoformat()
            }
        )
    
    @staticmethod
    def log_deal_processed(deal_id: str, connection_id: str, action: str, result: str):
        """Log deal processing events."""
        audit_log.info(
            "Deal processed",
            extra={
                "event_type": "deal_processed",
                "deal_id": deal_id,
                "connection_id": connection_id,
                "action": action,
                "result": result,
                "timestamp": datetime.utcnow().isoformat()
            }
        )
    
    @staticmethod
    def log_sync_operation(connection_id: str, deals_synced: int, duration: float, status: str):
        """Log synchronization operations."""
        audit_log.info(
            "Sync operation completed",
            extra={
                "event_type": "sync_operation",
                "connection_id": connection_id,
                "deals_synced": deals_synced,
                "duration_seconds": duration,
                "status": status,
                "timestamp": datetime.utcnow().isoformat()
            }
        )
```

This comprehensive data models documentation provides a complete reference for all CRM integration data structures, validation rules, transformations, and security considerations. It serves as a guide for developers implementing CRM integrations and for maintaining data consistency across the platform.