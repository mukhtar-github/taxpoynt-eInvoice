"""
Toast POS Connector
Main connector implementation for Toast POS system integration.
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

from .auth import ToastAuthManager
from .rest_client import ToastRestClient
from .data_extractor import ToastDataExtractor
from .transaction_transformer import ToastTransactionTransformer
from .exceptions import (
    ToastConnectionError,
    ToastAuthenticationError,
    ToastAPIError,
    create_toast_exception
)

logger = logging.getLogger(__name__)


class ToastPOSConnector(BasePOSConnector):
    """
    Toast POS Connector Implementation
    
    Provides comprehensive integration with Toast POS systems including:
    - OAuth 2.0 authentication and token management
    - Transaction data extraction and synchronization
    - FIRS-compliant invoice transformation
    - Webhook processing and real-time updates
    - Multi-restaurant and multi-location support
    """
    
    def __init__(self, config: ConnectionConfig):
        """
        Initialize Toast POS connector.
        
        Args:
            config: Connection configuration with Toast credentials
        """
        super().__init__(config)
        
        # Initialize Toast components
        self.auth_manager = ToastAuthManager(config)
        self.rest_client = ToastRestClient(self.auth_manager)
        self.data_extractor = ToastDataExtractor(self.rest_client)
        self.transformer = ToastTransactionTransformer()
        
        # Connection state
        self._is_connected = False
        self._last_sync_time: Optional[datetime] = None
        self._restaurant_info: Optional[Dict[str, Any]] = None
        self._authorized_restaurants: List[Dict[str, Any]] = []
        
        # Configuration
        self.sync_config = {
            'batch_size': config.sync_config.get('batch_size', 100),
            'max_retries': config.sync_config.get('max_retries', 3),
            'retry_delay': config.sync_config.get('retry_delay', 5),
            'sync_interval': config.sync_config.get('sync_interval', 300),  # 5 minutes
            'webhook_enabled': config.sync_config.get('webhook_enabled', True),
            'concurrent_extractions': config.sync_config.get('concurrent_extractions', 3)
        }
        
        logger.info(f"Initialized Toast POS connector for restaurant: {config.restaurant_id}")
    
    async def connect(self) -> bool:
        """
        Establish connection to Toast POS system.
        
        Returns:
            bool: True if connection successful
            
        Raises:
            ToastConnectionError: If connection fails
            ToastAuthenticationError: If authentication fails
        """
        try:
            logger.info("Connecting to Toast POS system...")
            
            # Authenticate with Toast
            await self.auth_manager.authenticate()
            
            # Get authorized restaurants
            restaurants = await self.auth_manager.get_authorized_restaurants()
            if not restaurants:
                raise ToastConnectionError("No authorized restaurants found")
            
            self._authorized_restaurants = restaurants
            
            # Get specific restaurant info if restaurant_id is provided
            if self.config.restaurant_id:
                restaurant_info = await self.rest_client.get_restaurant_info(self.config.restaurant_id)
                if restaurant_info:
                    self._restaurant_info = restaurant_info
                else:
                    logger.warning(f"Could not find restaurant info for {self.config.restaurant_id}")
                    # Use first authorized restaurant as fallback
                    self._restaurant_info = restaurants[0]
            else:
                # Use first authorized restaurant
                self._restaurant_info = restaurants[0]
            
            self._is_connected = True
            
            restaurant_name = self._restaurant_info.get('restaurantName', 'Unknown')
            logger.info(f"Successfully connected to Toast POS - Restaurant: {restaurant_name}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to connect to Toast POS: {str(e)}")
            self._is_connected = False
            raise create_toast_exception(e)
    
    async def disconnect(self) -> bool:
        """
        Disconnect from Toast POS system.
        
        Returns:
            bool: True if disconnection successful
        """
        try:
            logger.info("Disconnecting from Toast POS system...")
            
            # Clean up resources
            await self.auth_manager.cleanup()
            self._is_connected = False
            self._restaurant_info = None
            self._authorized_restaurants = []
            
            logger.info("Successfully disconnected from Toast POS")
            return True
            
        except Exception as e:
            logger.error(f"Error during Toast POS disconnection: {str(e)}")
            return False
    
    async def test_connection(self) -> HealthStatus:
        """
        Test connection health to Toast POS system.
        
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
            restaurants = await self.auth_manager.get_authorized_restaurants()
            if not restaurants:
                return HealthStatus(
                    is_healthy=False,
                    status_message="No authorized restaurants",
                    last_check=datetime.utcnow(),
                    details={'api_status': 'no_access'}
                )
            
            # Connection is healthy
            return HealthStatus(
                is_healthy=True,
                status_message="Connection healthy",
                last_check=datetime.utcnow(),
                details={
                    'restaurant_count': len(restaurants),
                    'current_restaurant': self._restaurant_info.get('restaurantName') if self._restaurant_info else None,
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
        restaurant_ids: Optional[List[str]] = None
    ) -> SyncResult:
        """
        Synchronize transactions from Toast POS system.
        
        Args:
            start_date: Start date for sync (default: last sync time)
            end_date: End date for sync (default: now)
            restaurant_ids: Specific restaurant IDs to sync
            
        Returns:
            SyncResult: Synchronization results
            
        Raises:
            DataSyncError: If synchronization fails
        """
        try:
            logger.info("Starting Toast transaction synchronization...")
            
            # Set default date range
            if not start_date:
                start_date = self._last_sync_time or (datetime.utcnow() - timedelta(days=1))
            if not end_date:
                end_date = datetime.utcnow()
            
            # Determine restaurants to sync
            target_restaurants = []
            if restaurant_ids:
                target_restaurants = restaurant_ids
            elif self.config.restaurant_id:
                target_restaurants = [self.config.restaurant_id]
            else:
                # Sync all authorized restaurants
                target_restaurants = [r.get('guid') for r in self._authorized_restaurants if r.get('guid')]
            
            # Extract transactions from Toast
            all_transactions = []
            for restaurant_id in target_restaurants:
                try:
                    transactions = await self.data_extractor.extract_transactions(
                        restaurant_id=restaurant_id,
                        start_date=start_date,
                        end_date=end_date
                    )
                    all_transactions.extend(transactions)
                except Exception as e:
                    logger.error(f"Failed to extract from restaurant {restaurant_id}: {str(e)}")
                    continue
            
            logger.info(f"Extracted {len(all_transactions)} transactions from Toast")
            
            # Transform transactions to UBL invoices
            successful_invoices = []
            failed_transactions = []
            
            for transaction in all_transactions:
                try:
                    # Get Toast-specific metadata
                    toast_metadata = await self._get_transaction_metadata(transaction)
                    
                    # Transform to UBL invoice
                    invoice = await self.transformer.transform_transaction(
                        transaction,
                        self._restaurant_info,
                        toast_metadata
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
                records_processed=len(all_transactions),
                records_successful=len(successful_invoices),
                records_failed=len(failed_transactions),
                sync_start_time=start_date,
                sync_end_time=end_date,
                invoices=successful_invoices,
                errors=failed_transactions,
                metadata={
                    'source_system': 'toast_pos',
                    'restaurant_count': len(target_restaurants),
                    'restaurants_synced': target_restaurants
                }
            )
            
            logger.info(f"Toast sync completed: {len(successful_invoices)} successful, {len(failed_transactions)} failed")
            return result
            
        except Exception as e:
            logger.error(f"Toast transaction synchronization failed: {str(e)}")
            raise DataSyncError(f"Sync failed: {str(e)}")
    
    async def get_transaction(self, transaction_id: str, restaurant_id: Optional[str] = None) -> Optional[POSTransaction]:
        """
        Retrieve specific transaction from Toast POS.
        
        Args:
            transaction_id: Toast check GUID
            restaurant_id: Restaurant identifier (optional)
            
        Returns:
            POSTransaction: Transaction data or None if not found
        """
        try:
            # Use configured restaurant if not specified
            target_restaurant_id = restaurant_id or self.config.restaurant_id
            if not target_restaurant_id and self._restaurant_info:
                target_restaurant_id = self._restaurant_info.get('guid')
            
            if not target_restaurant_id:
                logger.error("No restaurant ID available for transaction retrieval")
                return None
            
            transaction = await self.data_extractor.get_single_transaction(
                target_restaurant_id, transaction_id
            )
            
            if transaction:
                logger.info(f"Retrieved Toast transaction: {transaction_id}")
            
            return transaction
            
        except Exception as e:
            logger.error(f"Failed to retrieve Toast transaction {transaction_id}: {str(e)}")
            return None
    
    async def process_webhook(self, payload: WebhookPayload) -> bool:
        """
        Process Toast webhook notification.
        
        Args:
            payload: Webhook payload from Toast
            
        Returns:
            bool: True if processing successful
        """
        try:
            logger.info(f"Processing Toast webhook: {payload.event_type}")
            
            # Validate webhook payload
            if not self._validate_webhook_payload(payload):
                logger.warning("Invalid Toast webhook payload")
                return False
            
            # Process based on event type
            if payload.event_type in ['ORDER_CREATED', 'ORDER_MODIFIED', 'CHECK_CREATED', 'CHECK_MODIFIED']:
                # Extract transaction from webhook data
                transaction = await self.data_extractor.extract_transaction_from_webhook(payload)
                
                if transaction:
                    # Transform to UBL invoice
                    toast_metadata = payload.data
                    invoice = await self.transformer.transform_transaction(
                        transaction,
                        self._restaurant_info,
                        toast_metadata
                    )
                    
                    # Trigger invoice processing (implementation specific)
                    await self._process_webhook_invoice(invoice, payload)
                    
                    logger.info(f"Successfully processed Toast webhook for transaction: {transaction.transaction_id}")
                    return True
            
            logger.info(f"Toast webhook {payload.event_type} processed successfully")
            return True
            
        except Exception as e:
            logger.error(f"Failed to process Toast webhook: {str(e)}")
            return False
    
    async def get_restaurant_info(self, restaurant_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Get restaurant information from Toast.
        
        Args:
            restaurant_id: Specific restaurant ID (optional)
            
        Returns:
            Dict: Restaurant information
        """
        try:
            if restaurant_id:
                return await self.rest_client.get_restaurant_info(restaurant_id) or {}
            elif self._restaurant_info:
                return self._restaurant_info
            else:
                return {}
        except Exception as e:
            logger.error(f"Failed to get Toast restaurant info: {str(e)}")
            return {}
    
    async def get_authorized_restaurants(self) -> List[Dict[str, Any]]:
        """
        Get all authorized restaurants.
        
        Returns:
            List[Dict]: Restaurant information
        """
        try:
            if self._authorized_restaurants:
                return self._authorized_restaurants
            
            restaurants = await self.auth_manager.get_authorized_restaurants()
            self._authorized_restaurants = restaurants
            logger.info(f"Retrieved {len(restaurants)} authorized Toast restaurants")
            return restaurants
            
        except Exception as e:
            logger.error(f"Failed to get authorized restaurants: {str(e)}")
            return []
    
    async def sync_batch_transactions(
        self,
        check_guids: List[str],
        restaurant_id: Optional[str] = None
    ) -> SyncResult:
        """
        Synchronize specific transactions by check GUID.
        
        Args:
            check_guids: List of Toast check GUIDs
            restaurant_id: Restaurant identifier (optional)
            
        Returns:
            SyncResult: Batch synchronization results
        """
        try:
            logger.info(f"Starting batch sync for {len(check_guids)} Toast transactions")
            
            # Use configured restaurant if not specified
            target_restaurant_id = restaurant_id or self.config.restaurant_id
            if not target_restaurant_id and self._restaurant_info:
                target_restaurant_id = self._restaurant_info.get('guid')
            
            if not target_restaurant_id:
                raise DataSyncError("No restaurant ID available for batch sync")
            
            successful_invoices = []
            failed_transactions = []
            
            # Process transactions in batches
            batch_size = self.sync_config['batch_size']
            for i in range(0, len(check_guids), batch_size):
                batch_guids = check_guids[i:i + batch_size]
                
                for check_guid in batch_guids:
                    try:
                        # Get transaction
                        transaction = await self.get_transaction(check_guid, target_restaurant_id)
                        if not transaction:
                            failed_transactions.append({
                                'transaction_id': check_guid,
                                'error': 'Transaction not found'
                            })
                            continue
                        
                        # Get metadata
                        toast_metadata = await self._get_transaction_metadata(transaction)
                        
                        # Transform to UBL invoice
                        invoice = await self.transformer.transform_transaction(
                            transaction,
                            self._restaurant_info,
                            toast_metadata
                        )
                        
                        successful_invoices.append(invoice)
                        
                    except Exception as e:
                        logger.error(f"Failed to process transaction {check_guid}: {str(e)}")
                        failed_transactions.append({
                            'transaction_id': check_guid,
                            'error': str(e)
                        })
                
                # Small delay between batches
                await asyncio.sleep(0.1)
            
            result = SyncResult(
                success=True,
                records_processed=len(check_guids),
                records_successful=len(successful_invoices),
                records_failed=len(failed_transactions),
                sync_start_time=datetime.utcnow(),
                sync_end_time=datetime.utcnow(),
                invoices=successful_invoices,
                errors=failed_transactions,
                metadata={
                    'source_system': 'toast_pos',
                    'sync_type': 'batch',
                    'restaurant_id': target_restaurant_id,
                    'batch_size': batch_size
                }
            )
            
            logger.info(f"Toast batch sync completed: {len(successful_invoices)} successful, {len(failed_transactions)} failed")
            return result
            
        except Exception as e:
            logger.error(f"Toast batch sync failed: {str(e)}")
            raise DataSyncError(f"Batch sync failed: {str(e)}")
    
    async def setup_webhooks(self, webhook_url: str, events: Optional[List[str]] = None) -> bool:
        """
        Setup webhook subscriptions for Toast events.
        
        Args:
            webhook_url: URL to receive webhook notifications
            events: List of events to subscribe to
            
        Returns:
            bool: True if setup successful
        """
        try:
            if not events:
                events = ['ORDER_CREATED', 'ORDER_MODIFIED', 'CHECK_CREATED', 'CHECK_MODIFIED']
            
            # Setup webhooks for each authorized restaurant
            for restaurant in self._authorized_restaurants:
                restaurant_id = restaurant.get('guid')
                if restaurant_id:
                    await self.auth_manager.create_webhook_subscription(
                        webhook_url, events, restaurant_id
                    )
            
            logger.info(f"Successfully setup Toast webhooks for {len(events)} events")
            return True
            
        except Exception as e:
            logger.error(f"Failed to setup Toast webhooks: {str(e)}")
            return False
    
    # Private helper methods
    
    async def _get_transaction_metadata(self, transaction: POSTransaction) -> Dict[str, Any]:
        """Get Toast-specific metadata for transaction."""
        metadata = {
            'restaurant_id': self.config.restaurant_id,
            'extraction_timestamp': datetime.utcnow().isoformat()
        }
        
        # Add any additional Toast metadata from transaction
        if transaction.metadata:
            metadata.update({
                'display_number': transaction.metadata.get('toast_display_number'),
                'dining_option': transaction.metadata.get('toast_dining_option'),
                'server_id': transaction.metadata.get('toast_server_id'),
                'table_id': transaction.metadata.get('toast_table_id')
            })
        
        return metadata
    
    def _validate_webhook_payload(self, payload: WebhookPayload) -> bool:
        """Validate Toast webhook payload."""
        required_fields = ['event_type', 'data']
        
        for field in required_fields:
            if not hasattr(payload, field) or not getattr(payload, field):
                return False
        
        # Validate event type
        valid_events = [
            'ORDER_CREATED', 'ORDER_MODIFIED', 'ORDER_DELETED',
            'CHECK_CREATED', 'CHECK_MODIFIED', 'CHECK_DELETED',
            'PAYMENT_CREATED', 'PAYMENT_MODIFIED',
            'RESTAURANT_UPDATED'
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
        """Check if connector is connected to Toast."""
        return self._is_connected
    
    @property
    def last_sync_time(self) -> Optional[datetime]:
        """Get last synchronization time."""
        return self._last_sync_time
    
    @property
    def connector_type(self) -> str:
        """Get connector type identifier."""
        return "toast_pos"
    
    async def __aenter__(self):
        """Async context manager entry."""
        await self.connect()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.disconnect()