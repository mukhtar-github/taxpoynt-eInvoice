/**
 * Feature Flag Provider
 * ====================
 * 
 * Provides role-based feature flag management for the TaxPoynt platform.
 * Enables/disables features based on user roles, permissions, and configuration,
 * allowing for gradual rollouts and role-specific feature sets.
 * 
 * Features:
 * - Role-based feature enablement
 * - Dynamic feature flag evaluation
 * - Local and remote feature flag management
 * - Feature flag caching and optimization
 * - A/B testing support
 * - Override capabilities for testing
 * - Integration with role and permission systems
 */

import React, { createContext, useContext, useState, useEffect, ReactNode } from 'react';
import { useRoleDetector, PlatformRole } from './role_detector';
import { usePermissions } from './permission_provider';

// Feature flag types
export enum FeatureFlagType {
  BOOLEAN = 'boolean',
  STRING = 'string',
  NUMBER = 'number',
  JSON = 'json'
}

export enum FeatureFlagScope {
  GLOBAL = 'global',
  ROLE_BASED = 'role_based',
  PERMISSION_BASED = 'permission_based',
  USER_SPECIFIC = 'user_specific',
  ORGANIZATION = 'organization',
  TENANT = 'tenant'
}

export enum FeatureFlagStatus {
  ACTIVE = 'active',
  INACTIVE = 'inactive',
  TESTING = 'testing',
  DEPRECATED = 'deprecated'
}

// Feature flag definition
export interface FeatureFlag {
  key: string;
  name: string;
  description: string;
  type: FeatureFlagType;
  scope: FeatureFlagScope;
  status: FeatureFlagStatus;
  defaultValue: any;
  allowedRoles?: PlatformRole[];
  requiredPermissions?: string[];
  conditions?: FeatureFlagCondition[];
  metadata: Record<string, any>;
  createdAt: Date;
  updatedAt: Date;
  expiresAt?: Date;
}

export interface FeatureFlagCondition {
  type: 'role' | 'permission' | 'organization' | 'tenant' | 'percentage' | 'date' | 'custom';
  operator: 'equals' | 'in' | 'not_in' | 'greater_than' | 'less_than' | 'between' | 'before' | 'after';
  value: any;
  description: string;
}

export interface FeatureFlagEvaluation {
  flag: string;
  enabled: boolean;
  value: any;
  reason: string;
  conditions: string[];
  overridden: boolean;
  source: 'default' | 'role' | 'permission' | 'override' | 'remote';
}

export interface FeatureFlagContext {
  // Feature flag evaluation
  isEnabled: (flag: string) => boolean;
  getValue: (flag: string, defaultValue?: any) => any;
  getEvaluation: (flag: string) => FeatureFlagEvaluation | null;
  
  // Bulk operations
  getEnabledFlags: () => string[];
  getDisabledFlags: () => string[];
  getAllFlags: () => Record<string, FeatureFlag>;
  
  // Feature flag management
  setOverride: (flag: string, value: any) => void;
  removeOverride: (flag: string) => void;
  clearOverrides: () => void;
  getOverrides: () => Record<string, any>;
  
  // Remote synchronization
  refreshFlags: () => Promise<void>;
  
  // State
  isLoading: boolean;
  error: string | null;
  lastSyncAt: Date | null;
}

