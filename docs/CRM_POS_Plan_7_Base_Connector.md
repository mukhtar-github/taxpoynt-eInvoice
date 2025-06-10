# TaxPoynt CRM & POS Integration - Base Connector Implementation

This document provides technical details and code samples for implementing the base connector classes that will be used for all CRM and POS integrations.

## Base Connector Class

The base connector class provides foundational functionality for all integration types:

```python
# /backend/app/integrations/base/connector.py
from typing import Dict, Any, Optional
import logging
from datetime import datetime
from app.schemas.integration import IntegrationTestResult

class BaseConnector:
    """Base class for all external system connectors"""
    
    def __init__(self, connection_config: Dict[str, Any]):
        """
        Initialize the base connector with connection configuration.
        
        Args:
            connection_config: Dictionary containing connection parameters
        """
        self.config = connection_config
        self.logger = logging.getLogger(f"{self.__class__.__name__}")
        self.last_connected_at = None
        
    async def authenticate(self) -> bool:
        """
        Authenticate with the external system.
        
        Returns:
            bool: True if authentication was successful
        
        Raises:
            NotImplementedError: Must be implemented by subclasses
        """
        raise NotImplementedError("Must be implemented by subclasses")
        
    async def test_connection(self) -> IntegrationTestResult:
        """
        Test connection to external system.
        
        Returns:
            IntegrationTestResult: Object containing test results
        """
        try:
            await self.authenticate()
            self.last_connected_at = datetime.now()
            return IntegrationTestResult(
                success=True,
                message="Connection successful",
                details={
                    "connected_at": self.last_connected_at.isoformat(),
                    "platform": self.config.get("platform_name", "Unknown")
                }
            )
        except Exception as e:
            self.logger.error(f"Connection test failed: {str(e)}", exc_info=True)
            return IntegrationTestResult(
                success=False,
                message=f"Connection failed: {str(e)}",
                details={
                    "error_type": e.__class__.__name__,
                    "error_details": str(e)
                }
            )
    
    async def health_check(self) -> Dict[str, Any]:
        """
        Perform a health check of the connection.
        
        Returns:
            Dict: Health status information
        """
        try:
            test_result = await self.test_connection()
            return {
                "status": "healthy" if test_result.success else "unhealthy",
                "last_checked": datetime.now().isoformat(),
                "details": test_result.details,
                "message": test_result.message
            }
        except Exception as e:
            self.logger.error(f"Health check failed: {str(e)}", exc_info=True)
            return {
                "status": "error",
                "last_checked": datetime.now().isoformat(),
                "error": str(e),
                "error_type": e.__class__.__name__
            }
```

## Secure Credential Management

Secure credential storage and management:

```python
# /backend/app/integrations/base/credential_manager.py
from cryptography.fernet import Fernet
from app.core.config import settings
import json
from typing import Dict, Any, Optional
import base64

class SecureCredentialManager:
    """Secure manager for integration credentials"""
    
    def __init__(self):
        """Initialize with encryption key"""
        self.key = base64.urlsafe_b64decode(settings.CREDENTIAL_ENCRYPTION_KEY)
        self.cipher_suite = Fernet(settings.CREDENTIAL_ENCRYPTION_KEY)
        
    def encrypt_credentials(self, credentials: Dict[str, Any]) -> str:
        """
        Encrypt credentials for secure storage.
        
        Args:
            credentials: Dictionary of credential information
            
        Returns:
            str: Encrypted credentials string
        """
        if not credentials:
            return ""
            
        # Convert to JSON string
        credentials_json = json.dumps(credentials)
        
        # Encrypt
        encrypted_data = self.cipher_suite.encrypt(credentials_json.encode('utf-8'))
        
        return encrypted_data.decode('utf-8')
        
    def decrypt_credentials(self, encrypted_data: str) -> Dict[str, Any]:
        """
        Decrypt credentials for use.
        
        Args:
            encrypted_data: Encrypted credentials string
            
        Returns:
            Dict: Decrypted credentials dictionary
        """
        if not encrypted_data:
            return {}
            
        # Decrypt
        decrypted_data = self.cipher_suite.decrypt(encrypted_data.encode('utf-8'))
        
        # Convert from JSON
        return json.loads(decrypted_data.decode('utf-8'))
```

## Error Handling and Retry Logic

Centralized error handling with retry capabilities:

```python
# /backend/app/integrations/base/error_handler.py
import asyncio
from typing import Callable, Any, Dict, Optional
import logging
from functools import wraps

logger = logging.getLogger(__name__)

class IntegrationError(Exception):
    """Base exception for all integration errors"""
    pass

class AuthenticationError(IntegrationError):
    """Error during authentication"""
    pass

class RateLimitError(IntegrationError):
    """API rate limit exceeded"""
    pass

class ConnectionError(IntegrationError):
    """Connection to external system failed"""
    pass

def with_retry(
    max_retries: int = 3,
    base_delay: float = 0.5,
    backoff_factor: float = 2,
    retry_on: tuple = (ConnectionError, RateLimitError)
):
    """
    Decorator for functions that should be retried on failure.
    
    Args:
        max_retries: Maximum number of retry attempts
        base_delay: Initial delay between retries in seconds
        backoff_factor: Multiplier for delay on each retry
        retry_on: Tuple of exception types that should trigger a retry
    """
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            retries = 0
            delay = base_delay
            
            while True:
                try:
                    return await func(*args, **kwargs)
                except retry_on as e:
                    retries += 1
                    if retries > max_retries:
                        logger.error(f"Max retries ({max_retries}) exceeded for {func.__name__}")
                        raise
                        
                    # Calculate next delay with exponential backoff
                    delay = base_delay * (backoff_factor ** (retries - 1))
                    
                    logger.warning(
                        f"Retry {retries}/{max_retries} for {func.__name__} "
                        f"after error: {str(e)}. Waiting {delay}s"
                    )
                    
                    # Wait before retry
                    await asyncio.sleep(delay)
                except Exception:
                    # Don't retry other exceptions
                    raise
                    
        return wrapper
    return decorator
```

## Implementation Usage Example

Example of implementing a concrete connector using the base classes:

```python
# Example usage in a concrete connector
from app.integrations.base.connector import BaseConnector
from app.integrations.base.error_handler import with_retry, ConnectionError

class ConcreteConnector(BaseConnector):
    """Concrete implementation of a connector"""
    
    async def authenticate(self):
        """Authenticate with external system"""
        # Implementation
        
    @with_retry(max_retries=3, base_delay=1.0)
    async def fetch_data(self, resource_id):
        """Fetch data with automatic retry"""
        # Implementation that might fail and be retried
```

This foundation provides a solid base for creating specific CRM and POS connectors while ensuring consistent error handling, authentication, and monitoring across all integration types.
