"""
Threat Intelligence Platform - Core Platform Security

Comprehensive threat intelligence and analysis system for the TaxPoynt platform.
Provides threat analysis, intelligence gathering, and predictive security insights.
"""

import asyncio
import logging
import time
import uuid
import hashlib
import json
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Set, Union, Callable, Tuple
from enum import Enum
from dataclasses import dataclass, field
from collections import defaultdict, deque
import re
import ipaddress

logger = logging.getLogger(__name__)


class ThreatCategory(Enum):
    """Categories of threats"""
    MALWARE = "malware"
    PHISHING = "phishing"
    BOTNET = "botnet"
    APT = "apt"  # Advanced Persistent Threat
    RANSOMWARE = "ransomware"
    DATA_BREACH = "data_breach"
    INSIDER_THREAT = "insider_threat"
    SUPPLY_CHAIN = "supply_chain"
    WEB_ATTACK = "web_attack"
    NETWORK_ATTACK = "network_attack"
    SOCIAL_ENGINEERING = "social_engineering"
    FRAUD = "fraud"


class ThreatSeverity(Enum):
    """Threat severity levels"""
    INFO = "info"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class IndicatorType(Enum):
    """Types of threat indicators"""
    IP_ADDRESS = "ip_address"
    DOMAIN = "domain"
    URL = "url"
    EMAIL = "email"
    FILE_HASH = "file_hash"
    USER_AGENT = "user_agent"
    CERTIFICATE_HASH = "certificate_hash"
    ATTACK_PATTERN = "attack_pattern"
    BEHAVIOR_PATTERN = "behavior_pattern"
    GEOLOCATION = "geolocation"


class IntelligenceSource(Enum):
    """Sources of threat intelligence"""
    INTERNAL = "internal"
    COMMERCIAL_FEED = "commercial_feed"
    OPEN_SOURCE = "open_source"
    GOVERNMENT = "government"
    INDUSTRY_SHARING = "industry_sharing"
    HONEYPOT = "honeypot"
    SANDBOX = "sandbox"
    ANALYST_RESEARCH = "analyst_research"


class ThreatConfidence(Enum):
    """Confidence levels for threat intelligence"""
    UNKNOWN = "unknown"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CONFIRMED = "confirmed"


@dataclass
class ThreatIndicator:
    """Threat indicator with intelligence"""
    indicator_id: str
    indicator_type: IndicatorType
    value: str
    threat_categories: List[ThreatCategory]
    severity: ThreatSeverity
    confidence: ThreatConfidence
    source: IntelligenceSource
    first_seen: datetime
    last_seen: datetime
    tags: List[str] = field(default_factory=list)
    attributes: Dict[str, Any] = field(default_factory=dict)
    false_positive_score: float = 0.0
    reputation_score: float = 0.0
    context: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ThreatActor:
    """Threat actor profile"""
    actor_id: str
    name: str
    aliases: List[str]
    threat_categories: List[ThreatCategory]
    sophistication_level: str
    motivation: List[str]
    target_sectors: List[str]
    attack_patterns: List[str]
    tools: List[str]
    infrastructure: List[str] = field(default_factory=list)
    attribution_confidence: ThreatConfidence = ThreatConfidence.UNKNOWN
    first_observed: datetime = field(default_factory=datetime.utcnow)
    last_activity: datetime = field(default_factory=datetime.utcnow)


@dataclass
class ThreatCampaign:
    """Threat campaign tracking"""
    campaign_id: str
    name: str
    threat_actors: List[str]
    threat_categories: List[ThreatCategory]
    start_date: datetime
    end_date: Optional[datetime]
    targets: List[str]
    indicators: List[str]
    attack_patterns: List[str]
    objectives: List[str]
    status: str = "active"
    confidence: ThreatConfidence = ThreatConfidence.MEDIUM


@dataclass
class ThreatIntelligenceReport:
    """Comprehensive threat intelligence report"""
    report_id: str
    title: str
    summary: str
    threat_categories: List[ThreatCategory]
    severity: ThreatSeverity
    indicators: List[ThreatIndicator]
    actors: List[ThreatActor]
    campaigns: List[ThreatCampaign]
    recommendations: List[str]
    mitigations: List[str]
    created_at: datetime = field(default_factory=datetime.utcnow)
    analyst: Optional[str] = None
    sources: List[str] = field(default_factory=list)


@dataclass
class ThreatAssessment:
    """Threat assessment for specific context"""
    assessment_id: str
    target: str  # Service, IP, domain, etc.
    threat_level: ThreatSeverity
    confidence: ThreatConfidence
    matching_indicators: List[ThreatIndicator]
    risk_factors: List[str]
    recommendations: List[str]
    assessment_timestamp: datetime = field(default_factory=datetime.utcnow)


