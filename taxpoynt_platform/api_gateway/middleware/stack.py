"""
Middleware Stack Integration
===========================
Centralized middleware stack configuration and management for TaxPoynt API Gateway.
"""

import logging
from typing import List, Optional, Dict, Any
from fastapi import FastAPI
from starlette.middleware.base import BaseHTTPMiddleware

from .role_authenticator import RoleAuthenticatorMiddleware, AuthConfig
from .request_validator import RequestValidatorMiddleware, ValidationConfig
from .rate_limiter import RateLimiterMiddleware, RateLimitConfig
from .request_transformer import RequestTransformerMiddleware, TransformConfig
from .response_formatter import ResponseFormatterMiddleware, ResponseFormatConfig

logger = logging.getLogger(__name__)


class MiddlewareStackConfig:
    """Configuration for the complete middleware stack."""
    
    def __init__(self):
        self.auth_config = AuthConfig()
        self.validation_config = ValidationConfig()
        self.rate_limit_config = RateLimitConfig()
        self.transform_config = TransformConfig()
        self.response_format_config = ResponseFormatConfig()
        
        # Stack configuration
        self.enabled_middleware = [
            "response_formatter",  # Last - formats final response
            "request_transformer", # Transform request data
            "rate_limiter",        # Check rate limits
            "request_validator",   # Validate request
            "role_authenticator"   # First - authenticate user
        ]
        
        self.middleware_order = {
            "role_authenticator": 1,
            "request_validator": 2, 
            "rate_limiter": 3,
            "request_transformer": 4,
            "response_formatter": 5
        }


