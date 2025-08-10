"""
Universal Compliance Validator
=============================
Central validation engine that coordinates compliance validation across all regulatory frameworks.
Provides unified validation interface and orchestrates framework-specific validators.
"""

import logging
import asyncio
import time
import hashlib
import json
from typing import Dict, Any, List, Optional, Union, Tuple
from datetime import datetime, timedelta
from concurrent.futures import ThreadPoolExecutor, as_completed
from functools import wraps

from .models import (
    ValidationRequest, ValidationResponse, ValidationExecutionContext,
    ValidationMode, ConflictResolutionStrategy, ValidationPhase,
    RuleConflict, CrossFrameworkResult, AggregatedValidationResult,
    ValidationCache, PluginExecutionResult
)
from .rule_engine import ComplianceRuleEngine
from .validation_aggregator import ValidationAggregator
from .plugin_manager import ValidationPluginManager

from ..orchestrator.models import (
    ComplianceFramework, ComplianceStatus, ValidationSeverity,
    ComplianceRule, ValidationResult
)

logger = logging.getLogger(__name__)

def performance_monitor(func):
    """Decorator to monitor validation performance"""
    @wraps(func)
    def wrapper(self, *args, **kwargs):
        start_time = time.time()
        try:
            result = func(self, *args, **kwargs)
            execution_time = (time.time() - start_time) * 1000  # Convert to milliseconds
            self._record_performance_metric(func.__name__, execution_time, True)
            return result
        except Exception as e:
            execution_time = (time.time() - start_time) * 1000
            self._record_performance_metric(func.__name__, execution_time, False)
            raise
    return wrapper

