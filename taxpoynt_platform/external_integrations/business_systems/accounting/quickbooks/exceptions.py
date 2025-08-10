"""
QuickBooks Accounting Exception Classes
Custom exceptions for QuickBooks accounting platform integration errors.
"""
from typing import Optional, Dict, Any

from ....connector_framework.base_accounting_connector import (
    AccountingConnectionError,
    AccountingAuthenticationError,
    AccountingDataError,
    AccountingValidationError,
    AccountingTransformationError
)


class QuickBooksConnectionError(AccountingConnectionError):
    """Raised when QuickBooks connection fails."""
    
    def __init__(self, message: str, company_id: Optional[str] = None, details: Optional[Dict[str, Any]] = None):
        super().__init__(message)
        self.company_id = company_id
        self.details = details or {}


class QuickBooksAuthenticationError(AccountingAuthenticationError):
    """Raised when QuickBooks API authentication fails."""
    
    def __init__(self, message: str, auth_type: Optional[str] = None, details: Optional[Dict[str, Any]] = None):
        super().__init__(message)
        self.auth_type = auth_type
        self.details = details or {}


class QuickBooksDataError(AccountingDataError):
    """Raised when QuickBooks data operations fail."""
    
    def __init__(self, message: str, resource_type: Optional[str] = None, details: Optional[Dict[str, Any]] = None):
        super().__init__(message)
        self.resource_type = resource_type
        self.details = details or {}


class QuickBooksValidationError(AccountingValidationError):
    """Raised when QuickBooks data validation fails."""
    
    def __init__(self, message: str, field_name: Optional[str] = None, details: Optional[Dict[str, Any]] = None):
        super().__init__(message)
        self.field_name = field_name
        self.details = details or {}


class QuickBooksTransformationError(AccountingTransformationError):
    """Raised when QuickBooks UBL transformation fails."""
    
    def __init__(self, message: str, transaction_id: Optional[str] = None, details: Optional[Dict[str, Any]] = None):
        super().__init__(message)
        self.transaction_id = transaction_id
        self.details = details or {}


class QuickBooksInvoiceNotFoundError(QuickBooksDataError):
    """Raised when a specific QuickBooks invoice is not found."""
    
    def __init__(self, invoice_id: str, details: Optional[Dict[str, Any]] = None):
        message = f"QuickBooks invoice not found: {invoice_id}"
        super().__init__(message, "invoice", details)
        self.invoice_id = invoice_id


class QuickBooksCustomerNotFoundError(QuickBooksDataError):
    """Raised when a specific QuickBooks customer is not found."""
    
    def __init__(self, customer_id: str, details: Optional[Dict[str, Any]] = None):
        message = f"QuickBooks customer not found: {customer_id}"
        super().__init__(message, "customer", details)
        self.customer_id = customer_id


class QuickBooksVendorNotFoundError(QuickBooksDataError):
    """Raised when a specific QuickBooks vendor is not found."""
    
    def __init__(self, vendor_id: str, details: Optional[Dict[str, Any]] = None):
        message = f"QuickBooks vendor not found: {vendor_id}"
        super().__init__(message, "vendor", details)
        self.vendor_id = vendor_id


class QuickBooksCompanyNotFoundError(QuickBooksConnectionError):
    """Raised when QuickBooks company is not found or inaccessible."""
    
    def __init__(self, company_id: str, details: Optional[Dict[str, Any]] = None):
        message = f"QuickBooks company not found or inaccessible: {company_id}"
        super().__init__(message, company_id, details)


