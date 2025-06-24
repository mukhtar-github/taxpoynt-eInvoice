"""
Advanced Templating System for Invoice Generation from CRM Deals.

This module provides a flexible and powerful templating system that can generate
invoices from CRM deals using customizable templates, with support for dynamic
content, conditional logic, and multi-format output.
"""

import logging
import json
import re
from typing import Dict, Any, List, Optional, Union, Callable
from datetime import datetime, timedelta
from decimal import Decimal, ROUND_HALF_UP
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
import jinja2
from jinja2 import Environment, DictLoader, select_autoescape

logger = logging.getLogger(__name__)


class TemplateType(str, Enum):
    """Supported template types."""
    INVOICE = "invoice"
    QUOTE = "quote"
    RECEIPT = "receipt"
    PROFORMA = "proforma"
    CREDIT_NOTE = "credit_note"
    CUSTOM = "custom"


class OutputFormat(str, Enum):
    """Supported output formats."""
    JSON = "json"
    XML = "xml"
    UBL = "ubl"
    PDF = "pdf"
    HTML = "html"


@dataclass
class LineItemTemplate:
    """Template for invoice line items."""
    description_template: str
    quantity_source: str = "fixed:1"
    unit_price_source: str = "deal_amount"
    tax_rate: Decimal = Decimal("7.5")
    category: Optional[str] = None
    product_code: Optional[str] = None
    custom_fields: Dict[str, str] = field(default_factory=dict)


@dataclass
class CustomerTemplate:
    """Template for customer information."""
    name_template: str
    email_template: Optional[str] = None
    phone_template: Optional[str] = None
    address_template: Optional[str] = None
    tax_id_template: Optional[str] = None
    company_template: Optional[str] = None
    custom_fields: Dict[str, str] = field(default_factory=dict)


@dataclass
class InvoiceTemplate:
    """Complete invoice template configuration."""
    template_id: str
    template_name: str
    template_type: TemplateType
    platform: str
    
    # Core templates
    invoice_number_template: str
    description_template: str
    customer_template: CustomerTemplate
    line_items: List[LineItemTemplate]
    
    # Financial settings
    currency_code: str = "NGN"
    tax_inclusive: bool = False
    default_due_days: int = 30
    
    # Conditional logic
    conditions: Dict[str, Any] = field(default_factory=dict)
    
    # Metadata
    created_by: Optional[str] = None
    created_at: Optional[datetime] = None
    version: str = "1.0"
    is_active: bool = True
    
    # Custom fields and calculations
    custom_calculations: Dict[str, str] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)


