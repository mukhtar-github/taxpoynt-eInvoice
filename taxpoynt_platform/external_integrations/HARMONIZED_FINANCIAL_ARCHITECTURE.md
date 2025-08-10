# 🏗️ Harmonized Financial Systems Architecture

## 📋 Overview

This document provides the definitive harmonized architecture for financial systems integration within the TaxPoynt platform, resolving discrepancies between various implementation documents and establishing clear implementation guide-rails.

---

## 🎯 **Architectural Harmonization Decisions**

### **Key Resolved Discrepancies:**

✅ **Centralized Connector Framework**: All connector frameworks consolidated under `external_integrations/connector_framework/`  
✅ **API-Based Classification Engine**: Centralized as shared service for ALL financial integrations  
✅ **Provider Optimization**: Removed Okra (discontinued services), focus on Mono + Stitch  
✅ **SI Subscription Integration**: Clean alignment with unified subscription model  
✅ **Nigerian Market Focus**: Optimized for Nigerian banking and business patterns  

---

## 🏗️ **Final Harmonized Architecture**

```
taxpoynt_platform/external_integrations/
├── connector_framework/                 # 🔧 CENTRALIZED FRAMEWORK
│   ├── classification_engine/           # 🧠 API-BASED TRANSACTION CLASSIFICATION
│   │   ├── __init__.py                  # Engine exports and interfaces
│   │   ├── nigerian_classifier.py       # Main OpenAI GPT-4o-mini classifier
│   │   ├── cost_optimizer.py           # API cost optimization logic  
│   │   ├── privacy_protection.py       # Data anonymization and PII removal
│   │   ├── cache_manager.py            # Smart caching with Redis integration
│   │   ├── rule_fallback.py            # Nigerian rule-based fallback system
│   │   ├── classification_models.py    # Pydantic data models
│   │   └── usage_tracker.py            # Classification usage analytics
│   ├── base_connectors/                # Base connector classes
│   │   ├── __init__.py
│   │   ├── base_financial_connector.py # Universal financial system base
│   │   ├── base_banking_connector.py   # Banking-specific base class
│   │   ├── base_payment_connector.py   # Payment processor base class
│   │   └── base_forex_connector.py     # Forex system base class
│   ├── shared_utilities/               # Shared framework utilities
│   │   ├── __init__.py
│   │   ├── webhook_framework.py        # Standardized webhook handling
│   │   ├── rate_limiter.py            # API rate limiting utilities
│   │   ├── error_handler.py           # Unified error handling patterns
│   │   ├── audit_logger.py            # Compliance and audit logging
│   │   └── retry_manager.py           # Intelligent retry mechanisms
│   └── testing_framework/              # Centralized testing utilities
│       ├── __init__.py
│       ├── mock_providers.py          # Mock financial service responses
│       ├── integration_tests.py       # End-to-end integration testing
│       └── classification_tests.py    # Classification accuracy testing
├── financial_systems/                  # 💰 FINANCIAL SYSTEM INTEGRATIONS
│   ├── banking/                        # Banking System Integrations
│   │   ├── __init__.py
│   │   ├── open_banking/              # Open Banking Providers
│   │   │   ├── __init__.py
│   │   │   ├── providers/             # Provider-specific implementations
│   │   │   │   ├── __init__.py
│   │   │   │   ├── mono/              # Mono API Integration (PRIMARY)
│   │   │   │   │   ├── __init__.py
│   │   │   │   │   ├── connector.py          # Main Mono connector
│   │   │   │   │   ├── auth.py               # Mono authentication
│   │   │   │   │   ├── transaction_fetcher.py # Transaction API calls
│   │   │   │   │   ├── webhook_handler.py    # Real-time webhooks
│   │   │   │   │   ├── exceptions.py         # Mono-specific exceptions
│   │   │   │   │   └── models.py             # Mono data models
│   │   │   │   ├── stitch/            # Stitch API Integration (ENTERPRISE)
│   │   │   │   │   ├── __init__.py
│   │   │   │   │   ├── connector.py          # Main Stitch connector
│   │   │   │   │   ├── auth.py               # Stitch authentication
│   │   │   │   │   ├── transaction_fetcher.py # Transaction API calls
│   │   │   │   │   ├── webhook_handler.py    # Real-time webhooks
│   │   │   │   │   ├── exceptions.py         # Stitch-specific exceptions
│   │   │   │   │   └── models.py             # Stitch data models
│   │   │   │   └── unified_banking/   # Multi-provider Interface
│   │   │   │       ├── __init__.py
│   │   │   │       ├── aggregator.py         # Provider aggregation logic
│   │   │   │       ├── provider_selector.py  # Intelligent provider selection
│   │   │   │       ├── failover_manager.py   # Provider failover handling
│   │   │   │       └── load_balancer.py      # Provider load balancing  
│   │   │   ├── transaction_processing/  # Transaction Analysis & Processing
│   │   │   │   ├── __init__.py
│   │   │   │   ├── transaction_validator.py  # Transaction data validation
│   │   │   │   ├── duplicate_detector.py     # Prevent duplicate processing
│   │   │   │   ├── amount_validator.py       # Amount validation & fraud detection
│   │   │   │   ├── business_rule_engine.py   # Nigerian business logic rules
│   │   │   │   └── pattern_matcher.py        # Transaction pattern recognition
│   │   │   ├── invoice_automation/      # Automated Invoice Generation
│   │   │   │   ├── __init__.py
│   │   │   │   ├── auto_invoice_generator.py # Main invoice generation engine
│   │   │   │   ├── customer_matcher.py       # Bank transfer → customer matching
│   │   │   │   ├── tax_calculator.py         # Nigerian tax calculations (7.5% VAT)
│   │   │   │   ├── firs_submitter.py         # Automatic FIRS submission
│   │   │   │   └── invoice_templates.py      # Nigerian invoice templates
│   │   │   └── compliance/              # Banking Compliance & Security
│   │   │       ├── __init__.py
│   │   │       ├── consent_manager.py        # User consent handling (NDPR)
│   │   │       ├── data_retention.py         # Data retention policies (7-year FIRS requirement)
│   │   │       ├── audit_logger.py           # Comprehensive audit trails
│   │   │       ├── security_monitor.py       # Security monitoring & alerts
│   │   │       └── privacy_compliance.py     # Nigerian privacy regulation compliance
│   │   ├── ussd_gateway/                # USSD Banking Services  
│   │   │   ├── __init__.py
│   │   │   ├── providers/               # USSD provider implementations
│   │   │   │   ├── __init__.py
│   │   │   │   ├── mtn_ussd/           # MTN USSD integration
│   │   │   │   ├── airtel_ussd/        # Airtel USSD integration
│   │   │   │   ├── glo_ussd/           # Glo USSD integration
│   │   │   │   └── etisalat_ussd/      # 9mobile USSD integration
│   │   │   ├── ussd_processor.py       # USSD transaction processing
│   │   │   └── session_manager.py      # USSD session management
│   │   ├── nibss_integration/          # Nigerian Inter-Bank Settlement System
│   │   │   ├── __init__.py
│   │   │   ├── nibss_connector.py      # NIBSS API integration
│   │   │   ├── interbank_processor.py  # Inter-bank transaction processing
│   │   │   └── settlement_manager.py   # Settlement management
│   │   └── bvn_validation/             # Bank Verification Number Services
│   │       ├── __init__.py
│   │       ├── bvn_validator.py        # BVN validation services
│   │       ├── identity_verifier.py    # Identity verification
│   │       └── kyc_processor.py        # Know Your Customer processing
│   ├── payments/                       # Payment Processor Integrations
│   │   ├── __init__.py
│   │   ├── nigerian_processors/        # 🇳🇬 NIGERIAN PRIMARY PROCESSORS
│   │   │   ├── __init__.py
│   │   │   ├── paystack/               # Paystack (Nigerian Market Leader)
│   │   │   │   ├── __init__.py
│   │   │   │   ├── connector.py
│   │   │   │   ├── auth.py
│   │   │   │   ├── payment_processor.py
│   │   │   │   ├── webhook_handler.py
│   │   │   │   └── models.py
│   │   │   ├── moniepoint/             # Moniepoint (POS/Agent Banking Leader)
│   │   │   │   ├── __init__.py
│   │   │   │   ├── connector.py
│   │   │   │   ├── auth.py
│   │   │   │   ├── payment_processor.py
│   │   │   │   ├── pos_integration.py
│   │   │   │   ├── agent_banking.py
│   │   │   │   ├── webhook_handler.py
│   │   │   │   └── models.py
│   │   │   ├── opay/                   # OPay (Opera Mobile Payments)
│   │   │   │   ├── __init__.py
│   │   │   │   ├── connector.py
│   │   │   │   ├── auth.py
│   │   │   │   ├── payment_processor.py
│   │   │   │   ├── mobile_wallet.py
│   │   │   │   ├── merchant_services.py
│   │   │   │   ├── webhook_handler.py
│   │   │   │   └── models.py
│   │   │   ├── palmpay/                # PalmPay (Mobile Payment Platform)
│   │   │   │   ├── __init__.py
│   │   │   │   ├── connector.py
│   │   │   │   ├── auth.py
│   │   │   │   ├── payment_processor.py
│   │   │   │   ├── mobile_payment.py
│   │   │   │   ├── merchant_integration.py
│   │   │   │   ├── webhook_handler.py
│   │   │   │   └── models.py
│   │   │   └── interswitch/            # Interswitch (Nigerian Interbank)
│   │   │       ├── __init__.py
│   │   │       ├── connector.py
│   │   │       ├── auth.py
│   │   │       ├── payment_processor.py
│   │   │       ├── interbank_switching.py
│   │   │       └── models.py
│   │   ├── african_processors/         # 🌍 AFRICAN REGIONAL PROCESSORS
│   │   │   ├── __init__.py
│   │   │   └── flutterwave/            # Flutterwave (Pan-African)
│   │   │       ├── __init__.py
│   │   │       ├── connector.py
│   │   │       ├── auth.py
│   │   │       ├── payment_processor.py
│   │   │       ├── multi_country.py
│   │   │       ├── webhook_handler.py
│   │   │       └── models.py
│   │   └── global_processors/          # 🌐 GLOBAL PROCESSORS
│   │       ├── __init__.py
│   │       ├── stripe/                 # Stripe (Global)
│   │       │   ├── __init__.py
│   │       │   ├── connector.py
│   │       │   ├── auth.py
│   │       │   ├── payment_processor.py
│   │       │   ├── webhook_handler.py
│   │       │   └── models.py
│   │       └── square_payments/        # Square Payment Processing
│   │           ├── __init__.py
│   │           ├── connector.py
│   │           ├── auth.py
│   │           ├── payment_processor.py
│   │           └── models.py
│   └── forex/                          # Foreign Exchange Rate Services
│       ├── __init__.py
│       ├── xe_currency/                # XE Currency Rates (Global)
│       │   ├── __init__.py
│       │   ├── connector.py
│       │   ├── rate_fetcher.py
│       │   └── models.py
│       ├── fixer_io/                   # Fixer.io Exchange Rates
│       │   ├── __init__.py
│       │   ├── connector.py
│       │   ├── rate_fetcher.py
│       │   └── models.py
│       └── cbn_rates/                  # Central Bank of Nigeria Rates (Official)
│           ├── __init__.py
│           ├── connector.py
│           ├── official_rate_fetcher.py
│           └── models.py
```

