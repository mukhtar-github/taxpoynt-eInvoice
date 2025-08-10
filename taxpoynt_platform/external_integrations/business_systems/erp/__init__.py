"""
External Integrations - ERP Business Systems

Specific ERP system connector implementations.
Uses the universal connector framework for consistent interfaces.
"""

from ...connector_framework import BaseERPConnector, GenericERPConnector
from .odoo import OdooConnector
from .sap import SAPConnector
from .oracle import OracleERPConnector

__all__ = [
    "BaseERPConnector",
    "GenericERPConnector", 
    "OdooConnector",
    "SAPConnector",
    "OracleERPConnector"
]