// TaxPoynt-specific feature flags
const TAXPOYNT_FEATURE_FLAGS: FeatureFlag[] = [
  // System Integrator Features
  {
    key: 'si_advanced_integration',
    name: 'Advanced SI Integration',
    description: 'Advanced integration features for System Integrators',
    type: FeatureFlagType.BOOLEAN,
    scope: FeatureFlagScope.ROLE_BASED,
    status: FeatureFlagStatus.ACTIVE,
    defaultValue: false,
    allowedRoles: [PlatformRole.SYSTEM_INTEGRATOR, PlatformRole.HYBRID, PlatformRole.PLATFORM_ADMIN],
    metadata: { category: 'integration', priority: 'high' },
    createdAt: new Date('2024-01-01'),
    updatedAt: new Date('2024-01-01')
  },
  {
    key: 'si_custom_schemas',
    name: 'Custom Schema Support',
    description: 'Allow SIs to create custom invoice schemas',
    type: FeatureFlagType.BOOLEAN,
    scope: FeatureFlagScope.ROLE_BASED,
    status: FeatureFlagStatus.ACTIVE,
    defaultValue: false,
    allowedRoles: [PlatformRole.SYSTEM_INTEGRATOR, PlatformRole.HYBRID, PlatformRole.PLATFORM_ADMIN],
    requiredPermissions: ['si_integration_create'],
    metadata: { category: 'schema', priority: 'medium' },
    createdAt: new Date('2024-01-01'),
    updatedAt: new Date('2024-01-01')
  },
  {
    key: 'si_white_label',
    name: 'White Label Interface',
    description: 'White label branding for SI clients',
    type: FeatureFlagType.BOOLEAN,
    scope: FeatureFlagScope.ROLE_BASED,
    status: FeatureFlagStatus.TESTING,
    defaultValue: false,
    allowedRoles: [PlatformRole.SYSTEM_INTEGRATOR, PlatformRole.HYBRID],
    metadata: { category: 'branding', priority: 'low' },
    createdAt: new Date('2024-01-01'),
    updatedAt: new Date('2024-01-01')
  },

  // Access Point Provider Features
  {
    key: 'app_bulk_submission',
    name: 'Bulk Invoice Submission',
    description: 'Submit multiple invoices to FIRS at once',
    type: FeatureFlagType.BOOLEAN,
    scope: FeatureFlagScope.ROLE_BASED,
    status: FeatureFlagStatus.ACTIVE,
    defaultValue: true,
    allowedRoles: [PlatformRole.ACCESS_POINT_PROVIDER, PlatformRole.HYBRID, PlatformRole.PLATFORM_ADMIN],
    metadata: { category: 'submission', priority: 'high' },
    createdAt: new Date('2024-01-01'),
    updatedAt: new Date('2024-01-01')
  },
  {
    key: 'app_real_time_validation',
    name: 'Real-time Validation',
    description: 'Real-time FIRS validation before submission',
    type: FeatureFlagType.BOOLEAN,
    scope: FeatureFlagScope.ROLE_BASED,
    status: FeatureFlagStatus.ACTIVE,
    defaultValue: true,
    allowedRoles: [PlatformRole.ACCESS_POINT_PROVIDER, PlatformRole.HYBRID, PlatformRole.PLATFORM_ADMIN],
    requiredPermissions: ['app_compliance_monitor'],
    metadata: { category: 'validation', priority: 'high' },
    createdAt: new Date('2024-01-01'),
    updatedAt: new Date('2024-01-01')
  },
  {
    key: 'app_grant_tracking',
    name: 'Grant Tracking Dashboard',
    description: 'Detailed grant compliance tracking',
    type: FeatureFlagType.BOOLEAN,
    scope: FeatureFlagScope.ROLE_BASED,
    status: FeatureFlagStatus.ACTIVE,
    defaultValue: true,
    allowedRoles: [PlatformRole.ACCESS_POINT_PROVIDER, PlatformRole.HYBRID, PlatformRole.PLATFORM_ADMIN],
    metadata: { category: 'grants', priority: 'medium' },
    createdAt: new Date('2024-01-01'),
    updatedAt: new Date('2024-01-01')
  },

  // Hybrid Features
  {
    key: 'hybrid_cross_role_analytics',
    name: 'Cross-Role Analytics',
    description: 'Analytics across SI and APP operations',
    type: FeatureFlagType.BOOLEAN,
    scope: FeatureFlagScope.ROLE_BASED,
    status: FeatureFlagStatus.ACTIVE,
    defaultValue: true,
    allowedRoles: [PlatformRole.HYBRID, PlatformRole.PLATFORM_ADMIN],
    metadata: { category: 'analytics', priority: 'high' },
    createdAt: new Date('2024-01-01'),
    updatedAt: new Date('2024-01-01')
  },
  {
    key: 'hybrid_unified_dashboard',
    name: 'Unified Dashboard',
    description: 'Single dashboard for SI and APP operations',
    type: FeatureFlagType.BOOLEAN,
    scope: FeatureFlagScope.ROLE_BASED,
    status: FeatureFlagStatus.ACTIVE,
    defaultValue: true,
    allowedRoles: [PlatformRole.HYBRID, PlatformRole.PLATFORM_ADMIN],
    metadata: { category: 'ui', priority: 'medium' },
    createdAt: new Date('2024-01-01'),
    updatedAt: new Date('2024-01-01')
  },

  // Admin Features
  {
    key: 'admin_system_monitoring',
    name: 'System Monitoring',
    description: 'Comprehensive system health monitoring',
    type: FeatureFlagType.BOOLEAN,
    scope: FeatureFlagScope.ROLE_BASED,
    status: FeatureFlagStatus.ACTIVE,
    defaultValue: true,
    allowedRoles: [PlatformRole.PLATFORM_ADMIN],
    requiredPermissions: ['admin_system_config'],
    metadata: { category: 'monitoring', priority: 'high' },
    createdAt: new Date('2024-01-01'),
    updatedAt: new Date('2024-01-01')
  },
  {
    key: 'admin_user_impersonation',
    name: 'User Impersonation',
    description: 'Ability to impersonate users for support',
    type: FeatureFlagType.BOOLEAN,
    scope: FeatureFlagScope.ROLE_BASED,
    status: FeatureFlagStatus.TESTING,
    defaultValue: false,
    allowedRoles: [PlatformRole.PLATFORM_ADMIN],
    requiredPermissions: ['admin_user_manage'],
    metadata: { category: 'support', priority: 'low' },
    createdAt: new Date('2024-01-01'),
    updatedAt: new Date('2024-01-01')
  },

  // General Features
  {
    key: 'enhanced_reporting',
    name: 'Enhanced Reporting',
    description: 'Advanced reporting capabilities',
    type: FeatureFlagType.BOOLEAN,
    scope: FeatureFlagScope.ROLE_BASED,
    status: FeatureFlagStatus.ACTIVE,
    defaultValue: false,
    allowedRoles: [PlatformRole.SYSTEM_INTEGRATOR, PlatformRole.ACCESS_POINT_PROVIDER, PlatformRole.HYBRID, PlatformRole.PLATFORM_ADMIN],
    metadata: { category: 'reporting', priority: 'medium' },
    createdAt: new Date('2024-01-01'),
    updatedAt: new Date('2024-01-01')
  },
  {
    key: 'dark_mode',
    name: 'Dark Mode UI',
    description: 'Dark mode interface option',
    type: FeatureFlagType.BOOLEAN,
    scope: FeatureFlagScope.GLOBAL,
    status: FeatureFlagStatus.TESTING,
    defaultValue: false,
    metadata: { category: 'ui', priority: 'low' },
    createdAt: new Date('2024-01-01'),
    updatedAt: new Date('2024-01-01')
  },

  // Configuration features
  {
    key: 'api_rate_limit',
    name: 'API Rate Limit',
    description: 'Per-role API rate limiting configuration',
    type: FeatureFlagType.NUMBER,
    scope: FeatureFlagScope.ROLE_BASED,
    status: FeatureFlagStatus.ACTIVE,
    defaultValue: 1000,
    metadata: { category: 'api', priority: 'high' },
    conditions: [
      {
        type: 'role',
        operator: 'equals',
        value: PlatformRole.SYSTEM_INTEGRATOR,
        description: 'SI rate limit'
      }
    ],
    createdAt: new Date('2024-01-01'),
    updatedAt: new Date('2024-01-01')
  }
];