---

## 🧠 **Centralized Classification Engine Architecture**

### **Why Centralized Classification?**

✅ **Universal Applicability**: Used by Banking, Payments, and Forex systems  
✅ **Cost Optimization**: Centralized API usage and caching reduces costs  
✅ **Consistency**: Same classification logic across all financial integrations  
✅ **Privacy Compliance**: Single point for data anonymization and PII protection  
✅ **Scalability**: Easy to upgrade from API-based to local ML models  
✅ **Maintenance**: One classification engine to maintain and improve  

### **Classification Engine Components**

#### **1. Nigerian Classifier (`nigerian_classifier.py`)**
```python
class NigerianTransactionClassifier:
    """
    OpenAI GPT-4o-mini powered transaction classifier optimized for Nigerian business patterns
    """
    
    def __init__(self):
        self.client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        self.nigerian_context = self._load_nigerian_business_context()
        self.cost_tracker = CostTracker()
        
    async def classify_transaction(self, transaction: Dict, user_context: Dict = None) -> ClassificationResult:
        """
        Classify Nigerian bank transaction for FIRS tax compliance
        
        Features:
        - Nigerian business pattern recognition
        - FIRS compliance focus (7.5% VAT)
        - Customer identification and matching
        - Privacy-first data handling
        - Cost optimization with smart caching
        """
```

