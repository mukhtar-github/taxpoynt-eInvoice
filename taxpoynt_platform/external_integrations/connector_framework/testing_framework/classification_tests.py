"""
Classification Engine Testing Suite
===================================

Comprehensive testing for Nigerian transaction classification accuracy,
performance, privacy compliance, and cost optimization.
"""

import logging
import asyncio
import pytest
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timedelta
from decimal import Decimal
from dataclasses import dataclass
import statistics
import json

from ..classification_engine import (
    NigerianTransactionClassifier,
    TransactionClassificationRequest,
    TransactionClassificationResult,
    UserContext,
    BusinessContext,
    ClassificationTier,
    PrivacyLevel,
    TaxCategory
)
from ..classification_engine.cost_optimizer import CostOptimizer, OptimizationStrategy
from ..classification_engine.privacy_protection import APIPrivacyProtection
from ..classification_engine.cache_manager import ClassificationCacheManager, CacheStrategy
from ..classification_engine.rule_fallback import NigerianRuleFallback
from ..classification_engine.usage_tracker import ClassificationUsageTracker

from .mock_providers import MockOpenAIClient, MockRedisClient

logger = logging.getLogger(__name__)

@dataclass
class TestCase:
    """Individual test case for classification"""
    
    name: str
    transaction_data: Dict[str, Any]
    expected_result: Dict[str, Any]
    confidence_threshold: float = 0.7
    description: Optional[str] = None

@dataclass
class AccuracyMetrics:
    """Classification accuracy metrics"""
    
    total_tests: int
    correct_predictions: int
    false_positives: int
    false_negatives: int
    average_confidence: float
    accuracy_percentage: float
    precision: float
    recall: float
    f1_score: float

