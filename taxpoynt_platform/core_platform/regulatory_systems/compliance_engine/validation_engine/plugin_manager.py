"""
Validation Plugin Manager
=========================
Manages validation plugins for different compliance frameworks and provides
plugin lifecycle management, discovery, and execution coordination.
"""

import logging
import importlib
import inspect
from typing import Dict, Any, List, Optional, Type, Protocol
from datetime import datetime
from abc import ABC, abstractmethod

from .models import (
    ValidationPlugin, PluginStatus, ValidationPhase, ValidationRequest,
    PluginExecutionResult
)
from ..orchestrator.models import ComplianceFramework, ValidationResult

logger = logging.getLogger(__name__)

class ValidationPluginInterface(Protocol):
    """Protocol defining the interface for validation plugins"""
    
    def validate(self, data: Dict[str, Any], context: Dict[str, Any]) -> PluginExecutionResult:
        """Execute validation for the framework"""
        ...
    
    def get_supported_rules(self) -> List[str]:
        """Get list of supported rule IDs"""
        ...
    
    def is_applicable(self, data: Dict[str, Any]) -> bool:
        """Check if plugin is applicable to the data"""
        ...

class BaseValidationPlugin(ABC):
    """Base class for validation plugins"""
    
    def __init__(self, framework: ComplianceFramework):
        """Initialize base plugin"""
        self.framework = framework
        self.logger = logging.getLogger(f"{__name__}.{framework.value}")
        self.plugin_id = f"{framework.value}_validator"
        self.version = "1.0.0"
    
    @abstractmethod
    def validate(self, data: Dict[str, Any], context: Dict[str, Any]) -> PluginExecutionResult:
        """Execute validation - must be implemented by subclasses"""
        pass
    
    @abstractmethod
    def get_supported_rules(self) -> List[str]:
        """Get supported rule IDs - must be implemented by subclasses"""
        pass
    
    def is_applicable(self, data: Dict[str, Any]) -> bool:
        """Default applicability check - can be overridden"""
        return True
    
    def get_plugin_info(self) -> ValidationPlugin:
        """Get plugin information"""
        return ValidationPlugin(
            plugin_id=self.plugin_id,
            plugin_name=f"{self.framework.value.title()} Validator",
            framework=self.framework,
            version=self.version,
            description=f"Validation plugin for {self.framework.value} compliance",
            author="TaxPoynt Platform",
            supported_versions=["1.0.0"],
            supported_phases=[ValidationPhase.BUSINESS_RULES],
            rule_categories=["all"],
            data_requirements=[]
        )

class FIRSValidationPlugin(BaseValidationPlugin):
    """FIRS compliance validation plugin"""
    
    def __init__(self):
        super().__init__(ComplianceFramework.FIRS)
    
    def validate(self, data: Dict[str, Any], context: Dict[str, Any]) -> PluginExecutionResult:
        """Execute FIRS validation"""
        start_time = datetime.now()
        validation_results = []
        
        try:
            # Import FIRS validator
            from ...nigerian_regulators.firs_compliance.firs_validator import FIRSValidator
            
            validator = FIRSValidator()
            firs_result = validator.validate_invoice_compliance(data)
            
            # Convert FIRS result to ValidationResult format
            if firs_result.is_compliant:
                from ..orchestrator.models import ComplianceStatus, ValidationSeverity
                
                validation_result = ValidationResult(
                    rule_id="FIRS_OVERALL",
                    framework=self.framework,
                    status=ComplianceStatus.COMPLIANT,
                    severity=ValidationSeverity.INFO,
                    validation_timestamp=datetime.now(),
                    validation_score=firs_result.compliance_score,
                    issues_found=[],
                    recommendations=firs_result.recommendations
                )
                validation_results.append(validation_result)
            else:
                validation_result = ValidationResult(
                    rule_id="FIRS_OVERALL",
                    framework=self.framework,
                    status=ComplianceStatus.NON_COMPLIANT,
                    severity=ValidationSeverity.HIGH,
                    validation_timestamp=datetime.now(),
                    validation_score=firs_result.compliance_score,
                    issues_found=firs_result.errors,
                    recommendations=firs_result.recommendations
                )
                validation_results.append(validation_result)
            
            execution_duration = (datetime.now() - start_time).total_seconds() * 1000
            
            return PluginExecutionResult(
                plugin_id=self.plugin_id,
                framework=self.framework,
                phase=ValidationPhase.BUSINESS_RULES,
                execution_start=start_time,
                execution_duration_ms=execution_duration,
                status=ComplianceStatus.COMPLIANT if firs_result.is_compliant else ComplianceStatus.NON_COMPLIANT,
                validation_results=validation_results,
                rules_processed=1
            )
            
        except Exception as e:
            self.logger.error(f"FIRS validation plugin failed: {str(e)}")
            execution_duration = (datetime.now() - start_time).total_seconds() * 1000
            
            return PluginExecutionResult(
                plugin_id=self.plugin_id,
                framework=self.framework,
                phase=ValidationPhase.BUSINESS_RULES,
                execution_start=start_time,
                execution_duration_ms=execution_duration,
                status=ComplianceStatus.ERROR,
                validation_results=[],
                rules_processed=0,
                errors=[f"Plugin execution error: {str(e)}"]
            )
    
    def get_supported_rules(self) -> List[str]:
        """Get supported FIRS rules"""
        return [
            "FIRS_TIN_VALIDATION",
            "FIRS_VAT_CALCULATION",
            "FIRS_INVOICE_FORMAT",
            "FIRS_BUSINESS_RULES",
            "FIRS_OVERALL"
        ]