class TemplateEngine:
    """Advanced template engine for invoice generation."""
    
    def __init__(self):
        """Initialize the template engine."""
        self.jinja_env = Environment(
            loader=DictLoader({}),
            autoescape=select_autoescape(['html', 'xml']),
            trim_blocks=True,
            lstrip_blocks=True
        )
        
        # Register custom filters
        self._register_custom_filters()
        
        # Template storage
        self.templates: Dict[str, InvoiceTemplate] = {}
        
        # Load default templates
        self._load_default_templates()
    
    def _register_custom_filters(self):
        """Register custom Jinja2 filters."""
        
        def format_currency(value, currency="NGN", locale="en_NG"):
            """Format currency value."""
            try:
                decimal_value = Decimal(str(value))
                if currency == "NGN":
                    return f"₦{decimal_value:,.2f}"
                elif currency == "USD":
                    return f"${decimal_value:,.2f}"
                elif currency == "EUR":
                    return f"€{decimal_value:,.2f}"
                elif currency == "GBP":
                    return f"£{decimal_value:,.2f}"
                else:
                    return f"{currency} {decimal_value:,.2f}"
            except:
                return str(value)
        
        def format_date(value, format="%Y-%m-%d"):
            """Format date value."""
            if isinstance(value, str):
                try:
                    value = datetime.fromisoformat(value.replace('Z', '+00:00'))
                except:
                    return value
            if isinstance(value, datetime):
                return value.strftime(format)
            return str(value)
        
        def calculate_tax(amount, rate=7.5):
            """Calculate tax amount."""
            try:
                return Decimal(str(amount)) * Decimal(str(rate)) / Decimal("100")
            except:
                return Decimal("0")
        
        def round_decimal(value, places=2):
            """Round decimal to specified places."""
            try:
                return Decimal(str(value)).quantize(Decimal(10) ** -places, rounding=ROUND_HALF_UP)
            except:
                return value
        
        def extract_domain(email):
            """Extract domain from email."""
            if isinstance(email, str) and '@' in email:
                return email.split('@')[1]
            return ""
        
        def format_phone(phone, country_code="+234"):
            """Format phone number."""
            if not phone:
                return ""
            
            # Remove all non-digits except +
            clean_phone = re.sub(r'[^\d+]', '', str(phone))
            
            # Add country code if missing
            if not clean_phone.startswith('+'):
                if clean_phone.startswith('0'):
                    clean_phone = country_code + clean_phone[1:]
                else:
                    clean_phone = country_code + clean_phone
            
            return clean_phone
        
        def conditional(value, condition, true_value, false_value=""):
            """Conditional value selection."""
            if condition:
                return true_value
            return false_value
        
        def safe_get(obj, key, default=""):
            """Safely get value from object."""
            if isinstance(obj, dict):
                return obj.get(key, default)
            return default
        
        # Register filters
        self.jinja_env.filters['currency'] = format_currency
        self.jinja_env.filters['date'] = format_date
        self.jinja_env.filters['tax'] = calculate_tax
        self.jinja_env.filters['round'] = round_decimal
        self.jinja_env.filters['domain'] = extract_domain
        self.jinja_env.filters['phone'] = format_phone
        self.jinja_env.filters['conditional'] = conditional
        self.jinja_env.filters['safe_get'] = safe_get
    
    def _load_default_templates(self):
        """Load default invoice templates."""
        
        # HubSpot Default Template
        hubspot_template = InvoiceTemplate(
            template_id="hubspot_default",
            template_name="HubSpot Default Invoice",
            template_type=TemplateType.INVOICE,
            platform="hubspot",
            invoice_number_template="HUB-{{ deal.id }}-{{ now().strftime('%Y%m') }}",
            description_template="Invoice for {{ deal.properties.dealname | default('HubSpot Deal') }}",
            customer_template=CustomerTemplate(
                name_template="{{ contact.firstname | default('') }} {{ contact.lastname | default('') }} | {{ company.name | default('Unknown Customer') }}",
                email_template="{{ contact.email | default('') }}",
                phone_template="{{ contact.phone | default('') | phone }}",
                address_template="{{ contact.address | default('') }}",
                company_template="{{ company.name | default('') }}"
            ),
            line_items=[
                LineItemTemplate(
                    description_template="{{ deal.properties.dealname | default('Service') }}",
                    quantity_source="fixed:1",
                    unit_price_source="deal.properties.amount",
                    tax_rate=Decimal("7.5")
                )
            ],
            currency_code="NGN",
            default_due_days=30,
            conditions={
                "generate_if": "deal.properties.dealstage == 'closedwon'"
            }
        )
        
        # Salesforce Default Template
        salesforce_template = InvoiceTemplate(
            template_id="salesforce_default",
            template_name="Salesforce Default Invoice",
            template_type=TemplateType.INVOICE,
            platform="salesforce",
            invoice_number_template="SF-{{ opportunity.Id }}-{{ now().strftime('%Y%m') }}",
            description_template="Invoice for {{ opportunity.Name | default('Salesforce Opportunity') }}",
            customer_template=CustomerTemplate(
                name_template="{{ opportunity.Account.Name | default('Unknown Customer') }}",
                phone_template="{{ opportunity.Account.Phone | default('') | phone }}",
                address_template="{{ opportunity.Account.BillingStreet | default('') }}, {{ opportunity.Account.BillingCity | default('') }}, {{ opportunity.Account.BillingState | default('') }}",
                company_template="{{ opportunity.Account.Name | default('') }}"
            ),
            line_items=[
                LineItemTemplate(
                    description_template="{{ opportunity.Name | default('Salesforce Service') }}",
                    quantity_source="fixed:1",
                    unit_price_source="opportunity.Amount",
                    tax_rate=Decimal("7.5")
                )
            ],
            currency_code="USD",
            default_due_days=30,
            conditions={
                "generate_if": "opportunity.StageName == 'Closed Won'"
            }
        )
        
        self.templates["hubspot_default"] = hubspot_template
        self.templates["salesforce_default"] = salesforce_template
    
    def register_template(self, template: InvoiceTemplate):
        """Register a new invoice template."""
        self.templates[template.template_id] = template
        logger.info(f"Registered template: {template.template_id}")
    
    def get_template(self, template_id: str) -> Optional[InvoiceTemplate]:
        """Get a template by ID."""
        return self.templates.get(template_id)
    
    def list_templates(self, platform: Optional[str] = None) -> List[InvoiceTemplate]:
        """List available templates."""
        templates = list(self.templates.values())
        if platform:
            templates = [t for t in templates if t.platform.lower() == platform.lower()]
        return templates
    
    def generate_invoice(
        self,
        deal_data: Dict[str, Any],
        template_id: str,
        context: Optional[Dict[str, Any]] = None,
        output_format: OutputFormat = OutputFormat.JSON
    ) -> Dict[str, Any]:
        """
        Generate invoice from deal data using specified template.
        
        Args:
            deal_data: CRM deal data
            template_id: Template ID to use
            context: Additional context data
            output_format: Output format
            
        Returns:
            Generated invoice data
        """
        if context is None:
            context = {}
        
        template = self.get_template(template_id)
        if not template:
            raise ValueError(f"Template not found: {template_id}")
        
        # Check conditions
        if not self._check_conditions(deal_data, template.conditions, context):
            raise ValueError("Template conditions not met")
        
        # Prepare template context
        template_context = {
            "deal": deal_data,
            "template": template,
            "context": context,
            "now": datetime.now,
            **context
        }
        
        # Generate invoice components
        invoice_data = {
            "invoice_number": self._render_template(template.invoice_number_template, template_context),
            "description": self._render_template(template.description_template, template_context),
            "invoice_date": datetime.now().strftime("%Y-%m-%d"),
            "due_date": (datetime.now() + timedelta(days=template.default_due_days)).strftime("%Y-%m-%d"),
            "currency": template.currency_code,
            "tax_inclusive": template.tax_inclusive,
            
            # Customer information
            "customer": self._generate_customer_info(deal_data, template.customer_template, template_context),
            
            # Line items
            "line_items": self._generate_line_items(deal_data, template.line_items, template_context),
            
            # Metadata
            "template_metadata": {
                "template_id": template.template_id,
                "template_name": template.template_name,
                "platform": template.platform,
                "generated_at": datetime.now().isoformat(),
                "version": template.version
            }
        }
        
        # Calculate totals
        self._calculate_totals(invoice_data)
        
        # Apply custom calculations
        self._apply_custom_calculations(invoice_data, template.custom_calculations, template_context)
        
        # Format output
        if output_format == OutputFormat.JSON:
            return invoice_data
        elif output_format == OutputFormat.UBL:
            return self._convert_to_ubl(invoice_data)
        elif output_format == OutputFormat.XML:
            return self._convert_to_xml(invoice_data)
        else:
            raise ValueError(f"Unsupported output format: {output_format}")
    
    def _render_template(self, template_string: str, context: Dict[str, Any]) -> str:
        """Render a template string with context."""
        try:
            template = self.jinja_env.from_string(template_string)
            return template.render(**context).strip()
        except Exception as e:
            logger.error(f"Template rendering failed: {e}")
            return template_string
    
    def _check_conditions(
        self,
        deal_data: Dict[str, Any],
        conditions: Dict[str, Any],
        context: Dict[str, Any]
    ) -> bool:
        """Check if template conditions are met."""
        if not conditions:
            return True
        
        template_context = {
            "deal": deal_data,
            "context": context,
            **context
        }
        
        for condition_name, condition_expr in conditions.items():
            try:
                # Simple condition evaluation
                if condition_name == "generate_if":
                    result = self._evaluate_condition(condition_expr, template_context)
                    if not result:
                        return False
            except Exception as e:
                logger.warning(f"Condition evaluation failed for '{condition_name}': {e}")
                return False
        
        return True
    
    def _evaluate_condition(self, condition_expr: str, context: Dict[str, Any]) -> bool:
        """Evaluate a condition expression."""
        # Simple condition evaluation (could be enhanced with a proper expression parser)
        template = self.jinja_env.from_string(f"{{{{ {condition_expr} }}}}")
        result = template.render(**context)
        return result.lower() in ('true', '1', 'yes')
    
    def _generate_customer_info(
        self,
        deal_data: Dict[str, Any],
        customer_template: CustomerTemplate,
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Generate customer information from template."""
        customer_info = {}
        
        if customer_template.name_template:
            customer_info["name"] = self._render_template(customer_template.name_template, context)
        
        if customer_template.email_template:
            customer_info["email"] = self._render_template(customer_template.email_template, context)
        
        if customer_template.phone_template:
            customer_info["phone"] = self._render_template(customer_template.phone_template, context)
        
        if customer_template.address_template:
            customer_info["address"] = self._render_template(customer_template.address_template, context)
        
        if customer_template.tax_id_template:
            customer_info["tax_id"] = self._render_template(customer_template.tax_id_template, context)
        
        if customer_template.company_template:
            customer_info["company"] = self._render_template(customer_template.company_template, context)
        
        # Add custom fields
        for field_name, field_template in customer_template.custom_fields.items():
            customer_info[field_name] = self._render_template(field_template, context)
        
        return customer_info
    
    def _generate_line_items(
        self,
        deal_data: Dict[str, Any],
        line_item_templates: List[LineItemTemplate],
        context: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Generate line items from templates."""
        line_items = []
        
        for template in line_item_templates:
            line_item = {}
            
            # Description
            line_item["description"] = self._render_template(template.description_template, context)
            
            # Quantity
            quantity = self._resolve_value_source(template.quantity_source, context)
            line_item["quantity"] = max(1, int(float(quantity) if quantity else 1))
            
            # Unit price
            unit_price = self._resolve_value_source(template.unit_price_source, context)
            line_item["unit_price"] = Decimal(str(unit_price) if unit_price else "0")
            
            # Calculate line total
            line_item["line_total"] = line_item["unit_price"] * line_item["quantity"]
            
            # Tax
            line_item["tax_rate"] = template.tax_rate
            line_item["tax_amount"] = line_item["line_total"] * template.tax_rate / Decimal("100")
            
            # Additional fields
            if template.category:
                line_item["category"] = template.category
            
            if template.product_code:
                line_item["product_code"] = template.product_code
            
            # Custom fields
            for field_name, field_template in template.custom_fields.items():
                line_item[field_name] = self._render_template(field_template, context)
            
            line_items.append(line_item)
        
        return line_items
    
    def _resolve_value_source(self, source: str, context: Dict[str, Any]) -> Any:
        """Resolve value from source specification."""
        if source.startswith("fixed:"):
            return source[6:]
        elif source.startswith("template:"):
            return self._render_template(source[9:], context)
        else:
            # Treat as template expression
            return self._render_template(f"{{{{ {source} }}}}", context)
    
    def _calculate_totals(self, invoice_data: Dict[str, Any]):
        """Calculate invoice totals."""
        line_items = invoice_data.get("line_items", [])
        
        subtotal = Decimal("0")
        tax_total = Decimal("0")
        
        for item in line_items:
            item_total = Decimal(str(item.get("line_total", 0)))
            item_tax = Decimal(str(item.get("tax_amount", 0)))
            
            subtotal += item_total
            tax_total += item_tax
        
        total = subtotal + tax_total
        
        invoice_data["subtotal"] = float(subtotal)
        invoice_data["tax_total"] = float(tax_total)
        invoice_data["total"] = float(total)
    
    def _apply_custom_calculations(
        self,
        invoice_data: Dict[str, Any],
        calculations: Dict[str, str],
        context: Dict[str, Any]
    ):
        """Apply custom calculations to invoice data."""
        # Add invoice data to context for calculations
        calc_context = {**context, "invoice": invoice_data}
        
        for field_name, calculation_expr in calculations.items():
            try:
                result = self._render_template(f"{{{{ {calculation_expr} }}}}", calc_context)
                invoice_data[field_name] = result
            except Exception as e:
                logger.warning(f"Custom calculation '{field_name}' failed: {e}")
    
    def _convert_to_ubl(self, invoice_data: Dict[str, Any]) -> Dict[str, Any]:
        """Convert invoice data to UBL format."""
        # This would implement UBL conversion
        # For now, return the original data with UBL wrapper
        return {
            "ubl_version": "2.1",
            "document_type": "Invoice",
            "invoice_data": invoice_data
        }
    
    def _convert_to_xml(self, invoice_data: Dict[str, Any]) -> str:
        """Convert invoice data to XML format."""
        # Simple XML conversion - could be enhanced
        import xml.etree.ElementTree as ET
        
        root = ET.Element("Invoice")
        
        def dict_to_xml(parent, data):
            for key, value in data.items():
                if isinstance(value, dict):
                    child = ET.SubElement(parent, key)
                    dict_to_xml(child, value)
                elif isinstance(value, list):
                    for item in value:
                        child = ET.SubElement(parent, key[:-1] if key.endswith('s') else key)
                        if isinstance(item, dict):
                            dict_to_xml(child, item)
                        else:
                            child.text = str(item)
                else:
                    child = ET.SubElement(parent, key)
                    child.text = str(value)
        
        dict_to_xml(root, invoice_data)
        return ET.tostring(root, encoding='unicode')
    
    def create_template_from_deal(
        self,
        deal_data: Dict[str, Any],
        platform: str,
        template_name: str
    ) -> InvoiceTemplate:
        """Create a template by analyzing deal data structure."""
        # Analyze deal structure and create a template
        template_id = f"{platform}_{template_name.lower().replace(' ', '_')}"
        
        # Basic template based on common patterns
        template = InvoiceTemplate(
            template_id=template_id,
            template_name=template_name,
            template_type=TemplateType.INVOICE,
            platform=platform,
            invoice_number_template=f"{platform.upper()}-{{{{ deal.id }}}}-{{{{ now().strftime('%Y%m') }}}}",
            description_template="Invoice for {{ deal.name | default('Deal') }}",
            customer_template=CustomerTemplate(
                name_template="{{ customer.name | default('Unknown Customer') }}",
                email_template="{{ customer.email | default('') }}",
                phone_template="{{ customer.phone | default('') | phone }}"
            ),
            line_items=[
                LineItemTemplate(
                    description_template="{{ deal.name | default('Service') }}",
                    unit_price_source="deal.amount"
                )
            ]
        )
        
        return template


# Global template engine instance
template_engine = TemplateEngine()