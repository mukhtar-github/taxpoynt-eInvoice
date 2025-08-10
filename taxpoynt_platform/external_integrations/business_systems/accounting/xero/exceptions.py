"""
Xero Accounting Exception Classes
Custom exceptions for Xero accounting platform integration errors.
"""
from typing import Optional, Dict, Any
from ....connector_framework.base_accounting_connector import (
    AccountingConnectionError,
    AccountingAuthenticationError,
    AccountingDataError,
    AccountingValidationError,
    AccountingTransformationError
)


class XeroConnectionError(AccountingConnectionError):
    """Xero connection and network related errors."""
    
    def __init__(self, message: str, status_code: Optional[int] = None, response_data: Optional[Dict[str, Any]] = None):
        super().__init__(message)
        self.status_code = status_code
        self.response_data = response_data or {}
        self.platform = "Xero"


class XeroAuthenticationError(AccountingAuthenticationError):
    """Xero authentication and authorization errors."""
    
    def __init__(self, message: str, auth_type: Optional[str] = None, error_code: Optional[str] = None):
        super().__init__(message)
        self.auth_type = auth_type
        self.error_code = error_code
        self.platform = "Xero"


class XeroRateLimitError(XeroConnectionError):
    """Xero API rate limiting errors."""
    
    def __init__(self, message: str, retry_after: Optional[int] = None, daily_limit_exceeded: bool = False):
        super().__init__(message)
        self.retry_after = retry_after
        self.daily_limit_exceeded = daily_limit_exceeded
        self.error_type = "rate_limit"


class XeroDataError(AccountingDataError):
    """Xero data retrieval and processing errors."""
    
    def __init__(self, message: str, endpoint: Optional[str] = None, error_details: Optional[Dict[str, Any]] = None):
        super().__init__(message)
        self.endpoint = endpoint
        self.error_details = error_details or {}
        self.platform = "Xero"


class XeroValidationError(AccountingValidationError):
    """Xero data validation and business rule errors."""
    
    def __init__(self, message: str, validation_errors: Optional[list] = None, field_name: Optional[str] = None):
        super().__init__(message)
        self.validation_errors = validation_errors or []
        self.field_name = field_name
        self.platform = "Xero"


class XeroTransformationError(AccountingTransformationError):
    """Xero to UBL transformation errors."""
    
    def __init__(self, message: str, source_data: Optional[Dict[str, Any]] = None, transformation_stage: Optional[str] = None):
        super().__init__(message)
        self.source_data = source_data or {}
        self.transformation_stage = transformation_stage
        self.platform = "Xero"


class XeroWebhookError(XeroConnectionError):
    """Xero webhook processing errors."""
    
    def __init__(self, message: str, webhook_id: Optional[str] = None, event_type: Optional[str] = None):
        super().__init__(message)
        self.webhook_id = webhook_id
        self.event_type = event_type
        self.error_type = "webhook"


class XeroOrganisationError(XeroDataError):
    """Xero organisation (tenant) related errors."""
    
    def __init__(self, message: str, tenant_id: Optional[str] = None, organisation_id: Optional[str] = None):
        super().__init__(message)
        self.tenant_id = tenant_id
        self.organisation_id = organisation_id
        self.error_type = "organisation"


class XeroInvoiceError(XeroValidationError):
    """Xero invoice specific errors."""
    
    def __init__(self, message: str, invoice_id: Optional[str] = None, invoice_number: Optional[str] = None):
        super().__init__(message)
        self.invoice_id = invoice_id
        self.invoice_number = invoice_number
        self.error_type = "invoice"


class XeroContactError(XeroValidationError):
    """Xero contact (customer/supplier) specific errors."""
    
    def __init__(self, message: str, contact_id: Optional[str] = None, contact_name: Optional[str] = None):
        super().__init__(message)
        self.contact_id = contact_id
        self.contact_name = contact_name
        self.error_type = "contact"


class XeroAccountError(XeroValidationError):
    """Xero chart of accounts specific errors."""
    
    def __init__(self, message: str, account_id: Optional[str] = None, account_code: Optional[str] = None):
        super().__init__(message)
        self.account_id = account_id
        self.account_code = account_code
        self.error_type = "account"


class XeroTaxError(XeroValidationError):
    """Xero tax calculation and validation errors."""
    
    def __init__(self, message: str, tax_type: Optional[str] = None, tax_rate: Optional[float] = None):
        super().__init__(message)
        self.tax_type = tax_type
        self.tax_rate = tax_rate
        self.error_type = "tax"


