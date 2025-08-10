"""
Sage Accounting Exception Classes
Custom exceptions for Sage Business Cloud Accounting integration errors.
"""
from typing import Optional, Dict, Any
from ....connector_framework.base_accounting_connector import (
    AccountingConnectionError,
    AccountingAuthenticationError,
    AccountingDataError,
    AccountingValidationError,
    AccountingTransformationError
)


class SageConnectionError(AccountingConnectionError):
    """Sage connection and network related errors."""
    
    def __init__(self, message: str, status_code: Optional[int] = None, response_data: Optional[Dict[str, Any]] = None):
        super().__init__(message)
        self.status_code = status_code
        self.response_data = response_data or {}
        self.platform = "Sage Business Cloud Accounting"


class SageAuthenticationError(AccountingAuthenticationError):
    """Sage authentication and authorization errors."""
    
    def __init__(self, message: str, auth_type: Optional[str] = None, error_code: Optional[str] = None):
        super().__init__(message)
        self.auth_type = auth_type
        self.error_code = error_code
        self.platform = "Sage Business Cloud Accounting"


class SageRateLimitError(SageConnectionError):
    """Sage API rate limiting errors."""
    
    def __init__(self, message: str, retry_after: Optional[int] = None, quota_exceeded: bool = False):
        super().__init__(message)
        self.retry_after = retry_after
        self.quota_exceeded = quota_exceeded
        self.error_type = "rate_limit"


class SageDataError(AccountingDataError):
    """Sage data retrieval and processing errors."""
    
    def __init__(self, message: str, endpoint: Optional[str] = None, error_details: Optional[Dict[str, Any]] = None):
        super().__init__(message)
        self.endpoint = endpoint
        self.error_details = error_details or {}
        self.platform = "Sage Business Cloud Accounting"


class SageValidationError(AccountingValidationError):
    """Sage data validation and business rule errors."""
    
    def __init__(self, message: str, validation_errors: Optional[list] = None, field_name: Optional[str] = None):
        super().__init__(message)
        self.validation_errors = validation_errors or []
        self.field_name = field_name
        self.platform = "Sage Business Cloud Accounting"


class SageTransformationError(AccountingTransformationError):
    """Sage to UBL transformation errors."""
    
    def __init__(self, message: str, source_data: Optional[Dict[str, Any]] = None, transformation_stage: Optional[str] = None):
        super().__init__(message)
        self.source_data = source_data or {}
        self.transformation_stage = transformation_stage
        self.platform = "Sage Business Cloud Accounting"


class SageWebhookError(SageConnectionError):
    """Sage webhook processing errors."""
    
    def __init__(self, message: str, webhook_id: Optional[str] = None, event_type: Optional[str] = None):
        super().__init__(message)
        self.webhook_id = webhook_id
        self.event_type = event_type
        self.error_type = "webhook"


class SageBusinessError(SageDataError):
    """Sage business (company) related errors."""
    
    def __init__(self, message: str, business_id: Optional[str] = None, business_name: Optional[str] = None):
        super().__init__(message)
        self.business_id = business_id
        self.business_name = business_name
        self.error_type = "business"


class SageInvoiceError(SageValidationError):
    """Sage invoice specific errors."""
    
    def __init__(self, message: str, invoice_id: Optional[str] = None, invoice_number: Optional[str] = None):
        super().__init__(message)
        self.invoice_id = invoice_id
        self.invoice_number = invoice_number
        self.error_type = "invoice"


class SageContactError(SageValidationError):
    """Sage contact (customer/supplier) specific errors."""
    
    def __init__(self, message: str, contact_id: Optional[str] = None, contact_name: Optional[str] = None):
        super().__init__(message)
        self.contact_id = contact_id
        self.contact_name = contact_name
        self.error_type = "contact"


class SageLedgerAccountError(SageValidationError):
    """Sage ledger account specific errors."""
    
    def __init__(self, message: str, account_id: Optional[str] = None, account_code: Optional[str] = None):
        super().__init__(message)
        self.account_id = account_id
        self.account_code = account_code
        self.error_type = "ledger_account"


