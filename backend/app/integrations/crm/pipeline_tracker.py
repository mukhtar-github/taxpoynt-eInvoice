"""
Pipeline Stage Tracking for Predictive Invoicing.

This module provides sophisticated pipeline stage tracking and predictive analytics
for CRM deals, enabling proactive invoice generation and revenue forecasting.
"""

import logging
import json
from typing import Dict, Any, List, Optional, Tuple, Union
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from dataclasses import dataclass, field
from enum import Enum
import statistics
import asyncio
from collections import defaultdict, deque

logger = logging.getLogger(__name__)


class StageType(str, Enum):
    """Pipeline stage types."""
    LEAD = "lead"
    QUALIFIED = "qualified"
    PROPOSAL = "proposal"
    NEGOTIATION = "negotiation"
    CLOSED_WON = "closed_won"
    CLOSED_LOST = "closed_lost"
    ON_HOLD = "on_hold"
    CUSTOM = "custom"


class PredictionModel(str, Enum):
    """Prediction model types."""
    HISTORICAL_AVERAGE = "historical_average"
    WEIGHTED_PIPELINE = "weighted_pipeline"
    VELOCITY_BASED = "velocity_based"
    MACHINE_LEARNING = "machine_learning"
    HYBRID = "hybrid"


class TriggerCondition(str, Enum):
    """Invoice generation trigger conditions."""
    STAGE_CHANGE = "stage_change"
    PROBABILITY_THRESHOLD = "probability_threshold"
    DATE_BASED = "date_based"
    AMOUNT_THRESHOLD = "amount_threshold"
    CUSTOM_RULE = "custom_rule"
    PREDICTIVE = "predictive"


@dataclass
class StageDefinition:
    """Definition of a pipeline stage."""
    stage_id: str
    stage_name: str
    stage_type: StageType
    probability: Decimal
    sequence_order: int
    is_closed: bool = False
    is_won: bool = False
    generate_invoice: bool = False
    auto_actions: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class StageTransition:
    """Represents a stage transition event."""
    deal_id: str
    from_stage: str
    to_stage: str
    transition_date: datetime
    duration_in_stage: timedelta
    deal_amount: Decimal
    probability_change: Decimal
    trigger_source: str
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class PipelineMetrics:
    """Pipeline performance metrics."""
    total_deals: int
    total_value: Decimal
    average_deal_size: Decimal
    conversion_rate: Decimal
    average_cycle_time: timedelta
    stage_conversion_rates: Dict[str, Decimal]
    velocity_metrics: Dict[str, Decimal]
    forecasted_revenue: Decimal
    confidence_score: Decimal


@dataclass
class PredictiveInsight:
    """Predictive insight for deal progression."""
    deal_id: str
    current_stage: str
    predicted_next_stage: str
    probability_of_transition: Decimal
    predicted_transition_date: datetime
    predicted_close_date: datetime
    win_probability: Decimal
    forecasted_amount: Decimal
    confidence_level: str
    recommendation: str
    factors: List[str]


