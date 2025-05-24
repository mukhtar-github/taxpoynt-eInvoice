"""API key models for system integration.

This is a compatibility module that imports from api_keys.py.
All model definitions have been consolidated into api_keys.py.

Please import from app.models.api_keys directly in new code.
"""

# Import APIKey from the consolidated module
from app.models.api_keys import APIKey, APIKeyUsage

# Re-export for backward compatibility
__all__ = ['APIKey', 'APIKeyUsage']