class MiddlewareStack:
    """Manages the complete middleware stack for the API Gateway."""
    
    def __init__(self, config: Optional[MiddlewareStackConfig] = None):
        self.config = config or MiddlewareStackConfig()
        self.middleware_instances = {}
        self.metrics = {
            "requests_processed": 0,
            "authentication_failures": 0,
            "validation_failures": 0,
            "rate_limit_violations": 0,
            "transformation_errors": 0,
            "formatting_errors": 0
        }
        
    def setup_middleware(self, app: FastAPI) -> None:
        """Setup all middleware in the correct order."""
        logger.info("Setting up TaxPoynt API Gateway middleware stack")
        
        # Create middleware instances
        self._create_middleware_instances()
        
        # Add middleware to FastAPI app in reverse order (last added = first executed)
        middleware_to_add = []
        
        for middleware_name in self.config.enabled_middleware:
            if middleware_name in self.middleware_instances:
                middleware_to_add.append((middleware_name, self.middleware_instances[middleware_name]))
        
        # Sort by reverse order (higher numbers first)
        middleware_to_add.sort(key=lambda x: self.config.middleware_order.get(x[0], 999), reverse=True)
        
        # Add to FastAPI app
        for name, middleware in middleware_to_add:
            logger.info(f"Adding {name} middleware to stack")
            app.add_middleware(type(middleware), **self._get_middleware_kwargs(name))
            
        logger.info(f"Middleware stack setup complete with {len(middleware_to_add)} middleware components")
    
    def _create_middleware_instances(self) -> None:
        """Create instances of all middleware components."""
        
        # Role Authenticator
        if "role_authenticator" in self.config.enabled_middleware:
            self.middleware_instances["role_authenticator"] = RoleAuthenticatorMiddleware
            
        # Request Validator
        if "request_validator" in self.config.enabled_middleware:
            self.middleware_instances["request_validator"] = RequestValidatorMiddleware
            
        # Rate Limiter
        if "rate_limiter" in self.config.enabled_middleware:
            self.middleware_instances["rate_limiter"] = RateLimiterMiddleware
            
        # Request Transformer
        if "request_transformer" in self.config.enabled_middleware:
            self.middleware_instances["request_transformer"] = RequestTransformerMiddleware
            
        # Response Formatter
        if "response_formatter" in self.config.enabled_middleware:
            self.middleware_instances["response_formatter"] = ResponseFormatterMiddleware
    
    def _get_middleware_kwargs(self, middleware_name: str) -> Dict[str, Any]:
        """Get configuration kwargs for specific middleware."""
        kwargs = {}
        
        if middleware_name == "role_authenticator":
            kwargs["config"] = self.config.auth_config
        elif middleware_name == "request_validator":
            kwargs["config"] = self.config.validation_config
        elif middleware_name == "rate_limiter":
            kwargs["config"] = self.config.rate_limit_config
        elif middleware_name == "request_transformer":
            kwargs["config"] = self.config.transform_config
        elif middleware_name == "response_formatter":
            kwargs["config"] = self.config.response_format_config
            
        return kwargs
    
    def get_middleware_status(self) -> Dict[str, Any]:
        """Get status of all middleware components."""
        status = {
            "enabled_middleware": self.config.enabled_middleware,
            "total_middleware": len(self.middleware_instances),
            "metrics": self.metrics.copy(),
            "configurations": {
                "auth_enabled": "role_authenticator" in self.config.enabled_middleware,
                "validation_enabled": "request_validator" in self.config.enabled_middleware,
                "rate_limiting_enabled": "rate_limiter" in self.config.enabled_middleware,
                "transformation_enabled": "request_transformer" in self.config.enabled_middleware,
                "formatting_enabled": "response_formatter" in self.config.enabled_middleware
            }
        }
        
        return status
    
    def update_config(self, middleware_name: str, new_config: Any) -> bool:
        """Update configuration for specific middleware."""
        try:
            if middleware_name == "role_authenticator":
                self.config.auth_config = new_config
            elif middleware_name == "request_validator":
                self.config.validation_config = new_config
            elif middleware_name == "rate_limiter":
                self.config.rate_limit_config = new_config
            elif middleware_name == "request_transformer":
                self.config.transform_config = new_config
            elif middleware_name == "response_formatter":
                self.config.response_format_config = new_config
            else:
                logger.warning(f"Unknown middleware: {middleware_name}")
                return False
                
            logger.info(f"Updated configuration for {middleware_name}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to update {middleware_name} config: {e}")
            return False
    
    def enable_middleware(self, middleware_name: str) -> bool:
        """Enable specific middleware."""
        if middleware_name not in self.config.enabled_middleware:
            self.config.enabled_middleware.append(middleware_name)
            logger.info(f"Enabled {middleware_name} middleware")
            return True
        return False
    
    def disable_middleware(self, middleware_name: str) -> bool:
        """Disable specific middleware."""
        if middleware_name in self.config.enabled_middleware:
            self.config.enabled_middleware.remove(middleware_name)
            logger.info(f"Disabled {middleware_name} middleware")
            return True
        return False


def create_default_middleware_stack() -> MiddlewareStack:
    """Create a middleware stack with default configuration."""
    config = MiddlewareStackConfig()
    
    # Customize default settings if needed
    config.auth_config.require_authentication = True
    config.validation_config.strict_validation = True
    config.rate_limit_config.default_requests_per_minute = 1000
    
    return MiddlewareStack(config)


def setup_production_middleware(app: FastAPI) -> MiddlewareStack:
    """Setup middleware stack optimized for production."""
    stack = create_default_middleware_stack()
    
    # Production-specific configurations
    stack.config.auth_config.jwt_secret_key = "your-production-secret"
    stack.config.rate_limit_config.default_requests_per_minute = 500
    stack.config.validation_config.strict_validation = True
    
    # Setup middleware
    stack.setup_middleware(app)
    
    logger.info("Production middleware stack configured")
    return stack


def setup_development_middleware(app: FastAPI) -> MiddlewareStack:
    """Setup middleware stack optimized for development."""
    stack = create_default_middleware_stack()
    
    # Development-specific configurations
    stack.config.auth_config.require_authentication = False
    stack.config.rate_limit_config.default_requests_per_minute = 10000
    stack.config.validation_config.strict_validation = False
    
    # Setup middleware
    stack.setup_middleware(app)
    
    logger.info("Development middleware stack configured")
    return stack


# Export main components
__all__ = [
    "MiddlewareStack",
    "MiddlewareStackConfig", 
    "create_default_middleware_stack",
    "setup_production_middleware",
    "setup_development_middleware"
]