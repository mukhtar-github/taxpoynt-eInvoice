"""
Role-Based Response Formatter Middleware
=======================================
FastAPI middleware for formatting responses based on role-specific requirements.
Provides response transformation, data filtering, and role-specific formatting.
"""

import logging
import json
import time
from typing import Dict, Any, List, Optional, Union, Callable
from datetime import datetime, timezone
from fastapi import Request, Response
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
import asyncio

from core_platform.authentication.role_manager import PlatformRole
from core_platform.authentication.models import UserRole


logger = logging.getLogger(__name__)


class ResponseFormatConfig:
    """Configuration for response formatting rules."""
    
    def __init__(self):
        self.role_formats = {
            PlatformRole.ADMIN: {
                "include_debug": True,
                "include_metadata": True,
                "include_performance": True,
                "include_system_info": True,
                "max_depth": None,
                "sensitive_fields": [],
                "compression": False
            },
            PlatformRole.DEVELOPER: {
                "include_debug": True,
                "include_metadata": True,
                "include_performance": True,
                "include_system_info": False,
                "max_depth": 10,
                "sensitive_fields": ["password", "secret", "key"],
                "compression": False
            },
            PlatformRole.OPERATIONS: {
                "include_debug": False,
                "include_metadata": True,
                "include_performance": True,
                "include_system_info": False,
                "max_depth": 8,
                "sensitive_fields": ["password", "secret", "key", "token"],
                "compression": True
            },
            PlatformRole.BUSINESS_USER: {
                "include_debug": False,
                "include_metadata": False,
                "include_performance": False,
                "include_system_info": False,
                "max_depth": 5,
                "sensitive_fields": ["password", "secret", "key", "token", "internal_id"],
                "compression": True
            },
            PlatformRole.API_CLIENT: {
                "include_debug": False,
                "include_metadata": False,
                "include_performance": False,
                "include_system_info": False,
                "max_depth": 3,
                "sensitive_fields": ["password", "secret", "key", "token", "internal_id", "debug"],
                "compression": True
            },
            PlatformRole.GUEST: {
                "include_debug": False,
                "include_metadata": False,
                "include_performance": False,
                "include_system_info": False,
                "max_depth": 2,
                "sensitive_fields": ["password", "secret", "key", "token", "internal_id", "debug", "user_id"],
                "compression": True
            }
        }
        
        self.endpoint_formats = {
            "/api/v1/health": {"format": "minimal", "cache_ttl": 60},
            "/api/v1/auth": {"format": "secure", "cache_ttl": 0},
            "/api/v1/invoices": {"format": "business", "cache_ttl": 300},
            "/api/v1/admin": {"format": "full", "cache_ttl": 0},
            "/api/v1/integrations": {"format": "technical", "cache_ttl": 600}
        }


class ResponseMetrics:
    """Track response formatting metrics."""
    
    def __init__(self):
        self.format_times = {}
        self.compression_savings = {}
        self.filter_counts = {}
        
    def record_format_time(self, role: str, endpoint: str, duration: float):
        """Record formatting duration."""
        key = f"{role}:{endpoint}"
        if key not in self.format_times:
            self.format_times[key] = []
        self.format_times[key].append(duration)
        
    def record_compression(self, original_size: int, compressed_size: int):
        """Record compression savings."""
        savings = original_size - compressed_size
        self.compression_savings[datetime.now()] = {
            "original": original_size,
            "compressed": compressed_size,
            "savings": savings,
            "ratio": savings / original_size if original_size > 0 else 0
        }
        
    def record_filtering(self, role: str, fields_filtered: int):
        """Record field filtering counts."""
        if role not in self.filter_counts:
            self.filter_counts[role] = []
        self.filter_counts[role].append(fields_filtered)


