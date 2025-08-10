"""
Unified Compliance Orchestrator
==============================
Main orchestration engine that coordinates all regulatory compliance frameworks
including Nigerian and international standards for comprehensive compliance validation.
"""
import logging
import asyncio
from typing import Dict, Any, List, Optional, Union, Tuple
from datetime import datetime, timedelta
from concurrent.futures import ThreadPoolExecutor, as_completed
import importlib
import uuid

from .models import (
    ComplianceResult, ComplianceFramework, ComplianceStatus, OrchestrationContext,
    ComplianceRule, ValidationResult, ValidationSeverity, ComplianceMatrix,
    FrameworkIntegration, AuditEvent
)


class ComplianceOrchestrator:
    """
    Central orchestrator for all regulatory compliance frameworks
    """
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.framework_integrations = {}
        self.compliance_matrix = None
        self.audit_events = []
        
        # Performance tracking
        self.performance_metrics = {
            "total_assessments": 0,
            "successful_assessments": 0,
            "failed_assessments": 0,
            "average_assessment_time": 0.0,
            "framework_performance": {}
        }
        
        # Initialize framework integrations
        self._initialize_framework_integrations()
        self._initialize_compliance_matrix()
        
    def _initialize_framework_integrations(self):
        """Initialize all compliance framework integrations"""
        
        try:
            # International Standards Integrations
            self.framework_integrations = {
                ComplianceFramework.UBL: FrameworkIntegration(
                    framework=ComplianceFramework.UBL,
                    integration_name="UBL Compliance Engine",
                    validator_class="UBLComplianceEngine",
                    validator_module="taxpoynt_platform.core_platform.regulatory_systems.international_standards.ubl_framework.ubl_compliance_engine",
                    required_data_fields=["invoice_data", "document_type"],
                    priority_level=9  # High priority for core invoicing
                ),
                
                ComplianceFramework.WCO_HS: FrameworkIntegration(
                    framework=ComplianceFramework.WCO_HS,
                    integration_name="WCO HS Code Classifier",
                    validator_class="HSClassifier",
                    validator_module="taxpoynt_platform.core_platform.regulatory_systems.international_standards.wco_hs_classifier.hs_classifier",
                    required_data_fields=["product_data", "trade_classification"],
                    priority_level=7
                ),
                
                ComplianceFramework.GDPR: FrameworkIntegration(
                    framework=ComplianceFramework.GDPR,
                    integration_name="GDPR Compliance Engine",
                    validator_class="GDPRComplianceEngine",
                    validator_module="taxpoynt_platform.core_platform.regulatory_systems.international_standards.gdpr_framework.gdpr_compliance_engine",
                    required_data_fields=["personal_data", "processing_purpose"],
                    priority_level=8  # High priority for data protection
                ),
                
                ComplianceFramework.NDPA: FrameworkIntegration(
                    framework=ComplianceFramework.NDPA,
                    integration_name="NDPA Compliance Engine",
                    validator_class="NDPAComplianceEngine",
                    validator_module="taxpoynt_platform.core_platform.regulatory_systems.nigerian_regulators.nitda_compliance.ndpa_compliance_engine",
                    required_data_fields=["personal_data", "nigerian_context"],
                    priority_level=9  # Critical for Nigerian operations
                ),
                
                ComplianceFramework.ISO_20022: FrameworkIntegration(
                    framework=ComplianceFramework.ISO_20022,
                    integration_name="ISO 20022 Financial Messaging Validator",
                    validator_class="ISO20022Validator",
                    validator_module="taxpoynt_platform.core_platform.regulatory_systems.international_standards.iso20022_processor.iso20022_validator",
                    required_data_fields=["financial_message", "message_type"],
                    priority_level=6
                ),
                
                ComplianceFramework.ISO_27001: FrameworkIntegration(
                    framework=ComplianceFramework.ISO_27001,
                    integration_name="ISO 27001 Security Management System",
                    validator_class="SecurityManagementSystem",
                    validator_module="taxpoynt_platform.core_platform.regulatory_systems.international_standards.iso27001_framework.security_management_system",
                    required_data_fields=["security_context", "asset_information"],
                    priority_level=8  # High priority for security
                ),
                
                ComplianceFramework.PEPPOL: FrameworkIntegration(
                    framework=ComplianceFramework.PEPPOL,
                    integration_name="PEPPOL Standards Validator",
                    validator_class="PEPPOLValidator",
                    validator_module="taxpoynt_platform.core_platform.regulatory_systems.international_standards.peppol_compliance.peppol_validator",
                    required_data_fields=["peppol_document", "participant_info"],
                    priority_level=7
                ),
                
                ComplianceFramework.LEI: FrameworkIntegration(
                    framework=ComplianceFramework.LEI,
                    integration_name="LEI Validation System",
                    validator_class="LEIValidator",
                    validator_module="taxpoynt_platform.core_platform.regulatory_systems.international_standards.gleif_lei.lei_validator",
                    required_data_fields=["lei_code", "entity_information"],
                    priority_level=5
                )
                
                # Nigerian regulatory frameworks will be added as we implement them
            }
            
            self.logger.info(f"Initialized {len(self.framework_integrations)} compliance framework integrations")
            
        except Exception as e:
            self.logger.error(f"Framework integration initialization failed: {str(e)}")
            raise
    
    def _initialize_compliance_matrix(self):
        """Initialize compliance requirements matrix"""
        
        try:
            self.compliance_matrix = ComplianceMatrix(
                matrix_id="TAXPOYNT_COMPLIANCE_MATRIX_V1",
                created_timestamp=datetime.now(),
                
                # Document type requirements
                document_type_frameworks={
                    "invoice": [ComplianceFramework.UBL, ComplianceFramework.FIRS, ComplianceFramework.GDPR],
                    "credit_note": [ComplianceFramework.UBL, ComplianceFramework.FIRS],
                    "peppol_invoice": [ComplianceFramework.UBL, ComplianceFramework.PEPPOL, ComplianceFramework.LEI],
                    "international_invoice": [ComplianceFramework.UBL, ComplianceFramework.PEPPOL, ComplianceFramework.WCO_HS, ComplianceFramework.LEI],
                    "financial_message": [ComplianceFramework.ISO_20022],
                    "trade_document": [ComplianceFramework.WCO_HS, ComplianceFramework.UBL]
                },
                
                # Jurisdiction requirements
                jurisdiction_frameworks={
                    "NG": [ComplianceFramework.FIRS, ComplianceFramework.NITDA, ComplianceFramework.CAC, ComplianceFramework.NDPA],
                    "EU": [ComplianceFramework.GDPR, ComplianceFramework.PEPPOL],
                    "US": [ComplianceFramework.LEI],
                    "INTL": [ComplianceFramework.PEPPOL, ComplianceFramework.LEI, ComplianceFramework.ISO_20022],
                    "CROSS_BORDER": [ComplianceFramework.PEPPOL, ComplianceFramework.WCO_HS, ComplianceFramework.LEI]
                },
                
                # Business type requirements
                business_type_frameworks={
                    "financial_institution": [ComplianceFramework.ISO_20022, ComplianceFramework.LEI, ComplianceFramework.ISO_27001],
                    "large_taxpayer": [ComplianceFramework.FIRS, ComplianceFramework.UBL, ComplianceFramework.ISO_27001],
                    "sme": [ComplianceFramework.FIRS, ComplianceFramework.UBL],
                    "multinational": [ComplianceFramework.PEPPOL, ComplianceFramework.LEI, ComplianceFramework.GDPR, ComplianceFramework.WCO_HS],
                    "government": [ComplianceFramework.PEPPOL, ComplianceFramework.ISO_27001],
                    "access_point_provider": [ComplianceFramework.PEPPOL, ComplianceFramework.ISO_27001, ComplianceFramework.NITDA]
                },
                
                # Framework dependencies
                framework_dependencies={
                    ComplianceFramework.PEPPOL: [ComplianceFramework.UBL, ComplianceFramework.ISO_27001],
                    ComplianceFramework.FIRS: [ComplianceFramework.UBL],
                    ComplianceFramework.EINVOICE_NIGERIA: [ComplianceFramework.FIRS, ComplianceFramework.UBL, ComplianceFramework.NITDA],
                    ComplianceFramework.CROSS_BORDER: [ComplianceFramework.PEPPOL, ComplianceFramework.WCO_HS, ComplianceFramework.LEI]
                },
                
                # Framework weights for scoring
                framework_weights={
                    ComplianceFramework.FIRS: 10.0,  # Critical for Nigerian operations
                    ComplianceFramework.UBL: 9.0,   # Core invoicing standard
                    ComplianceFramework.GDPR: 8.0,  # Important for data protection
                    ComplianceFramework.NDPA: 9.0,  # Critical for Nigerian data protection
                    ComplianceFramework.PEPPOL: 8.0, # Important for international business
                    ComplianceFramework.ISO_27001: 7.0, # Important for security
                    ComplianceFramework.LEI: 6.0,   # Important for entity identification
                    ComplianceFramework.WCO_HS: 5.0, # Important for trade
                    ComplianceFramework.ISO_20022: 5.0, # Important for financial messaging
                    ComplianceFramework.NITDA: 8.0, # Important for Nigerian tech compliance
                    ComplianceFramework.CAC: 7.0    # Important for Nigerian corporate compliance
                }
            )
            
            self.logger.info("Compliance matrix initialized successfully")
            
        except Exception as e:
            self.logger.error(f"Compliance matrix initialization failed: {str(e)}")
            raise
    
    def assess_compliance(self, context: OrchestrationContext) -> ComplianceResult:
        """
        Perform comprehensive compliance assessment
        
        Args:
            context: Orchestration context with document data and requirements
            
        Returns:
            Comprehensive compliance result
        """
        try:
            assessment_start = datetime.now()
            compliance_id = f"COMP_{uuid.uuid4().hex[:8].upper()}"
            
            # Log assessment start
            self._log_audit_event(
                event_type="compliance_assessment_started",
                compliance_id=compliance_id,
                description=f"Started compliance assessment for document {context.document_data.get('document_id', 'unknown')}",
                technical_details={"context_id": context.context_id}
            )
            
            # Initialize result
            compliance_result = ComplianceResult(
                compliance_id=compliance_id,
                assessment_timestamp=assessment_start,
                document_id=context.document_data.get("document_id", "unknown"),
                document_type=context.document_data.get("document_type", "unknown"),
                overall_status=ComplianceStatus.PENDING,
                overall_score=0.0,
                assessment_context={"context_id": context.context_id}
            )
            
            # Determine applicable frameworks
            applicable_frameworks = self._determine_applicable_frameworks(context)
            compliance_result.assessed_frameworks = applicable_frameworks
            
            # Validate frameworks in parallel if enabled
            if context.parallel_validation and len(applicable_frameworks) > 1:
                framework_results = self._validate_frameworks_parallel(applicable_frameworks, context)
            else:
                framework_results = self._validate_frameworks_sequential(applicable_frameworks, context)
            
            # Compile results
            compliance_result.framework_results = framework_results
            
            # Calculate overall compliance status and scores
            self._calculate_overall_compliance(compliance_result)
            
            # Generate recommendations
            compliance_result.compliance_recommendations = self._generate_compliance_recommendations(compliance_result)
            compliance_result.priority_actions = self._generate_priority_actions(compliance_result)
            
            # Assess business and regulatory risk
            compliance_result.business_risk_level = self._assess_business_risk(compliance_result)
            compliance_result.regulatory_risk_level = self._assess_regulatory_risk(compliance_result)
            
            # Update performance metrics
            assessment_duration = (datetime.now() - assessment_start).total_seconds() * 1000
            self._update_performance_metrics(compliance_result, assessment_duration)
            
            # Log assessment completion
            self._log_audit_event(
                event_type="compliance_assessment_completed",
                compliance_id=compliance_id,
                description=f"Completed compliance assessment - Status: {compliance_result.overall_status.value}, Score: {compliance_result.overall_score:.2f}",
                technical_details={
                    "assessment_duration_ms": assessment_duration,
                    "frameworks_assessed": len(applicable_frameworks),
                    "overall_score": compliance_result.overall_score
                }
            )
            
            return compliance_result
            
        except Exception as e:
            self.logger.error(f"Compliance assessment failed: {str(e)}")
            self.performance_metrics["failed_assessments"] += 1
            
            # Log assessment failure
            self._log_audit_event(
                event_type="compliance_assessment_failed",
                compliance_id=compliance_id if 'compliance_id' in locals() else "unknown",
                description=f"Compliance assessment failed: {str(e)}",
                severity_level=ValidationSeverity.CRITICAL,
                technical_details={"error": str(e)}
            )
            
            # Return error result
            return ComplianceResult(
                compliance_id=f"ERROR_{uuid.uuid4().hex[:8].upper()}",
                assessment_timestamp=datetime.now(),
                document_id=context.document_data.get("document_id", "unknown"),
                document_type=context.document_data.get("document_type", "unknown"),
                overall_status=ComplianceStatus.ERROR,
                overall_score=0.0,
                priority_actions=[f"Resolve assessment error: {str(e)}"]
            )
    
    def _determine_applicable_frameworks(self, context: OrchestrationContext) -> List[ComplianceFramework]:
        """Determine which compliance frameworks apply to this context"""
        
        applicable_frameworks = set()
        
        # Add explicitly required frameworks
        applicable_frameworks.update(context.required_frameworks)
        
        # Add frameworks based on document type
        document_type = context.document_data.get("document_type", "").lower()
        document_frameworks = self.compliance_matrix.document_type_frameworks.get(document_type, [])
        applicable_frameworks.update(document_frameworks)
        
        # Add frameworks based on jurisdiction
        jurisdictions = self._extract_jurisdictions(context)
        for jurisdiction in jurisdictions:
            jurisdiction_frameworks = self.compliance_matrix.jurisdiction_frameworks.get(jurisdiction, [])
            applicable_frameworks.update(jurisdiction_frameworks)
        
        # Add frameworks based on business context
        business_type = context.transaction_context.get("business_type", "").lower()
        business_frameworks = self.compliance_matrix.business_type_frameworks.get(business_type, [])
        applicable_frameworks.update(business_frameworks)
        
        # Add optional frameworks if specified
        applicable_frameworks.update(context.optional_frameworks)
        
        # Resolve dependencies
        resolved_frameworks = self._resolve_framework_dependencies(list(applicable_frameworks))
        
        # Filter by available integrations
        available_frameworks = [fw for fw in resolved_frameworks if fw in self.framework_integrations]
        
        self.logger.info(f"Determined {len(available_frameworks)} applicable frameworks: {[fw.value for fw in available_frameworks]}")
        
        return available_frameworks
    
    def _extract_jurisdictions(self, context: OrchestrationContext) -> List[str]:
        """Extract relevant jurisdictions from context"""
        
        jurisdictions = set()
        
        # Check sender jurisdiction
        sender_country = context.sender_info.get("country_code", "").upper()
        if sender_country:
            jurisdictions.add(sender_country)
        
        # Check receiver jurisdiction
        receiver_country = context.receiver_info.get("country_code", "").upper()
        if receiver_country:
            jurisdictions.add(receiver_country)
        
        # Check transaction jurisdiction requirements
        transaction_jurisdictions = context.jurisdiction_requirements.keys()
        jurisdictions.update(transaction_jurisdictions)
        
        # Determine if cross-border
        if len(jurisdictions) > 1:
            jurisdictions.add("CROSS_BORDER")
        
        # Add international if PEPPOL is involved
        if any("peppol" in str(fw).lower() for fw in context.required_frameworks + context.optional_frameworks):
            jurisdictions.add("INTL")
        
        return list(jurisdictions)
    
    def _resolve_framework_dependencies(self, frameworks: List[ComplianceFramework]) -> List[ComplianceFramework]:
        """Resolve framework dependencies"""
        
        resolved = set(frameworks)
        
        for framework in frameworks:
            dependencies = self.compliance_matrix.framework_dependencies.get(framework, [])
            resolved.update(dependencies)
        
        return list(resolved)
    
    def _validate_frameworks_parallel(self, frameworks: List[ComplianceFramework], 
                                    context: OrchestrationContext) -> Dict[ComplianceFramework, ValidationResult]:
        """Validate frameworks in parallel for improved performance"""
        
        framework_results = {}
        
        with ThreadPoolExecutor(max_workers=min(len(frameworks), 5)) as executor:
            # Submit validation tasks
            future_to_framework = {
                executor.submit(self._validate_single_framework, framework, context): framework
                for framework in frameworks
            }
            
            # Collect results
            for future in as_completed(future_to_framework, timeout=context.max_validation_time_ms/1000):
                framework = future_to_framework[future]
                try:
                    result = future.result()
                    framework_results[framework] = result
                except Exception as e:
                    self.logger.error(f"Parallel validation failed for {framework.value}: {str(e)}")
                    # Create error result
                    framework_results[framework] = ValidationResult(
                        rule_id=f"{framework.value}_VALIDATION_ERROR",
                        framework=framework,
                        status=ComplianceStatus.ERROR,
                        severity=ValidationSeverity.HIGH,
                        validation_timestamp=datetime.now(),
                        validation_score=0.0,
                        issues_found=[f"Validation error: {str(e)}"]
                    )
        
        return framework_results
    
    def _validate_frameworks_sequential(self, frameworks: List[ComplianceFramework],
                                      context: OrchestrationContext) -> Dict[ComplianceFramework, ValidationResult]:
        """Validate frameworks sequentially"""
        
        framework_results = {}
        
        # Sort by priority for sequential execution
        sorted_frameworks = sorted(frameworks, 
                                 key=lambda fw: self.framework_integrations.get(fw, FrameworkIntegration(
                                     framework=fw, integration_name="", validator_class="", validator_module=""
                                 )).priority_level, 
                                 reverse=True)
        
        for framework in sorted_frameworks:
            try:
                result = self._validate_single_framework(framework, context)
                framework_results[framework] = result
            except Exception as e:
                self.logger.error(f"Sequential validation failed for {framework.value}: {str(e)}")
                framework_results[framework] = ValidationResult(
                    rule_id=f"{framework.value}_VALIDATION_ERROR",
                    framework=framework,
                    status=ComplianceStatus.ERROR,
                    severity=ValidationSeverity.HIGH,
                    validation_timestamp=datetime.now(),
                    validation_score=0.0,
                    issues_found=[f"Validation error: {str(e)}"]
                )
        
        return framework_results
    
    def _validate_single_framework(self, framework: ComplianceFramework,
                                 context: OrchestrationContext) -> ValidationResult:
        """Validate single compliance framework"""
        
        validation_start = datetime.now()
        
        try:
            # Get framework integration
            integration = self.framework_integrations.get(framework)
            if not integration:
                raise ValueError(f"No integration found for framework: {framework.value}")
            
            # Check required data fields
            missing_fields = []
            for field in integration.required_data_fields:
                if field not in context.document_data:
                    missing_fields.append(field)
            
            if missing_fields:
                return ValidationResult(
                    rule_id=f"{framework.value}_MISSING_DATA",
                    framework=framework,
                    status=ComplianceStatus.NON_COMPLIANT,
                    severity=ValidationSeverity.HIGH,
                    validation_timestamp=datetime.now(),
                    validation_score=0.0,
                    issues_found=[f"Missing required data fields: {', '.join(missing_fields)}"],
                    recommendations=[f"Provide required data fields: {', '.join(missing_fields)}"]
                )
            
            # Load and execute validator
            validator = self._load_validator(integration)
            
            # Prepare framework-specific context
            framework_context = self._prepare_framework_context(framework, context)
            
            # Execute validation
            validation_result = self._execute_framework_validation(validator, framework_context)
            
            # Calculate validation duration
            validation_duration = (datetime.now() - validation_start).total_seconds() * 1000
            validation_result.validation_duration_ms = int(validation_duration)
            
            # Update framework performance metrics
            self._update_framework_performance(framework, validation_duration, validation_result.status == ComplianceStatus.COMPLIANT)
            
            return validation_result
            
        except Exception as e:
            self.logger.error(f"Framework validation failed for {framework.value}: {str(e)}")
            raise
    
    def _load_validator(self, integration: FrameworkIntegration):
        """Dynamically load validator class"""
        
        try:
            # Import module
            module = importlib.import_module(integration.validator_module)
            
            # Get validator class
            validator_class = getattr(module, integration.validator_class)
            
            # Instantiate validator
            validator = validator_class()
            
            return validator
            
        except ImportError as e:
            self.logger.error(f"Failed to import validator module {integration.validator_module}: {str(e)}")
            raise
        except AttributeError as e:
            self.logger.error(f"Validator class {integration.validator_class} not found in module: {str(e)}")
            raise
        except Exception as e:
            self.logger.error(f"Failed to instantiate validator {integration.validator_class}: {str(e)}")
            raise
    
    def _prepare_framework_context(self, framework: ComplianceFramework, 
                                 context: OrchestrationContext) -> Dict[str, Any]:
        """Prepare framework-specific validation context"""
        
        framework_context = {
            "framework": framework.value,
            "document_data": context.document_data,
            "document_metadata": context.document_metadata,
            "sender_info": context.sender_info,
            "receiver_info": context.receiver_info,
            "transaction_context": context.transaction_context,
            "assessment_level": context.assessment_level,
            "include_recommendations": context.include_recommendations
        }
        
        # Add framework-specific context enhancements
        if framework == ComplianceFramework.PEPPOL:
            framework_context.update({
                "peppol_document": context.document_data,
                "participant_info": {
                    "sender": context.sender_info,
                    "receiver": context.receiver_info
                }
            })
        elif framework == ComplianceFramework.UBL:
            framework_context.update({
                "invoice_data": context.document_data,
                "document_type": context.document_data.get("document_type")
            })
        elif framework in [ComplianceFramework.GDPR, ComplianceFramework.NDPA]:
            framework_context.update({
                "personal_data": context.document_data.get("personal_data", {}),
                "processing_purpose": context.transaction_context.get("processing_purpose"),
                "nigerian_context": framework == ComplianceFramework.NDPA
            })
        elif framework == ComplianceFramework.LEI:
            framework_context.update({
                "lei_code": context.sender_info.get("lei") or context.receiver_info.get("lei"),
                "entity_information": {
                    "sender": context.sender_info,
                    "receiver": context.receiver_info
                }
            })
        
        return framework_context
    
    def _execute_framework_validation(self, validator, framework_context: Dict[str, Any]) -> ValidationResult:
        """Execute framework-specific validation"""
        
        try:
            # The specific validation method depends on the validator type
            # This is a generic approach - each validator should have a validate method
            
            if hasattr(validator, 'validate_compliance'):
                result = validator.validate_compliance(framework_context)
            elif hasattr(validator, 'validate'):
                result = validator.validate(framework_context)
            elif hasattr(validator, 'assess_compliance'):
                result = validator.assess_compliance(framework_context)
            else:
                raise AttributeError(f"Validator {type(validator).__name__} has no compatible validation method")
            
            # Convert validator-specific result to ValidationResult
            return self._convert_to_validation_result(result, framework_context)
            
        except Exception as e:
            self.logger.error(f"Framework validation execution failed: {str(e)}")
            raise
    
    def _convert_to_validation_result(self, validator_result: Any, 
                                    framework_context: Dict[str, Any]) -> ValidationResult:
        """Convert validator-specific result to standard ValidationResult"""
        
        # This is a generic conversion - specific implementations would handle
        # the actual result structures from each validator
        
        framework = ComplianceFramework(framework_context["framework"])
        
        if hasattr(validator_result, '__dict__'):
            # Handle object results
            return ValidationResult(
                rule_id=getattr(validator_result, 'rule_id', f"{framework.value}_VALIDATION"),
                framework=framework,
                status=getattr(validator_result, 'status', ComplianceStatus.COMPLIANT),
                severity=getattr(validator_result, 'severity', ValidationSeverity.INFO),
                validation_timestamp=datetime.now(),
                validation_score=getattr(validator_result, 'score', 100.0),
                issues_found=getattr(validator_result, 'issues', []),
                recommendations=getattr(validator_result, 'recommendations', []),
                validation_evidence=getattr(validator_result, 'evidence', {}),
                business_context=framework_context
            )
        elif isinstance(validator_result, dict):
            # Handle dictionary results
            return ValidationResult(
                rule_id=validator_result.get('rule_id', f"{framework.value}_VALIDATION"),
                framework=framework,
                status=ComplianceStatus(validator_result.get('status', 'compliant')),
                severity=ValidationSeverity(validator_result.get('severity', 'info')),
                validation_timestamp=datetime.now(),
                validation_score=validator_result.get('score', 100.0),
                issues_found=validator_result.get('issues', []),
                recommendations=validator_result.get('recommendations', []),
                validation_evidence=validator_result.get('evidence', {}),
                business_context=framework_context
            )
        else:
            # Handle simple boolean or other results
            is_compliant = bool(validator_result)
            return ValidationResult(
                rule_id=f"{framework.value}_VALIDATION",
                framework=framework,
                status=ComplianceStatus.COMPLIANT if is_compliant else ComplianceStatus.NON_COMPLIANT,
                severity=ValidationSeverity.INFO if is_compliant else ValidationSeverity.MEDIUM,
                validation_timestamp=datetime.now(),
                validation_score=100.0 if is_compliant else 0.0,
                business_context=framework_context
            )
    
    def _calculate_overall_compliance(self, compliance_result: ComplianceResult):
        """Calculate overall compliance status and scores"""
        
        if not compliance_result.framework_results:
            compliance_result.overall_status = ComplianceStatus.ERROR
            compliance_result.overall_score = 0.0
            return
        
        # Calculate weighted score
        total_weighted_score = 0.0
        total_weight = 0.0
        
        # Count issues by severity
        critical_issues = 0
        high_issues = 0
        medium_issues = 0
        low_issues = 0
        
        compliant_frameworks = 0
        error_frameworks = 0
        
        for framework, result in compliance_result.framework_results.items():
            # Get framework weight
            weight = self.compliance_matrix.framework_weights.get(framework, 1.0)
            total_weight += weight
            total_weighted_score += result.validation_score * weight
            
            # Count framework status
            if result.status == ComplianceStatus.COMPLIANT:
                compliant_frameworks += 1
            elif result.status == ComplianceStatus.ERROR:
                error_frameworks += 1
            
            # Count issues by severity
            if result.severity == ValidationSeverity.CRITICAL:
                critical_issues += 1
            elif result.severity == ValidationSeverity.HIGH:
                high_issues += 1
            elif result.severity == ValidationSeverity.MEDIUM:
                medium_issues += 1
            elif result.severity == ValidationSeverity.LOW:
                low_issues += 1
        
        # Calculate overall score
        compliance_result.overall_score = total_weighted_score / total_weight if total_weight > 0 else 0.0
        
        # Update issue counts
        compliance_result.critical_issues = critical_issues
        compliance_result.high_issues = high_issues
        compliance_result.medium_issues = medium_issues
        compliance_result.low_issues = low_issues
        
        # Determine overall status
        if error_frameworks > 0:
            compliance_result.overall_status = ComplianceStatus.ERROR
        elif critical_issues > 0:
            compliance_result.overall_status = ComplianceStatus.NON_COMPLIANT
        elif high_issues > 0:
            compliance_result.overall_status = ComplianceStatus.PARTIALLY_COMPLIANT
        elif compliant_frameworks == len(compliance_result.framework_results):
            compliance_result.overall_status = ComplianceStatus.COMPLIANT
        else:
            compliance_result.overall_status = ComplianceStatus.PARTIALLY_COMPLIANT
    
    def _generate_compliance_recommendations(self, compliance_result: ComplianceResult) -> List[str]:
        """Generate overall compliance recommendations"""
        
        recommendations = []
        
        # Critical issue recommendations
        if compliance_result.critical_issues > 0:
            recommendations.append(f"Address {compliance_result.critical_issues} critical compliance issues immediately")
        
        # High issue recommendations
        if compliance_result.high_issues > 0:
            recommendations.append(f"Resolve {compliance_result.high_issues} high-priority compliance issues")
        
        # Framework-specific recommendations
        for framework, result in compliance_result.framework_results.items():
            if result.status != ComplianceStatus.COMPLIANT and result.recommendations:
                recommendations.extend([f"{framework.value}: {rec}" for rec in result.recommendations[:2]])  # Limit to top 2
        
        # Overall score recommendations
        if compliance_result.overall_score < 70:
            recommendations.append("Overall compliance score is below 70% - conduct comprehensive compliance review")
        elif compliance_result.overall_score < 90:
            recommendations.append("Consider implementing additional compliance measures to achieve >90% score")
        
        return recommendations
    
    def _generate_priority_actions(self, compliance_result: ComplianceResult) -> List[str]:
        """Generate priority action items"""
        
        actions = []
        
        # Critical framework failures
        for framework, result in compliance_result.framework_results.items():
            if result.status == ComplianceStatus.NON_COMPLIANT and result.severity == ValidationSeverity.CRITICAL:
                actions.append(f"URGENT: Fix critical {framework.value} compliance failure")
        
        # Nigerian regulatory priorities
        nigerian_frameworks = [ComplianceFramework.FIRS, ComplianceFramework.NITDA, ComplianceFramework.CAC]
        for framework in nigerian_frameworks:
            if framework in compliance_result.framework_results:
                result = compliance_result.framework_results[framework]
                if result.status != ComplianceStatus.COMPLIANT:
                    actions.append(f"Priority: Address {framework.value} compliance for Nigerian operations")
        
        # International compliance priorities
        if ComplianceFramework.PEPPOL in compliance_result.framework_results:
            peppol_result = compliance_result.framework_results[ComplianceFramework.PEPPOL]
            if peppol_result.status != ComplianceStatus.COMPLIANT:
                actions.append("Priority: Fix PEPPOL compliance for international transactions")
        
        return actions
    
    def _assess_business_risk(self, compliance_result: ComplianceResult) -> str:
        """Assess business risk level based on compliance results"""
        
        if compliance_result.critical_issues > 0:
            return "critical"
        elif compliance_result.high_issues > 2:
            return "high"
        elif compliance_result.overall_score < 70:
            return "high"
        elif compliance_result.overall_score < 85:
            return "medium"
        else:
            return "low"
    
    def _assess_regulatory_risk(self, compliance_result: ComplianceResult) -> str:
        """Assess regulatory risk level"""
        
        # Nigerian regulatory frameworks have higher weight
        nigerian_risk = False
        for framework in [ComplianceFramework.FIRS, ComplianceFramework.NITDA, ComplianceFramework.CAC]:
            if framework in compliance_result.framework_results:
                result = compliance_result.framework_results[framework]
                if result.status != ComplianceStatus.COMPLIANT:
                    nigerian_risk = True
                    break
        
        if nigerian_risk:
            return "critical"
        elif compliance_result.critical_issues > 0:
            return "high"
        elif compliance_result.high_issues > 0:
            return "medium"
        else:
            return "low"
    
    def _update_performance_metrics(self, compliance_result: ComplianceResult, 
                                  assessment_duration: float):
        """Update performance metrics"""
        
        self.performance_metrics["total_assessments"] += 1
        
        if compliance_result.overall_status != ComplianceStatus.ERROR:
            self.performance_metrics["successful_assessments"] += 1
        else:
            self.performance_metrics["failed_assessments"] += 1
        
        # Update average assessment time
        total_assessments = self.performance_metrics["total_assessments"]
        current_avg = self.performance_metrics["average_assessment_time"]
        new_avg = ((current_avg * (total_assessments - 1)) + assessment_duration) / total_assessments
        self.performance_metrics["average_assessment_time"] = new_avg
    
    def _update_framework_performance(self, framework: ComplianceFramework, 
                                    duration: float, success: bool):
        """Update framework-specific performance metrics"""
        
        if framework not in self.performance_metrics["framework_performance"]:
            self.performance_metrics["framework_performance"][framework] = {
                "total_validations": 0,
                "successful_validations": 0,
                "average_duration": 0.0
            }
        
        fw_metrics = self.performance_metrics["framework_performance"][framework]
        fw_metrics["total_validations"] += 1
        
        if success:
            fw_metrics["successful_validations"] += 1
        
        # Update average duration
        total = fw_metrics["total_validations"]
        current_avg = fw_metrics["average_duration"]
        fw_metrics["average_duration"] = ((current_avg * (total - 1)) + duration) / total
    
    def _log_audit_event(self, event_type: str, compliance_id: str = None,
                        description: str = "", severity_level: ValidationSeverity = ValidationSeverity.INFO,
                        technical_details: Dict[str, Any] = None):
        """Log audit event"""
        
        event = AuditEvent(
            event_id=f"AUDIT_{uuid.uuid4().hex[:8].upper()}",
            timestamp=datetime.now(),
            event_type=event_type,
            compliance_id=compliance_id,
            event_description=description,
            event_category="compliance_orchestration",
            severity_level=severity_level,
            source_system="ComplianceOrchestrator",
            technical_details=technical_details or {}
        )
        
        self.audit_events.append(event)
        
        # Keep only last 1000 events in memory
        if len(self.audit_events) > 1000:
            self.audit_events = self.audit_events[-1000:]
    
    def get_performance_metrics(self) -> Dict[str, Any]:
        """Get current performance metrics"""
        return self.performance_metrics.copy()
    
    def get_audit_events(self, limit: int = 100) -> List[AuditEvent]:
        """Get recent audit events"""
        return self.audit_events[-limit:]
    
    def get_compliance_matrix(self) -> ComplianceMatrix:
        """Get compliance requirements matrix"""
        return self.compliance_matrix