#### **2. Cost Optimizer (`cost_optimizer.py`)**
```python
class CostOptimizer:
    """
    Intelligent cost optimization for API-based classification
    """
    
    def determine_classification_tier(self, transaction: Dict, user_context: Dict) -> str:
        """
        Determines optimal classification method:
        - 'rule_based': Free rule-based for obvious cases
        - 'api_lite': GPT-3.5-turbo for simple cases  
        - 'api_premium': GPT-4o-mini for complex cases
        """
```

#### **3. Privacy Protection (`privacy_protection.py`)**
```python
class APIPrivacyProtection:
    """
    NDPR-compliant data anonymization for API calls
    """
    
    def anonymize_for_api(self, transaction: Dict) -> Dict:
        """
        Remove/mask sensitive data before external API calls:
        - Round amounts to nearest ₦1,000
        - Redact account numbers and phone numbers  
        - Replace names with [NAME] tokens
        - Categorize rather than expose raw data
        """
```

### **Classification Data Flow**

```
Financial Transaction → Privacy Filter → Cache Check → 
Classification Tier Decision → API Call → Result Enhancement → 
Cache Store → Return Classified Result
```

---

## 💰 **SI Subscription Integration**

### **Financial System Access by SI Tier**

| Tier | Banking Features | Payment Features | Classification Access |
|------|-----------------|------------------|---------------------|
| **STARTER** | Basic Open Banking<br/>Standard transaction fetching | **Nigerian Processors**: Paystack, Moniepoint, OPay, PalmPay<br/>Standard payment processing<br/>Basic webhook support | Rule-based + Limited API<br/>100 classifications/month |
| **PROFESSIONAL** | Advanced banking analytics<br/>Real-time webhooks<br/>Bulk processing | **All Nigerian + Regional**: Flutterwave<br/>Priority payment processing<br/>Advanced webhook features<br/>Multi-processor aggregation | Full API classification<br/>10,000 classifications/month |
| **ENTERPRISE** | Real-time financial insights<br/>Custom banking workflows<br/>White-label features | **All Processors + Global**: Stripe, Square<br/>Custom payment workflows<br/>White-label payment pages<br/>Payment reconciliation | Advanced AI classification<br/>Custom business rules |
| **SCALE** | Enterprise banking infrastructure<br/>Dedicated banking support<br/>SLA guarantees | **Unlimited Payment Infrastructure**<br/>Dedicated payment infrastructure<br/>24/7 payment support<br/>Custom processor integrations | Unlimited AI classification<br/>Priority API access |

