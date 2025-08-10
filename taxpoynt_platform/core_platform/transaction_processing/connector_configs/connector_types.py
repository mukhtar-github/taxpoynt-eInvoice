"""
Connector Type Definitions
==========================

Comprehensive enumeration of all supported external connector types in the
TaxPoynt platform. Each connector type has specific characteristics that
influence transaction processing behavior.

This module defines the complete taxonomy of business systems that TaxPoynt
integrates with for Nigerian e-invoicing compliance.
"""

from enum import Enum
from typing import Dict, List, Optional
from dataclasses import dataclass


class ConnectorType(Enum):
    """
    Business system connectors that generate transactions requiring invoice processing.
    
    Focus: External Business Systems → Transaction Processing → Invoice Generation → FIRS Compliance
    
    These are the actual business systems that TaxPoynt customers use to run their
    operations, and TaxPoynt helps them generate compliant invoices from their data.
    """
    
    # ERP Systems (Primary business transaction sources)
    ERP_SAP = "erp_sap"
    ERP_ORACLE = "erp_oracle"
    ERP_MICROSOFT_DYNAMICS = "erp_microsoft_dynamics"
    ERP_NETSUITE = "erp_netsuite"
    ERP_ODOO = "erp_odoo"
    ERP_SAGE = "erp_sage"
    
    # CRM Systems (Service billing and customer transactions)
    CRM_SALESFORCE = "crm_salesforce"
    CRM_HUBSPOT = "crm_hubspot"
    CRM_MICROSOFT_DYNAMICS_CRM = "crm_microsoft_dynamics_crm"
    CRM_ZOHO = "crm_zoho"
    CRM_PIPEDRIVE = "crm_pipedrive"
    
    # POS Systems (Retail and hospitality transactions)
    POS_RETAIL = "pos_retail"
    POS_HOSPITALITY = "pos_hospitality"
    POS_ECOMMERCE = "pos_ecommerce"
    
    # E-commerce Platforms (Online sales transactions)
    ECOMMERCE_SHOPIFY = "ecommerce_shopify"
    ECOMMERCE_WOOCOMMERCE = "ecommerce_woocommerce"
    ECOMMERCE_MAGENTO = "ecommerce_magento"
    ECOMMERCE_JUMIA = "ecommerce_jumia"
    ECOMMERCE_BIGCOMMERCE = "ecommerce_bigcommerce"
    
    # Accounting Systems (Financial record systems)
    ACCOUNTING_QUICKBOOKS = "accounting_quickbooks"
    ACCOUNTING_XERO = "accounting_xero"
    ACCOUNTING_WAVE = "accounting_wave"
    ACCOUNTING_FRESHBOOKS = "accounting_freshbooks"
    ACCOUNTING_SAGE = "accounting_sage"
    
    # Inventory Management (Stock and supply chain transactions)
    INVENTORY_FISHBOWL = "inventory_fishbowl"
    INVENTORY_CIN7 = "inventory_cin7"
    
    # Banking & Financial Systems (Transaction data for invoice generation)
    BANKING_OPEN_BANKING = "banking_open_banking"
    
    # Nigerian Payment Processors (Transaction data collection for compliance)
    PAYMENT_PAYSTACK = "payment_paystack"
    PAYMENT_FLUTTERWAVE = "payment_flutterwave"
    PAYMENT_MONIEPOINT = "payment_moniepoint"
    PAYMENT_OPAY = "payment_opay"
    PAYMENT_PALMPAY = "payment_palmpay"
    PAYMENT_INTERSWITCH = "payment_interswitch"


class ConnectorCategory(Enum):
    """High-level categorization of connector types."""
    FINANCIAL_DATA = "financial_data"          # Banking transaction data
    BUSINESS_MANAGEMENT = "business_management" # ERP, Accounting systems  
    CUSTOMER_MANAGEMENT = "customer_management" # CRM systems
    SALES_CHANNEL = "sales_channel"            # POS, E-commerce
    INVENTORY_MANAGEMENT = "inventory_management" # Stock systems
    PAYMENT_PROCESSING = "payment_processing"  # Payment processors
    MARKET_DATA = "market_data"                # Market/pricing data


class DataStructureLevel(Enum):
    """Level of data structure from the connector."""
    HIGHLY_STRUCTURED = "highly_structured"      # ERP, Accounting systems
    MODERATELY_STRUCTURED = "moderately_structured"  # CRM, E-commerce
    SEMI_STRUCTURED = "semi_structured"          # POS, some banking
    UNSTRUCTURED = "unstructured"               # Raw banking webhooks, USSD


