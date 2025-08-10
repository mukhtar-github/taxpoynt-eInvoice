"""
Validation Aggregator
====================
Aggregates validation results across multiple frameworks and provides unified analysis.
"""

import logging
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime, timedelta
from decimal import Decimal
from collections import defaultdict, Counter

from .models import (
    ValidationResponse, AggregatedValidationResult, CrossFrameworkResult
)
from ..orchestrator.models import (
    ComplianceFramework, ComplianceStatus, ValidationSeverity, ValidationResult
)

logger = logging.getLogger(__name__)

class ValidationAggregator:
    """
    Aggregates and analyzes validation results across multiple compliance frameworks
    """
    
    def __init__(self):
        """Initialize validation aggregator"""
        self.logger = logging.getLogger(__name__)
        
        # Framework weights for scoring (higher weight = more important)
        self.framework_weights = {
            ComplianceFramework.FIRS: 0.25,        # 25% - Critical for Nigerian operations
            ComplianceFramework.CAC: 0.20,         # 20% - Essential for corporate compliance
            ComplianceFramework.NITDA: 0.15,       # 15% - Data protection compliance
            ComplianceFramework.ISO_27001: 0.10,   # 10% - Security management
            ComplianceFramework.ISO_20022: 0.08,   # 8% - Financial messaging
            ComplianceFramework.UBL: 0.07,         # 7% - Business document standards
            ComplianceFramework.PEPPOL: 0.05,      # 5% - Electronic procurement
            ComplianceFramework.GDPR: 0.03,        # 3% - EU data protection
            ComplianceFramework.NDPA: 0.03,        # 3% - Nigerian data protection
            ComplianceFramework.WCO_HS: 0.02,      # 2% - Product classification
            ComplianceFramework.LEI: 0.02          # 2% - Legal entity identification
        }
        
        # Severity weights for issue scoring
        self.severity_weights = {
            ValidationSeverity.CRITICAL: 100,
            ValidationSeverity.HIGH: 75,
            ValidationSeverity.MEDIUM: 50,
            ValidationSeverity.LOW: 25,
            ValidationSeverity.INFO: 10
        }
        
        self.logger.info("Validation Aggregator initialized")
    
    def aggregate_validation_results(self, responses: List[ValidationResponse]) -> AggregatedValidationResult:
        """
        Aggregate multiple validation responses into unified result
        
        Args:
            responses: List of validation responses to aggregate
            
        Returns:
            AggregatedValidationResult with comprehensive analysis
        """
        try:
            self.logger.info(f"Aggregating {len(responses)} validation responses")
            
            if not responses:
                raise ValueError("No validation responses provided for aggregation")
            
            # Calculate overall compliance score
            overall_score = self._calculate_weighted_compliance_score(responses)
            
            # Calculate framework scores
            framework_scores = self._calculate_framework_scores(responses)
            
            # Count issues by severity
            issue_counts = self._count_issues_by_severity(responses)
            
            # Categorize frameworks by compliance
            compliance_categorization = self._categorize_frameworks_by_compliance(responses)
            
            # Assess business risk and readiness
            risk_assessment = self._assess_business_risk(responses, overall_score)
            
            # Generate action plans
            action_plans = self._generate_action_plans(responses, issue_counts)
            
            # Calculate quality metrics
            quality_metrics = self._calculate_quality_metrics(responses)
            
            # Create aggregated result
            aggregated_result = AggregatedValidationResult(
                source_request_id=responses[0].request_id,
                overall_compliance_score=overall_score,
                framework_scores=framework_scores,
                framework_weights=self.framework_weights,
                total_critical_issues=issue_counts['critical'],
                total_high_issues=issue_counts['high'],
                total_medium_issues=issue_counts['medium'],
                total_low_issues=issue_counts['low'],
                fully_compliant_frameworks=compliance_categorization['fully_compliant'],
                partially_compliant_frameworks=compliance_categorization['partially_compliant'],
                non_compliant_frameworks=compliance_categorization['non_compliant'],
                business_risk_level=risk_assessment['risk_level'],
                compliance_readiness=risk_assessment['readiness'],
                estimated_remediation_effort=risk_assessment['remediation_effort'],
                immediate_actions=action_plans['immediate'],
                short_term_actions=action_plans['short_term'],
                long_term_actions=action_plans['long_term'],
                validation_confidence=quality_metrics['confidence'],
                data_completeness=quality_metrics['data_completeness'],
                rule_coverage=quality_metrics['rule_coverage']
            )
            
            self.logger.info(f"Aggregation completed with overall score: {overall_score:.2f}")
            return aggregated_result
            
        except Exception as e:
            self.logger.error(f"Validation aggregation failed: {str(e)}")
            raise
    
    def compare_validation_results(
        self,
        baseline_response: ValidationResponse,
        comparison_response: ValidationResponse
    ) -> Dict[str, Any]:
        """
        Compare two validation responses to identify changes
        
        Args:
            baseline_response: Baseline validation response
            comparison_response: Comparison validation response
            
        Returns:
            Dictionary with comparison analysis
        """
        try:
            self.logger.info("Comparing validation responses")
            
            comparison_result = {
                'score_change': comparison_response.overall_score - baseline_response.overall_score,
                'status_changes': {},
                'new_issues': [],
                'resolved_issues': [],
                'framework_changes': {},
                'improvement_summary': {}
            }
            
            # Compare overall status
            if baseline_response.overall_status != comparison_response.overall_status:
                comparison_result['status_changes']['overall'] = {
                    'from': baseline_response.overall_status,
                    'to': comparison_response.overall_status
                }
            
            # Compare framework results
            baseline_frameworks = set(baseline_response.framework_results.keys())
            comparison_frameworks = set(comparison_response.framework_results.keys())
            
            common_frameworks = baseline_frameworks & comparison_frameworks
            
            for framework in common_frameworks:
                baseline_results = baseline_response.framework_results[framework]
                comparison_results = comparison_response.framework_results[framework]
                
                framework_comparison = self._compare_framework_results(baseline_results, comparison_results)
                if framework_comparison:
                    comparison_result['framework_changes'][framework] = framework_comparison
            
            # Identify new and resolved issues
            baseline_issues = set(baseline_response.critical_issues + baseline_response.warnings)
            comparison_issues = set(comparison_response.critical_issues + comparison_response.warnings)
            
            comparison_result['new_issues'] = list(comparison_issues - baseline_issues)
            comparison_result['resolved_issues'] = list(baseline_issues - comparison_issues)
            
            # Generate improvement summary
            comparison_result['improvement_summary'] = self._generate_improvement_summary(comparison_result)
            
            return comparison_result
            
        except Exception as e:
            self.logger.error(f"Validation comparison failed: {str(e)}")
            raise
    
    def generate_trend_analysis(self, historical_responses: List[ValidationResponse]) -> Dict[str, Any]:
        """
        Generate trend analysis from historical validation responses
        
        Args:
            historical_responses: List of historical validation responses (chronologically ordered)
            
        Returns:
            Dictionary with trend analysis
        """
        try:
            self.logger.info(f"Generating trend analysis for {len(historical_responses)} historical responses")
            
            if len(historical_responses) < 2:
                return {'error': 'Insufficient historical data for trend analysis'}
            
            # Calculate score trends
            scores = [response.overall_score for response in historical_responses]
            score_trend = self._calculate_trend(scores)
            
            # Calculate issue trends by severity
            issue_trends = {}
            for severity in ValidationSeverity:
                severity_counts = []
                for response in historical_responses:
                    count = len([issue for result_list in response.framework_results.values() 
                               for result in result_list 
                               if result.severity == severity and result.status != ComplianceStatus.COMPLIANT])
                    severity_counts.append(count)
                issue_trends[severity.value] = self._calculate_trend(severity_counts)
            
            # Framework compliance trends
            framework_trends = {}
            for framework in ComplianceFramework:
                framework_scores = []
                for response in historical_responses:
                    if framework in response.framework_results:
                        results = response.framework_results[framework]
                        compliant_count = sum(1 for r in results if r.status == ComplianceStatus.COMPLIANT)
                        framework_score = (compliant_count / len(results) * 100) if results else 0
                        framework_scores.append(framework_score)
                    else:
                        framework_scores.append(0)
                
                if any(score > 0 for score in framework_scores):
                    framework_trends[framework.value] = self._calculate_trend(framework_scores)
            
            # Generate predictions
            predictions = self._generate_compliance_predictions(scores, issue_trends)
            
            trend_analysis = {
                'analysis_period': {
                    'start_date': historical_responses[0].validation_timestamp.isoformat(),
                    'end_date': historical_responses[-1].validation_timestamp.isoformat(),
                    'data_points': len(historical_responses)
                },
                'overall_score_trend': score_trend,
                'issue_trends': issue_trends,
                'framework_trends': framework_trends,
                'predictions': predictions,
                'key_insights': self._generate_trend_insights(score_trend, issue_trends, framework_trends)
            }
            
            return trend_analysis
            
        except Exception as e:
            self.logger.error(f"Trend analysis generation failed: {str(e)}")
            raise
    
    # Private helper methods
    
    def _calculate_weighted_compliance_score(self, responses: List[ValidationResponse]) -> float:
        """Calculate weighted overall compliance score"""
        total_weighted_score = 0.0
        total_weight = 0.0
        
        for response in responses:
            for framework in response.frameworks_validated:
                framework_weight = self.framework_weights.get(framework, 0.01)
                framework_score = response.overall_score  # Simplified - would calculate per framework
                
                total_weighted_score += framework_score * framework_weight
                total_weight += framework_weight
        
        return (total_weighted_score / total_weight) if total_weight > 0 else 0.0
    
    def _calculate_framework_scores(self, responses: List[ValidationResponse]) -> Dict[ComplianceFramework, float]:
        """Calculate individual framework scores"""
        framework_scores = {}
        
        for response in responses:
            for framework, results in response.framework_results.items():
                if results:
                    compliant_count = sum(1 for r in results if r.status == ComplianceStatus.COMPLIANT)
                    framework_score = (compliant_count / len(results)) * 100
                    framework_scores[framework] = framework_score
                else:
                    framework_scores[framework] = 0.0
        
        return framework_scores
    
    def _count_issues_by_severity(self, responses: List[ValidationResponse]) -> Dict[str, int]:
        """Count issues by severity across all responses"""
        issue_counts = {
            'critical': 0,
            'high': 0,
            'medium': 0,
            'low': 0
        }
        
        for response in responses:
            for results in response.framework_results.values():
                for result in results:
                    if result.status != ComplianceStatus.COMPLIANT:
                        if result.severity == ValidationSeverity.CRITICAL:
                            issue_counts['critical'] += 1
                        elif result.severity == ValidationSeverity.HIGH:
                            issue_counts['high'] += 1
                        elif result.severity == ValidationSeverity.MEDIUM:
                            issue_counts['medium'] += 1
                        elif result.severity == ValidationSeverity.LOW:
                            issue_counts['low'] += 1
        
        return issue_counts
    
    def _categorize_frameworks_by_compliance(self, responses: List[ValidationResponse]) -> Dict[str, List[ComplianceFramework]]:
        """Categorize frameworks by compliance level"""
        categorization = {
            'fully_compliant': [],
            'partially_compliant': [],
            'non_compliant': []
        }
        
        framework_compliance = {}
        
        for response in responses:
            for framework, results in response.framework_results.items():
                if results:
                    compliant_count = sum(1 for r in results if r.status == ComplianceStatus.COMPLIANT)
                    compliance_rate = (compliant_count / len(results)) * 100
                    framework_compliance[framework] = compliance_rate
        
        for framework, compliance_rate in framework_compliance.items():
            if compliance_rate == 100:
                categorization['fully_compliant'].append(framework)
            elif compliance_rate >= 70:
                categorization['partially_compliant'].append(framework)
            else:
                categorization['non_compliant'].append(framework)
        
        return categorization
    
    def _assess_business_risk(self, responses: List[ValidationResponse], overall_score: float) -> Dict[str, str]:
        """Assess business risk based on compliance results"""
        critical_issues = sum(len(response.critical_issues) for response in responses)
        
        # Determine risk level
        if critical_issues > 5 or overall_score < 60:
            risk_level = "high"
        elif critical_issues > 2 or overall_score < 80:
            risk_level = "medium"
        else:
            risk_level = "low"
        
        # Determine readiness
        if overall_score >= 95:
            readiness = "ready"
        elif overall_score >= 85:
            readiness = "mostly_ready"
        elif overall_score >= 70:
            readiness = "partially_ready"
        else:
            readiness = "not_ready"
        
        # Estimate remediation effort
        if overall_score >= 90:
            remediation_effort = "minimal"
        elif overall_score >= 75:
            remediation_effort = "moderate"
        elif overall_score >= 60:
            remediation_effort = "significant"
        else:
            remediation_effort = "extensive"
        
        return {
            'risk_level': risk_level,
            'readiness': readiness,
            'remediation_effort': remediation_effort
        }
    
    def _generate_action_plans(self, responses: List[ValidationResponse], issue_counts: Dict[str, int]) -> Dict[str, List[str]]:
        """Generate action plans based on validation results"""
        action_plans = {
            'immediate': [],
            'short_term': [],
            'long_term': []
        }
        
        # Immediate actions (critical issues)
        if issue_counts['critical'] > 0:
            action_plans['immediate'].append(f"Address {issue_counts['critical']} critical compliance issues")
        
        if issue_counts['high'] > 3:
            action_plans['immediate'].append("Review and fix high-priority compliance gaps")
        
        # Short-term actions (30 days)
        if issue_counts['medium'] > 0:
            action_plans['short_term'].append(f"Resolve {issue_counts['medium']} medium-priority issues")
        
        if any(len(response.rule_conflicts) > 0 for response in responses):
            action_plans['short_term'].append("Resolve rule conflicts between frameworks")
        
        # Long-term actions (strategic)
        action_plans['long_term'].append("Implement automated compliance monitoring")
        action_plans['long_term'].append("Regular compliance assessment and improvement")
        action_plans['long_term'].append("Staff training on regulatory requirements")
        
        return action_plans
    
    def _calculate_quality_metrics(self, responses: List[ValidationResponse]) -> Dict[str, float]:
        """Calculate validation quality metrics"""
        total_rules = sum(response.total_rules_checked for response in responses)
        total_execution_time = sum(response.execution_time_ms for response in responses)
        
        # Confidence based on execution success and completeness
        confidence = 100.0
        for response in responses:
            if response.overall_status == ComplianceStatus.ERROR:
                confidence -= 20.0
            elif len(response.warnings) > 0:
                confidence -= 5.0
        
        confidence = max(0.0, min(100.0, confidence))
        
        # Data completeness (simplified)
        data_completeness = 100.0  # Would be calculated based on required vs provided data
        
        # Rule coverage
        rule_coverage = 100.0  # Would be calculated based on applicable vs executed rules
        
        return {
            'confidence': confidence,
            'data_completeness': data_completeness,
            'rule_coverage': rule_coverage,
            'average_execution_time': total_execution_time / len(responses) if responses else 0
        }
    
    def _compare_framework_results(self, baseline_results: List[ValidationResult], comparison_results: List[ValidationResult]) -> Optional[Dict[str, Any]]:
        """Compare framework results between two validations"""
        if not baseline_results or not comparison_results:
            return None
        
        baseline_status_count = Counter(r.status for r in baseline_results)
        comparison_status_count = Counter(r.status for r in comparison_results)
        
        changes = {}
        for status in ComplianceStatus:
            baseline_count = baseline_status_count.get(status, 0)
            comparison_count = comparison_status_count.get(status, 0)
            
            if baseline_count != comparison_count:
                changes[status.value] = {
                    'from': baseline_count,
                    'to': comparison_count,
                    'change': comparison_count - baseline_count
                }
        
        return changes if changes else None
    
    def _generate_improvement_summary(self, comparison_result: Dict[str, Any]) -> Dict[str, Any]:
        """Generate improvement summary from comparison"""
        summary = {
            'overall_improvement': comparison_result['score_change'] > 0,
            'score_change_magnitude': abs(comparison_result['score_change']),
            'issues_resolved': len(comparison_result['resolved_issues']),
            'new_issues_introduced': len(comparison_result['new_issues']),
            'net_improvement': len(comparison_result['resolved_issues']) - len(comparison_result['new_issues'])
        }
        
        # Generate textual summary
        if comparison_result['score_change'] > 10:
            summary['improvement_level'] = "significant_improvement"
        elif comparison_result['score_change'] > 0:
            summary['improvement_level'] = "improvement"
        elif comparison_result['score_change'] == 0:
            summary['improvement_level'] = "no_change"
        elif comparison_result['score_change'] > -10:
            summary['improvement_level'] = "minor_regression"
        else:
            summary['improvement_level'] = "significant_regression"
        
        return summary
    
    def _calculate_trend(self, values: List[float]) -> Dict[str, Any]:
        """Calculate trend for a series of values"""
        if len(values) < 2:
            return {'trend': 'insufficient_data'}
        
        # Simple linear trend calculation
        n = len(values)
        x_sum = sum(range(n))
        y_sum = sum(values)
        xy_sum = sum(i * values[i] for i in range(n))
        x2_sum = sum(i * i for i in range(n))
        
        slope = (n * xy_sum - x_sum * y_sum) / (n * x2_sum - x_sum * x_sum) if (n * x2_sum - x_sum * x_sum) != 0 else 0
        
        # Determine trend direction
        if slope > 0.5:
            trend_direction = "improving"
        elif slope < -0.5:
            trend_direction = "declining"
        else:
            trend_direction = "stable"
        
        return {
            'trend': trend_direction,
            'slope': slope,
            'start_value': values[0],
            'end_value': values[-1],
            'change': values[-1] - values[0],
            'change_percentage': ((values[-1] - values[0]) / values[0] * 100) if values[0] != 0 else 0
        }
    
    def _generate_compliance_predictions(self, scores: List[float], issue_trends: Dict[str, Dict[str, Any]]) -> Dict[str, Any]:
        """Generate compliance predictions based on trends"""
        predictions = {}
        
        if len(scores) >= 3:
            recent_trend = self._calculate_trend(scores[-3:])
            
            # Predict next score
            if recent_trend['slope'] != 0:
                predicted_next_score = scores[-1] + recent_trend['slope']
                predicted_next_score = max(0, min(100, predicted_next_score))
                predictions['next_score'] = predicted_next_score
            
            # Predict time to full compliance
            if scores[-1] < 100 and recent_trend['slope'] > 0:
                periods_to_compliance = (100 - scores[-1]) / recent_trend['slope']
                predictions['periods_to_full_compliance'] = max(1, int(periods_to_compliance))
        
        return predictions
    
    def _generate_trend_insights(
        self,
        score_trend: Dict[str, Any],
        issue_trends: Dict[str, Dict[str, Any]],
        framework_trends: Dict[str, Dict[str, Any]]
    ) -> List[str]:
        """Generate key insights from trend analysis"""
        insights = []
        
        # Overall score insights
        if score_trend.get('trend') == 'improving':
            insights.append(f"Overall compliance score is improving with {score_trend.get('change_percentage', 0):.1f}% increase")
        elif score_trend.get('trend') == 'declining':
            insights.append(f"Overall compliance score is declining with {score_trend.get('change_percentage', 0):.1f}% decrease")
        
        # Issue trend insights
        for severity, trend in issue_trends.items():
            if trend.get('trend') == 'improving' and severity in ['critical', 'high']:
                insights.append(f"Significant reduction in {severity} severity issues")
            elif trend.get('trend') == 'declining' and severity in ['critical', 'high']:
                insights.append(f"Concerning increase in {severity} severity issues")
        
        # Framework insights
        improving_frameworks = [f for f, trend in framework_trends.items() if trend.get('trend') == 'improving']
        if improving_frameworks:
            insights.append(f"Improving compliance in: {', '.join(improving_frameworks[:3])}")
        
        declining_frameworks = [f for f, trend in framework_trends.items() if trend.get('trend') == 'declining']
        if declining_frameworks:
            insights.append(f"Declining compliance in: {', '.join(declining_frameworks[:3])}")
        
        return insights