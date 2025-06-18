"""
Base connector class for all external system integrations.

This module provides the foundation for all integration connectors in the TaxPoynt platform,
including CRM, POS, and ERP systems. It implements common functionality like authentication,
connection testing, error handling, and monitoring.
"""

import logging
from datetime import datetime
from typing import Dict, Any, Optional, Union

from pydantic import BaseModel


class IntegrationTestResult(BaseModel):
    """Model for integration connection test results."""
    success: bool
    message: str
    details: Optional[Dict[str, Any]] = None


class BaseConnector:
    """Base class for all external system connectors."""
    
    def __init__(self, connection_config: Dict[str, Any]):
        """
        Initialize the base connector with configuration.
        
        Args:
            connection_config: Dictionary containing connection parameters
        """
        self.config = connection_config
        self.logger = logging.getLogger(f"{self.__class__.__name__}")
        self.name = self.__class__.__name__
        self._authenticated = False
        self._last_auth_time = None
        self._connection_id = connection_config.get("connection_id")
        
    async def authenticate(self) -> Dict[str, Any]:
        """
        Authenticate with the external system.
        
        Returns:
            Dict containing authentication results
            
        Raises:
            NotImplementedError: Must be implemented by subclasses
        """
        raise NotImplementedError("Must be implemented by subclasses")
    
    async def test_connection(self) -> IntegrationTestResult:
        """
        Test connection to the external system.
        
        Returns:
            IntegrationTestResult with connection status
        """
        try:
            await self.authenticate()
            self._authenticated = True
            self._last_auth_time = datetime.now()
            return IntegrationTestResult(
                success=True,
                message="Connection successful",
                details={
                    "connected_at": self._last_auth_time.isoformat(),
                    "connector_name": self.name,
                    "connection_id": self._connection_id
                }
            )
        except Exception as e:
            self.logger.error(f"Connection test failed: {str(e)}", exc_info=True)
            self._authenticated = False
            return IntegrationTestResult(
                success=False,
                message=f"Connection failed: {str(e)}",
                details={
                    "error_type": e.__class__.__name__,
                    "connector_name": self.name,
                    "connection_id": self._connection_id
                }
            )
    
    async def health_check(self) -> IntegrationTestResult:
        """
        Check the health of the integration.
        
        Returns:
            IntegrationTestResult with health status
        """
        return await self.test_connection()
    
    def is_authenticated(self) -> bool:
        """
        Check if the connector is currently authenticated.
        
        Returns:
            bool: True if authenticated, False otherwise
        """
        return self._authenticated
    
    async def execute_with_retry(self, operation_func, max_retries: int = 3) -> Any:
        """
        Execute an operation with retry logic.
        
        Args:
            operation_func: Async function to execute
            max_retries: Maximum number of retry attempts
            
        Returns:
            Result of the operation function
            
        Raises:
            Exception: If all retry attempts fail
        """
        retries = 0
        last_error = None
        
        while retries <= max_retries:
            try:
                if not self.is_authenticated() and retries > 0:
                    self.logger.info("Re-authenticating before retry")
                    await self.authenticate()
                
                return await operation_func()
            except Exception as e:
                retries += 1
                last_error = e
                self.logger.warning(
                    f"Operation failed (attempt {retries}/{max_retries}): {str(e)}"
                )
                
                if retries <= max_retries:
                    # Exponential backoff could be implemented here
                    continue
                else:
                    self.logger.error(f"Operation failed after {max_retries} attempts")
                    raise last_error
    
    def get_connector_info(self) -> Dict[str, Any]:
        """
        Get information about this connector instance.
        
        Returns:
            Dict with connector metadata
        """
        return {
            "name": self.name,
            "connection_id": self._connection_id,
            "authenticated": self._authenticated,
            "last_auth_time": self._last_auth_time.isoformat() if self._last_auth_time else None
        }
