"""
Hybrid Service: Process Coordinator
Coordinates cross-role processes and manages inter-service communication
"""
import asyncio
import json
import logging
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, Optional, List, Union, Callable
from dataclasses import dataclass, asdict
from enum import Enum
import uuid

from core_platform.database import get_db_session
from core_platform.models.process import ProcessExecution, ProcessStep, ProcessCoordination
from core_platform.cache import CacheService
from core_platform.events import EventBus
from core_platform.monitoring import MetricsCollector
from core_platform.notifications import NotificationService

logger = logging.getLogger(__name__)


class ProcessType(str, Enum):
    """Process coordination types"""
    SI_TO_APP_HANDOFF = "si_to_app_handoff"
    APP_TO_SI_FEEDBACK = "app_to_si_feedback"
    CROSS_ROLE_VALIDATION = "cross_role_validation"
    DATA_SYNCHRONIZATION = "data_synchronization"
    ERROR_ESCALATION = "error_escalation"
    COMPLIANCE_COORDINATION = "compliance_coordination"
    CERTIFICATE_COORDINATION = "certificate_coordination"
    AUDIT_COORDINATION = "audit_coordination"


class CoordinationStatus(str, Enum):
    """Coordination status"""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    WAITING_FOR_SI = "waiting_for_si"
    WAITING_FOR_APP = "waiting_for_app"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    TIMEOUT = "timeout"


class ServiceRole(str, Enum):
    """Service roles"""
    SI = "si"
    APP = "app"
    CORE = "core"
    HYBRID = "hybrid"


