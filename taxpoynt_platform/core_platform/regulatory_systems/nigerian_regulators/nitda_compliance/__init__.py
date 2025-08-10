"""
NITDA NDPA Compliance Framework
==============================
Nigerian Data Protection Act (NDPA) compliance implementation under 
Nigeria Information Technology Development Agency (NITDA) oversight.

Components:
- ndpa_compliance_engine.py: Core NDPA compliance orchestrator
- data_subject_rights.py: Nigerian data subject rights management
- consent_management.py: NDPA-compliant consent handling
- breach_notification.py: Nigerian breach notification requirements
- privacy_impact_assessment.py: NDPA privacy impact assessments
- models.py: NDPA data models and structures

Nigerian NDPA Features:
- Nigerian data residency requirements
- Naira-denominated penalty calculations
- Nigerian legal entity validation
- NITDA reporting and compliance
- Cross-border transfer restrictions
- Local data protection officer requirements
"""

from .ndpa_compliance_engine import NDPAComplianceEngine
from .data_subject_rights import NigerianDataSubjectRights
from .models import NDPAComplianceResult, NigerianConsentRecord, NDPABreachNotification

__all__ = [
    'NDPAComplianceEngine',
    'NigerianDataSubjectRights',
    'NDPAComplianceResult',
    'NigerianConsentRecord', 
    'NDPABreachNotification'
]