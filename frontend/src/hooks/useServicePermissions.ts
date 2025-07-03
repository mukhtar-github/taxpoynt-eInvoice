import { useServiceAccess } from '../contexts/ServiceAccessContext';

export const useServicePermissions = () => {
  const { hasAccess, getAccessLevel, userServices } = useServiceAccess();

  return {
    // Core service access checkers
    canAccessApp: (level = 'read') => hasAccess('access_point_provider', level),
    canAccessSI: (level = 'read') => hasAccess('system_integration', level),
    canAccessCompliance: (level = 'read') => hasAccess('nigerian_compliance', level),
    canManageOrg: (level = 'read') => hasAccess('organization_management', level),
    
    // Legacy compatibility - existing FIRS permission system
    canAccessFirs: (level = 'read') => hasAccess('firs_api_access', level),
    canAccessDashboard: (level = 'read') => hasAccess('dashboard_access', level),
    
    // Specific permission checks based on business requirements
    canGenerateIRN: () => hasAccess('access_point_provider', 'write'),
    canSubmitToFirs: () => hasAccess('access_point_provider', 'write'),
    canManageIntegrations: () => hasAccess('system_integration', 'write'),
    canCreateConnections: () => hasAccess('system_integration', 'write'),
    canViewCompliance: () => hasAccess('nigerian_compliance', 'read'),
    canManageCompliance: () => hasAccess('nigerian_compliance', 'write'),
    canManageUsers: () => hasAccess('organization_management', 'admin'),
    canManageOrganization: () => hasAccess('organization_management', 'admin'),
    
    // Certificate and security operations
    canManageCertificates: () => hasAccess('access_point_provider', 'admin'),
    canViewCertificates: () => hasAccess('access_point_provider', 'read'),
    canSignDocuments: () => hasAccess('access_point_provider', 'write'),
    
    // Integration-specific permissions
    canConnectCRM: () => hasAccess('system_integration', 'write'),
    canConnectERP: () => hasAccess('system_integration', 'write'),
    canConnectPOS: () => hasAccess('system_integration', 'write'),
    canViewIntegrations: () => hasAccess('system_integration', 'read'),
    
    // Analytics and reporting
    canViewAnalytics: () => hasAccess('nigerian_compliance', 'read') || hasAccess('access_point_provider', 'read'),
    canExportData: () => hasAccess('nigerian_compliance', 'write') || hasAccess('access_point_provider', 'write'),
    canGenerateReports: () => hasAccess('nigerian_compliance', 'read'),
    
    // Access level getters
    getAppAccess: () => getAccessLevel('access_point_provider'),
    getSIAccess: () => getAccessLevel('system_integration'),
    getComplianceAccess: () => getAccessLevel('nigerian_compliance'),
    getOrgAccess: () => getAccessLevel('organization_management'),
    getFirsAccess: () => getAccessLevel('firs_api_access'),
    
    // User type identification
    isOwner: () => ['access_point_provider', 'system_integration', 'nigerian_compliance', 'organization_management']
      .some(service => getAccessLevel(service) === 'owner'),
    
    isAdmin: () => ['access_point_provider', 'system_integration', 'nigerian_compliance', 'organization_management']
      .some(service => ['admin', 'owner'].includes(getAccessLevel(service) || '')),
    
    isHybridUser: () => hasAccess('access_point_provider') && hasAccess('system_integration'),
    isPureAppUser: () => hasAccess('access_point_provider') && !hasAccess('system_integration'),
    isPureSIUser: () => hasAccess('system_integration') && !hasAccess('access_point_provider'),
    isPureComplianceUser: () => hasAccess('nigerian_compliance') && !hasAccess('access_point_provider') && !hasAccess('system_integration'),
    
    // Service combination checks
    hasMultipleServices: () => {
      const serviceCount = ['access_point_provider', 'system_integration', 'nigerian_compliance', 'organization_management']
        .filter(service => hasAccess(service)).length;
      return serviceCount > 1;
    },
    
    // Premium/Enterprise feature checks
    hasEnterpriseFeatures: () => hasAccess('organization_management', 'admin') || hasAccess('access_point_provider', 'owner'),
    hasPremiumFeatures: () => hasAccess('system_integration', 'write') || hasAccess('access_point_provider', 'write'),
    
    // Utility functions
    getAllServices: () => userServices.map(s => s.serviceType),
    getServicesByLevel: (level: string) => userServices.filter(s => s.accessLevel === level).map(s => s.serviceType),
    
    // Role-based UI helpers
    shouldShowAppFeatures: () => hasAccess('access_point_provider'),
    shouldShowSIFeatures: () => hasAccess('system_integration'),
    shouldShowComplianceFeatures: () => hasAccess('nigerian_compliance'),
    shouldShowOrgFeatures: () => hasAccess('organization_management'),
    
    // Navigation helpers
    getDefaultRoute: () => {
      if (hasAccess('access_point_provider')) return '/dashboard';
      if (hasAccess('system_integration')) return '/integrations';
      if (hasAccess('nigerian_compliance')) return '/compliance';
      if (hasAccess('organization_management')) return '/organization';
      return '/login';
    },
    
    // Feature flags
    canUseBetaFeatures: () => hasAccess('access_point_provider', 'admin') || hasAccess('system_integration', 'admin'),
    canAccessAPIKeys: () => hasAccess('system_integration', 'write') || hasAccess('access_point_provider', 'write'),
    canManageWebhooks: () => hasAccess('system_integration', 'write'),
    
    // Advanced checks with business logic
    canPerformBulkOperations: () => hasAccess('access_point_provider', 'write') && hasAccess('system_integration', 'read'),
    canAccessCrossServiceData: () => hasAccess('access_point_provider', 'read') && hasAccess('system_integration', 'read'),
    
    // Legacy permission compatibility
    hasLegacyPermission: (permission: string) => hasAccess(permission, 'read'),
    
    // Debug helpers (for development)
    getAllPermissions: () => userServices,
    debugAccess: (service: string, level: string = 'read') => {
      const hasPermission = hasAccess(service, level);
      const userLevel = getAccessLevel(service);
      console.log(`Service: ${service}, Required: ${level}, User Level: ${userLevel}, Has Access: ${hasPermission}`);
      return hasPermission;
    }
  };
};