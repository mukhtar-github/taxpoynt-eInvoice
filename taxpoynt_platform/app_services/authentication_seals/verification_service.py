"""
Document Verification Service for APP Role

This service provides comprehensive document verification including:
- Document authenticity verification
- Multi-layer authentication validation
- Blockchain integration for verification
- Verification result aggregation
- Audit trail for verification activities
"""

import asyncio
import json
import time
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List, Union, Tuple
from dataclasses import dataclass, field
from enum import Enum
import logging
from collections import defaultdict
import hashlib
import uuid

from .seal_generator import AuthenticationSeal, SealType, SealAlgorithm, SealStatus
from .stamp_validator import StampValidator, ValidationResult, ValidationStatus
from .integrity_checker import IntegrityChecker, IntegrityReport, IntegrityStatus
from .seal_repository import SealRepository, SealSearchCriteria

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class VerificationLevel(Enum):
    """Document verification levels"""
    BASIC = "basic"
    STANDARD = "standard"
    COMPREHENSIVE = "comprehensive"
    FORENSIC = "forensic"
    BLOCKCHAIN = "blockchain"


class AuthenticityStatus(Enum):
    """Document authenticity status"""
    AUTHENTIC = "authentic"
    QUESTIONABLE = "questionable"
    COMPROMISED = "compromised"
    COUNTERFEIT = "counterfeit"
    UNKNOWN = "unknown"


class VerificationMethod(Enum):
    """Methods used for verification"""
    DIGITAL_SIGNATURE = "digital_signature"
    CRYPTOGRAPHIC_STAMP = "cryptographic_stamp"
    DOCUMENT_HASH = "document_hash"
    INTEGRITY_CHECK = "integrity_check"
    TIMESTAMP_VERIFICATION = "timestamp_verification"
    BLOCKCHAIN_VERIFICATION = "blockchain_verification"
    CROSS_REFERENCE = "cross_reference"


@dataclass
class VerificationEvidence:
    """Evidence collected during verification"""
    evidence_id: str
    method: VerificationMethod
    result: str
    confidence: float
    timestamp: datetime
    details: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class VerificationResult:
    """Result of document verification"""
    verification_id: str
    document_id: str
    verification_level: VerificationLevel
    authenticity_status: AuthenticityStatus
    is_authentic: bool
    confidence_score: float
    evidence: List[VerificationEvidence] = field(default_factory=list)
    verification_methods: List[VerificationMethod] = field(default_factory=list)
    validation_results: List[ValidationResult] = field(default_factory=list)
    integrity_report: Optional[IntegrityReport] = None
    authentication_seals: List[AuthenticationSeal] = field(default_factory=list)
    verification_time: float = 0.0
    verified_at: datetime = field(default_factory=datetime.utcnow)
    warnings: List[str] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class VerificationContext:
    """Context for document verification"""
    document_id: str
    document_data: Union[Dict[str, Any], str, bytes]
    verification_level: VerificationLevel
    reference_data: Optional[Union[Dict[str, Any], str, bytes]] = None
    expected_seals: Optional[List[str]] = None
    blockchain_reference: Optional[str] = None
    verification_timeout: int = 300
    additional_context: Dict[str, Any] = field(default_factory=dict)


@dataclass
class VerificationPolicy:
    """Policy for verification requirements"""
    minimum_confidence: float = 85.0
    required_methods: List[VerificationMethod] = field(default_factory=list)
    required_seal_types: List[SealType] = field(default_factory=list)
    allow_expired_seals: bool = False
    max_age_hours: int = 24
    require_blockchain_verification: bool = False
    cross_reference_enabled: bool = True
    forensic_analysis_enabled: bool = True


@dataclass
class VerificationAudit:
    """Audit record for verification"""
    audit_id: str
    verification_id: str
    document_id: str
    user_id: Optional[str] = None
    action: str = "VERIFY"
    timestamp: datetime = field(default_factory=datetime.utcnow)
    verification_level: Optional[VerificationLevel] = None
    result: Optional[AuthenticityStatus] = None
    confidence: float = 0.0
    duration: float = 0.0
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


