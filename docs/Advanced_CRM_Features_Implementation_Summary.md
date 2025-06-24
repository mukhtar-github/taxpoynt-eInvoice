# Advanced CRM Features Implementation Summary

## Overview

This document summarizes the implementation of advanced CRM features for the TaxPoynt eInvoice platform, including cross-platform data mapping capabilities, templating system for invoice generation from deals, and pipeline stage tracking for predictive invoicing.

## Implementation Summary

### 1. Cross-Platform Data Mapping Capabilities

**File:** `backend/app/integrations/crm/data_mapper.py`

#### Key Features

- **Universal Field Mapping**: Support for mapping data between HubSpot, Salesforce, Pipedrive, Zoho and custom CRM platforms
- **Advanced Type Conversion**: Handles strings, numbers, dates, emails, phone numbers, currencies, arrays, and objects
- **Transformation Rules**: 13 built-in transformation rules including:
  - Text transformations (uppercase, lowercase, capitalize, strip spaces)
  - Phone formatting with country code support
  - Email formatting and validation
  - Currency conversion with configurable rates
  - Date parsing and formatting
  - Domain extraction from emails
  - Concatenation and splitting operations
  - Custom transformations via registered functions
- **Validation Framework**: Pattern-based validation and required field checking
- **Dot Notation Support**: Navigate nested data structures using dot notation (e.g., `properties.dealname`)
- **Global Transformations**: Apply transformations across entire data structures
- **Custom Transformers**: Register custom transformation functions for specific business logic

#### Supported Field Types

- `STRING` - Text data with transformation support
- `NUMBER` - Integer values with comma handling
- `DECIMAL` - Precise decimal values for financial data
- `BOOLEAN` - Boolean values with flexible input parsing
- `DATE` - Date values with multiple format support
- `DATETIME` - DateTime values with timezone handling
- `EMAIL` - Email addresses with validation
- `PHONE` - Phone numbers with formatting
- `CURRENCY` - Currency values with symbol removal
- `ARRAY` - List data with JSON parsing support
- `OBJECT` - Complex objects with JSON support

#### Platform Mappings

**Default HubSpot Mappings:**
- `properties.dealname` → `deal_title`
- `properties.amount` → `deal_amount`
- `properties.dealstage` → `deal_stage`
- `properties.closedate` → `expected_close_date`
- `properties.createdate` → `created_at_source`
- `id` → `external_deal_id`

**Default Salesforce Mappings:**
- `Name` → `deal_title`
- `Amount` → `deal_amount`
- `StageName` → `deal_stage`
- `CloseDate` → `expected_close_date`
- `CreatedDate` → `created_at_source`
- `Id` → `external_deal_id`
- `Account.Name` → `customer_name`
- `Account.Phone` → `customer_phone` (with phone formatting)

#### Usage Example

```python
from app.integrations.crm.data_mapper import cross_platform_mapper

# Map HubSpot deal to TaxPoynt format
mapped_data = cross_platform_mapper.map_data(
    source_data=hubspot_deal_data,
    source_platform="hubspot",
    target_format="taxpoynt",
    context={"source_currency": "USD", "target_currency": "NGN"}
)

# Register custom platform mapping
from app.integrations.crm.data_mapper import PlatformMapping, FieldMapping, FieldType

custom_mapping = PlatformMapping(
    platform_name="Custom CRM",
    platform_version="1.0",
    field_mappings=[
        FieldMapping("deal_name", "deal_title", FieldType.STRING, required=True),
        FieldMapping("deal_value", "deal_amount", FieldType.DECIMAL)
    ]
)
cross_platform_mapper.register_platform_mapping(custom_mapping)
```

### 2. Templating System for Invoice Generation

**File:** `backend/app/integrations/crm/template_engine.py`

#### Key Features

- **Flexible Templates**: Support for multiple document types:
  - `INVOICE` - Standard invoices
  - `QUOTE` - Price quotations
  - `RECEIPT` - Payment receipts
  - `PROFORMA` - Proforma invoices
  - `CREDIT_NOTE` - Credit notes
  - `CUSTOM` - Custom document types

