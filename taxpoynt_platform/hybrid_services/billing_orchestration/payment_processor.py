"""
Payment Processor - Handle payments for SI billing
Comprehensive payment processing system with multiple payment gateways, 
fraud detection, retry logic, and webhook handling.
"""

import asyncio
import logging
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, asdict
from enum import Enum
from uuid import UUID, uuid4
from decimal import Decimal

from core_platform.cache import CacheService
from core_platform.events import EventBus
from core_platform.monitoring import MetricsCollector
from core_platform.notifications import NotificationService

logger = logging.getLogger(__name__)


class PaymentGateway(str, Enum):
    """Supported payment gateways"""
    PAYSTACK = "paystack"
    FLUTTERWAVE = "flutterwave"
    STRIPE = "stripe"
    INTERSWITCH = "interswitch"
    BANK_TRANSFER = "bank_transfer"
    MANUAL = "manual"


class PaymentMethod(str, Enum):
    """Payment methods"""
    CREDIT_CARD = "credit_card"
    DEBIT_CARD = "debit_card"
    BANK_TRANSFER = "bank_transfer"
    MOBILE_MONEY = "mobile_money"
    CRYPTO = "crypto"
    CHECK = "check"
    CASH = "cash"


class PaymentStatus(str, Enum):
    """Payment processing status"""
    PENDING = "pending"
    PROCESSING = "processing"
    AUTHORIZED = "authorized"
    CAPTURED = "captured"
    SUCCESS = "success"
    FAILED = "failed"
    CANCELLED = "cancelled"
    REFUNDED = "refunded"
    DISPUTED = "disputed"
    EXPIRED = "expired"


