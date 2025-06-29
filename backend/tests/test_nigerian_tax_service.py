"""
Tests for Nigerian Tax Jurisdiction Service

Comprehensive test suite for Nigerian tax calculations, state management,
and FIRS penalty tracking.
"""

import pytest
import asyncio
from datetime import datetime, timedelta
from decimal import Decimal
from uuid import uuid4

from app.services.nigerian_tax_service import (
    NigerianTaxJurisdictionService,
    FIRSPenaltyManager,
    Location,
    TaxBreakdown,
    PenaltyCalculation,
    PaymentPlan
)
from app.models.nigerian_compliance import FIRSPenaltyTracking
from app.models.nigerian_business import NigerianSubsidiary
from tests.conftest import TestDB


class TestNigerianTaxJurisdictionService:
    """Test cases for Nigerian Tax Jurisdiction Service."""
    
    @pytest.fixture
    def tax_service(self, test_db):
        """Create tax service instance."""
        return NigerianTaxJurisdictionService(test_db)
    
    @pytest.fixture
    def sample_locations(self):
        """Sample Nigerian locations for testing."""
        return [
            Location(
                state_code='LA',
                state_name='Lagos',
                lga_code='IKEJA',
                lga_name='Ikeja',
                region='South West'
            ),
            Location(
                state_code='KN',
                state_name='Kano',
                lga_code='KANO_MUNICIPAL',
                lga_name='Kano Municipal',
                region='North West'
            )
        ]
    
    def test_load_nigerian_states(self, tax_service):
        """Test loading of Nigerian states data."""
        states = tax_service._load_nigerian_states()
        
        assert len(states) >= 6, "Should have at least 6 states defined"
        
        # Check for specific states
        state_codes = [state.code for state in states]
        assert 'LA' in state_codes, "Lagos should be included"
        assert 'KN' in state_codes, "Kano should be included"
        assert 'FC' in state_codes, "FCT should be included"
        
        # Verify Lagos state details
        lagos = next(state for state in states if state.code == 'LA')
        assert lagos.name == 'Lagos'
        assert lagos.capital == 'Ikeja'
        assert lagos.region == 'South West'
        assert 'Lagos State Internal Revenue Service' in lagos.internal_revenue_service
        assert 'business' in lagos.tax_rates
        assert len(lagos.major_lgas) > 0
    
    def test_get_state_info(self, tax_service):
        """Test getting state information by code."""
        lagos_info = tax_service._get_state_info('LA')
        
        assert lagos_info is not None
        assert lagos_info.name == 'Lagos'
        assert lagos_info.code == 'LA'
        
        # Test non-existent state
        non_existent = tax_service._get_state_info('XX')
        assert non_existent is None
    
    def test_get_lga_tax_rate(self, tax_service):
        """Test LGA tax rate calculation."""
        rate = tax_service._get_lga_tax_rate('IKEJA')
        
        assert rate == 0.005, "LGA tax rate should be 0.5%"
    
    @pytest.mark.asyncio
    async def test_get_nigerian_states_data(self, tax_service):
        """Test async method to get states data."""
        states = await tax_service.get_nigerian_states_data()
        
        assert len(states) >= 6
        assert all(hasattr(state, 'code') for state in states)
        assert all(hasattr(state, 'name') for state in states)
        assert all(hasattr(state, 'tax_rates') for state in states)
    
    @pytest.mark.asyncio
    async def test_validate_jurisdiction(self, tax_service):
        """Test jurisdiction validation."""
        # Valid combinations
        assert await tax_service.validate_jurisdiction('LA', 'IKEJA')
        
        # Invalid state code
        assert not await tax_service.validate_jurisdiction('XX', 'IKEJA')
    
    @pytest.mark.asyncio
    async def test_calculate_multi_jurisdiction_tax_single_location(self, tax_service, sample_locations):
        """Test tax calculation for single location."""
        invoice_amount = 10000000.0  # ₦10M
        single_location = [sample_locations[0]]  # Just Lagos
        
        tax_breakdown = await tax_service.calculate_multi_jurisdiction_tax(
            single_location, invoice_amount
        )
        
        assert isinstance(tax_breakdown, TaxBreakdown)
        assert tax_breakdown.total_tax > 0
        assert len(tax_breakdown.federal_taxes) == 2  # VAT + CIT
        assert len(tax_breakdown.state_taxes) == 1   # Lagos state tax
        assert len(tax_breakdown.local_taxes) == 1   # Ikeja LGA tax
        
        # Verify VAT calculation (7.5%)
        vat_taxes = [tax for tax in tax_breakdown.federal_taxes if tax['type'] == 'VAT']
        assert len(vat_taxes) == 1
        assert vat_taxes[0]['amount'] == invoice_amount * 0.075
        assert vat_taxes[0]['authority'] == 'FIRS'
        
        # Verify CIT calculation
        cit_taxes = [tax for tax in tax_breakdown.federal_taxes if tax['type'] == 'Company Income Tax']
        assert len(cit_taxes) == 1
        assert cit_taxes[0]['rate'] == 0.30  # Large company rate for ₦10M
        
        # Verify state tax
        assert tax_breakdown.state_taxes[0]['authority'] == 'Lagos State Internal Revenue Service'
        
        # Verify LGA tax
        assert tax_breakdown.local_taxes[0]['authority'] == 'Ikeja Local Government'
        assert tax_breakdown.local_taxes[0]['rate'] == 0.005
    
    @pytest.mark.asyncio
    async def test_calculate_multi_jurisdiction_tax_multiple_locations(self, tax_service, sample_locations):
        """Test tax calculation for multiple locations."""
        invoice_amount = 5000000.0  # ₦5M
        
        tax_breakdown = await tax_service.calculate_multi_jurisdiction_tax(
            sample_locations, invoice_amount
        )
        
        assert len(tax_breakdown.federal_taxes) == 4  # VAT + CIT for each location
        assert len(tax_breakdown.state_taxes) == 2   # Lagos + Kano state taxes
        assert len(tax_breakdown.local_taxes) == 2   # Ikeja + Kano Municipal LGA taxes
        
        # Verify total tax is sum of all components
        expected_total = (
            sum(tax['amount'] for tax in tax_breakdown.federal_taxes) +
            sum(tax['amount'] for tax in tax_breakdown.state_taxes) +
            sum(tax['amount'] for tax in tax_breakdown.local_taxes)
        )
        assert abs(tax_breakdown.total_tax - expected_total) < 0.01
    
    @pytest.mark.asyncio
    async def test_calculate_small_company_tax_rate(self, tax_service, sample_locations):
        """Test CIT calculation for small companies."""
        invoice_amount = 20000000.0  # ₦20M (below ₦25M threshold)
        single_location = [sample_locations[0]]
        
        tax_breakdown = await tax_service.calculate_multi_jurisdiction_tax(
            single_location, invoice_amount
        )
        
        # Verify small company CIT rate (20%)
        cit_taxes = [tax for tax in tax_breakdown.federal_taxes if tax['type'] == 'Company Income Tax']
        assert len(cit_taxes) == 1
        assert cit_taxes[0]['rate'] == 0.20


