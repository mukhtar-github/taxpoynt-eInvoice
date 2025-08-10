"""
Validation Engine Data Models
=============================
Pydantic models specific to the universal compliance validation engine.
"""

from datetime import datetime, date
from decimal import Decimal
from typing import Dict, Any, List, Optional, Union, Callable
from pydantic import BaseModel, Field, validator
from enum import Enum
import uuid

# Import from orchestrator models
from ..orchestrator.models import (
    ComplianceFramework, ComplianceStatus, ValidationSeverity,
    ComplianceRule, ValidationResult
)

class ValidationMode(str, Enum):
    """Validation execution modes"""
    STRICT = "strict"          # All rules must pass
    LENIENT = "lenient"        # Allow minor violations
    ADVISORY = "advisory"      # Report issues but don't fail
    QUICK = "quick"           # Fast validation, skip complex rules
    COMPREHENSIVE = "comprehensive"  # Full validation with all rules

class ConflictResolutionStrategy(str, Enum):
    """Strategies for resolving rule conflicts"""
    STRICT_PRECEDENCE = "strict_precedence"    # Higher severity wins
    FRAMEWORK_PRIORITY = "framework_priority"  # Framework priority order
    LATEST_RULE = "latest_rule"               # Most recent rule wins
    MANUAL = "manual"                         # Require manual resolution
    AGGREGATE = "aggregate"                   # Combine all requirements

class ValidationPhase(str, Enum):
    """Validation execution phases"""
    PRE_VALIDATION = "pre_validation"
    STRUCTURAL = "structural"
    BUSINESS_RULES = "business_rules"
    CROSS_FRAMEWORK = "cross_framework"
    POST_VALIDATION = "post_validation"
    FINALIZATION = "finalization"

class PluginStatus(str, Enum):
    """Validation plugin status"""
    ACTIVE = "active"
    INACTIVE = "inactive"
    ERROR = "error"
    LOADING = "loading"
    DISABLED = "disabled"

class ValidationRequest(BaseModel):
    """Universal validation request"""
    request_id: str = Field(default_factory=lambda: str(uuid.uuid4()), description="Unique request identifier")
    data: Dict[str, Any] = Field(..., description="Data to validate")
    frameworks: List[ComplianceFramework] = Field(..., description="Frameworks to validate against")
    validation_mode: ValidationMode = Field(ValidationMode.COMPREHENSIVE, description="Validation mode")
    
    # Context and configuration
    context: Dict[str, Any] = Field(default_factory=dict, description="Validation context")
    rules_override: List[str] = Field(default_factory=list, description="Rules to override/skip")
    custom_rules: List[ComplianceRule] = Field(default_factory=list, description="Additional custom rules")
    
    # Execution preferences
    parallel_execution: bool = Field(True, description="Enable parallel framework validation")
    timeout_seconds: int = Field(300, description="Validation timeout in seconds")
    conflict_resolution: ConflictResolutionStrategy = Field(ConflictResolutionStrategy.STRICT_PRECEDENCE)
    
    # Audit and tracking
    requester_id: Optional[str] = Field(None, description="ID of requester")
    business_context: Optional[str] = Field(None, description="Business context description")
    priority: str = Field("normal", description="Validation priority (low, normal, high, urgent)")
    
    @validator('frameworks')
    def validate_frameworks_not_empty(cls, v):
        """Ensure at least one framework is specified"""
        if not v:
            raise ValueError("At least one compliance framework must be specified")
        return v

class ValidationResponse(BaseModel):
    """Universal validation response"""
    request_id: str = Field(..., description="Original request identifier")
    overall_status: ComplianceStatus = Field(..., description="Overall validation status")
    overall_score: float = Field(..., ge=0, le=100, description="Overall compliance score")
    
    # Execution details
    validation_timestamp: datetime = Field(default_factory=datetime.now)
    execution_time_ms: float = Field(..., description="Total execution time in milliseconds")
    frameworks_validated: List[ComplianceFramework] = Field(..., description="Frameworks that were validated")
    
    # Results by framework
    framework_results: Dict[ComplianceFramework, List[ValidationResult]] = Field(
        default_factory=dict, description="Validation results by framework"
    )
    
    # Cross-framework analysis
    cross_framework_issues: List[str] = Field(default_factory=list, description="Cross-framework conflicts/issues")
    rule_conflicts: List['RuleConflict'] = Field(default_factory=list, description="Detected rule conflicts")
    
    # Aggregated insights
    total_rules_checked: int = Field(0, description="Total rules evaluated", ge=0)
    rules_passed: int = Field(0, description="Rules that passed", ge=0)
    rules_failed: int = Field(0, description="Rules that failed", ge=0)
    rules_skipped: int = Field(0, description="Rules that were skipped", ge=0)
    
    # Issues and recommendations
    critical_issues: List[str] = Field(default_factory=list, description="Critical issues found")
    warnings: List[str] = Field(default_factory=list, description="Warning messages")
    recommendations: List[str] = Field(default_factory=list, description="Improvement recommendations")
    
    # Compliance summary
    compliance_summary: Dict[str, Any] = Field(default_factory=dict, description="Executive compliance summary")
    next_steps: List[str] = Field(default_factory=list, description="Recommended next steps")

