"""
Shopify E-commerce Exception Classes
Custom exceptions for Shopify e-commerce platform integration errors.
"""

from typing import Optional, Dict, Any

from ....shared.exceptions.integration_exceptions import (
    ConnectionError,
    AuthenticationError,
    DataSyncError,
    ValidationError,
    RateLimitError,
    WebhookError
)


class ShopifyConnectionError(ConnectionError):
    """Shopify connection and network related errors."""
    
    def __init__(
        self,
        message: str,
        shop_name: Optional[str] = None,
        endpoint: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(message)
        self.shop_name = shop_name
        self.endpoint = endpoint
        self.details = details or {}


class ShopifyAuthenticationError(AuthenticationError):
    """Shopify authentication and authorization errors."""
    
    def __init__(
        self,
        message: str,
        shop_name: Optional[str] = None,
        auth_type: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(message)
        self.shop_name = shop_name
        self.auth_type = auth_type
        self.details = details or {}


class ShopifyAPIError(Exception):
    """Shopify API specific errors including rate limits and API responses."""
    
    def __init__(
        self,
        message: str,
        status_code: Optional[int] = None,
        response_data: Optional[Dict[str, Any]] = None,
        endpoint: Optional[str] = None,
        shop_name: Optional[str] = None
    ):
        super().__init__(message)
        self.status_code = status_code
        self.response_data = response_data or {}
        self.endpoint = endpoint
        self.shop_name = shop_name


class ShopifyRateLimitError(RateLimitError):
    """Shopify API rate limit exceeded errors."""
    
    def __init__(
        self,
        message: str = "Shopify API rate limit exceeded",
        retry_after: Optional[int] = None,
        call_limit: Optional[int] = None,
        calls_made: Optional[int] = None,
        shop_name: Optional[str] = None
    ):
        super().__init__(message, retry_after)
        self.call_limit = call_limit
        self.calls_made = calls_made
        self.shop_name = shop_name


class ShopifyValidationError(ValidationError):
    """Shopify data validation errors."""
    
    def __init__(
        self,
        message: str,
        field_name: Optional[str] = None,
        invalid_value: Optional[Any] = None,
        order_id: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(message)
        self.field_name = field_name
        self.invalid_value = invalid_value
        self.order_id = order_id
        self.details = details or {}


class ShopifyWebhookError(WebhookError):
    """Shopify webhook processing errors."""
    
    def __init__(
        self,
        message: str,
        webhook_topic: Optional[str] = None,
        shop_name: Optional[str] = None,
        webhook_id: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(message)
        self.webhook_topic = webhook_topic
        self.shop_name = shop_name
        self.webhook_id = webhook_id
        self.details = details or {}


class ShopifyDataExtractionError(DataSyncError):
    """Shopify data extraction and synchronization errors."""
    
    def __init__(
        self,
        message: str,
        order_id: Optional[str] = None,
        shop_name: Optional[str] = None,
        extraction_type: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(message)
        self.order_id = order_id
        self.shop_name = shop_name
        self.extraction_type = extraction_type
        self.details = details or {}


class ShopifyTransformationError(Exception):
    """Shopify order to UBL invoice transformation errors."""
    
    def __init__(
        self,
        message: str,
        order_id: Optional[str] = None,
        order_number: Optional[str] = None,
        transformation_stage: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(message)
        self.order_id = order_id
        self.order_number = order_number
        self.transformation_stage = transformation_stage
        self.details = details or {}


class ShopifyConfigurationError(Exception):
    """Shopify connector configuration errors."""
    
    def __init__(
        self,
        message: str,
        config_key: Optional[str] = None,
        shop_name: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(message)
        self.config_key = config_key
        self.shop_name = shop_name
        self.details = details or {}


class ShopifyProductError(Exception):
    """Shopify product-related errors."""
    
    def __init__(
        self,
        message: str,
        product_id: Optional[str] = None,
        sku: Optional[str] = None,
        shop_name: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(message)
        self.product_id = product_id
        self.sku = sku
        self.shop_name = shop_name
        self.details = details or {}


class ShopifyCustomerError(Exception):
    """Shopify customer-related errors."""
    
    def __init__(
        self,
        message: str,
        customer_id: Optional[str] = None,
        email: Optional[str] = None,
        shop_name: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(message)
        self.customer_id = customer_id
        self.email = email
        self.shop_name = shop_name
        self.details = details or {}


class ShopifyInventoryError(Exception):
    """Shopify inventory and fulfillment errors."""
    
    def __init__(
        self,
        message: str,
        inventory_item_id: Optional[str] = None,
        location_id: Optional[str] = None,
        shop_name: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(message)
        self.inventory_item_id = inventory_item_id
        self.location_id = location_id
        self.shop_name = shop_name
        self.details = details or {}


def create_shopify_exception(
    error: Exception,
    context: Optional[Dict[str, Any]] = None
) -> Exception:
    """
    Create appropriate Shopify exception based on the original error type and context.
    
    Args:
        error: Original exception
        context: Additional context for error classification
        
    Returns:
        Exception: Appropriate Shopify exception
    """
    context = context or {}
    error_message = str(error)
    
    # Extract common context
    shop_name = context.get('shop_name')
    endpoint = context.get('endpoint')
    status_code = context.get('status_code')
    
    # Connection errors
    if any(keyword in error_message.lower() for keyword in [
        'connection', 'network', 'timeout', 'unreachable', 'dns'
    ]):
        return ShopifyConnectionError(
            error_message,
            shop_name=shop_name,
            endpoint=endpoint,
            details=context
        )
    
    # Authentication errors
    if any(keyword in error_message.lower() for keyword in [
        'unauthorized', 'forbidden', 'invalid token', 'authentication', 'permission'
    ]) or status_code in [401, 403]:
        return ShopifyAuthenticationError(
            error_message,
            shop_name=shop_name,
            details=context
        )
    
    # Rate limit errors
    if 'rate limit' in error_message.lower() or status_code == 429:
        return ShopifyRateLimitError(
            error_message,
            shop_name=shop_name
        )
    
    # API errors
    if status_code and status_code >= 400:
        return ShopifyAPIError(
            error_message,
            status_code=status_code,
            endpoint=endpoint,
            shop_name=shop_name,
            response_data=context.get('response_data')
        )
    
    # Validation errors
    if any(keyword in error_message.lower() for keyword in [
        'invalid', 'validation', 'required', 'format'
    ]):
        return ShopifyValidationError(
            error_message,
            details=context
        )
    
    # Webhook errors
    if 'webhook' in error_message.lower():
        return ShopifyWebhookError(
            error_message,
            shop_name=shop_name,
            details=context
        )
    
    # Data extraction errors
    if any(keyword in error_message.lower() for keyword in [
        'extraction', 'sync', 'data'
    ]):
        return ShopifyDataExtractionError(
            error_message,
            shop_name=shop_name,
            details=context
        )
    
    # Configuration errors
    if any(keyword in error_message.lower() for keyword in [
        'config', 'setting', 'credential'
    ]):
        return ShopifyConfigurationError(
            error_message,
            shop_name=shop_name,
            details=context
        )
    
    # Default to generic API error
    return ShopifyAPIError(
        error_message,
        shop_name=shop_name,
        endpoint=endpoint,
        status_code=status_code
    )