class TestFIRSPenaltyManager:
    """Test cases for FIRS Penalty Manager."""
    
    @pytest.fixture
    def penalty_manager(self, test_db):
        """Create penalty manager instance."""
        return FIRSPenaltyManager(test_db)
    
    @pytest.fixture
    def sample_organization_id(self):
        """Sample organization ID."""
        return uuid4()
    
    @pytest.mark.asyncio
    async def test_calculate_non_compliance_penalty_single_day(self, penalty_manager, sample_organization_id):
        """Test penalty calculation for single day violation."""
        violation_date = datetime.utcnow() - timedelta(days=1)
        
        penalty = await penalty_manager.calculate_non_compliance_penalty(
            sample_organization_id, violation_date
        )
        
        assert isinstance(penalty, PenaltyCalculation)
        assert penalty.days_non_compliant == 1
        assert penalty.total_penalty == 1000000  # ₦1M first day
        assert penalty.first_day_penalty == 1000000
        assert penalty.subsequent_days_penalty == 0
        assert penalty.daily_penalty_rate == 10000
        assert len(penalty.penalty_breakdown) == 1
        assert penalty.penalty_breakdown[0]['type'] == 'First Day Penalty'
    
    @pytest.mark.asyncio
    async def test_calculate_non_compliance_penalty_multiple_days(self, penalty_manager, sample_organization_id):
        """Test penalty calculation for multiple days violation."""
        violation_date = datetime.utcnow() - timedelta(days=5)
        
        penalty = await penalty_manager.calculate_non_compliance_penalty(
            sample_organization_id, violation_date
        )
        
        assert penalty.days_non_compliant == 5
        assert penalty.first_day_penalty == 1000000
        assert penalty.subsequent_days_penalty == 4 * 10000  # 4 additional days × ₦10K
        assert penalty.total_penalty == 1000000 + (4 * 10000)
        assert len(penalty.penalty_breakdown) == 2
        
        # Check breakdown details
        first_day = penalty.penalty_breakdown[0]
        assert first_day['type'] == 'First Day Penalty'
        assert first_day['amount'] == 1000000
        
        subsequent_days = penalty.penalty_breakdown[1]
        assert subsequent_days['type'] == 'Subsequent Days Penalty'
        assert subsequent_days['days'] == 4
        assert subsequent_days['daily_rate'] == 10000
        assert subsequent_days['amount'] == 40000
    
    @pytest.mark.asyncio
    async def test_calculate_non_compliance_penalty_future_date(self, penalty_manager, sample_organization_id):
        """Test penalty calculation for future violation date (should return zero)."""
        violation_date = datetime.utcnow() + timedelta(days=1)
        
        penalty = await penalty_manager.calculate_non_compliance_penalty(
            sample_organization_id, violation_date
        )
        
        assert penalty.total_penalty == 0
        assert penalty.days_non_compliant == 0
    
    @pytest.mark.asyncio
    async def test_setup_penalty_payment_plan(self, penalty_manager, sample_organization_id):
        """Test penalty payment plan setup."""
        penalty_amount = 1040000.0  # ₦1.04M (5 days penalty)
        
        payment_plan = await penalty_manager.setup_penalty_payment_plan(
            sample_organization_id, penalty_amount
        )
        
        assert isinstance(payment_plan, PaymentPlan)
        assert payment_plan.penalty_amount == penalty_amount
        assert len(payment_plan.options) == 4
        assert payment_plan.grace_period_days == 30
        assert payment_plan.late_payment_additional_penalty == 0.01
        
        # Check immediate payment option
        immediate_option = next(opt for opt in payment_plan.options if opt.type == 'immediate')
        assert immediate_option.discount == 0.05
        assert immediate_option.installments == 1
        assert '5% discount' in immediate_option.terms
        
        # Check quarterly option
        quarterly_option = next(opt for opt in payment_plan.options if opt.type == 'quarterly')
        assert quarterly_option.installments == 4
        assert quarterly_option.interest_rate == 0.02
        
        # Check monthly option
        monthly_option = next(opt for opt in payment_plan.options if opt.type == 'monthly')
        assert monthly_option.installments == 12
        assert monthly_option.interest_rate == 0.015
    
    @pytest.mark.asyncio
    async def test_track_penalty_status(self, penalty_manager, sample_organization_id, test_db):
        """Test penalty status tracking in database."""
        penalty_data = {
            'penalty_type': 'non_compliance',
            'penalty_amount': 1040000.0,
            'violation_date': datetime.utcnow() - timedelta(days=5),
            'days_non_compliant': 5,
            'payment_plan_type': 'quarterly',
            'installments': 4,
            'monthly_amount': 260000.0,
            'next_payment_date': datetime.utcnow() + timedelta(days=30),
            'amount_paid': 0.0
        }
        
        penalty_tracking = await penalty_manager.track_penalty_status(
            sample_organization_id, penalty_data
        )
        
        assert penalty_tracking.organization_id == sample_organization_id
        assert penalty_tracking.penalty_type == 'non_compliance'
        assert penalty_tracking.penalty_amount_ngn == 1040000.0
        assert penalty_tracking.days_non_compliant == 5
        assert penalty_tracking.payment_plan_selected == 'quarterly'
        assert penalty_tracking.penalty_status == 'active'
        assert penalty_tracking.remaining_balance == 1040000.0
    
    @pytest.mark.asyncio
    async def test_process_penalty_payment(self, penalty_manager, sample_organization_id, test_db):
        """Test penalty payment processing."""
        # First create a penalty record
        penalty_data = {
            'penalty_type': 'non_compliance',
            'penalty_amount': 1040000.0,
            'violation_date': datetime.utcnow() - timedelta(days=5),
            'days_non_compliant': 5,
            'payment_plan_type': 'quarterly',
            'installments': 4,
            'amount_paid': 0.0
        }
        
        penalty_tracking = await penalty_manager.track_penalty_status(
            sample_organization_id, penalty_data
        )
        
        # Process a payment
        payment_amount = 260000.0  # First installment
        updated_penalty = await penalty_manager.process_penalty_payment(
            penalty_tracking.id, payment_amount
        )
        
        assert updated_penalty.total_amount_paid == 260000.0
        assert updated_penalty.remaining_balance == 780000.0
        assert updated_penalty.penalty_status == 'active'  # Still active with remaining balance
        assert updated_penalty.last_payment_date is not None
        assert updated_penalty.next_payment_due_date is not None
        
        # Process final payments to settle
        await penalty_manager.process_penalty_payment(penalty_tracking.id, 780000.0)
        
        # Refresh the record
        final_penalty = await test_db.get(FIRSPenaltyTracking, penalty_tracking.id)
        await test_db.refresh(final_penalty)
        
        assert final_penalty.remaining_balance == 0.0
        assert final_penalty.penalty_status == 'settled'
        assert final_penalty.settlement_date is not None
    
    @pytest.mark.asyncio
    async def test_get_organization_penalties(self, penalty_manager, sample_organization_id, test_db):
        """Test retrieving penalties for an organization."""
        # Create multiple penalty records
        penalty_data_1 = {
            'penalty_type': 'non_compliance',
            'penalty_amount': 1040000.0,
            'violation_date': datetime.utcnow() - timedelta(days=5),
            'days_non_compliant': 5
        }
        
        penalty_data_2 = {
            'penalty_type': 'late_submission',
            'penalty_amount': 500000.0,
            'violation_date': datetime.utcnow() - timedelta(days=10),
            'days_non_compliant': 1
        }
        
        await penalty_manager.track_penalty_status(sample_organization_id, penalty_data_1)
        await penalty_manager.track_penalty_status(sample_organization_id, penalty_data_2)
        
        # Retrieve penalties
        penalties = await penalty_manager.get_organization_penalties(sample_organization_id)
        
        assert len(penalties) == 2
        assert penalties[0].violation_date >= penalties[1].violation_date  # Ordered by date desc
    
    @pytest.mark.asyncio
    async def test_get_penalty_summary(self, penalty_manager, sample_organization_id, test_db):
        """Test penalty summary calculation."""
        # Create penalty records with different statuses
        penalty_data_1 = {
            'penalty_type': 'non_compliance',
            'penalty_amount': 1040000.0,
            'violation_date': datetime.utcnow() - timedelta(days=5),
            'amount_paid': 260000.0
        }
        
        penalty_data_2 = {
            'penalty_type': 'late_submission',
            'penalty_amount': 500000.0,
            'violation_date': datetime.utcnow() - timedelta(days=10),
            'amount_paid': 500000.0  # Fully paid
        }
        
        penalty_1 = await penalty_manager.track_penalty_status(sample_organization_id, penalty_data_1)
        penalty_2 = await penalty_manager.track_penalty_status(sample_organization_id, penalty_data_2)
        
        # Update payment status
        await penalty_manager.process_penalty_payment(penalty_1.id, 260000.0)
        await penalty_manager.process_penalty_payment(penalty_2.id, 500000.0)
        
        # Get summary
        summary = await penalty_manager.get_penalty_summary(sample_organization_id)
        
        assert summary['total_penalties_ngn'] == 1540000.0
        assert summary['total_paid_ngn'] == 760000.0
        assert summary['outstanding_balance_ngn'] == 780000.0
        assert summary['active_penalty_count'] == 1  # Only penalty_1 is still active
        assert summary['settled_penalty_count'] == 1  # penalty_2 is settled


