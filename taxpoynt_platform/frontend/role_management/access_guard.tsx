/**
 * Access Guard Component
 * =====================
 * 
 * Provides comprehensive access control for components, routes, and features based
 * on user roles and permissions. Guards content and provides fallback UI for
 * unauthorized access attempts.
 * 
 * Features:
 * - Role-based component access control
 * - Permission-based content guarding
 * - Route protection with redirects
 * - Graceful fallback UI for unauthorized access
 * - Loading states and error handling
 * - Accessibility support
 * - Audit logging for access attempts
 */

import React, { ReactNode, useEffect, useState } from 'react';
import { useRouter } from 'next/router';
import { useRoleDetector, PlatformRole } from './role_detector';
import { usePermissions, PermissionAction, PermissionResource } from './permission_provider';

// Access guard types
export enum GuardType {
  ROLE = 'role',
  PERMISSION = 'permission',
  FEATURE_FLAG = 'feature_flag',
  CUSTOM = 'custom'
}

export enum AccessLevel {
  STRICT = 'strict',      // Must have ALL required permissions/roles
  PERMISSIVE = 'permissive', // Must have ANY required permissions/roles
  CONDITIONAL = 'conditional' // Custom condition evaluation
}

export enum FallbackBehavior {
  HIDE = 'hide',         // Hide component completely
  SHOW_MESSAGE = 'show_message', // Show access denied message
  REDIRECT = 'redirect',  // Redirect to another route
  RENDER_FALLBACK = 'render_fallback' // Render custom fallback component
}

// Guard configuration interfaces
export interface AccessGuardConfig {
  type: GuardType;
  level: AccessLevel;
  fallbackBehavior: FallbackBehavior;
  requiredRoles?: PlatformRole[];
  requiredPermissions?: string[];
  requiredFeatureFlags?: string[];
  customCondition?: (context: AccessContext) => boolean;
  fallbackComponent?: ReactNode;
  fallbackMessage?: string;
  redirectTo?: string;
  allowedRoles?: PlatformRole[];
  deniedRoles?: PlatformRole[];
  context?: Record<string, any>;
  auditLog?: boolean;
  loading?: ReactNode;
}

export interface AccessContext {
  userRoles: PlatformRole[];
  userPermissions: string[];
  currentRole: PlatformRole | null;
  organizationId?: string;
  tenantId?: string;
  route: string;
  metadata: Record<string, any>;
}

// Access guard result
export interface AccessResult {
  granted: boolean;
  reason: string;
  missingRoles?: PlatformRole[];
  missingPermissions?: string[];
  alternatives?: string[];
  bypassAvailable?: boolean;
}

// Main Access Guard component props
export interface AccessGuardProps extends Partial<AccessGuardConfig> {
  children: ReactNode;
  className?: string;
  onAccessDenied?: (result: AccessResult) => void;
  onAccessGranted?: (context: AccessContext) => void;
}

// Role Guard specific props
export interface RoleGuardProps {
  children: ReactNode;
  requiredRoles: PlatformRole[];
  level?: AccessLevel;
  fallbackBehavior?: FallbackBehavior;
  fallbackComponent?: ReactNode;
  fallbackMessage?: string;
  className?: string;
}

// Permission Guard specific props
export interface PermissionGuardProps {
  children: ReactNode;
  requiredPermissions: string[];
  level?: AccessLevel;
  fallbackBehavior?: FallbackBehavior;
  fallbackComponent?: ReactNode;
  fallbackMessage?: string;
  className?: string;
}

// Feature Flag Guard specific props
export interface FeatureGuardProps {
  children: ReactNode;
  requiredFeatures: string[];
  level?: AccessLevel;
  fallbackBehavior?: FallbackBehavior;
  fallbackComponent?: ReactNode;
  className?: string;
}

// Access evaluation engine
class AccessEvaluator {
  private static instance: AccessEvaluator;
  private accessAttempts: Map<string, number> = new Map();

  static getInstance(): AccessEvaluator {
    if (!this.instance) {
      this.instance = new AccessEvaluator();
    }
    return this.instance;
  }

  /**
   * Evaluate access based on configuration
   */
  evaluateAccess(config: AccessGuardConfig, context: AccessContext): AccessResult {
    try {
      // Log access attempt if enabled
      if (config.auditLog) {
        this.logAccessAttempt(config, context);
      }

      switch (config.type) {
        case GuardType.ROLE:
          return this.evaluateRoleAccess(config, context);
        case GuardType.PERMISSION:
          return this.evaluatePermissionAccess(config, context);
        case GuardType.FEATURE_FLAG:
          return this.evaluateFeatureFlagAccess(config, context);
        case GuardType.CUSTOM:
          return this.evaluateCustomAccess(config, context);
        default:
          return { granted: false, reason: 'Invalid guard type' };
      }
    } catch (error) {
      console.error('Access evaluation error:', error);
      return { granted: false, reason: 'Access evaluation failed' };
    }
  }

