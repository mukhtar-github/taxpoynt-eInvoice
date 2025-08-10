/**
 * Role Management System - TaxPoynt Frontend
 * =========================================
 * 
 * Complete role-based UI management system for the TaxPoynt platform.
 * Provides comprehensive access control, role switching, permissions,
 * and feature flag management.
 * 
 * Features:
 * - Role detection and management
 * - Permission-based access control  
 * - Role switching for hybrid users
 * - Component and route guards
 * - Feature flag management
 * - Integration with backend role system
 * 
 * Usage:
 * ```tsx
 * import { 
 *   RoleDetectorProvider, 
 *   PermissionProvider,
 *   useRoleDetector,
 *   usePermissions,
 *   RoleGuard,
 *   AccessGuard 
 * } from '@/role_management';
 * 
 * // Wrap your app with providers
 * <RoleDetectorProvider>
 *   <PermissionProvider>
 *     <FeatureFlagProvider>
 *       <App />
 *     </FeatureFlagProvider>
 *   </PermissionProvider>
 * </RoleDetectorProvider>
 * ```
 */

// Core role detection
export {
  RoleDetectorProvider,
  useRoleDetector,
  PlatformRole,
  RoleScope,
  RoleStatus
} from './role_detector';

export type {
  UserRoleAssignment,
  RoleDetectionResult,
  RoleDetectorContextValue
} from './role_detector';

// Permission management
export {
  PermissionProvider,
  usePermissions,
  PermissionCategory,
  PermissionAction,
  PermissionResource
} from './permission_provider';

export type {
  Permission,
  PermissionCondition,
  PermissionCheck,
  PermissionResult,
  PermissionContext
} from './permission_provider';

// Role switcher
export {
  RoleSwitcher,
  useRoleSwitch
} from './role_switcher';

export type {
  RoleMetadata
} from './role_switcher';

// Access guards
export {
  AccessGuard,
  RoleGuard,
  PermissionGuard,
  FeatureGuard,
  useAccessControl,
  GuardType,
  AccessLevel,
  FallbackBehavior
} from './access_guard';

export type {
  AccessGuardConfig,
  AccessContext,
  AccessResult,
  AccessGuardProps,
  RoleGuardProps,
  PermissionGuardProps,
  FeatureGuardProps
} from './access_guard';

// Feature flags
export {
  FeatureFlagProvider,
  useFeatureFlags,
  useFeature,
  FeatureGate,
  FeatureFlagType,
  FeatureFlagScope,
  FeatureFlagStatus
} from './feature_flag_provider';

export type {
  FeatureFlag,
  FeatureFlagCondition,
  FeatureFlagEvaluation,
  FeatureFlagContext
} from './feature_flag_provider';

// Combined provider for easy setup
export { CombinedRoleProvider } from './combined_provider';

// Utility functions and constants
export const ROLE_PRIORITIES = {
  [PlatformRole.HYBRID]: 5,
  [PlatformRole.PLATFORM_ADMIN]: 4,
  [PlatformRole.SYSTEM_INTEGRATOR]: 3,
  [PlatformRole.ACCESS_POINT_PROVIDER]: 2,
  [PlatformRole.TENANT_ADMIN]: 1,
  [PlatformRole.USER]: 0
} as const;

export const ROLE_COLORS = {
  [PlatformRole.SYSTEM_INTEGRATOR]: 'blue',
  [PlatformRole.ACCESS_POINT_PROVIDER]: 'green',
  [PlatformRole.HYBRID]: 'purple',
  [PlatformRole.PLATFORM_ADMIN]: 'red',
  [PlatformRole.TENANT_ADMIN]: 'orange',
  [PlatformRole.USER]: 'gray'
} as const;

export const ROLE_ICONS = {
  [PlatformRole.SYSTEM_INTEGRATOR]: '🔗',
  [PlatformRole.ACCESS_POINT_PROVIDER]: '🏛️',
  [PlatformRole.HYBRID]: '👑',
  [PlatformRole.PLATFORM_ADMIN]: '⚙️',
  [PlatformRole.TENANT_ADMIN]: '👥',
  [PlatformRole.USER]: '👤'
} as const;

