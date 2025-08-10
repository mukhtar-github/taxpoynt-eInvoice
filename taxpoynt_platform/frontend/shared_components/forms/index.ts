/**
 * Forms Components Index
 * =====================
 * 
 * Central export for all TaxPoynt Platform form components.
 * Provides form building blocks with consistent validation and styling.
 * 
 * @author TaxPoynt Development Team
 * @version 1.0.0
 */

// Form Components
export { FormField } from './FormField';
export type { FormFieldProps } from './FormField';

export { Select } from './Select';
export type { SelectProps, SelectOption } from './Select';

export { FormSection } from './FormSection';
export type { FormSectionProps } from './FormSection';

// Form utilities and types
export interface FormValidationError {
  field: string;
  message: string;
  type: 'required' | 'format' | 'min' | 'max' | 'custom';
}

export interface FormState<T = any> {
  values: T;
  errors: Record<string, string | string[]>;
  touched: Record<string, boolean>;
  isSubmitting: boolean;
  isValid: boolean;
}

// Common validation patterns for Nigerian business context
export const ValidationPatterns = {
  // Nigerian phone number (e.g., +234, 0803, etc.)
  nigerianPhone: /^(\+234|0)[789][01]\d{8}$/,
  
  // Tax Identification Number (TIN) - 8 digits
  tin: /^\d{8}$/,
  
  // Corporate Affairs Commission (CAC) number
  cac: /^(RC|BN|IT)\d+$/,
  
  // Nigerian postal code
  postalCode: /^\d{6}$/,
  
  // Email validation
  email: /^[^\s@]+@[^\s@]+\.[^\s@]+$/,
  
  // Currency amount (Naira)
  nairaAmount: /^\d{1,3}(,\d{3})*(\.\d{2})?$/,
  
  // Bank verification number (BVN) - 11 digits
  bvn: /^\d{11}$/,
  
  // Account number - 10 digits
  accountNumber: /^\d{10}$/,
};

// Form validation helpers
export const FormValidators = {
  required: (value: any) => {
    if (value === null || value === undefined || value === '') {
      return 'This field is required';
    }
    if (Array.isArray(value) && value.length === 0) {
      return 'This field is required';
    }
    return null;
  },

  email: (value: string) => {
    if (!value) return null;
    if (!ValidationPatterns.email.test(value)) {
      return 'Please enter a valid email address';
    }
    return null;
  },

  nigerianPhone: (value: string) => {
    if (!value) return null;
    if (!ValidationPatterns.nigerianPhone.test(value)) {
      return 'Please enter a valid Nigerian phone number';
    }
    return null;
  },

  tin: (value: string) => {
    if (!value) return null;
    if (!ValidationPatterns.tin.test(value)) {
      return 'TIN must be 8 digits';
    }
    return null;
  },

  cac: (value: string) => {
    if (!value) return null;
    if (!ValidationPatterns.cac.test(value)) {
      return 'Please enter a valid CAC registration number (e.g., RC123456)';
    }
    return null;
  },

  minLength: (min: number) => (value: string) => {
    if (!value) return null;
    if (value.length < min) {
      return `Must be at least ${min} characters`;
    }
    return null;
  },

  maxLength: (max: number) => (value: string) => {
    if (!value) return null;
    if (value.length > max) {
      return `Must be no more than ${max} characters`;
    }
    return null;
  },

  minValue: (min: number) => (value: number) => {
    if (value === null || value === undefined) return null;
    if (value < min) {
      return `Must be at least ${min}`;
    }
    return null;
  },

  maxValue: (max: number) => (value: number) => {
    if (value === null || value === undefined) return null;
    if (value > max) {
      return `Must be no more than ${max}`;
    }
    return null;
  },

  custom: (validator: (value: any) => string | null) => validator,
};