class FraudRiskLevel(str, Enum):
    """Fraud risk assessment levels"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class PaymentTransaction:
    """Payment transaction record"""
    transaction_id: str
    tenant_id: UUID
    organization_id: UUID
    invoice_id: str
    
    # Payment details
    amount: Decimal
    currency: str
    payment_method: PaymentMethod
    gateway: PaymentGateway
    gateway_transaction_id: Optional[str]
    
    # Status and timestamps
    status: PaymentStatus
    created_at: datetime
    updated_at: datetime
    authorized_at: Optional[datetime] = None
    captured_at: Optional[datetime] = None
    failed_at: Optional[datetime] = None
    
    # Customer details
    customer_email: str
    customer_phone: Optional[str] = None
    billing_address: Optional[Dict[str, str]] = None
    
    # Fraud detection
    fraud_risk_level: FraudRiskLevel = FraudRiskLevel.LOW
    fraud_score: float = 0.0
    fraud_checks: Dict[str, Any] = None
    
    # Gateway response
    gateway_response: Dict[str, Any] = None
    failure_reason: Optional[str] = None
    
    # Metadata
    metadata: Dict[str, Any] = None


@dataclass
class PaymentWebhook:
    """Payment webhook event"""
    webhook_id: str
    gateway: PaymentGateway
    event_type: str
    transaction_id: str
    payload: Dict[str, Any]
    signature: str
    received_at: datetime
    processed_at: Optional[datetime] = None
    processed: bool = False
    retries: int = 0


@dataclass
class RefundTransaction:
    """Refund transaction record"""
    refund_id: str
    original_transaction_id: str
    amount: Decimal
    reason: str
    status: PaymentStatus
    gateway_refund_id: Optional[str]
    processed_at: Optional[datetime]
    metadata: Dict[str, Any]


class PaymentProcessor:
    """SI Payment Processing System"""
    
    def __init__(self):
        self.cache_service = CacheService()
        self.event_bus = EventBus()
        self.metrics_collector = MetricsCollector()
        self.notification_service = NotificationService()
        self.logger = logging.getLogger(__name__)
        
        # Payment registries
        self.transactions: Dict[str, PaymentTransaction] = {}
        self.webhooks: Dict[str, PaymentWebhook] = {}
        self.refunds: Dict[str, RefundTransaction] = {}
        
        # Gateway configurations
        self.gateway_configs = {
            PaymentGateway.PAYSTACK: {
                "public_key": "pk_test_xxx",
                "secret_key": "sk_test_xxx",
                "webhook_secret": "whsec_xxx",
                "enabled": True,
                "currencies": ["NGN", "USD"],
                "fee_percentage": 0.015,  # 1.5%
                "fee_cap": 2000  # ₦20 cap
            },
            PaymentGateway.FLUTTERWAVE: {
                "public_key": "FLWPUBK_TEST-xxx",
                "secret_key": "FLWSECK_TEST-xxx",
                "webhook_secret": "FLWSECK_HASH-xxx",
                "enabled": True,
                "currencies": ["NGN", "USD", "GBP"],
                "fee_percentage": 0.014
            },
            PaymentGateway.STRIPE: {
                "public_key": "pk_test_xxx",
                "secret_key": "sk_test_xxx",
                "webhook_secret": "whsec_xxx",
                "enabled": True,
                "currencies": ["USD", "EUR", "GBP"],
                "fee_percentage": 0.029,
                "fee_fixed": 0.30
            }
        }
        
        # Configuration
        self.config = {
            "default_gateway": PaymentGateway.PAYSTACK,
            "retry_attempts": 3,
            "retry_delay_seconds": [30, 300, 900],  # 30s, 5m, 15m
            "payment_timeout_minutes": 60,
            "fraud_threshold_score": 0.75,
            "webhook_timeout_seconds": 30,
            "auto_capture": True,
            "supported_currencies": ["NGN", "USD", "GBP", "EUR"]
        }
    
    async def initiate_payment(
        self,
        invoice_id: str,
        tenant_id: UUID,
        organization_id: UUID,
        amount: Decimal,
        currency: str,
        payment_method: PaymentMethod,
        customer_email: str,
        customer_phone: Optional[str] = None,
        billing_address: Optional[Dict[str, str]] = None,
        gateway: Optional[PaymentGateway] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Initiate payment transaction"""
        try:
            # Select gateway
            selected_gateway = gateway or self._select_optimal_gateway(currency, amount)
            
            # Validate payment details
            validation_result = await self._validate_payment_request(
                amount, currency, payment_method, selected_gateway
            )
            if not validation_result["valid"]:
                return {"status": "error", "message": validation_result["message"]}
            
            # Create transaction record
            transaction = PaymentTransaction(
                transaction_id=str(uuid4()),
                tenant_id=tenant_id,
                organization_id=organization_id,
                invoice_id=invoice_id,
                amount=amount,
                currency=currency,
                payment_method=payment_method,
                gateway=selected_gateway,
                status=PaymentStatus.PENDING,
                customer_email=customer_email,
                customer_phone=customer_phone,
                billing_address=billing_address,
                metadata=metadata or {},
                created_at=datetime.now(timezone.utc),
                updated_at=datetime.now(timezone.utc)
            )
            
            # Perform fraud detection
            fraud_result = await self._perform_fraud_detection(transaction)
            transaction.fraud_risk_level = fraud_result["risk_level"]
            transaction.fraud_score = fraud_result["score"]
            transaction.fraud_checks = fraud_result["checks"]
            
            # Check fraud threshold
            if fraud_result["score"] > self.config["fraud_threshold_score"]:
                transaction.status = PaymentStatus.FAILED
                transaction.failure_reason = "High fraud risk detected"
                self.transactions[transaction.transaction_id] = transaction
                
                return {
                    "status": "error",
                    "message": "Payment blocked due to fraud risk",
                    "transaction_id": transaction.transaction_id
                }
            
            # Initialize payment with gateway
            gateway_result = await self._initialize_gateway_payment(transaction)
            
            if gateway_result["status"] == "success":
                transaction.gateway_transaction_id = gateway_result.get("gateway_transaction_id")
                transaction.gateway_response = gateway_result.get("response", {})
                transaction.status = PaymentStatus.PROCESSING
            else:
                transaction.status = PaymentStatus.FAILED
                transaction.failure_reason = gateway_result.get("message", "Gateway initialization failed")
            
            transaction.updated_at = datetime.now(timezone.utc)
            
            # Store transaction
            self.transactions[transaction.transaction_id] = transaction
            
            # Cache for quick lookup
            await self.cache_service.set(
                f"payment_transaction:{transaction.transaction_id}",
                asdict(transaction),
                ttl=3600  # 1 hour
            )
            
            # Emit event
            await self.event_bus.emit("payment_initiated", {
                "transaction_id": transaction.transaction_id,
                "tenant_id": str(tenant_id),
                "invoice_id": invoice_id,
                "amount": float(amount),
                "currency": currency,
                "gateway": selected_gateway.value,
                "status": transaction.status.value,
                "timestamp": datetime.now(timezone.utc).isoformat()
            })
            
            self.logger.info(f"Payment initiated: {transaction.transaction_id} for {amount} {currency}")
            
            return {
                "status": "success",
                "transaction_id": transaction.transaction_id,
                "gateway": selected_gateway.value,
                "payment_url": gateway_result.get("payment_url"),
                "authorization_url": gateway_result.get("authorization_url"),
                "reference": gateway_result.get("reference"),
                "expires_at": (
                    datetime.now(timezone.utc) + timedelta(minutes=self.config["payment_timeout_minutes"])
                ).isoformat()
            }
            
        except Exception as e:
            self.logger.error(f"Error initiating payment: {str(e)}")
            return {"status": "error", "message": str(e)}
    
    async def verify_payment(
        self,
        transaction_id: str,
        gateway_reference: Optional[str] = None
    ) -> Dict[str, Any]:
        """Verify payment status with gateway"""
        try:
            transaction = self.transactions.get(transaction_id)
            if not transaction:
                return {"status": "error", "message": "Transaction not found"}
            
            # Verify with gateway
            verification_result = await self._verify_with_gateway(transaction, gateway_reference)
            
            # Update transaction status
            old_status = transaction.status
            transaction.status = verification_result["status"]
            transaction.gateway_response = verification_result.get("response", {})
            transaction.updated_at = datetime.now(timezone.utc)
            
            if verification_result["status"] == PaymentStatus.SUCCESS:
                transaction.captured_at = datetime.now(timezone.utc)
                
                # Auto-capture if enabled
                if self.config["auto_capture"]:
                    capture_result = await self._capture_payment(transaction)
                    if capture_result["status"] == "success":
                        transaction.status = PaymentStatus.CAPTURED
            
            elif verification_result["status"] == PaymentStatus.FAILED:
                transaction.failed_at = datetime.now(timezone.utc)
                transaction.failure_reason = verification_result.get("failure_reason")
            
            # Update cache
            await self.cache_service.set(
                f"payment_transaction:{transaction_id}",
                asdict(transaction),
                ttl=3600
            )
            
            # Emit status change event if status changed
            if old_status != transaction.status:
                await self.event_bus.emit("payment_status_changed", {
                    "transaction_id": transaction_id,
                    "tenant_id": str(transaction.tenant_id),
                    "old_status": old_status.value,
                    "new_status": transaction.status.value,
                    "amount": float(transaction.amount),
                    "timestamp": datetime.now(timezone.utc).isoformat()
                })
            
            return {
                "status": "success",
                "transaction_id": transaction_id,
                "payment_status": transaction.status.value,
                "amount": float(transaction.amount),
                "currency": transaction.currency,
                "gateway_response": verification_result.get("response", {})
            }
            
        except Exception as e:
            self.logger.error(f"Error verifying payment {transaction_id}: {str(e)}")
            return {"status": "error", "message": str(e)}
    
    async def process_webhook(
        self,
        gateway: PaymentGateway,
        event_type: str,
        payload: Dict[str, Any],
        signature: str
    ) -> Dict[str, Any]:
        """Process payment webhook from gateway"""
        try:
            webhook_id = str(uuid4())
            
            # Create webhook record
            webhook = PaymentWebhook(
                webhook_id=webhook_id,
                gateway=gateway,
                event_type=event_type,
                transaction_id=payload.get("transaction_id", ""),
                payload=payload,
                signature=signature,
                received_at=datetime.now(timezone.utc)
            )
            
            # Verify webhook signature
            if not await self._verify_webhook_signature(webhook):
                return {
                    "status": "error",
                    "message": "Invalid webhook signature",
                    "webhook_id": webhook_id
                }
            
            # Process webhook
            processing_result = await self._process_webhook_event(webhook)
            
            webhook.processed = processing_result["success"]
            webhook.processed_at = datetime.now(timezone.utc)
            
            # Store webhook
            self.webhooks[webhook_id] = webhook
            
            # Emit event
            await self.event_bus.emit("payment_webhook_processed", {
                "webhook_id": webhook_id,
                "gateway": gateway.value,
                "event_type": event_type,
                "success": processing_result["success"],
                "timestamp": datetime.now(timezone.utc).isoformat()
            })
            
            self.logger.info(f"Webhook processed: {webhook_id} from {gateway.value}")
            
            return {
                "status": "success",
                "webhook_id": webhook_id,
                "processed": processing_result["success"],
                "transaction_updates": processing_result.get("transaction_updates", [])
            }
            
        except Exception as e:
            self.logger.error(f"Error processing webhook: {str(e)}")
            return {"status": "error", "message": str(e)}
    
    async def initiate_refund(
        self,
        original_transaction_id: str,
        refund_amount: Decimal,
        reason: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Initiate refund for payment"""
        try:
            original_transaction = self.transactions.get(original_transaction_id)
            if not original_transaction:
                return {"status": "error", "message": "Original transaction not found"}
            
            # Validate refund
            if original_transaction.status != PaymentStatus.CAPTURED:
                return {
                    "status": "error",
                    "message": "Can only refund captured payments"
                }
            
            if refund_amount > original_transaction.amount:
                return {
                    "status": "error",
                    "message": "Refund amount cannot exceed original amount"
                }
            
            # Create refund record
            refund = RefundTransaction(
                refund_id=str(uuid4()),
                original_transaction_id=original_transaction_id,
                amount=refund_amount,
                reason=reason,
                status=PaymentStatus.PENDING,
                gateway_refund_id=None,
                processed_at=None,
                metadata=metadata or {}
            )
            
            # Process refund with gateway
            refund_result = await self._process_gateway_refund(original_transaction, refund)
            
            if refund_result["status"] == "success":
                refund.status = PaymentStatus.PROCESSING
                refund.gateway_refund_id = refund_result.get("gateway_refund_id")
            else:
                refund.status = PaymentStatus.FAILED
            
            refund.processed_at = datetime.now(timezone.utc)
            
            # Store refund
            self.refunds[refund.refund_id] = refund
            
            # Emit event
            await self.event_bus.emit("refund_initiated", {
                "refund_id": refund.refund_id,
                "original_transaction_id": original_transaction_id,
                "tenant_id": str(original_transaction.tenant_id),
                "refund_amount": float(refund_amount),
                "reason": reason,
                "status": refund.status.value,
                "timestamp": datetime.now(timezone.utc).isoformat()
            })
            
            self.logger.info(f"Refund initiated: {refund.refund_id} for {refund_amount}")
            
            return {
                "status": "success",
                "refund_id": refund.refund_id,
                "refund_status": refund.status.value,
                "estimated_completion": "3-5 business days"
            }
            
        except Exception as e:
            self.logger.error(f"Error initiating refund: {str(e)}")
            return {"status": "error", "message": str(e)}
    
    async def get_payment_analytics(
        self,
        tenant_id: Optional[UUID] = None,
        time_range_days: int = 30
    ) -> Dict[str, Any]:
        """Get payment processing analytics"""
        try:
            end_date = datetime.now(timezone.utc)
            start_date = end_date - timedelta(days=time_range_days)
            
            # Filter transactions
            transactions = list(self.transactions.values())
            if tenant_id:
                transactions = [t for t in transactions if t.tenant_id == tenant_id]
            
            transactions = [
                t for t in transactions 
                if start_date <= t.created_at <= end_date
            ]
            
            # Calculate metrics
            total_transactions = len(transactions)
            successful_transactions = len([t for t in transactions if t.status == PaymentStatus.CAPTURED])
            failed_transactions = len([t for t in transactions if t.status == PaymentStatus.FAILED])
            
            success_rate = (successful_transactions / total_transactions * 100) if total_transactions > 0 else 0
            
            # Volume and revenue
            total_volume = sum(t.amount for t in transactions if t.status == PaymentStatus.CAPTURED)
            average_transaction = total_volume / successful_transactions if successful_transactions > 0 else 0
            
            # Gateway breakdown
            gateway_stats = {}
            for gateway in PaymentGateway:
                gateway_transactions = [t for t in transactions if t.gateway == gateway]
                gateway_stats[gateway.value] = {
                    "count": len(gateway_transactions),
                    "success_rate": (
                        len([t for t in gateway_transactions if t.status == PaymentStatus.CAPTURED]) /
                        len(gateway_transactions) * 100
                    ) if gateway_transactions else 0,
                    "volume": float(sum(
                        t.amount for t in gateway_transactions 
                        if t.status == PaymentStatus.CAPTURED
                    ))
                }
            
            # Fraud stats
            fraud_detected = len([t for t in transactions if t.fraud_risk_level == FraudRiskLevel.HIGH])
            
            return {
                "period": {
                    "start_date": start_date.isoformat(),
                    "end_date": end_date.isoformat(),
                    "days": time_range_days
                },
                "summary": {
                    "total_transactions": total_transactions,
                    "successful_transactions": successful_transactions,
                    "failed_transactions": failed_transactions,
                    "success_rate": round(success_rate, 2),
                    "total_volume": float(total_volume),
                    "average_transaction": float(average_transaction),
                    "fraud_detected": fraud_detected
                },
                "gateway_performance": gateway_stats,
                "tenant_id": str(tenant_id) if tenant_id else "all",
                "generated_at": datetime.now(timezone.utc).isoformat()
            }
            
        except Exception as e:
            self.logger.error(f"Error generating payment analytics: {str(e)}")
            return {"status": "error", "message": str(e)}
    
    # Private helper methods
    
    def _select_optimal_gateway(self, currency: str, amount: Decimal) -> PaymentGateway:
        """Select optimal payment gateway based on currency and amount"""
        try:
            # Simple selection logic - can be enhanced with ML
            if currency == "NGN":
                if amount < 100000:  # Less than ₦1000
                    return PaymentGateway.PAYSTACK
                else:
                    return PaymentGateway.FLUTTERWAVE
            elif currency in ["USD", "EUR", "GBP"]:
                return PaymentGateway.STRIPE
            else:
                return self.config["default_gateway"]
                
        except Exception:
            return self.config["default_gateway"]
    
    async def _validate_payment_request(
        self,
        amount: Decimal,
        currency: str,
        payment_method: PaymentMethod,
        gateway: PaymentGateway
    ) -> Dict[str, Any]:
        """Validate payment request parameters"""
        try:
            # Check amount
            if amount <= 0:
                return {"valid": False, "message": "Amount must be greater than 0"}
            
            # Check currency support
            if currency not in self.config["supported_currencies"]:
                return {"valid": False, "message": f"Currency {currency} not supported"}
            
            # Check gateway availability
            gateway_config = self.gateway_configs.get(gateway, {})
            if not gateway_config.get("enabled", False):
                return {"valid": False, "message": f"Gateway {gateway.value} not available"}
            
            # Check currency support by gateway
            gateway_currencies = gateway_config.get("currencies", [])
            if currency not in gateway_currencies:
                return {"valid": False, "message": f"Gateway {gateway.value} does not support {currency}"}
            
            return {"valid": True, "message": "Validation passed"}
            
        except Exception as e:
            return {"valid": False, "message": f"Validation error: {str(e)}"}
    
    async def _perform_fraud_detection(self, transaction: PaymentTransaction) -> Dict[str, Any]:
        """Perform fraud detection analysis"""
        try:
            fraud_score = 0.0
            checks = {}
            
            # Email domain check
            email_domain = transaction.customer_email.split("@")[1] if "@" in transaction.customer_email else ""
            suspicious_domains = ["10minutemail.com", "tempmail.org", "guerrillamail.com"]
            if email_domain in suspicious_domains:
                fraud_score += 0.3
                checks["suspicious_email_domain"] = True
            
            # Amount-based checks
            if transaction.amount > Decimal("1000000"):  # Very high amount
                fraud_score += 0.4
                checks["high_amount"] = True
            
            # Velocity checks (simplified)
            recent_transactions = [
                t for t in self.transactions.values()
                if (t.customer_email == transaction.customer_email and
                    t.created_at > datetime.now(timezone.utc) - timedelta(hours=1))
            ]
            if len(recent_transactions) > 3:
                fraud_score += 0.5
                checks["high_velocity"] = True
            
            # Determine risk level
            if fraud_score >= 0.75:
                risk_level = FraudRiskLevel.CRITICAL
            elif fraud_score >= 0.5:
                risk_level = FraudRiskLevel.HIGH
            elif fraud_score >= 0.25:
                risk_level = FraudRiskLevel.MEDIUM
            else:
                risk_level = FraudRiskLevel.LOW
            
            return {
                "score": fraud_score,
                "risk_level": risk_level,
                "checks": checks
            }
            
        except Exception as e:
            self.logger.error(f"Error in fraud detection: {str(e)}")
            return {
                "score": 0.0,
                "risk_level": FraudRiskLevel.LOW,
                "checks": {}
            }
    
    async def health_check(self) -> Dict[str, Any]:
        """Health check for payment processor"""
        try:
            return {
                "status": "healthy",
                "service": "payment_processor",
                "transactions": len(self.transactions),
                "webhooks": len(self.webhooks),
                "refunds": len(self.refunds),
                "gateways_enabled": len([g for g, c in self.gateway_configs.items() if c.get("enabled")]),
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
        except Exception as e:
            self.logger.error(f"Health check failed: {str(e)}")
            return {
                "status": "error",
                "service": "payment_processor",
                "error": str(e),
                "timestamp": datetime.now(timezone.utc).isoformat()
            }


def create_payment_processor() -> PaymentProcessor:
    """Create payment processor instance"""
    return PaymentProcessor()