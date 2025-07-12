"""
Nigerian Tax Jurisdiction Management Service

This service provides comprehensive Nigerian tax jurisdiction management,
building upon the existing Nigerian business services with enhanced
multi-jurisdictional tax calculations and FIRS penalty management.
"""

from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from uuid import UUID
from decimal import Decimal
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func
from dataclasses import dataclass

from app.models.nigerian_business import (
    NigerianConglomerate,
    NigerianSubsidiary,
    TaxConsolidationType
)
from app.models.nigerian_compliance import (
    FIRSPenaltyTracking,
    NigerianBusinessRegistration
)
from app.models.organization import Organization


@dataclass
class Location:
    """Location data structure for tax calculations."""
    state_code: str
    state_name: str
    lga_code: str
    lga_name: str
    region: str


@dataclass
class TaxBreakdown:
    """Comprehensive tax breakdown structure."""
    federal_taxes: List[Dict[str, Any]]
    state_taxes: List[Dict[str, Any]]
    local_taxes: List[Dict[str, Any]]
    total_tax: float
    
    def __init__(self):
        self.federal_taxes = []
        self.state_taxes = []
        self.local_taxes = []
        self.total_tax = 0.0


@dataclass
class NigerianState:
    """Nigerian state data structure."""
    code: str
    name: str
    capital: str
    region: str
    internal_revenue_service: str
    tax_rates: Dict[str, float]
    major_lgas: List[str]


@dataclass
class PenaltyCalculation:
    """FIRS penalty calculation result."""
    total_penalty: float
    first_day_penalty: float
    subsequent_days_penalty: float
    days_non_compliant: int
    daily_penalty_rate: float
    penalty_breakdown: List[Dict[str, Any]]
    
    def __init__(self, total_penalty: float = 0, days: int = 0):
        self.total_penalty = total_penalty
        self.days_non_compliant = days
        self.penalty_breakdown = []


@dataclass
class PaymentOption:
    """Payment option for penalty settlement."""
    type: str
    discount: float = 0.0
    installments: int = 1
    interest_rate: float = 0.0
    terms: str = ""


@dataclass
class PaymentPlan:
    """Payment plan for penalty settlement."""
    penalty_amount: float
    options: List[PaymentOption]
    grace_period_days: int
    late_payment_additional_penalty: float