class RuleConflict(BaseModel):
    """Represents a conflict between rules from different frameworks"""
    conflict_id: str = Field(default_factory=lambda: str(uuid.uuid4()), description="Conflict identifier")
    conflicting_rules: List[str] = Field(..., description="Rule IDs in conflict")
    frameworks_involved: List[ComplianceFramework] = Field(..., description="Frameworks with conflicting rules")
    
    # Conflict details
    conflict_type: str = Field(..., description="Type of conflict (requirement, format, calculation)")
    conflict_description: str = Field(..., description="Description of the conflict")
    data_field: Optional[str] = Field(None, description="Data field causing conflict")
    
    # Resolution
    resolution_strategy: ConflictResolutionStrategy = Field(..., description="Strategy used to resolve")
    resolution_result: str = Field(..., description="How the conflict was resolved")
    winning_rule: Optional[str] = Field(None, description="Rule that took precedence")
    
    # Impact assessment
    business_impact: str = Field(..., description="Business impact of the conflict")
    severity: ValidationSeverity = Field(..., description="Conflict severity")

class ValidationPlugin(BaseModel):
    """Validation plugin descriptor"""
    plugin_id: str = Field(..., description="Unique plugin identifier")
    plugin_name: str = Field(..., description="Human-readable plugin name")
    framework: ComplianceFramework = Field(..., description="Target compliance framework")
    version: str = Field(..., description="Plugin version")
    
    # Plugin metadata
    description: str = Field(..., description="Plugin description")
    author: str = Field(..., description="Plugin author")
    supported_versions: List[str] = Field(..., description="Supported engine versions")
    
    # Plugin configuration
    status: PluginStatus = Field(PluginStatus.ACTIVE, description="Plugin status")
    priority: int = Field(100, description="Execution priority (lower = higher priority)")
    dependencies: List[str] = Field(default_factory=list, description="Required dependencies")
    
    # Validation capabilities
    supported_phases: List[ValidationPhase] = Field(..., description="Supported validation phases")
    rule_categories: List[str] = Field(..., description="Rule categories handled")
    data_requirements: List[str] = Field(..., description="Required data fields")
    
    # Performance characteristics
    estimated_execution_time: float = Field(0.0, description="Estimated execution time (seconds)")
    memory_usage: str = Field("low", description="Memory usage profile (low, medium, high)")
    thread_safe: bool = Field(True, description="Whether plugin is thread-safe")

class CrossFrameworkResult(BaseModel):
    """Result of cross-framework validation analysis"""
    analysis_id: str = Field(default_factory=lambda: str(uuid.uuid4()), description="Analysis identifier")
    frameworks_analyzed: List[ComplianceFramework] = Field(..., description="Frameworks included in analysis")
    
    # Consistency analysis
    consistent_requirements: List[str] = Field(default_factory=list, description="Requirements that are consistent")
    conflicting_requirements: List[RuleConflict] = Field(default_factory=list, description="Conflicting requirements")
    
    # Gap analysis
    framework_gaps: Dict[ComplianceFramework, List[str]] = Field(
        default_factory=dict, description="Gaps identified per framework"
    )
    missing_validations: List[str] = Field(default_factory=list, description="Validations missing across frameworks")
    
    # Compliance harmonization
    harmonization_score: float = Field(0.0, ge=0, le=100, description="How well frameworks align")
    harmonization_issues: List[str] = Field(default_factory=list, description="Issues preventing harmonization")
    
    # Recommendations
    framework_prioritization: Dict[ComplianceFramework, int] = Field(
        default_factory=dict, description="Recommended framework priority order"
    )
    optimization_suggestions: List[str] = Field(default_factory=list, description="Optimization suggestions")

class AggregatedValidationResult(BaseModel):
    """Aggregated validation result across all frameworks"""
    aggregation_id: str = Field(default_factory=lambda: str(uuid.uuid4()), description="Aggregation identifier")
    source_request_id: str = Field(..., description="Original validation request ID")
    
    # Overall metrics
    overall_compliance_score: float = Field(..., ge=0, le=100, description="Weighted overall compliance score")
    framework_scores: Dict[ComplianceFramework, float] = Field(..., description="Individual framework scores")
    framework_weights: Dict[ComplianceFramework, float] = Field(..., description="Framework weights used")
    
    # Issue aggregation
    total_critical_issues: int = Field(0, description="Total critical issues across frameworks", ge=0)
    total_high_issues: int = Field(0, description="Total high severity issues", ge=0)
    total_medium_issues: int = Field(0, description="Total medium severity issues", ge=0)
    total_low_issues: int = Field(0, description="Total low severity issues", ge=0)
    
    # Compliance categorization
    fully_compliant_frameworks: List[ComplianceFramework] = Field(
        default_factory=list, description="Frameworks with full compliance"
    )
    partially_compliant_frameworks: List[ComplianceFramework] = Field(
        default_factory=list, description="Frameworks with partial compliance"
    )
    non_compliant_frameworks: List[ComplianceFramework] = Field(
        default_factory=list, description="Non-compliant frameworks"
    )
    
    # Business impact assessment
    business_risk_level: str = Field("low", description="Overall business risk level")
    compliance_readiness: str = Field("ready", description="Readiness for compliance certification")
    estimated_remediation_effort: str = Field("minimal", description="Estimated effort to achieve full compliance")
    
    # Action planning
    immediate_actions: List[str] = Field(default_factory=list, description="Actions requiring immediate attention")
    short_term_actions: List[str] = Field(default_factory=list, description="Actions for next 30 days")
    long_term_actions: List[str] = Field(default_factory=list, description="Strategic compliance improvements")
    
    # Quality metrics
    validation_confidence: float = Field(100.0, ge=0, le=100, description="Confidence in validation results")
    data_completeness: float = Field(100.0, ge=0, le=100, description="Completeness of input data")
    rule_coverage: float = Field(100.0, ge=0, le=100, description="Percentage of applicable rules checked")

