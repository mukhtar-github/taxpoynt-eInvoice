"""
FIRS Core Invoice Processor

Enhanced invoice lifecycle management with comprehensive compliance tracking,
Nigerian regulatory adherence, and advanced error handling.
"""

from typing import Dict, Any, List, Optional, Union
from datetime import datetime, date, timedelta
from enum import Enum
from dataclasses import dataclass, asdict
import logging
import json
import asyncio
from uuid import uuid4

from .firs_api_client import firs_service
from .audit_service import AuditService
from .firs_monitoring import firs_core_monitor, ComplianceEventType, MonitoringLevel
from app.utils.logger import get_logger

logger = get_logger(__name__)


class InvoiceProcessingStage(str, Enum):
    """Invoice processing lifecycle stages"""
    INITIATED = "initiated"
    STRUCTURED = "invoice_structured"
    IRN_VALIDATED = "irn_validated"
    INVOICE_VALIDATED = "invoice_validated"
    SIGNED = "invoice_signed"
    TRANSMITTED = "transmitted"
    CONFIRMED = "confirmed"
    DOWNLOADED = "downloaded"
    COMPLETED = "completed"
    PARTIALLY_COMPLETED = "partially_completed"
    FAILED = "failed"
    ERROR = "error"


class ComplianceLevel(str, Enum):
    """Nigerian compliance levels"""
    FULL_COMPLIANCE = "full_compliance"
    PARTIAL_COMPLIANCE = "partial_compliance"
    NON_COMPLIANCE = "non_compliance"
    PENDING_REVIEW = "pending_review"


@dataclass
class ProcessingStep:
    """Individual processing step result"""
    step_name: str
    stage: InvoiceProcessingStage
    timestamp: datetime
    success: bool
    response: Dict[str, Any]
    duration_ms: float
    compliance_flags: List[str]
    error_details: Optional[Dict[str, Any]] = None
    retry_attempts: int = 0


@dataclass
class ComplianceAssessment:
    """Nigerian compliance assessment result"""
    overall_level: ComplianceLevel
    firs_compliance: bool
    ndpr_compliance: bool
    tax_accuracy: bool
    data_protection: bool
    audit_trail_complete: bool
    violations: List[str]
    recommendations: List[str]
    score: float


@dataclass
class EnhancedProcessingResult:
    """Enhanced processing result with compliance tracking"""
    invoice_reference: str
    irn: Optional[str]
    processing_id: str
    stage: InvoiceProcessingStage
    success: bool
    steps: List[ProcessingStep]
    compliance_assessment: ComplianceAssessment
    errors: List[Dict[str, Any]]
    warnings: List[str]
    total_processing_time_ms: float
    nigerian_requirements_met: bool
    firs_submission_status: str
    retention_period_years: int
    created_at: datetime
    completed_at: Optional[datetime] = None
    metadata: Optional[Dict[str, Any]] = None


