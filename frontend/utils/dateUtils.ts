/**
 * Utility functions for date and currency formatting
 */

/**
 * Format a date string or timestamp to a human-readable format
 * @param dateString Date string or timestamp
 * @param options Intl.DateTimeFormatOptions
 * @returns Formatted date string
 */
export const formatDate = (dateString: string | number | Date, options?: Intl.DateTimeFormatOptions): string => {
  if (!dateString) return '-';
  
  const date = new Date(dateString);
  
  // Check if date is valid
  if (isNaN(date.getTime())) return '-';
  
  const defaultOptions: Intl.DateTimeFormatOptions = {
    year: 'numeric',
    month: 'short',
    day: 'numeric',
    ...options
  };
  
  return new Intl.DateTimeFormat('en-NG', defaultOptions).format(date);
};

/**
 * Format a number as currency
 * @param amount Amount to format
 * @param currencyCode Currency code (ISO 4217)
 * @returns Formatted currency string
 */
export const formatCurrency = (amount: number, currencyCode: string = 'NGN'): string => {
  if (amount === undefined || amount === null) return '-';
  
  return new Intl.NumberFormat('en-NG', {
    style: 'currency',
    currency: currencyCode,
    minimumFractionDigits: 2,
    maximumFractionDigits: 2
  }).format(amount);
};

/**
 * Get a relative time string (e.g., "2 hours ago")
 * @param dateString Date string or timestamp
 * @returns Relative time string
 */
export const getRelativeTime = (dateString: string | number | Date): string => {
  if (!dateString) return '';
  
  const date = new Date(dateString);
  
  // Check if date is valid
  if (isNaN(date.getTime())) return '';
  
  const rtf = new Intl.RelativeTimeFormat('en', { numeric: 'auto' });
  const now = new Date();
  const diffInSeconds = Math.floor((now.getTime() - date.getTime()) / 1000);
  
  // Less than a minute
  if (diffInSeconds < 60) {
    return 'Just now';
  }
  
  // Less than an hour
  if (diffInSeconds < 3600) {
    const minutes = Math.floor(diffInSeconds / 60);
    return rtf.format(-minutes, 'minute');
  }
  
  // Less than a day
  if (diffInSeconds < 86400) {
    const hours = Math.floor(diffInSeconds / 3600);
    return rtf.format(-hours, 'hour');
  }
  
  // Less than a week
  if (diffInSeconds < 604800) {
    const days = Math.floor(diffInSeconds / 86400);
    return rtf.format(-days, 'day');
  }
  
  // Less than a month
  if (diffInSeconds < 2592000) {
    const weeks = Math.floor(diffInSeconds / 604800);
    return rtf.format(-weeks, 'week');
  }
  
  // Less than a year
  if (diffInSeconds < 31536000) {
    const months = Math.floor(diffInSeconds / 2592000);
    return rtf.format(-months, 'month');
  }
  
  // More than a year
  const years = Math.floor(diffInSeconds / 31536000);
  return rtf.format(-years, 'year');
};
