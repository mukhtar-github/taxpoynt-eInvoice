"""
Nigerian SMS Service for Payment Notifications
Supports major Nigerian SMS providers
"""

import asyncio
import aiohttp
from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Any
from datetime import datetime
from enum import Enum
from pydantic import BaseModel
import logging

from ..core.config import settings

logger = logging.getLogger(__name__)

class SMSProvider(str, Enum):
    """SMS provider enumeration"""
    TERMII = "termii"
    INFOBIP = "infobip"
    SMARTSMS = "smartsms"
    TWILIO = "twilio"
    BULK_SMS_NG = "bulk_sms_ng"

class SMSStatus(str, Enum):
    """SMS delivery status"""
    PENDING = "pending"
    SENT = "sent"
    DELIVERED = "delivered"
    FAILED = "failed"
    EXPIRED = "expired"

class SMSMessage(BaseModel):
    """SMS message structure"""
    id: str
    to: str
    message: str
    sender_id: str
    status: SMSStatus
    provider: SMSProvider
    sent_at: Optional[datetime] = None
    delivered_at: Optional[datetime] = None
    error_message: Optional[str] = None
    cost: Optional[float] = None
    metadata: Dict[str, Any] = {}

class SMSResponse(BaseModel):
    """SMS sending response"""
    success: bool
    message_id: Optional[str] = None
    status: SMSStatus
    error: Optional[str] = None
    cost: Optional[float] = None
    provider: SMSProvider

