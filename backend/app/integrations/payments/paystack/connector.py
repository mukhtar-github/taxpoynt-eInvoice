"""
Paystack payment gateway integration for Nigeria
"""

import httpx
import hashlib
import hmac
from typing import Dict, Any, Optional
from datetime import datetime

from ..base import (
    BasePaymentConnector, 
    PaymentInitResponse, 
    PaymentVerificationResponse, 
    WebhookResponse,
    PaymentStatus,
    PaymentChannel
)


class PaystackConnector(BasePaymentConnector):
    """Paystack payment gateway integration for Nigeria."""
    
    def _get_base_url(self) -> str:
        """Get Paystack API base URL"""
        return "https://api.paystack.co"
    
    def _get_headers(self) -> Dict[str, str]:
        """Get headers for Paystack API requests"""
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
        """Initialize Paystack payment."""
        
        # Convert amount to kobo (smallest NGN unit)
        amount_kobo = amount if amount > 100 else self.naira_to_kobo(amount)
        
        payload = {
            "amount": amount_kobo,
            "email": email,
            "reference": reference,
            "currency": "NGN",
            "channels": ["card", "bank", "ussd", "qr", "mobile_money"],
            "metadata": metadata or {}
        }
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.base_url}/transaction/initialize",
                json=payload,
                headers=self._get_headers()
            )
            
            if response.status_code != 200:
                raise Exception(f"Paystack initialization failed: {response.text}")
            
            data = response.json()["data"]
            
            return PaymentInitResponse(
                payment_id=data["reference"],
                reference=reference,
                authorization_url=data["authorization_url"],
                access_code=data["access_code"],
                status=PaymentStatus.PENDING,
                amount=amount_kobo,
                currency="NGN",
                channels=[
                    PaymentChannel.CARD,
                    PaymentChannel.BANK_TRANSFER,
                    PaymentChannel.USSD,
                    PaymentChannel.QR_CODE,
                    PaymentChannel.MOBILE_MONEY
                ]
            )
    
    async def verify_payment(self, reference: str) -> PaymentVerificationResponse:
        """Verify payment status with Paystack."""
        
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.base_url}/transaction/verify/{reference}",
                headers=self._get_headers()
            )
            
            if response.status_code != 200:
                raise Exception(f"Paystack verification failed: {response.text}")
            
            data = response.json()["data"]
            
            # Map Paystack status to our status
            status_mapping = {
                "success": PaymentStatus.SUCCESS,
                "failed": PaymentStatus.FAILED,
                "abandoned": PaymentStatus.CANCELLED,
                "pending": PaymentStatus.PENDING
            }
            
            # Map Paystack channel to our channel
            channel_mapping = {
                "card": PaymentChannel.CARD,
                "bank": PaymentChannel.BANK_TRANSFER,
                "ussd": PaymentChannel.USSD,
                "qr": PaymentChannel.QR_CODE,
                "mobile_money": PaymentChannel.MOBILE_MONEY
            }
            
            paid_at = None
            if data.get("paid_at"):
                paid_at = datetime.fromisoformat(data["paid_at"].replace("Z", "+00:00"))
            
            return PaymentVerificationResponse(
                payment_id=str(data["id"]),
                reference=data["reference"],
                status=status_mapping.get(data["status"], PaymentStatus.PENDING),
                amount=data["amount"],
                currency=data["currency"],
                channel=channel_mapping.get(data.get("channel")),
                gateway_response=data.get("gateway_response", ""),
                paid_at=paid_at,
                customer_email=data["customer"]["email"],
                customer_name=data["customer"].get("first_name"),
                metadata=data.get("metadata", {})
            )
    
    async def process_webhook(self, payload: Dict[str, Any]) -> WebhookResponse:
        """Process Paystack webhook events."""
        
        event_type = payload.get("event")
        data = payload.get("data", {})
        
        if event_type == "charge.success":
            return WebhookResponse(
                event_type=event_type,
                payment_id=str(data.get("id")),
                reference=data.get("reference"),
                status=PaymentStatus.SUCCESS,
                processed=True,
                invoice_updated=True
            )
        
        elif event_type == "charge.failed":
            return WebhookResponse(
                event_type=event_type,
                payment_id=str(data.get("id")),
                reference=data.get("reference"),
                status=PaymentStatus.FAILED,
                processed=True
            )
        
        else:
            return WebhookResponse(
                event_type=event_type or "unknown",
                payment_id=str(data.get("id", "")),
                reference=data.get("reference", ""),
                status=PaymentStatus.PENDING,
                processed=False,
                error=f"Unhandled event type: {event_type}"
            )
    
    def verify_webhook_signature(self, payload: str, signature: str) -> bool:
        """Verify webhook signature from Paystack"""
        if not self.config.get("webhook_secret"):
            return True  # Skip verification if no webhook secret configured
        
        expected_signature = hmac.new(
            self.config["webhook_secret"].encode('utf-8'),
            payload.encode('utf-8'),
            hashlib.sha512
        ).hexdigest()
        
        return hmac.compare_digest(expected_signature, signature)
    
    async def get_payment_channels(self) -> list[PaymentChannel]:
        """Get available payment channels for Paystack"""
        return [
            PaymentChannel.CARD,
            PaymentChannel.BANK_TRANSFER,
            PaymentChannel.USSD,
            PaymentChannel.QR_CODE,
            PaymentChannel.MOBILE_MONEY
        ]
    
    async def get_supported_banks(self) -> list[Dict[str, str]]:
        """Get list of supported banks for bank transfer"""
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.base_url}/bank",
                headers=self._get_headers()
            )
            
            if response.status_code == 200:
                banks = response.json()["data"]
                return [{"code": bank["code"], "name": bank["name"]} for bank in banks]
            
            return []
    
    async def create_transfer_recipient(
        self, 
        account_number: str, 
        bank_code: str, 
        name: str
    ) -> Dict[str, Any]:
        """Create transfer recipient for payouts"""
        payload = {
            "type": "nuban",
            "name": name,
            "account_number": account_number,
            "bank_code": bank_code,
            "currency": "NGN"
        }
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.base_url}/transferrecipient",
                json=payload,
                headers=self._get_headers()
            )
            
            if response.status_code == 201:
                return response.json()["data"]
            
            raise Exception(f"Failed to create transfer recipient: {response.text}")
    
    async def initiate_transfer(
        self,
        amount: int,
        recipient_code: str,
        reason: str = "Invoice payment"
    ) -> Dict[str, Any]:
        """Initiate transfer to recipient"""
        payload = {
            "source": "balance",
            "amount": amount,
            "recipient": recipient_code,
            "reason": reason
        }
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.base_url}/transfer",
                json=payload,
                headers=self._get_headers()
            )
            
            if response.status_code == 200:
                return response.json()["data"]
            
            raise Exception(f"Failed to initiate transfer: {response.text}")