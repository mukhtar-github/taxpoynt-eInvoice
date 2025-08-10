"""
Lightspeed POS Connector - Main Module

Integrates all Lightspeed POS connector components for TaxPoynt eInvoice System Integrator functions.

This module combines OAuth 2.0 authentication, REST API communication, data extraction, 
and transaction-to-invoice transformation into a unified connector interface compatible with the BasePOSConnector.
"""

import asyncio
import logging
from typing import Any, Dict, List, Optional
from datetime import datetime

from ....connector_framework.base_pos_connector import (
    BasePOSConnector, POSTransaction, POSWebhookEvent, POSLocation, 
    POSPaymentMethod, POSInventoryItem
)
from .auth import LightspeedAuthenticator
from .rest_client import LightspeedRESTClient
from .data_extractor import LightspeedDataExtractor
from .transaction_transformer import LightspeedTransactionTransformer
from .exceptions import (
    LightspeedAPIError, LightspeedAuthenticationError, LightspeedConnectionError,
    LightspeedWebhookError, LightspeedConfigurationError
)

logger = logging.getLogger(__name__)


class LightspeedPOSConnector(BasePOSConnector):
    """
    Lightspeed POS Connector for TaxPoynt eInvoice - System Integrator Functions.
    
    This module provides System Integrator (SI) role functionality for Lightspeed POS integration,
    supporting both Lightspeed Retail (R-Series) and Restaurant (K-Series) systems.
    
    Enhanced with modular architecture for better maintainability and testing.
    
    SI Role Responsibilities:
    - Lightspeed API connectivity and OAuth 2.0 authentication
    - Sale/Transaction data extraction and management
    - Real-time webhook processing (when supported)
    - Connection health monitoring and error handling
    - Transaction data transformation for FIRS-compliant invoice generation
    - Location and inventory management
    
    Supported Lightspeed APIs:
    - Retail API (R-Series): Sales, customers, items, locations
    - Restaurant API (K-Series): Orders, customers, products, locations
    - OAuth 2.0 Authentication for both API types
    
    Nigerian Market Adaptations:
    - Currency conversion to NGN
    - 7.5% VAT calculations
    - TIN validation and compliance
    - FIRS-compliant invoice generation
    """
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize the Lightspeed POS connector with configuration.
        
        Args:
            config: Configuration dictionary containing Lightspeed-specific settings
        """
        super().__init__(config)
        self.logger = logging.getLogger(__name__)
        
        # Validate required configuration
        self._validate_config(config)
        
        # Initialize components
        self.auth = LightspeedAuthenticator(config)
        self.client = LightspeedRESTClient(self.auth)
        self.extractor = LightspeedDataExtractor(self.client, config)
        self.transformer = LightspeedTransactionTransformer(config)
        
        # Lightspeed-specific settings
        self.api_type = config.get('api_type', 'retail')  # 'retail' or 'restaurant'
        self.auto_sync_enabled = config.get('auto_sync_enabled', False)
        self.sync_interval_minutes = config.get('sync_interval_minutes', 15)
        self.location_ids = config.get('location_ids', [])
        
        # Performance settings
        self.batch_size = config.get('batch_size', 100)
        self.max_concurrent_requests = config.get('max_concurrent_requests', 3)  # Conservative for Lightspeed
        
        self.logger.info(f"Lightspeed POS connector initialized for API type: {self.api_type}")
    
    def _validate_config(self, config: Dict[str, Any]):
        """Validate required configuration parameters."""
        required_fields = ['client_id', 'client_secret', 'redirect_uri']
        
        for field in required_fields:
            if not config.get(field):
                raise LightspeedConfigurationError(
                    field, f"Missing required configuration field: {field}"
                )
        
        # Validate API type
        api_type = config.get('api_type', 'retail')
        if api_type not in ['retail', 'restaurant']:
            raise LightspeedConfigurationError(
                'api_type', f"Invalid API type: {api_type}. Must be 'retail' or 'restaurant'"
            )
    
    async def authenticate(self) -> bool:
        """
        Authenticate with Lightspeed POS system.
        
        Returns:
            True if authentication successful, False otherwise
        """
        try:
            result = await self.auth.authenticate()
            if result:
                self.logger.info("Lightspeed POS authentication successful")
            else:
                self.logger.error("Lightspeed POS authentication failed")
            return result
        except Exception as e:
            self.logger.error(f"Lightspeed authentication error: {str(e)}")
            raise LightspeedAuthenticationError(f"Authentication failed: {str(e)}")
    
    async def test_connection(self) -> Dict[str, Any]:
        """
        Test connection to Lightspeed POS system.
        
        Returns:
            Connection test results
        """
        try:
            # Test authentication
            auth_result = await self.auth.test_authentication()
            if not auth_result.get('success'):
                return {
                    'success': False,
                    'error': f"Authentication failed: {auth_result.get('error')}",
                    'component': 'authentication'
                }
            
            # Test API access
            api_result = await self.auth.test_api_access()
            if not api_result.get('success'):
                return {
                    'success': False,
                    'error': f"API access failed: {api_result.get('error')}",
                    'component': 'api_access'
                }
            
            # Perform health check
            health_result = await self.client.health_check()
            
            # Get account info
            try:
                account_info = await self.auth.get_account_info()
            except Exception as e:
                account_info = {'error': str(e)}
            
            return {
                'success': True,
                'message': 'Lightspeed POS connection successful',
                'authentication': auth_result,
                'api_access': api_result,
                'health_check': health_result,
                'account_info': account_info,
                'connector_info': {
                    'api_type': self.api_type,
                    'base_url': self.auth.base_url,
                    'account_id': self.auth.account_id,
                    'location_ids': self.location_ids,
                    'available_features': self.get_supported_features()
                }
            }
        
        except Exception as e:
            self.logger.error(f"Connection test failed: {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'component': 'connection_test'
            }
    
    async def get_transactions(self,
                             filters: Optional[Dict[str, Any]] = None,
                             limit: Optional[int] = None) -> List[POSTransaction]:
        """
        Retrieve transactions from Lightspeed POS.
        
        Args:
            filters: Filter criteria including:
                - location_id: Specific location/shop
                - start_date: Start date for transaction range
                - end_date: End date for transaction range
                - payment_method: Filter by payment method
                - min_amount: Minimum transaction amount
                - max_amount: Maximum transaction amount
                - customer_id: Filter by customer
                - register_id: Filter by register/terminal
                - completed: Only completed transactions (default: true)
            limit: Maximum number of transactions to return
        
        Returns:
            List of POSTransaction objects
        """
        try:
            self.logger.info(f"Retrieving Lightspeed transactions with filters: {filters}")
            
            # Ensure authentication
            if not await self.auth.ensure_valid_token():
                raise LightspeedAuthenticationError("Failed to authenticate with Lightspeed")
            
            # Extract transactions using data extractor
            transactions = await self.extractor.extract_transactions(filters, limit)
            
            self.logger.info(f"Retrieved {len(transactions)} transactions from Lightspeed")
            return transactions
        
        except Exception as e:
            self.logger.error(f"Error retrieving transactions: {str(e)}")
            raise
    
    async def get_transaction_by_id(self, transaction_id: str) -> Optional[POSTransaction]:
        """
        Retrieve a specific transaction by ID.
        
        Args:
            transaction_id: Lightspeed sale ID
        
        Returns:
            POSTransaction object or None if not found
        """
        try:
            if not await self.auth.ensure_valid_token():
                raise LightspeedAuthenticationError("Failed to authenticate with Lightspeed")
            
            transaction = await self.extractor.extract_transaction_by_id(transaction_id)
            
            if transaction:
                self.logger.info(f"Retrieved transaction {transaction_id} from Lightspeed")
            else:
                self.logger.warning(f"Transaction {transaction_id} not found in Lightspeed")
            
            return transaction
        
        except Exception as e:
            self.logger.error(f"Error retrieving transaction {transaction_id}: {str(e)}")
            raise
    
    async def process_webhook(self, webhook_data: Dict[str, Any]) -> POSWebhookEvent:
        """
        Process incoming webhook from Lightspeed.
        
        Note: Lightspeed doesn't have extensive webhook support like some other POS systems.
        This method provides a framework for future webhook implementations.
        
        Args:
            webhook_data: Raw webhook payload from Lightspeed
        
        Returns:
            Processed POSWebhookEvent
        """
        try:
            # Extract webhook details
            event_type = webhook_data.get('event_type', webhook_data.get('type', 'unknown'))
            event_id = webhook_data.get('id', f"lightspeed_{int(datetime.now().timestamp())}")
            
            # Extract event data
            data = webhook_data.get('data', webhook_data)
            
            # Create webhook event
            webhook_event = POSWebhookEvent(
                event_type=event_type,
                event_id=event_id,
                timestamp=datetime.now(),
                data=data,
                source='lightspeed',
                processed=False
            )
            
            # Process specific event types
            await self._process_webhook_event(webhook_event)
            
            self.logger.info(f"Processed Lightspeed webhook: {event_type}")
            return webhook_event
        
        except Exception as e:
            self.logger.error(f"Error processing webhook: {str(e)}")
            raise LightspeedWebhookError(
                message=f"Webhook processing failed: {str(e)}",
                webhook_event=webhook_data.get('event_type', 'unknown')
            )
    
    async def _process_webhook_event(self, webhook_event: POSWebhookEvent):
        """Process specific webhook event types."""
        event_type = webhook_event.event_type
        
        try:
            if event_type == 'sale_created':
                await self._handle_sale_created(webhook_event)
            elif event_type == 'sale_updated':
                await self._handle_sale_updated(webhook_event)
            elif event_type == 'sale_completed':
                await self._handle_sale_completed(webhook_event)
            elif event_type == 'customer_created':
                await self._handle_customer_created(webhook_event)
            elif event_type == 'customer_updated':
                await self._handle_customer_updated(webhook_event)
            elif event_type == 'item_created':
                await self._handle_item_created(webhook_event)
            elif event_type == 'item_updated':
                await self._handle_item_updated(webhook_event)
            else:
                self.logger.info(f"Unhandled webhook event type: {event_type}")
            
            webhook_event.processed = True
            
        except Exception as e:
            self.logger.error(f"Error processing webhook event {event_type}: {str(e)}")
            raise
    
    async def _handle_sale_created(self, webhook_event: POSWebhookEvent):
        """Handle sale_created webhook event."""
        sale_data = webhook_event.data
        sale_id = sale_data.get('id', sale_data.get('saleID'))
        
        if sale_id:
            self.logger.info(f"Processing new sale: {sale_id}")
            # Additional processing logic here
    
    async def _handle_sale_updated(self, webhook_event: POSWebhookEvent):
        """Handle sale_updated webhook event."""
        sale_data = webhook_event.data
        sale_id = sale_data.get('id', sale_data.get('saleID'))
        
        if sale_id:
            self.logger.info(f"Sale updated: {sale_id}")
            # Update processing logic here
    
    async def _handle_sale_completed(self, webhook_event: POSWebhookEvent):
        """Handle sale_completed webhook event."""
        sale_data = webhook_event.data
        sale_id = sale_data.get('id', sale_data.get('saleID'))
        
        if sale_id:
            self.logger.info(f"Sale completed: {sale_id}")
            # Completion processing logic here (e.g., auto-generate invoice)
    
    async def _handle_customer_created(self, webhook_event: POSWebhookEvent):
        """Handle customer_created webhook event."""
        customer_data = webhook_event.data
        customer_id = customer_data.get('id', customer_data.get('customerID'))
        
        if customer_id:
            self.logger.info(f"New customer created: {customer_id}")
    
    async def _handle_customer_updated(self, webhook_event: POSWebhookEvent):
        """Handle customer_updated webhook event."""
        customer_data = webhook_event.data
        customer_id = customer_data.get('id', customer_data.get('customerID'))
        
        if customer_id:
            self.logger.info(f"Customer updated: {customer_id}")
    
    async def _handle_item_created(self, webhook_event: POSWebhookEvent):
        """Handle item_created webhook event."""
        item_data = webhook_event.data
        item_id = item_data.get('id', item_data.get('itemID'))
        
        if item_id:
            self.logger.info(f"New item created: {item_id}")
    
    async def _handle_item_updated(self, webhook_event: POSWebhookEvent):
        """Handle item_updated webhook event."""
        item_data = webhook_event.data
        item_id = item_data.get('id', item_data.get('itemID'))
        
        if item_id:
            self.logger.info(f"Item updated: {item_id}")
    
    async def get_locations(self) -> List[POSLocation]:
        """
        Retrieve all locations/shops from Lightspeed.
        
        Returns:
            List of POSLocation objects
        """
        try:
            if not await self.auth.ensure_valid_token():
                raise LightspeedAuthenticationError("Failed to authenticate with Lightspeed")
            
            locations = await self.extractor.extract_locations()
            
            self.logger.info(f"Retrieved {len(locations)} locations from Lightspeed")
            return locations
        
        except Exception as e:
            self.logger.error(f"Error retrieving locations: {str(e)}")
            raise
    
    async def get_payment_methods(self) -> List[POSPaymentMethod]:
        """
        Retrieve available payment methods.
        
        Returns:
            List of POSPaymentMethod objects
        """
        try:
            payment_methods = await self.extractor.extract_payment_methods()
            
            self.logger.info(f"Retrieved {len(payment_methods)} payment methods")
            return payment_methods
        
        except Exception as e:
            self.logger.error(f"Error retrieving payment methods: {str(e)}")
            raise
    
    async def transform_transaction_to_invoice(self,
                                             transaction_id: str,
                                             transformation_options: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Transform Lightspeed transaction to FIRS-compliant invoice.
        
        Args:
            transaction_id: Transaction to transform (sale ID)
            transformation_options: Additional settings including:
                - issue_date: Invoice issue date
                - due_date: Invoice due date
                - invoice_number: Custom invoice number
                - customer_tin: Customer TIN number
                - include_tax_breakdown: Detailed tax information
                - location_info: Lightspeed location information
        
        Returns:
            FIRS-compliant invoice data (UBL format)
        """
        try:
            # Get transaction
            transaction = await self.get_transaction_by_id(transaction_id)
            if not transaction:
                raise LightspeedAPIError(f"Transaction {transaction_id} not found")
            
            # Add location info to transformation options if available
            if not transformation_options:
                transformation_options = {}
            
            if 'location_info' not in transformation_options and transaction.location_id:
                try:
                    locations = await self.get_locations()
                    location_info = None
                    for loc in locations:
                        if loc.location_id == transaction.location_id:
                            location_info = {
                                'name': loc.name,
                                'address': loc.address
                            }
                            break
                    
                    if location_info:
                        transformation_options['location_info'] = location_info
                except Exception as e:
                    self.logger.warning(f"Could not retrieve location info: {str(e)}")
            
            # Transform to invoice
            invoice_data = await self.transformer.transform_transaction_to_invoice(
                transaction, transformation_options
            )
            
            self.logger.info(f"Transformed transaction {transaction_id} to FIRS invoice")
            return invoice_data
        
        except Exception as e:
            self.logger.error(f"Error transforming transaction to invoice: {str(e)}")
            raise
    
    async def get_inventory(self,
                          filters: Optional[Dict[str, Any]] = None) -> List[POSInventoryItem]:
        """
        Retrieve inventory items from Lightspeed products.
        
        Args:
            filters: Filter criteria for inventory items
        
        Returns:
            List of POSInventoryItem objects
        """
        try:
            if not await self.auth.ensure_valid_token():
                raise LightspeedAuthenticationError("Failed to authenticate with Lightspeed")
            
            items = await self.extractor.extract_inventory_items(filters)
            
            self.logger.info(f"Retrieved {len(items)} inventory items from Lightspeed")
            return items
        
        except Exception as e:
            self.logger.error(f"Error retrieving inventory: {str(e)}")
            raise
    
    async def sync_transactions(self,
                              sync_options: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Synchronize transactions from Lightspeed POS.
        
        Args:
            sync_options: Synchronization options including:
                - full_sync: Whether to perform full synchronization
                - last_sync_date: Last synchronization timestamp
                - batch_size: Number of transactions per batch
                - location_id: Specific location to sync
                - completed_only: Only sync completed sales (default: true)
        
        Returns:
            Synchronization results
        """
        try:
            options = sync_options or {}
            batch_size = options.get('batch_size', self.batch_size)
            
            self.logger.info(f"Starting Lightspeed transaction sync with options: {options}")
            
            # Build filters for sync
            filters = {}
            
            if options.get('location_id'):
                filters['location_id'] = options['location_id']
            
            if options.get('last_sync_date') and not options.get('full_sync', False):
                filters['start_date'] = options['last_sync_date']
            
            if options.get('completed_only', True):
                filters['completed'] = True
            
            # Get all transactions
            all_transactions = await self.get_transactions(filters=filters)
            
            # Process in batches
            batches = [
                all_transactions[i:i + batch_size] 
                for i in range(0, len(all_transactions), batch_size)
            ]
            
            processed_count = 0
            failed_count = 0
            
            sync_results = {
                'total_records': len(all_transactions),
                'batches_processed': len(batches),
                'batch_size': batch_size,
                'processed_count': 0,
                'failed_count': 0,
                'sync_timestamp': datetime.now().isoformat(),
                'transactions': []
            }
            
            # Process batches with rate limiting
            for batch_index, batch in enumerate(batches):
                self.logger.info(f"Processing batch {batch_index + 1}/{len(batches)} ({len(batch)} records)")
                
                # Process batch transactions
                batch_results = []
                for transaction in batch:
                    try:
                        # Add to results
                        batch_results.append(transaction)
                        processed_count += 1
                    except Exception as e:
                        self.logger.error(f"Error processing transaction {transaction.transaction_id}: {str(e)}")
                        failed_count += 1
                
                sync_results['transactions'].extend(batch_results)
                
                # Rate limiting between batches
                if batch_index < len(batches) - 1:
                    await asyncio.sleep(1.0)  # Lightspeed rate limiting
            
            sync_results['processed_count'] = processed_count
            sync_results['failed_count'] = failed_count
            
            self.logger.info(f"Sync completed: {processed_count} processed, {failed_count} failed")
            return sync_results
        
        except Exception as e:
            self.logger.error(f"Error during sync: {str(e)}")
            return {
                'error': str(e),
                'sync_timestamp': datetime.now().isoformat(),
                'processed_count': 0,
                'failed_count': 0
            }
    
    async def disconnect(self) -> bool:
        """
        Disconnect from Lightspeed POS system.
        
        Returns:
            True if disconnection successful
        """
        try:
            result = await self.auth.disconnect()
            if result:
                self.logger.info("Lightspeed POS disconnection successful")
            else:
                self.logger.warning("Lightspeed POS disconnection completed with warnings")
            return result
        except Exception as e:
            self.logger.error(f"Error during Lightspeed disconnect: {str(e)}")
            return False
    
    def get_supported_features(self) -> List[str]:
        """Get list of features supported by Lightspeed POS connector."""
        features = super().get_supported_features()
        features.extend([
            'oauth_authentication',
            'transaction_retrieval',
            'location_management',
            'payment_methods',
            'inventory_integration',
            'invoice_transformation',
            'firs_compliance',
            'nigerian_tax_handling',
            'multi_api_support',  # Both retail and restaurant APIs
            'customer_management',
            'product_management',
            'batch_processing',
            'transaction_sync',
            'daily_reporting',
            'multi_currency',
            'rate_limiting'
        ])
        return features
    
    def get_connection_info(self) -> Dict[str, Any]:
        """Get detailed connection information."""
        return {
            'connector_type': 'lightspeed_pos',
            'version': '1.0',
            'authentication': self.auth.get_connection_info(),
            'features': self.get_supported_features(),
            'configuration': {
                'api_type': self.api_type,
                'base_url': self.auth.base_url,
                'account_id': self.auth.account_id,
                'auto_sync_enabled': self.auto_sync_enabled,
                'batch_size': self.batch_size,
                'max_concurrent_requests': self.max_concurrent_requests,
                'location_ids': self.location_ids
            },
            'nigerian_compliance': {
                'firs_integration': True,
                'vat_rate': float(self.vat_rate),
                'currency_support': ['NGN', 'USD', 'EUR', 'GBP'],
                'tin_validation': True,
                'ubl_bis_3_0': True
            },
            'lightspeed_specific': {
                'supports_retail_api': True,
                'supports_restaurant_api': True,
                'webhook_support': 'limited',  # Lightspeed has limited webhook support
                'rate_limit_aware': True,
                'multi_location_support': True
            }
        }