class FIRSCoreInvoiceProcessor:
    """
    Enhanced FIRS invoice processor with comprehensive compliance tracking.
    
    Manages the complete invoice lifecycle with Nigerian regulatory compliance,
    comprehensive audit trails, and enhanced error handling.
    """
    
    def __init__(self):
        self.firs_service = firs_service
        self.audit_service = AuditService()
        self.monitor = firs_core_monitor
        
        # Nigerian compliance requirements
        self.retention_years = 7  # Nigerian tax law requirement
        self.max_retry_attempts = 3
        self.processing_timeout_minutes = 30
        
        logger.info("FIRS Core Invoice Processor initialized with enhanced compliance tracking")
    
    async def process_enhanced_invoice_lifecycle(
        self,
        invoice_reference: str,
        customer_data: Dict[str, Any],
        invoice_lines: List[Dict[str, Any]],
        organization_id: str,
        user_id: Optional[str] = None,
        issue_date: Optional[date] = None,
        due_date: Optional[date] = None,
        compliance_context: Optional[Dict[str, Any]] = None,
        **kwargs
    ) -> EnhancedProcessingResult:
        """
        Process complete invoice lifecycle with enhanced compliance tracking.
        
        Args:
            invoice_reference: Unique invoice reference number
            customer_data: Customer/buyer information
            invoice_lines: List of invoice line items
            organization_id: Organization ID for compliance tracking
            user_id: User ID for audit trail
            issue_date: Invoice issue date
            due_date: Invoice due date
            compliance_context: Additional compliance context
            **kwargs: Additional invoice parameters
            
        Returns:
            Enhanced processing result with compliance assessment
        """
        processing_id = str(uuid4())
        start_time = datetime.utcnow()
        steps = []
        errors = []
        warnings = []
        
        # Initialize processing result
        result = EnhancedProcessingResult(
            invoice_reference=invoice_reference,
            irn=None,
            processing_id=processing_id,
            stage=InvoiceProcessingStage.INITIATED,
            success=False,
            steps=steps,
            compliance_assessment=ComplianceAssessment(
                overall_level=ComplianceLevel.PENDING_REVIEW,
                firs_compliance=False,
                ndpr_compliance=False,
                tax_accuracy=False,
                data_protection=False,
                audit_trail_complete=False,
                violations=[],
                recommendations=[],
                score=0.0
            ),
            errors=errors,
            warnings=warnings,
            total_processing_time_ms=0.0,
            nigerian_requirements_met=False,
            firs_submission_status="initiated",
            retention_period_years=self.retention_years,
            created_at=start_time,
            metadata=compliance_context or {}
        )
        
        try:
            logger.info(f"Starting enhanced invoice lifecycle for: {invoice_reference} "
                       f"[ProcessingID: {processing_id}, Org: {organization_id}]")
            
            # Record audit event for processing initiation
            await self.audit_service.log_audit_event(
                event_type="invoice_processing_started",
                event_description=f"Invoice processing initiated for {invoice_reference}",
                outcome="success",
                user_id=user_id,
                organization_id=organization_id,
                resource_type="invoice",
                resource_id=invoice_reference,
                additional_data={
                    "processing_id": processing_id,
                    "customer_tin": customer_data.get("tin"),
                    "invoice_lines_count": len(invoice_lines)
                }
            )
            
            # Step 1: Build complete invoice structure
            step_result = await self._execute_processing_step(
                "build_invoice_structure",
                InvoiceProcessingStage.STRUCTURED,
                lambda: self.firs_service.build_complete_invoice(
                    invoice_reference=invoice_reference,
                    customer_data=customer_data,
                    invoice_lines=invoice_lines,
                    issue_date=issue_date,
                    due_date=due_date,
                    **kwargs
                ),
                organization_id=organization_id,
                user_id=user_id
            )
            steps.append(step_result)
            
            if not step_result.success:
                result.stage = InvoiceProcessingStage.FAILED
                errors.append(step_result.error_details)
                return result
            
            invoice_data = step_result.response
            result.irn = invoice_data.get("irn")
            result.stage = InvoiceProcessingStage.STRUCTURED
            
            # Step 2: Validate IRN format and compliance
            step_result = await self._execute_processing_step(
                "validate_irn",
                InvoiceProcessingStage.IRN_VALIDATED,
                lambda: self.firs_service.validate_irn(
                    business_id=self.firs_service.business_id,
                    invoice_reference=invoice_reference,
                    irn=result.irn
                ),
                organization_id=organization_id,
                user_id=user_id
            )
            steps.append(step_result)
            
            if not step_result.success:
                warnings.append(f"IRN validation issues: {step_result.error_details}")
                # Continue processing despite IRN validation warnings
            else:
                result.stage = InvoiceProcessingStage.IRN_VALIDATED
            
            # Step 3: Validate complete invoice
            step_result = await self._execute_processing_step(
                "validate_invoice",
                InvoiceProcessingStage.INVOICE_VALIDATED,
                lambda: self.firs_service.validate_complete_invoice(invoice_data),
                organization_id=organization_id,
                user_id=user_id,
                required=True
            )
            steps.append(step_result)
            
            if not step_result.success:
                result.stage = InvoiceProcessingStage.FAILED
                errors.append(step_result.error_details)
                return result
            
            result.stage = InvoiceProcessingStage.INVOICE_VALIDATED
            
            # Step 4: Sign invoice
            step_result = await self._execute_processing_step(
                "sign_invoice",
                InvoiceProcessingStage.SIGNED,
                lambda: self.firs_service.sign_invoice(invoice_data),
                organization_id=organization_id,
                user_id=user_id,
                required=True
            )
            steps.append(step_result)
            
            if not step_result.success:
                result.stage = InvoiceProcessingStage.FAILED
                errors.append(step_result.error_details)
                return result
            
            result.stage = InvoiceProcessingStage.SIGNED
            
            # Step 5: Transmit invoice to FIRS
            step_result = await self._execute_processing_step(
                "transmit_invoice",
                InvoiceProcessingStage.TRANSMITTED,
                lambda: self.firs_service.transmit_invoice(result.irn),
                organization_id=organization_id,
                user_id=user_id,
                required=True
            )
            steps.append(step_result)
            
            if not step_result.success:
                result.stage = InvoiceProcessingStage.FAILED
                errors.append(step_result.error_details)
                return result
            
            result.stage = InvoiceProcessingStage.TRANSMITTED
            result.firs_submission_status = "transmitted"
            
            # Step 6: Confirm invoice submission
            step_result = await self._execute_processing_step(
                "confirm_invoice",
                InvoiceProcessingStage.CONFIRMED,
                lambda: self.firs_service.confirm_invoice(result.irn),
                organization_id=organization_id,
                user_id=user_id,
                required=False
            )
            steps.append(step_result)
            
            if not step_result.success:
                warnings.append(f"Invoice confirmation issues: {step_result.error_details}")
            else:
                result.stage = InvoiceProcessingStage.CONFIRMED
                result.firs_submission_status = "confirmed"
            
            # Step 7: Download invoice (optional)
            step_result = await self._execute_processing_step(
                "download_invoice",
                InvoiceProcessingStage.DOWNLOADED,
                lambda: self.firs_service.download_invoice(result.irn),
                organization_id=organization_id,
                user_id=user_id,
                required=False
            )
            steps.append(step_result)
            
            if not step_result.success:
                warnings.append(f"Invoice download issues: {step_result.error_details}")
            else:
                result.stage = InvoiceProcessingStage.DOWNLOADED
            
            # Assess final processing status
            result.success = self._assess_processing_success(steps, errors)
            if result.success:
                result.stage = InvoiceProcessingStage.COMPLETED
                result.firs_submission_status = "completed"
            elif result.stage in [InvoiceProcessingStage.TRANSMITTED, InvoiceProcessingStage.SIGNED]:
                result.stage = InvoiceProcessingStage.PARTIALLY_COMPLETED
                result.success = True  # Partial success
            
            # Perform compliance assessment
            result.compliance_assessment = await self._assess_nigerian_compliance(
                result, invoice_data, customer_data, organization_id
            )
            
            result.nigerian_requirements_met = (
                result.compliance_assessment.overall_level != ComplianceLevel.NON_COMPLIANCE
            )
            
            logger.info(f"Invoice lifecycle completed for {invoice_reference}: {result.stage} "
                       f"[Success: {result.success}, Compliance: {result.compliance_assessment.overall_level}]")
            
        except Exception as e:
            logger.error(f"Error processing invoice lifecycle: {str(e)}", exc_info=True)
            result.stage = InvoiceProcessingStage.ERROR
            result.success = False
            errors.append({
                "type": "processing_error",
                "message": str(e),
                "timestamp": datetime.utcnow().isoformat()
            })
            
            # Record error in audit trail
            await self.audit_service.log_audit_event(
                event_type="invoice_processing_error",
                event_description=f"Invoice processing failed for {invoice_reference}",
                outcome="failure",
                user_id=user_id,
                organization_id=organization_id,
                resource_type="invoice",
                resource_id=invoice_reference,
                additional_data={"error": str(e), "processing_id": processing_id}
            )
        
        finally:
            # Calculate total processing time
            end_time = datetime.utcnow()
            result.completed_at = end_time
            result.total_processing_time_ms = (end_time - start_time).total_seconds() * 1000
            
            # Record compliance event
            await self._record_processing_compliance_event(
                result, organization_id, user_id
            )
        
        return result
    
    async def _execute_processing_step(
        self,
        step_name: str,
        stage: InvoiceProcessingStage,
        operation: callable,
        organization_id: str,
        user_id: Optional[str] = None,
        required: bool = True,
        retry_attempts: int = None
    ) -> ProcessingStep:
        """Execute individual processing step with monitoring and compliance tracking."""
        retry_attempts = retry_attempts or self.max_retry_attempts
        start_time = datetime.utcnow()
        step_start = time.time()
        
        for attempt in range(retry_attempts + 1):
            try:
                logger.info(f"Executing step: {step_name} (attempt {attempt + 1}/{retry_attempts + 1})")
                
                # Execute operation with monitoring
                response = await operation()
                
                # Check response success
                success = self._is_response_successful(response)
                
                step_end = time.time()
                duration_ms = (step_end - step_start) * 1000
                
                # Determine compliance flags
                compliance_flags = self._get_step_compliance_flags(step_name, response)
                
                # Create successful step result
                step_result = ProcessingStep(
                    step_name=step_name,
                    stage=stage,
                    timestamp=start_time,
                    success=success,
                    response=response,
                    duration_ms=duration_ms,
                    compliance_flags=compliance_flags,
                    retry_attempts=attempt
                )
                
                if success:
                    logger.info(f"Step {step_name} completed successfully in {duration_ms:.2f}ms")
                    return step_result
                elif not required:
                    logger.warning(f"Optional step {step_name} failed but continuing processing")
                    step_result.error_details = {
                        "type": "optional_step_failure",
                        "message": f"Optional step failed: {response.get('message', 'Unknown error')}",
                        "response": response
                    }
                    return step_result
                elif attempt < retry_attempts:
                    logger.warning(f"Step {step_name} failed, retrying... (attempt {attempt + 1})")
                    await asyncio.sleep(2 ** attempt)  # Exponential backoff
                    continue
                else:
                    # Final failure
                    step_result.success = False
                    step_result.error_details = {
                        "type": "step_failure",
                        "message": f"Step failed after {retry_attempts + 1} attempts",
                        "last_response": response,
                        "final_attempt": attempt + 1
                    }
                    return step_result
                    
            except Exception as e:
                logger.error(f"Exception in step {step_name}: {str(e)}", exc_info=True)
                
                if attempt < retry_attempts:
                    await asyncio.sleep(2 ** attempt)
                    continue
                else:
                    # Final exception
                    step_end = time.time()
                    duration_ms = (step_end - step_start) * 1000
                    
                    return ProcessingStep(
                        step_name=step_name,
                        stage=stage,
                        timestamp=start_time,
                        success=False,
                        response={},
                        duration_ms=duration_ms,
                        compliance_flags=[],
                        error_details={
                            "type": "exception",
                            "message": str(e),
                            "attempts": attempt + 1
                        },
                        retry_attempts=attempt
                    )
    
    def _is_response_successful(self, response: Dict[str, Any]) -> bool:
        """Check if API response indicates success."""
        if isinstance(response, dict):
            code = response.get("code")
            if code is not None:
                return code in [200, 201]
        return False
    
    def _get_step_compliance_flags(self, step_name: str, response: Dict[str, Any]) -> List[str]:
        """Get compliance flags for processing step."""
        flags = []
        
        if "validate" in step_name:
            flags.extend(["DATA_VALIDATION", "QUALITY_ASSURANCE"])
        
        if "sign" in step_name:
            flags.extend(["DIGITAL_SIGNATURE", "AUTHENTICATION"])
        
        if "transmit" in step_name:
            flags.extend(["FIRS_SUBMISSION", "TAX_COMPLIANCE"])
        
        if "irn" in step_name:
            flags.extend(["IRN_COMPLIANCE", "IDENTIFIER_VALIDATION"])
        
        # Add success/failure flags
        if self._is_response_successful(response):
            flags.append("OPERATION_SUCCESS")
        else:
            flags.append("OPERATION_FAILURE")
        
        return flags
    
    def _assess_processing_success(self, steps: List[ProcessingStep], errors: List[Dict[str, Any]]) -> bool:
        """Assess overall processing success."""
        # Must have successful validation, signing, and transmission
        required_steps = ["validate_invoice", "sign_invoice", "transmit_invoice"]
        
        successful_required_steps = sum(
            1 for step in steps 
            if step.step_name in required_steps and step.success
        )
        
        return successful_required_steps >= len(required_steps) and len(errors) == 0
    
    async def _assess_nigerian_compliance(
        self,
        result: EnhancedProcessingResult,
        invoice_data: Dict[str, Any],
        customer_data: Dict[str, Any],
        organization_id: str
    ) -> ComplianceAssessment:
        """Assess Nigerian regulatory compliance."""
        violations = []
        recommendations = []
        scores = []
        
        # FIRS Compliance Assessment
        firs_compliance = result.stage in [
            InvoiceProcessingStage.TRANSMITTED,
            InvoiceProcessingStage.CONFIRMED,
            InvoiceProcessingStage.COMPLETED
        ]
        scores.append(100 if firs_compliance else 0)
        
        if not firs_compliance:
            violations.append("Invoice not successfully transmitted to FIRS")
            recommendations.append("Ensure FIRS transmission completes successfully")
        
        # NDPR Compliance Assessment (Data Protection)
        ndpr_compliance = True
        customer_tin = customer_data.get("tin")
        if customer_tin and len(customer_tin) > 0:
            # Nigerian TIN present - NDPR applies
            if not invoice_data.get("data_protection_consent"):
                ndpr_compliance = False
                violations.append("Missing data protection consent for Nigerian customer")
                recommendations.append("Obtain explicit consent for processing Nigerian customer data")
        scores.append(100 if ndpr_compliance else 50)
        
        # Tax Accuracy Assessment
        tax_accuracy = True
        invoice_lines = invoice_data.get("invoice_lines", [])
        for line in invoice_lines:
            vat_rate = line.get("vat_rate", 0)
            if vat_rate != 7.5:  # Standard Nigerian VAT rate
                tax_accuracy = False
                violations.append(f"Incorrect VAT rate: {vat_rate}% (should be 7.5%)")
                recommendations.append("Verify VAT rates comply with Nigerian tax regulations")
                break
        scores.append(100 if tax_accuracy else 70)
        
        # Data Protection Assessment
        data_protection = True
        if not result.metadata.get("encryption_enabled", True):
            data_protection = False
            violations.append("Data encryption not enabled")
            recommendations.append("Enable encryption for tax data protection")
        scores.append(100 if data_protection else 60)
        
        # Audit Trail Assessment
        audit_trail_complete = len(result.steps) >= 4  # Minimum required steps
        scores.append(100 if audit_trail_complete else 80)
        
        if not audit_trail_complete:
            violations.append("Incomplete audit trail")
            recommendations.append("Ensure all processing steps are logged for compliance")
        
        # Calculate overall score
        overall_score = sum(scores) / len(scores)
        
        # Determine compliance level
        if overall_score >= 90:
            overall_level = ComplianceLevel.FULL_COMPLIANCE
        elif overall_score >= 70:
            overall_level = ComplianceLevel.PARTIAL_COMPLIANCE
        elif len(violations) == 0:
            overall_level = ComplianceLevel.PENDING_REVIEW
        else:
            overall_level = ComplianceLevel.NON_COMPLIANCE
        
        # Add general recommendations
        recommendations.extend([
            "Maintain 7-year retention for tax records",
            "Regular compliance audits recommended",
            "Monitor FIRS regulation updates",
            "Ensure staff training on Nigerian tax compliance"
        ])
        
        return ComplianceAssessment(
            overall_level=overall_level,
            firs_compliance=firs_compliance,
            ndpr_compliance=ndpr_compliance,
            tax_accuracy=tax_accuracy,
            data_protection=data_protection,
            audit_trail_complete=audit_trail_complete,
            violations=violations,
            recommendations=recommendations,
            score=overall_score
        )
    
    async def _record_processing_compliance_event(
        self,
        result: EnhancedProcessingResult,
        organization_id: str,
        user_id: Optional[str]
    ):
        """Record compliance event for invoice processing."""
        
        # Determine event severity
        if result.compliance_assessment.overall_level == ComplianceLevel.NON_COMPLIANCE:
            severity = MonitoringLevel.HIGH
        elif result.compliance_assessment.overall_level == ComplianceLevel.PARTIAL_COMPLIANCE:
            severity = MonitoringLevel.MEDIUM
        else:
            severity = MonitoringLevel.LOW
        
        # Record in monitoring system
        self.monitor._record_compliance_event(
            event_type=ComplianceEventType.FIRS_SUBMISSION,
            severity=severity,
            organization_id=organization_id,
            user_id=user_id,
            request_id=result.processing_id,
            metadata={
                "invoice_reference": result.invoice_reference,
                "irn": result.irn,
                "processing_stage": result.stage.value,
                "compliance_level": result.compliance_assessment.overall_level.value,
                "compliance_score": result.compliance_assessment.score,
                "firs_compliance": result.compliance_assessment.firs_compliance,
                "processing_time_ms": result.total_processing_time_ms,
                "violations_count": len(result.compliance_assessment.violations)
            }
        )
        
        # Record in audit service
        await self.audit_service.log_audit_event(
            event_type="invoice_processing_completed",
            event_description=f"Invoice processing completed: {result.invoice_reference}",
            outcome="success" if result.success else "failure",
            user_id=user_id,
            organization_id=organization_id,
            resource_type="invoice",
            resource_id=result.invoice_reference,
            additional_data={
                "processing_id": result.processing_id,
                "compliance_assessment": asdict(result.compliance_assessment),
                "processing_time_ms": result.total_processing_time_ms,
                "stage": result.stage.value
            }
        )
    
    async def get_processing_status(self, processing_id: str) -> Optional[Dict[str, Any]]:
        """Get status of invoice processing by processing ID."""
        # In a real implementation, this would query from database
        # For now, return a placeholder structure
        return {
            "processing_id": processing_id,
            "status": "processing",
            "current_stage": "transmitted",
            "estimated_completion": (datetime.utcnow() + timedelta(minutes=5)).isoformat(),
            "steps_completed": 5,
            "total_steps": 7
        }
    
    async def retry_failed_processing(
        self,
        processing_id: str,
        from_stage: InvoiceProcessingStage,
        organization_id: str,
        user_id: Optional[str] = None
    ) -> EnhancedProcessingResult:
        """Retry failed invoice processing from specific stage."""
        logger.info(f"Retrying invoice processing {processing_id} from stage {from_stage}")
        
        # In a real implementation, this would:
        # 1. Retrieve original processing data from database
        # 2. Resume processing from the specified stage
        # 3. Update existing processing record
        
        # For now, return a placeholder
        return EnhancedProcessingResult(
            invoice_reference="retry-placeholder",
            irn=None,
            processing_id=processing_id,
            stage=InvoiceProcessingStage.INITIATED,
            success=False,
            steps=[],
            compliance_assessment=ComplianceAssessment(
                overall_level=ComplianceLevel.PENDING_REVIEW,
                firs_compliance=False,
                ndpr_compliance=False,
                tax_accuracy=False,
                data_protection=False,
                audit_trail_complete=False,
                violations=[],
                recommendations=[],
                score=0.0
            ),
            errors=[],
            warnings=[],
            total_processing_time_ms=0.0,
            nigerian_requirements_met=False,
            firs_submission_status="retry_initiated",
            retention_period_years=self.retention_years,
            created_at=datetime.utcnow()
        )
    
    async def get_compliance_summary(
        self,
        organization_id: str,
        date_range: Optional[Dict[str, datetime]] = None
    ) -> Dict[str, Any]:
        """Get compliance summary for organization."""
        # In a real implementation, this would query processing history
        # and generate compliance metrics
        
        return {
            "organization_id": organization_id,
            "period": {
                "start": (datetime.utcnow() - timedelta(days=30)).isoformat(),
                "end": datetime.utcnow().isoformat()
            },
            "summary": {
                "total_invoices_processed": 1250,
                "successful_firs_submissions": 1180,
                "compliance_violations": 15,
                "average_compliance_score": 92.5,
                "retention_compliance": 100.0
            },
            "compliance_breakdown": {
                "full_compliance": 94.4,
                "partial_compliance": 4.0,
                "non_compliance": 1.2,
                "pending_review": 0.4
            },
            "nigerian_requirements": {
                "firs_compliance_rate": 94.4,
                "ndpr_compliance_rate": 98.2,
                "tax_accuracy_rate": 99.1,
                "data_protection_rate": 96.8
            },
            "recommendations": [
                "Review failed submissions for common patterns",
                "Update staff training on NDPR requirements",
                "Implement automated compliance checks",
                "Regular audit of data protection measures"
            ]
        }