class NigerianTaxJurisdictionService:
    """Comprehensive Nigerian tax jurisdiction management service."""
    
    def __init__(self, db: Session):
        self.db = db
        self.states = self._load_nigerian_states()
        self.local_governments = self._load_lgas()
        self.tax_authorities = self._load_tax_authorities()
    
    def _load_nigerian_states(self) -> List[NigerianState]:
        """Load comprehensive Nigerian states data."""
        return [
            NigerianState(
                code='LA',
                name='Lagos',
                capital='Ikeja',
                region='South West',
                internal_revenue_service='Lagos State Internal Revenue Service',
                tax_rates={'personal_income': 0.10, 'business': 0.30, 'withholding': 0.05},
                major_lgas=['Ikeja', 'Lagos Island', 'Lagos Mainland', 'Surulere', 'Alimosho', 'Kosofe']
            ),
            NigerianState(
                code='KN',
                name='Kano',
                capital='Kano',
                region='North West',
                internal_revenue_service='Kano State Internal Revenue Service',
                tax_rates={'personal_income': 0.05, 'business': 0.25, 'withholding': 0.03},
                major_lgas=['Kano Municipal', 'Fagge', 'Dala', 'Gwale', 'Tarauni', 'Nassarawa']
            ),
            NigerianState(
                code='RV',
                name='Rivers',
                capital='Port Harcourt',
                region='South South',
                internal_revenue_service='Rivers State Internal Revenue Service',
                tax_rates={'personal_income': 0.07, 'business': 0.28, 'withholding': 0.04},
                major_lgas=['Port Harcourt', 'Obio-Akpor', 'Okrika', 'Oyigbo', 'Eleme', 'Ikwerre']
            ),
            NigerianState(
                code='OG',
                name='Ogun',
                capital='Abeokuta',
                region='South West',
                internal_revenue_service='Ogun State Internal Revenue Service',
                tax_rates={'personal_income': 0.08, 'business': 0.26, 'withholding': 0.035},
                major_lgas=['Abeokuta North', 'Abeokuta South', 'Sagamu', 'Ijebu Ode', 'Ado-Odo/Ota', 'Ewekoro']
            ),
            NigerianState(
                code='FC',
                name='Federal Capital Territory',
                capital='Abuja',
                region='North Central',
                internal_revenue_service='FCT Internal Revenue Service',
                tax_rates={'personal_income': 0.09, 'business': 0.30, 'withholding': 0.045},
                major_lgas=['Abuja Municipal', 'Gwagwalada', 'Kuje', 'Bwari', 'Abaji', 'Kwali']
            ),
            NigerianState(
                code='KD',
                name='Kaduna',
                capital='Kaduna',
                region='North West',
                internal_revenue_service='Kaduna State Internal Revenue Service',
                tax_rates={'personal_income': 0.06, 'business': 0.24, 'withholding': 0.03},
                major_lgas=['Kaduna North', 'Kaduna South', 'Chikun', 'Igabi', 'Kajuru', 'Zaria']
            )
            # Additional states would be added here for complete coverage
        ]
    
    def _load_lgas(self) -> Dict[str, List[str]]:
        """Load Local Government Areas by state."""
        return {
            'Lagos': [
                'Agege', 'Ajeromi-Ifelodun', 'Alimosho', 'Amuwo-Odofin', 'Apapa',
                'Badagry', 'Epe', 'Eti Osa', 'Ibeju-Lekki', 'Ifako-Ijaiye',
                'Ikeja', 'Ikorodu', 'Kosofe', 'Lagos Island', 'Lagos Mainland',
                'Mushin', 'Ojo', 'Oshodi-Isolo', 'Shomolu', 'Surulere'
            ],
            'Kano': [
                'Ajingi', 'Albasu', 'Bagwai', 'Bebeji', 'Bichi', 'Bunkure',
                'Dala', 'Dambatta', 'Dawakin Kudu', 'Dawakin Tofa', 'Doguwa',
                'Fagge', 'Gabasawa', 'Garko', 'Garun Mallam', 'Gaya', 'Gezawa',
                'Gwale', 'Gwarzo', 'Kabo', 'Kano Municipal', 'Karaye', 'Kibiya',
                'Kiru', 'Kumbotso', 'Kunchi', 'Kura', 'Madobi', 'Makoda',
                'Minjibir', 'Nasarawa', 'Rano', 'Rimin Gado', 'Rogo', 'Shanono',
                'Sumaila', 'Takai', 'Tarauni', 'Tofa', 'Tsanyawa', 'Tudun Wada',
                'Ungogo', 'Warawa', 'Wudil'
            ]
            # Additional LGAs for other states would be added here
        }
    
    def _load_tax_authorities(self) -> Dict[str, Dict[str, Any]]:
        """Load tax authority information."""
        return {
            'FIRS': {
                'name': 'Federal Inland Revenue Service',
                'jurisdiction': 'Federal',
                'taxes': ['VAT', 'Company Income Tax', 'Withholding Tax', 'Capital Gains Tax'],
                'penalties': {
                    'first_day': 1000000,  # ₦1M
                    'subsequent_day': 10000  # ₦10K per day
                }
            },
            'LIRS': {
                'name': 'Lagos State Internal Revenue Service',
                'jurisdiction': 'State',
                'taxes': ['Personal Income Tax', 'Land Use Charge', 'Development Levy'],
                'penalties': {
                    'percentage': 0.05,  # 5% of tax due
                    'minimum': 50000     # ₦50K minimum
                }
            }
        }
    
    async def calculate_multi_jurisdiction_tax(self, 
                                             business_locations: List[Location],
                                             invoice_amount: float) -> TaxBreakdown:
        """Calculate taxes across Nigerian jurisdictions."""
        
        tax_breakdown = TaxBreakdown()
        
        for location in business_locations:
            # Federal taxes (FIRS) - Applied to all locations
            federal_vat = invoice_amount * 0.075  # 7.5% VAT
            tax_breakdown.federal_taxes.append({
                'type': 'VAT',
                'rate': 0.075,
                'amount': federal_vat,
                'authority': 'FIRS',
                'jurisdiction': 'Federal',
                'location': location.state_name
            })
            
            # Company Income Tax - Applied based on annual revenue
            if invoice_amount > 25000000:  # ₦25M threshold for large companies
                cit_rate = 0.30
            else:
                cit_rate = 0.20  # Small companies
                
            cit_amount = invoice_amount * cit_rate
            tax_breakdown.federal_taxes.append({
                'type': 'Company Income Tax',
                'rate': cit_rate,
                'amount': cit_amount,
                'authority': 'FIRS',
                'jurisdiction': 'Federal',
                'location': location.state_name
            })
            
            # State taxes - Based on specific state
            state_info = self._get_state_info(location.state_code)
            if state_info:
                state_tax_rate = state_info.tax_rates.get('business', 0.015)
                state_tax = invoice_amount * state_tax_rate
                
                tax_breakdown.state_taxes.append({
                    'type': 'State Revenue Tax',
                    'rate': state_tax_rate,
                    'amount': state_tax,
                    'authority': state_info.internal_revenue_service,
                    'jurisdiction': 'State',
                    'location': location.state_name
                })
            
            # Local Government taxes
            lga_tax_rate = self._get_lga_tax_rate(location.lga_code)
            lga_tax = invoice_amount * lga_tax_rate
            
            tax_breakdown.local_taxes.append({
                'type': 'Local Government Service Tax',
                'rate': lga_tax_rate,
                'amount': lga_tax,
                'authority': f"{location.lga_name} Local Government",
                'jurisdiction': 'Local',
                'location': f"{location.lga_name}, {location.state_name}"
            })
        
        # Calculate total tax
        tax_breakdown.total_tax = (
            sum(tax['amount'] for tax in tax_breakdown.federal_taxes) +
            sum(tax['amount'] for tax in tax_breakdown.state_taxes) +
            sum(tax['amount'] for tax in tax_breakdown.local_taxes)
        )
        
        return tax_breakdown
    
    def _get_state_info(self, state_code: str) -> Optional[NigerianState]:
        """Get state information by code."""
        return next((state for state in self.states if state.code == state_code), None)
    
    def _get_lga_tax_rate(self, lga_code: str) -> float:
        """Get LGA tax rate (typically standardized)."""
        # Most LGAs use 0.5% service tax
        return 0.005
    
    async def get_nigerian_states_data(self) -> List[NigerianState]:
        """Get comprehensive Nigerian states data."""
        return self.states
    
    async def validate_jurisdiction(self, state_code: str, lga_code: str) -> bool:
        """Validate if the state and LGA combination is valid."""
        state_info = self._get_state_info(state_code)
        if not state_info:
            return False
        
        state_lgas = self.local_governments.get(state_info.name, [])
        return lga_code in [lga.replace(' ', '_').upper() for lga in state_lgas]
        

