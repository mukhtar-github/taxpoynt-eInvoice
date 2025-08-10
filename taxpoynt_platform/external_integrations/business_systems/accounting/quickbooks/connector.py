"""
QuickBooks Accounting Connector
Main connector implementation for QuickBooks Online integration.
"""
import asyncio
import logging
from typing import Dict, Any, List, Optional, Set
from datetime import datetime, timedelta

from .auth import QuickBooksAuthManager
from .rest_client import QuickBooksRestClient
from .data_extractor import QuickBooksDataExtractor
from .ubl_transformer import QuickBooksUBLTransformer
from .exceptions import (
    QuickBooksConnectionError,
    QuickBooksAuthenticationError,
    QuickBooksDataError,
    QuickBooksValidationError
)
from ....connector_framework.base_accounting_connector import (
    BaseAccountingConnector,
    AccountingTransaction,
    AccountingContact,
    AccountingAccount,
    AccountingWebhookEvent,
    AccountingTransactionType,
    AccountingDocumentStatus
)
from .....core.invoice_processing.ubl_models import UBLInvoice


class QuickBooksConnector(BaseAccountingConnector):
    """
    QuickBooks Online accounting system connector.
    
    Provides:
    - Full QuickBooks Online API integration
    - Invoice and transaction data extraction
    - UBL 2.1 transformation for FIRS compliance
    - Real-time data synchronization
    - Webhook event processing
    """
    
    PLATFORM_NAME = "QuickBooks Online"
    SUPPORTED_COUNTRIES = ["NG", "US", "CA", "GB", "AU"]
    SUPPORTED_CURRENCIES = ["NGN", "USD", "CAD", "GBP", "AUD"]
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize QuickBooks connector.
        
        Expected config:
        {
            "client_id": "QuickBooks app client ID",
            "client_secret": "QuickBooks app client secret",
            "company_id": "QuickBooks company ID",
            "sandbox": bool,  # Use sandbox environment
            "webhook_verifier_token": "Webhook verification token",
            "auth_tokens": {
                "access_token": "OAuth2 access token",
                "refresh_token": "OAuth2 refresh token",
                "expires_at": "Token expiration timestamp"
            }
        }
        """
        super().__init__(config)
        self.logger = logging.getLogger(__name__)
        
        # Configuration validation
        required_fields = ["client_id", "client_secret", "company_id"]
        for field in required_fields:
            if not config.get(field):
                raise QuickBooksValidationError(f"Missing required config field: {field}")
        
        self.client_id = config["client_id"]
        self.client_secret = config["client_secret"]
        self.company_id = config["company_id"]
        self.sandbox = config.get("sandbox", True)
        self.webhook_verifier_token = config.get("webhook_verifier_token")
        
        # Initialize components
        self.auth_manager: Optional[QuickBooksAuthManager] = None
        self.rest_client: Optional[QuickBooksRestClient] = None
        self.data_extractor: Optional[QuickBooksDataExtractor] = None
        self.ubl_transformer: Optional[QuickBooksUBLTransformer] = None
        
        # Connection state
        self._connected = False
        self._company_info: Optional[Dict[str, Any]] = None
        self._last_sync: Optional[datetime] = None
        
        # Webhook processing
        self._webhook_handlers = {
            'invoice': self._handle_invoice_webhook,
            'customer': self._handle_customer_webhook,
            'item': self._handle_item_webhook
        }
    
    async def connect(self) -> bool:
        """
        Establish connection to QuickBooks Online.
        
        Returns:
            True if connection successful
            
        Raises:
            QuickBooksConnectionError: Connection failed
            QuickBooksAuthenticationError: Authentication failed
        """
        try:
            if self._connected:
                return True
            
            self.logger.info(f"Connecting to QuickBooks Online (Company: {self.company_id})")
            
            # Initialize authentication manager
            self.auth_manager = QuickBooksAuthManager(
                client_id=self.client_id,
                client_secret=self.client_secret,
                sandbox=self.sandbox
            )
            
            # Set existing tokens if available
            auth_tokens = self.config.get("auth_tokens", {})
            if auth_tokens.get("access_token"):
                await self.auth_manager.set_tokens(
                    access_token=auth_tokens["access_token"],
                    refresh_token=auth_tokens["refresh_token"],
                    expires_at=auth_tokens.get("expires_at")
                )
            
            # Initialize REST client
            self.rest_client = QuickBooksRestClient(
                auth_manager=self.auth_manager,
                company_id=self.company_id
            )
            
            # Test connection by fetching company info
            async with self.rest_client:
                self._company_info = await self.rest_client.get_company_info()
            
            # Initialize data extractor
            self.data_extractor = QuickBooksDataExtractor(self.rest_client)
            
            # Initialize UBL transformer
            self.ubl_transformer = QuickBooksUBLTransformer(self._company_info)
            
            self._connected = True
            self._last_sync = datetime.now()
            
            company_name = self._company_info.get('QueryResponse', {}).get('CompanyInfo', [{}])[0].get('CompanyName', 'Unknown')
            self.logger.info(f"Successfully connected to QuickBooks Online: {company_name}")
            
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to connect to QuickBooks Online: {str(e)}")
            if "authentication" in str(e).lower():
                raise QuickBooksAuthenticationError(f"Authentication failed: {str(e)}")
            else:
                raise QuickBooksConnectionError(f"Connection failed: {str(e)}")
    
    async def disconnect(self) -> None:
        """Disconnect from QuickBooks Online."""
        try:
            if self.rest_client:
                await self.rest_client.disconnect()
            
            self._connected = False
            self.logger.info("Disconnected from QuickBooks Online")
            
        except Exception as e:
            self.logger.warning(f"Error during disconnect: {str(e)}")
    
    async def test_connection(self) -> Dict[str, Any]:
        """
        Test QuickBooks Online connection.
        
        Returns:
            Connection test results
        """
        try:
            if not self._connected:
                await self.connect()
            
            # Test basic API access
            async with self.rest_client:
                company_info = await self.rest_client.get_company_info()
                
                # Test data access
                items = await self.rest_client.get_items()
                customers = await self.rest_client.get_customers()
                
                return {
                    "status": "success",
                    "connected": True,
                    "company_name": company_info.get('QueryResponse', {}).get('CompanyInfo', [{}])[0].get('CompanyName'),
                    "company_id": self.company_id,
                    "platform": self.PLATFORM_NAME,
                    "data_access": {
                        "items_count": len(items),
                        "customers_count": len(customers)
                    },
                    "last_sync": self._last_sync.isoformat() if self._last_sync else None,
                    "sandbox": self.sandbox
                }
        
        except Exception as e:
            return {
                "status": "error",
                "connected": False,
                "error": str(e),
                "platform": self.PLATFORM_NAME
            }
    
    async def get_invoices(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        customer_ids: Optional[Set[str]] = None,
        status_filter: Optional[Set[AccountingDocumentStatus]] = None
    ) -> List[AccountingTransaction]:
        """
        Retrieve invoices from QuickBooks Online.
        
        Args:
            start_date: Filter invoices from this date
            end_date: Filter invoices until this date
            customer_ids: Filter by specific customer IDs
            status_filter: Filter by document status
            
        Returns:
            List of normalized invoice transactions
        """
        if not self._connected:
            await self.connect()
        
        try:
            self.logger.info(f"Retrieving invoices from QuickBooks Online")
            
            # Extract invoices from QuickBooks
            invoices = await self.data_extractor.extract_invoices(
                start_date=start_date,
                end_date=end_date,
                customer_ids=customer_ids
            )
            
            # Apply status filter if specified
            if status_filter:
                invoices = [inv for inv in invoices if inv.status in status_filter]
            
            self.logger.info(f"Retrieved {len(invoices)} invoices from QuickBooks Online")
            return invoices
            
        except Exception as e:
            self.logger.error(f"Failed to retrieve invoices: {str(e)}")
            raise QuickBooksDataError(f"Invoice retrieval failed: {str(e)}")
    
    async def get_invoice_by_id(self, invoice_id: str) -> Optional[AccountingTransaction]:
        """
        Get specific invoice by ID.
        
        Args:
            invoice_id: QuickBooks invoice ID
            
        Returns:
            Normalized invoice transaction or None
        """
        if not self._connected:
            await self.connect()
        
        try:
            return await self.data_extractor.get_transaction_by_id(invoice_id, "Invoice")
        except Exception as e:
            self.logger.error(f"Failed to retrieve invoice {invoice_id}: {str(e)}")
            return None
    
    async def get_customers(
        self,
        active_only: bool = True,
        modified_since: Optional[datetime] = None
    ) -> List[AccountingContact]:
        """
        Retrieve customers from QuickBooks Online.
        
        Args:
            active_only: Only return active customers
            modified_since: Only return customers modified since this date
            
        Returns:
            List of normalized customer contacts
        """
        if not self._connected:
            await self.connect()
        
        try:
            return await self.data_extractor.extract_customers(
                active_only=active_only,
                modified_since=modified_since
            )
        except Exception as e:
            self.logger.error(f"Failed to retrieve customers: {str(e)}")
            raise QuickBooksDataError(f"Customer retrieval failed: {str(e)}")
    
    async def get_chart_of_accounts(self) -> List[AccountingAccount]:
        """
        Retrieve chart of accounts from QuickBooks Online.
        
        Returns:
            List of normalized account records
        """
        if not self._connected:
            await self.connect()
        
        try:
            return await self.data_extractor.extract_chart_of_accounts()
        except Exception as e:
            self.logger.error(f"Failed to retrieve chart of accounts: {str(e)}")
            raise QuickBooksDataError(f"Chart of accounts retrieval failed: {str(e)}")
    
    async def transform_to_ubl(self, transaction: AccountingTransaction) -> UBLInvoice:
        """
        Transform accounting transaction to UBL format.
        
        Args:
            transaction: Normalized accounting transaction
            
        Returns:
            UBL Invoice document
        """
        if not self._connected:
            await self.connect()
        
        try:
            if transaction.transaction_type == AccountingTransactionType.CREDIT_NOTE:
                return self.ubl_transformer.create_credit_note_ubl(transaction)
            else:
                return self.ubl_transformer.transform_invoice_to_ubl(transaction)
        except Exception as e:
            self.logger.error(f"Failed to transform transaction to UBL: {str(e)}")
            raise QuickBooksDataError(f"UBL transformation failed: {str(e)}")
    
    async def validate_ubl_invoice(self, ubl_invoice: UBLInvoice) -> List[str]:
        """
        Validate UBL invoice for FIRS compliance.
        
        Args:
            ubl_invoice: UBL invoice to validate
            
        Returns:
            List of validation errors (empty if valid)
        """
        if not self.ubl_transformer:
            await self.connect()
        
        return self.ubl_transformer.validate_ubl_invoice(ubl_invoice)
    
    async def sync_incremental(self, since: datetime) -> Dict[str, Any]:
        """
        Perform incremental sync since specified datetime.
        
        Args:
            since: Sync changes since this datetime
            
        Returns:
            Sync results summary
        """
        if not self._connected:
            await self.connect()
        
        try:
            self.logger.info(f"Starting incremental sync since {since}")
            
            # Sync in parallel
            invoices_task = asyncio.create_task(
                self.get_invoices(start_date=since)
            )
            customers_task = asyncio.create_task(
                self.get_customers(modified_since=since)
            )
            
            invoices, customers = await asyncio.gather(
                invoices_task, customers_task,
                return_exceptions=True
            )
            
            # Handle results
            invoice_count = len(invoices) if not isinstance(invoices, Exception) else 0
            customer_count = len(customers) if not isinstance(customers, Exception) else 0
            
            self._last_sync = datetime.now()
            
            sync_result = {
                "status": "success",
                "sync_timestamp": self._last_sync.isoformat(),
                "since": since.isoformat(),
                "changes": {
                    "invoices": invoice_count,
                    "customers": customer_count
                },
                "errors": []
            }
            
            # Add any errors
            if isinstance(invoices, Exception):
                sync_result["errors"].append(f"Invoice sync failed: {str(invoices)}")
            if isinstance(customers, Exception):
                sync_result["errors"].append(f"Customer sync failed: {str(customers)}")
            
            self.logger.info(f"Incremental sync completed: {invoice_count} invoices, {customer_count} customers")
            return sync_result
            
        except Exception as e:
            self.logger.error(f"Incremental sync failed: {str(e)}")
            raise QuickBooksDataError(f"Incremental sync failed: {str(e)}")
    
    async def process_webhook(self, payload: Dict[str, Any], headers: Dict[str, str]) -> AccountingWebhookEvent:
        """
        Process QuickBooks webhook notification.
        
        Args:
            payload: Webhook payload
            headers: HTTP headers
            
        Returns:
            Processed webhook event
        """
        try:
            # Verify webhook signature if verifier token is configured
            if self.webhook_verifier_token:
                signature = headers.get('intuit-signature')
                if not self._verify_webhook_signature(payload, signature):
                    raise QuickBooksValidationError("Invalid webhook signature")
            
            # Extract event information
            event_notifications = payload.get('eventNotifications', [])
            
            webhook_event = AccountingWebhookEvent(
                id=payload.get('eventNotifications', [{}])[0].get('id', ''),
                event_type=self._determine_event_type(event_notifications),
                timestamp=datetime.now(),
                source_system=self.PLATFORM_NAME,
                data=payload,
                processed=False
            )
            
            # Process individual entity changes
            for notification in event_notifications:
                realm_id = notification.get('realmId')
                if realm_id != self.company_id:
                    continue
                
                data_change_event = notification.get('dataChangeEvent', {})
                entities = data_change_event.get('entities', [])
                
                for entity in entities:
                    entity_name = entity.get('name', '').lower()
                    operation = entity.get('operation')
                    entity_id = entity.get('id')
                    
                    if entity_name in self._webhook_handlers:
                        await self._webhook_handlers[entity_name](
                            entity_id, operation, webhook_event
                        )
            
            webhook_event.processed = True
            return webhook_event
            
        except Exception as e:
            self.logger.error(f"Webhook processing failed: {str(e)}")
            raise QuickBooksDataError(f"Webhook processing failed: {str(e)}")
    
    def _verify_webhook_signature(self, payload: Dict[str, Any], signature: str) -> bool:
        """Verify webhook signature using verifier token."""
        # Implementation depends on QuickBooks webhook signature verification
        # This is a placeholder - implement according to QuickBooks documentation
        return True
    
    def _determine_event_type(self, event_notifications: List[Dict[str, Any]]) -> str:
        """Determine the primary event type from notifications."""
        if not event_notifications:
            return "unknown"
        
        # Extract entity types
        entity_types = set()
        for notification in event_notifications:
            data_change_event = notification.get('dataChangeEvent', {})
            entities = data_change_event.get('entities', [])
            for entity in entities:
                entity_types.add(entity.get('name', '').lower())
        
        if 'invoice' in entity_types:
            return 'invoice_changed'
        elif 'customer' in entity_types:
            return 'customer_changed'
        elif 'item' in entity_types:
            return 'item_changed'
        else:
            return 'data_changed'
    
    async def _handle_invoice_webhook(self, entity_id: str, operation: str, webhook_event: AccountingWebhookEvent) -> None:
        """Handle invoice webhook events."""
        self.logger.info(f"Processing invoice webhook: {operation} for {entity_id}")
        
        try:
            if operation in ['Create', 'Update']:
                # Fetch updated invoice data
                invoice = await self.get_invoice_by_id(entity_id)
                if invoice:
                    webhook_event.related_transactions = [invoice]
        except Exception as e:
            self.logger.warning(f"Failed to process invoice webhook: {str(e)}")
    
    async def _handle_customer_webhook(self, entity_id: str, operation: str, webhook_event: AccountingWebhookEvent) -> None:
        """Handle customer webhook events."""
        self.logger.info(f"Processing customer webhook: {operation} for {entity_id}")
        # Implementation for customer change handling
    
    async def _handle_item_webhook(self, entity_id: str, operation: str, webhook_event: AccountingWebhookEvent) -> None:
        """Handle item webhook events."""
        self.logger.info(f"Processing item webhook: {operation} for {entity_id}")
        # Implementation for item change handling
    
    async def get_auth_url(self, redirect_uri: str, state: str) -> str:
        """
        Get OAuth2 authorization URL for QuickBooks.
        
        Args:
            redirect_uri: OAuth2 redirect URI
            state: OAuth2 state parameter
            
        Returns:
            Authorization URL
        """
        if not self.auth_manager:
            self.auth_manager = QuickBooksAuthManager(
                client_id=self.client_id,
                client_secret=self.client_secret,
                sandbox=self.sandbox
            )
        
        return self.auth_manager.get_authorization_url(redirect_uri, state)
    
    async def handle_oauth_callback(self, code: str, state: str, realm_id: str) -> Dict[str, Any]:
        """
        Handle OAuth2 callback from QuickBooks.
        
        Args:
            code: Authorization code
            state: OAuth2 state parameter
            realm_id: QuickBooks company realm ID
            
        Returns:
            Token information
        """
        if not self.auth_manager:
            raise QuickBooksConnectionError("Auth manager not initialized")
        
        try:
            tokens = await self.auth_manager.exchange_code_for_tokens(code, realm_id)
            
            # Update company ID if provided
            if realm_id and realm_id != self.company_id:
                self.company_id = realm_id
            
            return {
                "status": "success",
                "company_id": realm_id,
                "tokens": tokens,
                "expires_at": tokens.get("expires_at")
            }
            
        except Exception as e:
            self.logger.error(f"OAuth callback handling failed: {str(e)}")
            raise QuickBooksAuthenticationError(f"OAuth callback failed: {str(e)}")
    
    def get_platform_info(self) -> Dict[str, Any]:
        """Get platform information."""
        return {
            "name": self.PLATFORM_NAME,
            "type": "accounting",
            "version": "1.0.0",
            "supported_countries": self.SUPPORTED_COUNTRIES,
            "supported_currencies": self.SUPPORTED_CURRENCIES,
            "features": {
                "invoices": True,
                "customers": True,
                "items": True,
                "chart_of_accounts": True,
                "ubl_transformation": True,
                "webhooks": True,
                "oauth2": True,
                "incremental_sync": True
            },
            "requirements": {
                "oauth2_setup": True,
                "webhook_endpoint": True,
                "ssl_certificate": True
            }
        }