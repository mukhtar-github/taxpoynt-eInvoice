"""
Acknowledgment Handler Service for APP Role

This service handles acknowledgments from FIRS including:
- Processing FIRS acknowledgment responses
- Validating acknowledgment authenticity
- Extracting acknowledgment data and status
- Handling acknowledgment retries and timeouts
- Integration with status tracking system
"""

import asyncio
import json
import time
import hashlib
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List, Callable
from dataclasses import dataclass, field
from enum import Enum
import logging
from collections import defaultdict, deque
import uuid
import re

from .status_tracker import StatusTracker, SubmissionStatus

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class AckType(Enum):
    """Types of FIRS acknowledgments"""
    RECEIPT = "receipt"
    VALIDATION = "validation"
    PROCESSING = "processing"
    ACCEPTANCE = "acceptance"
    REJECTION = "rejection"
    STATUS_UPDATE = "status_update"
    ERROR = "error"


class AckFormat(Enum):
    """Acknowledgment formats"""
    JSON = "json"
    XML = "xml"
    PLAIN_TEXT = "plain_text"
    SOAP = "soap"


class AckStatus(Enum):
    """Acknowledgment processing status"""
    RECEIVED = "received"
    VALIDATING = "validating"
    PROCESSED = "processed"
    APPLIED = "applied"
    FAILED = "failed"
    IGNORED = "ignored"


@dataclass
class AckValidationRule:
    """Acknowledgment validation rule"""
    rule_id: str
    rule_name: str
    field_path: str
    validation_type: str  # required, format, range, etc.
    validation_value: Any
    error_message: str
    is_critical: bool = True


@dataclass
class FIRSAcknowledgment:
    """FIRS acknowledgment structure"""
    ack_id: str
    submission_id: Optional[str]
    document_id: Optional[str]
    ack_type: AckType
    ack_format: AckFormat
    received_at: datetime
    processed_at: Optional[datetime] = None
    
    # FIRS reference information
    firs_reference: Optional[str] = None
    firs_timestamp: Optional[datetime] = None
    firs_status_code: Optional[str] = None
    firs_status_message: Optional[str] = None
    
    # Acknowledgment content
    raw_content: str = ""
    parsed_content: Dict[str, Any] = field(default_factory=dict)
    
    # Processing information
    processing_status: AckStatus = AckStatus.RECEIVED
    validation_results: List[Dict[str, Any]] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    
    # Digital signature verification
    signature_valid: bool = False
    certificate_valid: bool = False
    signature_details: Dict[str, Any] = field(default_factory=dict)
    
    # Retry information
    retry_count: int = 0
    max_retries: int = 3
    next_retry_at: Optional[datetime] = None
    
    # Additional metadata
    source_ip: Optional[str] = None
    headers: Dict[str, str] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class AckProcessingResult:
    """Result of acknowledgment processing"""
    ack_id: str
    success: bool
    submission_id: Optional[str] = None
    new_status: Optional[SubmissionStatus] = None
    firs_reference: Optional[str] = None
    acknowledgment_code: Optional[str] = None
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    processing_time: float = 0.0
    actions_taken: List[str] = field(default_factory=list)


@dataclass
class AckPattern:
    """Pattern for acknowledgment recognition"""
    pattern_id: str
    ack_type: AckType
    format_type: AckFormat
    identification_rules: List[Dict[str, Any]]
    extraction_rules: Dict[str, str]
    status_mapping: Dict[str, SubmissionStatus]
    priority: int = 1