### **Usage Tracking Integration**

```python
# All financial integrations track against unified SI limits
from taxpoynt_platform.si_services.subscription_management import record_si_usage, SIUsageType

async def process_classified_transaction(transaction, classification_result):
    """Record usage against SI subscription limits"""
    
    # Record invoice processing if classified as business income
    if classification_result.is_business_income:
        await record_si_usage(
            organization_id,
            SIUsageType.INVOICES_PROCESSED,  # Unified SI metric
            1,
            metadata={
                "source": "open_banking_mono",
                "classification_method": "api_gpt4o_mini", 
                "confidence": classification_result.confidence,
                "classification_cost_ngn": classification_result.api_cost_estimate
            }
        )
    
    # Record API classification usage
    await record_si_usage(
        organization_id,
        SIUsageType.API_CALLS,
        1,
        metadata={
            "api_type": "transaction_classification",
            "provider": "openai_gpt4o_mini"
        }
    )
```

---

## 🔄 **Provider Strategy & Prioritization**

### **Open Banking Providers (Okra Removed)**

#### **PRIMARY: Mono Integration**
- **Coverage**: 95% of Nigerian banks
- **Strength**: Largest aggregator with excellent API quality
- **Focus**: Broad market coverage for all SI tiers
- **Implementation Priority**: HIGH

#### **SECONDARY: Stitch Integration**  
- **Coverage**: 85% of Nigerian banks
- **Strength**: Enterprise compliance and large business focus
- **Focus**: ENTERPRISE and SCALE tier customers
- **Implementation Priority**: MEDIUM

#### **Removed: Okra Integration**
- **Reason**: Company has discontinued services
- **Migration**: Existing Okra customers migrate to Mono or Stitch
- **Timeline**: Immediate removal from all new implementations

### **Payment Processor Prioritization (Nigerian-First Strategy)**

