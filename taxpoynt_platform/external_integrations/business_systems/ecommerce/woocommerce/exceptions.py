"""
WooCommerce E-commerce Exception Classes
Custom exceptions for WooCommerce e-commerce platform integration errors.
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


class WooCommerceConnectionError(ConnectionError):
    """WooCommerce connection and network related errors."""
    
    def __init__(
        self,
        message: str,
        store_url: Optional[str] = None,
        endpoint: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(message)
        self.store_url = store_url
        self.endpoint = endpoint
        self.details = details or {}


class WooCommerceAuthenticationError(AuthenticationError):
    """WooCommerce authentication and authorization errors."""
    
    def __init__(
        self,
        message: str,
        store_url: Optional[str] = None,
        auth_type: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(message)
        self.store_url = store_url
        self.auth_type = auth_type
        self.details = details or {}


class WooCommerceAPIError(Exception):
    """WooCommerce REST API specific errors."""
    
    def __init__(
        self,
        message: str,
        status_code: Optional[int] = None,
        error_code: Optional[str] = None,
        response_data: Optional[Dict[str, Any]] = None,
        endpoint: Optional[str] = None,
        store_url: Optional[str] = None
    ):
        super().__init__(message)
        self.status_code = status_code
        self.error_code = error_code
        self.response_data = response_data or {}
        self.endpoint = endpoint
        self.store_url = store_url


class WooCommerceRateLimitError(RateLimitError):
    """WooCommerce API rate limit exceeded errors."""
    
    def __init__(
        self,
        message: str = "WooCommerce API rate limit exceeded",
        retry_after: Optional[int] = None,
        requests_per_minute: Optional[int] = None,
        store_url: Optional[str] = None
    ):
        super().__init__(message, retry_after)
        self.requests_per_minute = requests_per_minute
        self.store_url = store_url


class WooCommerceValidationError(ValidationError):
    """WooCommerce data validation errors."""
    
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


class WooCommerceWebhookError(WebhookError):
    """WooCommerce webhook processing errors."""
    
    def __init__(
        self,
        message: str,
        webhook_topic: Optional[str] = None,
        store_url: Optional[str] = None,
        webhook_id: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(message)
        self.webhook_topic = webhook_topic
        self.store_url = store_url
        self.webhook_id = webhook_id
        self.details = details or {}


class WooCommerceDataExtractionError(DataSyncError):
    """WooCommerce data extraction and synchronization errors."""
    
    def __init__(
        self,
        message: str,
        order_id: Optional[str] = None,
        store_url: Optional[str] = None,
        extraction_type: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(message)
        self.order_id = order_id
        self.store_url = store_url
        self.extraction_type = extraction_type
        self.details = details or {}


class WooCommerceTransformationError(Exception):
    """WooCommerce order to UBL invoice transformation errors."""
    
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


class WooCommerceConfigurationError(Exception):
    """WooCommerce connector configuration errors."""
    
    def __init__(
        self,
        message: str,
        config_key: Optional[str] = None,
        store_url: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(message)
        self.config_key = config_key
        self.store_url = store_url
        self.details = details or {}


class WooCommerceProductError(Exception):
    """WooCommerce product-related errors."""
    
    def __init__(
        self,
        message: str,
        product_id: Optional[str] = None,
        sku: Optional[str] = None,
        store_url: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(message)
        self.product_id = product_id
        self.sku = sku
        self.store_url = store_url
        self.details = details or {}


class WooCommerceCustomerError(Exception):
    """WooCommerce customer-related errors."""
    
    def __init__(
        self,
        message: str,
        customer_id: Optional[str] = None,
        email: Optional[str] = None,
        store_url: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(message)
        self.customer_id = customer_id
        self.email = email
        self.store_url = store_url
        self.details = details or {}


class WooCommercePluginError(Exception):
    """WooCommerce plugin and extension errors."""
    
    def __init__(
        self,
        message: str,
        plugin_name: Optional[str] = None,
        plugin_version: Optional[str] = None,
        store_url: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(message)
        self.plugin_name = plugin_name
        self.plugin_version = plugin_version
        self.store_url = store_url
        self.details = details or {}


class WooCommerceWordPressError(Exception):
    """WordPress-specific errors for WooCommerce integration."""
    
    def __init__(
        self,
        message: str,
        wp_version: Optional[str] = None,
        wc_version: Optional[str] = None,
        store_url: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(message)
        self.wp_version = wp_version
        self.wc_version = wc_version
        self.store_url = store_url
        self.details = details or {}


def create_woocommerce_exception(
    error: Exception,
    context: Optional[Dict[str, Any]] = None
) -> Exception:
    """
    Create appropriate WooCommerce exception based on the original error type and context.
    
    Args:
        error: Original exception
        context: Additional context for error classification
        
    Returns:
        Exception: Appropriate WooCommerce exception
    """
    context = context or {}
    error_message = str(error)
    
    # Extract common context
    store_url = context.get('store_url')
    endpoint = context.get('endpoint')
    status_code = context.get('status_code')
    error_code = context.get('error_code')
    
    # Connection errors
    if any(keyword in error_message.lower() for keyword in [
        'connection', 'network', 'timeout', 'unreachable', 'dns', 'ssl'
    ]):
        return WooCommerceConnectionError(
            error_message,
            store_url=store_url,
            endpoint=endpoint,
            details=context
        )
    
    # Authentication errors
    if any(keyword in error_message.lower() for keyword in [
        'unauthorized', 'forbidden', 'invalid key', 'authentication', 
        'consumer_key', 'consumer_secret', 'signature'
    ]) or status_code in [401, 403]:
        return WooCommerceAuthenticationError(
            error_message,
            store_url=store_url,
            details=context
        )
    
    # Rate limit errors
    if 'rate limit' in error_message.lower() or status_code == 429:
        return WooCommerceRateLimitError(
            error_message,
            store_url=store_url
        )
    
    # WordPress/WooCommerce specific errors
    if any(keyword in error_message.lower() for keyword in [
        'wordpress', 'wp-json', 'rest_no_route', 'woocommerce_rest'
    ]):
        return WooCommerceWordPressError(
            error_message,
            store_url=store_url,
            details=context
        )
    
    # Plugin errors
    if any(keyword in error_message.lower() for keyword in [
        'plugin', 'extension', 'addon'
    ]):
        return WooCommercePluginError(
            error_message,
            store_url=store_url,
            details=context
        )
    
    # API errors
    if status_code and status_code >= 400:
        return WooCommerceAPIError(
            error_message,
            status_code=status_code,
            error_code=error_code,
            endpoint=endpoint,
            store_url=store_url,
            response_data=context.get('response_data')
        )
    
    # Validation errors
    if any(keyword in error_message.lower() for keyword in [
        'invalid', 'validation', 'required', 'format', 'missing'
    ]):
        return WooCommerceValidationError(
            error_message,
            details=context
        )
    
    # Webhook errors
    if 'webhook' in error_message.lower():
        return WooCommerceWebhookError(
            error_message,
            store_url=store_url,
            details=context
        )
    
    # Data extraction errors
    if any(keyword in error_message.lower() for keyword in [
        'extraction', 'sync', 'data'
    ]):
        return WooCommerceDataExtractionError(
            error_message,
            store_url=store_url,
            details=context
        )
    
    # Configuration errors
    if any(keyword in error_message.lower() for keyword in [
        'config', 'setting', 'credential', 'key', 'secret'
    ]):
        return WooCommerceConfigurationError(
            error_message,
            store_url=store_url,
            details=context
        )
    
    # Default to generic API error
    return WooCommerceAPIError(
        error_message,
        store_url=store_url,
        endpoint=endpoint,
        status_code=status_code,
        error_code=error_code
    )