"""
Wave Accounting Connector
Main connector implementation for Wave Accounting integration.
"""
import asyncio
import logging
from typing import Dict, List, Optional, Any, Union
from datetime import datetime, timedelta

from .auth import WaveAuthManager
from .rest_client import WaveRestClient
from .data_extractor import WaveDataExtractor
from .ubl_transformer import WaveUBLTransformer
from .exceptions import (
    WaveException,
    WaveAuthenticationError,
    WaveConfigurationError,
    WaveConnectionError,
    WaveDataError
)


logger = logging.getLogger(__name__)


class WaveConnector:
    """
    Main connector for Wave Accounting integration.
    
    Provides a unified interface for Wave Accounting operations including
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
        Initialize Wave connector.
        
        Args:
            client_id: Wave application client ID
            client_secret: Wave application client secret
            redirect_uri: OAuth2 redirect URI
            sandbox: Whether to use sandbox environment
            session: Optional aiohttp session
        """
        self.sandbox = sandbox
        
        # Initialize components
        self.auth_manager = WaveAuthManager(
            client_id=client_id,
            client_secret=client_secret,
            redirect_uri=redirect_uri,
            sandbox=sandbox,
            session=session
        )
        
        self.rest_client = WaveRestClient(
            auth_manager=self.auth_manager,
            session=session
        )
        
        self.data_extractor = WaveDataExtractor(self.rest_client)
        self.ubl_transformer = WaveUBLTransformer()
        
        # Connection state
        self._is_connected = False
        self._current_business_id: Optional[str] = None
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
    
    def get_authorization_url(self, state: Optional[str] = None) -> tuple[str, str, str]:
        """
        Get OAuth2 authorization URL for user authentication.
        
        Args:
            state: Optional state parameter for CSRF protection
            
        Returns:
            Tuple of (authorization_url, code_verifier, state)
        """
        return self.auth_manager.get_authorization_url(state)
    
    async def authenticate_with_code(
        self,
        authorization_code: str,
        code_verifier: str,
        state: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Complete OAuth2 authentication with authorization code.
        
        Args:
            authorization_code: Authorization code from callback
            code_verifier: PKCE code verifier
            state: State parameter for validation
            
        Returns:
            Authentication result with token info
        """
        try:
            token_data = await self.auth_manager.exchange_code_for_tokens(
                authorization_code, code_verifier, state
            )
            
            # Verify authentication worked
            user_info = await self.auth_manager.get_user_info()
            
            self._is_connected = True
            self._connection_metadata = {
                "authenticated_at": datetime.utcnow().isoformat(),
                "user_info": user_info,
                "token_scope": token_data.get("scope"),
                "sandbox": self.sandbox
            }
            
            logger.info("Successfully authenticated with Wave")
            
            return {
                "success": True,
                "user_info": user_info,
                "token_info": self.auth_manager.get_token_info(),
                "connection_metadata": self._connection_metadata
            }
            
        except Exception as e:
            logger.error(f"Authentication failed: {e}")
            raise WaveAuthenticationError(f"Authentication failed: {str(e)}")
    
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
            raise WaveAuthenticationError(f"Token refresh failed: {str(e)}")
    
    def is_authenticated(self) -> bool:
        """Check if currently authenticated."""
        return self._is_connected and self.auth_manager.is_authenticated()
    
    # Business Management
    
    async def list_businesses(self) -> List[Dict[str, Any]]:
        """
        List all businesses accessible to the authenticated user.
        
        Returns:
            List of business objects
        """
        if not self.is_authenticated():
            raise WaveAuthenticationError("Not authenticated")
        
        try:
            businesses = await self.data_extractor.extract_business_info("")
            # Since Wave uses GraphQL, we need to get businesses differently
            businesses = await self.rest_client.get_businesses()
            
            normalized_businesses = []
            for business in businesses:
                normalized_business = await self.data_extractor.extract_business_info(business["id"])
                normalized_businesses.append(normalized_business)
            
            logger.info(f"Retrieved {len(normalized_businesses)} businesses")
            return normalized_businesses
            
        except Exception as e:
            logger.error(f"Failed to list businesses: {e}")
            raise WaveDataError(f"Failed to retrieve businesses: {str(e)}")
    
    async def select_business(self, business_id: str) -> Dict[str, Any]:
        """
        Select a business for operations.
        
        Args:
            business_id: Wave business ID
            
        Returns:
            Business information
        """
        if not self.is_authenticated():
            raise WaveAuthenticationError("Not authenticated")
        
        try:
            # Validate business access
            business_info = await self.data_extractor.extract_business_info(business_id)
            
            self._current_business_id = business_id
            self._connection_metadata["current_business"] = {
                "id": business_id,
                "name": business_info.get("name"),
                "selected_at": datetime.utcnow().isoformat()
            }
            
            logger.info(f"Selected business: {business_info.get('name')} ({business_id})")
            return business_info
            
        except Exception as e:
            logger.error(f"Failed to select business: {e}")
            raise WaveDataError(f"Failed to select business: {str(e)}")
    
    def get_current_business_id(self) -> Optional[str]:
        """Get currently selected business ID."""
        return self._current_business_id
    
    # Data Extraction Methods
    
    async def get_customers(
        self,
        business_id: Optional[str] = None,
        modified_since: Optional[datetime] = None,
        limit: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        Get customers from Wave.
        
        Args:
            business_id: Wave business ID (uses current if not provided)
            modified_since: Only return customers modified since this date
            limit: Maximum number of customers to return
            
        Returns:
            List of customer objects
        """
        business_id = business_id or self._current_business_id
        if not business_id:
            raise WaveConfigurationError("No business selected")
        
        try:
            customers = await self.data_extractor.extract_customers(
                business_id=business_id,
                modified_since=modified_since,
                limit=limit
            )
            
            logger.info(f"Retrieved {len(customers)} customers")
            return customers
            
        except Exception as e:
            logger.error(f"Failed to get customers: {e}")
            raise WaveDataError(f"Failed to retrieve customers: {str(e)}")
    
    async def get_products(
        self,
        business_id: Optional[str] = None,
        modified_since: Optional[datetime] = None,
        limit: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        Get products from Wave.
        
        Args:
            business_id: Wave business ID (uses current if not provided)
            modified_since: Only return products modified since this date
            limit: Maximum number of products to return
            
        Returns:
            List of product objects
        """
        business_id = business_id or self._current_business_id
        if not business_id:
            raise WaveConfigurationError("No business selected")
        
        try:
            products = await self.data_extractor.extract_products(
                business_id=business_id,
                modified_since=modified_since,
                limit=limit
            )
            
            logger.info(f"Retrieved {len(products)} products")
            return products
            
        except Exception as e:
            logger.error(f"Failed to get products: {e}")
            raise WaveDataError(f"Failed to retrieve products: {str(e)}")
    
    async def get_invoices(
        self,
        business_id: Optional[str] = None,
        modified_since: Optional[datetime] = None,
        status_filter: Optional[str] = None,
        limit: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        Get invoices from Wave.
        
        Args:
            business_id: Wave business ID (uses current if not provided)
            modified_since: Only return invoices modified since this date
            status_filter: Filter by invoice status
            limit: Maximum number of invoices to return
            
        Returns:
            List of invoice objects
        """
        business_id = business_id or self._current_business_id
        if not business_id:
            raise WaveConfigurationError("No business selected")
        
        try:
            invoices = await self.data_extractor.extract_invoices(
                business_id=business_id,
                modified_since=modified_since,
                status_filter=status_filter,
                limit=limit
            )
            
            logger.info(f"Retrieved {len(invoices)} invoices")
            return invoices
            
        except Exception as e:
            logger.error(f"Failed to get invoices: {e}")
            raise WaveDataError(f"Failed to retrieve invoices: {str(e)}")
    
    async def get_invoice_by_id(
        self,
        invoice_id: str,
        business_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Get a specific invoice by ID.
        
        Args:
            invoice_id: Wave invoice ID
            business_id: Wave business ID (uses current if not provided)
            
        Returns:
            Invoice object
        """
        business_id = business_id or self._current_business_id
        if not business_id:
            raise WaveConfigurationError("No business selected")
        
        try:
            invoice = await self.data_extractor.extract_invoice_by_id(business_id, invoice_id)
            logger.info(f"Retrieved invoice: {invoice.get('invoice_number')}")
            return invoice
            
        except Exception as e:
            logger.error(f"Failed to get invoice {invoice_id}: {e}")
            raise WaveDataError(f"Failed to retrieve invoice: {str(e)}")
    
    # UBL Transformation Methods
    
    async def convert_invoice_to_ubl(
        self,
        invoice_id: str,
        business_id: Optional[str] = None,
        include_customer_details: bool = True
    ) -> Dict[str, Any]:
        """
        Convert Wave invoice to UBL 2.1 format.
        
        Args:
            invoice_id: Wave invoice ID
            business_id: Wave business ID (uses current if not provided)
            include_customer_details: Whether to fetch detailed customer info
            
        Returns:
            UBL 2.1 compliant invoice
        """
        business_id = business_id or self._current_business_id
        if not business_id:
            raise WaveConfigurationError("No business selected")
        
        try:
            # Get invoice data
            invoice_data = await self.get_invoice_by_id(invoice_id, business_id)
            
            # Get business data
            business_data = await self.data_extractor.extract_business_info(business_id)
            
            # Get detailed customer data if requested
            customer_data = None
            if include_customer_details:
                customer_id = invoice_data["customer"]["id"]
                if customer_id:
                    customers = await self.get_customers(business_id, limit=100)
                    customer_data = next(
                        (c for c in customers if c["id"] == customer_id), 
                        None
                    )
            
            # Transform to UBL
            ubl_invoice = self.ubl_transformer.transform_invoice_to_ubl(
                invoice_data=invoice_data,
                business_data=business_data,
                customer_data=customer_data
            )
            
            logger.info(f"Converted invoice {invoice_data.get('invoice_number')} to UBL")
            return ubl_invoice
            
        except Exception as e:
            logger.error(f"Failed to convert invoice to UBL: {e}")
            raise WaveDataError(f"UBL conversion failed: {str(e)}")
    
    async def batch_convert_invoices_to_ubl(
        self,
        invoice_ids: List[str],
        business_id: Optional[str] = None,
        include_customer_details: bool = True
    ) -> List[Dict[str, Any]]:
        """
        Convert multiple Wave invoices to UBL format.
        
        Args:
            invoice_ids: List of Wave invoice IDs
            business_id: Wave business ID (uses current if not provided)
            include_customer_details: Whether to fetch detailed customer info
            
        Returns:
            List of UBL 2.1 compliant invoices
        """
        business_id = business_id or self._current_business_id
        if not business_id:
            raise WaveConfigurationError("No business selected")
        
        results = []
        errors = []
        
        # Process invoices concurrently (with limit to avoid rate limiting)
        semaphore = asyncio.Semaphore(5)  # Limit concurrent requests
        
        async def convert_single_invoice(invoice_id: str) -> Optional[Dict[str, Any]]:
            async with semaphore:
                try:
                    return await self.convert_invoice_to_ubl(
                        invoice_id=invoice_id,
                        business_id=business_id,
                        include_customer_details=include_customer_details
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
        Test the connection to Wave API.
        
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
            user_info = await self.auth_manager.get_user_info()
            businesses = await self.rest_client.get_businesses()
            
            return {
                "success": True,
                "authenticated": True,
                "user_info": user_info,
                "businesses_count": len(businesses),
                "connection_metadata": self._connection_metadata,
                "api_status": "operational"
            }
            
        except Exception as e:
            logger.error(f"Connection test failed: {e}")
            return {
                "success": False,
                "error": str(e),
                "authenticated": self.is_authenticated(),
                "details": "Failed to communicate with Wave API"
            }
    
    async def get_sync_status(self, business_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Get synchronization status for a business.
        
        Args:
            business_id: Wave business ID (uses current if not provided)
            
        Returns:
            Sync status information
        """
        business_id = business_id or self._current_business_id
        if not business_id:
            raise WaveConfigurationError("No business selected")
        
        try:
            # Get counts of various entities
            recent_date = datetime.utcnow() - timedelta(days=30)
            
            customers = await self.get_customers(business_id, limit=1)
            products = await self.get_products(business_id, limit=1)
            invoices = await self.get_invoices(business_id, limit=1)
            recent_invoices = await self.get_invoices(
                business_id, modified_since=recent_date, limit=100
            )
            
            return {
                "business_id": business_id,
                "sync_timestamp": datetime.utcnow().isoformat(),
                "entities": {
                    "customers_available": len(customers) > 0,
                    "products_available": len(products) > 0,
                    "invoices_available": len(invoices) > 0,
                    "recent_invoices_count": len(recent_invoices)
                },
                "last_sync": self._connection_metadata.get("last_sync"),
                "status": "ready"
            }
            
        except Exception as e:
            logger.error(f"Failed to get sync status: {e}")
            return {
                "business_id": business_id,
                "sync_timestamp": datetime.utcnow().isoformat(),
                "status": "error",
                "error": str(e)
            }
    
    def get_connection_info(self) -> Dict[str, Any]:
        """Get current connection information."""
        return {
            "is_connected": self._is_connected,
            "is_authenticated": self.is_authenticated(),
            "current_business_id": self._current_business_id,
            "sandbox": self.sandbox,
            "connection_metadata": self._connection_metadata,
            "token_info": self.auth_manager.get_token_info() if self.is_authenticated() else None
        }
    
    async def disconnect(self) -> bool:
        """
        Disconnect from Wave API.
        
        Returns:
            True if disconnection successful
        """
        try:
            await self.auth_manager.revoke_token()
            
            self._is_connected = False
            self._current_business_id = None
            self._connection_metadata = {}
            
            logger.info("Successfully disconnected from Wave")
            return True
            
        except Exception as e:
            logger.error(f"Disconnection failed: {e}")
            return False