#### **🇳🇬 NIGERIAN PRIMARY PROCESSORS (STARTER+ Tiers)**
1. **Paystack** - Nigerian market leader, most comprehensive API
2. **Moniepoint** - POS/agent banking dominance, massive SME reach
3. **OPay** - Mobile payment leader, huge user base
4. **PalmPay** - Strong retail/SME presence, mobile-first
5. **Interswitch** - Interbank switching, enterprise focus

#### **🌍 AFRICAN REGIONAL (PROFESSIONAL+ Tiers)**  
6. **Flutterwave** - Pan-African reach, multi-country support

#### **🌐 GLOBAL PROCESSORS (ENTERPRISE+ Tiers)**
7. **Stripe** - Global processing, international businesses
8. **Square** - International POS systems, SCALE tier focus

---

## 🚀 **Implementation Roadmap**

### **Phase 1: Core Classification Engine (Week 1)**
- [ ] Build centralized classification engine
- [ ] Implement Nigerian business pattern recognition
- [ ] Add privacy protection and cost optimization
- [ ] Create comprehensive testing framework

### **Phase 2: Primary Open Banking (Week 2)**
- [ ] Implement Mono connector with full transaction processing
- [ ] Build automated invoice generation pipeline
- [ ] Integrate with FIRS submission system
- [ ] Add real-time webhook handling

### **Phase 3: Enterprise Banking (Week 3)**
- [ ] Implement Stitch connector for enterprise customers
- [ ] Build unified banking aggregator
- [ ] Add provider failover and load balancing
- [ ] Enhanced compliance and audit features

### **Phase 4: Nigerian Payment Processors (Week 4)**
- [ ] Implement Paystack connector (Nigerian market leader)
- [ ] Implement Moniepoint connector (POS/agent banking)
- [ ] Implement OPay connector (mobile payments)
- [ ] Implement PalmPay connector (mobile platform)
- [ ] Add payment transaction classification for all Nigerian processors
- [ ] Build unified Nigerian payment webhook processing
- [ ] Integrate with SI subscription tiers

### **Phase 5: Regional & Global Processors (Week 5)**
- [ ] Implement Flutterwave connector (Pan-African)
- [ ] Implement Interswitch connector (Nigerian interbank)
- [ ] Add Stripe connector (global processing)
- [ ] Build unified payment processor aggregator
- [ ] Add multi-currency support for international payments

### **Phase 6: Advanced Features (Week 6-7)**
- [ ] Forex rate integration for multi-currency support
- [ ] Advanced payment analytics and business insights
- [ ] Custom payment workflow builder for ENTERPRISE+ tiers
- [ ] Performance optimization and scaling
- [ ] Payment reconciliation automation

---

## 🔐 **Compliance & Security Framework**

### **Nigerian Data Protection Regulation (NDPR) Compliance**

```python
class NDPRCompliance:
    """NDPR compliance implementation for financial data"""
    
    user_consent_required = True
    data_minimization = "Only transaction data necessary for tax compliance"
    retention_period = "7 years (FIRS requirement)"
    deletion_rights = "User can request data deletion after retention period"
    breach_notification = "24 hours to NITDA, 72 hours to user"
    cross_border_transfer = "Only to countries with adequate protection (OpenAI US with safeguards)"
```

### **Banking Security Standards**

- **PCI DSS Compliance**: Payment card industry data security standards
- **ISO 27001**: Information security management system
- **SOC 2 Type II**: Service organization controls for security and availability
- **CBN Guidelines**: Central Bank of Nigeria cybersecurity requirements

### **Technical Security Measures**

- **Authentication**: OAuth 2.0 with PKCE for all banking connections
- **Authorization**: Granular permissions (read-only financial data)
- **Encryption**: End-to-end AES-256 encryption for all data
- **API Security**: Rate limiting, IP whitelisting, comprehensive audit logging
- **Token Management**: Short-lived access tokens with secure refresh mechanisms

---

## 📊 **Integration Patterns & Examples**

### **Standard Financial Connector Pattern**

