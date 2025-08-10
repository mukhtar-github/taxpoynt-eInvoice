"""
Square POS Connector Exceptions

Custom exception classes for Square POS integration errors and error handling.
Provides specific error types for different Square API and authentication scenarios.
"""

from typing import Any, Dict, List, Optional


class SquareError(Exception):
    """Base exception for all Square POS connector errors."""
    
    def __init__(
        self, 
        message: str, 
        error_code: Optional[str] = None, 
        details: Optional[Dict[str, Any]] = None
    ):
        """
        Initialize Square error.
        
        Args:
            message: Error message
            error_code: Square API error code
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


class SquareConnectionError(SquareError):
    """Exception raised for Square API connection issues."""
    
    def __init__(
        self, 
        message: str = "Square API connection failed", 
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


class SquareAuthenticationError(SquareError):
    """Exception raised for Square authentication failures."""
    
    def __init__(
        self, 
        message: str = "Square authentication failed", 
        auth_type: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        """
        Initialize authentication error.
        
        Args:
            message: Error message
            auth_type: Type of authentication that failed (oauth, api_key, etc.)
            details: Additional error details
        """
        super().__init__(message, details=details)
        self.auth_type = auth_type
        if auth_type:
            self.details['auth_type'] = auth_type


class SquareAPIError(SquareError):
    """Exception raised for Square API request failures."""
    
    def __init__(
        self, 
        message: str = "Square API request failed", 
        error_code: Optional[str] = None,
        status_code: Optional[int] = None,
        errors: Optional[List[Dict[str, Any]]] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        """
        Initialize API error.
        
        Args:
            message: Error message
            error_code: Square API error code
            status_code: HTTP status code
            errors: List of Square API errors
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
        default_message: str = "Square API request failed"
    ) -> 'SquareAPIError':
        """
        Create SquareAPIError from API response.
        
        Args:
            response_data: Square API response data
            status_code: HTTP status code
            default_message: Default error message if none in response
        
        Returns:
            SquareAPIError instance
        """
        errors = response_data.get('errors', [])
        
        if errors:
            # Use first error for main message and code
            first_error = errors[0]
            message = first_error.get('detail', default_message)
            error_code = first_error.get('code', str(status_code))
        else:
            message = default_message
            error_code = str(status_code)
        
        return cls(
            message=message,
            error_code=error_code,
            status_code=status_code,
            errors=errors,
            details={'response_data': response_data}
        )