// Feature flag evaluation engine
class FeatureFlagEvaluator {
  private static instance: FeatureFlagEvaluator;
  private flags: Map<string, FeatureFlag> = new Map();
  private overrides: Map<string, any> = new Map();
  private evaluationCache: Map<string, FeatureFlagEvaluation> = new Map();

  static getInstance(): FeatureFlagEvaluator {
    if (!this.instance) {
      this.instance = new FeatureFlagEvaluator();
    }
    return this.instance;
  }

  constructor() {
    // Initialize with default flags
    TAXPOYNT_FEATURE_FLAGS.forEach(flag => {
      this.flags.set(flag.key, flag);
    });
  }

  /**
   * Evaluate a feature flag for the current user context
   */
  evaluate(
    flagKey: string,
    userRoles: PlatformRole[],
    userPermissions: string[],
    context: Record<string, any> = {}
  ): FeatureFlagEvaluation {
    // Check cache first
    const cacheKey = `${flagKey}_${userRoles.join(',')}_${JSON.stringify(context)}`;
    if (this.evaluationCache.has(cacheKey)) {
      return this.evaluationCache.get(cacheKey)!;
    }

    const flag = this.flags.get(flagKey);
    if (!flag) {
      const evaluation: FeatureFlagEvaluation = {
        flag: flagKey,
        enabled: false,
        value: false,
        reason: 'Flag not found',
        conditions: [],
        overridden: false,
        source: 'default'
      };
      this.evaluationCache.set(cacheKey, evaluation);
      return evaluation;
    }

    // Check for override first
    if (this.overrides.has(flagKey)) {
      const overrideValue = this.overrides.get(flagKey);
      const evaluation: FeatureFlagEvaluation = {
        flag: flagKey,
        enabled: Boolean(overrideValue),
        value: overrideValue,
        reason: 'Manual override',
        conditions: ['Override active'],
        overridden: true,
        source: 'override'
      };
      this.evaluationCache.set(cacheKey, evaluation);
      return evaluation;
    }

    // Check if flag is active
    if (flag.status !== FeatureFlagStatus.ACTIVE) {
      const evaluation: FeatureFlagEvaluation = {
        flag: flagKey,
        enabled: false,
        value: flag.defaultValue,
        reason: `Flag status is ${flag.status}`,
        conditions: [`Status: ${flag.status}`],
        overridden: false,
        source: 'default'
      };
      this.evaluationCache.set(cacheKey, evaluation);
      return evaluation;
    }

    // Check expiration
    if (flag.expiresAt && new Date() > flag.expiresAt) {
      const evaluation: FeatureFlagEvaluation = {
        flag: flagKey,
        enabled: false,
        value: flag.defaultValue,
        reason: 'Flag has expired',
        conditions: ['Expired'],
        overridden: false,
        source: 'default'
      };
      this.evaluationCache.set(cacheKey, evaluation);
      return evaluation;
    }

    // Evaluate based on scope
    const evaluation = this.evaluateByScope(flag, userRoles, userPermissions, context);
    this.evaluationCache.set(cacheKey, evaluation);
    return evaluation;
  }

