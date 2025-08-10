"""
OPay POS Transaction Transformer
Transforms OPay POS transaction data into FIRS-compliant UBL BIS 3.0 invoices
with Nigerian tax compliance and mobile money integration.
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


class OPayTransactionTransformer:
    """
    Transforms OPay POS transactions into FIRS-compliant UBL BIS 3.0 invoices.
    
    Handles Nigerian tax compliance, currency conversion, and OPay-specific
    business logic for electronic invoicing with mobile money integration.
    """
    
    def __init__(self):
        """Initialize transformer with Nigerian tax compliance."""
        self.tax_calculator = NigerianTaxCalculator()
        self.currency_converter = CurrencyConverter()
        self.validator = ValidationUtils()
        
        # Nigerian VAT rate
        self.nigerian_vat_rate = Decimal('0.075')  # 7.5%
        
        # OPay-specific configuration
        self.opay_config = {
            'default_currency': 'NGN',
            'supported_payment_types': [
                'WALLET', 'CARD', 'BANK_TRANSFER', 'USSD', 'QR_CODE', 
                'MOBILE_MONEY', 'CASH', 'POS', 'OTHER'
            ],
            'tax_inclusive_by_default': True,  # OPay amounts typically include VAT
            'mobile_money_integration': True,
            'wallet_support': True
        }
        
        # Mobile money service mapping
        self.mobile_money_mapping = {
            'OPAY_WALLET': 'OPay Wallet',
            'MTN_MOMO': 'MTN Mobile Money',
            'AIRTEL_MONEY': 'Airtel Money',
            'GLO_MOBILE_MONEY': 'Glo Mobile Money',
            '9MOBILE_MONEY': '9mobile Mobile Money'
        }
    
    async def transform_transaction(
        self,
        pos_transaction: POSTransaction,
        merchant_info: Dict[str, Any],
        opay_metadata: Optional[Dict[str, Any]] = None
    ) -> UBLInvoice:
        """
        Transform OPay POS transaction to UBL BIS 3.0 invoice.
        
        Args:
            pos_transaction: Standardized POS transaction
            merchant_info: Merchant business information
            opay_metadata: Additional OPay-specific data
            
        Returns:
            UBLInvoice: FIRS-compliant electronic invoice
            
        Raises:
            ValidationError: If transaction data is invalid
            TransformationError: If transformation fails
        """
        try:
            logger.info(f"Transforming OPay transaction {pos_transaction.transaction_id}")
            
            # Validate transaction data
            await self._validate_transaction_data(pos_transaction)
            
            # Create invoice header
            header = await self._create_invoice_header(
                pos_transaction, merchant_info, opay_metadata
            )
            
            # Create customer information
            customer = await self._create_invoice_customer(
                pos_transaction.customer_info, opay_metadata
            )
            
            # Create line items with Nigerian tax compliance
            line_items = await self._create_invoice_line_items(
                pos_transaction.line_items, opay_metadata
            )
            
            # Calculate taxes (Nigerian VAT)
            taxes = await self._calculate_invoice_taxes(line_items, pos_transaction, opay_metadata)
            
            # Create payment information
            payments = await self._create_invoice_payments(
                pos_transaction.payments, opay_metadata
            )
            
            # Create UBL invoice
            ubl_invoice = UBLInvoice(
                header=header,
                customer=customer,
                line_items=line_items,
                taxes=taxes,
                payments=payments,
                metadata={
                    'source_system': 'opay_pos',
                    'opay_merchant_id': pos_transaction.metadata.get('opay_merchant_id') if pos_transaction.metadata else None,
                    'opay_order_no': pos_transaction.transaction_id,
                    'opay_reference': pos_transaction.metadata.get('opay_reference') if pos_transaction.metadata else None,
                    'opay_terminal_id': pos_transaction.metadata.get('opay_terminal_id') if pos_transaction.metadata else None,
                    'opay_payment_method': pos_transaction.metadata.get('opay_payment_method') if pos_transaction.metadata else None,
                    'mobile_money_integration': True,
                    'transformation_timestamp': datetime.utcnow().isoformat(),
                    **pos_transaction.metadata
                }
            )
            
            logger.info(f"Successfully transformed OPay transaction {pos_transaction.transaction_id}")
            return ubl_invoice
            
        except Exception as e:
            logger.error(f"Failed to transform OPay transaction: {str(e)}")
            raise
    
    async def _validate_transaction_data(self, transaction: POSTransaction) -> None:
        """Validate OPay POS transaction data."""
        if not transaction.transaction_id:
            raise ValueError("Transaction ID is required")
        
        if not transaction.line_items:
            raise ValueError("Transaction must have line items")
        
        if transaction.total_amount <= 0:
            raise ValueError("Transaction total must be positive")
        
        # Currency should be NGN for Nigerian market
        if transaction.currency and transaction.currency != 'NGN':
            logger.warning(f"Non-NGN currency detected: {transaction.currency}")
    
    async def _create_invoice_header(
        self,
        transaction: POSTransaction,
        merchant_info: Dict[str, Any],
        opay_metadata: Optional[Dict[str, Any]] = None
    ) -> InvoiceHeader:
        """Create UBL invoice header from OPay transaction."""
        # Amount should already be in NGN
        total_ngn = transaction.total_amount
        if transaction.currency and transaction.currency != 'NGN':
            total_ngn = await self.currency_converter.convert(
                transaction.total_amount, transaction.currency, 'NGN'
            )
        
        return InvoiceHeader(
            invoice_id=self._generate_invoice_id(transaction.transaction_id),
            invoice_number=self._generate_invoice_number(transaction, opay_metadata),
            issue_date=transaction.timestamp.date(),
            due_date=transaction.timestamp.date(),  # Mobile payments are immediate
            currency_code='NGN',
            total_amount=total_ngn,
            tax_amount=transaction.tax_amount,
            supplier_info={
                'name': merchant_info.get('businessName', 'Unknown Merchant'),
                'tin': merchant_info.get('tin'),
                'address': merchant_info.get('address', {}),
                'contact_info': merchant_info.get('contact_info', {}),
                'opay_merchant_id': transaction.metadata.get('opay_merchant_id') if transaction.metadata else None,
                'wallet_id': merchant_info.get('walletId')
            },
            document_type='mobile_payment_receipt',
            original_currency=transaction.currency or 'NGN'
        )
    
    async def _create_invoice_customer(
        self,
        customer_info: Optional[CustomerInfo],
        opay_metadata: Optional[Dict[str, Any]] = None
    ) -> InvoiceCustomer:
        """Create UBL invoice customer from OPay customer data."""
        if not customer_info:
            # Create default customer for anonymous mobile payments
            return InvoiceCustomer(
                customer_id='mobile-customer',
                name='Mobile Customer',
                tin='00000000-0001',  # Default TIN for mobile customers
                customer_type='individual',
                address=InvoiceAddress(
                    country='NG',
                    state='Unknown',
                    city='Unknown'
                ),
                metadata={
                    'opay_customer_type': 'mobile',
                    'opay_user_id': opay_metadata.get('user_id') if opay_metadata else None
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
                'opay_user_id': customer_info.metadata.get('opay_user_id') if customer_info.metadata else None,
                'opay_user_phone': customer_info.phone,
                'opay_user_email': customer_info.email,
                'original_customer_data': customer_info.metadata if customer_info else {}
            }
        )
    
    async def _create_invoice_line_items(
        self,
        line_items: List[POSLineItem],
        opay_metadata: Optional[Dict[str, Any]] = None
    ) -> List[InvoiceLineItem]:
        """Create UBL invoice line items from OPay line items."""
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
            # OPay amounts are typically VAT-inclusive
            tax_amount = await self._calculate_line_item_tax(item, vat_inclusive=True)
            
            # Determine item category
            item_category = self._determine_item_category(item, opay_metadata)
            
            invoice_item = InvoiceLineItem(
                line_id=str(idx + 1),
                item_code=item.item_code or f"OPAY-{uuid4().hex[:8]}",
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
                    'opay_order_no': item.metadata.get('opay_order_no') if item.metadata else None,
                    'opay_product_name': item.metadata.get('opay_product_name') if item.metadata else None,
                    'opay_transaction_type': item.metadata.get('opay_transaction_type') if item.metadata else None,
                    'opay_subject': item.metadata.get('opay_subject') if item.metadata else None,
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
        opay_metadata: Optional[Dict[str, Any]] = None
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
                        'calculation_method': 'opay_provided',
                        'vat_inclusive': True
                    }
                )
            ]
        
        # Calculate total taxable amount (VAT-exclusive)
        total_amount = sum(item.total_price for item in line_items)
        
        if total_amount <= 0:
            return []
        
        # Since OPay amounts are typically VAT-inclusive
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
                    'opay_tax_calculation': True,
                    'vat_inclusive': True
                }
            )
        ]
    
    async def _create_invoice_payments(
        self,
        payments: List[PaymentInfo],
        opay_metadata: Optional[Dict[str, Any]] = None
    ) -> List[InvoicePayment]:
        """Create UBL invoice payments from OPay payment data."""
        invoice_payments = []
        
        for payment in payments:
            # Amount should already be in NGN
            amount_ngn = payment.amount
            if payment.currency and payment.currency != 'NGN':
                amount_ngn = await self.currency_converter.convert(
                    payment.amount, payment.currency, 'NGN'
                )
            
            # Map OPay payment method to standard format
            payment_method = self._map_opay_payment_method(payment.payment_method)
            
            # Get fee information if available
            fee_amount = Decimal('0')
            if payment.metadata and payment.metadata.get('opay_fee'):
                fee_amount = Decimal(str(payment.metadata['opay_fee']))
            
            # Get mobile money service if available
            mobile_service = self._get_mobile_money_service(payment, opay_metadata)
            
            invoice_payment = InvoicePayment(
                payment_id=payment.payment_id or str(uuid4()),
                payment_method=payment_method,
                amount=amount_ngn,
                currency='NGN',
                payment_date=payment.payment_date,
                reference=payment.reference,
                status=payment.status or 'completed',
                metadata={
                    'opay_order_no': payment.metadata.get('opay_order_no') if payment.metadata else None,
                    'opay_payment_method': payment.metadata.get('opay_payment_method') if payment.metadata else None,
                    'opay_terminal_id': payment.metadata.get('opay_terminal_id') if payment.metadata else None,
                    'opay_fee': str(fee_amount) if fee_amount > 0 else None,
                    'opay_bank_code': payment.metadata.get('opay_bank_code') if payment.metadata else None,
                    'opay_bank_name': payment.metadata.get('opay_bank_name') if payment.metadata else None,
                    'mobile_money_service': mobile_service,
                    'mobile_payment_integration': True,
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
        opay_metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """Determine item category for Nigerian compliance."""
        if item.metadata and item.metadata.get('opay_transaction_type'):
            transaction_type = item.metadata['opay_transaction_type'].upper()
            
            # Common OPay transaction types
            if 'PAYMENT' in transaction_type:
                return 'service_payment'
            elif 'TRANSFER' in transaction_type:
                return 'financial_service'
            elif 'PURCHASE' in transaction_type:
                return 'goods_purchase'
            elif 'AIRTIME' in transaction_type or 'RECHARGE' in transaction_type:
                return 'telecommunications'
            elif 'BILL' in transaction_type:
                return 'utility_payment'
        
        # Default categorization based on name patterns
        name_lower = item.name.lower()
        
        if any(word in name_lower for word in ['payment', 'service', 'fee']):
            return 'service_payment'
        elif any(word in name_lower for word in ['transfer', 'send', 'wallet']):
            return 'financial_service'
        elif any(word in name_lower for word in ['airtime', 'recharge', 'credit', 'data']):
            return 'telecommunications'
        elif any(word in name_lower for word in ['bill', 'utility', 'electricity', 'water']):
            return 'utility_payment'
        elif any(word in name_lower for word in ['purchase', 'goods', 'product']):
            return 'goods_purchase'
        else:
            return 'mobile_payment'
    
    def _map_opay_payment_method(self, opay_method: str) -> str:
        """Map OPay payment method to standard format."""
        method_mapping = {
            'mobile_wallet': 'mobile_wallet',
            'debit_card': 'debit_card',
            'bank_transfer': 'bank_transfer',
            'ussd': 'ussd',
            'qr_code': 'qr_code',
            'mobile_money': 'mobile_money',
            'cash': 'cash',
            'pos_terminal': 'pos_terminal',
            'other': 'other'
        }
        
        return method_mapping.get(opay_method.lower(), 'other')
    
    def _get_mobile_money_service(
        self, 
        payment: PaymentInfo, 
        opay_metadata: Optional[Dict[str, Any]] = None
    ) -> Optional[str]:
        """Get mobile money service name."""
        if payment.metadata:
            payment_method = payment.metadata.get('opay_payment_method', '').upper()
            if payment_method in self.mobile_money_mapping:
                return self.mobile_money_mapping[payment_method]
        
        # Default to OPay Wallet
        if payment.payment_method == 'mobile_wallet':
            return 'OPay Wallet'
        
        return None
    
    def _generate_invoice_id(self, transaction_id: str) -> str:
        """Generate unique invoice ID from transaction ID."""
        return f"OPAY-{transaction_id}"
    
    def _generate_invoice_number(
        self,
        transaction: POSTransaction,
        opay_metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """Generate human-readable invoice number."""
        timestamp = transaction.timestamp.strftime('%Y%m%d')
        
        if transaction.metadata and transaction.metadata.get('opay_reference'):
            reference = transaction.metadata['opay_reference']
            return f"OPAY-{timestamp}-{reference[-8:]}"
        
        # Use transaction ID
        return f"OPAY-{timestamp}-{transaction.transaction_id[-8:]}"

    async def transform_batch_transactions(
        self,
        transactions: List[POSTransaction],
        merchant_info: Dict[str, Any],
        opay_metadata: Optional[Dict[str, Any]] = None
    ) -> List[UBLInvoice]:
        """
        Transform multiple OPay transactions in batch.
        
        Args:
            transactions: List of POS transactions
            merchant_info: Merchant business information
            opay_metadata: Additional OPay-specific data
            
        Returns:
            List[UBLInvoice]: List of transformed invoices
        """
        invoices = []
        
        for transaction in transactions:
            try:
                invoice = await self.transform_transaction(
                    transaction, merchant_info, opay_metadata
                )
                invoices.append(invoice)
            except Exception as e:
                logger.error(f"Failed to transform transaction {transaction.transaction_id}: {str(e)}")
                continue
        
        logger.info(f"Successfully transformed {len(invoices)}/{len(transactions)} OPay transactions")
        return invoices