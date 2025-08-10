"""
CBN (Central Bank of Nigeria) Compliance Module
===============================================
Comprehensive banking compliance validation system for Nigerian financial regulations.

The CBN compliance module provides validation and monitoring for:
- Banking license compliance and prudential guidelines
- Know Your Customer (KYC) and Anti-Money Laundering (AML) regulations
- Consumer protection and financial services standards
- Payment system oversight and electronic payment regulations
- Foreign exchange and international payment compliance
- Capital adequacy and risk management requirements
- Corporate governance and operational risk standards

Core Components:
- models.py: CBN-specific data models and financial entities
- cbn_validator.py: Main CBN compliance validation engine
- banking_regulations.py: Banking license and prudential compliance
- kyc_aml_validator.py: KYC/AML compliance validation
- payment_systems.py: Payment system and e-payment compliance
- forex_compliance.py: Foreign exchange regulation compliance
- consumer_protection.py: Consumer protection standard validation
- risk_management.py: Risk management and capital adequacy validation

Integration:
- Integrates with Universal Compliance Validation Engine
- Provides CBN-specific validation plugins for compliance orchestrator
- Supports real-time compliance monitoring and alerting
- Generates CBN regulatory submission reports
"""

from .models import (
    CBNComplianceRequest, CBNValidationResult, BankingLicense,
    KYCProfile, AMLTransaction, PaymentSystemRegistration,
    ForexTransaction, ConsumerComplaint, RiskAssessment,
    CBNComplianceStatus, CBNRiskLevel, CBNRegulationType
)
from .cbn_validator import CBNValidator
from .banking_regulations import BankingRegulationsValidator
from .kyc_aml_validator import KYCAMLValidator
from .payment_systems import PaymentSystemsValidator
from .forex_compliance import ForexComplianceValidator
from .consumer_protection import ConsumerProtectionValidator
from .risk_management import RiskManagementValidator

__all__ = [
    # Data Models
    'CBNComplianceRequest',
    'CBNValidationResult', 
    'BankingLicense',
    'KYCProfile',
    'AMLTransaction',
    'PaymentSystemRegistration',
    'ForexTransaction',
    'ConsumerComplaint',
    'RiskAssessment',
    'CBNComplianceStatus',
    'CBNRiskLevel',
    'CBNRegulationType',
    
    # Validators
    'CBNValidator',
    'BankingRegulationsValidator',
    'KYCAMLValidator',
    'PaymentSystemsValidator', 
    'ForexComplianceValidator',
    'ConsumerProtectionValidator',
    'RiskManagementValidator'
]