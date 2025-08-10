/**
 * System Integrator (SI) Interface - Main Export Index
 * ==================================================
 * 
 * Complete System Integrator interface for TaxPoynt e-invoicing platform.
 * Provides comprehensive tools for business system integration, compliance
 * monitoring, and FIRS e-invoicing submission.
 * 
 * Features:
 * - Business system integration (ERP, CRM, POS, E-commerce, Accounting, Inventory)
 * - Nigerian compliance monitoring (FIRS, VAT, CBN, NDPR)
 * - Document processing and validation workflows
 * - Certificate and security management
 * - Real-time processing monitoring
 * - Data extraction and schema validation
 */

// Pages
export { default as IntegrationSetup } from './pages/integration_setup';
export { default as DataMapping } from './pages/data_mapping';
export { default as ProcessingMonitor } from './pages/processing_monitor';
export { default as ComplianceDashboard } from './pages/compliance_dashboard';

// Workflows
export { default as ERPOnboarding } from './workflows/erp_onboarding';
export { default as DocumentPreparation } from './workflows/document_preparation';
export { default as ValidationProcess } from './workflows/validation_process';

// Core Components
export { CertificateManager } from './components/certificate_management/CertificateManager';
export { DataExtractor } from './components/data_extraction/DataExtractor';
export { DocumentProcessor } from './components/document_processing/DocumentProcessor';
export { SchemaValidator } from './components/schema_validation/SchemaValidator';

// Business System Components
export { ERPDashboard } from './components/business_systems/erp_dashboard/ERPDashboard';
export { CRMDashboard } from './components/business_systems/crm_dashboard/CRMDashboard';
export { POSDashboard } from './components/business_systems/pos_dashboard/POSDashboard';
export { EcommerceDashboard } from './components/business_systems/ecommerce_dashboard/EcommerceDashboard';
export { AccountingDashboard } from './components/business_systems/accounting_dashboard/AccountingDashboard';
export { InventoryDashboard } from './components/business_systems/inventory_dashboard/InventoryDashboard';

// Financial System Components
export { MonoBankingDashboard } from './components/financial_systems/banking_integration/MonoBankingDashboard';
export { MonoConsentIntegration } from './components/financial_systems/banking_integration/MonoConsentIntegration';
export { PaymentProcessorDashboard } from './components/financial_systems/payment_processors/PaymentProcessorDashboard';
export { FinancialValidator } from './components/financial_systems/validation_tools/FinancialValidator';

// Component Types and Interfaces
export type {
  // Integration Types
  IntegrationConfig,
  SystemConnection,
  ConnectionStatus,
  
  // Business System Types
  ERPSystem,
  CRMSystem,
  POSSystem,
  EcommerceSystem,
  AccountingSystem,
  InventorySystem,
  
  // Processing Types
  ProcessingJob,
  ProcessingStatus,
  DocumentBatch,
  ValidationResult,
  
  // Compliance Types
  ComplianceStatus,
  FIRSStatus,
  VATCompliance,
  CBNCompliance,
  NDPRCompliance,
  
  // Certificate Types
  Certificate,
  CertificateStatus,
  SecurityCredential,
  
  // Data Types
  DataMapping,
  FieldMapping,
  DataExtraction,
  SchemaDefinition,
  ValidationRule
} from './types';

/**
 * SI Interface Navigation Structure
 * ================================
 * 
 * Main Navigation:
 * - Integration Setup    -> Multi-step business system integration
 * - Data Mapping        -> Visual field mapping and schema configuration
 * - Processing Monitor  -> Real-time processing and submission tracking
 * - Compliance Dashboard -> Nigerian compliance monitoring and reporting
 * 
 * Workflows:
 * - ERP Onboarding     -> Complete organization setup and ERP integration
 * - Document Preparation -> Batch processing and FIRS formatting
 * - Validation Process -> Multi-tier validation and quality assurance
 * 
 * Components:
 * - Certificate Manager -> Digital certificate and security management
 * - Data Extractor     -> Multi-source data extraction and processing
 * - Document Processor -> Document transformation and validation
 * - Schema Validator   -> Schema compliance and rule validation
 * 
 * Business Systems:
 * - ERP Dashboard      -> Enterprise Resource Planning integration
 * - CRM Dashboard      -> Customer Relationship Management integration
 * - POS Dashboard      -> Point of Sale system integration
 * - E-commerce Dashboard -> Online marketplace and store integration
 * - Accounting Dashboard -> Financial accounting system integration
 * - Inventory Dashboard -> Inventory management system integration
 * 
 * Financial Systems:
 * - Mono Banking       -> Banking integration and transaction processing
 * - Payment Processors -> Payment gateway integration (Paystack, Flutterwave, etc.)
 * - Validation Tools   -> Financial data validation and Nigerian compliance
 */

// Default export - Main SI Interface Router
export { default } from './SIInterface';