class SquareRateLimitError(SquareAPIError):
    """Exception raised when Square API rate limits are exceeded."""
    
    def __init__(
        self, 
        message: str = "Square API rate limit exceeded", 
        retry_after: Optional[int] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        """
        Initialize rate limit error.
        
        Args:
            message: Error message
            retry_after: Seconds to wait before retrying
            details: Additional error details
        """
        super().__init__(message, error_code="RATE_LIMITED", status_code=429, details=details)
        self.retry_after = retry_after
        if retry_after:
            self.details['retry_after'] = retry_after


class SquareNotFoundError(SquareAPIError):
    """Exception raised when Square API resource is not found."""
    
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
        message = f"Square {resource_type} not found"
        if resource_id:
            message += f" (ID: {resource_id})"
        
        super().__init__(message, error_code="NOT_FOUND", status_code=404, details=details)
        self.resource_type = resource_type
        self.resource_id = resource_id
        
        if resource_id:
            self.details['resource_id'] = resource_id
        self.details['resource_type'] = resource_type


class SquareValidationError(SquareError):
    """Exception raised for Square API validation errors."""
    
    def __init__(
        self, 
        message: str = "Square API validation failed", 
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


class SquareWebhookError(SquareError):
    """Exception raised for Square webhook processing errors."""
    
    def __init__(
        self, 
        message: str = "Square webhook processing failed", 
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


class SquarePaymentError(SquareAPIError):
    """Exception raised for Square payment processing errors."""
    
    def __init__(
        self, 
        message: str = "Square payment processing failed", 
        payment_id: Optional[str] = None,
        error_code: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        """
        Initialize payment error.
        
        Args:
            message: Error message
            payment_id: Square payment ID
            error_code: Square payment error code
            details: Additional error details
        """
        super().__init__(message, error_code=error_code, details=details)
        self.payment_id = payment_id
        
        if payment_id:
            self.details['payment_id'] = payment_id


class SquareOrderError(SquareAPIError):
    """Exception raised for Square order processing errors."""
    
    def __init__(
        self, 
        message: str = "Square order processing failed", 
        order_id: Optional[str] = None,
        error_code: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        """
        Initialize order error.
        
        Args:
            message: Error message
            order_id: Square order ID
            error_code: Square order error code
            details: Additional error details
        """
        super().__init__(message, error_code=error_code, details=details)
        self.order_id = order_id
        
        if order_id:
            self.details['order_id'] = order_id


class SquareInventoryError(SquareAPIError):
    """Exception raised for Square inventory management errors."""
    
    def __init__(
        self, 
        message: str = "Square inventory operation failed", 
        catalog_object_id: Optional[str] = None,
        error_code: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        """
        Initialize inventory error.
        
        Args:
            message: Error message
            catalog_object_id: Square catalog object ID
            error_code: Square inventory error code
            details: Additional error details
        """
        super().__init__(message, error_code=error_code, details=details)
        self.catalog_object_id = catalog_object_id
        
        if catalog_object_id:
            self.details['catalog_object_id'] = catalog_object_id


class SquareConfigurationError(SquareError):
    """Exception raised for Square connector configuration errors."""
    
    def __init__(
        self, 
        message: str = "Square connector configuration error", 
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


class SquareTimeoutError(SquareConnectionError):
    """Exception raised for Square API request timeouts."""
    
    def __init__(
        self, 
        message: str = "Square API request timeout", 
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


# Exception mapping for Square API error codes
SQUARE_ERROR_CODE_MAPPING = {
    'UNAUTHORIZED': SquareAuthenticationError,
    'FORBIDDEN': SquareAuthenticationError,
    'NOT_FOUND': SquareNotFoundError,
    'RATE_LIMITED': SquareRateLimitError,
    'VALIDATION_ERROR': SquareValidationError,
    'PAYMENT_METHOD_NOT_SUPPORTED': SquarePaymentError,
    'PAYMENT_DECLINED': SquarePaymentError,
    'INSUFFICIENT_FUNDS': SquarePaymentError,
    'CARD_DECLINED': SquarePaymentError,
    'CVV_FAILURE': SquarePaymentError,
    'ADDRESS_VERIFICATION_FAILURE': SquarePaymentError,
    'INVALID_CARD': SquarePaymentError,
    'INVALID_PIN': SquarePaymentError,
    'CHECKOUT_EXPIRED': SquarePaymentError,
    'ORDER_NOT_FOUND': SquareOrderError,
    'ORDER_CLOSED': SquareOrderError,
    'INVALID_ORDER_STATE': SquareOrderError,
    'CATALOG_OBJECT_NOT_FOUND': SquareInventoryError,
    'INVENTORY_CHANGE_NOT_FOUND': SquareInventoryError,
    'INVALID_INVENTORY_STATE': SquareInventoryError
}


def create_square_exception(
    error_code: str, 
    message: str, 
    status_code: Optional[int] = None,
    details: Optional[Dict[str, Any]] = None
) -> SquareError:
    """
    Create appropriate Square exception based on error code.
    
    Args:
        error_code: Square API error code
        message: Error message
        status_code: HTTP status code
        details: Additional error details
    
    Returns:
        Appropriate Square exception instance
    """
    exception_class = SQUARE_ERROR_CODE_MAPPING.get(error_code, SquareAPIError)
    
    if exception_class == SquareAPIError:
        return exception_class(
            message=message,
            error_code=error_code,
            status_code=status_code,
            details=details
        )
    elif exception_class in (SquarePaymentError, SquareOrderError, SquareInventoryError):
        return exception_class(
            message=message,
            error_code=error_code,
            details=details
        )
    else:
        return exception_class(message=message, details=details)