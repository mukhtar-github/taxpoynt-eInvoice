"""Square POS connector implementation."""

import asyncio
import hashlib
import hmac
import base64
from datetime import datetime
from typing import Dict, Any, Optional, List

import httpx
from fastapi import HTTPException

from app.integrations.pos.base_pos_connector import BasePOSConnector, POSTransaction, POSLocation
from .models import (
    SquareTransaction, SquareLocation, SquareWebhookEvent, 
    SquareOrder, SquarePayment, SquareMoney, SquareWebhookSignature
)


class SquarePOSConnector(BasePOSConnector):
    """Square POS connector with real-time transaction processing."""
    
    def __init__(self, connection_config: Dict[str, Any]):
        """
        Initialize Square POS connector.
        
        Args:
            connection_config: Dictionary containing Square connection parameters
                - access_token: Square access token
                - application_id: Square application ID
                - environment: 'sandbox' or 'production'
                - webhook_signature_key: Webhook signature key for verification
                - location_id: Square location ID
        """
        super().__init__(connection_config)
        self.access_token = connection_config.get("access_token")
        self.application_id = connection_config.get("application_id")
        self.environment = connection_config.get("environment", "sandbox")
        self.webhook_signature_key = connection_config.get("webhook_signature_key")
        
        # Set base URL based on environment
        if self.environment == "production":
            self.base_url = "https://connect.squareup.com"
        else:
            self.base_url = "https://connect.squareupsandbox.com"
            
        self.headers = {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json",
            "Square-Version": "2023-10-18"  # Latest Square API version
        }
    
    async def authenticate(self) -> Dict[str, Any]:
        """
        Authenticate with Square API by testing the access token.
        
        Returns:
            Dict containing authentication results
        """
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.base_url}/v2/locations",
                    headers=self.headers
                )
                
                if response.status_code == 200:
                    locations_data = response.json()
                    self._authenticated = True
                    self._last_auth_time = datetime.now()
                    
                    return {
                        "success": True,
                        "message": "Authentication successful",
                        "locations_count": len(locations_data.get("locations", [])),
                        "application_id": self.application_id,
                        "environment": self.environment
                    }
                else:
                    error_msg = f"Authentication failed: {response.status_code}"
                    self.logger.error(error_msg)
                    raise HTTPException(status_code=response.status_code, detail=error_msg)
                    
        except Exception as e:
            self.logger.error(f"Square authentication error: {str(e)}", exc_info=True)
            raise
    
    async def verify_webhook_signature(
        self, 
        payload: bytes, 
        signature: str, 
        timestamp: Optional[str] = None
    ) -> bool:
        """
        Verify Square webhook signature.
        
        Args:
            payload: Raw webhook payload
            signature: Signature from X-Square-Signature header
            timestamp: Not used by Square (kept for interface compatibility)
            
        Returns:
            bool: True if signature is valid
        """
        if not self.webhook_signature_key:
            self.logger.warning("Webhook signature key not configured")
            return False
            
        try:
            # Square webhook signature verification
            notification_url = self.webhook_url or ""
            webhook_signature = SquareWebhookSignature(
                signature=signature,
                notification_url=notification_url,
                request_body=payload.decode('utf-8')
            )
            
            return webhook_signature.is_valid(self.webhook_signature_key)
            
        except Exception as e:
            self.logger.error(f"Webhook signature verification failed: {str(e)}", exc_info=True)
            return False
    
    async def process_transaction(self, transaction_data: Dict[str, Any]) -> POSTransaction:
        """
        Process a Square transaction from webhook or API data.
        
        Args:
            transaction_data: Raw transaction data from Square
            
        Returns:
            POSTransaction: Normalized transaction object
        """
        try:
            # Handle different Square event types
            if "payment" in transaction_data:
                payment_data = transaction_data["payment"]
                order_data = transaction_data.get("order", {})
                
                # Extract basic transaction info
                payment_id = payment_data.get("id")
                order_id = order_data.get("id") if order_data else None
                amount_money = payment_data.get("amount_money", {})
                
                # Calculate amount in base currency units
                amount = amount_money.get("amount", 0) / 100.0  # Convert from cents
                currency = amount_money.get("currency", "USD")
                
                # Determine payment method
                payment_method = self._extract_payment_method(payment_data)
                
                # Extract items from order
                items = self._extract_order_items(order_data)
                
                # Extract customer info
                customer_info = self._extract_customer_info(transaction_data)
                
                # Extract tax information
                tax_info = self._extract_tax_info(order_data)
                
                transaction = POSTransaction(
                    transaction_id=payment_id,
                    location_id=payment_data.get("location_id", self.location_id),
                    amount=amount,
                    currency=currency,
                    payment_method=payment_method,
                    timestamp=datetime.fromisoformat(
                        payment_data.get("created_at", datetime.now().isoformat()).replace('Z', '+00:00')
                    ),
                    items=items,
                    customer_info=customer_info,
                    tax_info=tax_info,
                    metadata={
                        "payment_id": payment_id,
                        "order_id": order_id,
                        "receipt_number": payment_data.get("receipt_number"),
                        "receipt_url": payment_data.get("receipt_url"),
                        "source": "square_pos",
                        "environment": self.environment
                    }
                )
                
                return transaction
                
            else:
                raise ValueError("Invalid transaction data format")
                
        except Exception as e:
            self.logger.error(f"Error processing Square transaction: {str(e)}", exc_info=True)
            raise
    
    async def get_transaction_by_id(self, transaction_id: str) -> Optional[POSTransaction]:
        """
        Retrieve Square transaction details by payment ID.
        
        Args:
            transaction_id: Square payment ID
            
        Returns:
            POSTransaction or None if not found
        """
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.base_url}/v2/payments/{transaction_id}",
                    headers=self.headers
                )
                
                if response.status_code == 200:
                    payment_data = response.json().get("payment", {})
                    
                    # Get associated order if available
                    order_id = payment_data.get("order_id")
                    order_data = {}
                    
                    if order_id:
                        order_response = await client.get(
                            f"{self.base_url}/v2/orders/{order_id}",
                            headers=self.headers
                        )
                        if order_response.status_code == 200:
                            order_data = order_response.json().get("order", {})
                    
                    # Process the transaction data
                    return await self.process_transaction({
                        "payment": payment_data,
                        "order": order_data
                    })
                    
                elif response.status_code == 404:
                    return None
                else:
                    self.logger.error(f"Error fetching transaction {transaction_id}: {response.status_code}")
                    return None
                    
        except Exception as e:
            self.logger.error(f"Error retrieving Square transaction {transaction_id}: {str(e)}", exc_info=True)
            return None
    
    async def get_location_details(self) -> POSLocation:
        """
        Get Square location/store details.
        
        Returns:
            POSLocation: Location information
        """
        try:
            location_id = self.location_id
            if not location_id:
                # Get first available location
                async with httpx.AsyncClient() as client:
                    response = await client.get(
                        f"{self.base_url}/v2/locations",
                        headers=self.headers
                    )
                    if response.status_code == 200:
                        locations = response.json().get("locations", [])
                        if locations:
                            location_id = locations[0]["id"]
                        else:
                            raise ValueError("No locations found")
                    else:
                        raise HTTPException(status_code=response.status_code, detail="Failed to fetch locations")
            
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.base_url}/v2/locations/{location_id}",
                    headers=self.headers
                )
                
                if response.status_code == 200:
                    location_data = response.json().get("location", {})
                    
                    return POSLocation(
                        location_id=location_data["id"],
                        name=location_data.get("name", ""),
                        address=location_data.get("address"),
                        timezone=location_data.get("timezone"),
                        currency=location_data.get("currency", "USD"),
                        tax_settings=location_data.get("tax_ids"),
                        metadata={
                            "business_name": location_data.get("business_name"),
                            "type": location_data.get("type"),
                            "website_url": location_data.get("website_url"),
                            "mcc": location_data.get("mcc"),
                            "coordinates": location_data.get("coordinates"),
                            "source": "square_pos"
                        }
                    )
                else:
                    raise HTTPException(status_code=response.status_code, detail="Failed to fetch location details")
                    
        except Exception as e:
            self.logger.error(f"Error retrieving Square location details: {str(e)}", exc_info=True)
            raise
    
    async def get_transactions_in_range(
        self, 
        start_date: datetime, 
        end_date: datetime,
        limit: int = 100
    ) -> List[POSTransaction]:
        """
        Get Square transactions within a date range.
        
        Args:
            start_date: Start of date range
            end_date: End of date range
            limit: Maximum number of transactions to return
            
        Returns:
            List of POSTransaction objects
        """
        try:
            async with httpx.AsyncClient() as client:
                # Square Payments API search
                search_body = {
                    "filter": {
                        "location_id": self.location_id,
                        "created_at": {
                            "start_at": start_date.isoformat(),
                            "end_at": end_date.isoformat()
                        }
                    },
                    "sort": {
                        "order": "DESC",
                        "sort_field": "CREATED_AT"
                    },
                    "limit": min(limit, 500)  # Square API limit
                }
                
                response = await client.post(
                    f"{self.base_url}/v2/payments/search",
                    headers=self.headers,
                    json=search_body
                )
                
                if response.status_code == 200:
                    payments_data = response.json().get("payments", [])
                    transactions = []
                    
                    for payment in payments_data:
                        # Get associated order for each payment
                        order_data = {}
                        order_id = payment.get("order_id")
                        
                        if order_id:
                            order_response = await client.get(
                                f"{self.base_url}/v2/orders/{order_id}",
                                headers=self.headers
                            )
                            if order_response.status_code == 200:
                                order_data = order_response.json().get("order", {})
                        
                        # Process transaction
                        transaction = await self.process_transaction({
                            "payment": payment,
                            "order": order_data
                        })
                        transactions.append(transaction)
                    
                    return transactions
                    
                else:
                    self.logger.error(f"Error searching Square transactions: {response.status_code}")
                    return []
                    
        except Exception as e:
            self.logger.error(f"Error retrieving Square transactions in range: {str(e)}", exc_info=True)
            return []
    
    def _extract_payment_method(self, payment_data: Dict[str, Any]) -> str:
        """Extract payment method from Square payment data."""
        source_type = payment_data.get("source_type", "UNKNOWN")
        
        if source_type == "CARD":
            card_details = payment_data.get("card_details", {})
            card = card_details.get("card", {})
            return f"CARD_{card.get('card_brand', 'UNKNOWN')}"
        elif source_type == "CASH":
            return "CASH"
        elif source_type == "EXTERNAL":
            return "EXTERNAL"
        else:
            return source_type
    
    def _extract_order_items(self, order_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Extract order items from Square order data."""
        items = []
        line_items = order_data.get("line_items", [])
        
        for item in line_items:
            items.append({
                "name": item.get("name", ""),
                "quantity": item.get("quantity", "1"),
                "unit_price": item.get("base_price_money", {}).get("amount", 0) / 100.0,
                "total_price": item.get("gross_sales_money", {}).get("amount", 0) / 100.0,
                "tax_amount": item.get("total_tax_money", {}).get("amount", 0) / 100.0,
                "discount_amount": item.get("total_discount_money", {}).get("amount", 0) / 100.0,
                "variation_name": item.get("variation_name"),
                "catalog_object_id": item.get("catalog_object_id"),
                "metadata": item.get("metadata", {})
            })
        
        return items
    
    def _extract_customer_info(self, transaction_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Extract customer information from Square transaction data."""
        order_data = transaction_data.get("order", {})
        customer_id = order_data.get("customer_id")
        
        if customer_id:
            return {
                "customer_id": customer_id,
                "source": "square_pos"
            }
        
        return None
    
    def _extract_tax_info(self, order_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Extract tax information from Square order data."""
        total_tax_money = order_data.get("total_tax_money", {})
        
        if total_tax_money.get("amount", 0) > 0:
            return {
                "total_tax": total_tax_money.get("amount", 0) / 100.0,
                "currency": total_tax_money.get("currency", "USD"),
                "source": "square_pos"
            }
        
        return None