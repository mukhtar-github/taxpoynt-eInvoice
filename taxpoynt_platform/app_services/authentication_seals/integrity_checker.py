"""
Document Integrity Verification Service for APP Role

This service handles document integrity verification including:
- Document tampering detection
- Structural integrity checks
- Content integrity verification
- Version control integrity
- Multi-level integrity analysis
"""

import hashlib
import json
import time
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List, Union, Tuple, Set
from dataclasses import dataclass, field
from enum import Enum
import logging
from collections import defaultdict
import difflib

from .seal_generator import AuthenticationSeal, SealType, SealAlgorithm
from .stamp_validator import StampValidator, ValidationResult, ValidationStatus

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class IntegrityLevel(Enum):
    """Integrity check levels"""
    BASIC = "basic"
    STANDARD = "standard"
    COMPREHENSIVE = "comprehensive"
    FORENSIC = "forensic"


class IntegrityStatus(Enum):
    """Document integrity status"""
    INTACT = "intact"
    MODIFIED = "modified"
    CORRUPTED = "corrupted"
    TAMPERED = "tampered"
    UNKNOWN = "unknown"


class IntegrityViolation(Enum):
    """Types of integrity violations"""
    HASH_MISMATCH = "hash_mismatch"
    SIZE_MISMATCH = "size_mismatch"
    STRUCTURE_CHANGE = "structure_change"
    CONTENT_MODIFICATION = "content_modification"
    FIELD_ADDITION = "field_addition"
    FIELD_REMOVAL = "field_removal"
    VALUE_CHANGE = "value_change"
    TIMESTAMP_MANIPULATION = "timestamp_manipulation"
    SIGNATURE_INVALID = "signature_invalid"


@dataclass
class IntegrityCheckpoint:
    """Integrity checkpoint for document"""
    checkpoint_id: str
    document_id: str
    document_hash: str
    structure_hash: str
    content_hash: str
    field_count: int
    document_size: int
    created_at: datetime
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class IntegrityViolationDetail:
    """Detail of integrity violation"""
    violation_type: IntegrityViolation
    field_path: str
    expected_value: Optional[str] = None
    actual_value: Optional[str] = None
    severity: str = "medium"
    description: str = ""
    suggestion: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class IntegrityReport:
    """Document integrity verification report"""
    document_id: str
    check_level: IntegrityLevel
    integrity_status: IntegrityStatus
    is_intact: bool
    violations: List[IntegrityViolationDetail] = field(default_factory=list)
    checkpoints_verified: int = 0
    total_checks: int = 0
    passed_checks: int = 0
    failed_checks: int = 0
    confidence_score: float = 0.0
    verification_time: float = 0.0
    verified_at: datetime = field(default_factory=datetime.utcnow)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class IntegrityAnalysis:
    """Integrity analysis results"""
    document_id: str
    original_hash: str
    current_hash: str
    hash_matches: bool
    structure_changes: List[str] = field(default_factory=list)
    content_changes: List[str] = field(default_factory=list)
    added_fields: List[str] = field(default_factory=list)
    removed_fields: List[str] = field(default_factory=list)
    modified_fields: List[str] = field(default_factory=list)
    risk_score: float = 0.0
    analysis_time: float = 0.0
    metadata: Dict[str, Any] = field(default_factory=dict)


