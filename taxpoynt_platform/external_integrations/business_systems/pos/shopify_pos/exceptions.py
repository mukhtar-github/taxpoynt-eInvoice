"""
Shopify POS Connector Exceptions

Custom exception classes for Shopify POS integration errors and error handling.
Provides specific error types for different Shopify API and authentication scenarios.
"""

from typing import Any, Dict, List, Optional


class ShopifyError(Exception):
    """Base exception for all Shopify POS connector errors."""
    
    def __init__(
        self, 
        message: str, 
        error_code: Optional[str] = None, 
        details: Optional[Dict[str, Any]] = None
    ):
        """
        Initialize Shopify error.
        
        Args:
            message: Error message
            error_code: Shopify API error code
            details: Additional error details
        """
        super().__init__(message)
        self.message = message
        self.error_code = error_code
        self.details = details or {}
    
    def __str__(self) -> str:
        """String representation of the error."""
        if self.error_code:
            return f"[{self.error_code}] {self.message}"
        return self.message
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert error to dictionary format."""
        return {
            'error_type': self.__class__.__name__,
            'message': self.message,
            'error_code': self.error_code,
            'details': self.details
        }


class ShopifyConnectionError(ShopifyError):
    """Exception raised for Shopify API connection issues."""
    
    def __init__(
        self, 
        message: str = "Shopify API connection failed", 
        status_code: Optional[int] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        """
        Initialize connection error.
        
        Args:
            message: Error message
            status_code: HTTP status code
            details: Additional error details
        """
        super().__init__(message, details=details)
        self.status_code = status_code
        if status_code:
            self.details['status_code'] = status_code


class ShopifyAuthenticationError(ShopifyError):
    """Exception raised for Shopify authentication failures."""
    
    def __init__(
        self, 
        message: str = "Shopify authentication failed", 
        auth_type: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        """
        Initialize authentication error.
        
        Args:
            message: Error message
            auth_type: Type of authentication that failed (oauth, private_app, etc.)
            details: Additional error details
        """
        super().__init__(message, details=details)
        self.auth_type = auth_type
        if auth_type:
            self.details['auth_type'] = auth_type


class ShopifyAPIError(ShopifyError):
    """Exception raised for Shopify API request failures."""
    
    def __init__(
        self, 
        message: str = "Shopify API request failed", 
        error_code: Optional[str] = None,
        status_code: Optional[int] = None,
        errors: Optional[List[Dict[str, Any]]] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        """
        Initialize API error.
        
        Args:
            message: Error message
            error_code: Shopify API error code
            status_code: HTTP status code
            errors: List of Shopify API errors
            details: Additional error details
        """
        super().__init__(message, error_code=error_code, details=details)
        self.status_code = status_code
        self.errors = errors or []
        
        if status_code:
            self.details['status_code'] = status_code
        if self.errors:
            self.details['api_errors'] = self.errors
    
    @classmethod
    def from_response(
        cls, 
        response_data: Dict[str, Any], 
        status_code: int,
        default_message: str = "Shopify API request failed"
    ) -> 'ShopifyAPIError':
        """
        Create ShopifyAPIError from API response.
        
        Args:
            response_data: Shopify API response data
            status_code: HTTP status code
            default_message: Default error message if none in response
        
        Returns:
            ShopifyAPIError instance
        """
        errors = response_data.get('errors', [])
        
        if errors:
            # Handle different error formats from Shopify
            if isinstance(errors, dict):
                # Format: {"errors": {"field": ["error message"]}}
                error_messages = []
                for field, messages in errors.items():
                    if isinstance(messages, list):
                        error_messages.extend([f"{field}: {msg}" for msg in messages])
                    else:
                        error_messages.append(f"{field}: {messages}")
                message = "; ".join(error_messages)
                error_code = "VALIDATION_ERROR"
            elif isinstance(errors, list):
                # Format: {"errors": [{"message": "error", "code": "error_code"}]}
                if errors and isinstance(errors[0], dict):
                    first_error = errors[0]
                    message = first_error.get('message', default_message)
                    error_code = first_error.get('code', str(status_code))
                else:
                    # Format: {"errors": ["error message"]}
                    message = errors[0] if errors else default_message
                    error_code = str(status_code)
            else:
                message = str(errors)
                error_code = str(status_code)
        else:
            message = default_message
            error_code = str(status_code)
        
        return cls(
            message=message,
            error_code=error_code,
            status_code=status_code,
            errors=errors if isinstance(errors, list) else [errors] if errors else [],
            details={'response_data': response_data}
        )


class ShopifyRateLimitError(ShopifyAPIError):
    """Exception raised when Shopify API rate limits are exceeded."""
    
    def __init__(
        self, 
        message: str = "Shopify API rate limit exceeded", 
        retry_after: Optional[int] = None,
        call_limit: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        """
        Initialize rate limit error.
        
        Args:
            message: Error message
            retry_after: Seconds to wait before retrying
            call_limit: Shopify call limit header value
            details: Additional error details
        """
        super().__init__(message, error_code="RATE_LIMITED", status_code=429, details=details)
        self.retry_after = retry_after
        self.call_limit = call_limit
        
        if retry_after:
            self.details['retry_after'] = retry_after
        if call_limit:
            self.details['call_limit'] = call_limit


class ShopifyNotFoundError(ShopifyAPIError):
    """Exception raised when Shopify API resource is not found."""
    
    def __init__(
        self, 
        resource_type: str = "resource",
        resource_id: Optional[str] = None, 
        details: Optional[Dict[str, Any]] = None
    ):
        """
        Initialize not found error.
        
        Args:
            resource_type: Type of resource that was not found
            resource_id: ID of the resource that was not found
            details: Additional error details
        """
        message = f"Shopify {resource_type} not found"
        if resource_id:
            message += f" (ID: {resource_id})"
        
        super().__init__(message, error_code="NOT_FOUND", status_code=404, details=details)
        self.resource_type = resource_type
        self.resource_id = resource_id
        
        if resource_id:
            self.details['resource_id'] = resource_id
        self.details['resource_type'] = resource_type


class ShopifyValidationError(ShopifyError):
    """Exception raised for Shopify API validation errors."""
    
    def __init__(
        self, 
        message: str = "Shopify API validation failed", 
        field_errors: Optional[Dict[str, List[str]]] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        """
        Initialize validation error.
        
        Args:
            message: Error message
            field_errors: Dictionary of field validation errors
            details: Additional error details
        """
        super().__init__(message, error_code="VALIDATION_ERROR", details=details)
        self.field_errors = field_errors or {}
        if self.field_errors:
            self.details['field_errors'] = self.field_errors


class ShopifyWebhookError(ShopifyError):
    """Exception raised for Shopify webhook processing errors."""
    
    def __init__(
        self, 
        message: str = "Shopify webhook processing failed", 
        webhook_id: Optional[str] = None,
        event_type: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        """
        Initialize webhook error.
        
        Args:
            message: Error message
            webhook_id: Webhook ID
            event_type: Webhook event type
            details: Additional error details
        """
        super().__init__(message, details=details)
        self.webhook_id = webhook_id
        self.event_type = event_type
        
        if webhook_id:
            self.details['webhook_id'] = webhook_id
        if event_type:
            self.details['event_type'] = event_type


class ShopifyOrderError(ShopifyAPIError):
    """Exception raised for Shopify order processing errors."""
    
    def __init__(
        self, 
        message: str = "Shopify order processing failed", 
        order_id: Optional[str] = None,
        error_code: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        """
        Initialize order error.
        
        Args:
            message: Error message
            order_id: Shopify order ID
            error_code: Shopify order error code
            details: Additional error details
        """
        super().__init__(message, error_code=error_code, details=details)
        self.order_id = order_id
        
        if order_id:
            self.details['order_id'] = order_id


class ShopifyProductError(ShopifyAPIError):
    """Exception raised for Shopify product management errors."""
    
    def __init__(
        self, 
        message: str = "Shopify product operation failed", 
        product_id: Optional[str] = None,
        error_code: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        """
        Initialize product error.
        
        Args:
            message: Error message
            product_id: Shopify product ID
            error_code: Shopify product error code
            details: Additional error details
        """
        super().__init__(message, error_code=error_code, details=details)
        self.product_id = product_id
        
        if product_id:
            self.details['product_id'] = product_id


class ShopifyLocationError(ShopifyAPIError):
    """Exception raised for Shopify location management errors."""
    
    def __init__(
        self, 
        message: str = "Shopify location operation failed", 
        location_id: Optional[str] = None,
        error_code: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        """
        Initialize location error.
        
        Args:
            message: Error message
            location_id: Shopify location ID
            error_code: Shopify location error code
            details: Additional error details
        """
        super().__init__(message, error_code=error_code, details=details)
        self.location_id = location_id
        
        if location_id:
            self.details['location_id'] = location_id


class ShopifyConfigurationError(ShopifyError):
    """Exception raised for Shopify connector configuration errors."""
    
    def __init__(
        self, 
        message: str = "Shopify connector configuration error", 
        config_field: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        """
        Initialize configuration error.
        
        Args:
            message: Error message
            config_field: Configuration field that caused the error
            details: Additional error details
        """
        super().__init__(message, error_code="CONFIGURATION_ERROR", details=details)
        self.config_field = config_field
        
        if config_field:
            self.details['config_field'] = config_field


class ShopifyTimeoutError(ShopifyConnectionError):
    """Exception raised for Shopify API request timeouts."""
    
    def __init__(
        self, 
        message: str = "Shopify API request timeout", 
        timeout_duration: Optional[float] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        """
        Initialize timeout error.
        
        Args:
            message: Error message
            timeout_duration: Timeout duration in seconds
            details: Additional error details
        """
        super().__init__(message, details=details)
        self.timeout_duration = timeout_duration
        
        if timeout_duration:
            self.details['timeout_duration'] = timeout_duration


class ShopifyPermissionError(ShopifyAPIError):
    """Exception raised for Shopify API permission/scope errors."""
    
    def __init__(
        self, 
        message: str = "Shopify API permission denied", 
        required_scope: Optional[str] = None,
        current_scopes: Optional[List[str]] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        """
        Initialize permission error.
        
        Args:
            message: Error message
            required_scope: Required scope for the operation
            current_scopes: Current available scopes
            details: Additional error details
        """
        super().__init__(message, error_code="PERMISSION_DENIED", status_code=403, details=details)
        self.required_scope = required_scope
        self.current_scopes = current_scopes or []
        
        if required_scope:
            self.details['required_scope'] = required_scope
        if self.current_scopes:
            self.details['current_scopes'] = self.current_scopes


# Exception mapping for Shopify API error codes
SHOPIFY_ERROR_CODE_MAPPING = {
    'UNAUTHORIZED': ShopifyAuthenticationError,
    'FORBIDDEN': ShopifyPermissionError,
    'NOT_FOUND': ShopifyNotFoundError,
    'TOO_MANY_REQUESTS': ShopifyRateLimitError,
    'VALIDATION_ERROR': ShopifyValidationError,
    'UNPROCESSABLE_ENTITY': ShopifyValidationError,
    'ORDER_NOT_FOUND': ShopifyOrderError,
    'PRODUCT_NOT_FOUND': ShopifyProductError,
    'LOCATION_NOT_FOUND': ShopifyLocationError,
    'INVALID_API_KEY': ShopifyAuthenticationError,
    'INVALID_PERMISSIONS': ShopifyPermissionError,
    'RATE_LIMITED': ShopifyRateLimitError
}


def create_shopify_exception(
    error_code: str, 
    message: str, 
    status_code: Optional[int] = None,
    details: Optional[Dict[str, Any]] = None
) -> ShopifyError:
    """
    Create appropriate Shopify exception based on error code.
    
    Args:
        error_code: Shopify API error code
        message: Error message
        status_code: HTTP status code
        details: Additional error details
    
    Returns:
        Appropriate Shopify exception instance
    """
    exception_class = SHOPIFY_ERROR_CODE_MAPPING.get(error_code, ShopifyAPIError)
    
    if exception_class == ShopifyAPIError:
        return exception_class(
            message=message,
            error_code=error_code,
            status_code=status_code,
            details=details
        )
    elif exception_class in (ShopifyOrderError, ShopifyProductError, ShopifyLocationError):
        return exception_class(
            message=message,
            error_code=error_code,
            details=details
        )
    elif exception_class == ShopifyRateLimitError:
        return exception_class(
            message=message,
            details=details
        )
    else:
        return exception_class(message=message, details=details)