@dataclass
class ProcessCoordinationRequest:
    """Process coordination request"""
    coordination_id: str
    process_type: ProcessType
    initiator_role: ServiceRole
    target_role: ServiceRole
    data: Dict[str, Any]
    metadata: Dict[str, Any]
    priority: int
    timeout: int
    retry_count: int
    callback_url: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class ProcessCoordinationResponse:
    """Process coordination response"""
    coordination_id: str
    status: CoordinationStatus
    result: Optional[Dict[str, Any]]
    error: Optional[str]
    started_at: datetime
    completed_at: Optional[datetime]
    duration: float
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class HandoffContext:
    """Context for SI to APP handoff"""
    handoff_id: str
    si_process_id: str
    app_process_id: str
    data_package: Dict[str, Any]
    validation_results: Dict[str, Any]
    certificates: List[Dict[str, Any]]
    metadata: Dict[str, Any]
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class FeedbackContext:
    """Context for APP to SI feedback"""
    feedback_id: str
    original_handoff_id: str
    transmission_status: str
    firs_response: Dict[str, Any]
    error_details: Optional[Dict[str, Any]]
    recommendations: List[str]
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class ValidationContext:
    """Context for cross-role validation"""
    validation_id: str
    validation_type: str
    data_source: ServiceRole
    validation_rules: List[Dict[str, Any]]
    validation_results: Dict[str, Any]
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class ProcessCoordinator:
    """Process coordinator for cross-role operations"""
    
    def __init__(self):
        self.cache_service = CacheService()
        self.event_bus = EventBus()
        self.metrics_collector = MetricsCollector()
        self.notification_service = NotificationService()
        self.logger = logging.getLogger(__name__)
        
        # Active coordinations
        self.active_coordinations: Dict[str, ProcessCoordinationRequest] = {}
        
        # Service registry
        self.service_registry: Dict[ServiceRole, Dict[str, Any]] = {}
        
        # Process handlers
        self.process_handlers: Dict[ProcessType, Callable] = {
            ProcessType.SI_TO_APP_HANDOFF: self._handle_si_to_app_handoff,
            ProcessType.APP_TO_SI_FEEDBACK: self._handle_app_to_si_feedback,
            ProcessType.CROSS_ROLE_VALIDATION: self._handle_cross_role_validation,
            ProcessType.DATA_SYNCHRONIZATION: self._handle_data_synchronization,
            ProcessType.ERROR_ESCALATION: self._handle_error_escalation,
            ProcessType.COMPLIANCE_COORDINATION: self._handle_compliance_coordination,
            ProcessType.CERTIFICATE_COORDINATION: self._handle_certificate_coordination,
            ProcessType.AUDIT_COORDINATION: self._handle_audit_coordination
        }
    
    async def coordinate_process(
        self,
        request: ProcessCoordinationRequest
    ) -> ProcessCoordinationResponse:
        """Coordinate a cross-role process"""
        try:
            # Add to active coordinations
            self.active_coordinations[request.coordination_id] = request
            
            # Emit start event
            await self.event_bus.emit("process_coordination_started", {
                "coordination_id": request.coordination_id,
                "process_type": request.process_type,
                "initiator_role": request.initiator_role,
                "target_role": request.target_role,
                "timestamp": datetime.now(timezone.utc).isoformat()
            })
            
            # Get process handler
            handler = self.process_handlers.get(request.process_type)
            if not handler:
                raise ValueError(f"No handler for process type: {request.process_type}")
            
            # Execute coordination with timeout
            response = await asyncio.wait_for(
                handler(request),
                timeout=request.timeout
            )
            
            # Remove from active coordinations
            if request.coordination_id in self.active_coordinations:
                del self.active_coordinations[request.coordination_id]
            
            # Store coordination result
            await self._store_coordination_result(request, response)
            
            # Emit completion event
            await self.event_bus.emit("process_coordination_completed", {
                "coordination_id": request.coordination_id,
                "status": response.status,
                "duration": response.duration,
                "timestamp": datetime.now(timezone.utc).isoformat()
            })
            
            return response
            
        except asyncio.TimeoutError:
            # Handle timeout
            response = ProcessCoordinationResponse(
                coordination_id=request.coordination_id,
                status=CoordinationStatus.TIMEOUT,
                result=None,
                error="Process coordination timeout",
                started_at=datetime.now(timezone.utc),
                completed_at=datetime.now(timezone.utc),
                duration=request.timeout
            )
            
            # Remove from active coordinations
            if request.coordination_id in self.active_coordinations:
                del self.active_coordinations[request.coordination_id]
            
            return response
            
        except Exception as e:
            self.logger.error(f"Error in process coordination: {str(e)}")
            
            # Create error response
            response = ProcessCoordinationResponse(
                coordination_id=request.coordination_id,
                status=CoordinationStatus.FAILED,
                result=None,
                error=str(e),
                started_at=datetime.now(timezone.utc),
                completed_at=datetime.now(timezone.utc),
                duration=0.0
            )
            
            # Remove from active coordinations
            if request.coordination_id in self.active_coordinations:
                del self.active_coordinations[request.coordination_id]
            
            return response
    
    async def initiate_si_to_app_handoff(
        self,
        si_process_id: str,
        data_package: Dict[str, Any],
        validation_results: Dict[str, Any],
        certificates: List[Dict[str, Any]],
        metadata: Dict[str, Any]
    ) -> HandoffContext:
        """Initiate SI to APP handoff"""
        try:
            handoff_id = str(uuid.uuid4())
            
            # Create handoff context
            handoff_context = HandoffContext(
                handoff_id=handoff_id,
                si_process_id=si_process_id,
                app_process_id="",  # Will be set by APP
                data_package=data_package,
                validation_results=validation_results,
                certificates=certificates,
                metadata=metadata
            )
            
            # Create coordination request
            request = ProcessCoordinationRequest(
                coordination_id=handoff_id,
                process_type=ProcessType.SI_TO_APP_HANDOFF,
                initiator_role=ServiceRole.SI,
                target_role=ServiceRole.APP,
                data=handoff_context.to_dict(),
                metadata=metadata,
                priority=1,
                timeout=300,  # 5 minutes
                retry_count=3
            )
            
            # Execute coordination
            response = await self.coordinate_process(request)
            
            if response.status == CoordinationStatus.COMPLETED:
                # Update handoff context with APP process ID
                if response.result:
                    handoff_context.app_process_id = response.result.get("app_process_id", "")
            
            return handoff_context
            
        except Exception as e:
            self.logger.error(f"Error initiating SI to APP handoff: {str(e)}")
            raise
    
    async def submit_app_to_si_feedback(
        self,
        original_handoff_id: str,
        transmission_status: str,
        firs_response: Dict[str, Any],
        error_details: Optional[Dict[str, Any]] = None,
        recommendations: Optional[List[str]] = None
    ) -> FeedbackContext:
        """Submit APP to SI feedback"""
        try:
            feedback_id = str(uuid.uuid4())
            
            # Create feedback context
            feedback_context = FeedbackContext(
                feedback_id=feedback_id,
                original_handoff_id=original_handoff_id,
                transmission_status=transmission_status,
                firs_response=firs_response,
                error_details=error_details,
                recommendations=recommendations or []
            )
            
            # Create coordination request
            request = ProcessCoordinationRequest(
                coordination_id=feedback_id,
                process_type=ProcessType.APP_TO_SI_FEEDBACK,
                initiator_role=ServiceRole.APP,
                target_role=ServiceRole.SI,
                data=feedback_context.to_dict(),
                metadata={"original_handoff_id": original_handoff_id},
                priority=1,
                timeout=120,  # 2 minutes
                retry_count=2
            )
            
            # Execute coordination
            response = await self.coordinate_process(request)
            
            return feedback_context
            
        except Exception as e:
            self.logger.error(f"Error submitting APP to SI feedback: {str(e)}")
            raise
    
    async def coordinate_cross_role_validation(
        self,
        validation_type: str,
        data_source: ServiceRole,
        validation_rules: List[Dict[str, Any]],
        data: Dict[str, Any]
    ) -> ValidationContext:
        """Coordinate cross-role validation"""
        try:
            validation_id = str(uuid.uuid4())
            
            # Create validation context
            validation_context = ValidationContext(
                validation_id=validation_id,
                validation_type=validation_type,
                data_source=data_source,
                validation_rules=validation_rules,
                validation_results={}
            )
            
            # Create coordination request
            request = ProcessCoordinationRequest(
                coordination_id=validation_id,
                process_type=ProcessType.CROSS_ROLE_VALIDATION,
                initiator_role=ServiceRole.HYBRID,
                target_role=ServiceRole.HYBRID,
                data={
                    "validation_context": validation_context.to_dict(),
                    "data_to_validate": data
                },
                metadata={"validation_type": validation_type},
                priority=2,
                timeout=180,  # 3 minutes
                retry_count=2
            )
            
            # Execute coordination
            response = await self.coordinate_process(request)
            
            if response.status == CoordinationStatus.COMPLETED and response.result:
                validation_context.validation_results = response.result.get("validation_results", {})
            
            return validation_context
            
        except Exception as e:
            self.logger.error(f"Error coordinating cross-role validation: {str(e)}")
            raise
    
    async def get_coordination_status(self, coordination_id: str) -> Optional[ProcessCoordinationResponse]:
        """Get coordination status"""
        try:
            # Check active coordinations
            if coordination_id in self.active_coordinations:
                return ProcessCoordinationResponse(
                    coordination_id=coordination_id,
                    status=CoordinationStatus.IN_PROGRESS,
                    result=None,
                    error=None,
                    started_at=datetime.now(timezone.utc),
                    completed_at=None,
                    duration=0.0
                )
            
            # Check stored results
            return await self._get_stored_coordination_result(coordination_id)
            
        except Exception as e:
            self.logger.error(f"Error getting coordination status: {str(e)}")
            return None
    
    async def cancel_coordination(self, coordination_id: str) -> bool:
        """Cancel active coordination"""
        try:
            if coordination_id in self.active_coordinations:
                del self.active_coordinations[coordination_id]
                
                # Emit cancellation event
                await self.event_bus.emit("process_coordination_cancelled", {
                    "coordination_id": coordination_id,
                    "timestamp": datetime.now(timezone.utc).isoformat()
                })
                
                return True
            
            return False
            
        except Exception as e:
            self.logger.error(f"Error cancelling coordination: {str(e)}")
            return False
    
    async def list_active_coordinations(self) -> List[Dict[str, Any]]:
        """List active coordinations"""
        try:
            active_list = []
            
            for coordination_id, request in self.active_coordinations.items():
                active_list.append({
                    "coordination_id": coordination_id,
                    "process_type": request.process_type,
                    "initiator_role": request.initiator_role,
                    "target_role": request.target_role,
                    "priority": request.priority,
                    "timeout": request.timeout
                })
            
            return active_list
            
        except Exception as e:
            self.logger.error(f"Error listing active coordinations: {str(e)}")
            return []
    
    # Process handlers
    
    async def _handle_si_to_app_handoff(self, request: ProcessCoordinationRequest) -> ProcessCoordinationResponse:
        """Handle SI to APP handoff"""
        start_time = datetime.now(timezone.utc)
        
        try:
            handoff_context = HandoffContext(**request.data)
            
            # Validate handoff data
            validation_result = await self._validate_handoff_data(handoff_context)
            if not validation_result["valid"]:
                raise ValueError(f"Invalid handoff data: {validation_result['errors']}")
            
            # Get APP service
            app_service = await self._get_service(ServiceRole.APP, "transmission_service")
            
            # Initiate APP processing
            app_result = await app_service.initiate_processing(
                handoff_context.data_package,
                handoff_context.validation_results,
                handoff_context.certificates,
                handoff_context.metadata
            )
            
            # Create response
            response = ProcessCoordinationResponse(
                coordination_id=request.coordination_id,
                status=CoordinationStatus.COMPLETED,
                result={
                    "app_process_id": app_result.get("process_id"),
                    "handoff_status": "successful",
                    "app_response": app_result
                },
                error=None,
                started_at=start_time,
                completed_at=datetime.now(timezone.utc),
                duration=(datetime.now(timezone.utc) - start_time).total_seconds()
            )
            
            return response
            
        except Exception as e:
            self.logger.error(f"Error handling SI to APP handoff: {str(e)}")
            
            return ProcessCoordinationResponse(
                coordination_id=request.coordination_id,
                status=CoordinationStatus.FAILED,
                result=None,
                error=str(e),
                started_at=start_time,
                completed_at=datetime.now(timezone.utc),
                duration=(datetime.now(timezone.utc) - start_time).total_seconds()
            )
    
    async def _handle_app_to_si_feedback(self, request: ProcessCoordinationRequest) -> ProcessCoordinationResponse:
        """Handle APP to SI feedback"""
        start_time = datetime.now(timezone.utc)
        
        try:
            feedback_context = FeedbackContext(**request.data)
            
            # Get SI service
            si_service = await self._get_service(ServiceRole.SI, "irn_service")
            
            # Submit feedback to SI
            si_result = await si_service.process_feedback(
                feedback_context.original_handoff_id,
                feedback_context.transmission_status,
                feedback_context.firs_response,
                feedback_context.error_details,
                feedback_context.recommendations
            )
            
            # Create response
            response = ProcessCoordinationResponse(
                coordination_id=request.coordination_id,
                status=CoordinationStatus.COMPLETED,
                result={
                    "feedback_processed": True,
                    "si_response": si_result
                },
                error=None,
                started_at=start_time,
                completed_at=datetime.now(timezone.utc),
                duration=(datetime.now(timezone.utc) - start_time).total_seconds()
            )
            
            return response
            
        except Exception as e:
            self.logger.error(f"Error handling APP to SI feedback: {str(e)}")
            
            return ProcessCoordinationResponse(
                coordination_id=request.coordination_id,
                status=CoordinationStatus.FAILED,
                result=None,
                error=str(e),
                started_at=start_time,
                completed_at=datetime.now(timezone.utc),
                duration=(datetime.now(timezone.utc) - start_time).total_seconds()
            )
    
    async def _handle_cross_role_validation(self, request: ProcessCoordinationRequest) -> ProcessCoordinationResponse:
        """Handle cross-role validation"""
        start_time = datetime.now(timezone.utc)
        
        try:
            validation_context = ValidationContext(**request.data["validation_context"])
            data_to_validate = request.data["data_to_validate"]
            
            # Execute validation rules
            validation_results = {}
            
            for rule in validation_context.validation_rules:
                rule_result = await self._execute_validation_rule(rule, data_to_validate)
                validation_results[rule["rule_id"]] = rule_result
            
            # Determine overall validation status
            overall_valid = all(result["valid"] for result in validation_results.values())
            
            # Create response
            response = ProcessCoordinationResponse(
                coordination_id=request.coordination_id,
                status=CoordinationStatus.COMPLETED,
                result={
                    "validation_results": validation_results,
                    "overall_valid": overall_valid
                },
                error=None,
                started_at=start_time,
                completed_at=datetime.now(timezone.utc),
                duration=(datetime.now(timezone.utc) - start_time).total_seconds()
            )
            
            return response
            
        except Exception as e:
            self.logger.error(f"Error handling cross-role validation: {str(e)}")
            
            return ProcessCoordinationResponse(
                coordination_id=request.coordination_id,
                status=CoordinationStatus.FAILED,
                result=None,
                error=str(e),
                started_at=start_time,
                completed_at=datetime.now(timezone.utc),
                duration=(datetime.now(timezone.utc) - start_time).total_seconds()
            )
    
    async def _handle_data_synchronization(self, request: ProcessCoordinationRequest) -> ProcessCoordinationResponse:
        """Handle data synchronization"""
        start_time = datetime.now(timezone.utc)
        
        try:
            # Get synchronization service
            sync_service = await self._get_service(ServiceRole.HYBRID, "data_synchronization")
            
            # Execute synchronization
            sync_result = await sync_service.synchronize_data(
                request.data,
                request.metadata
            )
            
            # Create response
            response = ProcessCoordinationResponse(
                coordination_id=request.coordination_id,
                status=CoordinationStatus.COMPLETED,
                result=sync_result,
                error=None,
                started_at=start_time,
                completed_at=datetime.now(timezone.utc),
                duration=(datetime.now(timezone.utc) - start_time).total_seconds()
            )
            
            return response
            
        except Exception as e:
            self.logger.error(f"Error handling data synchronization: {str(e)}")
            
            return ProcessCoordinationResponse(
                coordination_id=request.coordination_id,
                status=CoordinationStatus.FAILED,
                result=None,
                error=str(e),
                started_at=start_time,
                completed_at=datetime.now(timezone.utc),
                duration=(datetime.now(timezone.utc) - start_time).total_seconds()
            )
    
    async def _handle_error_escalation(self, request: ProcessCoordinationRequest) -> ProcessCoordinationResponse:
        """Handle error escalation"""
        start_time = datetime.now(timezone.utc)
        
        try:
            # Get error management service
            error_service = await self._get_service(ServiceRole.HYBRID, "error_management")
            
            # Escalate error
            escalation_result = await error_service.escalate_error(
                request.data,
                request.metadata
            )
            
            # Create response
            response = ProcessCoordinationResponse(
                coordination_id=request.coordination_id,
                status=CoordinationStatus.COMPLETED,
                result=escalation_result,
                error=None,
                started_at=start_time,
                completed_at=datetime.now(timezone.utc),
                duration=(datetime.now(timezone.utc) - start_time).total_seconds()
            )
            
            return response
            
        except Exception as e:
            self.logger.error(f"Error handling error escalation: {str(e)}")
            
            return ProcessCoordinationResponse(
                coordination_id=request.coordination_id,
                status=CoordinationStatus.FAILED,
                result=None,
                error=str(e),
                started_at=start_time,
                completed_at=datetime.now(timezone.utc),
                duration=(datetime.now(timezone.utc) - start_time).total_seconds()
            )
    
    async def _handle_compliance_coordination(self, request: ProcessCoordinationRequest) -> ProcessCoordinationResponse:
        """Handle compliance coordination"""
        start_time = datetime.now(timezone.utc)
        
        try:
            # Get compliance service
            compliance_service = await self._get_service(ServiceRole.HYBRID, "compliance_coordination")
            
            # Execute compliance coordination
            compliance_result = await compliance_service.coordinate_compliance(
                request.data,
                request.metadata
            )
            
            # Create response
            response = ProcessCoordinationResponse(
                coordination_id=request.coordination_id,
                status=CoordinationStatus.COMPLETED,
                result=compliance_result,
                error=None,
                started_at=start_time,
                completed_at=datetime.now(timezone.utc),
                duration=(datetime.now(timezone.utc) - start_time).total_seconds()
            )
            
            return response
            
        except Exception as e:
            self.logger.error(f"Error handling compliance coordination: {str(e)}")
            
            return ProcessCoordinationResponse(
                coordination_id=request.coordination_id,
                status=CoordinationStatus.FAILED,
                result=None,
                error=str(e),
                started_at=start_time,
                completed_at=datetime.now(timezone.utc),
                duration=(datetime.now(timezone.utc) - start_time).total_seconds()
            )
    
    async def _handle_certificate_coordination(self, request: ProcessCoordinationRequest) -> ProcessCoordinationResponse:
        """Handle certificate coordination"""
        start_time = datetime.now(timezone.utc)
        
        try:
            # Get certificate service
            cert_service = await self._get_service(ServiceRole.HYBRID, "certificate_coordination")
            
            # Execute certificate coordination
            cert_result = await cert_service.coordinate_certificates(
                request.data,
                request.metadata
            )
            
            # Create response
            response = ProcessCoordinationResponse(
                coordination_id=request.coordination_id,
                status=CoordinationStatus.COMPLETED,
                result=cert_result,
                error=None,
                started_at=start_time,
                completed_at=datetime.now(timezone.utc),
                duration=(datetime.now(timezone.utc) - start_time).total_seconds()
            )
            
            return response
            
        except Exception as e:
            self.logger.error(f"Error handling certificate coordination: {str(e)}")
            
            return ProcessCoordinationResponse(
                coordination_id=request.coordination_id,
                status=CoordinationStatus.FAILED,
                result=None,
                error=str(e),
                started_at=start_time,
                completed_at=datetime.now(timezone.utc),
                duration=(datetime.now(timezone.utc) - start_time).total_seconds()
            )
    
    async def _handle_audit_coordination(self, request: ProcessCoordinationRequest) -> ProcessCoordinationResponse:
        """Handle audit coordination"""
        start_time = datetime.now(timezone.utc)
        
        try:
            # Get audit service
            audit_service = await self._get_service(ServiceRole.CORE, "audit_service")
            
            # Execute audit coordination
            audit_result = await audit_service.coordinate_audit(
                request.data,
                request.metadata
            )
            
            # Create response
            response = ProcessCoordinationResponse(
                coordination_id=request.coordination_id,
                status=CoordinationStatus.COMPLETED,
                result=audit_result,
                error=None,
                started_at=start_time,
                completed_at=datetime.now(timezone.utc),
                duration=(datetime.now(timezone.utc) - start_time).total_seconds()
            )
            
            return response
            
        except Exception as e:
            self.logger.error(f"Error handling audit coordination: {str(e)}")
            
            return ProcessCoordinationResponse(
                coordination_id=request.coordination_id,
                status=CoordinationStatus.FAILED,
                result=None,
                error=str(e),
                started_at=start_time,
                completed_at=datetime.now(timezone.utc),
                duration=(datetime.now(timezone.utc) - start_time).total_seconds()
            )
    
    # Helper methods
    
    async def _validate_handoff_data(self, handoff_context: HandoffContext) -> Dict[str, Any]:
        """Validate handoff data"""
        try:
            errors = []
            
            # Check required fields
            if not handoff_context.data_package:
                errors.append("Data package is required")
            
            if not handoff_context.validation_results:
                errors.append("Validation results are required")
            
            # Check data package structure
            if handoff_context.data_package:
                required_fields = ["invoice_data", "irn", "qr_code"]
                for field in required_fields:
                    if field not in handoff_context.data_package:
                        errors.append(f"Missing required field: {field}")
            
            return {
                "valid": len(errors) == 0,
                "errors": errors
            }
            
        except Exception as e:
            self.logger.error(f"Error validating handoff data: {str(e)}")
            return {
                "valid": False,
                "errors": [str(e)]
            }
    
    async def _execute_validation_rule(self, rule: Dict[str, Any], data: Dict[str, Any]) -> Dict[str, Any]:
        """Execute validation rule"""
        try:
            rule_type = rule.get("type")
            rule_config = rule.get("config", {})
            
            if rule_type == "required_field":
                field_name = rule_config.get("field_name")
                return {
                    "valid": field_name in data and data[field_name] is not None,
                    "message": f"Field {field_name} is required"
                }
            
            elif rule_type == "data_type":
                field_name = rule_config.get("field_name")
                expected_type = rule_config.get("expected_type")
                
                if field_name not in data:
                    return {"valid": False, "message": f"Field {field_name} not found"}
                
                actual_type = type(data[field_name]).__name__
                return {
                    "valid": actual_type == expected_type,
                    "message": f"Field {field_name} should be {expected_type}, got {actual_type}"
                }
            
            elif rule_type == "value_range":
                field_name = rule_config.get("field_name")
                min_value = rule_config.get("min_value")
                max_value = rule_config.get("max_value")
                
                if field_name not in data:
                    return {"valid": False, "message": f"Field {field_name} not found"}
                
                value = data[field_name]
                valid = min_value <= value <= max_value
                return {
                    "valid": valid,
                    "message": f"Field {field_name} should be between {min_value} and {max_value}"
                }
            
            else:
                return {
                    "valid": False,
                    "message": f"Unknown validation rule type: {rule_type}"
                }
                
        except Exception as e:
            self.logger.error(f"Error executing validation rule: {str(e)}")
            return {
                "valid": False,
                "message": str(e)
            }
    
    async def _get_service(self, role: ServiceRole, service_name: str) -> Any:
        """Get service instance"""
        try:
            # This would integrate with the actual service registry
            # For now, return a mock service
            return MockService()
            
        except Exception as e:
            self.logger.error(f"Error getting service: {str(e)}")
            raise
    
    async def _store_coordination_result(
        self,
        request: ProcessCoordinationRequest,
        response: ProcessCoordinationResponse
    ) -> None:
        """Store coordination result"""
        try:
            # Store in database
            with get_db_session() as db:
                db_coordination = ProcessCoordination(
                    coordination_id=request.coordination_id,
                    process_type=request.process_type,
                    initiator_role=request.initiator_role,
                    target_role=request.target_role,
                    request_data=request.to_dict(),
                    response_data=response.to_dict(),
                    status=response.status,
                    created_at=response.started_at,
                    completed_at=response.completed_at
                )
                db.add(db_coordination)
                db.commit()
            
            # Cache result
            await self.cache_service.set(
                f"process_coordination:{request.coordination_id}",
                response.to_dict(),
                ttl=3600  # 1 hour
            )
            
        except Exception as e:
            self.logger.error(f"Error storing coordination result: {str(e)}")
            raise
    
    async def _get_stored_coordination_result(self, coordination_id: str) -> Optional[ProcessCoordinationResponse]:
        """Get stored coordination result"""
        try:
            # Check cache first
            cached_result = await self.cache_service.get(f"process_coordination:{coordination_id}")
            if cached_result:
                return ProcessCoordinationResponse(**cached_result)
            
            # Check database
            with get_db_session() as db:
                db_coordination = db.query(ProcessCoordination).filter(
                    ProcessCoordination.coordination_id == coordination_id
                ).first()
                
                if db_coordination:
                    return ProcessCoordinationResponse(**db_coordination.response_data)
            
            return None
            
        except Exception as e:
            self.logger.error(f"Error getting stored coordination result: {str(e)}")
            return None
    
    async def health_check(self) -> Dict[str, Any]:
        """Health check for process coordinator"""
        try:
            return {
                "status": "healthy",
                "service": "process_coordinator",
                "active_coordinations": len(self.active_coordinations),
                "registered_handlers": len(self.process_handlers),
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
            
        except Exception as e:
            self.logger.error(f"Error in health check: {str(e)}")
            return {
                "status": "error",
                "service": "process_coordinator",
                "error": str(e),
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
    
    async def cleanup(self) -> None:
        """Cleanup coordinator resources"""
        try:
            # Cancel all active coordinations
            for coordination_id in list(self.active_coordinations.keys()):
                await self.cancel_coordination(coordination_id)
            
            # Clear registries
            self.active_coordinations.clear()
            self.service_registry.clear()
            
            self.logger.info("Process coordinator cleanup completed")
            
        except Exception as e:
            self.logger.error(f"Error during cleanup: {str(e)}")


class MockService:
    """Mock service for testing"""
    
    async def initiate_processing(self, data_package, validation_results, certificates, metadata):
        """Mock processing initiation"""
        return {"process_id": str(uuid.uuid4()), "status": "initiated"}
    
    async def process_feedback(self, handoff_id, status, response, errors, recommendations):
        """Mock feedback processing"""
        return {"feedback_processed": True, "status": "processed"}
    
    async def synchronize_data(self, data, metadata):
        """Mock data synchronization"""
        return {"synchronized": True, "status": "completed"}
    
    async def escalate_error(self, data, metadata):
        """Mock error escalation"""
        return {"escalated": True, "status": "escalated"}
    
    async def coordinate_compliance(self, data, metadata):
        """Mock compliance coordination"""
        return {"compliance_coordinated": True, "status": "coordinated"}
    
    async def coordinate_certificates(self, data, metadata):
        """Mock certificate coordination"""
        return {"certificates_coordinated": True, "status": "coordinated"}
    
    async def coordinate_audit(self, data, metadata):
        """Mock audit coordination"""
        return {"audit_coordinated": True, "status": "coordinated"}


def create_process_coordinator() -> ProcessCoordinator:
    """Create process coordinator instance"""
    return ProcessCoordinator()