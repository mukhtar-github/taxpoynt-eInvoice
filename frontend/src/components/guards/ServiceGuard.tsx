import React from 'react';
import { useServiceAccess } from '../../contexts/ServiceAccessContext';
import { AccessDenied } from '../ui/AccessDenied';

interface ServiceGuardProps {
  service: string;
  level?: string;
  children: React.ReactNode;
  fallback?: React.ReactNode;
  showUpgrade?: boolean;
  message?: string;
}

export const ServiceGuard: React.FC<ServiceGuardProps> = ({
  service,
  level = 'read',
  children,
  fallback,
  showUpgrade = false,
  message
}) => {
  const { hasAccess, isLoading } = useServiceAccess();

  // Show loading state while checking permissions
  if (isLoading) {
    return (
      <div className="flex items-center justify-center p-8">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary-500"></div>
      </div>
    );
  }

  // Check if user has required access
  if (!hasAccess(service, level)) {
    return fallback || (
      <AccessDenied 
        service={service} 
        requiredLevel={level}
        message={message}
        showUpgrade={showUpgrade}
      />
    );
  }

  // Render children if access is granted
  return <>{children}</>;
};

// Specialized guard components for common use cases
export const AppGuard: React.FC<Omit<ServiceGuardProps, 'service'>> = (props) => (
  <ServiceGuard {...props} service="access_point_provider" />
);

export const SIGuard: React.FC<Omit<ServiceGuardProps, 'service'>> = (props) => (
  <ServiceGuard {...props} service="system_integration" />
);

export const ComplianceGuard: React.FC<Omit<ServiceGuardProps, 'service'>> = (props) => (
  <ServiceGuard {...props} service="nigerian_compliance" />
);

export const OrgGuard: React.FC<Omit<ServiceGuardProps, 'service'>> = (props) => (
  <ServiceGuard {...props} service="organization_management" />
);

export const FirsGuard: React.FC<Omit<ServiceGuardProps, 'service'>> = (props) => (
  <ServiceGuard {...props} service="firs_api_access" />
);

// Multi-service guard for features requiring multiple services
interface MultiServiceGuardProps {
  services: Array<{ service: string; level?: string }>;
  operator?: 'AND' | 'OR';
  children: React.ReactNode;
  fallback?: React.ReactNode;
  message?: string;
}

export const MultiServiceGuard: React.FC<MultiServiceGuardProps> = ({
  services,
  operator = 'AND',
  children,
  fallback,
  message
}) => {
  const { hasAccess, isLoading } = useServiceAccess();

  if (isLoading) {
    return (
      <div className="flex items-center justify-center p-8">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary-500"></div>
      </div>
    );
  }

  const hasRequiredAccess = operator === 'AND' 
    ? services.every(({ service, level = 'read' }) => hasAccess(service, level))
    : services.some(({ service, level = 'read' }) => hasAccess(service, level));

  if (!hasRequiredAccess) {
    return fallback || (
      <AccessDenied 
        message={message || `You need access to ${operator === 'AND' ? 'all' : 'one'} of the required services`}
      />
    );
  }

  return <>{children}</>;
};

// Inline permission check component
interface PermissionCheckProps {
  service: string;
  level?: string;
  children: (hasAccess: boolean) => React.ReactNode;
}

export const PermissionCheck: React.FC<PermissionCheckProps> = ({
  service,
  level = 'read',
  children
}) => {
  const { hasAccess } = useServiceAccess();
  return <>{children(hasAccess(service, level))}</>;
};

export default ServiceGuard;