class RiskProfile(Enum):
    """Default risk profile for connector type."""
    LOW_RISK = "low_risk"          # Trusted business systems (ERP, Accounting)
    MEDIUM_RISK = "medium_risk"    # Customer-facing systems (CRM, E-commerce)
    HIGH_RISK = "high_risk"        # Financial transactions (Banking, Payments)
    VARIABLE_RISK = "variable_risk" # Context-dependent (POS, USSD)


@dataclass
class ConnectorCharacteristics:
    """Characteristics that define how a connector type should be processed."""
    category: ConnectorCategory
    data_structure_level: DataStructureLevel
    default_risk_profile: RiskProfile
    requires_fraud_detection: bool
    requires_customer_matching: bool
    supports_batch_processing: bool
    typical_transaction_volume: str  # "low", "medium", "high", "very_high"
    nigerian_compliance_requirements: List[str]
    data_quality_expectations: str  # "high", "medium", "low"


# Connector type characteristics mapping
CONNECTOR_CHARACTERISTICS: Dict[ConnectorType, ConnectorCharacteristics] = {
    
    # Banking & Financial Systems
    ConnectorType.BANKING_OPEN_BANKING: ConnectorCharacteristics(
        category=ConnectorCategory.FINANCIAL,
        data_structure_level=DataStructureLevel.SEMI_STRUCTURED,
        default_risk_profile=RiskProfile.HIGH_RISK,
        requires_fraud_detection=True,
        requires_customer_matching=True,
        supports_batch_processing=True,
        typical_transaction_volume="very_high",
        nigerian_compliance_requirements=[
            "CBN_GUIDELINES", "ANTI_MONEY_LAUNDERING", "KYC_VERIFICATION",
            "TRANSACTION_REPORTING", "FIRS_REPORTING"
        ],
        data_quality_expectations="medium"
    ),
    
    ConnectorType.BANKING_NIBSS: ConnectorCharacteristics(
        category=ConnectorCategory.FINANCIAL,
        data_structure_level=DataStructureLevel.MODERATELY_STRUCTURED,
        default_risk_profile=RiskProfile.HIGH_RISK,
        requires_fraud_detection=True,
        requires_customer_matching=True,
        supports_batch_processing=True,
        typical_transaction_volume="very_high",
        nigerian_compliance_requirements=[
            "NIBSS_STANDARDS", "CBN_GUIDELINES", "ANTI_MONEY_LAUNDERING",
            "FIRS_REPORTING", "INTER_BANK_COMPLIANCE"
        ],
        data_quality_expectations="high"
    ),
    
    ConnectorType.USSD_MTN: ConnectorCharacteristics(
        category=ConnectorCategory.FINANCIAL,
        data_structure_level=DataStructureLevel.UNSTRUCTURED,
        default_risk_profile=RiskProfile.VARIABLE_RISK,
        requires_fraud_detection=True,
        requires_customer_matching=True,
        supports_batch_processing=False,
        typical_transaction_volume="high",
        nigerian_compliance_requirements=[
            "USSD_REGULATIONS", "CBN_GUIDELINES", "CONSUMER_PROTECTION",
            "FIRS_REPORTING"
        ],
        data_quality_expectations="low"
    ),
    
    # ERP Systems
    ConnectorType.ERP_SAP: ConnectorCharacteristics(
        category=ConnectorCategory.BUSINESS_MANAGEMENT,
        data_structure_level=DataStructureLevel.HIGHLY_STRUCTURED,
        default_risk_profile=RiskProfile.LOW_RISK,
        requires_fraud_detection=False,
        requires_customer_matching=True,
        supports_batch_processing=True,
        typical_transaction_volume="high",
        nigerian_compliance_requirements=[
            "ACCOUNTING_STANDARDS", "AUDIT_TRAIL", "FIRS_REPORTING",
            "CORPORATE_GOVERNANCE", "TAX_COMPLIANCE"
        ],
        data_quality_expectations="high"
    ),
    
    ConnectorType.ERP_ORACLE: ConnectorCharacteristics(
        category=ConnectorCategory.BUSINESS_MANAGEMENT,
        data_structure_level=DataStructureLevel.HIGHLY_STRUCTURED,
        default_risk_profile=RiskProfile.LOW_RISK,
        requires_fraud_detection=False,
        requires_customer_matching=True,
        supports_batch_processing=True,
        typical_transaction_volume="high",
        nigerian_compliance_requirements=[
            "ACCOUNTING_STANDARDS", "AUDIT_TRAIL", "FIRS_REPORTING",
            "CORPORATE_GOVERNANCE", "TAX_COMPLIANCE"
        ],
        data_quality_expectations="high"
    ),
    
    ConnectorType.ERP_ODOO: ConnectorCharacteristics(
        category=ConnectorCategory.BUSINESS_MANAGEMENT,
        data_structure_level=DataStructureLevel.HIGHLY_STRUCTURED,
        default_risk_profile=RiskProfile.LOW_RISK,
        requires_fraud_detection=False,
        requires_customer_matching=True,
        supports_batch_processing=True,
        typical_transaction_volume="medium",
        nigerian_compliance_requirements=[
            "ACCOUNTING_STANDARDS", "FIRS_REPORTING", "SME_COMPLIANCE"
        ],
        data_quality_expectations="high"
    ),
    
    # CRM Systems
    ConnectorType.CRM_SALESFORCE: ConnectorCharacteristics(
        category=ConnectorCategory.CUSTOMER_MANAGEMENT,
        data_structure_level=DataStructureLevel.MODERATELY_STRUCTURED,
        default_risk_profile=RiskProfile.MEDIUM_RISK,
        requires_fraud_detection=False,
        requires_customer_matching=True,
        supports_batch_processing=True,
        typical_transaction_volume="medium",
        nigerian_compliance_requirements=[
            "SERVICE_BILLING", "CUSTOMER_DATA_PROTECTION", "FIRS_REPORTING"
        ],
        data_quality_expectations="high"
    ),
    
    ConnectorType.CRM_HUBSPOT: ConnectorCharacteristics(
        category=ConnectorCategory.CUSTOMER_MANAGEMENT,
        data_structure_level=DataStructureLevel.MODERATELY_STRUCTURED,
        default_risk_profile=RiskProfile.MEDIUM_RISK,
        requires_fraud_detection=False,
        requires_customer_matching=True,
        supports_batch_processing=True,
        typical_transaction_volume="medium",
        nigerian_compliance_requirements=[
            "SERVICE_BILLING", "CUSTOMER_DATA_PROTECTION", "FIRS_REPORTING"
        ],
        data_quality_expectations="high"
    ),
    
    # POS Systems
    ConnectorType.POS_RETAIL: ConnectorCharacteristics(
        category=ConnectorCategory.SALES_CHANNEL,
        data_structure_level=DataStructureLevel.SEMI_STRUCTURED,
        default_risk_profile=RiskProfile.MEDIUM_RISK,
        requires_fraud_detection=True,
        requires_customer_matching=False,
        supports_batch_processing=True,
        typical_transaction_volume="high",
        nigerian_compliance_requirements=[
            "RETAIL_REGULATIONS", "VAT_COMPLIANCE", "RECEIPT_REQUIREMENTS",
            "FIRS_REPORTING"
        ],
        data_quality_expectations="medium"
    ),
    
    # E-commerce Platforms
    ConnectorType.ECOMMERCE_SHOPIFY: ConnectorCharacteristics(
        category=ConnectorCategory.SALES_CHANNEL,
        data_structure_level=DataStructureLevel.MODERATELY_STRUCTURED,
        default_risk_profile=RiskProfile.MEDIUM_RISK,
        requires_fraud_detection=True,
        requires_customer_matching=True,
        supports_batch_processing=True,
        typical_transaction_volume="medium",
        nigerian_compliance_requirements=[
            "ECOMMERCE_REGULATIONS", "VAT_COMPLIANCE", "CONSUMER_PROTECTION",
            "FIRS_REPORTING"
        ],
        data_quality_expectations="medium"
    ),
    
    ConnectorType.ECOMMERCE_JUMIA: ConnectorCharacteristics(
        category=ConnectorCategory.SALES_CHANNEL,
        data_structure_level=DataStructureLevel.MODERATELY_STRUCTURED,
        default_risk_profile=RiskProfile.MEDIUM_RISK,
        requires_fraud_detection=True,
        requires_customer_matching=True,
        supports_batch_processing=True,
        typical_transaction_volume="high",
        nigerian_compliance_requirements=[
            "ECOMMERCE_REGULATIONS", "VAT_COMPLIANCE", "CONSUMER_PROTECTION",
            "FIRS_REPORTING", "LOCAL_MARKET_COMPLIANCE"
        ],
        data_quality_expectations="medium"
    ),
    
    # Accounting Systems
    ConnectorType.ACCOUNTING_QUICKBOOKS: ConnectorCharacteristics(
        category=ConnectorCategory.BUSINESS_MANAGEMENT,
        data_structure_level=DataStructureLevel.HIGHLY_STRUCTURED,
        default_risk_profile=RiskProfile.LOW_RISK,
        requires_fraud_detection=False,
        requires_customer_matching=True,
        supports_batch_processing=True,
        typical_transaction_volume="medium",
        nigerian_compliance_requirements=[
            "ACCOUNTING_STANDARDS", "TAX_COMPLIANCE", "FIRS_REPORTING",
            "SME_COMPLIANCE"
        ],
        data_quality_expectations="high"
    ),
    
    ConnectorType.ACCOUNTING_XERO: ConnectorCharacteristics(
        category=ConnectorCategory.BUSINESS_MANAGEMENT,
        data_structure_level=DataStructureLevel.HIGHLY_STRUCTURED,
        default_risk_profile=RiskProfile.LOW_RISK,
        requires_fraud_detection=False,
        requires_customer_matching=True,
        supports_batch_processing=True,
        typical_transaction_volume="medium",
        nigerian_compliance_requirements=[
            "ACCOUNTING_STANDARDS", "TAX_COMPLIANCE", "FIRS_REPORTING",
            "SME_COMPLIANCE"
        ],
        data_quality_expectations="high"
    ),
    
    # Payment Processors
    ConnectorType.PAYMENT_PAYSTACK: ConnectorCharacteristics(
        category=ConnectorCategory.PAYMENT_PROCESSING,
        data_structure_level=DataStructureLevel.MODERATELY_STRUCTURED,
        default_risk_profile=RiskProfile.HIGH_RISK,
        requires_fraud_detection=True,
        requires_customer_matching=True,
        supports_batch_processing=True,
        typical_transaction_volume="very_high",
        nigerian_compliance_requirements=[
            "PAYMENT_REGULATIONS", "CBN_GUIDELINES", "ANTI_MONEY_LAUNDERING",
            "PCI_COMPLIANCE", "FIRS_REPORTING"
        ],
        data_quality_expectations="high"
    ),
    
    ConnectorType.PAYMENT_FLUTTERWAVE: ConnectorCharacteristics(
        category=ConnectorCategory.PAYMENT_PROCESSING,
        data_structure_level=DataStructureLevel.MODERATELY_STRUCTURED,
        default_risk_profile=RiskProfile.HIGH_RISK,
        requires_fraud_detection=True,
        requires_customer_matching=True,
        supports_batch_processing=True,
        typical_transaction_volume="very_high",
        nigerian_compliance_requirements=[
            "PAYMENT_REGULATIONS", "CBN_GUIDELINES", "ANTI_MONEY_LAUNDERING",
            "PCI_COMPLIANCE", "FIRS_REPORTING"
        ],
        data_quality_expectations="high"
    ),
    
    ConnectorType.PAYMENT_MONIEPOINT: ConnectorCharacteristics(
        category=ConnectorCategory.PAYMENT_PROCESSING,
        data_structure_level=DataStructureLevel.MODERATELY_STRUCTURED,
        default_risk_profile=RiskProfile.HIGH_RISK,
        requires_fraud_detection=True,
        requires_customer_matching=True,
        supports_batch_processing=True,
        typical_transaction_volume="very_high",
        nigerian_compliance_requirements=[
            "PAYMENT_REGULATIONS", "CBN_GUIDELINES", "ANTI_MONEY_LAUNDERING",
            "PCI_COMPLIANCE", "FIRS_REPORTING", "AGENT_BANKING_COMPLIANCE"
        ],
        data_quality_expectations="high"
    ),
    
    ConnectorType.PAYMENT_OPAY: ConnectorCharacteristics(
        category=ConnectorCategory.PAYMENT_PROCESSING,
        data_structure_level=DataStructureLevel.MODERATELY_STRUCTURED,
        default_risk_profile=RiskProfile.HIGH_RISK,
        requires_fraud_detection=True,
        requires_customer_matching=True,
        supports_batch_processing=True,
        typical_transaction_volume="very_high",
        nigerian_compliance_requirements=[
            "PAYMENT_REGULATIONS", "CBN_GUIDELINES", "ANTI_MONEY_LAUNDERING",
            "PCI_COMPLIANCE", "FIRS_REPORTING", "MOBILE_MONEY_COMPLIANCE"
        ],
        data_quality_expectations="high"
    ),
    
    ConnectorType.PAYMENT_PALMPAY: ConnectorCharacteristics(
        category=ConnectorCategory.PAYMENT_PROCESSING,
        data_structure_level=DataStructureLevel.MODERATELY_STRUCTURED,
        default_risk_profile=RiskProfile.HIGH_RISK,
        requires_fraud_detection=True,
        requires_customer_matching=True,
        supports_batch_processing=True,
        typical_transaction_volume="very_high",
        nigerian_compliance_requirements=[
            "PAYMENT_REGULATIONS", "CBN_GUIDELINES", "ANTI_MONEY_LAUNDERING",
            "PCI_COMPLIANCE", "FIRS_REPORTING", "MOBILE_MONEY_COMPLIANCE"
        ],
        data_quality_expectations="high"
    ),
    
    ConnectorType.PAYMENT_INTERSWITCH: ConnectorCharacteristics(
        category=ConnectorCategory.PAYMENT_PROCESSING,
        data_structure_level=DataStructureLevel.HIGHLY_STRUCTURED,
        default_risk_profile=RiskProfile.HIGH_RISK,
        requires_fraud_detection=True,
        requires_customer_matching=True,
        supports_batch_processing=True,
        typical_transaction_volume="very_high",
        nigerian_compliance_requirements=[
            "PAYMENT_REGULATIONS", "CBN_GUIDELINES", "ANTI_MONEY_LAUNDERING",
            "PCI_COMPLIANCE", "FIRS_REPORTING", "INTERBANK_COMPLIANCE", "NIBSS_STANDARDS"
        ],
        data_quality_expectations="high"
    )
}