class SageTaxRateError(SageValidationError):
    """Sage tax rate calculation and validation errors."""
    
    def __init__(self, message: str, tax_rate_id: Optional[str] = None, tax_percentage: Optional[float] = None):
        super().__init__(message)
        self.tax_rate_id = tax_rate_id
        self.tax_percentage = tax_percentage
        self.error_type = "tax_rate"


class SageProductError(SageValidationError):
    """Sage product/service specific errors."""
    
    def __init__(self, message: str, product_id: Optional[str] = None, product_code: Optional[str] = None):
        super().__init__(message)
        self.product_id = product_id
        self.product_code = product_code
        self.error_type = "product"


def create_sage_exception(error_data: Dict[str, Any], context: Optional[str] = None) -> Exception:
    """
    Factory function to create appropriate Sage exception from API error response.
    
    Args:
        error_data: Error data from Sage API response
        context: Additional context about where the error occurred
        
    Returns:
        Appropriate Sage exception instance
    """
    # Extract common error information
    error_message = error_data.get('message', error_data.get('error_description', 'Unknown Sage error'))
    error_code = error_data.get('error', error_data.get('error_code', ''))
    status_code = error_data.get('status_code')
    
    # Add context to message if provided
    if context:
        error_message = f"{context}: {error_message}"
    
    # Map Sage error codes to exception classes
    if error_code in ['invalid_token', 'expired_token', 'unauthorized']:
        return SageAuthenticationError(
            message=error_message,
            error_code=error_code
        )
    
    elif error_code in ['rate_limit_exceeded', 'quota_exceeded']:
        return SageRateLimitError(
            message=error_message,
            retry_after=error_data.get('retry_after'),
            quota_exceeded=error_code == 'quota_exceeded'
        )
    
    elif error_code in ['validation_failed', 'invalid_request']:
        validation_errors = error_data.get('errors', [])
        return SageValidationError(
            message=error_message,
            validation_errors=validation_errors
        )
    
    elif error_code in ['business_not_found', 'invalid_business']:
        return SageBusinessError(
            message=error_message,
            business_id=error_data.get('business_id')
        )
    
    elif error_code in ['invoice_not_found', 'invalid_invoice']:
        return SageInvoiceError(
            message=error_message,
            invoice_id=error_data.get('invoice_id')
        )
    
    elif error_code in ['contact_not_found', 'invalid_contact']:
        return SageContactError(
            message=error_message,
            contact_id=error_data.get('contact_id')
        )
    
    elif error_code in ['account_not_found', 'invalid_account']:
        return SageLedgerAccountError(
            message=error_message,
            account_id=error_data.get('account_id')
        )
    
    elif error_code in ['product_not_found', 'invalid_product']:
        return SageProductError(
            message=error_message,
            product_id=error_data.get('product_id')
        )
    
    elif status_code in [401, 403]:
        return SageAuthenticationError(
            message=error_message,
            error_code=str(status_code)
        )
    
    elif status_code == 429:
        return SageRateLimitError(
            message=error_message,
            retry_after=error_data.get('retry_after')
        )
    
    elif status_code in [400, 422]:
        return SageValidationError(
            message=error_message,
            validation_errors=error_data.get('errors', [])
        )
    
    elif status_code in [404, 410]:
        return SageDataError(
            message=error_message,
            endpoint=error_data.get('endpoint')
        )
    
    elif status_code in [500, 502, 503, 504]:
        return SageConnectionError(
            message=error_message,
            status_code=status_code
        )
    
    else:
        # Default to general data error
        return SageDataError(
            message=error_message,
            error_details=error_data
        )


def handle_sage_api_error(response_data: Dict[str, Any], endpoint: str = "") -> None:
    """
    Handle Sage API error response and raise appropriate exception.
    
    Args:
        response_data: Sage API error response
        endpoint: API endpoint that caused the error
        
    Raises:
        Appropriate Sage exception based on error type
    """
    # Sage API error structure
    if 'error' in response_data or 'message' in response_data:
        # Single error
        error_data = response_data.copy()
        error_data['endpoint'] = endpoint
        raise create_sage_exception(error_data, f"Sage API error at {endpoint}")
    
    elif 'errors' in response_data:
        # Multiple validation errors
        errors = response_data.get('errors', [])
        
        if errors:
            # Use first error as primary, include all in validation_errors
            primary_error = errors[0] if isinstance(errors[0], dict) else {'message': str(errors[0])}
            error_message = primary_error.get('message', f"Validation failed for {endpoint}")
            
            raise SageValidationError(
                message=error_message,
                validation_errors=errors
            )
        else:
            raise SageValidationError(
                message=f"Validation failed for {endpoint}",
                validation_errors=[]
            )
    
    elif 'error_description' in response_data:
        # OAuth or authentication error
        raise SageAuthenticationError(
            message=response_data['error_description'],
            error_code=response_data.get('error')
        )
    
    else:
        # Unknown error format
        raise SageConnectionError(
            message=f"Unknown error format from Sage API: {response_data}",
            response_data=response_data
        )


