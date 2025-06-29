"""
Nigerian Analytics API Routes

Provides endpoints for Nigerian market analytics, compliance metrics,
and business intelligence data.
"""

from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import func, and_, or_

from app.database import get_db
from app.models.nigerian_compliance import (
    NITDAAccreditation,
    NDPRCompliance,
    FIRSPenaltyTracking,
    NigerianBusinessRegistration,
    ISO27001Compliance
)
from app.models.nigerian_business import (
    NigerianConglomerate,
    NigerianSubsidiary,
    NigerianClientAssignment,
    NigerianBusinessInteraction,
    NigerianCulturalPreferences
)
from app.models.organization import Organization
from app.services.nigerian_tax_service import (
    NigerianTaxJurisdictionService,
    FIRSPenaltyManager
)
from app.services.auth_service import get_current_user
from app.models.user import User

router = APIRouter(prefix="/api/dashboard/nigerian-analytics", tags=["Nigerian Analytics"])

@router.get("/")
async def get_nigerian_analytics(
    time_range: str = Query("30d", regex="^(7d|30d|90d|1y)$"),
    state_codes: Optional[str] = Query(None),
    business_sectors: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get comprehensive Nigerian analytics data.
    """
    try:
        # Calculate date range
        days_map = {"7d": 7, "30d": 30, "90d": 90, "1y": 365}
        days = days_map.get(time_range, 30)
        start_date = datetime.utcnow() - timedelta(days=days)
        
        # Parse filters
        state_filter = state_codes.split(',') if state_codes else None
        sector_filter = business_sectors.split(',') if business_sectors else None
        
        # Get compliance data
        compliance_data = await _get_compliance_overview(db, start_date)
        
        # Get state revenue data
        state_revenue = await _get_state_revenue_data(db, start_date, state_filter)
        
        # Get payment method data
        payment_methods = await _get_payment_method_data(db, start_date)
        
        # Get language usage data
        language_usage = await _get_language_usage_data(db, start_date)
        
        # Get device usage data
        device_usage = await _get_device_usage_data(db, start_date)
        
        # Get support channel data
        support_channels = await _get_support_channel_data(db, start_date)
        
        return {
            "success": True,
            "data": {
                **compliance_data,
                "state_revenue": state_revenue,
                "payment_methods": payment_methods,
                "language_usage": language_usage,
                "device_usage": device_usage,
                "support_channels": support_channels,
                "time_range": time_range,
                "generated_at": datetime.utcnow().isoformat()
            }
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch analytics data: {str(e)}")

@router.get("/compliance")
async def get_compliance_metrics(
    time_range: str = Query("30d", regex="^(7d|30d|90d|1y)$"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get detailed compliance metrics for Nigerian regulations.
    """
    try:
        days_map = {"7d": 7, "30d": 30, "90d": 90, "1y": 365}
        days = days_map.get(time_range, 30)
        start_date = datetime.utcnow() - timedelta(days=days)
        
        # NITDA Compliance
        nitda_records = db.query(NITDAAccreditation).filter(
            NITDAAccreditation.created_at >= start_date
        ).all()
        
        nitda_active = sum(1 for record in nitda_records if record.accreditation_status == 'active')
        nitda_compliance = {
            "status": "Active" if nitda_active > 0 else "Inactive",
            "score": (nitda_active / len(nitda_records) * 100) if nitda_records else 0,
            "expiry_date": max([record.expiry_date for record in nitda_records], default=None),
            "last_audit": max([record.last_audit_date for record in nitda_records], default=None)
        }
        
        # NDPR Compliance
        ndpr_records = db.query(NDPRCompliance).filter(
            NDPRCompliance.created_at >= start_date
        ).all()
        
        ndpr_compliant = sum(1 for record in ndpr_records if record.compliance_status == 'compliant')
        ndpr_compliance = {
            "score": (ndpr_compliant / len(ndpr_records) * 100) if ndpr_records else 0,
            "data_categories_compliant": sum(record.data_categories_compliant or 0 for record in ndpr_records),
            "total_data_categories": sum(record.total_data_categories or 0 for record in ndpr_records),
            "last_assessment": max([record.last_assessment_date for record in ndpr_records], default=None)
        }
        
        # ISO 27001 Compliance
        iso_records = db.query(ISO27001Compliance).filter(
            ISO27001Compliance.created_at >= start_date
        ).all()
        
        iso_certified = sum(1 for record in iso_records if record.certification_status == 'certified')
        iso_compliance = {
            "status": "Certified" if iso_certified > 0 else "Not Certified",
            "certification_date": max([record.certification_date for record in iso_records], default=None),
            "next_audit": min([record.next_audit_date for record in iso_records], default=None),
            "non_conformities": sum(record.non_conformities_count or 0 for record in iso_records)
        }
        
        # FIRS Penalties
        penalty_records = db.query(FIRSPenaltyTracking).filter(
            FIRSPenaltyTracking.created_at >= start_date
        ).all()
        
        firs_penalties = {
            "total_amount": sum(float(record.penalty_amount_ngn or 0) for record in penalty_records),
            "active_penalties": sum(1 for record in penalty_records if record.penalty_status == 'active'),
            "resolved_penalties": sum(1 for record in penalty_records if record.penalty_status == 'settled'),
            "payment_plans_active": sum(1 for record in penalty_records if record.payment_plan_selected)
        }
        
        return {
            "success": True,
            "data": {
                "nitda_compliance": nitda_compliance,
                "ndpr_compliance": ndpr_compliance,
                "iso_compliance": iso_compliance,
                "firs_penalties": firs_penalties,
                "time_range": time_range,
                "generated_at": datetime.utcnow().isoformat()
            }
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch compliance metrics: {str(e)}")

@router.get("/regional")
async def get_regional_metrics(
    time_range: str = Query("30d", regex="^(7d|30d|90d|1y)$"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get regional performance metrics across Nigerian states and LGAs.
    """
    try:
        days_map = {"7d": 7, "30d": 30, "90d": 90, "1y": 365}
        days = days_map.get(time_range, 30)
        start_date = datetime.utcnow() - timedelta(days=days)
        
        # Get state performance
        state_performance = db.query(
            NigerianSubsidiary.operating_state,
            func.count(NigerianSubsidiary.id).label('businesses'),
            func.sum(NigerianSubsidiary.annual_revenue_ngn).label('revenue'),
            func.avg(NigerianSubsidiary.annual_revenue_ngn).label('avg_revenue')
        ).filter(
            NigerianSubsidiary.created_at >= start_date
        ).group_by(
            NigerianSubsidiary.operating_state
        ).all()
        
        # Get business registration data for compliance rates
        business_registrations = db.query(NigerianBusinessRegistration).filter(
            NigerianBusinessRegistration.created_at >= start_date
        ).all()
        
        # Calculate compliance rates by state
        state_compliance = {}
        for reg in business_registrations:
            state = reg.state
            if state not in state_compliance:
                state_compliance[state] = {'total': 0, 'compliant': 0}
            state_compliance[state]['total'] += 1
            if reg.compliance_status == 'compliant':
                state_compliance[state]['compliant'] += 1
        
        # Format state performance data
        state_data = []
        for state_perf in state_performance:
            state = state_perf.operating_state
            compliance_data = state_compliance.get(state, {'total': 1, 'compliant': 0})
            compliance_rate = (compliance_data['compliant'] / compliance_data['total']) * 100
            
            state_data.append({
                "state": state,
                "state_code": _get_state_code(state),
                "region": _get_region(state),
                "businesses": state_perf.businesses,
                "revenue": float(state_perf.revenue or 0),
                "growth_rate": _calculate_growth_rate(state, start_date, db),
                "compliance_rate": compliance_rate,
                "top_industries": _get_top_industries_by_state(state, db)
            })
        
        # Get LGA performance (simplified)
        lga_performance = db.query(
            NigerianSubsidiary.local_government_area,
            NigerianSubsidiary.operating_state,
            func.count(NigerianSubsidiary.id).label('businesses'),
            func.sum(NigerianSubsidiary.annual_revenue_ngn).label('revenue')
        ).filter(
            NigerianSubsidiary.created_at >= start_date
        ).group_by(
            NigerianSubsidiary.local_government_area,
            NigerianSubsidiary.operating_state
        ).all()
        
        lga_data = []
        for lga_perf in lga_performance:
            lga_data.append({
                "lga": lga_perf.local_government_area,
                "state": lga_perf.operating_state,
                "businesses": lga_perf.businesses,
                "revenue": float(lga_perf.revenue or 0),
                "compliance_rate": 85.0  # Mock data - would be calculated from actual compliance records
            })
        
        # Regional summary
        regions = {}
        for state in state_data:
            region = state['region']
            if region not in regions:
                regions[region] = {'businesses': 0, 'revenue': 0, 'compliance_rates': []}
            regions[region]['businesses'] += state['businesses']
            regions[region]['revenue'] += state['revenue']
            regions[region]['compliance_rates'].append(state['compliance_rate'])
        
        regional_summary = []
        for region, data in regions.items():
            avg_compliance = sum(data['compliance_rates']) / len(data['compliance_rates']) if data['compliance_rates'] else 0
            regional_summary.append({
                "region": region,
                "total_businesses": data['businesses'],
                "total_revenue": data['revenue'],
                "average_compliance_rate": avg_compliance
            })
        
        return {
            "success": True,
            "data": {
                "state_performance": state_data,
                "lga_performance": lga_data,
                "regional_summary": regional_summary,
                "time_range": time_range,
                "generated_at": datetime.utcnow().isoformat()
            }
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch regional metrics: {str(e)}")

@router.get("/cultural")
async def get_cultural_metrics(
    time_range: str = Query("30d", regex="^(7d|30d|90d|1y)$"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get cultural adoption and engagement metrics.
    """
    try:
        days_map = {"7d": 7, "30d": 30, "90d": 90, "1y": 365}
        days = days_map.get(time_range, 30)
        start_date = datetime.utcnow() - timedelta(days=days)
        
        # Language preferences
        cultural_prefs = db.query(NigerianCulturalPreferences).filter(
            NigerianCulturalPreferences.created_at >= start_date
        ).all()
        
        language_counts = {}
        for pref in cultural_prefs:
            lang = pref.primary_language.value if pref.primary_language else 'english'
            language_counts[lang] = language_counts.get(lang, 0) + 1
        
        total_users = len(cultural_prefs)
        language_preferences = []
        for lang, count in language_counts.items():
            language_preferences.append({
                "language": lang.title(),
                "users": count,
                "percentage": (count / total_users * 100) if total_users > 0 else 0,
                "engagement_rate": 85.0,  # Mock data
                "satisfaction_score": 4.5   # Mock data
            })
        
        # Communication channels
        interactions = db.query(NigerianBusinessInteraction).filter(
            NigerianBusinessInteraction.interaction_date >= start_date
        ).all()
        
        channel_usage = {}
        for interaction in interactions:
            channel = interaction.interaction_type or 'email'
            if channel not in channel_usage:
                channel_usage[channel] = {'count': 0, 'total_satisfaction': 0, 'response_times': []}
            channel_usage[channel]['count'] += 1
            # Mock satisfaction and response time data
            channel_usage[channel]['total_satisfaction'] += 4.2
            channel_usage[channel]['response_times'].append(120)  # 2 hours
        
        communication_channels = []
        for channel, data in channel_usage.items():
            avg_satisfaction = data['total_satisfaction'] / data['count'] if data['count'] > 0 else 0
            avg_response_time = sum(data['response_times']) / len(data['response_times']) if data['response_times'] else 0
            
            communication_channels.append({
                "channel": channel.replace('_', ' ').title(),
                "usage_count": data['count'],
                "satisfaction_rate": avg_satisfaction,
                "response_time": avg_response_time
            })
        
        # Cultural features adoption
        cultural_features = [
            {
                "feature": "Greeting Style Preferences",
                "adoption_rate": 78.5,
                "satisfaction": 4.3,
                "frequency": "Daily"
            },
            {
                "feature": "Hierarchy Acknowledgment",
                "adoption_rate": 92.1,
                "satisfaction": 4.7,
                "frequency": "Always"
            },
            {
                "feature": "Relationship Building Time",
                "adoption_rate": 85.3,
                "satisfaction": 4.4,
                "frequency": "Weekly"
            },
            {
                "feature": "WhatsApp Business Integration",
                "adoption_rate": 95.2,
                "satisfaction": 4.8,
                "frequency": "Daily"
            }
        ]
        
        # Relationship management
        assignments = db.query(NigerianClientAssignment).filter(
            NigerianClientAssignment.created_at >= start_date
        ).all()
        
        total_assignments = len(assignments)
        avg_satisfaction = sum(assignment.relationship_score for assignment in assignments) / total_assignments if total_assignments > 0 else 0
        
        relationship_management = {
            "total_assignments": total_assignments,
            "average_satisfaction": avg_satisfaction,
            "cultural_alignment_score": 4.5  # Mock data
        }
        
        return {
            "success": True,
            "data": {
                "language_preferences": language_preferences,
                "communication_channels": communication_channels,
                "cultural_features": cultural_features,
                "relationship_management": relationship_management,
                "time_range": time_range,
                "generated_at": datetime.utcnow().isoformat()
            }
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch cultural metrics: {str(e)}")

@router.get("/penalties")
async def get_penalty_details(
    organization_id: Optional[str] = Query(None),
    time_range: str = Query("30d", regex="^(7d|30d|90d|1y)$"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get detailed FIRS penalty information.
    """
    try:
        penalty_manager = FIRSPenaltyManager(db)
        
        if organization_id:
            # Get penalties for specific organization
            penalties = await penalty_manager.get_organization_penalties(organization_id)
            summary = await penalty_manager.get_penalty_summary(organization_id)
        else:
            # Get all penalties
            days_map = {"7d": 7, "30d": 30, "90d": 90, "1y": 365}
            days = days_map.get(time_range, 30)
            start_date = datetime.utcnow() - timedelta(days=days)
            
            penalties = db.query(FIRSPenaltyTracking).filter(
                FIRSPenaltyTracking.created_at >= start_date
            ).all()
            
            total_penalties = sum(float(p.penalty_amount_ngn or 0) for p in penalties)
            total_paid = sum(float(p.total_amount_paid or 0) for p in penalties)
            active_count = sum(1 for p in penalties if p.penalty_status == 'active')
            
            summary = {
                "total_penalties": total_penalties,
                "total_paid": total_paid,
                "outstanding_balance": total_penalties - total_paid,
                "active_count": active_count
            }
        
        penalty_data = []
        for penalty in penalties:
            penalty_data.append({
                "id": str(penalty.id),
                "organization_id": str(penalty.organization_id),
                "penalty_type": penalty.penalty_type,
                "amount": float(penalty.penalty_amount_ngn or 0),
                "violation_date": penalty.violation_date.isoformat() if penalty.violation_date else None,
                "status": penalty.penalty_status,
                "payment_plan": penalty.payment_plan_selected,
                "remaining_balance": float(penalty.remaining_balance or 0),
                "next_payment_date": penalty.next_payment_due_date.isoformat() if penalty.next_payment_due_date else None
            })
        
        return {
            "success": True,
            "data": {
                "penalties": penalty_data,
                "summary": summary,
                "time_range": time_range,
                "generated_at": datetime.utcnow().isoformat()
            }
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch penalty details: {str(e)}")

# Helper functions
async def _get_compliance_overview(db: Session, start_date: datetime) -> Dict[str, Any]:
    """Get compliance overview data."""
    # NITDA status
    nitda_records = db.query(NITDAAccreditation).filter(
        NITDAAccreditation.created_at >= start_date
    ).all()
    
    nitda_active = any(record.accreditation_status == 'active' for record in nitda_records)
    nitda_expiry = max([record.expiry_date for record in nitda_records], default=None)
    
    # NDPR compliance
    ndpr_records = db.query(NDPRCompliance).filter(
        NDPRCompliance.created_at >= start_date
    ).all()
    
    ndpr_compliant = sum(1 for record in ndpr_records if record.compliance_status == 'compliant')
    ndpr_score = (ndpr_compliant / len(ndpr_records) * 100) if ndpr_records else 95.0
    
    # ISO status
    iso_records = db.query(ISO27001Compliance).filter(
        ISO27001Compliance.created_at >= start_date
    ).all()
    
    iso_certified = any(record.certification_status == 'certified' for record in iso_records)
    iso_next_audit = min([record.next_audit_date for record in iso_records], default=None)
    
    # FIRS penalties
    penalty_records = db.query(FIRSPenaltyTracking).filter(
        FIRSPenaltyTracking.created_at >= start_date
    ).all()
    
    total_penalties = sum(float(record.penalty_amount_ngn or 0) for record in penalty_records)
    
    return {
        "nitda_status": "Active" if nitda_active else "Inactive",
        "nitda_expiry": nitda_expiry.isoformat() if nitda_expiry else None,
        "ndpr_compliance_score": ndpr_score,
        "iso_status": "Certified" if iso_certified else "Not Certified",
        "next_audit_date": iso_next_audit.isoformat() if iso_next_audit else None,
        "total_penalties": total_penalties
    }

async def _get_state_revenue_data(db: Session, start_date: datetime, state_filter: Optional[List[str]]) -> List[Dict[str, Any]]:
    """Get revenue data by Nigerian state."""
    query = db.query(
        NigerianSubsidiary.operating_state,
        func.sum(NigerianSubsidiary.annual_revenue_ngn).label('revenue'),
        func.count(NigerianSubsidiary.id).label('businesses')
    ).filter(
        NigerianSubsidiary.created_at >= start_date
    )
    
    if state_filter:
        query = query.filter(NigerianSubsidiary.operating_state.in_(state_filter))
    
    results = query.group_by(NigerianSubsidiary.operating_state).all()
    
    state_data = []
    for result in results:
        state_data.append({
            "state": result.operating_state,
            "revenue": float(result.revenue or 0),
            "growth": 12.5  # Mock growth rate
        })
    
    return state_data

async def _get_payment_method_data(db: Session, start_date: datetime) -> List[Dict[str, Any]]:
    """Get payment method distribution data."""
    # Mock payment method data - in real implementation, this would come from transaction records
    return [
        {"method": "Bank Transfer", "volume": 45, "value": 12000000000},
        {"method": "USSD", "volume": 30, "value": 3500000000},
        {"method": "Card Payment", "volume": 15, "value": 2800000000},
        {"method": "Mobile Money", "volume": 8, "value": 1200000000},
        {"method": "Cash", "volume": 2, "value": 500000000}
    ]

async def _get_language_usage_data(db: Session, start_date: datetime) -> List[Dict[str, Any]]:
    """Get language usage statistics."""
    cultural_prefs = db.query(NigerianCulturalPreferences).filter(
        NigerianCulturalPreferences.created_at >= start_date
    ).all()
    
    language_counts = {}
    for pref in cultural_prefs:
        lang = pref.primary_language.value if pref.primary_language else 'english'
        language_counts[lang] = language_counts.get(lang, 0) + 1
    
    total_users = len(cultural_prefs) or 1
    language_data = []
    for lang, count in language_counts.items():
        language_data.append({
            "language": lang.title(),
            "users": count,
            "percentage": (count / total_users * 100)
        })
    
    # Add mock data if no records exist
    if not language_data:
        language_data = [
            {"language": "English", "users": 12500, "percentage": 62},
            {"language": "Hausa", "users": 4200, "percentage": 21},
            {"language": "Yoruba", "users": 2800, "percentage": 14},
            {"language": "Igbo", "users": 600, "percentage": 3}
        ]
    
    return language_data

async def _get_device_usage_data(db: Session, start_date: datetime) -> List[Dict[str, Any]]:
    """Get device usage statistics."""
    # Mock device usage data
    return [
        {"device": "Mobile", "users": 14800, "sessions": 45200},
        {"device": "Desktop", "users": 4200, "sessions": 8900},
        {"device": "Tablet", "users": 1000, "sessions": 1800}
    ]

async def _get_support_channel_data(db: Session, start_date: datetime) -> List[Dict[str, Any]]:
    """Get support channel performance data."""
    # Mock support channel data
    return [
        {"channel": "WhatsApp Business", "tickets": 1250, "satisfaction": 4.8},
        {"channel": "Phone Support", "tickets": 890, "satisfaction": 4.5},
        {"channel": "Email", "tickets": 560, "satisfaction": 4.2},
        {"channel": "In-App Chat", "tickets": 340, "satisfaction": 4.0}
    ]

def _get_state_code(state_name: str) -> str:
    """Get state code from state name."""
    state_codes = {
        'Lagos': 'LA',
        'Kano': 'KN',
        'Rivers': 'RV',
        'Ogun': 'OG',
        'Federal Capital Territory': 'FC',
        'Kaduna': 'KD'
    }
    return state_codes.get(state_name, state_name[:2].upper())

def _get_region(state_name: str) -> str:
    """Get region from state name."""
    regions = {
        'Lagos': 'South West',
        'Ogun': 'South West',
        'Kano': 'North West',
        'Kaduna': 'North West',
        'Rivers': 'South South',
        'Federal Capital Territory': 'North Central'
    }
    return regions.get(state_name, 'Unknown')

def _calculate_growth_rate(state: str, start_date: datetime, db: Session) -> float:
    """Calculate growth rate for a state (mock implementation)."""
    # Mock growth rates
    growth_rates = {
        'Lagos': 12.5,
        'Rivers': 8.3,
        'Kano': 15.2,
        'Ogun': 9.7,
        'Federal Capital Territory': 11.8,
        'Kaduna': 7.2
    }
    return growth_rates.get(state, 10.0)

def _get_top_industries_by_state(state: str, db: Session) -> List[str]:
    """Get top industries by state (mock implementation)."""
    industries = {
        'Lagos': ['Financial Services', 'Technology', 'Manufacturing'],
        'Rivers': ['Oil & Gas', 'Maritime', 'Manufacturing'],
        'Kano': ['Agriculture', 'Textiles', 'Trading'],
        'Ogun': ['Manufacturing', 'Agriculture', 'Cement'],
        'Federal Capital Territory': ['Government', 'Services', 'Technology'],
        'Kaduna': ['Agriculture', 'Textiles', 'Manufacturing']
    }
    return industries.get(state, ['Services', 'Trading', 'Agriculture'])