class ThreatIntelligencePlatform:
    """
    Comprehensive threat intelligence platform for the TaxPoynt ecosystem.
    
    Provides threat intelligence for:
    - SI Services (ERP integration threats, certificate-based attacks, etc.)
    - APP Services (FIRS communication threats, taxpayer targeting, etc.) 
    - Hybrid Services (Cross-service attacks, billing fraud, etc.)
    - Core Platform (Authentication threats, infrastructure attacks, etc.)
    - External Integrations (Third-party threats, supply chain attacks, etc.)
    """
    
    def __init__(self):
        # Threat intelligence data
        self.threat_indicators: Dict[str, ThreatIndicator] = {}
        self.threat_actors: Dict[str, ThreatActor] = {}
        self.threat_campaigns: Dict[str, ThreatCampaign] = {}
        self.intelligence_reports: List[ThreatIntelligenceReport] = []
        
        # Indicator lookups for fast searching
        self.indicators_by_type: Dict[IndicatorType, Set[str]] = defaultdict(set)
        self.indicators_by_value: Dict[str, str] = {}  # value -> indicator_id
        
        # Feed management
        self.intelligence_feeds: Dict[str, Dict[str, Any]] = {}
        self.feed_update_status: Dict[str, datetime] = {}
        
        # Analysis and correlation
        self.threat_correlations: Dict[str, List[str]] = defaultdict(list)
        self.behavioral_patterns: Dict[str, Dict[str, Any]] = {}
        
        # Processing queues
        self.indicator_processing_queue: asyncio.Queue = asyncio.Queue()
        self.analysis_queue: asyncio.Queue = asyncio.Queue()
        self.enrichment_queue: asyncio.Queue = asyncio.Queue()
        
        # Background tasks
        self._running = False
        self._feed_updater_task = None
        self._indicator_processor_task = None
        self._analyzer_task = None
        self._enricher_task = None
        
        # Dependencies
        self.security_orchestrator = None
        self.vulnerability_scanner = None
        self.metrics_aggregator = None
        
        # Configuration
        self.indicator_retention_days = 365
        self.auto_enrichment_enabled = True
        self.correlation_enabled = True
        self.reputation_scoring_enabled = True
        
        # Statistics
        self.stats = {
            "total_indicators": 0,
            "indicators_by_type": defaultdict(int),
            "indicators_by_confidence": defaultdict(int),
            "threat_assessments": 0,
            "feed_updates": 0,
            "correlations_found": 0,
            "false_positives": 0
        }
        
        # Event handlers
        self.threat_detected_handlers: List[Callable] = []
        self.indicator_added_handlers: List[Callable] = []
        self.campaign_detected_handlers: List[Callable] = []
    
    # === Dependency Injection ===
    
    def set_security_orchestrator(self, security_orchestrator):
        """Inject security orchestrator dependency"""
        self.security_orchestrator = security_orchestrator
    
    def set_vulnerability_scanner(self, vulnerability_scanner):
        """Inject vulnerability scanner dependency"""
        self.vulnerability_scanner = vulnerability_scanner
    
    def set_metrics_aggregator(self, metrics_aggregator):
        """Inject metrics aggregator dependency"""
        self.metrics_aggregator = metrics_aggregator
    
    # === Threat Indicator Management ===
    
    async def add_threat_indicator(
        self,
        indicator_type: IndicatorType,
        value: str,
        threat_categories: List[ThreatCategory],
        severity: ThreatSeverity,
        confidence: ThreatConfidence,
        source: IntelligenceSource,
        tags: Optional[List[str]] = None,
        attributes: Optional[Dict[str, Any]] = None,
        context: Optional[Dict[str, Any]] = None
    ) -> str:
        """Add a new threat indicator"""
        
        # Check if indicator already exists
        if value in self.indicators_by_value:
            existing_id = self.indicators_by_value[value]
            await self._update_existing_indicator(existing_id, severity, confidence, source)
            return existing_id
        
        indicator_id = str(uuid.uuid4())
        
        indicator = ThreatIndicator(
            indicator_id=indicator_id,
            indicator_type=indicator_type,
            value=value,
            threat_categories=threat_categories,
            severity=severity,
            confidence=confidence,
            source=source,
            first_seen=datetime.utcnow(),
            last_seen=datetime.utcnow(),
            tags=tags or [],
            attributes=attributes or {},
            context=context or {}
        )
        
        # Validate indicator
        if not self._validate_indicator(indicator):
            logger.warning(f"Invalid indicator rejected: {value}")
            return ""
        
        # Store indicator
        self.threat_indicators[indicator_id] = indicator
        self.indicators_by_type[indicator_type].add(indicator_id)
        self.indicators_by_value[value] = indicator_id
        
        # Update statistics
        self.stats["total_indicators"] += 1
        self.stats["indicators_by_type"][indicator_type.value] += 1
        self.stats["indicators_by_confidence"][confidence.value] += 1
        
        # Queue for processing
        await self.indicator_processing_queue.put(indicator)
        
        # Notify handlers
        await self._notify_indicator_added_handlers(indicator)
        
        logger.info(f"Added threat indicator: {indicator_type.value} - {value}")
        return indicator_id
    
    async def _update_existing_indicator(self, indicator_id: str, severity: ThreatSeverity, confidence: ThreatConfidence, source: IntelligenceSource):
        """Update existing indicator with new intelligence"""
        if indicator_id not in self.threat_indicators:
            return
        
        indicator = self.threat_indicators[indicator_id]
        
        # Update last seen
        indicator.last_seen = datetime.utcnow()
        
        # Update severity if higher
        if self._severity_weight(severity) > self._severity_weight(indicator.severity):
            indicator.severity = severity
        
        # Update confidence if higher  
        if self._confidence_weight(confidence) > self._confidence_weight(indicator.confidence):
            indicator.confidence = confidence
        
        # Add source if not already present
        if source not in indicator.attributes.get("sources", []):
            if "sources" not in indicator.attributes:
                indicator.attributes["sources"] = []
            indicator.attributes["sources"].append(source.value)
        
        logger.debug(f"Updated existing indicator: {indicator_id}")
    
    def _validate_indicator(self, indicator: ThreatIndicator) -> bool:
        """Validate threat indicator"""
        try:
            # Validate IP addresses
            if indicator.indicator_type == IndicatorType.IP_ADDRESS:
                ipaddress.ip_address(indicator.value)
            
            # Validate domains
            elif indicator.indicator_type == IndicatorType.DOMAIN:
                if not re.match(r'^[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', indicator.value):
                    return False
            
            # Validate URLs
            elif indicator.indicator_type == IndicatorType.URL:
                if not re.match(r'^https?://', indicator.value):
                    return False
            
            # Validate email addresses
            elif indicator.indicator_type == IndicatorType.EMAIL:
                if not re.match(r'^[^@]+@[^@]+\.[^@]+$', indicator.value):
                    return False
            
            # Validate file hashes
            elif indicator.indicator_type == IndicatorType.FILE_HASH:
                if not re.match(r'^[a-fA-F0-9]{32,128}$', indicator.value):
                    return False
            
            return True
            
        except Exception:
            return False
    
    # === Threat Assessment ===
    
    async def assess_threat(
        self,
        target: str,
        target_type: str,
        context: Optional[Dict[str, Any]] = None
    ) -> ThreatAssessment:
        """Assess threat level for a specific target"""
        
        assessment_id = str(uuid.uuid4())
        matching_indicators = []
        risk_factors = []
        
        # Look for matching indicators
        if target_type == "ip_address":
            matching_indicators = await self._find_ip_indicators(target)
        elif target_type == "domain":
            matching_indicators = await self._find_domain_indicators(target)
        elif target_type == "url":
            matching_indicators = await self._find_url_indicators(target)
        elif target_type == "email":
            matching_indicators = await self._find_email_indicators(target)
        elif target_type == "file_hash":
            matching_indicators = await self._find_hash_indicators(target)
        
        # Calculate threat level
        threat_level = self._calculate_threat_level(matching_indicators)
        confidence = self._calculate_assessment_confidence(matching_indicators)
        
        # Generate risk factors
        risk_factors = self._generate_risk_factors(matching_indicators, context)
        
        # Generate recommendations
        recommendations = self._generate_threat_recommendations(threat_level, matching_indicators, risk_factors)
        
        assessment = ThreatAssessment(
            assessment_id=assessment_id,
            target=target,
            threat_level=threat_level,
            confidence=confidence,
            matching_indicators=matching_indicators,
            risk_factors=risk_factors,
            recommendations=recommendations
        )
        
        # Update statistics
        self.stats["threat_assessments"] += 1
        
        # Send metrics if available
        if self.metrics_aggregator:
            await self._send_assessment_metrics(assessment)
        
        return assessment
    
    async def _find_ip_indicators(self, ip_address: str) -> List[ThreatIndicator]:
        """Find threat indicators for an IP address"""
        indicators = []
        
        # Direct IP match
        if ip_address in self.indicators_by_value:
            indicator_id = self.indicators_by_value[ip_address]
            indicators.append(self.threat_indicators[indicator_id])
        
        # CIDR range matching (simplified)
        try:
            target_ip = ipaddress.ip_address(ip_address)
            for indicator_id in self.indicators_by_type[IndicatorType.IP_ADDRESS]:
                indicator = self.threat_indicators[indicator_id]
                if '/' in indicator.value:  # CIDR notation
                    try:
                        network = ipaddress.ip_network(indicator.value, strict=False)
                        if target_ip in network:
                            indicators.append(indicator)
                    except:
                        continue
        except:
            pass
        
        return indicators
    
    async def _find_domain_indicators(self, domain: str) -> List[ThreatIndicator]:
        """Find threat indicators for a domain"""
        indicators = []
        
        # Direct domain match
        if domain in self.indicators_by_value:
            indicator_id = self.indicators_by_value[domain]
            indicators.append(self.threat_indicators[indicator_id])
        
        # Subdomain matching
        domain_parts = domain.split('.')
        for i in range(len(domain_parts)):
            parent_domain = '.'.join(domain_parts[i:])
            if parent_domain in self.indicators_by_value:
                indicator_id = self.indicators_by_value[parent_domain]
                indicators.append(self.threat_indicators[indicator_id])
        
        return indicators
    
    async def _find_url_indicators(self, url: str) -> List[ThreatIndicator]:
        """Find threat indicators for a URL"""
        indicators = []
        
        # Direct URL match
        if url in self.indicators_by_value:
            indicator_id = self.indicators_by_value[url]
            indicators.append(self.threat_indicators[indicator_id])
        
        # Extract domain from URL and check domain indicators
        try:
            from urllib.parse import urlparse
            parsed = urlparse(url)
            domain = parsed.netloc
            domain_indicators = await self._find_domain_indicators(domain)
            indicators.extend(domain_indicators)
        except:
            pass
        
        return indicators
    
    async def _find_email_indicators(self, email: str) -> List[ThreatIndicator]:
        """Find threat indicators for an email address"""
        indicators = []
        
        # Direct email match
        if email in self.indicators_by_value:
            indicator_id = self.indicators_by_value[email]
            indicators.append(self.threat_indicators[indicator_id])
        
        # Check domain part of email
        if '@' in email:
            domain = email.split('@')[1]
            domain_indicators = await self._find_domain_indicators(domain)
            indicators.extend(domain_indicators)
        
        return indicators
    
    async def _find_hash_indicators(self, file_hash: str) -> List[ThreatIndicator]:
        """Find threat indicators for a file hash"""
        indicators = []
        
        # Direct hash match
        if file_hash in self.indicators_by_value:
            indicator_id = self.indicators_by_value[file_hash]
            indicators.append(self.threat_indicators[indicator_id])
        
        return indicators
    
    def _calculate_threat_level(self, indicators: List[ThreatIndicator]) -> ThreatSeverity:
        """Calculate overall threat level from indicators"""
        if not indicators:
            return ThreatSeverity.INFO
        
        # Get highest severity
        max_severity = max(indicators, key=lambda i: self._severity_weight(i.severity)).severity
        
        # Adjust based on number of indicators and confidence
        high_confidence_count = len([i for i in indicators if i.confidence in [ThreatConfidence.HIGH, ThreatConfidence.CONFIRMED]])
        
        if high_confidence_count >= 3 and max_severity.value in ["medium", "high"]:
            return ThreatSeverity.HIGH
        elif high_confidence_count >= 1 and max_severity == ThreatSeverity.CRITICAL:
            return ThreatSeverity.CRITICAL
        
        return max_severity
    
    def _calculate_assessment_confidence(self, indicators: List[ThreatIndicator]) -> ThreatConfidence:
        """Calculate confidence level for threat assessment"""
        if not indicators:
            return ThreatConfidence.LOW
        
        # Average confidence with weighting
        confidence_weights = [self._confidence_weight(i.confidence) for i in indicators]
        avg_confidence = sum(confidence_weights) / len(confidence_weights)
        
        if avg_confidence >= 4:
            return ThreatConfidence.CONFIRMED
        elif avg_confidence >= 3:
            return ThreatConfidence.HIGH
        elif avg_confidence >= 2:
            return ThreatConfidence.MEDIUM
        else:
            return ThreatConfidence.LOW
    
    def _generate_risk_factors(self, indicators: List[ThreatIndicator], context: Optional[Dict[str, Any]]) -> List[str]:
        """Generate risk factors based on indicators and context"""
        risk_factors = []
        
        if not indicators:
            return risk_factors
        
        # Analyze threat categories
        categories = set()
        for indicator in indicators:
            categories.update(indicator.threat_categories)
        
        if ThreatCategory.MALWARE in categories:
            risk_factors.append("Malware association detected")
        
        if ThreatCategory.PHISHING in categories:
            risk_factors.append("Phishing campaign involvement")
        
        if ThreatCategory.BOTNET in categories:
            risk_factors.append("Botnet participation")
        
        if ThreatCategory.APT in categories:
            risk_factors.append("Advanced Persistent Threat indicators")
        
        # Analyze confidence levels
        high_confidence_indicators = [i for i in indicators if i.confidence in [ThreatConfidence.HIGH, ThreatConfidence.CONFIRMED]]
        if len(high_confidence_indicators) >= 2:
            risk_factors.append("Multiple high-confidence threat indicators")
        
        # Analyze recency
        recent_indicators = [i for i in indicators if (datetime.utcnow() - i.last_seen).days <= 7]
        if recent_indicators:
            risk_factors.append("Recent threat activity observed")
        
        # Context-based risk factors
        if context:
            if context.get("internal_network"):
                risk_factors.append("Internal network exposure")
            
            if context.get("external_facing"):
                risk_factors.append("External exposure risk")
            
            if context.get("privileged_access"):
                risk_factors.append("Privileged access potential")
        
        return risk_factors
    
    def _generate_threat_recommendations(self, threat_level: ThreatSeverity, indicators: List[ThreatIndicator], risk_factors: List[str]) -> List[str]:
        """Generate recommendations based on threat assessment"""
        recommendations = []
        
        if threat_level == ThreatSeverity.CRITICAL:
            recommendations.append("IMMEDIATE ACTION: Block target and investigate")
            recommendations.append("Activate incident response procedures")
            recommendations.append("Notify security team and stakeholders")
        
        elif threat_level == ThreatSeverity.HIGH:
            recommendations.append("HIGH PRIORITY: Enhanced monitoring required")
            recommendations.append("Consider blocking or restricting access")
            recommendations.append("Review security controls and policies")
        
        elif threat_level == ThreatSeverity.MEDIUM:
            recommendations.append("Increased monitoring and logging")
            recommendations.append("Review access patterns and behavior")
            recommendations.append("Consider additional security measures")
        
        elif threat_level == ThreatSeverity.LOW:
            recommendations.append("Continue standard monitoring")
            recommendations.append("Periodic review recommended")
        
        # Specific recommendations based on threat categories
        categories = set()
        for indicator in indicators:
            categories.update(indicator.threat_categories)
        
        if ThreatCategory.MALWARE in categories:
            recommendations.append("Deploy additional anti-malware scanning")
            recommendations.append("Quarantine potentially infected systems")
        
        if ThreatCategory.PHISHING in categories:
            recommendations.append("User awareness training recommended")
            recommendations.append("Email security controls review")
        
        if ThreatCategory.BOTNET in categories:
            recommendations.append("Network traffic analysis")
            recommendations.append("Check for command and control communications")
        
        return recommendations[:10]  # Limit to top 10 recommendations
    
    # === Security Event Analysis ===
    
    async def analyze_security_event(self, security_event) -> Dict[str, Any]:
        """Analyze security event against threat intelligence"""
        analysis_result = {
            "event_id": security_event.event_id,
            "threat_indicators_found": [],
            "threat_level": "low",
            "confidence": "low",
            "analysis_timestamp": datetime.utcnow(),
            "recommendations": []
        }
        
        try:
            # Extract potential indicators from event
            potential_indicators = self._extract_indicators_from_event(security_event)
            
            matching_indicators = []
            for indicator_value, indicator_type in potential_indicators:
                assessment = await self.assess_threat(indicator_value, indicator_type)
                if assessment.matching_indicators:
                    matching_indicators.extend(assessment.matching_indicators)
            
            if matching_indicators:
                analysis_result["threat_indicators_found"] = [
                    {
                        "indicator_id": ind.indicator_id,
                        "type": ind.indicator_type.value,
                        "value": ind.value,
                        "severity": ind.severity.value,
                        "confidence": ind.confidence.value,
                        "threat_categories": [cat.value for cat in ind.threat_categories]
                    }
                    for ind in matching_indicators
                ]
                
                # Calculate overall threat level
                threat_level = self._calculate_threat_level(matching_indicators)
                confidence = self._calculate_assessment_confidence(matching_indicators)
                
                analysis_result["threat_level"] = threat_level.value
                analysis_result["confidence"] = confidence.value
                analysis_result["recommendations"] = self._generate_threat_recommendations(
                    threat_level, matching_indicators, []
                )
                
                # Trigger handlers if significant threat found
                if threat_level in [ThreatSeverity.HIGH, ThreatSeverity.CRITICAL]:
                    await self._notify_threat_detected_handlers(security_event, matching_indicators)
        
        except Exception as e:
            logger.error(f"Error analyzing security event: {e}")
            analysis_result["error"] = str(e)
        
        return analysis_result
    
    def _extract_indicators_from_event(self, security_event) -> List[Tuple[str, str]]:
        """Extract potential threat indicators from security event"""
        indicators = []
        
        # Extract from user context
        if security_event.user_context:
            # Source IP
            if "source_ip" in security_event.user_context:
                indicators.append((security_event.user_context["source_ip"], "ip_address"))
            
            # User agent
            if "user_agent" in security_event.user_context:
                indicators.append((security_event.user_context["user_agent"], "user_agent"))
        
        # Extract from event details
        if security_event.details:
            # URLs
            url_pattern = r'https?://[^\s]+'
            urls = re.findall(url_pattern, str(security_event.details))
            for url in urls:
                indicators.append((url, "url"))
            
            # Email addresses
            email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
            emails = re.findall(email_pattern, str(security_event.details))
            for email in emails:
                indicators.append((email, "email"))
            
            # File hashes
            hash_pattern = r'\b[a-fA-F0-9]{32,128}\b'
            hashes = re.findall(hash_pattern, str(security_event.details))
            for hash_val in hashes:
                indicators.append((hash_val, "file_hash"))
        
        return indicators
    
    # === Threat Intelligence Feeds ===
    
    def register_intelligence_feed(
        self,
        feed_name: str,
        feed_url: str,
        feed_type: str,
        update_interval_hours: int = 24,
        api_key: Optional[str] = None,
        format_type: str = "json"
    ) -> bool:
        """Register a threat intelligence feed"""
        try:
            feed_config = {
                "feed_name": feed_name,
                "feed_url": feed_url,
                "feed_type": feed_type,
                "update_interval_hours": update_interval_hours,
                "api_key": api_key,
                "format_type": format_type,
                "enabled": True,
                "last_update": None,
                "total_indicators": 0,
                "errors": 0
            }
            
            self.intelligence_feeds[feed_name] = feed_config
            logger.info(f"Registered intelligence feed: {feed_name}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to register intelligence feed {feed_name}: {e}")
            return False
    
    async def update_intelligence_feeds(self, feed_name: Optional[str] = None):
        """Update intelligence feeds"""
        feeds_to_update = [feed_name] if feed_name else list(self.intelligence_feeds.keys())
        
        for feed in feeds_to_update:
            if feed not in self.intelligence_feeds:
                continue
                
            feed_config = self.intelligence_feeds[feed]
            if not feed_config["enabled"]:
                continue
            
            try:
                await self._update_single_feed(feed, feed_config)
                self.stats["feed_updates"] += 1
                
            except Exception as e:
                logger.error(f"Error updating feed {feed}: {e}")
                feed_config["errors"] += 1
    
    async def _update_single_feed(self, feed_name: str, feed_config: Dict[str, Any]):
        """Update a single intelligence feed"""
        # This is a simplified implementation
        # In production, this would fetch from actual threat intelligence APIs
        
        logger.info(f"Updating intelligence feed: {feed_name}")
        
        # Mock feed update with sample indicators
        sample_indicators = [
            {
                "type": "ip_address",
                "value": "192.168.1.100",
                "categories": ["malware"],
                "severity": "medium",
                "confidence": "high"
            },
            {
                "type": "domain",
                "value": "malicious-example.com",
                "categories": ["phishing"],
                "severity": "high",
                "confidence": "confirmed"
            }
        ]
        
        indicators_added = 0
        for indicator_data in sample_indicators:
            try:
                await self.add_threat_indicator(
                    indicator_type=IndicatorType(indicator_data["type"]),
                    value=indicator_data["value"],
                    threat_categories=[ThreatCategory(cat) for cat in indicator_data["categories"]],
                    severity=ThreatSeverity(indicator_data["severity"]),
                    confidence=ThreatConfidence(indicator_data["confidence"]),
                    source=IntelligenceSource.COMMERCIAL_FEED
                )
                indicators_added += 1
                
            except Exception as e:
                logger.error(f"Error adding indicator from feed {feed_name}: {e}")
        
        # Update feed status
        feed_config["last_update"] = datetime.utcnow()
        feed_config["total_indicators"] += indicators_added
        self.feed_update_status[feed_name] = datetime.utcnow()
        
        logger.info(f"Feed {feed_name} updated: {indicators_added} indicators added")
    
    # === Intelligence Reporting ===
    
    def generate_intelligence_report(
        self,
        title: str,
        summary: str,
        threat_categories: List[ThreatCategory],
        severity: ThreatSeverity,
        analyst: Optional[str] = None
    ) -> str:
        """Generate threat intelligence report"""
        
        report_id = str(uuid.uuid4())
        
        # Get relevant indicators
        relevant_indicators = []
        for indicator in self.threat_indicators.values():
            if any(cat in threat_categories for cat in indicator.threat_categories):
                relevant_indicators.append(indicator)
        
        # Get relevant actors and campaigns
        relevant_actors = [actor for actor in self.threat_actors.values() 
                          if any(cat in threat_categories for cat in actor.threat_categories)]
        
        relevant_campaigns = [campaign for campaign in self.threat_campaigns.values()
                             if any(cat in threat_categories for cat in campaign.threat_categories)]
        
        # Generate recommendations
        recommendations = self._generate_report_recommendations(threat_categories, severity, relevant_indicators)
        
        # Generate mitigations
        mitigations = self._generate_report_mitigations(threat_categories, severity)
        
        report = ThreatIntelligenceReport(
            report_id=report_id,
            title=title,
            summary=summary,
            threat_categories=threat_categories,
            severity=severity,
            indicators=relevant_indicators,
            actors=relevant_actors,
            campaigns=relevant_campaigns,
            recommendations=recommendations,
            mitigations=mitigations,
            analyst=analyst
        )
        
        self.intelligence_reports.append(report)
        
        logger.info(f"Generated intelligence report: {title}")
        return report_id
    
    def _generate_report_recommendations(self, categories: List[ThreatCategory], severity: ThreatSeverity, indicators: List[ThreatIndicator]) -> List[str]:
        """Generate recommendations for intelligence report"""
        recommendations = []
        
        if severity in [ThreatSeverity.HIGH, ThreatSeverity.CRITICAL]:
            recommendations.append("Immediate threat assessment and response planning required")
            recommendations.append("Review and update security controls")
            recommendations.append("Enhance monitoring for related indicators")
        
        if ThreatCategory.MALWARE in categories:
            recommendations.append("Deploy advanced malware detection capabilities")
            recommendations.append("Regular system scanning and updates")
        
        if ThreatCategory.PHISHING in categories:
            recommendations.append("Implement email security solutions")
            recommendations.append("Conduct user awareness training")
        
        if ThreatCategory.APT in categories:
            recommendations.append("Implement advanced threat hunting capabilities")
            recommendations.append("Long-term monitoring and analysis")
        
        return recommendations
    
    def _generate_report_mitigations(self, categories: List[ThreatCategory], severity: ThreatSeverity) -> List[str]:
        """Generate mitigations for intelligence report"""
        mitigations = []
        
        if ThreatCategory.MALWARE in categories:
            mitigations.append("Block known malicious indicators")
            mitigations.append("Quarantine infected systems")
            mitigations.append("Update anti-malware signatures")
        
        if ThreatCategory.PHISHING in categories:
            mitigations.append("Block malicious domains and URLs")
            mitigations.append("Implement email filtering")
            mitigations.append("User education programs")
        
        if ThreatCategory.BOTNET in categories:
            mitigations.append("Block command and control communications")
            mitigations.append("Network segmentation")
            mitigations.append("Monitor for unusual traffic patterns")
        
        return mitigations
    
    # === Utility Methods ===
    
    def _severity_weight(self, severity: ThreatSeverity) -> int:
        """Get numeric weight for severity"""
        weights = {
            ThreatSeverity.INFO: 0,
            ThreatSeverity.LOW: 1,
            ThreatSeverity.MEDIUM: 2,
            ThreatSeverity.HIGH: 3,
            ThreatSeverity.CRITICAL: 4
        }
        return weights.get(severity, 0)
    
    def _confidence_weight(self, confidence: ThreatConfidence) -> int:
        """Get numeric weight for confidence"""
        weights = {
            ThreatConfidence.UNKNOWN: 0,
            ThreatConfidence.LOW: 1,
            ThreatConfidence.MEDIUM: 2,
            ThreatConfidence.HIGH: 3,
            ThreatConfidence.CONFIRMED: 4
        }
        return weights.get(confidence, 0)
    
    # === Background Tasks ===
    
    async def start_threat_intelligence(self):
        """Start threat intelligence background tasks"""
        if self._running:
            return
        
        self._running = True
        
        # Start background tasks
        self._feed_updater_task = asyncio.create_task(self._feed_updater())
        self._indicator_processor_task = asyncio.create_task(self._process_indicators())
        self._analyzer_task = asyncio.create_task(self._analyze_threats())
        self._enricher_task = asyncio.create_task(self._enrich_indicators())
        
        logger.info("Threat intelligence platform started")
    
    async def stop_threat_intelligence(self):
        """Stop threat intelligence background tasks"""
        self._running = False
        
        # Cancel tasks
        for task in [self._feed_updater_task, self._indicator_processor_task, 
                     self._analyzer_task, self._enricher_task]:
            if task:
                task.cancel()
        
        logger.info("Threat intelligence platform stopped")
    
    async def _feed_updater(self):
        """Background task for updating intelligence feeds"""
        while self._running:
            try:
                await self.update_intelligence_feeds()
                await asyncio.sleep(3600)  # Update every hour
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in feed updater: {e}")
                await asyncio.sleep(3600)
    
    async def _process_indicators(self):
        """Background task for processing threat indicators"""
        while self._running:
            try:
                # Get indicator from queue with timeout
                indicator = await asyncio.wait_for(self.indicator_processing_queue.get(), timeout=1.0)
                
                # Process the indicator
                await self._process_single_indicator(indicator)
                
                # Mark task as done
                self.indicator_processing_queue.task_done()
                
            except asyncio.TimeoutError:
                continue
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error processing indicator: {e}")
                await asyncio.sleep(1)
    
    async def _analyze_threats(self):
        """Background task for threat analysis"""
        while self._running:
            try:
                # Perform periodic threat analysis
                await self._correlate_threats()
                await asyncio.sleep(1800)  # Every 30 minutes
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in threat analysis: {e}")
                await asyncio.sleep(1800)
    
    async def _enrich_indicators(self):
        """Background task for indicator enrichment"""
        while self._running:
            try:
                if self.auto_enrichment_enabled:
                    await self._enrich_existing_indicators()
                await asyncio.sleep(7200)  # Every 2 hours
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in indicator enrichment: {e}")
                await asyncio.sleep(7200)
    
    async def _process_single_indicator(self, indicator: ThreatIndicator):
        """Process a single threat indicator"""
        try:
            # Calculate reputation score
            if self.reputation_scoring_enabled:
                indicator.reputation_score = self._calculate_reputation_score(indicator)
            
            # Check for correlations
            if self.correlation_enabled:
                await self._find_indicator_correlations(indicator)
            
        except Exception as e:
            logger.error(f"Error processing indicator {indicator.indicator_id}: {e}")
    
    def _calculate_reputation_score(self, indicator: ThreatIndicator) -> float:
        """Calculate reputation score for indicator"""
        score = 0.0
        
        # Base score from severity
        severity_scores = {
            ThreatSeverity.INFO: 0.1,
            ThreatSeverity.LOW: 0.3,
            ThreatSeverity.MEDIUM: 0.5,
            ThreatSeverity.HIGH: 0.8,
            ThreatSeverity.CRITICAL: 1.0
        }
        score += severity_scores.get(indicator.severity, 0.0) * 0.4
        
        # Confidence weighting
        confidence_scores = {
            ThreatConfidence.UNKNOWN: 0.1,
            ThreatConfidence.LOW: 0.3,
            ThreatConfidence.MEDIUM: 0.5,
            ThreatConfidence.HIGH: 0.8,
            ThreatConfidence.CONFIRMED: 1.0
        }
        score += confidence_scores.get(indicator.confidence, 0.0) * 0.3
        
        # Source reliability
        source_scores = {
            IntelligenceSource.CONFIRMED: 1.0,
            IntelligenceSource.GOVERNMENT: 0.9,
            IntelligenceSource.COMMERCIAL_FEED: 0.8,
            IntelligenceSource.ANALYST_RESEARCH: 0.7,
            IntelligenceSource.INDUSTRY_SHARING: 0.6,
            IntelligenceSource.OPEN_SOURCE: 0.5,
            IntelligenceSource.HONEYPOT: 0.6,
            IntelligenceSource.SANDBOX: 0.5,
            IntelligenceSource.INTERNAL: 0.7
        }
        score += source_scores.get(indicator.source, 0.5) * 0.2
        
        # Recency factor
        days_old = (datetime.utcnow() - indicator.last_seen).days
        recency_factor = max(0, 1 - (days_old / 90))  # Decay over 90 days
        score += recency_factor * 0.1
        
        return min(score, 1.0)
    
    async def _find_indicator_correlations(self, indicator: ThreatIndicator):
        """Find correlations for an indicator"""
        correlations = []
        
        # Simple correlation based on shared attributes
        for other_id, other_indicator in self.threat_indicators.items():
            if other_id == indicator.indicator_id:
                continue
            
            correlation_score = self._calculate_correlation_score(indicator, other_indicator)
            if correlation_score > 0.7:
                correlations.append(other_id)
        
        if correlations:
            self.threat_correlations[indicator.indicator_id] = correlations
            self.stats["correlations_found"] += len(correlations)
    
    def _calculate_correlation_score(self, indicator1: ThreatIndicator, indicator2: ThreatIndicator) -> float:
        """Calculate correlation score between two indicators"""
        score = 0.0
        
        # Shared threat categories
        shared_categories = set(indicator1.threat_categories) & set(indicator2.threat_categories)
        if shared_categories:
            score += len(shared_categories) / max(len(indicator1.threat_categories), len(indicator2.threat_categories)) * 0.4
        
        # Shared tags
        shared_tags = set(indicator1.tags) & set(indicator2.tags)
        if shared_tags:
            score += len(shared_tags) / max(len(indicator1.tags), len(indicator2.tags)) * 0.3
        
        # Temporal proximity
        time_diff = abs((indicator1.last_seen - indicator2.last_seen).total_seconds())
        if time_diff < 86400:  # 24 hours
            score += (86400 - time_diff) / 86400 * 0.3
        
        return score
    
    async def _correlate_threats(self):
        """Correlate threats across indicators"""
        # This would implement more sophisticated threat correlation
        pass
    
    async def _enrich_existing_indicators(self):
        """Enrich existing indicators with additional intelligence"""
        # This would implement indicator enrichment from external sources
        pass
    
    # === Event Handlers ===
    
    async def _notify_threat_detected_handlers(self, security_event, indicators: List[ThreatIndicator]):
        """Notify threat detected handlers"""
        for handler in self.threat_detected_handlers:
            try:
                if asyncio.iscoroutinefunction(handler):
                    await handler(security_event, indicators)
                else:
                    handler(security_event, indicators)
            except Exception as e:
                logger.error(f"Error in threat detected handler: {e}")
    
    async def _notify_indicator_added_handlers(self, indicator: ThreatIndicator):
        """Notify indicator added handlers"""
        for handler in self.indicator_added_handlers:
            try:
                if asyncio.iscoroutinefunction(handler):
                    await handler(indicator)
                else:
                    handler(indicator)
            except Exception as e:
                logger.error(f"Error in indicator added handler: {e}")
    
    async def _send_assessment_metrics(self, assessment: ThreatAssessment):
        """Send threat assessment metrics"""
        try:
            if self.metrics_aggregator:
                await self.metrics_aggregator.collect_metric_point(
                    name="threat_assessment",
                    value=1,
                    service_role="core_platform",
                    service_name="threat_intelligence",
                    tags={
                        "threat_level": assessment.threat_level.value,
                        "confidence": assessment.confidence.value,
                        "indicators_found": len(assessment.matching_indicators)
                    }
                )
        except Exception as e:
            logger.error(f"Error sending assessment metrics: {e}")
    
    # === Health and Status ===
    
    def get_threat_intelligence_health(self) -> Dict[str, Any]:
        """Get health status of threat intelligence platform"""
        return {
            "status": "running" if self._running else "stopped",
            "total_indicators": len(self.threat_indicators),
            "indicators_by_type": {t.value: len(ids) for t, ids in self.indicators_by_type.items()},
            "threat_actors": len(self.threat_actors),
            "campaigns": len(self.threat_campaigns),
            "intelligence_feeds": len(self.intelligence_feeds),
            "active_correlations": len(self.threat_correlations),
            "intelligence_reports": len(self.intelligence_reports),
            "statistics": dict(self.stats),
            "configuration": {
                "auto_enrichment_enabled": self.auto_enrichment_enabled,
                "correlation_enabled": self.correlation_enabled,
                "reputation_scoring_enabled": self.reputation_scoring_enabled,
                "indicator_retention_days": self.indicator_retention_days
            }
        }