// Form submission helper
export const handleFormSubmit = <T>(
  values: T,
  validators: Record<keyof T, Array<(value: any) => string | null>>,
  onSubmit: (values: T) => Promise<void> | void
) => {
  const errors: Record<string, string> = {};
  
  // Validate all fields
  Object.keys(validators).forEach(field => {
    const fieldValidators = validators[field as keyof T];
    const fieldValue = values[field as keyof T];
    
    for (const validator of fieldValidators) {
      const error = validator(fieldValue);
      if (error) {
        errors[field] = error;
        break;
      }
    }
  });
  
  // If no errors, submit the form
  if (Object.keys(errors).length === 0) {
    return onSubmit(values);
  }
  
  // Return errors
  throw new Error(`Validation failed: ${JSON.stringify(errors)}`);
};

// Nigerian business form presets
export const NigerianBusinessFormOptions = {
  states: [
    { value: 'AB', label: 'Abia' },
    { value: 'FC', label: 'Abuja (FCT)' },
    { value: 'AD', label: 'Adamawa' },
    { value: 'AK', label: 'Akwa Ibom' },
    { value: 'AN', label: 'Anambra' },
    { value: 'BA', label: 'Bauchi' },
    { value: 'BY', label: 'Bayelsa' },
    { value: 'BE', label: 'Benue' },
    { value: 'BO', label: 'Borno' },
    { value: 'CR', label: 'Cross River' },
    { value: 'DE', label: 'Delta' },
    { value: 'EB', label: 'Ebonyi' },
    { value: 'ED', label: 'Edo' },
    { value: 'EK', label: 'Ekiti' },
    { value: 'EN', label: 'Enugu' },
    { value: 'GO', label: 'Gombe' },
    { value: 'IM', label: 'Imo' },
    { value: 'JI', label: 'Jigawa' },
    { value: 'KD', label: 'Kaduna' },
    { value: 'KN', label: 'Kano' },
    { value: 'KT', label: 'Katsina' },
    { value: 'KE', label: 'Kebbi' },
    { value: 'KO', label: 'Kogi' },
    { value: 'KW', label: 'Kwara' },
    { value: 'LA', label: 'Lagos' },
    { value: 'NA', label: 'Nasarawa' },
    { value: 'NI', label: 'Niger' },
    { value: 'OG', label: 'Ogun' },
    { value: 'ON', label: 'Ondo' },
    { value: 'OS', label: 'Osun' },
    { value: 'OY', label: 'Oyo' },
    { value: 'PL', label: 'Plateau' },
    { value: 'RI', label: 'Rivers' },
    { value: 'SO', label: 'Sokoto' },
    { value: 'TA', label: 'Taraba' },
    { value: 'YO', label: 'Yobe' },
    { value: 'ZA', label: 'Zamfara' },
  ],

  businessTypes: [
    { value: 'limited_company', label: 'Limited Liability Company (LLC)' },
    { value: 'public_company', label: 'Public Limited Company (PLC)' },
    { value: 'partnership', label: 'Partnership' },
    { value: 'sole_proprietorship', label: 'Sole Proprietorship' },
    { value: 'cooperative', label: 'Cooperative Society' },
    { value: 'ngo', label: 'Non-Governmental Organization' },
    { value: 'trust', label: 'Trust' },
  ],

  industries: [
    { value: 'agriculture', label: 'Agriculture & Agro-Processing' },
    { value: 'manufacturing', label: 'Manufacturing' },
    { value: 'oil_gas', label: 'Oil & Gas' },
    { value: 'financial_services', label: 'Financial Services' },
    { value: 'telecommunications', label: 'Telecommunications' },
    { value: 'construction', label: 'Construction & Real Estate' },
    { value: 'retail_trade', label: 'Retail & Wholesale Trade' },
    { value: 'hospitality', label: 'Hospitality & Tourism' },
    { value: 'healthcare', label: 'Healthcare & Pharmaceuticals' },
    { value: 'education', label: 'Education' },
    { value: 'technology', label: 'Information Technology' },
    { value: 'transportation', label: 'Transportation & Logistics' },
    { value: 'mining', label: 'Mining & Quarrying' },
    { value: 'entertainment', label: 'Entertainment & Media' },
    { value: 'professional_services', label: 'Professional Services' },
  ],
};