  /**
   * Evaluate flag based on its scope
   */
  private evaluateByScope(
    flag: FeatureFlag,
    userRoles: PlatformRole[],
    userPermissions: string[],
    context: Record<string, any>
  ): FeatureFlagEvaluation {
    const conditions: string[] = [];

    switch (flag.scope) {
      case FeatureFlagScope.GLOBAL:
        return {
          flag: flag.key,
          enabled: Boolean(flag.defaultValue),
          value: flag.defaultValue,
          reason: 'Global flag',
          conditions: ['Global scope'],
          overridden: false,
          source: 'default'
        };

      case FeatureFlagScope.ROLE_BASED:
        return this.evaluateRoleBased(flag, userRoles, conditions);

      case FeatureFlagScope.PERMISSION_BASED:
        return this.evaluatePermissionBased(flag, userPermissions, conditions);

      case FeatureFlagScope.USER_SPECIFIC:
        return this.evaluateUserSpecific(flag, context, conditions);

      case FeatureFlagScope.ORGANIZATION:
        return this.evaluateOrganizationBased(flag, context, conditions);

      case FeatureFlagScope.TENANT:
        return this.evaluateTenantBased(flag, context, conditions);

      default:
        return {
          flag: flag.key,
          enabled: false,
          value: flag.defaultValue,
          reason: 'Unknown scope',
          conditions: ['Unknown scope'],
          overridden: false,
          source: 'default'
        };
    }
  }

