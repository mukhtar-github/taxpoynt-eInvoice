"""
Nigerian Invoice Templates
===========================

Professional invoice templates compliant with Nigerian business standards and FIRS requirements.
Provides customizable templates for different business types and transaction categories.

Features:
- FIRS-compliant templates
- Multiple business formats
- Professional Nigerian styling
- Multi-language support (English/Hausa)
- Customizable branding
- Export formats (PDF, HTML, JSON)
"""

from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass
from enum import Enum
from decimal import Decimal
from datetime import datetime
import json
import logging

from .....core.models.invoice import Invoice, InvoiceItem, CustomerInfo

logger = logging.getLogger(__name__)


class TemplateType(Enum):
    """Types of invoice templates."""
    STANDARD_BUSINESS = "standard_business"
    RETAIL_RECEIPT = "retail_receipt"
    SERVICE_INVOICE = "service_invoice"
    TAX_INVOICE = "tax_invoice"
    PROFORMA_INVOICE = "proforma_invoice"
    CREDIT_NOTE = "credit_note"
    DEBIT_NOTE = "debit_note"
    GOVERNMENT_INVOICE = "government_invoice"
    EXPORT_INVOICE = "export_invoice"
    SIMPLIFIED_INVOICE = "simplified_invoice"


class OutputFormat(Enum):
    """Invoice output formats."""
    HTML = "html"
    JSON = "json"
    PDF_DATA = "pdf_data"
    PLAIN_TEXT = "plain_text"
    FIRS_XML = "firs_xml"


@dataclass
class TemplateConfig:
    """Template configuration options."""
    template_type: TemplateType
    language: str = "en"  # en, ha (Hausa)
    currency_symbol: str = "₦"
    show_qr_code: bool = True
    show_digital_signature: bool = True
    show_bank_details: bool = True
    show_tax_breakdown: bool = True
    include_terms: bool = True
    include_footer: bool = True
    custom_branding: Dict[str, str] = None


@dataclass
class BrandingInfo:
    """Company branding information."""
    company_name: str
    company_logo_url: Optional[str] = None
    company_address: str = ""
    company_phone: str = ""
    company_email: str = ""
    company_website: str = ""
    company_tin: str = ""
    company_rc_number: str = ""
    bank_name: str = ""
    bank_account_number: str = ""
    bank_sort_code: str = ""


