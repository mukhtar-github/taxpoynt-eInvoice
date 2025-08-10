"""
CAC (Corporate Affairs Commission) Compliance Framework
=====================================================
Comprehensive Nigerian corporate entity validation system for CAC regulatory requirements.

CAC Registration Validation Components:
- Nigerian company registration number (RC) validation and verification
- Business name validation and availability checking
- Director and shareholder information validation
- Corporate structure and compliance status verification
- Annual filing compliance and status tracking

Core Components:
- cac_validator.py: Main CAC compliance validation engine
- models.py: CAC-specific data models and validation schemas
- entity_validator.py: Nigerian corporate entity validation engine
- business_rules.py: CAC business rules and regulatory compliance
- registration_handler.py: CAC registration verification and status checking
"""

from .cac_validator import CACValidator
from .models import (
    CACValidationResult, NigerianEntityInfo, RCValidationResult,
    CACComplianceStatus, BusinessNameValidation, DirectorInfo,
    EntityRegistration, CACFilingStatus
)

__all__ = [
    'CACValidator',
    'CACValidationResult',
    'NigerianEntityInfo',
    'RCValidationResult',
    'CACComplianceStatus',
    'BusinessNameValidation',
    'DirectorInfo',
    'EntityRegistration',
    'CACFilingStatus'
]