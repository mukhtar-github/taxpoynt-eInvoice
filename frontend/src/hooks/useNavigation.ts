import { useRouter } from 'next/router';
import { useServiceAccess } from '../contexts/ServiceAccessContext';
import { useServicePermissions } from './useServicePermissions';
import { 
  navigationItems, 
  getNavigationByCategory, 
  getNavigationByService,
  getNavigationItemById,
  type NavItem 
} from '../config/navigationConfig';

export interface NavigationState {
  currentPath: string;
  currentItem: NavItem | null;
  breadcrumbs: NavItem[];
  visibleItems: NavItem[];
  itemsByCategory: Record<string, NavItem[]>;
  isLoading: boolean;
}

export const useNavigation = () => {
  const router = useRouter();
  const { hasAccess, isLoading } = useServiceAccess();
  const permissions = useServicePermissions();

  // Get current navigation item based on path
  const getCurrentItem = (): NavItem | null => {
    const currentPath = router.pathname;
    
    // Find exact match first
    let currentItem = navigationItems.find(item => item.href === currentPath);
    
    // If no exact match, find item whose href is a prefix of current path
    if (!currentItem) {
      currentItem = navigationItems.find(item => 
        currentPath.startsWith(item.href) && item.href !== '/'
      );
    }
    
    return currentItem || null;
  };

  // Generate breadcrumbs based on current path
  const getBreadcrumbs = (): NavItem[] => {
    const currentPath = router.pathname;
    const pathSegments = currentPath.split('/').filter(Boolean);
    const breadcrumbs: NavItem[] = [];

    // Build breadcrumbs by checking each path segment
    let buildPath = '';
    for (const segment of pathSegments) {
      buildPath += `/${segment}`;
      const item = navigationItems.find(nav => nav.href === buildPath);
      if (item) {
        breadcrumbs.push(item);
      }
    }

    return breadcrumbs;
  };

  // Filter navigation items based on user permissions
  const getVisibleItems = (): NavItem[] => {
    return navigationItems.filter(item => {
      if (item.service === 'any') return true;
      return hasAccess(item.service, item.level || 'read');
    });
  };

  // Group visible items by category
  const getItemsByCategory = () => {
    const visibleItems = getVisibleItems();
    const categorized: Record<string, NavItem[]> = {};

    visibleItems.forEach(item => {
      if (!item.category) return;
      
      if (!categorized[item.category]) {
        categorized[item.category] = [];
      }
      categorized[item.category].push(item);
    });

    return categorized;
  };

  // Navigation actions
  const navigateTo = (href: string, options?: { replace?: boolean }) => {
    if (options?.replace) {
      router.replace(href);
    } else {
      router.push(href);
    }
  };

  const navigateToItem = (item: NavItem, options?: { replace?: boolean }) => {
    navigateTo(item.href, options);
  };

  const goBack = () => {
    if (window.history.length > 1) {
      router.back();
    } else {
      // Fallback to default route if no history
      navigateTo(permissions.getDefaultRoute());
    }
  };

  const goToDefaultRoute = () => {
    navigateTo(permissions.getDefaultRoute());
  };

  // Check if a path is active
  const isActive = (href: string): boolean => {
    return router.pathname === href || router.pathname.startsWith(`${href}/`);
  };

  // Check if user can access a specific navigation item
  const canAccessItem = (item: NavItem): boolean => {
    if (item.service === 'any') return true;
    return hasAccess(item.service, item.level || 'read');
  };

  // Get user's available services for navigation context
  const getAvailableServices = (): string[] => {
    const services = new Set<string>();
    getVisibleItems().forEach(item => {
      if (item.service !== 'any') {
        services.add(item.service);
      }
    });
    return Array.from(services);
  };

  // Get navigation state
  const getNavigationState = (): NavigationState => {
    return {
      currentPath: router.pathname,
      currentItem: getCurrentItem(),
      breadcrumbs: getBreadcrumbs(),
      visibleItems: getVisibleItems(),
      itemsByCategory: getItemsByCategory(),
      isLoading
    };
  };

  // Check if current page requires specific service access
  const getCurrentPageRequirements = () => {
    const currentItem = getCurrentItem();
    return {
      item: currentItem,
      service: currentItem?.service,
      level: currentItem?.level || 'read',
      hasAccess: currentItem ? canAccessItem(currentItem) : true
    };
  };

  // Get recommended next actions based on user permissions
  const getRecommendedActions = (): NavItem[] => {
    const recommended: NavItem[] = [];
    
    // Add high-value items user can access
    if (permissions.canGenerateIRN()) {
      const irnItem = getNavigationItemById('generate-irn');
      if (irnItem) recommended.push(irnItem);
    }
    
    if (permissions.canManageIntegrations()) {
      const integrationItem = getNavigationItemById('integration-setup');
      if (integrationItem) recommended.push(integrationItem);
    }
    
    if (permissions.canViewCompliance()) {
      const complianceItem = getNavigationItemById('compliance-dashboard');
      if (complianceItem) recommended.push(complianceItem);
    }
    
    return recommended.slice(0, 3); // Limit to top 3 recommendations
  };

  return {
    // State
    ...getNavigationState(),
    
    // Actions
    navigateTo,
    navigateToItem,
    goBack,
    goToDefaultRoute,
    
    // Utilities
    isActive,
    canAccessItem,
    getCurrentItem,
    getBreadcrumbs,
    getVisibleItems,
    getItemsByCategory,
    getAvailableServices,
    getCurrentPageRequirements,
    getRecommendedActions,
    
    // Helper functions
    getNavigationByCategory,
    getNavigationByService,
    getNavigationItemById
  };
};

// Hook for breadcrumb navigation
export const useBreadcrumbs = () => {
  const { breadcrumbs, navigateToItem } = useNavigation();
  
  return {
    breadcrumbs,
    navigateToBreadcrumb: navigateToItem
  };
};

// Hook for checking current page access
export const useCurrentPageAccess = () => {
  const { getCurrentPageRequirements } = useNavigation();
  
  return getCurrentPageRequirements();
};

// Hook for navigation recommendations
export const useNavigationRecommendations = () => {
  const { getRecommendedActions } = useNavigation();
  
  return {
    recommendations: getRecommendedActions()
  };
};

export default useNavigation;