// Common permission patterns
export const COMMON_PERMISSIONS = {
  // SI Permissions
  SI_CREATE_INTEGRATION: 'si_integration_create',
  SI_MANAGE_CERTIFICATES: 'si_certificate_manage',
  SI_ACCESS_BILLING: 'si_billing_access',
  
  // APP Permissions
  APP_SUBMIT_INVOICE: 'app_invoice_submit',
  APP_MONITOR_COMPLIANCE: 'app_compliance_monitor',
  APP_ACCESS_GRANTS: 'app_grant_access',
  
  // Hybrid Permissions
  HYBRID_FULL_ACCESS: 'hybrid_full_access',
  
  // Admin Permissions
  ADMIN_MANAGE_USERS: 'admin_user_manage',
  ADMIN_SYSTEM_CONFIG: 'admin_system_config',
  ADMIN_MANAGE_GRANTS: 'admin_grant_manage',
  
  // Common Permissions
  COMMON_READ_INVOICES: 'common_invoice_read',
  COMMON_READ_REPORTS: 'common_report_read'
} as const;

// Common feature flags
export const COMMON_FEATURES = {
  // SI Features
  SI_ADVANCED_INTEGRATION: 'si_advanced_integration',
  SI_CUSTOM_SCHEMAS: 'si_custom_schemas',
  SI_WHITE_LABEL: 'si_white_label',
  
  // APP Features
  APP_BULK_SUBMISSION: 'app_bulk_submission',
  APP_REAL_TIME_VALIDATION: 'app_real_time_validation',
  APP_GRANT_TRACKING: 'app_grant_tracking',
  
  // Hybrid Features
  HYBRID_CROSS_ROLE_ANALYTICS: 'hybrid_cross_role_analytics',
  HYBRID_UNIFIED_DASHBOARD: 'hybrid_unified_dashboard',
  
  // Admin Features
  ADMIN_SYSTEM_MONITORING: 'admin_system_monitoring',
  ADMIN_USER_IMPERSONATION: 'admin_user_impersonation',
  
  // General Features
  ENHANCED_REPORTING: 'enhanced_reporting',
  DARK_MODE: 'dark_mode'
} as const;

// Utility functions
export const getRoleDisplayName = (role: PlatformRole): string => {
  const names = {
    [PlatformRole.SYSTEM_INTEGRATOR]: 'System Integrator',
    [PlatformRole.ACCESS_POINT_PROVIDER]: 'Access Point Provider',
    [PlatformRole.HYBRID]: 'Hybrid Premium',
    [PlatformRole.PLATFORM_ADMIN]: 'Platform Admin',
    [PlatformRole.TENANT_ADMIN]: 'Tenant Admin',
    [PlatformRole.USER]: 'User'
  };
  return names[role];
};

export const getRoleDescription = (role: PlatformRole): string => {
  const descriptions = {
    [PlatformRole.SYSTEM_INTEGRATOR]: 'Manage integrations with ERPs, CRMs, and business systems',
    [PlatformRole.ACCESS_POINT_PROVIDER]: 'Submit invoices to FIRS and manage compliance',
    [PlatformRole.HYBRID]: 'Full access to both SI and APP capabilities',
    [PlatformRole.PLATFORM_ADMIN]: 'Administer the entire TaxPoynt platform',
    [PlatformRole.TENANT_ADMIN]: 'Administer your organization',
    [PlatformRole.USER]: 'Basic platform access'
  };
  return descriptions[role];
};

export const isHigherRole = (role1: PlatformRole, role2: PlatformRole): boolean => {
  return ROLE_PRIORITIES[role1] > ROLE_PRIORITIES[role2];
};

export const getHighestRole = (roles: PlatformRole[]): PlatformRole | null => {
  if (roles.length === 0) return null;
  
  return roles.reduce((highest, current) => 
    isHigherRole(current, highest) ? current : highest
  );
};

export const canSwitchBetweenRoles = (roles: PlatformRole[]): boolean => {
  return roles.includes(PlatformRole.HYBRID) || 
         (roles.includes(PlatformRole.SYSTEM_INTEGRATOR) && 
          roles.includes(PlatformRole.ACCESS_POINT_PROVIDER));
};