class UniversalComplianceValidator:
    """
    Universal compliance validator that orchestrates validation across all frameworks
    """
    
    def __init__(self):
        """Initialize universal compliance validator"""
        self.logger = logging.getLogger(__name__)
        
        # Initialize components
        self.rule_engine = ComplianceRuleEngine()
        self.aggregator = ValidationAggregator()
        self.plugin_manager = ValidationPluginManager()
        
        # Performance and caching
        self.validation_cache: Dict[str, ValidationCache] = {}
        self.performance_metrics: Dict[str, Dict[str, Any]] = {}
        
        # Configuration
        self.max_parallel_validations = 10
        self.default_timeout_seconds = 300
        self.cache_ttl_seconds = 3600
        self.enable_caching = True
        
        # Framework priorities (lower number = higher priority)
        self.framework_priorities = {
            ComplianceFramework.FIRS: 1,
            ComplianceFramework.CAC: 2,
            ComplianceFramework.NITDA: 3,
            ComplianceFramework.ISO_27001: 4,
            ComplianceFramework.ISO_20022: 5,
            ComplianceFramework.UBL: 6,
            ComplianceFramework.PEPPOL: 7,
            ComplianceFramework.GDPR: 8,
            ComplianceFramework.NDPA: 9,
            ComplianceFramework.WCO_HS: 10,
            ComplianceFramework.LEI: 11
        }
        
        self.logger.info("Universal Compliance Validator initialized")
    
    @performance_monitor
    def validate(self, request: ValidationRequest) -> ValidationResponse:
        """
        Main validation entry point - validates data against specified frameworks
        
        Args:
            request: Validation request with data and configuration
            
        Returns:
            ValidationResponse with comprehensive validation results
        """
        try:
            self.logger.info(f"Starting universal validation: {request.request_id}")
            start_time = time.time()
            
            # Create execution context
            context = ValidationExecutionContext(request=request)
            
            # Check cache first
            if self.enable_caching:
                cached_result = self._check_cache(request)
                if cached_result:
                    self.logger.info(f"Returning cached result for request: {request.request_id}")
                    return cached_result
            
            # Pre-validation phase
            context.current_phase = ValidationPhase.PRE_VALIDATION
            self._pre_validation_checks(request, context)
            
            # Execute validation
            if request.parallel_execution and len(request.frameworks) > 1:
                response = self._execute_parallel_validation(request, context)
            else:
                response = self._execute_sequential_validation(request, context)
            
            # Post-validation processing
            context.current_phase = ValidationPhase.POST_VALIDATION
            response = self._post_validation_processing(response, context)
            
            # Cache the result
            if self.enable_caching:
                self._cache_result(request, response)
            
            execution_time = (time.time() - start_time) * 1000
            response.execution_time_ms = execution_time
            
            self.logger.info(f"Universal validation completed: {request.request_id} in {execution_time:.2f}ms")
            return response
            
        except Exception as e:
            self.logger.error(f"Universal validation failed: {str(e)}")
            return self._create_error_response(request, str(e))
    
    @performance_monitor
    def validate_cross_framework(self, data: Dict[str, Any], frameworks: List[ComplianceFramework]) -> CrossFrameworkResult:
        """
        Perform cross-framework validation analysis
        
        Args:
            data: Data to analyze
            frameworks: Frameworks to analyze across
            
        Returns:
            CrossFrameworkResult with cross-framework analysis
        """
        try:
            self.logger.info(f"Starting cross-framework analysis for {len(frameworks)} frameworks")
            
            # Create individual validation requests
            individual_results = {}
            for framework in frameworks:
                request = ValidationRequest(
                    data=data,
                    frameworks=[framework],
                    validation_mode=ValidationMode.COMPREHENSIVE
                )
                result = self.validate(request)
                individual_results[framework] = result
            
            # Analyze cross-framework consistency
            cross_result = self._analyze_cross_framework_consistency(individual_results, frameworks)
            
            self.logger.info(f"Cross-framework analysis completed with {len(cross_result.conflicting_requirements)} conflicts")
            return cross_result
            
        except Exception as e:
            self.logger.error(f"Cross-framework analysis failed: {str(e)}")
            return CrossFrameworkResult(
                frameworks_analyzed=frameworks,
                harmonization_issues=[f"Analysis error: {str(e)}"]
            )
    
    @performance_monitor
    def aggregate_results(self, validation_responses: List[ValidationResponse]) -> AggregatedValidationResult:
        """
        Aggregate multiple validation responses into a single result
        
        Args:
            validation_responses: List of validation responses to aggregate
            
        Returns:
            AggregatedValidationResult with aggregated analysis
        """
        try:
            self.logger.info(f"Aggregating {len(validation_responses)} validation responses")
            
            if not validation_responses:
                raise ValueError("No validation responses provided for aggregation")
            
            # Use the aggregator component
            aggregated_result = self.aggregator.aggregate_validation_results(validation_responses)
            
            self.logger.info(f"Aggregation completed with overall score: {aggregated_result.overall_compliance_score}")
            return aggregated_result
            
        except Exception as e:
            self.logger.error(f"Result aggregation failed: {str(e)}")
            raise
    
    def get_validation_status(self, request_id: str) -> Optional[Dict[str, Any]]:
        """
        Get status of ongoing validation
        
        Args:
            request_id: Validation request ID
            
        Returns:
            Status information or None if not found
        """
        # This would track ongoing validations in a production system
        return None
    
    def cancel_validation(self, request_id: str) -> bool:
        """
        Cancel ongoing validation
        
        Args:
            request_id: Validation request ID to cancel
            
        Returns:
            True if cancelled successfully
        """
        # This would cancel ongoing validations in a production system
        self.logger.info(f"Cancellation requested for validation: {request_id}")
        return False
    
    def get_performance_metrics(self) -> Dict[str, Any]:
        """
        Get validation performance metrics
        
        Returns:
            Dictionary with performance metrics
        """
        return {
            'cache_stats': {
                'total_entries': len(self.validation_cache),
                'hit_rate': self._calculate_cache_hit_rate(),
                'average_response_time': self._calculate_average_response_time()
            },
            'validation_metrics': self.performance_metrics,
            'plugin_performance': self.plugin_manager.get_performance_metrics()
        }
    
    def clear_cache(self) -> int:
        """
        Clear validation cache
        
        Returns:
            Number of cache entries cleared
        """
        cleared_count = len(self.validation_cache)
        self.validation_cache.clear()
        self.logger.info(f"Cleared {cleared_count} cache entries")
        return cleared_count
    
    # Private helper methods
    
    def _pre_validation_checks(self, request: ValidationRequest, context: ValidationExecutionContext):
        """Perform pre-validation checks"""
        # Validate request data
        if not request.data:
            raise ValueError("No data provided for validation")
        
        # Check framework availability
        unavailable_frameworks = []
        for framework in request.frameworks:
            if not self.plugin_manager.is_framework_available(framework):
                unavailable_frameworks.append(framework)
        
        if unavailable_frameworks:
            self.logger.warning(f"Unavailable frameworks: {unavailable_frameworks}")
        
        # Set execution order based on priorities
        context.framework_execution_order = sorted(
            request.frameworks,
            key=lambda f: self.framework_priorities.get(f, 999)
        )
        
        self.logger.debug(f"Framework execution order: {context.framework_execution_order}")
    
    def _execute_parallel_validation(self, request: ValidationRequest, context: ValidationExecutionContext) -> ValidationResponse:
        """Execute validation in parallel across frameworks"""
        self.logger.info(f"Executing parallel validation across {len(request.frameworks)} frameworks")
        
        framework_results = {}
        execution_times = {}
        
        with ThreadPoolExecutor(max_workers=self.max_parallel_validations) as executor:
            # Submit validation tasks
            future_to_framework = {
                executor.submit(self._validate_single_framework, framework, request): framework
                for framework in request.frameworks
            }
            
            # Collect results
            for future in as_completed(future_to_framework, timeout=request.timeout_seconds):
                framework = future_to_framework[future]
                try:
                    start_time = time.time()
                    result = future.result()
                    execution_time = (time.time() - start_time) * 1000
                    
                    framework_results[framework] = result
                    execution_times[framework] = execution_time
                    context.completed_frameworks.append(framework)
                    
                except Exception as e:
                    self.logger.error(f"Framework {framework} validation failed: {str(e)}")
                    context.failed_frameworks.append(framework)
                    context.execution_errors.append(f"{framework}: {str(e)}")
        
        # Create response
        return self._create_validation_response(request, framework_results, execution_times, context)
    
    def _execute_sequential_validation(self, request: ValidationRequest, context: ValidationExecutionContext) -> ValidationResponse:
        """Execute validation sequentially across frameworks"""
        self.logger.info(f"Executing sequential validation across {len(request.frameworks)} frameworks")
        
        framework_results = {}
        execution_times = {}
        
        for framework in context.framework_execution_order:
            try:
                start_time = time.time()
                result = self._validate_single_framework(framework, request)
                execution_time = (time.time() - start_time) * 1000
                
                framework_results[framework] = result
                execution_times[framework] = execution_time
                context.completed_frameworks.append(framework)
                
                # Store intermediate results
                context.intermediate_results[framework] = result
                
            except Exception as e:
                self.logger.error(f"Framework {framework} validation failed: {str(e)}")
                context.failed_frameworks.append(framework)
                context.execution_errors.append(f"{framework}: {str(e)}")
        
        return self._create_validation_response(request, framework_results, execution_times, context)
    
    def _validate_single_framework(self, framework: ComplianceFramework, request: ValidationRequest) -> List[ValidationResult]:
        """Validate data against a single framework"""
        try:
            self.logger.debug(f"Validating framework: {framework}")
            
            # Get framework-specific plugin
            plugin = self.plugin_manager.get_plugin(framework)
            if not plugin:
                raise ValueError(f"No plugin available for framework: {framework}")
            
            # Execute plugin validation
            plugin_result = plugin.validate(request.data, request.context)
            
            return plugin_result.validation_results
            
        except Exception as e:
            self.logger.error(f"Single framework validation failed for {framework}: {str(e)}")
            raise
    
    def _create_validation_response(
        self,
        request: ValidationRequest,
        framework_results: Dict[ComplianceFramework, List[ValidationResult]],
        execution_times: Dict[ComplianceFramework, float],
        context: ValidationExecutionContext
    ) -> ValidationResponse:
        """Create comprehensive validation response"""
        
        # Calculate overall metrics
        total_rules = sum(len(results) for results in framework_results.values())
        passed_rules = sum(1 for results in framework_results.values() for r in results if r.status == ComplianceStatus.COMPLIANT)
        failed_rules = sum(1 for results in framework_results.values() for r in results if r.status == ComplianceStatus.NON_COMPLIANT)
        
        # Calculate overall score
        overall_score = (passed_rules / total_rules * 100) if total_rules > 0 else 0
        
        # Determine overall status
        if failed_rules == 0:
            overall_status = ComplianceStatus.COMPLIANT
        elif passed_rules > failed_rules:
            overall_status = ComplianceStatus.PARTIALLY_COMPLIANT
        else:
            overall_status = ComplianceStatus.NON_COMPLIANT
        
        # Detect rule conflicts
        rule_conflicts = self._detect_rule_conflicts(framework_results, request.conflict_resolution)
        
        # Generate recommendations
        recommendations = self._generate_recommendations(framework_results, rule_conflicts)
        
        # Create response
        response = ValidationResponse(
            request_id=request.request_id,
            overall_status=overall_status,
            overall_score=overall_score,
            execution_time_ms=sum(execution_times.values()),
            frameworks_validated=list(framework_results.keys()),
            framework_results=framework_results,
            rule_conflicts=rule_conflicts,
            total_rules_checked=total_rules,
            rules_passed=passed_rules,
            rules_failed=failed_rules,
            rules_skipped=0,  # TODO: Track skipped rules
            recommendations=recommendations,
            compliance_summary=self._generate_compliance_summary(framework_results, overall_score)
        )
        
        # Add critical issues and warnings
        for results in framework_results.values():
            for result in results:
                if result.severity == ValidationSeverity.CRITICAL and result.status != ComplianceStatus.COMPLIANT:
                    response.critical_issues.extend(result.issues_found)
                elif result.severity in [ValidationSeverity.HIGH, ValidationSeverity.MEDIUM]:
                    response.warnings.extend(result.issues_found)
        
        return response
    
    def _post_validation_processing(self, response: ValidationResponse, context: ValidationExecutionContext) -> ValidationResponse:
        """Perform post-validation processing"""
        # Add execution context information
        if context.execution_errors:
            response.warnings.extend([f"Execution warning: {error}" for error in context.execution_errors])
        
        # Generate next steps
        response.next_steps = self._generate_next_steps(response)
        
        return response
    
    def _detect_rule_conflicts(
        self,
        framework_results: Dict[ComplianceFramework, List[ValidationResult]],
        resolution_strategy: ConflictResolutionStrategy
    ) -> List[RuleConflict]:
        """Detect conflicts between framework rules"""
        conflicts = []
        
        # This is a simplified conflict detection
        # In production, this would be more sophisticated
        rule_requirements = {}
        
        for framework, results in framework_results.items():
            for result in results:
                rule_key = f"{result.rule_id}"
                if rule_key not in rule_requirements:
                    rule_requirements[rule_key] = []
                rule_requirements[rule_key].append((framework, result))
        
        # Look for conflicting requirements
        for rule_key, framework_results_list in rule_requirements.items():
            if len(framework_results_list) > 1:
                statuses = set(result.status for _, result in framework_results_list)
                if len(statuses) > 1:  # Conflicting statuses
                    frameworks_involved = [framework for framework, _ in framework_results_list]
                    conflict = RuleConflict(
                        conflicting_rules=[f"{rule_key}_{framework}" for framework in frameworks_involved],
                        frameworks_involved=frameworks_involved,
                        conflict_type="requirement",
                        conflict_description=f"Conflicting validation results for rule {rule_key}",
                        resolution_strategy=resolution_strategy,
                        resolution_result=self._resolve_conflict(framework_results_list, resolution_strategy),
                        business_impact="May require manual review",
                        severity=ValidationSeverity.MEDIUM
                    )
                    conflicts.append(conflict)
        
        return conflicts
    
    def _resolve_conflict(self, conflicting_results: List[Tuple], strategy: ConflictResolutionStrategy) -> str:
        """Resolve rule conflict based on strategy"""
        if strategy == ConflictResolutionStrategy.STRICT_PRECEDENCE:
            # Highest severity wins
            highest_severity = None
            winning_result = None
            
            for framework, result in conflicting_results:
                if highest_severity is None or result.severity.value < highest_severity.value:
                    highest_severity = result.severity
                    winning_result = (framework, result)
            
            return f"Resolved using strict precedence: {winning_result[0]} rule takes precedence"
        
        elif strategy == ConflictResolutionStrategy.FRAMEWORK_PRIORITY:
            # Framework with highest priority wins
            highest_priority_framework = min(
                (framework for framework, _ in conflicting_results),
                key=lambda f: self.framework_priorities.get(f, 999)
            )
            return f"Resolved using framework priority: {highest_priority_framework} takes precedence"
        
        else:
            return "Conflict requires manual resolution"
    
    def _generate_recommendations(
        self,
        framework_results: Dict[ComplianceFramework, List[ValidationResult]],
        conflicts: List[RuleConflict]
    ) -> List[str]:
        """Generate compliance recommendations"""
        recommendations = []
        
        # Framework-specific recommendations
        for framework, results in framework_results.items():
            failed_results = [r for r in results if r.status != ComplianceStatus.COMPLIANT]
            if failed_results:
                recommendations.append(f"Address {len(failed_results)} issues in {framework.value} compliance")
        
        # Conflict resolution recommendations
        if conflicts:
            recommendations.append(f"Resolve {len(conflicts)} rule conflicts between frameworks")
        
        # Generic recommendations
        total_failed = sum(len([r for r in results if r.status != ComplianceStatus.COMPLIANT]) 
                          for results in framework_results.values())
        if total_failed > 0:
            recommendations.append("Implement systematic compliance monitoring")
        
        return recommendations
    
    def _generate_compliance_summary(self, framework_results: Dict[ComplianceFramework, List[ValidationResult]], overall_score: float) -> Dict[str, Any]:
        """Generate executive compliance summary"""
        return {
            'overall_compliance_score': overall_score,
            'frameworks_assessed': len(framework_results),
            'compliant_frameworks': len([f for f, results in framework_results.items() 
                                       if all(r.status == ComplianceStatus.COMPLIANT for r in results)]),
            'compliance_level': 'High' if overall_score >= 90 else 'Medium' if overall_score >= 70 else 'Low',
            'key_strengths': self._identify_strengths(framework_results),
            'improvement_areas': self._identify_improvement_areas(framework_results)
        }
    
    def _generate_next_steps(self, response: ValidationResponse) -> List[str]:
        """Generate recommended next steps"""
        next_steps = []
        
        if response.critical_issues:
            next_steps.append("Address critical compliance issues immediately")
        
        if response.rule_conflicts:
            next_steps.append("Resolve rule conflicts between frameworks")
        
        if response.overall_score < 90:
            next_steps.append("Implement improvement plan for identified gaps")
        
        if not next_steps:
            next_steps.append("Maintain current compliance status through regular monitoring")
        
        return next_steps
    
    def _identify_strengths(self, framework_results: Dict[ComplianceFramework, List[ValidationResult]]) -> List[str]:
        """Identify compliance strengths"""
        strengths = []
        
        for framework, results in framework_results.items():
            compliant_count = sum(1 for r in results if r.status == ComplianceStatus.COMPLIANT)
            if compliant_count == len(results) and results:
                strengths.append(f"Full compliance with {framework.value}")
        
        return strengths
    
    def _identify_improvement_areas(self, framework_results: Dict[ComplianceFramework, List[ValidationResult]]) -> List[str]:
        """Identify areas for improvement"""
        improvement_areas = []
        
        for framework, results in framework_results.items():
            failed_count = sum(1 for r in results if r.status == ComplianceStatus.NON_COMPLIANT)
            if failed_count > 0:
                improvement_areas.append(f"{framework.value}: {failed_count} non-compliant rules")
        
        return improvement_areas
    
    def _analyze_cross_framework_consistency(
        self,
        individual_results: Dict[ComplianceFramework, ValidationResponse],
        frameworks: List[ComplianceFramework]
    ) -> CrossFrameworkResult:
        """Analyze consistency across frameworks"""
        
        # Calculate harmonization score
        total_rules = sum(r.total_rules_checked for r in individual_results.values())
        total_passed = sum(r.rules_passed for r in individual_results.values())
        harmonization_score = (total_passed / total_rules * 100) if total_rules > 0 else 0
        
        # Identify consistent vs conflicting requirements
        consistent_requirements = []
        conflicting_requirements = []
        
        # This would be more sophisticated in production
        for framework, response in individual_results.items():
            if response.overall_status == ComplianceStatus.COMPLIANT:
                consistent_requirements.append(f"{framework.value} requirements")
            else:
                for conflict in response.rule_conflicts:
                    conflicting_requirements.append(conflict)
        
        return CrossFrameworkResult(
            frameworks_analyzed=frameworks,
            consistent_requirements=consistent_requirements,
            conflicting_requirements=conflicting_requirements,
            harmonization_score=harmonization_score,
            harmonization_issues=[f"Low harmonization score: {harmonization_score:.1f}%"] if harmonization_score < 80 else [],
            framework_prioritization={f: i for i, f in enumerate(frameworks, 1)},
            optimization_suggestions=[
                "Standardize validation criteria across frameworks",
                "Implement unified compliance dashboard",
                "Regular cross-framework compliance reviews"
            ]
        )
    
    def _check_cache(self, request: ValidationRequest) -> Optional[ValidationResponse]:
        """Check if validation result is cached"""
        cache_key = self._generate_cache_key(request)
        
        if cache_key in self.validation_cache:
            cache_entry = self.validation_cache[cache_key]
            if cache_entry.is_valid:
                cache_entry.access_count += 1
                cache_entry.last_access = datetime.now()
                return cache_entry.cached_response
            else:
                # Remove expired cache entry
                del self.validation_cache[cache_key]
        
        return None
    
    def _cache_result(self, request: ValidationRequest, response: ValidationResponse):
        """Cache validation result"""
        cache_key = self._generate_cache_key(request)
        request_hash = self._generate_request_hash(request)
        
        cache_entry = ValidationCache(
            cache_key=cache_key,
            request_hash=request_hash,
            cached_response=response,
            cache_ttl_seconds=self.cache_ttl_seconds,
            frameworks_involved=request.frameworks,
            data_fingerprint=self._generate_data_fingerprint(request.data)
        )
        
        self.validation_cache[cache_key] = cache_entry
    
    def _generate_cache_key(self, request: ValidationRequest) -> str:
        """Generate cache key for request"""
        key_data = {
            'frameworks': sorted([f.value for f in request.frameworks]),
            'data_hash': self._generate_data_fingerprint(request.data),
            'mode': request.validation_mode.value
        }
        return hashlib.md5(json.dumps(key_data, sort_keys=True).encode()).hexdigest()
    
    def _generate_request_hash(self, request: ValidationRequest) -> str:
        """Generate hash of the entire request"""
        request_dict = request.dict()
        return hashlib.sha256(json.dumps(request_dict, sort_keys=True, default=str).encode()).hexdigest()
    
    def _generate_data_fingerprint(self, data: Dict[str, Any]) -> str:
        """Generate fingerprint of validation data"""
        return hashlib.md5(json.dumps(data, sort_keys=True, default=str).encode()).hexdigest()
    
    def _create_error_response(self, request: ValidationRequest, error_message: str) -> ValidationResponse:
        """Create error response for failed validation"""
        return ValidationResponse(
            request_id=request.request_id,
            overall_status=ComplianceStatus.ERROR,
            overall_score=0.0,
            execution_time_ms=0.0,
            frameworks_validated=[],
            critical_issues=[error_message],
            recommendations=["Fix validation system error and retry"]
        )
    
    def _record_performance_metric(self, operation: str, execution_time: float, success: bool):
        """Record performance metric"""
        if operation not in self.performance_metrics:
            self.performance_metrics[operation] = {
                'total_calls': 0,
                'successful_calls': 0,
                'failed_calls': 0,
                'total_time': 0.0,
                'average_time': 0.0,
                'min_time': float('inf'),
                'max_time': 0.0
            }
        
        metrics = self.performance_metrics[operation]
        metrics['total_calls'] += 1
        metrics['total_time'] += execution_time
        metrics['average_time'] = metrics['total_time'] / metrics['total_calls']
        metrics['min_time'] = min(metrics['min_time'], execution_time)
        metrics['max_time'] = max(metrics['max_time'], execution_time)
        
        if success:
            metrics['successful_calls'] += 1
        else:
            metrics['failed_calls'] += 1
    
    def _calculate_cache_hit_rate(self) -> float:
        """Calculate cache hit rate"""
        if not self.validation_cache:
            return 0.0
        
        total_accesses = sum(entry.access_count for entry in self.validation_cache.values())
        if total_accesses == 0:
            return 0.0
        
        return (total_accesses / len(self.validation_cache)) * 100
    
    def _calculate_average_response_time(self) -> float:
        """Calculate average response time"""
        if 'validate' not in self.performance_metrics:
            return 0.0
        
        return self.performance_metrics['validate']['average_time']