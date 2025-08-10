/**
 * Permission Provider
 * ==================
 * 
 * Provides comprehensive role-based permission management throughout the TaxPoynt
 * frontend application. Integrates with the role detector to provide fine-grained
 * access control for components, routes, and features.
 * 
 * Features:
 * - Role-based permission checking
 * - Component-level access control
 * - Route-level protection
 * - Feature flag management based on roles
 * - Permission caching and optimization
 * - Integration with backend permission system
 */

import React, { createContext, useContext, useState, useEffect, ReactNode, useMemo } from 'react';
import { useRoleDetector, PlatformRole, RoleScope } from './role_detector';

// Permission categories based on TaxPoynt's business model
export enum PermissionCategory {
  SYSTEM_INTEGRATION = 'system_integration',
  INVOICE_PROCESSING = 'invoice_processing',
  FIRS_COMPLIANCE = 'firs_compliance',
  BILLING_MANAGEMENT = 'billing_management',
  USER_MANAGEMENT = 'user_management',
  ADMIN_FUNCTIONS = 'admin_functions',
  REPORTING = 'reporting',
  INTEGRATION_MANAGEMENT = 'integration_management',
  CERTIFICATE_MANAGEMENT = 'certificate_management',
  GRANT_MANAGEMENT = 'grant_management'
}

export enum PermissionAction {
  CREATE = 'create',
  READ = 'read',
  UPDATE = 'update',
  DELETE = 'delete',
  EXECUTE = 'execute',
  APPROVE = 'approve',
  SUBMIT = 'submit',
  CONFIGURE = 'configure',
  MONITOR = 'monitor',
  EXPORT = 'export'
}

export enum PermissionResource {
  INVOICE = 'invoice',
  INTEGRATION = 'integration',
  CERTIFICATE = 'certificate',
  USER = 'user',
  ORGANIZATION = 'organization',
  BILLING = 'billing',
  REPORT = 'report',
  WEBHOOK = 'webhook',
  API_KEY = 'api_key',
  GRANT = 'grant',
  COMPLIANCE_RULE = 'compliance_rule',
  SYSTEM_CONFIG = 'system_config'
}

// Permission string format: category:action:resource
export interface Permission {
  id: string;
  category: PermissionCategory;
  action: PermissionAction;
  resource: PermissionResource;
  scope: RoleScope;
  description: string;
  requiredRoles: PlatformRole[];
  conditions?: PermissionCondition[];
}

export interface PermissionCondition {
  type: 'tenant' | 'organization' | 'time' | 'ip' | 'feature_flag';
  operator: 'equals' | 'in' | 'not_in' | 'before' | 'after' | 'between';
  value: any;
  description: string;
}

export interface PermissionCheck {
  permission: string;
  context?: Record<string, any>;
  resource?: string;
  scope?: RoleScope;
}

export interface PermissionResult {
  granted: boolean;
  reason?: string;
  conditions?: string[];
  alternatives?: string[];
}

export interface PermissionContext {
  // Permission checking
  hasPermission: (permission: string, context?: Record<string, any>) => boolean;
  checkPermission: (check: PermissionCheck) => PermissionResult;
  hasAnyPermission: (permissions: string[], context?: Record<string, any>) => boolean;
  hasAllPermissions: (permissions: string[], context?: Record<string, any>) => boolean;
  
  // Role-based checks
  canPerformAction: (action: PermissionAction, resource: PermissionResource, context?: Record<string, any>) => boolean;
  canAccessCategory: (category: PermissionCategory) => boolean;
  
  // Component access
  canRenderComponent: (componentName: string) => boolean;
  canAccessRoute: (route: string) => boolean;
  
  // Feature flags
  isFeatureEnabled: (feature: string) => boolean;
  getFeatureConfig: (feature: string) => any;
  
  // Permission metadata
  getAllPermissions: () => Permission[];
  getUserPermissions: () => string[];
  getRolePermissions: (role: PlatformRole) => string[];
  