class QuickBooksRateLimitError(QuickBooksConnectionError):
    """Raised when QuickBooks API rate limit is exceeded."""
    
    def __init__(
        self,
        message: str = "QuickBooks API rate limit exceeded",
        retry_after: Optional[int] = None,
        limit_type: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(message, details=details)
        self.retry_after = retry_after
        self.limit_type = limit_type  # 'per_app', 'per_company', etc.


class QuickBooksSandboxError(QuickBooksConnectionError):
    """Raised when QuickBooks Sandbox operations fail."""
    
    def __init__(
        self,
        message: str,
        sandbox_company_id: Optional[str] = None,
        operation: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(message, sandbox_company_id, details)
        self.operation = operation


class QuickBooksWebhookError(QuickBooksDataError):
    """Raised when QuickBooks webhook processing fails."""
    
    def __init__(
        self,
        message: str,
        event_type: Optional[str] = None,
        webhook_id: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(message, "webhook", details)
        self.event_type = event_type
        self.webhook_id = webhook_id


class QuickBooksPermissionError(QuickBooksAuthenticationError):
    """Raised when QuickBooks API permissions are insufficient."""
    
    def __init__(
        self,
        message: str,
        required_scope: Optional[str] = None,
        current_scopes: Optional[List[str]] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(message, "oauth2", details)
        self.required_scope = required_scope
        self.current_scopes = current_scopes or []


class QuickBooksReportError(QuickBooksDataError):
    """Raised when QuickBooks report generation fails."""
    
    def __init__(
        self,
        message: str,
        report_type: Optional[str] = None,
        report_params: Optional[Dict[str, Any]] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(message, "report", details)
        self.report_type = report_type
        self.report_params = report_params or {}


class QuickBooksBatchError(QuickBooksDataError):
    """Raised when QuickBooks batch operations fail."""
    
    def __init__(
        self,
        message: str,
        batch_id: Optional[str] = None,
        failed_operations: Optional[List[Dict[str, Any]]] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(message, "batch", details)
        self.batch_id = batch_id
        self.failed_operations = failed_operations or []


class QuickBooksAttachmentError(QuickBooksDataError):
    """Raised when QuickBooks attachment operations fail."""
    
    def __init__(
        self,
        message: str,
        attachment_id: Optional[str] = None,
        entity_id: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(message, "attachment", details)
        self.attachment_id = attachment_id
        self.entity_id = entity_id


# Error code mapping for QuickBooks API responses
QB_ERROR_CODE_MAPPING = {
    400: QuickBooksValidationError,
    401: QuickBooksAuthenticationError,
    403: QuickBooksPermissionError,
    404: QuickBooksDataError,
    429: QuickBooksRateLimitError,
    500: QuickBooksConnectionError,
    502: QuickBooksConnectionError,
    503: QuickBooksConnectionError,
    504: QuickBooksConnectionError
}


def map_quickbooks_error(
    status_code: int,
    message: str,
    response_data: Optional[Dict[str, Any]] = None,
    endpoint: Optional[str] = None
) -> Exception:
    """
    Map HTTP status codes and QuickBooks error responses to appropriate exception types.
    
    Args:
        status_code: HTTP status code
        message: Error message
        response_data: QuickBooks API response data
        endpoint: API endpoint that failed
        
    Returns:
        Appropriate QuickBooks exception instance
    """
    exception_class = QB_ERROR_CODE_MAPPING.get(status_code, QuickBooksConnectionError)
    
    # Parse QuickBooks-specific error details
    qb_errors = []
    if response_data and isinstance(response_data, dict):
        # QuickBooks API returns errors in various formats
        if 'Fault' in response_data:
            fault = response_data['Fault']
            if 'Error' in fault:
                errors = fault['Error'] if isinstance(fault['Error'], list) else [fault['Error']]
                for error in errors:
                    qb_errors.append({
                        'code': error.get('code'),
                        'detail': error.get('Detail'),
                        'element': error.get('element')
                    })
        elif 'errors' in response_data:
            errors = response_data['errors']
            if isinstance(errors, list):
                qb_errors = errors
    
    details = {
        'status_code': status_code,
        'endpoint': endpoint,
        'quickbooks_errors': qb_errors,
        'raw_response': response_data
    }
    
    # Create specific exception based on error type
    if exception_class == QuickBooksRateLimitError:
        retry_after = None
        if response_data:
            # QuickBooks rate limit headers
            retry_after = response_data.get('intuit_tid')  # Transaction ID for tracking
        
        return exception_class(
            message,
            retry_after=retry_after,
            details=details
        )
    elif exception_class == QuickBooksPermissionError:
        required_scope = None
        if qb_errors:
            for error in qb_errors:
                if 'scope' in str(error.get('detail', '')).lower():
                    required_scope = error.get('detail')
                    break
        
        return exception_class(
            message,
            required_scope=required_scope,
            details=details
        )
    else:
        return exception_class(message, details=details)


# QuickBooks-specific error patterns
QB_ERROR_PATTERNS = {
    'INVALID_TOKEN': QuickBooksAuthenticationError,
    'TOKEN_EXPIRED': QuickBooksAuthenticationError,
    'INSUFFICIENT_SCOPE': QuickBooksPermissionError,
    'COMPANY_NOT_FOUND': QuickBooksCompanyNotFoundError,
    'ENTITY_NOT_FOUND': QuickBooksDataError,
    'VALIDATION_ERROR': QuickBooksValidationError,
    'BUSINESS_VALIDATION_ERROR': QuickBooksValidationError,
    'STALE_OBJECT_ERROR': QuickBooksDataError,
    'DUPLICATE_DOCUMENT_NUMBER': QuickBooksValidationError,
    'REQUIRED_FIELD_MISSING': QuickBooksValidationError,
    'INVALID_REFERENCE': QuickBooksValidationError
}


def get_quickbooks_exception_for_error_code(error_code: str) -> type:
    """
    Get appropriate exception class for QuickBooks error code.
    
    Args:
        error_code: QuickBooks error code
        
    Returns:
        Exception class to raise
    """
    return QB_ERROR_PATTERNS.get(error_code, QuickBooksDataError)