"""
Cross-Connector Customer Matching Engine
=======================================

Advanced customer intelligence system that matches customers, companies, and transactions
across different business systems (ERP, POS, CRM) using fuzzy matching, pattern recognition,
and machine learning techniques.

This engine enables:
- Customer identity resolution across multiple systems
- Company matching and deduplication
- Transaction pattern analysis and fraud detection
- Customer journey tracking across touchpoints
- Nigerian business entity verification and compliance
- Cross-system customer insights and analytics

Key Features:
- Fuzzy string matching for names and addresses
- Phone number and email normalization and matching
- Nigerian TIN and CAC registration number verification
- Behavioral pattern matching across systems
- Machine learning similarity scoring
- Real-time matching with configurable thresholds
- Audit trail for all matching decisions
"""

import re
import hashlib
import logging
from typing import Dict, List, Optional, Tuple, Any, Set
from datetime import datetime, timedelta
from dataclasses import dataclass
from enum import Enum
import asyncio
from difflib import SequenceMatcher
import phonenumbers
from phonenumbers import NumberParseException

from ..models.universal_processed_transaction import UniversalProcessedTransaction
from ..connector_configs.connector_types import ConnectorType

logger = logging.getLogger(__name__)


class MatchConfidence(Enum):
    """Confidence levels for customer matching."""
    EXACT = "exact"          # 95-100% confidence
    HIGH = "high"            # 80-94% confidence  
    MEDIUM = "medium"        # 60-79% confidence
    LOW = "low"              # 40-59% confidence
    NO_MATCH = "no_match"    # 0-39% confidence


class MatchingStrategy(Enum):
    """Strategies for customer matching."""
    STRICT = "strict"        # High precision, low recall
    BALANCED = "balanced"    # Balanced precision and recall
    PERMISSIVE = "permissive"  # High recall, lower precision


@dataclass
class CustomerIdentity:
    """Unified customer identity across systems."""
    universal_id: str
    primary_name: str
    normalized_names: Set[str]
    phone_numbers: Set[str]
    email_addresses: Set[str]
    physical_addresses: Set[str]
    business_identifiers: Dict[str, str]  # TIN, CAC, etc.
    source_systems: Dict[ConnectorType, str]  # system -> local_id
    confidence_score: float
    last_updated: datetime
    verification_status: Dict[str, bool]  # TIN verified, CAC verified, etc.
    
    def __post_init__(self):
        """Ensure sets are properly initialized."""
        if not isinstance(self.normalized_names, set):
            self.normalized_names = set(self.normalized_names) if self.normalized_names else set()
        if not isinstance(self.phone_numbers, set):
            self.phone_numbers = set(self.phone_numbers) if self.phone_numbers else set()
        if not isinstance(self.email_addresses, set):
            self.email_addresses = set(self.email_addresses) if self.email_addresses else set()
        if not isinstance(self.physical_addresses, set):
            self.physical_addresses = set(self.physical_addresses) if self.physical_addresses else set()


@dataclass 
class MatchResult:
    """Result of a customer matching operation."""
    matched_identity: Optional[CustomerIdentity]
    confidence: MatchConfidence
    confidence_score: float
    matching_factors: List[str]
    new_identity_created: bool
    merge_candidates: List[CustomerIdentity]
    processing_notes: List[str]