class TestIntegration:
    """Integration tests for Nigerian tax services."""
    
    @pytest.mark.asyncio
    async def test_end_to_end_tax_calculation_and_penalty_tracking(self, test_db):
        """Test end-to-end workflow from tax calculation to penalty tracking."""
        # Setup services
        tax_service = NigerianTaxJurisdictionService(test_db)
        penalty_manager = FIRSPenaltyManager(test_db)
        organization_id = uuid4()
        
        # Step 1: Calculate taxes for business
        locations = [Location(
            state_code='LA',
            state_name='Lagos',
            lga_code='IKEJA',
            lga_name='Ikeja',
            region='South West'
        )]
        
        invoice_amount = 10000000.0
        tax_breakdown = await tax_service.calculate_multi_jurisdiction_tax(locations, invoice_amount)
        
        assert tax_breakdown.total_tax > 0
        
        # Step 2: Simulate non-compliance (late payment)
        violation_date = datetime.utcnow() - timedelta(days=3)
        penalty_calc = await penalty_manager.calculate_non_compliance_penalty(
            organization_id, violation_date
        )
        
        assert penalty_calc.total_penalty == 1020000.0  # ₦1M + 2×₦10K
        
        # Step 3: Setup payment plan
        payment_plan = await penalty_manager.setup_penalty_payment_plan(
            organization_id, penalty_calc.total_penalty
        )
        
        assert len(payment_plan.options) == 4
        
        # Step 4: Track penalty in database
        penalty_data = {
            'penalty_type': 'late_tax_payment',
            'penalty_amount': penalty_calc.total_penalty,
            'violation_date': violation_date,
            'days_non_compliant': penalty_calc.days_non_compliant,
            'payment_plan_type': 'monthly'
        }
        
        penalty_tracking = await penalty_manager.track_penalty_status(
            organization_id, penalty_data
        )
        
        assert penalty_tracking.penalty_amount_ngn == penalty_calc.total_penalty
        
        # Step 5: Process payment
        payment_amount = penalty_calc.total_penalty * 0.25  # 25% payment
        updated_penalty = await penalty_manager.process_penalty_payment(
            penalty_tracking.id, payment_amount
        )
        
        assert updated_penalty.total_amount_paid == payment_amount
        assert updated_penalty.remaining_balance == penalty_calc.total_penalty - payment_amount
        
        # Step 6: Get summary
        summary = await penalty_manager.get_penalty_summary(organization_id)
        
        assert summary['total_penalties_ngn'] == penalty_calc.total_penalty
        assert summary['total_paid_ngn'] == payment_amount
        assert summary['outstanding_balance_ngn'] == penalty_calc.total_penalty - payment_amount


if __name__ == "__main__":
    pytest.main([__file__, "-v"])