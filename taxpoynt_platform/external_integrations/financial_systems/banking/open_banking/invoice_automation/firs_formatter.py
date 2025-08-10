"""
FIRS Formatter
==============

Formats invoices into FIRS-compliant e-invoice structure for submission.
Handles Nigerian e-invoicing requirements and validation.

Features:
- FIRS JSON format generation
- QR code generation for invoices
- Digital signature integration
- Validation against FIRS schema
- Batch formatting capabilities
"""

from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass, asdict
from decimal import Decimal
from datetime import datetime
import json
import uuid
import base64
import logging

from .....core.models.invoice import Invoice, InvoiceItem
from .....core.exceptions import FormattingError, ValidationError
from .....core.utils.qr_generator import QRCodeGenerator
from .....core.utils.digital_signature import DigitalSigner

logger = logging.getLogger(__name__)


@dataclass
class FIRSInvoiceHeader:
    """FIRS invoice header structure."""
    invoice_number: str
    invoice_date: str
    due_date: str
    currency_code: str
    supplier_tin: str
    customer_tin: Optional[str] = None
    invoice_type: str = "STANDARD"
    transaction_type: str = "SALE"
    payment_terms: str = "NET30"


@dataclass
class FIRSInvoiceItem:
    """FIRS invoice item structure."""
    item_id: str
    description: str
    quantity: str
    unit_price: str
    total_amount: str
    vat_rate: str
    vat_amount: str
    category_code: str
    unit_of_measure: str = "EACH"


@dataclass
class FIRSCustomer:
    """FIRS customer information structure."""
    name: str
    address: str
    tin: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    customer_type: str = "INDIVIDUAL"


@dataclass
class FIRSSupplier:
    """FIRS supplier information structure."""
    name: str
    address: str
    tin: str
    phone: str
    email: str
    business_registration: str


@dataclass
class FIRSTotals:
    """FIRS invoice totals structure."""
    subtotal: str
    total_vat: str
    total_amount: str
    discount_amount: str = "0.00"
    adjustment_amount: str = "0.00"


@dataclass
class FIRSInvoice:
    """Complete FIRS invoice structure."""
    header: FIRSInvoiceHeader
    supplier: FIRSSupplier
    customer: FIRSCustomer
    items: List[FIRSInvoiceItem]
    totals: FIRSTotals
    qr_code: Optional[str] = None
    digital_signature: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


@dataclass
class FormattingResult:
    """Result of FIRS formatting process."""
    success: bool
    firs_invoice: Optional[FIRSInvoice] = None
    json_data: Optional[str] = None
    validation_errors: List[str] = None
    warnings: List[str] = None
    qr_code_data: Optional[str] = None
    file_size: Optional[int] = None


