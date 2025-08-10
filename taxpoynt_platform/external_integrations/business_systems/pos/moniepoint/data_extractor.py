"""
Moniepoint POS Data Extractor
Extracts and transforms POS transaction data from Moniepoint REST API
into standardized POSTransaction objects for TaxPoynt eInvoice processing.
"""

import logging
from datetime import datetime
from decimal import Decimal, ROUND_HALF_UP
from typing import Any, Dict, List, Optional
from uuid import uuid4

from ....framework.models.pos_models import (
    CustomerInfo,
    POSLineItem,
    POSTransaction,
    PaymentInfo,
    TaxInfo,
    WebhookPayload
)
from ....shared.utils.data_transformer import DataTransformer
from ....shared.utils.validation_utils import ValidationUtils
from .rest_client import MoniepointRestClient
from .exceptions import MoniepointDataExtractionError, create_moniepoint_exception

logger = logging.getLogger(__name__)


class MoniepointDataExtractor:
    """
    Moniepoint POS Data Extractor
    
    Extracts transaction data from Moniepoint POS REST API and transforms it
    into standardized POSTransaction objects with Nigerian banking integration.
    """
    
    def __init__(self, rest_client: MoniepointRestClient):
        """
        Initialize Moniepoint data extractor.
        
        Args:
            rest_client: Moniepoint REST API client
        """
        self.rest_client = rest_client
        self.data_transformer = DataTransformer()
        self.validator = ValidationUtils()
        
        # Moniepoint-specific configuration
        self.moniepoint_config = {
            'default_currency': 'NGN',
            'date_format': '%Y-%m-%dT%H:%M:%S.%fZ',
            'timezone': 'Africa/Lagos',
            'extract_batch_size': 100,
            'max_concurrent_extractions': 5
        }
        
        # Payment method mapping
        self.payment_method_mapping = {
            'CARD': 'debit_card',
            'BANK_TRANSFER': 'bank_transfer',
            'USSD': 'ussd',
            'QR': 'qr_code',
            'NIP': 'bank_transfer',
            'MOBILE_MONEY': 'mobile_money',
            'CASH': 'cash',
            'OTHER': 'other'
        }
        
        # Transaction status mapping
        self.status_mapping = {
            'PAID': 'completed',
            'PENDING': 'pending',
            'FAILED': 'failed',
            'CANCELLED': 'cancelled',
            'EXPIRED': 'expired',
            'REVERSED': 'reversed'
        }
        
        logger.info("Initialized Moniepoint data extractor")
    
    async def extract_transactions(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        limit: Optional[int] = None,
        merchant_id: Optional[str] = None
    ) -> List[POSTransaction]:
        """
        Extract transactions from Moniepoint POS for a date range.
        
        Args:
            start_date: Start date for extraction
            end_date: End date for extraction
            limit: Maximum number of transactions to extract
            merchant_id: Specific merchant ID
            
        Returns:
            List[POSTransaction]: List of standardized transactions
            
        Raises:
            MoniepointDataExtractionError: If extraction fails
        """
        try:
            logger.info(f"Extracting Moniepoint transactions for merchant {merchant_id}")
            
            # Get transactions from Moniepoint API
            transactions = await self.rest_client.get_transactions(
                start_date=start_date,
                end_date=end_date,
                size=limit,
                merchant_id=merchant_id
            )
            
            if not transactions:
                logger.info("No Moniepoint transactions found for the specified criteria")
                return []
            
            # Transform transactions to POS transaction objects
            pos_transactions = []
            for transaction_data in transactions:
                try:
                    # Transform transaction to POS transaction
                    pos_transaction = await self._transform_transaction_to_pos(
                        transaction_data, merchant_id
                    )
                    
                    if pos_transaction:
                        pos_transactions.append(pos_transaction)
                        
                except Exception as e:
                    logger.error(f"Failed to process Moniepoint transaction {transaction_data.get('transactionReference', 'unknown')}: {str(e)}")
                    continue
            
            logger.info(f"Successfully extracted {len(pos_transactions)} Moniepoint transactions")
            return pos_transactions
            
        except Exception as e:
            logger.error(f"Moniepoint transaction extraction failed: {str(e)}")
            raise MoniepointDataExtractionError(f"Extraction failed: {str(e)}", merchant_id)
    
    async def get_single_transaction(
        self,
        transaction_reference: str
    ) -> Optional[POSTransaction]:
        """
        Extract a single transaction by reference.
        
        Args:
            transaction_reference: Moniepoint transaction reference
            
        Returns:
            POSTransaction: Standardized transaction or None if not found
        """
        try:
            logger.info(f"Extracting single Moniepoint transaction: {transaction_reference}")
            
            # Get transaction details
            transaction_data = await self.rest_client.get_transaction_details(transaction_reference)
            if not transaction_data:
                logger.warning(f"Moniepoint transaction not found: {transaction_reference}")
                return None
            
            # Transform to POS transaction
            pos_transaction = await self._transform_transaction_to_pos(transaction_data)
            
            if pos_transaction:
                logger.info(f"Successfully extracted Moniepoint transaction: {transaction_reference}")
            
            return pos_transaction
            
        except Exception as e:
            logger.error(f"Failed to extract Moniepoint transaction {transaction_reference}: {str(e)}")
            return None
    
    async def extract_transaction_from_webhook(
        self,
        payload: WebhookPayload
    ) -> Optional[POSTransaction]:
        """
        Extract transaction from Moniepoint webhook payload.
        
        Args:
            payload: Moniepoint webhook payload
            
        Returns:
            POSTransaction: Standardized transaction or None
        """
        try:
            logger.info(f"Extracting transaction from Moniepoint webhook: {payload.event_type}")
            
            # Get transaction data from webhook payload
            webhook_data = payload.data
            transaction_reference = webhook_data.get('transactionReference')
            
            if not transaction_reference:
                logger.warning("Webhook missing transaction reference")
                return None
            
            # For some events, we might have complete data in webhook
            if payload.event_type in ['TRANSACTION_COMPLETED', 'PAYMENT_RECEIVED']:
                # Transform webhook data directly
                pos_transaction = await self._transform_transaction_to_pos(webhook_data)
            else:
                # Get full transaction details from API
                transaction_data = await self.rest_client.get_transaction_details(transaction_reference)
                if not transaction_data:
                    # Fall back to webhook data
                    transaction_data = webhook_data
                
                pos_transaction = await self._transform_transaction_to_pos(transaction_data)
            
            if pos_transaction:
                # Add webhook metadata
                pos_transaction.metadata = pos_transaction.metadata or {}
                pos_transaction.metadata.update({
                    'webhook_event': payload.event_type,
                    'webhook_timestamp': payload.timestamp.isoformat() if payload.timestamp else None,
                    'webhook_source': 'moniepoint'
                })
            
            logger.info(f"Successfully extracted transaction from Moniepoint webhook: {transaction_reference}")
            return pos_transaction
            
        except Exception as e:
            logger.error(f"Failed to extract transaction from Moniepoint webhook: {str(e)}")
            return None
    
    # Private transformation methods
    
    async def _transform_transaction_to_pos(
        self,
        transaction_data: Dict[str, Any],
        merchant_id: Optional[str] = None
    ) -> Optional[POSTransaction]:
        """Transform Moniepoint transaction data to POSTransaction."""
        try:
            transaction_reference = transaction_data.get('transactionReference')
            if not transaction_reference:
                raise MoniepointDataExtractionError("Transaction missing reference")
            
            # Basic transaction info
            amount = Decimal(str(transaction_data.get('amountPaid', 0)))
            currency = transaction_data.get('currencyCode', self.moniepoint_config['default_currency'])
            
            # Parse timestamps
            created_on = transaction_data.get('createdOn')
            paid_on = transaction_data.get('paidOn')
            timestamp = self._parse_moniepoint_timestamp(paid_on or created_on)
            if not timestamp:
                timestamp = datetime.utcnow()
            
            # Extract customer information
            customer_info = await self._extract_customer_info(transaction_data)
            
            # Create line items (Moniepoint typically has single item per transaction)
            line_items = await self._extract_line_items(transaction_data)
            
            # Extract payments
            payments = await self._extract_payments(transaction_data)
            
            # Calculate tax amount (if available)
            tax_amount = self._calculate_tax_amount(transaction_data, amount)
            
            # Create POS transaction
            pos_transaction = POSTransaction(
                transaction_id=transaction_reference,
                timestamp=timestamp,
                total_amount=amount,
                tax_amount=tax_amount,
                currency=currency,
                line_items=line_items,
                payments=payments,
                customer_info=customer_info,
                metadata={
                    'moniepoint_merchant_id': merchant_id or self.rest_client.auth_manager.merchant_id,
                    'moniepoint_transaction_reference': transaction_reference,
                    'moniepoint_payment_reference': transaction_data.get('paymentReference'),
                    'moniepoint_order_reference': transaction_data.get('orderReference'),
                    'moniepoint_product_code': transaction_data.get('productCode'),
                    'moniepoint_payment_method': transaction_data.get('paymentMethod'),
                    'moniepoint_channel': transaction_data.get('channel'),
                    'moniepoint_created_on': created_on,
                    'moniepoint_paid_on': paid_on,
                    'moniepoint_status': transaction_data.get('paymentStatus'),
                    'extraction_timestamp': datetime.utcnow().isoformat()
                }
            )
            
            return pos_transaction
            
        except Exception as e:
            logger.error(f"Failed to transform Moniepoint transaction to POS: {str(e)}")
            raise MoniepointDataExtractionError(f"Transaction transformation failed: {str(e)}", transaction_data.get('transactionReference'))
    
    async def _extract_customer_info(self, transaction_data: Dict[str, Any]) -> Optional[CustomerInfo]:
        """Extract customer information from Moniepoint transaction."""
        try:
            customer_name = transaction_data.get('customerName')
            customer_email = transaction_data.get('customerEmail')
            
            if not customer_name and not customer_email:
                return None
            
            customer_id = transaction_data.get('customerReference', str(uuid4()))
            
            return CustomerInfo(
                customer_id=customer_id,
                name=customer_name or 'Unknown Customer',
                email=customer_email,
                phone=transaction_data.get('customerPhone'),
                customer_type='individual',  # Moniepoint typically handles individual customers
                metadata={
                    'moniepoint_customer_reference': customer_id,
                    'moniepoint_customer_name': customer_name,
                    'moniepoint_customer_email': customer_email,
                    'moniepoint_customer_phone': transaction_data.get('customerPhone')
                }
            )
            
        except Exception as e:
            logger.error(f"Failed to extract customer info: {str(e)}")
            return None
    
    async def _extract_line_items(self, transaction_data: Dict[str, Any]) -> List[POSLineItem]:
        """Extract line items from Moniepoint transaction."""
        line_items = []
        
        try:
            # Moniepoint transactions are typically single-item
            amount = Decimal(str(transaction_data.get('amountPaid', 0)))
            currency = transaction_data.get('currencyCode', self.moniepoint_config['default_currency'])
            
            # Get product/service information
            product_code = transaction_data.get('productCode', 'DEFAULT')
            product_name = transaction_data.get('productName') or transaction_data.get('paymentDescription') or 'Payment'
            
            line_item = POSLineItem(
                item_code=product_code,
                name=product_name,
                description=transaction_data.get('paymentDescription') or product_name,
                quantity=Decimal('1'),  # Moniepoint typically has quantity of 1
                unit_price=amount,
                total_price=amount,
                currency=currency,
                metadata={
                    'moniepoint_product_code': product_code,
                    'moniepoint_product_name': product_name,
                    'moniepoint_payment_description': transaction_data.get('paymentDescription'),
                    'moniepoint_order_reference': transaction_data.get('orderReference')
                }
            )
            
            line_items.append(line_item)
            
            logger.info("Extracted 1 line item from Moniepoint transaction")
            return line_items
            
        except Exception as e:
            logger.error(f"Failed to extract line items: {str(e)}")
            return []
    
    async def _extract_payments(self, transaction_data: Dict[str, Any]) -> List[PaymentInfo]:
        """Extract payment information from Moniepoint transaction."""
        payments = []
        
        try:
            payment_reference = transaction_data.get('paymentReference', str(uuid4()))
            payment_method = transaction_data.get('paymentMethod', 'OTHER')
            
            # Map Moniepoint payment method to standard format
            mapped_method = self.payment_method_mapping.get(payment_method, 'other')
            
            # Amount
            amount = Decimal(str(transaction_data.get('amountPaid', 0)))
            currency = transaction_data.get('currencyCode', self.moniepoint_config['default_currency'])
            
            # Payment date
            paid_on = transaction_data.get('paidOn')
            payment_date = self._parse_moniepoint_timestamp(paid_on) or datetime.utcnow()
            
            # Payment status
            payment_status = transaction_data.get('paymentStatus', 'PENDING')
            mapped_status = self.status_mapping.get(payment_status, 'pending')
            
            payment_info = PaymentInfo(
                payment_id=payment_reference,
                payment_method=mapped_method,
                amount=amount,
                currency=currency,
                payment_date=payment_date,
                reference=transaction_data.get('transactionReference'),
                status=mapped_status,
                metadata={
                    'moniepoint_payment_reference': payment_reference,
                    'moniepoint_payment_method': payment_method,
                    'moniepoint_payment_status': payment_status,
                    'moniepoint_channel': transaction_data.get('channel'),
                    'moniepoint_settlement_amount': transaction_data.get('settlementAmount'),
                    'moniepoint_fee': transaction_data.get('fee'),
                    'moniepoint_paid_on': paid_on
                }
            )
            
            payments.append(payment_info)
            
            logger.info("Extracted 1 payment from Moniepoint transaction")
            return payments
            
        except Exception as e:
            logger.error(f"Failed to extract payments: {str(e)}")
            return []
    
    def _calculate_tax_amount(self, transaction_data: Dict[str, Any], total_amount: Decimal) -> Decimal:
        """Calculate tax amount from Moniepoint transaction."""
        try:
            # Check if VAT is specified separately
            vat_amount = transaction_data.get('vatAmount')
            if vat_amount:
                return Decimal(str(vat_amount))
            
            # Calculate 7.5% VAT from total amount (inclusive)
            # VAT = (Total Amount * VAT Rate) / (1 + VAT Rate)
            vat_rate = Decimal('0.075')  # 7.5%
            vat_amount = (total_amount * vat_rate) / (Decimal('1') + vat_rate)
            
            return vat_amount.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
            
        except Exception:
            return Decimal('0')
    
    def _parse_moniepoint_timestamp(self, timestamp_str: Optional[str]) -> Optional[datetime]:
        """Parse Moniepoint timestamp string to datetime."""
        if not timestamp_str:
            return None
        
        try:
            # Moniepoint typically uses ISO format
            if 'T' in timestamp_str:
                # Remove timezone info if present for parsing
                clean_timestamp = timestamp_str.replace('Z', '').split('+')[0].split('.')[0]
                return datetime.fromisoformat(clean_timestamp)
            else:
                # Handle other formats
                return datetime.strptime(timestamp_str, '%Y-%m-%d %H:%M:%S')
        except Exception as e:
            logger.warning(f"Failed to parse Moniepoint timestamp '{timestamp_str}': {str(e)}")
            return None
    
    async def extract_account_transactions(
        self,
        account_reference: str,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        limit: Optional[int] = None
    ) -> List[POSTransaction]:
        """
        Extract transactions for a specific account.
        
        Args:
            account_reference: Account reference
            start_date: Start date for extraction
            end_date: End date for extraction
            limit: Maximum number of transactions to extract
            
        Returns:
            List[POSTransaction]: List of account transactions
        """
        try:
            logger.info(f"Extracting Moniepoint account transactions for {account_reference}")
            
            # Get account transactions from Moniepoint API
            transactions = await self.rest_client.get_account_transactions(
                account_reference=account_reference,
                start_date=start_date,
                end_date=end_date,
                size=limit
            )
            
            if not transactions:
                logger.info("No account transactions found for the specified criteria")
                return []
            
            # Transform transactions to POS transaction objects
            pos_transactions = []
            for transaction_data in transactions:
                try:
                    pos_transaction = await self._transform_transaction_to_pos(transaction_data)
                    if pos_transaction:
                        # Add account-specific metadata
                        pos_transaction.metadata = pos_transaction.metadata or {}
                        pos_transaction.metadata['moniepoint_account_reference'] = account_reference
                        pos_transactions.append(pos_transaction)
                        
                except Exception as e:
                    logger.error(f"Failed to process account transaction: {str(e)}")
                    continue
            
            logger.info(f"Successfully extracted {len(pos_transactions)} account transactions")
            return pos_transactions
            
        except Exception as e:
            logger.error(f"Account transaction extraction failed: {str(e)}")
            raise MoniepointDataExtractionError(f"Account extraction failed: {str(e)}", account_reference)