  // Permission state
  isLoading: boolean;
  error: string | null;
  refreshPermissions: () => Promise<void>;
}

// Create context
const PermissionContext = createContext<PermissionContext | undefined>(undefined);

// Hook for using permission context
export const usePermissions = (): PermissionContext => {
  const context = useContext(PermissionContext);
  if (!context) {
    throw new Error('usePermissions must be used within a PermissionProvider');
  }
  return context;
};

// Permission manager class
class PermissionManager {
  private static instance: PermissionManager;
  private permissionCache: Map<string, PermissionResult> = new Map();
  private featureFlags: Map<string, any> = new Map();
  
  static getInstance(): PermissionManager {
    if (!this.instance) {
      this.instance = new PermissionManager();
    }
    return this.instance;
  }

  /**
   * Core permission definitions based on TaxPoynt roles
   */
  private getDefaultPermissions(): Permission[] {
    return [
      // System Integrator (SI) Permissions
      {
        id: 'si_integration_create',
        category: PermissionCategory.SYSTEM_INTEGRATION,
        action: PermissionAction.CREATE,
        resource: PermissionResource.INTEGRATION,
        scope: RoleScope.TENANT,
        description: 'Create new system integrations',
        requiredRoles: [PlatformRole.SYSTEM_INTEGRATOR, PlatformRole.HYBRID, PlatformRole.PLATFORM_ADMIN]
      },
      {
        id: 'si_certificate_manage',
        category: PermissionCategory.CERTIFICATE_MANAGEMENT,
        action: PermissionAction.CONFIGURE,
        resource: PermissionResource.CERTIFICATE,
        scope: RoleScope.TENANT,
        description: 'Manage digital certificates',
        requiredRoles: [PlatformRole.SYSTEM_INTEGRATOR, PlatformRole.HYBRID, PlatformRole.PLATFORM_ADMIN]
      },
      {
        id: 'si_billing_access',
        category: PermissionCategory.BILLING_MANAGEMENT,
        action: PermissionAction.READ,
        resource: PermissionResource.BILLING,
        scope: RoleScope.TENANT,
        description: 'Access billing information',
        requiredRoles: [PlatformRole.SYSTEM_INTEGRATOR, PlatformRole.HYBRID, PlatformRole.PLATFORM_ADMIN]
      },

      // Access Point Provider (APP) Permissions
      {
        id: 'app_invoice_submit',
        category: PermissionCategory.INVOICE_PROCESSING,
        action: PermissionAction.SUBMIT,
        resource: PermissionResource.INVOICE,
        scope: RoleScope.TENANT,
        description: 'Submit invoices to FIRS',
        requiredRoles: [PlatformRole.ACCESS_POINT_PROVIDER, PlatformRole.HYBRID, PlatformRole.PLATFORM_ADMIN]
      },
      {
        id: 'app_compliance_monitor',
        category: PermissionCategory.FIRS_COMPLIANCE,
        action: PermissionAction.MONITOR,
        resource: PermissionResource.COMPLIANCE_RULE,
        scope: RoleScope.TENANT,
        description: 'Monitor FIRS compliance status',
        requiredRoles: [PlatformRole.ACCESS_POINT_PROVIDER, PlatformRole.HYBRID, PlatformRole.PLATFORM_ADMIN]
      },
      {
        id: 'app_grant_access',
        category: PermissionCategory.GRANT_MANAGEMENT,
        action: PermissionAction.READ,
        resource: PermissionResource.GRANT,
        scope: RoleScope.TENANT,
        description: 'Access grant information',
        requiredRoles: [PlatformRole.ACCESS_POINT_PROVIDER, PlatformRole.HYBRID, PlatformRole.PLATFORM_ADMIN]
      },

      // Hybrid Role Permissions (SI + APP combined)
      {
        id: 'hybrid_full_access',
        category: PermissionCategory.SYSTEM_INTEGRATION,
        action: PermissionAction.EXECUTE,
        resource: PermissionResource.INTEGRATION,
        scope: RoleScope.TENANT,
        description: 'Full access to SI and APP capabilities',
        requiredRoles: [PlatformRole.HYBRID, PlatformRole.PLATFORM_ADMIN]
      },

      // Admin Permissions
      {
        id: 'admin_user_manage',
        category: PermissionCategory.USER_MANAGEMENT,
        action: PermissionAction.CREATE,
        resource: PermissionResource.USER,
        scope: RoleScope.GLOBAL,
        description: 'Manage platform users',
        requiredRoles: [PlatformRole.PLATFORM_ADMIN]
      },
      {
        id: 'admin_system_config',
        category: PermissionCategory.ADMIN_FUNCTIONS,
        action: PermissionAction.CONFIGURE,
        resource: PermissionResource.SYSTEM_CONFIG,
        scope: RoleScope.GLOBAL,
        description: 'Configure system settings',
        requiredRoles: [PlatformRole.PLATFORM_ADMIN]
      },
      {
        id: 'admin_grant_manage',
        category: PermissionCategory.GRANT_MANAGEMENT,
        action: PermissionAction.CONFIGURE,
        resource: PermissionResource.GRANT,
        scope: RoleScope.GLOBAL,
        description: 'Manage FIRS grants and compliance',
        requiredRoles: [PlatformRole.PLATFORM_ADMIN]
      },

      // Common Permissions
      {
        id: 'common_invoice_read',
        category: PermissionCategory.INVOICE_PROCESSING,
        action: PermissionAction.READ,
        resource: PermissionResource.INVOICE,
        scope: RoleScope.TENANT,
        description: 'View invoices',
        requiredRoles: [PlatformRole.SYSTEM_INTEGRATOR, PlatformRole.ACCESS_POINT_PROVIDER, PlatformRole.HYBRID, PlatformRole.PLATFORM_ADMIN]
      },
      {
        id: 'common_report_read',
        category: PermissionCategory.REPORTING,
        action: PermissionAction.READ,
        resource: PermissionResource.REPORT,
        scope: RoleScope.TENANT,
        description: 'View reports',
        requiredRoles: [PlatformRole.SYSTEM_INTEGRATOR, PlatformRole.ACCESS_POINT_PROVIDER, PlatformRole.HYBRID, PlatformRole.PLATFORM_ADMIN]
      }
    ];
  }

