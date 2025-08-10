"""
AI Classification Accuracy Monitoring System

Builds upon existing AI classification capabilities from Nigerian payment processors
to provide comprehensive monitoring, accuracy tracking, and continuous improvement
for transaction classification and business categorization.

Enhances patterns from:
- taxpoynt_platform/external_integrations/financial_systems/payments/nigerian_processors/*/payment_processor.py
- backend/app/services/firs_monitoring.py
- backend/app/models/nigerian_compliance.py
"""

import asyncio
import logging
from typing import Dict, List, Optional, Any, Union, Tuple, Callable
from datetime import datetime, timedelta
from uuid import UUID, uuid4
from dataclasses import dataclass, field
from enum import Enum
import json
import numpy as np
from sqlalchemy.orm import Session
from sqlalchemy.sql import text, func
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score, confusion_matrix
import joblib
from collections import defaultdict, Counter

# Import existing components
from .production_database_manager import ProductionDatabaseManager
from .cache_manager import CacheManager
from ..transaction_processing.universal_transaction_processor import UniversalTransactionProcessor
from ...external_integrations.financial_systems.payments.nigerian_processors.paystack.payment_processor import PaystackPaymentProcessor
from ...external_integrations.financial_systems.payments.nigerian_processors.moniepoint.payment_processor import MoniepointPaymentProcessor
from ...external_integrations.financial_systems.payments.nigerian_processors.opay.payment_processor import OPayPaymentProcessor
from ...external_integrations.financial_systems.payments.nigerian_processors.palmpay.payment_processor import PalmPayPaymentProcessor
from ...external_integrations.financial_systems.payments.nigerian_processors.interswitch.payment_processor import InterswitchPaymentProcessor

logger = logging.getLogger(__name__)


class ClassificationAccuracy(Enum):
    """AI classification accuracy levels."""
    EXCELLENT = "excellent"  # 95-100% accuracy
    GOOD = "good"          # 85-94% accuracy
    ACCEPTABLE = "acceptable"  # 75-84% accuracy
    POOR = "poor"          # 60-74% accuracy
    CRITICAL = "critical"   # <60% accuracy


class ClassificationType(Enum):
    """Types of AI classification."""
    BUSINESS_CATEGORY = "business_category"
    TRANSACTION_TYPE = "transaction_type"
    MERCHANT_IDENTIFICATION = "merchant_identification"
    RISK_ASSESSMENT = "risk_assessment"
    COMPLIANCE_STATUS = "compliance_status"
    FRAUD_DETECTION = "fraud_detection"
    CUSTOMER_SEGMENTATION = "customer_segmentation"


@dataclass
class ClassificationMetrics:
    """Comprehensive AI classification metrics."""
    classification_type: ClassificationType
    total_predictions: int = 0
    correct_predictions: int = 0
    accuracy_score: float = 0.0
    precision_score: float = 0.0
    recall_score: float = 0.0
    f1_score: float = 0.0
    
    # Confidence metrics
    avg_confidence: float = 0.0
    low_confidence_count: int = 0
    high_confidence_count: int = 0
    
    # Performance metrics
    avg_processing_time_ms: float = 0.0
    model_version: str = "unknown"
    
    # Quality indicators
    accuracy_level: ClassificationAccuracy = ClassificationAccuracy.ACCEPTABLE
    drift_detected: bool = False
    requires_retraining: bool = False
    
    # Temporal metrics
    period_start: datetime = field(default_factory=datetime.utcnow)
    period_end: datetime = field(default_factory=datetime.utcnow)
    last_updated: datetime = field(default_factory=datetime.utcnow)
    
    def calculate_derived_metrics(self):
        """Calculate derived classification metrics."""
        if self.total_predictions > 0:
            self.accuracy_score = (self.correct_predictions / self.total_predictions) * 100
            
            # Determine accuracy level
            if self.accuracy_score >= 95:
                self.accuracy_level = ClassificationAccuracy.EXCELLENT
            elif self.accuracy_score >= 85:
                self.accuracy_level = ClassificationAccuracy.GOOD
            elif self.accuracy_score >= 75:
                self.accuracy_level = ClassificationAccuracy.ACCEPTABLE
            elif self.accuracy_score >= 60:
                self.accuracy_level = ClassificationAccuracy.POOR
            else:
                self.accuracy_level = ClassificationAccuracy.CRITICAL
            
            # Check if retraining is needed
            self.requires_retraining = (
                self.accuracy_score < 80 or 
                self.drift_detected or
                self.low_confidence_count / self.total_predictions > 0.3
            )


