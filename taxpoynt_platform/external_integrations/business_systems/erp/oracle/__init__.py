"""
Oracle ERP Cloud Connector Package
System Integrator (SI) role functionality for Oracle ERP Cloud integration.

This package provides modular Oracle ERP Cloud connectivity including:
- REST API connection and authentication (OAuth 2.0)
- Data extraction from Oracle Financial and CRM modules
- FIRS format transformation
- Connection testing and validation

Supported Oracle Modules:
- Invoices Module: /fscmRestApi/resources/11.13.18.05/invoices
- Customers Module: /crmRestApi/resources/11.13.18.05/accounts
- Receivables Module: /fscmRestApi/resources/11.13.18.05/receivables
- ERP Integrations: /fscmRestApi/resources/11.13.18.05/erpintegrations
"""

from .connector import OracleERPConnector
from .exceptions import OracleAPIError, OracleAuthenticationError

__all__ = [
    "OracleERPConnector",
    "OracleAPIError",
    "OracleAuthenticationError"
]