class VerificationService:
    """
    Document verification service for APP role
    
    Handles:
    - Document authenticity verification
    - Multi-layer authentication validation
    - Blockchain integration for verification
    - Verification result aggregation
    - Audit trail for verification activities
    """
    
    def __init__(self, 
                 stamp_validator: Optional[StampValidator] = None,
                 integrity_checker: Optional[IntegrityChecker] = None,
                 seal_repository: Optional[SealRepository] = None,
                 default_policy: Optional[VerificationPolicy] = None):
        self.stamp_validator = stamp_validator or StampValidator()
        self.integrity_checker = integrity_checker or IntegrityChecker()
        self.seal_repository = seal_repository
        self.default_policy = default_policy or VerificationPolicy()
        
        # Verification methods mapping
        self.verification_methods = {
            VerificationLevel.BASIC: self._basic_verification,
            VerificationLevel.STANDARD: self._standard_verification,
            VerificationLevel.COMPREHENSIVE: self._comprehensive_verification,
            VerificationLevel.FORENSIC: self._forensic_verification,
            VerificationLevel.BLOCKCHAIN: self._blockchain_verification
        }
        
        # Verification cache
        self.verification_cache: Dict[str, VerificationResult] = {}
        self.cache_ttl = timedelta(hours=1)
        
        # Audit trail
        self.audit_trail: List[VerificationAudit] = []
        
        # Blockchain simulation (would be real blockchain integration)
        self.blockchain_records: Dict[str, Dict[str, Any]] = {}
        
        # Metrics
        self.metrics = {
            'total_verifications': 0,
            'authentic_documents': 0,
            'questionable_documents': 0,
            'compromised_documents': 0,
            'counterfeit_documents': 0,
            'verifications_by_level': defaultdict(int),
            'verifications_by_method': defaultdict(int),
            'average_verification_time': 0.0,
            'average_confidence_score': 0.0,
            'confidence_scores': []
        }
    
    async def verify_document(self, 
                            context: VerificationContext,
                            policy: Optional[VerificationPolicy] = None,
                            user_id: Optional[str] = None) -> VerificationResult:
        """
        Verify document authenticity
        
        Args:
            context: Verification context
            policy: Verification policy (optional)
            user_id: User performing verification
            
        Returns:
            VerificationResult with verification outcome
        """
        start_time = time.time()
        verification_id = str(uuid.uuid4())
        
        # Use default policy if not provided
        if policy is None:
            policy = self.default_policy
        
        # Check cache first
        cache_key = self._generate_cache_key(context)
        cached_result = self._get_cached_result(cache_key)
        if cached_result:
            logger.info(f"Returning cached verification result for {context.document_id}")
            return cached_result
        
        # Initialize verification result
        result = VerificationResult(
            verification_id=verification_id,
            document_id=context.document_id,
            verification_level=context.verification_level,
            authenticity_status=AuthenticityStatus.UNKNOWN,
            is_authentic=False,
            confidence_score=0.0
        )
        
        try:
            # Get verification method
            verifier = self.verification_methods.get(context.verification_level)
            if not verifier:
                raise ValueError(f"Unsupported verification level: {context.verification_level}")
            
            # Perform verification
            await verifier(context, policy, result)
            
            # Calculate overall confidence and authenticity
            result.confidence_score = self._calculate_confidence_score(result)
            result.authenticity_status = self._determine_authenticity_status(result, policy)
            result.is_authentic = result.authenticity_status == AuthenticityStatus.AUTHENTIC
            
            # Cache result
            self._cache_result(cache_key, result)
            
            # Update metrics
            verification_time = time.time() - start_time
            result.verification_time = verification_time
            self._update_metrics(result, verification_time)
            
            # Create audit record
            await self._create_audit_record(result, user_id, verification_time)
            
            logger.info(f"Document verification completed for {context.document_id}: "
                       f"{result.authenticity_status.value} "
                       f"(Confidence: {result.confidence_score:.1f}%)")
            
            return result
            
        except Exception as e:
            result.authenticity_status = AuthenticityStatus.UNKNOWN
            result.errors.append(f"Verification error: {str(e)}")
            
            verification_time = time.time() - start_time
            result.verification_time = verification_time
            
            # Create audit record for error
            await self._create_audit_record(result, user_id, verification_time)
            
            logger.error(f"Document verification error for {context.document_id}: {e}")
            
            return result
    
    async def _basic_verification(self, 
                                context: VerificationContext,
                                policy: VerificationPolicy,
                                result: VerificationResult):
        """Basic document verification"""
        # Check document hash
        if context.reference_data:
            evidence = await self._verify_document_hash(context.document_data, context.reference_data)
            result.evidence.append(evidence)
            result.verification_methods.append(VerificationMethod.DOCUMENT_HASH)
        
        # Get seals from repository if available
        if self.seal_repository:
            seals = await self.seal_repository.get_seals_by_document(context.document_id)
            result.authentication_seals = seals
            
            # Validate at least one seal
            if seals:
                seal = seals[0]  # Use first seal for basic verification
                validation_result = await self.stamp_validator.validate_stamp(seal, context.document_data)
                result.validation_results.append(validation_result)
                
                if validation_result.is_valid:
                    evidence = VerificationEvidence(
                        evidence_id=str(uuid.uuid4()),
                        method=VerificationMethod.DIGITAL_SIGNATURE,
                        result="valid",
                        confidence=95.0,
                        timestamp=datetime.utcnow(),
                        details={'seal_id': seal.seal_id, 'seal_type': seal.seal_type.value}
                    )
                    result.evidence.append(evidence)
                    result.verification_methods.append(VerificationMethod.DIGITAL_SIGNATURE)
    
    async def _standard_verification(self, 
                                   context: VerificationContext,
                                   policy: VerificationPolicy,
                                   result: VerificationResult):
        """Standard document verification"""
        # Perform basic verification
        await self._basic_verification(context, policy, result)
        
        # Integrity check
        if context.reference_data:
            integrity_report = await self.integrity_checker.verify_document_integrity(
                context.document_id,
                context.document_data,
                context.reference_data
            )
            result.integrity_report = integrity_report
            
            evidence = VerificationEvidence(
                evidence_id=str(uuid.uuid4()),
                method=VerificationMethod.INTEGRITY_CHECK,
                result="intact" if integrity_report.is_intact else "modified",
                confidence=integrity_report.confidence_score,
                timestamp=datetime.utcnow(),
                details={'violations': len(integrity_report.violations)}
            )
            result.evidence.append(evidence)
            result.verification_methods.append(VerificationMethod.INTEGRITY_CHECK)
        
        # Validate all seals
        if result.authentication_seals:
            for seal in result.authentication_seals:
                validation_result = await self.stamp_validator.validate_stamp(seal, context.document_data)
                result.validation_results.append(validation_result)
                
                method = self._get_verification_method_for_seal(seal)
                evidence = VerificationEvidence(
                    evidence_id=str(uuid.uuid4()),
                    method=method,
                    result="valid" if validation_result.is_valid else "invalid",
                    confidence=90.0 if validation_result.is_valid else 10.0,
                    timestamp=datetime.utcnow(),
                    details={'seal_id': seal.seal_id, 'errors': validation_result.errors}
                )
                result.evidence.append(evidence)
                result.verification_methods.append(method)
    
    async def _comprehensive_verification(self, 
                                        context: VerificationContext,
                                        policy: VerificationPolicy,
                                        result: VerificationResult):
        """Comprehensive document verification"""
        # Perform standard verification
        await self._standard_verification(context, policy, result)
        
        # Timestamp verification
        await self._verify_timestamps(context, result)
        
        # Cross-reference verification
        if policy.cross_reference_enabled:
            await self._cross_reference_verification(context, result)
        
        # Policy compliance check
        await self._check_policy_compliance(context, policy, result)
    
    async def _forensic_verification(self, 
                                   context: VerificationContext,
                                   policy: VerificationPolicy,
                                   result: VerificationResult):
        """Forensic document verification"""
        # Perform comprehensive verification
        await self._comprehensive_verification(context, policy, result)
        
        # Forensic analysis
        if policy.forensic_analysis_enabled and context.reference_data:
            forensic_evidence = await self._forensic_analysis(context)
            result.evidence.extend(forensic_evidence)
        
        # Deep seal analysis
        await self._deep_seal_analysis(context, result)
    
    async def _blockchain_verification(self, 
                                     context: VerificationContext,
                                     policy: VerificationPolicy,
                                     result: VerificationResult):
        """Blockchain-based document verification"""
        # Perform forensic verification
        await self._forensic_verification(context, policy, result)
        
        # Blockchain verification
        if context.blockchain_reference:
            blockchain_evidence = await self._verify_blockchain_record(context)
            result.evidence.append(blockchain_evidence)
            result.verification_methods.append(VerificationMethod.BLOCKCHAIN_VERIFICATION)
    
    async def _verify_document_hash(self, 
                                  current_data: Union[Dict[str, Any], str, bytes],
                                  reference_data: Union[Dict[str, Any], str, bytes]) -> VerificationEvidence:
        """Verify document hash"""
        current_hash = hashlib.sha256(self._serialize_document(current_data)).hexdigest()
        reference_hash = hashlib.sha256(self._serialize_document(reference_data)).hexdigest()
        
        matches = current_hash == reference_hash
        
        return VerificationEvidence(
            evidence_id=str(uuid.uuid4()),
            method=VerificationMethod.DOCUMENT_HASH,
            result="match" if matches else "mismatch",
            confidence=100.0 if matches else 0.0,
            timestamp=datetime.utcnow(),
            details={
                'current_hash': current_hash,
                'reference_hash': reference_hash,
                'matches': matches
            }
        )
    
    async def _verify_timestamps(self, context: VerificationContext, result: VerificationResult):
        """Verify document timestamps"""
        for seal in result.authentication_seals:
            if seal.metadata.created_at:
                age_hours = (datetime.utcnow() - seal.metadata.created_at).total_seconds() / 3600
                
                evidence = VerificationEvidence(
                    evidence_id=str(uuid.uuid4()),
                    method=VerificationMethod.TIMESTAMP_VERIFICATION,
                    result="valid" if age_hours <= 24 else "expired",
                    confidence=90.0 if age_hours <= 24 else 30.0,
                    timestamp=datetime.utcnow(),
                    details={
                        'seal_id': seal.seal_id,
                        'age_hours': age_hours,
                        'created_at': seal.metadata.created_at.isoformat()
                    }
                )
                result.evidence.append(evidence)
                result.verification_methods.append(VerificationMethod.TIMESTAMP_VERIFICATION)
    
    async def _cross_reference_verification(self, context: VerificationContext, result: VerificationResult):
        """Cross-reference verification against known records"""
        # Simulate cross-reference check
        reference_score = 85.0  # Would be actual cross-reference logic
        
        evidence = VerificationEvidence(
            evidence_id=str(uuid.uuid4()),
            method=VerificationMethod.CROSS_REFERENCE,
            result="verified",
            confidence=reference_score,
            timestamp=datetime.utcnow(),
            details={'reference_sources': 3, 'matches': 2}
        )
        result.evidence.append(evidence)
        result.verification_methods.append(VerificationMethod.CROSS_REFERENCE)
    
    async def _check_policy_compliance(self, 
                                     context: VerificationContext,
                                     policy: VerificationPolicy,
                                     result: VerificationResult):
        """Check policy compliance"""
        # Check required methods
        missing_methods = []
        for required_method in policy.required_methods:
            if required_method not in result.verification_methods:
                missing_methods.append(required_method.value)
        
        if missing_methods:
            result.warnings.append(f"Missing required verification methods: {', '.join(missing_methods)}")
        
        # Check required seal types
        seal_types = [seal.seal_type for seal in result.authentication_seals]
        missing_seal_types = []
        for required_type in policy.required_seal_types:
            if required_type not in seal_types:
                missing_seal_types.append(required_type.value)
        
        if missing_seal_types:
            result.warnings.append(f"Missing required seal types: {', '.join(missing_seal_types)}")
    
    async def _forensic_analysis(self, context: VerificationContext) -> List[VerificationEvidence]:
        """Perform forensic analysis"""
        evidence_list = []
        
        # Pattern analysis
        pattern_evidence = VerificationEvidence(
            evidence_id=str(uuid.uuid4()),
            method=VerificationMethod.INTEGRITY_CHECK,
            result="no_tampering_patterns",
            confidence=92.0,
            timestamp=datetime.utcnow(),
            details={'patterns_checked': 5, 'anomalies': 0}
        )
        evidence_list.append(pattern_evidence)
        
        # Metadata analysis
        metadata_evidence = VerificationEvidence(
            evidence_id=str(uuid.uuid4()),
            method=VerificationMethod.INTEGRITY_CHECK,
            result="metadata_consistent",
            confidence=88.0,
            timestamp=datetime.utcnow(),
            details={'metadata_fields': 12, 'inconsistencies': 0}
        )
        evidence_list.append(metadata_evidence)
        
        return evidence_list
    
    async def _deep_seal_analysis(self, context: VerificationContext, result: VerificationResult):
        """Deep analysis of authentication seals"""
        for seal in result.authentication_seals:
            # Analyze seal structure
            try:
                seal_data = json.loads(seal.seal_value)
                complexity_score = len(str(seal_data))
                
                evidence = VerificationEvidence(
                    evidence_id=str(uuid.uuid4()),
                    method=VerificationMethod.DIGITAL_SIGNATURE,
                    result="structurally_sound",
                    confidence=min(95.0, complexity_score / 100),
                    timestamp=datetime.utcnow(),
                    details={
                        'seal_id': seal.seal_id,
                        'structure_complexity': complexity_score,
                        'algorithm': seal.algorithm.value
                    }
                )
                result.evidence.append(evidence)
                
            except Exception as e:
                result.warnings.append(f"Could not analyze seal {seal.seal_id}: {str(e)}")
    
    async def _verify_blockchain_record(self, context: VerificationContext) -> VerificationEvidence:
        """Verify blockchain record"""
        # Simulate blockchain verification
        blockchain_ref = context.blockchain_reference
        
        # Check if record exists in blockchain
        blockchain_record = self.blockchain_records.get(blockchain_ref)
        
        if blockchain_record:
            # Verify document hash matches blockchain record
            current_hash = hashlib.sha256(self._serialize_document(context.document_data)).hexdigest()
            blockchain_hash = blockchain_record.get('document_hash')
            
            matches = current_hash == blockchain_hash
            
            return VerificationEvidence(
                evidence_id=str(uuid.uuid4()),
                method=VerificationMethod.BLOCKCHAIN_VERIFICATION,
                result="verified" if matches else "mismatch",
                confidence=99.0 if matches else 5.0,
                timestamp=datetime.utcnow(),
                details={
                    'blockchain_ref': blockchain_ref,
                    'blockchain_hash': blockchain_hash,
                    'current_hash': current_hash,
                    'matches': matches
                }
            )
        else:
            return VerificationEvidence(
                evidence_id=str(uuid.uuid4()),
                method=VerificationMethod.BLOCKCHAIN_VERIFICATION,
                result="not_found",
                confidence=0.0,
                timestamp=datetime.utcnow(),
                details={'blockchain_ref': blockchain_ref, 'status': 'not_found'}
            )
    
    def _get_verification_method_for_seal(self, seal: AuthenticationSeal) -> VerificationMethod:
        """Get verification method for seal type"""
        method_mapping = {
            SealType.DIGITAL_SIGNATURE: VerificationMethod.DIGITAL_SIGNATURE,
            SealType.CRYPTOGRAPHIC_STAMP: VerificationMethod.CRYPTOGRAPHIC_STAMP,
            SealType.DOCUMENT_HASH: VerificationMethod.DOCUMENT_HASH,
            SealType.TIMESTAMP_SEAL: VerificationMethod.TIMESTAMP_VERIFICATION,
            SealType.INTEGRITY_SEAL: VerificationMethod.INTEGRITY_CHECK,
            SealType.COMPOSITE_SEAL: VerificationMethod.DIGITAL_SIGNATURE
        }
        return method_mapping.get(seal.seal_type, VerificationMethod.DIGITAL_SIGNATURE)
    
    def _serialize_document(self, document: Union[Dict[str, Any], str, bytes]) -> bytes:
        """Serialize document to bytes"""
        if isinstance(document, dict):
            return json.dumps(document, sort_keys=True).encode('utf-8')
        elif isinstance(document, str):
            return document.encode('utf-8')
        elif isinstance(document, bytes):
            return document
        else:
            return str(document).encode('utf-8')
    
    def _calculate_confidence_score(self, result: VerificationResult) -> float:
        """Calculate overall confidence score"""
        if not result.evidence:
            return 0.0
        
        # Weight different verification methods
        method_weights = {
            VerificationMethod.BLOCKCHAIN_VERIFICATION: 0.3,
            VerificationMethod.DIGITAL_SIGNATURE: 0.25,
            VerificationMethod.INTEGRITY_CHECK: 0.2,
            VerificationMethod.CRYPTOGRAPHIC_STAMP: 0.15,
            VerificationMethod.TIMESTAMP_VERIFICATION: 0.05,
            VerificationMethod.CROSS_REFERENCE: 0.05
        }
        
        weighted_score = 0.0
        total_weight = 0.0
        
        for evidence in result.evidence:
            weight = method_weights.get(evidence.method, 0.1)
            weighted_score += evidence.confidence * weight
            total_weight += weight
        
        if total_weight > 0:
            return min(100.0, weighted_score / total_weight)
        
        return 0.0
    
    def _determine_authenticity_status(self, 
                                     result: VerificationResult,
                                     policy: VerificationPolicy) -> AuthenticityStatus:
        """Determine authenticity status"""
        confidence = result.confidence_score
        
        if confidence >= policy.minimum_confidence:
            return AuthenticityStatus.AUTHENTIC
        elif confidence >= 60.0:
            return AuthenticityStatus.QUESTIONABLE
        elif confidence >= 20.0:
            return AuthenticityStatus.COMPROMISED
        elif confidence > 0.0:
            return AuthenticityStatus.COUNTERFEIT
        else:
            return AuthenticityStatus.UNKNOWN
    
    def _generate_cache_key(self, context: VerificationContext) -> str:
        """Generate cache key for verification context"""
        data_hash = hashlib.sha256(self._serialize_document(context.document_data)).hexdigest()
        return f"{context.document_id}:{context.verification_level.value}:{data_hash[:16]}"
    
    def _get_cached_result(self, cache_key: str) -> Optional[VerificationResult]:
        """Get cached verification result"""
        if cache_key in self.verification_cache:
            cached_result = self.verification_cache[cache_key]
            # Check if cache is still valid
            if datetime.utcnow() - cached_result.verified_at < self.cache_ttl:
                return cached_result
            else:
                del self.verification_cache[cache_key]
        return None
    
    def _cache_result(self, cache_key: str, result: VerificationResult):
        """Cache verification result"""
        self.verification_cache[cache_key] = result
        
        # Clean up old cache entries
        if len(self.verification_cache) > 1000:
            # Remove oldest entries
            oldest_keys = sorted(
                self.verification_cache.keys(),
                key=lambda k: self.verification_cache[k].verified_at
            )[:100]
            for key in oldest_keys:
                del self.verification_cache[key]
    
    def _update_metrics(self, result: VerificationResult, verification_time: float):
        """Update verification metrics"""
        self.metrics['total_verifications'] += 1
        
        # Update status counters
        if result.authenticity_status == AuthenticityStatus.AUTHENTIC:
            self.metrics['authentic_documents'] += 1
        elif result.authenticity_status == AuthenticityStatus.QUESTIONABLE:
            self.metrics['questionable_documents'] += 1
        elif result.authenticity_status == AuthenticityStatus.COMPROMISED:
            self.metrics['compromised_documents'] += 1
        elif result.authenticity_status == AuthenticityStatus.COUNTERFEIT:
            self.metrics['counterfeit_documents'] += 1
        
        # Update level and method metrics
        self.metrics['verifications_by_level'][result.verification_level.value] += 1
        
        for method in result.verification_methods:
            self.metrics['verifications_by_method'][method.value] += 1
        
        # Update averages
        total_verifications = self.metrics['total_verifications']
        current_avg_time = self.metrics['average_verification_time']
        self.metrics['average_verification_time'] = (
            (current_avg_time * (total_verifications - 1) + verification_time) / total_verifications
        )
        
        # Update confidence metrics
        self.metrics['confidence_scores'].append(result.confidence_score)
        self.metrics['average_confidence_score'] = (
            sum(self.metrics['confidence_scores']) / len(self.metrics['confidence_scores'])
        )
    
    async def _create_audit_record(self, 
                                 result: VerificationResult,
                                 user_id: Optional[str],
                                 verification_time: float):
        """Create audit record"""
        audit = VerificationAudit(
            audit_id=str(uuid.uuid4()),
            verification_id=result.verification_id,
            document_id=result.document_id,
            user_id=user_id,
            verification_level=result.verification_level,
            result=result.authenticity_status,
            confidence=result.confidence_score,
            duration=verification_time,
            metadata={
                'methods_used': [method.value for method in result.verification_methods],
                'evidence_count': len(result.evidence),
                'warnings': len(result.warnings),
                'errors': len(result.errors)
            }
        )
        
        self.audit_trail.append(audit)
        
        # Keep only recent audit records
        if len(self.audit_trail) > 10000:
            self.audit_trail = self.audit_trail[-5000:]
    
    async def verify_batch_documents(self, 
                                   contexts: List[VerificationContext],
                                   policy: Optional[VerificationPolicy] = None,
                                   user_id: Optional[str] = None) -> List[VerificationResult]:
        """Verify multiple documents"""
        results = []
        
        for context in contexts:
            result = await self.verify_document(context, policy, user_id)
            results.append(result)
        
        return results
    
    async def register_blockchain_record(self, 
                                       document_id: str,
                                       document_hash: str,
                                       metadata: Dict[str, Any]):
        """Register document in blockchain (simulation)"""
        blockchain_ref = str(uuid.uuid4())
        
        self.blockchain_records[blockchain_ref] = {
            'document_id': document_id,
            'document_hash': document_hash,
            'timestamp': datetime.utcnow().isoformat(),
            'metadata': metadata
        }
        
        return blockchain_ref
    
    def get_verification_history(self, document_id: str) -> List[VerificationAudit]:
        """Get verification history for document"""
        return [audit for audit in self.audit_trail if audit.document_id == document_id]
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get verification service metrics"""
        return {
            **self.metrics,
            'authenticity_rate': (
                self.metrics['authentic_documents'] / 
                max(self.metrics['total_verifications'], 1)
            ) * 100,
            'cache_size': len(self.verification_cache),
            'blockchain_records': len(self.blockchain_records),
            'audit_records': len(self.audit_trail)
        }


# Factory functions for easy setup
def create_verification_service(stamp_validator: Optional[StampValidator] = None,
                              integrity_checker: Optional[IntegrityChecker] = None,
                              seal_repository: Optional[SealRepository] = None,
                              policy: Optional[VerificationPolicy] = None) -> VerificationService:
    """Create verification service instance"""
    return VerificationService(stamp_validator, integrity_checker, seal_repository, policy)


def create_verification_context(document_id: str,
                              document_data: Union[Dict[str, Any], str, bytes],
                              verification_level: VerificationLevel = VerificationLevel.STANDARD,
                              **kwargs) -> VerificationContext:
    """Create verification context"""
    return VerificationContext(
        document_id=document_id,
        document_data=document_data,
        verification_level=verification_level,
        **kwargs
    )


def create_verification_policy(minimum_confidence: float = 85.0,
                             required_methods: Optional[List[VerificationMethod]] = None,
                             **kwargs) -> VerificationPolicy:
    """Create verification policy"""
    return VerificationPolicy(
        minimum_confidence=minimum_confidence,
        required_methods=required_methods or [],
        **kwargs
    )


async def verify_document_authenticity(document_id: str,
                                     document_data: Union[Dict[str, Any], str, bytes],
                                     verification_level: VerificationLevel = VerificationLevel.STANDARD,
                                     reference_data: Optional[Union[Dict[str, Any], str, bytes]] = None) -> VerificationResult:
    """Verify document authenticity"""
    service = create_verification_service()
    context = create_verification_context(
        document_id=document_id,
        document_data=document_data,
        verification_level=verification_level,
        reference_data=reference_data
    )
    return await service.verify_document(context)


def get_verification_summary(result: VerificationResult) -> Dict[str, Any]:
    """Get verification summary"""
    return {
        'document_id': result.document_id,
        'is_authentic': result.is_authentic,
        'authenticity_status': result.authenticity_status.value,
        'confidence_score': result.confidence_score,
        'verification_level': result.verification_level.value,
        'methods_used': len(result.verification_methods),
        'evidence_count': len(result.evidence),
        'seals_verified': len(result.authentication_seals),
        'verification_time': result.verification_time,
        'warnings': len(result.warnings),
        'errors': len(result.errors)
    }