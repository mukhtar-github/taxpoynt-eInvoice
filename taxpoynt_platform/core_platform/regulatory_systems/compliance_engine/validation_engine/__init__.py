"""
Universal Compliance Validation Engine
=====================================
Cross-framework validation engine that provides unified validation logic for all regulatory frameworks.

This validation engine serves as the central processing layer that:
- Coordinates validation across multiple compliance frameworks
- Implements universal rule engine with pluggable compliance modules
- Handles rule conflict resolution and result aggregation
- Provides consistent validation interfaces for all frameworks

Core Components:
- universal_validator.py: Main universal validation engine
- rule_engine.py: Universal rule processing and conflict resolution engine
- validation_aggregator.py: Result aggregation and cross-framework analysis
- plugin_manager.py: Plugin system for framework-specific validators
- models.py: Validation engine specific data models
"""

from .universal_validator import UniversalComplianceValidator
from .rule_engine import ComplianceRuleEngine
from .validation_aggregator import ValidationAggregator
from .plugin_manager import ValidationPluginManager
from .models import (
    ValidationRequest, ValidationResponse, RuleConflict,
    ValidationPlugin, CrossFrameworkResult, AggregatedValidationResult
)

__all__ = [
    'UniversalComplianceValidator',
    'ComplianceRuleEngine',
    'ValidationAggregator',
    'ValidationPluginManager',
    'ValidationRequest',
    'ValidationResponse',
    'RuleConflict',
    'ValidationPlugin',
    'CrossFrameworkResult',
    'AggregatedValidationResult'
]