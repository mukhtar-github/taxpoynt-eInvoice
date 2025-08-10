"""
Toast POS Data Extractor
Extracts and transforms POS transaction data from Toast REST API
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
from .rest_client import ToastRestClient
from .exceptions import ToastDataExtractionError, create_toast_exception

logger = logging.getLogger(__name__)


class ToastDataExtractor:
    """
    Toast POS Data Extractor
    
    Extracts transaction data from Toast POS REST API and transforms it
    into standardized POSTransaction objects with Nigerian market adaptations.
    """
    
    def __init__(self, rest_client: ToastRestClient):
        """
        Initialize Toast data extractor.
        
        Args:
            rest_client: Toast REST API client
        """
        self.rest_client = rest_client
        self.data_transformer = DataTransformer()
        self.validator = ValidationUtils()
        
        # Toast-specific configuration
        self.toast_config = {
            'default_currency': 'USD',
            'date_format': '%Y-%m-%dT%H:%M:%S.%fZ',
            'timezone': 'UTC',
            'extract_batch_size': 100,
            'max_concurrent_extractions': 5
        }
        
        # Payment method mapping
        self.payment_method_mapping = {
            'CASH': 'cash',
            'CREDIT': 'credit_card',
            'CREDIT_CARD': 'credit_card',
            'DEBIT': 'debit_card',
            'DEBIT_CARD': 'debit_card',
            'GIFT_CARD': 'gift_card',
            'HOUSE_ACCOUNT': 'house_account',
            'LOYALTY': 'loyalty_points',
            'EXTERNAL_PAYMENT': 'external_payment',
            'OTHER': 'other'
        }
        
        logger.info("Initialized Toast data extractor")
    
    async def extract_transactions(
        self,
        restaurant_id: str,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        limit: Optional[int] = None
    ) -> List[POSTransaction]:
        """
        Extract transactions from Toast POS for a date range.
        
        Args:
            restaurant_id: Toast restaurant identifier
            start_date: Start date for extraction
            end_date: End date for extraction
            limit: Maximum number of transactions to extract
            
        Returns:
            List[POSTransaction]: List of standardized transactions
            
        Raises:
            ToastDataExtractionError: If extraction fails
        """
        try:
            logger.info(f"Extracting Toast transactions for restaurant {restaurant_id}")
            
            # Get checks from Toast API
            checks = await self.rest_client.get_checks(
                restaurant_id=restaurant_id,
                start_date=start_date,
                end_date=end_date,
                limit=limit
            )
            
            if not checks:
                logger.info("No Toast checks found for the specified criteria")
                return []
            
            # Extract detailed check information
            transactions = []
            for check_summary in checks:
                try:
                    check_guid = check_summary.get('guid')
                    if not check_guid:
                        logger.warning(f"Check missing GUID: {check_summary}")
                        continue
                    
                    # Get detailed check information
                    check_details = await self.rest_client.get_check_details(restaurant_id, check_guid)
                    if not check_details:
                        logger.warning(f"Could not get details for check: {check_guid}")
                        continue
                    
                    # Transform check to POS transaction
                    transaction = await self._transform_check_to_transaction(
                        check_details, restaurant_id
                    )
                    
                    if transaction:
                        transactions.append(transaction)
                        
                except Exception as e:
                    logger.error(f"Failed to process Toast check {check_summary.get('guid', 'unknown')}: {str(e)}")
                    continue
            
            logger.info(f"Successfully extracted {len(transactions)} Toast transactions")
            return transactions
            
        except Exception as e:
            logger.error(f"Toast transaction extraction failed: {str(e)}")
            raise ToastDataExtractionError(f"Extraction failed: {str(e)}", restaurant_id)
    
    async def get_single_transaction(
        self,
        restaurant_id: str,
        check_guid: str
    ) -> Optional[POSTransaction]:
        """
        Extract a single transaction by check GUID.
        
        Args:
            restaurant_id: Toast restaurant identifier
            check_guid: Toast check GUID
            
        Returns:
            POSTransaction: Standardized transaction or None if not found
        """
        try:
            logger.info(f"Extracting single Toast transaction: {check_guid}")
            
            # Get check details
            check_details = await self.rest_client.get_check_details(restaurant_id, check_guid)
            if not check_details:
                logger.warning(f"Toast check not found: {check_guid}")
                return None
            
            # Transform to POS transaction
            transaction = await self._transform_check_to_transaction(check_details, restaurant_id)
            
            if transaction:
                logger.info(f"Successfully extracted Toast transaction: {check_guid}")
            
            return transaction
            
        except Exception as e:
            logger.error(f"Failed to extract Toast transaction {check_guid}: {str(e)}")
            return None
    
    async def extract_transaction_from_webhook(
        self,
        payload: WebhookPayload
    ) -> Optional[POSTransaction]:
        """
        Extract transaction from Toast webhook payload.
        
        Args:
            payload: Toast webhook payload
            
        Returns:
            POSTransaction: Standardized transaction or None
        """
        try:
            logger.info(f"Extracting transaction from Toast webhook: {payload.event_type}")
            
            # Get check data from webhook payload
            webhook_data = payload.data
            restaurant_id = webhook_data.get('restaurantGuid')
            check_guid = webhook_data.get('guid')
            
            if not restaurant_id or not check_guid:
                logger.warning("Webhook missing restaurant or check GUID")
                return None
            
            # For some events, we might have partial data in webhook
            if payload.event_type in ['ORDER_DELETED', 'CHECK_DELETED']:
                # Handle deletion events differently
                return await self._create_deletion_transaction(webhook_data, restaurant_id)
            
            # Get full check details for complete data
            check_details = await self.rest_client.get_check_details(restaurant_id, check_guid)
            if not check_details:
                # Fall back to webhook data
                check_details = webhook_data
            
            # Transform to POS transaction
            transaction = await self._transform_check_to_transaction(check_details, restaurant_id)
            
            if transaction:
                # Add webhook metadata
                transaction.metadata = transaction.metadata or {}
                transaction.metadata.update({
                    'webhook_event': payload.event_type,
                    'webhook_timestamp': payload.timestamp.isoformat() if payload.timestamp else None,
                    'webhook_source': 'toast'
                })
            
            logger.info(f"Successfully extracted transaction from Toast webhook: {check_guid}")
            return transaction
            
        except Exception as e:
            logger.error(f"Failed to extract transaction from Toast webhook: {str(e)}")
            return None
    
    # Private transformation methods
    
    async def _transform_check_to_transaction(
        self,
        check_data: Dict[str, Any],
        restaurant_id: str
    ) -> Optional[POSTransaction]:
        """Transform Toast check data to POSTransaction."""
        try:
            check_guid = check_data.get('guid')
            if not check_guid:
                raise ToastDataExtractionError("Check missing GUID")
            
            # Basic transaction info
            display_number = check_data.get('displayNumber', '')
            created_date = check_data.get('createdDate')
            modified_date = check_data.get('modifiedDate')
            
            # Parse timestamps
            timestamp = self._parse_toast_timestamp(created_date or modified_date)
            if not timestamp:
                timestamp = datetime.utcnow()
            
            # Extract customer information
            customer_info = await self._extract_customer_info(check_data)
            
            # Extract line items
            line_items = await self._extract_line_items(check_data)
            
            # Extract payments
            payments = await self._extract_payments(check_data)
            
            # Calculate totals
            total_amount = self._calculate_total_amount(check_data)
            tax_amount = self._calculate_tax_amount(check_data)
            
            # Create POS transaction
            transaction = POSTransaction(
                transaction_id=check_guid,
                timestamp=timestamp,
                total_amount=total_amount,
                tax_amount=tax_amount,
                currency=self.toast_config['default_currency'],
                line_items=line_items,
                payments=payments,
                customer_info=customer_info,
                metadata={
                    'toast_restaurant_id': restaurant_id,
                    'toast_check_guid': check_guid,
                    'toast_display_number': display_number,
                    'toast_created_date': created_date,
                    'toast_modified_date': modified_date,
                    'toast_table_id': check_data.get('table', {}).get('guid'),
                    'toast_server_id': check_data.get('server', {}).get('guid'),
                    'toast_dining_option': check_data.get('diningOption', {}).get('name'),
                    'extraction_timestamp': datetime.utcnow().isoformat()
                }
            )
            
            return transaction
            
        except Exception as e:
            logger.error(f"Failed to transform Toast check to transaction: {str(e)}")
            raise ToastDataExtractionError(f"Check transformation failed: {str(e)}", check_data.get('guid'))
    
    async def _extract_customer_info(self, check_data: Dict[str, Any]) -> Optional[CustomerInfo]:
        """Extract customer information from Toast check."""
        try:
            customer_data = check_data.get('customer')
            if not customer_data:
                return None
            
            customer_guid = customer_data.get('guid', str(uuid4()))
            first_name = customer_data.get('firstName', '')
            last_name = customer_data.get('lastName', '')
            name = f"{first_name} {last_name}".strip() or 'Unknown Customer'
            
            return CustomerInfo(
                customer_id=customer_guid,
                name=name,
                email=customer_data.get('email'),
                phone=customer_data.get('phone'),
                customer_type='individual',  # Toast typically handles individual customers
                metadata={
                    'toast_customer_guid': customer_guid,
                    'toast_first_name': first_name,
                    'toast_last_name': last_name,
                    'toast_created_date': customer_data.get('createdDate')
                }
            )
            
        except Exception as e:
            logger.error(f"Failed to extract customer info: {str(e)}")
            return None
    
    async def _extract_line_items(self, check_data: Dict[str, Any]) -> List[POSLineItem]:
        """Extract line items from Toast check."""
        line_items = []
        
        try:
            selections = check_data.get('selections', [])
            
            for idx, selection in enumerate(selections):
                try:
                    item = selection.get('item', {})
                    item_guid = item.get('guid', str(uuid4()))
                    item_name = item.get('name', 'Unknown Item')
                    
                    # Quantity and pricing
                    quantity = Decimal(str(selection.get('quantity', 1)))
                    unit_price = Decimal(str(selection.get('unitPrice', 0))) / 100  # Toast uses cents
                    total_price = Decimal(str(selection.get('price', 0))) / 100  # Toast uses cents
                    
                    # Handle modifiers and their prices
                    modifiers = []
                    modifier_price = Decimal('0')
                    for modifier in selection.get('modifiers', []):
                        mod_price = Decimal(str(modifier.get('price', 0))) / 100
                        modifier_price += mod_price
                        modifiers.append({
                            'name': modifier.get('modifier', {}).get('name', 'Unknown Modifier'),
                            'price': mod_price
                        })
                    
                    # Adjust total price with modifiers
                    total_price += modifier_price
                    
                    # Handle discounts
                    applied_discounts = selection.get('appliedDiscounts', [])
                    discount_amount = Decimal('0')
                    for discount in applied_discounts:
                        discount_amount += Decimal(str(discount.get('discount', 0))) / 100
                    
                    line_item = POSLineItem(
                        item_code=item_guid,
                        name=item_name,
                        description=item.get('description') or item_name,
                        quantity=quantity,
                        unit_price=unit_price,
                        total_price=total_price - discount_amount,  # Net price after discounts
                        discount_amount=discount_amount,
                        currency=self.toast_config['default_currency'],
                        metadata={
                            'toast_item_guid': item_guid,
                            'toast_selection_guid': selection.get('guid'),
                            'toast_item_category': item.get('category', {}).get('name'),
                            'toast_modifiers': modifiers,
                            'toast_applied_discounts': applied_discounts,
                            'toast_void_reason': selection.get('voidReason'),
                            'toast_is_voided': selection.get('voided', False)
                        }
                    )
                    
                    line_items.append(line_item)
                    
                except Exception as e:
                    logger.error(f"Failed to process Toast selection {idx}: {str(e)}")
                    continue
            
            logger.info(f"Extracted {len(line_items)} line items from Toast check")
            return line_items
            
        except Exception as e:
            logger.error(f"Failed to extract line items: {str(e)}")
            return []
    
    async def _extract_payments(self, check_data: Dict[str, Any]) -> List[PaymentInfo]:
        """Extract payment information from Toast check."""
        payments = []
        
        try:
            payment_data = check_data.get('payments', [])
            
            for payment in payment_data:
                try:
                    payment_guid = payment.get('guid', str(uuid4()))
                    payment_type = payment.get('type', 'OTHER')
                    
                    # Map Toast payment type to standard format
                    mapped_method = self.payment_method_mapping.get(payment_type, 'other')
                    
                    # Amount in dollars (Toast uses cents)
                    amount = Decimal(str(payment.get('amount', 0))) / 100
                    
                    # Payment date
                    payment_date = self._parse_toast_timestamp(payment.get('paidDate'))
                    
                    payment_info = PaymentInfo(
                        payment_id=payment_guid,
                        payment_method=mapped_method,
                        amount=amount,
                        currency=self.toast_config['default_currency'],
                        payment_date=payment_date or datetime.utcnow(),
                        reference=payment.get('externalId'),
                        status='completed',  # Toast payments are typically completed
                        metadata={
                            'toast_payment_guid': payment_guid,
                            'toast_payment_type': payment_type,
                            'toast_card_type': payment.get('cardType'),
                            'toast_last_four': payment.get('last4'),
                            'toast_tip_amount': Decimal(str(payment.get('tipAmount', 0))) / 100,
                            'toast_cash_drawer_guid': payment.get('cashDrawer', {}).get('guid'),
                            'toast_refund_status': payment.get('refundStatus')
                        }
                    )
                    
                    payments.append(payment_info)
                    
                except Exception as e:
                    logger.error(f"Failed to process Toast payment: {str(e)}")
                    continue
            
            logger.info(f"Extracted {len(payments)} payments from Toast check")
            return payments
            
        except Exception as e:
            logger.error(f"Failed to extract payments: {str(e)}")
            return []
    
    def _calculate_total_amount(self, check_data: Dict[str, Any]) -> Decimal:
        """Calculate total amount from Toast check."""
        try:
            # Toast stores amounts in cents
            amount_cents = check_data.get('amount', 0)
            return Decimal(str(amount_cents)) / 100
        except Exception:
            return Decimal('0')
    
    def _calculate_tax_amount(self, check_data: Dict[str, Any]) -> Decimal:
        """Calculate tax amount from Toast check."""
        try:
            # Get applied taxes
            applied_taxes = check_data.get('appliedTaxes', [])
            total_tax = Decimal('0')
            
            for tax in applied_taxes:
                tax_amount = Decimal(str(tax.get('taxAmount', 0))) / 100
                total_tax += tax_amount
            
            return total_tax
        except Exception:
            return Decimal('0')
    
    def _parse_toast_timestamp(self, timestamp_str: Optional[str]) -> Optional[datetime]:
        """Parse Toast timestamp string to datetime."""
        if not timestamp_str:
            return None
        
        try:
            # Toast typically uses ISO format
            if 'T' in timestamp_str:
                # Remove timezone info if present for parsing
                clean_timestamp = timestamp_str.replace('Z', '').split('+')[0].split('-')[0]
                return datetime.fromisoformat(clean_timestamp)
            else:
                # Handle other formats
                return datetime.strptime(timestamp_str, '%Y-%m-%d %H:%M:%S')
        except Exception as e:
            logger.warning(f"Failed to parse Toast timestamp '{timestamp_str}': {str(e)}")
            return None
    
    async def _create_deletion_transaction(
        self,
        webhook_data: Dict[str, Any],
        restaurant_id: str
    ) -> Optional[POSTransaction]:
        """Create a transaction record for deletion events."""
        try:
            check_guid = webhook_data.get('guid')
            if not check_guid:
                return None
            
            # Create minimal transaction for deletion tracking
            transaction = POSTransaction(
                transaction_id=check_guid,
                timestamp=datetime.utcnow(),
                total_amount=Decimal('0'),
                tax_amount=Decimal('0'),
                currency=self.toast_config['default_currency'],
                line_items=[],
                payments=[],
                customer_info=None,
                metadata={
                    'toast_restaurant_id': restaurant_id,
                    'toast_check_guid': check_guid,
                    'is_deletion': True,
                    'deletion_timestamp': datetime.utcnow().isoformat()
                }
            )
            
            return transaction
            
        except Exception as e:
            logger.error(f"Failed to create deletion transaction: {str(e)}")
            return None