class NigerianTestDataGenerator:
    """Generate realistic Nigerian transaction test data"""
    
    def __init__(self):
        self.logger = logging.getLogger(f"{__name__}.NigerianTestDataGenerator")
        
        # Nigerian business patterns
        self.business_patterns = {
            'strong_business': [
                ("Payment for goods supplied to Alaba Market", True, 0.90),
                ("Invoice settlement - Contract 2024/001", True, 0.95),
                ("Professional consultation fee - Legal services", True, 0.88),
                ("Sales revenue from Victoria Island outlet", True, 0.92),
                ("Commission payment - Real estate transaction", True, 0.85),
                ("Service delivery payment - IT support", True, 0.87),
                ("Supply of office equipment - Lagos branch", True, 0.90),
                ("Contract payment - Construction project", True, 0.93)
            ],
            'moderate_business': [
                ("Payment for services rendered", True, 0.75),
                ("Business transaction - quarterly payment", True, 0.70),
                ("Purchase of goods for retail", True, 0.72),
                ("Professional service fee", True, 0.78),
                ("Sales payment received", True, 0.74)
            ],
            'strong_personal': [
                ("Salary payment - January 2024", False, 0.95),
                ("Family support - Monthly allowance", False, 0.90),
                ("Personal loan repayment", False, 0.88),
                ("School fees payment - University", False, 0.85),
                ("Medical expenses - Hospital bill", False, 0.87),
                ("Rent payment - Apartment in Lekki", False, 0.82),
                ("Airtime recharge - MTN", False, 0.95),
                ("Gift money from relatives", False, 0.90)
            ],
            'edge_cases': [
                ("Transfer", None, 0.40),  # Ambiguous
                ("Payment", None, 0.45),   # Very generic
                ("TRNSFR/FRM/12345", None, 0.35),  # Bank code
                ("", None, 0.30),  # Empty narration
                ("Cash deposit", None, 0.50)  # Could be either
            ]
        }
        
        # Nigerian business locations
        self.business_locations = [
            "Computer Village Lagos", "Alaba Market", "Trade Fair Complex",
            "Victoria Island", "Lekki Business District", "Ikeja GRA",
            "Wuse Market Abuja", "Central Area Abuja", "Port Harcourt Mall",
            "Onitsha Main Market", "Aba Commercial Center"
        ]
        
        # Nigerian names and businesses
        self.nigerian_names = [
            "Adebayo Enterprises Ltd", "Fatima Trading Company", "Chinedu Ventures",
            "Aisha Manufacturing", "Emeka Global Services", "Kemi Consulting",
            "Ibrahim Construction", "Blessing Motors", "Yusuf Logistics"
        ]
    
    def generate_test_suite(self, count: int = 100) -> List[TestCase]:
        """Generate comprehensive test suite"""
        
        test_cases = []
        
        # Add pattern-based tests
        for category, patterns in self.business_patterns.items():
            for narration, expected_business, expected_confidence in patterns:
                test_case = TestCase(
                    name=f"{category}_{len(test_cases)}",
                    transaction_data={
                        'amount': Decimal('50000'),
                        'narration': narration,
                        'date': datetime.utcnow(),
                        'time': '14:30',
                        'sender_name': 'Test Sender'
                    },
                    expected_result={
                        'is_business_income': expected_business,
                        'confidence_min': expected_confidence - 0.1,
                        'confidence_max': expected_confidence + 0.1
                    },
                    confidence_threshold=0.6,
                    description=f"Test {category} pattern recognition"
                )
                test_cases.append(test_case)
        
        # Add amount-based tests
        amount_tests = [
            (Decimal('500'), "Small retail transaction", True, 0.60),
            (Decimal('25000'), "Medium business payment", True, 0.75),
            (Decimal('500000'), "Large business contract", True, 0.85),
            (Decimal('100'), "Micro payment", False, 0.70)
        ]
        
        for amount, description, expected_business, expected_confidence in amount_tests:
            test_case = TestCase(
                name=f"amount_test_{amount}",
                transaction_data={
                    'amount': amount,
                    'narration': description,
                    'date': datetime.utcnow(),
                    'time': '10:00',
                    'sender_name': 'Amount Test'
                },
                expected_result={
                    'is_business_income': expected_business,
                    'confidence_min': expected_confidence - 0.15,
                    'confidence_max': expected_confidence + 0.15
                },
                description=f"Amount-based classification test"
            )
            test_cases.append(test_case)
        
        # Add time-based tests
        time_tests = [
            ('09:00', 'weekday', True, 0.65),   # Business hours
            ('22:00', 'weekday', False, 0.60),  # After hours
            ('14:00', 'saturday', True, 0.60),  # Weekend business
            ('02:00', 'sunday', False, 0.70)    # Late night
        ]
        
        for time_str, day_type, expected_business, expected_confidence in time_tests:
            test_date = datetime.utcnow()
            if day_type == 'saturday':
                test_date = test_date + timedelta(days=(5 - test_date.weekday()))
            elif day_type == 'sunday':
                test_date = test_date + timedelta(days=(6 - test_date.weekday()))
            
            test_case = TestCase(
                name=f"time_test_{time_str}_{day_type}",
                transaction_data={
                    'amount': Decimal('30000'),
                    'narration': 'Standard payment transaction',
                    'date': test_date,
                    'time': time_str,
                    'sender_name': 'Time Test'
                },
                expected_result={
                    'is_business_income': expected_business,
                    'confidence_min': expected_confidence - 0.2,
                    'confidence_max': expected_confidence + 0.2
                },
                description=f"Time-based classification test"
            )
            test_cases.append(test_case)
        
        return test_cases[:count]

