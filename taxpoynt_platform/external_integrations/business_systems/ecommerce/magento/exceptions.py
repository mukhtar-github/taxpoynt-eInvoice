"""
Magento E-commerce Exception Classes
Custom exceptions for Magento e-commerce platform integration errors.
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


class MagentoConnectionError(ConnectionError):
    """Magento connection and network related errors."""
    
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


class MagentoAuthenticationError(AuthenticationError):
    """Magento authentication and authorization errors."""
    
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


class MagentoAPIError(Exception):
    """Magento REST API specific errors."""
    
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


class MagentoRateLimitError(RateLimitError):
    """Magento API rate limit exceeded errors."""
    
    def __init__(
        self,
        message: str = "Magento API rate limit exceeded",
        retry_after: Optional[int] = None,
        requests_per_hour: Optional[int] = None,
        store_url: Optional[str] = None
    ):
        super().__init__(message, retry_after)
        self.requests_per_hour = requests_per_hour
        self.store_url = store_url


class MagentoValidationError(ValidationError):
    """Magento data validation errors."""
    
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


class MagentoWebhookError(WebhookError):
    """Magento webhook processing errors."""
    
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


class MagentoDataExtractionError(DataSyncError):
    """Magento data extraction and synchronization errors."""
    
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


class MagentoTransformationError(Exception):
    """Magento order to UBL invoice transformation errors."""
    
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


class MagentoConfigurationError(Exception):
    """Magento connector configuration errors."""
    
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


class MagentoProductError(Exception):
    """Magento product-related errors."""
    
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


class MagentoCustomerError(Exception):
    """Magento customer-related errors."""
    
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


class MagentoExtensionError(Exception):
    """Magento extension and module errors."""
    
    def __init__(
        self,
        message: str,
        extension_name: Optional[str] = None,
        extension_version: Optional[str] = None,
        store_url: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(message)
        self.extension_name = extension_name
        self.extension_version = extension_version
        self.store_url = store_url
        self.details = details or {}


class MagentoStoreViewError(Exception):
    """Magento store view and multi-store errors."""
    
    def __init__(
        self,
        message: str,
        store_view_id: Optional[str] = None,
        store_code: Optional[str] = None,
        store_url: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(message)
        self.store_view_id = store_view_id
        self.store_code = store_code
        self.store_url = store_url
        self.details = details or {}


class MagentoInventoryError(Exception):
    """Magento inventory and MSI (Multi-Source Inventory) errors."""
    
    def __init__(
        self,
        message: str,
        source_code: Optional[str] = None,
        stock_id: Optional[str] = None,
        sku: Optional[str] = None,
        store_url: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(message)
        self.source_code = source_code
        self.stock_id = stock_id
        self.sku = sku
        self.store_url = store_url
        self.details = details or {}


def create_magento_exception(
    error: Exception,
    context: Optional[Dict[str, Any]] = None
) -> Exception:
    """
    Create appropriate Magento exception based on the original error type and context.
    
    Args:
        error: Original exception
        context: Additional context for error classification
        
    Returns:
        Exception: Appropriate Magento exception
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
        return MagentoConnectionError(
            error_message,
            store_url=store_url,
            endpoint=endpoint,
            details=context
        )
    
    # Authentication errors
    if any(keyword in error_message.lower() for keyword in [
        'unauthorized', 'forbidden', 'invalid token', 'authentication', 
        'access token', 'bearer token', 'signature'
    ]) or status_code in [401, 403]:
        return MagentoAuthenticationError(
            error_message,
            store_url=store_url,
            details=context
        )
    
    # Rate limit errors
    if 'rate limit' in error_message.lower() or status_code == 429:
        return MagentoRateLimitError(
            error_message,
            store_url=store_url
        )
    
    # Magento-specific errors
    if any(keyword in error_message.lower() for keyword in [
        'magento', 'rest/v1', 'rest/default/v1', 'integration'
    ]):
        return MagentoAPIError(
            error_message,
            status_code=status_code,
            error_code=error_code,
            endpoint=endpoint,
            store_url=store_url,
            response_data=context.get('response_data')
        )
    
    # Store view errors
    if any(keyword in error_message.lower() for keyword in [
        'store view', 'store code', 'website', 'store group'
    ]):
        return MagentoStoreViewError(
            error_message,
            store_url=store_url,
            details=context
        )
    
    # Extension/module errors
    if any(keyword in error_message.lower() for keyword in [
        'extension', 'module', 'plugin', 'addon'
    ]):
        return MagentoExtensionError(
            error_message,
            store_url=store_url,
            details=context
        )
    
    # Inventory errors
    if any(keyword in error_message.lower() for keyword in [
        'inventory', 'stock', 'msi', 'source', 'salable'
    ]):
        return MagentoInventoryError(
            error_message,
            store_url=store_url,
            details=context
        )
    
    # API errors
    if status_code and status_code >= 400:
        return MagentoAPIError(
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
        return MagentoValidationError(
            error_message,
            details=context
        )
    
    # Webhook errors
    if 'webhook' in error_message.lower():
        return MagentoWebhookError(
            error_message,
            store_url=store_url,
            details=context
        )
    
    # Data extraction errors
    if any(keyword in error_message.lower() for keyword in [
        'extraction', 'sync', 'data'
    ]):
        return MagentoDataExtractionError(
            error_message,
            store_url=store_url,
            details=context
        )
    
    # Configuration errors
    if any(keyword in error_message.lower() for keyword in [
        'config', 'setting', 'credential', 'token'
    ]):
        return MagentoConfigurationError(
            error_message,
            store_url=store_url,
            details=context
        )
    
    # Default to generic API error
    return MagentoAPIError(
        error_message,
        store_url=store_url,
        endpoint=endpoint,
        status_code=status_code,
        error_code=error_code
    )