class ValidationExecutionContext(BaseModel):
    """Context for validation execution"""
    execution_id: str = Field(default_factory=lambda: str(uuid.uuid4()), description="Execution identifier")
    request: ValidationRequest = Field(..., description="Original validation request")
    
    # Execution state
    current_phase: ValidationPhase = Field(ValidationPhase.PRE_VALIDATION, description="Current execution phase")
    start_time: datetime = Field(default_factory=datetime.now, description="Execution start time")
    
    # Framework execution tracking
    framework_execution_order: List[ComplianceFramework] = Field(
        default_factory=list, description="Order of framework execution"
    )
    completed_frameworks: List[ComplianceFramework] = Field(
        default_factory=list, description="Completed frameworks"
    )
    failed_frameworks: List[ComplianceFramework] = Field(
        default_factory=list, description="Failed frameworks"
    )
    
    # Intermediate results
    intermediate_results: Dict[ComplianceFramework, List[ValidationResult]] = Field(
        default_factory=dict, description="Intermediate validation results"
    )
    detected_conflicts: List[RuleConflict] = Field(
        default_factory=list, description="Conflicts detected during execution"
    )
    
    # Performance tracking
    framework_execution_times: Dict[ComplianceFramework, float] = Field(
        default_factory=dict, description="Execution time per framework (ms)"
    )
    memory_usage_peak: Optional[float] = Field(None, description="Peak memory usage (MB)")
    
    # Error handling
    execution_errors: List[str] = Field(default_factory=list, description="Execution errors encountered")
    recovery_actions: List[str] = Field(default_factory=list, description="Recovery actions taken")

class PluginExecutionResult(BaseModel):
    """Result of plugin execution"""
    plugin_id: str = Field(..., description="Plugin identifier")
    framework: ComplianceFramework = Field(..., description="Framework validated")
    phase: ValidationPhase = Field(..., description="Validation phase")
    
    # Execution details
    execution_start: datetime = Field(..., description="Plugin execution start time")
    execution_duration_ms: float = Field(..., description="Execution duration in milliseconds")
    status: ComplianceStatus = Field(..., description="Plugin execution status")
    
    # Results
    validation_results: List[ValidationResult] = Field(
        default_factory=list, description="Validation results from plugin"
    )
    rules_processed: int = Field(0, description="Number of rules processed", ge=0)
    
    # Plugin-specific data
    plugin_metadata: Dict[str, Any] = Field(default_factory=dict, description="Plugin-specific metadata")
    performance_metrics: Dict[str, Any] = Field(default_factory=dict, description="Performance metrics")
    
    # Error handling
    errors: List[str] = Field(default_factory=list, description="Errors encountered during execution")
    warnings: List[str] = Field(default_factory=list, description="Warnings generated during execution")

class ValidationCache(BaseModel):
    """Validation result cache entry"""
    cache_key: str = Field(..., description="Cache key for the validation")
    request_hash: str = Field(..., description="Hash of the original request")
    
    # Cached data
    cached_response: ValidationResponse = Field(..., description="Cached validation response")
    cache_timestamp: datetime = Field(default_factory=datetime.now, description="When result was cached")
    
    # Cache metadata
    cache_ttl_seconds: int = Field(3600, description="Time to live in seconds")
    access_count: int = Field(0, description="Number of times cache was accessed", ge=0)
    last_access: datetime = Field(default_factory=datetime.now, description="Last access timestamp")
    
    # Invalidation criteria
    frameworks_involved: List[ComplianceFramework] = Field(..., description="Frameworks in cached result")
    data_fingerprint: str = Field(..., description="Fingerprint of validated data")
    
    @property
    def is_expired(self) -> bool:
        """Check if cache entry is expired"""
        return (datetime.now() - self.cache_timestamp).total_seconds() > self.cache_ttl_seconds
    
    @property
    def is_valid(self) -> bool:
        """Check if cache entry is still valid"""
        return not self.is_expired and self.cached_response.overall_status != ComplianceStatus.ERROR

# Ensure forward reference resolution
RuleConflict.model_rebuild()
ValidationResponse.model_rebuild()