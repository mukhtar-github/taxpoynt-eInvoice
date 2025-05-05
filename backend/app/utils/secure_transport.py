"""
Secure data transmission utilities for FIRS e-Invoice system.

This module provides functions for:
- Secure HTTP client setup with TLS
- Certificate validation
- Secure API communication
- TLS configuration
"""

import logging
import ssl
import certifi
from typing import Dict, Optional, Union, Any
from urllib.parse import urlparse

import httpx
from fastapi import HTTPException
from pydantic import BaseModel

from app.core.config import settings


# Configure logger
logger = logging.getLogger(__name__)


class SecureResponse(BaseModel):
    """Model for standardized secure API responses"""
    status_code: int
    content: Union[Dict, str, bytes]
    headers: Dict
    success: bool


def create_secure_client(
    verify_ssl: bool = True,
    cert_path: Optional[str] = None,
    timeout: int = 30
) -> httpx.Client:
    """
    Create a secure HTTP client with proper TLS configuration.
    
    Args:
        verify_ssl: Whether to verify SSL certificates
        cert_path: Optional path to client certificate for mutual TLS
        timeout: Request timeout in seconds
        
    Returns:
        Configured HTTPX client
    """
    # Use Mozilla's CA bundle by default (via certifi)
    ssl_context = ssl.create_default_context(cafile=certifi.where())
    
    # Configure for TLS 1.2 or higher only
    ssl_context.minimum_version = ssl.TLSVersion.TLSv1_2
    
    # Disable weak cipher suites
    ssl_context.set_ciphers('HIGH:!aNULL:!eNULL:!EXPORT:!DES:!RC4:!MD5:!PSK')
    
    if cert_path:
        # For mutual TLS (client certificate)
        client_cert = cert_path
        client_key = settings.CLIENT_KEY_PATH
        
        # Configure client for mutual TLS
        return httpx.Client(
            verify=ssl_context,
            cert=(client_cert, client_key) if client_key else client_cert,
            timeout=timeout
        )
    
    # Standard TLS client
    return httpx.Client(
        verify=ssl_context if verify_ssl else False,
        timeout=timeout
    )


async def create_secure_async_client(
    verify_ssl: bool = True,
    cert_path: Optional[str] = None,
    timeout: int = 30
) -> httpx.AsyncClient:
    """
    Create a secure async HTTP client with proper TLS configuration.
    
    Args:
        verify_ssl: Whether to verify SSL certificates
        cert_path: Optional path to client certificate for mutual TLS
        timeout: Request timeout in seconds
        
    Returns:
        Configured async HTTPX client
    """
    # Use Mozilla's CA bundle by default (via certifi)
    ssl_context = ssl.create_default_context(cafile=certifi.where())
    
    # Configure for TLS 1.2 or higher only
    ssl_context.minimum_version = ssl.TLSVersion.TLSv1_2
    
    # Disable weak cipher suites
    ssl_context.set_ciphers('HIGH:!aNULL:!eNULL:!EXPORT:!DES:!RC4:!MD5:!PSK')
    
    if cert_path:
        # For mutual TLS (client certificate)
        client_cert = cert_path
        client_key = settings.CLIENT_KEY_PATH
        
        # Configure client for mutual TLS
        return httpx.AsyncClient(
            verify=ssl_context,
            cert=(client_cert, client_key) if client_key else client_cert,
            timeout=timeout
        )
    
    # Standard TLS client
    return httpx.AsyncClient(
        verify=ssl_context if verify_ssl else False,
        timeout=timeout
    )


