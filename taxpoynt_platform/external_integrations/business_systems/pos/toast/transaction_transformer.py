"""
Toast POS Transaction Transformer
Transforms Toast POS transaction data into FIRS-compliant UBL BIS 3.0 invoices
with Nigerian tax compliance and Toast-specific business logic.
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


class ToastTransactionTransformer:
    """
    Transforms Toast POS transactions into FIRS-compliant UBL BIS 3.0 invoices.
    
    Handles Nigerian tax compliance, currency conversion, and Toast-specific
    business logic for electronic invoicing.
    """
    
    def __init__(self):
        """Initialize transformer with Nigerian tax compliance."""
        self.tax_calculator = NigerianTaxCalculator()
        self.currency_converter = CurrencyConverter()
        self.validator = ValidationUtils()
        
        # Nigerian VAT rate
        self.nigerian_vat_rate = Decimal('0.075')  # 7.5%
        
        # Toast-specific configuration
        self.toast_config = {
            'default_currency': 'USD',
            'supported_payment_types': [
                'CASH', 'CREDIT', 'CREDIT_CARD', 'DEBIT', 'DEBIT_CARD',
                'GIFT_CARD', 'HOUSE_ACCOUNT', 'LOYALTY', 'EXTERNAL_PAYMENT', 'OTHER'
            ],
            'tax_exempt_categories': ['SERVICE_CHARGE', 'TIP', 'DELIVERY_FEE'],
            'restaurant_item_classification': {
                'FOOD': 'food_beverage',
                'BEVERAGE': 'beverage',
                'ALCOHOL': 'alcoholic_beverage',
                'SERVICE': 'service',
                'MERCHANDISE': 'retail_merchandise'
            }
        }
    
    async def transform_transaction(
        self,
        pos_transaction: POSTransaction,
        restaurant_info: Dict[str, Any],
        toast_metadata: Optional[Dict[str, Any]] = None
    ) -> UBLInvoice:
        """
        Transform Toast POS transaction to UBL BIS 3.0 invoice.
        
        Args:
            pos_transaction: Standardized POS transaction
            restaurant_info: Restaurant business information
            toast_metadata: Additional Toast-specific data
            
        Returns:
            UBLInvoice: FIRS-compliant electronic invoice
            
        Raises:
            ValidationError: If transaction data is invalid
            TransformationError: If transformation fails
        """
        try:
            logger.info(f"Transforming Toast transaction {pos_transaction.transaction_id}")
            
            # Validate transaction data
            await self._validate_transaction_data(pos_transaction)
            
            # Create invoice header
            header = await self._create_invoice_header(
                pos_transaction, restaurant_info, toast_metadata
            )
            
            # Create customer information
            customer = await self._create_invoice_customer(
                pos_transaction.customer_info, toast_metadata
            )
            
            # Create line items with Nigerian tax compliance
            line_items = await self._create_invoice_line_items(
                pos_transaction.line_items, toast_metadata
            )
            
            # Calculate taxes (Nigerian VAT)
            taxes = await self._calculate_invoice_taxes(line_items, toast_metadata)
            
            # Create payment information
            payments = await self._create_invoice_payments(
                pos_transaction.payments, toast_metadata
            )
            
            # Create UBL invoice
            ubl_invoice = UBLInvoice(
                header=header,
                customer=customer,
                line_items=line_items,
                taxes=taxes,
                payments=payments,
                metadata={
                    'source_system': 'toast_pos',
                    'toast_restaurant_id': toast_metadata.get('restaurant_id') if toast_metadata else None,
                    'toast_check_guid': pos_transaction.transaction_id,
                    'toast_display_number': toast_metadata.get('display_number') if toast_metadata else None,
                    'toast_dining_option': toast_metadata.get('dining_option') if toast_metadata else None,
                    'transformation_timestamp': datetime.utcnow().isoformat(),
                    **pos_transaction.metadata
                }
            )
            
            logger.info(f"Successfully transformed Toast transaction {pos_transaction.transaction_id}")
            return ubl_invoice
            
        except Exception as e:
            logger.error(f"Failed to transform Toast transaction: {str(e)}")
            raise
    
    async def _validate_transaction_data(self, transaction: POSTransaction) -> None:
        """Validate Toast POS transaction data."""
        if not transaction.transaction_id:
            raise ValueError("Transaction ID is required")
        
        if not transaction.line_items:
            raise ValueError("Transaction must have line items")
        
        if transaction.total_amount <= 0:
            raise ValueError("Transaction total must be positive")
        
        # Validate Toast-specific requirements
        if transaction.metadata.get('toast_check_guid'):
            if not self.validator.validate_uuid_format(
                transaction.metadata['toast_check_guid']
            ):
                raise ValueError("Invalid Toast check GUID format")
    
    async def _create_invoice_header(
        self,
        transaction: POSTransaction,
        restaurant_info: Dict[str, Any],
        toast_metadata: Optional[Dict[str, Any]] = None
    ) -> InvoiceHeader:
        """Create UBL invoice header from Toast transaction."""
        # Convert amount to NGN if needed
        total_ngn = await self._convert_to_ngn(
            transaction.total_amount,
            transaction.currency or self.toast_config['default_currency']
        )
        
        return InvoiceHeader(
            invoice_id=self._generate_invoice_id(transaction.transaction_id),
            invoice_number=self._generate_invoice_number(transaction, toast_metadata),
            issue_date=transaction.timestamp.date(),
            due_date=transaction.timestamp.date(),  # Restaurant orders are immediate
            currency_code='NGN',
            total_amount=total_ngn,
            tax_amount=await self._calculate_total_tax_amount(transaction),
            supplier_info={
                'name': restaurant_info.get('name', 'Unknown Restaurant'),
                'tin': restaurant_info.get('tin'),
                'address': restaurant_info.get('address', {}),
                'contact_info': restaurant_info.get('contact_info', {}),
                'toast_restaurant_id': toast_metadata.get('restaurant_id') if toast_metadata else None
            },
            document_type='restaurant_receipt',
            original_currency=transaction.currency or self.toast_config['default_currency']
        )
    
    async def _create_invoice_customer(
        self,
        customer_info: Optional[CustomerInfo],
        toast_metadata: Optional[Dict[str, Any]] = None
    ) -> InvoiceCustomer:
        """Create UBL invoice customer from Toast customer data."""
        if not customer_info:
            # Create default customer for walk-in dining
            return InvoiceCustomer(
                customer_id='walk-in-diner',
                name='Walk-in Customer',
                tin='00000000-0001',  # Default TIN for walk-in customers
                customer_type='individual',
                address=InvoiceAddress(
                    country='NG',
                    state='Unknown',
                    city='Unknown'
                ),
                metadata={
                    'toast_customer_type': 'walk-in',
                    'toast_customer_guid': toast_metadata.get('customer_guid') if toast_metadata else None
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
                'toast_customer_guid': toast_metadata.get('customer_guid') if toast_metadata else None,
                'original_customer_data': customer_info.metadata if customer_info else {}
            }
        )
    
    async def _create_invoice_line_items(
        self,
        line_items: List[POSLineItem],
        toast_metadata: Optional[Dict[str, Any]] = None
    ) -> List[InvoiceLineItem]:
        """Create UBL invoice line items from Toast line items."""
        invoice_items = []
        
        for idx, item in enumerate(line_items):
            # Skip voided items
            if item.metadata and item.metadata.get('toast_is_voided'):
                logger.info(f"Skipping voided Toast item: {item.name}")
                continue
            
            # Convert amounts to NGN
            unit_price_ngn = await self._convert_to_ngn(
                item.unit_price,
                item.currency or self.toast_config['default_currency']
            )
            
            total_price_ngn = await self._convert_to_ngn(
                item.total_price,
                item.currency or self.toast_config['default_currency']
            )
            
            # Calculate tax amount (Nigerian VAT)
            tax_amount = await self._calculate_line_item_tax(item)
            
            # Handle Toast-specific item categorization
            item_category = self._determine_item_category(item, toast_metadata)
            
            # Handle modifiers in description
            description = item.description or item.name
            if item.metadata and item.metadata.get('toast_modifiers'):
                modifier_names = [mod['name'] for mod in item.metadata['toast_modifiers']]
                if modifier_names:
                    description += f" (with {', '.join(modifier_names)})"
            
            invoice_item = InvoiceLineItem(
                line_id=str(idx + 1),
                item_code=item.item_code or f"TOAST-{uuid4().hex[:8]}",
                item_name=item.name,
                description=description,
                quantity=item.quantity,
                unit_price=unit_price_ngn,
                total_price=total_price_ngn,
                tax_amount=tax_amount,
                tax_rate=self.nigerian_vat_rate if not self._is_tax_exempt(item) else Decimal('0'),
                discount_amount=await self._convert_to_ngn(
                    item.discount_amount or Decimal('0'),
                    item.currency or self.toast_config['default_currency']
                ),
                item_category=item_category,
                metadata={
                    'toast_item_guid': item.metadata.get('toast_item_guid') if item.metadata else None,
                    'toast_selection_guid': item.metadata.get('toast_selection_guid') if item.metadata else None,
                    'toast_category': item.metadata.get('toast_item_category') if item.metadata else None,
                    'toast_modifiers': item.metadata.get('toast_modifiers', []) if item.metadata else [],
                    'toast_applied_discounts': item.metadata.get('toast_applied_discounts', []) if item.metadata else [],
                    'original_currency': item.currency or self.toast_config['default_currency'],
                    'tax_exempt': self._is_tax_exempt(item)
                }
            )
            
            invoice_items.append(invoice_item)
        
        return invoice_items
    
    async def _calculate_invoice_taxes(
        self,
        line_items: List[InvoiceLineItem],
        toast_metadata: Optional[Dict[str, Any]] = None
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
                    'toast_tax_calculation': True
                }
            )
        ]
    
    async def _create_invoice_payments(
        self,
        payments: List[PaymentInfo],
        toast_metadata: Optional[Dict[str, Any]] = None
    ) -> List[InvoicePayment]:
        """Create UBL invoice payments from Toast payment data."""
        invoice_payments = []
        
        for payment in payments:
            # Convert amount to NGN
            amount_ngn = await self._convert_to_ngn(
                payment.amount,
                payment.currency or self.toast_config['default_currency']
            )
            
            # Map Toast payment method to standard format
            payment_method = self._map_toast_payment_method(payment.payment_method)
            
            # Handle tips separately if present
            tip_amount_ngn = Decimal('0')
            if payment.metadata and payment.metadata.get('toast_tip_amount'):
                tip_amount = Decimal(str(payment.metadata['toast_tip_amount']))
                tip_amount_ngn = await self._convert_to_ngn(
                    tip_amount,
                    payment.currency or self.toast_config['default_currency']
                )
            
            invoice_payment = InvoicePayment(
                payment_id=payment.payment_id or str(uuid4()),
                payment_method=payment_method,
                amount=amount_ngn,
                currency='NGN',
                payment_date=payment.payment_date,
                reference=payment.reference,
                status=payment.status or 'completed',
                metadata={
                    'toast_payment_guid': payment.metadata.get('toast_payment_guid') if payment.metadata else None,
                    'toast_payment_type': payment.metadata.get('toast_payment_type') if payment.metadata else None,
                    'toast_card_type': payment.metadata.get('toast_card_type') if payment.metadata else None,
                    'toast_last_four': payment.metadata.get('toast_last_four') if payment.metadata else None,
                    'toast_tip_amount': str(tip_amount_ngn) if tip_amount_ngn > 0 else None,
                    'original_currency': payment.currency or self.toast_config['default_currency'],
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
            item.currency or self.toast_config['default_currency']
        )
        
        return (total_price_ngn * self.nigerian_vat_rate).quantize(
            Decimal('0.01'), rounding=ROUND_HALF_UP
        )
    
    def _is_tax_exempt(self, item: POSLineItem) -> bool:
        """Check if line item is tax exempt."""
        if item.metadata:
            category = item.metadata.get('toast_category', '').upper()
            if category in self.toast_config['tax_exempt_categories']:
                return True
        
        # Check if item is explicitly marked as tax exempt
        return item.metadata.get('tax_exempt', False) if item.metadata else False
    
    def _determine_item_category(
        self,
        item: POSLineItem,
        toast_metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """Determine item category for Nigerian compliance."""
        if item.metadata and item.metadata.get('toast_category'):
            toast_category = item.metadata['toast_category'].upper()
            return self.toast_config['restaurant_item_classification'].get(
                toast_category, 'food_beverage'
            )
        
        # Default categorization based on name patterns
        name_lower = item.name.lower()
        
        if any(word in name_lower for word in ['food', 'meal', 'dish', 'plate', 'sandwich', 'burger', 'pizza']):
            return 'food_beverage'
        elif any(word in name_lower for word in ['drink', 'beverage', 'juice', 'soda', 'coffee', 'tea', 'water']):
            return 'beverage'
        elif any(word in name_lower for word in ['beer', 'wine', 'alcohol', 'cocktail', 'whiskey', 'vodka']):
            return 'alcoholic_beverage'
        elif any(word in name_lower for word in ['service', 'delivery', 'tip', 'gratuity']):
            return 'service'
        else:
            return 'food_beverage'  # Default for restaurant items
    
    def _map_toast_payment_method(self, toast_method: str) -> str:
        """Map Toast payment method to standard format."""
        method_mapping = {
            'cash': 'cash',
            'credit_card': 'credit_card',
            'debit_card': 'debit_card',
            'gift_card': 'gift_card',
            'house_account': 'house_account',
            'loyalty_points': 'loyalty_points',
            'external_payment': 'external_payment',
            'other': 'other'
        }
        
        return method_mapping.get(toast_method.lower(), 'other')
    
    def _generate_invoice_id(self, transaction_id: str) -> str:
        """Generate unique invoice ID from transaction ID."""
        return f"TOAST-{transaction_id}"
    
    def _generate_invoice_number(
        self,
        transaction: POSTransaction,
        toast_metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """Generate human-readable invoice number."""
        timestamp = transaction.timestamp.strftime('%Y%m%d')
        
        if toast_metadata and toast_metadata.get('display_number'):
            return f"TOAST-{timestamp}-{toast_metadata['display_number']}"
        
        # Use transaction ID if no display number
        return f"TOAST-{timestamp}-{transaction.transaction_id[-8:]}"

    async def transform_batch_transactions(
        self,
        transactions: List[POSTransaction],
        restaurant_info: Dict[str, Any],
        toast_metadata: Optional[Dict[str, Any]] = None
    ) -> List[UBLInvoice]:
        """
        Transform multiple Toast transactions in batch.
        
        Args:
            transactions: List of POS transactions
            restaurant_info: Restaurant business information
            toast_metadata: Additional Toast-specific data
            
        Returns:
            List[UBLInvoice]: List of transformed invoices
        """
        invoices = []
        
        for transaction in transactions:
            try:
                invoice = await self.transform_transaction(
                    transaction, restaurant_info, toast_metadata
                )
                invoices.append(invoice)
            except Exception as e:
                logger.error(f"Failed to transform transaction {transaction.transaction_id}: {str(e)}")
                continue
        
        logger.info(f"Successfully transformed {len(invoices)}/{len(transactions)} Toast transactions")
        return invoices