  /**
   * Evaluate role-based flag
   */
  private evaluateRoleBased(
    flag: FeatureFlag,
    userRoles: PlatformRole[],
    conditions: string[]
  ): FeatureFlagEvaluation {
    if (!flag.allowedRoles || flag.allowedRoles.length === 0) {
      conditions.push('No role restrictions');
      return {
        flag: flag.key,
        enabled: Boolean(flag.defaultValue),
        value: flag.defaultValue,
        reason: 'No role restrictions',
        conditions,
        overridden: false,
        source: 'role'
      };
    }

    const hasRequiredRole = flag.allowedRoles.some(role => userRoles.includes(role));
    conditions.push(`Required roles: ${flag.allowedRoles.join(', ')}`);
    conditions.push(`User roles: ${userRoles.join(', ')}`);

    return {
      flag: flag.key,
      enabled: hasRequiredRole && Boolean(flag.defaultValue),
      value: hasRequiredRole ? flag.defaultValue : false,
      reason: hasRequiredRole ? 'Role requirement met' : 'Role requirement not met',
      conditions,
      overridden: false,
      source: 'role'
    };
  }

  /**
   * Evaluate permission-based flag
   */
  private evaluatePermissionBased(
    flag: FeatureFlag,
    userPermissions: string[],
    conditions: string[]
  ): FeatureFlagEvaluation {
    if (!flag.requiredPermissions || flag.requiredPermissions.length === 0) {
      conditions.push('No permission restrictions');
      return {
        flag: flag.key,
        enabled: Boolean(flag.defaultValue),
        value: flag.defaultValue,
        reason: 'No permission restrictions',
        conditions,
        overridden: false,
        source: 'permission'
      };
    }

    const hasRequiredPermissions = flag.requiredPermissions.some(permission => 
      userPermissions.includes(permission)
    );
    conditions.push(`Required permissions: ${flag.requiredPermissions.join(', ')}`);

    return {
      flag: flag.key,
      enabled: hasRequiredPermissions && Boolean(flag.defaultValue),
      value: hasRequiredPermissions ? flag.defaultValue : false,
      reason: hasRequiredPermissions ? 'Permission requirement met' : 'Permission requirement not met',
      conditions,
      overridden: false,
      source: 'permission'
    };
  }

  /**
   * Evaluate user-specific flag
   */
  private evaluateUserSpecific(
    flag: FeatureFlag,
    context: Record<string, any>,
    conditions: string[]
  ): FeatureFlagEvaluation {
    // Implementation would check user-specific conditions
    conditions.push('User-specific evaluation');
    return {
      flag: flag.key,
      enabled: Boolean(flag.defaultValue),
      value: flag.defaultValue,
      reason: 'User-specific flag',
      conditions,
      overridden: false,
      source: 'default'
    };
  }