async def secure_api_request(
    url: str,
    method: str = "GET",
    json_data: Optional[Dict] = None,
    headers: Optional[Dict] = None,
    params: Optional[Dict] = None,
    verify_ssl: bool = True,
    cert_path: Optional[str] = None,
    timeout: int = 30
) -> SecureResponse:
    """
    Make a secure API request to an external service.
    
    Args:
        url: The URL to request
        method: HTTP method (GET, POST, etc.)
        json_data: JSON payload for request
        headers: HTTP headers
        params: URL parameters
        verify_ssl: Whether to verify SSL certificates
        cert_path: Optional path to client certificate for mutual TLS
        timeout: Request timeout in seconds
        
    Returns:
        SecureResponse object
    """
    # Create secure client
    async with await create_secure_async_client(
        verify_ssl=verify_ssl,
        cert_path=cert_path,
        timeout=timeout
    ) as client:
        try:
            # Set default headers if none provided
            if headers is None:
                headers = {
                    "User-Agent": f"TaxpoyNT-eInvoice/{settings.VERSION}",
                    "Accept": "application/json",
                    "Content-Type": "application/json",
                }
            
            # Make the request with appropriate method
            if method.upper() == "GET":
                response = await client.get(url, headers=headers, params=params)
            elif method.upper() == "POST":
                response = await client.post(url, json=json_data, headers=headers, params=params)
            elif method.upper() == "PUT":
                response = await client.put(url, json=json_data, headers=headers, params=params)
            elif method.upper() == "DELETE":
                response = await client.delete(url, headers=headers, params=params)
            else:
                raise ValueError(f"Unsupported HTTP method: {method}")
            
            # Parse response content
            try:
                content = response.json()
            except Exception:
                content = response.text
            
            # Check for success based on status code
            success = 200 <= response.status_code < 300
            
            # Log failed requests for security monitoring
            if not success:
                logger.warning(
                    f"Failed API request to {url} with status {response.status_code}: {content}"
                )
            
            return SecureResponse(
                status_code=response.status_code,
                content=content,
                headers=dict(response.headers),
                success=success
            )
            
        except httpx.TimeoutException:
            logger.error(f"Request to {url} timed out after {timeout} seconds")
            raise HTTPException(status_code=504, detail="Gateway Timeout")
            
        except httpx.RequestError as e:
            logger.error(f"Request error to {url}: {str(e)}")
            raise HTTPException(status_code=502, detail=f"Request failed: {str(e)}")
            
        except Exception as e:
            logger.error(f"Error making secure request to {url}: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


def validate_tls_connection(url: str) -> Dict[str, Any]:
    """
    Validate TLS connection to a remote server.
    
    Checks:
    - TLS version
    - Certificate validity
    - Cipher suite
    - Certificate chain
    
    Args:
        url: URL to validate
        
    Returns:
        Dict with validation results
    """
    parsed_url = urlparse(url)
    hostname = parsed_url.netloc.split(':')[0]
    port = parsed_url.port or (443 if parsed_url.scheme == 'https' else 80)
    
    if parsed_url.scheme != 'https':
        return {
            "valid": False,
            "error": "Non-HTTPS URL provided. TLS validation requires HTTPS.",
            "url": url
        }
    
    try:
        # Create SSL context for validation
        context = ssl.create_default_context(cafile=certifi.where())
        
        # Create connection to server
        with socket.create_connection((hostname, port)) as sock:
            with context.wrap_socket(sock, server_hostname=hostname) as ssock:
                # Get certificate info
                cert = ssock.getpeercert()
                cipher = ssock.cipher()
                version = ssock.version()
                
                # Check certificate validity
                ssl.match_hostname(cert, hostname)
                
                # Get additional information
                issuer = dict(x[0] for x in cert['issuer'])
                subject = dict(x[0] for x in cert['subject'])
                not_after = cert['notAfter']
                
                return {
                    "valid": True,
                    "hostname": hostname,
                    "port": port,
                    "tls_version": version,
                    "cipher_suite": cipher,
                    "issuer": issuer,
                    "subject": subject,
                    "expires": not_after,
                    "url": url
                }
    
    except ssl.SSLError as e:
        return {
            "valid": False,
            "error": f"SSL Error: {str(e)}",
            "url": url
        }
    except ssl.CertificateError as e:
        return {
            "valid": False,
            "error": f"Certificate Error: {str(e)}",
            "url": url
        }
    except Exception as e:
        return {
            "valid": False,
            "error": f"Validation Error: {str(e)}",
            "url": url
        }


# Import missing socket module
import socket

