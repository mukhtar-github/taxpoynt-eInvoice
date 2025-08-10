"""
Billing Engine - Generate invoices and manage billing cycles
Comprehensive billing engine for SI commercial model with automated invoice generation, 
tax calculations, discounts, and billing cycle management.
"""

import asyncio
import logging
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, asdict
from enum import Enum
from uuid import UUID, uuid4
from decimal import Decimal, ROUND_HALF_UP

from core_platform.data_management.billing_repository import (
    BillingRepository, BillingRecord, SubscriptionTier, PaymentStatus
)
from core_platform.cache import CacheService
from core_platform.events import EventBus
from core_platform.monitoring import MetricsCollector
from core_platform.notifications import NotificationService

logger = logging.getLogger(__name__)


class InvoiceType(str, Enum):
    """Types of invoices generated"""
    SUBSCRIPTION = "subscription"      # Regular monthly subscription
    OVERAGE = "overage"               # Usage overage charges
    UPGRADE_PRORATION = "upgrade_proration"  # Prorated upgrade charges
    DOWNGRADE_CREDIT = "downgrade_credit"   # Credit for downgrades
    ONE_TIME = "one_time"             # One-time charges
    REFUND = "refund"                 # Refund transactions


class InvoiceStatus(str, Enum):
    """Invoice status lifecycle"""
    DRAFT = "draft"
    PENDING = "pending"
    SENT = "sent"
    PAID = "paid"
    OVERDUE = "overdue"
    CANCELLED = "cancelled"
    REFUNDED = "refunded"


class TaxRegion(str, Enum):
    """Tax regions for calculation"""
    NIGERIA = "nigeria"
    US = "us"
    EU = "eu"
    UK = "uk"
    OTHER = "other"


@dataclass
class LineItem:
    """Invoice line item"""
    item_id: str
    description: str
    quantity: Decimal
    unit_price: Decimal
    line_total: Decimal
    tax_rate: Decimal
    tax_amount: Decimal
    discount_rate: Decimal
    discount_amount: Decimal
    metadata: Dict[str, Any]


@dataclass
class TaxCalculation:
    """Tax calculation details"""
    region: TaxRegion
    tax_rate: Decimal
    taxable_amount: Decimal
    tax_amount: Decimal
    tax_breakdown: Dict[str, Decimal]  # VAT, service tax, etc.
    exemption_reason: Optional[str] = None


@dataclass
class Invoice:
    """Complete invoice record"""
    invoice_id: str
    invoice_number: str
    tenant_id: UUID
    organization_id: UUID
    invoice_type: InvoiceType
    status: InvoiceStatus
    issue_date: datetime
    due_date: datetime
    billing_period_start: Optional[datetime]
    billing_period_end: Optional[datetime]
    
    # Financial details
    line_items: List[LineItem]
    subtotal: Decimal
    total_discount: Decimal
    tax_calculation: TaxCalculation
    total_amount: Decimal
    amount_paid: Decimal
    amount_due: Decimal
    
    # Payment details
    currency: str
    payment_terms: str
    payment_methods: List[str]
    
    # References
    subscription_id: Optional[str]
    previous_invoice_id: Optional[str]
    
    # Metadata
    notes: Optional[str]
    metadata: Dict[str, Any]
    created_at: datetime
    updated_at: datetime


@dataclass
class BillingCycle:
    """Billing cycle configuration"""
    cycle_id: str
    tenant_id: UUID
    cycle_start_date: datetime
    cycle_end_date: datetime
    invoice_generation_date: datetime
    due_date: datetime
    auto_billing_enabled: bool
    reminders_enabled: bool
    late_fee_enabled: bool
    grace_period_days: int