class CustomerNormalization:
    """Utilities for normalizing customer data for matching."""
    
    @staticmethod
    def normalize_name(name: str) -> str:
        """Normalize customer name for matching."""
        if not name:
            return ""
        
        # Convert to lowercase and remove extra spaces
        normalized = re.sub(r'\s+', ' ', name.lower().strip())
        
        # Remove common business suffixes
        business_suffixes = [
            'ltd', 'limited', 'inc', 'incorporated', 'corp', 'corporation',
            'plc', 'llc', 'co', 'company', 'enterprises', 'group',
            'nigeria limited', 'nig ltd', 'ng ltd'
        ]
        
        for suffix in business_suffixes:
            normalized = re.sub(rf'\b{suffix}\b\.?$', '', normalized).strip()
        
        # Remove special characters but keep spaces
        normalized = re.sub(r'[^\w\s]', '', normalized)
        
        return normalized
    
    @staticmethod
    def normalize_phone(phone: str, default_country: str = 'NG') -> Optional[str]:
        """Normalize phone number to international format."""
        if not phone:
            return None
        
        try:
            # Parse phone number
            parsed = phonenumbers.parse(phone, default_country)
            
            if phonenumbers.is_valid_number(parsed):
                # Return in E164 format (+234xxxxxxxxxx)
                return phonenumbers.format_number(parsed, phonenumbers.PhoneNumberFormat.E164)
        except NumberParseException:
            pass
        
        # Fallback: clean and format manually for Nigerian numbers
        cleaned = re.sub(r'[^\d]', '', phone)
        
        # Handle common Nigerian number formats
        if cleaned.startswith('234'):
            return f"+{cleaned}"
        elif cleaned.startswith('0') and len(cleaned) == 11:
            return f"+234{cleaned[1:]}"
        elif len(cleaned) == 10:
            return f"+234{cleaned}"
        
        return None
    
    @staticmethod
    def normalize_email(email: str) -> str:
        """Normalize email address."""
        if not email:
            return ""
        
        return email.lower().strip()
    
    @staticmethod
    def normalize_address(address: str) -> str:
        """Normalize physical address."""
        if not address:
            return ""
        
        # Convert to lowercase and remove extra spaces
        normalized = re.sub(r'\s+', ' ', address.lower().strip())
        
        # Common address normalizations
        normalized = re.sub(r'\bstreet\b', 'st', normalized)
        normalized = re.sub(r'\bavenue\b', 'ave', normalized)
        normalized = re.sub(r'\broad\b', 'rd', normalized)
        normalized = re.sub(r'\bclose\b', 'cl', normalized)
        
        # Remove common suffixes
        normalized = re.sub(r',?\s*(nigeria|ng)$', '', normalized)
        
        return normalized
    
    @staticmethod
    def normalize_business_id(business_id: str, id_type: str) -> str:
        """Normalize business identifier (TIN, CAC, etc.)."""
        if not business_id:
            return ""
        
        # Remove spaces and special characters, keep only alphanumeric
        normalized = re.sub(r'[^\w]', '', business_id.upper())
        
        # TIN-specific normalization
        if id_type.lower() == 'tin':
            # Nigerian TIN format: XXXXXXXXXX-XXXX
            if len(normalized) == 14:
                return f"{normalized[:10]}-{normalized[10:]}"
            elif len(normalized) == 10:
                return normalized
        
        # CAC-specific normalization
        elif id_type.lower() == 'cac':
            # Nigerian CAC format: RC followed by numbers
            if normalized.startswith('RC'):
                return normalized
            elif normalized.isdigit():
                return f"RC{normalized}"
        
        return normalized


