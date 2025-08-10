"""
Validation Error Handling Service for APP Role

This service handles validation errors including:
- Error aggregation and classification
- Error recovery suggestions
- Error reporting and logging
- Error pattern analysis
- User-friendly error messages
"""

import json
import traceback
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List, Union, Callable
from dataclasses import dataclass, field
from enum import Enum
import logging
from collections import defaultdict, Counter
import hashlib

from .firs_validator import FIRSValidationReport, ValidationResult, ValidationSeverity
from .submission_validator import SubmissionValidationReport, SubmissionCheck, CheckStatus
from .format_validator import FormatValidationReport, FormatValidationResult, FormatSeverity
from .completeness_checker import CompletenessReport, CompletenessResult, CompletionSeverity

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ErrorCategory(Enum):
    """Validation error categories"""
    CRITICAL = "critical"
    FUNCTIONAL = "functional"
    DATA_QUALITY = "data_quality"
    COMPLIANCE = "compliance"
    PERFORMANCE = "performance"
    USABILITY = "usability"
    BUSINESS_RULE = "business_rule"


class ErrorPattern(Enum):
    """Common error patterns"""
    MISSING_REQUIRED_FIELD = "missing_required_field"
    INVALID_FORMAT = "invalid_format"
    BUSINESS_RULE_VIOLATION = "business_rule_violation"
    CALCULATION_ERROR = "calculation_error"
    REFERENCE_ERROR = "reference_error"
    PERMISSION_ERROR = "permission_error"
    SYSTEM_ERROR = "system_error"


class ErrorResolution(Enum):
    """Error resolution status"""
    UNRESOLVED = "unresolved"
    RESOLVED = "resolved"
    PARTIALLY_RESOLVED = "partially_resolved"
    CANNOT_RESOLVE = "cannot_resolve"
    IGNORED = "ignored"


@dataclass
class ValidationError:
    """Unified validation error"""
    error_id: str
    source: str
    category: ErrorCategory
    pattern: ErrorPattern
    severity: str
    field_path: str
    message: str
    details: Optional[str] = None
    suggestion: Optional[str] = None
    resolution: ErrorResolution = ErrorResolution.UNRESOLVED
    timestamp: datetime = field(default_factory=datetime.utcnow)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ErrorGroup:
    """Group of related errors"""
    group_id: str
    category: ErrorCategory
    pattern: ErrorPattern
    errors: List[ValidationError]
    count: int
    severity_distribution: Dict[str, int]
    common_fields: List[str]
    suggested_actions: List[str]
    estimated_fix_time: int
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ErrorAnalysis:
    """Error analysis results"""
    total_errors: int
    error_categories: Dict[ErrorCategory, int]
    error_patterns: Dict[ErrorPattern, int]
    severity_distribution: Dict[str, int]
    most_common_errors: List[ErrorGroup]
    resolution_suggestions: List[str]
    estimated_total_fix_time: int
    error_trends: Dict[str, Any]
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ErrorHandlingReport:
    """Comprehensive error handling report"""
    document_id: str
    validation_timestamp: datetime
    total_errors: int
    resolved_errors: int
    unresolved_errors: int
    error_groups: List[ErrorGroup]
    error_analysis: ErrorAnalysis
    recovery_actions: List[str]
    user_friendly_summary: str
    detailed_report: str
    metadata: Dict[str, Any] = field(default_factory=dict)


