/**
 * Utility functions for formatting numbers, dates, durations, and currency.
 * Enhanced with Nigerian localization support.
 */

/**
 * Format a number with thousands separators and optional decimal places.
 * 
 * @param value The number to format
 * @param decimals The number of decimal places (default: 0)
 * @param locale The locale to use for formatting (default: 'en-NG')
 * @returns Formatted number string
 */
export const formatNumber = (value: number, decimals: number = 0, locale: string = 'en-NG'): string => {
  if (isNaN(value)) return '0';
  
  return new Intl.NumberFormat(locale, {
    minimumFractionDigits: decimals,
    maximumFractionDigits: decimals,
  }).format(value);
};

/**
 * Format a currency amount in Nigerian Naira.
 * 
 * @param amount The amount to format
 * @param locale The locale to use for formatting (default: 'en-NG')
 * @returns Formatted currency string
 */
export const formatCurrency = (amount: number, locale: string = 'en-NG'): string => {
  if (isNaN(amount)) return '₦0.00';
  
  return new Intl.NumberFormat(locale, {
    style: 'currency',
    currency: 'NGN',
    currencyDisplay: 'symbol'
  }).format(amount);
};

/**
 * Format amount to kobo (smallest Nigerian currency unit).
 * 
 * @param naira Amount in naira
 * @returns Amount in kobo
 */
export const toKobo = (naira: number): number => {
  return Math.round(naira * 100);
};

/**
 * Format kobo to naira.
 * 
 * @param kobo Amount in kobo
 * @returns Amount in naira
 */
export const fromKobo = (kobo: number): number => {
  return kobo / 100;
};

/**
 * Format a duration in milliseconds to a human-readable string.
 * 
 * @param ms Duration in milliseconds
 * @returns Formatted duration string (e.g., "2.5s" or "1m 30s")
 */
export const formatDuration = (ms: number): string => {
  if (ms < 1000) {
    return `${ms}ms`;
  }
  
  if (ms < 60000) {
    return `${(ms / 1000).toFixed(1)}s`;
  }
  
  const minutes = Math.floor(ms / 60000);
  const seconds = Math.floor((ms % 60000) / 1000);
  
  return `${minutes}m ${seconds}s`;
};

/**
 * Format a date string to a human-readable format.
 * 
 * @param dateString Date string in ISO format or Date object
 * @param locale The locale to use for formatting (default: 'en-NG')
 * @returns Formatted date string (e.g., "May 22, 2025")
 */
export const formatDate = (dateString: string | Date, locale: string = 'en-NG'): string => {
  const date = typeof dateString === 'string' ? new Date(dateString) : dateString;
  
  // Use GB locale for DD/MM/YYYY format which is standard in Nigeria
  return date.toLocaleDateString('en-GB', {
    year: 'numeric',
    month: 'short',
    day: 'numeric',
  });
};

/**
 * Format a date string to include time.
 * 
 * @param dateString Date string in ISO format or Date object
 * @param locale The locale to use for formatting (default: 'en-NG')
 * @returns Formatted date and time string (e.g., "May 22, 2025, 14:30")
 */
export const formatDateTime = (dateString: string | Date, locale: string = 'en-NG'): string => {
  const date = typeof dateString === 'string' ? new Date(dateString) : dateString;
  
  // Use GB locale for DD/MM/YYYY format with 12-hour time
  return date.toLocaleString('en-GB', {
    year: 'numeric',
    month: 'short',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
    hour12: true
  });
};

/**
 * Format a date in Nigerian standard format (DD/MM/YYYY).
 * 
 * @param dateString Date string in ISO format or Date object
 * @returns Formatted date string in DD/MM/YYYY format
 */
export const formatNigerianDate = (dateString: string | Date): string => {
  const date = typeof dateString === 'string' ? new Date(dateString) : dateString;
  
  const day = date.getDate().toString().padStart(2, '0');
  const month = (date.getMonth() + 1).toString().padStart(2, '0');
  const year = date.getFullYear();
  
  return `${day}/${month}/${year}`;
};