class ClassificationTestSuite:
    """Comprehensive classification testing suite"""
    
    def __init__(self):
        self.logger = logging.getLogger(f"{__name__}.ClassificationTestSuite")
        self.test_data_generator = NigerianTestDataGenerator()
        
        # Initialize test dependencies
        self.mock_openai = MockOpenAIClient()
        self.mock_redis = MockRedisClient()
        
    async def run_accuracy_tests(self, 
                               classifier: NigerianTransactionClassifier,
                               test_count: int = 100) -> AccuracyMetrics:
        """Run classification accuracy tests"""
        
        self.logger.info(f"Running accuracy tests with {test_count} test cases")
        
        test_cases = self.test_data_generator.generate_test_suite(test_count)
        results = []
        
        for test_case in test_cases:
            try:
                # Create classification request
                request = TransactionClassificationRequest(
                    amount=test_case.transaction_data['amount'],
                    narration=test_case.transaction_data['narration'],
                    date=test_case.transaction_data['date'],
                    time=test_case.transaction_data['time'],
                    sender_name=test_case.transaction_data['sender_name'],
                    user_context=self._create_test_user_context(),
                    request_id=f"test_{test_case.name}"
                )
                
                # Classify transaction
                result = await classifier.classify_transaction(request)
                
                # Evaluate result
                is_correct = self._evaluate_result(result, test_case.expected_result)
                
                results.append({
                    'test_case': test_case,
                    'result': result,
                    'is_correct': is_correct,
                    'actual_business': result.is_business_income,
                    'expected_business': test_case.expected_result.get('is_business_income'),
                    'confidence': result.confidence
                })
                
            except Exception as e:
                self.logger.error(f"Error in test case {test_case.name}: {e}")
                results.append({
                    'test_case': test_case,
                    'result': None,
                    'is_correct': False,
                    'error': str(e)
                })
        
        # Calculate metrics
        metrics = self._calculate_accuracy_metrics(results)
        
        self.logger.info(f"Accuracy test completed: {metrics.accuracy_percentage:.2f}% accuracy")
        return metrics
    
    async def run_performance_tests(self,
                                  classifier: NigerianTransactionClassifier,
                                  test_count: int = 50) -> Dict[str, Any]:
        """Run classification performance tests"""
        
        self.logger.info(f"Running performance tests with {test_count} requests")
        
        test_cases = self.test_data_generator.generate_test_suite(test_count)
        response_times = []
        
        start_time = datetime.utcnow()
        
        for test_case in test_cases:
            request_start = datetime.utcnow()
            
            try:
                request = TransactionClassificationRequest(
                    amount=test_case.transaction_data['amount'],
                    narration=test_case.transaction_data['narration'],
                    date=test_case.transaction_data['date'],
                    time=test_case.transaction_data['time'],
                    user_context=self._create_test_user_context(),
                    request_id=f"perf_test_{test_case.name}"
                )
                
                await classifier.classify_transaction(request)
                
                request_end = datetime.utcnow()
                response_time = (request_end - request_start).total_seconds() * 1000
                response_times.append(response_time)
                
            except Exception as e:
                self.logger.error(f"Performance test error: {e}")
        
        total_time = (datetime.utcnow() - start_time).total_seconds()
        
        # Calculate performance metrics
        if response_times:
            avg_response_time = statistics.mean(response_times)
            median_response_time = statistics.median(response_times)
            p95_response_time = response_times[int(len(response_times) * 0.95)] if len(response_times) > 20 else max(response_times)
            throughput = len(response_times) / total_time
        else:
            avg_response_time = median_response_time = p95_response_time = throughput = 0
        
        return {
            'performance_summary': {
                'total_requests': test_count,
                'successful_requests': len(response_times),
                'failed_requests': test_count - len(response_times),
                'total_time_seconds': total_time,
                'throughput_requests_per_second': round(throughput, 2)
            },
            'response_times': {
                'average_ms': round(avg_response_time, 2),
                'median_ms': round(median_response_time, 2),
                'p95_ms': round(p95_response_time, 2),
                'min_ms': round(min(response_times), 2) if response_times else 0,
                'max_ms': round(max(response_times), 2) if response_times else 0
            },
            'performance_grade': self._grade_performance(avg_response_time, throughput)
        }
    
    async def run_privacy_tests(self,
                              privacy_protection: APIPrivacyProtection) -> Dict[str, Any]:
        """Test privacy protection and NDPR compliance"""
        
        self.logger.info("Running privacy protection tests")
        
        # Test cases with PII
        pii_test_cases = [
            {
                'name': 'phone_number_test',
                'narration': 'Payment from John Doe +2348012345678',
                'expected_redactions': ['phone_number']
            },
            {
                'name': 'account_number_test', 
                'narration': 'Transfer from account 1234567890',
                'expected_redactions': ['account_number']
            },
            {
                'name': 'email_test',
                'narration': 'Payment from john.doe@example.com',
                'expected_redactions': ['email']
            },
            {
                'name': 'multiple_pii_test',
                'narration': 'Transfer from Adebayo Johnson +2347012345678 account 9876543210',
                'expected_redactions': ['phone_number', 'account_number', 'name']
            }
        ]
        
        privacy_results = []
        
        for test_case in pii_test_cases:
            # Create test request
            request = TransactionClassificationRequest(
                amount=Decimal('25000'),
                narration=test_case['narration'],
                date=datetime.utcnow(),
                user_context=self._create_test_user_context(),
                privacy_level=PrivacyLevel.HIGH,
                request_id=f"privacy_test_{test_case['name']}"
            )
            
            # Anonymize data
            anonymized_data = privacy_protection.anonymize_for_api(request)
            
            # Validate anonymization
            validation_report = privacy_protection.validate_anonymization(anonymized_data)
            
            # Check for expected redactions
            anonymized_narration = anonymized_data.get('narration', '')
            redactions_found = []
            
            if '[PHONE]' in anonymized_narration:
                redactions_found.append('phone_number')
            if '[ACCOUNT]' in anonymized_narration:
                redactions_found.append('account_number')
            if '[EMAIL]' in anonymized_narration:
                redactions_found.append('email')
            if '[NAME]' in anonymized_narration:
                redactions_found.append('name')
            
            privacy_results.append({
                'test_case': test_case['name'],
                'original_narration': test_case['narration'],
                'anonymized_narration': anonymized_narration,
                'expected_redactions': test_case['expected_redactions'],
                'found_redactions': redactions_found,
                'validation_passed': validation_report['is_valid'],
                'privacy_score': validation_report['privacy_score']
            })
        
        # Calculate privacy compliance score
        total_tests = len(privacy_results)
        passed_tests = sum(1 for r in privacy_results if r['validation_passed'])
        compliance_score = (passed_tests / total_tests) * 100
        
        return {
            'privacy_compliance': {
                'total_tests': total_tests,
                'passed_tests': passed_tests,
                'compliance_score_percent': round(compliance_score, 2),
                'ndpr_compliant': compliance_score >= 95
            },
            'test_results': privacy_results,
            'recommendations': self._generate_privacy_recommendations(privacy_results)
        }
    
    async def run_cost_optimization_tests(self,
                                        cost_optimizer: CostOptimizer) -> Dict[str, Any]:
        """Test cost optimization strategies"""
        
        self.logger.info("Running cost optimization tests")
        
        # Test different transaction complexities
        complexity_tests = [
            {
                'name': 'simple_transaction',
                'amount': Decimal('1000'),
                'narration': 'Payment',
                'expected_tier': ClassificationTier.RULE_BASED
            },
            {
                'name': 'complex_transaction',
                'amount': Decimal('500000'),
                'narration': 'Multi-party contract settlement with international vendor',
                'expected_tier': ClassificationTier.API_PREMIUM
            },
            {
                'name': 'ambiguous_transaction',
                'amount': Decimal('50000'),
                'narration': 'Transfer from John',
                'expected_tier': ClassificationTier.API_LITE
            }
        ]
        
        optimization_results = []
        total_estimated_cost = Decimal('0')
        
        for test in complexity_tests:
            request = TransactionClassificationRequest(
                amount=test['amount'],
                narration=test['narration'],
                date=datetime.utcnow(),
                user_context=self._create_test_user_context(),
                request_id=f"cost_test_{test['name']}"
            )
            
            # Test different strategies
            for strategy in OptimizationStrategy:
                recommended_tier = await cost_optimizer.optimize_classification_tier(
                    request, strategy
                )
                
                estimated_cost = cost_optimizer.estimate_cost(recommended_tier)
                total_estimated_cost += estimated_cost
                
                optimization_results.append({
                    'test_name': test['name'],
                    'strategy': strategy.value,
                    'recommended_tier': recommended_tier.value,
                    'expected_tier': test['expected_tier'].value,
                    'estimated_cost_ngn': float(estimated_cost),
                    'tier_matches_expected': recommended_tier == test['expected_tier']
                })
        
        # Calculate optimization effectiveness
        correct_recommendations = sum(
            1 for r in optimization_results 
            if r['tier_matches_expected']
        )
        
        optimization_score = (correct_recommendations / len(optimization_results)) * 100
        
        return {
            'cost_optimization': {
                'total_tests': len(optimization_results),
                'correct_recommendations': correct_recommendations,
                'optimization_score_percent': round(optimization_score, 2),
                'total_estimated_cost_ngn': float(total_estimated_cost)
            },
            'strategy_performance': self._analyze_strategy_performance(optimization_results),
            'test_results': optimization_results
        }
    
    def _create_test_user_context(self) -> UserContext:
        """Create test user context"""
        
        business_context = BusinessContext(
            industry="Technology",
            business_size="medium",
            annual_revenue=Decimal("50000000"),
            employee_count=25,
            years_in_operation=5,
            state="Lagos",
            business_type="limited_liability"
        )
        
        return UserContext(
            user_id="test_user_123",
            organization_id="test_org_456",
            subscription_tier="PROFESSIONAL",
            business_context=business_context,
            previous_classifications=[]
        )
    
    def _evaluate_result(self, 
                        result: TransactionClassificationResult,
                        expected: Dict[str, Any]) -> bool:
        """Evaluate if classification result matches expected outcome"""
        
        # Check business classification
        expected_business = expected.get('is_business_income')
        if expected_business is not None and result.is_business_income != expected_business:
            return False
        
        # Check confidence range
        confidence_min = expected.get('confidence_min', 0.0)
        confidence_max = expected.get('confidence_max', 1.0)
        if not (confidence_min <= result.confidence <= confidence_max):
            return False
        
        return True
    
    def _calculate_accuracy_metrics(self, results: List[Dict[str, Any]]) -> AccuracyMetrics:
        """Calculate comprehensive accuracy metrics"""
        
        # Filter out error cases
        valid_results = [r for r in results if r.get('result') is not None]
        
        if not valid_results:
            return AccuracyMetrics(0, 0, 0, 0, 0.0, 0.0, 0.0, 0.0, 0.0)
        
        # Count correct predictions
        correct_predictions = sum(1 for r in valid_results if r['is_correct'])
        
        # Calculate confusion matrix
        true_positives = sum(
            1 for r in valid_results 
            if r['actual_business'] == True and r['expected_business'] == True
        )
        
        false_positives = sum(
            1 for r in valid_results 
            if r['actual_business'] == True and r['expected_business'] == False
        )
        
        false_negatives = sum(
            1 for r in valid_results 
            if r['actual_business'] == False and r['expected_business'] == True
        )
        
        true_negatives = sum(
            1 for r in valid_results 
            if r['actual_business'] == False and r['expected_business'] == False
        )
        
        # Calculate metrics
        total_tests = len(valid_results)
        accuracy = (correct_predictions / total_tests) * 100
        
        precision = true_positives / max(1, true_positives + false_positives)
        recall = true_positives / max(1, true_positives + false_negatives)
        f1_score = 2 * (precision * recall) / max(0.001, precision + recall)
        
        confidences = [r['confidence'] for r in valid_results if r.get('confidence')]
        avg_confidence = statistics.mean(confidences) if confidences else 0.0
        
        return AccuracyMetrics(
            total_tests=total_tests,
            correct_predictions=correct_predictions,
            false_positives=false_positives,
            false_negatives=false_negatives,
            average_confidence=avg_confidence,
            accuracy_percentage=accuracy,
            precision=precision,
            recall=recall,
            f1_score=f1_score
        )
    
    def _grade_performance(self, avg_response_time: float, throughput: float) -> str:
        """Grade performance based on response time and throughput"""
        
        if avg_response_time < 1000 and throughput > 10:
            return "EXCELLENT"
        elif avg_response_time < 2000 and throughput > 5:
            return "GOOD"
        elif avg_response_time < 5000 and throughput > 2:
            return "ACCEPTABLE"
        else:
            return "NEEDS_IMPROVEMENT"
    
    def _generate_privacy_recommendations(self, results: List[Dict[str, Any]]) -> List[str]:
        """Generate privacy improvement recommendations"""
        
        recommendations = []
        
        failed_tests = [r for r in results if not r['validation_passed']]
        
        if failed_tests:
            recommendations.append("Review PII detection patterns for improved accuracy")
        
        low_privacy_scores = [r for r in results if r['privacy_score'] < 0.8]
        if low_privacy_scores:
            recommendations.append("Consider implementing stricter anonymization for sensitive data")
        
        if not recommendations:
            recommendations.append("Privacy protection is functioning well")
        
        return recommendations
    
    def _analyze_strategy_performance(self, results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze cost optimization strategy performance"""
        
        strategy_analysis = {}
        
        for strategy in OptimizationStrategy:
            strategy_results = [r for r in results if r['strategy'] == strategy.value]
            
            if strategy_results:
                correct_count = sum(1 for r in strategy_results if r['tier_matches_expected'])
                total_cost = sum(r['estimated_cost_ngn'] for r in strategy_results)
                
                strategy_analysis[strategy.value] = {
                    'accuracy_percent': round((correct_count / len(strategy_results)) * 100, 2),
                    'total_cost_ngn': round(total_cost, 2),
                    'avg_cost_per_transaction': round(total_cost / len(strategy_results), 2)
                }
        
        return strategy_analysis

class AccuracyTester:
    """Dedicated accuracy testing utility"""
    
    def __init__(self):
        self.logger = logging.getLogger(f"{__name__}.AccuracyTester")
    
    async def test_nigerian_patterns(self, 
                                   classifier: NigerianTransactionClassifier) -> Dict[str, Any]:
        """Test Nigerian-specific pattern recognition"""
        
        nigerian_patterns = [
            # Lagos business patterns
            ("Payment for goods - Computer Village Lagos", True, 0.85),
            ("Service payment - Victoria Island office", True, 0.80),
            ("Contract settlement - Lekki business district", True, 0.85),
            
            # Market patterns  
            ("Purchase from Alaba Market vendor", True, 0.90),
            ("Sales payment - Trade Fair Complex", True, 0.88),
            ("Goods supply - Onitsha Main Market", True, 0.87),
            
            # Nigerian business terms
            ("Payment for contract work - Naira denomination", True, 0.75),
            ("Professional service - Engineering consultation", True, 0.82),
            ("Business transaction - Import/Export", True, 0.85),
            
            # Personal patterns
            ("Salary payment - December 2024", False, 0.90),
            ("Family support - Monthly contribution", False, 0.85),
            ("School fees - University of Lagos", False, 0.88),
            ("Medical bills - General Hospital", False, 0.80)
        ]
        
        results = []
        
        for narration, expected_business, expected_confidence in nigerian_patterns:
            request = TransactionClassificationRequest(
                amount=Decimal('50000'),
                narration=narration,
                date=datetime.utcnow(),
                user_context=self._create_nigerian_user_context(),
                request_id=f"nigerian_test_{len(results)}"
            )
            
            result = await classifier.classify_transaction(request)
            
            # Evaluate accuracy
            is_correct = result.is_business_income == expected_business
            confidence_in_range = abs(result.confidence - expected_confidence) <= 0.2
            
            results.append({
                'narration': narration,
                'expected_business': expected_business,
                'actual_business': result.is_business_income,
                'expected_confidence': expected_confidence,
                'actual_confidence': result.confidence,
                'is_correct': is_correct,
                'confidence_acceptable': confidence_in_range,
                'reasoning': result.reasoning
            })
        
        # Calculate Nigerian pattern accuracy
        correct_classifications = sum(1 for r in results if r['is_correct'])
        accuracy = (correct_classifications / len(results)) * 100
        
        return {
            'nigerian_pattern_accuracy': {
                'total_patterns_tested': len(results),
                'correct_classifications': correct_classifications,
                'accuracy_percentage': round(accuracy, 2),
                'patterns_by_category': self._categorize_pattern_results(results)
            },
            'detailed_results': results
        }
    
    def _create_nigerian_user_context(self) -> UserContext:
        """Create Nigerian business context for testing"""
        
        business_context = BusinessContext(
            industry="Trading",
            business_size="medium",
            annual_revenue=Decimal("100000000"),
            employee_count=15,
            years_in_operation=8,
            state="Lagos",
            business_type="limited_liability"
        )
        
        return UserContext(
            user_id="nigerian_test_user",
            organization_id="nigerian_test_org",
            subscription_tier="PROFESSIONAL",
            business_context=business_context,
            previous_classifications=[
                {'sender_name': 'Alaba Vendor', 'is_business_income': True, 'amount': 25000},
                {'sender_name': 'Family Member', 'is_business_income': False, 'amount': 15000}
            ]
        )
    
    def _categorize_pattern_results(self, results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Categorize pattern test results"""
        
        categories = {
            'lagos_business': [],
            'market_patterns': [],
            'business_terms': [],
            'personal_patterns': []
        }
        
        for result in results:
            narration = result['narration'].lower()
            
            if any(location in narration for location in ['computer village', 'victoria island', 'lekki']):
                categories['lagos_business'].append(result)
            elif any(market in narration for market in ['alaba', 'trade fair', 'onitsha', 'market']):
                categories['market_patterns'].append(result)
            elif any(term in narration for term in ['contract', 'professional', 'business']):
                categories['business_terms'].append(result)
            else:
                categories['personal_patterns'].append(result)
        
        # Calculate accuracy for each category
        category_accuracy = {}
        for category, results_list in categories.items():
            if results_list:
                correct = sum(1 for r in results_list if r['is_correct'])
                accuracy = (correct / len(results_list)) * 100
                category_accuracy[category] = {
                    'count': len(results_list),
                    'correct': correct,
                    'accuracy_percent': round(accuracy, 2)
                }
        
        return category_accuracy