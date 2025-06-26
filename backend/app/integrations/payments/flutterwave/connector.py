"""
Flutterwave payment gateway integration for Nigeria and Africa
"""

import httpx
import hashlib
import hmac
from typing import Dict, Any, Optional, List
from datetime import datetime

from ..base import (
    BasePaymentConnector, 
    PaymentInitResponse, 
    PaymentVerificationResponse, 
    WebhookResponse,
    PaymentStatus,
    PaymentChannel
)


class FlutterwaveConnector(BasePaymentConnector):
    """Flutterwave payment gateway integration."""
    
    def _get_base_url(self) -> str:
        """Get Flutterwave API base URL"""
        return "https://api.flutterwave.com/v3"
    
    def _get_headers(self) -> Dict[str, str]:
        """Get headers for Flutterwave API requests"""
        return {
            "Authorization": f"Bearer {self.secret_key}",
            "Content-Type": "application/json"
        }
    
    async def initialize_payment(
        self,
        amount: int,
        email: str,
        reference: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> PaymentInitResponse:
        """Initialize Flutterwave payment."""
        
        # Flutterwave uses actual currency amounts, not kobo
        amount_ngn = amount if amount > 100 else amount
        
        payload = {
            "tx_ref": reference,
            "amount": str(amount_ngn),
            "currency": "NGN",
            "redirect_url": metadata.get("redirect_url", ""),
            "payment_options": "card,mobilemoney,ussd,banktransfer",
            "customer": {
                "email": email,
                "phone_number": metadata.get("phone_number", ""),
                "name": metadata.get("customer_name", email.split("@")[0])
            },
            "customizations": {
                "title": "TaxPoynt Invoice Payment",
                "description": metadata.get("description", "Invoice payment"),
                "logo": metadata.get("logo_url", "")
            },
            "meta": metadata or {}
        }
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.base_url}/payments",
                json=payload,
                headers=self._get_headers()
            )
            
            if response.status_code != 200:
                raise Exception(f"Flutterwave initialization failed: {response.text}")
            
            data = response.json()["data"]
            
            return PaymentInitResponse(
                payment_id=str(data["id"]),
                reference=reference,
                authorization_url=data["link"],
                status=PaymentStatus.PENDING,
                amount=self.naira_to_kobo(float(amount_ngn)),
                currency="NGN",
                channels=[
                    PaymentChannel.CARD,
                    PaymentChannel.MOBILE_MONEY,
                    PaymentChannel.USSD,
                    PaymentChannel.BANK_TRANSFER
                ]
            )
    
    async def verify_payment(self, reference: str) -> PaymentVerificationResponse:
        """Verify payment status with Flutterwave."""
        
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.base_url}/transactions/verify_by_reference",
                params={"tx_ref": reference},
                headers=self._get_headers()
            )
            
            if response.status_code != 200:
                raise Exception(f"Flutterwave verification failed: {response.text}")
            
            data = response.json()["data"]
            
            # Map Flutterwave status to our status
            status_mapping = {
                "successful": PaymentStatus.SUCCESS,
                "failed": PaymentStatus.FAILED,
                "cancelled": PaymentStatus.CANCELLED,
                "pending": PaymentStatus.PENDING
            }
            
            # Map Flutterwave processor to our channel
            channel_mapping = {
                "card": PaymentChannel.CARD,
                "account": PaymentChannel.BANK_TRANSFER,
                "mobilemoney": PaymentChannel.MOBILE_MONEY,
                "ussd": PaymentChannel.USSD,
                "banktransfer": PaymentChannel.BANK_TRANSFER
            }
            
            created_at = None
            if data.get("created_at"):
                created_at = datetime.fromisoformat(data["created_at"].replace("Z", "+00:00"))
            
            return PaymentVerificationResponse(
                payment_id=str(data["id"]),
                reference=data["tx_ref"],
                status=status_mapping.get(data["status"], PaymentStatus.PENDING),
                amount=self.naira_to_kobo(float(data["amount"])),
                currency=data["currency"],
                channel=channel_mapping.get(data.get("processor_response", "").lower()),
                gateway_response=data.get("processor_response", ""),
                paid_at=created_at,
                customer_email=data["customer"]["email"],
                customer_name=data["customer"].get("name"),
                metadata=data.get("meta", {})
            )
    
    async def process_webhook(self, payload: Dict[str, Any]) -> WebhookResponse:
        """Process Flutterwave webhook events."""
        
        event_type = payload.get("event")
        data = payload.get("data", {})
        
        if event_type == "charge.completed":
            # Check if payment was successful
            if data.get("status") == "successful":
                return WebhookResponse(
                    event_type=event_type,
                    payment_id=str(data.get("id")),
                    reference=data.get("tx_ref"),
                    status=PaymentStatus.SUCCESS,
                    processed=True,
                    invoice_updated=True
                )
            else:
                return WebhookResponse(
                    event_type=event_type,
                    payment_id=str(data.get("id")),
                    reference=data.get("tx_ref"),
                    status=PaymentStatus.FAILED,
                    processed=True
                )
        
        else:
            return WebhookResponse(
                event_type=event_type or "unknown",
                payment_id=str(data.get("id", "")),
                reference=data.get("tx_ref", ""),
                status=PaymentStatus.PENDING,
                processed=False,
                error=f"Unhandled event type: {event_type}"
            )
    
    def verify_webhook_signature(self, payload: str, signature: str) -> bool:
        """Verify webhook signature from Flutterwave"""
        if not self.config.get("webhook_secret"):
            return True  # Skip verification if no webhook secret configured
        
        expected_signature = hmac.new(
            self.config["webhook_secret"].encode('utf-8'),
            payload.encode('utf-8'),
            hashlib.sha256
        ).hexdigest()
        
        return hmac.compare_digest(expected_signature, signature)
    
    async def get_payment_channels(self) -> List[PaymentChannel]:
        """Get available payment channels for Flutterwave"""
        return [
            PaymentChannel.CARD,
            PaymentChannel.MOBILE_MONEY,
            PaymentChannel.USSD,
            PaymentChannel.BANK_TRANSFER
        ]
    
    async def get_supported_banks(self) -> List[Dict[str, str]]:
        """Get list of supported banks for Nigeria"""
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.base_url}/banks/ng",
                headers=self._get_headers()
            )
            
            if response.status_code == 200:
                banks = response.json()["data"]
                return [{"code": bank["code"], "name": bank["name"]} for bank in banks]
            
            return []
    
    async def create_payment_link(
        self,
        amount: int,
        email: str,
        reference: str,
        title: str = "TaxPoynt Invoice",
        description: str = "Invoice Payment",
        currency: str = "NGN"
    ) -> Dict[str, Any]:
        """Create Flutterwave payment link."""
        
        payload = {
            "tx_ref": reference,
            "amount": str(amount),
            "currency": currency,
            "customer": {
                "email": email
            },
            "customizations": {
                "title": title,
                "description": description
            }
        }
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.base_url}/payment-links",
                json=payload,
                headers=self._get_headers()
            )
            
            if response.status_code == 200:
                return response.json()["data"]
            
            raise Exception(f"Failed to create payment link: {response.text}")
    
    async def get_transaction_fee(self, amount: int, currency: str = "NGN") -> Dict[str, Any]:
        """Get transaction fee for an amount"""
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.base_url}/transactions/fee",
                params={"amount": amount, "currency": currency},
                headers=self._get_headers()
            )
            
            if response.status_code == 200:
                return response.json()["data"]
            
            return {"fee": 0, "currency": currency}
    
    async def get_exchange_rates(self, from_currency: str, to_currency: str) -> Dict[str, Any]:
        """Get exchange rates between currencies"""
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.base_url}/fx-rates",
                params={"from": from_currency, "to": to_currency, "amount": 1},
                headers=self._get_headers()
            )
            
            if response.status_code == 200:
                return response.json()["data"]
            
            return {"rate": 1.0}
    
    async def initiate_bulk_transfer(
        self,
        transfers: List[Dict[str, Any]],
        title: str = "TaxPoynt Bulk Transfer"
    ) -> Dict[str, Any]:
        """Initiate bulk transfer for multiple recipients"""
        
        payload = {
            "title": title,
            "bulk_data": transfers
        }
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.base_url}/bulk-transfers",
                json=payload,
                headers=self._get_headers()
            )
            
            if response.status_code == 200:
                return response.json()["data"]
            
            raise Exception(f"Failed to initiate bulk transfer: {response.text}")
    
    async def get_supported_countries(self) -> List[Dict[str, str]]:
        """Get list of supported countries"""
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.base_url}/countries",
                headers=self._get_headers()
            )
            
            if response.status_code == 200:
                countries = response.json()["data"]
                return [{"code": country["iso_code"], "name": country["name"]} for country in countries]
            
            return []