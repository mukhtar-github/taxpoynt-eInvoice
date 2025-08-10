"""
FreshBooks Connector
Main connector implementation for FreshBooks integration.
"""
import asyncio
import logging
from typing import Dict, List, Optional, Any, Union
from datetime import datetime, timedelta

from .auth import FreshBooksAuthManager
from .rest_client import FreshBooksRestClient
from .data_extractor import FreshBooksDataExtractor
from .ubl_transformer import FreshBooksUBLTransformer
from .exceptions import (
    FreshBooksException,
    FreshBooksAuthenticationError,
    FreshBooksConfigurationError,
    FreshBooksConnectionError,
    FreshBooksDataError
)


logger = logging.getLogger(__name__)


class FreshBooksConnector:
    """
    Main connector for FreshBooks integration.
    
    Provides a unified interface for FreshBooks operations including
    authentication, data extraction, and UBL transformation for FIRS e-invoicing.
    """
    
    def __init__(
        self,
        client_id: str,
        client_secret: str,
        redirect_uri: str,
        sandbox: bool = True,
        session: Optional[object] = None
    ):
        """
        Initialize FreshBooks connector.
        
        Args:
            client_id: FreshBooks application client ID
            client_secret: FreshBooks application client secret
            redirect_uri: OAuth2 redirect URI
            sandbox: Whether to use sandbox environment
            session: Optional aiohttp session
        """
        self.sandbox = sandbox
        
        # Initialize components
        self.auth_manager = FreshBooksAuthManager(
            client_id=client_id,
            client_secret=client_secret,
            redirect_uri=redirect_uri,
            sandbox=sandbox,
            session=session
        )
        
        self.rest_client = FreshBooksRestClient(
            auth_manager=self.auth_manager,
            session=session
        )
        
        self.data_extractor = FreshBooksDataExtractor(self.rest_client)
        self.ubl_transformer = FreshBooksUBLTransformer()
        
        # Connection state
        self._is_connected = False
        self._current_account_id: Optional[str] = None
        self._connection_metadata: Dict[str, Any] = {}
    
    async def __aenter__(self):
        """Async context manager entry."""
        await self.auth_manager.__aenter__()
        await self.rest_client.__aenter__()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.rest_client.__aexit__(exc_type, exc_val, exc_tb)
        await self.auth_manager.__aexit__(exc_type, exc_val, exc_tb)
    
    # Authentication Methods
    
    def get_authorization_url(self, state: Optional[str] = None) -> tuple[str, str]:
        """
        Get OAuth2 authorization URL for user authentication.
        
        Args:
            state: Optional state parameter for CSRF protection
            
        Returns:
            Tuple of (authorization_url, state)
        """
        return self.auth_manager.get_authorization_url(state)
    
    async def authenticate_with_code(
        self,
        authorization_code: str,
        state: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Complete OAuth2 authentication with authorization code.
        
        Args:
            authorization_code: Authorization code from callback
            state: State parameter for validation
            
        Returns:
            Authentication result with token info
        """
        try:
            token_data = await self.auth_manager.exchange_code_for_tokens(
                authorization_code, state
            )
            
            # Verify authentication worked
            identity_info = await self.auth_manager.get_identity_info()
            
            # Set account ID if available
            self._current_account_id = self.auth_manager.get_account_id()
            
            self._is_connected = True
            self._connection_metadata = {
                "authenticated_at": datetime.utcnow().isoformat(),
                "identity_info": identity_info,
                "token_scope": token_data.get("scope"),
                "account_id": self._current_account_id,
                "sandbox": self.sandbox
            }
            
            logger.info("Successfully authenticated with FreshBooks")
            
            return {
                "success": True,
                "identity_info": identity_info,
                "token_info": self.auth_manager.get_token_info(),
                "connection_metadata": self._connection_metadata
            }
            
        except Exception as e:
            logger.error(f"Authentication failed: {e}")
            raise FreshBooksAuthenticationError(f"Authentication failed: {str(e)}")
    
    async def refresh_authentication(self) -> Dict[str, Any]:
        """
        Refresh authentication tokens.
        
        Returns:
            Refreshed token information
        """
        try:
            token_data = await self.auth_manager.refresh_access_token()
            
            self._connection_metadata["last_refresh"] = datetime.utcnow().isoformat()
            
            logger.info("Successfully refreshed authentication")
            
            return {
                "success": True,
                "token_info": self.auth_manager.get_token_info(),
                "refreshed_at": self._connection_metadata["last_refresh"]
            }
            
        except Exception as e:
            logger.error(f"Token refresh failed: {e}")
            raise FreshBooksAuthenticationError(f"Token refresh failed: {str(e)}")
    
    def is_authenticated(self) -> bool:
        """Check if currently authenticated."""
        return self._is_connected and self.auth_manager.is_authenticated()
    
    # Account Management
    
    async def get_account_info(self, account_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Get account information.
        
        Args:
            account_id: FreshBooks account ID (uses current if not provided)
            
        Returns:
            Account information
        """
        if not self.is_authenticated():
            raise FreshBooksAuthenticationError("Not authenticated")
        
        account_id = account_id or self._current_account_id
        if not account_id:
            raise FreshBooksConfigurationError("No account ID available")
        
        try:
            account_info = await self.data_extractor.extract_account_info(account_id)
            logger.info(f"Retrieved account info for: {account_info.get('name')}")
            return account_info
            
        except Exception as e:
            logger.error(f"Failed to get account info: {e}")
            raise FreshBooksDataError(f"Failed to retrieve account info: {str(e)}")
    
    async def select_account(self, account_id: str) -> Dict[str, Any]:
        """
        Select an account for operations.
        
        Args:
            account_id: FreshBooks account ID
            
        Returns:
            Account information
        """
        if not self.is_authenticated():
            raise FreshBooksAuthenticationError("Not authenticated")
        
        try:
            # Validate account access
            account_info = await self.data_extractor.extract_account_info(account_id)
            
            self._current_account_id = account_id
            self._connection_metadata["current_account"] = {
                "id": account_id,
                "name": account_info.get("name"),
                "selected_at": datetime.utcnow().isoformat()
            }
            
            logger.info(f"Selected account: {account_info.get('name')} ({account_id})")
            return account_info
            
        except Exception as e:
            logger.error(f"Failed to select account: {e}")
            raise FreshBooksDataError(f"Failed to select account: {str(e)}")
    
    def get_current_account_id(self) -> Optional[str]:
        """Get currently selected account ID."""
        return self._current_account_id
    
    # Data Extraction Methods
    
    async def get_clients(
        self,
        account_id: Optional[str] = None,
        updated_since: Optional[datetime] = None,
        limit: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        Get clients from FreshBooks.
        
        Args:
            account_id: FreshBooks account ID (uses current if not provided)
            updated_since: Only return clients updated since this date
            limit: Maximum number of clients to return
            
        Returns:
            List of client objects
        """
        account_id = account_id or self._current_account_id
        if not account_id:
            raise FreshBooksConfigurationError("No account selected")
        
        try:
            clients = await self.data_extractor.extract_clients(
                account_id=account_id,
                updated_since=updated_since,
                limit=limit
            )
            
            logger.info(f"Retrieved {len(clients)} clients")
            return clients
            
        except Exception as e:
            logger.error(f"Failed to get clients: {e}")
            raise FreshBooksDataError(f"Failed to retrieve clients: {str(e)}")
    
    async def get_items(
        self,
        account_id: Optional[str] = None,
        updated_since: Optional[datetime] = None,
        limit: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        Get items from FreshBooks.
        
        Args:
            account_id: FreshBooks account ID (uses current if not provided)
            updated_since: Only return items updated since this date
            limit: Maximum number of items to return
            
        Returns:
            List of item objects
        """
        account_id = account_id or self._current_account_id
        if not account_id:
            raise FreshBooksConfigurationError("No account selected")
        
        try:
            items = await self.data_extractor.extract_items(
                account_id=account_id,
                updated_since=updated_since,
                limit=limit
            )
            
            logger.info(f"Retrieved {len(items)} items")
            return items
            
        except Exception as e:
            logger.error(f"Failed to get items: {e}")
            raise FreshBooksDataError(f"Failed to retrieve items: {str(e)}")
    
    async def get_invoices(
        self,
        account_id: Optional[str] = None,
        updated_since: Optional[datetime] = None,
        status_filter: Optional[str] = None,
        limit: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        Get invoices from FreshBooks.
        
        Args:
            account_id: FreshBooks account ID (uses current if not provided)
            updated_since: Only return invoices updated since this date
            status_filter: Filter by invoice status
            limit: Maximum number of invoices to return
            
        Returns:
            List of invoice objects
        """
        account_id = account_id or self._current_account_id
        if not account_id:
            raise FreshBooksConfigurationError("No account selected")
        
        try:
            invoices = await self.data_extractor.extract_invoices(
                account_id=account_id,
                updated_since=updated_since,
                status_filter=status_filter,
                limit=limit
            )
            
            logger.info(f"Retrieved {len(invoices)} invoices")
            return invoices
            
        except Exception as e:
            logger.error(f"Failed to get invoices: {e}")
            raise FreshBooksDataError(f"Failed to retrieve invoices: {str(e)}")
    
    async def get_invoice_by_id(
        self,
        invoice_id: str,
        account_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Get a specific invoice by ID.
        
        Args:
            invoice_id: FreshBooks invoice ID
            account_id: FreshBooks account ID (uses current if not provided)
            
        Returns:
            Invoice object
        """
        account_id = account_id or self._current_account_id
        if not account_id:
            raise FreshBooksConfigurationError("No account selected")
        
        try:
            invoice = await self.data_extractor.extract_invoice_by_id(invoice_id, account_id)
            logger.info(f"Retrieved invoice: {invoice.get('invoice_number')}")
            return invoice
            
        except Exception as e:
            logger.error(f"Failed to get invoice {invoice_id}: {e}")
            raise FreshBooksDataError(f"Failed to retrieve invoice: {str(e)}")
    
    # UBL Transformation Methods
    
    async def convert_invoice_to_ubl(
        self,
        invoice_id: str,
        account_id: Optional[str] = None,
        include_client_details: bool = True
    ) -> Dict[str, Any]:
        """
        Convert FreshBooks invoice to UBL 2.1 format.
        
        Args:
            invoice_id: FreshBooks invoice ID
            account_id: FreshBooks account ID (uses current if not provided)
            include_client_details: Whether to fetch detailed client info
            
        Returns:
            UBL 2.1 compliant invoice
        """
        account_id = account_id or self._current_account_id
        if not account_id:
            raise FreshBooksConfigurationError("No account selected")
        
        try:
            # Get invoice data
            invoice_data = await self.get_invoice_by_id(invoice_id, account_id)
            
            # Get account data
            account_data = await self.data_extractor.extract_account_info(account_id)
            
            # Get detailed client data if requested
            client_data = None
            if include_client_details:
                client_id = invoice_data["client"]["id"]
                if client_id:
                    clients = await self.get_clients(account_id, limit=100)
                    client_data = next(
                        (c for c in clients if c["id"] == client_id), 
                        None
                    )
            
            # Transform to UBL
            ubl_invoice = self.ubl_transformer.transform_invoice_to_ubl(
                invoice_data=invoice_data,
                account_data=account_data,
                client_data=client_data
            )
            
            logger.info(f"Converted invoice {invoice_data.get('invoice_number')} to UBL")
            return ubl_invoice
            
        except Exception as e:
            logger.error(f"Failed to convert invoice to UBL: {e}")
            raise FreshBooksDataError(f"UBL conversion failed: {str(e)}")
    
    async def batch_convert_invoices_to_ubl(
        self,
        invoice_ids: List[str],
        account_id: Optional[str] = None,
        include_client_details: bool = True
    ) -> List[Dict[str, Any]]:
        """
        Convert multiple FreshBooks invoices to UBL format.
        
        Args:
            invoice_ids: List of FreshBooks invoice IDs
            account_id: FreshBooks account ID (uses current if not provided)
            include_client_details: Whether to fetch detailed client info
            
        Returns:
            List of UBL 2.1 compliant invoices
        """
        account_id = account_id or self._current_account_id
        if not account_id:
            raise FreshBooksConfigurationError("No account selected")
        
        results = []
        errors = []
        
        # Process invoices concurrently (with limit to avoid rate limiting)
        semaphore = asyncio.Semaphore(5)  # Limit concurrent requests
        
        async def convert_single_invoice(invoice_id: str) -> Optional[Dict[str, Any]]:
            async with semaphore:
                try:
                    return await self.convert_invoice_to_ubl(
                        invoice_id=invoice_id,
                        account_id=account_id,
                        include_client_details=include_client_details
                    )
                except Exception as e:
                    logger.error(f"Failed to convert invoice {invoice_id}: {e}")
                    errors.append({"invoice_id": invoice_id, "error": str(e)})
                    return None
        
        # Execute conversions
        tasks = [convert_single_invoice(invoice_id) for invoice_id in invoice_ids]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Filter successful results
        successful_results = [r for r in results if r is not None and not isinstance(r, Exception)]
        
        logger.info(f"Converted {len(successful_results)}/{len(invoice_ids)} invoices to UBL")
        
        if errors:
            logger.warning(f"Failed to convert {len(errors)} invoices: {errors}")
        
        return successful_results
    
    # Utility Methods
    
    async def test_connection(self) -> Dict[str, Any]:
        """
        Test the connection to FreshBooks API.
        
        Returns:
            Connection test results
        """
        try:
            if not self.is_authenticated():
                return {
                    "success": False,
                    "error": "Not authenticated",
                    "details": "OAuth2 authentication required"
                }
            
            # Test API access
            identity_info = await self.auth_manager.get_identity_info()
            account_id = self._current_account_id or self.auth_manager.get_account_id()
            
            if account_id:
                account_info = await self.data_extractor.extract_account_info(account_id)
            else:
                account_info = None
            
            return {
                "success": True,
                "authenticated": True,
                "identity_info": identity_info,
                "account_info": account_info,
                "connection_metadata": self._connection_metadata,
                "api_status": "operational"
            }
            
        except Exception as e:
            logger.error(f"Connection test failed: {e}")
            return {
                "success": False,
                "error": str(e),
                "authenticated": self.is_authenticated(),
                "details": "Failed to communicate with FreshBooks API"
            }
    
    async def get_sync_status(self, account_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Get synchronization status for an account.
        
        Args:
            account_id: FreshBooks account ID (uses current if not provided)
            
        Returns:
            Sync status information
        """
        account_id = account_id or self._current_account_id
        if not account_id:
            raise FreshBooksConfigurationError("No account selected")
        
        try:
            # Get counts of various entities
            recent_date = datetime.utcnow() - timedelta(days=30)
            
            clients = await self.get_clients(account_id, limit=1)
            items = await self.get_items(account_id, limit=1)
            invoices = await self.get_invoices(account_id, limit=1)
            recent_invoices = await self.get_invoices(
                account_id, updated_since=recent_date, limit=100
            )
            
            return {
                "account_id": account_id,
                "sync_timestamp": datetime.utcnow().isoformat(),
                "entities": {
                    "clients_available": len(clients) > 0,
                    "items_available": len(items) > 0,
                    "invoices_available": len(invoices) > 0,
                    "recent_invoices_count": len(recent_invoices)
                },
                "last_sync": self._connection_metadata.get("last_sync"),
                "status": "ready"
            }
            
        except Exception as e:
            logger.error(f"Failed to get sync status: {e}")
            return {
                "account_id": account_id,
                "sync_timestamp": datetime.utcnow().isoformat(),
                "status": "error",
                "error": str(e)
            }
    
    def get_connection_info(self) -> Dict[str, Any]:
        """Get current connection information."""
        return {
            "is_connected": self._is_connected,
            "is_authenticated": self.is_authenticated(),
            "current_account_id": self._current_account_id,
            "sandbox": self.sandbox,
            "connection_metadata": self._connection_metadata,
            "token_info": self.auth_manager.get_token_info() if self.is_authenticated() else None
        }
    
    async def disconnect(self) -> bool:
        """
        Disconnect from FreshBooks API.
        
        Returns:
            True if disconnection successful
        """
        try:
            await self.auth_manager.revoke_token()
            
            self._is_connected = False
            self._current_account_id = None
            self._connection_metadata = {}
            
            logger.info("Successfully disconnected from FreshBooks")
            return True
            
        except Exception as e:
            logger.error(f"Disconnection failed: {e}")
            return False
    
    # Invoice Management Methods
    
    async def create_client(
        self,
        client_data: Dict[str, Any],
        account_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Create a new client in FreshBooks.
        
        Args:
            client_data: Client data
            account_id: FreshBooks account ID (uses current if not provided)
            
        Returns:
            Created client object
        """
        account_id = account_id or self._current_account_id
        if not account_id:
            raise FreshBooksConfigurationError("No account selected")
        
        try:
            response = await self.rest_client.create_client(client_data, account_id)
            logger.info(f"Created client: {client_data.get('organization') or client_data.get('fname')}")
            return response
            
        except Exception as e:
            logger.error(f"Failed to create client: {e}")
            raise FreshBooksDataError(f"Failed to create client: {str(e)}")
    
    async def create_invoice(
        self,
        invoice_data: Dict[str, Any],
        account_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Create a new invoice in FreshBooks.
        
        Args:
            invoice_data: Invoice data
            account_id: FreshBooks account ID (uses current if not provided)
            
        Returns:
            Created invoice object
        """
        account_id = account_id or self._current_account_id
        if not account_id:
            raise FreshBooksConfigurationError("No account selected")
        
        try:
            response = await self.rest_client.create_invoice(invoice_data, account_id)
            logger.info(f"Created invoice: {invoice_data.get('invoice_number')}")
            return response
            
        except Exception as e:
            logger.error(f"Failed to create invoice: {e}")
            raise FreshBooksDataError(f"Failed to create invoice: {str(e)}")
    
    async def send_invoice(
        self,
        invoice_id: str,
        account_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Send an invoice via FreshBooks.
        
        Args:
            invoice_id: FreshBooks invoice ID
            account_id: FreshBooks account ID (uses current if not provided)
            
        Returns:
            Send result
        """
        account_id = account_id or self._current_account_id
        if not account_id:
            raise FreshBooksConfigurationError("No account selected")
        
        try:
            response = await self.rest_client.send_invoice(invoice_id, account_id)
            logger.info(f"Sent invoice: {invoice_id}")
            return response
            
        except Exception as e:
            logger.error(f"Failed to send invoice: {e}")
            raise FreshBooksDataError(f"Failed to send invoice: {str(e)}")