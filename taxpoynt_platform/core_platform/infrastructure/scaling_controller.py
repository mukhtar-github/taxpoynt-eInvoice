"""
Scaling Controller - Core Platform Infrastructure
Comprehensive auto-scaling control system for the TaxPoynt platform.
Controls auto-scaling based on demand, metrics, and predictive analysis.
"""

import asyncio
import logging
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Set, Tuple
from dataclasses import dataclass, field
from enum import Enum
import json
import statistics
from abc import ABC, abstractmethod

logger = logging.getLogger(__name__)

class ScalingDirection(Enum):
    UP = "up"
    DOWN = "down"
    NONE = "none"

class ScalingTrigger(Enum):
    CPU_UTILIZATION = "cpu_utilization"
    MEMORY_UTILIZATION = "memory_utilization"
    REQUEST_RATE = "request_rate"
    RESPONSE_TIME = "response_time"
    QUEUE_LENGTH = "queue_length"
    CUSTOM_METRIC = "custom_metric"
    SCHEDULED = "scheduled"
    PREDICTIVE = "predictive"

class ScalingStrategy(Enum):
    REACTIVE = "reactive"      # Scale based on current metrics
    PREDICTIVE = "predictive"  # Scale based on predicted load
    SCHEDULED = "scheduled"    # Scale based on schedule
    HYBRID = "hybrid"          # Combine multiple strategies

class ScalingStatus(Enum):
    STABLE = "stable"
    SCALING_UP = "scaling_up"
    SCALING_DOWN = "scaling_down"
    COOLDOWN = "cooldown"
    ERROR = "error"

@dataclass
class ScalingMetric:
    name: str
    current_value: float
    threshold: float
    target_value: Optional[float] = None
    weight: float = 1.0
    aggregation_window: int = 300  # seconds
    history: List[float] = field(default_factory=list)
    timestamp: datetime = field(default_factory=datetime.utcnow)

@dataclass
class ScalingRule:
    id: str
    name: str
    service_id: str
    trigger: ScalingTrigger
    metric_name: str
    threshold_up: float
    threshold_down: float
    scale_up_step: int = 1
    scale_down_step: int = 1
    cooldown_period: int = 300  # seconds
    min_replicas: int = 1
    max_replicas: int = 10
    enabled: bool = True
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class ScalingPolicy:
    id: str
    name: str
    service_id: str
    strategy: ScalingStrategy
    rules: List[ScalingRule]
    target_replicas: int = 1
    current_replicas: int = 1
    status: ScalingStatus = ScalingStatus.STABLE
    last_scale_action: Optional[datetime] = None
    metrics: Dict[str, ScalingMetric] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.utcnow)

@dataclass
class ScalingAction:
    id: str
    policy_id: str
    service_id: str
    direction: ScalingDirection
    from_replicas: int
    to_replicas: int
    trigger: ScalingTrigger
    reason: str
    status: str = "pending"
    started_at: datetime = field(default_factory=datetime.utcnow)
    completed_at: Optional[datetime] = None
    error_message: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class ScheduledScaling:
    id: str
    policy_id: str
    service_id: str
    cron_expression: str
    target_replicas: int
    timezone: str = "UTC"
    enabled: bool = True
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class PredictiveModel:
    id: str
    service_id: str
    model_type: str
    features: List[str]
    training_data: List[Dict[str, Any]] = field(default_factory=list)
    model_parameters: Dict[str, Any] = field(default_factory=dict)
    accuracy_score: Optional[float] = None
    last_trained: Optional[datetime] = None
    predictions: List[Dict[str, Any]] = field(default_factory=list)

class ScalingProvider(ABC):
    @abstractmethod
    async def scale_service(self, service_id: str, replicas: int) -> bool:
        pass
    
    @abstractmethod
    async def get_current_replicas(self, service_id: str) -> int:
        pass
    
    @abstractmethod
    async def get_service_metrics(self, service_id: str) -> Dict[str, float]:
        pass

