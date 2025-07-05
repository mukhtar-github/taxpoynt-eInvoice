import React, { createContext, useContext, useEffect, useState } from 'react';
import { useRouter } from 'next/router';
import { useAuth } from '../../context/AuthContext';
import { useServiceAccess } from '../contexts/ServiceAccessContext';
import { PublicNavigation } from './PublicNavigation';
import { DynamicNavigation } from './DynamicNavigation';

interface NavigationState {
  isAuthenticated: boolean;
  isLoading: boolean;
  shouldShowPublicNav: boolean;
  shouldShowDynamicNav: boolean;
  navigationMode: 'public' | 'authenticated' | 'transitioning';
}

interface NavigationContextType extends NavigationState {
  refreshNavigation: () => void;
  forcePublicMode: () => void;
  forceAuthenticatedMode: () => void;
}

const NavigationContext = createContext<NavigationContextType | null>(null);

interface NavigationProviderProps {
  children: React.ReactNode;
  forceMode?: 'public' | 'authenticated';
}

export const NavigationProvider: React.FC<NavigationProviderProps> = ({
  children,
  forceMode
}) => {
  const { isAuthenticated, isLoading: authLoading } = useAuth();
  const { isLoading: serviceLoading } = useServiceAccess();
  const router = useRouter();
  
  const [navigationState, setNavigationState] = useState<NavigationState>({
    isAuthenticated: false,
    isLoading: true,
    shouldShowPublicNav: true,
    shouldShowDynamicNav: false,
    navigationMode: 'transitioning'
  });

  // Define routes that should always use public navigation
  const publicRoutes = [
    '/',
    '/pricing',
    '/contact',
    '/about',
    '/services',
    '/blog',
    '/auth/enhanced-signup',
    '/auth/enhanced-login',
    '/auth/signup',
    '/auth/login',
    '/auth/forgot-password',
    '/auth/reset-password'
  ];

  // Define routes that should always use authenticated navigation
  const authenticatedRoutes = [
    '/dashboard',
    '/onboarding',
    '/profile',
    '/settings',
    '/admin'
  ];

  const determineNavigationMode = (): 'public' | 'authenticated' | 'transitioning' => {
    // If force mode is specified, use that
    if (forceMode) return forceMode;
    
    // If still loading, show transitioning state
    if (authLoading || serviceLoading) return 'transitioning';
    
    const currentPath = router.pathname;
    
    // Check if current route explicitly requires public navigation
    if (publicRoutes.some(route => currentPath.startsWith(route))) {
      return 'public';
    }
    
    // Check if current route explicitly requires authenticated navigation
    if (authenticatedRoutes.some(route => currentPath.startsWith(route))) {
      return isAuthenticated ? 'authenticated' : 'public';
    }
    
    // Default behavior based on authentication state
    return isAuthenticated ? 'authenticated' : 'public';
  };

  // Update navigation state when auth or route changes
  useEffect(() => {
    const navigationMode = determineNavigationMode();
    
    setNavigationState({
      isAuthenticated,
      isLoading: authLoading || serviceLoading,
      shouldShowPublicNav: navigationMode === 'public',
      shouldShowDynamicNav: navigationMode === 'authenticated',
      navigationMode
    });
  }, [isAuthenticated, authLoading, serviceLoading, router.pathname, forceMode]);

  const refreshNavigation = () => {
    // Force a navigation state refresh
    setNavigationState(prev => ({
      ...prev,
      navigationMode: 'transitioning'
    }));
    
    // Immediately recalculate
    setTimeout(() => {
      const navigationMode = determineNavigationMode();
      setNavigationState({
        isAuthenticated,
        isLoading: authLoading || serviceLoading,
        shouldShowPublicNav: navigationMode === 'public',
        shouldShowDynamicNav: navigationMode === 'authenticated',
        navigationMode
      });
    }, 100);
  };

  const forcePublicMode = () => {
    setNavigationState(prev => ({
      ...prev,
      shouldShowPublicNav: true,
      shouldShowDynamicNav: false,
      navigationMode: 'public'
    }));
  };

  const forceAuthenticatedMode = () => {
    setNavigationState(prev => ({
      ...prev,
      shouldShowPublicNav: false,
      shouldShowDynamicNav: true,
      navigationMode: 'authenticated'
    }));
  };

  const contextValue: NavigationContextType = {
    ...navigationState,
    refreshNavigation,
    forcePublicMode,
    forceAuthenticatedMode
  };

  return (
    <NavigationContext.Provider value={contextValue}>
      {children}
    </NavigationContext.Provider>
  );
};

