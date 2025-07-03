import React, { useEffect, useState } from 'react';
import { useRouter } from 'next/router';
import { useAuth } from '../../../context/AuthContext';
import { useServiceAccess } from '../../contexts/ServiceAccessContext';
import { AccessDenied } from '../ui/AccessDenied';

interface ProtectedRouteProps {
  children: React.ReactNode;
  requiredService?: string;
  requiredLevel?: string;
  fallback?: React.ReactNode;
  redirectTo?: string;
  showUpgrade?: boolean;
}

export const ProtectedRoute: React.FC<ProtectedRouteProps> = ({
  children,
  requiredService,
  requiredLevel = 'read',
  fallback,
  redirectTo,
  showUpgrade = false
}) => {
  const { isAuthenticated, isLoading: authLoading } = useAuth();
  const { hasAccess, isLoading: serviceLoading } = useServiceAccess();
  const router = useRouter();
  const [hasRedirected, setHasRedirected] = useState(false);

  const isLoading = authLoading || serviceLoading;

  useEffect(() => {
    if (!isLoading && !hasRedirected) {
      // First check authentication
      if (!isAuthenticated) {
        setHasRedirected(true);
        router.push(`/auth/login?redirect=${encodeURIComponent(router.asPath)}`);
        return;
      }

      // Then check service permissions if required
      if (requiredService && !hasAccess(requiredService, requiredLevel)) {
        if (redirectTo) {
          setHasRedirected(true);
          router.push(redirectTo);
          return;
        }
        // If no redirect specified, component will show access denied
      }
    }
  }, [isAuthenticated, isLoading, hasAccess, requiredService, requiredLevel, router, redirectTo, hasRedirected]);

  // Show loading state
  if (isLoading || hasRedirected) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-500"></div>
      </div>
    );
  }

  // Check authentication first
  if (!isAuthenticated) {
    return null; // Will redirect via useEffect
  }

  // Check service permissions if required
  if (requiredService && !hasAccess(requiredService, requiredLevel)) {
    return fallback || (
      <AccessDenied 
        service={requiredService} 
        requiredLevel={requiredLevel}
        showUpgrade={showUpgrade}
      />
    );
  }

  // Render children if all checks pass
  return <>{children}</>;
};

// Specialized route protection components
export const AppProtectedRoute: React.FC<Omit<ProtectedRouteProps, 'requiredService'>> = (props) => (
  <ProtectedRoute {...props} requiredService="access_point_provider" />
);

export const SIProtectedRoute: React.FC<Omit<ProtectedRouteProps, 'requiredService'>> = (props) => (
  <ProtectedRoute {...props} requiredService="system_integration" />
);

export const ComplianceProtectedRoute: React.FC<Omit<ProtectedRouteProps, 'requiredService'>> = (props) => (
  <ProtectedRoute {...props} requiredService="nigerian_compliance" />
);

export const OrgProtectedRoute: React.FC<Omit<ProtectedRouteProps, 'requiredService'>> = (props) => (
  <ProtectedRoute {...props} requiredService="organization_management" />
);

export const FirsProtectedRoute: React.FC<Omit<ProtectedRouteProps, 'requiredService'>> = (props) => (
  <ProtectedRoute {...props} requiredService="firs_api_access" />
);

// Multi-service protected route
interface MultiServiceProtectedRouteProps {
  children: React.ReactNode;
  requiredServices: Array<{ service: string; level?: string }>;
  operator?: 'AND' | 'OR';
  fallback?: React.ReactNode;
  redirectTo?: string;
  showUpgrade?: boolean;
}

export const MultiServiceProtectedRoute: React.FC<MultiServiceProtectedRouteProps> = ({
  children,
  requiredServices,
  operator = 'AND',
  fallback,
  redirectTo,
  showUpgrade = false
}) => {
  const { isAuthenticated, isLoading: authLoading } = useAuth();
  const { hasAccess, isLoading: serviceLoading } = useServiceAccess();
  const router = useRouter();
  const [hasRedirected, setHasRedirected] = useState(false);

  const isLoading = authLoading || serviceLoading;

  useEffect(() => {
    if (!isLoading && !hasRedirected) {
      if (!isAuthenticated) {
        setHasRedirected(true);
        router.push(`/auth/login?redirect=${encodeURIComponent(router.asPath)}`);
        return;
      }

      const hasRequiredAccess = operator === 'AND' 
        ? requiredServices.every(({ service, level = 'read' }) => hasAccess(service, level))
        : requiredServices.some(({ service, level = 'read' }) => hasAccess(service, level));

      if (!hasRequiredAccess && redirectTo) {
        setHasRedirected(true);
        router.push(redirectTo);
      }
    }
  }, [isAuthenticated, isLoading, hasAccess, requiredServices, operator, router, redirectTo, hasRedirected]);

  if (isLoading || hasRedirected) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-500"></div>
      </div>
    );
  }

  if (!isAuthenticated) {
    return null;
  }

  const hasRequiredAccess = operator === 'AND' 
    ? requiredServices.every(({ service, level = 'read' }) => hasAccess(service, level))
    : requiredServices.some(({ service, level = 'read' }) => hasAccess(service, level));

  if (!hasRequiredAccess) {
    return fallback || (
      <AccessDenied 
        message={`You need access to ${operator === 'AND' ? 'all' : 'one'} of the required services`}
        showUpgrade={showUpgrade}
      />
    );
  }

  return <>{children}</>;
};

// Higher-order component for route protection
export const withProtectedRoute = <P extends object>(
  WrappedComponent: React.ComponentType<P>,
  options: {
    requiredService?: string;
    requiredLevel?: string;
    redirectTo?: string;
    showUpgrade?: boolean;
  } = {}
) => {
  const ProtectedComponent: React.FC<P> = (props) => (
    <ProtectedRoute {...options}>
      <WrappedComponent {...props} />
    </ProtectedRoute>
  );

  ProtectedComponent.displayName = `withProtectedRoute(${WrappedComponent.displayName || WrappedComponent.name})`;

  return ProtectedComponent;
};

export default ProtectedRoute;