  /**
   * Evaluate organization-based flag
   */
  private evaluateOrganizationBased(
    flag: FeatureFlag,
    context: Record<string, any>,
    conditions: string[]
  ): FeatureFlagEvaluation {
    // Implementation would check organization-specific conditions
    conditions.push(`Organization: ${context.organizationId || 'none'}`);
    return {
      flag: flag.key,
      enabled: Boolean(flag.defaultValue),
      value: flag.defaultValue,
      reason: 'Organization-based flag',
      conditions,
      overridden: false,
      source: 'default'
    };
  }

  /**
   * Evaluate tenant-based flag
   */
  private evaluateTenantBased(
    flag: FeatureFlag,
    context: Record<string, any>,
    conditions: string[]
  ): FeatureFlagEvaluation {
    // Implementation would check tenant-specific conditions
    conditions.push(`Tenant: ${context.tenantId || 'none'}`);
    return {
      flag: flag.key,
      enabled: Boolean(flag.defaultValue),
      value: flag.defaultValue,
      reason: 'Tenant-based flag',
      conditions,
      overridden: false,
      source: 'default'
    };
  }

  /**
   * Set flag override
   */
  setOverride(flagKey: string, value: any): void {
    this.overrides.set(flagKey, value);
    this.clearCache();
  }

  /**
   * Remove flag override
   */
  removeOverride(flagKey: string): void {
    this.overrides.delete(flagKey);
    this.clearCache();
  }

  /**
   * Clear all overrides
   */
  clearOverrides(): void {
    this.overrides.clear();
    this.clearCache();
  }

  /**
   * Get current overrides
   */
  getOverrides(): Record<string, any> {
    return Object.fromEntries(this.overrides);
  }

  /**
   * Get all flags
   */
  getAllFlags(): Record<string, FeatureFlag> {
    return Object.fromEntries(this.flags);
  }

  /**
   * Clear evaluation cache
   */
  private clearCache(): void {
    this.evaluationCache.clear();
  }

  /**
   * Update flags from remote source
   */
  async updateFlags(remoteFlags: FeatureFlag[]): Promise<void> {
    remoteFlags.forEach(flag => {
      this.flags.set(flag.key, flag);
    });
    this.clearCache();
  }
}

// Create context
const FeatureFlagContext = createContext<FeatureFlagContext | undefined>(undefined);

// Hook for using feature flags
export const useFeatureFlags = (): FeatureFlagContext => {
  const context = useContext(FeatureFlagContext);
  if (!context) {
    throw new Error('useFeatureFlags must be used within a FeatureFlagProvider');
  }
  return context;
};

// Provider component props
interface FeatureFlagProviderProps {
  children: ReactNode;
  remoteConfig?: {
    endpoint?: string;
    apiKey?: string;
    syncInterval?: number;
  };
  initialOverrides?: Record<string, any>;
}