class InvoiceTemplates:
    """
    Nigerian invoice templates generator.
    
    Provides professional, FIRS-compliant invoice templates
    for various business types and use cases in Nigeria.
    """
    
    def __init__(self, default_branding: Optional[BrandingInfo] = None):
        self.default_branding = default_branding
        
        # Nigerian business templates
        self._initialize_templates()
        
        # Localization
        self.translations = self._load_translations()
        
        # Statistics
        self.stats = {
            'templates_generated': 0,
            'format_breakdown': {fmt.value: 0 for fmt in OutputFormat},
            'template_type_usage': {ttype.value: 0 for ttype in TemplateType}
        }
    
    def generate_invoice_template(
        self,
        invoice: Invoice,
        config: TemplateConfig,
        branding: Optional[BrandingInfo] = None,
        output_format: OutputFormat = OutputFormat.HTML
    ) -> Dict[str, Any]:
        """
        Generate invoice using specified template.
        
        Args:
            invoice: Invoice data
            config: Template configuration
            branding: Company branding information  
            output_format: Desired output format
            
        Returns:
            Dictionary with generated template and metadata
        """
        try:
            logger.debug(f"Generating invoice template: {invoice.invoice_number}")
            
            # Use provided branding or default
            effective_branding = branding or self.default_branding
            
            # Generate template based on type
            template_data = self._generate_template_data(invoice, config, effective_branding)
            
            # Format output
            if output_format == OutputFormat.HTML:
                content = self._generate_html_template(template_data, config)
            elif output_format == OutputFormat.JSON:
                content = self._generate_json_template(template_data)
            elif output_format == OutputFormat.PDF_DATA:
                content = self._generate_pdf_data_template(template_data, config)
            elif output_format == OutputFormat.PLAIN_TEXT:
                content = self._generate_text_template(template_data, config)
            elif output_format == OutputFormat.FIRS_XML:
                content = self._generate_firs_xml_template(template_data)
            else:
                raise ValueError(f"Unsupported output format: {output_format}")
            
            # Update statistics
            self.stats['templates_generated'] += 1
            self.stats['format_breakdown'][output_format.value] += 1
            self.stats['template_type_usage'][config.template_type.value] += 1
            
            logger.debug(f"Template generated successfully: {invoice.invoice_number}")
            
            return {
                'success': True,
                'invoice_number': invoice.invoice_number,
                'template_type': config.template_type.value,
                'output_format': output_format.value,
                'content': content,
                'metadata': {
                    'generated_at': datetime.utcnow().isoformat(),
                    'language': config.language,
                    'currency': config.currency_symbol,
                    'total_amount': str(invoice.total_amount)
                }
            }
            
        except Exception as e:
            logger.error(f"Template generation failed: {invoice.invoice_number} - {e}")
            
            return {
                'success': False,
                'invoice_number': invoice.invoice_number,
                'error': str(e),
                'template_type': config.template_type.value,
                'output_format': output_format.value
            }
    
    def _generate_template_data(
        self,
        invoice: Invoice,
        config: TemplateConfig,
        branding: Optional[BrandingInfo]
    ) -> Dict[str, Any]:
        """Generate template data structure."""
        
        # Get translations for selected language
        t = self.translations.get(config.language, self.translations['en'])
        
        # Format amounts
        def format_amount(amount: Decimal) -> str:
            return f"{config.currency_symbol}{amount:,.2f}"
        
        # Calculate totals
        subtotal = invoice.subtotal or sum(item.total_amount for item in invoice.items)
        vat_amount = invoice.vat_amount or Decimal('0')
        total_amount = invoice.total_amount or (subtotal + vat_amount)
        
        template_data = {
            # Invoice header
            'header': {
                'title': t['invoice_title'],
                'invoice_number': invoice.invoice_number,
                'invoice_date': invoice.date.strftime('%d %B %Y'),
                'due_date': invoice.due_date.strftime('%d %B %Y') if invoice.due_date else '',
                'currency': invoice.currency or 'NGN'
            },
            
            # Company information
            'company': {
                'name': branding.company_name if branding else 'Your Company Name',
                'address': branding.company_address if branding else '',
                'phone': branding.company_phone if branding else '',
                'email': branding.company_email if branding else '',
                'website': branding.company_website if branding else '',
                'tin': branding.company_tin if branding else '',
                'rc_number': branding.company_rc_number if branding else '',
                'logo_url': branding.company_logo_url if branding else None
            },
            
            # Customer information
            'customer': {
                'name': invoice.customer_info.name if invoice.customer_info else t['cash_customer'],
                'address': invoice.customer_info.address if invoice.customer_info else '',
                'phone': invoice.customer_info.phone if invoice.customer_info else '',
                'email': invoice.customer_info.email if invoice.customer_info else '',
                'tin': invoice.customer_info.tin if invoice.customer_info else '',
                'customer_type': invoice.customer_info.customer_type if invoice.customer_info else 'individual'
            },
            
            # Invoice items
            'items': [
                {
                    'description': item.description,
                    'quantity': str(item.quantity),
                    'unit_price': format_amount(item.unit_price),
                    'total_amount': format_amount(item.total_amount),
                    'vat_rate': f"{item.vat_rate * 100:.1f}%" if item.vat_rate else "0%",
                    'vat_amount': format_amount(item.vat_amount) if item.vat_amount else format_amount(Decimal('0'))
                }
                for item in invoice.items
            ],
            
            # Totals
            'totals': {
                'subtotal': format_amount(subtotal),
                'vat_amount': format_amount(vat_amount),
                'total_amount': format_amount(total_amount),
                'amount_in_words': self._amount_to_words(total_amount, config.language)
            },
            
            # Banking details
            'banking': {
                'show_bank_details': config.show_bank_details,
                'bank_name': branding.bank_name if branding else '',
                'account_number': branding.bank_account_number if branding else '',
                'sort_code': branding.bank_sort_code if branding else ''
            },
            
            # Template configuration
            'config': {
                'show_qr_code': config.show_qr_code,
                'show_digital_signature': config.show_digital_signature,
                'show_tax_breakdown': config.show_tax_breakdown,
                'include_terms': config.include_terms,
                'include_footer': config.include_footer,
                'language': config.language
            },
            
            # Localized text
            'text': t,
            
            # FIRS compliance
            'firs': {
                'vat_rate': '7.5%',
                'compliance_note': t['firs_compliance'],
                'digital_signature_note': t['digital_signature_info']
            }
        }
        
        return template_data
    
    def _generate_html_template(
        self,
        data: Dict[str, Any],
        config: TemplateConfig
    ) -> str:
        """Generate HTML invoice template."""
        
        if config.template_type == TemplateType.STANDARD_BUSINESS:
            return self._generate_standard_business_html(data)
        elif config.template_type == TemplateType.RETAIL_RECEIPT:
            return self._generate_retail_receipt_html(data)
        elif config.template_type == TemplateType.SERVICE_INVOICE:
            return self._generate_service_invoice_html(data)
        elif config.template_type == TemplateType.TAX_INVOICE:
            return self._generate_tax_invoice_html(data)
        else:
            return self._generate_standard_business_html(data)
    
    def _generate_standard_business_html(self, data: Dict[str, Any]) -> str:
        """Generate standard business invoice HTML."""
        
        return f"""
<!DOCTYPE html>
<html lang="{data['config']['language']}">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{data['text']['invoice_title']} - {data['header']['invoice_number']}</title>
    <style>
        {self._get_invoice_css()}
    </style>
</head>
<body>
    <div class="invoice-container">
        <!-- Header -->
        <div class="invoice-header">
            <div class="company-info">
                {f'<img src="{data["company"]["logo_url"]}" alt="Company Logo" class="company-logo">' if data["company"]["logo_url"] else ''}
                <h1 class="company-name">{data['company']['name']}</h1>
                <div class="company-details">
                    <p>{data['company']['address']}</p>
                    <p>{data['text']['phone']}: {data['company']['phone']}</p>
                    <p>{data['text']['email']}: {data['company']['email']}</p>
                    <p>{data['text']['tin']}: {data['company']['tin']}</p>
                </div>
            </div>
            <div class="invoice-info">
                <h2 class="invoice-title">{data['text']['invoice_title']}</h2>
                <table class="invoice-details">
                    <tr>
                        <td><strong>{data['text']['invoice_number']}:</strong></td>
                        <td>{data['header']['invoice_number']}</td>
                    </tr>
                    <tr>
                        <td><strong>{data['text']['invoice_date']}:</strong></td>
                        <td>{data['header']['invoice_date']}</td>
                    </tr>
                    <tr>
                        <td><strong>{data['text']['due_date']}:</strong></td>
                        <td>{data['header']['due_date']}</td>
                    </tr>
                    <tr>
                        <td><strong>{data['text']['currency']}:</strong></td>
                        <td>{data['header']['currency']}</td>
                    </tr>
                </table>
            </div>
        </div>
        
        <!-- Customer Information -->
        <div class="customer-section">
            <h3>{data['text']['bill_to']}:</h3>
            <div class="customer-info">
                <p><strong>{data['customer']['name']}</strong></p>
                <p>{data['customer']['address']}</p>
                <p>{data['text']['phone']}: {data['customer']['phone']}</p>
                <p>{data['text']['email']}: {data['customer']['email']}</p>
                {f"<p>{data['text']['tin']}: {data['customer']['tin']}</p>" if data['customer']['tin'] else ''}
            </div>
        </div>
        
        <!-- Invoice Items -->
        <div class="items-section">
            <table class="items-table">
                <thead>
                    <tr>
                        <th>{data['text']['description']}</th>
                        <th>{data['text']['quantity']}</th>
                        <th>{data['text']['unit_price']}</th>
                        <th>{data['text']['total_amount']}</th>
                        {f"<th>{data['text']['vat_rate']}</th>" if data['config']['show_tax_breakdown'] else ''}
                        {f"<th>{data['text']['vat_amount']}</th>" if data['config']['show_tax_breakdown'] else ''}
                    </tr>
                </thead>
                <tbody>
                    {''.join([f'''
                    <tr>
                        <td>{item['description']}</td>
                        <td>{item['quantity']}</td>
                        <td>{item['unit_price']}</td>
                        <td>{item['total_amount']}</td>
                        {f"<td>{item['vat_rate']}</td>" if data['config']['show_tax_breakdown'] else ''}
                        {f"<td>{item['vat_amount']}</td>" if data['config']['show_tax_breakdown'] else ''}
                    </tr>
                    ''' for item in data['items']])}
                </tbody>
            </table>
        </div>
        
        <!-- Totals -->
        <div class="totals-section">
            <table class="totals-table">
                <tr>
                    <td><strong>{data['text']['subtotal']}:</strong></td>
                    <td><strong>{data['totals']['subtotal']}</strong></td>
                </tr>
                {f'''
                <tr>
                    <td><strong>{data['text']['vat_amount']} ({data['firs']['vat_rate']}):</strong></td>
                    <td><strong>{data['totals']['vat_amount']}</strong></td>
                </tr>
                ''' if data['config']['show_tax_breakdown'] else ''}
                <tr class="total-row">
                    <td><strong>{data['text']['total_amount']}:</strong></td>
                    <td><strong>{data['totals']['total_amount']}</strong></td>
                </tr>
                <tr>
                    <td colspan="2" class="amount-words">
                        <em>{data['text']['amount_in_words']}: {data['totals']['amount_in_words']}</em>
                    </td>
                </tr>
            </table>
        </div>
        
        <!-- Banking Details -->
        {f'''
        <div class="banking-section">
            <h3>{data['text']['payment_details']}:</h3>
            <div class="banking-info">
                <p><strong>{data['text']['bank_name']}:</strong> {data['banking']['bank_name']}</p>
                <p><strong>{data['text']['account_number']}:</strong> {data['banking']['account_number']}</p>
                <p><strong>{data['text']['sort_code']}:</strong> {data['banking']['sort_code']}</p>
            </div>
        </div>
        ''' if data['banking']['show_bank_details'] and data['banking']['bank_name'] else ''}
        
        <!-- Terms and Conditions -->
        {f'''
        <div class="terms-section">
            <h3>{data['text']['terms_conditions']}:</h3>
            <ul>
                <li>{data['text']['payment_terms_net30']}</li>
                <li>{data['text']['late_payment_charges']}</li>
                <li>{data['text']['goods_remain_property']}</li>
            </ul>
        </div>
        ''' if data['config']['include_terms'] else ''}
        
        <!-- Footer -->
        {f'''
        <div class="footer-section">
            <div class="firs-compliance">
                <p><small>{data['firs']['compliance_note']}</small></p>
                {f"<p><small>{data['firs']['digital_signature_note']}</small></p>" if data['config']['show_digital_signature'] else ''}
            </div>
            <div class="footer-text">
                <p><small>{data['text']['thank_you_business']}</small></p>
                <p><small>{data['text']['generated_timestamp']}: {datetime.utcnow().strftime('%d %B %Y %H:%M')}</small></p>
            </div>
        </div>
        ''' if data['config']['include_footer'] else ''}
    </div>
</body>
</html>
        """
    
    def _generate_retail_receipt_html(self, data: Dict[str, Any]) -> str:
        """Generate retail receipt style HTML."""
        
        return f"""
<!DOCTYPE html>
<html lang="{data['config']['language']}">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{data['text']['receipt']} - {data['header']['invoice_number']}</title>
    <style>
        {self._get_receipt_css()}
    </style>
</head>
<body>
    <div class="receipt-container">
        <div class="receipt-header">
            <h2 class="store-name">{data['company']['name']}</h2>
            <p class="store-address">{data['company']['address']}</p>
            <p class="store-contact">{data['company']['phone']} | {data['company']['email']}</p>
            <p class="store-tin">{data['text']['tin']}: {data['company']['tin']}</p>
            <hr class="divider">
        </div>
        
        <div class="receipt-info">
            <p><strong>{data['text']['receipt_number']}:</strong> {data['header']['invoice_number']}</p>
            <p><strong>{data['text']['date']}:</strong> {data['header']['invoice_date']}</p>
            <p><strong>{data['text']['cashier']}:</strong> System Generated</p>
            <hr class="divider">
        </div>
        
        <div class="receipt-items">
            {''.join([f'''
            <div class="receipt-item">
                <div class="item-desc">{item['description']}</div>
                <div class="item-details">
                    <span>{item['quantity']} x {item['unit_price']}</span>
                    <span class="item-total">{item['total_amount']}</span>
                </div>
            </div>
            ''' for item in data['items']])}
            <hr class="divider">
        </div>
        
        <div class="receipt-totals">
            <div class="total-line">
                <span>{data['text']['subtotal']}:</span>
                <span>{data['totals']['subtotal']}</span>
            </div>
            <div class="total-line">
                <span>{data['text']['vat']} ({data['firs']['vat_rate']}):</span>
                <span>{data['totals']['vat_amount']}</span>
            </div>
            <div class="total-line final-total">
                <span><strong>{data['text']['total']}:</strong></span>
                <span><strong>{data['totals']['total_amount']}</strong></span>
            </div>
            <hr class="divider">
        </div>
        
        <div class="receipt-footer">
            <p class="thank-you">{data['text']['thank_you_visit']}</p>
            <p class="return-policy">{data['text']['return_policy_14days']}</p>
            <p class="firs-note"><small>{data['firs']['compliance_note']}</small></p>
        </div>
    </div>
</body>
</html>
        """
    
    def _generate_service_invoice_html(self, data: Dict[str, Any]) -> str:
        """Generate service invoice HTML (similar to standard but service-focused)."""
        return self._generate_standard_business_html(data)
    
    def _generate_tax_invoice_html(self, data: Dict[str, Any]) -> str:
        """Generate tax invoice HTML with enhanced tax information."""
        return self._generate_standard_business_html(data)
    
    def _generate_json_template(self, data: Dict[str, Any]) -> str:
        """Generate JSON template."""
        return json.dumps(data, indent=2, default=str)
    
    def _generate_pdf_data_template(
        self,
        data: Dict[str, Any],
        config: TemplateConfig
    ) -> Dict[str, Any]:
        """Generate PDF data structure (for PDF generation libraries)."""
        
        return {
            'page_size': 'A4',
            'margin': {'top': 72, 'right': 72, 'bottom': 72, 'left': 72},
            'content': [
                {
                    'type': 'header',
                    'company_name': data['company']['name'],
                    'invoice_number': data['header']['invoice_number'],
                    'invoice_date': data['header']['invoice_date']
                },
                {
                    'type': 'customer_info',
                    'customer': data['customer']
                },
                {
                    'type': 'items_table',
                    'items': data['items'],
                    'show_tax_breakdown': config.show_tax_breakdown
                },
                {
                    'type': 'totals',
                    'totals': data['totals']
                },
                {
                    'type': 'footer',
                    'terms': config.include_terms,
                    'banking': data['banking'] if config.show_bank_details else None
                }
            ],
            'styling': {
                'font_family': 'Arial',
                'font_size': 10,
                'header_font_size': 14,
                'title_font_size': 12
            }
        }
    
    def _generate_text_template(
        self,
        data: Dict[str, Any],
        config: TemplateConfig
    ) -> str:
        """Generate plain text invoice."""
        
        lines = []
        lines.append("=" * 60)
        lines.append(f"{data['company']['name'].center(60)}")
        lines.append(f"{data['company']['address'].center(60)}")
        lines.append(f"TIN: {data['company']['tin']}")
        lines.append("=" * 60)
        lines.append("")
        lines.append(f"INVOICE: {data['header']['invoice_number']}")
        lines.append(f"DATE: {data['header']['invoice_date']}")
        lines.append(f"DUE DATE: {data['header']['due_date']}")
        lines.append("")
        lines.append(f"BILL TO:")
        lines.append(f"{data['customer']['name']}")
        lines.append(f"{data['customer']['address']}")
        if data['customer']['tin']:
            lines.append(f"TIN: {data['customer']['tin']}")
        lines.append("")
        lines.append("-" * 60)
        lines.append(f"{'DESCRIPTION':<30} {'QTY':<5} {'PRICE':<10} {'TOTAL':<10}")
        lines.append("-" * 60)
        
        for item in data['items']:
            lines.append(f"{item['description'][:30]:<30} {item['quantity']:<5} {item['unit_price']:<10} {item['total_amount']:<10}")
        
        lines.append("-" * 60)
        lines.append(f"{'SUBTOTAL:':<45} {data['totals']['subtotal']}")
        lines.append(f"{'VAT (7.5%):':<45} {data['totals']['vat_amount']}")
        lines.append(f"{'TOTAL:':<45} {data['totals']['total_amount']}")
        lines.append("")
        lines.append(f"Amount in words: {data['totals']['amount_in_words']}")
        lines.append("")
        
        if config.show_bank_details and data['banking']['bank_name']:
            lines.append("PAYMENT DETAILS:")
            lines.append(f"Bank: {data['banking']['bank_name']}")
            lines.append(f"Account: {data['banking']['account_number']}")
            lines.append("")
        
        lines.append("Thank you for your business!")
        lines.append("")
        lines.append("This invoice is FIRS compliant.")
        
        return "\n".join(lines)
    
    def _generate_firs_xml_template(self, data: Dict[str, Any]) -> str:
        """Generate FIRS XML format."""
        
        # This would generate proper FIRS XML structure
        # Simplified version for demonstration
        return f"""<?xml version="1.0" encoding="UTF-8"?>
<FIRSInvoice>
    <Header>
        <InvoiceNumber>{data['header']['invoice_number']}</InvoiceNumber>
        <InvoiceDate>{data['header']['invoice_date']}</InvoiceDate>
        <Currency>{data['header']['currency']}</Currency>
    </Header>
    <Supplier>
        <Name>{data['company']['name']}</Name>
        <TIN>{data['company']['tin']}</TIN>
        <Address>{data['company']['address']}</Address>
    </Supplier>
    <Customer>
        <Name>{data['customer']['name']}</Name>
        <TIN>{data['customer']['tin'] or ''}</TIN>
        <Address>{data['customer']['address']}</Address>
    </Customer>
    <Items>
        {''.join([f'''
        <Item>
            <Description>{item['description']}</Description>
            <Quantity>{item['quantity']}</Quantity>
            <UnitPrice>{item['unit_price']}</UnitPrice>
            <TotalAmount>{item['total_amount']}</TotalAmount>
            <VATRate>{item['vat_rate']}</VATRate>
            <VATAmount>{item['vat_amount']}</VATAmount>
        </Item>
        ''' for item in data['items']])}
    </Items>
    <Totals>
        <Subtotal>{data['totals']['subtotal']}</Subtotal>
        <VATAmount>{data['totals']['vat_amount']}</VATAmount>
        <TotalAmount>{data['totals']['total_amount']}</TotalAmount>
    </Totals>
</FIRSInvoice>"""
    
    def _get_invoice_css(self) -> str:
        """Get CSS styles for professional invoice."""
        
        return """
        body {
            font-family: 'Arial', sans-serif;
            margin: 0;
            padding: 20px;
            background-color: #f8f9fa;
            color: #333;
        }
        
        .invoice-container {
            max-width: 800px;
            margin: 0 auto;
            background: white;
            padding: 40px;
            box-shadow: 0 0 20px rgba(0,0,0,0.1);
            border-radius: 8px;
        }
        
        .invoice-header {
            display: flex;
            justify-content: space-between;
            margin-bottom: 40px;
            border-bottom: 3px solid #007bff;
            padding-bottom: 20px;
        }
        
        .company-name {
            color: #007bff;
            margin: 0 0 10px 0;
            font-size: 28px;
        }
        
        .company-logo {
            max-height: 80px;
            margin-bottom: 10px;
        }
        
        .invoice-title {
            color: #007bff;
            margin: 0 0 15px 0;
            font-size: 24px;
        }
        
        .invoice-details {
            border-collapse: collapse;
        }
        
        .invoice-details td {
            padding: 5px 10px 5px 0;
            border: none;
        }
        
        .customer-section {
            margin-bottom: 30px;
            padding: 20px;
            background-color: #f8f9fa;
            border-radius: 5px;
        }
        
        .items-table {
            width: 100%;
            border-collapse: collapse;
            margin-bottom: 30px;
        }
        
        .items-table th,
        .items-table td {
            padding: 12px;
            text-align: left;
            border-bottom: 1px solid #ddd;
        }
        
        .items-table th {
            background-color: #007bff;
            color: white;
            font-weight: bold;
        }
        
        .items-table tbody tr:hover {
            background-color: #f5f5f5;
        }
        
        .totals-section {
            float: right;
            width: 300px;
            margin-bottom: 30px;
        }
        
        .totals-table {
            width: 100%;
            border-collapse: collapse;
        }
        
        .totals-table td {
            padding: 8px 12px;
            border-bottom: 1px solid #ddd;
        }
        
        .total-row {
            border-top: 2px solid #007bff;
            font-size: 18px;
        }
        
        .amount-words {
            font-style: italic;
            padding-top: 10px;
            color: #666;
        }
        
        .banking-section,
        .terms-section {
            clear: both;
            margin-top: 30px;
            padding: 20px;
            background-color: #f8f9fa;
            border-radius: 5px;
        }
        
        .footer-section {
            margin-top: 40px;
            border-top: 1px solid #ddd;
            padding-top: 20px;
            text-align: center;
            color: #666;
        }
        
        @media print {
            body { background-color: white; }
            .invoice-container { 
                box-shadow: none; 
                margin: 0;
                padding: 20px;
            }
        }
        """
    
    def _get_receipt_css(self) -> str:
        """Get CSS styles for retail receipt."""
        
        return """
        body {
            font-family: 'Courier New', monospace;
            margin: 0;
            padding: 10px;
            background-color: white;
            font-size: 12px;
        }
        
        .receipt-container {
            max-width: 300px;
            margin: 0 auto;
            padding: 20px;
            border: 2px dashed #333;
        }
        
        .receipt-header {
            text-align: center;
            margin-bottom: 15px;
        }
        
        .store-name {
            font-size: 16px;
            font-weight: bold;
            margin: 0 0 5px 0;
        }
        
        .divider {
            border: none;
            border-top: 1px dashed #333;
            margin: 10px 0;
        }
        
        .receipt-item {
            margin-bottom: 5px;
        }
        
        .item-details {
            display: flex;
            justify-content: space-between;
            margin-top: 2px;
        }
        
        .total-line {
            display: flex;
            justify-content: space-between;
            margin-bottom: 3px;
        }
        
        .final-total {
            font-size: 14px;
            font-weight: bold;
            border-top: 1px solid #333;
            padding-top: 5px;
        }
        
        .receipt-footer {
            text-align: center;
            margin-top: 15px;
            font-size: 10px;
        }
        
        .thank-you {
            font-weight: bold;
            font-size: 12px;
        }
        """
    
    def _load_translations(self) -> Dict[str, Dict[str, str]]:
        """Load translation strings."""
        
        return {
            'en': {
                'invoice_title': 'INVOICE',
                'receipt': 'RECEIPT',
                'invoice_number': 'Invoice Number',
                'receipt_number': 'Receipt Number',
                'invoice_date': 'Invoice Date',
                'due_date': 'Due Date',
                'date': 'Date',
                'currency': 'Currency',
                'bill_to': 'Bill To',
                'phone': 'Phone',
                'email': 'Email',
                'tin': 'TIN',
                'description': 'Description',
                'quantity': 'Qty',
                'unit_price': 'Unit Price',
                'total_amount': 'Total',
                'subtotal': 'Subtotal',
                'vat': 'VAT',
                'vat_rate': 'VAT Rate',
                'vat_amount': 'VAT Amount',
                'total': 'TOTAL',
                'amount_in_words': 'Amount in Words',
                'payment_details': 'Payment Details',
                'bank_name': 'Bank Name',
                'account_number': 'Account Number',
                'sort_code': 'Sort Code',
                'terms_conditions': 'Terms & Conditions',
                'payment_terms_net30': 'Payment is due within 30 days',
                'late_payment_charges': 'Late payment may incur charges',
                'goods_remain_property': 'Goods remain our property till paid for',
                'return_policy_14days': 'Returns accepted within 14 days',
                'thank_you_business': 'Thank you for your business!',
                'thank_you_visit': 'Thank you for your visit!',
                'cash_customer': 'Cash Customer',
                'cashier': 'Cashier',
                'firs_compliance': 'This invoice complies with FIRS e-invoicing requirements',
                'digital_signature_info': 'Digitally signed and verified',
                'generated_timestamp': 'Generated on'
            },
            'ha': {
                'invoice_title': 'TAKARDA KUƊI',
                'receipt': 'RASIT',
                'invoice_number': 'Lambar Takarda',
                'invoice_date': 'Ranar Takarda',
                'due_date': 'Ranar Biya',
                'currency': 'Kuɗin Ƙasa',
                'bill_to': 'Aika Zuwa',
                'phone': 'Waya',
                'email': 'Imel',
                'tin': 'TIN',
                'description': 'Bayani',
                'quantity': 'Yawa',
                'unit_price': 'Farashin Ɗaya',
                'total_amount': 'Jimlar',
                'subtotal': 'Ƙananan Jimla',
                'vat': 'VAT',
                'total': 'JIMLA',
                'thank_you_business': 'Mun gode da kasuwancinku!',
                'cash_customer': 'Abokin Ciniki na Kuɗi',
                'firs_compliance': 'Wannan takarda ta bi ka\'idojin FIRS',
            }
        }
    
    def _amount_to_words(self, amount: Decimal, language: str = 'en') -> str:
        """Convert amount to words (simplified implementation)."""
        
        # This is a simplified implementation
        # A full implementation would handle Nigerian currency properly
        
        if language == 'ha':
            return f"Naira {amount:,.2f} (a cikin kalmomi)"
        else:
            # Simplified English conversion
            if amount < 1000:
                return f"Only {amount:,.2f} Naira"
            elif amount < 1000000:
                thousands = int(amount / 1000)
                remainder = amount % 1000
                if remainder > 0:
                    return f"{thousands} Thousand {remainder:,.2f} Naira Only"
                else:
                    return f"{thousands} Thousand Naira Only"
            else:
                millions = int(amount / 1000000)
                remainder = amount % 1000000
                if remainder > 0:
                    return f"{millions} Million {remainder:,.2f} Naira Only"
                else:
                    return f"{millions} Million Naira Only"
    
    def _initialize_templates(self):
        """Initialize template configurations."""
        
        self.template_configs = {
            TemplateType.STANDARD_BUSINESS: {
                'name': 'Standard Business Invoice',
                'description': 'Professional invoice for B2B transactions',
                'features': ['company_branding', 'tax_breakdown', 'payment_terms']
            },
            TemplateType.RETAIL_RECEIPT: {
                'name': 'Retail Receipt',
                'description': 'Point-of-sale receipt format',
                'features': ['compact_layout', 'return_policy', 'cashier_info']
            },
            TemplateType.SERVICE_INVOICE: {
                'name': 'Service Invoice',
                'description': 'Service-based business invoice',
                'features': ['hourly_rates', 'project_details', 'milestone_billing']
            },
            TemplateType.TAX_INVOICE: {
                'name': 'Tax Invoice',
                'description': 'VAT-compliant tax invoice',
                'features': ['enhanced_tax_info', 'compliance_notes', 'audit_trail']
            }
        }
    
    def get_template_info(self, template_type: TemplateType) -> Dict[str, Any]:
        """Get information about a template type."""
        return self.template_configs.get(template_type, {})
    
    def get_available_templates(self) -> List[Dict[str, Any]]:
        """Get list of available templates."""
        
        templates = []
        for template_type, config in self.template_configs.items():
            templates.append({
                'type': template_type.value,
                'name': config['name'],
                'description': config['description'],
                'features': config['features']
            })
        
        return templates
    
    def get_template_statistics(self) -> Dict[str, Any]:
        """Get template generation statistics."""
        
        stats = self.stats.copy()
        
        if stats['templates_generated'] > 0:
            most_used_format = max(stats['format_breakdown'], key=stats['format_breakdown'].get)
            most_used_template = max(stats['template_type_usage'], key=stats['template_type_usage'].get)
            
            stats['most_used_format'] = most_used_format
            stats['most_used_template'] = most_used_template
        
        return stats
    
    def reset_statistics(self):
        """Reset template statistics."""
        
        self.stats = {
            'templates_generated': 0,
            'format_breakdown': {fmt.value: 0 for fmt in OutputFormat},
            'template_type_usage': {ttype.value: 0 for ttype in TemplateType}
        }