  /**
   * Evaluate role-based access
   */
  private evaluateRoleAccess(config: AccessGuardConfig, context: AccessContext): AccessResult {
    const { requiredRoles = [], allowedRoles = [], deniedRoles = [], level = AccessLevel.PERMISSIVE } = config;
    
    // Check denied roles first
    if (deniedRoles.length > 0) {
      const hasDeniedRole = context.userRoles.some(role => deniedRoles.includes(role));
      if (hasDeniedRole) {
        return {
          granted: false,
          reason: 'User has denied role',
          missingRoles: deniedRoles
        };
      }
    }

    // Check required roles
    if (requiredRoles.length > 0) {
      const hasRequiredRoles = level === AccessLevel.STRICT
        ? requiredRoles.every(role => context.userRoles.includes(role))
        : requiredRoles.some(role => context.userRoles.includes(role));

      if (!hasRequiredRoles) {
        const missingRoles = requiredRoles.filter(role => !context.userRoles.includes(role));
        return {
          granted: false,
          reason: level === AccessLevel.STRICT ? 'Missing required roles' : 'No matching roles',
          missingRoles,
          alternatives: [`User needs ${level === AccessLevel.STRICT ? 'all' : 'any'} of: ${requiredRoles.join(', ')}`]
        };
      }
    }

    // Check allowed roles
    if (allowedRoles.length > 0) {
      const hasAllowedRole = context.userRoles.some(role => allowedRoles.includes(role));
      if (!hasAllowedRole) {
        return {
          granted: false,
          reason: 'User role not in allowed list',
          alternatives: [`User needs one of: ${allowedRoles.join(', ')}`]
        };
      }
    }

    return { granted: true, reason: 'Role access granted' };
  }

  /**
   * Evaluate permission-based access
   */
  private evaluatePermissionAccess(config: AccessGuardConfig, context: AccessContext): AccessResult {
    const { requiredPermissions = [], level = AccessLevel.PERMISSIVE } = config;

    if (requiredPermissions.length === 0) {
      return { granted: true, reason: 'No permissions required' };
    }

    const hasRequiredPermissions = level === AccessLevel.STRICT
      ? requiredPermissions.every(permission => context.userPermissions.includes(permission))
      : requiredPermissions.some(permission => context.userPermissions.includes(permission));

    if (!hasRequiredPermissions) {
      const missingPermissions = requiredPermissions.filter(permission => 
        !context.userPermissions.includes(permission)
      );

      return {
        granted: false,
        reason: level === AccessLevel.STRICT ? 'Missing required permissions' : 'No matching permissions',
        missingPermissions,
        alternatives: [`User needs ${level === AccessLevel.STRICT ? 'all' : 'any'} of: ${requiredPermissions.join(', ')}`]
      };
    }

    return { granted: true, reason: 'Permission access granted' };
  }

  /**
   * Evaluate feature flag access
   */
  private evaluateFeatureFlagAccess(config: AccessGuardConfig, context: AccessContext): AccessResult {
    const { requiredFeatureFlags = [], level = AccessLevel.PERMISSIVE } = config;

    if (requiredFeatureFlags.length === 0) {
      return { granted: true, reason: 'No feature flags required' };
    }

    // This would integrate with your feature flag service
    // For now, we'll use a simple implementation
    const enabledFlags = this.getEnabledFeatureFlags(context);
    
    const hasRequiredFlags = level === AccessLevel.STRICT
      ? requiredFeatureFlags.every(flag => enabledFlags.includes(flag))
      : requiredFeatureFlags.some(flag => enabledFlags.includes(flag));

    if (!hasRequiredFlags) {
      return {
        granted: false,
        reason: 'Required feature flags not enabled',
        alternatives: [`Required flags: ${requiredFeatureFlags.join(', ')}`]
      };
    }

    return { granted: true, reason: 'Feature flag access granted' };
  }

  /**
   * Evaluate custom access condition
   */
  private evaluateCustomAccess(config: AccessGuardConfig, context: AccessContext): AccessResult {
    if (!config.customCondition) {
      return { granted: false, reason: 'No custom condition provided' };
    }

    try {
      const granted = config.customCondition(context);
      return {
        granted,
        reason: granted ? 'Custom condition satisfied' : 'Custom condition not met'
      };
    } catch (error) {
      return { granted: false, reason: 'Custom condition evaluation failed' };
    }
  }