class KubernetesScalingProvider(ScalingProvider):
    async def scale_service(self, service_id: str, replicas: int) -> bool:
        try:
            logger.info(f"Scaling Kubernetes service {service_id} to {replicas} replicas")
            # In real implementation, this would use kubectl or Kubernetes Python client
            # kubectl scale deployment {service_id} --replicas={replicas}
            return True
        except Exception as e:
            logger.error(f"Failed to scale Kubernetes service: {e}")
            return False
    
    async def get_current_replicas(self, service_id: str) -> int:
        try:
            # Simulate getting current replica count
            return 3  # Example current replica count
        except Exception as e:
            logger.error(f"Failed to get current replicas: {e}")
            return 0
    
    async def get_service_metrics(self, service_id: str) -> Dict[str, float]:
        try:
            # Simulate metrics collection from Kubernetes/Prometheus
            import random
            return {
                'cpu_utilization': random.uniform(20, 90),
                'memory_utilization': random.uniform(30, 85),
                'request_rate': random.uniform(100, 1000),
                'response_time': random.uniform(50, 500),
                'active_connections': random.uniform(10, 100)
            }
        except Exception as e:
            logger.error(f"Failed to get service metrics: {e}")
            return {}

class DockerScalingProvider(ScalingProvider):
    async def scale_service(self, service_id: str, replicas: int) -> bool:
        try:
            logger.info(f"Scaling Docker service {service_id} to {replicas} containers")
            # Docker Swarm scaling: docker service scale {service_id}={replicas}
            return True
        except Exception as e:
            logger.error(f"Failed to scale Docker service: {e}")
            return False
    
    async def get_current_replicas(self, service_id: str) -> int:
        try:
            return 2  # Example current container count
        except Exception as e:
            logger.error(f"Failed to get current replicas: {e}")
            return 0
    
    async def get_service_metrics(self, service_id: str) -> Dict[str, float]:
        try:
            import random
            return {
                'cpu_utilization': random.uniform(15, 80),
                'memory_utilization': random.uniform(25, 75),
                'request_rate': random.uniform(50, 500),
                'response_time': random.uniform(30, 300)
            }
        except Exception as e:
            logger.error(f"Failed to get service metrics: {e}")
            return {}

