"""Square POS connector implementation using official Square Python SDK."""

import asyncio
import hashlib
import hmac
import base64
from datetime import datetime
from typing import Dict, Any, Optional, List

from square.client import Client
from square.models import CreatePaymentRequest, Money, SearchOrdersRequest, SearchOrdersQuery, SearchOrdersFilter
from square.exceptions import ApiException
from fastapi import HTTPException

from app.integrations.pos.base_pos_connector import BasePOSConnector, POSTransaction, POSLocation
from .models import (
    SquareTransaction, SquareLocation, SquareWebhookEvent, 
    SquareOrder, SquarePayment, SquareMoney, SquareWebhookSignature
)
from .firs_transformer import SquareToFIRSTransformer


class SquarePOSConnector(BasePOSConnector):
    """Square POS connector with real-time transaction processing."""
    
    def __init__(self, connection_config: Dict[str, Any]):
        """
        Initialize Square POS connector using official Square SDK.
        
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
        
        # Initialize Square client with official SDK
        self.client = Client(
            access_token=self.access_token,
            environment=self.environment
        )
        
        # Get API clients
        self.locations_api = self.client.locations
        self.orders_api = self.client.orders
        self.payments_api = self.client.payments
        self.customers_api = self.client.customers
        self.catalog_api = self.client.catalog
        self.webhooks_api = self.client.webhook_subscriptions
        
        # Initialize FIRS transformer if configuration is provided
        firs_config = connection_config.get("firs_config", {})
        if firs_config:
            self.firs_transformer = SquareToFIRSTransformer(firs_config)
        else:
            self.firs_transformer = None
    
    async def authenticate(self) -> Dict[str, Any]:
        """
        Authenticate with Square API using official SDK.
        
        Returns:
            Dict containing authentication results
        """
        try:
            # Test authentication by fetching locations
            result = self.locations_api.list_locations()
            
            if result.is_success():
                locations = result.body.get('locations', [])
                self._authenticated = True
                self._last_auth_time = datetime.now()
                
                return {
                    "success": True,
                    "message": "Authentication successful",
                    "locations_count": len(locations),
                    "application_id": self.application_id,
                    "environment": self.environment
                }
            else:
                errors = result.errors
                error_msg = f"Authentication failed: {[error['detail'] for error in errors]}"
                self.logger.error(error_msg)
                raise HTTPException(status_code=401, detail=error_msg)
                    
        except ApiException as e:
            self.logger.error(f"Square API authentication error: {str(e)}", exc_info=True)
            raise HTTPException(status_code=401, detail=f"Square API error: {str(e)}")
        except Exception as e:
            self.logger.error(f"Square authentication error: {str(e)}", exc_info=True)
            raise HTTPException(status_code=500, detail=f"Authentication error: {str(e)}")
    
    async def verify_webhook_signature(
        self, 
        payload: bytes, 
        signature: str, 
        timestamp: Optional[str] = None
    ) -> bool:
        """
        Verify Square webhook signature according to Square specifications.
        
        Square webhook signature verification process:
        1. Combine notification URL + request body
        2. Create HMAC-SHA1 hash using webhook signature key
        3. Base64 encode the hash
        4. Compare with provided signature
        
        Args:
            payload: Raw webhook payload bytes
            signature: Signature from X-Square-Signature header
            timestamp: Not used by Square (kept for interface compatibility)
            
        Returns:
            bool: True if signature is valid
        """
        if not self.webhook_signature_key:
            self.logger.warning("Webhook signature key not configured")
            return False
            
        try:
            # Square webhook signature verification process
            notification_url = self.webhook_url or ""
            request_body = payload.decode('utf-8')
            
            # Step 1: Combine notification URL with request body
            string_to_sign = notification_url + request_body
            
            # Step 2: Create HMAC-SHA1 hash
            computed_hash = hmac.new(
                self.webhook_signature_key.encode('utf-8'),
                string_to_sign.encode('utf-8'),
                hashlib.sha1
            ).digest()
            
            # Step 3: Base64 encode the hash
            computed_signature = base64.b64encode(computed_hash).decode('utf-8')
            
            # Step 4: Compare signatures using constant-time comparison
            is_valid = hmac.compare_digest(signature, computed_signature)
            
            if not is_valid:
                self.logger.warning(
                    f"Square webhook signature verification failed. "
                    f"Expected: {computed_signature[:10]}..., "
                    f"Received: {signature[:10]}..."
                )
            
            return is_valid
            
        except UnicodeDecodeError as e:
            self.logger.error(f"Webhook payload decode error: {str(e)}")
            return False
        except Exception as e:
            self.logger.error(f"Webhook signature verification failed: {str(e)}", exc_info=True)
            return False
    
    def verify_webhook_signature_sync(
        self,
        payload: bytes,
        signature: str,
        notification_url: str
    ) -> bool:
        """
        Synchronous version of webhook signature verification.
        
        This method can be used in non-async contexts.
        
        Args:
            payload: Raw webhook payload bytes
            signature: Signature from X-Square-Signature header
            notification_url: The webhook notification URL
            
        Returns:
            bool: True if signature is valid
        """
        if not self.webhook_signature_key:
            return False
            
        try:
            request_body = payload.decode('utf-8')
            string_to_sign = notification_url + request_body
            
            computed_hash = hmac.new(
                self.webhook_signature_key.encode('utf-8'),
                string_to_sign.encode('utf-8'),
                hashlib.sha1
            ).digest()
            
            computed_signature = base64.b64encode(computed_hash).decode('utf-8')
            return hmac.compare_digest(signature, computed_signature)
            
        except Exception:
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
        Retrieve Square transaction details by payment ID using official SDK.
        
        Args:
            transaction_id: Square payment ID
            
        Returns:
            POSTransaction or None if not found
        """
        try:
            # Get payment details
            result = self.payments_api.get_payment(payment_id=transaction_id)
            
            if result.is_success():
                payment_data = result.body.get("payment", {})
                
                # Get associated order if available
                order_id = payment_data.get("order_id")
                order_data = {}
                
                if order_id:
                    order_result = self.orders_api.retrieve_order(order_id=order_id)
                    if order_result.is_success():
                        order_data = order_result.body.get("order", {})
                
                # Process the transaction data
                return await self.process_transaction({
                    "payment": payment_data,
                    "order": order_data
                })
                
            elif result.is_error():
                errors = result.errors
                if any(error.get('code') == 'NOT_FOUND' for error in errors):
                    return None
                else:
                    self.logger.error(f"Error fetching transaction {transaction_id}: {errors}")
                    return None
                    
        except ApiException as e:
            self.logger.error(f"Square API error retrieving transaction {transaction_id}: {str(e)}", exc_info=True)
            return None
        except Exception as e:
            self.logger.error(f"Error retrieving Square transaction {transaction_id}: {str(e)}", exc_info=True)
            return None
    
    async def get_location_details(self) -> POSLocation:
        """
        Get Square location/store details using official SDK.
        
        Returns:
            POSLocation: Location information
        """
        try:
            location_id = self.location_id
            if not location_id:
                # Get first available location
                result = self.locations_api.list_locations()
                if result.is_success():
                    locations = result.body.get("locations", [])
                    if locations:
                        location_id = locations[0]["id"]
                    else:
                        raise ValueError("No locations found")
                else:
                    errors = result.errors
                    raise HTTPException(status_code=400, detail=f"Failed to fetch locations: {errors}")
            
            # Get specific location details
            result = self.locations_api.retrieve_location(location_id=location_id)
            
            if result.is_success():
                location_data = result.body.get("location", {})
                
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
                errors = result.errors
                raise HTTPException(status_code=400, detail=f"Failed to fetch location details: {errors}")
                    
        except ApiException as e:
            self.logger.error(f"Square API error retrieving location details: {str(e)}", exc_info=True)
            raise HTTPException(status_code=500, detail=f"Square API error: {str(e)}")
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
        Get Square transactions within a date range using official SDK.
        
        Args:
            start_date: Start of date range
            end_date: End of date range
            limit: Maximum number of transactions to return
            
        Returns:
            List of POSTransaction objects
        """
        try:
            from square.models import SearchPaymentsRequest, SearchPaymentsQuery, SearchPaymentsFilter
            from square.models import TimeRange, SearchPaymentsSort, SortOrder
            
            # Create time range filter
            time_range = TimeRange(
                start_at=start_date.isoformat(),
                end_at=end_date.isoformat()
            )
            
            # Create search filter
            search_filter = SearchPaymentsFilter(
                location_id=self.location_id,
                created_at=time_range
            )
            
            # Create search query
            search_query = SearchPaymentsQuery(
                filter=search_filter,
                sort=SearchPaymentsSort(
                    order=SortOrder.DESC,
                    sort_field="CREATED_AT"
                )
            )
            
            # Create search request
            search_request = SearchPaymentsRequest(
                query=search_query,
                limit=min(limit, 500)  # Square API limit
            )
            
            # Execute search
            result = self.payments_api.search_payments(body=search_request)
            
            if result.is_success():
                payments_data = result.body.get("payments", [])
                transactions = []
                
                for payment in payments_data:
                    # Get associated order for each payment
                    order_data = {}
                    order_id = payment.get("order_id")
                    
                    if order_id:
                        order_result = self.orders_api.retrieve_order(order_id=order_id)
                        if order_result.is_success():
                            order_data = order_result.body.get("order", {})
                    
                    # Process transaction
                    transaction = await self.process_transaction({
                        "payment": payment,
                        "order": order_data
                    })
                    transactions.append(transaction)
                
                return transactions
                
            else:
                errors = result.errors
                self.logger.error(f"Error searching Square transactions: {errors}")
                return []
                    
        except ApiException as e:
            self.logger.error(f"Square API error retrieving transactions in range: {str(e)}", exc_info=True)
            return []
        except Exception as e:
            self.logger.error(f"Error retrieving Square transactions in range: {str(e)}", exc_info=True)
            return []
    
    async def generate_firs_invoice(
        self,
        transaction: POSTransaction,
        customer_info: Optional[Dict[str, Any]] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Generate FIRS-compliant invoice from Square transaction.
        
        Args:
            transaction: POS transaction object
            customer_info: Optional customer information
            
        Returns:
            Dict containing FIRS invoice or None if transformer not configured
        """
        if not self.firs_transformer:
            self.logger.warning("FIRS transformer not configured")
            return None
        
        try:
            # Get location details
            location = await self.get_location_details()
            
            # Transform transaction to FIRS format
            firs_invoice = self.firs_transformer.transform_transaction_to_firs_invoice(
                transaction, location, customer_info
            )
            
            # Validate the generated invoice
            validation_result = self.firs_transformer.validate_firs_invoice(firs_invoice)
            
            if not validation_result["valid"]:
                self.logger.error(f"Generated FIRS invoice validation failed: {validation_result['errors']}")
                raise ValueError(f"Invoice validation failed: {validation_result['errors']}")
            
            self.logger.info(f"Successfully generated FIRS invoice for transaction {transaction.transaction_id}")
            return firs_invoice
            
        except Exception as e:
            self.logger.error(f"Error generating FIRS invoice: {str(e)}", exc_info=True)
            raise
    
    async def process_transaction_with_firs_invoice(
        self,
        transaction_data: Dict[str, Any],
        auto_generate_invoice: bool = True
    ) -> Dict[str, Any]:
        """
        Process Square transaction and optionally generate FIRS invoice.
        
        Args:
            transaction_data: Raw transaction data from Square
            auto_generate_invoice: Whether to automatically generate FIRS invoice
            
        Returns:
            Dict containing transaction and optional FIRS invoice
        """
        try:
            # Process the transaction
            transaction = await self.process_transaction(transaction_data)
            
            result = {
                "transaction": transaction,
                "firs_invoice": None,
                "invoice_generated": False
            }
            
            # Generate FIRS invoice if enabled and transformer is configured
            if auto_generate_invoice and self.firs_transformer:
                try:
                    # Get customer info if available
                    customer_info = None
                    if transaction.customer_info and transaction.customer_info.get("customer_id"):
                        customer_info = await self._get_customer_details(
                            transaction.customer_info["customer_id"]
                        )
                    
                    firs_invoice = await self.generate_firs_invoice(transaction, customer_info)
                    result["firs_invoice"] = firs_invoice
                    result["invoice_generated"] = True
                    
                except Exception as e:
                    self.logger.error(f"Failed to generate FIRS invoice: {str(e)}")
                    result["invoice_error"] = str(e)
            
            return result
            
        except Exception as e:
            self.logger.error(f"Error processing transaction with FIRS invoice: {str(e)}", exc_info=True)
            raise
    
    async def _get_customer_details(self, customer_id: str) -> Optional[Dict[str, Any]]:
        """
        Get customer details from Square.
        
        Args:
            customer_id: Square customer ID
            
        Returns:
            Dict containing customer information or None
        """
        try:
            result = self.customers_api.retrieve_customer(customer_id=customer_id)
            
            if result.is_success():
                customer_data = result.body.get("customer", {})
                return {
                    "customer_id": customer_data.get("id"),
                    "name": f"{customer_data.get('given_name', '')} {customer_data.get('family_name', '')}".strip(),
                    "email": customer_data.get("email_address"),
                    "phone": customer_data.get("phone_number"),
                    "address": customer_data.get("address"),
                    "reference_id": customer_data.get("reference_id"),
                    "company_name": customer_data.get("company_name")
                }
            else:
                self.logger.warning(f"Could not retrieve customer {customer_id}")
                return None
                
        except ApiException as e:
            self.logger.error(f"Square API error retrieving customer {customer_id}: {str(e)}")
            return None
        except Exception as e:
            self.logger.error(f"Error retrieving customer {customer_id}: {str(e)}")
            return None
    
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