/**
 * Utility functions for formatting numbers, dates, and durations.
 */

/**
 * Format a number with thousands separators and optional decimal places.
 * 
 * @param value The number to format
 * @param decimals The number of decimal places (default: 0)
 * @returns Formatted number string
 */
export const formatNumber = (value: number, decimals: number = 0): string => {
  if (isNaN(value)) return '0';
  
  return new Intl.NumberFormat('en-NG', {
    minimumFractionDigits: decimals,
    maximumFractionDigits: decimals,
  }).format(value);
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
 * @param dateString Date string in ISO format
 * @returns Formatted date string (e.g., "May 22, 2025")
 */
export const formatDate = (dateString: string): string => {
  return new Date(dateString).toLocaleDateString('en-NG', {
    year: 'numeric',
    month: 'short',
    day: 'numeric',
  });
};

/**
 * Format a date string to include time.
 * 
 * @param dateString Date string in ISO format
 * @returns Formatted date and time string (e.g., "May 22, 2025, 14:30")
 */
export const formatDateTime = (dateString: string): string => {
  return new Date(dateString).toLocaleString('en-NG', {
    year: 'numeric',
    month: 'short',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  });
};