class CACValidationPlugin(BaseValidationPlugin):
    """CAC compliance validation plugin"""
    
    def __init__(self):
        super().__init__(ComplianceFramework.CAC)
    
    def validate(self, data: Dict[str, Any], context: Dict[str, Any]) -> PluginExecutionResult:
        """Execute CAC validation"""
        start_time = datetime.now()
        validation_results = []
        
        try:
            # Import CAC validator
            from ...nigerian_regulators.cac_compliance.cac_validator import CACValidator
            
            validator = CACValidator()
            
            # Extract RC number from data
            rc_number = data.get('rc_number') or data.get('supplier_rc_number', '')
            
            if rc_number:
                cac_result = validator.validate_entity_compliance(rc_number)
                
                # Convert CAC result to ValidationResult format
                from ..orchestrator.models import ComplianceStatus, ValidationSeverity
                
                validation_result = ValidationResult(
                    rule_id="CAC_OVERALL",
                    framework=self.framework,
                    status=ComplianceStatus.COMPLIANT if cac_result.is_compliant else ComplianceStatus.NON_COMPLIANT,
                    severity=ValidationSeverity.HIGH if not cac_result.is_compliant else ValidationSeverity.INFO,
                    validation_timestamp=datetime.now(),
                    validation_score=cac_result.compliance_score,
                    issues_found=cac_result.errors,
                    recommendations=cac_result.recommendations
                )
                validation_results.append(validation_result)
            else:
                # No RC number provided
                validation_result = ValidationResult(
                    rule_id="CAC_RC_REQUIRED",
                    framework=self.framework,
                    status=ComplianceStatus.NON_COMPLIANT,
                    severity=ValidationSeverity.MEDIUM,
                    validation_timestamp=datetime.now(),
                    validation_score=0.0,
                    issues_found=["RC number not provided"],
                    recommendations=["Provide valid RC number for entity validation"]
                )
                validation_results.append(validation_result)
            
            execution_duration = (datetime.now() - start_time).total_seconds() * 1000
            
            return PluginExecutionResult(
                plugin_id=self.plugin_id,
                framework=self.framework,
                phase=ValidationPhase.BUSINESS_RULES,
                execution_start=start_time,
                execution_duration_ms=execution_duration,
                status=ComplianceStatus.COMPLIANT if validation_results and validation_results[0].status == ComplianceStatus.COMPLIANT else ComplianceStatus.NON_COMPLIANT,
                validation_results=validation_results,
                rules_processed=1
            )
            
        except Exception as e:
            self.logger.error(f"CAC validation plugin failed: {str(e)}")
            execution_duration = (datetime.now() - start_time).total_seconds() * 1000
            
            return PluginExecutionResult(
                plugin_id=self.plugin_id,
                framework=self.framework,
                phase=ValidationPhase.BUSINESS_RULES,
                execution_start=start_time,
                execution_duration_ms=execution_duration,
                status=ComplianceStatus.ERROR,
                validation_results=[],
                rules_processed=0,
                errors=[f"Plugin execution error: {str(e)}"]
            )
    
    def get_supported_rules(self) -> List[str]:
        """Get supported CAC rules"""
        return [
            "CAC_RC_VALIDATION",
            "CAC_ENTITY_STRUCTURE",
            "CAC_GOVERNANCE",
            "CAC_FILING_COMPLIANCE",
            "CAC_OVERALL"
        ]

