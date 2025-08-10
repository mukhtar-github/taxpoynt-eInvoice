"""
TaxPoynt Platform Testing Suite
==============================

Comprehensive testing framework for the entire TaxPoynt e-Invoice platform.
Organized by testing scope and purpose for maximum coverage and maintainability.

Testing Architecture:
- unit/          - Individual component testing
- integration/   - Service-to-service testing  
- uat/          - User acceptance and FIRS compliance testing
- fixtures/     - Shared test data and utilities

This structure supports both development testing and regulatory UAT sessions.
"""

__version__ = "1.0.0"
__author__ = "TaxPoynt Platform Team"

# Testing levels hierarchy:
# 1. Unit Tests - Individual component testing
# 2. Integration Tests - Service-to-service testing  
# 3. UAT Tests - User acceptance and compliance testing
# 4. Performance Tests - Load, stress, and scalability testing