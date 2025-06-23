/**
 * Integration Components - Week 3 Enhanced Export Index
 * 
 * This file provides clean imports for all Week 3 enhanced integration components.
 * Use these imports instead of individual component imports for better maintainability.
 */

// Enhanced Integration Components (Week 3)
export { default as EnhancedIntegrationStatusCard, IntegrationStatusGrid } from './EnhancedIntegrationStatusCard';
export { default as EnhancedSetupWizard } from './EnhancedSetupWizard';

// Legacy Components (Backward Compatibility)
export { default as IntegrationStatusMonitor } from './IntegrationStatusMonitor';
export { IntegrationForm } from './IntegrationForm';
export { default as IntegrationInfo } from './IntegrationInfo';

// Connection Forms (Specific Platforms)
export { default as OdooIntegrationForm } from './OdooIntegrationForm';
export { default as OdooConnectionForm } from './OdooConnectionForm';
export { default as QuickBooksConnectionForm } from './QuickBooksConnectionForm';
export { default as SAPConnectionForm } from './SAPConnectionForm';
export { default as OracleConnectionForm } from './OracleConnectionForm';
export { default as DynamicsConnectionForm } from './DynamicsConnectionForm';

// ERP Tab Components
export { default as ERPCustomersTab } from './ERPCustomersTab';
export { default as ERPInvoicesTab } from './ERPInvoicesTab';
export { default as ERPProductsTab } from './ERPProductsTab';
export { default as OdooCustomersTab } from './OdooCustomersTab';
export { default as OdooInvoicesTab } from './OdooInvoicesTab';
export { default as OdooProductsTab } from './OdooProductsTab';

// CRM Components
export { default as CRMConnectionCard } from './crm/CRMConnectionCard';

// POS Components
export { default as POSDashboard } from './pos/POSDashboard';
export { TransactionsList } from './pos/TransactionsList';
export { POSConnectorCard } from './pos/POSConnectorCard';
export { RealTimeStats } from './pos/RealTimeStats';

// Type exports for enhanced components
export type { 
  IntegrationMetrics,
  IntegrationStatusCardProps 
} from './EnhancedIntegrationStatusCard';

/**
 * Recommended Usage:
 * 
 * // Week 3 Enhanced Components (Preferred)
 * import { 
 *   IntegrationStatusGrid, 
 *   EnhancedSetupWizard 
 * } from '@/components/integrations';
 * 
 * // Legacy Components (Backward Compatibility)
 * import { 
 *   IntegrationStatusMonitor 
 * } from '@/components/integrations';
 */