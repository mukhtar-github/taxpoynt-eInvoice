"""
Hybrid Service: Workflow State Machine
Manages workflow state transitions and persistence
"""
import asyncio
import json
import logging
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, Optional, List, Union, Callable, Set
from dataclasses import dataclass, asdict
from enum import Enum
import uuid

from core_platform.database import get_db_session
from core_platform.models.workflow import WorkflowState, StateTransition, StateMachine
from core_platform.cache import CacheService
from core_platform.events import EventBus
from core_platform.monitoring import MetricsCollector
from core_platform.notifications import NotificationService

logger = logging.getLogger(__name__)


class StateType(str, Enum):
    """State types"""
    INITIAL = "initial"
    PROCESSING = "processing"
    WAITING = "waiting"
    DECISION = "decision"
    PARALLEL = "parallel"
    FINAL = "final"
    ERROR = "error"
    TIMEOUT = "timeout"


class TransitionType(str, Enum):
    """Transition types"""
    AUTOMATIC = "automatic"
    MANUAL = "manual"
    CONDITIONAL = "conditional"
    TIMED = "timed"
    EVENT_TRIGGERED = "event_triggered"


class TransitionCondition(str, Enum):
    """Transition conditions"""
    SUCCESS = "success"
    FAILURE = "failure"
    TIMEOUT = "timeout"
    MANUAL_APPROVAL = "manual_approval"
    EXTERNAL_EVENT = "external_event"
    DATA_CONDITION = "data_condition"