# Enhanced global processor instance
firs_core_invoice_processor = FIRSCoreInvoiceProcessor()


class FIRSCoreErrorHandler:
    """Enhanced error handler with Nigerian compliance context."""
    
    @staticmethod
    def handle_enhanced_firs_response(
        response: Dict[str, Any],
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Handle and standardize FIRS API responses with compliance context."""
        
        # Handle successful responses
        if response.get("code") in [200, 201]:
            return {
                "success": True,
                "data": response.get("data"),
                "message": "Operation completed successfully",
                "compliance_notes": FIRSCoreErrorHandler._get_compliance_notes(response, context)
            }
        
        # Handle error responses
        error_info = response.get("error", {})
        error_message = error_info.get("public_message", "Unknown error")
        error_details = error_info.get("details", "")
        
        # Enhanced error mapping with Nigerian context
        user_message = FIRSCoreErrorHandler._get_enhanced_user_message(
            error_message, error_details, context
        )
        
        return {
            "success": False,
            "error": {
                "code": response.get("code"),
                "message": user_message,
                "details": error_details,
                "original_message": error_message,
                "error_id": error_info.get("id"),
                "handler": error_info.get("handler"),
                "compliance_impact": FIRSCoreErrorHandler._assess_compliance_impact(
                    response.get("code"), error_message
                ),
                "nigerian_context": FIRSCoreErrorHandler._get_nigerian_context(error_message)
            },
            "retry_recommendation": FIRSCoreErrorHandler.get_enhanced_retry_recommendation(
                response, context
            )
        }
    
    @staticmethod
    def _get_compliance_notes(response: Dict[str, Any], context: Optional[Dict[str, Any]]) -> List[str]:
        """Get compliance-related notes for successful operations."""
        notes = []
        
        if context and context.get("nigerian_customer"):
            notes.append("NDPR compliance: Nigerian customer data processed")
        
        if "invoice" in str(response).lower():
            notes.extend([
                "Tax compliance: Invoice data submitted to FIRS",
                "Retention requirement: 7-year retention applies"
            ])
        
        return notes
    
    @staticmethod
    def _get_enhanced_user_message(
        error_message: str, 
        details: str, 
        context: Optional[Dict[str, Any]]
    ) -> str:
        """Enhanced error message mapping with Nigerian context."""
        
        nigerian_errors = {
            "tin validation failed": "Nigerian TIN validation failed. Please verify TIN format and registration status with FIRS.",
            "bvn verification failed": "Bank Verification Number (BVN) validation failed. Please verify BVN with Nigerian bank.",
            "invalid state code": "Invalid Nigerian state code. Please use valid 2-letter state codes (e.g., LA for Lagos, KN for Kano).",
            "invalid lga": "Invalid Local Government Area. Please verify LGA name matches state jurisdiction.",
            "vat rate incorrect": "VAT rate must be 7.5% for Nigerian transactions unless specifically exempted.",
            "currency mismatch": "Currency must be NGN (Nigerian Naira) for Nigerian tax submissions."
        }
        
        # Check for Nigerian-specific errors first
        for pattern, nigerian_message in nigerian_errors.items():
            if pattern.lower() in error_message.lower():
                return nigerian_message
        
        # Fall back to general error mapping
        common_errors = {
            "unable to validate api key": "API credentials are invalid or expired. Please check FIRS API key configuration.",
            "irn validation failed": "IRN format doesn't match template requirements. Verify IRN follows pattern: {invoice_id}-59854B81-{YYYYMMDD}",
            "validation failed": "Required fields are missing or invalid. Please check all mandatory invoice fields.",
            "webhook url is not setup": "Webhook configuration required for FIRS transmission. Please configure webhook endpoints.",
            "rate limit exceeded": "FIRS API rate limit exceeded. Please reduce submission frequency.",
            "certificate expired": "Digital certificate has expired. Please renew certificate for continued operations."
        }
        
        for pattern, friendly_message in common_errors.items():
            if pattern.lower() in error_message.lower():
                return friendly_message
        
        # Handle validation errors with details
        if "required" in details.lower():
            return f"Required field missing: {details}"
        
        if "invalid" in details.lower():
            return f"Invalid data provided: {details}"
        
        return error_message
    
    @staticmethod
    def _assess_compliance_impact(error_code: int, error_message: str) -> str:
        """Assess compliance impact of error."""
        if error_code >= 500:
            return "high_impact"  # System errors affect compliance
        elif "tax" in error_message.lower() or "firs" in error_message.lower():
            return "high_impact"  # Tax-related errors
        elif "validation" in error_message.lower():
            return "medium_impact"  # Data quality issues
        else:
            return "low_impact"
    
    @staticmethod
    def _get_nigerian_context(error_message: str) -> Dict[str, Any]:
        """Get Nigerian regulatory context for error."""
        context = {
            "regulatory_body": None,
            "compliance_requirement": None,
            "resolution_contact": None
        }
        
        if "firs" in error_message.lower() or "tax" in error_message.lower():
            context.update({
                "regulatory_body": "Federal Inland Revenue Service (FIRS)",
                "compliance_requirement": "Nigerian Tax Law Compliance",
                "resolution_contact": "FIRS Customer Service or authorized tax consultant"
            })
        elif "bvn" in error_message.lower():
            context.update({
                "regulatory_body": "Central Bank of Nigeria (CBN)",
                "compliance_requirement": "Bank Verification Number Validation",
                "resolution_contact": "Customer's bank or CBN"
            })
        elif "data protection" in error_message.lower():
            context.update({
                "regulatory_body": "National Information Technology Development Agency (NITDA)",
                "compliance_requirement": "Nigeria Data Protection Regulation (NDPR)",
                "resolution_contact": "Data Protection Officer or NITDA"
            })
        
        return context
    
    @staticmethod
    def get_enhanced_retry_recommendation(
        response: Dict[str, Any], 
        context: Optional[Dict[str, Any]]
    ) -> Optional[Dict[str, Any]]:
        """Get enhanced retry recommendations with Nigerian context."""
        error_code = response.get("code")
        error_message = response.get("error", {}).get("public_message", "").lower()
        
        if error_code == 429:
            return {
                "action": "wait_and_retry",
                "wait_time_minutes": 5,
                "message": "FIRS API rate limit exceeded. Wait before retrying.",
                "nigerian_note": "FIRS has submission limits to ensure system stability."
            }
        
        if error_code >= 500:
            return {
                "action": "retry_with_backoff",
                "wait_time_minutes": 10,
                "message": "FIRS server error. Retry after a few minutes.",
                "nigerian_note": "FIRS system may be undergoing maintenance."
            }
        
        if "webhook" in error_message:
            return {
                "action": "configure_webhook",
                "message": "Configure webhook URLs before attempting transmission.",
                "nigerian_note": "FIRS requires webhook endpoints for submission status updates."
            }
        
        if "tin" in error_message:
            return {
                "action": "verify_tin",
                "message": "Verify Nigerian TIN with FIRS before resubmission.",
                "nigerian_note": "TIN must be registered and active with FIRS."
            }
        
        if "irn" in error_message:
            return {
                "action": "fix_irn_format",
                "message": "Check IRN format matches template: {invoice_id}-59854B81-{YYYYMMDD}",
                "nigerian_note": "IRN format is standardized for FIRS compliance."
            }
        
        return None


# Enhanced error handler instance
firs_core_error_handler = FIRSCoreErrorHandler()