// HOC for role-based components
export const withRoleGuard = (
  Component: React.ComponentType<any>,
  requiredRoles: PlatformRole[],
  fallback?: React.ReactNode
) => {
  return (props: any) => (
    <RoleGuard 
      requiredRoles={requiredRoles} 
      fallbackComponent={fallback}
    >
      <Component {...props} />
    </RoleGuard>
  );
};

// HOC for permission-based components
export const withPermissionGuard = (
  Component: React.ComponentType<any>,
  requiredPermissions: string[],
  fallback?: React.ReactNode
) => {
  return (props: any) => (
    <PermissionGuard 
      requiredPermissions={requiredPermissions} 
      fallbackComponent={fallback}
    >
      <Component {...props} />
    </PermissionGuard>
  );
};

// HOC for feature-gated components
export const withFeatureGate = (
  Component: React.ComponentType<any>,
  requiredFeature: string,
  fallback?: React.ReactNode
) => {
  return (props: any) => (
    <FeatureGate 
      feature={requiredFeature} 
      fallback={fallback}
    >
      <Component {...props} />
    </FeatureGate>
  );
};

/**
 * Implementation Status and Integration Guide
 * ==========================================
 * 
 * ✅ Completed Components:
 * 1. RoleDetector - Detects and manages user roles from authentication
 * 2. PermissionProvider - Comprehensive role-based permission management
 * 3. RoleSwitcher - UI component for switching between roles
 * 4. AccessGuard - Guards for components, routes, and features
 * 5. FeatureFlagProvider - Role-based feature flag management
 * 
 * ✅ Key Features:
 * 1. Integration with existing backend role system
 * 2. Support for all TaxPoynt roles (SI, APP, Hybrid, Admin)
 * 3. Permission-based access control
 * 4. Role switching for hybrid users
 * 5. Feature flag management based on roles
 * 6. Comprehensive access guards and fallbacks
 * 7. Audit logging and access tracking
 * 8. Caching and performance optimization
 * 
 * ✅ Integration Points:
 * 1. Backend Role System - Integrates with core_platform/authentication/role_manager
 * 2. API Gateway - Works with api_gateway/role_routing system
 * 3. Frontend Components - Guards existing business interface components
 * 4. Design System - Uses existing design tokens and components
 * 
 * 🔧 Next Steps for Integration:
 * 1. Add role providers to main App component
 * 2. Update existing components to use access guards
 * 3. Configure feature flags for gradual rollouts
 * 4. Connect to actual authentication system
 * 5. Test role switching and permission flows
 * 6. Add comprehensive error handling
 * 7. Implement audit logging integration
 * 
 * 📋 Usage Examples:
 * 
 * Basic Setup:
 * ```tsx
 * // In your main App component
 * import { CombinedRoleProvider } from '@/role_management';
 * 
 * function App() {
 *   return (
 *     <CombinedRoleProvider authToken={userToken}>
 *       <Routes />
 *     </CombinedRoleProvider>
 *   );
 * }
 * ```
 * 
 * Component Protection:
 * ```tsx
 * import { RoleGuard, PlatformRole } from '@/role_management';
 * 
 * <RoleGuard requiredRoles={[PlatformRole.SYSTEM_INTEGRATOR, PlatformRole.HYBRID]}>
 *   <BillingComponent />
 * </RoleGuard>
 * ```
 * 
 * Role Switching:
 * ```tsx
 * import { RoleSwitcher } from '@/role_management';
 * 
 * <RoleSwitcher 
 *   variant="dropdown" 
 *   onRoleSwitch={(newRole) => console.log('Switched to', newRole)} 
 * />
 * ```
 * 
 * Feature Gating:
 * ```tsx
 * import { FeatureGate, useFeature } from '@/role_management';
 * 
 * <FeatureGate feature="si_advanced_integration">
 *   <AdvancedIntegrationPanel />
 * </FeatureGate>
 * 
 * // Or with hook
 * const { enabled } = useFeature('dark_mode');
 * ```
 */