"""
Clover POS Connector
Main connector implementation for Clover POS system integration.
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

from .auth import CloverAuthManager
from .rest_client import CloverRestClient
from .data_extractor import CloverDataExtractor
from .transaction_transformer import CloverTransactionTransformer
from .exceptions import (
    CloverConnectionError,
    CloverAuthenticationError,
    CloverAPIError,
    create_clover_exception
)

logger = logging.getLogger(__name__)


class CloverPOSConnector(BasePOSConnector):
    """
    Clover POS Connector Implementation
    
    Provides comprehensive integration with Clover POS systems including:
    - OAuth 2.0 authentication and token management
    - Transaction data extraction and synchronization
    - FIRS-compliant invoice transformation
    - Webhook processing and real-time updates
    - Multi-merchant and multi-location support
    """
    
    def __init__(self, config: ConnectionConfig):
        """
        Initialize Clover POS connector.
        
        Args:
            config: Connection configuration with Clover credentials
        """
        super().__init__(config)
        
        # Initialize Clover components
        self.auth_manager = CloverAuthManager(config)
        self.rest_client = CloverRestClient(self.auth_manager)
        self.data_extractor = CloverDataExtractor(self.rest_client)
        self.transformer = CloverTransactionTransformer()
        
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
            'webhook_enabled': config.sync_config.get('webhook_enabled', True)
        }
        
        logger.info(f"Initialized Clover POS connector for merchant: {config.merchant_id}")
    
    async def connect(self) -> bool:
        """
        Establish connection to Clover POS system.
        
        Returns:
            bool: True if connection successful
            
        Raises:
            CloverConnectionError: If connection fails
            CloverAuthenticationError: If authentication fails
        """
        try:
            logger.info("Connecting to Clover POS system...")
            
            # Authenticate with Clover
            await self.auth_manager.authenticate()
            
            # Test connection by fetching merchant info
            merchant_info = await self.rest_client.get_merchant_info()
            if not merchant_info:
                raise CloverConnectionError("Failed to retrieve merchant information")
            
            self._merchant_info = merchant_info
            self._is_connected = True
            
            logger.info(f"Successfully connected to Clover POS - Merchant: {merchant_info.get('name', 'Unknown')}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to connect to Clover POS: {str(e)}")
            self._is_connected = False
            raise create_clover_exception(e)
    
    async def disconnect(self) -> bool:
        """
        Disconnect from Clover POS system.
        
        Returns:
            bool: True if disconnection successful
        """
        try:
            logger.info("Disconnecting from Clover POS system...")
            
            # Clean up resources
            await self.auth_manager.cleanup()
            self._is_connected = False
            self._merchant_info = None
            
            logger.info("Successfully disconnected from Clover POS")
            return True
            
        except Exception as e:
            logger.error(f"Error during Clover POS disconnection: {str(e)}")
            return False
    
    async def test_connection(self) -> HealthStatus:
        """
        Test connection health to Clover POS system.
        
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
                    'merchant_id': merchant_info.get('id'),
                    'merchant_name': merchant_info.get('name'),
                    'api_status': 'connected',
                    'auth_status': 'valid'
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
        location_ids: Optional[List[str]] = None
    ) -> SyncResult:
        """
        Synchronize transactions from Clover POS system.
        
        Args:
            start_date: Start date for sync (default: last sync time)
            end_date: End date for sync (default: now)
            location_ids: Specific location IDs to sync
            
        Returns:
            SyncResult: Synchronization results
            
        Raises:
            DataSyncError: If synchronization fails
        """
        try:
            logger.info("Starting Clover transaction synchronization...")
            
            # Set default date range
            if not start_date:
                start_date = self._last_sync_time or (datetime.utcnow() - timedelta(days=1))
            if not end_date:
                end_date = datetime.utcnow()
            
            # Extract transactions from Clover
            transactions = await self.data_extractor.extract_transactions(
                start_date=start_date,
                end_date=end_date,
                location_ids=location_ids
            )
            
            logger.info(f"Extracted {len(transactions)} transactions from Clover")
            
            # Transform transactions to UBL invoices
            successful_invoices = []
            failed_transactions = []
            
            for transaction in transactions:
                try:
                    # Get Clover-specific metadata
                    clover_metadata = await self._get_transaction_metadata(transaction)
                    
                    # Transform to UBL invoice
                    invoice = await self.transformer.transform_transaction(
                        transaction,
                        self._merchant_info,
                        clover_metadata
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
                    'source_system': 'clover_pos',
                    'merchant_id': self._merchant_info.get('id') if self._merchant_info else None,
                    'location_count': len(location_ids) if location_ids else 'all'
                }
            )
            
            logger.info(f"Clover sync completed: {len(successful_invoices)} successful, {len(failed_transactions)} failed")
            return result
            
        except Exception as e:
            logger.error(f"Clover transaction synchronization failed: {str(e)}")
            raise DataSyncError(f"Sync failed: {str(e)}")
    
    async def get_transaction(self, transaction_id: str) -> Optional[POSTransaction]:
        """
        Retrieve specific transaction from Clover POS.
        
        Args:
            transaction_id: Clover order/payment ID
            
        Returns:
            POSTransaction: Transaction data or None if not found
        """
        try:
            transaction = await self.data_extractor.get_single_transaction(transaction_id)
            logger.info(f"Retrieved Clover transaction: {transaction_id}")
            return transaction
            
        except Exception as e:
            logger.error(f"Failed to retrieve Clover transaction {transaction_id}: {str(e)}")
            return None
    
    async def process_webhook(self, payload: WebhookPayload) -> bool:
        """
        Process Clover webhook notification.
        
        Args:
            payload: Webhook payload from Clover
            
        Returns:
            bool: True if processing successful
        """
        try:
            logger.info(f"Processing Clover webhook: {payload.event_type}")
            
            # Validate webhook payload
            if not self._validate_webhook_payload(payload):
                logger.warning("Invalid Clover webhook payload")
                return False
            
            # Process based on event type
            if payload.event_type in ['ORDER_CREATED', 'ORDER_UPDATED', 'PAYMENT_CREATED']:
                # Extract transaction from webhook data
                transaction = await self.data_extractor.extract_transaction_from_webhook(payload)
                
                if transaction:
                    # Transform to UBL invoice
                    clover_metadata = payload.data
                    invoice = await self.transformer.transform_transaction(
                        transaction,
                        self._merchant_info,
                        clover_metadata
                    )
                    
                    # Trigger invoice processing (implementation specific)
                    await self._process_webhook_invoice(invoice, payload)
                    
                    logger.info(f"Successfully processed Clover webhook for transaction: {transaction.transaction_id}")
                    return True
            
            logger.info(f"Clover webhook {payload.event_type} processed successfully")
            return True
            
        except Exception as e:
            logger.error(f"Failed to process Clover webhook: {str(e)}")
            return False
    
    async def get_merchant_info(self) -> Dict[str, Any]:
        """
        Get merchant information from Clover.
        
        Returns:
            Dict: Merchant information
        """
        if not self._merchant_info:
            self._merchant_info = await self.rest_client.get_merchant_info()
        
        return self._merchant_info or {}
    
    async def get_locations(self) -> List[Dict[str, Any]]:
        """
        Get all locations for the merchant.
        
        Returns:
            List[Dict]: Location information
        """
        try:
            locations = await self.rest_client.get_locations()
            logger.info(f"Retrieved {len(locations)} Clover locations")
            return locations
            
        except Exception as e:
            logger.error(f"Failed to get Clover locations: {str(e)}")
            return []
    
    async def sync_batch_transactions(
        self,
        transaction_ids: List[str]
    ) -> SyncResult:
        """
        Synchronize specific transactions by ID.
        
        Args:
            transaction_ids: List of Clover transaction IDs
            
        Returns:
            SyncResult: Batch synchronization results
        """
        try:
            logger.info(f"Starting batch sync for {len(transaction_ids)} Clover transactions")
            
            successful_invoices = []
            failed_transactions = []
            
            # Process transactions in batches
            batch_size = self.sync_config['batch_size']
            for i in range(0, len(transaction_ids), batch_size):
                batch_ids = transaction_ids[i:i + batch_size]
                
                for transaction_id in batch_ids:
                    try:
                        # Get transaction
                        transaction = await self.get_transaction(transaction_id)
                        if not transaction:
                            failed_transactions.append({
                                'transaction_id': transaction_id,
                                'error': 'Transaction not found'
                            })
                            continue
                        
                        # Get metadata
                        clover_metadata = await self._get_transaction_metadata(transaction)
                        
                        # Transform to UBL invoice
                        invoice = await self.transformer.transform_transaction(
                            transaction,
                            self._merchant_info,
                            clover_metadata
                        )
                        
                        successful_invoices.append(invoice)
                        
                    except Exception as e:
                        logger.error(f"Failed to process transaction {transaction_id}: {str(e)}")
                        failed_transactions.append({
                            'transaction_id': transaction_id,
                            'error': str(e)
                        })
                
                # Small delay between batches
                await asyncio.sleep(0.1)
            
            result = SyncResult(
                success=True,
                records_processed=len(transaction_ids),
                records_successful=len(successful_invoices),
                records_failed=len(failed_transactions),
                sync_start_time=datetime.utcnow(),
                sync_end_time=datetime.utcnow(),
                invoices=successful_invoices,
                errors=failed_transactions,
                metadata={
                    'source_system': 'clover_pos',
                    'sync_type': 'batch',
                    'batch_size': batch_size
                }
            )
            
            logger.info(f"Clover batch sync completed: {len(successful_invoices)} successful, {len(failed_transactions)} failed")
            return result
            
        except Exception as e:
            logger.error(f"Clover batch sync failed: {str(e)}")
            raise DataSyncError(f"Batch sync failed: {str(e)}")
    
    # Private helper methods
    
    async def _get_transaction_metadata(self, transaction: POSTransaction) -> Dict[str, Any]:
        """Get Clover-specific metadata for transaction."""
        metadata = {
            'merchant_id': self.config.merchant_id,
            'extraction_timestamp': datetime.utcnow().isoformat()
        }
        
        # Add any additional Clover metadata from transaction
        if transaction.metadata:
            metadata.update(transaction.metadata)
        
        return metadata
    
    def _validate_webhook_payload(self, payload: WebhookPayload) -> bool:
        """Validate Clover webhook payload."""
        required_fields = ['event_type', 'data']
        
        for field in required_fields:
            if not hasattr(payload, field) or not getattr(payload, field):
                return False
        
        # Validate event type
        valid_events = [
            'ORDER_CREATED', 'ORDER_UPDATED', 'ORDER_DELETED',
            'PAYMENT_CREATED', 'PAYMENT_UPDATED', 'PAYMENT_DELETED',
            'INVENTORY_UPDATED', 'MERCHANT_UPDATED'
        ]
        
        return payload.event_type in valid_events
    
    async def _process_webhook_invoice(self, invoice: UBLInvoice, payload: WebhookPayload) -> None:
        """Process invoice from webhook (implementation specific)."""
        # This would typically send the invoice to the TaxPoynt processing pipeline
        # Implementation depends on the specific invoice processing system
        logger.info(f"Processing webhook invoice: {invoice.header.invoice_id}")
        
        # Add webhook processing logic here
        # For example: await self.invoice_processor.process_invoice(invoice)
    
    @property
    def is_connected(self) -> bool:
        """Check if connector is connected to Clover."""
        return self._is_connected
    
    @property
    def last_sync_time(self) -> Optional[datetime]:
        """Get last synchronization time."""
        return self._last_sync_time
    
    @property
    def connector_type(self) -> str:
        """Get connector type identifier."""
        return "clover_pos"
    
    async def __aenter__(self):
        """Async context manager entry."""
        await self.connect()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.disconnect()