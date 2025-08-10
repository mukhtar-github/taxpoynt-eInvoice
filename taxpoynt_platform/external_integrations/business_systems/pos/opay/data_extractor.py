"""
OPay POS Data Extractor
Extracts and transforms POS transaction data from OPay REST API
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
from .rest_client import OPayRestClient
from .exceptions import OPayDataExtractionError, create_opay_exception

logger = logging.getLogger(__name__)


class OPayDataExtractor:
    """
    OPay POS Data Extractor
    
    Extracts transaction data from OPay POS REST API and transforms it
    into standardized POSTransaction objects with Nigerian mobile money
    and payment system integration.
    """
    
    def __init__(self, rest_client: OPayRestClient):
        """
        Initialize OPay data extractor.
        
        Args:
            rest_client: OPay REST API client
        """
        self.rest_client = rest_client
        self.data_transformer = DataTransformer()
        self.validator = ValidationUtils()
        
        # OPay-specific configuration
        self.opay_config = {
            'default_currency': 'NGN',
            'date_format': '%Y-%m-%d %H:%M:%S',
            'timezone': 'Africa/Lagos',
            'extract_batch_size': 100,
            'max_concurrent_extractions': 5
        }
        
        # Payment method mapping
        self.payment_method_mapping = {
            'WALLET': 'mobile_wallet',
            'CARD': 'debit_card',
            'BANK_TRANSFER': 'bank_transfer',
            'USSD': 'ussd',
            'QR_CODE': 'qr_code',
            'MOBILE_MONEY': 'mobile_money',
            'CASH': 'cash',
            'POS': 'pos_terminal',
            'OTHER': 'other'
        }
        
        # Transaction status mapping
        self.status_mapping = {
            'SUCCESS': 'completed',
            'PENDING': 'pending',
            'FAILED': 'failed',
            'CANCELLED': 'cancelled',
            'EXPIRED': 'expired',
            'PROCESSING': 'processing'
        }
        
        # Transaction type mapping
        self.transaction_type_mapping = {
            'PAYMENT': 'payment',
            'REFUND': 'refund',
            'TRANSFER': 'transfer',
            'WITHDRAWAL': 'withdrawal',
            'DEPOSIT': 'deposit',
            'PURCHASE': 'purchase'
        }
        
        logger.info("Initialized OPay data extractor")
    
    async def extract_transactions(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        limit: Optional[int] = None,
        transaction_type: Optional[str] = None
    ) -> List[POSTransaction]:
        """
        Extract transactions from OPay POS for a date range.
        
        Args:
            start_date: Start date for extraction
            end_date: End date for extraction
            limit: Maximum number of transactions to extract
            transaction_type: Type of transactions to extract
            
        Returns:
            List[POSTransaction]: List of standardized transactions
            
        Raises:
            OPayDataExtractionError: If extraction fails
        """
        try:
            logger.info("Extracting OPay transactions")
            
            # Get transactions from OPay API
            all_transactions = []
            
            # Get regular merchant transactions
            merchant_transactions = await self.rest_client.get_transactions(
                start_date=start_date,
                end_date=end_date,
                size=limit,
                transaction_type=transaction_type
            )
            all_transactions.extend(merchant_transactions)
            
            # Get POS terminal transactions if available
            try:
                pos_transactions = await self.rest_client.get_pos_transactions(
                    start_date=start_date,
                    end_date=end_date,
                    size=limit
                )
                all_transactions.extend(pos_transactions)
            except Exception as e:
                logger.warning(f"Failed to get POS transactions: {str(e)}")
            
            # Get wallet transactions
            try:
                wallet_transactions = await self.rest_client.get_wallet_transactions(
                    start_date=start_date,
                    end_date=end_date,
                    size=limit
                )
                all_transactions.extend(wallet_transactions)
            except Exception as e:
                logger.warning(f"Failed to get wallet transactions: {str(e)}")
            
            if not all_transactions:
                logger.info("No OPay transactions found for the specified criteria")
                return []
            
            # Transform transactions to POS transaction objects
            pos_transactions = []
            for transaction_data in all_transactions:
                try:
                    # Transform transaction to POS transaction
                    pos_transaction = await self._transform_transaction_to_pos(transaction_data)
                    
                    if pos_transaction:
                        pos_transactions.append(pos_transaction)
                        
                except Exception as e:
                    logger.error(f"Failed to process OPay transaction {transaction_data.get('orderNo', 'unknown')}: {str(e)}")
                    continue
            
            logger.info(f"Successfully extracted {len(pos_transactions)} OPay transactions")
            return pos_transactions
            
        except Exception as e:
            logger.error(f"OPay transaction extraction failed: {str(e)}")
            raise OPayDataExtractionError(f"Extraction failed: {str(e)}")
    
    async def get_single_transaction(
        self,
        order_no: str
    ) -> Optional[POSTransaction]:
        """
        Extract a single transaction by order number.
        
        Args:
            order_no: OPay order number
            
        Returns:
            POSTransaction: Standardized transaction or None if not found
        """
        try:
            logger.info(f"Extracting single OPay transaction: {order_no}")
            
            # Get transaction details
            transaction_data = await self.rest_client.get_transaction_details(order_no)
            if not transaction_data:
                logger.warning(f"OPay transaction not found: {order_no}")
                return None
            
            # Transform to POS transaction
            pos_transaction = await self._transform_transaction_to_pos(transaction_data)
            
            if pos_transaction:
                logger.info(f"Successfully extracted OPay transaction: {order_no}")
            
            return pos_transaction
            
        except Exception as e:
            logger.error(f"Failed to extract OPay transaction {order_no}: {str(e)}")
            return None
    
    async def extract_transaction_from_webhook(
        self,
        payload: WebhookPayload
    ) -> Optional[POSTransaction]:
        """
        Extract transaction from OPay webhook payload.
        
        Args:
            payload: OPay webhook payload
            
        Returns:
            POSTransaction: Standardized transaction or None
        """
        try:
            logger.info(f"Extracting transaction from OPay webhook: {payload.event_type}")
            
            # Get transaction data from webhook payload
            webhook_data = payload.data
            order_no = webhook_data.get('orderNo') or webhook_data.get('reference')
            
            if not order_no:
                logger.warning("Webhook missing order number or reference")
                return None
            
            # For some events, we might have complete data in webhook
            if payload.event_type in ['PAYMENT_SUCCESS', 'TRANSACTION_COMPLETED']:
                # Transform webhook data directly
                pos_transaction = await self._transform_transaction_to_pos(webhook_data)
            else:
                # Get full transaction details from API
                transaction_data = await self.rest_client.get_transaction_details(order_no)
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
                    'webhook_source': 'opay'
                })
            
            logger.info(f"Successfully extracted transaction from OPay webhook: {order_no}")
            return pos_transaction
            
        except Exception as e:
            logger.error(f"Failed to extract transaction from OPay webhook: {str(e)}")
            return None
    
    # Private transformation methods
    
    async def _transform_transaction_to_pos(
        self,
        transaction_data: Dict[str, Any]
    ) -> Optional[POSTransaction]:
        """Transform OPay transaction data to POSTransaction."""
        try:
            order_no = transaction_data.get('orderNo') or transaction_data.get('reference')
            if not order_no:
                raise OPayDataExtractionError("Transaction missing order number")
            
            # Basic transaction info
            amount = Decimal(str(transaction_data.get('amount', 0)))
            if 'amount' in transaction_data and transaction_data['amount'] > 100:
                # OPay sometimes returns amounts in kobo, convert to naira
                amount = amount / 100
            
            currency = transaction_data.get('currency', self.opay_config['default_currency'])
            
            # Parse timestamps
            created_at = transaction_data.get('createdAt') or transaction_data.get('createTime')
            completed_at = transaction_data.get('completedAt') or transaction_data.get('finishTime')
            timestamp = self._parse_opay_timestamp(completed_at or created_at)
            if not timestamp:
                timestamp = datetime.utcnow()
            
            # Extract customer information
            customer_info = await self._extract_customer_info(transaction_data)
            
            # Create line items (OPay typically has single item per transaction)
            line_items = await self._extract_line_items(transaction_data)
            
            # Extract payments
            payments = await self._extract_payments(transaction_data)
            
            # Calculate tax amount (if available)
            tax_amount = self._calculate_tax_amount(transaction_data, amount)
            
            # Create POS transaction
            pos_transaction = POSTransaction(
                transaction_id=order_no,
                timestamp=timestamp,
                total_amount=amount,
                tax_amount=tax_amount,
                currency=currency,
                line_items=line_items,
                payments=payments,
                customer_info=customer_info,
                metadata={
                    'opay_order_no': order_no,
                    'opay_reference': transaction_data.get('reference'),
                    'opay_transaction_type': transaction_data.get('type'),
                    'opay_status': transaction_data.get('status'),
                    'opay_payment_method': transaction_data.get('payMethod'),
                    'opay_terminal_id': transaction_data.get('terminalId'),
                    'opay_merchant_id': transaction_data.get('merchantId'),
                    'opay_created_at': created_at,
                    'opay_completed_at': completed_at,
                    'opay_fee': transaction_data.get('fee', 0),
                    'extraction_timestamp': datetime.utcnow().isoformat()
                }
            )
            
            return pos_transaction
            
        except Exception as e:
            logger.error(f"Failed to transform OPay transaction to POS: {str(e)}")
            raise OPayDataExtractionError(f"Transaction transformation failed: {str(e)}", transaction_data.get('orderNo'))
    
    async def _extract_customer_info(self, transaction_data: Dict[str, Any]) -> Optional[CustomerInfo]:
        """Extract customer information from OPay transaction."""
        try:
            customer_name = transaction_data.get('userName') or transaction_data.get('customerName')
            customer_phone = transaction_data.get('userPhone') or transaction_data.get('customerPhone')
            customer_email = transaction_data.get('userEmail') or transaction_data.get('customerEmail')
            
            if not customer_name and not customer_phone and not customer_email:
                return None
            
            customer_id = transaction_data.get('userId', str(uuid4()))
            
            return CustomerInfo(
                customer_id=customer_id,
                name=customer_name or 'Unknown Customer',
                email=customer_email,
                phone=customer_phone,
                customer_type='individual',  # OPay typically handles individual customers
                metadata={
                    'opay_user_id': customer_id,
                    'opay_user_name': customer_name,
                    'opay_user_phone': customer_phone,
                    'opay_user_email': customer_email
                }
            )
            
        except Exception as e:
            logger.error(f"Failed to extract customer info: {str(e)}")
            return None
    
    async def _extract_line_items(self, transaction_data: Dict[str, Any]) -> List[POSLineItem]:
        """Extract line items from OPay transaction."""
        line_items = []
        
        try:
            # OPay transactions are typically single-item
            amount = Decimal(str(transaction_data.get('amount', 0)))
            if amount > 100:
                # Convert from kobo to naira if necessary
                amount = amount / 100
                
            currency = transaction_data.get('currency', self.opay_config['default_currency'])
            
            # Get product/service information
            product_name = (transaction_data.get('productName') or 
                          transaction_data.get('subject') or 
                          transaction_data.get('remark') or 
                          'OPay Payment')
            
            order_no = transaction_data.get('orderNo', 'DEFAULT')
            
            line_item = POSLineItem(
                item_code=order_no,
                name=product_name,
                description=transaction_data.get('remark') or product_name,
                quantity=Decimal('1'),  # OPay typically has quantity of 1
                unit_price=amount,
                total_price=amount,
                currency=currency,
                metadata={
                    'opay_order_no': order_no,
                    'opay_product_name': product_name,
                    'opay_subject': transaction_data.get('subject'),
                    'opay_remark': transaction_data.get('remark'),
                    'opay_transaction_type': transaction_data.get('type')
                }
            )
            
            line_items.append(line_item)
            
            logger.info("Extracted 1 line item from OPay transaction")
            return line_items
            
        except Exception as e:
            logger.error(f"Failed to extract line items: {str(e)}")
            return []
    
    async def _extract_payments(self, transaction_data: Dict[str, Any]) -> List[PaymentInfo]:
        """Extract payment information from OPay transaction."""
        payments = []
        
        try:
            order_no = transaction_data.get('orderNo', str(uuid4()))
            payment_method = transaction_data.get('payMethod', 'OTHER')
            
            # Map OPay payment method to standard format
            mapped_method = self.payment_method_mapping.get(payment_method, 'other')
            
            # Amount
            amount = Decimal(str(transaction_data.get('amount', 0)))
            if amount > 100:
                # Convert from kobo to naira if necessary
                amount = amount / 100
                
            currency = transaction_data.get('currency', self.opay_config['default_currency'])
            
            # Payment date
            completed_at = transaction_data.get('completedAt') or transaction_data.get('finishTime')
            payment_date = self._parse_opay_timestamp(completed_at) or datetime.utcnow()
            
            # Payment status
            payment_status = transaction_data.get('status', 'PENDING')
            mapped_status = self.status_mapping.get(payment_status, 'pending')
            
            # Fee information
            fee_amount = Decimal(str(transaction_data.get('fee', 0)))
            if fee_amount > 100:
                fee_amount = fee_amount / 100
            
            payment_info = PaymentInfo(
                payment_id=order_no,
                payment_method=mapped_method,
                amount=amount,
                currency=currency,
                payment_date=payment_date,
                reference=transaction_data.get('reference'),
                status=mapped_status,
                metadata={
                    'opay_order_no': order_no,
                    'opay_payment_method': payment_method,
                    'opay_status': payment_status,
                    'opay_terminal_id': transaction_data.get('terminalId'),
                    'opay_fee': str(fee_amount),
                    'opay_completed_at': completed_at,
                    'opay_bank_code': transaction_data.get('bankCode'),
                    'opay_bank_name': transaction_data.get('bankName')
                }
            )
            
            payments.append(payment_info)
            
            logger.info("Extracted 1 payment from OPay transaction")
            return payments
            
        except Exception as e:
            logger.error(f"Failed to extract payments: {str(e)}")
            return []
    
    def _calculate_tax_amount(self, transaction_data: Dict[str, Any], total_amount: Decimal) -> Decimal:
        """Calculate tax amount from OPay transaction."""
        try:
            # Check if VAT is specified separately
            vat_amount = transaction_data.get('vatAmount') or transaction_data.get('tax')
            if vat_amount:
                vat_decimal = Decimal(str(vat_amount))
                if vat_decimal > 100:
                    vat_decimal = vat_decimal / 100
                return vat_decimal
            
            # Calculate 7.5% VAT from total amount (inclusive)
            # VAT = (Total Amount * VAT Rate) / (1 + VAT Rate)
            vat_rate = Decimal('0.075')  # 7.5%
            vat_amount = (total_amount * vat_rate) / (Decimal('1') + vat_rate)
            
            return vat_amount.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
            
        except Exception:
            return Decimal('0')
    
    def _parse_opay_timestamp(self, timestamp_str: Optional[str]) -> Optional[datetime]:
        """Parse OPay timestamp string to datetime."""
        if not timestamp_str:
            return None
        
        try:
            # OPay typically uses various formats
            if 'T' in timestamp_str:
                # ISO format
                clean_timestamp = timestamp_str.replace('Z', '').split('+')[0].split('.')[0]
                return datetime.fromisoformat(clean_timestamp)
            elif ' ' in timestamp_str:
                # Standard format
                return datetime.strptime(timestamp_str, self.opay_config['date_format'])
            else:
                # Timestamp
                try:
                    timestamp = int(timestamp_str)
                    if timestamp > 1000000000000:  # Milliseconds
                        timestamp = timestamp / 1000
                    return datetime.fromtimestamp(timestamp)
                except ValueError:
                    pass
                    
        except Exception as e:
            logger.warning(f"Failed to parse OPay timestamp '{timestamp_str}': {str(e)}")
            
        return None