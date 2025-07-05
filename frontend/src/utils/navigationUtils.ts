import { type NavItem } from '../config/navigationConfig';

/**
 * Navigation utility functions for common navigation tasks
 */

// Generate URL with query parameters
export const buildUrlWithParams = (
  baseUrl: string, 
  params: Record<string, string | number | boolean>
): string => {
  const url = new URL(baseUrl, window.location.origin);
  
  Object.entries(params).forEach(([key, value]) => {
    if (value !== undefined && value !== null) {
      url.searchParams.set(key, value.toString());
    }
  });
  
  return url.pathname + url.search;
};

// Extract query parameters from URL
export const getUrlParams = (url?: string): Record<string, string> => {
  const searchParams = new URLSearchParams(url ? new URL(url).search : window.location.search);
  const params: Record<string, string> = {};
  
  for (const [key, value] of searchParams.entries()) {
    params[key] = value;
  }
  
  return params;
};

// Check if URL matches pattern
export const urlMatches = (url: string, pattern: string): boolean => {
  // Convert pattern to regex (simple implementation)
  const regexPattern = pattern
    .replace(/\*/g, '.*')
    .replace(/\?/g, '\\?')
    .replace(/\./g, '\\.');
    
  const regex = new RegExp(`^${regexPattern}$`);
  return regex.test(url);
};

// Generate breadcrumb text from navigation items
export const generateBreadcrumbText = (breadcrumbs: NavItem[]): string => {
  return breadcrumbs.map(item => item.label).join(' > ');
};

// Get page title from navigation items
export const getPageTitle = (
  currentItem: NavItem | null, 
  siteTitle: string = 'TaxPoynt eInvoice'
): string => {
  if (!currentItem) return siteTitle;
  return `${currentItem.label} | ${siteTitle}`;
};

// Generate meta description from navigation item
export const getPageDescription = (currentItem: NavItem | null): string => {
  if (!currentItem || !currentItem.description) {
    return 'TaxPoynt eInvoice - FIRS-certified e-invoicing platform for Nigerian businesses';
  }
  return currentItem.description;
};

// Sort navigation items by priority/category
export const sortNavigationItems = (
  items: NavItem[], 
  sortBy: 'alphabetical' | 'category' | 'priority' = 'alphabetical'
): NavItem[] => {
  switch (sortBy) {
    case 'alphabetical':
      return [...items].sort((a, b) => a.label.localeCompare(b.label));
      
    case 'category':
      return [...items].sort((a, b) => {
        if (a.category !== b.category) {
          return (a.category || '').localeCompare(b.category || '');
        }
        return a.label.localeCompare(b.label);
      });
      
    case 'priority':
      // Priority based on badges and features
      const getPriority = (item: NavItem): number => {
        if (item.badge === 'Primary') return 5;
        if (item.isNew) return 4;
        if (item.isBeta) return 3;
        if (item.badge) return 2;
        return 1;
      };
      
      return [...items].sort((a, b) => {
        const priorityDiff = getPriority(b) - getPriority(a);
        if (priorityDiff !== 0) return priorityDiff;
        return a.label.localeCompare(b.label);
      });
      
    default:
      return items;
  }
};

// Filter navigation items by search query
export const searchNavigationItems = (
  items: NavItem[], 
  query: string
): NavItem[] => {
  if (!query.trim()) return items;
  
  const searchTerm = query.toLowerCase().trim();
  
  return items.filter(item => 
    item.label.toLowerCase().includes(searchTerm) ||
    item.description?.toLowerCase().includes(searchTerm) ||
    item.category?.toLowerCase().includes(searchTerm)
  );
};

// Group navigation items by a field
export const groupNavigationItems = <T extends keyof NavItem>(
  items: NavItem[], 
  groupBy: T
): Record<string, NavItem[]> => {
  const groups: Record<string, NavItem[]> = {};
  
  items.forEach(item => {
    const key = (item[groupBy] as string) || 'Other';
    if (!groups[key]) {
      groups[key] = [];
    }
    groups[key].push(item);
  });
  
  return groups;
};

// Check if navigation item is external link
export const isExternalLink = (href: string): boolean => {
  try {
    const url = new URL(href, window.location.origin);
    return url.origin !== window.location.origin;
  } catch {
    return href.startsWith('http://') || href.startsWith('https://');
  }
};

// Generate navigation analytics event data
export const getNavigationAnalytics = (item: NavItem) => {
  return {
    event: 'navigation_click',
    item_id: item.id,
    item_label: item.label,
    item_category: item.category,
    item_service: item.service,
    item_level: item.level,
    item_href: item.href,
    has_badge: !!(item.badge || item.isNew || item.isBeta),
    timestamp: new Date().toISOString()
  };
};

// Validate navigation item structure
export const validateNavigationItem = (item: any): item is NavItem => {
  return (
    typeof item === 'object' &&
    item !== null &&
    typeof item.id === 'string' &&
    typeof item.label === 'string' &&
    typeof item.href === 'string' &&
    typeof item.service === 'string' &&
    (item.icon === undefined || typeof item.icon === 'function')
  );
};

// Deep clone navigation items (for modification)
export const cloneNavigationItems = (items: NavItem[]): NavItem[] => {
  return JSON.parse(JSON.stringify(items));
};

// Get navigation item ancestors (for hierarchical navigation)
export const getNavigationAncestors = (
  items: NavItem[], 
  targetId: string
): NavItem[] => {
  const ancestors: NavItem[] = [];
  
  const findAncestors = (navItems: NavItem[], parentPath: NavItem[] = []): boolean => {
    for (const item of navItems) {
      const currentPath = [...parentPath, item];
      
      if (item.id === targetId) {
        ancestors.push(...parentPath);
        return true;
      }
      
      if (item.children && findAncestors(item.children, currentPath)) {
        return true;
      }
    }
    return false;
  };
  
  findAncestors(items);
  return ancestors;
};

// Calculate navigation item accessibility score
export const getAccessibilityScore = (item: NavItem): number => {
  let score = 100;
  
  // Deduct points for missing accessibility features
  if (!item.description) score -= 10;
  if (!item.icon) score -= 5;
  if (item.label.length < 3) score -= 15;
  if (item.label.length > 50) score -= 10;
  
  return Math.max(0, score);
};

// Generate navigation item preview data
export const getNavigationPreview = (item: NavItem) => {
  return {
    id: item.id,
    label: item.label,
    description: item.description || 'No description available',
    category: item.category || 'Uncategorized',
    service: item.service,
    level: item.level || 'read',
    href: item.href,
    hasIcon: !!item.icon,
    badges: [
      item.badge && { type: 'custom', text: item.badge },
      item.isNew && { type: 'new', text: 'New' },
      item.isBeta && { type: 'beta', text: 'Beta' }
    ].filter(Boolean),
    accessibilityScore: getAccessibilityScore(item)
  };
};

export default {
  buildUrlWithParams,
  getUrlParams,
  urlMatches,
  generateBreadcrumbText,
  getPageTitle,
  getPageDescription,
  sortNavigationItems,
  searchNavigationItems,
  groupNavigationItems,
  isExternalLink,
  getNavigationAnalytics,
  validateNavigationItem,
  cloneNavigationItems,
  getNavigationAncestors,
  getAccessibilityScore,
  getNavigationPreview
};