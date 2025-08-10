"""
GDPR Compliance Framework
========================
European General Data Protection Regulation (GDPR) compliance implementation
for international data protection requirements.

Components:
- gdpr_compliance_engine.py: Core GDPR compliance orchestrator
- data_subject_rights.py: European data subject rights management
- consent_management.py: GDPR-compliant consent handling
- breach_notification.py: GDPR breach notification (72-hour rule)
- privacy_impact_assessment.py: GDPR DPIA requirements
- cross_border_transfers.py: EU adequacy decisions and SCCs
- models.py: GDPR data models and structures

European GDPR Features:
- EU adequacy decision validation
- Standard Contractual Clauses (SCCs)
- EUR penalty calculations (4% of turnover)
- Data Protection Officer (DPO) requirements
- One-stop-shop mechanism
- Right to be forgotten implementation
- Privacy by design principles
"""

from .gdpr_compliance_engine import GDPRComplianceEngine
from .data_subject_rights import EuropeanDataSubjectRights
from .cross_border_transfers import CrossBorderTransferManager
from .models import GDPRComplianceResult, EuropeanConsentRecord, GDPRBreachNotification

__all__ = [
    'GDPRComplianceEngine',
    'EuropeanDataSubjectRights',
    'CrossBorderTransferManager',
    'GDPRComplianceResult',
    'EuropeanConsentRecord',
    'GDPRBreachNotification'
]