class ScalingController:
    def __init__(self):
        self.policies: Dict[str, ScalingPolicy] = {}
        self.actions: Dict[str, ScalingAction] = {}
        self.scheduled_scalings: Dict[str, ScheduledScaling] = {}
        self.predictive_models: Dict[str, PredictiveModel] = {}
        self.providers: Dict[str, ScalingProvider] = {}
        self.metrics_history: Dict[str, List[Dict[str, Any]]] = {}
        
        # Initialize providers
        self._initialize_providers()
        
        # Load default policies
        self._load_default_policies()
    
    def _initialize_providers(self):
        """Initialize scaling providers"""
        self.providers = {
            'kubernetes': KubernetesScalingProvider(),
            'docker': DockerScalingProvider()
        }
    
    def _load_default_policies(self):
        """Load default scaling policies"""
        default_policies = [
            ScalingPolicy(
                id="einvoice_api_policy",
                name="EInvoice API Auto Scaling",
                service_id="einvoice_api",
                strategy=ScalingStrategy.REACTIVE,
                rules=[
                    ScalingRule(
                        id="cpu_rule",
                        name="CPU-based scaling",
                        service_id="einvoice_api",
                        trigger=ScalingTrigger.CPU_UTILIZATION,
                        metric_name="cpu_utilization",
                        threshold_up=70.0,
                        threshold_down=30.0,
                        scale_up_step=2,
                        scale_down_step=1,
                        min_replicas=2,
                        max_replicas=20
                    ),
                    ScalingRule(
                        id="memory_rule",
                        name="Memory-based scaling",
                        service_id="einvoice_api",
                        trigger=ScalingTrigger.MEMORY_UTILIZATION,
                        metric_name="memory_utilization",
                        threshold_up=80.0,
                        threshold_down=40.0,
                        scale_up_step=1,
                        scale_down_step=1,
                        min_replicas=2,
                        max_replicas=20
                    )
                ],
                target_replicas=3,
                current_replicas=3
            ),
            ScalingPolicy(
                id="database_policy",
                name="Database Connection Pool Scaling",
                service_id="database_pool",
                strategy=ScalingStrategy.HYBRID,
                rules=[
                    ScalingRule(
                        id="connection_rule",
                        name="Connection pool scaling",
                        service_id="database_pool",
                        trigger=ScalingTrigger.CUSTOM_METRIC,
                        metric_name="active_connections",
                        threshold_up=80.0,
                        threshold_down=20.0,
                        scale_up_step=5,
                        scale_down_step=2,
                        min_replicas=10,
                        max_replicas=100
                    )
                ],
                target_replicas=20,
                current_replicas=20
            )
        ]
        
        for policy in default_policies:
            self.policies[policy.id] = policy
    
    async def create_scaling_policy(self, policy_data: Dict[str, Any]) -> Optional[ScalingPolicy]:
        """Create a new scaling policy"""
        try:
            # Parse scaling rules
            rules = []
            for rule_data in policy_data.get('rules', []):
                rule = ScalingRule(
                    id=rule_data.get('id', f"rule_{int(time.time())}"),
                    name=rule_data['name'],
                    service_id=policy_data['service_id'],
                    trigger=ScalingTrigger(rule_data['trigger']),
                    metric_name=rule_data['metric_name'],
                    threshold_up=rule_data['threshold_up'],
                    threshold_down=rule_data['threshold_down'],
                    scale_up_step=rule_data.get('scale_up_step', 1),
                    scale_down_step=rule_data.get('scale_down_step', 1),
                    cooldown_period=rule_data.get('cooldown_period', 300),
                    min_replicas=rule_data.get('min_replicas', 1),
                    max_replicas=rule_data.get('max_replicas', 10),
                    enabled=rule_data.get('enabled', True),
                    metadata=rule_data.get('metadata', {})
                )
                rules.append(rule)
            
            policy = ScalingPolicy(
                id=policy_data.get('id', f"policy_{int(time.time())}"),
                name=policy_data['name'],
                service_id=policy_data['service_id'],
                strategy=ScalingStrategy(policy_data.get('strategy', 'reactive')),
                rules=rules,
                target_replicas=policy_data.get('target_replicas', 1),
                current_replicas=policy_data.get('current_replicas', 1),
                metadata=policy_data.get('metadata', {})
            )
            
            self.policies[policy.id] = policy
            logger.info(f"Created scaling policy: {policy.id}")
            return policy
            
        except Exception as e:
            logger.error(f"Failed to create scaling policy: {e}")
            return None
    
    async def update_metrics(self, policy_id: str, provider_name: str = 'kubernetes'):
        """Update metrics for a scaling policy"""
        try:
            if policy_id not in self.policies:
                logger.warning(f"Policy not found: {policy_id}")
                return
            
            policy = self.policies[policy_id]
            
            if provider_name not in self.providers:
                logger.warning(f"Provider not found: {provider_name}")
                return
            
            provider = self.providers[provider_name]
            
            # Get current metrics
            metrics = await provider.get_service_metrics(policy.service_id)
            
            # Update policy metrics
            for metric_name, value in metrics.items():
                if metric_name in policy.metrics:
                    metric = policy.metrics[metric_name]
                    metric.history.append(value)
                    
                    # Keep only recent history
                    max_history = 100
                    if len(metric.history) > max_history:
                        metric.history = metric.history[-max_history:]
                    
                    metric.current_value = value
                    metric.timestamp = datetime.utcnow()
                else:
                    # Create new metric
                    policy.metrics[metric_name] = ScalingMetric(
                        name=metric_name,
                        current_value=value,
                        threshold=0.0,  # Will be set by rules
                        history=[value]
                    )
            
            # Store metrics history for analysis
            if policy.service_id not in self.metrics_history:
                self.metrics_history[policy.service_id] = []
            
            self.metrics_history[policy.service_id].append({
                'timestamp': datetime.utcnow().isoformat(),
                'metrics': metrics.copy()
            })
            
            # Keep only recent history
            if len(self.metrics_history[policy.service_id]) > 1000:
                self.metrics_history[policy.service_id] = self.metrics_history[policy.service_id][-1000:]
                
        except Exception as e:
            logger.error(f"Failed to update metrics: {e}")
    
    async def evaluate_scaling_decision(self, policy_id: str) -> Optional[ScalingAction]:
        """Evaluate if scaling is needed for a policy"""
        try:
            if policy_id not in self.policies:
                return None
            
            policy = self.policies[policy_id]
            
            # Check if in cooldown period
            if policy.last_scale_action:
                time_since_last_action = (datetime.utcnow() - policy.last_scale_action).total_seconds()
                if time_since_last_action < 300:  # 5 minute cooldown
                    return None
            
            scaling_decisions = []
            
            # Evaluate each rule
            for rule in policy.rules:
                if not rule.enabled:
                    continue
                
                if rule.metric_name not in policy.metrics:
                    continue
                
                metric = policy.metrics[rule.metric_name]
                decision = await self._evaluate_rule(rule, metric, policy)
                
                if decision:
                    scaling_decisions.append(decision)
            
            # Combine decisions (take the most aggressive scaling)
            if scaling_decisions:
                # Sort by priority: scale up > scale down
                scaling_decisions.sort(key=lambda x: (
                    x['direction'] == ScalingDirection.UP,
                    abs(x['target_replicas'] - policy.current_replicas)
                ), reverse=True)
                
                chosen_decision = scaling_decisions[0]
                
                # Create scaling action
                action = ScalingAction(
                    id=f"action_{int(time.time())}_{policy.service_id}",
                    policy_id=policy_id,
                    service_id=policy.service_id,
                    direction=chosen_decision['direction'],
                    from_replicas=policy.current_replicas,
                    to_replicas=chosen_decision['target_replicas'],
                    trigger=chosen_decision['trigger'],
                    reason=chosen_decision['reason']
                )
                
                return action
            
            return None
            
        except Exception as e:
            logger.error(f"Failed to evaluate scaling decision: {e}")
            return None
    
    async def _evaluate_rule(self, rule: ScalingRule, metric: ScalingMetric, policy: ScalingPolicy) -> Optional[Dict[str, Any]]:
        """Evaluate a single scaling rule"""
        try:
            current_value = metric.current_value
            
            # Calculate average over aggregation window if we have history
            if len(metric.history) >= 3:
                # Use recent values for stability
                recent_values = metric.history[-3:]
                avg_value = statistics.mean(recent_values)
                current_value = avg_value
            
            # Check scale up condition
            if current_value > rule.threshold_up:
                target_replicas = min(
                    policy.current_replicas + rule.scale_up_step,
                    rule.max_replicas
                )
                
                if target_replicas > policy.current_replicas:
                    return {
                        'direction': ScalingDirection.UP,
                        'target_replicas': target_replicas,
                        'trigger': rule.trigger,
                        'reason': f"{rule.metric_name} ({current_value:.1f}) > threshold ({rule.threshold_up})"
                    }
            
            # Check scale down condition
            elif current_value < rule.threshold_down:
                target_replicas = max(
                    policy.current_replicas - rule.scale_down_step,
                    rule.min_replicas
                )
                
                if target_replicas < policy.current_replicas:
                    return {
                        'direction': ScalingDirection.DOWN,
                        'target_replicas': target_replicas,
                        'trigger': rule.trigger,
                        'reason': f"{rule.metric_name} ({current_value:.1f}) < threshold ({rule.threshold_down})"
                    }
            
            return None
            
        except Exception as e:
            logger.error(f"Failed to evaluate rule: {e}")
            return None
    
    async def execute_scaling_action(self, action: ScalingAction, provider_name: str = 'kubernetes') -> bool:
        """Execute a scaling action"""
        try:
            if provider_name not in self.providers:
                logger.error(f"Provider not found: {provider_name}")
                return False
            
            provider = self.providers[provider_name]
            policy = self.policies[action.policy_id]
            
            action.status = "executing"
            
            # Execute scaling
            success = await provider.scale_service(action.service_id, action.to_replicas)
            
            if success:
                action.status = "completed"
                action.completed_at = datetime.utcnow()
                
                # Update policy state
                policy.current_replicas = action.to_replicas
                policy.target_replicas = action.to_replicas
                policy.last_scale_action = datetime.utcnow()
                policy.status = ScalingStatus.STABLE
                
                self.actions[action.id] = action
                
                logger.info(f"Scaling action completed: {action.service_id} {action.from_replicas} -> {action.to_replicas}")
                return True
            else:
                action.status = "failed"
                action.error_message = "Provider scaling failed"
                action.completed_at = datetime.utcnow()
                
                policy.status = ScalingStatus.ERROR
                
                self.actions[action.id] = action
                
                logger.error(f"Scaling action failed: {action.id}")
                return False
                
        except Exception as e:
            logger.error(f"Failed to execute scaling action: {e}")
            return False
    
    async def create_predictive_model(self, model_data: Dict[str, Any]) -> Optional[PredictiveModel]:
        """Create a predictive scaling model"""
        try:
            model = PredictiveModel(
                id=model_data.get('id', f"model_{int(time.time())}"),
                service_id=model_data['service_id'],
                model_type=model_data.get('model_type', 'linear_regression'),
                features=model_data.get('features', ['cpu_utilization', 'memory_utilization', 'request_rate']),
                model_parameters=model_data.get('model_parameters', {}),
                accuracy_score=model_data.get('accuracy_score')
            )
            
            self.predictive_models[model.id] = model
            logger.info(f"Created predictive model: {model.id}")
            return model
            
        except Exception as e:
            logger.error(f"Failed to create predictive model: {e}")
            return None
    
    async def train_predictive_model(self, model_id: str) -> bool:
        """Train a predictive model with historical data"""
        try:
            if model_id not in self.predictive_models:
                logger.error(f"Model not found: {model_id}")
                return False
            
            model = self.predictive_models[model_id]
            
            # Get historical data
            if model.service_id not in self.metrics_history:
                logger.warning(f"No historical data for service: {model.service_id}")
                return False
            
            training_data = self.metrics_history[model.service_id]
            
            # Simulate model training
            logger.info(f"Training predictive model {model.id} with {len(training_data)} data points")
            
            # In real implementation, this would:
            # 1. Prepare training data (features and labels)
            # 2. Train machine learning model (scikit-learn, tensorflow, etc.)
            # 3. Validate model performance
            # 4. Store trained model
            
            model.training_data = training_data[-500:]  # Keep recent data
            model.last_trained = datetime.utcnow()
            model.accuracy_score = 0.85  # Simulated accuracy
            
            logger.info(f"Model training completed: {model.id} (accuracy: {model.accuracy_score:.2f})")
            return True
            
        except Exception as e:
            logger.error(f"Failed to train predictive model: {e}")
            return False
    
    async def predict_scaling_needs(self, model_id: str, forecast_horizon: int = 3600) -> List[Dict[str, Any]]:
        """Predict future scaling needs using trained model"""
        try:
            if model_id not in self.predictive_models:
                logger.error(f"Model not found: {model_id}")
                return []
            
            model = self.predictive_models[model_id]
            
            if not model.last_trained:
                logger.warning(f"Model not trained: {model_id}")
                return []
            
            # Simulate predictions for next hour (in 15-minute intervals)
            predictions = []
            current_time = datetime.utcnow()
            
            for i in range(0, forecast_horizon, 900):  # 15-minute intervals
                prediction_time = current_time + timedelta(seconds=i)
                
                # Simulate prediction (in real implementation, use trained model)
                import random
                predicted_load = random.uniform(0.3, 0.9)  # CPU utilization prediction
                predicted_replicas = max(2, int(predicted_load * 10))
                
                predictions.append({
                    'timestamp': prediction_time.isoformat(),
                    'predicted_cpu_utilization': predicted_load * 100,
                    'recommended_replicas': predicted_replicas,
                    'confidence': random.uniform(0.7, 0.95)
                })
            
            model.predictions = predictions
            return predictions
            
        except Exception as e:
            logger.error(f"Failed to predict scaling needs: {e}")
            return []
    
    async def start_auto_scaling(self, interval: int = 60):
        """Start the auto-scaling control loop"""
        try:
            logger.info("Starting auto-scaling controller")
            
            while True:
                for policy_id in self.policies:
                    try:
                        # Update metrics
                        await self.update_metrics(policy_id)
                        
                        # Evaluate scaling decision
                        action = await self.evaluate_scaling_decision(policy_id)
                        
                        if action:
                            # Execute scaling action
                            success = await self.execute_scaling_action(action)
                            
                            if success:
                                logger.info(f"Auto-scaling executed: {action.service_id} -> {action.to_replicas} replicas")
                            else:
                                logger.error(f"Auto-scaling failed: {action.id}")
                        
                    except Exception as e:
                        logger.error(f"Error processing policy {policy_id}: {e}")
                
                await asyncio.sleep(interval)
                
        except Exception as e:
            logger.error(f"Auto-scaling controller failed: {e}")
    
    async def get_scaling_recommendations(self, service_id: str) -> Dict[str, Any]:
        """Get scaling recommendations for a service"""
        try:
            recommendations = {
                'service_id': service_id,
                'current_replicas': 0,
                'recommended_replicas': 0,
                'recommendations': [],
                'predictive_analysis': None
            }
            
            # Find policies for this service
            service_policies = [p for p in self.policies.values() if p.service_id == service_id]
            
            if not service_policies:
                return recommendations
            
            policy = service_policies[0]  # Use first policy
            recommendations['current_replicas'] = policy.current_replicas
            
            # Get current metrics analysis
            for rule in policy.rules:
                if rule.metric_name in policy.metrics:
                    metric = policy.metrics[rule.metric_name]
                    
                    if metric.current_value > rule.threshold_up:
                        recommendations['recommendations'].append({
                            'type': 'scale_up',
                            'reason': f"{rule.metric_name} ({metric.current_value:.1f}) above threshold ({rule.threshold_up})",
                            'suggested_replicas': min(policy.current_replicas + rule.scale_up_step, rule.max_replicas)
                        })
                    elif metric.current_value < rule.threshold_down:
                        recommendations['recommendations'].append({
                            'type': 'scale_down',
                            'reason': f"{rule.metric_name} ({metric.current_value:.1f}) below threshold ({rule.threshold_down})",
                            'suggested_replicas': max(policy.current_replicas - rule.scale_down_step, rule.min_replicas)
                        })
            
            # Add predictive analysis if available
            service_models = [m for m in self.predictive_models.values() if m.service_id == service_id]
            if service_models:
                model = service_models[0]
                if model.predictions:
                    recent_prediction = model.predictions[0] if model.predictions else None
                    if recent_prediction:
                        recommendations['predictive_analysis'] = {
                            'predicted_load': recent_prediction.get('predicted_cpu_utilization'),
                            'recommended_replicas': recent_prediction.get('recommended_replicas'),
                            'confidence': recent_prediction.get('confidence')
                        }
            
            # Determine final recommendation
            if recommendations['recommendations']:
                # Take the most conservative scaling recommendation
                scale_up_suggestions = [r for r in recommendations['recommendations'] if r['type'] == 'scale_up']
                scale_down_suggestions = [r for r in recommendations['recommendations'] if r['type'] == 'scale_down']
                
                if scale_up_suggestions:
                    recommendations['recommended_replicas'] = max([r['suggested_replicas'] for r in scale_up_suggestions])
                elif scale_down_suggestions:
                    recommendations['recommended_replicas'] = min([r['suggested_replicas'] for r in scale_down_suggestions])
            else:
                recommendations['recommended_replicas'] = policy.current_replicas
            
            return recommendations
            
        except Exception as e:
            logger.error(f"Failed to get scaling recommendations: {e}")
            return {}
    
    def get_scaling_statistics(self) -> Dict[str, Any]:
        """Get scaling system statistics"""
        try:
            total_actions = len(self.actions)
            
            # Action status distribution
            action_status_counts = {}
            for action in self.actions.values():
                status = action.status
                action_status_counts[status] = action_status_counts.get(status, 0) + 1
            
            # Scaling direction distribution
            direction_counts = {}
            for direction in ScalingDirection:
                direction_counts[direction.value] = len([
                    a for a in self.actions.values()
                    if a.direction == direction
                ])
            
            # Average scaling response time
            completed_actions = [
                a for a in self.actions.values()
                if a.status == "completed" and a.started_at and a.completed_at
            ]
            
            avg_response_time = 0
            if completed_actions:
                total_response_time = sum([
                    (a.completed_at - a.started_at).total_seconds()
                    for a in completed_actions
                ])
                avg_response_time = total_response_time / len(completed_actions)
            
            # Success rate
            successful_actions = len([a for a in self.actions.values() if a.status == "completed"])
            success_rate = (successful_actions / total_actions * 100) if total_actions > 0 else 0
            
            return {
                'total_policies': len(self.policies),
                'active_policies': len([p for p in self.policies.values() if any(r.enabled for r in p.rules)]),
                'total_actions': total_actions,
                'action_status_distribution': action_status_counts,
                'scaling_direction_distribution': direction_counts,
                'success_rate_percent': success_rate,
                'average_response_time_seconds': avg_response_time,
                'total_predictive_models': len(self.predictive_models),
                'trained_models': len([m for m in self.predictive_models.values() if m.last_trained])
            }
        except Exception as e:
            logger.error(f"Failed to get scaling statistics: {e}")
            return {}