@dataclass
class ModelPerformanceReport:
    """Detailed model performance report."""
    model_name: str
    model_version: str
    classification_type: ClassificationType
    processor_name: str
    
    # Accuracy metrics
    overall_accuracy: float
    class_accuracies: Dict[str, float]
    confusion_matrix: List[List[int]]
    
    # Performance trends
    accuracy_trend: List[Dict[str, Any]]  # Daily accuracy over time
    volume_trend: List[Dict[str, Any]]    # Prediction volume over time
    
    # Issues and recommendations
    identified_issues: List[Dict[str, Any]]
    improvement_recommendations: List[str]
    
    # Metadata
    total_samples: int
    evaluation_period: str
    generated_at: datetime = field(default_factory=datetime.utcnow)


class AIClassificationMonitor:
    """
    AI Classification Accuracy Monitoring System.
    
    Monitors and improves AI classification accuracy across all Nigerian
    payment processors and transaction types.
    """
    
    def __init__(
        self,
        db_manager: ProductionDatabaseManager,
        cache_manager: CacheManager,
        universal_processor: UniversalTransactionProcessor
    ):
        """
        Initialize AI classification monitor.
        
        Args:
            db_manager: Production database manager
            cache_manager: Cache manager instance
            universal_processor: Universal transaction processor
        """
        self.db_manager = db_manager
        self.cache_manager = cache_manager
        self.universal_processor = universal_processor
        
        # Payment processors with AI classification
        self.processors = {
            'paystack': PaystackPaymentProcessor(),
            'moniepoint': MoniepointPaymentProcessor(),
            'opay': OPayPaymentProcessor(),
            'palmpay': PalmPayPaymentProcessor(),
            'interswitch': InterswitchPaymentProcessor()
        }
        
        # Classification thresholds
        self.accuracy_thresholds = {
            ClassificationType.BUSINESS_CATEGORY: 85.0,
            ClassificationType.TRANSACTION_TYPE: 90.0,
            ClassificationType.MERCHANT_IDENTIFICATION: 80.0,
            ClassificationType.RISK_ASSESSMENT: 95.0,
            ClassificationType.COMPLIANCE_STATUS: 99.0,
            ClassificationType.FRAUD_DETECTION: 99.5,
            ClassificationType.CUSTOMER_SEGMENTATION: 75.0
        }
        
        # Confidence thresholds
        self.confidence_thresholds = {
            'low_confidence': 0.6,
            'high_confidence': 0.9
        }
        
        # Model performance tracking
        self.performance_history = defaultdict(list)
        self.model_versions = {}
        
        logger.info("AI Classification Monitor initialized")
    
    async def evaluate_classification_accuracy(
        self,
        organization_id: UUID,
        classification_type: ClassificationType,
        processor_name: Optional[str] = None,
        evaluation_period_days: int = 7
    ) -> ClassificationMetrics:
        """
        Evaluate AI classification accuracy for a specific type.
        
        Args:
            organization_id: Organization to evaluate
            classification_type: Type of classification to evaluate
            processor_name: Specific processor to evaluate (optional)
            evaluation_period_days: Period to evaluate over
            
        Returns:
            Classification metrics
        """
        period_end = datetime.utcnow()
        period_start = period_end - timedelta(days=evaluation_period_days)
        
        logger.info(f"Evaluating {classification_type.value} accuracy for org {organization_id} over {evaluation_period_days} days")
        
        # Check cache first
        cache_key = f"classification_metrics:{organization_id}:{classification_type.value}:{processor_name or 'all'}:{evaluation_period_days}"
        cached_metrics = self.cache_manager.get(cache_key)
        
        if cached_metrics:
            return ClassificationMetrics(**cached_metrics)
        
        # Initialize metrics
        metrics = ClassificationMetrics(
            classification_type=classification_type,
            period_start=period_start,
            period_end=period_end
        )
        
        async with self.db_manager.get_session(tenant_id=organization_id) as session:
            # Get classification data based on type
            if classification_type == ClassificationType.BUSINESS_CATEGORY:
                await self._evaluate_business_category_classification(session, organization_id, period_start, period_end, metrics, processor_name)
            
            elif classification_type == ClassificationType.TRANSACTION_TYPE:
                await self._evaluate_transaction_type_classification(session, organization_id, period_start, period_end, metrics, processor_name)
            
            elif classification_type == ClassificationType.MERCHANT_IDENTIFICATION:
                await self._evaluate_merchant_identification(session, organization_id, period_start, period_end, metrics, processor_name)
            
            elif classification_type == ClassificationType.RISK_ASSESSMENT:
                await self._evaluate_risk_assessment(session, organization_id, period_start, period_end, metrics, processor_name)
            
            elif classification_type == ClassificationType.FRAUD_DETECTION:
                await self._evaluate_fraud_detection(session, organization_id, period_start, period_end, metrics, processor_name)
            
            else:
                logger.warning(f"Classification type {classification_type.value} not implemented yet")
        
        # Calculate derived metrics
        metrics.calculate_derived_metrics()
        
        # Check for model drift
        await self._detect_model_drift(metrics, classification_type, processor_name)
        
        # Cache results
        self.cache_manager.set(cache_key, metrics.__dict__, ttl=1800)  # Cache for 30 minutes
        
        logger.info(f"Classification accuracy evaluation completed: {metrics.accuracy_score:.2f}% accuracy")
        
        return metrics
    
    async def _evaluate_business_category_classification(
        self,
        session: Session,
        organization_id: UUID,
        start_date: datetime,
        end_date: datetime,
        metrics: ClassificationMetrics,
        processor_name: Optional[str] = None
    ):
        """Evaluate business category classification accuracy."""
        # Query for transactions with both AI predictions and manual validations
        query = text("""
            SELECT 
                upt.transaction_id,
                upt.ai_business_category,
                upt.ai_category_confidence,
                upt.manual_business_category,
                upt.processing_time_ms,
                upt.connector_type
            FROM universal_processed_transactions upt
            WHERE upt.organization_id = :org_id
            AND upt.transaction_timestamp BETWEEN :start_date AND :end_date
            AND upt.ai_business_category IS NOT NULL
            AND upt.manual_business_category IS NOT NULL
            AND (:processor_name IS NULL OR upt.connector_type = :processor_name)
        """)
        
        result = await session.execute(query, {
            'org_id': str(organization_id),
            'start_date': start_date,
            'end_date': end_date,
            'processor_name': processor_name
        })
        
        total_predictions = 0
        correct_predictions = 0
        confidence_sum = 0.0
        processing_time_sum = 0.0
        low_confidence_count = 0
        high_confidence_count = 0
        
        for row in result:
            total_predictions += 1
            
            # Check if AI prediction matches manual validation
            if row.ai_business_category == row.manual_business_category:
                correct_predictions += 1
            
            # Track confidence metrics
            confidence = float(row.ai_category_confidence or 0.0)
            confidence_sum += confidence
            
            if confidence < self.confidence_thresholds['low_confidence']:
                low_confidence_count += 1
            elif confidence >= self.confidence_thresholds['high_confidence']:
                high_confidence_count += 1
            
            # Track processing time
            processing_time_sum += float(row.processing_time_ms or 0.0)
        
        # Update metrics
        metrics.total_predictions = total_predictions
        metrics.correct_predictions = correct_predictions
        metrics.avg_confidence = confidence_sum / total_predictions if total_predictions > 0 else 0.0
        metrics.low_confidence_count = low_confidence_count
        metrics.high_confidence_count = high_confidence_count
        metrics.avg_processing_time_ms = processing_time_sum / total_predictions if total_predictions > 0 else 0.0
    
    async def _evaluate_transaction_type_classification(
        self,
        session: Session,
        organization_id: UUID,
        start_date: datetime,
        end_date: datetime,
        metrics: ClassificationMetrics,
        processor_name: Optional[str] = None
    ):
        """Evaluate transaction type classification accuracy."""
        query = text("""
            SELECT 
                upt.transaction_id,
                upt.ai_transaction_type,
                upt.ai_type_confidence,
                upt.actual_transaction_type,
                upt.processing_time_ms
            FROM universal_processed_transactions upt
            WHERE upt.organization_id = :org_id
            AND upt.transaction_timestamp BETWEEN :start_date AND :end_date
            AND upt.ai_transaction_type IS NOT NULL
            AND upt.actual_transaction_type IS NOT NULL
            AND (:processor_name IS NULL OR upt.connector_type = :processor_name)
        """)
        
        result = await session.execute(query, {
            'org_id': str(organization_id),
            'start_date': start_date,
            'end_date': end_date,
            'processor_name': processor_name
        })
        
        total_predictions = 0
        correct_predictions = 0
        confidence_sum = 0.0
        
        for row in result:
            total_predictions += 1
            
            if row.ai_transaction_type == row.actual_transaction_type:
                correct_predictions += 1
            
            confidence_sum += float(row.ai_type_confidence or 0.0)
        
        metrics.total_predictions = total_predictions
        metrics.correct_predictions = correct_predictions
        metrics.avg_confidence = confidence_sum / total_predictions if total_predictions > 0 else 0.0
    
    async def _evaluate_merchant_identification(
        self,
        session: Session,
        organization_id: UUID,
        start_date: datetime,
        end_date: datetime,
        metrics: ClassificationMetrics,
        processor_name: Optional[str] = None
    ):
        """Evaluate merchant identification accuracy."""
        query = text("""
            SELECT 
                upt.transaction_id,
                upt.ai_merchant_name,
                upt.ai_merchant_confidence,
                upt.verified_merchant_name,
                upt.processing_time_ms
            FROM universal_processed_transactions upt
            WHERE upt.organization_id = :org_id
            AND upt.transaction_timestamp BETWEEN :start_date AND :end_date
            AND upt.ai_merchant_name IS NOT NULL
            AND upt.verified_merchant_name IS NOT NULL
            AND (:processor_name IS NULL OR upt.connector_type = :processor_name)
        """)
        
        result = await session.execute(query, {
            'org_id': str(organization_id),
            'start_date': start_date,
            'end_date': end_date,
            'processor_name': processor_name
        })
        
        total_predictions = 0
        correct_predictions = 0
        confidence_sum = 0.0
        
        for row in result:
            total_predictions += 1
            
            # Use fuzzy matching for merchant names
            ai_merchant = (row.ai_merchant_name or "").lower().strip()
            verified_merchant = (row.verified_merchant_name or "").lower().strip()
            
            # Consider it correct if there's significant overlap
            if ai_merchant in verified_merchant or verified_merchant in ai_merchant:
                correct_predictions += 1
            elif self._calculate_string_similarity(ai_merchant, verified_merchant) > 0.8:
                correct_predictions += 1
        
        metrics.total_predictions = total_predictions
        metrics.correct_predictions = correct_predictions
        metrics.avg_confidence = confidence_sum / total_predictions if total_predictions > 0 else 0.0
    
    async def _evaluate_risk_assessment(
        self,
        session: Session,
        organization_id: UUID,
        start_date: datetime,
        end_date: datetime,
        metrics: ClassificationMetrics,
        processor_name: Optional[str] = None
    ):
        """Evaluate risk assessment accuracy."""
        query = text("""
            SELECT 
                upt.transaction_id,
                upt.ai_risk_score,
                upt.ai_risk_level,
                upt.actual_risk_level,
                upt.is_fraudulent
            FROM universal_processed_transactions upt
            WHERE upt.organization_id = :org_id
            AND upt.transaction_timestamp BETWEEN :start_date AND :end_date
            AND upt.ai_risk_level IS NOT NULL
            AND (upt.actual_risk_level IS NOT NULL OR upt.is_fraudulent IS NOT NULL)
            AND (:processor_name IS NULL OR upt.connector_type = :processor_name)
        """)
        
        result = await session.execute(query, {
            'org_id': str(organization_id),
            'start_date': start_date,
            'end_date': end_date,
            'processor_name': processor_name
        })
        
        total_predictions = 0
        correct_predictions = 0
        
        for row in result:
            total_predictions += 1
            
            # Compare AI risk level with actual outcome
            ai_risk = row.ai_risk_level
            is_fraudulent = row.is_fraudulent
            actual_risk = row.actual_risk_level
            
            # If we know it's fraudulent, high risk should have been predicted
            if is_fraudulent is not None:
                if (is_fraudulent and ai_risk in ['high', 'critical']) or (not is_fraudulent and ai_risk in ['low', 'medium']):
                    correct_predictions += 1
            elif actual_risk is not None and ai_risk == actual_risk:
                correct_predictions += 1
        
        metrics.total_predictions = total_predictions
        metrics.correct_predictions = correct_predictions
    
    async def _evaluate_fraud_detection(
        self,
        session: Session,
        organization_id: UUID,
        start_date: datetime,
        end_date: datetime,
        metrics: ClassificationMetrics,
        processor_name: Optional[str] = None
    ):
        """Evaluate fraud detection accuracy."""
        query = text("""
            SELECT 
                upt.transaction_id,
                upt.ai_fraud_probability,
                upt.ai_fraud_prediction,
                upt.is_fraudulent,
                upt.fraud_confirmed_at
            FROM universal_processed_transactions upt
            WHERE upt.organization_id = :org_id
            AND upt.transaction_timestamp BETWEEN :start_date AND :end_date
            AND upt.ai_fraud_prediction IS NOT NULL
            AND upt.is_fraudulent IS NOT NULL
            AND (:processor_name IS NULL OR upt.connector_type = :processor_name)
        """)
        
        result = await session.execute(query, {
            'org_id': str(organization_id),
            'start_date': start_date,
            'end_date': end_date,
            'processor_name': processor_name
        })
        
        y_true = []
        y_pred = []
        
        for row in result:
            y_true.append(1 if row.is_fraudulent else 0)
            y_pred.append(1 if row.ai_fraud_prediction else 0)
        
        if len(y_true) > 0:
            # Calculate comprehensive fraud detection metrics
            accuracy = accuracy_score(y_true, y_pred) * 100
            precision = precision_score(y_true, y_pred, zero_division=0) * 100
            recall = recall_score(y_true, y_pred, zero_division=0) * 100
            f1 = f1_score(y_true, y_pred, zero_division=0) * 100
            
            metrics.total_predictions = len(y_true)
            metrics.correct_predictions = int(accuracy * len(y_true) / 100)
            metrics.accuracy_score = accuracy
            metrics.precision_score = precision
            metrics.recall_score = recall
            metrics.f1_score = f1
    
    def _calculate_string_similarity(self, str1: str, str2: str) -> float:
        """Calculate string similarity using Levenshtein distance."""
        if not str1 or not str2:
            return 0.0
        
        # Simple implementation of Levenshtein distance
        len1, len2 = len(str1), len(str2)
        if len1 == 0:
            return 0.0 if len2 > 0 else 1.0
        if len2 == 0:
            return 0.0
        
        # Create matrix
        matrix = [[0] * (len2 + 1) for _ in range(len1 + 1)]
        
        # Initialize first row and column
        for i in range(len1 + 1):
            matrix[i][0] = i
        for j in range(len2 + 1):
            matrix[0][j] = j
        
        # Fill matrix
        for i in range(1, len1 + 1):
            for j in range(1, len2 + 1):
                cost = 0 if str1[i-1] == str2[j-1] else 1
                matrix[i][j] = min(
                    matrix[i-1][j] + 1,      # deletion
                    matrix[i][j-1] + 1,      # insertion
                    matrix[i-1][j-1] + cost  # substitution
                )
        
        # Calculate similarity
        max_len = max(len1, len2)
        distance = matrix[len1][len2]
        similarity = (max_len - distance) / max_len
        
        return similarity
    
    async def _detect_model_drift(
        self,
        metrics: ClassificationMetrics,
        classification_type: ClassificationType,
        processor_name: Optional[str] = None
    ):
        """Detect model drift by comparing with historical performance."""
        # Get historical performance
        history_key = f"{classification_type.value}_{processor_name or 'all'}"
        historical_accuracies = self.performance_history.get(history_key, [])
        
        # Add current accuracy to history
        historical_accuracies.append({
            'accuracy': metrics.accuracy_score,
            'timestamp': datetime.utcnow(),
            'total_predictions': metrics.total_predictions
        })
        
        # Keep only recent history (last 30 data points)
        if len(historical_accuracies) > 30:
            historical_accuracies = historical_accuracies[-30:]
        
        self.performance_history[history_key] = historical_accuracies
        
        # Detect drift if we have enough history
        if len(historical_accuracies) >= 10:
            recent_accuracies = [h['accuracy'] for h in historical_accuracies[-5:]]
            older_accuracies = [h['accuracy'] for h in historical_accuracies[-10:-5]]
            
            recent_avg = np.mean(recent_accuracies)
            older_avg = np.mean(older_accuracies)
            
            # Detect significant degradation
            degradation_threshold = 5.0  # 5% degradation
            if older_avg - recent_avg > degradation_threshold:
                metrics.drift_detected = True
                logger.warning(f"Model drift detected for {classification_type.value}: {older_avg:.2f}% -> {recent_avg:.2f}%")
    
    async def generate_model_performance_report(
        self,
        organization_id: UUID,
        processor_name: str,
        evaluation_days: int = 30
    ) -> ModelPerformanceReport:
        """
        Generate comprehensive model performance report.
        
        Args:
            organization_id: Organization ID
            processor_name: Payment processor name
            evaluation_days: Days to evaluate over
            
        Returns:
            Detailed model performance report
        """
        logger.info(f"Generating model performance report for {processor_name} over {evaluation_days} days")
        
        # Evaluate all classification types
        classification_metrics = {}
        for classification_type in ClassificationType:
            metrics = await self.evaluate_classification_accuracy(
                organization_id=organization_id,
                classification_type=classification_type,
                processor_name=processor_name,
                evaluation_period_days=evaluation_days
            )
            classification_metrics[classification_type] = metrics
        
        # Calculate overall accuracy
        total_predictions = sum(m.total_predictions for m in classification_metrics.values())
        total_correct = sum(m.correct_predictions for m in classification_metrics.values())
        overall_accuracy = (total_correct / total_predictions * 100) if total_predictions > 0 else 0.0
        
        # Get class-specific accuracies
        class_accuracies = {
            ct.value: metrics.accuracy_score
            for ct, metrics in classification_metrics.items()
            if metrics.total_predictions > 0
        }
        
        # Generate accuracy trends
        accuracy_trend = await self._get_accuracy_trends(organization_id, processor_name, evaluation_days)
        volume_trend = await self._get_volume_trends(organization_id, processor_name, evaluation_days)
        
        # Identify issues and recommendations
        issues = self._identify_performance_issues(classification_metrics)
        recommendations = self._generate_improvement_recommendations(classification_metrics, issues)
        
        return ModelPerformanceReport(
            model_name=f"{processor_name}_classifier",
            model_version=self.model_versions.get(processor_name, "1.0.0"),
            classification_type=ClassificationType.BUSINESS_CATEGORY,  # Primary type
            processor_name=processor_name,
            overall_accuracy=overall_accuracy,
            class_accuracies=class_accuracies,
            confusion_matrix=[],  # Would be populated with actual confusion matrix
            accuracy_trend=accuracy_trend,
            volume_trend=volume_trend,
            identified_issues=issues,
            improvement_recommendations=recommendations,
            total_samples=total_predictions,
            evaluation_period=f"{evaluation_days}_days"
        )
    
    async def _get_accuracy_trends(
        self,
        organization_id: UUID,
        processor_name: str,
        days: int
    ) -> List[Dict[str, Any]]:
        """Get accuracy trends over specified period."""
        trends = []
        
        for i in range(days):
            day_start = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0) - timedelta(days=i)
            day_end = day_start + timedelta(days=1)
            
            # Get daily accuracy for business category classification
            daily_metrics = await self.evaluate_classification_accuracy(
                organization_id=organization_id,
                classification_type=ClassificationType.BUSINESS_CATEGORY,
                processor_name=processor_name,
                evaluation_period_days=1
            )
            
            trends.append({
                "date": day_start.date().isoformat(),
                "accuracy": daily_metrics.accuracy_score,
                "total_predictions": daily_metrics.total_predictions,
                "confidence": daily_metrics.avg_confidence
            })
        
        # Reverse to get chronological order
        trends.reverse()
        return trends
    
    async def _get_volume_trends(
        self,
        organization_id: UUID,
        processor_name: str,
        days: int
    ) -> List[Dict[str, Any]]:
        """Get prediction volume trends."""
        trends = []
        
        async with self.db_manager.get_session(tenant_id=organization_id) as session:
            for i in range(days):
                day_start = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0) - timedelta(days=i)
                day_end = day_start + timedelta(days=1)
                
                volume_query = text("""
                    SELECT COUNT(*) as prediction_count
                    FROM universal_processed_transactions upt
                    WHERE upt.organization_id = :org_id
                    AND upt.connector_type = :processor_name
                    AND upt.transaction_timestamp BETWEEN :start_date AND :end_date
                    AND upt.ai_business_category IS NOT NULL
                """)
                
                result = await session.execute(volume_query, {
                    'org_id': str(organization_id),
                    'processor_name': processor_name,
                    'start_date': day_start,
                    'end_date': day_end
                })
                
                volume = result.scalar() or 0
                
                trends.append({
                    "date": day_start.date().isoformat(),
                    "volume": volume
                })
        
        trends.reverse()
        return trends
    
    def _identify_performance_issues(
        self,
        classification_metrics: Dict[ClassificationType, ClassificationMetrics]
    ) -> List[Dict[str, Any]]:
        """Identify performance issues from classification metrics."""
        issues = []
        
        for classification_type, metrics in classification_metrics.items():
            threshold = self.accuracy_thresholds.get(classification_type, 80.0)
            
            if metrics.accuracy_score < threshold:
                issues.append({
                    "type": "low_accuracy",
                    "classification_type": classification_type.value,
                    "severity": "critical" if metrics.accuracy_score < threshold - 10 else "high",
                    "current_accuracy": metrics.accuracy_score,
                    "required_accuracy": threshold,
                    "description": f"{classification_type.value} accuracy of {metrics.accuracy_score:.1f}% is below threshold"
                })
            
            if metrics.low_confidence_count / max(1, metrics.total_predictions) > 0.3:
                issues.append({
                    "type": "high_uncertainty",
                    "classification_type": classification_type.value,
                    "severity": "medium",
                    "low_confidence_ratio": metrics.low_confidence_count / metrics.total_predictions,
                    "description": f"High proportion of low-confidence predictions for {classification_type.value}"
                })
            
            if metrics.drift_detected:
                issues.append({
                    "type": "model_drift",
                    "classification_type": classification_type.value,
                    "severity": "high",
                    "description": f"Model drift detected for {classification_type.value} classification"
                })
        
        return issues
    
    def _generate_improvement_recommendations(
        self,
        classification_metrics: Dict[ClassificationType, ClassificationMetrics],
        issues: List[Dict[str, Any]]
    ) -> List[str]:
        """Generate improvement recommendations based on performance analysis."""
        recommendations = []
        
        # General recommendations based on issues
        critical_issues = [i for i in issues if i.get('severity') == 'critical']
        if critical_issues:
            recommendations.append("Immediate model retraining required for critical accuracy issues")
        
        high_issues = [i for i in issues if i.get('severity') == 'high']
        if high_issues:
            recommendations.append("Schedule model retraining to address performance degradation")
        
        # Specific recommendations based on classification types
        for classification_type, metrics in classification_metrics.items():
            if metrics.requires_retraining:
                recommendations.append(f"Retrain {classification_type.value} classification model with recent data")
            
            if metrics.avg_confidence < 0.7:
                recommendations.append(f"Improve feature engineering for {classification_type.value} classification")
        
        # Data quality recommendations
        low_volume_types = [
            ct.value for ct, metrics in classification_metrics.items()
            if metrics.total_predictions < 100
        ]
        
        if low_volume_types:
            recommendations.append(f"Increase training data volume for: {', '.join(low_volume_types)}")
        
        # Performance optimization recommendations
        slow_processing = [
            ct.value for ct, metrics in classification_metrics.items()
            if metrics.avg_processing_time_ms > 1000
        ]
        
        if slow_processing:
            recommendations.append(f"Optimize processing speed for: {', '.join(slow_processing)}")
        
        return recommendations
    
    async def trigger_model_retraining(
        self,
        organization_id: UUID,
        classification_type: ClassificationType,
        processor_name: str
    ) -> Dict[str, Any]:
        """
        Trigger model retraining for improved accuracy.
        
        Args:
            organization_id: Organization ID
            classification_type: Classification type to retrain
            processor_name: Processor name
            
        Returns:
            Retraining job information
        """
        logger.info(f"Triggering model retraining for {classification_type.value} on {processor_name}")
        
        # This would integrate with your ML pipeline
        # For now, we'll simulate the retraining process
        
        retraining_job = {
            "job_id": str(uuid4()),
            "organization_id": str(organization_id),
            "classification_type": classification_type.value,
            "processor_name": processor_name,
            "status": "queued",
            "created_at": datetime.utcnow().isoformat(),
            "estimated_completion": (datetime.utcnow() + timedelta(hours=2)).isoformat()
        }
        
        # Cache the job info
        job_cache_key = f"retraining_job:{retraining_job['job_id']}"
        self.cache_manager.set(job_cache_key, retraining_job, ttl=86400)  # Cache for 24 hours
        
        # In a real implementation, this would:
        # 1. Extract training data from the database
        # 2. Submit to ML training pipeline
        # 3. Monitor training progress
        # 4. Deploy updated model when ready
        # 5. Update model version tracking
        
        return retraining_job
    
    async def get_monitoring_dashboard_data(
        self,
        organization_id: UUID
    ) -> Dict[str, Any]:
        """
        Get comprehensive AI monitoring dashboard data.
        
        Args:
            organization_id: Organization ID
            
        Returns:
            Dashboard data dictionary
        """
        dashboard_data = {
            "overview": {},
            "processor_performance": {},
            "classification_accuracy": {},
            "alerts": [],
            "recommendations": []
        }
        
        # Overall metrics across all processors
        overall_metrics = []
        
        for processor_name in self.processors.keys():
            # Generate performance report for each processor
            report = await self.generate_model_performance_report(
                organization_id=organization_id,
                processor_name=processor_name,
                evaluation_days=7
            )
            
            dashboard_data["processor_performance"][processor_name] = {
                "overall_accuracy": report.overall_accuracy,
                "total_samples": report.total_samples,
                "issues_count": len(report.identified_issues),
                "last_evaluation": report.generated_at.isoformat()
            }
            
            overall_metrics.append(report.overall_accuracy)
            
            # Collect alerts from issues
            for issue in report.identified_issues:
                if issue.get('severity') in ['critical', 'high']:
                    dashboard_data["alerts"].append({
                        "processor": processor_name,
                        "type": issue['type'],
                        "severity": issue['severity'],
                        "description": issue['description']
                    })
            
            # Collect recommendations
            dashboard_data["recommendations"].extend([
                f"{processor_name}: {rec}" for rec in report.improvement_recommendations
            ])
        
        # Calculate overview metrics
        if overall_metrics:
            dashboard_data["overview"] = {
                "average_accuracy": np.mean(overall_metrics),
                "best_performer": max(self.processors.keys(), key=lambda p: dashboard_data["processor_performance"][p]["overall_accuracy"]),
                "total_processors": len(self.processors),
                "active_alerts": len(dashboard_data["alerts"])
            }
        
        # Get classification-specific accuracy
        for classification_type in ClassificationType:
            metrics = await self.evaluate_classification_accuracy(
                organization_id=organization_id,
                classification_type=classification_type,
                evaluation_period_days=7
            )
            
            dashboard_data["classification_accuracy"][classification_type.value] = {
                "accuracy": metrics.accuracy_score,
                "total_predictions": metrics.total_predictions,
                "confidence": metrics.avg_confidence,
                "requires_retraining": metrics.requires_retraining
            }
        
        return dashboard_data
    
    def get_performance_statistics(self) -> Dict[str, Any]:
        """Get AI monitoring performance statistics."""
        return {
            "monitored_processors": len(self.processors),
            "classification_types": len(ClassificationType),
            "accuracy_thresholds": {
                ct.value: threshold for ct, threshold in self.accuracy_thresholds.items()
            },
            "confidence_thresholds": self.confidence_thresholds,
            "performance_history_size": {
                key: len(history) for key, history in self.performance_history.items()
            },
            "model_versions": self.model_versions
        }


# Factory function
def create_ai_classification_monitor(
    db_manager: ProductionDatabaseManager,
    cache_manager: CacheManager,
    universal_processor: UniversalTransactionProcessor
) -> AIClassificationMonitor:
    """
    Create AI classification monitor instance.
    
    Args:
        db_manager: Production database manager
        cache_manager: Cache manager
        universal_processor: Universal transaction processor
        
    Returns:
        Configured AIClassificationMonitor instance
    """
    return AIClassificationMonitor(
        db_manager=db_manager,
        cache_manager=cache_manager,
        universal_processor=universal_processor
    )
