"""
Clover POS Transaction Transformer
Transforms Clover POS transaction data into FIRS-compliant UBL BIS 3.0 invoices
with Nigerian tax compliance and Clover-specific business logic.
"""

import logging
from datetime import datetime
from decimal import Decimal, ROUND_HALF_UP
from typing import Any, Dict, List, Optional, Union
from uuid import uuid4

from ....framework.models.pos_models import (
    CustomerInfo,
    POSLineItem,
    POSTransaction,
    PaymentInfo,
    TaxInfo
)
from ....shared.models.invoice_models import (
    InvoiceAddress,
    InvoiceCustomer,
    InvoiceHeader,
    InvoiceLineItem,
    InvoicePayment,
    InvoiceTax,
    UBLInvoice
)
from ....shared.services.tax_calculator import NigerianTaxCalculator
from ....shared.utils.currency_converter import CurrencyConverter
from ....shared.utils.validation_utils import ValidationUtils

logger = logging.getLogger(__name__)


class CloverTransactionTransformer:
    """
    Transforms Clover POS transactions into FIRS-compliant UBL BIS 3.0 invoices.
    
    Handles Nigerian tax compliance, currency conversion, and Clover-specific
    business logic for electronic invoicing.
    """
    
    def __init__(self):
        """Initialize transformer with Nigerian tax compliance."""
        self.tax_calculator = NigerianTaxCalculator()
        self.currency_converter = CurrencyConverter()
        self.validator = ValidationUtils()
        
        # Nigerian VAT rate
        self.nigerian_vat_rate = Decimal('0.075')  # 7.5%
        
        # Clover-specific configuration
        self.clover_config = {
            'default_currency': 'USD',
            'supported_payment_types': [
                'CASH', 'CREDIT_CARD', 'DEBIT_CARD', 'GIFT_CARD',
                'EXTERNAL_PAYMENT', 'VAULTED_CARD', 'OTHER'
            ],
            'tax_exempt_categories': ['TIPS', 'DONATION'],
            'discount_handling': 'line_item'  # How to handle discounts
        }
    
    async def transform_transaction(
        self,
        pos_transaction: POSTransaction,
        merchant_info: Dict[str, Any],
        clover_metadata: Optional[Dict[str, Any]] = None
    ) -> UBLInvoice:
        """
        Transform Clover POS transaction to UBL BIS 3.0 invoice.
        
        Args:
            pos_transaction: Standardized POS transaction
            merchant_info: Merchant business information
            clover_metadata: Additional Clover-specific data
            
        Returns:
            UBLInvoice: FIRS-compliant electronic invoice
            
        Raises:
            ValidationError: If transaction data is invalid
            TransformationError: If transformation fails
        """
        try:
            logger.info(f"Transforming Clover transaction {pos_transaction.transaction_id}")
            
            # Validate transaction data
            await self._validate_transaction_data(pos_transaction)
            
            # Create invoice header
            header = await self._create_invoice_header(
                pos_transaction, merchant_info, clover_metadata
            )
            
            # Create customer information
            customer = await self._create_invoice_customer(
                pos_transaction.customer_info, clover_metadata
            )
            
            # Create line items with Nigerian tax compliance
            line_items = await self._create_invoice_line_items(
                pos_transaction.line_items, clover_metadata
            )
            
            # Calculate taxes (Nigerian VAT)
            taxes = await self._calculate_invoice_taxes(line_items, clover_metadata)
            
            # Create payment information
            payments = await self._create_invoice_payments(
                pos_transaction.payments, clover_metadata
            )
            
            # Create UBL invoice
            ubl_invoice = UBLInvoice(
                header=header,
                customer=customer,
                line_items=line_items,
                taxes=taxes,
                payments=payments,
                metadata={
                    'source_system': 'clover_pos',
                    'clover_order_id': clover_metadata.get('order_id') if clover_metadata else None,
                    'clover_device_id': clover_metadata.get('device_id') if clover_metadata else None,
                    'clover_merchant_id': clover_metadata.get('merchant_id') if clover_metadata else None,
                    'transformation_timestamp': datetime.utcnow().isoformat(),
                    **pos_transaction.metadata
                }
            )
            
            logger.info(f"Successfully transformed Clover transaction {pos_transaction.transaction_id}")
            return ubl_invoice
            
        except Exception as e:
            logger.error(f"Failed to transform Clover transaction: {str(e)}")
            raise
    
    async def _validate_transaction_data(self, transaction: POSTransaction) -> None:
        """Validate Clover POS transaction data."""
        if not transaction.transaction_id:
            raise ValueError("Transaction ID is required")
        
        if not transaction.line_items:
            raise ValueError("Transaction must have line items")
        
        if transaction.total_amount <= 0:
            raise ValueError("Transaction total must be positive")
        
        # Validate Clover-specific requirements
        if transaction.metadata.get('clover_order_id'):
            if not self.validator.validate_clover_order_id(
                transaction.metadata['clover_order_id']
            ):
                raise ValueError("Invalid Clover order ID format")
    
    async def _create_invoice_header(
        self,
        transaction: POSTransaction,
        merchant_info: Dict[str, Any],
        clover_metadata: Optional[Dict[str, Any]] = None
    ) -> InvoiceHeader:
        """Create UBL invoice header from Clover transaction."""
        # Convert amount to NGN if needed
        total_ngn = await self._convert_to_ngn(
            transaction.total_amount,
            transaction.currency or self.clover_config['default_currency']
        )
        
        return InvoiceHeader(
            invoice_id=self._generate_invoice_id(transaction.transaction_id),
            invoice_number=self._generate_invoice_number(transaction, clover_metadata),
            issue_date=transaction.timestamp.date(),
            due_date=transaction.timestamp.date(),  # POS transactions are immediate
            currency_code='NGN',
            total_amount=total_ngn,
            tax_amount=await self._calculate_total_tax_amount(transaction),
            supplier_info={
                'name': merchant_info.get('name', 'Unknown Merchant'),
                'tin': merchant_info.get('tin'),
                'address': merchant_info.get('address', {}),
                'contact_info': merchant_info.get('contact_info', {}),
                'clover_merchant_id': clover_metadata.get('merchant_id') if clover_metadata else None
            },
            document_type='pos_invoice',
            original_currency=transaction.currency or self.clover_config['default_currency']
        )
    
    async def _create_invoice_customer(
        self,
        customer_info: Optional[CustomerInfo],
        clover_metadata: Optional[Dict[str, Any]] = None
    ) -> InvoiceCustomer:
        """Create UBL invoice customer from Clover customer data."""
        if not customer_info:
            # Create default customer for walk-in sales
            return InvoiceCustomer(
                customer_id='walk-in',
                name='Walk-in Customer',
                tin='00000000-0001',  # Default TIN for walk-in customers
                customer_type='individual',
                address=InvoiceAddress(
                    country='NG',
                    state='Unknown',
                    city='Unknown'
                ),
                metadata={
                    'clover_customer_type': 'walk-in',
                    'clover_customer_id': clover_metadata.get('customer_id') if clover_metadata else None
                }
            )
        
        # Validate and format TIN
        tin = customer_info.tax_id or '00000000-0001'
        if not self.validator.validate_nigerian_tin(tin):
            logger.warning(f"Invalid TIN {tin}, using default")
            tin = '00000000-0001'
        
        return InvoiceCustomer(
            customer_id=customer_info.customer_id or str(uuid4()),
            name=customer_info.name or 'Unknown Customer',
            tin=tin,
            customer_type='individual' if customer_info.customer_type != 'business' else 'business',
            email=customer_info.email,
            phone=customer_info.phone,
            address=InvoiceAddress(
                street=customer_info.address.get('street') if customer_info.address else None,
                city=customer_info.address.get('city', 'Unknown') if customer_info.address else 'Unknown',
                state=customer_info.address.get('state', 'Unknown') if customer_info.address else 'Unknown',
                postal_code=customer_info.address.get('postal_code') if customer_info.address else None,
                country='NG'
            ),
            metadata={
                'clover_customer_id': clover_metadata.get('customer_id') if clover_metadata else None,
                'original_customer_data': customer_info.metadata if customer_info else {}
            }
        )
    
    async def _create_invoice_line_items(
        self,
        line_items: List[POSLineItem],
        clover_metadata: Optional[Dict[str, Any]] = None
    ) -> List[InvoiceLineItem]:
        """Create UBL invoice line items from Clover line items."""
        invoice_items = []
        
        for idx, item in enumerate(line_items):
            # Convert amounts to NGN
            unit_price_ngn = await self._convert_to_ngn(
                item.unit_price,
                item.currency or self.clover_config['default_currency']
            )
            
            total_price_ngn = await self._convert_to_ngn(
                item.total_price,
                item.currency or self.clover_config['default_currency']
            )
            
            # Calculate tax amount (Nigerian VAT)
            tax_amount = await self._calculate_line_item_tax(item)
            
            # Handle Clover-specific item categorization
            item_category = self._determine_item_category(item, clover_metadata)
            
            invoice_item = InvoiceLineItem(
                line_id=str(idx + 1),
                item_code=item.item_code or f"CLOVER-{uuid4().hex[:8]}",
                item_name=item.name,
                description=item.description or item.name,
                quantity=item.quantity,
                unit_price=unit_price_ngn,
                total_price=total_price_ngn,
                tax_amount=tax_amount,
                tax_rate=self.nigerian_vat_rate if not self._is_tax_exempt(item) else Decimal('0'),
                discount_amount=await self._convert_to_ngn(
                    item.discount_amount or Decimal('0'),
                    item.currency or self.clover_config['default_currency']
                ),
                item_category=item_category,
                metadata={
                    'clover_item_id': item.metadata.get('clover_item_id') if item.metadata else None,
                    'clover_category': item.metadata.get('category') if item.metadata else None,
                    'clover_modifiers': item.metadata.get('modifiers', []) if item.metadata else [],
                    'original_currency': item.currency or self.clover_config['default_currency'],
                    'tax_exempt': self._is_tax_exempt(item)
                }
            )
            
            invoice_items.append(invoice_item)
        
        return invoice_items
    
    async def _calculate_invoice_taxes(
        self,
        line_items: List[InvoiceLineItem],
        clover_metadata: Optional[Dict[str, Any]] = None
    ) -> List[InvoiceTax]:
        """Calculate Nigerian VAT for invoice."""
        # Calculate total taxable amount
        taxable_amount = sum(
            item.total_price for item in line_items
            if not item.metadata.get('tax_exempt', False)
        )
        
        if taxable_amount <= 0:
            return []
        
        vat_amount = (taxable_amount * self.nigerian_vat_rate).quantize(
            Decimal('0.01'), rounding=ROUND_HALF_UP
        )
        
        return [
            InvoiceTax(
                tax_type='VAT',
                tax_rate=self.nigerian_vat_rate,
                taxable_amount=taxable_amount,
                tax_amount=vat_amount,
                tax_code='NG-VAT-STD',
                metadata={
                    'calculation_method': 'nigerian_standard_vat',
                    'clover_tax_calculation': True
                }
            )
        ]
    
    async def _create_invoice_payments(
        self,
        payments: List[PaymentInfo],
        clover_metadata: Optional[Dict[str, Any]] = None
    ) -> List[InvoicePayment]:
        """Create UBL invoice payments from Clover payment data."""
        invoice_payments = []
        
        for payment in payments:
            # Convert amount to NGN
            amount_ngn = await self._convert_to_ngn(
                payment.amount,
                payment.currency or self.clover_config['default_currency']
            )
            
            # Map Clover payment method to standard format
            payment_method = self._map_clover_payment_method(payment.payment_method)
            
            invoice_payment = InvoicePayment(
                payment_id=payment.payment_id or str(uuid4()),
                payment_method=payment_method,
                amount=amount_ngn,
                currency='NGN',
                payment_date=payment.payment_date,
                reference=payment.reference,
                status=payment.status or 'completed',
                metadata={
                    'clover_payment_id': payment.metadata.get('clover_payment_id') if payment.metadata else None,
                    'clover_tender_type': payment.metadata.get('tender_type') if payment.metadata else None,
                    'clover_card_type': payment.metadata.get('card_type') if payment.metadata else None,
                    'original_currency': payment.currency or self.clover_config['default_currency'],
                    'original_amount': str(payment.amount)
                }
            )
            
            invoice_payments.append(invoice_payment)
        
        return invoice_payments
    
    async def _convert_to_ngn(self, amount: Decimal, from_currency: str) -> Decimal:
        """Convert amount to Nigerian Naira."""
        if from_currency == 'NGN':
            return amount
        
        return await self.currency_converter.convert(
            amount, from_currency, 'NGN'
        )
    
    async def _calculate_total_tax_amount(self, transaction: POSTransaction) -> Decimal:
        """Calculate total tax amount for transaction."""
        total_tax = Decimal('0')
        
        for item in transaction.line_items:
            if not self._is_tax_exempt(item):
                item_tax = await self._calculate_line_item_tax(item)
                total_tax += item_tax
        
        return total_tax
    
    async def _calculate_line_item_tax(self, item: POSLineItem) -> Decimal:
        """Calculate Nigerian VAT for line item."""
        if self._is_tax_exempt(item):
            return Decimal('0')
        
        # Convert to NGN first
        total_price_ngn = await self._convert_to_ngn(
            item.total_price,
            item.currency or self.clover_config['default_currency']
        )
        
        return (total_price_ngn * self.nigerian_vat_rate).quantize(
            Decimal('0.01'), rounding=ROUND_HALF_UP
        )
    
    def _is_tax_exempt(self, item: POSLineItem) -> bool:
        """Check if line item is tax exempt."""
        if item.metadata:
            category = item.metadata.get('category', '').upper()
            if category in self.clover_config['tax_exempt_categories']:
                return True
        
        # Check if item is explicitly marked as tax exempt
        return item.metadata.get('tax_exempt', False) if item.metadata else False
    
    def _determine_item_category(
        self,
        item: POSLineItem,
        clover_metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """Determine item category for Nigerian compliance."""
        if item.metadata and item.metadata.get('category'):
            return item.metadata['category'].lower()
        
        # Default categorization based on name patterns
        name_lower = item.name.lower()
        
        if any(word in name_lower for word in ['food', 'meal', 'dish', 'plate']):
            return 'food_beverage'
        elif any(word in name_lower for word in ['drink', 'beverage', 'juice', 'soda']):
            return 'beverage'
        elif any(word in name_lower for word in ['service', 'delivery', 'fee']):
            return 'service'
        else:
            return 'general_merchandise'
    
    def _map_clover_payment_method(self, clover_method: str) -> str:
        """Map Clover payment method to standard format."""
        method_mapping = {
            'CASH': 'cash',
            'CREDIT_CARD': 'credit_card',
            'DEBIT_CARD': 'debit_card',
            'GIFT_CARD': 'gift_card',
            'EXTERNAL_PAYMENT': 'external_payment',
            'VAULTED_CARD': 'stored_card',
            'OTHER': 'other'
        }
        
        return method_mapping.get(clover_method.upper(), 'other')
    
    def _generate_invoice_id(self, transaction_id: str) -> str:
        """Generate unique invoice ID from transaction ID."""
        return f"CLV-{transaction_id}"
    
    def _generate_invoice_number(
        self,
        transaction: POSTransaction,
        clover_metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """Generate human-readable invoice number."""
        timestamp = transaction.timestamp.strftime('%Y%m%d')
        
        if clover_metadata and clover_metadata.get('order_number'):
            return f"CLV-{timestamp}-{clover_metadata['order_number']}"
        
        # Use transaction ID if no order number
        return f"CLV-{timestamp}-{transaction.transaction_id[-6:]}"

    async def transform_batch_transactions(
        self,
        transactions: List[POSTransaction],
        merchant_info: Dict[str, Any],
        clover_metadata: Optional[Dict[str, Any]] = None
    ) -> List[UBLInvoice]:
        """
        Transform multiple Clover transactions in batch.
        
        Args:
            transactions: List of POS transactions
            merchant_info: Merchant business information
            clover_metadata: Additional Clover-specific data
            
        Returns:
            List[UBLInvoice]: List of transformed invoices
        """
        invoices = []
        
        for transaction in transactions:
            try:
                invoice = await self.transform_transaction(
                    transaction, merchant_info, clover_metadata
                )
                invoices.append(invoice)
            except Exception as e:
                logger.error(f"Failed to transform transaction {transaction.transaction_id}: {str(e)}")
                continue
        
        logger.info(f"Successfully transformed {len(invoices)}/{len(transactions)} Clover transactions")
        return invoices