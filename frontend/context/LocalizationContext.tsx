import React, { createContext, useContext, useState, useEffect, ReactNode } from 'react';
import { 
  NigerianLocalization, 
  LanguageConfig, 
  LocalizedBusinessTerms,
  LocalizationUtils,
  NairaCurrencyFormatter,
  NigerianDateFormatter,
  NigerianNumberFormatter
} from '../i18n/nigerian-localization';

interface LocalizationContextType {
  currentLanguage: string;
  languageConfig: LanguageConfig;
  changeLanguage: (languageCode: string) => void;
  
  // Utility functions
  t: (key: keyof LocalizedBusinessTerms) => string;
  tPhrase: (key: keyof LanguageConfig['common_phrases']) => string;
  tMessage: (key: keyof LanguageConfig['business_messages']) => string;
  
  // Formatting functions
  formatCurrency: (amount: number) => string;
  formatDate: (date: Date | string) => string;
  formatDateTime: (date: Date | string) => string;
  formatNumber: (value: number, decimals?: number) => string;
  
  // Greeting functions
  getGreeting: (timeOfDay?: 'morning' | 'afternoon' | 'evening') => string;
  getCurrentGreeting: () => string;
  
  // Supported languages
  supportedLanguages: Array<{code: string, name: string}>;
}

const LocalizationContext = createContext<LocalizationContextType | undefined>(undefined);

interface LocalizationProviderProps {
  children: ReactNode;
  initialLanguage?: string;
}

const STORAGE_KEY = 'taxpoynt-language';

export const LocalizationProvider: React.FC<LocalizationProviderProps> = ({ 
  children, 
  initialLanguage = 'en-NG' 
}) => {
  const [currentLanguage, setCurrentLanguage] = useState<string>(() => {
    // Try to get language from localStorage
    if (typeof window !== 'undefined') {
      const saved = localStorage.getItem(STORAGE_KEY);
      if (saved && saved in NigerianLocalization.languages) {
        return saved;
      }
    }
    return initialLanguage;
  });

  const languageConfig = NigerianLocalization.languages[currentLanguage as keyof typeof NigerianLocalization.languages] || 
                        NigerianLocalization.languages['en-NG'];

  const changeLanguage = (languageCode: string) => {
    if (languageCode in NigerianLocalization.languages) {
      setCurrentLanguage(languageCode);
      if (typeof window !== 'undefined') {
        localStorage.setItem(STORAGE_KEY, languageCode);
      }
    }
  };

  // Translation functions
  const t = (key: keyof LocalizedBusinessTerms): string => {
    return LocalizationUtils.getLocalizedBusinessTerm(key, currentLanguage);
  };

  const tPhrase = (key: keyof LanguageConfig['common_phrases']): string => {
    return LocalizationUtils.getLocalizedPhrase(key, currentLanguage);
  };

  const tMessage = (key: keyof LanguageConfig['business_messages']): string => {
    return LocalizationUtils.getLocalizedBusinessMessage(key, currentLanguage);
  };

  // Formatting functions
  const formatCurrency = (amount: number): string => {
    return NairaCurrencyFormatter.formatWithLocale(amount, currentLanguage);
  };

  const formatDate = (date: Date | string): string => {
    return NigerianDateFormatter.format(date, currentLanguage);
  };

  const formatDateTime = (date: Date | string): string => {
    return NigerianDateFormatter.formatDateTime(date, currentLanguage);
  };

  const formatNumber = (value: number, decimals: number = 0): string => {
    return NigerianNumberFormatter.format(value, currentLanguage, decimals);
  };

  // Greeting functions
  const getGreeting = (timeOfDay?: 'morning' | 'afternoon' | 'evening'): string => {
    return LocalizationUtils.getGreeting(currentLanguage, timeOfDay);
  };

  const getCurrentGreeting = (): string => {
    const timeOfDay = LocalizationUtils.getCurrentTimeOfDay();
    return getGreeting(timeOfDay);
  };

  const supportedLanguages = LocalizationUtils.getSupportedLanguages();

  const value: LocalizationContextType = {
    currentLanguage,
    languageConfig,
    changeLanguage,
    t,
    tPhrase,
    tMessage,
    formatCurrency,
    formatDate,
    formatDateTime,
    formatNumber,
    getGreeting,
    getCurrentGreeting,
    supportedLanguages
  };

  return (
    <LocalizationContext.Provider value={value}>
      {children}
    </LocalizationContext.Provider>
  );
};

export const useLocalization = (): LocalizationContextType => {
  const context = useContext(LocalizationContext);
  if (context === undefined) {
    throw new Error('useLocalization must be used within a LocalizationProvider');
  }
  return context;
};

// Custom hook for business terms
export const useBusinessTerms = () => {
  const { t } = useLocalization();
  return {
    invoice: t('invoice'),
    receipt: t('receipt'),
    payment: t('payment'),
    tax: t('tax'),
    vat: t('vat'),
    total: t('total'),
    subtotal: t('subtotal'),
    discount: t('discount'),
    customer: t('customer'),
    business: t('business'),
    date: t('date'),
    amount: t('amount'),
    description: t('description'),
    quantity: t('quantity'),
    price: t('price'),
    status: t('status'),
    pending: t('pending'),
    completed: t('completed'),
    failed: t('failed'),
    cancelled: t('cancelled'),
    refunded: t('refunded')
  };
};

// Custom hook for common phrases
export const useCommonPhrases = () => {
  const { tPhrase } = useLocalization();
  return {
    thank_you: tPhrase('thank_you'),
    please: tPhrase('please'),
    welcome: tPhrase('welcome'),
    goodbye: tPhrase('goodbye'),
    yes: tPhrase('yes'),
    no: tPhrase('no'),
    ok: tPhrase('ok'),
    cancel: tPhrase('cancel'),
    confirm: tPhrase('confirm'),
    save: tPhrase('save'),
    delete: tPhrase('delete'),
    edit: tPhrase('edit'),
    view: tPhrase('view'),
    download: tPhrase('download'),
    upload: tPhrase('upload'),
    search: tPhrase('search'),
    filter: tPhrase('filter'),
    sort: tPhrase('sort'),
    refresh: tPhrase('refresh'),
    loading: tPhrase('loading'),
    error: tPhrase('error'),
    success: tPhrase('success'),
    warning: tPhrase('warning'),
    info: tPhrase('info')
  };
};

// Custom hook for business messages
export const useBusinessMessages = () => {
  const { tMessage } = useLocalization();
  return {
    invoice_sent: tMessage('invoice_sent'),
    payment_received: tMessage('payment_received'),
    payment_pending: tMessage('payment_pending'),
    payment_failed: tMessage('payment_failed'),
    invoice_overdue: tMessage('invoice_overdue'),
    welcome_message: tMessage('welcome_message'),
    transaction_complete: tMessage('transaction_complete'),
    verification_required: tMessage('verification_required')
  };
};

export default LocalizationContext;