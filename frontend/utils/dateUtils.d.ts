/**
 * Type definitions for date utility functions
 */

/**
 * Format a date string or timestamp to a human-readable format
 */
export function formatDate(dateString: string | number | Date, options?: Intl.DateTimeFormatOptions): string;

/**
 * Format a number as currency
 */
export function formatCurrency(amount: number, currencyCode?: string): string;

/**
 * Get a relative time string (e.g., "2 hours ago")
 */
export function getRelativeTime(dateString: string | number | Date): string;