# Global instance for platform-wide access
threat_intelligence = ThreatIntelligencePlatform()


# Setup functions for easy integration
async def setup_default_threat_intelligence():
    """Setup default threat intelligence configuration"""
    
    # Register sample intelligence feeds
    threat_intelligence.register_intelligence_feed(
        feed_name="sample_malware_feed",
        feed_url="https://example.com/malware-feed",
        feed_type="malware_indicators",
        update_interval_hours=6
    )
    
    threat_intelligence.register_intelligence_feed(
        feed_name="sample_phishing_feed", 
        feed_url="https://example.com/phishing-feed",
        feed_type="phishing_indicators",
        update_interval_hours=4
    )
    
    # Add sample threat indicators
    await threat_intelligence.add_threat_indicator(
        indicator_type=IndicatorType.DOMAIN,
        value="known-malicious.example",
        threat_categories=[ThreatCategory.MALWARE],
        severity=ThreatSeverity.HIGH,
        confidence=ThreatConfidence.HIGH,
        source=IntelligenceSource.ANALYST_RESEARCH,
        tags=["sample", "test"]
    )
    
    logger.info("Default threat intelligence setup completed")


async def shutdown_threat_intelligence():
    """Shutdown threat intelligence platform"""
    await threat_intelligence.stop_threat_intelligence()
    logger.info("Threat intelligence platform shutdown completed")