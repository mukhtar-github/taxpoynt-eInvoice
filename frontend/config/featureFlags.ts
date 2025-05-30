/**
 * Feature flags configuration for TaxPoynt eInvoice
 * 
 * Controls the visibility and functionality of features across the application
 * Facilitates gradual rollout of features, particularly for APP functionality
 */

// Core SI feature flags
export const SI_FEATURES = {
  // ERP Integration features
  ODOO_INTEGRATION: true,
  SAP_INTEGRATION: false,
  QUICKBOOKS_INTEGRATION: false,
  SAGE_INTEGRATION: false,
  
  // FIRS API features
  FIRS_API_TESTING: true,
  FIRS_BATCH_SUBMISSION: true,
  FIRS_STATUS_CHECKS: true,
  
  // Dashboard features
  ADVANCED_ANALYTICS: false,
  REAL_TIME_MONITORING: false
};

// APP feature flags - initially disabled except for UI placeholders
export const APP_FEATURES = {
  // Enable UI placeholders for APP functionality
  APP_UI_ELEMENTS: true,
  
  // Core APP functionality - initially disabled
  CERTIFICATE_MANAGEMENT: false,
  CERTIFICATE_REQUEST: false,
  CERTIFICATE_RENEWAL: false,
  
  // Cryptographic functionality
  CRYPTOGRAPHIC_STAMPING: false,
  CSID_GENERATION: false,
  SIGNATURE_VERIFICATION: false,
  
  // Secure transmission
  SECURE_TRANSMISSION: false,
  ENCRYPTED_PAYLOAD: false,
  TRANSMISSION_MONITORING: false
};

// Function to check if a feature is enabled
export function isFeatureEnabled(featureName: string): boolean {
  // Check in SI features first
  if (featureName in SI_FEATURES) {
    return SI_FEATURES[featureName as keyof typeof SI_FEATURES];
  }
  
  // Then check in APP features
  if (featureName in APP_FEATURES) {
    return APP_FEATURES[featureName as keyof typeof APP_FEATURES];
  }
  
  // Feature not found in either set
  console.warn(`Feature flag not found: ${featureName}`);
  return false;
}

// Export default for easier imports
export default { SI_FEATURES, APP_FEATURES, isFeatureEnabled };
