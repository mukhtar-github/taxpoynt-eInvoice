"""
Fishbowl XML API Client
Handles all XML communication with Fishbowl inventory management API.
"""
import asyncio
import logging
import xml.etree.ElementTree as ET
from typing import Dict, List, Optional, Any, Union
from datetime import datetime, timedelta

import aiohttp
from aiohttp import ClientSession, ClientTimeout, ClientError

from .auth import FishbowlAuthManager
from .exceptions import (
    FishbowlAPIError,
    FishbowlConnectionError,
    FishbowlAuthenticationError,
    FishbowlXMLError,
    FishbowlSessionError,
    FishbowlProductNotFoundError,
    FishbowlWarehouseNotFoundError
)


logger = logging.getLogger(__name__)


class FishbowlXMLClient:
    """
    XML client for Fishbowl inventory management API.
    
    Handles XML communication, session management, and error handling
    for all Fishbowl API operations.
    """
    
    # Rate limiting settings (Fishbowl doesn't specify limits, but we'll be conservative)
    MAX_REQUESTS_PER_MINUTE = 60
    MAX_RETRIES = 3
    RETRY_DELAY = 2.0
    
    def __init__(
        self,
        auth_manager: FishbowlAuthManager,
        session: Optional[ClientSession] = None,
        max_retries: int = MAX_RETRIES
    ):
        """
        Initialize Fishbowl XML client.
        
        Args:
            auth_manager: Fishbowl authentication manager
            session: Optional aiohttp session
            max_retries: Maximum number of retry attempts
        """
        self.auth_manager = auth_manager
        self.session = session
        self.should_close_session = session is None
        self.max_retries = max_retries
        
        # Rate limiting
        self._request_times: List[datetime] = []
        self._rate_limit_lock = asyncio.Lock()
    
    async def __aenter__(self):
        """Async context manager entry."""
        if self.session is None:
            timeout = ClientTimeout(total=60, connect=10)
            connector = aiohttp.TCPConnector(limit=10, limit_per_host=5)
            self.session = ClientSession(
                timeout=timeout,
                connector=connector,
                headers={"User-Agent": "TaxPoynt-Fishbowl-Integration/1.0"}
            )
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        if self.should_close_session and self.session:
            await self.session.close()
    
    async def _rate_limit_check(self):
        """Check and enforce rate limiting."""
        async with self._rate_limit_lock:
            now = datetime.utcnow()
            # Remove requests older than 1 minute
            cutoff = now - timedelta(minutes=1)
            self._request_times = [t for t in self._request_times if t > cutoff]
            
            # Check if we're at rate limit
            if len(self._request_times) >= self.MAX_REQUESTS_PER_MINUTE:
                sleep_time = 60 - (now - self._request_times[0]).total_seconds()
                logger.warning(f"Rate limit reached, sleeping for {sleep_time:.2f} seconds")
                await asyncio.sleep(sleep_time)
                # Clean up old requests again after sleeping
                now = datetime.utcnow()
                cutoff = now - timedelta(minutes=1)
                self._request_times = [t for t in self._request_times if t > cutoff]
            
            # Record this request
            self._request_times.append(now)
    
    def _create_xml_request(self, request_type: str, **kwargs) -> str:
        """
        Create XML request for specific operation.
        
        Args:
            request_type: Type of request (e.g., 'PartGetRq', 'InventoryQtySetRq')
            **kwargs: Request parameters
            
        Returns:
            XML request string
        """
        request_elem = ET.Element(request_type)
        
        # Add parameters as XML elements
        for key, value in kwargs.items():
            if value is not None:
                elem = ET.SubElement(request_elem, key)
                if isinstance(value, dict):
                    # Handle nested objects
                    for sub_key, sub_value in value.items():
                        sub_elem = ET.SubElement(elem, sub_key)
                        sub_elem.text = str(sub_value)
                else:
                    elem.text = str(value)
        
        return ET.tostring(request_elem, encoding='unicode')
    
    def _parse_xml_response(self, xml_response: str) -> Dict[str, Any]:
        """
        Parse XML response from Fishbowl.
        
        Args:
            xml_response: XML response string
            
        Returns:
            Parsed response data
        """
        try:
            root = ET.fromstring(xml_response)
            
            # Check for session ticket updates
            ticket_elem = root.find("Ticket")
            if ticket_elem is not None and ticket_elem.text:
                # Update auth manager's session ticket
                self.auth_manager._session_ticket = ticket_elem.text
            
            # Extract response messages
            response_data = {
                "success": True,
                "messages": []
            }
            
            # Parse response messages
            msgs_rs = root.find("FbiMsgsRs")
            if msgs_rs is not None:
                for child in msgs_rs:
                    message_data = self._element_to_dict(child)
                    
                    # Check for error status
                    if "statusCode" in message_data and message_data["statusCode"] != "1000":
                        response_data["success"] = False
                        response_data["error"] = message_data.get("statusMessage", "Unknown error")
                        response_data["status_code"] = message_data["statusCode"]
                    
                    response_data["messages"].append({
                        "type": child.tag,
                        "data": message_data
                    })
            
            return response_data
            
        except ET.ParseError as e:
            raise FishbowlXMLError(f"Failed to parse XML response: {str(e)}")
    
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
    
    async def _make_request(self, request_xml: str) -> Dict[str, Any]:
        """
        Make a request to Fishbowl API.
        
        Args:
            request_xml: XML request body
            
        Returns:
            Response data
        """
        if not self.session:
            raise FishbowlConnectionError("No HTTP session available")
        
        await self._rate_limit_check()
        
        # Ensure we're authenticated
        if not self.auth_manager.is_authenticated():
            await self.auth_manager.authenticate()
        
        # Create authenticated request
        authenticated_xml = self.auth_manager._create_authenticated_request(request_xml)
        
        for attempt in range(self.max_retries + 1):
            try:
                async with self.session.post(
                    f"{self.auth_manager.base_url}/",
                    data=authenticated_xml,
                    headers=self.auth_manager.get_auth_headers()
                ) as response:
                    response_text = await response.text()
                    
                    # Handle HTTP errors
                    if response.status != 200:
                        raise FishbowlAPIError(
                            f"HTTP {response.status}: {response_text}",
                            status_code=response.status
                        )
                    
                    # Parse XML response
                    parsed_response = self._parse_xml_response(response_text)
                    
                    # Handle API errors
                    if not parsed_response["success"]:
                        error_msg = parsed_response.get("error", "Unknown API error")
                        status_code = parsed_response.get("status_code")
                        
                        # Handle session expiration
                        if status_code in ["1012", "1013"]:  # Session expired codes
                            logger.warning("Session expired, re-authenticating")
                            await self.auth_manager.refresh_session()
                            # Retry with new session
                            if attempt < self.max_retries:
                                continue
                        
                        raise FishbowlAPIError(f"API Error {status_code}: {error_msg}")
                    
                    return parsed_response
                    
            except (ClientError, asyncio.TimeoutError) as e:
                if attempt < self.max_retries:
                    sleep_time = self.RETRY_DELAY * (2 ** attempt)
                    logger.warning(f"Request failed, retrying in {sleep_time} seconds: {e}")
                    await asyncio.sleep(sleep_time)
                    continue
                raise FishbowlConnectionError(f"Failed to connect to Fishbowl API: {str(e)}")
        
        raise FishbowlConnectionError("Max retries exceeded")
    
    # Product Operations
    
    async def get_parts(
        self,
        part_type: str = "All",
        location_group: Optional[str] = None
    ) -> Dict[str, Any]:
        """Get parts (products) from Fishbowl."""
        request_xml = self._create_xml_request(
            "PartGetRq",
            PartType=part_type,
            LocationGroup=location_group
        )
        
        response = await self._make_request(request_xml)
        
        # Extract part data from response
        part_messages = [msg for msg in response["messages"] if msg["type"] == "PartGetRs"]
        if not part_messages:
            return {"parts": []}
        
        part_data = part_messages[0]["data"]
        parts = part_data.get("Parts", {}).get("Part", [])
        
        # Ensure parts is a list
        if not isinstance(parts, list):
            parts = [parts] if parts else []
        
        return {"parts": parts}
    
    async def get_part(self, part_number: str) -> Dict[str, Any]:
        """Get a specific part by part number."""
        request_xml = self._create_xml_request(
            "PartGetRq",
            Number=part_number
        )
        
        response = await self._make_request(request_xml)
        
        # Extract part data
        part_messages = [msg for msg in response["messages"] if msg["type"] == "PartGetRs"]
        if not part_messages:
            raise FishbowlProductNotFoundError(f"Part {part_number} not found")
        
        part_data = part_messages[0]["data"]
        parts = part_data.get("Parts", {}).get("Part", [])
        
        if not parts:
            raise FishbowlProductNotFoundError(f"Part {part_number} not found")
        
        # Return first matching part
        if isinstance(parts, list):
            return parts[0]
        else:
            return parts
    
    # Inventory Operations
    
    async def get_inventory_quantity(
        self,
        part_number: Optional[str] = None,
        location_group: Optional[str] = None
    ) -> Dict[str, Any]:
        """Get inventory quantities."""
        request_xml = self._create_xml_request(
            "InventoryQtyGetRq",
            PartNumber=part_number,
            LocationGroup=location_group
        )
        
        response = await self._make_request(request_xml)
        
        # Extract inventory data
        inv_messages = [msg for msg in response["messages"] if msg["type"] == "InventoryQtyGetRs"]
        if not inv_messages:
            return {"inventory": []}
        
        inv_data = inv_messages[0]["data"]
        inventory = inv_data.get("InventoryQty", [])
        
        # Ensure inventory is a list
        if not isinstance(inventory, list):
            inventory = [inventory] if inventory else []
        
        return {"inventory": inventory}
    
    async def set_inventory_quantity(
        self,
        part_number: str,
        location_name: str,
        quantity: float,
        unit_cost: Optional[float] = None
    ) -> Dict[str, Any]:
        """Set inventory quantity for a part."""
        inventory_data = {
            "PartNumber": part_number,
            "LocationName": location_name,
            "Qty": str(quantity)
        }
        
        if unit_cost is not None:
            inventory_data["UnitCost"] = str(unit_cost)
        
        request_xml = self._create_xml_request(
            "InventoryQtySetRq",
            InventoryQty=inventory_data
        )
        
        return await self._make_request(request_xml)
    
    # Purchase Order Operations
    
    async def get_purchase_orders(
        self,
        status: Optional[str] = None,
        location_group: Optional[str] = None
    ) -> Dict[str, Any]:
        """Get purchase orders."""
        request_xml = self._create_xml_request(
            "POGetRq",
            Status=status,
            LocationGroup=location_group
        )
        
        response = await self._make_request(request_xml)
        
        # Extract PO data
        po_messages = [msg for msg in response["messages"] if msg["type"] == "POGetRs"]
        if not po_messages:
            return {"purchase_orders": []}
        
        po_data = po_messages[0]["data"]
        pos = po_data.get("POs", {}).get("PO", [])
        
        # Ensure pos is a list
        if not isinstance(pos, list):
            pos = [pos] if pos else []
        
        return {"purchase_orders": pos}
    
    async def get_purchase_order(self, po_number: str) -> Dict[str, Any]:
        """Get a specific purchase order by number."""
        request_xml = self._create_xml_request(
            "POGetRq",
            Number=po_number
        )
        
        response = await self._make_request(request_xml)
        
        # Extract PO data
        po_messages = [msg for msg in response["messages"] if msg["type"] == "POGetRs"]
        if not po_messages:
            raise FishbowlPurchaseOrderNotFoundError(f"Purchase order {po_number} not found")
        
        po_data = po_messages[0]["data"]
        pos = po_data.get("POs", {}).get("PO", [])
        
        if not pos:
            raise FishbowlPurchaseOrderNotFoundError(f"Purchase order {po_number} not found")
        
        # Return first matching PO
        if isinstance(pos, list):
            return pos[0]
        else:
            return pos
    
    # Sales Order Operations
    
    async def get_sales_orders(
        self,
        status: Optional[str] = None,
        location_group: Optional[str] = None
    ) -> Dict[str, Any]:
        """Get sales orders."""
        request_xml = self._create_xml_request(
            "SOGetRq",
            Status=status,
            LocationGroup=location_group
        )
        
        response = await self._make_request(request_xml)
        
        # Extract SO data
        so_messages = [msg for msg in response["messages"] if msg["type"] == "SOGetRs"]
        if not so_messages:
            return {"sales_orders": []}
        
        so_data = so_messages[0]["data"]
        sos = so_data.get("SOs", {}).get("SO", [])
        
        # Ensure sos is a list
        if not isinstance(sos, list):
            sos = [sos] if sos else []
        
        return {"sales_orders": sos}
    
    async def get_sales_order(self, so_number: str) -> Dict[str, Any]:
        """Get a specific sales order by number."""
        request_xml = self._create_xml_request(
            "SOGetRq",
            Number=so_number
        )
        
        response = await self._make_request(request_xml)
        
        # Extract SO data
        so_messages = [msg for msg in response["messages"] if msg["type"] == "SOGetRs"]
        if not so_messages:
            raise FishbowlSalesOrderNotFoundError(f"Sales order {so_number} not found")
        
        so_data = so_messages[0]["data"]
        sos = so_data.get("SOs", {}).get("SO", [])
        
        if not sos:
            raise FishbowlSalesOrderNotFoundError(f"Sales order {so_number} not found")
        
        # Return first matching SO
        if isinstance(sos, list):
            return sos[0]
        else:
            return sos
    
    # Vendor Operations
    
    async def get_vendors(self) -> Dict[str, Any]:
        """Get all vendors."""
        request_xml = self._create_xml_request("VendorGetRq")
        
        response = await self._make_request(request_xml)
        
        # Extract vendor data
        vendor_messages = [msg for msg in response["messages"] if msg["type"] == "VendorGetRs"]
        if not vendor_messages:
            return {"vendors": []}
        
        vendor_data = vendor_messages[0]["data"]
        vendors = vendor_data.get("Vendors", {}).get("Vendor", [])
        
        # Ensure vendors is a list
        if not isinstance(vendors, list):
            vendors = [vendors] if vendors else []
        
        return {"vendors": vendors}
    
    # Location Operations
    
    async def get_locations(self) -> Dict[str, Any]:
        """Get all locations."""
        request_xml = self._create_xml_request("LocationGetRq")
        
        response = await self._make_request(request_xml)
        
        # Extract location data
        location_messages = [msg for msg in response["messages"] if msg["type"] == "LocationGetRs"]
        if not location_messages:
            return {"locations": []}
        
        location_data = location_messages[0]["data"]
        locations = location_data.get("Locations", {}).get("Location", [])
        
        # Ensure locations is a list
        if not isinstance(locations, list):
            locations = [locations] if locations else []
        
        return {"locations": locations}
    
    async def get_location(self, location_name: str) -> Dict[str, Any]:
        """Get a specific location by name."""
        request_xml = self._create_xml_request(
            "LocationGetRq",
            Name=location_name
        )
        
        response = await self._make_request(request_xml)
        
        # Extract location data
        location_messages = [msg for msg in response["messages"] if msg["type"] == "LocationGetRs"]
        if not location_messages:
            raise FishbowlWarehouseNotFoundError(f"Location {location_name} not found")
        
        location_data = location_messages[0]["data"]
        locations = location_data.get("Locations", {}).get("Location", [])
        
        if not locations:
            raise FishbowlWarehouseNotFoundError(f"Location {location_name} not found")
        
        # Return first matching location
        if isinstance(locations, list):
            return locations[0]
        else:
            return locations