  /**
   * Check if user has specific permission
   */
  checkPermission(
    permissionId: string,
    userRoles: PlatformRole[],
    userPermissions: string[],
    context?: Record<string, any>
  ): PermissionResult {
    // Check cache first
    const cacheKey = `${permissionId}_${userRoles.join(',')}_${JSON.stringify(context || {})}`;
    if (this.permissionCache.has(cacheKey)) {
      return this.permissionCache.get(cacheKey)!;
    }

    // Direct permission check
    if (userPermissions.includes(permissionId)) {
      const result = { granted: true, reason: 'Direct permission grant' };
      this.permissionCache.set(cacheKey, result);
      return result;
    }

    // Role-based permission check
    const permission = this.getDefaultPermissions().find(p => p.id === permissionId);
    if (!permission) {
      const result = { granted: false, reason: 'Permission not found' };
      this.permissionCache.set(cacheKey, result);
      return result;
    }

    // Check if user has required role
    const hasRequiredRole = permission.requiredRoles.some(role => userRoles.includes(role));
    if (!hasRequiredRole) {
      const result = { 
        granted: false, 
        reason: 'Insufficient role permissions',
        alternatives: permission.requiredRoles.map(r => `Requires ${r} role`)
      };
      this.permissionCache.set(cacheKey, result);
      return result;
    }

    // Check conditions if any
    if (permission.conditions) {
      const conditionResults = permission.conditions.map(condition => 
        this.evaluateCondition(condition, context)
      );
      
      if (conditionResults.some(result => !result)) {
        const result = { 
          granted: false, 
          reason: 'Permission conditions not met',
          conditions: permission.conditions.map(c => c.description)
        };
        this.permissionCache.set(cacheKey, result);
        return result;
      }
    }

    const result = { granted: true, reason: 'Role-based permission grant' };
    this.permissionCache.set(cacheKey, result);
    return result;
  }