class FIRSFormatter:
    """
    FIRS e-invoice formatter.
    
    Converts internal invoice objects to FIRS-compliant format
    with proper validation and digital signatures.
    """
    
    def __init__(
        self,
        supplier_info: Dict[str, str],
        qr_generator: Optional[QRCodeGenerator] = None,
        digital_signer: Optional[DigitalSigner] = None
    ):
        self.supplier_info = supplier_info
        self.qr_generator = qr_generator
        self.digital_signer = digital_signer
        
        # FIRS configuration
        self.api_version = "1.0"
        self.schema_version = "2023.1"
        self.max_description_length = 500
        self.max_items_per_invoice = 1000
        
        # Currency configuration
        self.default_currency = "NGN"
        self.supported_currencies = ["NGN", "USD", "EUR", "GBP"]
        
        # Category code mappings
        self.category_mappings = self._create_category_mappings()
        
        # Statistics
        self.stats = {
            'formatted': 0,
            'failed': 0,
            'total_amount_formatted': Decimal('0'),
            'qr_codes_generated': 0,
            'signatures_created': 0
        }
    
    async def format_invoice(self, invoice: Invoice) -> FormattingResult:
        """
        Format invoice into FIRS-compliant structure.
        
        Args:
            invoice: Internal invoice object
            
        Returns:
            FormattingResult with FIRS-formatted data
        """
        try:
            logger.info(f"Formatting invoice for FIRS: {invoice.invoice_number}")
            
            # Validate input invoice
            validation_errors = self._validate_input_invoice(invoice)
            if validation_errors:
                return FormattingResult(
                    success=False,
                    validation_errors=validation_errors
                )
            
            # Create FIRS invoice structure
            firs_invoice = await self._create_firs_invoice(invoice)
            
            # Generate QR code if generator available
            qr_code_data = None
            if self.qr_generator:
                qr_code_data = await self._generate_qr_code(firs_invoice)
                firs_invoice.qr_code = qr_code_data
                self.stats['qr_codes_generated'] += 1
            
            # Create digital signature if signer available
            if self.digital_signer:
                signature = await self._create_digital_signature(firs_invoice)
                firs_invoice.digital_signature = signature
                self.stats['signatures_created'] += 1
            
            # Convert to JSON
            json_data = self._convert_to_json(firs_invoice)
            
            # Final validation
            final_validation_errors = self._validate_firs_invoice(firs_invoice)
            
            # Update statistics
            self.stats['formatted'] += 1
            self.stats['total_amount_formatted'] += Decimal(firs_invoice.totals.total_amount)
            
            logger.info(f"Successfully formatted invoice: {invoice.invoice_number}")
            
            return FormattingResult(
                success=True,
                firs_invoice=firs_invoice,
                json_data=json_data,
                validation_errors=final_validation_errors,
                qr_code_data=qr_code_data,
                file_size=len(json_data.encode('utf-8'))
            )
            
        except Exception as e:
            logger.error(f"Failed to format invoice {invoice.invoice_number}: {e}")
            self.stats['failed'] += 1
            
            return FormattingResult(
                success=False,
                validation_errors=[str(e)]
            )
    
    async def format_batch_invoices(
        self,
        invoices: List[Invoice]
    ) -> List[FormattingResult]:
        """
        Format multiple invoices in batch.
        
        Args:
            invoices: List of invoice objects
            
        Returns:
            List of FormattingResult objects
        """
        logger.info(f"Batch formatting {len(invoices)} invoices for FIRS")
        
        results = []
        for invoice in invoices:
            result = await self.format_invoice(invoice)
            results.append(result)
        
        success_count = sum(1 for r in results if r.success)
        logger.info(f"Batch formatting completed. Success: {success_count}/{len(invoices)}")
        
        return results
    
    async def _create_firs_invoice(self, invoice: Invoice) -> FIRSInvoice:
        """Create FIRS invoice structure from internal invoice."""
        
        # Create header
        header = FIRSInvoiceHeader(
            invoice_number=invoice.invoice_number,
            invoice_date=invoice.date.strftime("%Y-%m-%d"),
            due_date=invoice.due_date.strftime("%Y-%m-%d") if invoice.due_date else invoice.date.strftime("%Y-%m-%d"),
            currency_code=invoice.currency or self.default_currency,
            supplier_tin=self.supplier_info['tin'],
            customer_tin=invoice.customer_info.tin if invoice.customer_info else None,
            invoice_type=self._determine_invoice_type(invoice),
            transaction_type="SALE"
        )
        
        # Create supplier info
        supplier = FIRSSupplier(
            name=self.supplier_info['name'],
            address=self.supplier_info['address'],
            tin=self.supplier_info['tin'],
            phone=self.supplier_info['phone'],
            email=self.supplier_info['email'],
            business_registration=self.supplier_info.get('business_registration', '')
        )
        
        # Create customer info
        customer = FIRSCustomer(
            name=invoice.customer_info.name if invoice.customer_info else "Cash Customer",
            address=invoice.customer_info.address if invoice.customer_info else "",
            tin=invoice.customer_info.tin if invoice.customer_info else None,
            phone=invoice.customer_info.phone if invoice.customer_info else None,
            email=invoice.customer_info.email if invoice.customer_info else None,
            customer_type=self._determine_customer_type(invoice.customer_info)
        )
        
        # Create items
        items = []
        for item in invoice.items:
            firs_item = FIRSInvoiceItem(
                item_id=item.id,
                description=self._truncate_description(item.description),
                quantity=str(item.quantity),
                unit_price=str(item.unit_price),
                total_amount=str(item.total_amount),
                vat_rate=str(item.vat_rate * 100),  # Convert to percentage
                vat_amount=str(item.vat_amount),
                category_code=self._map_category_code(item.category),
                unit_of_measure="EACH"
            )
            items.append(firs_item)
        
        # Create totals
        totals = FIRSTotals(
            subtotal=str(invoice.subtotal),
            total_vat=str(invoice.vat_amount),
            total_amount=str(invoice.total_amount)
        )
        
        # Create metadata
        metadata = {
            'api_version': self.api_version,
            'schema_version': self.schema_version,
            'created_timestamp': datetime.utcnow().isoformat(),
            'source_system': 'taxpoynt_platform',
            'original_invoice_id': invoice.id,
            'auto_generated': invoice.metadata.get('auto_generated', False) if invoice.metadata else False
        }
        
        return FIRSInvoice(
            header=header,
            supplier=supplier,
            customer=customer,
            items=items,
            totals=totals,
            metadata=metadata
        )
    
    async def _generate_qr_code(self, firs_invoice: FIRSInvoice) -> str:
        """Generate QR code for the invoice."""
        
        # Create QR code data
        qr_data = {
            'invoice_number': firs_invoice.header.invoice_number,
            'supplier_tin': firs_invoice.supplier.tin,
            'customer_tin': firs_invoice.customer.tin,
            'total_amount': firs_invoice.totals.total_amount,
            'invoice_date': firs_invoice.header.invoice_date,
            'verification_url': f"https://einvoice.firs.gov.ng/verify/{firs_invoice.header.invoice_number}"
        }
        
        # Generate QR code
        qr_code_image = await self.qr_generator.generate(
            data=json.dumps(qr_data),
            format='base64'
        )
        
        return qr_code_image
    
    async def _create_digital_signature(self, firs_invoice: FIRSInvoice) -> str:
        """Create digital signature for the invoice."""
        
        # Create signature data (excluding signature field itself)
        signature_data = {
            'header': asdict(firs_invoice.header),
            'supplier': asdict(firs_invoice.supplier),
            'customer': asdict(firs_invoice.customer),
            'items': [asdict(item) for item in firs_invoice.items],
            'totals': asdict(firs_invoice.totals)
        }
        
        # Generate signature
        signature = await self.digital_signer.sign(
            data=json.dumps(signature_data, sort_keys=True)
        )
        
        return signature
    
    def _convert_to_json(self, firs_invoice: FIRSInvoice) -> str:
        """Convert FIRS invoice to JSON string."""
        
        # Convert to dictionary
        invoice_dict = {
            'header': asdict(firs_invoice.header),
            'supplier': asdict(firs_invoice.supplier),
            'customer': asdict(firs_invoice.customer),
            'items': [asdict(item) for item in firs_invoice.items],
            'totals': asdict(firs_invoice.totals),
            'qr_code': firs_invoice.qr_code,
            'digital_signature': firs_invoice.digital_signature,
            'metadata': firs_invoice.metadata
        }
        
        # Convert to JSON with proper formatting
        return json.dumps(invoice_dict, indent=2, ensure_ascii=False)
    
    def _validate_input_invoice(self, invoice: Invoice) -> List[str]:
        """Validate input invoice before formatting."""
        
        errors = []
        
        # Basic validation
        if not invoice.invoice_number:
            errors.append("Invoice number is required")
        
        if not invoice.date:
            errors.append("Invoice date is required")
        
        if not invoice.items:
            errors.append("Invoice must have at least one item")
        
        if len(invoice.items) > self.max_items_per_invoice:
            errors.append(f"Invoice cannot have more than {self.max_items_per_invoice} items")
        
        if invoice.total_amount <= 0:
            errors.append("Invoice total must be positive")
        
        # Currency validation
        if invoice.currency and invoice.currency not in self.supported_currencies:
            errors.append(f"Unsupported currency: {invoice.currency}")
        
        # Item validation
        for i, item in enumerate(invoice.items):
            if not item.description:
                errors.append(f"Item {i+1}: Description is required")
            
            if item.quantity <= 0:
                errors.append(f"Item {i+1}: Quantity must be positive")
            
            if item.unit_price <= 0:
                errors.append(f"Item {i+1}: Unit price must be positive")
        
        return errors
    
    def _validate_firs_invoice(self, firs_invoice: FIRSInvoice) -> List[str]:
        """Validate FIRS invoice structure."""
        
        errors = []
        
        # Supplier validation
        if not firs_invoice.supplier.tin:
            errors.append("Supplier TIN is required")
        
        # Customer validation for corporate customers
        if (firs_invoice.customer.customer_type == "CORPORATE" and 
            not firs_invoice.customer.tin):
            errors.append("Corporate customer TIN is required")
        
        # Items validation
        for item in firs_invoice.items:
            if len(item.description) > self.max_description_length:
                errors.append(f"Item description too long: {item.description[:50]}...")
        
        # Totals validation
        calculated_total = sum(Decimal(item.total_amount) for item in firs_invoice.items)
        if abs(calculated_total - Decimal(firs_invoice.totals.subtotal)) > Decimal('0.01'):
            errors.append("Invoice totals do not match item totals")
        
        return errors
    
    def _determine_invoice_type(self, invoice: Invoice) -> str:
        """Determine FIRS invoice type from internal invoice."""
        
        if invoice.metadata:
            # Check for specific invoice types
            if invoice.metadata.get('is_credit_note'):
                return "CREDIT_NOTE"
            elif invoice.metadata.get('is_debit_note'):
                return "DEBIT_NOTE"
            elif invoice.metadata.get('is_proforma'):
                return "PROFORMA"
        
        return "STANDARD"
    
    def _determine_customer_type(self, customer_info) -> str:
        """Determine FIRS customer type."""
        
        if not customer_info:
            return "INDIVIDUAL"
        
        if hasattr(customer_info, 'customer_type'):
            type_mapping = {
                'individual': 'INDIVIDUAL',
                'corporate': 'CORPORATE',
                'government': 'GOVERNMENT',
                'ngo': 'NGO',
                'diplomat': 'DIPLOMAT'
            }
            return type_mapping.get(customer_info.customer_type, 'INDIVIDUAL')
        
        # Default based on TIN presence
        return "CORPORATE" if customer_info.tin else "INDIVIDUAL"
    
    def _truncate_description(self, description: str) -> str:
        """Truncate description to FIRS limits."""
        
        if len(description) <= self.max_description_length:
            return description
        
        return description[:self.max_description_length-3] + "..."
    
    def _map_category_code(self, category: str) -> str:
        """Map internal category to FIRS category code."""
        
        return self.category_mappings.get(category, "GEN001")
    
    def _create_category_mappings(self) -> Dict[str, str]:
        """Create mapping from internal categories to FIRS codes."""
        
        return {
            'goods': 'GDS001',
            'services': 'SRV001',
            'digital_services': 'DIG001',
            'financial_services': 'FIN001',
            'medical_services': 'MED001',
            'educational_services': 'EDU001',
            'transport': 'TRP001',
            'utilities': 'UTL001',
            'government_fees': 'GOV001',
            'donations': 'DON001',
            'food_beverages': 'FBV001',
            'clothing': 'CLT001',
            'electronics': 'ELC001',
            'automotive': 'AUT001',
            'construction': 'CNS001',
            'agriculture': 'AGR001',
            'manufacturing': 'MFG001',
            'retail': 'RTL001',
            'wholesale': 'WSL001',
            'consulting': 'CST001'
        }
    
    def create_firs_batch_file(
        self,
        formatted_invoices: List[FormattingResult],
        batch_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Create FIRS batch file for multiple invoices.
        
        Args:
            formatted_invoices: List of formatted invoice results
            batch_id: Optional batch identifier
            
        Returns:
            Dictionary containing batch file data
        """
        
        if not batch_id:
            batch_id = str(uuid.uuid4())
        
        successful_invoices = [r for r in formatted_invoices if r.success]
        
        batch_data = {
            'batch_header': {
                'batch_id': batch_id,
                'creation_timestamp': datetime.utcnow().isoformat(),
                'supplier_tin': self.supplier_info['tin'],
                'total_invoices': len(successful_invoices),
                'total_amount': str(sum(
                    Decimal(result.firs_invoice.totals.total_amount) 
                    for result in successful_invoices
                )),
                'api_version': self.api_version,
                'schema_version': self.schema_version
            },
            'invoices': [
                json.loads(result.json_data) for result in successful_invoices
            ]
        }
        
        return batch_data
    
    def get_formatting_stats(self) -> Dict[str, Any]:
        """Get formatting statistics."""
        return self.stats.copy()
    
    def reset_stats(self):
        """Reset formatting statistics."""
        self.stats = {
            'formatted': 0,
            'failed': 0,
            'total_amount_formatted': Decimal('0'),
            'qr_codes_generated': 0,
            'signatures_created': 0
        }