class SageErrorHandler:
    """
    Centralized error handling for Sage API operations.
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
        if isinstance(exception, SageRateLimitError):
            return not exception.quota_exceeded
        
        if isinstance(exception, SageConnectionError):
            # Retry on server errors but not client errors
            return exception.status_code and exception.status_code >= 500
        
        # Retry on network-related authentication errors (token might be refreshable)
        if isinstance(exception, SageAuthenticationError):
            return exception.error_code in ['expired_token', 'invalid_token']
        
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
        if isinstance(exception, SageRateLimitError):
            return exception.retry_after or 60
        
        if isinstance(exception, SageConnectionError):
            return 5  # 5 second delay for connection errors
        
        if isinstance(exception, SageAuthenticationError):
            return 2  # 2 second delay for auth errors (token refresh)
        
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
        if isinstance(exception, SageAuthenticationError):
            return f"Sage authentication failed: {str(exception)}"
        
        elif isinstance(exception, SageRateLimitError):
            if exception.quota_exceeded:
                return "Sage API quota exceeded. Please contact your Sage administrator."
            else:
                return f"Sage rate limit exceeded. Please wait {exception.retry_after or 60} seconds."
        
        elif isinstance(exception, SageValidationError):
            if exception.validation_errors:
                errors = []
                for error in exception.validation_errors[:3]:  # Show max 3 errors
                    if isinstance(error, dict):
                        errors.append(error.get('message', str(error)))
                    else:
                        errors.append(str(error))
                return f"Sage validation failed: {'; '.join(errors)}"
            else:
                return f"Sage validation failed: {str(exception)}"
        
        elif isinstance(exception, SageBusinessError):
            return f"Sage business error: {str(exception)}"
        
        elif isinstance(exception, SageInvoiceError):
            return f"Sage invoice error: {str(exception)}"
        
        elif isinstance(exception, SageContactError):
            return f"Sage contact error: {str(exception)}"
        
        elif isinstance(exception, SageLedgerAccountError):
            return f"Sage account error: {str(exception)}"
        
        elif isinstance(exception, SageProductError):
            return f"Sage product error: {str(exception)}"
        
        elif isinstance(exception, SageConnectionError):
            return f"Sage connection error: {str(exception)}"
        
        else:
            return f"Sage error: {str(exception)}"
    
    @staticmethod
    def extract_validation_details(exception: SageValidationError) -> Dict[str, Any]:
        """
        Extract detailed validation error information.
        
        Args:
            exception: Sage validation exception
            
        Returns:
            Detailed validation error information
        """
        details = {
            'field_name': exception.field_name,
            'primary_message': str(exception),
            'validation_errors': [],
            'error_count': len(exception.validation_errors)
        }
        
        for error in exception.validation_errors:
            if isinstance(error, dict):
                details['validation_errors'].append({
                    'field': error.get('field', 'unknown'),
                    'message': error.get('message', 'Unknown validation error'),
                    'code': error.get('code', ''),
                    'value': error.get('value', '')
                })
            else:
                details['validation_errors'].append({
                    'field': 'unknown',
                    'message': str(error),
                    'code': '',
                    'value': ''
                })
        
        return details
    
    @staticmethod
    def should_refresh_token(exception: Exception) -> bool:
        """
        Determine if token refresh should be attempted.
        
        Args:
            exception: Exception to check
            
        Returns:
            True if token refresh should be attempted
        """
        if isinstance(exception, SageAuthenticationError):
            return exception.error_code in ['expired_token', 'invalid_token']
        
        if isinstance(exception, SageConnectionError):
            return exception.status_code == 401
        
        return False