"""
Unleashed REST API Client
Handles all HTTP communication with Unleashed inventory management API.
"""
import asyncio
import logging
from typing import Dict, List, Optional, Any, Union
from datetime import datetime, timedelta
import json
from urllib.parse import urlencode

import aiohttp
from aiohttp import ClientSession, ClientTimeout, ClientError

from .auth import UnleashedAuthManager
from .exceptions import (
    UnleashedAPIError,
    UnleashedConnectionError,
    UnleashedRateLimitError,
    UnleashedAuthenticationError,
    UnleashedMaintenanceError,
    UnleashedProductNotFoundError,
    UnleashedWarehouseNotFoundError
)


logger = logging.getLogger(__name__)


class UnleashedRestClient:
    """
    REST client for Unleashed inventory management API.
    
    Handles HTTP communication, signature generation, rate limiting, 
    and error handling for all Unleashed API operations.
    """
    
    # Rate limiting settings (Unleashed allows 1000 requests per hour)
    MAX_REQUESTS_PER_HOUR = 1000
    MAX_RETRIES = 3
    RETRY_DELAY = 1.0
    
    def __init__(
        self,
        auth_manager: UnleashedAuthManager,
        session: Optional[ClientSession] = None,
        max_retries: int = MAX_RETRIES
    ):
        """
        Initialize Unleashed REST client.
        
        Args:
            auth_manager: Unleashed authentication manager
            session: Optional aiohttp session
            max_retries: Maximum number of retry attempts
        """
        self.auth_manager = auth_manager
        self.session = session
        self.should_close_session = session is None
        self.max_retries = max_retries
        
        # Rate limiting
        self._request_times: List[datetime] = []
        self._rate_limit_lock = asyncio.Lock()
    
    async def __aenter__(self):
        """Async context manager entry."""
        if self.session is None:
            timeout = ClientTimeout(total=60, connect=10)
            connector = aiohttp.TCPConnector(limit=10, limit_per_host=5)
            self.session = ClientSession(
                timeout=timeout,
                connector=connector,
                headers={"User-Agent": "TaxPoynt-Unleashed-Integration/1.0"}
            )
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        if self.should_close_session and self.session:
            await self.session.close()
    
    async def _rate_limit_check(self):
        """Check and enforce rate limiting."""
        async with self._rate_limit_lock:
            now = datetime.utcnow()
            # Remove requests older than 1 hour
            cutoff = now - timedelta(hours=1)
            self._request_times = [t for t in self._request_times if t > cutoff]
            
            # Check if we're at rate limit
            if len(self._request_times) >= self.MAX_REQUESTS_PER_HOUR:
                sleep_time = 3600 - (now - self._request_times[0]).total_seconds()
                logger.warning(f"Rate limit reached, sleeping for {sleep_time:.2f} seconds")
                await asyncio.sleep(sleep_time)
                # Clean up old requests again after sleeping
                now = datetime.utcnow()
                cutoff = now - timedelta(hours=1)
                self._request_times = [t for t in self._request_times if t > cutoff]
            
            # Record this request
            self._request_times.append(now)
    
    async def _make_request(
        self,
        method: str,
        endpoint: str,
        params: Optional[Dict[str, Any]] = None,
        data: Optional[Dict[str, Any]] = None,
        json_data: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Make a request to Unleashed API.
        
        Args:
            method: HTTP method (GET, POST, PUT, DELETE)
            endpoint: API endpoint path
            params: Query parameters
            data: Form data
            json_data: JSON data
            
        Returns:
            Response data
        """
        if not self.session:
            raise UnleashedConnectionError("No HTTP session available")
        
        await self._rate_limit_check()
        
        # Build URL and query string
        url = f"{self.auth_manager.base_url}/{endpoint.lstrip('/')}"
        query_string = ""
        
        if params:
            query_string = urlencode(params)
            url = f"{url}?{query_string}"
        
        # Get authentication headers (includes signature)
        headers = self.auth_manager.get_auth_headers(query_string)
        
        for attempt in range(self.max_retries + 1):
            try:
                kwargs = {
                    "headers": headers
                }
                
                if json_data:
                    kwargs["json"] = json_data
                elif data:
                    kwargs["data"] = data
                
                async with self.session.request(method, url, **kwargs) as response:
                    response_text = await response.text()
                    
                    # Handle HTTP errors
                    if response.status == 401:
                        raise UnleashedAuthenticationError("Authentication failed")
                    elif response.status == 429:
                        retry_after = int(response.headers.get("Retry-After", 3600))
                        raise UnleashedRateLimitError(
                            "Rate limit exceeded", 
                            retry_after=retry_after
                        )
                    elif response.status == 503:
                        raise UnleashedMaintenanceError("Unleashed API is under maintenance")
                    elif response.status >= 400:
                        # Try to parse error response
                        try:
                            error_data = json.loads(response_text)
                            error_msg = error_data.get("message", response_text)
                        except json.JSONDecodeError:
                            error_msg = response_text
                        
                        raise UnleashedAPIError(
                            f"HTTP {response.status}: {error_msg}",
                            status_code=response.status,
                            response_data={"raw_response": response_text}
                        )
                    
                    # Parse JSON response
                    try:
                        if response_text:
                            return json.loads(response_text)
                        else:
                            return {}
                    except json.JSONDecodeError:
                        return {"raw_response": response_text}
                    
            except UnleashedRateLimitError as e:
                if attempt < self.max_retries:
                    sleep_time = e.retry_after or (2 ** attempt)
                    logger.warning(f"Rate limited, retrying in {sleep_time} seconds")
                    await asyncio.sleep(sleep_time)
                    continue
                raise
            except (ClientError, asyncio.TimeoutError) as e:
                if attempt < self.max_retries:
                    sleep_time = self.RETRY_DELAY * (2 ** attempt)
                    logger.warning(f"Request failed, retrying in {sleep_time} seconds: {e}")
                    await asyncio.sleep(sleep_time)
                    continue
                raise UnleashedConnectionError(f"Failed to connect to Unleashed API: {str(e)}")
        
        raise UnleashedConnectionError("Max retries exceeded")
    
    # Product Operations
    
    async def get_products(
        self,
        page: int = 1,
        page_size: int = 200,
        product_code: Optional[str] = None,
        product_description: Optional[str] = None,
        modified_since: Optional[str] = None
    ) -> Dict[str, Any]:
        """Get products from Unleashed."""
        params = {
            "page": page,
            "pageSize": min(page_size, 200),  # Unleashed max is 200
        }
        
        if product_code:
            params["productCode"] = product_code
        if product_description:
            params["productDescription"] = product_description
        if modified_since:
            params["modifiedSince"] = modified_since
        
        return await self._make_request("GET", "Products", params=params)
    
    async def get_product(self, product_guid: str) -> Dict[str, Any]:
        """Get a specific product by GUID."""
        response = await self._make_request("GET", f"Products/{product_guid}")
        
        if not response:
            raise UnleashedProductNotFoundError(f"Product {product_guid} not found")
        
        return response
    
    async def create_product(self, product_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new product."""
        return await self._make_request("POST", "Products", json_data=product_data)
    
    async def update_product(self, product_guid: str, product_data: Dict[str, Any]) -> Dict[str, Any]:
        """Update an existing product."""
        return await self._make_request("PUT", f"Products/{product_guid}", json_data=product_data)
    
    # Stock On Hand Operations
    
    async def get_stock_on_hand(
        self,
        page: int = 1,
        page_size: int = 200,
        product_code: Optional[str] = None,
        warehouse_code: Optional[str] = None,
        modified_since: Optional[str] = None
    ) -> Dict[str, Any]:
        """Get stock on hand from Unleashed."""
        params = {
            "page": page,
            "pageSize": min(page_size, 200)
        }
        
        if product_code:
            params["productCode"] = product_code
        if warehouse_code:
            params["warehouseCode"] = warehouse_code
        if modified_since:
            params["modifiedSince"] = modified_since
        
        return await self._make_request("GET", "StockOnHand", params=params)
    
    async def get_stock_on_hand_by_guid(self, stock_guid: str) -> Dict[str, Any]:
        """Get specific stock on hand record by GUID."""
        response = await self._make_request("GET", f"StockOnHand/{stock_guid}")
        
        if not response:
            raise UnleashedStockOnHandNotFoundError(f"Stock on hand {stock_guid} not found")
        
        return response
    
    # Stock Movement Operations
    
    async def get_stock_movements(
        self,
        page: int = 1,
        page_size: int = 200,
        product_code: Optional[str] = None,
        warehouse_code: Optional[str] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None
    ) -> Dict[str, Any]:
        """Get stock movements from Unleashed."""
        params = {
            "page": page,
            "pageSize": min(page_size, 200)
        }
        
        if product_code:
            params["productCode"] = product_code
        if warehouse_code:
            params["warehouseCode"] = warehouse_code
        if start_date:
            params["startDate"] = start_date
        if end_date:
            params["endDate"] = end_date
        
        return await self._make_request("GET", "StockMovements", params=params)
    
    async def create_stock_adjustment(self, adjustment_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a stock adjustment."""
        return await self._make_request("POST", "StockAdjustments", json_data=adjustment_data)
    
    # Purchase Order Operations
    
    async def get_purchase_orders(
        self,
        page: int = 1,
        page_size: int = 200,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        modified_since: Optional[str] = None,
        order_status: Optional[str] = None
    ) -> Dict[str, Any]:
        """Get purchase orders from Unleashed."""
        params = {
            "page": page,
            "pageSize": min(page_size, 200)
        }
        
        if start_date:
            params["startDate"] = start_date
        if end_date:
            params["endDate"] = end_date
        if modified_since:
            params["modifiedSince"] = modified_since
        if order_status:
            params["orderStatus"] = order_status
        
        return await self._make_request("GET", "PurchaseOrders", params=params)
    
    async def get_purchase_order(self, order_guid: str) -> Dict[str, Any]:
        """Get a specific purchase order by GUID."""
        response = await self._make_request("GET", f"PurchaseOrders/{order_guid}")
        
        if not response:
            raise UnleashedPurchaseOrderNotFoundError(f"Purchase order {order_guid} not found")
        
        return response
    
    async def create_purchase_order(self, order_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new purchase order."""
        return await self._make_request("POST", "PurchaseOrders", json_data=order_data)
    
    # Sales Order Operations
    
    async def get_sales_orders(
        self,
        page: int = 1,
        page_size: int = 200,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        modified_since: Optional[str] = None,
        order_status: Optional[str] = None
    ) -> Dict[str, Any]:
        """Get sales orders from Unleashed."""
        params = {
            "page": page,
            "pageSize": min(page_size, 200)
        }
        
        if start_date:
            params["startDate"] = start_date
        if end_date:
            params["endDate"] = end_date
        if modified_since:
            params["modifiedSince"] = modified_since
        if order_status:
            params["orderStatus"] = order_status
        
        return await self._make_request("GET", "SalesOrders", params=params)
    
    async def get_sales_order(self, order_guid: str) -> Dict[str, Any]:
        """Get a specific sales order by GUID."""
        response = await self._make_request("GET", f"SalesOrders/{order_guid}")
        
        if not response:
            raise UnleashedSalesOrderNotFoundError(f"Sales order {order_guid} not found")
        
        return response
    
    async def create_sales_order(self, order_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new sales order."""
        return await self._make_request("POST", "SalesOrders", json_data=order_data)
    
    # Supplier Operations
    
    async def get_suppliers(
        self,
        page: int = 1,
        page_size: int = 200,
        supplier_code: Optional[str] = None,
        modified_since: Optional[str] = None
    ) -> Dict[str, Any]:
        """Get suppliers from Unleashed."""
        params = {
            "page": page,
            "pageSize": min(page_size, 200)
        }
        
        if supplier_code:
            params["supplierCode"] = supplier_code
        if modified_since:
            params["modifiedSince"] = modified_since
        
        return await self._make_request("GET", "Suppliers", params=params)
    
    async def get_supplier(self, supplier_guid: str) -> Dict[str, Any]:
        """Get a specific supplier by GUID."""
        response = await self._make_request("GET", f"Suppliers/{supplier_guid}")
        
        if not response:
            raise UnleashedSupplierNotFoundError(f"Supplier {supplier_guid} not found")
        
        return response
    
    async def create_supplier(self, supplier_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new supplier."""
        return await self._make_request("POST", "Suppliers", json_data=supplier_data)
    
    # Customer Operations
    
    async def get_customers(
        self,
        page: int = 1,
        page_size: int = 200,
        customer_code: Optional[str] = None,
        modified_since: Optional[str] = None
    ) -> Dict[str, Any]:
        """Get customers from Unleashed."""
        params = {
            "page": page,
            "pageSize": min(page_size, 200)
        }
        
        if customer_code:
            params["customerCode"] = customer_code
        if modified_since:
            params["modifiedSince"] = modified_since
        
        return await self._make_request("GET", "Customers", params=params)
    
    async def get_customer(self, customer_guid: str) -> Dict[str, Any]:
        """Get a specific customer by GUID."""
        response = await self._make_request("GET", f"Customers/{customer_guid}")
        
        if not response:
            raise UnleashedCustomerNotFoundError(f"Customer {customer_guid} not found")
        
        return response
    
    # Warehouse Operations
    
    async def get_warehouses(
        self,
        page: int = 1,
        page_size: int = 200,
        warehouse_code: Optional[str] = None
    ) -> Dict[str, Any]:
        """Get warehouses from Unleashed."""
        params = {
            "page": page,
            "pageSize": min(page_size, 200)
        }
        
        if warehouse_code:
            params["warehouseCode"] = warehouse_code
        
        return await self._make_request("GET", "Warehouses", params=params)
    
    async def get_warehouse(self, warehouse_guid: str) -> Dict[str, Any]:
        """Get a specific warehouse by GUID."""
        response = await self._make_request("GET", f"Warehouses/{warehouse_guid}")
        
        if not response:
            raise UnleashedWarehouseNotFoundError(f"Warehouse {warehouse_guid} not found")
        
        return response
    
    # Company Operations
    
    async def get_companies(
        self,
        page: int = 1,
        page_size: int = 200
    ) -> Dict[str, Any]:
        """Get companies from Unleashed."""
        params = {
            "page": page,
            "pageSize": min(page_size, 200)
        }
        
        return await self._make_request("GET", "Companies", params=params)
    
    # Transaction Operations
    
    async def get_stock_transactions(
        self,
        page: int = 1,
        page_size: int = 200,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        transaction_type: Optional[str] = None
    ) -> Dict[str, Any]:
        """Get stock transactions from Unleashed."""
        params = {
            "page": page,
            "pageSize": min(page_size, 200)
        }
        
        if start_date:
            params["startDate"] = start_date
        if end_date:
            params["endDate"] = end_date
        if transaction_type:
            params["transactionType"] = transaction_type
        
        return await self._make_request("GET", "StockTransactions", params=params)
    
    # Reporting Operations
    
    async def get_stock_report(
        self,
        warehouse_code: Optional[str] = None,
        as_at_date: Optional[str] = None
    ) -> Dict[str, Any]:
        """Get stock report from Unleashed."""
        params = {}
        
        if warehouse_code:
            params["warehouseCode"] = warehouse_code
        if as_at_date:
            params["asAtDate"] = as_at_date
        
        return await self._make_request("GET", "StockReport", params=params)
    
    async def get_stock_valuation_report(
        self,
        warehouse_code: Optional[str] = None,
        as_at_date: Optional[str] = None
    ) -> Dict[str, Any]:
        """Get stock valuation report from Unleashed."""
        params = {}
        
        if warehouse_code:
            params["warehouseCode"] = warehouse_code
        if as_at_date:
            params["asAtDate"] = as_at_date
        
        return await self._make_request("GET", "StockValuationReport", params=params)