class ValidationErrorHandler:
    """
    Validation error handling service for APP role
    
    Handles:
    - Error aggregation and classification
    - Error recovery suggestions
    - Error reporting and logging
    - Error pattern analysis
    - User-friendly error messages
    """
    
    def __init__(self, enable_analytics: bool = True):
        self.enable_analytics = enable_analytics
        
        # Error classification rules
        self.classification_rules = self._load_classification_rules()
        
        # Error pattern detection
        self.pattern_detectors = self._load_pattern_detectors()
        
        # Recovery strategies
        self.recovery_strategies = self._load_recovery_strategies()
        
        # Error history for analytics
        self.error_history: List[ValidationError] = []
        self.error_patterns: Dict[str, int] = defaultdict(int)
        
        # User-friendly message templates
        self.message_templates = self._load_message_templates()
        
        # Metrics
        self.metrics = {
            'total_errors_handled': 0,
            'errors_by_category': defaultdict(int),
            'errors_by_pattern': defaultdict(int),
            'resolution_rate': 0.0,
            'average_fix_time': 0.0,
            'user_satisfaction_score': 0.0
        }
    
    def _load_classification_rules(self) -> Dict[str, Dict[str, Any]]:
        """Load error classification rules"""
        return {
            'critical_missing_field': {
                'category': ErrorCategory.CRITICAL,
                'pattern': ErrorPattern.MISSING_REQUIRED_FIELD,
                'keywords': ['required', 'mandatory', 'critical', 'missing'],
                'severity_map': {'CRITICAL': ErrorCategory.CRITICAL, 'ERROR': ErrorCategory.FUNCTIONAL}
            },
            'format_violation': {
                'category': ErrorCategory.DATA_QUALITY,
                'pattern': ErrorPattern.INVALID_FORMAT,
                'keywords': ['format', 'pattern', 'invalid', 'malformed'],
                'severity_map': {'ERROR': ErrorCategory.DATA_QUALITY, 'WARNING': ErrorCategory.USABILITY}
            },
            'business_rule_violation': {
                'category': ErrorCategory.BUSINESS_RULE,
                'pattern': ErrorPattern.BUSINESS_RULE_VIOLATION,
                'keywords': ['business', 'rule', 'policy', 'compliance'],
                'severity_map': {'ERROR': ErrorCategory.BUSINESS_RULE, 'WARNING': ErrorCategory.COMPLIANCE}
            },
            'calculation_error': {
                'category': ErrorCategory.FUNCTIONAL,
                'pattern': ErrorPattern.CALCULATION_ERROR,
                'keywords': ['calculation', 'amount', 'total', 'sum', 'mismatch'],
                'severity_map': {'ERROR': ErrorCategory.FUNCTIONAL, 'WARNING': ErrorCategory.DATA_QUALITY}
            },
            'reference_error': {
                'category': ErrorCategory.FUNCTIONAL,
                'pattern': ErrorPattern.REFERENCE_ERROR,
                'keywords': ['reference', 'lookup', 'not found', 'invalid'],
                'severity_map': {'ERROR': ErrorCategory.FUNCTIONAL, 'WARNING': ErrorCategory.DATA_QUALITY}
            },
            'permission_error': {
                'category': ErrorCategory.CRITICAL,
                'pattern': ErrorPattern.PERMISSION_ERROR,
                'keywords': ['permission', 'access', 'unauthorized', 'forbidden'],
                'severity_map': {'ERROR': ErrorCategory.CRITICAL, 'WARNING': ErrorCategory.USABILITY}
            },
            'system_error': {
                'category': ErrorCategory.CRITICAL,
                'pattern': ErrorPattern.SYSTEM_ERROR,
                'keywords': ['system', 'internal', 'exception', 'error'],
                'severity_map': {'CRITICAL': ErrorCategory.CRITICAL, 'ERROR': ErrorCategory.FUNCTIONAL}
            }
        }
    
    def _load_pattern_detectors(self) -> Dict[ErrorPattern, Callable]:
        """Load error pattern detectors"""
        return {
            ErrorPattern.MISSING_REQUIRED_FIELD: self._detect_missing_field_pattern,
            ErrorPattern.INVALID_FORMAT: self._detect_format_pattern,
            ErrorPattern.BUSINESS_RULE_VIOLATION: self._detect_business_rule_pattern,
            ErrorPattern.CALCULATION_ERROR: self._detect_calculation_pattern,
            ErrorPattern.REFERENCE_ERROR: self._detect_reference_pattern,
            ErrorPattern.PERMISSION_ERROR: self._detect_permission_pattern,
            ErrorPattern.SYSTEM_ERROR: self._detect_system_pattern
        }
    
    def _load_recovery_strategies(self) -> Dict[ErrorPattern, Dict[str, Any]]:
        """Load error recovery strategies"""
        return {
            ErrorPattern.MISSING_REQUIRED_FIELD: {
                'actions': ['provide_field', 'use_default', 'mark_conditional'],
                'priority': 1,
                'estimated_time': 5
            },
            ErrorPattern.INVALID_FORMAT: {
                'actions': ['reformat_data', 'use_converter', 'validate_input'],
                'priority': 2,
                'estimated_time': 10
            },
            ErrorPattern.BUSINESS_RULE_VIOLATION: {
                'actions': ['check_policy', 'request_exception', 'modify_data'],
                'priority': 3,
                'estimated_time': 15
            },
            ErrorPattern.CALCULATION_ERROR: {
                'actions': ['recalculate', 'verify_amounts', 'check_formulas'],
                'priority': 2,
                'estimated_time': 8
            },
            ErrorPattern.REFERENCE_ERROR: {
                'actions': ['verify_reference', 'create_reference', 'use_alternative'],
                'priority': 3,
                'estimated_time': 12
            },
            ErrorPattern.PERMISSION_ERROR: {
                'actions': ['request_permission', 'use_delegate', 'escalate'],
                'priority': 1,
                'estimated_time': 20
            },
            ErrorPattern.SYSTEM_ERROR: {
                'actions': ['retry_operation', 'contact_support', 'use_fallback'],
                'priority': 1,
                'estimated_time': 30
            }
        }
    
    def _load_message_templates(self) -> Dict[str, str]:
        """Load user-friendly message templates"""
        return {
            'missing_required_field': "The field '{field}' is required. Please provide this information to continue.",
            'invalid_format': "The format of '{field}' is incorrect. Expected format: {expected_format}.",
            'business_rule_violation': "The value in '{field}' violates business rules. {details}",
            'calculation_error': "There's a calculation error in the amounts. Please verify your calculations.",
            'reference_error': "Cannot find reference '{reference}'. Please check if it exists.",
            'permission_error': "You don't have permission to perform this action. Please contact your administrator.",
            'system_error': "A system error occurred. Please try again or contact support if the problem persists."
        }
    
    async def handle_validation_errors(self, 
                                     document_id: str,
                                     *reports: Union[FIRSValidationReport, SubmissionValidationReport, 
                                                   FormatValidationReport, CompletenessReport]) -> ErrorHandlingReport:
        """
        Handle validation errors from multiple validation reports
        
        Args:
            document_id: Document identifier
            *reports: Variable number of validation reports
            
        Returns:
            ErrorHandlingReport with comprehensive error analysis
        """
        # Aggregate errors from all reports
        all_errors = []
        for report in reports:
            errors = await self._extract_errors_from_report(report)
            all_errors.extend(errors)
        
        # Classify and analyze errors
        classified_errors = await self._classify_errors(all_errors)
        
        # Group related errors
        error_groups = await self._group_errors(classified_errors)
        
        # Analyze error patterns
        error_analysis = await self._analyze_error_patterns(classified_errors)
        
        # Generate recovery actions
        recovery_actions = await self._generate_recovery_actions(error_groups)
        
        # Create user-friendly summary
        user_summary = await self._create_user_summary(error_groups, error_analysis)
        
        # Generate detailed report
        detailed_report = await self._generate_detailed_report(error_groups, error_analysis)
        
        # Create error handling report
        handling_report = ErrorHandlingReport(
            document_id=document_id,
            validation_timestamp=datetime.utcnow(),
            total_errors=len(classified_errors),
            resolved_errors=len([e for e in classified_errors if e.resolution == ErrorResolution.RESOLVED]),
            unresolved_errors=len([e for e in classified_errors if e.resolution == ErrorResolution.UNRESOLVED]),
            error_groups=error_groups,
            error_analysis=error_analysis,
            recovery_actions=recovery_actions,
            user_friendly_summary=user_summary,
            detailed_report=detailed_report
        )
        
        # Update metrics and history
        await self._update_metrics(handling_report)
        if self.enable_analytics:
            self.error_history.extend(classified_errors)
        
        logger.info(f"Error handling completed for {document_id}: "
                   f"{len(classified_errors)} errors, {len(error_groups)} groups")
        
        return handling_report
    
    async def _extract_errors_from_report(self, report: Any) -> List[ValidationError]:
        """Extract errors from validation report"""
        errors = []
        
        if isinstance(report, FIRSValidationReport):
            for result in report.results:
                if result.severity in [ValidationSeverity.ERROR, ValidationSeverity.CRITICAL]:
                    error = ValidationError(
                        error_id=f"FIRS_{result.rule_id}_{hash(result.field_name)}",
                        source="firs_validator",
                        category=ErrorCategory.COMPLIANCE,
                        pattern=ErrorPattern.BUSINESS_RULE_VIOLATION,
                        severity=result.severity.value,
                        field_path=result.field_name,
                        message=result.message,
                        suggestion=result.suggestion,
                        metadata={'rule_id': result.rule_id}
                    )
                    errors.append(error)
        
        elif isinstance(report, SubmissionValidationReport):
            for check in report.checks:
                if check.status == CheckStatus.FAILED:
                    error = ValidationError(
                        error_id=f"SUBMIT_{check.check_id}_{hash(check.check_name)}",
                        source="submission_validator",
                        category=ErrorCategory.FUNCTIONAL,
                        pattern=ErrorPattern.BUSINESS_RULE_VIOLATION,
                        severity=check.severity.value,
                        field_path=check.check_name,
                        message=check.message,
                        details=check.details,
                        suggestion=check.suggestion,
                        metadata={'check_id': check.check_id, 'category': check.category.value}
                    )
                    errors.append(error)
        
        elif isinstance(report, FormatValidationReport):
            for result in report.results:
                if result.severity in [FormatSeverity.ERROR, FormatSeverity.CRITICAL]:
                    error = ValidationError(
                        error_id=f"FORMAT_{result.field_type.value}_{hash(result.field_path)}",
                        source="format_validator",
                        category=ErrorCategory.DATA_QUALITY,
                        pattern=ErrorPattern.INVALID_FORMAT,
                        severity=result.severity.value,
                        field_path=result.field_path,
                        message=result.message,
                        suggestion=result.suggestion,
                        metadata={'field_type': result.field_type.value, 'expected_format': result.expected_format}
                    )
                    errors.append(error)
        
        elif isinstance(report, CompletenessReport):
            for result in report.results:
                if result.severity in [CompletionSeverity.ERROR, CompletionSeverity.CRITICAL]:
                    error = ValidationError(
                        error_id=f"COMPLETE_{result.rule_id}_{hash(result.field_path)}",
                        source="completeness_checker",
                        category=ErrorCategory.DATA_QUALITY,
                        pattern=ErrorPattern.MISSING_REQUIRED_FIELD,
                        severity=result.severity.value,
                        field_path=result.field_path,
                        message=result.message,
                        suggestion=result.suggestion,
                        metadata={'rule_id': result.rule_id, 'status': result.status.value}
                    )
                    errors.append(error)
        
        return errors
    
    async def _classify_errors(self, errors: List[ValidationError]) -> List[ValidationError]:
        """Classify errors using classification rules"""
        classified_errors = []
        
        for error in errors:
            # Detect pattern
            detected_pattern = await self._detect_error_pattern(error)
            if detected_pattern:
                error.pattern = detected_pattern
            
            # Classify category
            error.category = await self._classify_error_category(error)
            
            # Generate user-friendly message
            error.message = await self._generate_user_friendly_message(error)
            
            classified_errors.append(error)
        
        return classified_errors
    
    async def _detect_error_pattern(self, error: ValidationError) -> Optional[ErrorPattern]:
        """Detect error pattern"""
        message_lower = error.message.lower()
        
        # Check each pattern detector
        for pattern, detector in self.pattern_detectors.items():
            if await detector(error):
                return pattern
        
        # Fallback to keyword matching
        for rule_name, rule in self.classification_rules.items():
            if any(keyword in message_lower for keyword in rule['keywords']):
                return rule['pattern']
        
        return ErrorPattern.SYSTEM_ERROR
    
    async def _classify_error_category(self, error: ValidationError) -> ErrorCategory:
        """Classify error category"""
        # Use pattern-based classification
        pattern_category_map = {
            ErrorPattern.MISSING_REQUIRED_FIELD: ErrorCategory.CRITICAL,
            ErrorPattern.INVALID_FORMAT: ErrorCategory.DATA_QUALITY,
            ErrorPattern.BUSINESS_RULE_VIOLATION: ErrorCategory.BUSINESS_RULE,
            ErrorPattern.CALCULATION_ERROR: ErrorCategory.FUNCTIONAL,
            ErrorPattern.REFERENCE_ERROR: ErrorCategory.FUNCTIONAL,
            ErrorPattern.PERMISSION_ERROR: ErrorCategory.CRITICAL,
            ErrorPattern.SYSTEM_ERROR: ErrorCategory.CRITICAL
        }
        
        return pattern_category_map.get(error.pattern, ErrorCategory.FUNCTIONAL)
    
    async def _generate_user_friendly_message(self, error: ValidationError) -> str:
        """Generate user-friendly error message"""
        template_key = error.pattern.value
        template = self.message_templates.get(template_key, error.message)
        
        # Replace placeholders
        try:
            return template.format(
                field=error.field_path,
                expected_format=error.metadata.get('expected_format', 'correct format'),
                details=error.details or 'Please check the requirements',
                reference=error.metadata.get('reference', 'unknown')
            )
        except KeyError:
            return error.message
    
    async def _group_errors(self, errors: List[ValidationError]) -> List[ErrorGroup]:
        """Group related errors"""
        groups = defaultdict(list)
        
        # Group by pattern and category
        for error in errors:
            group_key = f"{error.pattern.value}_{error.category.value}"
            groups[group_key].append(error)
        
        error_groups = []
        for group_key, group_errors in groups.items():
            if len(group_errors) > 0:
                # Calculate group statistics
                severity_dist = Counter(error.severity for error in group_errors)
                common_fields = list(set(error.field_path for error in group_errors))
                
                # Generate suggested actions
                pattern = group_errors[0].pattern
                strategy = self.recovery_strategies.get(pattern, {})
                suggested_actions = strategy.get('actions', [])
                estimated_time = strategy.get('estimated_time', 10) * len(group_errors)
                
                error_group = ErrorGroup(
                    group_id=group_key,
                    category=group_errors[0].category,
                    pattern=pattern,
                    errors=group_errors,
                    count=len(group_errors),
                    severity_distribution=dict(severity_dist),
                    common_fields=common_fields[:10],  # Limit to 10
                    suggested_actions=suggested_actions,
                    estimated_fix_time=estimated_time
                )
                
                error_groups.append(error_group)
        
        # Sort by priority (critical first)
        error_groups.sort(key=lambda g: (
            g.category == ErrorCategory.CRITICAL,
            g.count
        ), reverse=True)
        
        return error_groups
    
    async def _analyze_error_patterns(self, errors: List[ValidationError]) -> ErrorAnalysis:
        """Analyze error patterns"""
        total_errors = len(errors)
        
        # Category distribution
        category_dist = Counter(error.category for error in errors)
        
        # Pattern distribution
        pattern_dist = Counter(error.pattern for error in errors)
        
        # Severity distribution
        severity_dist = Counter(error.severity for error in errors)
        
        # Most common error groups
        field_errors = defaultdict(list)
        for error in errors:
            field_errors[error.field_path].append(error)
        
        most_common_fields = sorted(field_errors.items(), key=lambda x: len(x[1]), reverse=True)[:5]
        
        # Generate resolution suggestions
        resolution_suggestions = []
        for pattern, count in pattern_dist.most_common(3):
            strategy = self.recovery_strategies.get(pattern, {})
            actions = strategy.get('actions', [])
            if actions:
                resolution_suggestions.append(f"For {pattern.value} errors ({count} occurrences): {', '.join(actions[:2])}")
        
        # Calculate estimated fix time
        total_fix_time = sum(
            self.recovery_strategies.get(pattern, {}).get('estimated_time', 10) * count
            for pattern, count in pattern_dist.items()
        )
        
        # Error trends (simplified)
        error_trends = {
            'peak_error_category': category_dist.most_common(1)[0][0].value if category_dist else 'none',
            'peak_error_pattern': pattern_dist.most_common(1)[0][0].value if pattern_dist else 'none',
            'critical_error_ratio': severity_dist.get('critical', 0) / max(total_errors, 1)
        }
        
        return ErrorAnalysis(
            total_errors=total_errors,
            error_categories=dict(category_dist),
            error_patterns=dict(pattern_dist),
            severity_distribution=dict(severity_dist),
            most_common_errors=[],  # Populated from groups
            resolution_suggestions=resolution_suggestions,
            estimated_total_fix_time=total_fix_time,
            error_trends=error_trends
        )
    
    async def _generate_recovery_actions(self, error_groups: List[ErrorGroup]) -> List[str]:
        """Generate recovery actions"""
        recovery_actions = []
        
        # Priority-based actions
        for group in error_groups:
            if group.category == ErrorCategory.CRITICAL:
                recovery_actions.append(f"URGENT: Fix {group.count} {group.pattern.value} errors immediately")
            
            # Add specific actions based on pattern
            for action in group.suggested_actions[:2]:  # Top 2 actions
                recovery_actions.append(f"{group.pattern.value}: {action}")
        
        # Add general recommendations
        if len(error_groups) > 5:
            recovery_actions.append("Consider reviewing document preparation process to reduce errors")
        
        return recovery_actions[:10]  # Limit to 10 actions
    
    async def _create_user_summary(self, error_groups: List[ErrorGroup], analysis: ErrorAnalysis) -> str:
        """Create user-friendly summary"""
        if analysis.total_errors == 0:
            return "✅ No validation errors found. Document is ready for submission."
        
        summary_parts = []
        
        # Overall status
        if analysis.severity_distribution.get('critical', 0) > 0:
            summary_parts.append(f"🚨 Found {analysis.total_errors} validation errors including {analysis.severity_distribution['critical']} critical issues.")
        else:
            summary_parts.append(f"⚠️ Found {analysis.total_errors} validation errors that need attention.")
        
        # Top issues
        if error_groups:
            top_group = error_groups[0]
            summary_parts.append(f"Primary issue: {top_group.count} {top_group.pattern.value} errors.")
        
        # Estimated fix time
        if analysis.estimated_total_fix_time > 0:
            summary_parts.append(f"Estimated fix time: {analysis.estimated_total_fix_time} minutes.")
        
        # Next steps
        if analysis.resolution_suggestions:
            summary_parts.append(f"Next step: {analysis.resolution_suggestions[0]}")
        
        return " ".join(summary_parts)
    
    async def _generate_detailed_report(self, error_groups: List[ErrorGroup], analysis: ErrorAnalysis) -> str:
        """Generate detailed error report"""
        report_parts = []
        
        report_parts.append("VALIDATION ERROR REPORT")
        report_parts.append("=" * 50)
        
        # Summary statistics
        report_parts.append(f"Total Errors: {analysis.total_errors}")
        report_parts.append(f"Error Categories: {', '.join(f'{cat.value}: {count}' for cat, count in analysis.error_categories.items())}")
        report_parts.append(f"Severity Distribution: {', '.join(f'{sev}: {count}' for sev, count in analysis.severity_distribution.items())}")
        report_parts.append("")
        
        # Error groups
        for i, group in enumerate(error_groups, 1):
            report_parts.append(f"{i}. {group.pattern.value.upper()} ({group.count} errors)")
            report_parts.append(f"   Category: {group.category.value}")
            report_parts.append(f"   Affected Fields: {', '.join(group.common_fields[:5])}")
            report_parts.append(f"   Suggested Actions: {', '.join(group.suggested_actions[:3])}")
            report_parts.append(f"   Estimated Fix Time: {group.estimated_fix_time} minutes")
            report_parts.append("")
        
        # Resolution suggestions
        if analysis.resolution_suggestions:
            report_parts.append("RESOLUTION SUGGESTIONS:")
            for suggestion in analysis.resolution_suggestions:
                report_parts.append(f"• {suggestion}")
        
        return "\n".join(report_parts)
    
    async def _update_metrics(self, report: ErrorHandlingReport):
        """Update error handling metrics"""
        self.metrics['total_errors_handled'] += report.total_errors
        
        # Update category metrics
        for group in report.error_groups:
            self.metrics['errors_by_category'][group.category.value] += group.count
            self.metrics['errors_by_pattern'][group.pattern.value] += group.count
        
        # Update resolution rate
        if report.total_errors > 0:
            self.metrics['resolution_rate'] = (report.resolved_errors / report.total_errors) * 100
        
        # Update average fix time
        if report.error_analysis.estimated_total_fix_time > 0:
            self.metrics['average_fix_time'] = report.error_analysis.estimated_total_fix_time / max(report.total_errors, 1)
    
    # Pattern detectors
    async def _detect_missing_field_pattern(self, error: ValidationError) -> bool:
        """Detect missing field pattern"""
        keywords = ['missing', 'required', 'mandatory', 'not found', 'absent']
        return any(keyword in error.message.lower() for keyword in keywords)
    
    async def _detect_format_pattern(self, error: ValidationError) -> bool:
        """Detect format pattern"""
        keywords = ['format', 'pattern', 'invalid', 'malformed', 'structure']
        return any(keyword in error.message.lower() for keyword in keywords)
    
    async def _detect_business_rule_pattern(self, error: ValidationError) -> bool:
        """Detect business rule pattern"""
        keywords = ['rule', 'policy', 'compliance', 'violation', 'business']
        return any(keyword in error.message.lower() for keyword in keywords)
    
    async def _detect_calculation_pattern(self, error: ValidationError) -> bool:
        """Detect calculation pattern"""
        keywords = ['calculation', 'amount', 'total', 'sum', 'mismatch', 'math']
        return any(keyword in error.message.lower() for keyword in keywords)
    
    async def _detect_reference_pattern(self, error: ValidationError) -> bool:
        """Detect reference pattern"""
        keywords = ['reference', 'lookup', 'foreign', 'key', 'not found']
        return any(keyword in error.message.lower() for keyword in keywords)
    
    async def _detect_permission_pattern(self, error: ValidationError) -> bool:
        """Detect permission pattern"""
        keywords = ['permission', 'access', 'unauthorized', 'forbidden', 'denied']
        return any(keyword in error.message.lower() for keyword in keywords)
    
    async def _detect_system_pattern(self, error: ValidationError) -> bool:
        """Detect system pattern"""
        keywords = ['system', 'internal', 'exception', 'server', 'database']
        return any(keyword in error.message.lower() for keyword in keywords)
    
    def get_error_statistics(self) -> Dict[str, Any]:
        """Get error handling statistics"""
        if not self.error_history:
            return {'message': 'No error history available'}
        
        # Calculate statistics from error history
        total_errors = len(self.error_history)
        resolved_errors = len([e for e in self.error_history if e.resolution == ErrorResolution.RESOLVED])
        
        category_stats = Counter(error.category for error in self.error_history)
        pattern_stats = Counter(error.pattern for error in self.error_history)
        severity_stats = Counter(error.severity for error in self.error_history)
        
        return {
            'total_errors': total_errors,
            'resolved_errors': resolved_errors,
            'resolution_rate': (resolved_errors / total_errors) * 100 if total_errors > 0 else 0,
            'category_distribution': dict(category_stats),
            'pattern_distribution': dict(pattern_stats),
            'severity_distribution': dict(severity_stats),
            'metrics': self.metrics
        }
    
    def get_error_trends(self, days: int = 7) -> Dict[str, Any]:
        """Get error trends over specified days"""
        if not self.error_history:
            return {'message': 'No error history available'}
        
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        recent_errors = [e for e in self.error_history if e.timestamp >= cutoff_date]
        
        if not recent_errors:
            return {'message': f'No errors in the last {days} days'}
        
        # Daily error counts
        daily_counts = defaultdict(int)
        for error in recent_errors:
            date_key = error.timestamp.strftime('%Y-%m-%d')
            daily_counts[date_key] += 1
        
        # Pattern trends
        pattern_trends = defaultdict(int)
        for error in recent_errors:
            pattern_trends[error.pattern.value] += 1
        
        return {
            'period_days': days,
            'total_errors': len(recent_errors),
            'daily_counts': dict(daily_counts),
            'pattern_trends': dict(pattern_trends),
            'average_daily_errors': len(recent_errors) / days
        }
    
    def clear_error_history(self):
        """Clear error history"""
        self.error_history.clear()
        self.error_patterns.clear()
        logger.info("Error history cleared")


# Factory functions for easy setup
def create_error_handler(enable_analytics: bool = True) -> ValidationErrorHandler:
    """Create validation error handler instance"""
    return ValidationErrorHandler(enable_analytics)


async def handle_validation_errors(document_id: str, 
                                  *reports,
                                  enable_analytics: bool = True) -> ErrorHandlingReport:
    """Handle validation errors from reports"""
    handler = create_error_handler(enable_analytics)
    return await handler.handle_validation_errors(document_id, *reports)


def get_error_summary(report: ErrorHandlingReport) -> Dict[str, Any]:
    """Get error summary from handling report"""
    return {
        'document_id': report.document_id,
        'total_errors': report.total_errors,
        'resolved_errors': report.resolved_errors,
        'unresolved_errors': report.unresolved_errors,
        'error_groups_count': len(report.error_groups),
        'estimated_fix_time': report.error_analysis.estimated_total_fix_time,
        'user_summary': report.user_friendly_summary
    }