class BaseSMSProvider(ABC):
    """Base SMS provider interface"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.base_url = self._get_base_url()
        self.api_key = config.get("api_key")
        self.sender_id = config.get("sender_id", "TaxPoynt")
        
    @abstractmethod
    def _get_base_url(self) -> str:
        """Get provider base URL"""
        pass
    
    @abstractmethod
    async def send_sms(self, to: str, message: str, sender_id: Optional[str] = None) -> SMSResponse:
        """Send SMS message"""
        pass
    
    @abstractmethod
    async def check_status(self, message_id: str) -> SMSStatus:
        """Check message delivery status"""
        pass
    
    def format_phone_number(self, phone: str) -> str:
        """Format phone number for Nigerian standards"""
        # Remove any non-digit characters
        phone = ''.join(filter(str.isdigit, phone))
        
        # Handle different Nigerian phone number formats
        if phone.startswith('234'):
            return phone  # Already in international format
        elif phone.startswith('0'):
            return '234' + phone[1:]  # Remove leading 0 and add country code
        elif len(phone) == 10:
            return '234' + phone  # Add country code to 10-digit number
        elif len(phone) == 11 and phone.startswith('0'):
            return '234' + phone[1:]  # 11-digit with leading 0
        else:
            return phone  # Return as-is if format is unclear

class TermiiSMSProvider(BaseSMSProvider):
    """Termii SMS provider - Nigerian focused"""
    
    def _get_base_url(self) -> str:
        return "https://api.ng.termii.com/api"
    
    async def send_sms(self, to: str, message: str, sender_id: Optional[str] = None) -> SMSResponse:
        """Send SMS via Termii"""
        
        url = f"{self.base_url}/sms/send"
        sender = sender_id or self.sender_id
        phone = self.format_phone_number(to)
        
        payload = {
            "to": phone,
            "from": sender,
            "sms": message,
            "type": "plain",
            "api_key": self.api_key,
            "channel": "generic"
        }
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(url, json=payload) as response:
                    if response.status == 200:
                        data = await response.json()
                        return SMSResponse(
                            success=True,
                            message_id=data.get("message_id"),
                            status=SMSStatus.SENT,
                            provider=SMSProvider.TERMII,
                            cost=data.get("cost", 0)
                        )
                    else:
                        error_data = await response.text()
                        return SMSResponse(
                            success=False,
                            status=SMSStatus.FAILED,
                            error=f"HTTP {response.status}: {error_data}",
                            provider=SMSProvider.TERMII
                        )
        except Exception as e:
            logger.error(f"Termii SMS error: {str(e)}")
            return SMSResponse(
                success=False,
                status=SMSStatus.FAILED,
                error=str(e),
                provider=SMSProvider.TERMII
            )
    
    async def check_status(self, message_id: str) -> SMSStatus:
        """Check message status via Termii"""
        
        url = f"{self.base_url}/sms/inbox"
        params = {
            "api_key": self.api_key,
            "message_id": message_id
        }
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, params=params) as response:
                    if response.status == 200:
                        data = await response.json()
                        status = data.get("status", "pending")
                        return SMSStatus(status.lower())
                    else:
                        return SMSStatus.FAILED
        except Exception:
            return SMSStatus.FAILED

class TwilioSMSProvider(BaseSMSProvider):
    """Twilio SMS provider"""
    
    def _get_base_url(self) -> str:
        account_sid = self.config.get("account_sid")
        return f"https://api.twilio.com/2010-04-01/Accounts/{account_sid}"
    
    async def send_sms(self, to: str, message: str, sender_id: Optional[str] = None) -> SMSResponse:
        """Send SMS via Twilio"""
        
        url = f"{self.base_url}/Messages.json"
        phone = self.format_phone_number(to)
        sender = sender_id or self.config.get("phone_number", self.sender_id)
        
        # Twilio requires HTTP Basic Auth
        import base64
        account_sid = self.config.get("account_sid")
        auth_token = self.config.get("auth_token")
        auth_string = base64.b64encode(f"{account_sid}:{auth_token}".encode()).decode()
        
        headers = {
            "Authorization": f"Basic {auth_string}",
            "Content-Type": "application/x-www-form-urlencoded"
        }
        
        data = {
            "To": f"+{phone}",
            "From": sender,
            "Body": message
        }
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(url, headers=headers, data=data) as response:
                    if response.status in [200, 201]:
                        data = await response.json()
                        return SMSResponse(
                            success=True,
                            message_id=data.get("sid"),
                            status=SMSStatus.SENT,
                            provider=SMSProvider.TWILIO,
                            cost=float(data.get("price", 0)) if data.get("price") else None
                        )
                    else:
                        error_data = await response.text()
                        return SMSResponse(
                            success=False,
                            status=SMSStatus.FAILED,
                            error=f"HTTP {response.status}: {error_data}",
                            provider=SMSProvider.TWILIO
                        )
        except Exception as e:
            logger.error(f"Twilio SMS error: {str(e)}")
            return SMSResponse(
                success=False,
                status=SMSStatus.FAILED,
                error=str(e),
                provider=SMSProvider.TWILIO
            )
    
    async def check_status(self, message_id: str) -> SMSStatus:
        """Check message status via Twilio"""
        
        url = f"{self.base_url}/Messages/{message_id}.json"
        
        account_sid = self.config.get("account_sid")
        auth_token = self.config.get("auth_token")
        auth_string = base64.b64encode(f"{account_sid}:{auth_token}".encode()).decode()
        
        headers = {"Authorization": f"Basic {auth_string}"}
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, headers=headers) as response:
                    if response.status == 200:
                        data = await response.json()
                        status = data.get("status", "pending")
                        
                        # Map Twilio statuses to our enum
                        status_map = {
                            "queued": SMSStatus.PENDING,
                            "sent": SMSStatus.SENT,
                            "delivered": SMSStatus.DELIVERED,
                            "failed": SMSStatus.FAILED,
                            "undelivered": SMSStatus.FAILED
                        }
                        
                        return status_map.get(status, SMSStatus.PENDING)
                    else:
                        return SMSStatus.FAILED
        except Exception:
            return SMSStatus.FAILED

class SmartSMSProvider(BaseSMSProvider):
    """SmartSMS Solutions provider - Nigerian local provider"""
    
    def _get_base_url(self) -> str:
        return "https://smartsmssolutions.com/api"
    
    async def send_sms(self, to: str, message: str, sender_id: Optional[str] = None) -> SMSResponse:
        """Send SMS via SmartSMS"""
        
        url = f"{self.base_url}/send"
        phone = self.format_phone_number(to)
        sender = sender_id or self.sender_id
        
        payload = {
            "token": self.api_key,
            "sender": sender,
            "to": phone,
            "message": message,
            "type": 0,  # Plain text
            "routing": 4,  # DND routing
            "ref_id": f"txp_{datetime.now().strftime('%Y%m%d%H%M%S')}"
        }
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(url, json=payload) as response:
                    if response.status == 200:
                        data = await response.json()
                        if data.get("successful") == "true":
                            return SMSResponse(
                                success=True,
                                message_id=data.get("message_id"),
                                status=SMSStatus.SENT,
                                provider=SMSProvider.SMARTSMS
                            )
                        else:
                            return SMSResponse(
                                success=False,
                                status=SMSStatus.FAILED,
                                error=data.get("comment", "Unknown error"),
                                provider=SMSProvider.SMARTSMS
                            )
                    else:
                        error_data = await response.text()
                        return SMSResponse(
                            success=False,
                            status=SMSStatus.FAILED,
                            error=f"HTTP {response.status}: {error_data}",
                            provider=SMSProvider.SMARTSMS
                        )
        except Exception as e:
            logger.error(f"SmartSMS error: {str(e)}")
            return SMSResponse(
                success=False,
                status=SMSStatus.FAILED,
                error=str(e),
                provider=SMSProvider.SMARTSMS
            )
    
    async def check_status(self, message_id: str) -> SMSStatus:
        """Check message status via SmartSMS"""
        # SmartSMS doesn't provide status checking in basic plan
        return SMSStatus.SENT

class NigerianSMSService:
    """SMS service for payment notifications in Nigeria."""
    
    def __init__(self, primary_provider: SMSProvider = SMSProvider.TERMII):
        self.primary_provider = primary_provider
        self.providers: Dict[SMSProvider, BaseSMSProvider] = {}
        self._initialize_providers()
        
    def _initialize_providers(self):
        """Initialize SMS providers based on configuration"""
        
        # Initialize Termii (primary choice for Nigeria)
        if hasattr(settings, 'TERMII_API_KEY') and settings.TERMII_API_KEY:
            self.providers[SMSProvider.TERMII] = TermiiSMSProvider({
                "api_key": settings.TERMII_API_KEY,
                "sender_id": getattr(settings, 'TERMII_SENDER_ID', 'TaxPoynt')
            })
        
        # Initialize Twilio (international backup)
        if hasattr(settings, 'TWILIO_ACCOUNT_SID') and settings.TWILIO_ACCOUNT_SID:
            self.providers[SMSProvider.TWILIO] = TwilioSMSProvider({
                "account_sid": settings.TWILIO_ACCOUNT_SID,
                "auth_token": settings.TWILIO_AUTH_TOKEN,
                "phone_number": getattr(settings, 'TWILIO_PHONE_NUMBER', None)
            })
        
        # Initialize SmartSMS (Nigerian local)
        if hasattr(settings, 'SMARTSMS_TOKEN') and settings.SMARTSMS_TOKEN:
            self.providers[SMSProvider.SMARTSMS] = SmartSMSProvider({
                "api_key": settings.SMARTSMS_TOKEN,
                "sender_id": getattr(settings, 'SMARTSMS_SENDER_ID', 'TaxPoynt')
            })
    
    async def send_sms(self, 
                      phone: str, 
                      message: str, 
                      language: str = 'en-NG',
                      priority: str = 'normal') -> SMSResponse:
        """Send SMS with automatic failover"""
        
        # Try primary provider first
        if self.primary_provider in self.providers:
            response = await self.providers[self.primary_provider].send_sms(phone, message)
            if response.success:
                return response
            
            logger.warning(f"Primary SMS provider {self.primary_provider} failed: {response.error}")
        
        # Try backup providers
        for provider_type, provider in self.providers.items():
            if provider_type != self.primary_provider:
                try:
                    response = await provider.send_sms(phone, message)
                    if response.success:
                        logger.info(f"SMS sent via backup provider {provider_type}")
                        return response
                except Exception as e:
                    logger.error(f"Backup SMS provider {provider_type} failed: {str(e)}")
                    continue
        
        # All providers failed
        return SMSResponse(
            success=False,
            status=SMSStatus.FAILED,
            error="All SMS providers failed",
            provider=self.primary_provider
        )
    
    async def send_payment_confirmation(self, 
                                      phone: str, 
                                      amount: float,
                                      reference: str,
                                      language: str = 'en-NG') -> SMSResponse:
        """Send payment confirmation SMS."""
        
        messages = {
            'en-NG': f"Payment of ₦{amount:,.2f} confirmed. Ref: {reference}. Thank you for using TaxPoynt!",
            'ha-NG': f"An tabbatar da biyan ₦{amount:,.2f}. Ref: {reference}. Na gode da amfani da TaxPoynt!",
            'yo-NG': f"Sisanwo ₦{amount:,.2f} ti ni idaniloju. Ref: {reference}. E se fun lilo TaxPoynt!",
            'ig-NG': f"Akwado ikwu ugwo ₦{amount:,.2f}. Ref: {reference}. Dalu maka iji TaxPoynt!"
        }
        
        message = messages.get(language, messages['en-NG'])
        return await self.send_sms(phone, message, language)
    
    async def send_payment_instructions(self,
                                      phone: str,
                                      bank_name: str,
                                      ussd_code: str,
                                      amount: float,
                                      reference: str,
                                      language: str = 'en-NG') -> SMSResponse:
        """Send USSD payment instructions SMS."""
        
        if language == 'ha-NG':
            message = f"""
