"""
FreshBooks Exceptions
Custom exception classes for FreshBooks integration errors.
"""
from typing import Optional, Dict, Any


class FreshBooksException(Exception):
    """Base exception for all FreshBooks integration errors."""
    
    def __init__(self, message: str, error_code: Optional[str] = None, details: Optional[Dict[str, Any]] = None):
        super().__init__(message)
        self.error_code = error_code
        self.details = details or {}


class FreshBooksAuthenticationError(FreshBooksException):
    """Raised when FreshBooks authentication fails."""
    pass


class FreshBooksAuthorizationError(FreshBooksException):
    """Raised when FreshBooks authorization fails (insufficient permissions)."""
    pass


class FreshBooksAPIError(FreshBooksException):
    """Raised when FreshBooks API returns an error response."""
    
    def __init__(self, message: str, status_code: Optional[int] = None, 
                 response_data: Optional[Dict[str, Any]] = None, **kwargs):
        super().__init__(message, **kwargs)
        self.status_code = status_code
        self.response_data = response_data or {}


class FreshBooksRateLimitError(FreshBooksAPIError):
    """Raised when FreshBooks API rate limit is exceeded."""
    
    def __init__(self, message: str, retry_after: Optional[int] = None, **kwargs):
        super().__init__(message, **kwargs)
        self.retry_after = retry_after


class FreshBooksConnectionError(FreshBooksException):
    """Raised when connection to FreshBooks API fails."""
    pass


class FreshBooksConfigurationError(FreshBooksException):
    """Raised when FreshBooks configuration is invalid."""
    pass


class FreshBooksDataError(FreshBooksException):
    """Raised when FreshBooks data is invalid or cannot be processed."""
    pass


class FreshBooksAccountNotFoundError(FreshBooksException):
    """Raised when specified FreshBooks account is not found."""
    pass


class FreshBooksClientNotFoundError(FreshBooksException):
    """Raised when specified FreshBooks client is not found."""
    pass


class FreshBooksInvoiceNotFoundError(FreshBooksException):
    """Raised when specified FreshBooks invoice is not found."""
    pass


class FreshBooksItemNotFoundError(FreshBooksException):
    """Raised when specified FreshBooks item is not found."""
    pass


class FreshBooksValidationError(FreshBooksDataError):
    """Raised when FreshBooks data validation fails."""
    pass


class FreshBooksTransformationError(FreshBooksDataError):
    """Raised when transforming FreshBooks data to UBL format fails."""
    pass


class FreshBooksSyncError(FreshBooksException):
    """Raised when FreshBooks data synchronization fails."""
    pass


class FreshBooksQuotaExceededError(FreshBooksException):
    """Raised when FreshBooks account quota is exceeded."""
    pass


class FreshBooksMaintenanceError(FreshBooksAPIError):
    """Raised when FreshBooks API is under maintenance."""
    pass


class FreshBooksDeprecationError(FreshBooksAPIError):
    """Raised when using deprecated FreshBooks API endpoints."""
    pass


class FreshBooksWebhookError(FreshBooksException):
    """Raised when FreshBooks webhook processing fails."""
    pass


class FreshBooksPermissionError(FreshBooksAuthorizationError):
    """Raised when FreshBooks permission is denied for specific operation."""
    pass