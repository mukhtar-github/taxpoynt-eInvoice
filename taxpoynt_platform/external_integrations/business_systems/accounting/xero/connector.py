"""
Xero Accounting Connector
Main connector implementation for Xero accounting integration.
"""
import asyncio
import logging
from typing import Dict, Any, List, Optional, Set
from datetime import datetime, timedelta

from .auth import XeroAuthManager
from .rest_client import XeroRestClient
from .data_extractor import XeroDataExtractor
from .ubl_transformer import XeroUBLTransformer
from .exceptions import (
    XeroConnectionError,
    XeroAuthenticationError,
    XeroDataError,
    XeroValidationError,
    XeroOrganisationError
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


class XeroConnector(BaseAccountingConnector):
    """
    Xero accounting system connector.
    
    Provides:
    - Full Xero Accounting API integration
    - Multi-tenant organization support
    - Invoice and transaction data extraction
    - UBL 2.1 transformation for FIRS compliance
    - Real-time data synchronization
    - Multi-currency support
    """
    
    PLATFORM_NAME = "Xero"
    SUPPORTED_COUNTRIES = ["NG", "NZ", "AU", "US", "GB", "CA"]
    SUPPORTED_CURRENCIES = ["NGN", "NZD", "AUD", "USD", "GBP", "CAD", "EUR"]
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize Xero connector.
        
        Expected config:
        {
            "client_id": "Xero app client ID",
            "client_secret": "Xero app client secret", 
            "redirect_uri": "OAuth2 redirect URI",
            "tenant_id": "Xero tenant ID (optional, can be set later)",
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
                raise XeroValidationError(f"Missing required config field: {field}")
        
        self.client_id = config["client_id"]
        self.client_secret = config["client_secret"]
        self.redirect_uri = config["redirect_uri"]
        self.tenant_id = config.get("tenant_id")
        
        # Initialize components
        self.auth_manager: Optional[XeroAuthManager] = None
        self.rest_client: Optional[XeroRestClient] = None
        self.data_extractor: Optional[XeroDataExtractor] = None
        self.ubl_transformer: Optional[XeroUBLTransformer] = None
        
        # Connection state
        self._connected = False
        self._organisation_info: Optional[Dict[str, Any]] = None
        self._last_sync: Optional[datetime] = None
        
        # Available tenants
        self._available_tenants: List[Dict[str, Any]] = []
    
    async def connect(self) -> bool:
        """
        Establish connection to Xero.
        
        Returns:
            True if connection successful
            
        Raises:
            XeroConnectionError: Connection failed
            XeroAuthenticationError: Authentication failed
            XeroOrganisationError: No valid tenant selected
        """
        try:
            if self._connected:
                return True
            
            self.logger.info(f"Connecting to Xero (Tenant: {self.tenant_id or 'Not set'})")
            
            # Initialize authentication manager
            self.auth_manager = XeroAuthManager(
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
                    tenant_id=self.tenant_id
                )
            
            # Set tenant if provided and not already set
            if self.tenant_id and not self.auth_manager.tenant_id:
                self.auth_manager.set_tenant(self.tenant_id)
            
            # Validate that we have a tenant selected
            if not self.auth_manager.tenant_id:
                available_tenants = self.auth_manager.list_available_tenants()
                if not available_tenants:
                    raise XeroAuthenticationError("No Xero organizations available. Please complete OAuth2 flow first.")
                elif len(available_tenants) == 1:
                    # Auto-select single tenant
                    self.auth_manager.set_tenant(available_tenants[0]['tenantId'])
                    self.tenant_id = available_tenants[0]['tenantId']
                else:
                    tenant_list = [f"{t['tenantName']} ({t['tenantId']})" for t in available_tenants]
                    raise XeroOrganisationError(
                        f"Multiple tenants available. Please specify tenant_id. Available: {', '.join(tenant_list)}"
                    )
            
            # Initialize REST client
            self.rest_client = XeroRestClient(self.auth_manager)
            
            # Test connection by fetching organisation info
            async with self.rest_client:
                self._organisation_info = await self.rest_client.get_organisation()
            
            # Initialize data extractor
            self.data_extractor = XeroDataExtractor(self.rest_client)
            
            # Initialize UBL transformer
            self.ubl_transformer = XeroUBLTransformer(self._organisation_info)
            
            self._connected = True
            self._last_sync = datetime.now()
            self._available_tenants = self.auth_manager.list_available_tenants()
            
            org_name = self._organisation_info.get('Organisations', [{}])[0].get('Name', 'Unknown')
            self.logger.info(f"Successfully connected to Xero: {org_name} (Tenant: {self.tenant_id})")
            
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to connect to Xero: {str(e)}")
            if "authentication" in str(e).lower() or "auth" in str(e).lower():
                raise XeroAuthenticationError(f"Authentication failed: {str(e)}")
            elif "tenant" in str(e).lower() or "organisation" in str(e).lower():
                raise XeroOrganisationError(f"Organisation error: {str(e)}")
            else:
                raise XeroConnectionError(f"Connection failed: {str(e)}")
    
    async def disconnect(self) -> None:
        """Disconnect from Xero."""
        try:
            if self.rest_client:
                await self.rest_client.disconnect()
            
            self._connected = False
            self.logger.info("Disconnected from Xero")
            
        except Exception as e:
            self.logger.warning(f"Error during disconnect: {str(e)}")
    
    async def test_connection(self) -> Dict[str, Any]:
        """
        Test Xero connection.
        
        Returns:
            Connection test results
        """
        try:
            if not self._connected:
                await self.connect()
            
            # Test basic API access
            async with self.rest_client:
                org_info = await self.rest_client.get_organisation()
                
                # Test data access
                contacts_result = await self.rest_client.get_contacts(order="Name", page=1)
                accounts_result = await self.rest_client.get_accounts(order="Name")
                
                org_data = org_info.get('Organisations', [{}])[0]
                
                return {
                    "status": "success",
                    "connected": True,
                    "organisation_name": org_data.get('Name'),
                    "organisation_id": org_data.get('OrganisationID'),
                    "tenant_id": self.tenant_id,
                    "platform": self.PLATFORM_NAME,
                    "data_access": {
                        "contacts_available": len(contacts_result.get('Contacts', [])),
                        "accounts_available": len(accounts_result.get('Accounts', []))
                    },
                    "last_sync": self._last_sync.isoformat() if self._last_sync else None,
                    "rate_limits": self.rest_client.get_rate_limit_status() if self.rest_client else {},
                    "available_tenants": len(self._available_tenants),
                    "auth_status": self.auth_manager.get_auth_status() if self.auth_manager else {}
                }
        
        except Exception as e:
            return {
                "status": "error",
                "connected": False,
                "error": str(e),
                "platform": self.PLATFORM_NAME,
                "tenant_id": self.tenant_id
            }
    
    async def get_invoices(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        contact_ids: Optional[Set[str]] = None,
        status_filter: Optional[Set[AccountingDocumentStatus]] = None,
        invoice_type: Optional[str] = None
    ) -> List[AccountingTransaction]:
        """
        Retrieve invoices from Xero.
        
        Args:
            start_date: Filter invoices from this date
            end_date: Filter invoices until this date
            contact_ids: Filter by specific contact IDs
            status_filter: Filter by document status
            invoice_type: Filter by invoice type (ACCREC, ACCPAY)
            
        Returns:
            List of normalized invoice transactions
        """
        if not self._connected:
            await self.connect()
        
        try:
            self.logger.info(f"Retrieving invoices from Xero")
            
            # Extract invoices from Xero
            invoices = await self.data_extractor.extract_invoices(
                start_date=start_date,
                end_date=end_date,
                contact_ids=contact_ids,
                invoice_type=invoice_type
            )
            
            # Apply status filter if specified
            if status_filter:
                invoices = [inv for inv in invoices if inv.status in status_filter]
            
            self.logger.info(f"Retrieved {len(invoices)} invoices from Xero")
            return invoices
            
        except Exception as e:
            self.logger.error(f"Failed to retrieve invoices: {str(e)}")
            raise XeroDataError(f"Invoice retrieval failed: {str(e)}")
    
    async def get_invoice_by_id(self, invoice_id: str) -> Optional[AccountingTransaction]:
        """
        Get specific invoice by ID.
        
        Args:
            invoice_id: Xero invoice ID
            
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
        Retrieve customers from Xero.
        
        Args:
            active_only: Only return active customers
            modified_since: Only return customers modified since this date
            
        Returns:
            List of normalized customer contacts
        """
        if not self._connected:
            await self.connect()
        
        try:
            return await self.data_extractor.extract_contacts(
                active_only=active_only,
                modified_since=modified_since,
                contact_type="Customer"
            )
        except Exception as e:
            self.logger.error(f"Failed to retrieve customers: {str(e)}")
            raise XeroDataError(f"Customer retrieval failed: {str(e)}")
    
    async def get_suppliers(
        self,
        active_only: bool = True,
        modified_since: Optional[datetime] = None
    ) -> List[AccountingContact]:
        """
        Retrieve suppliers from Xero.
        
        Args:
            active_only: Only return active suppliers
            modified_since: Only return suppliers modified since this date
            
        Returns:
            List of normalized supplier contacts
        """
        if not self._connected:
            await self.connect()
        
        try:
            return await self.data_extractor.extract_contacts(
                active_only=active_only,
                modified_since=modified_since,
                contact_type="Supplier"
            )
        except Exception as e:
            self.logger.error(f"Failed to retrieve suppliers: {str(e)}")
            raise XeroDataError(f"Supplier retrieval failed: {str(e)}")
    
    async def get_chart_of_accounts(self) -> List[AccountingAccount]:
        """
        Retrieve chart of accounts from Xero.
        
        Returns:
            List of normalized account records
        """
        if not self._connected:
            await self.connect()
        
        try:
            return await self.data_extractor.extract_chart_of_accounts()
        except Exception as e:
            self.logger.error(f"Failed to retrieve chart of accounts: {str(e)}")
            raise XeroDataError(f"Chart of accounts retrieval failed: {str(e)}")
    
    async def get_credit_notes(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> List[AccountingTransaction]:
        """
        Retrieve credit notes from Xero.
        
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
            raise XeroDataError(f"Credit notes retrieval failed: {str(e)}")
    
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
            raise XeroDataError(f"UBL transformation failed: {str(e)}")
    
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
            suppliers_task = asyncio.create_task(
                self.get_suppliers(modified_since=since)
            )
            credit_notes_task = asyncio.create_task(
                self.get_credit_notes(start_date=since)
            )
            
            invoices, customers, suppliers, credit_notes = await asyncio.gather(
                invoices_task, customers_task, suppliers_task, credit_notes_task,
                return_exceptions=True
            )
            
            # Handle results
            invoice_count = len(invoices) if not isinstance(invoices, Exception) else 0
            customer_count = len(customers) if not isinstance(customers, Exception) else 0
            supplier_count = len(suppliers) if not isinstance(suppliers, Exception) else 0
            credit_note_count = len(credit_notes) if not isinstance(credit_notes, Exception) else 0
            
            self._last_sync = datetime.now()
            
            sync_result = {
                "status": "success",
                "sync_timestamp": self._last_sync.isoformat(),
                "since": since.isoformat(),
                "tenant_id": self.tenant_id,
                "changes": {
                    "invoices": invoice_count,
                    "customers": customer_count,
                    "suppliers": supplier_count,
                    "credit_notes": credit_note_count
                },
                "errors": []
            }
            
            # Add any errors
            if isinstance(invoices, Exception):
                sync_result["errors"].append(f"Invoice sync failed: {str(invoices)}")
            if isinstance(customers, Exception):
                sync_result["errors"].append(f"Customer sync failed: {str(customers)}")
            if isinstance(suppliers, Exception):
                sync_result["errors"].append(f"Supplier sync failed: {str(suppliers)}")
            if isinstance(credit_notes, Exception):
                sync_result["errors"].append(f"Credit notes sync failed: {str(credit_notes)}")
            
            self.logger.info(f"Incremental sync completed: {invoice_count} invoices, {customer_count} customers, "
                           f"{supplier_count} suppliers, {credit_note_count} credit notes")
            return sync_result
            
        except Exception as e:
            self.logger.error(f"Incremental sync failed: {str(e)}")
            raise XeroDataError(f"Incremental sync failed: {str(e)}")
    
    async def get_auth_url(self, state: str, scopes: Optional[List[str]] = None) -> str:
        """
        Get OAuth2 authorization URL for Xero.
        
        Args:
            state: OAuth2 state parameter
            scopes: Optional custom scopes
            
        Returns:
            Authorization URL
        """
        if not self.auth_manager:
            self.auth_manager = XeroAuthManager(
                client_id=self.client_id,
                client_secret=self.client_secret,
                redirect_uri=self.redirect_uri
            )
        
        return self.auth_manager.get_authorization_url(state, scopes)
    
    async def handle_oauth_callback(self, code: str, state: str) -> Dict[str, Any]:
        """
        Handle OAuth2 callback from Xero.
        
        Args:
            code: Authorization code
            state: OAuth2 state parameter
            
        Returns:
            Token and tenant information
        """
        if not self.auth_manager:
            raise XeroConnectionError("Auth manager not initialized")
        
        try:
            tokens_info = await self.auth_manager.exchange_code_for_tokens(code, state)
            
            # Update available tenants
            self._available_tenants = tokens_info.get('tenants', [])
            
            return {
                "status": "success",
                "tokens": {
                    "access_token": tokens_info["access_token"],
                    "refresh_token": tokens_info["refresh_token"],
                    "expires_at": tokens_info["expires_at"]
                },
                "tenants": self._available_tenants,
                "requires_tenant_selection": len(self._available_tenants) > 1
            }
            
        except Exception as e:
            self.logger.error(f"OAuth callback handling failed: {str(e)}")
            raise XeroAuthenticationError(f"OAuth callback failed: {str(e)}")
    
    def set_tenant(self, tenant_id: str) -> None:
        """
        Set active tenant/organization.
        
        Args:
            tenant_id: Xero tenant ID
            
        Raises:
            XeroOrganisationError: Invalid tenant ID
        """
        if self.auth_manager:
            self.auth_manager.set_tenant(tenant_id)
        
        self.tenant_id = tenant_id
        self.logger.info(f"Set active tenant: {tenant_id}")
    
    def get_available_tenants(self) -> List[Dict[str, Any]]:
        """
        Get list of available tenants/organizations.
        
        Returns:
            List of tenant information
        """
        if self.auth_manager:
            return self.auth_manager.list_available_tenants()
        return self._available_tenants
    
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
                "credit_notes": True,
                "customers": True,
                "suppliers": True,
                "chart_of_accounts": True,
                "ubl_transformation": True,
                "multi_tenant": True,
                "oauth2": True,
                "incremental_sync": True,
                "multi_currency": True,
                "real_time_sync": False  # Xero doesn't have webhooks for accounting data
            },
            "requirements": {
                "oauth2_setup": True,
                "tenant_selection": True,
                "pkce_support": True,
                "openid_connect": True
            },
            "rate_limits": {
                "calls_per_minute": 60,
                "calls_per_day": 5000,
                "burst_support": False
            },
            "api_version": "2.0",
            "authentication": {
                "type": "oauth2",
                "flows": ["authorization_code"],
                "scopes": [
                    "accounting.transactions",
                    "accounting.contacts", 
                    "accounting.settings",
                    "offline_access"
                ]
            }
        }
    
    async def create_invoice(self, invoice_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create new invoice in Xero.
        
        Args:
            invoice_data: Invoice data in Xero format
            
        Returns:
            Created invoice response
        """
        if not self._connected:
            await self.connect()
        
        try:
            async with self.rest_client:
                return await self.rest_client.create_invoice(invoice_data)
        except Exception as e:
            self.logger.error(f"Failed to create invoice: {str(e)}")
            raise XeroDataError(f"Invoice creation failed: {str(e)}")
    
    async def create_contact(self, contact_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create new contact in Xero.
        
        Args:
            contact_data: Contact data in Xero format
            
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
            raise XeroDataError(f"Contact creation failed: {str(e)}")
    
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
            self.tenant_id is not None
        )
    
    def get_connection_status(self) -> Dict[str, Any]:
        """Get detailed connection status."""
        return {
            "connected": self._connected,
            "authenticated": self.is_authenticated(),
            "tenant_id": self.tenant_id,
            "available_tenants_count": len(self._available_tenants),
            "last_sync": self._last_sync.isoformat() if self._last_sync else None,
            "auth_status": self.auth_manager.get_auth_status() if self.auth_manager else {},
            "rate_limits": self.rest_client.get_rate_limit_status() if self.rest_client else {},
            "organisation_name": self._organisation_info.get('Organisations', [{}])[0].get('Name') if self._organisation_info else None,
            "platform": self.PLATFORM_NAME
        }