  /**
   * Evaluate permission condition
   */
  private evaluateCondition(condition: PermissionCondition, context?: Record<string, any>): boolean {
    if (!context) return false;

    switch (condition.type) {
      case 'tenant':
        return this.evaluateComparison(context.tenantId, condition.operator, condition.value);
      case 'organization':
        return this.evaluateComparison(context.organizationId, condition.operator, condition.value);
      case 'feature_flag':
        return this.isFeatureEnabled(condition.value);
      case 'time':
        return this.evaluateTimeCondition(condition.operator, condition.value);
      default:
        return false;
    }
  }

  /**
   * Evaluate comparison operators
   */
  private evaluateComparison(actual: any, operator: string, expected: any): boolean {
    switch (operator) {
      case 'equals':
        return actual === expected;
      case 'in':
        return Array.isArray(expected) && expected.includes(actual);
      case 'not_in':
        return Array.isArray(expected) && !expected.includes(actual);
      default:
        return false;
    }
  }

  /**
   * Evaluate time-based conditions
   */
  private evaluateTimeCondition(operator: string, value: any): boolean {
    const now = new Date();
    const compareTime = new Date(value);

    switch (operator) {
      case 'before':
        return now < compareTime;
      case 'after':
        return now > compareTime;
      case 'between':
        const [start, end] = value;
        return now >= new Date(start) && now <= new Date(end);
      default:
        return false;
    }
  }

  /**
   * Feature flag management
   */
  isFeatureEnabled(feature: string): boolean {
    return this.featureFlags.get(feature) === true;
  }

  setFeatureFlag(feature: string, enabled: boolean): void {
    this.featureFlags.set(feature, enabled);
  }

  /**
   * Clear permission cache
   */
  clearCache(): void {
    this.permissionCache.clear();
  }
}

// Provider component props
interface PermissionProviderProps {
  children: ReactNode;
  customPermissions?: Permission[];
  featureFlags?: Record<string, any>;
}

