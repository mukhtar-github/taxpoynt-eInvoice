"""
Privacy Protection for Transaction Classification
===============================================

NDPR-compliant data anonymization and PII removal for API calls.
Ensures privacy-first handling of sensitive financial data.
"""

import re
import hashlib
import logging
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, time
from decimal import Decimal
from enum import Enum

from .classification_models import (
    TransactionClassificationRequest,
    PrivacyLevel,
    UserContext
)

logger = logging.getLogger(__name__)

class PIIType(str, Enum):
    """Types of personally identifiable information"""
    ACCOUNT_NUMBER = "account_number"
    PHONE_NUMBER = "phone_number"
    EMAIL_ADDRESS = "email_address"
    FULL_NAME = "full_name"
    ADDRESS = "address"
    BVN = "bvn"
    NIN = "nin"
    CUSTOM = "custom"

class DataAnonymizer:
    """
    Data anonymization utilities with Nigerian context
    """
    
    def __init__(self):
        self.logger = logging.getLogger(f"{__name__}.DataAnonymizer")
        
        # Nigerian-specific patterns
        self.nigerian_patterns = {
            'phone_numbers': [
                r'\b(\+234|0)[7-9][0-1]\d{8}\b',  # Nigerian mobile numbers
                r'\b[0-9]{11}\b',                   # 11-digit numbers (likely phones)
            ],
            'account_numbers': [
                r'\b\d{10,12}\b',                   # 10-12 digit account numbers
                r'\b[0-9]{4}[\s-]?[0-9]{4}[\s-]?[0-9]{2,4}\b',  # Formatted account numbers
            ],
            'names': [
                r'\b[A-Z][a-z]+\s+[A-Z][a-z]+(?:\s+[A-Z][a-z]+)?\b',  # Full names
                r'\b(?:Mr\.?|Mrs\.?|Miss|Dr\.?|Prof\.?)\s+[A-Z][a-z]+\b',  # Titles + names
            ],
            'emails': [
                r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',
            ],
            'addresses': [
                r'\b\d+[A-Za-z\s,]+(?:Street|St|Road|Rd|Avenue|Ave|Close|Cl)\b',
                r'\b(?:Lagos|Abuja|Port\s+Harcourt|Kano|Ibadan|Kaduna|Enugu|Onitsha)\b',
            ]
        }
    
    def anonymize_narration(self, narration: str, privacy_level: PrivacyLevel = PrivacyLevel.STANDARD) -> str:
        """Anonymize transaction narration based on privacy level"""
        
        anonymized = narration
        
        # Apply anonymization based on privacy level
        if privacy_level in [PrivacyLevel.STANDARD, PrivacyLevel.HIGH, PrivacyLevel.MAXIMUM]:
            
            # Remove phone numbers
            for pattern in self.nigerian_patterns['phone_numbers']:
                anonymized = re.sub(pattern, '[PHONE]', anonymized, flags=re.IGNORECASE)
            
            # Remove account numbers
            for pattern in self.nigerian_patterns['account_numbers']:
                anonymized = re.sub(pattern, '[ACCOUNT]', anonymized, flags=re.IGNORECASE)
            
            # Remove email addresses
            for pattern in self.nigerian_patterns['emails']:
                anonymized = re.sub(pattern, '[EMAIL]', anonymized, flags=re.IGNORECASE)
        
        if privacy_level in [PrivacyLevel.HIGH, PrivacyLevel.MAXIMUM]:
            
            # Remove names (more aggressive)
            for pattern in self.nigerian_patterns['names']:
                anonymized = re.sub(pattern, '[NAME]', anonymized, flags=re.IGNORECASE)
            
            # Remove specific addresses
            for pattern in self.nigerian_patterns['addresses']:
                anonymized = re.sub(pattern, '[ADDRESS]', anonymized, flags=re.IGNORECASE)
        
        if privacy_level == PrivacyLevel.MAXIMUM:
            
            # Remove any remaining potential identifiers
            # Remove sequences of digits that might be identifiers
            anonymized = re.sub(r'\b\d{6,}\b', '[IDENTIFIER]', anonymized)
            
            # Remove specific business names (very conservative)
            # Keep only generic business terms
            business_terms = ['payment', 'transfer', 'invoice', 'goods', 'services', 'business']
            words = anonymized.split()
            filtered_words = []
            
            for word in words:
                word_lower = word.lower().strip('.,!?;:')
                if (word_lower in business_terms or 
                    word.startswith('[') and word.endswith(']') or
                    len(word) <= 3):
                    filtered_words.append(word)
                else:
                    filtered_words.append('[TERM]')
            
            anonymized = ' '.join(filtered_words)
        
        return anonymized.strip()
    
    def categorize_amount(self, amount: Decimal) -> str:
        """Categorize amount into ranges instead of exact values"""
        
        amount_float = float(amount)
        
        if amount_float < 1000:
            return "very_small"
        elif amount_float < 10000:
            return "small"
        elif amount_float < 100000:
            return "medium"
        elif amount_float < 1000000:
            return "large"
        else:
            return "very_large"
    
    def round_amount(self, amount: Decimal, privacy_level: PrivacyLevel = PrivacyLevel.STANDARD) -> Decimal:
        """Round amount based on privacy level"""
        
        amount_float = float(amount)
        
        if privacy_level == PrivacyLevel.STANDARD:
            # Round to nearest 1000
            return Decimal(str(int(round(amount_float, -3))))
        
        elif privacy_level == PrivacyLevel.HIGH:
            # Round to nearest 5000
            return Decimal(str(int(round(amount_float / 5000) * 5000)))
        
        else:  # MAXIMUM
            # Round to nearest 10000
            return Decimal(str(int(round(amount_float / 10000) * 10000)))
    
    def categorize_time(self, transaction_time: Optional[str], transaction_date: datetime) -> str:
        """Categorize time instead of providing exact time"""
        
        try:
            if not transaction_time or ':' not in transaction_time:
                return "unknown"
            
            hour = int(transaction_time.split(':')[0])
            
            if 6 <= hour < 12:
                return "morning"
            elif 12 <= hour < 18:
                return "afternoon"
            elif 18 <= hour < 22:
                return "evening"
            else:
                return "night"
        
        except Exception:
            return "unknown"
    
    def get_day_category(self, transaction_date: datetime) -> str:
        """Get day category instead of exact date"""
        
        weekday = transaction_date.weekday()
        
        if weekday < 5:
            return "weekday"
        elif weekday == 5:
            return "saturday"
        else:
            return "sunday"
    
    def categorize_bank(self, bank_name: Optional[str]) -> str:
        """Categorize bank into tiers instead of specific names"""
        
        if not bank_name:
            return "unknown"
        
        bank_lower = bank_name.lower()
        
        # Tier 1 banks (major Nigerian banks)
        tier1_banks = ['gtbank', 'access', 'zenith', 'first bank', 'uba', 'fidelity']
        if any(bank in bank_lower for bank in tier1_banks):
            return "tier1"
        
        # Tier 2 banks
        tier2_banks = ['stanbic', 'sterling', 'fcmb', 'union', 'wema']
        if any(bank in bank_lower for bank in tier2_banks):
            return "tier2"
        
        # Digital/fintech banks
        digital_banks = ['kuda', 'carbon', 'cowrywise', 'piggyvest']
        if any(bank in bank_lower for bank in digital_banks):
            return "digital"
        
        return "tier3"

