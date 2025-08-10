"""
Sage Business Cloud Accounting Connector
Main connector implementation for Sage Business Cloud Accounting integration.
"""
import asyncio
import logging
from typing import Dict, Any, List, Optional, Set
from datetime import datetime, timedelta

from .auth import SageAuthManager
from .rest_client import SageRestClient
from .data_extractor import SageDataExtractor
from .ubl_transformer import SageUBLTransformer
from .exceptions import (
    SageConnectionError,
    SageAuthenticationError,
    SageDataError,
    SageValidationError,
    SageBusinessError
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


class SageConnector(BaseAccountingConnector):
    """
    Sage Business Cloud Accounting system connector.
    
    Provides:
    - Full Sage Business Cloud Accounting API integration
    - Multi-business support with business selection
    - Sales and purchase invoice data extraction
    - UBL 2.1 transformation for FIRS compliance
    - Multi-currency support with exchange rates
    - UK and Nigerian tax compliance
    """
    
    PLATFORM_NAME = "Sage Business Cloud Accounting"
    SUPPORTED_COUNTRIES = ["NG", "GB", "US", "CA", "AU", "IE", "FR", "DE", "ES"]
    SUPPORTED_CURRENCIES = ["NGN", "GBP", "USD", "CAD", "AUD", "EUR"]
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize Sage connector.
        
        Expected config:
        {
            "client_id": "Sage app client ID",
            "client_secret": "Sage app client secret",
            "redirect_uri": "OAuth2 redirect URI",
            "business_id": "Sage business ID (optional, can be set later)",
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
        required_fields = ["client_id", "client_secret", "redirect_uri"]
        for field in required_fields:
            if not config.get(field):
                raise SageValidationError(f"Missing required config field: {field}")
        
        self.client_id = config["client_id"]
        self.client_secret = config["client_secret"]
        self.redirect_uri = config["redirect_uri"]
        self.business_id = config.get("business_id")
        
        # Initialize components
        self.auth_manager: Optional[SageAuthManager] = None
        self.rest_client: Optional[SageRestClient] = None
        self.data_extractor: Optional[SageDataExtractor] = None
        self.ubl_transformer: Optional[SageUBLTransformer] = None
        
        # Connection state
        self._connected = False
        self._business_info: Optional[Dict[str, Any]] = None
        self._last_sync: Optional[datetime] = None
        
        # Available businesses
        self._available_businesses: List[Dict[str, Any]] = []
    
    async def connect(self) -> bool:
        """
        Establish connection to Sage Business Cloud Accounting.
        
        Returns:
            True if connection successful
            
        Raises:
            SageConnectionError: Connection failed
            SageAuthenticationError: Authentication failed
            SageBusinessError: No valid business selected
        """
        try:
            if self._connected:
                return True
            
            self.logger.info(f"Connecting to Sage Business Cloud Accounting (Business: {self.business_id or 'Not set'})")
            
            # Initialize authentication manager
            self.auth_manager = SageAuthManager(
                client_id=self.client_id,
                client_secret=self.client_secret,
                redirect_uri=self.redirect_uri
            )
            
            # Set existing tokens if available
            auth_tokens = self.config.get("auth_tokens", {})
            if auth_tokens.get("access_token"):
                await self.auth_manager.set_tokens(
                    access_token=auth_tokens["access_token"],
                    refresh_token=auth_tokens["refresh_token"],
                    expires_at=auth_tokens.get("expires_at"),
                    business_id=self.business_id
                )
            
            # Set business if provided and not already set
            if self.business_id and not self.auth_manager.business_id:
                self.auth_manager.set_business(self.business_id)
            
            # Validate that we have a business selected
            if not self.auth_manager.business_id:
                available_businesses = self.auth_manager.list_available_businesses()
                if not available_businesses:
                    raise SageAuthenticationError("No Sage businesses available. Please complete OAuth2 flow first.")
                elif len(available_businesses) == 1:
                    # Auto-select single business
                    self.auth_manager.set_business(available_businesses[0]['id'])
                    self.business_id = available_businesses[0]['id']
                else:
                    business_list = [f"{b.get('name', 'Unknown')} ({b['id']})" for b in available_businesses]
                    raise SageBusinessError(
                        f"Multiple businesses available. Please specify business_id. Available: {', '.join(business_list)}"
                    )
            
            # Initialize REST client
            self.rest_client = SageRestClient(self.auth_manager)
            
            # Test connection by fetching business info
            async with self.rest_client:
                self._business_info = await self.rest_client.get_business_info()
            
            # Initialize data extractor
            self.data_extractor = SageDataExtractor(self.rest_client)
            
            # Initialize UBL transformer
            self.ubl_transformer = SageUBLTransformer(self._business_info)
            
            self._connected = True
            self._last_sync = datetime.now()
            self._available_businesses = self.auth_manager.list_available_businesses()
            
            business_name = self._business_info.get('name', 'Unknown')
            self.logger.info(f"Successfully connected to Sage Business Cloud Accounting: {business_name} (Business: {self.business_id})")
            
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to connect to Sage Business Cloud Accounting: {str(e)}")
            if "authentication" in str(e).lower() or "auth" in str(e).lower():
                raise SageAuthenticationError(f"Authentication failed: {str(e)}")
            elif "business" in str(e).lower():
                raise SageBusinessError(f"Business error: {str(e)}")
            else:
                raise SageConnectionError(f"Connection failed: {str(e)}")
    
    async def disconnect(self) -> None:
        """Disconnect from Sage Business Cloud Accounting."""
        try:
            if self.rest_client:
                await self.rest_client.disconnect()
            
            self._connected = False
            self.logger.info("Disconnected from Sage Business Cloud Accounting")
            
        except Exception as e:
            self.logger.warning(f"Error during disconnect: {str(e)}")
    
    async def test_connection(self) -> Dict[str, Any]:
        """
        Test Sage Business Cloud Accounting connection.
        
        Returns:
            Connection test results
        """
        try:
            if not self._connected:
                await self.connect()
            
            # Test basic API access
            async with self.rest_client:
                business_info = await self.rest_client.get_business_info()
                
                # Test data access
                contacts_result = await self.rest_client.get_contacts(items_per_page=5, page=1)
                accounts_result = await self.rest_client.get_ledger_accounts(items_per_page=5, page=1)
                
                return {
                    "status": "success",
                    "connected": True,
                    "business_name": business_info.get('name'),
                    "business_id": self.business_id,
                    "platform": self.PLATFORM_NAME,
                    "data_access": {
                        "contacts_available": len(contacts_result.get('$items', [])),
                        "accounts_available": len(accounts_result.get('$items', []))
                    },
                    "last_sync": self._last_sync.isoformat() if self._last_sync else None,
                    "rate_limits": self.rest_client.get_rate_limit_status() if self.rest_client else {},
                    "available_businesses": len(self._available_businesses),
                    "auth_status": self.auth_manager.get_auth_status() if self.auth_manager else {},
                    "business_info": {
                        "currency": business_info.get('base_currency', {}).get('currency_code', ''),
                        "country": business_info.get('country', ''),
                        "subscription_type": business_info.get('subscription_type', ''),
                        "active": business_info.get('active', True)
                    }
                }
        
        except Exception as e:
            return {
                "status": "error",
                "connected": False,
                "error": str(e),
                "platform": self.PLATFORM_NAME,
                "business_id": self.business_id
            }
    
    async def get_invoices(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        contact_ids: Optional[Set[str]] = None,
        status_filter: Optional[Set[AccountingDocumentStatus]] = None,
        invoice_type: str = "sales"
    ) -> List[AccountingTransaction]:
        """
        Retrieve invoices from Sage Business Cloud Accounting.
        
        Args:
            start_date: Filter invoices from this date
            end_date: Filter invoices until this date
            contact_ids: Filter by specific contact IDs
            status_filter: Filter by document status
            invoice_type: Type of invoices (sales, purchase)
            
        Returns:
            List of normalized invoice transactions
        """
        if not self._connected:
            await self.connect()
        
        try:
            self.logger.info(f"Retrieving {invoice_type} invoices from Sage Business Cloud Accounting")
            
            # Extract invoices from Sage
            invoices = await self.data_extractor.extract_invoices(
                start_date=start_date,
                end_date=end_date,
                contact_ids=contact_ids,
                invoice_type=invoice_type
            )
            
            # Apply status filter if specified
            if status_filter:
                invoices = [inv for inv in invoices if inv.status in status_filter]
            
            self.logger.info(f"Retrieved {len(invoices)} {invoice_type} invoices from Sage Business Cloud Accounting")
            return invoices
            
        except Exception as e:
            self.logger.error(f"Failed to retrieve {invoice_type} invoices: {str(e)}")
            raise SageDataError(f"{invoice_type.title()} invoice retrieval failed: {str(e)}")
    
    async def get_sales_invoices(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        contact_ids: Optional[Set[str]] = None,
        status_filter: Optional[Set[AccountingDocumentStatus]] = None
    ) -> List[AccountingTransaction]:
        """
        Retrieve sales invoices from Sage Business Cloud Accounting.
        
        Args:
            start_date: Filter invoices from this date
            end_date: Filter invoices until this date
            contact_ids: Filter by specific contact IDs
            status_filter: Filter by document status
            
        Returns:
            List of normalized sales invoice transactions
        """
        return await self.get_invoices(
            start_date=start_date,
            end_date=end_date,
            contact_ids=contact_ids,
            status_filter=status_filter,
            invoice_type="sales"
        )
    
    async def get_purchase_invoices(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        contact_ids: Optional[Set[str]] = None,
        status_filter: Optional[Set[AccountingDocumentStatus]] = None
    ) -> List[AccountingTransaction]:
        """
        Retrieve purchase invoices from Sage Business Cloud Accounting.
        
        Args:
            start_date: Filter invoices from this date
            end_date: Filter invoices until this date
            contact_ids: Filter by specific contact IDs
            status_filter: Filter by document status
            
        Returns:
            List of normalized purchase invoice transactions
        """
        return await self.get_invoices(
            start_date=start_date,
            end_date=end_date,
            contact_ids=contact_ids,
            status_filter=status_filter,
            invoice_type="purchase"
        )
    
    async def get_invoice_by_id(self, invoice_id: str, invoice_type: str = "sales") -> Optional[AccountingTransaction]:
        """
        Get specific invoice by ID.
        
        Args:
            invoice_id: Sage invoice ID
            invoice_type: Type of invoice (sales, purchase)
            
        Returns:
            Normalized invoice transaction or None
        """
        if not self._connected:
            await self.connect()
        
        try:
            transaction_type = f"{invoice_type}_invoice"
            return await self.data_extractor.get_transaction_by_id(invoice_id, transaction_type)
        except Exception as e:
            self.logger.error(f"Failed to retrieve {invoice_type} invoice {invoice_id}: {str(e)}")
            return None
    
    async def get_customers(
        self,
        active_only: bool = True
    ) -> List[AccountingContact]:
        """
        Retrieve customers from Sage Business Cloud Accounting.
        
        Args:
            active_only: Only return active customers (Sage doesn't have inactive status)
            
        Returns:
            List of normalized customer contacts
        """
        if not self._connected:
            await self.connect()
        
        try:
            return await self.data_extractor.extract_contacts(
                active_only=active_only,
                contact_type="Customer"
            )
        except Exception as e:
            self.logger.error(f"Failed to retrieve customers: {str(e)}")
            raise SageDataError(f"Customer retrieval failed: {str(e)}")
    
    async def get_suppliers(
        self,
        active_only: bool = True
    ) -> List[AccountingContact]:
        """
        Retrieve suppliers from Sage Business Cloud Accounting.
        
        Args:
            active_only: Only return active suppliers
            
        Returns:
            List of normalized supplier contacts
        """
        if not self._connected:
            await self.connect()
        
        try:
            return await self.data_extractor.extract_contacts(
                active_only=active_only,
                contact_type="Vendor"
            )
        except Exception as e:
            self.logger.error(f"Failed to retrieve suppliers: {str(e)}")
            raise SageDataError(f"Supplier retrieval failed: {str(e)}")
    
    async def get_chart_of_accounts(self) -> List[AccountingAccount]:
        """
        Retrieve chart of accounts from Sage Business Cloud Accounting.
        
        Returns:
            List of normalized account records
        """
        if not self._connected:
            await self.connect()
        
        try:
            return await self.data_extractor.extract_chart_of_accounts()
        except Exception as e:
            self.logger.error(f"Failed to retrieve chart of accounts: {str(e)}")
            raise SageDataError(f"Chart of accounts retrieval failed: {str(e)}")
    
    async def get_credit_notes(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> List[AccountingTransaction]:
        """
        Retrieve credit notes from Sage Business Cloud Accounting.
        
        Args:
            start_date: Filter credit notes from this date
            end_date: Filter credit notes until this date
            
        Returns:
            List of normalized credit note transactions
        """
        if not self._connected:
            await self.connect()
        
        try:
            return await self.data_extractor.extract_credit_notes(
                start_date=start_date,
                end_date=end_date
            )
        except Exception as e:
            self.logger.error(f"Failed to retrieve credit notes: {str(e)}")
            raise SageDataError(f"Credit notes retrieval failed: {str(e)}")
    
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
            raise SageDataError(f"UBL transformation failed: {str(e)}")
    
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
            sales_invoices_task = asyncio.create_task(
                self.get_sales_invoices(start_date=since)
            )
            purchase_invoices_task = asyncio.create_task(
                self.get_purchase_invoices(start_date=since)
            )
            customers_task = asyncio.create_task(
                self.get_customers()
            )
            suppliers_task = asyncio.create_task(
                self.get_suppliers()
            )
            credit_notes_task = asyncio.create_task(
                self.get_credit_notes(start_date=since)
            )
            
            sales_invoices, purchase_invoices, customers, suppliers, credit_notes = await asyncio.gather(
                sales_invoices_task, purchase_invoices_task, customers_task, suppliers_task, credit_notes_task,
                return_exceptions=True
            )
            
            # Handle results
            sales_invoice_count = len(sales_invoices) if not isinstance(sales_invoices, Exception) else 0
            purchase_invoice_count = len(purchase_invoices) if not isinstance(purchase_invoices, Exception) else 0
            customer_count = len(customers) if not isinstance(customers, Exception) else 0
            supplier_count = len(suppliers) if not isinstance(suppliers, Exception) else 0
            credit_note_count = len(credit_notes) if not isinstance(credit_notes, Exception) else 0
            
            self._last_sync = datetime.now()
            
            sync_result = {
                "status": "success",
                "sync_timestamp": self._last_sync.isoformat(),
                "since": since.isoformat(),
                "business_id": self.business_id,
                "changes": {
                    "sales_invoices": sales_invoice_count,
                    "purchase_invoices": purchase_invoice_count,
                    "customers": customer_count,
                    "suppliers": supplier_count,
                    "credit_notes": credit_note_count,
                    "total_invoices": sales_invoice_count + purchase_invoice_count
                },
                "errors": []
            }
            
            # Add any errors
            if isinstance(sales_invoices, Exception):
                sync_result["errors"].append(f"Sales invoice sync failed: {str(sales_invoices)}")
            if isinstance(purchase_invoices, Exception):
                sync_result["errors"].append(f"Purchase invoice sync failed: {str(purchase_invoices)}")
            if isinstance(customers, Exception):
                sync_result["errors"].append(f"Customer sync failed: {str(customers)}")
            if isinstance(suppliers, Exception):
                sync_result["errors"].append(f"Supplier sync failed: {str(suppliers)}")
            if isinstance(credit_notes, Exception):
                sync_result["errors"].append(f"Credit notes sync failed: {str(credit_notes)}")
            
            self.logger.info(f"Incremental sync completed: {sales_invoice_count} sales invoices, "
                           f"{purchase_invoice_count} purchase invoices, {customer_count} customers, "
                           f"{supplier_count} suppliers, {credit_note_count} credit notes")
            return sync_result
            
        except Exception as e:
            self.logger.error(f"Incremental sync failed: {str(e)}")
            raise SageDataError(f"Incremental sync failed: {str(e)}")
    
    async def get_auth_url(self, state: str, scopes: Optional[List[str]] = None) -> str:
        """
        Get OAuth2 authorization URL for Sage Business Cloud Accounting.
        
        Args:
            state: OAuth2 state parameter
            scopes: Optional custom scopes
            
        Returns:
            Authorization URL
        """
        if not self.auth_manager:
            self.auth_manager = SageAuthManager(
                client_id=self.client_id,
                client_secret=self.client_secret,
                redirect_uri=self.redirect_uri
            )
        
        return self.auth_manager.get_authorization_url(state, scopes)
    
    async def handle_oauth_callback(self, code: str, state: str) -> Dict[str, Any]:
        """
        Handle OAuth2 callback from Sage Business Cloud Accounting.
        
        Args:
            code: Authorization code
            state: OAuth2 state parameter
            
        Returns:
            Token and business information
        """
        if not self.auth_manager:
            raise SageConnectionError("Auth manager not initialized")
        
        try:
            tokens_info = await self.auth_manager.exchange_code_for_tokens(code, state)
            
            # Update available businesses
            self._available_businesses = tokens_info.get('businesses', [])
            
            return {
                "status": "success",
                "tokens": {
                    "access_token": tokens_info["access_token"],
                    "refresh_token": tokens_info["refresh_token"],
                    "expires_at": tokens_info["expires_at"]
                },
                "businesses": self._available_businesses,
                "requires_business_selection": len(self._available_businesses) > 1
            }
            
        except Exception as e:
            self.logger.error(f"OAuth callback handling failed: {str(e)}")
            raise SageAuthenticationError(f"OAuth callback failed: {str(e)}")
    
    def set_business(self, business_id: str) -> None:
        """
        Set active business.
        
        Args:
            business_id: Sage business ID
            
        Raises:
            SageBusinessError: Invalid business ID
        """
        if self.auth_manager:
            self.auth_manager.set_business(business_id)
        
        self.business_id = business_id
        self.logger.info(f"Set active business: {business_id}")
    
    def get_available_businesses(self) -> List[Dict[str, Any]]:
        """
        Get list of available businesses.
        
        Returns:
            List of business information
        """
        if self.auth_manager:
            return self.auth_manager.list_available_businesses()
        return self._available_businesses
    
    def get_platform_info(self) -> Dict[str, Any]:
        """Get platform information."""
        return {
            "name": self.PLATFORM_NAME,
            "type": "accounting",
            "version": "1.0.0",
            "supported_countries": self.SUPPORTED_COUNTRIES,
            "supported_currencies": self.SUPPORTED_CURRENCIES,
            "features": {
                "sales_invoices": True,
                "purchase_invoices": True,
                "credit_notes": True,
                "customers": True,
                "suppliers": True,
                "chart_of_accounts": True,
                "ubl_transformation": True,
                "multi_business": True,
                "oauth2": True,
                "incremental_sync": True,
                "multi_currency": True,
                "exchange_rates": True,
                "uk_vat_compliance": True,
                "nigerian_vat_compliance": True,
                "real_time_sync": False  # Sage doesn't have webhooks
            },
            "requirements": {
                "oauth2_setup": True,
                "business_selection": True,
                "pkce_support": True
            },
            "rate_limits": {
                "calls_per_hour": 5000,
                "burst_support": False
            },
            "api_version": "3.1",
            "authentication": {
                "type": "oauth2",
                "flows": ["authorization_code"],
                "scopes": ["full_access"]
            }
        }
    
    async def create_sales_invoice(self, invoice_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create new sales invoice in Sage Business Cloud Accounting.
        
        Args:
            invoice_data: Invoice data in Sage format
            
        Returns:
            Created invoice response
        """
        if not self._connected:
            await self.connect()
        
        try:
            async with self.rest_client:
                return await self.rest_client.create_sales_invoice(invoice_data)
        except Exception as e:
            self.logger.error(f"Failed to create sales invoice: {str(e)}")
            raise SageDataError(f"Sales invoice creation failed: {str(e)}")
    
    async def create_contact(self, contact_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create new contact in Sage Business Cloud Accounting.
        
        Args:
            contact_data: Contact data in Sage format
            
        Returns:
            Created contact response
        """
        if not self._connected:
            await self.connect()
        
        try:
            async with self.rest_client:
                return await self.rest_client.create_contact(contact_data)
        except Exception as e:
            self.logger.error(f"Failed to create contact: {str(e)}")
            raise SageDataError(f"Contact creation failed: {str(e)}")
    
    def get_multi_currency_info(self, transaction: AccountingTransaction) -> Dict[str, Any]:
        """
        Get multi-currency information for a transaction.
        
        Args:
            transaction: Accounting transaction
            
        Returns:
            Multi-currency information
        """
        if not self.ubl_transformer:
            return {"requires_conversion": False}
        
        return self.ubl_transformer.handle_multi_currency_transaction(transaction, 'NGN')
    
    def is_authenticated(self) -> bool:
        """Check if connector is authenticated."""
        return (
            self.auth_manager is not None and
            self.auth_manager.is_authenticated() and
            self.business_id is not None
        )
    
    def get_connection_status(self) -> Dict[str, Any]:
        """Get detailed connection status."""
        return {
            "connected": self._connected,
            "authenticated": self.is_authenticated(),
            "business_id": self.business_id,
            "available_businesses_count": len(self._available_businesses),
            "last_sync": self._last_sync.isoformat() if self._last_sync else None,
            "auth_status": self.auth_manager.get_auth_status() if self.auth_manager else {},
            "rate_limits": self.rest_client.get_rate_limit_status() if self.rest_client else {},
            "business_name": self._business_info.get('name') if self._business_info else None,
            "business_currency": self._business_info.get('base_currency', {}).get('currency_code') if self._business_info else None,
            "platform": self.PLATFORM_NAME
        }