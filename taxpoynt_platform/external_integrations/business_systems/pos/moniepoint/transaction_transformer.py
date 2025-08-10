"""
Moniepoint POS Transaction Transformer
Transforms Moniepoint POS transaction data into FIRS-compliant UBL BIS 3.0 invoices
with Nigerian tax compliance and banking integration.
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


class MoniepointTransactionTransformer:
    """
    Transforms Moniepoint POS transactions into FIRS-compliant UBL BIS 3.0 invoices.
    
    Handles Nigerian tax compliance, currency conversion, and Moniepoint-specific
    business logic for electronic invoicing with Nigerian banking integration.
    """
    
    def __init__(self):
        """Initialize transformer with Nigerian tax compliance."""
        self.tax_calculator = NigerianTaxCalculator()
        self.currency_converter = CurrencyConverter()
        self.validator = ValidationUtils()
        
        # Nigerian VAT rate
        self.nigerian_vat_rate = Decimal('0.075')  # 7.5%
        
        # Moniepoint-specific configuration
        self.moniepoint_config = {
            'default_currency': 'NGN',
            'supported_payment_types': [
                'CARD', 'BANK_TRANSFER', 'USSD', 'QR', 'NIP', 'MOBILE_MONEY', 'CASH', 'OTHER'
            ],
            'tax_inclusive_by_default': True,  # Moniepoint amounts typically include VAT
            'banking_integration': True,
            'nip_support': True  # Nigeria Instant Payment support
        }
        
        # Nigerian banking codes mapping
        self.bank_code_mapping = {
            '044': 'Access Bank',
            '014': 'Afribank Nigeria Plc',
            '023': 'Citibank Nigeria Limited',
            '050': 'Ecobank Nigeria Plc',
            '011': 'First Bank of Nigeria Limited',
            '214': 'First City Monument Bank Limited',
            '070': 'Fidelity Bank Plc',
            '058': 'Guaranty Trust Bank Plc',
            '030': 'Heritage Banking Company Ltd.',
            '082': 'Keystone Bank Limited',
            '221': 'Stanbic IBTC Bank Plc',
            '068': 'Standard Chartered Bank Nigeria Limited',
            '032': 'Union Bank of Nigeria Plc',
            '033': 'United Bank for Africa Plc',
            '215': 'Unity Bank Plc',
            '035': 'Wema Bank Plc',
            '057': 'Zenith Bank Plc'
        }
    
    async def transform_transaction(
        self,
        pos_transaction: POSTransaction,
        merchant_info: Dict[str, Any],
        moniepoint_metadata: Optional[Dict[str, Any]] = None
    ) -> UBLInvoice:
        """
        Transform Moniepoint POS transaction to UBL BIS 3.0 invoice.
        
        Args:
            pos_transaction: Standardized POS transaction
            merchant_info: Merchant business information
            moniepoint_metadata: Additional Moniepoint-specific data
            
        Returns:
            UBLInvoice: FIRS-compliant electronic invoice
            
        Raises:
            ValidationError: If transaction data is invalid
            TransformationError: If transformation fails
        """
        try:
            logger.info(f"Transforming Moniepoint transaction {pos_transaction.transaction_id}")
            
            # Validate transaction data
            await self._validate_transaction_data(pos_transaction)
            
            # Create invoice header
            header = await self._create_invoice_header(
                pos_transaction, merchant_info, moniepoint_metadata
            )
            
            # Create customer information
            customer = await self._create_invoice_customer(
                pos_transaction.customer_info, moniepoint_metadata
            )
            
            # Create line items with Nigerian tax compliance
            line_items = await self._create_invoice_line_items(
                pos_transaction.line_items, moniepoint_metadata
            )
            
            # Calculate taxes (Nigerian VAT)
            taxes = await self._calculate_invoice_taxes(line_items, pos_transaction, moniepoint_metadata)
            
            # Create payment information
            payments = await self._create_invoice_payments(
                pos_transaction.payments, moniepoint_metadata
            )
            
            # Create UBL invoice
            ubl_invoice = UBLInvoice(
                header=header,
                customer=customer,
                line_items=line_items,
                taxes=taxes,
                payments=payments,
                metadata={
                    'source_system': 'moniepoint_pos',
                    'moniepoint_merchant_id': pos_transaction.metadata.get('moniepoint_merchant_id') if pos_transaction.metadata else None,
                    'moniepoint_transaction_reference': pos_transaction.transaction_id,
                    'moniepoint_payment_reference': pos_transaction.metadata.get('moniepoint_payment_reference') if pos_transaction.metadata else None,
                    'moniepoint_channel': pos_transaction.metadata.get('moniepoint_channel') if pos_transaction.metadata else None,
                    'nigerian_banking_integration': True,
                    'transformation_timestamp': datetime.utcnow().isoformat(),
                    **pos_transaction.metadata
                }
            )
            
            logger.info(f"Successfully transformed Moniepoint transaction {pos_transaction.transaction_id}")
            return ubl_invoice
            
        except Exception as e:
            logger.error(f"Failed to transform Moniepoint transaction: {str(e)}")
            raise
    
    async def _validate_transaction_data(self, transaction: POSTransaction) -> None:
        """Validate Moniepoint POS transaction data."""
        if not transaction.transaction_id:
            raise ValueError("Transaction ID is required")
        
        if not transaction.line_items:
            raise ValueError("Transaction must have line items")
        
        if transaction.total_amount <= 0:
            raise ValueError("Transaction total must be positive")
        
        # Validate currency (should be NGN for Nigerian market)
        if transaction.currency and transaction.currency != 'NGN':
            logger.warning(f"Non-NGN currency detected: {transaction.currency}")
    
    async def _create_invoice_header(
        self,
        transaction: POSTransaction,
        merchant_info: Dict[str, Any],
        moniepoint_metadata: Optional[Dict[str, Any]] = None
    ) -> InvoiceHeader:
        """Create UBL invoice header from Moniepoint transaction."""
        # Amount should already be in NGN
        total_ngn = transaction.total_amount
        if transaction.currency and transaction.currency != 'NGN':
            total_ngn = await self.currency_converter.convert(
                transaction.total_amount, transaction.currency, 'NGN'
            )
        
        return InvoiceHeader(
            invoice_id=self._generate_invoice_id(transaction.transaction_id),
            invoice_number=self._generate_invoice_number(transaction, moniepoint_metadata),
            issue_date=transaction.timestamp.date(),
            due_date=transaction.timestamp.date(),  # Payment transactions are immediate
            currency_code='NGN',
            total_amount=total_ngn,
            tax_amount=transaction.tax_amount,
            supplier_info={
                'name': merchant_info.get('businessName', 'Unknown Merchant'),
                'tin': merchant_info.get('tin'),
                'address': merchant_info.get('address', {}),
                'contact_info': merchant_info.get('contact_info', {}),
                'moniepoint_merchant_id': transaction.metadata.get('moniepoint_merchant_id') if transaction.metadata else None,
                'cac_number': merchant_info.get('cacNumber'),
                'bank_account': merchant_info.get('defaultAccountNumber')
            },
            document_type='payment_receipt',
            original_currency=transaction.currency or 'NGN'
        )
    
    async def _create_invoice_customer(
        self,
        customer_info: Optional[CustomerInfo],
        moniepoint_metadata: Optional[Dict[str, Any]] = None
    ) -> InvoiceCustomer:
        """Create UBL invoice customer from Moniepoint customer data."""
        if not customer_info:
            # Create default customer for anonymous payments
            return InvoiceCustomer(
                customer_id='anonymous-payer',
                name='Anonymous Customer',
                tin='00000000-0001',  # Default TIN for anonymous customers
                customer_type='individual',
                address=InvoiceAddress(
                    country='NG',
                    state='Unknown',
                    city='Unknown'
                ),
                metadata={
                    'moniepoint_customer_type': 'anonymous',
                    'moniepoint_customer_reference': moniepoint_metadata.get('customer_reference') if moniepoint_metadata else None
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
                'moniepoint_customer_reference': customer_info.metadata.get('moniepoint_customer_reference') if customer_info.metadata else None,
                'moniepoint_customer_email': customer_info.email,
                'moniepoint_customer_phone': customer_info.phone,
                'original_customer_data': customer_info.metadata if customer_info else {}
            }
        )
    
    async def _create_invoice_line_items(
        self,
        line_items: List[POSLineItem],
        moniepoint_metadata: Optional[Dict[str, Any]] = None
    ) -> List[InvoiceLineItem]:
        """Create UBL invoice line items from Moniepoint line items."""
        invoice_items = []
        
        for idx, item in enumerate(line_items):
            # Amounts should already be in NGN
            unit_price_ngn = item.unit_price
            total_price_ngn = item.total_price
            
            if item.currency and item.currency != 'NGN':
                unit_price_ngn = await self.currency_converter.convert(
                    item.unit_price, item.currency, 'NGN'
                )
                total_price_ngn = await self.currency_converter.convert(
                    item.total_price, item.currency, 'NGN'
                )
            
            # Calculate tax amount (Nigerian VAT)
            # Moniepoint amounts are typically VAT-inclusive
            tax_amount = await self._calculate_line_item_tax(item, vat_inclusive=True)
            
            # Determine item category
            item_category = self._determine_item_category(item, moniepoint_metadata)
            
            invoice_item = InvoiceLineItem(
                line_id=str(idx + 1),
                item_code=item.item_code or f"MP-{uuid4().hex[:8]}",
                item_name=item.name,
                description=item.description or item.name,
                quantity=item.quantity,
                unit_price=unit_price_ngn,
                total_price=total_price_ngn,
                tax_amount=tax_amount,
                tax_rate=self.nigerian_vat_rate,
                discount_amount=item.discount_amount or Decimal('0'),
                item_category=item_category,
                metadata={
                    'moniepoint_product_code': item.metadata.get('moniepoint_product_code') if item.metadata else None,
                    'moniepoint_product_name': item.metadata.get('moniepoint_product_name') if item.metadata else None,
                    'moniepoint_order_reference': item.metadata.get('moniepoint_order_reference') if item.metadata else None,
                    'original_currency': item.currency or 'NGN',
                    'vat_inclusive': True
                }
            )
            
            invoice_items.append(invoice_item)
        
        return invoice_items
    
    async def _calculate_invoice_taxes(
        self,
        line_items: List[InvoiceLineItem],
        transaction: POSTransaction,
        moniepoint_metadata: Optional[Dict[str, Any]] = None
    ) -> List[InvoiceTax]:
        """Calculate Nigerian VAT for invoice."""
        # Use pre-calculated tax amount from transaction if available
        if transaction.tax_amount and transaction.tax_amount > 0:
            return [
                InvoiceTax(
                    tax_type='VAT',
                    tax_rate=self.nigerian_vat_rate,
                    taxable_amount=transaction.total_amount - transaction.tax_amount,
                    tax_amount=transaction.tax_amount,
                    tax_code='NG-VAT-STD',
                    metadata={
                        'calculation_method': 'moniepoint_provided',
                        'vat_inclusive': True
                    }
                )
            ]
        
        # Calculate total taxable amount (VAT-exclusive)
        total_amount = sum(item.total_price for item in line_items)
        
        if total_amount <= 0:
            return []
        
        # Since Moniepoint amounts are typically VAT-inclusive
        # VAT = (Total Amount * VAT Rate) / (1 + VAT Rate)
        vat_amount = (total_amount * self.nigerian_vat_rate) / (Decimal('1') + self.nigerian_vat_rate)
        vat_amount = vat_amount.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
        
        taxable_amount = total_amount - vat_amount
        
        return [
            InvoiceTax(
                tax_type='VAT',
                tax_rate=self.nigerian_vat_rate,
                taxable_amount=taxable_amount,
                tax_amount=vat_amount,
                tax_code='NG-VAT-STD',
                metadata={
                    'calculation_method': 'nigerian_vat_inclusive',
                    'moniepoint_tax_calculation': True,
                    'vat_inclusive': True
                }
            )
        ]
    
    async def _create_invoice_payments(
        self,
        payments: List[PaymentInfo],
        moniepoint_metadata: Optional[Dict[str, Any]] = None
    ) -> List[InvoicePayment]:
        """Create UBL invoice payments from Moniepoint payment data."""
        invoice_payments = []
        
        for payment in payments:
            # Amount should already be in NGN
            amount_ngn = payment.amount
            if payment.currency and payment.currency != 'NGN':
                amount_ngn = await self.currency_converter.convert(
                    payment.amount, payment.currency, 'NGN'
                )
            
            # Map Moniepoint payment method to standard format
            payment_method = self._map_moniepoint_payment_method(payment.payment_method)
            
            # Get fee information if available
            fee_amount = Decimal('0')
            if payment.metadata and payment.metadata.get('moniepoint_fee'):
                fee_amount = Decimal(str(payment.metadata['moniepoint_fee']))
            
            invoice_payment = InvoicePayment(
                payment_id=payment.payment_id or str(uuid4()),
                payment_method=payment_method,
                amount=amount_ngn,
                currency='NGN',
                payment_date=payment.payment_date,
                reference=payment.reference,
                status=payment.status or 'completed',
                metadata={
                    'moniepoint_payment_reference': payment.metadata.get('moniepoint_payment_reference') if payment.metadata else None,
                    'moniepoint_payment_method': payment.metadata.get('moniepoint_payment_method') if payment.metadata else None,
                    'moniepoint_channel': payment.metadata.get('moniepoint_channel') if payment.metadata else None,
                    'moniepoint_settlement_amount': payment.metadata.get('moniepoint_settlement_amount') if payment.metadata else None,
                    'moniepoint_fee': str(fee_amount) if fee_amount > 0 else None,
                    'nigerian_banking_channel': True,
                    'original_currency': payment.currency or 'NGN',
                    'original_amount': str(payment.amount)
                }
            )
            
            invoice_payments.append(invoice_payment)
        
        return invoice_payments
    
    async def _calculate_line_item_tax(self, item: POSLineItem, vat_inclusive: bool = True) -> Decimal:
        """Calculate Nigerian VAT for line item."""
        if vat_inclusive:
            # VAT = (Total Price * VAT Rate) / (1 + VAT Rate)
            vat_amount = (item.total_price * self.nigerian_vat_rate) / (Decimal('1') + self.nigerian_vat_rate)
        else:
            # VAT = Total Price * VAT Rate
            vat_amount = item.total_price * self.nigerian_vat_rate
        
        return vat_amount.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
    
    def _determine_item_category(
        self,
        item: POSLineItem,
        moniepoint_metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """Determine item category for Nigerian compliance."""
        if item.metadata and item.metadata.get('moniepoint_product_code'):
            product_code = item.metadata['moniepoint_product_code'].upper()
            
            # Common Moniepoint product codes
            if 'BILL' in product_code:
                return 'utility_payment'
            elif 'AIRTIME' in product_code or 'RECHARGE' in product_code:
                return 'telecommunications'
            elif 'DATA' in product_code:
                return 'data_services'
            elif 'TRANSFER' in product_code:
                return 'financial_service'
        
        # Default categorization based on name patterns
        name_lower = item.name.lower()
        
        if any(word in name_lower for word in ['payment', 'service', 'fee']):
            return 'service_payment'
        elif any(word in name_lower for word in ['bill', 'utility', 'electricity', 'water']):
            return 'utility_payment'
        elif any(word in name_lower for word in ['airtime', 'recharge', 'credit']):
            return 'telecommunications'
        elif any(word in name_lower for word in ['transfer', 'send', 'remittance']):
            return 'financial_service'
        else:
            return 'general_payment'
    
    def _map_moniepoint_payment_method(self, moniepoint_method: str) -> str:
        """Map Moniepoint payment method to standard format."""
        method_mapping = {
            'card': 'debit_card',
            'bank_transfer': 'bank_transfer',
            'ussd': 'ussd',
            'qr_code': 'qr_code',
            'mobile_money': 'mobile_money',
            'cash': 'cash',
            'other': 'other'
        }
        
        return method_mapping.get(moniepoint_method.lower(), 'other')
    
    def _generate_invoice_id(self, transaction_id: str) -> str:
        """Generate unique invoice ID from transaction ID."""
        return f"MP-{transaction_id}"
    
    def _generate_invoice_number(
        self,
        transaction: POSTransaction,
        moniepoint_metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """Generate human-readable invoice number."""
        timestamp = transaction.timestamp.strftime('%Y%m%d')
        
        if transaction.metadata and transaction.metadata.get('moniepoint_payment_reference'):
            payment_ref = transaction.metadata['moniepoint_payment_reference']
            return f"MP-{timestamp}-{payment_ref[-8:]}"
        
        # Use transaction ID
        return f"MP-{timestamp}-{transaction.transaction_id[-8:]}"

    async def transform_batch_transactions(
        self,
        transactions: List[POSTransaction],
        merchant_info: Dict[str, Any],
        moniepoint_metadata: Optional[Dict[str, Any]] = None
    ) -> List[UBLInvoice]:
        """
        Transform multiple Moniepoint transactions in batch.
        
        Args:
            transactions: List of POS transactions
            merchant_info: Merchant business information
            moniepoint_metadata: Additional Moniepoint-specific data
            
        Returns:
            List[UBLInvoice]: List of transformed invoices
        """
        invoices = []
        
        for transaction in transactions:
            try:
                invoice = await self.transform_transaction(
                    transaction, merchant_info, moniepoint_metadata
                )
                invoices.append(invoice)
            except Exception as e:
                logger.error(f"Failed to transform transaction {transaction.transaction_id}: {str(e)}")
                continue
        
        logger.info(f"Successfully transformed {len(invoices)}/{len(transactions)} Moniepoint transactions")
        return invoices