@dataclass
class State:
    """State definition"""
    state_id: str
    name: str
    description: str
    state_type: StateType
    entry_actions: List[str]
    exit_actions: List[str]
    timeout: Optional[int] = None
    metadata: Dict[str, Any] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class Transition:
    """Transition definition"""
    transition_id: str
    from_state: str
    to_state: str
    condition: TransitionCondition
    transition_type: TransitionType
    guard_condition: Optional[str] = None
    actions: List[str] = None
    timeout: Optional[int] = None
    metadata: Dict[str, Any] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class StateMachineDefinition:
    """State machine definition"""
    machine_id: str
    name: str
    description: str
    initial_state: str
    final_states: List[str]
    states: List[State]
    transitions: List[Transition]
    global_timeout: Optional[int] = None
    metadata: Dict[str, Any] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class StateMachineInstance:
    """State machine instance"""
    instance_id: str
    machine_id: str
    current_state: str
    context: Dict[str, Any]
    history: List[Dict[str, Any]]
    created_at: datetime
    updated_at: datetime
    completed_at: Optional[datetime] = None
    status: str = "active"
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class StateTransitionEvent:
    """State transition event"""
    event_id: str
    instance_id: str
    from_state: str
    to_state: str
    transition_id: str
    trigger: str
    context: Dict[str, Any]
    timestamp: datetime
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class WorkflowStateMachine:
    """Workflow state machine manager"""
    
    def __init__(self):
        self.cache_service = CacheService()
        self.event_bus = EventBus()
        self.metrics_collector = MetricsCollector()
        self.notification_service = NotificationService()
        self.logger = logging.getLogger(__name__)
        
        # State machine definitions
        self.machine_definitions: Dict[str, StateMachineDefinition] = {}
        
        # Active instances
        self.active_instances: Dict[str, StateMachineInstance] = {}
        
        # State handlers
        self.state_handlers: Dict[str, Callable] = {}
        
        # Transition guards
        self.transition_guards: Dict[str, Callable] = {}
        
        # Action handlers
        self.action_handlers: Dict[str, Callable] = {}
    
    async def register_state_machine(self, definition: StateMachineDefinition) -> bool:
        """Register a state machine definition"""
        try:
            # Validate definition
            if not await self._validate_state_machine_definition(definition):
                raise ValueError(f"Invalid state machine definition: {definition.machine_id}")
            
            # Store definition
            self.machine_definitions[definition.machine_id] = definition
            
            # Cache definition
            await self.cache_service.set(
                f"state_machine_definition:{definition.machine_id}",
                definition.to_dict(),
                ttl=86400  # 24 hours
            )
            
            # Emit event
            await self.event_bus.emit("state_machine_registered", {
                "machine_id": definition.machine_id,
                "name": definition.name,
                "timestamp": datetime.now(timezone.utc).isoformat()
            })
            
            self.logger.info(f"State machine registered: {definition.machine_id}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error registering state machine: {str(e)}")
            raise
    
    async def create_instance(
        self,
        machine_id: str,
        context: Dict[str, Any],
        instance_id: Optional[str] = None
    ) -> StateMachineInstance:
        """Create a new state machine instance"""
        try:
            if not instance_id:
                instance_id = str(uuid.uuid4())
            
            # Get machine definition
            definition = await self._get_machine_definition(machine_id)
            if not definition:
                raise ValueError(f"State machine not found: {machine_id}")
            
            # Create instance
            instance = StateMachineInstance(
                instance_id=instance_id,
                machine_id=machine_id,
                current_state=definition.initial_state,
                context=context,
                history=[],
                created_at=datetime.now(timezone.utc),
                updated_at=datetime.now(timezone.utc),
                status="active"
            )
            
            # Add to active instances
            self.active_instances[instance_id] = instance
            
            # Execute entry actions for initial state
            await self._execute_entry_actions(instance, definition.initial_state)
            
            # Store instance
            await self._store_instance(instance)
            
            # Emit event
            await self.event_bus.emit("state_machine_instance_created", {
                "instance_id": instance_id,
                "machine_id": machine_id,
                "initial_state": definition.initial_state,
                "timestamp": datetime.now(timezone.utc).isoformat()
            })
            
            self.logger.info(f"State machine instance created: {instance_id}")
            return instance
            
        except Exception as e:
            self.logger.error(f"Error creating state machine instance: {str(e)}")
            raise
    
    async def transition_state(
        self,
        instance_id: str,
        trigger: str,
        context_update: Optional[Dict[str, Any]] = None
    ) -> bool:
        """Trigger a state transition"""
        try:
            # Get instance
            instance = await self._get_instance(instance_id)
            if not instance:
                raise ValueError(f"State machine instance not found: {instance_id}")
            
            # Get machine definition
            definition = await self._get_machine_definition(instance.machine_id)
            if not definition:
                raise ValueError(f"State machine definition not found: {instance.machine_id}")
            
            # Find applicable transitions
            applicable_transitions = await self._find_applicable_transitions(
                instance, definition, trigger
            )
            
            if not applicable_transitions:
                self.logger.warning(f"No applicable transitions for trigger '{trigger}' from state '{instance.current_state}'")
                return False
            
            # Select transition (first applicable one)
            transition = applicable_transitions[0]
            
            # Update context if provided
            if context_update:
                instance.context.update(context_update)
            
            # Execute transition
            success = await self._execute_transition(instance, transition, trigger)
            
            if success:
                # Update instance
                instance.updated_at = datetime.now(timezone.utc)
                
                # Store updated instance
                await self._store_instance(instance)
                
                # Check if reached final state
                if instance.current_state in definition.final_states:
                    instance.status = "completed"
                    instance.completed_at = datetime.now(timezone.utc)
                    
                    # Remove from active instances
                    if instance_id in self.active_instances:
                        del self.active_instances[instance_id]
                    
                    # Emit completion event
                    await self.event_bus.emit("state_machine_instance_completed", {
                        "instance_id": instance_id,
                        "machine_id": instance.machine_id,
                        "final_state": instance.current_state,
                        "timestamp": datetime.now(timezone.utc).isoformat()
                    })
            
            return success
            
        except Exception as e:
            self.logger.error(f"Error transitioning state: {str(e)}")
            raise
    
    async def get_instance_status(self, instance_id: str) -> Optional[StateMachineInstance]:
        """Get state machine instance status"""
        try:
            # Check active instances first
            if instance_id in self.active_instances:
                return self.active_instances[instance_id]
            
            # Check stored instances
            return await self._get_stored_instance(instance_id)
            
        except Exception as e:
            self.logger.error(f"Error getting instance status: {str(e)}")
            return None
    
    async def get_possible_transitions(self, instance_id: str) -> List[Dict[str, Any]]:
        """Get possible transitions from current state"""
        try:
            # Get instance
            instance = await self._get_instance(instance_id)
            if not instance:
                return []
            
            # Get machine definition
            definition = await self._get_machine_definition(instance.machine_id)
            if not definition:
                return []
            
            # Find transitions from current state
            possible_transitions = []
            
            for transition in definition.transitions:
                if transition.from_state == instance.current_state:
                    # Check guard condition if present
                    if transition.guard_condition:
                        if not await self._evaluate_guard_condition(
                            transition.guard_condition, instance
                        ):
                            continue
                    
                    possible_transitions.append({
                        "transition_id": transition.transition_id,
                        "to_state": transition.to_state,
                        "condition": transition.condition,
                        "transition_type": transition.transition_type,
                        "description": transition.metadata.get("description", "") if transition.metadata else ""
                    })
            
            return possible_transitions
            
        except Exception as e:
            self.logger.error(f"Error getting possible transitions: {str(e)}")
            return []
    
    async def cancel_instance(self, instance_id: str) -> bool:
        """Cancel a state machine instance"""
        try:
            # Get instance
            instance = await self._get_instance(instance_id)
            if not instance:
                return False
            
            # Execute exit actions for current state
            await self._execute_exit_actions(instance, instance.current_state)
            
            # Update instance status
            instance.status = "cancelled"
            instance.completed_at = datetime.now(timezone.utc)
            instance.updated_at = datetime.now(timezone.utc)
            
            # Remove from active instances
            if instance_id in self.active_instances:
                del self.active_instances[instance_id]
            
            # Store updated instance
            await self._store_instance(instance)
            
            # Emit event
            await self.event_bus.emit("state_machine_instance_cancelled", {
                "instance_id": instance_id,
                "machine_id": instance.machine_id,
                "cancelled_at_state": instance.current_state,
                "timestamp": datetime.now(timezone.utc).isoformat()
            })
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error cancelling instance: {str(e)}")
            return False
    
    async def list_active_instances(self) -> List[Dict[str, Any]]:
        """List all active state machine instances"""
        try:
            active_list = []
            
            for instance_id, instance in self.active_instances.items():
                active_list.append({
                    "instance_id": instance_id,
                    "machine_id": instance.machine_id,
                    "current_state": instance.current_state,
                    "status": instance.status,
                    "created_at": instance.created_at.isoformat(),
                    "updated_at": instance.updated_at.isoformat()
                })
            
            return active_list
            
        except Exception as e:
            self.logger.error(f"Error listing active instances: {str(e)}")
            return []
    
    async def get_state_machine_metrics(self, machine_id: str) -> Dict[str, Any]:
        """Get state machine metrics"""
        try:
            with get_db_session() as db:
                # Get total instances
                total_instances = db.query(StateMachineInstance).filter(
                    StateMachineInstance.machine_id == machine_id
                ).count()
                
                # Get completed instances
                completed_instances = db.query(StateMachineInstance).filter(
                    StateMachineInstance.machine_id == machine_id,
                    StateMachineInstance.status == "completed"
                ).count()
                
                # Get cancelled instances
                cancelled_instances = db.query(StateMachineInstance).filter(
                    StateMachineInstance.machine_id == machine_id,
                    StateMachineInstance.status == "cancelled"
                ).count()
                
                # Get active instances
                active_instances = len([
                    i for i in self.active_instances.values()
                    if i.machine_id == machine_id
                ])
                
                # Calculate completion rate
                completion_rate = (completed_instances / total_instances * 100) if total_instances > 0 else 0
                
                # Get average execution time
                avg_execution_time = await self._calculate_average_execution_time(db, machine_id)
                
                # Get state distribution
                state_distribution = await self._get_state_distribution(db, machine_id)
                
                return {
                    "machine_id": machine_id,
                    "total_instances": total_instances,
                    "completed_instances": completed_instances,
                    "cancelled_instances": cancelled_instances,
                    "active_instances": active_instances,
                    "completion_rate": completion_rate,
                    "average_execution_time": avg_execution_time,
                    "state_distribution": state_distribution,
                    "timestamp": datetime.now(timezone.utc).isoformat()
                }
                
        except Exception as e:
            self.logger.error(f"Error getting state machine metrics: {str(e)}")
            raise
    
    # Handler registration methods
    
    def register_state_handler(self, state_id: str, handler: Callable) -> None:
        """Register a state handler"""
        self.state_handlers[state_id] = handler
    
    def register_transition_guard(self, guard_name: str, guard: Callable) -> None:
        """Register a transition guard"""
        self.transition_guards[guard_name] = guard
    
    def register_action_handler(self, action_name: str, handler: Callable) -> None:
        """Register an action handler"""
        self.action_handlers[action_name] = handler
    
    # Private helper methods
    
    async def _validate_state_machine_definition(self, definition: StateMachineDefinition) -> bool:
        """Validate state machine definition"""
        try:
            # Check required fields
            if not definition.machine_id or not definition.name:
                return False
            
            # Check states
            if not definition.states:
                return False
            
            # Check initial state exists
            state_ids = {state.state_id for state in definition.states}
            if definition.initial_state not in state_ids:
                return False
            
            # Check final states exist
            for final_state in definition.final_states:
                if final_state not in state_ids:
                    return False
            
            # Check transitions
            for transition in definition.transitions:
                if transition.from_state not in state_ids or transition.to_state not in state_ids:
                    return False
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error validating state machine definition: {str(e)}")
            return False
    
    async def _get_machine_definition(self, machine_id: str) -> Optional[StateMachineDefinition]:
        """Get state machine definition"""
        try:
            # Check cache first
            cached_def = await self.cache_service.get(f"state_machine_definition:{machine_id}")
            if cached_def:
                return StateMachineDefinition(**cached_def)
            
            # Check registry
            if machine_id in self.machine_definitions:
                return self.machine_definitions[machine_id]
            
            return None
            
        except Exception as e:
            self.logger.error(f"Error getting machine definition: {str(e)}")
            return None
    
    async def _get_instance(self, instance_id: str) -> Optional[StateMachineInstance]:
        """Get state machine instance"""
        try:
            # Check active instances first
            if instance_id in self.active_instances:
                return self.active_instances[instance_id]
            
            # Check stored instances
            return await self._get_stored_instance(instance_id)
            
        except Exception as e:
            self.logger.error(f"Error getting instance: {str(e)}")
            return None
    
    async def _find_applicable_transitions(
        self,
        instance: StateMachineInstance,
        definition: StateMachineDefinition,
        trigger: str
    ) -> List[Transition]:
        """Find applicable transitions for trigger"""
        try:
            applicable_transitions = []
            
            for transition in definition.transitions:
                if transition.from_state != instance.current_state:
                    continue
                
                # Check condition
                if not await self._check_transition_condition(transition, trigger, instance):
                    continue
                
                # Check guard condition
                if transition.guard_condition:
                    if not await self._evaluate_guard_condition(transition.guard_condition, instance):
                        continue
                
                applicable_transitions.append(transition)
            
            return applicable_transitions
            
        except Exception as e:
            self.logger.error(f"Error finding applicable transitions: {str(e)}")
            return []
    
    async def _check_transition_condition(
        self,
        transition: Transition,
        trigger: str,
        instance: StateMachineInstance
    ) -> bool:
        """Check if transition condition is met"""
        try:
            if transition.condition == TransitionCondition.SUCCESS and trigger == "success":
                return True
            elif transition.condition == TransitionCondition.FAILURE and trigger == "failure":
                return True
            elif transition.condition == TransitionCondition.TIMEOUT and trigger == "timeout":
                return True
            elif transition.condition == TransitionCondition.MANUAL_APPROVAL and trigger == "manual_approval":
                return True
            elif transition.condition == TransitionCondition.EXTERNAL_EVENT and trigger == "external_event":
                return True
            elif transition.condition == TransitionCondition.DATA_CONDITION:
                return await self._evaluate_data_condition(transition, instance)
            
            return False
            
        except Exception as e:
            self.logger.error(f"Error checking transition condition: {str(e)}")
            return False
    
    async def _evaluate_guard_condition(self, guard_condition: str, instance: StateMachineInstance) -> bool:
        """Evaluate transition guard condition"""
        try:
            # Get guard function
            guard_func = self.transition_guards.get(guard_condition)
            if not guard_func:
                self.logger.warning(f"Guard condition not found: {guard_condition}")
                return True  # Default to allow if guard not found
            
            # Execute guard
            if asyncio.iscoroutinefunction(guard_func):
                return await guard_func(instance)
            else:
                return guard_func(instance)
                
        except Exception as e:
            self.logger.error(f"Error evaluating guard condition: {str(e)}")
            return False
    
    async def _evaluate_data_condition(self, transition: Transition, instance: StateMachineInstance) -> bool:
        """Evaluate data condition"""
        try:
            # Simple data condition evaluation
            # In production, this would use a more robust expression evaluator
            condition_expr = transition.metadata.get("condition_expression") if transition.metadata else None
            if not condition_expr:
                return False
            
            return eval(condition_expr, {"context": instance.context})
            
        except Exception as e:
            self.logger.error(f"Error evaluating data condition: {str(e)}")
            return False
    
    async def _execute_transition(
        self,
        instance: StateMachineInstance,
        transition: Transition,
        trigger: str
    ) -> bool:
        """Execute state transition"""
        try:
            old_state = instance.current_state
            new_state = transition.to_state
            
            # Execute exit actions for current state
            await self._execute_exit_actions(instance, old_state)
            
            # Execute transition actions
            if transition.actions:
                for action in transition.actions:
                    await self._execute_action(action, instance)
            
            # Update current state
            instance.current_state = new_state
            
            # Execute entry actions for new state
            await self._execute_entry_actions(instance, new_state)
            
            # Add to history
            transition_event = StateTransitionEvent(
                event_id=str(uuid.uuid4()),
                instance_id=instance.instance_id,
                from_state=old_state,
                to_state=new_state,
                transition_id=transition.transition_id,
                trigger=trigger,
                context=instance.context.copy(),
                timestamp=datetime.now(timezone.utc)
            )
            
            instance.history.append(transition_event.to_dict())
            
            # Emit transition event
            await self.event_bus.emit("state_transition_executed", {
                "instance_id": instance.instance_id,
                "machine_id": instance.machine_id,
                "from_state": old_state,
                "to_state": new_state,
                "transition_id": transition.transition_id,
                "trigger": trigger,
                "timestamp": datetime.now(timezone.utc).isoformat()
            })
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error executing transition: {str(e)}")
            return False
    
    async def _execute_entry_actions(self, instance: StateMachineInstance, state_id: str) -> None:
        """Execute entry actions for state"""
        try:
            # Get machine definition
            definition = await self._get_machine_definition(instance.machine_id)
            if not definition:
                return
            
            # Find state
            state = next((s for s in definition.states if s.state_id == state_id), None)
            if not state or not state.entry_actions:
                return
            
            # Execute entry actions
            for action in state.entry_actions:
                await self._execute_action(action, instance)
                
        except Exception as e:
            self.logger.error(f"Error executing entry actions: {str(e)}")
    
    async def _execute_exit_actions(self, instance: StateMachineInstance, state_id: str) -> None:
        """Execute exit actions for state"""
        try:
            # Get machine definition
            definition = await self._get_machine_definition(instance.machine_id)
            if not definition:
                return
            
            # Find state
            state = next((s for s in definition.states if s.state_id == state_id), None)
            if not state or not state.exit_actions:
                return
            
            # Execute exit actions
            for action in state.exit_actions:
                await self._execute_action(action, instance)
                
        except Exception as e:
            self.logger.error(f"Error executing exit actions: {str(e)}")
    
    async def _execute_action(self, action: str, instance: StateMachineInstance) -> None:
        """Execute action"""
        try:
            # Get action handler
            handler = self.action_handlers.get(action)
            if not handler:
                self.logger.warning(f"Action handler not found: {action}")
                return
            
            # Execute action
            if asyncio.iscoroutinefunction(handler):
                await handler(instance)
            else:
                handler(instance)
                
        except Exception as e:
            self.logger.error(f"Error executing action: {str(e)}")
    
    async def _store_instance(self, instance: StateMachineInstance) -> None:
        """Store state machine instance"""
        try:
            # Store in database
            with get_db_session() as db:
                db_instance = StateMachineInstance(
                    instance_id=instance.instance_id,
                    machine_id=instance.machine_id,
                    current_state=instance.current_state,
                    context=instance.context,
                    history=instance.history,
                    created_at=instance.created_at,
                    updated_at=instance.updated_at,
                    completed_at=instance.completed_at,
                    status=instance.status
                )
                db.merge(db_instance)
                db.commit()
            
            # Cache instance
            await self.cache_service.set(
                f"state_machine_instance:{instance.instance_id}",
                instance.to_dict(),
                ttl=3600  # 1 hour
            )
            
        except Exception as e:
            self.logger.error(f"Error storing instance: {str(e)}")
            raise
    
    async def _get_stored_instance(self, instance_id: str) -> Optional[StateMachineInstance]:
        """Get stored state machine instance"""
        try:
            # Check cache first
            cached_instance = await self.cache_service.get(f"state_machine_instance:{instance_id}")
            if cached_instance:
                return StateMachineInstance(**cached_instance)
            
            # Check database
            with get_db_session() as db:
                db_instance = db.query(StateMachineInstance).filter(
                    StateMachineInstance.instance_id == instance_id
                ).first()
                
                if db_instance:
                    return StateMachineInstance(
                        instance_id=db_instance.instance_id,
                        machine_id=db_instance.machine_id,
                        current_state=db_instance.current_state,
                        context=db_instance.context,
                        history=db_instance.history,
                        created_at=db_instance.created_at,
                        updated_at=db_instance.updated_at,
                        completed_at=db_instance.completed_at,
                        status=db_instance.status
                    )
            
            return None
            
        except Exception as e:
            self.logger.error(f"Error getting stored instance: {str(e)}")
            return None
    
    async def _calculate_average_execution_time(self, db, machine_id: str) -> float:
        """Calculate average execution time"""
        try:
            from sqlalchemy import func
            
            result = db.query(
                func.avg(
                    func.extract('epoch', StateMachineInstance.completed_at) - 
                    func.extract('epoch', StateMachineInstance.created_at)
                )
            ).filter(
                StateMachineInstance.machine_id == machine_id,
                StateMachineInstance.status == "completed"
            ).scalar()
            
            return result or 0.0
            
        except Exception as e:
            self.logger.error(f"Error calculating average execution time: {str(e)}")
            return 0.0
    
    async def _get_state_distribution(self, db, machine_id: str) -> Dict[str, int]:
        """Get state distribution"""
        try:
            from sqlalchemy import func
            
            results = db.query(
                StateMachineInstance.current_state,
                func.count(StateMachineInstance.instance_id)
            ).filter(
                StateMachineInstance.machine_id == machine_id,
                StateMachineInstance.status == "active"
            ).group_by(StateMachineInstance.current_state).all()
            
            return {state: count for state, count in results}
            
        except Exception as e:
            self.logger.error(f"Error getting state distribution: {str(e)}")
            return {}
    
    async def health_check(self) -> Dict[str, Any]:
        """Health check for state machine"""
        try:
            return {
                "status": "healthy",
                "service": "workflow_state_machine",
                "registered_machines": len(self.machine_definitions),
                "active_instances": len(self.active_instances),
                "registered_handlers": len(self.state_handlers),
                "registered_guards": len(self.transition_guards),
                "registered_actions": len(self.action_handlers),
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
            
        except Exception as e:
            self.logger.error(f"Error in health check: {str(e)}")
            return {
                "status": "error",
                "service": "workflow_state_machine",
                "error": str(e),
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
    
    async def cleanup(self) -> None:
        """Cleanup state machine resources"""
        try:
            # Cancel all active instances
            for instance_id in list(self.active_instances.keys()):
                await self.cancel_instance(instance_id)
            
            # Clear registries
            self.machine_definitions.clear()
            self.active_instances.clear()
            self.state_handlers.clear()
            self.transition_guards.clear()
            self.action_handlers.clear()
            
            self.logger.info("State machine cleanup completed")
            
        except Exception as e:
            self.logger.error(f"Error during cleanup: {str(e)}")


def create_state_machine() -> WorkflowStateMachine:
    """Create workflow state machine instance"""
    return WorkflowStateMachine()