def create_xero_exception(error_data: Dict[str, Any], context: Optional[str] = None) -> Exception:
    """
    Factory function to create appropriate Xero exception from API error response.
    
    Args:
        error_data: Error data from Xero API response
        context: Additional context about where the error occurred
        
    Returns:
        Appropriate Xero exception instance
    """
    # Extract common error information
    error_message = error_data.get('Detail', error_data.get('Message', 'Unknown Xero error'))
    error_type = error_data.get('Type', '').lower()
    status_code = error_data.get('StatusCode')
    
    # Add context to message if provided
    if context:
        error_message = f"{context}: {error_message}"
    
    # Map Xero error types to exception classes
    if 'authentication' in error_type or 'authorization' in error_type:
        return XeroAuthenticationError(
            message=error_message,
            error_code=error_data.get('ErrorNumber')
        )
    
    elif 'rate' in error_type and 'limit' in error_type:
        return XeroRateLimitError(
            message=error_message,
            retry_after=error_data.get('RetryAfter')
        )
    
    elif 'validation' in error_type or status_code in [400, 422]:
        validation_errors = error_data.get('ValidationErrors', [])
        return XeroValidationError(
            message=error_message,
            validation_errors=validation_errors
        )
    
    elif 'organisation' in error_type or 'tenant' in error_type:
        return XeroOrganisationError(
            message=error_message,
            tenant_id=error_data.get('TenantId')
        )
    
    elif 'invoice' in error_type:
        return XeroInvoiceError(
            message=error_message,
            invoice_id=error_data.get('InvoiceID')
        )
    
    elif 'contact' in error_type:
        return XeroContactError(
            message=error_message,
            contact_id=error_data.get('ContactID')
        )
    
    elif 'account' in error_type:
        return XeroAccountError(
            message=error_message,
            account_id=error_data.get('AccountID')
        )
    
    elif 'tax' in error_type:
        return XeroTaxError(
            message=error_message,
            tax_type=error_data.get('TaxType')
        )
    
    elif status_code in [401, 403]:
        return XeroAuthenticationError(
            message=error_message,
            error_code=str(status_code)
        )
    
    elif status_code == 429:
        return XeroRateLimitError(
            message=error_message,
            retry_after=error_data.get('RetryAfter')
        )
    
    elif status_code in [404, 410]:
        return XeroDataError(
            message=error_message,
            endpoint=error_data.get('Endpoint')
        )
    
    elif status_code in [500, 502, 503, 504]:
        return XeroConnectionError(
            message=error_message,
            status_code=status_code
        )
    
    else:
        # Default to general data error
        return XeroDataError(
            message=error_message,
            error_details=error_data
        )


def handle_xero_api_error(response_data: Dict[str, Any], endpoint: str = "") -> None:
    """
    Handle Xero API error response and raise appropriate exception.
    
    Args:
        response_data: Xero API error response
        endpoint: API endpoint that caused the error
        
    Raises:
        Appropriate Xero exception based on error type
    """
    # Xero API error structure can vary
    if 'ErrorNumber' in response_data or 'Type' in response_data:
        # Single error
        error_data = response_data
        error_data['Endpoint'] = endpoint
        raise create_xero_exception(error_data, f"Xero API error at {endpoint}")
    
    elif 'Elements' in response_data:
        # Multiple errors in Elements array
        elements = response_data.get('Elements', [])
        if elements and 'ValidationErrors' in elements[0]:
            # Validation errors
            validation_errors = []
            for element in elements:
                validation_errors.extend(element.get('ValidationErrors', []))
            
            error_message = f"Validation failed for {endpoint}"
            if validation_errors:
                error_details = validation_errors[0]
                error_message = error_details.get('Message', error_message)
            
            raise XeroValidationError(
                message=error_message,
                validation_errors=validation_errors
            )
    
    elif 'Detail' in response_data:
        # Generic error with detail
        raise XeroDataError(
            message=response_data['Detail'],
            endpoint=endpoint
        )
    
    else:
        # Unknown error format
        raise XeroConnectionError(
            message=f"Unknown error format from Xero API: {response_data}",
            response_data=response_data
        )


class XeroErrorHandler:
    """
    Centralized error handling for Xero API operations.
    """
    
    @staticmethod
    def is_retryable_error(exception: Exception) -> bool:
        """
        Determine if an error is retryable.
        
        Args:
            exception: Exception to check
            
        Returns:
            True if error is retryable
        """
        if isinstance(exception, XeroRateLimitError):
            return not exception.daily_limit_exceeded
        
        if isinstance(exception, XeroConnectionError):
            # Retry on server errors but not client errors
            return exception.status_code and exception.status_code >= 500
        
        return False
    
    @staticmethod
    def get_retry_delay(exception: Exception) -> int:
        """
        Get recommended retry delay in seconds.
        
        Args:
            exception: Exception to get delay for
            
        Returns:
            Delay in seconds
        """
        if isinstance(exception, XeroRateLimitError):
            return exception.retry_after or 60
        
        if isinstance(exception, XeroConnectionError):
            return 5  # 5 second delay for connection errors
        
        return 1  # Default 1 second delay
    
    @staticmethod
    def format_error_message(exception: Exception) -> str:
        """
        Format exception into user-friendly error message.
        
        Args:
            exception: Exception to format
            
        Returns:
            Formatted error message
        """
        if isinstance(exception, XeroAuthenticationError):
            return f"Xero authentication failed: {str(exception)}"
        
        elif isinstance(exception, XeroRateLimitError):
            if exception.daily_limit_exceeded:
                return "Xero daily API limit exceeded. Please try again tomorrow."
            else:
                return f"Xero rate limit exceeded. Please wait {exception.retry_after or 60} seconds."
        
        elif isinstance(exception, XeroValidationError):
            if exception.validation_errors:
                errors = []
                for error in exception.validation_errors[:3]:  # Show max 3 errors
                    errors.append(error.get('Message', str(error)))
                return f"Xero validation failed: {'; '.join(errors)}"
            else:
                return f"Xero validation failed: {str(exception)}"
        
        elif isinstance(exception, XeroOrganisationError):
            return f"Xero organisation error: {str(exception)}"
        
        elif isinstance(exception, XeroConnectionError):
            return f"Xero connection error: {str(exception)}"
        
        else:
            return f"Xero error: {str(exception)}"