# Global scaling controller instance
scaling_controller = ScalingController()

async def initialize_scaling_controller():
    """Initialize the scaling controller"""
    try:
        logger.info("Scaling controller initialized successfully")
        return True
    except Exception as e:
        logger.error(f"Failed to initialize scaling controller: {e}")
        return False

if __name__ == "__main__":
    async def main():
        await initialize_scaling_controller()
        
        # Example usage
        # Create scaling policy
        policy_data = {
            'name': 'Test Service Auto Scaling',
            'service_id': 'test_service',
            'strategy': 'reactive',
            'rules': [
                {
                    'name': 'CPU-based scaling',
                    'trigger': 'cpu_utilization',
                    'metric_name': 'cpu_utilization',
                    'threshold_up': 70.0,
                    'threshold_down': 30.0,
                    'scale_up_step': 2,
                    'scale_down_step': 1,
                    'min_replicas': 2,
                    'max_replicas': 10
                }
            ],
            'current_replicas': 3
        }
        
        policy = await scaling_controller.create_scaling_policy(policy_data)
        if policy:
            print(f"Created scaling policy: {policy.id}")
            
            # Update metrics and evaluate scaling
            await scaling_controller.update_metrics(policy.id)
            action = await scaling_controller.evaluate_scaling_decision(policy.id)
            
            if action:
                print(f"Scaling action recommended: {action.direction.value} to {action.to_replicas} replicas")
                success = await scaling_controller.execute_scaling_action(action)
                print(f"Scaling action executed: {success}")
            else:
                print("No scaling action needed")
            
            # Get recommendations
            recommendations = await scaling_controller.get_scaling_recommendations('test_service')
            print(f"Scaling recommendations: {json.dumps(recommendations, indent=2)}")
            
            # Get statistics
            stats = scaling_controller.get_scaling_statistics()
            print(f"Scaling statistics: {json.dumps(stats, indent=2)}")
    
    asyncio.run(main())