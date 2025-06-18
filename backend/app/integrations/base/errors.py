"""
Error handling for integration connectors.

This module provides standardized error handling, custom exceptions,
and utilities for managing integration errors.
"""

import logging
from typing import Dict, Any, Optional, List, Type

logger = logging.getLogger(__name__)


class IntegrationError(Exception):
    """Base exception for all integration errors."""
    
    def __init__(
        self,
        message: str,
        error_code: str = "INTEGRATION_ERROR",
        details: Optional[Dict[str, Any]] = None
    ):
        """
        Initialize integration error.
        
        Args:
            message: Error message
            error_code: Error code identifier
            details: Additional error details
        """
        self.message = message
        self.error_code = error_code
        self.details = details or {}
        super().__init__(self.message)


class AuthenticationError(IntegrationError):
    """Error during authentication with external system."""
    
    def __init__(
        self,
        message: str = "Authentication with external system failed",
        details: Optional[Dict[str, Any]] = None
    ):
        """Initialize authentication error."""
        super().__init__(message, "AUTHENTICATION_ERROR", details)


class ConnectionError(IntegrationError):
    """Error establishing connection to external system."""
    
    def __init__(
        self,
        message: str = "Connection to external system failed",
        details: Optional[Dict[str, Any]] = None
    ):
        """Initialize connection error."""
        super().__init__(message, "CONNECTION_ERROR", details)


class RateLimitError(IntegrationError):
    """Error due to rate limiting by external system."""
    
    def __init__(
        self,
        message: str = "Rate limit exceeded",
        retry_after: Optional[int] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        """
        Initialize rate limit error.
        
        Args:
            message: Error message
            retry_after: Seconds to wait before retrying (if available)
            details: Additional error details
        """
        details = details or {}
        if retry_after:
            details["retry_after"] = retry_after
            
        super().__init__(message, "RATE_LIMIT_ERROR", details)


class DataValidationError(IntegrationError):
    """Error validating data from or for external system."""
    
    def __init__(
        self,
        message: str = "Data validation failed",
        validation_errors: Optional[List[Dict[str, Any]]] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        """
        Initialize data validation error.
        
        Args:
            message: Error message
            validation_errors: List of specific validation errors
            details: Additional error details
        """
        details = details or {}
        if validation_errors:
            details["validation_errors"] = validation_errors
            
        super().__init__(message, "DATA_VALIDATION_ERROR", details)


class PermissionError(IntegrationError):
    """Error due to insufficient permissions in external system."""
    
    def __init__(
        self,
        message: str = "Insufficient permissions",
        required_permissions: Optional[List[str]] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        """
        Initialize permission error.
        
        Args:
            message: Error message
            required_permissions: List of required permissions
            details: Additional error details
        """
        details = details or {}
        if required_permissions:
            details["required_permissions"] = required_permissions
            
        super().__init__(message, "PERMISSION_ERROR", details)


def handle_integration_error(
    error: Exception,
    integration_name: str,
    operation: str
) -> IntegrationError:
    """
    Handle and normalize external system errors into standard IntegrationErrors.
    
    Args:
        error: Original exception
        integration_name: Name of the integration
        operation: Name of the operation that failed
        
    Returns:
        Standardized IntegrationError
    """
    # If it's already an IntegrationError, just return it
    if isinstance(error, IntegrationError):
        return error
        
    # Log the original error
    logger.error(
        f"Error in {integration_name} during {operation}: {str(error)}",
        exc_info=True
    )
    
    # Common HTTP status code handling
    if hasattr(error, "status_code"):
        status_code = error.status_code
        
        # Authentication errors
        if status_code in (401, 403):
            return AuthenticationError(
                f"Authentication failed for {integration_name}: {str(error)}",
                details={"original_error": str(error), "status_code": status_code}
            )
            
        # Rate limiting
        if status_code == 429:
            # Try to extract retry-after header if available
            retry_after = None
            if hasattr(error, "headers") and error.headers.get("retry-after"):
                try:
                    retry_after = int(error.headers["retry-after"])
                except (ValueError, TypeError):
                    pass
                    
            return RateLimitError(
                f"Rate limit exceeded for {integration_name}",
                retry_after=retry_after,
                details={"original_error": str(error)}
            )
            
        # Permission issues
        if status_code in (401, 403):
            return PermissionError(
                f"Permission denied in {integration_name}: {str(error)}",
                details={"original_error": str(error), "status_code": status_code}
            )
            
        # Data validation issues
        if status_code == 400:
            return DataValidationError(
                f"Data validation failed in {integration_name}: {str(error)}",
                details={"original_error": str(error)}
            )
            
        # Connection issues
        if status_code in (502, 503, 504):
            return ConnectionError(
                f"Connection to {integration_name} failed: {str(error)}",
                details={"original_error": str(error), "status_code": status_code}
            )
    
    # Handle common error types by name pattern
    error_class_name = error.__class__.__name__.lower()
    
    if "timeout" in error_class_name:
        return ConnectionError(
            f"Connection to {integration_name} timed out: {str(error)}",
            details={"original_error": str(error), "error_type": "timeout"}
        )
        
    if "connection" in error_class_name:
        return ConnectionError(
            f"Connection to {integration_name} failed: {str(error)}",
            details={"original_error": str(error)}
        )
        
    # Default to generic integration error
    return IntegrationError(
        f"Error in {integration_name} during {operation}: {str(error)}",
        details={"original_error": str(error), "error_type": error.__class__.__name__}
    )


def error_to_dict(error: Exception) -> Dict[str, Any]:
    """
    Convert an exception to a standardized error dictionary.
    
    Args:
        error: Exception to convert
        
    Returns:
        Dictionary with error details
    """
    if isinstance(error, IntegrationError):
        result = {
            "error_code": error.error_code,
            "message": error.message,
        }
        
        if error.details:
            result["details"] = error.details
            
        return result
    else:
        return {
            "error_code": "UNKNOWN_ERROR",
            "message": str(error),
            "details": {"error_type": error.__class__.__name__}
        }
