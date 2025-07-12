"""
Nigerian Conglomerate Service

This service manages Nigerian business conglomerates, hierarchical approvals,
and relationship management for Nigerian business culture.
"""

from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from uuid import UUID
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func

from app.models.nigerian_business import (
    NigerianConglomerate,
    NigerianSubsidiary,
    NigerianApprovalLevel,
    NigerianApprovalRequest,
    NigerianRelationshipManager,
    NigerianClientAssignment,
    NigerianCulturalPreferences,
    NigerianBusinessInteraction,
    ApprovalStatus,
    TaxConsolidationType,
    LanguagePreference,
    GreetingStyle,
    CommunicationPace
)
from app.models.organization import Organization
from app.models.user import User


class ApprovalMatrix:
    """Class to represent approval matrix structure"""
    def __init__(self):
        self.levels: List[Dict[str, Any]] = []
        self.total_levels = 0


class TaxCalculation:
    """Class to represent tax calculation breakdown"""
    def __init__(self):
        self.federal_taxes: List[Dict[str, Any]] = []
        self.state_taxes: List[Dict[str, Any]] = []
        self.local_taxes: List[Dict[str, Any]] = []
        self.total_tax = 0.0


class NigerianConglomerateService:
    """Service for managing Nigerian business conglomerates."""
    
    def __init__(self, db: Session):
        self.db = db
    
    async def create_conglomerate(self, 
                                parent_organization_id: UUID,
                                conglomerate_data: Dict[str, Any]) -> NigerianConglomerate:
        """Create a new Nigerian conglomerate."""
        
        conglomerate = NigerianConglomerate(
            parent_organization_id=parent_organization_id,
            conglomerate_name=conglomerate_data.get("conglomerate_name"),
            cac_group_registration=conglomerate_data.get("cac_group_registration"),
            tax_consolidation_type=TaxConsolidationType(
                conglomerate_data.get("tax_consolidation_type", "separate")
            ),
            primary_business_sector=conglomerate_data.get("primary_business_sector"),
            total_employees=conglomerate_data.get("total_employees"),
            consolidated_revenue_ngn=conglomerate_data.get("consolidated_revenue_ngn"),
            board_structure=conglomerate_data.get("board_structure"),
            governance_model=conglomerate_data.get("governance_model", "traditional")
        )
        
        self.db.add(conglomerate)
        await self.db.commit()
        await self.db.refresh(conglomerate)
        
        # Setup default approval hierarchy
        await self.setup_hierarchical_approvals(conglomerate.id)
        
        return conglomerate
    
    async def setup_hierarchical_approvals(self, conglomerate_id: UUID) -> ApprovalMatrix:
        """Setup approval hierarchy respecting Nigerian corporate culture."""
        
        # Get the conglomerate
        conglomerate = await self.db.get(NigerianConglomerate, conglomerate_id)
        if not conglomerate:
            raise ValueError("Conglomerate not found")
        
        # Traditional Nigerian hierarchy levels with amounts in Naira
        approval_levels = [
            {
                "level_name": "Junior Staff",
                "level_order": 1,
                "amount_limit_ngn": 100000,  # ₦100K
                "requires_superior_approval": True,
                "requires_board_approval": False,
                "requires_board_ratification": False,
                "conditions": {
                    "requires_documentation": True,
                    "requires_receipt": True,
                    "max_frequency": "weekly"
                }
            },
            {
                "level_name": "Middle Management",
                "level_order": 2,
                "amount_limit_ngn": 1000000,  # ₦1M
                "requires_superior_approval": True,
                "requires_board_approval": False,
                "requires_board_ratification": False,
                "conditions": {
                    "requires_documentation": True,
                    "requires_justification": True,
                    "requires_budget_allocation": True
                }
            },
            {
                "level_name": "Senior Management",
                "level_order": 3,
                "amount_limit_ngn": 10000000,  # ₦10M
                "requires_superior_approval": True,
                "requires_board_approval": True,
                "requires_board_ratification": False,
                "conditions": {
                    "requires_detailed_proposal": True,
                    "requires_financial_impact_analysis": True,
                    "requires_risk_assessment": True
                }
            },
            {
                "level_name": "Executive Directors",
                "level_order": 4,
                "amount_limit_ngn": 100000000,  # ₦100M
                "requires_superior_approval": False,
                "requires_board_approval": True,
                "requires_board_ratification": True,
                "conditions": {
                    "requires_board_meeting": True,
                    "requires_unanimous_consent": True,
                    "requires_external_audit": True
                }
            }
        ]
        
        approval_matrix = ApprovalMatrix()
        
        for level_data in approval_levels:
            approval_level = NigerianApprovalLevel(
                organization_id=conglomerate.parent_organization_id,
                **level_data
            )
            self.db.add(approval_level)
            approval_matrix.levels.append(level_data)
        
        await self.db.commit()
        approval_matrix.total_levels = len(approval_levels)
        
        return approval_matrix
    
    async def create_approval_request(self,
                                    organization_id: UUID,
                                    request_data: Dict[str, Any]) -> NigerianApprovalRequest:
        """Create a new approval request based on amount and type."""
        
        amount = request_data.get("amount_ngn", 0)
        
        # Find appropriate approval level based on amount
        approval_level = await self.db.query(NigerianApprovalLevel).filter(
            and_(
                NigerianApprovalLevel.organization_id == organization_id,
                NigerianApprovalLevel.amount_limit_ngn >= amount,
                NigerianApprovalLevel.is_active == True
            )
        ).order_by(NigerianApprovalLevel.level_order).first()
        
        if not approval_level:
            # Amount exceeds all approval levels, require board approval
            approval_level = await self.db.query(NigerianApprovalLevel).filter(
                and_(
                    NigerianApprovalLevel.organization_id == organization_id,
                    NigerianApprovalLevel.requires_board_approval == True,
                    NigerianApprovalLevel.is_active == True
                )
            ).order_by(NigerianApprovalLevel.level_order.desc()).first()
        
        if not approval_level:
            raise ValueError("No appropriate approval level found")
        
        approval_request = NigerianApprovalRequest(
            organization_id=organization_id,
            approval_level_id=approval_level.id,
            request_type=request_data.get("request_type"),
            request_reference=request_data.get("request_reference"),
            amount_ngn=amount,
            description=request_data.get("description"),
            requester_user_id=request_data.get("requester_user_id"),
            request_data=request_data.get("additional_data")
        )
        
        self.db.add(approval_request)
        await self.db.commit()
        await self.db.refresh(approval_request)
        
        return approval_request
    
    async def process_approval(self,
                             approval_request_id: UUID,
                             approver_user_id: UUID,
                             action: str,
                             reason: Optional[str] = None) -> NigerianApprovalRequest:
        """Process an approval request (approve/reject/escalate)."""
        
        approval_request = await self.db.get(NigerianApprovalRequest, approval_request_id)
        if not approval_request:
            raise ValueError("Approval request not found")
        
        if action == "approve":
            approval_request.status = ApprovalStatus.APPROVED
            approval_request.approver_user_id = approver_user_id
            approval_request.approved_at = datetime.utcnow()
        elif action == "reject":
            approval_request.status = ApprovalStatus.REJECTED
            approval_request.approver_user_id = approver_user_id
            approval_request.rejection_reason = reason
        elif action == "escalate":
            approval_request.status = ApprovalStatus.ESCALATED
            approval_request.escalation_level += 1
            approval_request.escalated_at = datetime.utcnow()
            approval_request.escalation_reason = reason
        
        await self.db.commit()
        await self.db.refresh(approval_request)
        
        return approval_request
    
    async def manage_multi_jurisdiction_tax(self, subsidiary_id: UUID) -> TaxCalculation:
        """Calculate taxes across Nigerian jurisdictions."""
        
        subsidiary = await self.db.get(NigerianSubsidiary, subsidiary_id)
        if not subsidiary:
            raise ValueError("Subsidiary not found")
        
        tax_calculation = TaxCalculation()
        
        # Get annual revenue for calculation
        annual_revenue = float(subsidiary.annual_revenue_ngn or 0)
        
        if annual_revenue == 0:
            return tax_calculation
        
        # Federal taxes (FIRS)
        federal_vat_rate = 0.075  # 7.5% VAT
        federal_vat = annual_revenue * federal_vat_rate
        
        tax_calculation.federal_taxes.append({
            'type': 'VAT',
            'rate': federal_vat_rate,
            'amount': federal_vat,
            'authority': 'FIRS',
            'jurisdiction': 'Federal'
        })
        
        # Company Income Tax (CIT) - 30% for large companies
        if annual_revenue > 25000000:  # ₦25M threshold
            cit_rate = 0.30
        else:
            cit_rate = 0.20  # Small companies
        
        cit_amount = annual_revenue * cit_rate
        tax_calculation.federal_taxes.append({
            'type': 'Company Income Tax',
            'rate': cit_rate,
            'amount': cit_amount,
            'authority': 'FIRS',
            'jurisdiction': 'Federal'
        })
        
        # State taxes based on operating state
        state_tax_rates = {
            'Lagos': 0.015,  # 1.5%
            'Rivers': 0.012,  # 1.2%
            'Kano': 0.010,   # 1.0%
            'Ogun': 0.011,   # 1.1%
            'Abuja': 0.013,  # 1.3%
        }
        
        state_name = subsidiary.operating_state
        if state_name in state_tax_rates:
            state_tax_rate = state_tax_rates[state_name]
            state_tax = annual_revenue * state_tax_rate
            
            tax_calculation.state_taxes.append({
                'type': 'State Revenue Tax',
                'rate': state_tax_rate,
                'amount': state_tax,
                'authority': f"{state_name} State Internal Revenue Service",
                'jurisdiction': 'State'
            })
        
        # Local Government taxes (typically 0.5% of revenue)
        lga_tax_rate = 0.005
        lga_tax = annual_revenue * lga_tax_rate
        
        tax_calculation.local_taxes.append({
            'type': 'Local Government Service Tax',
            'rate': lga_tax_rate,
            'amount': lga_tax,
            'authority': f"{subsidiary.local_government_area} Local Government",
            'jurisdiction': 'Local'
        })
        
        # Calculate total tax
        tax_calculation.total_tax = (
            sum(tax['amount'] for tax in tax_calculation.federal_taxes) +
            sum(tax['amount'] for tax in tax_calculation.state_taxes) +
            sum(tax['amount'] for tax in tax_calculation.local_taxes)
        )
        
        return tax_calculation
    
    async def assign_relationship_manager(self,
                                        organization_id: UUID,
                                        manager_preferences: Dict[str, Any]) -> NigerianClientAssignment:
        """Assign a relationship manager to a Nigerian client."""
        
        # Find available relationship managers based on preferences
        query = self.db.query(NigerianRelationshipManager).filter(
            NigerianRelationshipManager.is_active == True,
            NigerianRelationshipManager.current_client_count < NigerianRelationshipManager.client_capacity
        )
        
        # Filter by language preference if specified
        if manager_preferences.get("language_preference"):
            query = query.filter(
                NigerianRelationshipManager.local_language_preference == 
                LanguagePreference(manager_preferences["language_preference"])
            )
        
        # Filter by industry specialization if specified
        if manager_preferences.get("industry"):
            query = query.filter(
                NigerianRelationshipManager.industry_specialization.contains(
                    [manager_preferences["industry"]]
                )
            )
        
        # Get manager with lowest client count
        relationship_manager = query.order_by(
            NigerianRelationshipManager.current_client_count
        ).first()
        
        if not relationship_manager:
            raise ValueError("No available relationship managers found")
        
        # Create assignment
        assignment = NigerianClientAssignment(
            organization_id=organization_id,
            relationship_manager_id=relationship_manager.id,
            assignment_reason=manager_preferences.get("assignment_reason", "Auto-assigned based on availability"),
            cultural_preferences=manager_preferences.get("cultural_preferences"),
            communication_preferences=manager_preferences.get("communication_preferences"),
            meeting_preferences=manager_preferences.get("meeting_preferences")
        )
        
        self.db.add(assignment)
        
        # Update manager's client count
        relationship_manager.current_client_count += 1
        
        await self.db.commit()
        await self.db.refresh(assignment)
        
        return assignment
    
    async def setup_cultural_preferences(self,
                                       organization_id: UUID,
                                       preferences: Dict[str, Any]) -> NigerianCulturalPreferences:
        """Setup cultural preferences for a Nigerian organization."""
        
        # Check if preferences already exist
        existing_prefs = await self.db.query(NigerianCulturalPreferences).filter(
            NigerianCulturalPreferences.organization_id == organization_id
        ).first()
        
        if existing_prefs:
            # Update existing preferences
            for key, value in preferences.items():
                if hasattr(existing_prefs, key):
                    setattr(existing_prefs, key, value)
            
            await self.db.commit()
            await self.db.refresh(existing_prefs)
            return existing_prefs
        
        # Create new preferences
        cultural_prefs = NigerianCulturalPreferences(
            organization_id=organization_id,
            greeting_style=GreetingStyle(preferences.get("greeting_style", "formal")),
            communication_pace=CommunicationPace(preferences.get("communication_pace", "relationship_first")),
            relationship_building_time=preferences.get("relationship_building_time", 15),
            hierarchy_acknowledgment=preferences.get("hierarchy_acknowledgment", True),
            gift_exchange_customs=preferences.get("gift_exchange_customs", False),
            whatsapp_business_api=preferences.get("whatsapp_business_api", True),
            voice_calls=preferences.get("voice_calls", True),
            video_calls=preferences.get("video_calls", False),
            in_person_meetings=preferences.get("in_person_meetings", True),
            traditional_email=preferences.get("traditional_email", True),
            primary_language=LanguagePreference(preferences.get("primary_language", "english")),
            secondary_languages=preferences.get("secondary_languages"),
            respect_titles=preferences.get("respect_titles", True),
            age_respectful_language=preferences.get("age_respectful_language", True),
            gender_appropriate_language=preferences.get("gender_appropriate_language", True)
        )
        
        self.db.add(cultural_prefs)
        await self.db.commit()
        await self.db.refresh(cultural_prefs)
        
        return cultural_prefs
    
    async def log_business_interaction(self,
                                     organization_id: UUID,
                                     interaction_data: Dict[str, Any]) -> NigerianBusinessInteraction:
        """Log a business interaction for Nigerian cultural tracking."""
        
        interaction = NigerianBusinessInteraction(
            organization_id=organization_id,
            relationship_manager_id=interaction_data.get("relationship_manager_id"),
            interaction_type=interaction_data.get("interaction_type"),
            interaction_subject=interaction_data.get("interaction_subject"),
            interaction_notes=interaction_data.get("interaction_notes"),
            participants=interaction_data.get("participants"),
            relationship_building_time=interaction_data.get("relationship_building_time"),
            business_discussion_time=interaction_data.get("business_discussion_time"),
            cultural_elements_observed=interaction_data.get("cultural_elements_observed"),
            interaction_outcome=interaction_data.get("interaction_outcome"),
            follow_up_required=interaction_data.get("follow_up_required", False),
            follow_up_date=interaction_data.get("follow_up_date"),
            interaction_date=interaction_data.get("interaction_date", datetime.utcnow()),
            duration_minutes=interaction_data.get("duration_minutes")
        )
        
        self.db.add(interaction)
        await self.db.commit()
        await self.db.refresh(interaction)
        
        # Update relationship score based on interaction outcome
        if interaction.relationship_manager_id:
            await self.update_relationship_score(
                organization_id, 
                interaction.relationship_manager_id,
                interaction.interaction_outcome
            )
        
        return interaction
    
    async def update_relationship_score(self,
                                      organization_id: UUID,
                                      relationship_manager_id: UUID,
                                      interaction_outcome: str):
        """Update relationship score based on interaction outcome."""
        
        assignment = await self.db.query(NigerianClientAssignment).filter(
            and_(
                NigerianClientAssignment.organization_id == organization_id,
                NigerianClientAssignment.relationship_manager_id == relationship_manager_id,
                NigerianClientAssignment.is_active == True
            )
        ).first()
        
        if assignment:
            # Update score based on outcome
            score_changes = {
                "positive": 0.5,
                "neutral": 0.0,
                "negative": -0.3
            }
            
            score_change = score_changes.get(interaction_outcome, 0.0)
            assignment.relationship_score = max(0.0, min(10.0, assignment.relationship_score + score_change))
            assignment.last_interaction_date = datetime.utcnow()
            
            await self.db.commit()
    
    async def get_conglomerate_dashboard_data(self, conglomerate_id: UUID) -> Dict[str, Any]:
        """Get dashboard data for a Nigerian conglomerate."""
        
        conglomerate = await self.db.get(NigerianConglomerate, conglomerate_id)
        if not conglomerate:
            raise ValueError("Conglomerate not found")
        
        # Get subsidiaries
        subsidiaries = await self.db.query(NigerianSubsidiary).filter(
            NigerianSubsidiary.conglomerate_id == conglomerate_id
        ).all()
        
        # Get pending approvals
        pending_approvals = await self.db.query(NigerianApprovalRequest).filter(
            and_(
                NigerianApprovalRequest.organization_id == conglomerate.parent_organization_id,
                NigerianApprovalRequest.status == ApprovalStatus.PENDING
            )
        ).count()
        
        # Calculate total revenue
        total_revenue = sum(float(sub.annual_revenue_ngn or 0) for sub in subsidiaries)
        
        # Get relationship manager assignments
        assignments = await self.db.query(NigerianClientAssignment).filter(
            NigerianClientAssignment.organization_id == conglomerate.parent_organization_id
        ).all()
        
        return {
            "conglomerate": {
                "id": conglomerate.id,
                "name": conglomerate.conglomerate_name,
                "total_subsidiaries": len(subsidiaries),
                "total_revenue_ngn": total_revenue,
                "primary_sector": conglomerate.primary_business_sector,
                "tax_consolidation_type": conglomerate.tax_consolidation_type.value
            },
            "subsidiaries": [
                {
                    "id": sub.id,
                    "name": sub.subsidiary_name,
                    "state": sub.operating_state,
                    "revenue_ngn": float(sub.annual_revenue_ngn or 0),
                    "employees": sub.employee_count
                }
                for sub in subsidiaries
            ],
            "pending_approvals": pending_approvals,
            "relationship_managers": [
                {
                    "manager_id": assignment.relationship_manager_id,
                    "relationship_score": assignment.relationship_score,
                    "last_interaction": assignment.last_interaction_date
                }
                for assignment in assignments
            ]
        }