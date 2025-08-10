"""
Fishbowl Authentication Manager
Handles API authentication for Fishbowl inventory management system.
"""
import asyncio
import logging
import base64
import hashlib
import xml.etree.ElementTree as ET
from typing import Dict, Optional, Any
from datetime import datetime, timedelta

import aiohttp
from aiohttp import ClientSession, ClientTimeout, ClientError

from .exceptions import (
    FishbowlAuthenticationError,
    FishbowlAuthorizationError,
    FishbowlConnectionError,
    FishbowlConfigurationError,
    FishbowlSessionError
)


logger = logging.getLogger(__name__)


class FishbowlAuthManager:
    """
    Manages authentication for Fishbowl API.
    
    Fishbowl uses a session-based authentication system with username/password
    credentials and maintains session tickets for subsequent API calls.
    """
    
    def __init__(
        self,
        server_host: str,
        server_port: int,
        username: str,
        password: str,
        app_name: str = "TaxPoynt",
        app_description: str = "TaxPoynt E-Invoice Integration",
        session: Optional[ClientSession] = None
    ):
        """
        Initialize Fishbowl authentication manager.
        
        Args:
            server_host: Fishbowl server hostname/IP
            server_port: Fishbowl server port (usually 28192)
            username: Fishbowl username
            password: Fishbowl password
            app_name: Application name for identification
            app_description: Application description
            session: Optional aiohttp session to use
        """
        if not all([server_host, server_port, username, password]):
            raise FishbowlConfigurationError("Server host, port, username and password are required")
        
        self.server_host = server_host
        self.server_port = server_port
        self.username = username
        self.password = password
        self.app_name = app_name
        self.app_description = app_description
        self.session = session
        self.should_close_session = session is None
        
        # Connection state
        self._is_authenticated = False
        self._session_ticket: Optional[str] = None
        self._last_auth_check: Optional[datetime] = None
        self._user_info: Optional[Dict[str, Any]] = None
        
        # API endpoints
        self.base_url = f"http://{server_host}:{server_port}"
    
    async def __aenter__(self):
        """Async context manager entry."""
        if self.session is None:
            timeout = ClientTimeout(total=30, connect=10)
            self.session = ClientSession(timeout=timeout)
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        if self.should_close_session and self.session:
            await self.session.close()
    
    def _create_login_request(self) -> str:
        """
        Create XML login request for Fishbowl.
        
        Returns:
            XML login request string
        """
        # Create encoded password (Base64 encoded MD5 hash)
        password_hash = hashlib.md5(self.password.encode()).hexdigest()
        encoded_password = base64.b64encode(password_hash.encode()).decode()
        
        # Build XML request
        root = ET.Element("FbiXml")
        ticket = ET.SubElement(root, "Ticket")
        request = ET.SubElement(root, "FbiMsgsRq")
        
        login_rq = ET.SubElement(request, "LoginRq")
        ET.SubElement(login_rq, "UserName").text = self.username
        ET.SubElement(login_rq, "UserPassword").text = encoded_password
        
        app_info = ET.SubElement(login_rq, "AppInfo")
        ET.SubElement(app_info, "Name").text = self.app_name
        ET.SubElement(app_info, "Description").text = self.app_description
        
        return ET.tostring(root, encoding='unicode')
    
    def _create_authenticated_request(self, request_body: str) -> str:
        """
        Create authenticated XML request with session ticket.
        
        Args:
            request_body: Inner request XML body
            
        Returns:
            Complete XML request with authentication
        """
        if not self._session_ticket:
            raise FishbowlSessionError("No valid session ticket available")
        
        root = ET.Element("FbiXml")
        ticket = ET.SubElement(root, "Ticket")
        ticket.text = self._session_ticket
        
        # Add the request body
        request = ET.SubElement(root, "FbiMsgsRq")
        request.append(ET.fromstring(request_body))
        
        return ET.tostring(root, encoding='unicode')
    
    def _parse_response(self, xml_response: str) -> Dict[str, Any]:
        """
        Parse XML response from Fishbowl.
        
        Args:
            xml_response: XML response string
            
        Returns:
            Parsed response data
        """
        try:
            root = ET.fromstring(xml_response)
            
            # Extract ticket if present
            ticket_elem = root.find("Ticket")
            if ticket_elem is not None:
                self._session_ticket = ticket_elem.text
            
            # Extract response data
            response_data = {
                "success": True,
                "ticket": self._session_ticket,
                "messages": []
            }
            
            # Parse messages
            msgs_rs = root.find("FbiMsgsRs")
            if msgs_rs is not None:
                for child in msgs_rs:
                    response_data["messages"].append({
                        "type": child.tag,
                        "data": self._element_to_dict(child)
                    })
            
            return response_data
            
        except ET.ParseError as e:
            raise FishbowlAuthenticationError(f"Failed to parse XML response: {str(e)}")
    
    def _element_to_dict(self, element: ET.Element) -> Dict[str, Any]:
        """Convert XML element to dictionary."""
        result = {}
        
        # Add attributes
        if element.attrib:
            result.update(element.attrib)
        
        # Add text content
        if element.text and element.text.strip():
            if len(element) == 0:
                return element.text.strip()
            result["text"] = element.text.strip()
        
        # Add child elements
        for child in element:
            child_data = self._element_to_dict(child)
            if child.tag in result:
                # Handle multiple children with same tag
                if not isinstance(result[child.tag], list):
                    result[child.tag] = [result[child.tag]]
                result[child.tag].append(child_data)
            else:
                result[child.tag] = child_data
        
        return result
    
    async def authenticate(self) -> Dict[str, Any]:
        """
        Authenticate with Fishbowl server.
        
        Returns:
            Authentication result with session information
        """
        if not self.session:
            raise FishbowlConnectionError("No HTTP session available")
        
        try:
            # Create login request
            login_xml = self._create_login_request()
            
            # Send login request
            async with self.session.post(
                f"{self.base_url}/",
                data=login_xml,
                headers={"Content-Type": "text/xml"}
            ) as response:
                if response.status != 200:
                    raise FishbowlAuthenticationError(f"Authentication failed: HTTP {response.status}")
                
                response_xml = await response.text()
                parsed_response = self._parse_response(response_xml)
                
                # Check for authentication success
                login_messages = [msg for msg in parsed_response["messages"] if msg["type"] == "LoginRs"]
                
                if not login_messages:
                    raise FishbowlAuthenticationError("No login response received")
                
                login_response = login_messages[0]["data"]
                
                # Check for errors
                if "statusCode" in login_response and login_response["statusCode"] != "1000":
                    error_msg = login_response.get("statusMessage", "Authentication failed")
                    raise FishbowlAuthenticationError(f"Login failed: {error_msg}")
                
                self._is_authenticated = True
                self._last_auth_check = datetime.utcnow()
                self._user_info = login_response
                
                logger.info("Successfully authenticated with Fishbowl")
                
                return {
                    "success": True,
                    "session_ticket": self._session_ticket,
                    "user_info": self._user_info,
                    "authenticated_at": self._last_auth_check.isoformat()
                }
                
        except ClientError as e:
            raise FishbowlConnectionError(f"Failed to connect to Fishbowl server: {str(e)}")
        except Exception as e:
            raise FishbowlAuthenticationError(f"Authentication failed: {str(e)}")
    
    async def test_connection(self) -> Dict[str, Any]:
        """
        Test the connection to Fishbowl server.
        
        Returns:
            Connection test results
        """
        try:
            auth_result = await self.authenticate()
            
            return {
                "success": True,
                "status": "connected",
                "server_host": self.server_host,
                "server_port": self.server_port,
                "user_info": self._user_info,
                "session_ticket": self._session_ticket,
                "last_check": self._last_auth_check.isoformat() if self._last_auth_check else None
            }
            
        except Exception as e:
            logger.error(f"Connection test failed: {e}")
            return {
                "success": False,
                "status": "failed",
                "error": str(e),
                "server_host": self.server_host,
                "server_port": self.server_port
            }
    
    def is_authenticated(self) -> bool:
        """
        Check if currently authenticated.
        
        Returns:
            True if authenticated, False otherwise
        """
        return self._is_authenticated and self._session_ticket is not None
    
    def get_session_ticket(self) -> Optional[str]:
        """
        Get current session ticket.
        
        Returns:
            Session ticket if available
        """
        return self._session_ticket
    
    def get_user_info(self) -> Optional[Dict[str, Any]]:
        """
        Get cached user information.
        
        Returns:
            User information if available
        """
        return self._user_info
    
    async def refresh_session(self) -> Dict[str, Any]:
        """
        Refresh session by re-authenticating.
        
        Returns:
            Refresh result
        """
        logger.info("Refreshing Fishbowl session")
        
        # Clear current session
        self._is_authenticated = False
        self._session_ticket = None
        self._user_info = None
        
        # Re-authenticate
        return await self.authenticate()
    
    def get_auth_headers(self) -> Dict[str, str]:
        """
        Get authentication headers for API requests.
        Note: Fishbowl uses XML with embedded tickets, not HTTP headers
        
        Returns:
            Headers dict for XML requests
        """
        return {
            "Content-Type": "text/xml",
            "Accept": "text/xml"
        }
    
    def get_api_info(self) -> Dict[str, Any]:
        """
        Get API configuration information.
        
        Returns:
            API configuration details
        """
        return {
            "server_host": self.server_host,
            "server_port": self.server_port,
            "base_url": self.base_url,
            "username": self.username,
            "app_name": self.app_name,
            "is_authenticated": self._is_authenticated,
            "has_session_ticket": self._session_ticket is not None,
            "last_auth_check": self._last_auth_check.isoformat() if self._last_auth_check else None
        }
    
    async def validate_permissions(self, required_permissions: Optional[list] = None) -> Dict[str, Any]:
        """
        Validate API permissions for required operations.
        
        Args:
            required_permissions: List of required permissions to check
            
        Returns:
            Permission validation results
        """
        if not self._user_info:
            await self.authenticate()
        
        # Default required permissions for inventory operations
        if required_permissions is None:
            required_permissions = [
                "inventory_read",
                "inventory_write",
                "products_read", 
                "products_write",
                "orders_read",
                "vendors_read"
            ]
        
        # Fishbowl permissions are typically role-based
        user_info = self._user_info or {}
        
        return {
            "has_access": self._is_authenticated,
            "user_id": user_info.get("userId"),
            "user_name": user_info.get("userName", self.username),
            "server_name": user_info.get("serverName"),
            "database_name": user_info.get("dbName"),
            "required_permissions": required_permissions,
            "validation_note": "Fishbowl uses role-based permissions. Access validated through successful authentication."
        }
    
    def disconnect(self) -> bool:
        """
        Disconnect from Fishbowl server.
        
        Returns:
            True if disconnection successful
        """
        self._is_authenticated = False
        self._session_ticket = None
        self._last_auth_check = None
        self._user_info = None
        
        logger.info("Disconnected from Fishbowl server")
        return True