class AcknowledgmentHandler:
    """
    Acknowledgment handler service for APP role
    
    Handles:
    - Processing FIRS acknowledgment responses
    - Validating acknowledgment authenticity
    - Extracting acknowledgment data and status
    - Handling acknowledgment retries and timeouts
    - Integration with status tracking system
    """
    
    def __init__(self,
                 status_tracker: Optional[StatusTracker] = None,
                 validation_enabled: bool = True,
                 signature_verification_enabled: bool = True,
                 retry_interval: int = 300):  # 5 minutes
        
        self.status_tracker = status_tracker
        self.validation_enabled = validation_enabled
        self.signature_verification_enabled = signature_verification_enabled
        self.retry_interval = retry_interval
        
        # Storage
        self.acknowledgments: Dict[str, FIRSAcknowledgment] = {}
        self.pending_retries: deque = deque()
        
        # Validation rules
        self.validation_rules: Dict[AckType, List[AckValidationRule]] = defaultdict(list)
        self._setup_default_validation_rules()
        
        # Acknowledgment patterns
        self.ack_patterns: List[AckPattern] = []
        self._setup_default_patterns()
        
        # Processing callbacks
        self.ack_callbacks: Dict[AckType, List[Callable]] = defaultdict(list)
        
        # Background tasks
        self.retry_task: Optional[asyncio.Task] = None
        self.cleanup_task: Optional[asyncio.Task] = None
        self.running = False
        
        # Metrics
        self.metrics = {
            'total_acknowledgments': 0,
            'processed_acknowledgments': 0,
            'failed_acknowledgments': 0,
            'validation_failures': 0,
            'signature_failures': 0,
            'retries_performed': 0,
            'acks_by_type': defaultdict(int),
            'acks_by_format': defaultdict(int),
            'acks_by_status': defaultdict(int),
            'average_processing_time': 0.0,
            'duplicate_acknowledgments': 0
        }
    
    async def start(self):
        """Start acknowledgment handler service"""
        self.running = True
        
        # Start background tasks
        self.retry_task = asyncio.create_task(self._process_retries())
        self.cleanup_task = asyncio.create_task(self._periodic_cleanup())
        
        logger.info("Acknowledgment handler service started")
    
    async def stop(self):
        """Stop acknowledgment handler service"""
        self.running = False
        
        # Cancel background tasks
        if self.retry_task:
            self.retry_task.cancel()
        if self.cleanup_task:
            self.cleanup_task.cancel()
        
        logger.info("Acknowledgment handler service stopped")
    
    async def process_acknowledgment(self,
                                   raw_content: str,
                                   content_type: str = "application/json",
                                   headers: Optional[Dict[str, str]] = None,
                                   source_ip: Optional[str] = None) -> AckProcessingResult:
        """
        Process incoming FIRS acknowledgment
        
        Args:
            raw_content: Raw acknowledgment content
            content_type: Content type of acknowledgment
            headers: HTTP headers
            source_ip: Source IP address
            
        Returns:
            AckProcessingResult with processing outcome
        """
        start_time = time.time()
        ack_id = str(uuid.uuid4())
        
        try:
            # Determine acknowledgment format
            ack_format = self._determine_format(content_type, raw_content)
            
            # Create acknowledgment record
            acknowledgment = FIRSAcknowledgment(
                ack_id=ack_id,
                ack_type=AckType.RECEIPT,  # Will be determined later
                ack_format=ack_format,
                received_at=datetime.utcnow(),
                raw_content=raw_content,
                headers=headers or {},
                source_ip=source_ip
            )
            
            # Store acknowledgment
            self.acknowledgments[ack_id] = acknowledgment
            self.metrics['total_acknowledgments'] += 1
            self.metrics['acks_by_format'][ack_format.value] += 1
            
            # Parse content
            parsing_result = await self._parse_acknowledgment(acknowledgment)
            if not parsing_result:
                return self._create_error_result(ack_id, ["Failed to parse acknowledgment content"])
            
            # Identify acknowledgment type
            ack_type = await self._identify_acknowledgment_type(acknowledgment)
            acknowledgment.ack_type = ack_type
            self.metrics['acks_by_type'][ack_type.value] += 1
            
            # Extract submission information
            await self._extract_submission_info(acknowledgment)
            
            # Validate acknowledgment
            if self.validation_enabled:
                validation_result = await self._validate_acknowledgment(acknowledgment)
                if not validation_result:
                    acknowledgment.processing_status = AckStatus.FAILED
                    self.metrics['validation_failures'] += 1
                    return self._create_error_result(ack_id, acknowledgment.errors)
            
            # Verify digital signature
            if self.signature_verification_enabled:
                signature_result = await self._verify_signature(acknowledgment)
                if not signature_result:
                    acknowledgment.warnings.append("Digital signature verification failed")
                    self.metrics['signature_failures'] += 1
            
            # Process acknowledgment
            processing_result = await self._process_acknowledgment_content(acknowledgment)
            
            # Update status tracker if submission is found
            if acknowledgment.submission_id and self.status_tracker:
                await self._update_submission_status(acknowledgment, processing_result)
            
            # Execute callbacks
            await self._execute_callbacks(acknowledgment)
            
            # Mark as processed
            acknowledgment.processing_status = AckStatus.PROCESSED
            acknowledgment.processed_at = datetime.utcnow()
            self.metrics['processed_acknowledgments'] += 1
            
            # Create success result
            result = AckProcessingResult(
                ack_id=ack_id,
                success=True,
                submission_id=acknowledgment.submission_id,
                new_status=processing_result.get('new_status'),
                firs_reference=acknowledgment.firs_reference,
                acknowledgment_code=acknowledgment.firs_status_code,
                warnings=acknowledgment.warnings,
                processing_time=time.time() - start_time,
                actions_taken=processing_result.get('actions', [])
            )
            
            # Update average processing time
            self._update_average_processing_time(result.processing_time)
            
            logger.info(f"Processed acknowledgment {ack_id} for submission {acknowledgment.submission_id}")
            
            return result
            
        except Exception as e:
            self.metrics['failed_acknowledgments'] += 1
            logger.error(f"Error processing acknowledgment {ack_id}: {e}")
            
            return self._create_error_result(ack_id, [f"Processing error: {str(e)}"])
    
    def _determine_format(self, content_type: str, raw_content: str) -> AckFormat:
        """Determine acknowledgment format"""
        content_type = content_type.lower()
        
        if 'json' in content_type:
            return AckFormat.JSON
        elif 'xml' in content_type or 'soap' in content_type:
            return AckFormat.XML
        elif raw_content.strip().startswith(('<', '<?xml')):
            return AckFormat.XML
        elif raw_content.strip().startswith(('{', '[')):
            return AckFormat.JSON
        else:
            return AckFormat.PLAIN_TEXT
    
    async def _parse_acknowledgment(self, acknowledgment: FIRSAcknowledgment) -> bool:
        """Parse acknowledgment content"""
        try:
            if acknowledgment.ack_format == AckFormat.JSON:
                acknowledgment.parsed_content = json.loads(acknowledgment.raw_content)
            elif acknowledgment.ack_format == AckFormat.XML:
                root = ET.fromstring(acknowledgment.raw_content)
                acknowledgment.parsed_content = self._xml_to_dict(root)
            else:
                # Plain text parsing
                acknowledgment.parsed_content = {'content': acknowledgment.raw_content}
            
            return True
            
        except Exception as e:
            acknowledgment.errors.append(f"Content parsing error: {str(e)}")
            return False
    
    async def _identify_acknowledgment_type(self, acknowledgment: FIRSAcknowledgment) -> AckType:
        """Identify acknowledgment type using patterns"""
        content = acknowledgment.parsed_content
        
        # Try to match against patterns
        for pattern in sorted(self.ack_patterns, key=lambda p: p.priority, reverse=True):
            if self._matches_pattern(content, pattern):
                return pattern.ack_type
        
        # Default identification based on content
        if any(key in str(content).lower() for key in ['accept', 'approved', 'success']):
            return AckType.ACCEPTANCE
        elif any(key in str(content).lower() for key in ['reject', 'denied', 'failed']):
            return AckType.REJECTION
        elif any(key in str(content).lower() for key in ['receipt', 'received']):
            return AckType.RECEIPT
        elif any(key in str(content).lower() for key in ['validation', 'validate']):
            return AckType.VALIDATION
        elif any(key in str(content).lower() for key in ['processing', 'process']):
            return AckType.PROCESSING
        elif any(key in str(content).lower() for key in ['error', 'exception']):
            return AckType.ERROR
        else:
            return AckType.STATUS_UPDATE
    
    async def _extract_submission_info(self, acknowledgment: FIRSAcknowledgment):
        """Extract submission information from acknowledgment"""
        content = acknowledgment.parsed_content
        
        # Try to extract submission ID
        submission_id_fields = [
            'submission_id', 'submissionId', 'transaction_id', 'transactionId',
            'reference', 'ref', 'id', 'invoice_id', 'invoiceId'
        ]
        
        for field in submission_id_fields:
            if field in content:
                acknowledgment.submission_id = str(content[field])
                break
        
        # Try to extract document ID
        document_id_fields = [
            'document_id', 'documentId', 'invoice_number', 'invoiceNumber',
            'document_reference', 'documentReference'
        ]
        
        for field in document_id_fields:
            if field in content:
                acknowledgment.document_id = str(content[field])
                break
        
        # Extract FIRS reference
        firs_ref_fields = [
            'firs_reference', 'firsReference', 'confirmation_code',
            'confirmationCode', 'receipt_number', 'receiptNumber'
        ]
        
        for field in firs_ref_fields:
            if field in content:
                acknowledgment.firs_reference = str(content[field])
                break
        
        # Extract FIRS timestamp
        timestamp_fields = ['timestamp', 'date', 'processing_date', 'processingDate']
        
        for field in timestamp_fields:
            if field in content:
                try:
                    timestamp_str = str(content[field])
                    acknowledgment.firs_timestamp = datetime.fromisoformat(
                        timestamp_str.replace('Z', '+00:00')
                    )
                    break
                except:
                    pass
        
        # Extract status information
        status_fields = ['status', 'status_code', 'statusCode', 'result', 'outcome']
        
        for field in status_fields:
            if field in content:
                acknowledgment.firs_status_code = str(content[field])
                break
        
        message_fields = ['message', 'status_message', 'statusMessage', 'description']
        
        for field in message_fields:
            if field in content:
                acknowledgment.firs_status_message = str(content[field])
                break
    
    async def _validate_acknowledgment(self, acknowledgment: FIRSAcknowledgment) -> bool:
        """Validate acknowledgment content"""
        validation_rules = self.validation_rules.get(acknowledgment.ack_type, [])
        validation_success = True
        
        for rule in validation_rules:
            try:
                result = self._apply_validation_rule(acknowledgment.parsed_content, rule)
                acknowledgment.validation_results.append({
                    'rule_id': rule.rule_id,
                    'rule_name': rule.rule_name,
                    'success': result,
                    'field_path': rule.field_path
                })
                
                if not result:
                    if rule.is_critical:
                        acknowledgment.errors.append(rule.error_message)
                        validation_success = False
                    else:
                        acknowledgment.warnings.append(rule.error_message)
                        
            except Exception as e:
                acknowledgment.errors.append(f"Validation rule {rule.rule_id} failed: {str(e)}")
                validation_success = False
        
        return validation_success
    
    def _apply_validation_rule(self, content: Dict[str, Any], rule: AckValidationRule) -> bool:
        """Apply single validation rule"""
        # Get field value using path
        field_value = self._get_field_by_path(content, rule.field_path)
        
        if rule.validation_type == "required":
            return field_value is not None and field_value != ""
        elif rule.validation_type == "format":
            if field_value is None:
                return False
            pattern = rule.validation_value
            return bool(re.match(pattern, str(field_value)))
        elif rule.validation_type == "range":
            if field_value is None:
                return False
            min_val, max_val = rule.validation_value
            return min_val <= len(str(field_value)) <= max_val
        elif rule.validation_type == "enum":
            return field_value in rule.validation_value
        
        return True
    
    def _get_field_by_path(self, content: Dict[str, Any], path: str) -> Any:
        """Get field value by dot-separated path"""
        keys = path.split('.')
        value = content
        
        for key in keys:
            if isinstance(value, dict) and key in value:
                value = value[key]
            else:
                return None
        
        return value
    
    async def _verify_signature(self, acknowledgment: FIRSAcknowledgment) -> bool:
        """Verify digital signature of acknowledgment"""
        # This would implement actual signature verification
        # For now, return True if signature data is present
        
        signature_fields = ['signature', 'digital_signature', 'hash', 'checksum']
        
        for field in signature_fields:
            if field in acknowledgment.parsed_content:
                acknowledgment.signature_valid = True
                acknowledgment.signature_details = {
                    'field': field,
                    'value': acknowledgment.parsed_content[field],
                    'algorithm': 'SHA256',  # Would be determined from signature
                    'verified_at': datetime.utcnow().isoformat()
                }
                return True
        
        return False
    
    async def _process_acknowledgment_content(self, acknowledgment: FIRSAcknowledgment) -> Dict[str, Any]:
        """Process acknowledgment content and determine actions"""
        result = {
            'new_status': None,
            'actions': []
        }
        
        # Determine new submission status based on acknowledgment type
        if acknowledgment.ack_type == AckType.RECEIPT:
            result['new_status'] = SubmissionStatus.ACKNOWLEDGED
            result['actions'].append('acknowledged_receipt')
            
        elif acknowledgment.ack_type == AckType.VALIDATION:
            # Check validation outcome
            if 'success' in acknowledgment.parsed_content:
                if acknowledgment.parsed_content['success']:
                    result['new_status'] = SubmissionStatus.VALIDATED
                    result['actions'].append('validation_passed')
                else:
                    result['new_status'] = SubmissionStatus.FAILED
                    result['actions'].append('validation_failed')
            else:
                result['new_status'] = SubmissionStatus.PROCESSING
                result['actions'].append('validation_in_progress')
                
        elif acknowledgment.ack_type == AckType.ACCEPTANCE:
            result['new_status'] = SubmissionStatus.ACCEPTED
            result['actions'].append('submission_accepted')
            
        elif acknowledgment.ack_type == AckType.REJECTION:
            result['new_status'] = SubmissionStatus.REJECTED
            result['actions'].append('submission_rejected')
            
        elif acknowledgment.ack_type == AckType.PROCESSING:
            result['new_status'] = SubmissionStatus.PROCESSING
            result['actions'].append('processing_status_update')
            
        elif acknowledgment.ack_type == AckType.ERROR:
            result['new_status'] = SubmissionStatus.FAILED
            result['actions'].append('error_reported')
        
        return result
    
    async def _update_submission_status(self, acknowledgment: FIRSAcknowledgment, processing_result: Dict[str, Any]):
        """Update submission status in status tracker"""
        if not acknowledgment.submission_id or not processing_result.get('new_status'):
            return
        
        try:
            success = await self.status_tracker.update_status(
                submission_id=acknowledgment.submission_id,
                new_status=processing_result['new_status'],
                reason=f"FIRS acknowledgment: {acknowledgment.ack_type.value}",
                metadata={
                    'ack_id': acknowledgment.ack_id,
                    'firs_reference': acknowledgment.firs_reference,
                    'firs_timestamp': acknowledgment.firs_timestamp.isoformat() if acknowledgment.firs_timestamp else None,
                    'ack_type': acknowledgment.ack_type.value
                },
                firs_reference=acknowledgment.firs_reference,
                acknowledgment_code=acknowledgment.firs_status_code
            )
            
            if success:
                acknowledgment.processing_status = AckStatus.APPLIED
                processing_result['actions'].append('status_updated')
            else:
                acknowledgment.warnings.append("Failed to update submission status")
                
        except Exception as e:
            acknowledgment.errors.append(f"Status update error: {str(e)}")
    
    async def _execute_callbacks(self, acknowledgment: FIRSAcknowledgment):
        """Execute registered callbacks for acknowledgment type"""
        callbacks = self.ack_callbacks.get(acknowledgment.ack_type, [])
        
        for callback in callbacks:
            try:
                if asyncio.iscoroutinefunction(callback):
                    await callback(acknowledgment)
                else:
                    callback(acknowledgment)
            except Exception as e:
                logger.error(f"Error executing acknowledgment callback: {e}")
    
    def _matches_pattern(self, content: Dict[str, Any], pattern: AckPattern) -> bool:
        """Check if content matches acknowledgment pattern"""
        for rule in pattern.identification_rules:
            field_path = rule.get('field_path')
            expected_value = rule.get('value')
            match_type = rule.get('type', 'equals')
            
            field_value = self._get_field_by_path(content, field_path)
            
            if match_type == 'equals':
                if field_value != expected_value:
                    return False
            elif match_type == 'contains':
                if expected_value not in str(field_value):
                    return False
            elif match_type == 'regex':
                if not re.search(expected_value, str(field_value or '')):
                    return False
        
        return True
    
    def _xml_to_dict(self, element) -> Dict[str, Any]:
        """Convert XML element to dictionary"""
        result = {}
        
        # Add attributes
        if element.attrib:
            result.update(element.attrib)
        
        # Add text content
        if element.text and element.text.strip():
            if len(element) == 0:
                return element.text.strip()
            result['_text'] = element.text.strip()
        
        # Add child elements
        for child in element:
            child_data = self._xml_to_dict(child)
            if child.tag in result:
                # Convert to list if multiple elements with same tag
                if not isinstance(result[child.tag], list):
                    result[child.tag] = [result[child.tag]]
                result[child.tag].append(child_data)
            else:
                result[child.tag] = child_data
        
        return result
    
    def _create_error_result(self, ack_id: str, errors: List[str]) -> AckProcessingResult:
        """Create error processing result"""
        return AckProcessingResult(
            ack_id=ack_id,
            success=False,
            errors=errors,
            processing_time=0.0
        )
    
    def _update_average_processing_time(self, processing_time: float):
        """Update average processing time metric"""
        processed_count = self.metrics['processed_acknowledgments']
        current_avg = self.metrics['average_processing_time']
        
        if processed_count > 0:
            self.metrics['average_processing_time'] = (
                (current_avg * (processed_count - 1) + processing_time) / processed_count
            )
    
    def _setup_default_validation_rules(self):
        """Setup default validation rules"""
        # Receipt acknowledgment rules
        self.validation_rules[AckType.RECEIPT] = [
            AckValidationRule(
                rule_id="receipt_ref_required",
                rule_name="Receipt Reference Required",
                field_path="receipt_number",
                validation_type="required",
                validation_value=None,
                error_message="Receipt number is required"
            ),
            AckValidationRule(
                rule_id="receipt_timestamp",
                rule_name="Receipt Timestamp Required",
                field_path="timestamp",
                validation_type="required",
                validation_value=None,
                error_message="Receipt timestamp is required"
            )
        ]
        
        # Acceptance acknowledgment rules
        self.validation_rules[AckType.ACCEPTANCE] = [
            AckValidationRule(
                rule_id="acceptance_code",
                rule_name="Acceptance Code Required",
                field_path="acceptance_code",
                validation_type="required",
                validation_value=None,
                error_message="Acceptance code is required"
            ),
            AckValidationRule(
                rule_id="acceptance_status",
                rule_name="Valid Acceptance Status",
                field_path="status",
                validation_type="enum",
                validation_value=["ACCEPTED", "APPROVED", "SUCCESS"],
                error_message="Invalid acceptance status"
            )
        ]
        
        # Rejection acknowledgment rules
        self.validation_rules[AckType.REJECTION] = [
            AckValidationRule(
                rule_id="rejection_reason",
                rule_name="Rejection Reason Required",
                field_path="reason",
                validation_type="required",
                validation_value=None,
                error_message="Rejection reason is required"
            ),
            AckValidationRule(
                rule_id="rejection_code",
                rule_name="Rejection Code Format",
                field_path="error_code",
                validation_type="format",
                validation_value=r"^[A-Z0-9]{3,10}$",
                error_message="Invalid rejection code format"
            )
        ]
    
    def _setup_default_patterns(self):
        """Setup default acknowledgment patterns"""
        # Receipt pattern
        self.ack_patterns.append(AckPattern(
            pattern_id="firs_receipt",
            ack_type=AckType.RECEIPT,
            format_type=AckFormat.JSON,
            identification_rules=[
                {'field_path': 'type', 'value': 'receipt', 'type': 'equals'},
                {'field_path': 'receipt_number', 'value': r'.+', 'type': 'regex'}
            ],
            extraction_rules={
                'submission_id': 'transaction_id',
                'firs_reference': 'receipt_number',
                'timestamp': 'timestamp'
            },
            status_mapping={'received': SubmissionStatus.ACKNOWLEDGED},
            priority=10
        ))
        
        # Acceptance pattern
        self.ack_patterns.append(AckPattern(
            pattern_id="firs_acceptance",
            ack_type=AckType.ACCEPTANCE,
            format_type=AckFormat.JSON,
            identification_rules=[
                {'field_path': 'status', 'value': 'ACCEPTED|APPROVED|SUCCESS', 'type': 'regex'}
            ],
            extraction_rules={
                'submission_id': 'transaction_id',
                'firs_reference': 'confirmation_code',
                'status_code': 'status'
            },
            status_mapping={'ACCEPTED': SubmissionStatus.ACCEPTED},
            priority=10
        ))
        
        # Rejection pattern
        self.ack_patterns.append(AckPattern(
            pattern_id="firs_rejection",
            ack_type=AckType.REJECTION,
            format_type=AckFormat.JSON,
            identification_rules=[
                {'field_path': 'status', 'value': 'REJECTED|DENIED|FAILED', 'type': 'regex'}
            ],
            extraction_rules={
                'submission_id': 'transaction_id',
                'error_code': 'error_code',
                'error_message': 'reason'
            },
            status_mapping={'REJECTED': SubmissionStatus.REJECTED},
            priority=10
        ))
    
    async def _process_retries(self):
        """Process acknowledgment retries"""
        while self.running:
            try:
                current_time = datetime.utcnow()
                retries_to_process = []
                
                # Find acknowledgments ready for retry
                for ack_id, acknowledgment in self.acknowledgments.items():
                    if (acknowledgment.processing_status == AckStatus.FAILED and
                        acknowledgment.retry_count < acknowledgment.max_retries and
                        acknowledgment.next_retry_at and
                        current_time >= acknowledgment.next_retry_at):
                        retries_to_process.append(ack_id)
                
                # Process retries
                for ack_id in retries_to_process:
                    acknowledgment = self.acknowledgments[ack_id]
                    acknowledgment.retry_count += 1
                    acknowledgment.processing_status = AckStatus.RECEIVED
                    acknowledgment.errors.clear()
                    acknowledgment.warnings.clear()
                    
                    # Reprocess acknowledgment
                    result = await self.process_acknowledgment(
                        acknowledgment.raw_content,
                        headers=acknowledgment.headers,
                        source_ip=acknowledgment.source_ip
                    )
                    
                    if not result.success:
                        # Schedule next retry
                        acknowledgment.next_retry_at = current_time + timedelta(seconds=self.retry_interval)
                    
                    self.metrics['retries_performed'] += 1
                
                await asyncio.sleep(60)  # Check every minute
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error processing retries: {e}")
                await asyncio.sleep(60)
    
    async def _periodic_cleanup(self):
        """Periodic cleanup of old acknowledgments"""
        while self.running:
            try:
                await asyncio.sleep(3600)  # Run every hour
                
                current_time = datetime.utcnow()
                cutoff_time = current_time - timedelta(hours=24)
                
                # Remove old processed acknowledgments
                old_acks = []
                for ack_id, acknowledgment in self.acknowledgments.items():
                    if (acknowledgment.processing_status in [AckStatus.PROCESSED, AckStatus.APPLIED] and
                        acknowledgment.processed_at and
                        acknowledgment.processed_at < cutoff_time):
                        old_acks.append(ack_id)
                
                for ack_id in old_acks:
                    del self.acknowledgments[ack_id]
                
                if old_acks:
                    logger.info(f"Cleaned up {len(old_acks)} old acknowledgments")
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in periodic cleanup: {e}")
    
    def add_validation_rule(self, ack_type: AckType, rule: AckValidationRule):
        """Add custom validation rule"""
        self.validation_rules[ack_type].append(rule)
    
    def add_acknowledgment_pattern(self, pattern: AckPattern):
        """Add custom acknowledgment pattern"""
        self.ack_patterns.append(pattern)
        # Sort by priority
        self.ack_patterns.sort(key=lambda p: p.priority, reverse=True)
    
    def register_callback(self, ack_type: AckType, callback: Callable):
        """Register callback for acknowledgment type"""
        self.ack_callbacks[ack_type].append(callback)
    
    def get_acknowledgment(self, ack_id: str) -> Optional[FIRSAcknowledgment]:
        """Get acknowledgment by ID"""
        return self.acknowledgments.get(ack_id)
    
    def get_acknowledgments_by_submission(self, submission_id: str) -> List[FIRSAcknowledgment]:
        """Get acknowledgments for submission"""
        return [ack for ack in self.acknowledgments.values() 
                if ack.submission_id == submission_id]
    
    def get_acknowledgments_by_type(self, ack_type: AckType) -> List[FIRSAcknowledgment]:
        """Get acknowledgments by type"""
        return [ack for ack in self.acknowledgments.values() 
                if ack.ack_type == ack_type]
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get acknowledgment handler metrics"""
        success_rate = 0
        if self.metrics['total_acknowledgments'] > 0:
            success_rate = (self.metrics['processed_acknowledgments'] / 
                          self.metrics['total_acknowledgments']) * 100
        
        return {
            **self.metrics,
            'success_rate': success_rate,
            'active_acknowledgments': len(self.acknowledgments),
            'validation_rules': sum(len(rules) for rules in self.validation_rules.values()),
            'acknowledgment_patterns': len(self.ack_patterns),
            'registered_callbacks': sum(len(callbacks) for callbacks in self.ack_callbacks.values())
        }


# Factory functions for easy setup
def create_acknowledgment_handler(status_tracker: Optional[StatusTracker] = None,
                                validation_enabled: bool = True) -> AcknowledgmentHandler:
    """Create acknowledgment handler instance"""
    return AcknowledgmentHandler(
        status_tracker=status_tracker,
        validation_enabled=validation_enabled
    )


def create_ack_validation_rule(rule_id: str,
                             field_path: str,
                             validation_type: str,
                             error_message: str,
                             **kwargs) -> AckValidationRule:
    """Create acknowledgment validation rule"""
    return AckValidationRule(
        rule_id=rule_id,
        rule_name=rule_id.replace('_', ' ').title(),
        field_path=field_path,
        validation_type=validation_type,
        validation_value=kwargs.get('validation_value'),
        error_message=error_message,
        **kwargs
    )


async def process_firs_acknowledgment(raw_content: str,
                                    content_type: str = "application/json",
                                    handler: Optional[AcknowledgmentHandler] = None) -> AckProcessingResult:
    """Process FIRS acknowledgment"""
    if not handler:
        handler = create_acknowledgment_handler()
        await handler.start()
    
    try:
        return await handler.process_acknowledgment(raw_content, content_type)
    finally:
        if not handler.running:
            await handler.stop()


def get_acknowledgment_summary(handler: AcknowledgmentHandler) -> Dict[str, Any]:
    """Get acknowledgment handler summary"""
    metrics = handler.get_metrics()
    
    return {
        'total_acknowledgments': metrics['total_acknowledgments'],
        'processed_acknowledgments': metrics['processed_acknowledgments'],
        'success_rate': metrics['success_rate'],
        'validation_failures': metrics['validation_failures'],
        'signature_failures': metrics['signature_failures'],
        'retries_performed': metrics['retries_performed'],
        'average_processing_time': metrics['average_processing_time'],
        'ack_type_distribution': dict(metrics['acks_by_type']),
        'format_distribution': dict(metrics['acks_by_format'])
    }