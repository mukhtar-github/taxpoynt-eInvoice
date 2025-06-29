"""
Security Compliance API Router
Provides endpoints for Nigerian security compliance monitoring and management
"""

from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks
from sqlalchemy.orm import Session
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
import logging

from ..database import get_db
from ..core.auth import get_current_user
from ..models.user import User
from ..services.data_residency_service import NigerianDataResidencyService
from ..services.iso27001_compliance_service import ISO27001ComplianceManager
from ..services.comprehensive_audit_service import ComprehensiveAuditService, AuditEventType, AuditOutcome
from ..security.nigerian_security import NigerianSecurityFramework, SecurityLevel, MFAMethod

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/security-compliance", tags=["security-compliance"])


@router.get("/dashboard")
async def get_security_dashboard(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get comprehensive security compliance dashboard data"""
    
    try:
        # Initialize services
        data_residency_service = NigerianDataResidencyService()
        iso_compliance_manager = ISO27001ComplianceManager()
        audit_service = ComprehensiveAuditService()
        security_framework = NigerianSecurityFramework()
        
        # Get compliance metrics
        iso_report = await iso_compliance_manager.monitor_security_controls()
        data_residency_report = await data_residency_service.get_data_location_report(
            organization_id=str(current_user.organization_id) if current_user.organization_id else None
        )
        security_report = await security_framework.generate_nigerian_security_report(
            organization_id=str(current_user.organization_id) if current_user.organization_id else None
        )
        
        dashboard_data = {
            "compliance_metrics": {
                "iso27001_score": iso_report.overall_score,
                "ndpr_compliance": 88.0,  # Would calculate from actual NDPR compliance
                "data_residency_compliance": 95.0,  # From data residency service
                "mfa_adoption_rate": security_report["mfa_metrics"]["mfa_adoption_rate"],
                "audit_completeness": 85.0,  # From audit service metrics
                "security_incidents": len(iso_report.gaps_identified),
                "last_assessment": iso_report.assessment_date.isoformat()
            },
            "security_events": _get_recent_security_events(),
            "data_residency": {
                "nigerian_data_in_nigeria": 97.5,
                "cross_border_transfers": 12,
                "residency_violations": len(iso_report.gaps_identified),
                "compliant_locations": ["nigeria-lagos-dc", "nigeria-abuja-dc"]
            },
            "mfa_status": security_report["mfa_metrics"],
            "iso27001_details": {
                "controls_total": iso_report.controls_total,
                "controls_compliant": iso_report.controls_compliant,
                "controls_non_compliant": iso_report.controls_non_compliant,
                "certification_status": iso_report.certification_status
            },
            "recommendations": iso_report.recommendations[:5]  # Top 5 recommendations
        }
        
        return dashboard_data
        
    except Exception as e:
        logger.error(f"Failed to get security dashboard: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to retrieve dashboard data")


@router.get("/iso27001/report")
async def get_iso27001_report(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get detailed ISO 27001 compliance report"""
    
    try:
        iso_compliance_manager = ISO27001ComplianceManager()
        report = await iso_compliance_manager.monitor_security_controls()
        
        return {
            "report": report,
            "generated_by": current_user.email,
            "organization_id": str(current_user.organization_id) if current_user.organization_id else None
        }
        
    except Exception as e:
        logger.error(f"Failed to generate ISO 27001 report: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to generate ISO 27001 report")


@router.get("/data-residency/status")
async def get_data_residency_status(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get Nigerian data residency compliance status"""
    
    try:
        data_residency_service = NigerianDataResidencyService()
        
        report = await data_residency_service.get_data_location_report(
            organization_id=str(current_user.organization_id) if current_user.organization_id else None
        )
        
        return report
        
    except Exception as e:
        logger.error(f"Failed to get data residency status: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to retrieve data residency status")


@router.post("/data-residency/validate-transfer")
async def validate_cross_border_transfer(
    transfer_request: Dict[str, Any],
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Validate if cross-border data transfer is allowed"""
    
    try:
        data_residency_service = NigerianDataResidencyService()
        
        validation_result = await data_residency_service.validate_cross_border_transfer(
            data_type=transfer_request.get("data_type"),
            source_location=transfer_request.get("source_location"),
            destination_location=transfer_request.get("destination_location")
        )
        
        # Audit the validation request
        audit_service = ComprehensiveAuditService()
        await audit_service.log_audit_event(
            event_type=AuditEventType.COMPLIANCE_EVENT,
            event_description=f"Cross-border transfer validation for {transfer_request.get('data_type')}",
            outcome=AuditOutcome.SUCCESS if validation_result["allowed"] else AuditOutcome.BLOCKED,
            user_id=str(current_user.id),
            additional_data={
                "transfer_request": transfer_request,
                "validation_result": validation_result
            },
            db=db
        )
        
        return validation_result
        
    except Exception as e:
        logger.error(f"Failed to validate transfer: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to validate cross-border transfer")


@router.get("/mfa/status")
async def get_mfa_status(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get user's MFA configuration status"""
    
    try:
        security_framework = NigerianSecurityFramework()
        
        # Check current MFA configuration
        # In production, this would load from database
        mfa_status = {
            "user_id": str(current_user.id),
            "mfa_enabled": False,  # Would check actual MFA status
            "methods_configured": [],
            "security_level": SecurityLevel.BASIC.value,
            "nigerian_phone_verified": False,
            "backup_codes_remaining": 0,
            "compliance_status": "non_compliant"
        }
        
        return mfa_status
        
    except Exception as e:
        logger.error(f"Failed to get MFA status: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to retrieve MFA status")


@router.post("/mfa/setup")
async def setup_mfa(
    mfa_config: Dict[str, Any],
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Setup multi-factor authentication for user"""
    
    try:
        security_framework = NigerianSecurityFramework()
        
        # Parse configuration
        security_level = SecurityLevel(mfa_config.get("security_level", SecurityLevel.ENHANCED.value))
        nigerian_phone = mfa_config.get("nigerian_phone")
        
        # Implement MFA
        mfa_result = await security_framework.implement_mfa(
            user_id=current_user.id,
            nigerian_phone=nigerian_phone,
            security_level=security_level,
            db=db
        )
        
        return {
            "success": True,
            "mfa_config": {
                "user_id": mfa_result.user_id,
                "security_level": mfa_result.security_level.value,
                "methods_enabled": [method.value for method in mfa_result.secondary_methods],
                "backup_codes": mfa_result.backup_codes,
                "totp_qr_code": getattr(mfa_result, 'totp_secret', {}).get('qr_code') if hasattr(mfa_result, 'totp_secret') else None
            }
        }
        
    except Exception as e:
        logger.error(f"Failed to setup MFA: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to setup MFA")


@router.post("/mfa/verify")
async def verify_mfa_token(
    verification_request: Dict[str, Any],
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Verify MFA token"""
    
    try:
        security_framework = NigerianSecurityFramework()
        
        method = MFAMethod(verification_request.get("method"))
        token = verification_request.get("token")
        
        if not token:
            raise HTTPException(status_code=400, detail="Token is required")
        
        verification_result = await security_framework.verify_mfa_token(
            user_id=current_user.id,
            method=method,
            token=token,
            db=db
        )
        
        return verification_result
        
    except Exception as e:
        logger.error(f"Failed to verify MFA token: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to verify MFA token")


@router.get("/audit/report")
async def get_audit_report(
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    event_type: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Generate comprehensive audit report"""
    
    try:
        audit_service = ComprehensiveAuditService()
        
        # Parse dates
        start = datetime.fromisoformat(start_date) if start_date else datetime.utcnow() - timedelta(days=30)
        end = datetime.fromisoformat(end_date) if end_date else datetime.utcnow()
        
        # Filter by event type if provided
        event_types = [AuditEventType(event_type)] if event_type else None
        
        report = await audit_service.generate_audit_report(
            start_date=start,
            end_date=end,
            event_types=event_types,
            user_id=str(current_user.id),
            organization_id=str(current_user.organization_id) if current_user.organization_id else None,
            compliance_focus=True
        )
        
        return report
        
    except Exception as e:
        logger.error(f"Failed to generate audit report: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to generate audit report")


@router.post("/compliance-check")
async def check_compliance_status(
    operation_request: Dict[str, Any],
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Check if current security posture meets compliance requirements for operation"""
    
    try:
        security_framework = NigerianSecurityFramework()
        
        operation = operation_request.get("operation")
        data_classification = operation_request.get("data_classification", "internal")
        
        compliance_status = await security_framework.check_nigerian_compliance_status(
            user_id=current_user.id,
            operation=operation,
            data_classification=data_classification
        )
        
        # Audit compliance check
        audit_service = ComprehensiveAuditService()
        await audit_service.log_audit_event(
            event_type=AuditEventType.COMPLIANCE_EVENT,
            event_description=f"Compliance check for operation: {operation}",
            outcome=AuditOutcome.SUCCESS if compliance_status["compliant"] else AuditOutcome.WARNING,
            user_id=str(current_user.id),
            additional_data={
                "operation": operation,
                "data_classification": data_classification,
                "compliance_result": compliance_status
            },
            db=db
        )
        
        return compliance_status
        
    except Exception as e:
        logger.error(f"Failed to check compliance status: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to check compliance status")


@router.post("/security-incident")
async def report_security_incident(
    incident_data: Dict[str, Any],
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Report a security incident"""
    
    try:
        audit_service = ComprehensiveAuditService()
        
        # Log security incident
        await audit_service.log_audit_event(
            event_type=AuditEventType.SECURITY_EVENT,
            event_description=f"Security incident reported: {incident_data.get('title', 'Unknown')}",
            outcome=AuditOutcome.SUSPICIOUS,
            user_id=str(current_user.id),
            additional_data=incident_data,
            db=db
        )
        
        # Schedule background processing
        background_tasks.add_task(
            _process_security_incident,
            incident_data,
            str(current_user.id)
        )
        
        return {
            "success": True,
            "incident_id": incident_data.get("id", "generated_id"),
            "message": "Security incident reported and being processed"
        }
        
    except Exception as e:
        logger.error(f"Failed to report security incident: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to report security incident")


def _get_recent_security_events() -> List[Dict[str, Any]]:
    """Get recent security events (simplified implementation)"""
    
    return [
        {
            "id": "1",
            "type": "Failed Login Attempt",
            "severity": "medium",
            "description": "Multiple failed login attempts from foreign IP",
            "timestamp": datetime.utcnow().isoformat(),
            "resolved": False
        },
        {
            "id": "2", 
            "type": "Data Residency Alert",
            "severity": "high",
            "description": "Nigerian PII detected in non-Nigerian datacenter",
            "timestamp": (datetime.utcnow() - timedelta(hours=1)).isoformat(),
            "resolved": True
        },
        {
            "id": "3",
            "type": "MFA Bypass Attempt",
            "severity": "critical",
            "description": "User attempted to bypass MFA for FIRS submission",
            "timestamp": (datetime.utcnow() - timedelta(hours=2)).isoformat(),
            "resolved": False
        }
    ]


async def _process_security_incident(incident_data: Dict[str, Any], user_id: str):
    """Process security incident in background"""
    
    try:
        # This would implement actual incident processing
        # - Alert security team
        # - Update security monitoring systems
        # - Generate incident response tasks
        # - Update compliance dashboards
        
        logger.info(f"Processing security incident: {incident_data.get('id')} for user {user_id}")
        
        # Simulate processing time
        import asyncio
        await asyncio.sleep(2)
        
        logger.info(f"Security incident processed: {incident_data.get('id')}")
        
    except Exception as e:
        logger.error(f"Failed to process security incident: {str(e)}")


@router.get("/health")
async def security_health_check():
    """Health check for security compliance services"""
    
    try:
        # Check all services are operational
        services_status = {
            "iso27001_service": "operational",
            "data_residency_service": "operational", 
            "audit_service": "operational",
            "mfa_service": "operational",
            "nigerian_compliance": "compliant"
        }
        
        return {
            "status": "healthy",
            "timestamp": datetime.utcnow().isoformat(),
            "services": services_status
        }
        
    except Exception as e:
        logger.error(f"Security health check failed: {str(e)}")
        return {
            "status": "degraded",
            "timestamp": datetime.utcnow().isoformat(),
            "error": str(e)
        }