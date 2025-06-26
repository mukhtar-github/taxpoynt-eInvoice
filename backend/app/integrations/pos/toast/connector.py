"""
Toast POS connector implementation for restaurant businesses.

This module provides integration with Toast POS system including OAuth authentication,
order processing, menu synchronization, and webhook handling for restaurants.

NOTE: Toast POS is currently only available in the United States. This implementation
is provided for future international expansion but is not immediately relevant for
the Nigerian market. Priority should be given to POS systems available in Nigeria
such as Paystack POS, Flutterwave POS, Interswitch POS, etc.
"""

import asyncio
import hashlib
import hmac
import json
import time
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List

import aiohttp
from fastapi import HTTPException

from app.integrations.pos.base_pos_connector import BasePOSConnector, POSTransaction, POSLocation
from .models import (
    ToastOrder, ToastLocation, ToastWebhookEvent, ToastMenu,
    ToastMenuItem, ToastCustomer, ToastPayment, ToastMoney, ToastAPIResponse
)


class ToastPOSConnector(BasePOSConnector):
    """Toast POS connector with real-time order processing and restaurant features."""
    
    # Toast API endpoints
    BASE_URL = "https://ws-api.toasttab.com"
    SANDBOX_BASE_URL = "https://ws-sandbox-api.toasttab.com"
    OAUTH_URL = "https://oauth.toasttab.com/oauth/authorize"
    TOKEN_URL = "https://oauth.toasttab.com/oauth/token"
    
    def __init__(self, connection_config: Dict[str, Any]):
        """
        Initialize Toast POS connector.
        
        Args:
            connection_config: Dictionary containing Toast connection parameters
                - client_id: Toast OAuth client ID
                - client_secret: Toast OAuth client secret
                - access_token: Toast access token
                - refresh_token: Toast refresh token
                - restaurant_guid: Toast restaurant GUID
                - management_group_guid: Toast management group GUID
                - environment: 'sandbox' or 'production'
                - webhook_secret: Webhook signature verification secret
        """
        super().__init__(connection_config)
        self.client_id = connection_config.get("client_id")
        self.client_secret = connection_config.get("client_secret")
        self.access_token = connection_config.get("access_token")
        self.refresh_token = connection_config.get("refresh_token")
        self.restaurant_guid = connection_config.get("restaurant_guid")
        self.management_group_guid = connection_config.get("management_group_guid")
        self.environment = connection_config.get("environment", "sandbox")
        
        # Set API base URL based on environment
        self.api_base_url = self.BASE_URL if self.environment == "production" else self.SANDBOX_BASE_URL
        
        # API endpoints
        self.endpoints = {
            "orders": f"{self.api_base_url}/orders/v2/orders",
            "restaurants": f"{self.api_base_url}/config/v1/restaurants",
            "menus": f"{self.api_base_url}/config/v1/menus",
            "customers": f"{self.api_base_url}/crm/v1/customers",
            "payments": f"{self.api_base_url}/orders/v2/orderPayments"
        }
        
        # Session for HTTP requests
        self.session: Optional[aiohttp.ClientSession] = None
    
    async def authenticate(self) -> Dict[str, Any]:
        """
        Authenticate with Toast API using OAuth 2.0.
        
        Returns:
            Dict containing authentication results
        """
        if not self.access_token:
            raise HTTPException(status_code=401, detail="No access token provided")
        
        try:
            # Test authentication by making a simple API call
            headers = await self._get_auth_headers()
            
            if not self.session:
                self.session = aiohttp.ClientSession()
            
            # Test with restaurant info endpoint
            restaurant_url = f"{self.endpoints['restaurants']}/{self.restaurant_guid}"
            
            async with self.session.get(restaurant_url, headers=headers) as response:
                if response.status == 200:
                    restaurant_data = await response.json()
                    self._authenticated = True
                    self._last_auth_time = datetime.now()
                    
                    return {
                        "success": True,
                        "message": "Authentication successful",
                        "restaurant_name": restaurant_data.get("name", "Unknown"),
                        "restaurant_guid": self.restaurant_guid,
                        "environment": self.environment
                    }
                elif response.status == 401:
                    # Token might be expired, try to refresh
                    if self.refresh_token:
                        await self._refresh_access_token()
                        return await self.authenticate()  # Retry after refresh
                    else:
                        raise HTTPException(status_code=401, detail="Access token expired and no refresh token available")
                else:
                    error_text = await response.text()
                    raise HTTPException(status_code=response.status, detail=f"Toast API error: {error_text}")
                    
        except aiohttp.ClientError as e:
            self.logger.error(f"Toast API connection error: {str(e)}", exc_info=True)
            raise HTTPException(status_code=500, detail=f"Connection error: {str(e)}")
        except Exception as e:
            self.logger.error(f"Toast authentication error: {str(e)}", exc_info=True)
            raise HTTPException(status_code=500, detail=f"Authentication error: {str(e)}")
    
    async def verify_webhook_signature(
        self, 
        payload: bytes, 
        signature: str, 
        timestamp: Optional[str] = None
    ) -> bool:
        """
        Verify Toast webhook signature.
        
        Toast webhook signature verification:
        1. Create HMAC-SHA256 hash using webhook secret and payload
        2. Compare with provided signature
        
        Args:
            payload: Raw webhook payload bytes
            signature: Signature from Toast-Signature header
            timestamp: Optional timestamp for replay protection
            
        Returns:
            bool: True if signature is valid
        """
        if not self.webhook_secret:
            self.logger.warning("Toast webhook secret not configured")
            return False
        
        try:
            # Verify timestamp if provided (replay protection)
            if timestamp and not self._verify_timestamp(timestamp):
                self.logger.warning("Toast webhook timestamp outside tolerance window")
                return False
            
            # Create HMAC-SHA256 signature
            computed_signature = hmac.new(
                self.webhook_secret.encode('utf-8'),
                payload,
                hashlib.sha256
            ).hexdigest()
            
            # Toast signature format: sha256=<hash>
            if signature.startswith('sha256='):
                signature = signature[7:]  # Remove 'sha256=' prefix
            
            # Compare signatures using constant-time comparison
            is_valid = hmac.compare_digest(signature, computed_signature)
            
            if not is_valid:
                self.logger.warning(f"Toast webhook signature verification failed")
            
            return is_valid
            
        except Exception as e:
            self.logger.error(f"Toast webhook signature verification error: {str(e)}", exc_info=True)
            return False
    
    async def process_transaction(self, transaction_data: Dict[str, Any]) -> POSTransaction:
        """
        Process a Toast order/transaction from webhook or API data.
        
        Args:
            transaction_data: Raw order data from Toast
            
        Returns:
            POSTransaction: Normalized transaction object
        """
        try:
            # Create Toast order model from raw data
            toast_order = ToastOrder(**transaction_data)
            
            # Extract basic transaction information
            total_amount = toast_order.total_amount.dollars
            tax_amount = toast_order.tax_amount.dollars
            tip_amount = toast_order.tip_amount.dollars if toast_order.tip_amount else 0.0
            service_charge = toast_order.service_charge_amount.dollars if toast_order.service_charge_amount else 0.0
            
            # Extract order items
            items = self._extract_order_items(toast_order)
            
            # Extract customer information
            customer_info = self._extract_customer_info(toast_order)
            
            # Extract payment information
            payment_method = self._extract_payment_method(toast_order)
            
            # Build tax information
            tax_info = {
                "total_tax": tax_amount,
                "tip_amount": tip_amount,
                "service_charge": service_charge,
                "currency": toast_order.total_amount.currency,
                "source": "toast_pos"
            }
            
            # Create normalized POS transaction
            transaction = POSTransaction(
                transaction_id=toast_order.guid,
                location_id=toast_order.restaurant_guid,
                amount=total_amount,
                currency=toast_order.total_amount.currency,
                payment_method=payment_method,
                timestamp=toast_order.closed_date or toast_order.modified_date,
                items=items,
                customer_info=customer_info,
                tax_info=tax_info,
                metadata={
                    "order_guid": toast_order.guid,
                    "order_number": toast_order.order_number,
                    "external_id": toast_order.external_id,
                    "order_type": toast_order.order_type,
                    "dining_option": toast_order.dining_option,
                    "table": toast_order.table,
                    "service_area": toast_order.service_area,
                    "server": toast_order.server,
                    "source": "toast_pos",
                    "environment": self.environment,
                    "state": toast_order.state,
                    "voided": toast_order.voided
                }
            )
            
            return transaction
            
        except Exception as e:
            self.logger.error(f"Error processing Toast transaction: {str(e)}", exc_info=True)
            raise
    
    async def get_transaction_by_id(self, transaction_id: str) -> Optional[POSTransaction]:
        """
        Retrieve Toast order details by order GUID.
        
        Args:
            transaction_id: Toast order GUID
            
        Returns:
            POSTransaction or None if not found
        """
        try:
            if not self.session:
                self.session = aiohttp.ClientSession()
            
            headers = await self._get_auth_headers()
            order_url = f"{self.endpoints['orders']}/{transaction_id}"
            
            async with self.session.get(order_url, headers=headers) as response:
                if response.status == 200:
                    order_data = await response.json()
                    return await self.process_transaction(order_data)
                elif response.status == 404:
                    return None
                else:
                    error_text = await response.text()
                    self.logger.error(f"Error fetching Toast order {transaction_id}: {error_text}")
                    return None
                    
        except Exception as e:
            self.logger.error(f"Error retrieving Toast transaction {transaction_id}: {str(e)}", exc_info=True)
            return None
    
    async def get_location_details(self) -> POSLocation:
        """
        Get Toast restaurant location details.
        
        Returns:
            POSLocation: Restaurant location information
        """
        try:
            if not self.session:
                self.session = aiohttp.ClientSession()
            
            headers = await self._get_auth_headers()
            restaurant_url = f"{self.endpoints['restaurants']}/{self.restaurant_guid}"
            
            async with self.session.get(restaurant_url, headers=headers) as response:
                if response.status == 200:
                    restaurant_data = await response.json()
                    
                    # Create Toast location model
                    toast_location = ToastLocation(**restaurant_data)
                    
                    # Convert to standardized POSLocation
                    return POSLocation(
                        location_id=toast_location.guid,
                        name=toast_location.name,
                        address={
                            "formatted_address": toast_location.address_string,
                            "details": toast_location.address
                        } if toast_location.address else None,
                        timezone=toast_location.timezone,
                        currency=toast_location.currency,
                        tax_settings={
                            "tax_rates": toast_location.tax_rates,
                            "service_charges": toast_location.service_charges
                        },
                        metadata={
                            "management_group_guid": toast_location.management_group_guid,
                            "restaurant_group_guid": toast_location.restaurant_group_guid,
                            "phone": toast_location.phone,
                            "website": toast_location.website,
                            "ordering_enabled": toast_location.ordering_enabled,
                            "delivery_enabled": toast_location.delivery_enabled,
                            "takeout_enabled": toast_location.takeout_enabled,
                            "source": "toast_pos"
                        }
                    )
                else:
                    error_text = await response.text()
                    raise HTTPException(status_code=response.status, detail=f"Toast API error: {error_text}")
                    
        except Exception as e:
            self.logger.error(f"Error retrieving Toast location details: {str(e)}", exc_info=True)
            raise
    
    async def get_transactions_in_range(
        self, 
        start_date: datetime, 
        end_date: datetime,
        limit: int = 100
    ) -> List[POSTransaction]:
        """
        Get Toast orders within a date range.
        
        Args:
            start_date: Start of date range
            end_date: End of date range
            limit: Maximum number of orders to return
            
        Returns:
            List of POSTransaction objects
        """
        try:
            if not self.session:
                self.session = aiohttp.ClientSession()
            
            headers = await self._get_auth_headers()
            
            # Format dates for Toast API
            start_str = start_date.strftime("%Y-%m-%dT%H:%M:%S.%fZ")
            end_str = end_date.strftime("%Y-%m-%dT%H:%M:%S.%fZ")
            
            # Build query parameters
            params = {
                "restaurantGuid": self.restaurant_guid,
                "startDate": start_str,
                "endDate": end_str,
                "pageSize": min(limit, 100),  # Toast API page size limit
                "businessDate": start_date.strftime("%Y%m%d")  # Business date format
            }
            
            transactions = []
            page_token = None
            
            while len(transactions) < limit:
                if page_token:
                    params["pageToken"] = page_token
                
                async with self.session.get(self.endpoints['orders'], headers=headers, params=params) as response:
                    if response.status == 200:
                        data = await response.json()
                        orders = data.get("data", [])
                        
                        for order_data in orders:
                            if len(transactions) >= limit:
                                break
                            
                            transaction = await self.process_transaction(order_data)
                            transactions.append(transaction)
                        
                        # Check for more pages
                        page_token = data.get("nextPageToken")
                        if not page_token or not orders:
                            break
                    else:
                        error_text = await response.text()
                        self.logger.error(f"Error fetching Toast orders: {error_text}")
                        break
            
            return transactions
            
        except Exception as e:
            self.logger.error(f"Error retrieving Toast transactions in range: {str(e)}", exc_info=True)
            return []
    
    async def get_menu_data(self) -> Optional[ToastMenu]:
        """
        Retrieve restaurant menu data from Toast.
        
        Returns:
            ToastMenu object or None if not found
        """
        try:
            if not self.session:
                self.session = aiohttp.ClientSession()
            
            headers = await self._get_auth_headers()
            menu_url = f"{self.endpoints['menus']}"
            
            params = {"restaurantGuid": self.restaurant_guid}
            
            async with self.session.get(menu_url, headers=headers, params=params) as response:
                if response.status == 200:
                    menu_data = await response.json()
                    menus = menu_data.get("data", [])
                    
                    if menus:
                        # Return the first active menu
                        for menu in menus:
                            if menu.get("visibility") == "VISIBLE":
                                return ToastMenu(**menu)
                        
                        # If no visible menu, return first menu
                        return ToastMenu(**menus[0])
                    
                    return None
                else:
                    error_text = await response.text()
                    self.logger.error(f"Error fetching Toast menu: {error_text}")
                    return None
                    
        except Exception as e:
            self.logger.error(f"Error retrieving Toast menu: {str(e)}", exc_info=True)
            return None
    
    async def _get_auth_headers(self) -> Dict[str, str]:
        """Get authentication headers for Toast API requests."""
        return {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json",
            "Toast-Restaurant-External-ID": self.restaurant_guid
        }
    
    async def _refresh_access_token(self) -> bool:
        """
        Refresh the access token using refresh token.
        
        Returns:
            bool: True if refresh was successful
        """
        if not self.refresh_token:
            return False
        
        try:
            if not self.session:
                self.session = aiohttp.ClientSession()
            
            data = {
                "grant_type": "refresh_token",
                "refresh_token": self.refresh_token,
                "client_id": self.client_id,
                "client_secret": self.client_secret
            }
            
            async with self.session.post(self.TOKEN_URL, data=data) as response:
                if response.status == 200:
                    token_data = await response.json()
                    self.access_token = token_data.get("access_token")
                    new_refresh_token = token_data.get("refresh_token")
                    
                    if new_refresh_token:
                        self.refresh_token = new_refresh_token
                    
                    self.logger.info("Toast access token refreshed successfully")
                    return True
                else:
                    error_text = await response.text()
                    self.logger.error(f"Token refresh failed: {error_text}")
                    return False
                    
        except Exception as e:
            self.logger.error(f"Error refreshing Toast token: {str(e)}", exc_info=True)
            return False
    
    def _extract_order_items(self, toast_order: ToastOrder) -> List[Dict[str, Any]]:
        """Extract order items from Toast order."""
        items = []
        
        for selection in toast_order.selections:
            if selection.voided:
                continue
                
            item = {
                "name": selection.menu_item_guid,  # This would need menu lookup for actual name
                "guid": selection.guid,
                "menu_item_guid": selection.menu_item_guid,
                "quantity": selection.quantity,
                "unit_price": selection.base_price.dollars,
                "total_price": selection.price.dollars,
                "tax_amount": selection.tax_amount.dollars if selection.tax_amount else 0.0,
                "modifiers": selection.modifiers,
                "special_instructions": selection.special_instructions,
                "source": "toast_pos"
            }
            items.append(item)
        
        return items
    
    def _extract_customer_info(self, toast_order: ToastOrder) -> Optional[Dict[str, Any]]:
        """Extract customer information from Toast order."""
        if not toast_order.customer:
            return None
        
        customer = toast_order.customer
        return {
            "customer_guid": customer.guid,
            "name": customer.full_name,
            "first_name": customer.first_name,
            "last_name": customer.last_name,
            "email": customer.email,
            "phone": customer.phone,
            "source": "toast_pos"
        }
    
    def _extract_payment_method(self, toast_order: ToastOrder) -> str:
        """Extract primary payment method from Toast order."""
        if not toast_order.payments:
            return "UNKNOWN"
        
        # Get the payment with the largest amount
        primary_payment = max(toast_order.payments, key=lambda p: p.amount.amount)
        
        payment_type = primary_payment.type.upper()
        
        if payment_type == "CREDIT_CARD":
            card_type = primary_payment.card_type or "UNKNOWN"
            return f"CARD_{card_type}"
        elif payment_type == "CASH":
            return "CASH"
        elif payment_type == "GIFT_CARD":
            return "GIFT_CARD"
        else:
            return payment_type
    
    async def close(self):
        """Close the HTTP session."""
        if self.session:
            await self.session.close()
            self.session = None