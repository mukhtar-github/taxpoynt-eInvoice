"""
Mono API Exceptions
===================

Custom exception classes for Mono Open Banking integration.
Provides specific error handling for different failure scenarios.

Exception Hierarchy:
- MonoBaseException (base for all Mono errors)
  - MonoConnectionError (network/API connectivity issues)
  - MonoAuthenticationError (authentication/authorization failures)
  - MonoValidationError (request validation failures)  
  - MonoRateLimitError (rate limiting exceeded)
  - MonoAccountError (account-specific errors)
  - MonoTransactionError (transaction-related errors)
  - MonoWebhookError (webhook processing errors)

Architecture consistent with existing TaxPoynt exception patterns.
"""

from typing import Optional, Dict, Any


class MonoBaseException(Exception):
    """Base exception for all Mono API errors"""
    
    def __init__(
        self,
        message: str,
        error_code: Optional[str] = None,
        status_code: Optional[int] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(message)
        self.message = message
        self.error_code = error_code
        self.status_code = status_code
        self.details = details or {}
    
    def __str__(self) -> str:
        error_parts = [self.message]
        if self.error_code:
            error_parts.append(f"Error Code: {self.error_code}")
        if self.status_code:
            error_parts.append(f"Status: {self.status_code}")
        return " | ".join(error_parts)


class MonoConnectionError(MonoBaseException):
    """Raised when there are network or API connectivity issues"""
    
    def __init__(
        self,
        message: str = "Failed to connect to Mono API",
        error_code: Optional[str] = None,
        status_code: Optional[int] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(message, error_code, status_code, details)


class MonoAuthenticationError(MonoBaseException):
    """Raised when authentication or authorization fails"""
    
    def __init__(
        self,
        message: str = "Mono API authentication failed",
        error_code: Optional[str] = None,
        status_code: Optional[int] = 401,
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(message, error_code, status_code, details)


class MonoValidationError(MonoBaseException):
    """Raised when request validation fails"""
    
    def __init__(
        self,
        message: str = "Request validation failed",
        error_code: Optional[str] = None,
        status_code: Optional[int] = 400,
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(message, error_code, status_code, details)


class MonoRateLimitError(MonoBaseException):
    """Raised when API rate limits are exceeded"""
    
    def __init__(
        self,
        message: str = "Mono API rate limit exceeded",
        error_code: Optional[str] = "RATE_LIMIT_EXCEEDED",
        status_code: Optional[int] = 429,
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(message, error_code, status_code, details)
        self.retry_after = details.get("retry_after", 60) if details else 60


class MonoAccountError(MonoBaseException):
    """Raised when there are account-specific errors"""
    
    def __init__(
        self,
        message: str = "Account operation failed",
        error_code: Optional[str] = None,
        status_code: Optional[int] = None,
        details: Optional[Dict[str, Any]] = None,
        account_id: Optional[str] = None
    ):
        super().__init__(message, error_code, status_code, details)
        self.account_id = account_id


class MonoAccountNotFoundError(MonoAccountError):
    """Raised when an account is not found"""
    
    def __init__(
        self,
        account_id: str,
        message: Optional[str] = None
    ):
        message = message or f"Account not found: {account_id}"
        super().__init__(
            message=message,
            error_code="ACCOUNT_NOT_FOUND",
            status_code=404,
            account_id=account_id
        )


class MonoAccountDisconnectedError(MonoAccountError):
    """Raised when trying to access a disconnected account"""
    
    def __init__(
        self,
        account_id: str,
        message: Optional[str] = None
    ):
        message = message or f"Account is disconnected: {account_id}"
        super().__init__(
            message=message,
            error_code="ACCOUNT_DISCONNECTED",
            status_code=403,
            account_id=account_id
        )


class MonoReauthorizationRequiredError(MonoAccountError):
    """Raised when account reauthorization is required"""
    
    def __init__(
        self,
        account_id: str,
        reauth_url: Optional[str] = None,
        message: Optional[str] = None
    ):
        message = message or f"Account reauthorization required: {account_id}"
        details = {"reauth_url": reauth_url} if reauth_url else {}
        super().__init__(
            message=message,
            error_code="REAUTHORIZATION_REQUIRED",
            status_code=403,
            details=details,
            account_id=account_id
        )
        self.reauth_url = reauth_url


class MonoTransactionError(MonoBaseException):
    """Raised when there are transaction-related errors"""
    
    def __init__(
        self,
        message: str = "Transaction operation failed",
        error_code: Optional[str] = None,
        status_code: Optional[int] = None,
        details: Optional[Dict[str, Any]] = None,
        transaction_id: Optional[str] = None
    ):
        super().__init__(message, error_code, status_code, details)
        self.transaction_id = transaction_id


class MonoInsufficientDataError(MonoTransactionError):
    """Raised when insufficient transaction data is available"""
    
    def __init__(
        self,
        message: str = "Insufficient transaction data available",
        error_code: str = "INSUFFICIENT_DATA",
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(message, error_code, 404, details)


class MonoWebhookError(MonoBaseException):
    """Raised when there are webhook processing errors"""
    
    def __init__(
        self,
        message: str = "Webhook processing failed",
        error_code: Optional[str] = None,
        status_code: Optional[int] = None,
        details: Optional[Dict[str, Any]] = None,
        event_type: Optional[str] = None
    ):
        super().__init__(message, error_code, status_code, details)
        self.event_type = event_type


class MonoWebhookSignatureError(MonoWebhookError):
    """Raised when webhook signature verification fails"""
    
    def __init__(
        self,
        message: str = "Webhook signature verification failed",
        error_code: str = "INVALID_SIGNATURE"
    ):
        super().__init__(message, error_code, 401)


class MonoInvalidEventError(MonoWebhookError):
    """Raised when webhook event format is invalid"""
    
    def __init__(
        self,
        event_type: str,
        message: Optional[str] = None
    ):
        message = message or f"Invalid webhook event format: {event_type}"
        super().__init__(
            message=message,
            error_code="INVALID_EVENT_FORMAT",
            status_code=400,
            event_type=event_type
        )


class MonoServiceUnavailableError(MonoBaseException):
    """Raised when Mono service is temporarily unavailable"""
    
    def __init__(
        self,
        message: str = "Mono service temporarily unavailable",
        error_code: str = "SERVICE_UNAVAILABLE",
        retry_after: int = 300  # 5 minutes
    ):
        super().__init__(
            message=message,
            error_code=error_code,
            status_code=503,
            details={"retry_after": retry_after}
        )
        self.retry_after = retry_after


class MonoConfigurationError(MonoBaseException):
    """Raised when there are configuration-related errors"""
    
    def __init__(
        self,
        message: str = "Mono configuration error",
        error_code: str = "CONFIGURATION_ERROR"
    ):
        super().__init__(message, error_code)


class MonoInsufficientPermissionsError(MonoBaseException):
    """Raised when API key lacks required permissions"""
    
    def __init__(
        self,
        message: str = "Insufficient permissions for this operation",
        error_code: str = "INSUFFICIENT_PERMISSIONS",
        required_scope: Optional[str] = None
    ):
        details = {"required_scope": required_scope} if required_scope else {}
        super().__init__(
            message=message,
            error_code=error_code,
            status_code=403,
            details=details
        )


class MonoDataRetentionError(MonoBaseException):
    """Raised when data retention policies prevent operation"""
    
    def __init__(
        self,
        message: str = "Operation violates data retention policy",
        error_code: str = "DATA_RETENTION_VIOLATION",
        retention_period: Optional[int] = None
    ):
        details = {"retention_period_days": retention_period} if retention_period else {}
        super().__init__(
            message=message,
            error_code=error_code,
            status_code=403,
            details=details
        )


class MonoNigerianComplianceError(MonoBaseException):
    """Raised when operations violate Nigerian banking compliance rules"""
    
    def __init__(
        self,
        message: str = "Operation violates Nigerian banking compliance",
        error_code: str = "COMPLIANCE_VIOLATION",
        regulation: Optional[str] = None
    ):
        details = {"regulation": regulation} if regulation else {}
        super().__init__(
            message=message,
            error_code=error_code,
            status_code=403,
            details=details
        )


# Utility function to map Mono API error responses to appropriate exceptions
def map_mono_error(
    status_code: int,
    error_data: Dict[str, Any],
    context: Optional[str] = None
) -> MonoBaseException:
    """
    Map Mono API error responses to appropriate exception types.
    
    Args:
        status_code: HTTP status code
        error_data: Error response data from Mono API
        context: Optional context about the operation that failed
        
    Returns:
        MonoBaseException: Appropriate exception instance
    """
    message = error_data.get("message", "Unknown Mono API error")
    error_code = error_data.get("code") or error_data.get("error")
    
    if context:
        message = f"{context}: {message}"
    
    if status_code == 400:
        return MonoValidationError(message, error_code, status_code, error_data)
    elif status_code == 401:
        return MonoAuthenticationError(message, error_code, status_code, error_data)
    elif status_code == 403:
        if "reauthorization" in message.lower():
            return MonoReauthorizationRequiredError(
                account_id=error_data.get("account_id", "unknown"),
                message=message
            )
        elif "permissions" in message.lower():
            return MonoInsufficientPermissionsError(message, error_code)
        else:
            return MonoAccountError(message, error_code, status_code, error_data)
    elif status_code == 404:
        if "account" in message.lower():
            return MonoAccountNotFoundError(
                account_id=error_data.get("account_id", "unknown"),
                message=message
            )
        else:
            return MonoValidationError(message, error_code, status_code, error_data)
    elif status_code == 429:
        return MonoRateLimitError(message, error_code, status_code, error_data)
    elif status_code == 503:
        return MonoServiceUnavailableError(
            message=message,
            error_code=error_code or "SERVICE_UNAVAILABLE",
            retry_after=error_data.get("retry_after", 300)
        )
    else:
        return MonoConnectionError(message, error_code, status_code, error_data)


# Export all exceptions
__all__ = [
    "MonoBaseException",
    "MonoConnectionError", 
    "MonoAuthenticationError",
    "MonoValidationError",
    "MonoRateLimitError",
    "MonoAccountError",
    "MonoAccountNotFoundError",
    "MonoAccountDisconnectedError", 
    "MonoReauthorizationRequiredError",
    "MonoTransactionError",
    "MonoInsufficientDataError",
    "MonoWebhookError",
    "MonoWebhookSignatureError",
    "MonoInvalidEventError",
    "MonoServiceUnavailableError",
    "MonoConfigurationError",
    "MonoInsufficientPermissionsError",
    "MonoDataRetentionError",
    "MonoNigerianComplianceError",
    "map_mono_error"
]