class ValidationPluginManager:
    """
    Manages validation plugins for different compliance frameworks
    """
    
    def __init__(self):
        """Initialize plugin manager"""
        self.logger = logging.getLogger(__name__)
        
        # Plugin registry
        self.plugins: Dict[ComplianceFramework, BaseValidationPlugin] = {}
        self.plugin_metadata: Dict[ComplianceFramework, ValidationPlugin] = {}
        
        # Plugin performance tracking
        self.performance_metrics: Dict[str, Dict[str, Any]] = {}
        
        # Load built-in plugins
        self._load_builtin_plugins()
        
        self.logger.info(f"Plugin Manager initialized with {len(self.plugins)} plugins")
    
    def get_plugin(self, framework: ComplianceFramework) -> Optional[BaseValidationPlugin]:
        """
        Get plugin for specified framework
        
        Args:
            framework: Compliance framework
            
        Returns:
            Validation plugin or None if not found
        """
        return self.plugins.get(framework)
    
    def is_framework_available(self, framework: ComplianceFramework) -> bool:
        """
        Check if framework plugin is available
        
        Args:
            framework: Compliance framework to check
            
        Returns:
            True if plugin is available and active
        """
        plugin = self.plugins.get(framework)
        if not plugin:
            return False
        
        plugin_info = self.plugin_metadata.get(framework)
        return plugin_info and plugin_info.status == PluginStatus.ACTIVE
    
    def register_plugin(self, plugin: BaseValidationPlugin) -> bool:
        """
        Register a new validation plugin
        
        Args:
            plugin: Plugin to register
            
        Returns:
            True if registration successful
        """
        try:
            framework = plugin.framework
            
            # Validate plugin interface
            if not self._validate_plugin_interface(plugin):
                self.logger.error(f"Plugin {plugin.plugin_id} does not implement required interface")
                return False
            
            # Register plugin
            self.plugins[framework] = plugin
            self.plugin_metadata[framework] = plugin.get_plugin_info()
            
            # Initialize performance tracking
            self.performance_metrics[plugin.plugin_id] = {
                'total_executions': 0,
                'successful_executions': 0,
                'failed_executions': 0,
                'total_execution_time': 0.0,
                'average_execution_time': 0.0,
                'last_execution': None
            }
            
            self.logger.info(f"Registered plugin: {plugin.plugin_id} for framework: {framework}")
            return True
            
        except Exception as e:
            self.logger.error(f"Plugin registration failed: {str(e)}")
            return False
    
    def unregister_plugin(self, framework: ComplianceFramework) -> bool:
        """
        Unregister plugin for framework
        
        Args:
            framework: Framework to unregister
            
        Returns:
            True if unregistration successful
        """
        if framework in self.plugins:
            plugin_id = self.plugins[framework].plugin_id
            del self.plugins[framework]
            del self.plugin_metadata[framework]
            
            if plugin_id in self.performance_metrics:
                del self.performance_metrics[plugin_id]
            
            self.logger.info(f"Unregistered plugin for framework: {framework}")
            return True
        
        return False
    
    def get_plugin_info(self, framework: ComplianceFramework) -> Optional[ValidationPlugin]:
        """
        Get plugin information
        
        Args:
            framework: Target framework
            
        Returns:
            Plugin information or None
        """
        return self.plugin_metadata.get(framework)
    
    def get_all_plugins(self) -> Dict[ComplianceFramework, ValidationPlugin]:
        """
        Get information for all registered plugins
        
        Returns:
            Dictionary of plugin information by framework
        """
        return self.plugin_metadata.copy()
    
    def get_performance_metrics(self) -> Dict[str, Dict[str, Any]]:
        """
        Get performance metrics for all plugins
        
        Returns:
            Dictionary of performance metrics by plugin ID
        """
        return self.performance_metrics.copy()
    
    def execute_plugin(
        self,
        framework: ComplianceFramework,
        data: Dict[str, Any],
        context: Dict[str, Any]
    ) -> Optional[PluginExecutionResult]:
        """
        Execute plugin for framework
        
        Args:
            framework: Target framework
            data: Data to validate
            context: Validation context
            
        Returns:
            Plugin execution result or None if plugin not found
        """
        plugin = self.plugins.get(framework)
        if not plugin:
            self.logger.warning(f"No plugin found for framework: {framework}")
            return None
        
        try:
            start_time = datetime.now()
            
            # Check if plugin is applicable
            if not plugin.is_applicable(data):
                self.logger.debug(f"Plugin {plugin.plugin_id} not applicable to data")
                return None
            
            # Execute plugin
            result = plugin.validate(data, context)
            
            # Update performance metrics
            execution_time = (datetime.now() - start_time).total_seconds() * 1000
            self._update_performance_metrics(plugin.plugin_id, execution_time, result.status != ComplianceStatus.ERROR)
            
            return result
            
        except Exception as e:
            self.logger.error(f"Plugin execution failed for {framework}: {str(e)}")
            execution_time = (datetime.now() - start_time).total_seconds() * 1000
            self._update_performance_metrics(plugin.plugin_id, execution_time, False)
            
            # Return error result
            return PluginExecutionResult(
                plugin_id=plugin.plugin_id,
                framework=framework,
                phase=ValidationPhase.BUSINESS_RULES,
                execution_start=start_time,
                execution_duration_ms=execution_time,
                status=ComplianceStatus.ERROR,
                validation_results=[],
                rules_processed=0,
                errors=[f"Plugin execution error: {str(e)}"]
            )
    
    def health_check(self) -> Dict[str, Any]:
        """
        Perform health check on all plugins
        
        Returns:
            Dictionary with health check results
        """
        health_status = {
            'overall_status': 'healthy',
            'total_plugins': len(self.plugins),
            'active_plugins': 0,
            'inactive_plugins': 0,
            'plugin_status': {}
        }
        
        for framework, plugin in self.plugins.items():
            try:
                # Simple health check - try to get plugin info
                plugin_info = plugin.get_plugin_info()
                health_status['plugin_status'][framework.value] = {
                    'status': 'healthy',
                    'plugin_id': plugin.plugin_id,
                    'version': plugin_info.version
                }
                health_status['active_plugins'] += 1
                
            except Exception as e:
                health_status['plugin_status'][framework.value] = {
                    'status': 'unhealthy',
                    'error': str(e)
                }
                health_status['inactive_plugins'] += 1
                health_status['overall_status'] = 'degraded'
        
        if health_status['inactive_plugins'] == health_status['total_plugins']:
            health_status['overall_status'] = 'unhealthy'
        
        return health_status
    
    # Private helper methods
    
    def _load_builtin_plugins(self):
        """Load built-in validation plugins"""
        builtin_plugins = [
            FIRSValidationPlugin(),
            CACValidationPlugin()
        ]
        
        for plugin in builtin_plugins:
            self.register_plugin(plugin)
        
        self.logger.info(f"Loaded {len(builtin_plugins)} built-in plugins")
    
    def _validate_plugin_interface(self, plugin: BaseValidationPlugin) -> bool:
        """Validate that plugin implements required interface"""
        required_methods = ['validate', 'get_supported_rules', 'is_applicable']
        
        for method_name in required_methods:
            if not hasattr(plugin, method_name):
                return False
            
            method = getattr(plugin, method_name)
            if not callable(method):
                return False
        
        return True
    
    def _update_performance_metrics(self, plugin_id: str, execution_time: float, success: bool):
        """Update performance metrics for plugin"""
        if plugin_id not in self.performance_metrics:
            self.performance_metrics[plugin_id] = {
                'total_executions': 0,
                'successful_executions': 0,
                'failed_executions': 0,
                'total_execution_time': 0.0,
                'average_execution_time': 0.0,
                'last_execution': None
            }
        
        metrics = self.performance_metrics[plugin_id]
        metrics['total_executions'] += 1
        metrics['total_execution_time'] += execution_time
        metrics['average_execution_time'] = metrics['total_execution_time'] / metrics['total_executions']
        metrics['last_execution'] = datetime.now().isoformat()
        
        if success:
            metrics['successful_executions'] += 1
        else:
            metrics['failed_executions'] += 1
    
    def discover_plugins(self, plugin_directory: str) -> List[str]:
        """
        Discover plugins in directory (for future extensibility)
        
        Args:
            plugin_directory: Directory to search for plugins
            
        Returns:
            List of discovered plugin module names
        """
        # This would implement plugin discovery from filesystem
        # For now, return empty list
        self.logger.info(f"Plugin discovery not yet implemented for directory: {plugin_directory}")
        return []
    
    def load_external_plugin(self, plugin_module_path: str) -> bool:
        """
        Load external plugin from module path
        
        Args:
            plugin_module_path: Python module path to plugin
            
        Returns:
            True if plugin loaded successfully
        """
        try:
            # Import the plugin module
            module = importlib.import_module(plugin_module_path)
            
            # Find plugin classes in module
            for name, obj in inspect.getmembers(module):
                if (inspect.isclass(obj) and 
                    issubclass(obj, BaseValidationPlugin) and 
                    obj != BaseValidationPlugin):
                    
                    # Instantiate and register plugin
                    plugin_instance = obj()
                    return self.register_plugin(plugin_instance)
            
            self.logger.warning(f"No valid plugin classes found in module: {plugin_module_path}")
            return False
            
        except Exception as e:
            self.logger.error(f"Failed to load external plugin {plugin_module_path}: {str(e)}")
            return False