// Provider component
export const FeatureFlagProvider: React.FC<FeatureFlagProviderProps> = ({
  children,
  remoteConfig,
  initialOverrides = {}
}) => {
  const { detectionResult, isLoading: roleLoading } = useRoleDetector();
  const { getUserPermissions, isLoading: permissionLoading } = usePermissions();
  
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [lastSyncAt, setLastSyncAt] = useState<Date | null>(null);

  const evaluator = FeatureFlagEvaluator.getInstance();

  // Initialize overrides
  useEffect(() => {
    Object.entries(initialOverrides).forEach(([flag, value]) => {
      evaluator.setOverride(flag, value);
    });
  }, [initialOverrides]);

  // Get current user context
  const userRoles = detectionResult?.availableRoles || [];
  const userPermissions = getUserPermissions();
  const userContext = {
    organizationId: detectionResult?.organizationId,
    tenantId: detectionResult?.tenantId,
    currentRole: detectionResult?.primaryRole
  };

  // Feature flag functions
  const isEnabled = (flag: string): boolean => {
    if (roleLoading || permissionLoading) return false;
    
    const evaluation = evaluator.evaluate(flag, userRoles, userPermissions, userContext);
    return evaluation.enabled;
  };

  const getValue = (flag: string, defaultValue: any = false): any => {
    if (roleLoading || permissionLoading) return defaultValue;
    
    const evaluation = evaluator.evaluate(flag, userRoles, userPermissions, userContext);
    return evaluation.enabled ? evaluation.value : defaultValue;
  };

  const getEvaluation = (flag: string): FeatureFlagEvaluation | null => {
    if (roleLoading || permissionLoading) return null;
    
    return evaluator.evaluate(flag, userRoles, userPermissions, userContext);
  };

  const getEnabledFlags = (): string[] => {
    if (roleLoading || permissionLoading) return [];
    
    const allFlags = evaluator.getAllFlags();
    return Object.keys(allFlags).filter(flag => isEnabled(flag));
  };

  const getDisabledFlags = (): string[] => {
    if (roleLoading || permissionLoading) return [];
    
    const allFlags = evaluator.getAllFlags();
    return Object.keys(allFlags).filter(flag => !isEnabled(flag));
  };

  const getAllFlags = (): Record<string, FeatureFlag> => {
    return evaluator.getAllFlags();
  };

  const setOverride = (flag: string, value: any): void => {
    evaluator.setOverride(flag, value);
  };

  const removeOverride = (flag: string): void => {
    evaluator.removeOverride(flag);
  };

  const clearOverrides = (): void => {
    evaluator.clearOverrides();
  };

  const getOverrides = (): Record<string, any> => {
    return evaluator.getOverrides();
  };

  const refreshFlags = async (): Promise<void> => {
    if (!remoteConfig?.endpoint) return;

    setIsLoading(true);
    setError(null);

    try {
      const response = await fetch(remoteConfig.endpoint, {
        headers: {
          'Content-Type': 'application/json',
          ...(remoteConfig.apiKey && { 'Authorization': `Bearer ${remoteConfig.apiKey}` })
        }
      });

      if (!response.ok) {
        throw new Error(`Failed to fetch flags: ${response.status}`);
      }

      const data = await response.json();
      const flags = data.flags || data;

      await evaluator.updateFlags(flags);
      setLastSyncAt(new Date());

    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to refresh flags');
      console.error('Feature flag refresh failed:', err);
    } finally {
      setIsLoading(false);
    }
  };

  // Auto-sync if configured
  useEffect(() => {
    if (remoteConfig?.syncInterval && remoteConfig.endpoint) {
      const interval = setInterval(refreshFlags, remoteConfig.syncInterval);
      return () => clearInterval(interval);
    }
  }, [remoteConfig]);

  const contextValue: FeatureFlagContext = {
    isEnabled,
    getValue,
    getEvaluation,
    getEnabledFlags,
    getDisabledFlags,
    getAllFlags,
    setOverride,
    removeOverride,
    clearOverrides,
    getOverrides,
    refreshFlags,
    isLoading: isLoading || roleLoading || permissionLoading,
    error,
    lastSyncAt
  };

  return (
    <FeatureFlagContext.Provider value={contextValue}>
      {children}
    </FeatureFlagContext.Provider>
  );
};

// Utility hook for specific feature checks
export const useFeature = (flagKey: string, defaultValue: any = false) => {
  const { isEnabled, getValue, getEvaluation } = useFeatureFlags();
  
  return {
    enabled: isEnabled(flagKey),
    value: getValue(flagKey, defaultValue),
    evaluation: getEvaluation(flagKey)
  };
};

// Component wrapper for feature-gated content
export const FeatureGate: React.FC<{
  feature: string;
  children: ReactNode;
  fallback?: ReactNode;
  className?: string;
}> = ({ feature, children, fallback = null, className = '' }) => {
  const { isEnabled } = useFeatureFlags();
  
  if (!isEnabled(feature)) {
    return <div className={className}>{fallback}</div>;
  }
  
  return <div className={className}>{children}</div>;
};

export default FeatureFlagProvider;