class IntegrityChecker:
    """
    Document integrity verification service for APP role
    
    Handles:
    - Document tampering detection
    - Structural integrity checks
    - Content integrity verification
    - Version control integrity
    - Multi-level integrity analysis
    """
    
    def __init__(self, 
                 stamp_validator: Optional[StampValidator] = None,
                 default_check_level: IntegrityLevel = IntegrityLevel.STANDARD):
        self.stamp_validator = stamp_validator or StampValidator()
        self.default_check_level = default_check_level
        
        # Integrity checkpoints storage
        self.checkpoints: Dict[str, List[IntegrityCheckpoint]] = defaultdict(list)
        
        # Integrity rules
        self.integrity_rules = {
            IntegrityLevel.BASIC: self._basic_integrity_check,
            IntegrityLevel.STANDARD: self._standard_integrity_check,
            IntegrityLevel.COMPREHENSIVE: self._comprehensive_integrity_check,
            IntegrityLevel.FORENSIC: self._forensic_integrity_check
        }
        
        # Critical fields that should never change
        self.critical_fields = {
            'document_id',
            'document_type',
            'invoice_number',
            'invoice_date',
            'total_amount',
            'supplier.tin',
            'customer.name'
        }
        
        # Sensitive fields that require special attention
        self.sensitive_fields = {
            'subtotal',
            'tax_amount',
            'vat.amount',
            'wht.amount',
            'supplier.name',
            'customer.address'
        }
        
        # Metrics
        self.metrics = {
            'total_checks': 0,
            'intact_documents': 0,
            'modified_documents': 0,
            'tampered_documents': 0,
            'average_check_time': 0.0,
            'violations_by_type': defaultdict(int),
            'confidence_scores': []
        }
    
    async def verify_document_integrity(self, 
                                      document_id: str,
                                      current_document: Union[Dict[str, Any], str, bytes],
                                      reference_data: Optional[Union[Dict[str, Any], str, bytes]] = None,
                                      authentication_seals: Optional[List[AuthenticationSeal]] = None,
                                      check_level: Optional[IntegrityLevel] = None) -> IntegrityReport:
        """
        Verify document integrity
        
        Args:
            document_id: Document identifier
            current_document: Current document data
            reference_data: Reference document data for comparison
            authentication_seals: Authentication seals to verify
            check_level: Level of integrity checking
            
        Returns:
            IntegrityReport with integrity verification results
        """
        start_time = time.time()
        check_level = check_level or self.default_check_level
        
        # Initialize report
        report = IntegrityReport(
            document_id=document_id,
            check_level=check_level,
            integrity_status=IntegrityStatus.UNKNOWN,
            is_intact=False
        )
        
        try:
            # Get integrity checker for specified level
            checker = self.integrity_rules.get(check_level)
            if not checker:
                raise ValueError(f"Unsupported check level: {check_level}")
            
            # Perform integrity check
            await checker(current_document, reference_data, authentication_seals, report)
            
            # Calculate confidence score
            report.confidence_score = self._calculate_confidence_score(report)
            
            # Determine overall integrity status
            report.integrity_status = self._determine_integrity_status(report)
            report.is_intact = report.integrity_status == IntegrityStatus.INTACT
            
            # Update metrics
            self._update_metrics(report, time.time() - start_time)
            
            logger.info(f"Integrity verification completed for {document_id}: "
                       f"{report.integrity_status.value} "
                       f"(Confidence: {report.confidence_score:.1f}%)")
            
            return report
            
        except Exception as e:
            report.integrity_status = IntegrityStatus.UNKNOWN
            report.violations.append(IntegrityViolationDetail(
                violation_type=IntegrityViolation.HASH_MISMATCH,
                field_path="system",
                description=f"Integrity check error: {str(e)}",
                severity="critical"
            ))
            
            logger.error(f"Integrity verification error for {document_id}: {e}")
            return report
    
    async def _basic_integrity_check(self, 
                                   current_document: Union[Dict[str, Any], str, bytes],
                                   reference_data: Optional[Union[Dict[str, Any], str, bytes]],
                                   authentication_seals: Optional[List[AuthenticationSeal]],
                                   report: IntegrityReport):
        """Basic integrity check"""
        # Check document hash
        current_hash = self._calculate_document_hash(current_document)
        
        # Verify against reference data if provided
        if reference_data:
            reference_hash = self._calculate_document_hash(reference_data)
            report.total_checks += 1
            
            if current_hash == reference_hash:
                report.passed_checks += 1
            else:
                report.failed_checks += 1
                report.violations.append(IntegrityViolationDetail(
                    violation_type=IntegrityViolation.HASH_MISMATCH,
                    field_path="document",
                    expected_value=reference_hash,
                    actual_value=current_hash,
                    severity="high",
                    description="Document hash mismatch - document may have been modified"
                ))
        
        # Verify authentication seals if provided
        if authentication_seals:
            for seal in authentication_seals:
                report.total_checks += 1
                
                # Validate seal
                validation_result = await self.stamp_validator.validate_stamp(seal, current_document)
                
                if validation_result.is_valid:
                    report.passed_checks += 1
                else:
                    report.failed_checks += 1
                    report.violations.append(IntegrityViolationDetail(
                        violation_type=IntegrityViolation.SIGNATURE_INVALID,
                        field_path=f"seal.{seal.seal_id}",
                        description=f"Authentication seal validation failed: {validation_result.errors}",
                        severity="high"
                    ))
    
    async def _standard_integrity_check(self, 
                                      current_document: Union[Dict[str, Any], str, bytes],
                                      reference_data: Optional[Union[Dict[str, Any], str, bytes]],
                                      authentication_seals: Optional[List[AuthenticationSeal]],
                                      report: IntegrityReport):
        """Standard integrity check"""
        # Perform basic checks
        await self._basic_integrity_check(current_document, reference_data, authentication_seals, report)
        
        # Additional standard checks
        if isinstance(current_document, dict):
            # Check document structure
            await self._check_document_structure(current_document, reference_data, report)
            
            # Check critical fields
            await self._check_critical_fields(current_document, reference_data, report)
            
            # Check document size
            await self._check_document_size(current_document, reference_data, report)
    
    async def _comprehensive_integrity_check(self, 
                                           current_document: Union[Dict[str, Any], str, bytes],
                                           reference_data: Optional[Union[Dict[str, Any], str, bytes]],
                                           authentication_seals: Optional[List[AuthenticationSeal]],
                                           report: IntegrityReport):
        """Comprehensive integrity check"""
        # Perform standard checks
        await self._standard_integrity_check(current_document, reference_data, authentication_seals, report)
        
        # Additional comprehensive checks
        if isinstance(current_document, dict):
            # Deep field comparison
            await self._deep_field_comparison(current_document, reference_data, report)
            
            # Check sensitive fields
            await self._check_sensitive_fields(current_document, reference_data, report)
            
            # Check timestamp integrity
            await self._check_timestamp_integrity(current_document, reference_data, report)
            
            # Check nested object integrity
            await self._check_nested_integrity(current_document, reference_data, report)
    
    async def _forensic_integrity_check(self, 
                                      current_document: Union[Dict[str, Any], str, bytes],
                                      reference_data: Optional[Union[Dict[str, Any], str, bytes]],
                                      authentication_seals: Optional[List[AuthenticationSeal]],
                                      report: IntegrityReport):
        """Forensic integrity check"""
        # Perform comprehensive checks
        await self._comprehensive_integrity_check(current_document, reference_data, authentication_seals, report)
        
        # Additional forensic checks
        if isinstance(current_document, dict):
            # Forensic analysis
            await self._forensic_analysis(current_document, reference_data, report)
            
            # Check for tampering patterns
            await self._check_tampering_patterns(current_document, reference_data, report)
            
            # Analyze modification history
            await self._analyze_modification_history(current_document, reference_data, report)
    
    async def _check_document_structure(self, 
                                      current_document: Dict[str, Any],
                                      reference_data: Optional[Union[Dict[str, Any], str, bytes]],
                                      report: IntegrityReport):
        """Check document structure integrity"""
        if not isinstance(reference_data, dict):
            return
        
        # Check field count
        current_fields = self._get_all_field_paths(current_document)
        reference_fields = self._get_all_field_paths(reference_data)
        
        report.total_checks += 1
        
        if len(current_fields) != len(reference_fields):
            report.failed_checks += 1
            
            # Find added/removed fields
            added_fields = current_fields - reference_fields
            removed_fields = reference_fields - current_fields
            
            if added_fields:
                report.violations.append(IntegrityViolationDetail(
                    violation_type=IntegrityViolation.FIELD_ADDITION,
                    field_path="structure",
                    description=f"Fields added: {', '.join(added_fields)}",
                    severity="medium"
                ))
            
            if removed_fields:
                report.violations.append(IntegrityViolationDetail(
                    violation_type=IntegrityViolation.FIELD_REMOVAL,
                    field_path="structure",
                    description=f"Fields removed: {', '.join(removed_fields)}",
                    severity="medium"
                ))
        else:
            report.passed_checks += 1
    
    async def _check_critical_fields(self, 
                                   current_document: Dict[str, Any],
                                   reference_data: Optional[Union[Dict[str, Any], str, bytes]],
                                   report: IntegrityReport):
        """Check critical fields integrity"""
        if not isinstance(reference_data, dict):
            return
        
        for field_path in self.critical_fields:
            report.total_checks += 1
            
            current_value = self._get_nested_value(current_document, field_path)
            reference_value = self._get_nested_value(reference_data, field_path)
            
            if current_value != reference_value:
                report.failed_checks += 1
                report.violations.append(IntegrityViolationDetail(
                    violation_type=IntegrityViolation.VALUE_CHANGE,
                    field_path=field_path,
                    expected_value=str(reference_value),
                    actual_value=str(current_value),
                    severity="critical",
                    description=f"Critical field {field_path} has been modified"
                ))
            else:
                report.passed_checks += 1
    
    async def _check_sensitive_fields(self, 
                                    current_document: Dict[str, Any],
                                    reference_data: Optional[Union[Dict[str, Any], str, bytes]],
                                    report: IntegrityReport):
        """Check sensitive fields integrity"""
        if not isinstance(reference_data, dict):
            return
        
        for field_path in self.sensitive_fields:
            report.total_checks += 1
            
            current_value = self._get_nested_value(current_document, field_path)
            reference_value = self._get_nested_value(reference_data, field_path)
            
            if current_value != reference_value:
                report.failed_checks += 1
                report.violations.append(IntegrityViolationDetail(
                    violation_type=IntegrityViolation.VALUE_CHANGE,
                    field_path=field_path,
                    expected_value=str(reference_value),
                    actual_value=str(current_value),
                    severity="high",
                    description=f"Sensitive field {field_path} has been modified"
                ))
            else:
                report.passed_checks += 1
    
    async def _check_document_size(self, 
                                 current_document: Union[Dict[str, Any], str, bytes],
                                 reference_data: Optional[Union[Dict[str, Any], str, bytes]],
                                 report: IntegrityReport):
        """Check document size integrity"""
        if reference_data is None:
            return
        
        current_size = len(self._serialize_document(current_document))
        reference_size = len(self._serialize_document(reference_data))
        
        report.total_checks += 1
        
        if current_size != reference_size:
            report.failed_checks += 1
            report.violations.append(IntegrityViolationDetail(
                violation_type=IntegrityViolation.SIZE_MISMATCH,
                field_path="document",
                expected_value=str(reference_size),
                actual_value=str(current_size),
                severity="medium",
                description=f"Document size changed from {reference_size} to {current_size} bytes"
            ))
        else:
            report.passed_checks += 1
    
    async def _deep_field_comparison(self, 
                                   current_document: Dict[str, Any],
                                   reference_data: Optional[Union[Dict[str, Any], str, bytes]],
                                   report: IntegrityReport):
        """Deep field comparison"""
        if not isinstance(reference_data, dict):
            return
        
        # Compare all fields
        all_fields = self._get_all_field_paths(current_document) | self._get_all_field_paths(reference_data)
        
        for field_path in all_fields:
            report.total_checks += 1
            
            current_value = self._get_nested_value(current_document, field_path)
            reference_value = self._get_nested_value(reference_data, field_path)
            
            if current_value != reference_value:
                report.failed_checks += 1
                
                # Determine severity based on field type
                severity = "low"
                if field_path in self.critical_fields:
                    severity = "critical"
                elif field_path in self.sensitive_fields:
                    severity = "high"
                elif field_path.endswith(('.amount', '.total', '.price')):
                    severity = "high"
                
                report.violations.append(IntegrityViolationDetail(
                    violation_type=IntegrityViolation.VALUE_CHANGE,
                    field_path=field_path,
                    expected_value=str(reference_value),
                    actual_value=str(current_value),
                    severity=severity,
                    description=f"Field {field_path} value changed"
                ))
            else:
                report.passed_checks += 1
    
    async def _check_timestamp_integrity(self, 
                                       current_document: Dict[str, Any],
                                       reference_data: Optional[Union[Dict[str, Any], str, bytes]],
                                       report: IntegrityReport):
        """Check timestamp integrity"""
        if not isinstance(reference_data, dict):
            return
        
        timestamp_fields = ['invoice_date', 'due_date', 'created_at', 'updated_at']
        
        for field_path in timestamp_fields:
            if field_path in current_document and field_path in reference_data:
                report.total_checks += 1
                
                current_ts = current_document[field_path]
                reference_ts = reference_data[field_path]
                
                if current_ts != reference_ts:
                    report.failed_checks += 1
                    report.violations.append(IntegrityViolationDetail(
                        violation_type=IntegrityViolation.TIMESTAMP_MANIPULATION,
                        field_path=field_path,
                        expected_value=str(reference_ts),
                        actual_value=str(current_ts),
                        severity="high",
                        description=f"Timestamp {field_path} has been modified"
                    ))
                else:
                    report.passed_checks += 1
    
    async def _check_nested_integrity(self, 
                                    current_document: Dict[str, Any],
                                    reference_data: Optional[Union[Dict[str, Any], str, bytes]],
                                    report: IntegrityReport):
        """Check nested object integrity"""
        if not isinstance(reference_data, dict):
            return
        
        # Check nested objects
        nested_objects = ['supplier', 'customer', 'items', 'vat', 'wht']
        
        for obj_name in nested_objects:
            if obj_name in current_document and obj_name in reference_data:
                current_obj = current_document[obj_name]
                reference_obj = reference_data[obj_name]
                
                # Calculate hash for nested object
                current_hash = self._calculate_object_hash(current_obj)
                reference_hash = self._calculate_object_hash(reference_obj)
                
                report.total_checks += 1
                
                if current_hash != reference_hash:
                    report.failed_checks += 1
                    report.violations.append(IntegrityViolationDetail(
                        violation_type=IntegrityViolation.STRUCTURE_CHANGE,
                        field_path=obj_name,
                        expected_value=reference_hash,
                        actual_value=current_hash,
                        severity="medium",
                        description=f"Nested object {obj_name} has been modified"
                    ))
                else:
                    report.passed_checks += 1
    
    async def _forensic_analysis(self, 
                               current_document: Dict[str, Any],
                               reference_data: Optional[Union[Dict[str, Any], str, bytes]],
                               report: IntegrityReport):
        """Forensic analysis of document"""
        if not isinstance(reference_data, dict):
            return
        
        # Analyze modification patterns
        modifications = []
        
        # Check for systematic changes
        current_str = json.dumps(current_document, sort_keys=True)
        reference_str = json.dumps(reference_data, sort_keys=True)
        
        # Use difflib to find differences
        diff = list(difflib.unified_diff(
            reference_str.splitlines(),
            current_str.splitlines(),
            lineterm=''
        ))
        
        if diff:
            report.violations.append(IntegrityViolationDetail(
                violation_type=IntegrityViolation.CONTENT_MODIFICATION,
                field_path="forensic",
                description=f"Forensic analysis detected {len(diff)} modifications",
                severity="medium",
                metadata={'diff_lines': len(diff)}
            ))
    
    async def _check_tampering_patterns(self, 
                                      current_document: Dict[str, Any],
                                      reference_data: Optional[Union[Dict[str, Any], str, bytes]],
                                      report: IntegrityReport):
        """Check for tampering patterns"""
        if not isinstance(reference_data, dict):
            return
        
        # Check for common tampering patterns
        patterns = [
            ('amount_inflation', self._check_amount_inflation),
            ('date_manipulation', self._check_date_manipulation),
            ('entity_substitution', self._check_entity_substitution)
        ]
        
        for pattern_name, pattern_checker in patterns:
            if await pattern_checker(current_document, reference_data):
                report.violations.append(IntegrityViolationDetail(
                    violation_type=IntegrityViolation.TAMPERED,
                    field_path="pattern",
                    description=f"Tampering pattern detected: {pattern_name}",
                    severity="critical"
                ))
    
    async def _analyze_modification_history(self, 
                                          current_document: Dict[str, Any],
                                          reference_data: Optional[Union[Dict[str, Any], str, bytes]],
                                          report: IntegrityReport):
        """Analyze modification history"""
        # This would typically analyze timestamps and modification patterns
        # For now, we'll do a basic analysis
        
        if isinstance(reference_data, dict):
            # Check for modification timestamps
            if 'updated_at' in current_document and 'created_at' in current_document:
                try:
                    created = datetime.fromisoformat(current_document['created_at'].replace('Z', '+00:00'))
                    updated = datetime.fromisoformat(current_document['updated_at'].replace('Z', '+00:00'))
                    
                    if updated < created:
                        report.violations.append(IntegrityViolationDetail(
                            violation_type=IntegrityViolation.TIMESTAMP_MANIPULATION,
                            field_path="timestamps",
                            description="Updated timestamp is before created timestamp",
                            severity="high"
                        ))
                except Exception:
                    pass
    
    async def _check_amount_inflation(self, current_document: Dict[str, Any], reference_data: Dict[str, Any]) -> bool:
        """Check for amount inflation tampering"""
        amount_fields = ['total_amount', 'subtotal', 'tax_amount']
        
        for field in amount_fields:
            current_val = self._get_nested_value(current_document, field)
            reference_val = self._get_nested_value(reference_data, field)
            
            if current_val and reference_val:
                try:
                    current_amount = float(current_val)
                    reference_amount = float(reference_val)
                    
                    # Check for significant increase
                    if current_amount > reference_amount * 1.1:  # 10% increase
                        return True
                except (ValueError, TypeError):
                    pass
        
        return False
    
    async def _check_date_manipulation(self, current_document: Dict[str, Any], reference_data: Dict[str, Any]) -> bool:
        """Check for date manipulation tampering"""
        date_fields = ['invoice_date', 'due_date']
        
        for field in date_fields:
            current_date = self._get_nested_value(current_document, field)
            reference_date = self._get_nested_value(reference_data, field)
            
            if current_date != reference_date:
                return True
        
        return False
    
    async def _check_entity_substitution(self, current_document: Dict[str, Any], reference_data: Dict[str, Any]) -> bool:
        """Check for entity substitution tampering"""
        entity_fields = ['supplier.name', 'supplier.tin', 'customer.name']
        
        for field in entity_fields:
            current_val = self._get_nested_value(current_document, field)
            reference_val = self._get_nested_value(reference_data, field)
            
            if current_val != reference_val:
                return True
        
        return False
    
    def _calculate_document_hash(self, document: Union[Dict[str, Any], str, bytes]) -> str:
        """Calculate document hash"""
        data = self._serialize_document(document)
        return hashlib.sha256(data).hexdigest()
    
    def _calculate_object_hash(self, obj: Any) -> str:
        """Calculate hash for object"""
        if isinstance(obj, dict):
            data = json.dumps(obj, sort_keys=True).encode('utf-8')
        else:
            data = str(obj).encode('utf-8')
        
        return hashlib.sha256(data).hexdigest()
    
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
    
    def _get_all_field_paths(self, obj: Dict[str, Any], prefix: str = '') -> Set[str]:
        """Get all field paths in object"""
        paths = set()
        
        for key, value in obj.items():
            field_path = f"{prefix}.{key}" if prefix else key
            paths.add(field_path)
            
            if isinstance(value, dict):
                paths.update(self._get_all_field_paths(value, field_path))
            elif isinstance(value, list):
                for i, item in enumerate(value):
                    if isinstance(item, dict):
                        paths.update(self._get_all_field_paths(item, f"{field_path}[{i}]"))
        
        return paths
    
    def _get_nested_value(self, obj: Dict[str, Any], path: str) -> Any:
        """Get nested value from object"""
        keys = path.split('.')
        current = obj
        
        for key in keys:
            if isinstance(current, dict) and key in current:
                current = current[key]
            else:
                return None
        
        return current
    
    def _calculate_confidence_score(self, report: IntegrityReport) -> float:
        """Calculate confidence score"""
        if report.total_checks == 0:
            return 0.0
        
        # Base score from passed checks
        base_score = (report.passed_checks / report.total_checks) * 100
        
        # Adjust based on violation severity
        severity_penalties = {
            'critical': 25,
            'high': 15,
            'medium': 5,
            'low': 1
        }
        
        total_penalty = 0
        for violation in report.violations:
            total_penalty += severity_penalties.get(violation.severity, 5)
        
        # Apply penalty
        confidence_score = max(0, base_score - total_penalty)
        
        return confidence_score
    
    def _determine_integrity_status(self, report: IntegrityReport) -> IntegrityStatus:
        """Determine overall integrity status"""
        if report.confidence_score >= 95:
            return IntegrityStatus.INTACT
        elif report.confidence_score >= 80:
            return IntegrityStatus.MODIFIED
        elif report.confidence_score >= 60:
            return IntegrityStatus.CORRUPTED
        else:
            return IntegrityStatus.TAMPERED
    
    def _update_metrics(self, report: IntegrityReport, verification_time: float):
        """Update integrity metrics"""
        self.metrics['total_checks'] += 1
        
        if report.integrity_status == IntegrityStatus.INTACT:
            self.metrics['intact_documents'] += 1
        elif report.integrity_status == IntegrityStatus.MODIFIED:
            self.metrics['modified_documents'] += 1
        elif report.integrity_status == IntegrityStatus.TAMPERED:
            self.metrics['tampered_documents'] += 1
        
        # Update average check time
        total_checks = self.metrics['total_checks']
        current_avg = self.metrics['average_check_time']
        self.metrics['average_check_time'] = (
            (current_avg * (total_checks - 1) + verification_time) / total_checks
        )
        
        # Track violation types
        for violation in report.violations:
            self.metrics['violations_by_type'][violation.violation_type.value] += 1
        
        # Track confidence scores
        self.metrics['confidence_scores'].append(report.confidence_score)
    
    async def create_integrity_checkpoint(self, 
                                        document_id: str,
                                        document_data: Union[Dict[str, Any], str, bytes]) -> IntegrityCheckpoint:
        """Create integrity checkpoint"""
        checkpoint = IntegrityCheckpoint(
            checkpoint_id=str(time.time()),
            document_id=document_id,
            document_hash=self._calculate_document_hash(document_data),
            structure_hash=self._calculate_object_hash(document_data) if isinstance(document_data, dict) else "",
            content_hash=hashlib.md5(self._serialize_document(document_data)).hexdigest(),
            field_count=len(self._get_all_field_paths(document_data)) if isinstance(document_data, dict) else 0,
            document_size=len(self._serialize_document(document_data)),
            created_at=datetime.utcnow()
        )
        
        # Store checkpoint
        self.checkpoints[document_id].append(checkpoint)
        
        return checkpoint
    
    async def get_integrity_analysis(self, 
                                   document_id: str,
                                   current_document: Union[Dict[str, Any], str, bytes]) -> IntegrityAnalysis:
        """Get integrity analysis"""
        current_hash = self._calculate_document_hash(current_document)
        
        # Get latest checkpoint
        checkpoints = self.checkpoints.get(document_id, [])
        if not checkpoints:
            return IntegrityAnalysis(
                document_id=document_id,
                original_hash="",
                current_hash=current_hash,
                hash_matches=False,
                risk_score=50.0  # Unknown risk
            )
        
        latest_checkpoint = checkpoints[-1]
        
        return IntegrityAnalysis(
            document_id=document_id,
            original_hash=latest_checkpoint.document_hash,
            current_hash=current_hash,
            hash_matches=latest_checkpoint.document_hash == current_hash,
            risk_score=0.0 if latest_checkpoint.document_hash == current_hash else 100.0
        )
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get integrity checker metrics"""
        return {
            **self.metrics,
            'integrity_rate': (
                self.metrics['intact_documents'] / 
                max(self.metrics['total_checks'], 1)
            ) * 100,
            'average_confidence': (
                sum(self.metrics['confidence_scores']) / 
                max(len(self.metrics['confidence_scores']), 1)
            ) if self.metrics['confidence_scores'] else 0.0,
            'total_checkpoints': sum(len(checkpoints) for checkpoints in self.checkpoints.values())
        }


# Factory functions for easy setup
def create_integrity_checker(stamp_validator: Optional[StampValidator] = None,
                           check_level: IntegrityLevel = IntegrityLevel.STANDARD) -> IntegrityChecker:
    """Create integrity checker instance"""
    return IntegrityChecker(stamp_validator, check_level)


async def verify_document_integrity(document_id: str,
                                  current_document: Union[Dict[str, Any], str, bytes],
                                  reference_data: Optional[Union[Dict[str, Any], str, bytes]] = None,
                                  check_level: IntegrityLevel = IntegrityLevel.STANDARD) -> IntegrityReport:
    """Verify document integrity"""
    checker = create_integrity_checker(None, check_level)
    return await checker.verify_document_integrity(document_id, current_document, reference_data)


def get_integrity_summary(report: IntegrityReport) -> Dict[str, Any]:
    """Get integrity summary"""
    return {
        'document_id': report.document_id,
        'is_intact': report.is_intact,
        'integrity_status': report.integrity_status.value,
        'confidence_score': report.confidence_score,
        'violations_count': len(report.violations),
        'critical_violations': len([v for v in report.violations if v.severity == 'critical']),
        'high_violations': len([v for v in report.violations if v.severity == 'high']),
        'verification_time': report.verification_time
    }