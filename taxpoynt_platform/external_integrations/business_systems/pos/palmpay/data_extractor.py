"""
PalmPay POS Data Extraction Module
Extracts transaction and payment data from PalmPay POS REST APIs.
Handles Nigerian mobile payment systems and agent network integration.
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Union
from decimal import Decimal

from ....framework.models.pos_models import POSTransaction, TransactionLineItem, PaymentInfo
from ....shared.exceptions.integration_exceptions import DataExtractionError
from .rest_client import PalmPayRestClient
from .exceptions import (
    PalmPayDataExtractionError,
    PalmPayAPIError,
    create_palmpay_exception
)

logger = logging.getLogger(__name__)


class PalmPayDataExtractor:
    """
    PalmPay POS Data Extraction Service
    
    Handles extraction and parsing of transaction data from PalmPay POS systems
    including mobile money transactions, agent network operations, and wallet payments.
    """
    
    def __init__(self, rest_client: PalmPayRestClient):
        """
        Initialize PalmPay data extractor.
        
        Args:
            rest_client: PalmPay REST API client
        """
        self.rest_client = rest_client
        self.merchant_id = rest_client.auth_manager.merchant_id
        
        # Nigerian market configuration
        self.nigerian_config = {
            'currency': 'NGN',
            'vat_rate': 0.075,  # 7.5% VAT
            'default_tin': '00000000-0001',
            'vat_inclusive': True
        }
        
        logger.info("Initialized PalmPay data extractor")
    
    async def extract_transactions(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        transaction_type: Optional[str] = None,
        include_mobile_money: bool = True,
        include_agent_transactions: bool = True
    ) -> List[POSTransaction]:
        """
        Extract transactions from PalmPay POS system.
        
        Args:
            start_date: Start date for extraction
            end_date: End date for extraction
            transaction_type: Filter by transaction type
            include_mobile_money: Include mobile money transactions
            include_agent_transactions: Include agent network transactions
            
        Returns:
            List[POSTransaction]: Extracted transactions
        """
        try:
            logger.info("Starting PalmPay transaction extraction...")
            
            # Set default date range
            if not start_date:
                start_date = datetime.utcnow() - timedelta(days=1)
            if not end_date:
                end_date = datetime.utcnow()
            
            all_transactions = []
            
            # Extract regular merchant transactions
            merchant_transactions = await self._extract_merchant_transactions(
                start_date, end_date, transaction_type
            )
            all_transactions.extend(merchant_transactions)
            
            # Extract mobile money transactions
            if include_mobile_money:
                mobile_money_transactions = await self._extract_mobile_money_transactions(
                    start_date, end_date
                )
                all_transactions.extend(mobile_money_transactions)
            
            # Extract agent transactions
            if include_agent_transactions:
                agent_transactions = await self._extract_agent_transactions(
                    start_date, end_date
                )
                all_transactions.extend(agent_transactions)
            
            # Remove duplicates based on transaction ID
            unique_transactions = self._deduplicate_transactions(all_transactions)
            
            logger.info(f"Extracted {len(unique_transactions)} unique PalmPay transactions")
            return unique_transactions
            
        except Exception as e:
            logger.error(f"PalmPay transaction extraction failed: {str(e)}")
            raise PalmPayDataExtractionError(f"Extraction failed: {str(e)}")
    
    async def get_single_transaction(self, order_no: str) -> Optional[POSTransaction]:
        """
        Extract a single transaction by order number.
        
        Args:
            order_no: PalmPay order number
            
        Returns:
            POSTransaction: Transaction data or None if not found
        """
        try:
            logger.info(f"Extracting single PalmPay transaction: {order_no}")
            
            # Get transaction details
            transaction_data = await self.rest_client.get_transaction_details(order_no)
            
            if not transaction_data:
                logger.warning(f"PalmPay transaction not found: {order_no}")
                return None
            
            # Parse transaction
            transaction = await self._parse_single_transaction(transaction_data)
            
            logger.info(f"Successfully extracted PalmPay transaction: {order_no}")
            return transaction
            
        except Exception as e:
            logger.error(f"Failed to extract transaction {order_no}: {str(e)}")
            return None
    
    async def extract_transaction_from_webhook(self, webhook_payload: Dict[str, Any]) -> Optional[POSTransaction]:
        """
        Extract transaction from webhook payload.
        
        Args:
            webhook_payload: PalmPay webhook data
            
        Returns:
            POSTransaction: Extracted transaction or None
        """
        try:
            logger.info("Extracting transaction from PalmPay webhook")
            
            # Extract transaction data from webhook
            transaction_data = webhook_payload.get('data', {})
            
            if not transaction_data:
                logger.warning("No transaction data in webhook payload")
                return None
            
            # Parse webhook transaction
            transaction = await self._parse_webhook_transaction(transaction_data, webhook_payload)
            
            logger.info(f"Extracted transaction from webhook: {transaction.transaction_id}")
            return transaction
            
        except Exception as e:
            logger.error(f"Failed to extract webhook transaction: {str(e)}")
            return None
    
    # Private extraction methods
    
    async def _extract_merchant_transactions(
        self,
        start_date: datetime,
        end_date: datetime,
        transaction_type: Optional[str] = None
    ) -> List[POSTransaction]:
        """Extract regular merchant transactions."""
        try:
            transactions_data = await self.rest_client.get_transactions(
                start_date=start_date,
                end_date=end_date,
                transaction_type=transaction_type
            )
            
            transactions = []
            for data in transactions_data:
                try:
                    transaction = await self._parse_single_transaction(data)
                    if transaction:
                        transactions.append(transaction)
                except Exception as e:
                    logger.error(f"Failed to parse merchant transaction: {str(e)}")
                    continue
            
            logger.info(f"Extracted {len(transactions)} merchant transactions")
            return transactions
            
        except Exception as e:
            logger.error(f"Failed to extract merchant transactions: {str(e)}")
            return []
    
    async def _extract_mobile_money_transactions(
        self,
        start_date: datetime,
        end_date: datetime
    ) -> List[POSTransaction]:
        """Extract mobile money transactions."""
        try:
            mobile_money_data = await self.rest_client.get_mobile_money_transactions(
                start_date=start_date,
                end_date=end_date
            )
            
            transactions = []
            for data in mobile_money_data:
                try:
                    transaction = await self._parse_mobile_money_transaction(data)
                    if transaction:
                        transactions.append(transaction)
                except Exception as e:
                    logger.error(f"Failed to parse mobile money transaction: {str(e)}")
                    continue
            
            logger.info(f"Extracted {len(transactions)} mobile money transactions")
            return transactions
            
        except Exception as e:
            logger.error(f"Failed to extract mobile money transactions: {str(e)}")
            return []
    
    async def _extract_agent_transactions(
        self,
        start_date: datetime,
        end_date: datetime
    ) -> List[POSTransaction]:
        """Extract agent network transactions."""
        try:
            agent_data = await self.rest_client.get_agent_transactions(
                start_date=start_date,
                end_date=end_date
            )
            
            transactions = []
            for data in agent_data:
                try:
                    transaction = await self._parse_agent_transaction(data)
                    if transaction:
                        transactions.append(transaction)
                except Exception as e:
                    logger.error(f"Failed to parse agent transaction: {str(e)}")
                    continue
            
            logger.info(f"Extracted {len(transactions)} agent transactions")
            return transactions
            
        except Exception as e:
            logger.error(f"Failed to extract agent transactions: {str(e)}")
            return []
    
    # Transaction parsing methods
    
    async def _parse_single_transaction(self, data: Dict[str, Any]) -> Optional[POSTransaction]:
        """Parse a standard PalmPay transaction."""
        try:
            # Basic transaction info
            order_no = data.get('orderNo') or data.get('transactionId')
            if not order_no:
                logger.warning("Transaction missing order number")
                return None
            
            # Parse amounts (PalmPay uses kobo/cents)
            amount_kobo = data.get('amount', 0)
            amount = Decimal(str(amount_kobo)) / 100 if amount_kobo else Decimal('0')
            
            # Calculate VAT (7.5% VAT-inclusive)
            vat_amount = amount * Decimal(str(self.nigerian_config['vat_rate'])) / Decimal('1.075')
            subtotal = amount - vat_amount
            
            # Transaction timestamp
            transaction_time_str = data.get('createTime') or data.get('transactionTime')
            if transaction_time_str:
                # PalmPay timestamps are typically in milliseconds
                if isinstance(transaction_time_str, int):
                    transaction_time = datetime.fromtimestamp(transaction_time_str / 1000)
                else:
                    try:
                        transaction_time = datetime.fromisoformat(transaction_time_str.replace('Z', '+00:00'))
                    except:
                        transaction_time = datetime.utcnow()
            else:
                transaction_time = datetime.utcnow()
            
            # Payment information
            payment_info = PaymentInfo(
                payment_method=data.get('paymentMethod', 'wallet'),
                amount_paid=float(amount),
                payment_reference=data.get('reference') or order_no,
                payment_status=self._map_payment_status(data.get('status', 'unknown')),
                currency_code=self.nigerian_config['currency']
            )
            
            # Line items
            line_items = [
                TransactionLineItem(
                    item_id=str(1),
                    item_name=data.get('description', 'PalmPay Payment'),
                    quantity=Decimal('1'),
                    unit_price=float(subtotal),
                    total_amount=float(amount),
                    tax_amount=float(vat_amount),
                    tax_rate=self.nigerian_config['vat_rate'],
                    category='payment_service'
                )
            ]
            
            # Customer information
            customer_info = {
                'name': data.get('customerName', 'PalmPay Customer'),
                'phone': data.get('customerPhone', ''),
                'email': data.get('customerEmail', ''),
                'tin': self.nigerian_config['default_tin']
            }
            
            # Additional metadata
            metadata = {
                'palmpay_order_no': order_no,
                'palmpay_reference': data.get('reference'),
                'palmpay_terminal_id': data.get('terminalId'),
                'palmpay_payment_method': data.get('paymentMethod'),
                'palmpay_transaction_type': data.get('transactionType'),
                'palmpay_merchant_id': self.merchant_id,
                'mobile_money_integration': True,
                'agent_network': data.get('agentId') is not None,
                'original_data': data
            }
            
            return POSTransaction(
                transaction_id=order_no,
                timestamp=transaction_time,
                total_amount=float(amount),
                subtotal=float(subtotal),
                tax_amount=float(vat_amount),
                currency_code=self.nigerian_config['currency'],
                payment_info=payment_info,
                line_items=line_items,
                customer_info=customer_info,
                metadata=metadata
            )
            
        except Exception as e:
            logger.error(f"Failed to parse PalmPay transaction: {str(e)}")
            return None
    
    async def _parse_mobile_money_transaction(self, data: Dict[str, Any]) -> Optional[POSTransaction]:
        """Parse mobile money transaction."""
        # Similar to _parse_single_transaction but with mobile money specifics
        transaction = await self._parse_single_transaction(data)
        
        if transaction and transaction.metadata:
            # Add mobile money specific metadata
            transaction.metadata.update({
                'transaction_source': 'mobile_money',
                'mobile_network': data.get('network'),
                'ussd_code': data.get('ussdCode'),
                'qr_code_used': data.get('qrCodeUsed', False),
                'wallet_type': data.get('walletType', 'palmpay')
            })
            
            # Update line item category
            if transaction.line_items:
                transaction.line_items[0].category = 'mobile_money_payment'
        
        return transaction
    
    async def _parse_agent_transaction(self, data: Dict[str, Any]) -> Optional[POSTransaction]:
        """Parse agent network transaction."""
        # Similar to _parse_single_transaction but with agent specifics
        transaction = await self._parse_single_transaction(data)
        
        if transaction and transaction.metadata:
            # Add agent network specific metadata
            transaction.metadata.update({
                'transaction_source': 'agent_network',
                'agent_id': data.get('agentId'),
                'agent_name': data.get('agentName'),
                'agent_location': data.get('agentLocation'),
                'commission_amount': data.get('commissionAmount', 0),
                'agent_network': True
            })
            
            # Update line item category
            if transaction.line_items:
                transaction.line_items[0].category = 'agent_network_payment'
        
        return transaction
    
    async def _parse_webhook_transaction(
        self,
        transaction_data: Dict[str, Any],
        webhook_payload: Dict[str, Any]
    ) -> Optional[POSTransaction]:
        """Parse transaction from webhook payload."""
        # Parse as standard transaction first
        transaction = await self._parse_single_transaction(transaction_data)
        
        if transaction and transaction.metadata:
            # Add webhook-specific metadata
            transaction.metadata.update({
                'webhook_event': webhook_payload.get('event_type'),
                'webhook_timestamp': webhook_payload.get('timestamp'),
                'webhook_id': webhook_payload.get('id'),
                'real_time_processing': True
            })
        
        return transaction
    
    def _map_payment_status(self, status: str) -> str:
        """Map PalmPay payment status to standardized status."""
        status_mapping = {
            'SUCCESS': 'completed',
            'COMPLETED': 'completed',
            'PAID': 'completed',
            'PENDING': 'pending',
            'PROCESSING': 'pending',
            'FAILED': 'failed',
            'CANCELLED': 'cancelled',
            'REFUNDED': 'refunded'
        }
        
        return status_mapping.get(status.upper(), 'unknown')
    
    def _deduplicate_transactions(self, transactions: List[POSTransaction]) -> List[POSTransaction]:
        """Remove duplicate transactions based on transaction ID."""
        seen_ids = set()
        unique_transactions = []
        
        for transaction in transactions:
            if transaction.transaction_id not in seen_ids:
                seen_ids.add(transaction.transaction_id)
                unique_transactions.append(transaction)
        
        return unique_transactions
    
    async def extract_batch_transactions(
        self,
        order_numbers: List[str]
    ) -> List[POSTransaction]:
        """
        Extract multiple transactions by order numbers.
        
        Args:
            order_numbers: List of PalmPay order numbers
            
        Returns:
            List[POSTransaction]: Extracted transactions
        """
        try:
            logger.info(f"Extracting batch of {len(order_numbers)} PalmPay transactions")
            
            # Use REST client batch method
            transactions_data = await self.rest_client.batch_get_transactions(order_numbers)
            
            transactions = []
            for data in transactions_data:
                try:
                    transaction = await self._parse_single_transaction(data)
                    if transaction:
                        transactions.append(transaction)
                except Exception as e:
                    logger.error(f"Failed to parse batch transaction: {str(e)}")
                    continue
            
            logger.info(f"Successfully extracted {len(transactions)} transactions from batch")
            return transactions
            
        except Exception as e:
            logger.error(f"Batch transaction extraction failed: {str(e)}")
            raise PalmPayDataExtractionError(f"Batch extraction failed: {str(e)}")