- **Jinja2 Integration**: Powerful templating engine with custom filters:
  - `currency` - Format currency values (₦, $, €, £)
  - `date` - Format date values with custom patterns
  - `tax` - Calculate tax amounts with configurable rates
  - `round` - Round decimal values to specified places
  - `phone` - Format phone numbers with country codes
  - `domain` - Extract domain from email addresses
  - `conditional` - Conditional value selection
  - `safe_get` - Safe dictionary value retrieval

- **Multi-Platform Support**: Platform-specific templates for:
  - HubSpot with deal properties mapping
  - Salesforce with opportunity mapping
  - Custom CRM platforms

- **Dynamic Content Generation**:
  - Template-driven customer information extraction
  - Configurable line item generation
  - Custom calculation formulas
  - Conditional logic based on deal attributes

- **Multiple Output Formats**:
  - `JSON` - Structured data format
  - `XML` - XML document format
  - `UBL` - Universal Business Language format
  - `PDF` - Portable Document Format (planned)
  - `HTML` - Web-ready format (planned)

#### Template Components

**Invoice Template Structure:**
```python
@dataclass
class InvoiceTemplate:
    template_id: str
    template_name: str
    template_type: TemplateType
    platform: str
    invoice_number_template: str
    description_template: str
    customer_template: CustomerTemplate
    line_items: List[LineItemTemplate]
    currency_code: str = "NGN"
    default_due_days: int = 30
    conditions: Dict[str, Any] = field(default_factory=dict)
```

**Customer Template:**
```python
@dataclass
class CustomerTemplate:
    name_template: str
    email_template: Optional[str] = None
    phone_template: Optional[str] = None
    address_template: Optional[str] = None
    tax_id_template: Optional[str] = None
    company_template: Optional[str] = None
    custom_fields: Dict[str, str] = field(default_factory=dict)
```

**Line Item Template:**
```python
@dataclass
class LineItemTemplate:
    description_template: str
    quantity_source: str = "fixed:1"
    unit_price_source: str = "deal_amount"
    tax_rate: Decimal = Decimal("7.5")
    category: Optional[str] = None
    product_code: Optional[str] = None
    custom_fields: Dict[str, str] = field(default_factory=dict)
```

#### Default Templates

**HubSpot Default Template:**
- Invoice Number: `HUB-{{ deal.id }}-{{ now().strftime('%Y%m') }}`
- Customer Name: `{{ contact.firstname }} {{ contact.lastname }} | {{ company.name }}`
- Description: `{{ deal.properties.dealname | default('HubSpot Deal') }}`
- Condition: `deal.properties.dealstage == 'closedwon'`

**Salesforce Default Template:**
- Invoice Number: `SF-{{ opportunity.Id }}-{{ now().strftime('%Y%m') }}`
- Customer Name: `{{ opportunity.Account.Name }}`
- Description: `{{ opportunity.Name | default('Salesforce Opportunity') }}`
- Condition: `opportunity.StageName == 'Closed Won'`

#### Usage Example

```python
from app.integrations.crm.template_engine import template_engine, OutputFormat

# Generate invoice from deal using template
invoice = template_engine.generate_invoice(
    deal_data=salesforce_opportunity,
    template_id="salesforce_default",
    context={"custom_tax_rate": 10.0},
    output_format=OutputFormat.JSON
)

# Register custom template
from app.integrations.crm.template_engine import InvoiceTemplate, CustomerTemplate, LineItemTemplate

custom_template = InvoiceTemplate(
    template_id="custom_service_invoice",
    template_name="Service Invoice Template",
    template_type=TemplateType.INVOICE,
    platform="hubspot",
    invoice_number_template="SVC-{{ deal.id }}-{{ now().year }}",
    description_template="Professional services for {{ deal.properties.dealname }}",
    customer_template=CustomerTemplate(
        name_template="{{ contact.firstname }} {{ contact.lastname }}",
        email_template="{{ contact.email }}",
        phone_template="{{ contact.phone | phone }}"
    ),
    line_items=[
        LineItemTemplate(
            description_template="Consulting services: {{ deal.properties.dealname }}",
            unit_price_source="deal.properties.amount",
            tax_rate=Decimal("7.5")
        )
    ]
)
template_engine.register_template(custom_template)
```

