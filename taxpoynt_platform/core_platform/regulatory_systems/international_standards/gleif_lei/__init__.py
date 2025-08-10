"""
Legal Entity Identifier (LEI) Validation System
=============================================
GLEIF (Global Legal Entity Identifier Foundation) compliant LEI validation
and entity verification system for international regulatory compliance.

LEI provides unique identification of legal entities participating in financial
transactions, supporting regulatory reporting and entity verification requirements.

Core Features:
- ISO 17442 compliant LEI format validation with check digit verification
- GLEIF registry integration for real-time entity verification
- Nigerian entity mapping with TIN/CAC registration integration
- Batch validation capabilities for high-volume processing
- Comprehensive validation reporting and performance metrics
- Entity relationship mapping and corporate structure analysis

Components:
- lei_validator.py: Core LEI validation and verification engine
- models.py: LEI data models and validation schemas with Nigerian extensions
"""

from .lei_validator import LEIValidator
from .models import (
    LEIRecord, LEIValidationResult, EntityStatus, LEIRelationship,
    RegistrationAuthority, LEIComplianceReport, NigerianEntityMapping,
    LEIValidationStatus, GLEIFApiResponse, LEIPerformanceMetrics
)

__all__ = [
    'LEIValidator',
    'LEIRecord',
    'LEIValidationResult', 
    'EntityStatus',
    'LEIRelationship',
    'RegistrationAuthority',
    'LEIComplianceReport',
    'NigerianEntityMapping',
    'LEIValidationStatus',
    'GLEIFApiResponse',
    'LEIPerformanceMetrics'
]