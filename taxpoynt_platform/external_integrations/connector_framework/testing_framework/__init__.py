"""
Testing Framework for Connector Framework
=========================================

Comprehensive testing utilities for financial system connectors and classification engine.
Provides mock providers, integration tests, and classification accuracy testing.
"""

from .mock_providers import *
from .integration_tests import *
from .classification_tests import *

__version__ = "1.0.0"
__author__ = "TaxPoynt Platform Team"

__all__ = [
    # Mock providers
    "MockBankingProvider",
    "MockPaymentProvider", 
    "MockForexProvider",
    "MockOpenAIClient",
    "MockRedisClient",
    
    # Test utilities
    "IntegrationTestSuite",
    "ConnectorTestCase",
    "ClassificationTestSuite",
    "AccuracyTester",
    
    # Test data generators
    "generate_test_transactions",
    "generate_nigerian_test_data",
    "create_mock_user_context"
]