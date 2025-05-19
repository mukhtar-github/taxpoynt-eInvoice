"""
FIRS API configuration settings.

This module provides dedicated settings for the FIRS API integration,
including configuration for both production and sandbox environments.
"""

from typing import Optional
from pydantic import BaseSettings, validator
import os
from app.core.config import settings

class FIRSSettings(BaseSettings):
    """
    FIRS API configuration settings.
    
    This class provides all the necessary configuration for connecting
    to the FIRS API, with support for both production and sandbox environments.
    """
    
    # Production API settings
    FIRS_API_URL: str = "https://api.firs.gov.ng"
    FIRS_API_KEY: Optional[str] = None
    FIRS_API_SECRET: Optional[str] = None
    
    # Sandbox API settings
    FIRS_SANDBOX_API_URL: str = "https://sandbox.firs.gov.ng/api"
    FIRS_SANDBOX_API_KEY: Optional[str] = None
    FIRS_SANDBOX_API_SECRET: Optional[str] = None
    
    # Environment control
    FIRS_USE_SANDBOX: bool = True
    
    # Submission configuration
    FIRS_SUBMISSION_TIMEOUT: int = 30
    FIRS_RETRY_ATTEMPTS: int = 3
    FIRS_MAX_BATCH_SIZE: int = 100
    
    @validator('FIRS_API_KEY', 'FIRS_API_SECRET', 'FIRS_SANDBOX_API_KEY', 'FIRS_SANDBOX_API_SECRET')
    def validate_api_credentials(cls, v):
        """
        Validate that API credentials are provided when needed.
        
        Note: This only validates structure, not that they are valid credentials.
        """
        if v is None:
            return ""  # Return empty string if None - will be caught at runtime
        return v
    
    class Config:
        """Pydantic configuration."""
        env_file = ".env"
        case_sensitive = True

# Create a global settings instance
firs_settings = FIRSSettings()

def get_active_firs_url() -> str:
    """
    Get the currently active FIRS API URL based on environment settings.
    
    Returns:
        str: The API URL to use (production or sandbox)
    """
    return firs_settings.FIRS_SANDBOX_API_URL if firs_settings.FIRS_USE_SANDBOX else firs_settings.FIRS_API_URL

def get_active_firs_credentials() -> tuple:
    """
    Get the currently active FIRS API credentials based on environment settings.
    
    Returns:
        tuple: (api_key, api_secret) for the active environment
    """
    if firs_settings.FIRS_USE_SANDBOX:
        return (firs_settings.FIRS_SANDBOX_API_KEY, firs_settings.FIRS_SANDBOX_API_SECRET)
    else:
        return (firs_settings.FIRS_API_KEY, firs_settings.FIRS_API_SECRET)