class FIRSPenaltyManager:
    """Manage FIRS compliance penalties for Nigerian businesses."""
    
    def __init__(self, db: Session):
        self.db = db
    
    async def calculate_non_compliance_penalty(self, 
                                             organization_id: UUID,
                                             violation_date: datetime) -> PenaltyCalculation:
        """Calculate FIRS non-compliance penalties."""
        
        days_non_compliant = (datetime.utcnow() - violation_date).days
        
        if days_non_compliant <= 0:
            return PenaltyCalculation(total_penalty=0, days=0)
        
        # FIRS penalty structure according to Nigerian tax laws
        first_day_penalty = 1000000  # ₦1,000,000 first day
        subsequent_day_penalty = 10000  # ₦10,000 each subsequent day
        
        penalty_calc = PenaltyCalculation(days=days_non_compliant)
        
        if days_non_compliant == 1:
            penalty_calc.total_penalty = first_day_penalty
            penalty_calc.first_day_penalty = first_day_penalty
            penalty_calc.subsequent_days_penalty = 0
        else:
            subsequent_total = (days_non_compliant - 1) * subsequent_day_penalty
            penalty_calc.total_penalty = first_day_penalty + subsequent_total
            penalty_calc.first_day_penalty = first_day_penalty
            penalty_calc.subsequent_days_penalty = subsequent_total
        
        penalty_calc.daily_penalty_rate = subsequent_day_penalty
        
        # Create penalty breakdown
        penalty_calc.penalty_breakdown = [
            {
                'type': 'First Day Penalty',
                'amount': first_day_penalty,
                'description': 'Initial non-compliance penalty'
            }
        ]
        
        if days_non_compliant > 1:
            penalty_calc.penalty_breakdown.append({
                'type': 'Subsequent Days Penalty',
                'days': days_non_compliant - 1,
                'daily_rate': subsequent_day_penalty,
                'amount': subsequent_total,
                'description': f'Daily penalty for {days_non_compliant - 1} additional days'
            })
        
        return penalty_calc
    
    async def setup_penalty_payment_plan(self, 
                                        organization_id: UUID,
                                        penalty_amount: float) -> PaymentPlan:
        """Setup penalty payment plan with FIRS."""
        
        # Nigerian business-friendly payment terms
        payment_options = [
            PaymentOption(
                type='immediate',
                discount=0.05,  # 5% discount for immediate payment
                terms='Full payment within 7 days with 5% discount'
            ),
            PaymentOption(
                type='short_term',
                installments=2,
                interest_rate=0.01,  # 1% interest
                terms='2 equal installments over 60 days'
            ),
            PaymentOption(
                type='quarterly',
                installments=4,
                interest_rate=0.02,  # 2% quarterly interest
                terms='4 quarterly installments with 2% quarterly interest'
            ),
            PaymentOption(
                type='monthly',
                installments=12,
                interest_rate=0.015,  # 1.5% monthly interest
                terms='12 monthly installments with 1.5% monthly interest'
            )
        ]
        
        return PaymentPlan(
            penalty_amount=penalty_amount,
            options=payment_options,
            grace_period_days=30,
            late_payment_additional_penalty=0.01  # 1% per month
        )
    
    async def track_penalty_status(self, 
                                  organization_id: UUID,
                                  penalty_data: Dict[str, Any]) -> FIRSPenaltyTracking:
        """Track FIRS penalty status in the database."""
        
        penalty_tracking = FIRSPenaltyTracking(
            organization_id=organization_id,
            penalty_type=penalty_data.get('penalty_type', 'non_compliance'),
            penalty_amount_ngn=penalty_data.get('penalty_amount'),
            violation_date=penalty_data.get('violation_date'),
            penalty_calculation_date=datetime.utcnow(),
            days_non_compliant=penalty_data.get('days_non_compliant'),
            payment_plan_selected=penalty_data.get('payment_plan_type'),
            installment_count=penalty_data.get('installments', 1),
            monthly_installment_amount=penalty_data.get('monthly_amount'),
            next_payment_due_date=penalty_data.get('next_payment_date'),
            total_amount_paid=penalty_data.get('amount_paid', 0),
            remaining_balance=penalty_data.get('penalty_amount', 0),
            penalty_status='active'
        )
        
        self.db.add(penalty_tracking)
        await self.db.commit()
        await self.db.refresh(penalty_tracking)
        
        return penalty_tracking
    
    async def process_penalty_payment(self,
                                    penalty_id: UUID,
                                    payment_amount: float) -> FIRSPenaltyTracking:
        """Process a penalty payment."""
        
        penalty = await self.db.get(FIRSPenaltyTracking, penalty_id)
        if not penalty:
            raise ValueError("Penalty record not found")
        
        penalty.total_amount_paid += payment_amount
        penalty.remaining_balance = max(0, penalty.remaining_balance - payment_amount)
        penalty.last_payment_date = datetime.utcnow()
        
        if penalty.remaining_balance <= 0:
            penalty.penalty_status = 'settled'
            penalty.settlement_date = datetime.utcnow()
        else:
            # Calculate next payment date based on payment plan
            if penalty.payment_plan_selected == 'monthly':
                penalty.next_payment_due_date = datetime.utcnow() + timedelta(days=30)
            elif penalty.payment_plan_selected == 'quarterly':
                penalty.next_payment_due_date = datetime.utcnow() + timedelta(days=90)
        
        await self.db.commit()
        await self.db.refresh(penalty)
        
        return penalty
    
    async def get_organization_penalties(self, organization_id: UUID) -> List[FIRSPenaltyTracking]:
        """Get all penalties for an organization."""
        
        penalties = await self.db.query(FIRSPenaltyTracking).filter(
            FIRSPenaltyTracking.organization_id == organization_id
        ).order_by(FIRSPenaltyTracking.violation_date.desc()).all()
        
        return penalties
    
    async def get_penalty_summary(self, organization_id: UUID) -> Dict[str, Any]:
        """Get penalty summary for an organization."""
        
        penalties = await self.get_organization_penalties(organization_id)
        
        total_penalties = sum(float(p.penalty_amount_ngn or 0) for p in penalties)
        total_paid = sum(float(p.total_amount_paid or 0) for p in penalties)
        active_penalties = [p for p in penalties if p.penalty_status == 'active']
        
        return {
            'total_penalties_ngn': total_penalties,
            'total_paid_ngn': total_paid,
            'outstanding_balance_ngn': total_penalties - total_paid,
            'active_penalty_count': len(active_penalties),
            'settled_penalty_count': len([p for p in penalties if p.penalty_status == 'settled']),
            'next_payment_due': min([p.next_payment_due_date for p in active_penalties if p.next_payment_due_date], default=None)
        }