export const useNavigationState = () => {
  const context = useContext(NavigationContext);
  if (!context) {
    throw new Error('useNavigationState must be used within NavigationProvider');
  }
  return context;
};

// Smart Navigation Component that renders the appropriate navigation
interface SmartNavigationProps {
  className?: string;
  variant?: 'sidebar' | 'horizontal' | 'dropdown';
  showCategories?: boolean;
  showDescriptions?: boolean;
  showBadges?: boolean;
}

export const SmartNavigation: React.FC<SmartNavigationProps> = ({
  className,
  variant = 'horizontal',
  ...dynamicNavProps
}) => {
  const { 
    shouldShowPublicNav, 
    shouldShowDynamicNav, 
    navigationMode, 
    isLoading 
  } = useNavigationState();

  // Show loading state during transitions
  if (isLoading || navigationMode === 'transitioning') {
    return (
      <div className={`animate-pulse bg-gray-200 rounded h-16 ${className}`}>
        <div className="flex items-center justify-between h-full px-4">
          <div className="w-32 h-6 bg-gray-300 rounded"></div>
          <div className="flex space-x-4">
            <div className="w-16 h-6 bg-gray-300 rounded"></div>
            <div className="w-16 h-6 bg-gray-300 rounded"></div>
            <div className="w-16 h-6 bg-gray-300 rounded"></div>
          </div>
        </div>
      </div>
    );
  }

  // Render public navigation
  if (shouldShowPublicNav) {
    return <PublicNavigation className={className} />;
  }

  // Render authenticated navigation
  if (shouldShowDynamicNav) {
    return (
      <DynamicNavigation 
        variant={variant}
        className={className}
        {...dynamicNavProps}
      />
    );
  }

  // Fallback to public navigation
  return <PublicNavigation className={className} />;
};

// HOC for pages that need specific navigation behavior
export const withNavigationMode = <P extends object>(
  WrappedComponent: React.ComponentType<P>,
  mode: 'public' | 'authenticated'
) => {
  const NavigationModeComponent: React.FC<P> = (props) => (
    <NavigationProvider forceMode={mode}>
      <WrappedComponent {...props} />
    </NavigationProvider>
  );

  NavigationModeComponent.displayName = `withNavigationMode(${WrappedComponent.displayName || WrappedComponent.name})`;

  return NavigationModeComponent;
};

// Navigation Transition Component for smooth state changes
interface NavigationTransitionProps {
  children: React.ReactNode;
  className?: string;
}

export const NavigationTransition: React.FC<NavigationTransitionProps> = ({
  children,
  className
}) => {
  const { navigationMode } = useNavigationState();
  const [isVisible, setIsVisible] = useState(true);

  useEffect(() => {
    if (navigationMode === 'transitioning') {
      setIsVisible(false);
      const timer = setTimeout(() => setIsVisible(true), 150);
      return () => clearTimeout(timer);
    } else {
      setIsVisible(true);
    }
  }, [navigationMode]);

  return (
    <div 
      className={`transition-opacity duration-150 ${isVisible ? 'opacity-100' : 'opacity-0'} ${className}`}
    >
      {children}
    </div>
  );
};

export default NavigationProvider;