  /**
   * Get enabled feature flags for user
   */
  private getEnabledFeatureFlags(context: AccessContext): string[] {
    // This would integrate with your actual feature flag service
    // For now, return some mock flags based on roles
    const flags: string[] = [];
    
    if (context.userRoles.includes(PlatformRole.PLATFORM_ADMIN)) {
      flags.push('admin_features', 'advanced_analytics', 'system_monitoring');
    }
    
    if (context.userRoles.includes(PlatformRole.HYBRID)) {
      flags.push('hybrid_features', 'premium_support', 'advanced_reporting');
    }

    return flags;
  }

  /**
   * Log access attempt for audit purposes
   */
  private logAccessAttempt(config: AccessGuardConfig, context: AccessContext): void {
    const attemptKey = `${context.currentRole}_${context.route}_${config.type}`;
    const currentAttempts = this.accessAttempts.get(attemptKey) || 0;
    this.accessAttempts.set(attemptKey, currentAttempts + 1);

    // In a real implementation, this would send to your audit logging service
    console.log('Access attempt:', {
      user: context.currentRole,
      route: context.route,
      guardType: config.type,
      attempt: currentAttempts + 1,
      timestamp: new Date().toISOString()
    });
  }
}

// Default fallback components
const DefaultAccessDeniedMessage: React.FC<{ message?: string; result?: AccessResult }> = ({ 
  message = "You don't have permission to access this content.", 
  result 
}) => (
  <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4 my-4">
    <div className="flex items-center">
      <div className="flex-shrink-0">
        <svg className="h-5 w-5 text-yellow-400" fill="currentColor" viewBox="0 0 20 20">
          <path fillRule="evenodd" d="M8.257 3.099c.765-1.36 2.722-1.36 3.486 0l5.58 9.92c.75 1.334-.213 2.98-1.742 2.98H4.42c-1.53 0-2.493-1.646-1.743-2.98l5.58-9.92zM11 13a1 1 0 11-2 0 1 1 0 012 0zm-1-8a1 1 0 00-1 1v3a1 1 0 002 0V6a1 1 0 00-1-1z" clipRule="evenodd" />
        </svg>
      </div>
      <div className="ml-3">
        <h3 className="text-sm font-medium text-yellow-800">
          Access Restricted
        </h3>
        <div className="mt-1 text-sm text-yellow-700">
          <p>{message}</p>
          {result?.alternatives && (
            <ul className="mt-2 list-disc list-inside">
              {result.alternatives.map((alt, index) => (
                <li key={index}>{alt}</li>
              ))}
            </ul>
          )}
        </div>
      </div>
    </div>
  </div>
);

const DefaultLoadingComponent: React.FC = () => (
  <div className="flex items-center justify-center p-4">
    <svg className="animate-spin h-6 w-6 text-gray-400" fill="none" viewBox="0 0 24 24">
      <circle cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" className="opacity-25"/>
      <path fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" className="opacity-75"/>
    </svg>
    <span className="ml-2 text-gray-600">Checking access...</span>
  </div>
);