class PipelineTracker:
    """Advanced pipeline stage tracking and predictive analytics."""
    
    def __init__(self, platform: str):
        """
        Initialize pipeline tracker.
        
        Args:
            platform: CRM platform name (hubspot, salesforce, etc.)
        """
        self.platform = platform
        self.stage_definitions: Dict[str, StageDefinition] = {}
        self.stage_history: deque = deque(maxlen=10000)  # Store recent transitions
        self.deal_stages: Dict[str, str] = {}  # Current stage for each deal
        self.pipeline_metrics: Optional[PipelineMetrics] = None
        self.prediction_model = PredictionModel.HYBRID
        
        # Load default stage definitions
        self._load_default_stages()
        
        # Analytics cache
        self._metrics_cache = {}
        self._cache_ttl = timedelta(hours=1)
        self._last_cache_update = None
    
    def _load_default_stages(self):
        """Load default stage definitions for the platform."""
        if self.platform.lower() == "hubspot":
            default_stages = [
                StageDefinition("appointmentscheduled", "Appointment Scheduled", StageType.QUALIFIED, Decimal("20"), 1),
                StageDefinition("qualifiedtobuy", "Qualified to Buy", StageType.QUALIFIED, Decimal("40"), 2),
                StageDefinition("presentationscheduled", "Presentation Scheduled", StageType.PROPOSAL, Decimal("60"), 3),
                StageDefinition("decisionmakerboughtin", "Decision Maker Bought In", StageType.NEGOTIATION, Decimal("80"), 4),
                StageDefinition("contractsent", "Contract Sent", StageType.NEGOTIATION, Decimal("90"), 5),
                StageDefinition("closedwon", "Closed Won", StageType.CLOSED_WON, Decimal("100"), 6, 
                               is_closed=True, is_won=True, generate_invoice=True),
                StageDefinition("closedlost", "Closed Lost", StageType.CLOSED_LOST, Decimal("0"), 7, 
                               is_closed=True, is_won=False)
            ]
        
        elif self.platform.lower() == "salesforce":
            default_stages = [
                StageDefinition("prospecting", "Prospecting", StageType.LEAD, Decimal("10"), 1),
                StageDefinition("qualification", "Qualification", StageType.QUALIFIED, Decimal("25"), 2),
                StageDefinition("needs_analysis", "Needs Analysis", StageType.QUALIFIED, Decimal("50"), 3),
                StageDefinition("value_proposition", "Value Proposition", StageType.PROPOSAL, Decimal("65"), 4),
                StageDefinition("id_decision_makers", "Id. Decision Makers", StageType.PROPOSAL, Decimal("75"), 5),
                StageDefinition("proposal_price_quote", "Proposal/Price Quote", StageType.NEGOTIATION, Decimal("85"), 6),
                StageDefinition("negotiation_review", "Negotiation/Review", StageType.NEGOTIATION, Decimal("95"), 7),
                StageDefinition("closed_won", "Closed Won", StageType.CLOSED_WON, Decimal("100"), 8,
                               is_closed=True, is_won=True, generate_invoice=True),
                StageDefinition("closed_lost", "Closed Lost", StageType.CLOSED_LOST, Decimal("0"), 9,
                               is_closed=True, is_won=False)
            ]
        
        else:
            # Generic default stages
            default_stages = [
                StageDefinition("lead", "Lead", StageType.LEAD, Decimal("10"), 1),
                StageDefinition("qualified", "Qualified", StageType.QUALIFIED, Decimal("30"), 2),
                StageDefinition("proposal", "Proposal", StageType.PROPOSAL, Decimal("60"), 3),
                StageDefinition("negotiation", "Negotiation", StageType.NEGOTIATION, Decimal("80"), 4),
                StageDefinition("closed_won", "Closed Won", StageType.CLOSED_WON, Decimal("100"), 5,
                               is_closed=True, is_won=True, generate_invoice=True),
                StageDefinition("closed_lost", "Closed Lost", StageType.CLOSED_LOST, Decimal("0"), 6,
                               is_closed=True, is_won=False)
            ]
        
        for stage in default_stages:
            self.stage_definitions[stage.stage_id] = stage
    
    def register_stage_definition(self, stage: StageDefinition):
        """Register a custom stage definition."""
        self.stage_definitions[stage.stage_id] = stage
        logger.info(f"Registered stage definition: {stage.stage_id}")
    
    def track_stage_change(
        self,
        deal_id: str,
        from_stage: str,
        to_stage: str,
        deal_amount: Optional[Decimal] = None,
        metadata: Optional[Dict[str, Any]] = None
    ):
        """
        Track a stage change event.
        
        Args:
            deal_id: Deal identifier
            from_stage: Previous stage
            to_stage: New stage
            deal_amount: Deal amount
            metadata: Additional metadata
        """
        if metadata is None:
            metadata = {}
        
        # Calculate duration in previous stage
        duration_in_stage = timedelta(0)
        if deal_id in self.deal_stages:
            # Find the last transition to from_stage
            for transition in reversed(self.stage_history):
                if transition.deal_id == deal_id and transition.to_stage == from_stage:
                    duration_in_stage = datetime.now(timezone.utc) - transition.transition_date
                    break
        
        # Calculate probability change
        from_prob = self.stage_definitions.get(from_stage, StageDefinition("", "", StageType.CUSTOM, Decimal("0"), 0)).probability
        to_prob = self.stage_definitions.get(to_stage, StageDefinition("", "", StageType.CUSTOM, Decimal("0"), 0)).probability
        probability_change = to_prob - from_prob
        
        # Create transition record
        transition = StageTransition(
            deal_id=deal_id,
            from_stage=from_stage,
            to_stage=to_stage,
            transition_date=datetime.now(timezone.utc),
            duration_in_stage=duration_in_stage,
            deal_amount=deal_amount or Decimal("0"),
            probability_change=probability_change,
            trigger_source=metadata.get("trigger_source", "manual"),
            metadata=metadata
        )
        
        # Store transition
        self.stage_history.append(transition)
        self.deal_stages[deal_id] = to_stage
        
        # Clear metrics cache
        self._metrics_cache.clear()
        
        logger.info(f"Tracked stage change: {deal_id} from {from_stage} to {to_stage}")
        
        # Check for invoice generation triggers
        self._check_invoice_triggers(deal_id, to_stage, deal_amount, metadata)
    
    def _check_invoice_triggers(
        self,
        deal_id: str,
        stage: str,
        deal_amount: Optional[Decimal],
        metadata: Dict[str, Any]
    ):
        """Check if stage change should trigger invoice generation."""
        stage_def = self.stage_definitions.get(stage)
        if not stage_def:
            return
        
        triggers = []
        
        # Stage-based trigger
        if stage_def.generate_invoice:
            triggers.append({
                "type": TriggerCondition.STAGE_CHANGE,
                "reason": f"Deal reached invoice-generating stage: {stage_def.stage_name}",
                "confidence": "high"
            })
        
        # Probability threshold trigger
        if stage_def.probability >= Decimal("90"):
            triggers.append({
                "type": TriggerCondition.PROBABILITY_THRESHOLD,
                "reason": f"Deal probability reached {stage_def.probability}%",
                "confidence": "medium"
            })
        
        # Amount threshold trigger
        if deal_amount and deal_amount >= Decimal("50000"):  # Configurable threshold
            triggers.append({
                "type": TriggerCondition.AMOUNT_THRESHOLD,
                "reason": f"Deal amount (${deal_amount}) exceeds threshold",
                "confidence": "medium"
            })
        
        if triggers:
            logger.info(f"Invoice generation triggered for deal {deal_id}: {len(triggers)} triggers")
            metadata["invoice_triggers"] = triggers
    
    def get_current_stage(self, deal_id: str) -> Optional[str]:
        """Get current stage for a deal."""
        return self.deal_stages.get(deal_id)
    
    def get_stage_history(self, deal_id: str) -> List[StageTransition]:
        """Get stage history for a specific deal."""
        return [t for t in self.stage_history if t.deal_id == deal_id]
    
    def calculate_pipeline_metrics(self, days_back: int = 90) -> PipelineMetrics:
        """Calculate comprehensive pipeline metrics."""
        cutoff_date = datetime.now(timezone.utc) - timedelta(days=days_back)
        
        # Get recent transitions
        recent_transitions = [t for t in self.stage_history if t.transition_date >= cutoff_date]
        
        if not recent_transitions:
            return PipelineMetrics(
                total_deals=0,
                total_value=Decimal("0"),
                average_deal_size=Decimal("0"),
                conversion_rate=Decimal("0"),
                average_cycle_time=timedelta(0),
                stage_conversion_rates={},
                velocity_metrics={},
                forecasted_revenue=Decimal("0"),
                confidence_score=Decimal("0")
            )
        
        # Basic metrics
        deal_ids = set(t.deal_id for t in recent_transitions)
        total_deals = len(deal_ids)
        total_value = sum(t.deal_amount for t in recent_transitions)
        average_deal_size = total_value / total_deals if total_deals > 0 else Decimal("0")
        
        # Conversion rates by stage
        stage_conversions = defaultdict(list)
        for transition in recent_transitions:
            stage_conversions[transition.from_stage].append(transition.to_stage)
        
        stage_conversion_rates = {}
        for from_stage, to_stages in stage_conversions.items():
            won_transitions = sum(1 for stage in to_stages if self._is_won_stage(stage))
            stage_conversion_rates[from_stage] = Decimal(won_transitions) / len(to_stages) * 100
        
        # Calculate velocity metrics
        velocity_metrics = self._calculate_velocity_metrics(recent_transitions)
        
        # Calculate forecasted revenue
        forecasted_revenue = self._calculate_forecasted_revenue()
        
        # Overall conversion rate
        won_deals = sum(1 for deal_id in deal_ids if self._is_deal_won(deal_id))
        conversion_rate = Decimal(won_deals) / total_deals * 100 if total_deals > 0 else Decimal("0")
        
        # Average cycle time
        cycle_times = self._calculate_cycle_times(deal_ids)
        average_cycle_time = timedelta(seconds=statistics.mean(cycle_times)) if cycle_times else timedelta(0)
        
        # Confidence score based on data quality and volume
        confidence_score = min(Decimal("100"), Decimal(len(recent_transitions)) / 10)
        
        metrics = PipelineMetrics(
            total_deals=total_deals,
            total_value=total_value,
            average_deal_size=average_deal_size,
            conversion_rate=conversion_rate,
            average_cycle_time=average_cycle_time,
            stage_conversion_rates=stage_conversion_rates,
            velocity_metrics=velocity_metrics,
            forecasted_revenue=forecasted_revenue,
            confidence_score=confidence_score
        )
        
        self.pipeline_metrics = metrics
        return metrics
    
    def _calculate_velocity_metrics(self, transitions: List[StageTransition]) -> Dict[str, Decimal]:
        """Calculate velocity metrics for each stage."""
        velocity_metrics = {}
        
        stage_durations = defaultdict(list)
        for transition in transitions:
            if transition.duration_in_stage.total_seconds() > 0:
                stage_durations[transition.from_stage].append(transition.duration_in_stage.total_seconds())
        
        for stage, durations in stage_durations.items():
            if durations:
                avg_duration = statistics.mean(durations)
                velocity_metrics[f"{stage}_avg_duration_days"] = Decimal(avg_duration / 86400)  # Convert to days
                velocity_metrics[f"{stage}_velocity_score"] = Decimal("100") / max(Decimal("1"), Decimal(avg_duration / 86400))
        
        return velocity_metrics
    
    def _calculate_forecasted_revenue(self) -> Decimal:
        """Calculate forecasted revenue based on current pipeline."""
        forecasted = Decimal("0")
        
        # Get current pipeline
        current_deals = defaultdict(list)
        for deal_id, stage in self.deal_stages.items():
            stage_def = self.stage_definitions.get(stage)
            if stage_def and not stage_def.is_closed:
                # Find latest deal amount
                latest_amount = Decimal("0")
                for transition in reversed(self.stage_history):
                    if transition.deal_id == deal_id and transition.deal_amount > 0:
                        latest_amount = transition.deal_amount
                        break
                
                forecasted += latest_amount * (stage_def.probability / 100)
        
        return forecasted
    
    def _calculate_cycle_times(self, deal_ids: set) -> List[float]:
        """Calculate cycle times for completed deals."""
        cycle_times = []
        
        for deal_id in deal_ids:
            deal_transitions = [t for t in self.stage_history if t.deal_id == deal_id]
            if len(deal_transitions) >= 2:
                start_time = min(t.transition_date for t in deal_transitions)
                end_time = max(t.transition_date for t in deal_transitions)
                cycle_time = (end_time - start_time).total_seconds()
                cycle_times.append(cycle_time)
        
        return cycle_times
    
    def _is_won_stage(self, stage: str) -> bool:
        """Check if a stage represents a won deal."""
        stage_def = self.stage_definitions.get(stage)
        return stage_def and stage_def.is_won
    
    def _is_deal_won(self, deal_id: str) -> bool:
        """Check if a deal is in a won stage."""
        current_stage = self.deal_stages.get(deal_id)
        return current_stage and self._is_won_stage(current_stage)
    
    def generate_predictive_insights(self, deal_id: str) -> Optional[PredictiveInsight]:
        """Generate predictive insights for a specific deal."""
        current_stage = self.get_current_stage(deal_id)
        if not current_stage:
            return None
        
        deal_history = self.get_stage_history(deal_id)
        if not deal_history:
            return None
        
        # Analyze historical patterns
        similar_deals = self._find_similar_deals(deal_id, deal_history)
        
        # Predict next stage
        predicted_next_stage, transition_probability = self._predict_next_stage(current_stage, similar_deals)
        
        # Predict timing
        predicted_transition_date = self._predict_transition_date(current_stage, similar_deals)
        predicted_close_date = self._predict_close_date(deal_id, similar_deals)
        
        # Calculate win probability
        win_probability = self._calculate_win_probability(deal_id, deal_history, similar_deals)
        
        # Forecast amount
        forecasted_amount = self._forecast_deal_amount(deal_id, deal_history)
        
        # Determine confidence level
        confidence_level = self._determine_confidence_level(len(similar_deals), len(deal_history))
        
        # Generate recommendation
        recommendation = self._generate_recommendation(
            current_stage, predicted_next_stage, win_probability, transition_probability
        )
        
        # Identify key factors
        factors = self._identify_key_factors(deal_id, deal_history, similar_deals)
        
        return PredictiveInsight(
            deal_id=deal_id,
            current_stage=current_stage,
            predicted_next_stage=predicted_next_stage,
            probability_of_transition=transition_probability,
            predicted_transition_date=predicted_transition_date,
            predicted_close_date=predicted_close_date,
            win_probability=win_probability,
            forecasted_amount=forecasted_amount,
            confidence_level=confidence_level,
            recommendation=recommendation,
            factors=factors
        )
    
    def _find_similar_deals(self, deal_id: str, deal_history: List[StageTransition]) -> List[str]:
        """Find deals with similar characteristics."""
        if not deal_history:
            return []
        
        latest_transition = deal_history[-1]
        deal_amount = latest_transition.deal_amount
        
        similar_deals = []
        amount_threshold = deal_amount * Decimal("0.5")  # Within 50% of amount
        
        processed_deals = set()
        for transition in self.stage_history:
            if (transition.deal_id != deal_id and 
                transition.deal_id not in processed_deals and
                abs(transition.deal_amount - deal_amount) <= amount_threshold):
                similar_deals.append(transition.deal_id)
                processed_deals.add(transition.deal_id)
        
        return similar_deals[:20]  # Limit to 20 similar deals
    
    def _predict_next_stage(self, current_stage: str, similar_deals: List[str]) -> Tuple[str, Decimal]:
        """Predict the next stage and probability."""
        next_stages = defaultdict(int)
        
        for deal_id in similar_deals:
            deal_transitions = [t for t in self.stage_history if t.deal_id == deal_id]
            
            for i, transition in enumerate(deal_transitions):
                if transition.from_stage == current_stage and i + 1 < len(deal_transitions):
                    next_stage = deal_transitions[i + 1].to_stage
                    next_stages[next_stage] += 1
        
        if not next_stages:
            # Fallback: use stage sequence
            current_def = self.stage_definitions.get(current_stage)
            if current_def:
                next_sequence = current_def.sequence_order + 1
                for stage_id, stage_def in self.stage_definitions.items():
                    if stage_def.sequence_order == next_sequence:
                        return stage_id, Decimal("50")  # Default probability
            return current_stage, Decimal("0")
        
        # Find most likely next stage
        most_likely_stage = max(next_stages, key=next_stages.get)
        total_transitions = sum(next_stages.values())
        probability = Decimal(next_stages[most_likely_stage]) / total_transitions * 100
        
        return most_likely_stage, probability
    
    def _predict_transition_date(self, current_stage: str, similar_deals: List[str]) -> datetime:
        """Predict when the next stage transition will occur."""
        durations = []
        
        for deal_id in similar_deals:
            for transition in self.stage_history:
                if transition.deal_id == deal_id and transition.from_stage == current_stage:
                    durations.append(transition.duration_in_stage.total_seconds())
        
        if durations:
            avg_duration = statistics.median(durations)  # Use median for robustness
            return datetime.now(timezone.utc) + timedelta(seconds=avg_duration)
        else:
            # Default: 7 days
            return datetime.now(timezone.utc) + timedelta(days=7)
    
    def _predict_close_date(self, deal_id: str, similar_deals: List[str]) -> datetime:
        """Predict when the deal will close."""
        cycle_times = []
        
        for similar_deal_id in similar_deals:
            deal_transitions = [t for t in self.stage_history if t.deal_id == similar_deal_id]
            if len(deal_transitions) >= 2:
                start_time = min(t.transition_date for t in deal_transitions)
                end_time = max(t.transition_date for t in deal_transitions)
                # Only include closed deals
                last_stage = max(deal_transitions, key=lambda t: t.transition_date).to_stage
                if self.stage_definitions.get(last_stage, StageDefinition("", "", StageType.CUSTOM, Decimal("0"), 0)).is_closed:
                    cycle_times.append((end_time - start_time).total_seconds())
        
        if cycle_times:
            avg_cycle_time = statistics.median(cycle_times)
            # Estimate how much time has already passed
            deal_history = self.get_stage_history(deal_id)
            if deal_history:
                time_elapsed = (datetime.now(timezone.utc) - deal_history[0].transition_date).total_seconds()
                remaining_time = max(0, avg_cycle_time - time_elapsed)
                return datetime.now(timezone.utc) + timedelta(seconds=remaining_time)
        
        # Default: 30 days from now
        return datetime.now(timezone.utc) + timedelta(days=30)
    
    def _calculate_win_probability(
        self,
        deal_id: str,
        deal_history: List[StageTransition],
        similar_deals: List[str]
    ) -> Decimal:
        """Calculate probability of winning the deal."""
        # Base probability from current stage
        current_stage = self.get_current_stage(deal_id)
        base_probability = self.stage_definitions.get(current_stage, StageDefinition("", "", StageType.CUSTOM, Decimal("0"), 0)).probability
        
        # Adjust based on similar deals outcomes
        won_count = 0
        total_count = 0
        
        for similar_deal_id in similar_deals:
            if self._is_deal_won(similar_deal_id):
                won_count += 1
            total_count += 1
        
        if total_count > 0:
            historical_win_rate = Decimal(won_count) / total_count * 100
            # Weighted average of base probability and historical win rate
            return (base_probability * Decimal("0.6") + historical_win_rate * Decimal("0.4"))
        
        return base_probability
    
    def _forecast_deal_amount(self, deal_id: str, deal_history: List[StageTransition]) -> Decimal:
        """Forecast final deal amount."""
        if deal_history:
            latest_amount = deal_history[-1].deal_amount
            if latest_amount > 0:
                return latest_amount
        
        return Decimal("0")
    
    def _determine_confidence_level(self, similar_deals_count: int, history_length: int) -> str:
        """Determine confidence level for predictions."""
        score = similar_deals_count * 2 + history_length
        
        if score >= 20:
            return "high"
        elif score >= 10:
            return "medium"
        else:
            return "low"
    
    def _generate_recommendation(
        self,
        current_stage: str,
        predicted_next_stage: str,
        win_probability: Decimal,
        transition_probability: Decimal
    ) -> str:
        """Generate actionable recommendation."""
        recommendations = []
        
        if win_probability >= 80:
            recommendations.append("High win probability - prepare for invoice generation")
        elif win_probability >= 60:
            recommendations.append("Good win probability - focus on closing activities")
        elif win_probability < 40:
            recommendations.append("Low win probability - address potential objections")
        
        if transition_probability >= 70:
            recommendations.append(f"Likely to advance to {predicted_next_stage}")
        elif transition_probability < 50:
            recommendations.append("Deal may be stalling - consider intervention")
        
        return "; ".join(recommendations) if recommendations else "Monitor deal progress"
    
    def _identify_key_factors(
        self,
        deal_id: str,
        deal_history: List[StageTransition],
        similar_deals: List[str]
    ) -> List[str]:
        """Identify key factors affecting deal progression."""
        factors = []
        
        # Stage progression speed
        if deal_history:
            avg_duration = sum(t.duration_in_stage.total_seconds() for t in deal_history) / len(deal_history)
            if avg_duration < 7 * 24 * 3600:  # Less than 7 days average
                factors.append("Fast stage progression")
            elif avg_duration > 30 * 24 * 3600:  # More than 30 days average
                factors.append("Slow stage progression")
        
        # Deal size
        if deal_history:
            latest_amount = deal_history[-1].deal_amount
            if latest_amount > Decimal("100000"):
                factors.append("Large deal size")
            elif latest_amount < Decimal("10000"):
                factors.append("Small deal size")
        
        # Similar deals performance
        if len(similar_deals) >= 10:
            factors.append("Strong historical data available")
        elif len(similar_deals) < 3:
            factors.append("Limited historical data")
        
        return factors


# Global pipeline tracker instances
pipeline_trackers: Dict[str, PipelineTracker] = {}


def get_pipeline_tracker(platform: str) -> PipelineTracker:
    """Get or create a pipeline tracker for a platform."""
    if platform not in pipeline_trackers:
        pipeline_trackers[platform] = PipelineTracker(platform)
    return pipeline_trackers[platform]