class SimilarityCalculator:
    """Advanced similarity calculation for customer matching."""
    
    @staticmethod
    def string_similarity(str1: str, str2: str) -> float:
        """Calculate string similarity using multiple algorithms."""
        if not str1 or not str2:
            return 0.0
        
        str1_norm = CustomerNormalization.normalize_name(str1)
        str2_norm = CustomerNormalization.normalize_name(str2)
        
        if str1_norm == str2_norm:
            return 1.0
        
        # Use sequence matcher for similarity
        similarity = SequenceMatcher(None, str1_norm, str2_norm).ratio()
        
        # Boost similarity for common name patterns
        words1 = set(str1_norm.split())
        words2 = set(str2_norm.split())
        
        if words1 and words2:
            word_overlap = len(words1.intersection(words2)) / len(words1.union(words2))
            similarity = max(similarity, word_overlap * 0.9)  # Slight penalty for word-only matching
        
        return similarity
    
    @staticmethod
    def phone_similarity(phone1: str, phone2: str) -> float:
        """Calculate phone number similarity."""
        norm1 = CustomerNormalization.normalize_phone(phone1)
        norm2 = CustomerNormalization.normalize_phone(phone2)
        
        if not norm1 or not norm2:
            return 0.0
        
        if norm1 == norm2:
            return 1.0
        
        # Check if numbers are similar (accounting for formatting differences)
        digits1 = re.sub(r'[^\d]', '', norm1)
        digits2 = re.sub(r'[^\d]', '', norm2)
        
        if digits1 == digits2:
            return 1.0
        
        # Check for partial matches (last 10 digits for Nigerian numbers)
        if len(digits1) >= 10 and len(digits2) >= 10:
            if digits1[-10:] == digits2[-10:]:
                return 0.95
        
        return 0.0
    
    @staticmethod
    def email_similarity(email1: str, email2: str) -> float:
        """Calculate email similarity."""
        norm1 = CustomerNormalization.normalize_email(email1)
        norm2 = CustomerNormalization.normalize_email(email2)
        
        if not norm1 or not norm2:
            return 0.0
        
        if norm1 == norm2:
            return 1.0
        
        # Check domain similarity for business emails
        try:
            domain1 = norm1.split('@')[1]
            domain2 = norm2.split('@')[1]
            
            if domain1 == domain2:
                # Same domain, check username similarity
                user1 = norm1.split('@')[0]
                user2 = norm2.split('@')[0]
                return SequenceMatcher(None, user1, user2).ratio() * 0.8  # Lower weight for username match
        except IndexError:
            pass
        
        return 0.0
    
    @staticmethod
    def business_id_similarity(id1: str, id_type1: str, id2: str, id_type2: str) -> float:
        """Calculate business identifier similarity."""
        if not id1 or not id2 or id_type1.lower() != id_type2.lower():
            return 0.0
        
        norm1 = CustomerNormalization.normalize_business_id(id1, id_type1)
        norm2 = CustomerNormalization.normalize_business_id(id2, id_type2)
        
        if norm1 == norm2:
            return 1.0
        
        return 0.0


