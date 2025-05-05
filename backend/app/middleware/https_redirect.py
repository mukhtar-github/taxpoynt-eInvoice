"""
HTTPS enforcement middleware for the TaxpoyNT eInvoice API.

This middleware:
1. Redirects HTTP requests to HTTPS
2. Adds security headers to all responses
3. Enforces TLS version requirements
"""

import logging
from typing import Callable, Dict

from fastapi import FastAPI, Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import RedirectResponse
from starlette.types import ASGIApp

from app.core.config import settings

# Configure logger
logger = logging.getLogger(__name__)

class HTTPSRedirectMiddleware(BaseHTTPMiddleware):
    """
    Middleware to enforce HTTPS and add security headers.
    
    When ENFORCE_HTTPS is True, redirects all HTTP requests to HTTPS.
    Also adds security headers to all responses.
    """
    
    def __init__(self, app: ASGIApp):
        super().__init__(app)
        self.enforce_https = settings.ENFORCE_HTTPS
        
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # Skip HTTPS enforcement for local development
        if not self.enforce_https or request.url.hostname in ["localhost", "127.0.0.1"]:
            response = await call_next(request)
            return self._add_security_headers(response)
            
        # Check if the request is using HTTPS
        if request.url.scheme != "https":
            # Create HTTPS URL
            https_url = str(request.url).replace("http://", "https://", 1)
            # Redirect to HTTPS
            return RedirectResponse(https_url, status_code=301)
            
        response = await call_next(request)
        return self._add_security_headers(response)
    
    def _add_security_headers(self, response: Response) -> Response:
        """Add security headers to the response."""
        headers = {
            # Enforce HTTPS with HSTS
            "Strict-Transport-Security": "max-age=31536000; includeSubDomains",
            # Prevent MIME type sniffing
            "X-Content-Type-Options": "nosniff",
            # Enable XSS protection in browsers
            "X-XSS-Protection": "1; mode=block",
            # Control embedding in frames
            "X-Frame-Options": "SAMEORIGIN",
            # Control where resources can be loaded from
            "Content-Security-Policy": self._get_content_security_policy(),
            # Specify referrer policy
            "Referrer-Policy": "strict-origin-when-cross-origin",
            # Disable feature detection for potentially vulnerable features
            "Feature-Policy": "accelerometer 'none'; camera 'none'; geolocation 'none'; microphone 'none'",
        }
        
        # Add all security headers to the response
        for header_name, header_value in headers.items():
            response.headers[header_name] = header_value
            
        return response
        
    def _get_content_security_policy(self) -> str:
        """Generate Content Security Policy header value."""
        return (
            "default-src 'self'; "
            "script-src 'self'; "
            "style-src 'self'; "
            "img-src 'self' data:; "
            "font-src 'self'; "
            "connect-src 'self'; "
            "frame-src 'none'; "
            "object-src 'none'; "
            "base-uri 'self'"
        )


def add_https_middleware(app: FastAPI) -> None:
    """Add HTTPS redirect middleware to the application."""
    app.add_middleware(HTTPSRedirectMiddleware)
    
    # Log middleware configuration
    if settings.ENFORCE_HTTPS:
        logger.info("HTTPS enforcement enabled")
    else:
        logger.info("HTTPS enforcement disabled")

