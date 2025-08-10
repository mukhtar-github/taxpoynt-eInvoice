"""
Threat Detector Service for APP Role

This service detects and responds to security threats including:
- Real-time threat detection and analysis
- Behavioral anomaly detection
- Pattern recognition for attacks
- Automated threat response
- Integration with external threat intelligence
"""

import time
import hashlib
import re
import asyncio
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List, Set, Callable, Pattern
from dataclasses import dataclass, field
from enum import Enum
import logging
from collections import defaultdict, deque
import ipaddress
import user_agents
import math

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ThreatLevel(Enum):
    """Threat severity levels"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class ThreatType(Enum):
    """Types of threats"""
    BRUTE_FORCE = "brute_force"
    SQL_INJECTION = "sql_injection"
    XSS = "xss"
    DOS_ATTACK = "dos_attack"
    MALICIOUS_PAYLOAD = "malicious_payload"
    SUSPICIOUS_BEHAVIOR = "suspicious_behavior"
    DATA_EXFILTRATION = "data_exfiltration"
    PRIVILEGE_ESCALATION = "privilege_escalation"
    RECONNAISSANCE = "reconnaissance"
    MALWARE = "malware"
    PHISHING = "phishing"
    ANOMALOUS_ACCESS = "anomalous_access"


class ThreatStatus(Enum):
    """Threat detection status"""
    DETECTED = "detected"
    INVESTIGATING = "investigating"
    CONFIRMED = "confirmed"
    FALSE_POSITIVE = "false_positive"
    MITIGATED = "mitigated"
    RESOLVED = "resolved"


class ResponseAction(Enum):
    """Automated response actions"""
    LOG_ONLY = "log_only"
    ALERT = "alert"
    BLOCK_IP = "block_ip"
    BLOCK_USER = "block_user"
    RATE_LIMIT = "rate_limit"
    CHALLENGE_REQUEST = "challenge_request"
    QUARANTINE = "quarantine"
    ESCALATE = "escalate"


@dataclass
class ThreatSignature:
    """Threat detection signature"""
    signature_id: str
    threat_type: ThreatType
    pattern: str
    pattern_type: str  # regex, string, ip, etc.
    severity: ThreatLevel
    description: str
    enabled: bool = True
    false_positive_rate: float = 0.0
    last_updated: datetime = field(default_factory=datetime.utcnow)


@dataclass
class ThreatIndicator:
    """Threat indicator data"""
    indicator_id: str
    indicator_type: str  # ip, hash, domain, url, etc.
    indicator_value: str
    threat_types: List[ThreatType]
    confidence: float
    source: str
    first_seen: datetime
    last_seen: datetime
    is_active: bool = True


@dataclass
class SecurityEvent:
    """Security event data"""
    event_id: str
    timestamp: datetime
    source_ip: str
    user_id: Optional[str]
    event_type: str
    resource: str
    payload: Dict[str, Any]
    user_agent: Optional[str] = None
    session_id: Optional[str] = None
    request_id: Optional[str] = None


@dataclass
class ThreatDetection:
    """Threat detection result"""
    detection_id: str
    threat_type: ThreatType
    threat_level: ThreatLevel
    confidence: float
    description: str
    source_ip: str
    user_id: Optional[str]
    detected_at: datetime
    evidence: Dict[str, Any]
    status: ThreatStatus = ThreatStatus.DETECTED
    false_positive: bool = False
    response_actions: List[ResponseAction] = field(default_factory=list)
    related_events: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class BehavioralPattern:
    """User behavioral pattern"""
    user_id: str
    pattern_type: str
    baseline_metrics: Dict[str, float]
    current_metrics: Dict[str, float]
    deviation_score: float
    last_updated: datetime
    sample_count: int = 0


@dataclass
class AttackPattern:
    """Attack pattern recognition"""
    pattern_id: str
    attack_type: ThreatType
    indicators: List[str]
    time_window: int  # seconds
    threshold: int
    confidence: float
    description: str


@dataclass
class ThreatResponse:
    """Threat response configuration"""
    threat_type: ThreatType
    threat_level: ThreatLevel
    actions: List[ResponseAction]
    auto_execute: bool = True
    escalation_threshold: int = 3
    cooldown_period: int = 300  # seconds


class ThreatDetector:
    """
    Threat detector service for APP role
    
    Handles:
    - Real-time threat detection and analysis
    - Behavioral anomaly detection
    - Pattern recognition for attacks
    - Automated threat response
    - Integration with external threat intelligence
    """
    
    def __init__(self,
                 detection_window: int = 300,  # 5 minutes
                 max_events_memory: int = 10000):
        
        self.detection_window = detection_window
        self.max_events_memory = max_events_memory
        
        # Storage
        self.threat_signatures: Dict[str, ThreatSignature] = {}
        self.threat_indicators: Dict[str, ThreatIndicator] = {}
        self.security_events: deque = deque(maxlen=max_events_memory)
        self.threat_detections: List[ThreatDetection] = []
        self.behavioral_patterns: Dict[str, BehavioralPattern] = {}
        self.attack_patterns: Dict[str, AttackPattern] = {}
        self.threat_responses: Dict[Tuple[ThreatType, ThreatLevel], ThreatResponse] = {}
        
        # Real-time tracking
        self.ip_activity: Dict[str, Dict[str, Any]] = defaultdict(lambda: {
            'request_count': 0,
            'failed_attempts': 0,
            'first_seen': None,
            'last_seen': None,
            'user_agents': set(),
            'resources_accessed': set(),
            'threat_score': 0.0
        })
        
        self.user_activity: Dict[str, Dict[str, Any]] = defaultdict(lambda: {
            'request_count': 0,
            'locations': set(),
            'resources_accessed': set(),
            'last_activity': None,
            'behavior_score': 0.0
        })
        
        # Blocked entities
        self.blocked_ips: Set[str] = set()
        self.blocked_users: Set[str] = set()
        
        # Custom detection functions
        self.custom_detectors: List[Callable] = []
        
        # Setup default signatures and patterns
        self._setup_default_signatures()
        self._setup_default_attack_patterns()
        self._setup_default_responses()
        
        # Metrics
        self.metrics = {
            'total_events_processed': 0,
            'threats_detected': 0,
            'false_positives': 0,
            'threats_by_type': defaultdict(int),
            'threats_by_level': defaultdict(int),
            'responses_executed': 0,
            'blocked_ips': 0,
            'blocked_users': 0,
            'detection_accuracy': 0.0,
            'average_response_time': 0.0
        }
        
        # Background task
        self.cleanup_task: Optional[asyncio.Task] = None
        self.running = False
    
    async def start(self):
        """Start threat detector service"""
        self.running = True
        self.cleanup_task = asyncio.create_task(self._periodic_cleanup())
        logger.info("Threat detector service started")
    
    async def stop(self):
        """Stop threat detector service"""
        self.running = False
        if self.cleanup_task:
            self.cleanup_task.cancel()
        logger.info("Threat detector service stopped")
    
    def _setup_default_signatures(self):
        """Setup default threat signatures"""
        # SQL Injection patterns
        sql_patterns = [
            r"(\bUNION\b.*\bSELECT\b)",
            r"(\bSELECT\b.*\bFROM\b.*\bWHERE\b.*\bOR\b.*=.*)",
            r"('.*OR.*'.*=.*')",
            r"(;.*DROP\b.*TABLE)",
            r"(\bINSERT\b.*\bINTO\b.*\bVALUES\b)"
        ]
        
        for i, pattern in enumerate(sql_patterns):
            self.threat_signatures[f"sql_injection_{i}"] = ThreatSignature(
                signature_id=f"sql_injection_{i}",
                threat_type=ThreatType.SQL_INJECTION,
                pattern=pattern,
                pattern_type="regex",
                severity=ThreatLevel.HIGH,
                description=f"SQL injection pattern {i+1}"
            )
        
        # XSS patterns
        xss_patterns = [
            r"(<script.*?>.*?</script>)",
            r"(javascript:.*)",
            r"(on\w+\s*=.*)",
            r"(<iframe.*?>)",
            r"(eval\(.*\))"
        ]
        
        for i, pattern in enumerate(xss_patterns):
            self.threat_signatures[f"xss_{i}"] = ThreatSignature(
                signature_id=f"xss_{i}",
                threat_type=ThreatType.XSS,
                pattern=pattern,
                pattern_type="regex",
                severity=ThreatLevel.MEDIUM,
                description=f"XSS pattern {i+1}"
            )
        
        # Malicious payload patterns
        malicious_patterns = [
            r"(\.\.\/.*\.\.\/)",  # Path traversal
            r"(\/etc\/passwd)",   # Linux system files
            r"(\/proc\/.*)",      # Linux proc filesystem
            r"(cmd\.exe)",        # Windows command execution
            r"(powershell)",      # PowerShell execution
        ]
        
        for i, pattern in enumerate(malicious_patterns):
            self.threat_signatures[f"malicious_{i}"] = ThreatSignature(
                signature_id=f"malicious_{i}",
                threat_type=ThreatType.MALICIOUS_PAYLOAD,
                pattern=pattern,
                pattern_type="regex",
                severity=ThreatLevel.HIGH,
                description=f"Malicious payload pattern {i+1}"
            )
    
    def _setup_default_attack_patterns(self):
        """Setup default attack patterns"""
        # Brute force attack pattern
        self.attack_patterns['brute_force'] = AttackPattern(
            pattern_id='brute_force',
            attack_type=ThreatType.BRUTE_FORCE,
            indicators=['multiple_failed_logins', 'same_ip', 'short_timeframe'],
            time_window=300,  # 5 minutes
            threshold=10,     # 10 failed attempts
            confidence=0.9,
            description="Brute force login attack detection"
        )
        
        # DoS attack pattern
        self.attack_patterns['dos_attack'] = AttackPattern(
            pattern_id='dos_attack',
            attack_type=ThreatType.DOS_ATTACK,
            indicators=['high_request_rate', 'same_ip', 'repeated_requests'],
            time_window=60,   # 1 minute
            threshold=100,    # 100 requests
            confidence=0.85,
            description="Denial of Service attack detection"
        )
        
        # Data exfiltration pattern
        self.attack_patterns['data_exfiltration'] = AttackPattern(
            pattern_id='data_exfiltration',
            attack_type=ThreatType.DATA_EXFILTRATION,
            indicators=['large_response_size', 'multiple_data_requests', 'unusual_access_pattern'],
            time_window=600,  # 10 minutes
            threshold=5,      # 5 large requests
            confidence=0.75,
            description="Data exfiltration detection"
        )
    
    def _setup_default_responses(self):
        """Setup default threat responses"""
        # Critical threats
        self.threat_responses[(ThreatType.SQL_INJECTION, ThreatLevel.CRITICAL)] = ThreatResponse(
            threat_type=ThreatType.SQL_INJECTION,
            threat_level=ThreatLevel.CRITICAL,
            actions=[ResponseAction.BLOCK_IP, ResponseAction.ALERT, ResponseAction.ESCALATE],
            auto_execute=True
        )
        
        # High threats
        self.threat_responses[(ThreatType.BRUTE_FORCE, ThreatLevel.HIGH)] = ThreatResponse(
            threat_type=ThreatType.BRUTE_FORCE,
            threat_level=ThreatLevel.HIGH,
            actions=[ResponseAction.RATE_LIMIT, ResponseAction.ALERT],
            auto_execute=True
        )
        
        # Medium threats
        self.threat_responses[(ThreatType.XSS, ThreatLevel.MEDIUM)] = ThreatResponse(
            threat_type=ThreatType.XSS,
            threat_level=ThreatLevel.MEDIUM,
            actions=[ResponseAction.LOG_ONLY, ResponseAction.ALERT],
            auto_execute=True
        )
    
    async def process_event(self, event: SecurityEvent) -> List[ThreatDetection]:
        """
        Process security event and detect threats
        
        Args:
            event: Security event to process
            
        Returns:
            List of threat detections
        """
        start_time = time.time()
        detections = []
        
        try:
            # Add event to storage
            self.security_events.append(event)
            self.metrics['total_events_processed'] += 1
            
            # Update activity tracking
            self._update_ip_activity(event)
            if event.user_id:
                self._update_user_activity(event)
            
            # Check against threat signatures
            signature_detections = await self._check_threat_signatures(event)
            detections.extend(signature_detections)
            
            # Check against threat indicators
            indicator_detections = await self._check_threat_indicators(event)
            detections.extend(indicator_detections)
            
            # Check attack patterns
            pattern_detections = await self._check_attack_patterns(event)
            detections.extend(pattern_detections)
            
            # Check behavioral anomalies
            if event.user_id:
                behavioral_detections = await self._check_behavioral_anomalies(event)
                detections.extend(behavioral_detections)
            
            # Run custom detectors
            custom_detections = await self._run_custom_detectors(event)
            detections.extend(custom_detections)
            
            # Process detections
            for detection in detections:
                await self._process_detection(detection)
            
            # Update metrics
            response_time = time.time() - start_time
            self._update_response_time_metric(response_time)
            
            return detections
            
        except Exception as e:
            logger.error(f"Error processing security event {event.event_id}: {e}")
            return []
    
    async def _check_threat_signatures(self, event: SecurityEvent) -> List[ThreatDetection]:
        """Check event against threat signatures"""
        detections = []
        
        # Prepare search content
        search_content = []
        if 'url' in event.payload:
            search_content.append(event.payload['url'])
        if 'parameters' in event.payload:
            search_content.append(str(event.payload['parameters']))
        if 'headers' in event.payload:
            search_content.append(str(event.payload['headers']))
        if 'body' in event.payload:
            search_content.append(str(event.payload['body']))
        
        content = ' '.join(search_content).lower()
        
        # Check each signature
        for signature in self.threat_signatures.values():
            if not signature.enabled:
                continue
            
            try:
                if signature.pattern_type == "regex":
                    pattern = re.compile(signature.pattern, re.IGNORECASE)
                    matches = pattern.findall(content)
                    
                    if matches:
                        detection = ThreatDetection(
                            detection_id=f"sig_{signature.signature_id}_{int(time.time())}",
                            threat_type=signature.threat_type,
                            threat_level=signature.severity,
                            confidence=0.9 - signature.false_positive_rate,
                            description=f"Signature match: {signature.description}",
                            source_ip=event.source_ip,
                            user_id=event.user_id,
                            detected_at=datetime.utcnow(),
                            evidence={
                                'signature_id': signature.signature_id,
                                'matches': matches,
                                'pattern': signature.pattern,
                                'event_id': event.event_id
                            }
                        )
                        detections.append(detection)
                
                elif signature.pattern_type == "string":
                    if signature.pattern.lower() in content:
                        detection = ThreatDetection(
                            detection_id=f"sig_{signature.signature_id}_{int(time.time())}",
                            threat_type=signature.threat_type,
                            threat_level=signature.severity,
                            confidence=0.8 - signature.false_positive_rate,
                            description=f"String match: {signature.description}",
                            source_ip=event.source_ip,
                            user_id=event.user_id,
                            detected_at=datetime.utcnow(),
                            evidence={
                                'signature_id': signature.signature_id,
                                'pattern': signature.pattern,
                                'event_id': event.event_id
                            }
                        )
                        detections.append(detection)
                        
            except Exception as e:
                logger.error(f"Error checking signature {signature.signature_id}: {e}")
        
        return detections
    
    async def _check_threat_indicators(self, event: SecurityEvent) -> List[ThreatDetection]:
        """Check event against threat indicators"""
        detections = []
        
        # Check IP indicators
        for indicator in self.threat_indicators.values():
            if not indicator.is_active:
                continue
            
            try:
                if indicator.indicator_type == "ip" and indicator.indicator_value == event.source_ip:
                    for threat_type in indicator.threat_types:
                        detection = ThreatDetection(
                            detection_id=f"ioc_{indicator.indicator_id}_{int(time.time())}",
                            threat_type=threat_type,
                            threat_level=ThreatLevel.HIGH,
                            confidence=indicator.confidence,
                            description=f"Threat indicator match: {indicator.indicator_value}",
                            source_ip=event.source_ip,
                            user_id=event.user_id,
                            detected_at=datetime.utcnow(),
                            evidence={
                                'indicator_id': indicator.indicator_id,
                                'indicator_type': indicator.indicator_type,
                                'indicator_value': indicator.indicator_value,
                                'source': indicator.source,
                                'event_id': event.event_id
                            }
                        )
                        detections.append(detection)
                        
            except Exception as e:
                logger.error(f"Error checking indicator {indicator.indicator_id}: {e}")
        
        return detections
    
    async def _check_attack_patterns(self, event: SecurityEvent) -> List[ThreatDetection]:
        """Check for attack patterns"""
        detections = []
        
        for pattern in self.attack_patterns.values():
            try:
                if await self._matches_attack_pattern(event, pattern):
                    detection = ThreatDetection(
                        detection_id=f"pattern_{pattern.pattern_id}_{int(time.time())}",
                        threat_type=pattern.attack_type,
                        threat_level=ThreatLevel.HIGH,
                        confidence=pattern.confidence,
                        description=f"Attack pattern detected: {pattern.description}",
                        source_ip=event.source_ip,
                        user_id=event.user_id,
                        detected_at=datetime.utcnow(),
                        evidence={
                            'pattern_id': pattern.pattern_id,
                            'indicators': pattern.indicators,
                            'threshold': pattern.threshold,
                            'event_id': event.event_id
                        }
                    )
                    detections.append(detection)
                    
            except Exception as e:
                logger.error(f"Error checking attack pattern {pattern.pattern_id}: {e}")
        
        return detections
    
    async def _matches_attack_pattern(self, event: SecurityEvent, pattern: AttackPattern) -> bool:
        """Check if event matches attack pattern"""
        if pattern.attack_type == ThreatType.BRUTE_FORCE:
            return self._check_brute_force_pattern(event)
        elif pattern.attack_type == ThreatType.DOS_ATTACK:
            return self._check_dos_pattern(event, pattern)
        elif pattern.attack_type == ThreatType.DATA_EXFILTRATION:
            return self._check_data_exfiltration_pattern(event, pattern)
        
        return False
    
    def _check_brute_force_pattern(self, event: SecurityEvent) -> bool:
        """Check for brute force attack pattern"""
        ip_activity = self.ip_activity[event.source_ip]
        
        # Check failed login attempts
        if 'failed_attempts' in ip_activity and ip_activity['failed_attempts'] >= 10:
            time_diff = time.time() - ip_activity.get('first_failed_attempt', time.time())
            if time_diff <= 300:  # Within 5 minutes
                return True
        
        return False
    
    def _check_dos_pattern(self, event: SecurityEvent, pattern: AttackPattern) -> bool:
        """Check for DoS attack pattern"""
        ip_activity = self.ip_activity[event.source_ip]
        
        # Check request rate
        current_time = time.time()
        recent_requests = 0
        
        # Count recent events from this IP
        for stored_event in list(self.security_events):
            if (stored_event.source_ip == event.source_ip and 
                (current_time - stored_event.timestamp.timestamp()) <= pattern.time_window):
                recent_requests += 1
        
        return recent_requests >= pattern.threshold
    
    def _check_data_exfiltration_pattern(self, event: SecurityEvent, pattern: AttackPattern) -> bool:
        """Check for data exfiltration pattern"""
        # Check for large response sizes or multiple data requests
        if 'response_size' in event.payload:
            response_size = event.payload.get('response_size', 0)
            if response_size > 1024 * 1024:  # 1MB threshold
                return True
        
        # Check access to sensitive resources
        sensitive_resources = ['customer', 'invoice', 'financial', 'tax']
        for resource in sensitive_resources:
            if resource in event.resource.lower():
                user_activity = self.user_activity.get(event.user_id, {})
                if len(user_activity.get('resources_accessed', set())) > 10:
                    return True
        
        return False
    
    async def _check_behavioral_anomalies(self, event: SecurityEvent) -> List[ThreatDetection]:
        """Check for behavioral anomalies"""
        detections = []
        
        if not event.user_id:
            return detections
        
        try:
            # Get or create behavioral pattern
            if event.user_id not in self.behavioral_patterns:
                self.behavioral_patterns[event.user_id] = BehavioralPattern(
                    user_id=event.user_id,
                    pattern_type="access_behavior",
                    baseline_metrics={},
                    current_metrics={},
                    deviation_score=0.0,
                    last_updated=datetime.utcnow()
                )
            
            pattern = self.behavioral_patterns[event.user_id]
            
            # Update current metrics
            self._update_behavioral_metrics(event, pattern)
            
            # Calculate deviation score
            deviation_score = self._calculate_behavioral_deviation(pattern)
            pattern.deviation_score = deviation_score
            
            # Check for significant anomalies
            if deviation_score > 0.8:  # High deviation threshold
                detection = ThreatDetection(
                    detection_id=f"behavioral_{event.user_id}_{int(time.time())}",
                    threat_type=ThreatType.SUSPICIOUS_BEHAVIOR,
                    threat_level=ThreatLevel.MEDIUM,
                    confidence=deviation_score,
                    description=f"Behavioral anomaly detected for user {event.user_id}",
                    source_ip=event.source_ip,
                    user_id=event.user_id,
                    detected_at=datetime.utcnow(),
                    evidence={
                        'deviation_score': deviation_score,
                        'baseline_metrics': pattern.baseline_metrics,
                        'current_metrics': pattern.current_metrics,
                        'event_id': event.event_id
                    }
                )
                detections.append(detection)
                
        except Exception as e:
            logger.error(f"Error checking behavioral anomalies for user {event.user_id}: {e}")
        
        return detections
    
    def _update_behavioral_metrics(self, event: SecurityEvent, pattern: BehavioralPattern):
        """Update behavioral metrics for user"""
        current_hour = datetime.utcnow().hour
        
        # Update current metrics
        pattern.current_metrics['access_hour'] = current_hour
        pattern.current_metrics['request_frequency'] = self.user_activity[event.user_id].get('request_count', 0)
        pattern.current_metrics['unique_resources'] = len(self.user_activity[event.user_id].get('resources_accessed', set()))
        pattern.current_metrics['unique_locations'] = len(self.user_activity[event.user_id].get('locations', set()))
        
        # Update baseline if we have enough samples
        pattern.sample_count += 1
        if pattern.sample_count > 10:  # After 10 samples, start updating baseline
            alpha = 0.1  # Learning rate
            for metric, value in pattern.current_metrics.items():
                if metric in pattern.baseline_metrics:
                    pattern.baseline_metrics[metric] = (
                        (1 - alpha) * pattern.baseline_metrics[metric] + alpha * value
                    )
                else:
                    pattern.baseline_metrics[metric] = value
        
        pattern.last_updated = datetime.utcnow()
    
    def _calculate_behavioral_deviation(self, pattern: BehavioralPattern) -> float:
        """Calculate behavioral deviation score"""
        if not pattern.baseline_metrics:
            return 0.0
        
        deviations = []
        
        for metric, baseline_value in pattern.baseline_metrics.items():
            if metric in pattern.current_metrics:
                current_value = pattern.current_metrics[metric]
                
                # Calculate normalized deviation
                if baseline_value > 0:
                    deviation = abs(current_value - baseline_value) / baseline_value
                    deviations.append(min(deviation, 2.0))  # Cap at 200% deviation
        
        # Return average deviation
        return sum(deviations) / len(deviations) if deviations else 0.0
    
    async def _run_custom_detectors(self, event: SecurityEvent) -> List[ThreatDetection]:
        """Run custom detection functions"""
        detections = []
        
        for detector in self.custom_detectors:
            try:
                custom_detections = await detector(event)
                if custom_detections:
                    detections.extend(custom_detections)
            except Exception as e:
                logger.error(f"Error running custom detector: {e}")
        
        return detections
    
    async def _process_detection(self, detection: ThreatDetection):
        """Process threat detection and execute responses"""
        # Store detection
        self.threat_detections.append(detection)
        
        # Update metrics
        self.metrics['threats_detected'] += 1
        self.metrics['threats_by_type'][detection.threat_type.value] += 1
        self.metrics['threats_by_level'][detection.threat_level.value] += 1
        
        # Get response configuration
        response_key = (detection.threat_type, detection.threat_level)
        response_config = self.threat_responses.get(response_key)
        
        if response_config and response_config.auto_execute:
            await self._execute_response(detection, response_config)
        
        logger.warning(f"Threat detected: {detection.threat_type.value} "
                      f"({detection.threat_level.value}) from {detection.source_ip}")
    
    async def _execute_response(self, detection: ThreatDetection, response_config: ThreatResponse):
        """Execute automated threat response"""
        for action in response_config.actions:
            try:
                if action == ResponseAction.BLOCK_IP:
                    self.blocked_ips.add(detection.source_ip)
                    self.metrics['blocked_ips'] += 1
                    logger.info(f"Blocked IP: {detection.source_ip}")
                
                elif action == ResponseAction.BLOCK_USER and detection.user_id:
                    self.blocked_users.add(detection.user_id)
                    self.metrics['blocked_users'] += 1
                    logger.info(f"Blocked user: {detection.user_id}")
                
                elif action == ResponseAction.RATE_LIMIT:
                    # Implement rate limiting logic
                    logger.info(f"Applied rate limiting to: {detection.source_ip}")
                
                elif action == ResponseAction.ALERT:
                    # Send alert (would integrate with alerting system)
                    logger.warning(f"SECURITY ALERT: {detection.description}")
                
                elif action == ResponseAction.ESCALATE:
                    # Escalate to security team
                    logger.critical(f"ESCALATED: {detection.description}")
                
                detection.response_actions.append(action)
                self.metrics['responses_executed'] += 1
                
            except Exception as e:
                logger.error(f"Error executing response action {action.value}: {e}")
    
    def _update_ip_activity(self, event: SecurityEvent):
        """Update IP activity tracking"""
        ip_data = self.ip_activity[event.source_ip]
        current_time = time.time()
        
        ip_data['request_count'] += 1
        ip_data['last_seen'] = current_time
        
        if ip_data['first_seen'] is None:
            ip_data['first_seen'] = current_time
        
        if event.user_agent:
            ip_data['user_agents'].add(event.user_agent)
        
        ip_data['resources_accessed'].add(event.resource)
        
        # Track failed attempts
        if 'failed' in event.event_type.lower() or 'error' in event.event_type.lower():
            ip_data['failed_attempts'] += 1
            if 'first_failed_attempt' not in ip_data:
                ip_data['first_failed_attempt'] = current_time
    
    def _update_user_activity(self, event: SecurityEvent):
        """Update user activity tracking"""
        user_data = self.user_activity[event.user_id]
        
        user_data['request_count'] += 1
        user_data['last_activity'] = datetime.utcnow()
        user_data['locations'].add(event.source_ip)
        user_data['resources_accessed'].add(event.resource)
    
    def _update_response_time_metric(self, response_time: float):
        """Update average response time metric"""
        current_avg = self.metrics['average_response_time']
        total_events = self.metrics['total_events_processed']
        
        self.metrics['average_response_time'] = (
            (current_avg * (total_events - 1) + response_time) / total_events
        )
    
    async def _periodic_cleanup(self):
        """Periodic cleanup of old data"""
        while self.running:
            try:
                await asyncio.sleep(300)  # Run every 5 minutes
                
                current_time = time.time()
                cutoff_time = current_time - self.detection_window
                
                # Clean up old IP activity
                for ip in list(self.ip_activity.keys()):
                    ip_data = self.ip_activity[ip]
                    if ip_data['last_seen'] and ip_data['last_seen'] < cutoff_time:
                        del self.ip_activity[ip]
                
                # Clean up old detections
                cutoff_datetime = datetime.utcnow() - timedelta(seconds=86400)  # 24 hours
                self.threat_detections = [
                    d for d in self.threat_detections 
                    if d.detected_at > cutoff_datetime
                ]
                
                logger.debug("Completed periodic cleanup")
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in periodic cleanup: {e}")
    
    def add_threat_signature(self, signature: ThreatSignature):
        """Add custom threat signature"""
        self.threat_signatures[signature.signature_id] = signature
    
    def add_threat_indicator(self, indicator: ThreatIndicator):
        """Add threat indicator"""
        self.threat_indicators[indicator.indicator_id] = indicator
    
    def add_custom_detector(self, detector_function: Callable):
        """Add custom detection function"""
        self.custom_detectors.append(detector_function)
    
    def is_ip_blocked(self, ip_address: str) -> bool:
        """Check if IP is blocked"""
        return ip_address in self.blocked_ips
    
    def is_user_blocked(self, user_id: str) -> bool:
        """Check if user is blocked"""
        return user_id in self.blocked_users
    
    def unblock_ip(self, ip_address: str):
        """Unblock IP address"""
        self.blocked_ips.discard(ip_address)
    
    def unblock_user(self, user_id: str):
        """Unblock user"""
        self.blocked_users.discard(user_id)
    
    def get_threat_detections(self, 
                            threat_type: Optional[ThreatType] = None,
                            limit: int = 100) -> List[ThreatDetection]:
        """Get threat detections"""
        detections = self.threat_detections
        
        if threat_type:
            detections = [d for d in detections if d.threat_type == threat_type]
        
        return detections[-limit:]
    
    def get_ip_activity(self, ip_address: str) -> Optional[Dict[str, Any]]:
        """Get IP activity data"""
        return self.ip_activity.get(ip_address)
    
    def get_user_activity(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Get user activity data"""
        return self.user_activity.get(user_id)
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get threat detector metrics"""
        detection_rate = 0
        if self.metrics['total_events_processed'] > 0:
            detection_rate = (self.metrics['threats_detected'] / 
                            self.metrics['total_events_processed']) * 100
        
        return {
            **self.metrics,
            'detection_rate': detection_rate,
            'active_ip_tracking': len(self.ip_activity),
            'active_user_tracking': len(self.user_activity),
            'threat_signatures': len(self.threat_signatures),
            'threat_indicators': len(self.threat_indicators),
            'custom_detectors': len(self.custom_detectors),
            'blocked_ips_count': len(self.blocked_ips),
            'blocked_users_count': len(self.blocked_users)
        }


# Factory functions for easy setup
def create_threat_detector(detection_window: int = 300) -> ThreatDetector:
    """Create threat detector instance"""
    return ThreatDetector(detection_window=detection_window)


def create_security_event(source_ip: str,
                        event_type: str,
                        resource: str,
                        payload: Dict[str, Any],
                        user_id: Optional[str] = None,
                        **kwargs) -> SecurityEvent:
    """Create security event"""
    event_id = f"event_{int(time.time())}_{hashlib.md5(source_ip.encode()).hexdigest()[:8]}"
    
    return SecurityEvent(
        event_id=event_id,
        timestamp=datetime.utcnow(),
        source_ip=source_ip,
        user_id=user_id,
        event_type=event_type,
        resource=resource,
        payload=payload,
        **kwargs
    )


async def detect_threats_in_event(event: SecurityEvent,
                                detector: Optional[ThreatDetector] = None) -> List[ThreatDetection]:
    """Detect threats in security event"""
    if not detector:
        detector = create_threat_detector()
        await detector.start()
    
    try:
        return await detector.process_event(event)
    finally:
        if not detector.running:
            await detector.stop()


def get_threat_summary(detector: ThreatDetector) -> Dict[str, Any]:
    """Get threat detector summary"""
    metrics = detector.get_metrics()
    
    return {
        'total_events_processed': metrics['total_events_processed'],
        'threats_detected': metrics['threats_detected'],
        'detection_rate': metrics['detection_rate'],
        'blocked_ips': metrics['blocked_ips_count'],
        'blocked_users': metrics['blocked_users_count'],
        'responses_executed': metrics['responses_executed'],
        'average_response_time': metrics['average_response_time'],
        'top_threat_types': dict(sorted(
            metrics['threats_by_type'].items(),
            key=lambda x: x[1],
            reverse=True
        )[:5])
    }