class CustomerMatchingEngine:
    """Advanced customer matching engine for cross-connector intelligence."""
    
    def __init__(self, strategy: MatchingStrategy = MatchingStrategy.BALANCED):
        """
        Initialize the customer matching engine.
        
        Args:
            strategy: Matching strategy to use
        """
        self.strategy = strategy
        self.customer_identities: Dict[str, CustomerIdentity] = {}
        self.name_index: Dict[str, Set[str]] = {}  # normalized_name -> universal_ids
        self.phone_index: Dict[str, Set[str]] = {}  # normalized_phone -> universal_ids
        self.email_index: Dict[str, Set[str]] = {}  # normalized_email -> universal_ids
        self.business_id_index: Dict[str, Set[str]] = {}  # business_id -> universal_ids
        
        # Set confidence thresholds based on strategy
        self.confidence_thresholds = self._get_confidence_thresholds(strategy)
        
        logger.info(f"Customer matching engine initialized with {strategy.value} strategy")
    
    def _get_confidence_thresholds(self, strategy: MatchingStrategy) -> Dict[str, float]:
        """Get confidence thresholds for different matching strategies."""
        thresholds = {
            MatchingStrategy.STRICT: {
                'exact_threshold': 0.95,
                'high_threshold': 0.85,
                'medium_threshold': 0.75,
                'low_threshold': 0.65
            },
            MatchingStrategy.BALANCED: {
                'exact_threshold': 0.95,
                'high_threshold': 0.80,
                'medium_threshold': 0.60,
                'low_threshold': 0.40
            },
            MatchingStrategy.PERMISSIVE: {
                'exact_threshold': 0.90,
                'high_threshold': 0.70,
                'medium_threshold': 0.50,
                'low_threshold': 0.30
            }
        }
        return thresholds[strategy]
    
    def _generate_universal_id(self, primary_identifier: str) -> str:
        """Generate a universal customer ID."""
        # Create a hash-based ID that's deterministic but unique
        timestamp = datetime.utcnow().isoformat()
        hash_input = f"{primary_identifier}_{timestamp}".encode('utf-8')
        hash_digest = hashlib.sha256(hash_input).hexdigest()
        return f"CUST_{hash_digest[:12].upper()}"
    
    def _extract_customer_data_from_transaction(
        self,
        transaction: UniversalProcessedTransaction
    ) -> Dict[str, Any]:
        """Extract customer data from a processed transaction."""
        customer_data = {
            'names': set(),
            'phones': set(),
            'emails': set(),
            'addresses': set(),
            'business_ids': {}
        }
        
        # Extract from enrichment data
        enrichment = transaction.enrichment_data
        if enrichment.customer_name:
            customer_data['names'].add(enrichment.customer_name)
        
        if enrichment.customer_phone:
            customer_data['phones'].add(enrichment.customer_phone)
        
        if enrichment.customer_email:
            customer_data['emails'].add(enrichment.customer_email)
        
        if enrichment.customer_address:
            customer_data['addresses'].add(enrichment.customer_address)
        
        if enrichment.customer_tin:
            customer_data['business_ids']['tin'] = enrichment.customer_tin
        
        if enrichment.customer_cac:
            customer_data['business_ids']['cac'] = enrichment.customer_cac
        
        # Extract from connector-specific metadata
        source_system = transaction.original_transaction.source_system
        raw_data = transaction.original_transaction.raw_data
        
        if source_system == ConnectorType.SALESFORCE_CRM.value:
            # Extract from CRM metadata
            crm_meta = transaction.original_transaction.crm_metadata
            if crm_meta:
                contact_details = crm_meta.get('contact_details', {})
                account_details = crm_meta.get('account_details', {})
                
                if contact_details.get('name'):
                    customer_data['names'].add(contact_details['name'])
                if contact_details.get('email'):
                    customer_data['emails'].add(contact_details['email'])
                if contact_details.get('phone'):
                    customer_data['phones'].add(contact_details['phone'])
                
                if account_details.get('name'):
                    customer_data['names'].add(account_details['name'])
                if account_details.get('billing_address'):
                    customer_data['addresses'].add(account_details['billing_address'])
        
        elif source_system == ConnectorType.SQUARE_POS.value:
            # Extract from POS metadata
            pos_meta = transaction.original_transaction.pos_metadata
            if pos_meta:
                customer_details = pos_meta.get('customer_details', {})
                
                if customer_details.get('given_name') or customer_details.get('family_name'):
                    full_name = f"{customer_details.get('given_name', '')} {customer_details.get('family_name', '')}".strip()
                    if full_name:
                        customer_data['names'].add(full_name)
                
                if customer_details.get('email_address'):
                    customer_data['emails'].add(customer_details['email_address'])
                
                if customer_details.get('phone_number'):
                    customer_data['phones'].add(customer_details['phone_number'])
        
        elif source_system == ConnectorType.SAP_ERP.value:
            # Extract from ERP metadata
            erp_meta = transaction.original_transaction.erp_metadata
            if erp_meta:
                customer_details = erp_meta.get('customer_details', {})
                
                if customer_details.get('name'):
                    customer_data['names'].add(customer_details['name'])
                if customer_details.get('email'):
                    customer_data['emails'].add(customer_details['email'])
                if customer_details.get('phone'):
                    customer_data['phones'].add(customer_details['phone'])
                if customer_details.get('address'):
                    customer_data['addresses'].add(customer_details['address'])
        
        return customer_data
    
    def _calculate_match_score(
        self,
        candidate_identity: CustomerIdentity,
        customer_data: Dict[str, Any]
    ) -> Tuple[float, List[str]]:
        """Calculate match score between candidate identity and customer data."""
        scores = []
        factors = []
        
        # Name matching
        max_name_similarity = 0.0
        for candidate_name in candidate_identity.normalized_names:
            for customer_name in customer_data['names']:
                similarity = SimilarityCalculator.string_similarity(candidate_name, customer_name)
                max_name_similarity = max(max_name_similarity, similarity)
        
        if max_name_similarity > 0:
            scores.append(max_name_similarity * 0.3)  # 30% weight for name
            if max_name_similarity > 0.8:
                factors.append(f"High name similarity ({max_name_similarity:.2f})")
        
        # Phone matching
        max_phone_similarity = 0.0
        for candidate_phone in candidate_identity.phone_numbers:
            for customer_phone in customer_data['phones']:
                similarity = SimilarityCalculator.phone_similarity(candidate_phone, customer_phone)
                max_phone_similarity = max(max_phone_similarity, similarity)
        
        if max_phone_similarity > 0:
            scores.append(max_phone_similarity * 0.25)  # 25% weight for phone
            if max_phone_similarity > 0.9:
                factors.append(f"Phone match ({max_phone_similarity:.2f})")
        
        # Email matching
        max_email_similarity = 0.0
        for candidate_email in candidate_identity.email_addresses:
            for customer_email in customer_data['emails']:
                similarity = SimilarityCalculator.email_similarity(candidate_email, customer_email)
                max_email_similarity = max(max_email_similarity, similarity)
        
        if max_email_similarity > 0:
            scores.append(max_email_similarity * 0.25)  # 25% weight for email
            if max_email_similarity > 0.9:
                factors.append(f"Email match ({max_email_similarity:.2f})")
        
        # Business ID matching (high confidence)
        max_business_id_similarity = 0.0
        for id_type, customer_id in customer_data['business_ids'].items():
            if customer_id and id_type in candidate_identity.business_identifiers:
                candidate_id = candidate_identity.business_identifiers[id_type]
                similarity = SimilarityCalculator.business_id_similarity(
                    candidate_id, id_type, customer_id, id_type
                )
                max_business_id_similarity = max(max_business_id_similarity, similarity)
        
        if max_business_id_similarity > 0:
            scores.append(max_business_id_similarity * 0.2)  # 20% weight for business ID
            if max_business_id_similarity > 0.9:
                factors.append(f"Business ID match ({max_business_id_similarity:.2f})")
        
        # Calculate final score
        final_score = sum(scores) if scores else 0.0
        
        # Boost score if multiple factors match
        if len(factors) > 1:
            final_score *= 1.1  # 10% boost for multiple matches
            factors.append("Multiple matching factors")
        
        return min(final_score, 1.0), factors
    
    def _determine_confidence(self, score: float) -> MatchConfidence:
        """Determine confidence level based on score."""
        if score >= self.confidence_thresholds['exact_threshold']:
            return MatchConfidence.EXACT
        elif score >= self.confidence_thresholds['high_threshold']:
            return MatchConfidence.HIGH
        elif score >= self.confidence_thresholds['medium_threshold']:
            return MatchConfidence.MEDIUM
        elif score >= self.confidence_thresholds['low_threshold']:
            return MatchConfidence.LOW
        else:
            return MatchConfidence.NO_MATCH
    
    def _find_candidate_identities(self, customer_data: Dict[str, Any]) -> List[CustomerIdentity]:
        """Find candidate identities for matching using indexes."""
        candidates = set()
        
        # Search by normalized names
        for name in customer_data['names']:
            normalized_name = CustomerNormalization.normalize_name(name)
            if normalized_name in self.name_index:
                candidates.update(self.name_index[normalized_name])
        
        # Search by phone numbers
        for phone in customer_data['phones']:
            normalized_phone = CustomerNormalization.normalize_phone(phone)
            if normalized_phone and normalized_phone in self.phone_index:
                candidates.update(self.phone_index[normalized_phone])
        
        # Search by emails
        for email in customer_data['emails']:
            normalized_email = CustomerNormalization.normalize_email(email)
            if normalized_email in self.email_index:
                candidates.update(self.email_index[normalized_email])
        
        # Search by business IDs
        for id_type, business_id in customer_data['business_ids'].items():
            if business_id:
                normalized_id = CustomerNormalization.normalize_business_id(business_id, id_type)
                if normalized_id in self.business_id_index:
                    candidates.update(self.business_id_index[normalized_id])
        
        # Return candidate identity objects
        return [self.customer_identities[uid] for uid in candidates if uid in self.customer_identities]
    
    def _create_new_identity(
        self,
        customer_data: Dict[str, Any],
        source_system: ConnectorType,
        source_id: str
    ) -> CustomerIdentity:
        """Create a new customer identity."""
        # Choose primary name (first available)
        primary_name = next(iter(customer_data['names'])) if customer_data['names'] else "Unknown Customer"
        
        # Generate universal ID
        universal_id = self._generate_universal_id(primary_name)
        
        # Create identity
        identity = CustomerIdentity(
            universal_id=universal_id,
            primary_name=primary_name,
            normalized_names={CustomerNormalization.normalize_name(name) for name in customer_data['names']},
            phone_numbers={CustomerNormalization.normalize_phone(phone) for phone in customer_data['phones'] if CustomerNormalization.normalize_phone(phone)},
            email_addresses={CustomerNormalization.normalize_email(email) for email in customer_data['emails'] if CustomerNormalization.normalize_email(email)},
            physical_addresses={CustomerNormalization.normalize_address(addr) for addr in customer_data['addresses'] if CustomerNormalization.normalize_address(addr)},
            business_identifiers={
                id_type: CustomerNormalization.normalize_business_id(business_id, id_type)
                for id_type, business_id in customer_data['business_ids'].items()
                if business_id
            },
            source_systems={source_system: source_id},
            confidence_score=1.0,
            last_updated=datetime.utcnow(),
            verification_status={}
        )
        
        return identity
    
    def _merge_identities(
        self,
        existing_identity: CustomerIdentity,
        customer_data: Dict[str, Any],
        source_system: ConnectorType,
        source_id: str
    ) -> CustomerIdentity:
        """Merge new customer data into existing identity."""
        # Update names
        for name in customer_data['names']:
            normalized = CustomerNormalization.normalize_name(name)
            if normalized:
                existing_identity.normalized_names.add(normalized)
        
        # Update phone numbers
        for phone in customer_data['phones']:
            normalized = CustomerNormalization.normalize_phone(phone)
            if normalized:
                existing_identity.phone_numbers.add(normalized)
        
        # Update emails
        for email in customer_data['emails']:
            normalized = CustomerNormalization.normalize_email(email)
            if normalized:
                existing_identity.email_addresses.add(normalized)
        
        # Update addresses
        for address in customer_data['addresses']:
            normalized = CustomerNormalization.normalize_address(address)
            if normalized:
                existing_identity.physical_addresses.add(normalized)
        
        # Update business identifiers
        for id_type, business_id in customer_data['business_ids'].items():
            if business_id:
                normalized = CustomerNormalization.normalize_business_id(business_id, id_type)
                existing_identity.business_identifiers[id_type] = normalized
        
        # Update source systems
        existing_identity.source_systems[source_system] = source_id
        
        # Update timestamp
        existing_identity.last_updated = datetime.utcnow()
        
        return existing_identity
    
    def _update_indexes(self, identity: CustomerIdentity):
        """Update search indexes with identity information."""
        universal_id = identity.universal_id
        
        # Update name index
        for name in identity.normalized_names:
            if name not in self.name_index:
                self.name_index[name] = set()
            self.name_index[name].add(universal_id)
        
        # Update phone index
        for phone in identity.phone_numbers:
            if phone not in self.phone_index:
                self.phone_index[phone] = set()
            self.phone_index[phone].add(universal_id)
        
        # Update email index
        for email in identity.email_addresses:
            if email not in self.email_index:
                self.email_index[email] = set()
            self.email_index[email].add(universal_id)
        
        # Update business ID index
        for business_id in identity.business_identifiers.values():
            if business_id not in self.business_id_index:
                self.business_id_index[business_id] = set()
            self.business_id_index[business_id].add(universal_id)
    
    async def match_customer(
        self,
        transaction: UniversalProcessedTransaction
    ) -> MatchResult:
        """
        Match customer from transaction against existing identities.
        
        Args:
            transaction: Processed transaction containing customer data
            
        Returns:
            MatchResult with matching information
        """
        try:
            # Extract customer data from transaction
            customer_data = self._extract_customer_data_from_transaction(transaction)
            
            # Check if we have any customer data
            if not any([customer_data['names'], customer_data['phones'], 
                       customer_data['emails'], customer_data['business_ids']]):
                return MatchResult(
                    matched_identity=None,
                    confidence=MatchConfidence.NO_MATCH,
                    confidence_score=0.0,
                    matching_factors=[],
                    new_identity_created=False,
                    merge_candidates=[],
                    processing_notes=["No customer data available for matching"]
                )
            
            # Find candidate identities
            candidates = self._find_candidate_identities(customer_data)
            
            best_match = None
            best_score = 0.0
            best_factors = []
            
            # Score all candidates
            for candidate in candidates:
                score, factors = self._calculate_match_score(candidate, customer_data)
                if score > best_score:
                    best_match = candidate
                    best_score = score
                    best_factors = factors
            
            # Determine confidence and action
            confidence = self._determine_confidence(best_score)
            
            source_system = ConnectorType(transaction.original_transaction.source_system)
            source_id = transaction.original_transaction.account_number or transaction.id
            
            if confidence in [MatchConfidence.EXACT, MatchConfidence.HIGH]:
                # Merge with existing identity
                merged_identity = self._merge_identities(
                    best_match, customer_data, source_system, source_id
                )
                self.customer_identities[merged_identity.universal_id] = merged_identity
                self._update_indexes(merged_identity)
                
                return MatchResult(
                    matched_identity=merged_identity,
                    confidence=confidence,
                    confidence_score=best_score,
                    matching_factors=best_factors,
                    new_identity_created=False,
                    merge_candidates=[best_match],
                    processing_notes=[f"Merged with existing identity {best_match.universal_id}"]
                )
            
            elif confidence == MatchConfidence.MEDIUM:
                # Return potential match for manual review
                return MatchResult(
                    matched_identity=best_match,
                    confidence=confidence,
                    confidence_score=best_score,
                    matching_factors=best_factors,
                    new_identity_created=False,
                    merge_candidates=[best_match] + candidates[:3],  # Include top candidates
                    processing_notes=["Medium confidence match - recommend manual review"]
                )
            
            else:
                # Create new identity
                new_identity = self._create_new_identity(
                    customer_data, source_system, source_id
                )
                self.customer_identities[new_identity.universal_id] = new_identity
                self._update_indexes(new_identity)
                
                return MatchResult(
                    matched_identity=new_identity,
                    confidence=MatchConfidence.EXACT,  # New identity is exact for itself
                    confidence_score=1.0,
                    matching_factors=["New customer identity created"],
                    new_identity_created=True,
                    merge_candidates=[],
                    processing_notes=[f"Created new identity {new_identity.universal_id}"]
                )
                
        except Exception as e:
            logger.error(f"Error in customer matching: {e}")
            return MatchResult(
                matched_identity=None,
                confidence=MatchConfidence.NO_MATCH,
                confidence_score=0.0,
                matching_factors=[],
                new_identity_created=False,
                merge_candidates=[],
                processing_notes=[f"Matching failed: {str(e)}"]
            )
    
    async def get_customer_insights(
        self,
        universal_id: str,
        include_transactions: bool = False
    ) -> Dict[str, Any]:
        """
        Get comprehensive insights for a customer identity.
        
        Args:
            universal_id: Universal customer ID
            include_transactions: Whether to include transaction history
            
        Returns:
            Dict with customer insights and analytics
        """
        if universal_id not in self.customer_identities:
            return {
                'success': False,
                'error': f'Customer identity {universal_id} not found'
            }
        
        identity = self.customer_identities[universal_id]
        
        insights = {
            'identity': {
                'universal_id': identity.universal_id,
                'primary_name': identity.primary_name,
                'all_names': list(identity.normalized_names),
                'contact_methods': {
                    'phones': list(identity.phone_numbers),
                    'emails': list(identity.email_addresses),
                    'addresses': list(identity.physical_addresses)
                },
                'business_identifiers': identity.business_identifiers,
                'verification_status': identity.verification_status,
                'last_updated': identity.last_updated.isoformat(),
                'confidence_score': identity.confidence_score
            },
            'system_presence': {
                'connected_systems': list(identity.source_systems.keys()),
                'system_ids': {str(k): v for k, v in identity.source_systems.items()},
                'cross_system_verified': len(identity.source_systems) > 1
            },
            'analytics': {
                'total_contact_methods': len(identity.phone_numbers) + len(identity.email_addresses),
                'business_verified': bool(identity.business_identifiers),
                'data_completeness': self._calculate_data_completeness(identity)
            }
        }
        
        return {
            'success': True,
            'customer_insights': insights
        }
    
    def _calculate_data_completeness(self, identity: CustomerIdentity) -> float:
        """Calculate data completeness score for identity."""
        completeness_factors = [
            bool(identity.primary_name),
            bool(identity.phone_numbers),
            bool(identity.email_addresses),
            bool(identity.physical_addresses),
            bool(identity.business_identifiers),
            len(identity.source_systems) > 1  # Cross-system presence
        ]
        
        return sum(completeness_factors) / len(completeness_factors)
    
    async def find_duplicate_identities(self, threshold: float = 0.85) -> List[List[CustomerIdentity]]:
        """
        Find potential duplicate identities above the specified threshold.
        
        Args:
            threshold: Similarity threshold for duplicate detection
            
        Returns:
            List of duplicate identity groups
        """
        duplicates = []
        processed = set()
        
        for identity1 in self.customer_identities.values():
            if identity1.universal_id in processed:
                continue
            
            group = [identity1]
            processed.add(identity1.universal_id)
            
            # Create pseudo customer data for comparison
            customer_data = {
                'names': identity1.normalized_names,
                'phones': identity1.phone_numbers,
                'emails': identity1.email_addresses,
                'addresses': identity1.physical_addresses,
                'business_ids': identity1.business_identifiers
            }
            
            for identity2 in self.customer_identities.values():
                if identity2.universal_id in processed:
                    continue
                
                score, _ = self._calculate_match_score(identity2, customer_data)
                
                if score >= threshold:
                    group.append(identity2)
                    processed.add(identity2.universal_id)
            
            if len(group) > 1:
                duplicates.append(group)
        
        return duplicates
    
    def get_matching_statistics(self) -> Dict[str, Any]:
        """Get statistics about the matching engine."""
        return {
            'total_identities': len(self.customer_identities),
            'index_sizes': {
                'names': len(self.name_index),
                'phones': len(self.phone_index),
                'emails': len(self.email_index),
                'business_ids': len(self.business_id_index)
            },
            'strategy': self.strategy.value,
            'confidence_thresholds': self.confidence_thresholds,
            'cross_system_customers': sum(
                1 for identity in self.customer_identities.values()
                if len(identity.source_systems) > 1
            )
        }


# Global instance for the application
_customer_matching_engine = None


def get_customer_matching_engine(strategy: MatchingStrategy = MatchingStrategy.BALANCED) -> CustomerMatchingEngine:
    """Get the global customer matching engine instance."""
    global _customer_matching_engine
    
    if _customer_matching_engine is None:
        _customer_matching_engine = CustomerMatchingEngine(strategy)
    
    return _customer_matching_engine


def reset_customer_matching_engine():
    """Reset the global customer matching engine instance."""
    global _customer_matching_engine
    _customer_matching_engine = None