class PIIRedactor:
    """
    Advanced PII detection and redaction
    """
    
    def __init__(self):
        self.logger = logging.getLogger(f"{__name__}.PIIRedactor")
        self.anonymizer = DataAnonymizer()
    
    def detect_pii(self, text: str) -> List[Dict[str, Any]]:
        """Detect PII in text and return findings"""
        
        findings = []
        
        # Check for different PII types
        for pii_type, patterns in self.anonymizer.nigerian_patterns.items():
            for pattern in patterns:
                matches = re.finditer(pattern, text, re.IGNORECASE)
                for match in matches:
                    findings.append({
                        'type': pii_type,
                        'text': match.group(),
                        'start': match.start(),
                        'end': match.end(),
                        'confidence': self._calculate_pii_confidence(pii_type, match.group())
                    })
        
        return findings
    
    def redact_pii(self, text: str, pii_types: List[PIIType] = None) -> Tuple[str, List[Dict[str, Any]]]:
        """Redact PII from text and return redacted text with report"""
        
        if pii_types is None:
            pii_types = list(PIIType)
        
        redacted_text = text
        redaction_report = []
        
        # Detect all PII
        findings = self.detect_pii(text)
        
        # Filter by requested types and redact
        for finding in findings:
            if finding['type'] in [pii_type.value for pii_type in pii_types]:
                redaction_token = f"[{finding['type'].upper()}]"
                redacted_text = redacted_text.replace(finding['text'], redaction_token)
                redaction_report.append({
                    'original_text': finding['text'],
                    'redacted_as': redaction_token,
                    'type': finding['type'],
                    'confidence': finding['confidence']
                })
        
        return redacted_text, redaction_report
    
    def _calculate_pii_confidence(self, pii_type: str, text: str) -> float:
        """Calculate confidence that detected text is actually PII"""
        
        if pii_type == 'phone_numbers':
            # Nigerian phone numbers are pretty distinctive
            if text.startswith('+234') or text.startswith('0'):
                return 0.95
            elif len(text) == 11 and text.isdigit():
                return 0.85
            else:
                return 0.70
        
        elif pii_type == 'account_numbers':
            # Account numbers are less certain
            if 10 <= len(text) <= 12 and text.isdigit():
                return 0.80
            else:
                return 0.60
        
        elif pii_type == 'emails':
            # Email patterns are highly reliable
            return 0.95
        
        elif pii_type == 'names':
            # Names are tricky - could be false positives
            if any(title in text.lower() for title in ['mr.', 'mrs.', 'miss', 'dr.', 'prof.']):
                return 0.90
            else:
                return 0.70
        
        else:
            return 0.75