// Main Access Guard component
export const AccessGuard: React.FC<AccessGuardProps> = ({
  children,
  type = GuardType.ROLE,
  level = AccessLevel.PERMISSIVE,
  fallbackBehavior = FallbackBehavior.SHOW_MESSAGE,
  requiredRoles = [],
  requiredPermissions = [],
  requiredFeatureFlags = [],
  customCondition,
  fallbackComponent,
  fallbackMessage,
  redirectTo,
  allowedRoles = [],
  deniedRoles = [],
  context: additionalContext = {},
  auditLog = false,
  loading,
  className = '',
  onAccessDenied,
  onAccessGranted
}) => {
  const { detectionResult, isLoading: roleLoading } = useRoleDetector();
  const { getUserPermissions, isLoading: permissionLoading } = usePermissions();
  const router = useRouter();
  const [isEvaluating, setIsEvaluating] = useState(true);
  const [accessResult, setAccessResult] = useState<AccessResult | null>(null);

  const evaluator = AccessEvaluator.getInstance();

  // Build access context
  const accessContext: AccessContext = {
    userRoles: detectionResult?.availableRoles || [],
    userPermissions: getUserPermissions(),
    currentRole: detectionResult?.primaryRole || null,
    organizationId: detectionResult?.organizationId,
    tenantId: detectionResult?.tenantId,
    route: router.pathname,
    metadata: {
      ...additionalContext,
      timestamp: new Date().toISOString()
    }
  };

  // Evaluate access when dependencies change
  useEffect(() => {
    if (roleLoading || permissionLoading) return;

    setIsEvaluating(true);

    const config: AccessGuardConfig = {
      type,
      level,
      fallbackBehavior,
      requiredRoles,
      requiredPermissions,
      requiredFeatureFlags,
      customCondition,
      allowedRoles,
      deniedRoles,
      auditLog
    };

    const result = evaluator.evaluateAccess(config, accessContext);
    setAccessResult(result);

    // Trigger callbacks
    if (result.granted) {
      onAccessGranted?.(accessContext);
    } else {
      onAccessDenied?.(result);
    }

    setIsEvaluating(false);
  }, [
    roleLoading,
    permissionLoading,
    detectionResult,
    router.pathname,
    requiredRoles.join(','),
    requiredPermissions.join(','),
    requiredFeatureFlags.join(',')
  ]);

  // Handle redirect if access denied
  useEffect(() => {
    if (accessResult && !accessResult.granted && fallbackBehavior === FallbackBehavior.REDIRECT && redirectTo) {
      router.push(redirectTo);
    }
  }, [accessResult, fallbackBehavior, redirectTo, router]);

  // Show loading state
  if (isEvaluating || roleLoading || permissionLoading) {
    return (
      <div className={className}>
        {loading || <DefaultLoadingComponent />}
      </div>
    );
  }

  // Access granted - render children
  if (accessResult?.granted) {
    return <div className={className}>{children}</div>;
  }

  // Access denied - handle fallback behavior
  switch (fallbackBehavior) {
    case FallbackBehavior.HIDE:
      return null;

    case FallbackBehavior.RENDER_FALLBACK:
      return <div className={className}>{fallbackComponent}</div>;

    case FallbackBehavior.REDIRECT:
      // Redirect handled in useEffect above
      return null;

    case FallbackBehavior.SHOW_MESSAGE:
    default:
      return (
        <div className={className}>
          <DefaultAccessDeniedMessage message={fallbackMessage} result={accessResult} />
        </div>
      );
  }
};

// Specialized guard components
export const RoleGuard: React.FC<RoleGuardProps> = (props) => (
  <AccessGuard
    type={GuardType.ROLE}
    requiredRoles={props.requiredRoles}
    level={props.level}
    fallbackBehavior={props.fallbackBehavior}
    fallbackComponent={props.fallbackComponent}
    fallbackMessage={props.fallbackMessage}
    className={props.className}
  >
    {props.children}
  </AccessGuard>
);

export const PermissionGuard: React.FC<PermissionGuardProps> = (props) => (
  <AccessGuard
    type={GuardType.PERMISSION}
    requiredPermissions={props.requiredPermissions}
    level={props.level}
    fallbackBehavior={props.fallbackBehavior}
    fallbackComponent={props.fallbackComponent}
    fallbackMessage={props.fallbackMessage}
    className={props.className}
  >
    {props.children}
  </AccessGuard>
);

export const FeatureGuard: React.FC<FeatureGuardProps> = (props) => (
  <AccessGuard
    type={GuardType.FEATURE_FLAG}
    requiredFeatureFlags={props.requiredFeatures}
    level={props.level}
    fallbackBehavior={props.fallbackBehavior}
    fallbackComponent={props.fallbackComponent}
    className={props.className}
  >
    {props.children}
  </AccessGuard>
);

// Hook for programmatic access checking
export const useAccessControl = () => {
  const { detectionResult } = useRoleDetector();
  const { hasPermission, hasAnyPermission, hasAllPermissions } = usePermissions();
  const router = useRouter();

  const evaluator = AccessEvaluator.getInstance();

  const checkAccess = (config: Partial<AccessGuardConfig>): AccessResult => {
    const accessContext: AccessContext = {
      userRoles: detectionResult?.availableRoles || [],
      userPermissions: detectionResult?.activePermissions || [],
      currentRole: detectionResult?.primaryRole || null,
      organizationId: detectionResult?.organizationId,
      tenantId: detectionResult?.tenantId,
      route: router.pathname,
      metadata: {}
    };

    const fullConfig: AccessGuardConfig = {
      type: GuardType.ROLE,
      level: AccessLevel.PERMISSIVE,
      fallbackBehavior: FallbackBehavior.HIDE,
      ...config
    };

    return evaluator.evaluateAccess(fullConfig, accessContext);
  };

  return {
    checkAccess,
    hasPermission,
    hasAnyPermission,
    hasAllPermissions,
    currentRole: detectionResult?.primaryRole,
    userRoles: detectionResult?.availableRoles || []
  };
};

export default AccessGuard;