// Provider component
export const PermissionProvider: React.FC<PermissionProviderProps> = ({
  children,
  customPermissions = [],
  featureFlags = {}
}) => {
  const { detectionResult, isLoading: roleLoading, error: roleError } = useRoleDetector();
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  
  const permissionManager = PermissionManager.getInstance();

  // Initialize feature flags
  useEffect(() => {
    Object.entries(featureFlags).forEach(([feature, value]) => {
      permissionManager.setFeatureFlag(feature, value);
    });
  }, [featureFlags]);

  // Memoized permissions and user context
  const userRoles = useMemo(() => {
    return detectionResult?.availableRoles || [];
  }, [detectionResult]);

  const userPermissions = useMemo(() => {
    return detectionResult?.activePermissions || [];
  }, [detectionResult]);

  const userContext = useMemo(() => {
    return {
      tenantId: detectionResult?.tenantId,
      organizationId: detectionResult?.organizationId,
      scope: detectionResult?.currentScope
    };
  }, [detectionResult]);

  // Initialize loading state
  useEffect(() => {
    if (!roleLoading) {
      setIsLoading(false);
    }
    if (roleError) {
      setError(roleError);
    }
  }, [roleLoading, roleError]);

  // Permission checking functions
  const hasPermission = (permission: string, context?: Record<string, any>): boolean => {
    if (!detectionResult) return false;
    
    const mergedContext = { ...userContext, ...context };
    const result = permissionManager.checkPermission(permission, userRoles, userPermissions, mergedContext);
    return result.granted;
  };

  const checkPermission = (check: PermissionCheck): PermissionResult => {
    if (!detectionResult) {
      return { granted: false, reason: 'User not authenticated' };
    }
    
    const mergedContext = { ...userContext, ...check.context };
    return permissionManager.checkPermission(check.permission, userRoles, userPermissions, mergedContext);
  };

  const hasAnyPermission = (permissions: string[], context?: Record<string, any>): boolean => {
    return permissions.some(permission => hasPermission(permission, context));
  };

  const hasAllPermissions = (permissions: string[], context?: Record<string, any>): boolean => {
    return permissions.every(permission => hasPermission(permission, context));
  };

  const canPerformAction = (
    action: PermissionAction,
    resource: PermissionResource,
    context?: Record<string, any>
  ): boolean => {
    // Check for specific permission first
    const specificPermission = `${action}_${resource}`;
    if (hasPermission(specificPermission, context)) return true;

    // Check for category-based permissions
    const categoryPermissions = permissionManager.getDefaultPermissions().filter(
      p => p.action === action && p.resource === resource
    );
    
    return categoryPermissions.some(permission => 
      hasPermission(permission.id, context)
    );
  };

  const canAccessCategory = (category: PermissionCategory): boolean => {
    const categoryPermissions = permissionManager.getDefaultPermissions().filter(
      p => p.category === category
    );
    
    return categoryPermissions.some(permission => hasPermission(permission.id));
  };

  const canRenderComponent = (componentName: string): boolean => {
    // Component access rules
    const componentRules: Record<string, string[]> = {
      'BillingPage': ['si_billing_access'],
      'PackageSelector': ['si_billing_access'],
      'AdminGrantDashboard': ['admin_grant_manage'],
      'IntegrationManager': ['si_integration_create'],
      'FIRSComplianceMonitor': ['app_compliance_monitor']
    };

    const requiredPermissions = componentRules[componentName];
    if (!requiredPermissions) return true; // Allow access to unprotected components

    return hasAnyPermission(requiredPermissions);
  };

  const canAccessRoute = (route: string): boolean => {
    // Route access rules
    const routeRules: Record<string, string[]> = {
      '/admin': ['admin_user_manage', 'admin_system_config'],
      '/billing': ['si_billing_access'],
      '/service-packages': ['si_billing_access'],
      '/firs-integration': ['app_invoice_submit', 'app_compliance_monitor'],
      '/grant-tracking': ['admin_grant_manage']
    };

    const requiredPermissions = routeRules[route];
    if (!requiredPermissions) return true; // Allow access to unprotected routes

    return hasAnyPermission(requiredPermissions);
  };

  const isFeatureEnabled = (feature: string): boolean => {
    return permissionManager.isFeatureEnabled(feature);
  };

  const getFeatureConfig = (feature: string): any => {
    return featureFlags[feature];
  };

  const getAllPermissions = (): Permission[] => {
    return [...permissionManager.getDefaultPermissions(), ...customPermissions];
  };

  const getUserPermissions = (): string[] => {
    return userPermissions;
  };

  const getRolePermissions = (role: PlatformRole): string[] => {
    return permissionManager.getDefaultPermissions()
      .filter(p => p.requiredRoles.includes(role))
      .map(p => p.id);
  };

  const refreshPermissions = async (): Promise<void> => {
    permissionManager.clearCache();
    // Trigger role detection refresh if needed
  };

  const contextValue: PermissionContext = {
    hasPermission,
    checkPermission,
    hasAnyPermission,
    hasAllPermissions,
    canPerformAction,
    canAccessCategory,
    canRenderComponent,
    canAccessRoute,
    isFeatureEnabled,
    getFeatureConfig,
    getAllPermissions,
    getUserPermissions,
    getRolePermissions,
    isLoading,
    error,
    refreshPermissions
  };

  return (
    <PermissionContext.Provider value={contextValue}>
      {children}
    </PermissionContext.Provider>
  );
};

// Export hook and utilities
export default PermissionProvider;