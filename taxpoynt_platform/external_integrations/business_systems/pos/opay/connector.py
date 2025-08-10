"""
OPay POS Connector
Main connector implementation for OPay POS system integration.
Implements the BasePOSConnector interface for TaxPoynt eInvoice platform.
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Union
from uuid import uuid4

from ....framework.base.base_pos_connector import BasePOSConnector
from ....framework.models.pos_models import (
    ConnectionConfig,
    POSTransaction,
    SyncResult,
    HealthStatus,
    WebhookPayload
)
from ....shared.models.invoice_models import UBLInvoice
from ....shared.exceptions.integration_exceptions import (
    ConnectionError,
    AuthenticationError,
    DataSyncError,
    ValidationError
)

from .auth import OPayAuthManager
from .rest_client import OPayRestClient
from .data_extractor import OPayDataExtractor
from .transaction_transformer import OPayTransactionTransformer
from .exceptions import (
    OPayConnectionError,
    OPayAuthenticationError,
    OPayAPIError,
    create_opay_exception
)

logger = logging.getLogger(__name__)


class OPayPOSConnector(BasePOSConnector):
    """
    OPay POS Connector Implementation
    
    Provides comprehensive integration with OPay POS systems including:
    - Signature-based authentication and API access management
    - Transaction data extraction and synchronization
    - FIRS-compliant invoice transformation
    - Webhook processing and real-time updates
    - Nigerian mobile money and wallet integration
    - Multi-terminal and multi-merchant support
    """
    
    def __init__(self, config: ConnectionConfig):
        """
        Initialize OPay POS connector.
        
        Args:
            config: Connection configuration with OPay credentials
        """
        super().__init__(config)
        
        # Initialize OPay components
        self.auth_manager = OPayAuthManager(config)
        self.rest_client = OPayRestClient(self.auth_manager)
        self.data_extractor = OPayDataExtractor(self.rest_client)
        self.transformer = OPayTransactionTransformer()
        
        # Connection state
        self._is_connected = False
        self._last_sync_time: Optional[datetime] = None
        self._merchant_info: Optional[Dict[str, Any]] = None
        
        # Configuration
        self.sync_config = {
            'batch_size': config.sync_config.get('batch_size', 100),
            'max_retries': config.sync_config.get('max_retries', 3),
            'retry_delay': config.sync_config.get('retry_delay', 5),
            'sync_interval': config.sync_config.get('sync_interval', 300),  # 5 minutes
            'webhook_enabled': config.sync_config.get('webhook_enabled', True),
            'concurrent_extractions': config.sync_config.get('concurrent_extractions', 3)
        }
        
        logger.info(f"Initialized OPay POS connector for merchant: {config.merchant_id}")
    
    async def connect(self) -> bool:
        """
        Establish connection to OPay POS system.
        
        Returns:
            bool: True if connection successful
            
        Raises:
            OPayConnectionError: If connection fails
            OPayAuthenticationError: If authentication fails
        """
        try:
            logger.info("Connecting to OPay POS system...")
            
            # Authenticate with OPay (validate credentials)
            auth_success = await self.auth_manager.authenticate()
            if not auth_success:
                raise OPayConnectionError("Failed to validate OPay credentials")
            
            # Test connection by fetching merchant info
            merchant_info = await self.rest_client.get_merchant_info()
            if not merchant_info:
                raise OPayConnectionError("Failed to retrieve merchant information")
            
            self._merchant_info = merchant_info
            self._is_connected = True
            
            merchant_name = merchant_info.get('name', 'Unknown')
            logger.info(f"Successfully connected to OPay POS - Merchant: {merchant_name}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to connect to OPay POS: {str(e)}")
            self._is_connected = False
            raise create_opay_exception(e)
    
    async def disconnect(self) -> bool:
        """
        Disconnect from OPay POS system.
        
        Returns:
            bool: True if disconnection successful
        """
        try:
            logger.info("Disconnecting from OPay POS system...")
            
            # Clean up resources
            await self.auth_manager.cleanup()
            self._is_connected = False
            self._merchant_info = None
            
            logger.info("Successfully disconnected from OPay POS")
            return True
            
        except Exception as e:
            logger.error(f"Error during OPay POS disconnection: {str(e)}")
            return False
    
    async def test_connection(self) -> HealthStatus:
        """
        Test connection health to OPay POS system.
        
        Returns:
            HealthStatus: Connection health information
        """
        try:
            # Test authentication
            auth_valid = await self.auth_manager.validate_credentials()
            if not auth_valid:
                return HealthStatus(
                    is_healthy=False,
                    status_message="Authentication failed",
                    last_check=datetime.utcnow(),
                    details={'auth_status': 'invalid'}
                )
            
            # Test API connectivity
            merchant_info = await self.rest_client.get_merchant_info()
            if not merchant_info:
                return HealthStatus(
                    is_healthy=False,
                    status_message="API connectivity failed",
                    last_check=datetime.utcnow(),
                    details={'api_status': 'unreachable'}
                )
            
            # Test wallet balance access
            try:
                balance_info = await self.rest_client.get_wallet_balance()
                wallet_status = 'accessible' if balance_info else 'limited'
            except Exception:
                wallet_status = 'unavailable'
            
            # Connection is healthy
            return HealthStatus(
                is_healthy=True,
                status_message="Connection healthy",
                last_check=datetime.utcnow(),
                details={
                    'merchant_id': self.auth_manager.merchant_id,
                    'merchant_name': merchant_info.get('name'),
                    'api_status': 'connected',
                    'auth_status': 'valid',
                    'wallet_status': wallet_status,
                    'mobile_money_integration': 'active'
                }
            )
            
        except Exception as e:
            logger.error(f"Connection health check failed: {str(e)}")
            return HealthStatus(
                is_healthy=False,
                status_message=f"Health check failed: {str(e)}",
                last_check=datetime.utcnow(),
                details={'error': str(e)}
            )
    
    async def sync_transactions(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        transaction_type: Optional[str] = None
    ) -> SyncResult:
        """
        Synchronize transactions from OPay POS system.
        
        Args:
            start_date: Start date for sync (default: last sync time)
            end_date: End date for sync (default: now)
            transaction_type: Type of transactions to sync
            
        Returns:
            SyncResult: Synchronization results
            
        Raises:
            DataSyncError: If synchronization fails
        """
        try:
            logger.info("Starting OPay transaction synchronization...")
            
            # Set default date range
            if not start_date:
                start_date = self._last_sync_time or (datetime.utcnow() - timedelta(days=1))
            if not end_date:
                end_date = datetime.utcnow()
            
            # Extract transactions from OPay
            transactions = await self.data_extractor.extract_transactions(
                start_date=start_date,
                end_date=end_date,
                transaction_type=transaction_type
            )
            
            logger.info(f"Extracted {len(transactions)} transactions from OPay")
            
            # Transform transactions to UBL invoices
            successful_invoices = []
            failed_transactions = []
            
            for transaction in transactions:
                try:
                    # Get OPay-specific metadata
                    opay_metadata = await self._get_transaction_metadata(transaction)
                    
                    # Transform to UBL invoice
                    invoice = await self.transformer.transform_transaction(
                        transaction,
                        self._merchant_info,
                        opay_metadata
                    )
                    
                    successful_invoices.append(invoice)
                    
                except Exception as e:
                    logger.error(f"Failed to transform transaction {transaction.transaction_id}: {str(e)}")
                    failed_transactions.append({
                        'transaction_id': transaction.transaction_id,
                        'error': str(e)
                    })
            
            # Update sync time
            self._last_sync_time = end_date
            
            result = SyncResult(
                success=True,
                records_processed=len(transactions),
                records_successful=len(successful_invoices),
                records_failed=len(failed_transactions),
                sync_start_time=start_date,
                sync_end_time=end_date,
                invoices=successful_invoices,
                errors=failed_transactions,
                metadata={
                    'source_system': 'opay_pos',
                    'merchant_id': self.auth_manager.merchant_id,
                    'mobile_money_integration': True,
                    'wallet_transactions_included': True
                }
            )
            
            logger.info(f"OPay sync completed: {len(successful_invoices)} successful, {len(failed_transactions)} failed")
            return result
            
        except Exception as e:
            logger.error(f"OPay transaction synchronization failed: {str(e)}")
            raise DataSyncError(f"Sync failed: {str(e)}")
    
    async def get_transaction(self, transaction_id: str) -> Optional[POSTransaction]:
        """
        Retrieve specific transaction from OPay POS.
        
        Args:
            transaction_id: OPay order number
            
        Returns:
            POSTransaction: Transaction data or None if not found
        """
        try:
            transaction = await self.data_extractor.get_single_transaction(transaction_id)
            if transaction:
                logger.info(f"Retrieved OPay transaction: {transaction_id}")
            return transaction
            
        except Exception as e:
            logger.error(f"Failed to retrieve OPay transaction {transaction_id}: {str(e)}")
            return None
    
    async def process_webhook(self, payload: WebhookPayload) -> bool:
        """
        Process OPay webhook notification.
        
        Args:
            payload: Webhook payload from OPay
            
        Returns:
            bool: True if processing successful
        """
        try:
            logger.info(f"Processing OPay webhook: {payload.event_type}")
            
            # Validate webhook payload
            if not self._validate_webhook_payload(payload):
                logger.warning("Invalid OPay webhook payload")
                return False
            
            # Process based on event type
            if payload.event_type in ['PAYMENT_SUCCESS', 'TRANSACTION_COMPLETED', 'ORDER_PAID']:
                # Extract transaction from webhook data
                transaction = await self.data_extractor.extract_transaction_from_webhook(payload)
                
                if transaction:
                    # Transform to UBL invoice
                    opay_metadata = payload.data
                    invoice = await self.transformer.transform_transaction(
                        transaction,
                        self._merchant_info,
                        opay_metadata
                    )
                    
                    # Trigger invoice processing (implementation specific)
                    await self._process_webhook_invoice(invoice, payload)
                    
                    logger.info(f"Successfully processed OPay webhook for transaction: {transaction.transaction_id}")
                    return True
            
            logger.info(f"OPay webhook {payload.event_type} processed successfully")
            return True
            
        except Exception as e:
            logger.error(f"Failed to process OPay webhook: {str(e)}")
            return False
    
    async def get_merchant_info(self) -> Dict[str, Any]:
        """
        Get merchant information from OPay.
        
        Returns:
            Dict: Merchant information
        """
        if not self._merchant_info:
            self._merchant_info = await self.rest_client.get_merchant_info()
        
        return self._merchant_info or {}
    
    async def get_wallet_balance(self) -> Dict[str, Any]:
        """
        Get wallet balance information.
        
        Returns:
            Dict: Wallet balance information
        """
        try:
            balance_info = await self.rest_client.get_wallet_balance()
            logger.info("Retrieved OPay wallet balance")
            return balance_info
            
        except Exception as e:
            logger.error(f"Failed to get wallet balance: {str(e)}")
            return {}
    
    async def sync_batch_transactions(
        self,
        order_numbers: List[str]
    ) -> SyncResult:
        """
        Synchronize specific transactions by order number.
        
        Args:
            order_numbers: List of OPay order numbers
            
        Returns:
            SyncResult: Batch synchronization results
        """
        try:
            logger.info(f"Starting batch sync for {len(order_numbers)} OPay transactions")
            
            successful_invoices = []
            failed_transactions = []
            
            # Process transactions in batches
            batch_size = self.sync_config['batch_size']
            for i in range(0, len(order_numbers), batch_size):
                batch_orders = order_numbers[i:i + batch_size]
                
                for order_no in batch_orders:
                    try:
                        # Get transaction
                        transaction = await self.get_transaction(order_no)
                        if not transaction:
                            failed_transactions.append({
                                'transaction_id': order_no,
                                'error': 'Transaction not found'
                            })
                            continue
                        
                        # Get metadata
                        opay_metadata = await self._get_transaction_metadata(transaction)
                        
                        # Transform to UBL invoice
                        invoice = await self.transformer.transform_transaction(
                            transaction,
                            self._merchant_info,
                            opay_metadata
                        )
                        
                        successful_invoices.append(invoice)
                        
                    except Exception as e:
                        logger.error(f"Failed to process transaction {order_no}: {str(e)}")
                        failed_transactions.append({
                            'transaction_id': order_no,
                            'error': str(e)
                        })
                
                # Small delay between batches
                await asyncio.sleep(0.1)
            
            result = SyncResult(
                success=True,
                records_processed=len(order_numbers),
                records_successful=len(successful_invoices),
                records_failed=len(failed_transactions),
                sync_start_time=datetime.utcnow(),
                sync_end_time=datetime.utcnow(),
                invoices=successful_invoices,
                errors=failed_transactions,
                metadata={
                    'source_system': 'opay_pos',
                    'sync_type': 'batch',
                    'merchant_id': self.auth_manager.merchant_id,
                    'batch_size': batch_size
                }
            )
            
            logger.info(f"OPay batch sync completed: {len(successful_invoices)} successful, {len(failed_transactions)} failed")
            return result
            
        except Exception as e:
            logger.error(f"OPay batch sync failed: {str(e)}")
            raise DataSyncError(f"Batch sync failed: {str(e)}")
    
    async def initiate_payment(
        self,
        amount: float,
        customer_phone: str,
        reference: str,
        callback_url: Optional[str] = None,
        payment_method: str = 'wallet'
    ) -> Dict[str, Any]:
        """
        Initiate a payment through OPay.
        
        Args:
            amount: Payment amount
            customer_phone: Customer phone number
            reference: Payment reference
            callback_url: Optional callback URL
            payment_method: Payment method
            
        Returns:
            Dict: Payment response
        """
        try:
            payment_result = await self.rest_client.initiate_payment(
                amount=amount,
                customer_phone=customer_phone,
                reference=reference,
                callback_url=callback_url,
                payment_method=payment_method
            )
            
            logger.info(f"Initiated OPay payment: {reference}")
            return payment_result
            
        except Exception as e:
            logger.error(f"Failed to initiate payment: {str(e)}")
            raise create_opay_exception(e)
    
    async def verify_payment(
        self,
        reference: str
    ) -> Dict[str, Any]:
        """
        Verify payment status.
        
        Args:
            reference: Payment reference
            
        Returns:
            Dict: Payment verification details
        """
        try:
            verification_result = await self.rest_client.verify_payment(reference)
            logger.info(f"Verified OPay payment: {reference}")
            return verification_result
            
        except Exception as e:
            logger.error(f"Failed to verify payment: {str(e)}")
            raise create_opay_exception(e)
    
    async def get_payment_methods(self) -> List[Dict[str, Any]]:
        """
        Get supported payment methods.
        
        Returns:
            List[Dict]: List of payment methods
        """
        try:
            methods = await self.rest_client.get_payment_methods()
            logger.info(f"Retrieved {len(methods)} OPay payment methods")
            return methods
            
        except Exception as e:
            logger.error(f"Failed to get payment methods: {str(e)}")
            return []
    
    # Private helper methods
    
    async def _get_transaction_metadata(self, transaction: POSTransaction) -> Dict[str, Any]:
        """Get OPay-specific metadata for transaction."""
        metadata = {
            'merchant_id': self.auth_manager.merchant_id,
            'extraction_timestamp': datetime.utcnow().isoformat()
        }
        
        # Add any additional OPay metadata from transaction
        if transaction.metadata:
            metadata.update({
                'order_no': transaction.metadata.get('opay_order_no'),
                'reference': transaction.metadata.get('opay_reference'),
                'terminal_id': transaction.metadata.get('opay_terminal_id'),
                'payment_method': transaction.metadata.get('opay_payment_method'),
                'transaction_type': transaction.metadata.get('opay_transaction_type')
            })
        
        return metadata
    
    def _validate_webhook_payload(self, payload: WebhookPayload) -> bool:
        """Validate OPay webhook payload."""
        required_fields = ['event_type', 'data']
        
        for field in required_fields:
            if not hasattr(payload, field) or not getattr(payload, field):
                return False
        
        # Validate event type
        valid_events = [
            'PAYMENT_SUCCESS',
            'PAYMENT_FAILED',
            'TRANSACTION_COMPLETED',
            'ORDER_PAID',
            'ORDER_CANCELLED',
            'WALLET_CREDITED',
            'WALLET_DEBITED',
            'TRANSFER_COMPLETED',
            'REFUND_PROCESSED'
        ]
        
        return payload.event_type in valid_events
    
    async def _process_webhook_invoice(self, invoice: UBLInvoice, payload: WebhookPayload) -> None:
        """Process invoice from webhook (implementation specific)."""
        # This would typically send the invoice to the TaxPoynt processing pipeline
        logger.info(f"Processing webhook invoice: {invoice.header.invoice_id}")
        
        # Add webhook processing logic here
        # For example: await self.invoice_processor.process_invoice(invoice)
    
    @property
    def is_connected(self) -> bool:
        """Check if connector is connected to OPay."""
        return self._is_connected
    
    @property
    def last_sync_time(self) -> Optional[datetime]:
        """Get last synchronization time."""
        return self._last_sync_time
    
    @property
    def connector_type(self) -> str:
        """Get connector type identifier."""
        return "opay_pos"
    
    async def __aenter__(self):
        """Async context manager entry."""
        await self.connect()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.disconnect()