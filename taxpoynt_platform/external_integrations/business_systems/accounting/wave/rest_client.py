"""
Wave REST API Client
Handles all HTTP communication with Wave Accounting GraphQL API.
"""
import asyncio
import logging
from typing import Dict, List, Optional, Any, Union
from datetime import datetime, timedelta
import json

import aiohttp
from aiohttp import ClientSession, ClientTimeout, ClientError

from .auth import WaveAuthManager
from .exceptions import (
    WaveAPIError,
    WaveConnectionError,
    WaveRateLimitError,
    WaveAuthenticationError,
    WaveMaintenanceError,
    WaveBusinessNotFoundError
)


logger = logging.getLogger(__name__)


class WaveRestClient:
    """
    REST client for Wave Accounting GraphQL API.
    
    Wave uses GraphQL for their API, so this client handles GraphQL queries
    and mutations while providing a REST-like interface.
    """
    
    # Wave API endpoints
    SANDBOX_BASE_URL = "https://gql.waveapps.com"
    PRODUCTION_BASE_URL = "https://gql.waveapps.com"
    
    GRAPHQL_ENDPOINT = "/graphql/public"
    
    # Rate limiting settings
    MAX_REQUESTS_PER_MINUTE = 60
    MAX_RETRIES = 3
    RETRY_DELAY = 1.0
    
    def __init__(
        self,
        auth_manager: WaveAuthManager,
        session: Optional[ClientSession] = None,
        max_retries: int = MAX_RETRIES
    ):
        """
        Initialize Wave REST client.
        
        Args:
            auth_manager: Wave authentication manager
            session: Optional aiohttp session
            max_retries: Maximum number of retry attempts
        """
        self.auth_manager = auth_manager
        self.session = session
        self.should_close_session = session is None
        self.max_retries = max_retries
        
        self.base_url = (
            self.SANDBOX_BASE_URL if auth_manager.sandbox 
            else self.PRODUCTION_BASE_URL
        )
        
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
                headers={"User-Agent": "TaxPoynt-Wave-Integration/1.0"}
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
            # Remove requests older than 1 minute
            cutoff = now - timedelta(minutes=1)
            self._request_times = [t for t in self._request_times if t > cutoff]
            
            # Check if we're at rate limit
            if len(self._request_times) >= self.MAX_REQUESTS_PER_MINUTE:
                sleep_time = 60 - (now - self._request_times[0]).total_seconds()
                logger.warning(f"Rate limit reached, sleeping for {sleep_time:.2f} seconds")
                await asyncio.sleep(sleep_time)
                # Clean up old requests again after sleeping
                now = datetime.utcnow()
                cutoff = now - timedelta(minutes=1)
                self._request_times = [t for t in self._request_times if t > cutoff]
            
            # Record this request
            self._request_times.append(now)
    
    async def _make_request(
        self,
        query: str,
        variables: Optional[Dict[str, Any]] = None,
        operation_name: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Make a GraphQL request to Wave API.
        
        Args:
            query: GraphQL query or mutation
            variables: Query variables
            operation_name: Operation name for named queries
            
        Returns:
            Response data
        """
        if not self.session:
            raise WaveConnectionError("No HTTP session available")
        
        await self._rate_limit_check()
        
        # Ensure we have a valid token
        token = await self.auth_manager.ensure_valid_token()
        
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "query": query,
            "variables": variables or {},
        }
        
        if operation_name:
            payload["operationName"] = operation_name
        
        url = f"{self.base_url}{self.GRAPHQL_ENDPOINT}"
        
        for attempt in range(self.max_retries + 1):
            try:
                async with self.session.post(url, json=payload, headers=headers) as response:
                    response_data = await response.json()
                    
                    # Handle HTTP errors
                    if response.status == 401:
                        raise WaveAuthenticationError("Authentication failed")
                    elif response.status == 429:
                        retry_after = int(response.headers.get("Retry-After", 60))
                        raise WaveRateLimitError(
                            "Rate limit exceeded", 
                            retry_after=retry_after
                        )
                    elif response.status == 503:
                        raise WaveMaintenanceError("Wave API is under maintenance")
                    elif response.status >= 400:
                        raise WaveAPIError(
                            f"HTTP {response.status}: {response_data}",
                            status_code=response.status,
                            response_data=response_data
                        )
                    
                    # Handle GraphQL errors
                    if "errors" in response_data:
                        errors = response_data["errors"]
                        error_msg = "; ".join([err.get("message", str(err)) for err in errors])
                        raise WaveAPIError(f"GraphQL errors: {error_msg}")
                    
                    return response_data.get("data", {})
                    
            except WaveRateLimitError as e:
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
                raise WaveConnectionError(f"Failed to connect to Wave API: {str(e)}")
        
        raise WaveConnectionError("Max retries exceeded")
    
    async def get_businesses(self) -> List[Dict[str, Any]]:
        """
        Get list of businesses accessible to the authenticated user.
        
        Returns:
            List of business objects
        """
        query = """
        query GetBusinesses {
            businesses(first: 50) {
                edges {
                    node {
                        id
                        name
                        organizationName
                        businessType
                        currency {
                            code
                            symbol
                        }
                        address {
                            addressLine1
                            addressLine2
                            city
                            postalCode
                            countryCode
                            provinceCode
                        }
                        timezone
                        createdAt
                        modifiedAt
                    }
                }
            }
        }
        """
        
        response = await self._make_request(query)
        businesses = []
        
        for edge in response.get("businesses", {}).get("edges", []):
            business = edge.get("node", {})
            businesses.append(business)
        
        return businesses
    
    async def get_business(self, business_id: str) -> Dict[str, Any]:
        """
        Get specific business by ID.
        
        Args:
            business_id: Wave business ID
            
        Returns:
            Business object
        """
        query = """
        query GetBusiness($businessId: ID!) {
            business(id: $businessId) {
                id
                name
                organizationName
                businessType
                currency {
                    code
                    symbol
                }
                address {
                    addressLine1
                    addressLine2
                    city
                    postalCode
                    countryCode
                    provinceCode
                }
                timezone
                createdAt
                modifiedAt
            }
        }
        """
        
        variables = {"businessId": business_id}
        response = await self._make_request(query, variables)
        
        business = response.get("business")
        if not business:
            raise WaveBusinessNotFoundError(f"Business {business_id} not found")
        
        return business
    
    async def get_customers(
        self,
        business_id: str,
        limit: int = 50,
        cursor: Optional[str] = None,
        modified_since: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """
        Get customers for a business.
        
        Args:
            business_id: Wave business ID
            limit: Number of customers to retrieve
            cursor: Pagination cursor
            modified_since: Only return customers modified since this date
            
        Returns:
            Paginated customers response
        """
        query = """
        query GetCustomers($businessId: ID!, $first: Int!, $after: String, $modifiedAt: DateTime) {
            business(id: $businessId) {
                customers(first: $first, after: $after, modifiedAt: $modifiedAt) {
                    pageInfo {
                        hasNextPage
                        hasPreviousPage
                        startCursor
                        endCursor
                    }
                    edges {
                        node {
                            id
                            name
                            email
                            firstName
                            lastName
                            displayId
                            address {
                                addressLine1
                                addressLine2
                                city
                                postalCode
                                countryCode
                                provinceCode
                            }
                            phone
                            fax
                            mobile
                            tollFree
                            website
                            currency {
                                code
                                symbol
                            }
                            createdAt
                            modifiedAt
                        }
                    }
                }
            }
        }
        """
        
        variables = {
            "businessId": business_id,
            "first": min(limit, 50),  # Wave limits to 50 per request
        }
        
        if cursor:
            variables["after"] = cursor
        
        if modified_since:
            variables["modifiedAt"] = modified_since.isoformat()
        
        response = await self._make_request(query, variables)
        
        business = response.get("business")
        if not business:
            raise WaveBusinessNotFoundError(f"Business {business_id} not found")
        
        return business.get("customers", {})
    
    async def get_products(
        self,
        business_id: str,
        limit: int = 50,
        cursor: Optional[str] = None,
        modified_since: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """
        Get products for a business.
        
        Args:
            business_id: Wave business ID
            limit: Number of products to retrieve
            cursor: Pagination cursor
            modified_since: Only return products modified since this date
            
        Returns:
            Paginated products response
        """
        query = """
        query GetProducts($businessId: ID!, $first: Int!, $after: String, $modifiedAt: DateTime) {
            business(id: $businessId) {
                products(first: $first, after: $after, modifiedAt: $modifiedAt) {
                    pageInfo {
                        hasNextPage
                        hasPreviousPage
                        startCursor
                        endCursor
                    }
                    edges {
                        node {
                            id
                            name
                            description
                            unitPrice
                            defaultSalesTaxes {
                                id
                                name
                                rate
                            }
                            isArchived
                            createdAt
                            modifiedAt
                        }
                    }
                }
            }
        }
        """
        
        variables = {
            "businessId": business_id,
            "first": min(limit, 50),
        }
        
        if cursor:
            variables["after"] = cursor
        
        if modified_since:
            variables["modifiedAt"] = modified_since.isoformat()
        
        response = await self._make_request(query, variables)
        
        business = response.get("business")
        if not business:
            raise WaveBusinessNotFoundError(f"Business {business_id} not found")
        
        return business.get("products", {})
    
    async def get_invoices(
        self,
        business_id: str,
        limit: int = 50,
        cursor: Optional[str] = None,
        modified_since: Optional[datetime] = None,
        status_filter: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Get invoices for a business.
        
        Args:
            business_id: Wave business ID
            limit: Number of invoices to retrieve
            cursor: Pagination cursor
            modified_since: Only return invoices modified since this date
            status_filter: Filter by invoice status (DRAFT, SENT, PAID, etc.)
            
        Returns:
            Paginated invoices response
        """
        query = """
        query GetInvoices($businessId: ID!, $first: Int!, $after: String, $modifiedAt: DateTime, $status: InvoiceStatus) {
            business(id: $businessId) {
                invoices(first: $first, after: $after, modifiedAt: $modifiedAt, status: $status) {
                    pageInfo {
                        hasNextPage
                        hasPreviousPage
                        startCursor
                        endCursor
                    }
                    edges {
                        node {
                            id
                            invoiceNumber
                            poNumber
                            title
                            subhead
                            customer {
                                id
                                name
                                email
                            }
                            invoiceDate
                            dueDate
                            amountDue {
                                value
                                currency {
                                    code
                                }
                            }
                            amountPaid {
                                value
                                currency {
                                    code
                                }
                            }
                            taxTotal {
                                value
                                currency {
                                    code
                                }
                            }
                            total {
                                value
                                currency {
                                    code
                                }
                            }
                            exchangeRate
                            items {
                                product {
                                    id
                                    name
                                }
                                description
                                quantity
                                price
                                subtotal {
                                    value
                                }
                                total {
                                    value
                                }
                                taxes {
                                    salesTax {
                                        id
                                        name
                                        rate
                                    }
                                    amount {
                                        value
                                    }
                                }
                            }
                            status
                            createdAt
                            modifiedAt
                        }
                    }
                }
            }
        }
        """
        
        variables = {
            "businessId": business_id,
            "first": min(limit, 50),
        }
        
        if cursor:
            variables["after"] = cursor
        
        if modified_since:
            variables["modifiedAt"] = modified_since.isoformat()
        
        if status_filter:
            variables["status"] = status_filter
        
        response = await self._make_request(query, variables)
        
        business = response.get("business")
        if not business:
            raise WaveBusinessNotFoundError(f"Business {business_id} not found")
        
        return business.get("invoices", {})
    
    async def get_sales_taxes(self, business_id: str) -> List[Dict[str, Any]]:
        """
        Get sales taxes configured for a business.
        
        Args:
            business_id: Wave business ID
            
        Returns:
            List of sales tax objects
        """
        query = """
        query GetSalesTaxes($businessId: ID!) {
            business(id: $businessId) {
                salesTaxes {
                    id
                    name
                    abbreviation
                    description
                    rate
                    isCompound
                    isRecoverable
                    showTaxNumberOnInvoices
                }
            }
        }
        """
        
        variables = {"businessId": business_id}
        response = await self._make_request(query, variables)
        
        business = response.get("business")
        if not business:
            raise WaveBusinessNotFoundError(f"Business {business_id} not found")
        
        return business.get("salesTaxes", [])
    
    async def create_customer(
        self,
        business_id: str,
        customer_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Create a new customer in Wave.
        
        Args:
            business_id: Wave business ID
            customer_data: Customer data
            
        Returns:
            Created customer object
        """
        mutation = """
        mutation CustomerCreate($input: CustomerCreateInput!) {
            customerCreate(input: $input) {
                didSucceed
                inputErrors {
                    field
                    message
                }
                customer {
                    id
                    name
                    email
                    displayId
                }
            }
        }
        """
        
        input_data = {
            "businessId": business_id,
            **customer_data
        }
        
        variables = {"input": input_data}
        response = await self._make_request(mutation, variables)
        
        result = response.get("customerCreate", {})
        
        if not result.get("didSucceed"):
            errors = result.get("inputErrors", [])
            error_msg = "; ".join([f"{err['field']}: {err['message']}" for err in errors])
            raise WaveAPIError(f"Failed to create customer: {error_msg}")
        
        return result.get("customer", {})
    
    async def create_invoice(
        self,
        business_id: str,
        invoice_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Create a new invoice in Wave.
        
        Args:
            business_id: Wave business ID
            invoice_data: Invoice data
            
        Returns:
            Created invoice object
        """
        mutation = """
        mutation InvoiceCreate($input: InvoiceCreateInput!) {
            invoiceCreate(input: $input) {
                didSucceed
                inputErrors {
                    field
                    message
                }
                invoice {
                    id
                    invoiceNumber
                    status
                    total {
                        value
                        currency {
                            code
                        }
                    }
                }
            }
        }
        """
        
        input_data = {
            "businessId": business_id,
            **invoice_data
        }
        
        variables = {"input": input_data}
        response = await self._make_request(mutation, variables)
        
        result = response.get("invoiceCreate", {})
        
        if not result.get("didSucceed"):
            errors = result.get("inputErrors", [])
            error_msg = "; ".join([f"{err['field']}: {err['message']}" for err in errors])
            raise WaveAPIError(f"Failed to create invoice: {error_msg}")
        
        return result.get("invoice", {})