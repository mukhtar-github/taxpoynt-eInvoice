"""
PalmPay POS Transaction Transformer
Transforms PalmPay transactions to FIRS-compliant UBL BIS 3.0 invoices.
Handles Nigerian mobile payment and agent network transactions.
"""

import logging
from datetime import datetime
from typing import Any, Dict, List, Optional
from decimal import Decimal
from uuid import uuid4

from ....framework.models.pos_models import POSTransaction
from ....shared.models.invoice_models import (
    UBLInvoice,
    InvoiceHeader,
    InvoiceParty,
    InvoiceLine,
    TaxTotal,
    TaxSubtotal,
    MonetaryTotal,
    PaymentMeans,
    Address,
    Contact
)
from ....shared.utils.ubl_generator import UBLGenerator
from .exceptions import PalmPayTransformationError

logger = logging.getLogger(__name__)


class PalmPayTransactionTransformer:
    """
    PalmPay Transaction to UBL Invoice Transformer
    
    Converts PalmPay POS transactions into FIRS-compliant UBL BIS 3.0 invoices
    with Nigerian mobile payment and agent network compliance.
    """
    
    def __init__(self):
        """Initialize PalmPay transaction transformer."""
        self.ubl_generator = UBLGenerator()
        
        # Nigerian compliance configuration
        self.nigerian_config = {
            'currency': 'NGN',
            'vat_rate': 0.075,  # 7.5% VAT
            'country_code': 'NG',
            'tax_scheme_id': 'VAT',
            'tax_scheme_name': 'Value Added Tax',
            'default_tin': '00000000-0001'
        }
        
        # PalmPay specific configuration
        self.palmpay_config = {
            'supplier_name': 'PalmPay Nigeria',
            'supplier_id': 'PALMPAY-NG',
            'supplier_tin': '12345678-0001',  # PalmPay's TIN
            'scheme_id': 'PALMPAY-POS',
            'invoice_type_code': '380'  # Commercial invoice
        }
        
        logger.info("Initialized PalmPay transaction transformer")
    
    async def transform_transaction(
        self,
        transaction: POSTransaction,
        merchant_info: Dict[str, Any],
        palmpay_metadata: Optional[Dict[str, Any]] = None
    ) -> UBLInvoice:
        """
        Transform PalmPay transaction to UBL invoice.
        
        Args:
            transaction: PalmPay POS transaction
            merchant_info: PalmPay merchant information
            palmpay_metadata: Additional PalmPay-specific metadata
            
        Returns:
            UBLInvoice: FIRS-compliant UBL invoice
            
        Raises:
            PalmPayTransformationError: If transformation fails
        """
        try:
            logger.info(f"Transforming PalmPay transaction: {transaction.transaction_id}")
            
            # Generate unique invoice ID
            invoice_id = f"PALMPAY-{transaction.transaction_id}-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}"
            
            # Create invoice header
            header = self._create_invoice_header(transaction, invoice_id, palmpay_metadata)
            
            # Create supplier party (PalmPay Merchant)
            supplier_party = self._create_supplier_party(merchant_info)
            
            # Create customer party
            customer_party = self._create_customer_party(transaction)
            
            # Create invoice lines
            invoice_lines = self._create_invoice_lines(transaction)
            
            # Create tax totals
            tax_total = self._create_tax_total(transaction)
            
            # Create monetary totals
            legal_monetary_total = self._create_monetary_total(transaction)
            
            # Create payment means
            payment_means = self._create_payment_means(transaction)
            
            # Create UBL invoice
            ubl_invoice = UBLInvoice(
                header=header,
                supplier_party=supplier_party,
                customer_party=customer_party,
                invoice_lines=invoice_lines,
                tax_total=[tax_total] if tax_total else [],
                legal_monetary_total=legal_monetary_total,
                payment_means=payment_means,
                additional_document_references=[],
                delivery_terms=None
            )
            
            # Add PalmPay-specific metadata to UBL
            if palmpay_metadata:
                ubl_invoice.custom_metadata = {
                    'palmpay_order_no': palmpay_metadata.get('order_no'),
                    'palmpay_reference': palmpay_metadata.get('reference'),
                    'mobile_money_integration': True,
                    'agent_network': palmpay_metadata.get('agent_network', False),
                    'transaction_source': transaction.metadata.get('transaction_source', 'standard'),
                    'payment_method': transaction.payment_info.payment_method if transaction.payment_info else 'wallet',
                    'original_currency': transaction.currency_code,
                    'extraction_timestamp': palmpay_metadata.get('extraction_timestamp')
                }
            
            logger.info(f"Successfully transformed PalmPay transaction to UBL: {invoice_id}")
            return ubl_invoice
            
        except Exception as e:
            logger.error(f"Failed to transform PalmPay transaction {transaction.transaction_id}: {str(e)}")
            raise PalmPayTransformationError(
                f"Transformation failed: {str(e)}",
                transaction_id=transaction.transaction_id,
                details={'error': str(e), 'transaction_data': transaction.__dict__}
            )
    
    def _create_invoice_header(
        self,
        transaction: POSTransaction,
        invoice_id: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> InvoiceHeader:
        """Create invoice header for PalmPay transaction."""
        
        # Determine invoice type based on transaction source
        transaction_source = transaction.metadata.get('transaction_source', 'standard') if transaction.metadata else 'standard'
        
        if transaction_source == 'mobile_money':
            invoice_type = 'Mobile Money Payment'
            type_code = '380'  # Commercial invoice
        elif transaction_source == 'agent_network':
            invoice_type = 'Agent Network Payment'
            type_code = '380'  # Commercial invoice
        else:
            invoice_type = 'POS Payment'
            type_code = '380'  # Commercial invoice
        
        return InvoiceHeader(
            invoice_id=invoice_id,
            invoice_type_code=type_code,
            invoice_date=transaction.timestamp.date(),
            due_date=transaction.timestamp.date(),  # Immediate payment
            currency_code=transaction.currency_code,
            note=f"{invoice_type} via PalmPay POS System",
            order_reference=metadata.get('order_no') if metadata else transaction.transaction_id,
            buyer_reference=transaction.customer_info.get('phone', '') if transaction.customer_info else '',
            accounting_supplier_party_reference=self.palmpay_config['supplier_id'],
            supplier_assigned_account_id=metadata.get('merchant_id') if metadata else None
        )
    
    def _create_supplier_party(self, merchant_info: Dict[str, Any]) -> InvoiceParty:
        """Create supplier party from PalmPay merchant information."""
        
        # Use merchant info from PalmPay or defaults
        merchant_name = merchant_info.get('name', 'PalmPay Merchant')
        merchant_id = merchant_info.get('merchantId', merchant_info.get('id', 'PALMPAY-MERCHANT'))
        
        # Create address
        address = Address(
            street_name=merchant_info.get('address', {}).get('street', 'Unknown Street'),
            city_name=merchant_info.get('address', {}).get('city', 'Lagos'),
            postal_zone=merchant_info.get('address', {}).get('postalCode', '100001'),
            country_subentity=merchant_info.get('address', {}).get('state', 'Lagos State'),
            country_identification_code=self.nigerian_config['country_code'],
            country_name='Nigeria'
        )
        
        # Create contact
        contact = Contact(
            name=merchant_info.get('contactPerson', merchant_name),
            telephone=merchant_info.get('phone', ''),
            electronic_mail=merchant_info.get('email', ''),
            note='PalmPay POS Merchant'
        )
        
        return InvoiceParty(
            party_name=merchant_name,
            party_identification=merchant_id,
            party_tax_scheme_id=merchant_info.get('tin', self.palmpay_config['supplier_tin']),
            party_tax_scheme_name=self.nigerian_config['tax_scheme_name'],
            postal_address=address,
            contact=contact,
            party_legal_entity_registration_name=merchant_name,
            party_legal_entity_company_id=merchant_id
        )
    
    def _create_customer_party(self, transaction: POSTransaction) -> InvoiceParty:
        """Create customer party from transaction customer info."""
        
        customer_info = transaction.customer_info or {}
        customer_name = customer_info.get('name', 'PalmPay Customer')
        customer_phone = customer_info.get('phone', '')
        customer_email = customer_info.get('email', '')
        
        # Create basic address (limited info from POS)
        address = Address(
            street_name='Customer Address',
            city_name='Lagos',  # Default to Lagos
            postal_zone='100001',
            country_subentity='Lagos State',
            country_identification_code=self.nigerian_config['country_code'],
            country_name='Nigeria'
        )
        
        # Create contact
        contact = Contact(
            name=customer_name,
            telephone=customer_phone,
            electronic_mail=customer_email,
            note='PalmPay POS Customer'
        )
        
        return InvoiceParty(
            party_name=customer_name,
            party_identification=customer_phone or 'PALMPAY-CUSTOMER',
            party_tax_scheme_id=customer_info.get('tin', self.nigerian_config['default_tin']),
            party_tax_scheme_name=self.nigerian_config['tax_scheme_name'],
            postal_address=address,
            contact=contact,
            party_legal_entity_registration_name=customer_name,
            party_legal_entity_company_id=customer_phone or 'PALMPAY-CUSTOMER'
        )
    
    def _create_invoice_lines(self, transaction: POSTransaction) -> List[InvoiceLine]:
        """Create invoice lines from transaction line items."""
        
        invoice_lines = []
        
        if not transaction.line_items:
            # Create default line item for PalmPay transaction
            line_item = InvoiceLine(
                line_id="1",
                item_name="PalmPay Payment Service",
                item_description="Payment processing service via PalmPay POS",
                quantity=Decimal('1'),
                unit_code='EA',  # Each
                price_amount=Decimal(str(transaction.subtotal)),
                line_extension_amount=Decimal(str(transaction.subtotal)),
                tax_total_amount=Decimal(str(transaction.tax_amount)),
                item_classification_code='77100000-7',  # Financial services
                tax_category_id='S',  # Standard rate
                tax_category_percent=Decimal(str(self.nigerian_config['vat_rate'] * 100)),
                tax_scheme_id=self.nigerian_config['tax_scheme_id'],
                tax_scheme_name=self.nigerian_config['tax_scheme_name']
            )
            invoice_lines.append(line_item)
        else:
            # Convert transaction line items
            for idx, item in enumerate(transaction.line_items, 1):
                line_item = InvoiceLine(
                    line_id=str(idx),
                    item_name=item.item_name,
                    item_description=f"PalmPay {item.category.replace('_', ' ').title()}",
                    quantity=item.quantity,
                    unit_code='EA',
                    price_amount=Decimal(str(item.unit_price)),
                    line_extension_amount=Decimal(str(item.total_amount - item.tax_amount)),
                    tax_total_amount=Decimal(str(item.tax_amount)),
                    item_classification_code=self._get_item_classification_code(item.category),
                    tax_category_id='S',  # Standard rate
                    tax_category_percent=Decimal(str(item.tax_rate * 100)) if item.tax_rate else Decimal(str(self.nigerian_config['vat_rate'] * 100)),
                    tax_scheme_id=self.nigerian_config['tax_scheme_id'],
                    tax_scheme_name=self.nigerian_config['tax_scheme_name']
                )
                invoice_lines.append(line_item)
        
        return invoice_lines
    
    def _create_tax_total(self, transaction: POSTransaction) -> Optional[TaxTotal]:
        """Create tax total from transaction tax information."""
        
        if transaction.tax_amount <= 0:
            return None
        
        # Create tax subtotal
        tax_subtotal = TaxSubtotal(
            taxable_amount=Decimal(str(transaction.subtotal)),
            tax_amount=Decimal(str(transaction.tax_amount)),
            tax_category_id='S',  # Standard rate
            tax_category_percent=Decimal(str(self.nigerian_config['vat_rate'] * 100)),
            tax_scheme_id=self.nigerian_config['tax_scheme_id'],
            tax_scheme_name=self.nigerian_config['tax_scheme_name']
        )
        
        return TaxTotal(
            tax_amount=Decimal(str(transaction.tax_amount)),
            tax_subtotals=[tax_subtotal]
        )
    
    def _create_monetary_total(self, transaction: POSTransaction) -> MonetaryTotal:
        """Create monetary total from transaction amounts."""
        
        return MonetaryTotal(
            line_extension_amount=Decimal(str(transaction.subtotal)),
            tax_exclusive_amount=Decimal(str(transaction.subtotal)),
            tax_inclusive_amount=Decimal(str(transaction.total_amount)),
            allowance_total_amount=Decimal('0'),
            charge_total_amount=Decimal('0'),
            payable_amount=Decimal(str(transaction.total_amount))
        )
    
    def _create_payment_means(self, transaction: POSTransaction) -> List[PaymentMeans]:
        """Create payment means from transaction payment info."""
        
        payment_info = transaction.payment_info
        if not payment_info:
            return []
        
        # Map PalmPay payment method to UBL payment means code
        payment_means_code = self._get_payment_means_code(payment_info.payment_method)
        
        # Get payment method name
        payment_method_name = self._get_payment_method_name(payment_info.payment_method)
        
        payment_means = PaymentMeans(
            payment_means_code=payment_means_code,
            payment_due_date=transaction.timestamp.date(),
            payment_channel_code='ONLINE',
            instruction_id=payment_info.payment_reference,
            instruction_note=f"{payment_method_name} payment via PalmPay POS",
            payment_id=payment_info.payment_reference,
            payee_financial_account_id=transaction.metadata.get('palmpay_merchant_id') if transaction.metadata else None,
            payee_financial_account_name='PalmPay Merchant Account'
        )
        
        return [payment_means]
    
    def _get_item_classification_code(self, category: str) -> str:
        """Get UNSPSC classification code for item category."""
        
        classification_mapping = {
            'payment_service': '77100000-7',  # Financial services
            'mobile_money_payment': '77100000-7',  # Financial services
            'agent_network_payment': '77100000-7',  # Financial services
            'goods_purchase': '12000000-6',  # General goods
            'service_payment': '77000000-0',  # General services
            'utility_payment': '77100000-7',  # Financial services
            'telecommunications': '32000000-0',  # Telecommunications
            'default': '77100000-7'  # Financial services
        }
        
        return classification_mapping.get(category, classification_mapping['default'])
    
    def _get_payment_means_code(self, payment_method: str) -> str:
        """Get UBL payment means code for PalmPay payment method."""
        
        payment_code_mapping = {
            'wallet': '42',  # Payment to bank account
            'mobile_wallet': '42',  # Payment to bank account
            'debit_card': '48',  # Bank card
            'bank_transfer': '30',  # Credit transfer
            'ussd': '42',  # Payment to bank account
            'qr_code': '42',  # Payment to bank account
            'mobile_money': '42',  # Payment to bank account
            'cash': '10',  # Cash
            'pos_terminal': '48',  # Bank card
            'default': '42'  # Payment to bank account
        }
        
        return payment_code_mapping.get(payment_method, payment_code_mapping['default'])
    
    def _get_payment_method_name(self, payment_method: str) -> str:
        """Get human-readable payment method name."""
        
        method_names = {
            'wallet': 'PalmPay Wallet',
            'mobile_wallet': 'Mobile Wallet',
            'debit_card': 'Debit Card',
            'bank_transfer': 'Bank Transfer',
            'ussd': 'USSD Payment',
            'qr_code': 'QR Code Payment',
            'mobile_money': 'Mobile Money',
            'cash': 'Cash Payment',
            'pos_terminal': 'POS Terminal',
            'default': 'Electronic Payment'
        }
        
        return method_names.get(payment_method, method_names['default'])
    
    async def transform_batch_transactions(
        self,
        transactions: List[POSTransaction],
        merchant_info: Dict[str, Any],
        palmpay_metadata: Optional[Dict[str, Any]] = None
    ) -> List[UBLInvoice]:
        """
        Transform multiple PalmPay transactions to UBL invoices.
        
        Args:
            transactions: List of PalmPay transactions
            merchant_info: PalmPay merchant information
            palmpay_metadata: Additional metadata
            
        Returns:
            List[UBLInvoice]: List of UBL invoices
        """
        try:
            logger.info(f"Transforming batch of {len(transactions)} PalmPay transactions")
            
            invoices = []
            for transaction in transactions:
                try:
                    invoice = await self.transform_transaction(
                        transaction,
                        merchant_info,
                        palmpay_metadata
                    )
                    invoices.append(invoice)
                    
                except Exception as e:
                    logger.error(f"Failed to transform transaction {transaction.transaction_id}: {str(e)}")
                    continue
            
            logger.info(f"Successfully transformed {len(invoices)} PalmPay transactions")
            return invoices
            
        except Exception as e:
            logger.error(f"Batch transformation failed: {str(e)}")
            raise PalmPayTransformationError(f"Batch transformation failed: {str(e)}")
    
    def validate_ubl_invoice(self, invoice: UBLInvoice) -> bool:
        """
        Validate UBL invoice for FIRS compliance.
        
        Args:
            invoice: UBL invoice to validate
            
        Returns:
            bool: True if valid
        """
        try:
            # Basic validation checks
            if not invoice.header or not invoice.header.invoice_id:
                logger.error("Invoice missing header or invoice ID")
                return False
            
            if not invoice.supplier_party or not invoice.customer_party:
                logger.error("Invoice missing supplier or customer party")
                return False
            
            if not invoice.invoice_lines:
                logger.error("Invoice missing invoice lines")
                return False
            
            if not invoice.legal_monetary_total:
                logger.error("Invoice missing monetary totals")
                return False
            
            # Currency validation
            if invoice.header.currency_code != self.nigerian_config['currency']:
                logger.error(f"Invalid currency code: {invoice.header.currency_code}")
                return False
            
            # Tax validation for Nigerian VAT
            if invoice.tax_total:
                for tax_total in invoice.tax_total:
                    for tax_subtotal in tax_total.tax_subtotals:
                        if tax_subtotal.tax_scheme_id != self.nigerian_config['tax_scheme_id']:
                            logger.error(f"Invalid tax scheme: {tax_subtotal.tax_scheme_id}")
                            return False
            
            logger.info(f"UBL invoice validation passed: {invoice.header.invoice_id}")
            return True
            
        except Exception as e:
            logger.error(f"UBL invoice validation failed: {str(e)}")
            return False