TaxPoynt Umarni na Biya:

Adadi: ₦{amount:,.2f}
Reference: {reference}
Bank: {bank_name}

Ka buga: {ussd_code}
Ka bi umarnin don canja kudi
            """.strip()
        elif language == 'yo-NG':
            message = f"""
Itọnisọna Sisanwo TaxPoynt:

Iye: ₦{amount:,.2f}
Reference: {reference}
Bank: {bank_name}

Pe: {ussd_code}
Tẹle awọn itọnisọna fun gbigbe owo
            """.strip()
        elif language == 'ig-NG':
            message = f"""
Ntuziaka Ịkwụ Ụgwọ TaxPoynt:

Ego: ₦{amount:,.2f}
Reference: {reference}
Bank: {bank_name}

Kpọọ: {ussd_code}
Soro ntuziaka maka ịnyefe ego
            """.strip()
        else:  # English
            message = f"""
TaxPoynt Payment Instructions:

Amount: ₦{amount:,.2f}
Reference: {reference}
Bank: {bank_name}

Dial: {ussd_code}
Follow prompts for transfer
            """.strip()
        
        return await self.send_sms(phone, message, language)
    
    async def check_message_status(self, message_id: str, provider: SMSProvider) -> SMSStatus:
        """Check SMS delivery status"""
        
        if provider in self.providers:
            return await self.providers[provider].check_status(message_id)
        
        return SMSStatus.FAILED