### 3. Pipeline Stage Tracking for Predictive Invoicing

**File:** `backend/app/integrations/crm/pipeline_tracker.py`

#### Key Features

- **Comprehensive Stage Management**: Track deals through customizable pipeline stages with:
  - Probability percentages for each stage
  - Sequence ordering for logical progression
  - Automatic invoice generation triggers
  - Custom actions and metadata

- **Predictive Analytics**: Advanced algorithms for forecasting:
  - Next stage prediction with confidence percentages
  - Timeline forecasting based on historical patterns
  - Win probability calculation using multiple factors
  - Revenue forecasting with weighted probabilities

- **Velocity Metrics**: Performance analysis including:
  - Stage duration tracking and averages
  - Conversion rates between stages
  - Pipeline velocity scoring
  - Cycle time analysis for completed deals

- **Smart Triggers**: Automatic invoice generation based on:
  - `STAGE_CHANGE` - Deals reaching specific stages
  - `PROBABILITY_THRESHOLD` - High probability deals (>90%)
  - `DATE_BASED` - Time-based triggers
  - `AMOUNT_THRESHOLD` - Large deals (>$50,000)
  - `CUSTOM_RULE` - User-defined business rules
  - `PREDICTIVE` - AI-driven predictions

- **Similar Deal Analysis**: Machine learning approach:
  - Find deals with similar characteristics
  - Analyze historical patterns and outcomes
  - Generate predictions based on comparable data
  - Identify key success/failure factors

#### Stage Definitions

**HubSpot Default Stages:**
- Appointment Scheduled (20% probability)
- Qualified to Buy (40% probability)
- Presentation Scheduled (60% probability)
- Decision Maker Bought In (80% probability)
- Contract Sent (90% probability)
- Closed Won (100% probability, triggers invoice)
- Closed Lost (0% probability)

**Salesforce Default Stages:**
- Prospecting (10% probability)
- Qualification (25% probability)
- Needs Analysis (50% probability)
- Value Proposition (65% probability)
- Id. Decision Makers (75% probability)
- Proposal/Price Quote (85% probability)
- Negotiation/Review (95% probability)
- Closed Won (100% probability, triggers invoice)
- Closed Lost (0% probability)

#### Predictive Insights

**PredictiveInsight Structure:**
```python
@dataclass
class PredictiveInsight:
    deal_id: str
    current_stage: str
    predicted_next_stage: str
    probability_of_transition: Decimal
    predicted_transition_date: datetime
    predicted_close_date: datetime
    win_probability: Decimal
    forecasted_amount: Decimal
    confidence_level: str  # "high", "medium", "low"
    recommendation: str
    factors: List[str]
```

**Pipeline Metrics:**
```python
@dataclass
class PipelineMetrics:
    total_deals: int
    total_value: Decimal
    average_deal_size: Decimal
    conversion_rate: Decimal
    average_cycle_time: timedelta
    stage_conversion_rates: Dict[str, Decimal]
    velocity_metrics: Dict[str, Decimal]
    forecasted_revenue: Decimal
    confidence_score: Decimal
```

#### Usage Example

