"""
Moniepoint POS Connector
Main connector implementation for Moniepoint POS system integration.
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

from .auth import MoniepointAuthManager
from .rest_client import MoniepointRestClient
from .data_extractor import MoniepointDataExtractor
from .transaction_transformer import MoniepointTransactionTransformer
from .exceptions import (
    MoniepointConnectionError,
    MoniepointAuthenticationError,
    MoniepointAPIError,
    create_moniepoint_exception
)

logger = logging.getLogger(__name__)


class MoniepointPOSConnector(BasePOSConnector):
    """
    Moniepoint POS Connector Implementation
    
    Provides comprehensive integration with Moniepoint POS systems including:
    - API key authentication and token management
    - Transaction data extraction and synchronization
    - FIRS-compliant invoice transformation
    - Webhook processing and real-time updates
    - Nigerian banking system integration
    - NIP (Nigeria Instant Payment) support
    """
    
    def __init__(self, config: ConnectionConfig):
        """
        Initialize Moniepoint POS connector.
        
        Args:
            config: Connection configuration with Moniepoint credentials
        """
        super().__init__(config)
        
        # Initialize Moniepoint components
        self.auth_manager = MoniepointAuthManager(config)
        self.rest_client = MoniepointRestClient(self.auth_manager)
        self.data_extractor = MoniepointDataExtractor(self.rest_client)
        self.transformer = MoniepointTransactionTransformer()
        
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
        
        logger.info(f"Initialized Moniepoint POS connector for merchant: {config.merchant_id}")
    
    async def connect(self) -> bool:
        """
        Establish connection to Moniepoint POS system.
        
        Returns:
            bool: True if connection successful
            
        Raises:
            MoniepointConnectionError: If connection fails
            MoniepointAuthenticationError: If authentication fails
        """
        try:
            logger.info("Connecting to Moniepoint POS system...")
            
            # Authenticate with Moniepoint
            await self.auth_manager.authenticate()
            
            # Test connection by fetching merchant info
            merchant_info = await self.rest_client.get_merchant_info()
            if not merchant_info:
                raise MoniepointConnectionError("Failed to retrieve merchant information")
            
            self._merchant_info = merchant_info
            self._is_connected = True
            
            merchant_name = merchant_info.get('businessName', 'Unknown')
            logger.info(f"Successfully connected to Moniepoint POS - Merchant: {merchant_name}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to connect to Moniepoint POS: {str(e)}")
            self._is_connected = False
            raise create_moniepoint_exception(e)
    
    async def disconnect(self) -> bool:
        """
        Disconnect from Moniepoint POS system.
        
        Returns:
            bool: True if disconnection successful
        """
        try:
            logger.info("Disconnecting from Moniepoint POS system...")
            
            # Clean up resources
            await self.auth_manager.cleanup()
            self._is_connected = False
            self._merchant_info = None
            
            logger.info("Successfully disconnected from Moniepoint POS")
            return True
            
        except Exception as e:
            logger.error(f"Error during Moniepoint POS disconnection: {str(e)}")
            return False
    
    async def test_connection(self) -> HealthStatus:
        """
        Test connection health to Moniepoint POS system.
        
        Returns:
            HealthStatus: Connection health information
        """
        try:
            # Test authentication
            auth_valid = await self.auth_manager.validate_token()
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
            
            # Connection is healthy
            return HealthStatus(
                is_healthy=True,
                status_message="Connection healthy",
                last_check=datetime.utcnow(),
                details={
                    'merchant_id': self.auth_manager.merchant_id,
                    'merchant_name': merchant_info.get('businessName'),
                    'api_status': 'connected',
                    'auth_status': 'valid',
                    'banking_integration': 'active'
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
        merchant_id: Optional[str] = None
    ) -> SyncResult:
        """
        Synchronize transactions from Moniepoint POS system.
        
        Args:
            start_date: Start date for sync (default: last sync time)
            end_date: End date for sync (default: now)
            merchant_id: Specific merchant ID to sync
            
        Returns:
            SyncResult: Synchronization results
            
        Raises:
            DataSyncError: If synchronization fails
        """
        try:
            logger.info("Starting Moniepoint transaction synchronization...")
            
            # Set default date range
            if not start_date:
                start_date = self._last_sync_time or (datetime.utcnow() - timedelta(days=1))
            if not end_date:
                end_date = datetime.utcnow()
            
            # Extract transactions from Moniepoint
            transactions = await self.data_extractor.extract_transactions(
                start_date=start_date,
                end_date=end_date,
                merchant_id=merchant_id or self.auth_manager.merchant_id
            )
            
            logger.info(f"Extracted {len(transactions)} transactions from Moniepoint")
            
            # Transform transactions to UBL invoices
            successful_invoices = []
            failed_transactions = []
            
            for transaction in transactions:
                try:
                    # Get Moniepoint-specific metadata
                    moniepoint_metadata = await self._get_transaction_metadata(transaction)
                    
                    # Transform to UBL invoice
                    invoice = await self.transformer.transform_transaction(
                        transaction,
                        self._merchant_info,
                        moniepoint_metadata
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
                    'source_system': 'moniepoint_pos',
                    'merchant_id': merchant_id or self.auth_manager.merchant_id,
                    'banking_integration': True,
                    'nip_transactions_included': True
                }
            )
            
            logger.info(f"Moniepoint sync completed: {len(successful_invoices)} successful, {len(failed_transactions)} failed")
            return result
            
        except Exception as e:
            logger.error(f"Moniepoint transaction synchronization failed: {str(e)}")
            raise DataSyncError(f"Sync failed: {str(e)}")
    
    async def get_transaction(self, transaction_id: str) -> Optional[POSTransaction]:
        """
        Retrieve specific transaction from Moniepoint POS.
        
        Args:
            transaction_id: Moniepoint transaction reference
            
        Returns:
            POSTransaction: Transaction data or None if not found
        """
        try:
            transaction = await self.data_extractor.get_single_transaction(transaction_id)
            if transaction:
                logger.info(f"Retrieved Moniepoint transaction: {transaction_id}")
            return transaction
            
        except Exception as e:
            logger.error(f"Failed to retrieve Moniepoint transaction {transaction_id}: {str(e)}")
            return None
    
    async def process_webhook(self, payload: WebhookPayload) -> bool:
        """
        Process Moniepoint webhook notification.
        
        Args:
            payload: Webhook payload from Moniepoint
            
        Returns:
            bool: True if processing successful
        """
        try:
            logger.info(f"Processing Moniepoint webhook: {payload.event_type}")
            
            # Validate webhook payload
            if not self._validate_webhook_payload(payload):
                logger.warning("Invalid Moniepoint webhook payload")
                return False
            
            # Process based on event type
            if payload.event_type in ['TRANSACTION_COMPLETED', 'PAYMENT_RECEIVED', 'SUCCESSFUL_TRANSACTION']:
                # Extract transaction from webhook data
                transaction = await self.data_extractor.extract_transaction_from_webhook(payload)
                
                if transaction:
                    # Transform to UBL invoice
                    moniepoint_metadata = payload.data
                    invoice = await self.transformer.transform_transaction(
                        transaction,
                        self._merchant_info,
                        moniepoint_metadata
                    )
                    
                    # Trigger invoice processing (implementation specific)
                    await self._process_webhook_invoice(invoice, payload)
                    
                    logger.info(f"Successfully processed Moniepoint webhook for transaction: {transaction.transaction_id}")
                    return True
            
            logger.info(f"Moniepoint webhook {payload.event_type} processed successfully")
            return True
            
        except Exception as e:
            logger.error(f"Failed to process Moniepoint webhook: {str(e)}")
            return False
    
    async def get_merchant_info(self) -> Dict[str, Any]:
        """
        Get merchant information from Moniepoint.
        
        Returns:
            Dict: Merchant information
        """
        if not self._merchant_info:
            self._merchant_info = await self.rest_client.get_merchant_info()
        
        return self._merchant_info or {}
    
    async def get_virtual_accounts(self) -> List[Dict[str, Any]]:
        """
        Get virtual accounts for the merchant.
        
        Returns:
            List[Dict]: Virtual account information
        """
        try:
            accounts = await self.rest_client.get_virtual_accounts()
            logger.info(f"Retrieved {len(accounts)} Moniepoint virtual accounts")
            return accounts
            
        except Exception as e:
            logger.error(f"Failed to get virtual accounts: {str(e)}")
            return []
    
    async def sync_batch_transactions(
        self,
        transaction_references: List[str]
    ) -> SyncResult:
        """
        Synchronize specific transactions by reference.
        
        Args:
            transaction_references: List of Moniepoint transaction references
            
        Returns:
            SyncResult: Batch synchronization results
        """
        try:
            logger.info(f"Starting batch sync for {len(transaction_references)} Moniepoint transactions")
            
            successful_invoices = []
            failed_transactions = []
            
            # Process transactions in batches
            batch_size = self.sync_config['batch_size']
            for i in range(0, len(transaction_references), batch_size):
                batch_refs = transaction_references[i:i + batch_size]
                
                for transaction_ref in batch_refs:
                    try:
                        # Get transaction
                        transaction = await self.get_transaction(transaction_ref)
                        if not transaction:
                            failed_transactions.append({
                                'transaction_id': transaction_ref,
                                'error': 'Transaction not found'
                            })
                            continue
                        
                        # Get metadata
                        moniepoint_metadata = await self._get_transaction_metadata(transaction)
                        
                        # Transform to UBL invoice
                        invoice = await self.transformer.transform_transaction(
                            transaction,
                            self._merchant_info,
                            moniepoint_metadata
                        )
                        
                        successful_invoices.append(invoice)
                        
                    except Exception as e:
                        logger.error(f"Failed to process transaction {transaction_ref}: {str(e)}")
                        failed_transactions.append({
                            'transaction_id': transaction_ref,
                            'error': str(e)
                        })
                
                # Small delay between batches
                await asyncio.sleep(0.1)
            
            result = SyncResult(
                success=True,
                records_processed=len(transaction_references),
                records_successful=len(successful_invoices),
                records_failed=len(failed_transactions),
                sync_start_time=datetime.utcnow(),
                sync_end_time=datetime.utcnow(),
                invoices=successful_invoices,
                errors=failed_transactions,
                metadata={
                    'source_system': 'moniepoint_pos',
                    'sync_type': 'batch',
                    'merchant_id': self.auth_manager.merchant_id,
                    'batch_size': batch_size
                }
            )
            
            logger.info(f"Moniepoint batch sync completed: {len(successful_invoices)} successful, {len(failed_transactions)} failed")
            return result
            
        except Exception as e:
            logger.error(f"Moniepoint batch sync failed: {str(e)}")
            raise DataSyncError(f"Batch sync failed: {str(e)}")
    
    async def initiate_transfer(
        self,
        amount: float,
        destination_bank_code: str,
        destination_account_number: str,
        narration: str,
        reference: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Initiate a transfer through Moniepoint.
        
        Args:
            amount: Transfer amount
            destination_bank_code: Destination bank code
            destination_account_number: Destination account number
            narration: Transfer description
            reference: Optional transaction reference
            
        Returns:
            Dict: Transfer response
        """
        try:
            transfer_result = await self.rest_client.initiate_transfer(
                amount=amount,
                destination_bank_code=destination_bank_code,
                destination_account_number=destination_account_number,
                narration=narration,
                reference=reference
            )
            
            logger.info(f"Initiated Moniepoint transfer: {reference or 'auto-generated'}")
            return transfer_result
            
        except Exception as e:
            logger.error(f"Failed to initiate transfer: {str(e)}")
            raise create_moniepoint_exception(e)
    
    async def verify_account(
        self,
        account_number: str,
        bank_code: str
    ) -> Dict[str, Any]:
        """
        Verify account details.
        
        Args:
            account_number: Account number to verify
            bank_code: Bank code
            
        Returns:
            Dict: Account verification details
        """
        try:
            verification_result = await self.rest_client.verify_account(
                account_number=account_number,
                bank_code=bank_code
            )
            
            logger.info(f"Verified account: {account_number}")
            return verification_result
            
        except Exception as e:
            logger.error(f"Failed to verify account: {str(e)}")
            raise create_moniepoint_exception(e)
    
    # Private helper methods
    
    async def _get_transaction_metadata(self, transaction: POSTransaction) -> Dict[str, Any]:
        """Get Moniepoint-specific metadata for transaction."""
        metadata = {
            'merchant_id': self.auth_manager.merchant_id,
            'extraction_timestamp': datetime.utcnow().isoformat()
        }
        
        # Add any additional Moniepoint metadata from transaction
        if transaction.metadata:
            metadata.update({
                'payment_reference': transaction.metadata.get('moniepoint_payment_reference'),
                'order_reference': transaction.metadata.get('moniepoint_order_reference'),
                'product_code': transaction.metadata.get('moniepoint_product_code'),
                'channel': transaction.metadata.get('moniepoint_channel'),
                'payment_method': transaction.metadata.get('moniepoint_payment_method')
            })
        
        return metadata
    
    def _validate_webhook_payload(self, payload: WebhookPayload) -> bool:
        """Validate Moniepoint webhook payload."""
        required_fields = ['event_type', 'data']
        
        for field in required_fields:
            if not hasattr(payload, field) or not getattr(payload, field):
                return False
        
        # Validate event type
        valid_events = [
            'TRANSACTION_COMPLETED',
            'PAYMENT_RECEIVED',
            'SUCCESSFUL_TRANSACTION',
            'FAILED_TRANSACTION',
            'SETTLEMENT_COMPLETED',
            'ACCOUNT_CREDITED',
            'TRANSFER_COMPLETED'
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
        """Check if connector is connected to Moniepoint."""
        return self._is_connected
    
    @property
    def last_sync_time(self) -> Optional[datetime]:
        """Get last synchronization time."""
        return self._last_sync_time
    
    @property
    def connector_type(self) -> str:
        """Get connector type identifier."""
        return "moniepoint_pos"
    
    async def __aenter__(self):
        """Async context manager entry."""
        await self.connect()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.disconnect()