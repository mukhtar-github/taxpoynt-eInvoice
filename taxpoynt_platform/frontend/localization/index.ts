/**
 * TaxPoynt Localization System
 * ============================
 * 
 * Multi-language support for Nigerian markets with role-specific terminology.
 * Supports English and major Nigerian languages for inclusive user experience.
 * 
 * @author TaxPoynt Development Team
 * @version 1.0.0
 * @status FOUNDATION_READY - Implementation pending
 */

// Language configuration
export const SUPPORTED_LANGUAGES = {
  en: {
    code: 'en',
    name: 'English',
    nativeName: 'English',
    rtl: false,
    default: true
  },
  pcn: {
    code: 'pcn', 
    name: 'Nigerian Pidgin',
    nativeName: 'Naija',
    rtl: false,
    default: false
  },
  yo: {
    code: 'yo',
    name: 'Yoruba',
    nativeName: 'Yorùbá',
    rtl: false,
    default: false
  },
  ig: {
    code: 'ig',
    name: 'Igbo', 
    nativeName: 'Igbo',
    rtl: false,
    default: false
  },
  ha: {
    code: 'ha',
    name: 'Hausa',
    nativeName: 'Hausa',
    rtl: false,
    default: false
  }
} as const;

export type SupportedLanguage = keyof typeof SUPPORTED_LANGUAGES;

// Role-specific terminology mapping
export const ROLE_TERMINOLOGY = {
  si: 'System Integrator',
  app: 'Access Point Provider', 
  hybrid: 'Hybrid User',
  admin: 'Administrator'
} as const;

// Translation namespace structure
export const TRANSLATION_NAMESPACES = [
  'common',           // Common UI elements
  'navigation',       // Navigation and menus
  'forms',           // Form labels and validation
  'tables',          // Table headers and actions
  'charts',          // Chart labels and legends
  'auth',            // Authentication flows
  'compliance',      // Compliance and legal text
  'billing',         // Billing and payments
  'errors',          // Error messages
  'success',         // Success messages
  'roles'            // Role-specific terminology
] as const;

// Localization utilities (to be implemented)
export interface LocalizationContextType {
  currentLanguage: SupportedLanguage;
  setLanguage: (language: SupportedLanguage) => void;
  t: (key: string, namespace?: string) => string;
  isLoading: boolean;
  direction: 'ltr' | 'rtl';
}

// Placeholder for future implementation
export const useLocalization = (): LocalizationContextType => {
  return {
    currentLanguage: 'en',
    setLanguage: () => console.log('Localization: setLanguage not implemented'),
    t: (key: string) => `[${key}]`, // Placeholder - shows translation keys
    isLoading: false,
    direction: 'ltr'
  };
};

export default {
  SUPPORTED_LANGUAGES,
  ROLE_TERMINOLOGY,
  TRANSLATION_NAMESPACES,
  useLocalization
};