```python
from external_integrations.connector_framework.base_connectors import BaseFinancialConnector
from external_integrations.connector_framework.classification_engine import NigerianClassifier

class StandardFinancialConnector(BaseFinancialConnector):
    """Standard pattern for all financial system integrations"""
    
    def __init__(self, config: ConnectorConfig):
        super().__init__(config)
        self.classifier = NigerianClassifier()  # Centralized classification
        
    async def process_transaction(self, transaction: Dict) -> ProcessingResult:
        """Standard transaction processing workflow"""
        
        # 1. Validate transaction data
        validated_transaction = await self.validate_transaction(transaction)
        
        # 2. Classify using centralized engine
        classification = await self.classifier.classify_transaction(
            validated_transaction,
            self.get_user_context()
        )
        
        # 3. Generate invoice if business income
        if classification.is_business_income:
            invoice = await self.generate_invoice(validated_transaction, classification)
            
            # 4. Submit to FIRS
            firs_result = await self.submit_to_firs(invoice)
            
            # 5. Record SI usage
            await self.record_si_usage(invoice)
            
            return ProcessingResult(
                transaction=validated_transaction,
                classification=classification,
                invoice=invoice,
                firs_result=firs_result
            )
        
        return ProcessingResult(
            transaction=validated_transaction,
            classification=classification
        )
```

### **Multi-Provider Aggregation Pattern**

```python
from external_integrations.financial_systems.banking.open_banking.providers.unified_banking import UnifiedBankingAggregator

class BusinessBankingService:
    """High-level service using multiple banking providers"""
    
    def __init__(self):
        self.aggregator = UnifiedBankingAggregator()
        
    async def get_business_transactions(self, organization_id: str) -> List[Dict]:
        """Get transactions from all connected banking providers"""
        
        # Automatically selects best available provider
        transactions = await self.aggregator.fetch_transactions(
            organization_id,
            days=30,
            classification_required=True
        )
        
        return transactions
```

---

## 🎯 **Success Metrics & Monitoring**

### **Classification Engine KPIs**
- **Accuracy Rate**: Target >95% for business income detection
- **API Cost per Classification**: Target <₦50 per transaction
- **Cache Hit Rate**: Target >80% for similar transactions
- **Processing Time**: Target <5 seconds end-to-end

### **Financial Integration KPIs** 
- **Provider Uptime**: Target >99.9% across all banking providers
- **Transaction Processing Success**: Target >99.8% success rate
- **Invoice Generation Accuracy**: Target >99.5% correct invoices
- **FIRS Submission Success**: Target >99.8% submission success

### **Business Impact KPIs**
- **SME Onboarding**: Target 1,000+ SMEs per month by month 6
- **Tax Compliance Improvement**: Target >90% improvement in customer compliance
- **Revenue per Customer**: Target ₦50,000+ annually from financial integrations
- **Customer Satisfaction**: Target >4.5/5.0 satisfaction score

---

## 📋 **Implementation Checklist**

### **For Every New Financial Integration:**

- [ ] **Extend Base Connector**: Inherit from appropriate base class in `connector_framework/base_connectors/`
- [ ] **Use Centralized Classification**: Integrate with `classification_engine/nigerian_classifier.py`
- [ ] **Follow Security Patterns**: Implement authentication, encryption, and audit logging
- [ ] **SI Tier Integration**: Implement tier-based feature access and usage tracking
- [ ] **Error Handling**: Use standardized error handling from `shared_utilities/error_handler.py`
- [ ] **Testing Coverage**: Add integration tests using `testing_framework/`
- [ ] **Documentation**: Update API documentation and integration guides
- [ ] **Monitoring**: Add relevant metrics and health checks

---

## 🎉 **Conclusion**

The **Harmonized Financial Systems Architecture** provides:

✅ **Unified Structure**: All financial integrations follow consistent patterns  
✅ **Centralized Intelligence**: Shared classification engine reduces costs and improves accuracy  
✅ **Nigerian Optimization**: Specifically designed for Nigerian business patterns and compliance  
✅ **SI Integration**: Clean alignment with unified subscription model  
✅ **Scalable Foundation**: Easy to add new providers and expand functionality  
✅ **Compliance Ready**: Built-in NDPR, PCI DSS, and FIRS compliance  

This architecture resolves all identified discrepancies and provides a clear, scalable foundation for TaxPoynt's financial system integrations.

---

*Document Version: 1.0*  
*Created: 2025-07-24*  
*Status: **ACTIVE ARCHITECTURE GUIDE** - Definitive reference for all financial system implementations*  
*Next Review: Monthly during active development*