```python
from app.integrations.crm.pipeline_tracker import get_pipeline_tracker
from decimal import Decimal

# Get platform-specific tracker
tracker = get_pipeline_tracker("salesforce")

# Track stage change
tracker.track_stage_change(
    deal_id="deal_123",
    from_stage="qualification",
    to_stage="proposal",
    deal_amount=Decimal("50000"),
    metadata={"trigger_source": "webhook", "sales_rep": "john.doe"}
)

# Generate predictive insights
insights = tracker.generate_predictive_insights("deal_123")
print(f"Current stage: {insights.current_stage}")
print(f"Predicted next stage: {insights.predicted_next_stage}")
print(f"Win probability: {insights.win_probability}%")
print(f"Predicted close date: {insights.predicted_close_date}")
print(f"Recommendation: {insights.recommendation}")

# Calculate pipeline metrics
metrics = tracker.calculate_pipeline_metrics(days_back=90)
print(f"Total pipeline value: {metrics.total_value}")
print(f"Conversion rate: {metrics.conversion_rate}%")
print(f"Forecasted revenue: {metrics.forecasted_revenue}")

# Register custom stage definition
from app.integrations.crm.pipeline_tracker import StageDefinition, StageType

custom_stage = StageDefinition(
    stage_id="technical_review",
    stage_name="Technical Review",
    stage_type=StageType.QUALIFIED,
    probability=Decimal("55"),
    sequence_order=3,
    generate_invoice=False,
    auto_actions=["send_technical_questionnaire"]
)
tracker.register_stage_definition(custom_stage)
```

## Integration Architecture

### How Components Work Together

1. **Data Flow Pipeline:**
   ```
   CRM Platform → Data Mapper → Normalized Data → Template Engine → Invoice
                                      ↓
                              Pipeline Tracker → Predictive Insights
   ```

2. **Cross-Platform Compatibility:**
   - Data Mapper normalizes different CRM data formats
   - Template Engine uses normalized data for consistent invoice generation
   - Pipeline Tracker provides intelligent timing and automation

3. **Predictive Intelligence:**
   - Historical analysis drives prediction algorithms
   - Similar deal analysis improves accuracy
   - Confidence scoring ensures reliable recommendations

### Benefits

1. **Unified CRM Integration**: Single codebase supports multiple CRM platforms
2. **Intelligent Automation**: Predictive insights drive proactive invoice generation
3. **Flexible Templating**: Customizable invoice generation for different business needs
4. **Revenue Optimization**: Pipeline analytics and forecasting improve sales performance
5. **Scalable Architecture**: Component-based design allows easy extension

### Integration with Existing TaxPoynt Infrastructure

- **Authentication**: Leverages existing JWT and OAuth2 systems
- **Database**: Extends current schema with CRM-specific tables
- **API Layer**: Integrates with existing FastAPI routes
- **Encryption**: Uses existing credential encryption services
- **Monitoring**: Compatible with current logging and metrics systems

## Technical Specifications

### Dependencies

- **Core**: Python 3.8+, FastAPI, SQLAlchemy
- **Templating**: Jinja2 for template processing
- **Data Processing**: Decimal for financial calculations
- **Async Support**: AsyncIO for non-blocking operations
- **Validation**: Pydantic for data validation
- **Encryption**: Cryptography library for secure storage

### Performance Considerations

- **Caching**: Template and metrics caching with configurable TTL
- **Async Processing**: Non-blocking CRM API calls
- **Database Optimization**: Indexed queries for large datasets
- **Memory Management**: Circular buffers for stage history
- **Batch Processing**: Efficient handling of multiple deals

### Security Features

- **Credential Encryption**: All CRM credentials encrypted at rest
- **Data Sanitization**: Input validation and XSS prevention
- **Audit Logging**: Comprehensive tracking of all operations
- **Access Control**: Integration with existing RBAC system
- **Rate Limiting**: Protection against API abuse

## Future Enhancements

### Planned Features

1. **Machine Learning Integration**: Enhanced prediction models using scikit-learn
2. **Advanced Analytics**: Deeper insights with data visualization
3. **Workflow Automation**: Complex business rule execution
4. **Real-time Dashboards**: Live pipeline monitoring
5. **Mobile Optimization**: Mobile-first analytics interface

### Extensibility

- **Plugin Architecture**: Support for custom CRM connectors
- **Custom Transformers**: Business-specific data transformations
- **Template Marketplace**: Shareable invoice templates
- **API Extensions**: RESTful APIs for third-party integration
- **Event System**: Webhooks for external system integration

## Conclusion

The advanced CRM features provide a comprehensive foundation for intelligent invoice generation and revenue optimization. The modular architecture ensures scalability while the predictive capabilities enable proactive business operations. The implementation follows TaxPoynt's existing patterns and integrates seamlessly with the current infrastructure.