class ResponseFormatter:
    """Core response formatting logic."""
    
    def __init__(self, config: ResponseFormatConfig):
        self.config = config
        self.metrics = ResponseMetrics()
        
    async def format_response(
        self,
        response_data: Any,
        role: PlatformRole,
        endpoint: str,
        request: Request,
        start_time: float
    ) -> Dict[str, Any]:
        """Format response according to role and endpoint requirements."""
        format_start = time.time()
        
        try:
            # Get formatting rules for role
            role_format = self.config.role_formats.get(role, self.config.role_formats[PlatformRole.GUEST])
            endpoint_format = self._get_endpoint_format(endpoint)
            
            # Create base response structure
            formatted_response = {
                "success": True,
                "data": response_data,
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
            
            # Apply role-specific formatting
            formatted_response = await self._apply_role_formatting(
                formatted_response, role_format, role, request
            )
            
            # Apply endpoint-specific formatting
            formatted_response = await self._apply_endpoint_formatting(
                formatted_response, endpoint_format, endpoint
            )
            
            # Add metadata if required
            if role_format["include_metadata"]:
                formatted_response["metadata"] = await self._generate_metadata(
                    request, endpoint, role
                )
            
            # Add performance data if required
            if role_format["include_performance"]:
                formatted_response["performance"] = {
                    "response_time_ms": round((time.time() - start_time) * 1000, 2),
                    "format_time_ms": round((time.time() - format_start) * 1000, 2)
                }
            
            # Add debug information if required
            if role_format["include_debug"]:
                formatted_response["debug"] = await self._generate_debug_info(
                    request, role, endpoint
                )
            
            # Filter sensitive fields
            formatted_response = await self._filter_sensitive_fields(
                formatted_response, role_format["sensitive_fields"]
            )
            
            # Apply depth limiting
            if role_format["max_depth"]:
                formatted_response = await self._limit_depth(
                    formatted_response, role_format["max_depth"]
                )
            
            # Record metrics
            self.metrics.record_format_time(
                role.value, endpoint, time.time() - format_start
            )
            
            return formatted_response
            
        except Exception as e:
            logger.error(f"Response formatting error: {e}")
            return {
                "success": False,
                "error": "Response formatting failed",
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
    
    def _get_endpoint_format(self, endpoint: str) -> Dict[str, Any]:
        """Get endpoint-specific formatting rules."""
        for pattern, format_config in self.config.endpoint_formats.items():
            if endpoint.startswith(pattern):
                return format_config
        return {"format": "standard", "cache_ttl": 300}
    
    async def _apply_role_formatting(
        self,
        response: Dict[str, Any],
        role_format: Dict[str, Any],
        role: PlatformRole,
        request: Request
    ) -> Dict[str, Any]:
        """Apply role-specific formatting rules."""
        
        # Add role-specific headers
        response["role_context"] = {
            "role": role.value,
            "permissions": await self._get_role_permissions(role),
            "access_level": self._get_access_level(role)
        }
        
        # Apply compression if required
        if role_format["compression"]:
            response = await self._apply_compression_hints(response)
        
        return response
    
    async def _apply_endpoint_formatting(
        self,
        response: Dict[str, Any],
        endpoint_format: Dict[str, Any],
        endpoint: str
    ) -> Dict[str, Any]:
        """Apply endpoint-specific formatting rules."""
        
        format_type = endpoint_format.get("format", "standard")
        
        if format_type == "minimal":
            response = await self._apply_minimal_format(response)
        elif format_type == "secure":
            response = await self._apply_secure_format(response)
        elif format_type == "business":
            response = await self._apply_business_format(response)
        elif format_type == "technical":
            response = await self._apply_technical_format(response)
        elif format_type == "full":
            response = await self._apply_full_format(response)
        
        # Add cache headers
        if "cache_ttl" in endpoint_format:
            response["cache_info"] = {
                "ttl": endpoint_format["cache_ttl"],
                "cacheable": endpoint_format["cache_ttl"] > 0
            }
        
        return response
    
    async def _generate_metadata(
        self,
        request: Request,
        endpoint: str,
        role: PlatformRole
    ) -> Dict[str, Any]:
        """Generate response metadata."""
        return {
            "endpoint": endpoint,
            "method": request.method,
            "role": role.value,
            "request_id": getattr(request.state, "request_id", None),
            "api_version": "v1",
            "server_time": datetime.now(timezone.utc).isoformat()
        }
    
    async def _generate_debug_info(
        self,
        request: Request,
        role: PlatformRole,
        endpoint: str
    ) -> Dict[str, Any]:
        """Generate debug information."""
        return {
            "request_headers": dict(request.headers),
            "query_params": dict(request.query_params),
            "path_params": getattr(request, "path_params", {}),
            "user_agent": request.headers.get("user-agent"),
            "client_ip": request.client.host if request.client else None,
            "processing_time": time.time(),
            "memory_usage": await self._get_memory_usage()
        }
    
    async def _filter_sensitive_fields(
        self,
        data: Any,
        sensitive_fields: List[str]
    ) -> Any:
        """Remove sensitive fields from response data."""
        if isinstance(data, dict):
            filtered = {}
            fields_filtered = 0
            
            for key, value in data.items():
                if any(sensitive in key.lower() for sensitive in sensitive_fields):
                    filtered[key] = "[FILTERED]"
                    fields_filtered += 1
                else:
                    filtered[key] = await self._filter_sensitive_fields(value, sensitive_fields)
            
            return filtered
            
        elif isinstance(data, list):
            return [
                await self._filter_sensitive_fields(item, sensitive_fields)
                for item in data
            ]
        
        return data
    
    async def _limit_depth(self, data: Any, max_depth: int, current_depth: int = 0) -> Any:
        """Limit response data depth."""
        if current_depth >= max_depth:
            if isinstance(data, (dict, list)):
                return "[MAX_DEPTH_REACHED]"
            return data
        
        if isinstance(data, dict):
            return {
                key: await self._limit_depth(value, max_depth, current_depth + 1)
                for key, value in data.items()
            }
        elif isinstance(data, list):
            return [
                await self._limit_depth(item, max_depth, current_depth + 1)
                for item in data
            ]
        
        return data
    
    async def _apply_minimal_format(self, response: Dict[str, Any]) -> Dict[str, Any]:
        """Apply minimal formatting (health checks, etc)."""
        return {
            "status": "ok" if response.get("success") else "error",
            "timestamp": response["timestamp"]
        }
    
    async def _apply_secure_format(self, response: Dict[str, Any]) -> Dict[str, Any]:
        """Apply secure formatting (auth endpoints)."""
        # Remove any debug info for security
        secure_response = {
            "success": response["success"],
            "timestamp": response["timestamp"]
        }
        
        if "data" in response:
            secure_response["data"] = response["data"]
        
        return secure_response
    
    async def _apply_business_format(self, response: Dict[str, Any]) -> Dict[str, Any]:
        """Apply business user formatting."""
        business_response = response.copy()
        
        # Add business-friendly formatting
        if "data" in business_response:
            business_response["data"] = await self._format_business_data(
                business_response["data"]
            )
        
        return business_response
    
    async def _apply_technical_format(self, response: Dict[str, Any]) -> Dict[str, Any]:
        """Apply technical formatting (integrations, etc)."""
        technical_response = response.copy()
        
        # Add technical details
        technical_response["technical_info"] = {
            "api_version": "v1",
            "response_format": "technical",
            "integration_ready": True
        }
        
        return technical_response
    
    async def _apply_full_format(self, response: Dict[str, Any]) -> Dict[str, Any]:
        """Apply full formatting (admin users)."""
        # Return complete response with all available information
        return response
    
    async def _apply_compression_hints(self, response: Dict[str, Any]) -> Dict[str, Any]:
        """Add compression hints for response."""
        response["compression"] = {
            "enabled": True,
            "algorithm": "gzip",
            "min_size": 1024
        }
        return response
    
    async def _get_role_permissions(self, role: PlatformRole) -> List[str]:
        """Get permissions for role."""
        # This would integrate with the role manager
        permission_map = {
            PlatformRole.ADMIN: ["read", "write", "delete", "admin"],
            PlatformRole.DEVELOPER: ["read", "write", "debug"],
            PlatformRole.OPERATIONS: ["read", "write", "monitor"],
            PlatformRole.BUSINESS_USER: ["read", "write"],
            PlatformRole.API_CLIENT: ["read"],
            PlatformRole.GUEST: ["read_public"]
        }
        return permission_map.get(role, [])
    
    def _get_access_level(self, role: PlatformRole) -> str:
        """Get access level for role."""
        level_map = {
            PlatformRole.ADMIN: "full",
            PlatformRole.DEVELOPER: "technical",
            PlatformRole.OPERATIONS: "operational",
            PlatformRole.BUSINESS_USER: "business",
            PlatformRole.API_CLIENT: "api",
            PlatformRole.GUEST: "public"
        }
        return level_map.get(role, "public")
    
    async def _format_business_data(self, data: Any) -> Any:
        """Format data for business users."""
        if isinstance(data, dict):
            # Convert technical fields to business-friendly names
            business_data = {}
            for key, value in data.items():
                business_key = self._get_business_friendly_key(key)
                business_data[business_key] = await self._format_business_data(value)
            return business_data
        elif isinstance(data, list):
            return [await self._format_business_data(item) for item in data]
        
        return data
    
    def _get_business_friendly_key(self, key: str) -> str:
        """Convert technical field names to business-friendly names."""
        mapping = {
            "id": "ID",
            "created_at": "Created Date",
            "updated_at": "Last Modified",
            "user_id": "User ID",
            "invoice_id": "Invoice Number",
            "amount": "Amount",
            "currency": "Currency",
            "status": "Status"
        }
        return mapping.get(key, key.replace("_", " ").title())
    
    async def _get_memory_usage(self) -> Dict[str, Any]:
        """Get current memory usage information."""
        try:
            import psutil
            process = psutil.Process()
            memory_info = process.memory_info()
            return {
                "rss": memory_info.rss,
                "vms": memory_info.vms,
                "percent": process.memory_percent()
            }
        except ImportError:
            return {"error": "psutil not available"}


class ResponseFormatterMiddleware(BaseHTTPMiddleware):
    """FastAPI middleware for role-based response formatting."""
    
    def __init__(self, app, config: Optional[ResponseFormatConfig] = None):
        super().__init__(app)
        self.config = config or ResponseFormatConfig()
        self.formatter = ResponseFormatter(self.config)
        
    async def dispatch(self, request: Request, call_next):
        """Process request and format response."""
        start_time = time.time()
        
        try:
            # Get user role from request state (set by authentication middleware)
            user_role = getattr(request.state, "user_role", PlatformRole.GUEST)
            endpoint = request.url.path
            
            # Call the next middleware/endpoint
            response = await call_next(request)
            
            # Only format JSON responses
            if (
                response.headers.get("content-type", "").startswith("application/json")
                and response.status_code < 500
            ):
                # Get response body
                response_body = b""
                async for chunk in response.body_iterator:
                    response_body += chunk
                
                if response_body:
                    try:
                        # Parse JSON response
                        response_data = json.loads(response_body.decode())
                        
                        # Format response according to role
                        formatted_data = await self.formatter.format_response(
                            response_data,
                            user_role,
                            endpoint,
                            request,
                            start_time
                        )
                        
                        # Create new response with formatted data
                        return JSONResponse(
                            content=formatted_data,
                            status_code=response.status_code,
                            headers=dict(response.headers)
                        )
                        
                    except json.JSONDecodeError:
                        logger.warning(f"Failed to parse JSON response for formatting: {endpoint}")
            
            return response
            
        except Exception as e:
            logger.error(f"Response formatting middleware error: {e}")
            # Return original response on error
            return await call_next(request)


# Export configuration for easy customization
__all__ = [
    "ResponseFormatterMiddleware",
    "ResponseFormatConfig",
    "ResponseFormatter",
    "ResponseMetrics"
]