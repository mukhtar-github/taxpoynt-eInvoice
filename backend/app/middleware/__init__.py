"""Middleware initialization module."""
import os
from fastapi import FastAPI, Request
from starlette.middleware.cors import CORSMiddleware
from starlette.middleware.base import BaseHTTPMiddleware
from app.middleware.rate_limit import RateLimitMiddleware
from app.middleware.api_key_auth import APIKeyMiddleware
from app.middleware.security import SecurityMiddleware
from app.core.config import settings


class RailwayProxyMiddleware(BaseHTTPMiddleware):
    """
    Railway proxy middleware to handle Railway's specific proxy headers.
    This fixes the 301 redirect authentication loops on Railway deployments.
    """
    async def dispatch(self, request: Request, call_next):
        # Only apply Railway proxy handling in Railway environment
        if os.getenv("RAILWAY_ENVIRONMENT"):
            # Handle Railway's specific client IP header
            if request.headers.get("x-envoy-external-address"):
                request.scope["client"] = (
                    request.headers["x-envoy-external-address"], 0
                )
            
            # Fix scheme for HTTPS redirects
            if request.headers.get("x-forwarded-proto"):
                request.scope["scheme"] = request.headers["x-forwarded-proto"]
        
        return await call_next(request)


def setup_middleware(app: FastAPI) -> None:
    """
    Setup all application middleware.
    Order matters - middleware are executed in reverse order of registration.
    """
    # Railway proxy middleware (must be first to handle proxy headers)
    app.add_middleware(RailwayProxyMiddleware)
    # CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[str(origin) for origin in settings.CORS_ORIGINS],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    # Security middleware (HTTPS enforcement and security headers)
    app.add_middleware(
        SecurityMiddleware,
        https_redirect=settings.ENFORCE_HTTPS,
        enable_hsts=settings.HSTS_ENABLED
    )
    
    # API Key Authentication middleware (for two-layer auth with API key and Secret key)
    app.add_middleware(
        APIKeyMiddleware,
        api_key_header="X-API-KEY",
        secret_key_header="X-SECRET-KEY",
        exclude_paths=["/docs", "/redoc", "/openapi.json", "/auth"]
    )
    
    # Rate Limiting middleware using the original implementation
    # Define default and path-specific rate limits
    default_limits = {
        "ip": (settings.RATE_LIMIT_PER_MINUTE, 60),  # Per minute
        "user": (settings.RATE_LIMIT_PER_MINUTE * 2, 60),  # Authenticated users get higher limits
        "ip_daily": (settings.RATE_LIMIT_PER_DAY, 86400),  # Per day for IP
        "user_daily": (settings.RATE_LIMIT_PER_DAY * 2, 86400)  # Per day for authenticated users
    }
    
    path_limits = {
        # Auth endpoints - more restricted to prevent brute force
        "^/api/v1/auth/login": (settings.RATE_LIMIT_AUTH_MINUTE, 60),
        "^/api/v1/auth/register": (settings.RATE_LIMIT_AUTH_MINUTE, 60),
        "^/api/v1/auth/password-reset": (settings.RATE_LIMIT_AUTH_MINUTE, 60),
        "^/api/v1/auth/refresh-token": (settings.RATE_LIMIT_AUTH_MINUTE, 60),
        
        # High-volume endpoints
        "^/api/v1/irn/generate-batch": (settings.RATE_LIMIT_BATCH_MINUTE, 60),
        
        # API key management
        "^/api/v1/api-keys": (settings.RATE_LIMIT_API_MINUTE, 60),
    }
    
    # Function to identify users from requests
    async def identify_user(request: Request) -> str:
        # Try to get user from JWT token
        authorization = request.headers.get("Authorization", "")
        if authorization.startswith("Bearer "):
            return authorization
        
        # Check for API key authentication
        api_key = request.headers.get("X-API-KEY")
        if api_key:
            return f"api:{api_key}"
        
        # Fallback to client IP
        forwarded = request.headers.get("X-Forwarded-For")
        if forwarded:
            return forwarded.split(",")[0].strip()
        
        return request.client.host or "unknown"  # type: ignore
    
    app.add_middleware(
        RateLimitMiddleware,
        default_limits=default_limits,
        path_limits=path_limits,
        identify_user_func=identify_user
    )