def get_connector_characteristics(connector_type: ConnectorType) -> ConnectorCharacteristics:
    """Get characteristics for a specific connector type."""
    return CONNECTOR_CHARACTERISTICS.get(
        connector_type,
        # Default characteristics for unknown connector types
        ConnectorCharacteristics(
            category=ConnectorCategory.BUSINESS_MANAGEMENT,
            data_structure_level=DataStructureLevel.MODERATELY_STRUCTURED,
            default_risk_profile=RiskProfile.MEDIUM_RISK,
            requires_fraud_detection=True,
            requires_customer_matching=True,
            supports_batch_processing=True,
            typical_transaction_volume="medium",
            nigerian_compliance_requirements=["FIRS_REPORTING"],
            data_quality_expectations="medium"
        )
    )


def get_connectors_by_category(category: ConnectorCategory) -> List[ConnectorType]:
    """Get all connector types in a specific category."""
    return [
        connector_type for connector_type, characteristics in CONNECTOR_CHARACTERISTICS.items()
        if characteristics.category == category
    ]


def get_high_volume_connectors() -> List[ConnectorType]:
    """Get connector types that typically handle high transaction volumes."""
    return [
        connector_type for connector_type, characteristics in CONNECTOR_CHARACTERISTICS.items()
        if characteristics.typical_transaction_volume in ["high", "very_high"]
    ]


def get_high_risk_connectors() -> List[ConnectorType]:
    """Get connector types with high default risk profiles."""
    return [
        connector_type for connector_type, characteristics in CONNECTOR_CHARACTERISTICS.items()
        if characteristics.default_risk_profile == RiskProfile.HIGH_RISK
    ]


def requires_enhanced_fraud_detection(connector_type: ConnectorType) -> bool:
    """Check if connector type requires enhanced fraud detection."""
    characteristics = get_connector_characteristics(connector_type)
    return characteristics.requires_fraud_detection


def supports_batch_processing(connector_type: ConnectorType) -> bool:
    """Check if connector type supports batch processing."""
    characteristics = get_connector_characteristics(connector_type)
    return characteristics.supports_batch_processing


def get_nigerian_compliance_requirements(connector_type: ConnectorType) -> List[str]:
    """Get Nigerian compliance requirements for connector type."""
    characteristics = get_connector_characteristics(connector_type)
    return characteristics.nigerian_compliance_requirements