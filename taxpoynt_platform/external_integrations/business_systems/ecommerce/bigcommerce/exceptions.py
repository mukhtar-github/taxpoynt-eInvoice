"""
BigCommerce E-commerce Exception Classes
Custom exceptions for BigCommerce e-commerce platform integration errors.
"""
from typing import Optional, Dict, Any

from ....shared.exceptions.integration_exceptions import (
    ConnectionError,
    AuthenticationError,
    DataExtractionError,
    TransformationError,
    APIError
)


class BigCommerceConnectionError(ConnectionError):
    """Raised when BigCommerce store connection fails."""
    
    def __init__(self, message: str, store_hash: Optional[str] = None, details: Optional[Dict[str, Any]] = None):
        super().__init__(message, details)
        self.store_hash = store_hash


class BigCommerceAuthenticationError(AuthenticationError):
    """Raised when BigCommerce API authentication fails."""
    
    def __init__(self, message: str, auth_type: Optional[str] = None, details: Optional[Dict[str, Any]] = None):
        super().__init__(message, details)
        self.auth_type = auth_type


class BigCommerceDataExtractionError(DataExtractionError):
    """Raised when BigCommerce data extraction fails."""
    
    def __init__(self, message: str, resource_type: Optional[str] = None, details: Optional[Dict[str, Any]] = None):
        super().__init__(message, details)
        self.resource_type = resource_type


class BigCommerceTransformationError(TransformationError):
    """Raised when BigCommerce order transformation fails."""
    
    def __init__(self, message: str, order_id: Optional[str] = None, details: Optional[Dict[str, Any]] = None):
        super().__init__(message, details)
        self.order_id = order_id


class BigCommerceAPIError(APIError):
    """Raised when BigCommerce API returns an error."""
    
    def __init__(
        self,
        message: str,
        status_code: Optional[int] = None,
        response_data: Optional[Dict[str, Any]] = None,
        endpoint: Optional[str] = None
    ):
        super().__init__(message, status_code, response_data)
        self.endpoint = endpoint


class BigCommerceOrderNotFoundError(BigCommerceDataExtractionError):
    """Raised when a specific BigCommerce order is not found."""
    
    def __init__(self, order_id: str, details: Optional[Dict[str, Any]] = None):
        message = f"BigCommerce order not found: {order_id}"
        super().__init__(message, "order", details)
        self.order_id = order_id


class BigCommerceCustomerNotFoundError(BigCommerceDataExtractionError):
    """Raised when a specific BigCommerce customer is not found."""
    
    def __init__(self, customer_id: str, details: Optional[Dict[str, Any]] = None):
        message = f"BigCommerce customer not found: {customer_id}"
        super().__init__(message, "customer", details)
        self.customer_id = customer_id


class BigCommerceProductNotFoundError(BigCommerceDataExtractionError):
    """Raised when a specific BigCommerce product is not found."""
    
    def __init__(self, product_id: str, details: Optional[Dict[str, Any]] = None):
        message = f"BigCommerce product not found: {product_id}"
        super().__init__(message, "product", details)
        self.product_id = product_id


class BigCommerceStoreNotFoundError(BigCommerceConnectionError):
    """Raised when BigCommerce store is not found or inaccessible."""
    
    def __init__(self, store_hash: str, details: Optional[Dict[str, Any]] = None):
        message = f"BigCommerce store not found or inaccessible: {store_hash}"
        super().__init__(message, store_hash, details)


class BigCommerceRateLimitError(BigCommerceAPIError):
    """Raised when BigCommerce API rate limit is exceeded."""
    
    def __init__(
        self,
        message: str = "BigCommerce API rate limit exceeded",
        retry_after: Optional[int] = None,
        limit_type: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(message, 429, details)
        self.retry_after = retry_after
        self.limit_type = limit_type  # 'hourly', 'daily', etc.


class BigCommerceWebhookError(BigCommerceAPIError):
    """Raised when BigCommerce webhook processing fails."""
    
    def __init__(
        self,
        message: str,
        event_type: Optional[str] = None,
        webhook_id: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(message, details=details)
        self.event_type = event_type
        self.webhook_id = webhook_id


class BigCommerceChannelError(BigCommerceAPIError):
    """Raised when BigCommerce channel operations fail."""
    
    def __init__(
        self,
        message: str,
        channel_id: Optional[int] = None,
        channel_type: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(message, details=details)
        self.channel_id = channel_id
        self.channel_type = channel_type


class BigCommerceAppError(BigCommerceAPIError):
    """Raised when BigCommerce app-specific operations fail."""
    
    def __init__(
        self,
        message: str,
        app_id: Optional[str] = None,
        operation: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(message, details=details)
        self.app_id = app_id
        self.operation = operation


class BigCommerceScriptError(BigCommerceAPIError):
    """Raised when BigCommerce Script API operations fail."""
    
    def __init__(
        self,
        message: str,
        script_type: Optional[str] = None,
        script_id: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(message, details=details)
        self.script_type = script_type
        self.script_id = script_id


class BigCommerceCheckoutError(BigCommerceAPIError):
    """Raised when BigCommerce Checkout SDK operations fail."""
    
    def __init__(
        self,
        message: str,
        checkout_id: Optional[str] = None,
        step: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(message, details=details)
        self.checkout_id = checkout_id
        self.step = step


class BigCommerceMultiChannelError(BigCommerceAPIError):
    """Raised when BigCommerce multi-channel operations fail."""
    
    def __init__(
        self,
        message: str,
        channel_ids: Optional[list] = None,
        operation: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(message, details=details)
        self.channel_ids = channel_ids or []
        self.operation = operation


# Exception mapping for API error codes
BIGCOMMERCE_ERROR_CODE_MAPPING = {
    400: BigCommerceAPIError,
    401: BigCommerceAuthenticationError,
    403: BigCommerceAuthenticationError,
    404: BigCommerceAPIError,
    409: BigCommerceAPIError,
    422: BigCommerceAPIError,
    429: BigCommerceRateLimitError,
    500: BigCommerceAPIError,
    502: BigCommerceConnectionError,
    503: BigCommerceConnectionError,
    504: BigCommerceConnectionError
}


def map_api_error(
    status_code: int,
    message: str,
    response_data: Optional[Dict[str, Any]] = None,
    endpoint: Optional[str] = None
) -> BigCommerceAPIError:
    """
    Map HTTP status codes to appropriate BigCommerce exception types.
    
    Args:
        status_code: HTTP status code
        message: Error message
        response_data: API response data
        endpoint: API endpoint that failed
        
    Returns:
        Appropriate BigCommerce exception instance
    """
    exception_class = BIGCOMMERCE_ERROR_CODE_MAPPING.get(status_code, BigCommerceAPIError)
    
    if exception_class == BigCommerceRateLimitError:
        retry_after = None
        if response_data and isinstance(response_data, dict):
            retry_after = response_data.get('retry_after')
        return exception_class(message, retry_after=retry_after, details=response_data)
    elif exception_class in (BigCommerceConnectionError, BigCommerceAuthenticationError):
        return exception_class(message, details=response_data)
    else:
        return exception_class(message, status_code, response_data, endpoint)