class BillingEngine:
    """SI Commercial Billing Engine"""
    
    def __init__(self):
        self.billing_repository = BillingRepository()
        self.cache_service = CacheService()
        self.event_bus = EventBus()
        self.metrics_collector = MetricsCollector()
        self.notification_service = NotificationService()
        self.logger = logging.getLogger(__name__)
        
        # Invoice registries
        self.invoices: Dict[str, Invoice] = {}
        self.billing_cycles: Dict[str, BillingCycle] = {}
        
        # Configuration
        self.config = {
            "default_payment_terms": "net_30",
            "late_fee_percentage": Decimal("2.5"),  # 2.5% per month
            "grace_period_days": 7,
            "auto_reminder_days": [7, 3, 1],  # Days before due date
            "currency": "NGN",
            "invoice_number_prefix": "INV",
            "tax_rates": {
                TaxRegion.NIGERIA: Decimal("0.075"),  # 7.5% VAT
                TaxRegion.US: Decimal("0.08"),
                TaxRegion.EU: Decimal("0.20"),
                TaxRegion.UK: Decimal("0.20"),
                TaxRegion.OTHER: Decimal("0.00")
            },
            "discount_programs": {
                "annual_prepay": Decimal("0.15"),  # 15% discount for annual prepayment
                "enterprise_volume": Decimal("0.10"),  # 10% volume discount
                "early_adopter": Decimal("0.20")  # 20% early adopter discount
            }
        }
    
    async def generate_monthly_invoice(
        self,
        tenant_id: UUID,
        billing_period_start: datetime,
        billing_period_end: datetime,
        force_regenerate: bool = False
    ) -> Dict[str, Any]:
        """Generate monthly subscription invoice"""
        try:
            # Check if invoice already exists
            existing_invoice = await self._find_existing_invoice(
                tenant_id, InvoiceType.SUBSCRIPTION, billing_period_start
            )
            
            if existing_invoice and not force_regenerate:
                return {
                    "status": "exists",
                    "invoice_id": existing_invoice.invoice_id,
                    "message": "Invoice already generated for this period"
                }
            
            # Get subscription details
            subscription = await self.billing_repository.get_subscription(tenant_id)
            if not subscription:
                return {"status": "error", "message": "No active subscription found"}
            
            # Calculate billing record
            billing_record = await self.billing_repository.calculate_monthly_bill(
                tenant_id, billing_period_start, billing_period_end
            )
            
            if not billing_record:
                return {"status": "error", "message": "Failed to calculate billing"}
            
            # Generate invoice
            invoice = await self._create_subscription_invoice(
                billing_record, subscription, billing_period_start, billing_period_end
            )
            
            # Apply discounts if eligible
            await self._apply_eligible_discounts(invoice, subscription)
            
            # Calculate taxes
            await self._calculate_invoice_taxes(invoice, subscription)
            
            # Finalize invoice totals
            await self._finalize_invoice_totals(invoice)
            
            # Store invoice
            self.invoices[invoice.invoice_id] = invoice
            
            # Create billing record
            await self.billing_repository.create_billing_record(billing_record)
            
            # Send invoice
            if invoice.status == InvoiceStatus.PENDING:
                await self._send_invoice(invoice)
            
            # Schedule reminders
            await self._schedule_payment_reminders(invoice)
            
            # Emit event
            await self.event_bus.emit("invoice_generated", {
                "invoice_id": invoice.invoice_id,
                "tenant_id": str(tenant_id),
                "invoice_type": invoice.invoice_type.value,
                "total_amount": float(invoice.total_amount),
                "due_date": invoice.due_date.isoformat(),
                "timestamp": datetime.now(timezone.utc).isoformat()
            })
            
            self.logger.info(f"Monthly invoice generated for tenant {tenant_id}: {invoice.invoice_id}")
            
            return {
                "status": "success",
                "invoice_id": invoice.invoice_id,
                "invoice_number": invoice.invoice_number,
                "total_amount": float(invoice.total_amount),
                "due_date": invoice.due_date.isoformat(),
                "invoice": asdict(invoice)
            }
            
        except Exception as e:
            self.logger.error(f"Error generating monthly invoice for {tenant_id}: {str(e)}")
            return {"status": "error", "message": str(e)}
    
    async def generate_overage_invoice(
        self,
        tenant_id: UUID,
        overage_charges: Dict[str, Decimal],
        billing_period_start: datetime,
        billing_period_end: datetime
    ) -> Dict[str, Any]:
        """Generate invoice for usage overage charges"""
        try:
            subscription = await self.billing_repository.get_subscription(tenant_id)
            if not subscription:
                return {"status": "error", "message": "No active subscription found"}
            
            # Create overage invoice
            invoice = await self._create_overage_invoice(
                tenant_id, UUID(subscription["organization_id"]),
                overage_charges, billing_period_start, billing_period_end
            )
            
            # Calculate taxes
            await self._calculate_invoice_taxes(invoice, subscription)
            
            # Finalize totals
            await self._finalize_invoice_totals(invoice)
            
            # Store and send invoice
            self.invoices[invoice.invoice_id] = invoice
            await self._send_invoice(invoice)
            
            # Emit event
            await self.event_bus.emit("overage_invoice_generated", {
                "invoice_id": invoice.invoice_id,
                "tenant_id": str(tenant_id),
                "overage_amount": float(invoice.total_amount),
                "timestamp": datetime.now(timezone.utc).isoformat()
            })
            
            self.logger.info(f"Overage invoice generated for tenant {tenant_id}: {invoice.invoice_id}")
            
            return {
                "status": "success",
                "invoice_id": invoice.invoice_id,
                "total_amount": float(invoice.total_amount),
                "overage_charges": {k: float(v) for k, v in overage_charges.items()}
            }
            
        except Exception as e:
            self.logger.error(f"Error generating overage invoice for {tenant_id}: {str(e)}")
            return {"status": "error", "message": str(e)}
    
    async def process_payment(
        self,
        invoice_id: str,
        payment_amount: Decimal,
        payment_method: str,
        payment_reference: str,
        payment_date: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """Process payment for invoice"""
        try:
            invoice = self.invoices.get(invoice_id)
            if not invoice:
                return {"status": "error", "message": "Invoice not found"}
            
            payment_date = payment_date or datetime.now(timezone.utc)
            
            # Validate payment amount
            if payment_amount <= 0:
                return {"status": "error", "message": "Invalid payment amount"}
            
            # Update invoice payment details
            invoice.amount_paid += payment_amount
            invoice.amount_due = max(Decimal("0"), invoice.total_amount - invoice.amount_paid)
            
            # Update status
            if invoice.amount_due <= Decimal("0"):
                invoice.status = InvoiceStatus.PAID
            elif invoice.amount_paid > Decimal("0"):
                invoice.status = InvoiceStatus.PENDING  # Partially paid
            
            invoice.updated_at = datetime.now(timezone.utc)
            
            # Update billing repository
            await self.billing_repository.update_payment_status(
                UUID(invoice.metadata.get("billing_record_id")),
                PaymentStatus.PAID if invoice.status == InvoiceStatus.PAID else PaymentStatus.PENDING,
                payment_date
            )
            
            # Send payment confirmation
            await self._send_payment_confirmation(invoice, payment_amount, payment_method)
            
            # Emit event
            await self.event_bus.emit("payment_processed", {
                "invoice_id": invoice_id,
                "tenant_id": str(invoice.tenant_id),
                "payment_amount": float(payment_amount),
                "payment_method": payment_method,
                "invoice_status": invoice.status.value,
                "timestamp": payment_date.isoformat()
            })
            
            self.logger.info(f"Payment processed for invoice {invoice_id}: {payment_amount}")
            
            return {
                "status": "success",
                "invoice_id": invoice_id,
                "payment_amount": float(payment_amount),
                "amount_paid": float(invoice.amount_paid),
                "amount_due": float(invoice.amount_due),
                "invoice_status": invoice.status.value
            }
            
        except Exception as e:
            self.logger.error(f"Error processing payment for invoice {invoice_id}: {str(e)}")
            return {"status": "error", "message": str(e)}
    
    async def generate_refund_invoice(
        self,
        original_invoice_id: str,
        refund_amount: Decimal,
        refund_reason: str,
        refund_items: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """Generate refund invoice"""
        try:
            original_invoice = self.invoices.get(original_invoice_id)
            if not original_invoice:
                return {"status": "error", "message": "Original invoice not found"}
            
            # Validate refund amount
            if refund_amount > original_invoice.amount_paid:
                return {
                    "status": "error",
                    "message": "Refund amount cannot exceed amount paid"
                }
            
            # Create refund invoice
            refund_invoice = await self._create_refund_invoice(
                original_invoice, refund_amount, refund_reason, refund_items
            )
            
            # Update original invoice
            original_invoice.amount_paid -= refund_amount
            original_invoice.amount_due += refund_amount
            if refund_amount == original_invoice.total_amount:
                original_invoice.status = InvoiceStatus.REFUNDED
            
            # Store refund invoice
            self.invoices[refund_invoice.invoice_id] = refund_invoice
            
            # Send refund notification
            await self._send_refund_notification(refund_invoice, original_invoice)
            
            # Emit event
            await self.event_bus.emit("refund_issued", {
                "refund_invoice_id": refund_invoice.invoice_id,
                "original_invoice_id": original_invoice_id,
                "tenant_id": str(original_invoice.tenant_id),
                "refund_amount": float(refund_amount),
                "refund_reason": refund_reason,
                "timestamp": datetime.now(timezone.utc).isoformat()
            })
            
            self.logger.info(f"Refund invoice generated: {refund_invoice.invoice_id} for {refund_amount}")
            
            return {
                "status": "success",
                "refund_invoice_id": refund_invoice.invoice_id,
                "original_invoice_id": original_invoice_id,
                "refund_amount": float(refund_amount)
            }
            
        except Exception as e:
            self.logger.error(f"Error generating refund invoice: {str(e)}")
            return {"status": "error", "message": str(e)}
    
    async def get_invoice_details(self, invoice_id: str) -> Optional[Dict[str, Any]]:
        """Get complete invoice details"""
        try:
            invoice = self.invoices.get(invoice_id)
            if not invoice:
                return None
            
            # Add payment history
            payment_history = await self._get_payment_history(invoice_id)
            
            # Add aging information
            aging_info = await self._calculate_invoice_aging(invoice)
            
            invoice_dict = asdict(invoice)
            invoice_dict.update({
                "payment_history": payment_history,
                "aging_info": aging_info
            })
            
            return invoice_dict
            
        except Exception as e:
            self.logger.error(f"Error getting invoice details for {invoice_id}: {str(e)}")
            return None
    
    async def get_billing_summary(
        self,
        tenant_id: UUID,
        period_months: int = 12
    ) -> Dict[str, Any]:
        """Get comprehensive billing summary"""
        try:
            end_date = datetime.now(timezone.utc)
            start_date = end_date - timedelta(days=period_months * 30)
            
            # Get all invoices for period
            tenant_invoices = [
                invoice for invoice in self.invoices.values()
                if invoice.tenant_id == tenant_id and invoice.issue_date >= start_date
            ]
            
            # Calculate summary metrics
            total_billed = sum(invoice.total_amount for invoice in tenant_invoices)
            total_paid = sum(invoice.amount_paid for invoice in tenant_invoices)
            total_outstanding = sum(invoice.amount_due for invoice in tenant_invoices)
            
            # Group by status
            status_breakdown = {}
            for status in InvoiceStatus:
                status_invoices = [i for i in tenant_invoices if i.status == status]
                status_breakdown[status.value] = {
                    "count": len(status_invoices),
                    "total_amount": float(sum(i.total_amount for i in status_invoices))
                }
            
            # Monthly breakdown
            monthly_breakdown = await self._calculate_monthly_breakdown(tenant_invoices)
            
            # Overdue analysis
            overdue_analysis = await self._calculate_overdue_analysis(tenant_invoices)
            
            return {
                "tenant_id": str(tenant_id),
                "period": {
                    "start_date": start_date.isoformat(),
                    "end_date": end_date.isoformat(),
                    "months": period_months
                },
                "summary": {
                    "total_invoices": len(tenant_invoices),
                    "total_billed": float(total_billed),
                    "total_paid": float(total_paid),
                    "total_outstanding": float(total_outstanding),
                    "payment_rate": float(total_paid / total_billed) if total_billed > 0 else 0
                },
                "status_breakdown": status_breakdown,
                "monthly_breakdown": monthly_breakdown,
                "overdue_analysis": overdue_analysis,
                "generated_at": datetime.now(timezone.utc).isoformat()
            }
            
        except Exception as e:
            self.logger.error(f"Error generating billing summary for {tenant_id}: {str(e)}")
            return {"status": "error", "message": str(e)}
    
    # Private helper methods
    
    async def _create_subscription_invoice(
        self,
        billing_record: BillingRecord,
        subscription: Dict[str, Any],
        period_start: datetime,
        period_end: datetime
    ) -> Invoice:
        """Create subscription invoice from billing record"""
        try:
            invoice_id = str(uuid4())
            invoice_number = await self._generate_invoice_number()
            
            # Create line items
            line_items = []
            
            # Base subscription line item
            if billing_record.base_amount > 0:
                base_item = LineItem(
                    item_id=str(uuid4()),
                    description=f"{billing_record.subscription_tier.value.title()} Subscription",
                    quantity=Decimal("1"),
                    unit_price=billing_record.base_amount,
                    line_total=billing_record.base_amount,
                    tax_rate=Decimal("0"),
                    tax_amount=Decimal("0"),
                    discount_rate=Decimal("0"),
                    discount_amount=Decimal("0"),
                    metadata={"type": "subscription", "tier": billing_record.subscription_tier.value}
                )
                line_items.append(base_item)
            
            # Overage charges
            if billing_record.usage_amount > 0:
                overage_item = LineItem(
                    item_id=str(uuid4()),
                    description=f"Usage Overage ({billing_record.overage_invoices} invoices)",
                    quantity=Decimal(str(billing_record.overage_invoices)),
                    unit_price=billing_record.usage_amount / Decimal(str(billing_record.overage_invoices)),
                    line_total=billing_record.usage_amount,
                    tax_rate=Decimal("0"),
                    tax_amount=Decimal("0"),
                    discount_rate=Decimal("0"),
                    discount_amount=Decimal("0"),
                    metadata={"type": "overage", "overage_count": billing_record.overage_invoices}
                )
                line_items.append(overage_item)
            
            invoice = Invoice(
                invoice_id=invoice_id,
                invoice_number=invoice_number,
                tenant_id=billing_record.tenant_id,
                organization_id=billing_record.organization_id,
                invoice_type=InvoiceType.SUBSCRIPTION,
                status=InvoiceStatus.PENDING,
                issue_date=datetime.now(timezone.utc),
                due_date=datetime.now(timezone.utc) + timedelta(days=30),
                billing_period_start=period_start,
                billing_period_end=period_end,
                line_items=line_items,
                subtotal=billing_record.base_amount + billing_record.usage_amount,
                total_discount=Decimal("0"),
                tax_calculation=TaxCalculation(
                    region=TaxRegion.NIGERIA,
                    tax_rate=Decimal("0"),
                    taxable_amount=Decimal("0"),
                    tax_amount=Decimal("0"),
                    tax_breakdown={}
                ),
                total_amount=billing_record.total_amount,
                amount_paid=Decimal("0"),
                amount_due=billing_record.total_amount,
                currency=self.config["currency"],
                payment_terms=self.config["default_payment_terms"],
                payment_methods=["bank_transfer", "card", "wallet"],
                subscription_id=subscription.get("id"),
                previous_invoice_id=None,
                notes=None,
                metadata={
                    "billing_record_id": str(billing_record.id),
                    "subscription_tier": billing_record.subscription_tier.value,
                    "invoice_count": billing_record.invoice_count,
                    "overage_count": billing_record.overage_invoices
                },
                created_at=datetime.now(timezone.utc),
                updated_at=datetime.now(timezone.utc)
            )
            
            return invoice
            
        except Exception as e:
            self.logger.error(f"Error creating subscription invoice: {str(e)}")
            raise
    
    async def _generate_invoice_number(self) -> str:
        """Generate unique invoice number"""
        try:
            # Get current year and month
            now = datetime.now(timezone.utc)
            year_month = now.strftime("%Y%m")
            
            # Get sequential number for this month
            cache_key = f"invoice_sequence:{year_month}"
            sequence = await self.cache_service.get(cache_key) or 0
            sequence += 1
            
            # Store updated sequence
            await self.cache_service.set(cache_key, sequence, ttl=86400 * 32)  # 32 days
            
            # Format invoice number
            invoice_number = f"{self.config['invoice_number_prefix']}-{year_month}-{sequence:04d}"
            
            return invoice_number
            
        except Exception as e:
            self.logger.error(f"Error generating invoice number: {str(e)}")
            # Fallback to timestamp-based number
            return f"{self.config['invoice_number_prefix']}-{int(datetime.now().timestamp())}"
    
    async def health_check(self) -> Dict[str, Any]:
        """Health check for billing engine"""
        try:
            return {
                "status": "healthy",
                "service": "billing_engine",
                "invoices": len(self.invoices),
                "billing_cycles": len(self.billing_cycles),
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
        except Exception as e:
            self.logger.error(f"Health check failed: {str(e)}")
            return {
                "status": "error",
                "service": "billing_engine",
                "error": str(e),
                "timestamp": datetime.now(timezone.utc).isoformat()
            }


def create_billing_engine() -> BillingEngine:
    """Create billing engine instance"""
    return BillingEngine()