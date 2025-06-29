"""
Nigerian USSD Payment Service
Comprehensive USSD payment integration for Nigerian banks and basic phones
"""

import asyncio
import uuid
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from sqlalchemy.orm import Session

from .models import (
    USSDPaymentCode, USSDPaymentRequest, USSDSession, USSDSessionStatus,
    USSDTransactionResult, USSDCallbackPayload, BankUSSDCapabilities,
    USSDStepType, create_ussd_payment_code
)
from .bank_ussd_codes import (
    NIGERIAN_BANK_USSD_CODES, get_bank_by_code, validate_transaction_limits,
    NetworkOperator, NETWORK_CONSIDERATIONS
)
from ..payments.base import PaymentStatus
from ...services.sms_service import SMSService
from ...core.config import settings

class NigerianUSSDService:
    """USSD payment integration for basic phones."""
    
    def __init__(self, sms_service: Optional[SMSService] = None):
        self.sms_service = sms_service
        self.active_sessions: Dict[str, USSDSession] = {}
        self.payment_codes: Dict[str, USSDPaymentCode] = {}
        
    async def generate_ussd_payment_code(self, 
                                       request: USSDPaymentRequest) -> USSDPaymentCode:
        """Generate USSD payment code for basic phones."""
        
        # Validate bank support
        bank = get_bank_by_code(request.bank_code)
        if not bank:
            raise ValueError(f"Unsupported bank: {request.bank_code}")
        
        # Validate transaction limits
        amount_kobo = int(request.amount * 100)
        limit_check = validate_transaction_limits(request.bank_code, amount_kobo)
        if not limit_check['valid']:
            raise ValueError(f"Transaction exceeds limits: {limit_check.get('reason', 'Unknown')}")
        
        # Generate unique reference if not provided
        if not request.reference:
            request.reference = f"TPY{datetime.now().strftime('%Y%m%d%H%M%S')}{uuid.uuid4().hex[:6].upper()}"
        
        # Create USSD payment code
        payment_code = create_ussd_payment_code(
            bank_code=request.bank_code,
            amount=request.amount,
            reference=request.reference,
            expires_in_minutes=request.expires_in_minutes
        )
        
        # Store payment code for tracking
        self.payment_codes[request.reference] = payment_code
        
        # Send SMS with instructions if SMS service available
        if self.sms_service and request.customer_phone:
            await self._send_ussd_instructions_sms(request.customer_phone, payment_code)
        
        return payment_code
        
    async def initiate_ussd_session(self, 
                                  phone_number: str,
                                  payment_reference: str) -> USSDSession:
        """Initiate a USSD payment session."""
        
        # Get payment code details
        payment_code = self.payment_codes.get(payment_reference)
        if not payment_code:
            raise ValueError(f"Payment reference not found: {payment_reference}")
        
        if payment_code.expires_at < datetime.utcnow():
            raise ValueError("Payment code has expired")
        
        # Create session
        session_id = f"ussd_{uuid.uuid4().hex[:12]}"
        session = USSDSession(
            session_id=session_id,
            phone_number=phone_number,
            bank_code=payment_code.bank_code,
            payment_reference=payment_reference,
            amount=payment_code.amount_kobo,
            expires_at=datetime.utcnow() + timedelta(minutes=15)  # Session timeout
        )
        
        # Store active session
        self.active_sessions[session_id] = session
        
        return session
        
    async def process_ussd_response(self, 
                                  session_id: str,
                                  user_input: str) -> Tuple[str, USSDSessionStatus]:
        """Process USSD user response and return next prompt."""
        
        session = self.active_sessions.get(session_id)
        if not session:
            return "Session not found. Please start over.", USSDSessionStatus.FAILED
        
        if session.expires_at < datetime.utcnow():
            session.status = USSDSessionStatus.EXPIRED
            return "Session expired. Please start over.", USSDSessionStatus.EXPIRED
        
        # Process based on current step
        if session.current_step == USSDStepType.MENU_SELECTION:
            return await self._handle_menu_selection(session, user_input)
        elif session.current_step == USSDStepType.AMOUNT_INPUT:
            return await self._handle_amount_input(session, user_input)
        elif session.current_step == USSDStepType.ACCOUNT_INPUT:
            return await self._handle_account_input(session, user_input)
        elif session.current_step == USSDStepType.PIN_INPUT:
            return await self._handle_pin_input(session, user_input)
        elif session.current_step == USSDStepType.CONFIRMATION:
            return await self._handle_confirmation(session, user_input)
        else:
            return "Invalid session state.", USSDSessionStatus.FAILED
            
    async def verify_ussd_payment(self, reference: str) -> USSDTransactionResult:
        """Verify USSD payment completion."""
        
        payment_code = self.payment_codes.get(reference)
        if not payment_code:
            return USSDTransactionResult(
                reference=reference,
                status=PaymentStatus.FAILED,
                amount=0,
                bank_code="",
                customer_phone="",
                error_message="Payment reference not found"
            )
        
        # In a real implementation, this would check with bank APIs
        # For now, simulate based on session status
        session = self._find_session_by_reference(reference)
        if session and session.status == USSDSessionStatus.COMPLETED:
            return USSDTransactionResult(
                reference=reference,
                status=PaymentStatus.SUCCESS,
                amount=payment_code.amount_kobo,
                bank_code=payment_code.bank_code,
                customer_phone=session.phone_number,
                completed_at=datetime.utcnow(),
                session_log=session.session_data.get('log', [])
            )
        
        return USSDTransactionResult(
            reference=reference,
            status=PaymentStatus.PENDING,
            amount=payment_code.amount_kobo,
            bank_code=payment_code.bank_code,
            customer_phone=session.phone_number if session else "",
            error_message="Payment still pending or failed"
        )
        
    async def get_ussd_instructions(self, bank_code: str, language: str = 'en-NG') -> List[str]:
        """Get step-by-step USSD instructions."""
        
        bank = get_bank_by_code(bank_code)
        if not bank:
            return ["Bank not supported"]
        
        # Localized instructions based on language
        if language == 'ha-NG':  # Hausa
            return [
                f"Ka buga {bank['code']} a wayarka",
                f"Ka zaɓi zaɓi na 'Canja kudi' ko 'Biya'",
                f"Ka shigar da adadin kudin",
                f"Ka shigar da lambar reference na biyan kudin",
                f"Ka shigar da PIN naka na {bank['name']} USSD",
                f"Ka tabbatar da cikakkun bayanai na ma'amala",
                f"Za ka karɓi saƙon tabbatarwa ta SMS"
            ]
        elif language == 'yo-NG':  # Yoruba
            return [
                f"Pe {bank['code']} lori foonu rẹ",
                f"Yan ẹyan fun 'Gbigbe owo' tabi 'Sisanwo'",
                f"Tẹ iye owo naa sinu",
                f"Tẹ reference sisanwo naa sinu",
                f"Tẹ PIN USSD {bank['name']} rẹ sinu",
                f"Jẹrisi awọn alaye iṣowo naa",
                f"Iwọ yoo gba ijẹrisi SMS kan"
            ]
        elif language == 'ig-NG':  # Igbo
            return [
                f"Kpọọ {bank['code']} na ekwentị gị",
                f"Họrọ nhọrọ maka 'Ịnyefe ego' ma ọ bụ 'Ịkwụ ụgwọ'",
                f"Tinye ego ahụ",
                f"Tinye ntụaka ịkwụ ụgwọ",
                f"Tinye PIN USSD {bank['name']} gị",
                f"Kwenye nkọwa azụmahịa ahụ",
                f"Ị ga-enweta nkwenye SMS"
            ]
        else:  # English (default)
            return [
                f"Dial {bank['code']} on your phone",
                f"Select option for 'Transfer' or 'Payment'",
                f"Enter the payment amount",
                f"Enter the payment reference",
                f"Enter your {bank['name']} USSD PIN",
                f"Confirm the transaction details",
                f"You will receive an SMS confirmation"
            ]
            
    async def get_bank_capabilities(self, bank_code: str) -> Optional[BankUSSDCapabilities]:
        """Get bank USSD capabilities and limits."""
        
        bank = get_bank_by_code(bank_code)
        if not bank:
            return None
        
        return BankUSSDCapabilities(
            bank_code=bank_code,
            bank_name=bank['name'],
            supports_ussd=True,
            supports_merchant_payments=bank['features'].get('merchant_payment', False),
            supports_bill_payments=bank['features'].get('bill_payment', False),
            daily_limit=bank['limits']['daily_transfer'] * 100,  # Convert to kobo
            single_transaction_limit=bank['limits']['single_transaction'] * 100,
            monthly_limit=bank['limits']['monthly'] * 100,
            session_timeout_seconds=180,
            supported_networks=[net.value for net in bank['supported_networks']],
            fees={}  # Would be populated from bank API
        )
        
    async def cancel_ussd_session(self, session_id: str, reason: str = "User cancelled") -> bool:
        """Cancel an active USSD session."""
        
        session = self.active_sessions.get(session_id)
        if not session:
            return False
        
        session.status = USSDSessionStatus.CANCELLED
        session.error_message = reason
        session.updated_at = datetime.utcnow()
        
        # Send cancellation SMS if available
        if self.sms_service:
            payment_code = self.payment_codes.get(session.payment_reference)
            if payment_code:
                await self._send_cancellation_sms(session.phone_number, payment_code)
        
        return True
        
    # Private helper methods
    async def _send_ussd_instructions_sms(self, phone: str, payment_code: USSDPaymentCode):
        """Send USSD payment instructions via SMS."""
        
        bank = get_bank_by_code(payment_code.bank_code)
        message = f"""
TaxPoynt Payment Instructions:

Amount: ₦{payment_code.amount:,.2f}
Reference: {payment_code.reference}
Bank: {bank['name']}

Steps:
1. Dial {bank['code']} 
2. Follow prompts for transfer/payment
3. Use reference: {payment_code.reference}
4. Expires: {payment_code.expires_at.strftime('%H:%M on %d/%m/%Y')}

Need help? Reply HELP
        """.strip()
        
        await self.sms_service.send_sms(phone, message)
        
    async def _send_cancellation_sms(self, phone: str, payment_code: USSDPaymentCode):
        """Send payment cancellation SMS."""
        
        message = f"""
TaxPoynt Payment Cancelled

Reference: {payment_code.reference}
Amount: ₦{payment_code.amount:,.2f}

The payment session has been cancelled. 
You can restart the payment process if needed.
        """.strip()
        
        await self.sms_service.send_sms(phone, message)
        
    def _find_session_by_reference(self, reference: str) -> Optional[USSDSession]:
        """Find USSD session by payment reference."""
        
        for session in self.active_sessions.values():
            if session.payment_reference == reference:
                return session
        return None
        
    async def _handle_menu_selection(self, session: USSDSession, user_input: str) -> Tuple[str, USSDSessionStatus]:
        """Handle main menu selection."""
        
        if user_input == "1":  # Transfer/Payment
            session.current_step = USSDStepType.AMOUNT_INPUT
            session.steps_completed.append(USSDStepType.MENU_SELECTION)
            return f"Enter amount to pay (₦{session.amount/100:,.2f}):", USSDSessionStatus.IN_PROGRESS
        elif user_input == "0":  # Cancel
            session.status = USSDSessionStatus.CANCELLED
            return "Payment cancelled.", USSDSessionStatus.CANCELLED
        else:
            return "Invalid option. Press 1 for Payment, 0 to Cancel:", USSDSessionStatus.IN_PROGRESS
            
    async def _handle_amount_input(self, session: USSDSession, user_input: str) -> Tuple[str, USSDSessionStatus]:
        """Handle amount input step."""
        
        try:
            amount = float(user_input)
            expected_amount = session.amount / 100
            
            if abs(amount - expected_amount) < 0.01:  # Allow small rounding differences
                session.current_step = USSDStepType.ACCOUNT_INPUT
                session.steps_completed.append(USSDStepType.AMOUNT_INPUT)
                return "Enter TaxPoynt merchant account: 1234567890", USSDSessionStatus.IN_PROGRESS
            else:
                return f"Amount mismatch. Enter ₦{expected_amount:,.2f}:", USSDSessionStatus.IN_PROGRESS
        except ValueError:
            return "Invalid amount. Please enter numbers only:", USSDSessionStatus.IN_PROGRESS
            
    async def _handle_account_input(self, session: USSDSession, user_input: str) -> Tuple[str, USSDSessionStatus]:
        """Handle account number input step."""
        
        # In real implementation, validate against actual merchant account
        if user_input == "1234567890":  # Demo merchant account
            session.target_account = user_input
            session.current_step = USSDStepType.PIN_INPUT
            session.steps_completed.append(USSDStepType.ACCOUNT_INPUT)
            return "Enter your USSD PIN:", USSDSessionStatus.WAITING_PIN
        else:
            return "Invalid account. Enter TaxPoynt merchant account:", USSDSessionStatus.IN_PROGRESS
            
    async def _handle_pin_input(self, session: USSDSession, user_input: str) -> Tuple[str, USSDSessionStatus]:
        """Handle PIN input step."""
        
        # In real implementation, validate PIN with bank
        if len(user_input) >= 4:  # Basic PIN validation
            session.current_step = USSDStepType.CONFIRMATION
            session.steps_completed.append(USSDStepType.PIN_INPUT)
            return f"Confirm payment of ₦{session.amount/100:,.2f} to TaxPoynt? 1=Yes, 2=No", USSDSessionStatus.IN_PROGRESS
        else:
            return "Invalid PIN. Enter your 4-digit USSD PIN:", USSDSessionStatus.WAITING_PIN
            
    async def _handle_confirmation(self, session: USSDSession, user_input: str) -> Tuple[str, USSDSessionStatus]:
        """Handle payment confirmation step."""
        
        if user_input == "1":  # Confirmed
            session.status = USSDSessionStatus.COMPLETED
            session.steps_completed.append(USSDStepType.CONFIRMATION)
            session.session_data['completion_time'] = datetime.utcnow().isoformat()
            
            # Send success SMS
            if self.sms_service:
                await self._send_success_sms(session)
                
            return f"Payment successful! Ref: {session.payment_reference}", USSDSessionStatus.COMPLETED
        elif user_input == "2":  # Cancelled
            session.status = USSDSessionStatus.CANCELLED
            return "Payment cancelled by user.", USSDSessionStatus.CANCELLED
        else:
            return "Invalid option. 1=Yes, 2=No", USSDSessionStatus.IN_PROGRESS
            
    async def _send_success_sms(self, session: USSDSession):
        """Send payment success SMS."""
        
        payment_code = self.payment_codes.get(session.payment_reference)
        if not payment_code:
            return
            
        message = f"""
Payment Successful!

Amount: ₦{session.amount/100:,.2f}
Reference: {session.payment_reference}
Date: {datetime.now().strftime('%d/%m/%Y %H:%M')}

Thank you for using TaxPoynt!
        """.strip()
        
        await self.sms_service.send_sms(session.phone_number, message)