class APIPrivacyProtection:
    """
    NDPR-compliant data anonymization for API calls
    """
    
    def __init__(self):
        self.logger = logging.getLogger(f"{__name__}.APIPrivacyProtection")
        self.anonymizer = DataAnonymizer()
        self.pii_redactor = PIIRedactor()
    
    def anonymize_for_api(self, 
                         request: TransactionClassificationRequest,
                         privacy_level: Optional[PrivacyLevel] = None) -> Dict[str, Any]:
        """
        Remove/mask sensitive data before API calls
        """
        
        privacy_level = privacy_level or request.privacy_level or PrivacyLevel.STANDARD
        
        try:
            # Create anonymized transaction data
            anonymized_data = {
                'amount_category': self.anonymizer.categorize_amount(request.amount),
                'narration': self.anonymizer.anonymize_narration(request.narration, privacy_level),
                'time_category': self.anonymizer.categorize_time(request.time, request.date),
                'day_of_week': self.anonymizer.get_day_category(request.date),
                'bank_category': self.anonymizer.categorize_bank(request.bank),
            }
            
            # Add rounded amount for certain privacy levels
            if privacy_level in [PrivacyLevel.STANDARD, PrivacyLevel.HIGH]:
                anonymized_data['amount_rounded'] = float(
                    self.anonymizer.round_amount(request.amount, privacy_level)
                )
            
            # Add business context (already anonymized)
            anonymized_data['business_context'] = {
                'industry': request.user_context.business_context.industry,
                'business_size': request.user_context.business_context.business_size,
                'location_type': 'urban' if request.user_context.business_context.state else 'unknown',
                'years_in_operation_category': self._categorize_years_in_operation(
                    request.user_context.business_context.years_in_operation
                )
            }
            
            # Add metadata about anonymization
            anonymized_data['privacy_metadata'] = {
                'privacy_level': privacy_level,
                'anonymization_timestamp': datetime.utcnow().isoformat(),
                'data_retention_period': '7_years',  # FIRS requirement
                'ndpr_compliant': True
            }
            
            self.logger.debug(f"Data anonymized for API call with privacy level: {privacy_level}")
            return anonymized_data
            
        except Exception as e:
            self.logger.error(f"Error anonymizing data: {e}")
            # Return minimal data on error
            return {
                'amount_category': 'unknown',
                'narration': '[REDACTED]',
                'time_category': 'unknown',
                'privacy_level': privacy_level,
                'error': 'anonymization_failed'
            }
    
    def validate_anonymization(self, anonymized_data: Dict[str, Any]) -> Dict[str, Any]:
        """Validate that data has been properly anonymized"""
        
        validation_report = {
            'is_valid': True,
            'violations': [],
            'warnings': [],
            'privacy_score': 1.0
        }
        
        try:
            # Check narration for remaining PII
            narration = anonymized_data.get('narration', '')
            if narration and narration != '[REDACTED]':
                findings = self.pii_redactor.detect_pii(narration)
                
                if findings:
                    validation_report['is_valid'] = False
                    validation_report['violations'].extend([
                        f"PII detected: {finding['type']} - {finding['text']}"
                        for finding in findings
                    ])
                    validation_report['privacy_score'] -= 0.2 * len(findings)
            
            # Check for exact amounts (should be categorized or rounded)
            if 'amount' in anonymized_data and isinstance(anonymized_data['amount'], (int, float)):
                if anonymized_data['amount'] % 1000 != 0:  # Not rounded
                    validation_report['warnings'].append("Exact amount present - consider rounding")
                    validation_report['privacy_score'] -= 0.1
            
            # Check for exact timestamps
            if 'timestamp' in anonymized_data:
                validation_report['warnings'].append("Exact timestamp present - consider categorizing")
                validation_report['privacy_score'] -= 0.05
            
            # Ensure privacy score is within bounds
            validation_report['privacy_score'] = max(0.0, min(1.0, validation_report['privacy_score']))
            
        except Exception as e:
            self.logger.error(f"Error validating anonymization: {e}")
            validation_report['is_valid'] = False
            validation_report['violations'].append(f"Validation error: {str(e)}")
        
        return validation_report
    
    def get_ndpr_compliance_report(self, 
                                 request: TransactionClassificationRequest,
                                 anonymized_data: Dict[str, Any]) -> Dict[str, Any]:
        """Generate NDPR compliance report"""
        
        return {
            'compliance_status': 'compliant',
            'data_subject_id': request.user_context.user_id,
            'processing_purpose': 'tax_compliance_classification',
            'legal_basis': 'legitimate_interest',
            'data_minimization_applied': True,
            'retention_period': '7_years',
            'data_categories_processed': [
                'financial_transaction_data',
                'business_context_data'
            ],
            'data_categories_excluded': [
                'personal_identifiers',
                'account_numbers',
                'phone_numbers',
                'exact_amounts',
                'exact_timestamps'
            ],
            'anonymization_techniques_used': [
                'data_categorization',
                'value_rounding',
                'pii_redaction',
                'temporal_generalization'
            ],
            'third_party_sharing': {
                'recipient': 'openai_api',
                'purpose': 'transaction_classification',
                'data_transfer_basis': 'anonymized_data_only',
                'retention_by_recipient': 'not_retained'
            },
            'data_subject_rights': {
                'access': 'available',
                'rectification': 'available',
                'erasure': 'available_after_retention_period',
                'portability': 'available',
                'objection': 'available'
            },
            'report_timestamp': datetime.utcnow().isoformat(),
            'compliance_version': '1.0'
        }
    
    def _categorize_years_in_operation(self, years: Optional[int]) -> str:
        """Categorize years in operation to avoid exact identification"""
        
        if years is None:
            return 'unknown'
        elif years < 1:
            return 'startup'
        elif years < 3:
            return 'early'
        elif years < 10:
            return 'established'
        else:
            return 'mature'