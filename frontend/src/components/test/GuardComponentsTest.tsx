import React from 'react';
import { ServiceGuard, AppGuard, SIGuard, ComplianceGuard, OrgGuard, FirsGuard, MultiServiceGuard, PermissionCheck } from '../guards/ServiceGuard';
import { ProtectedRoute, AppProtectedRoute, SIProtectedRoute, MultiServiceProtectedRoute } from '../guards/ProtectedRoute';
import { useServicePermissions } from '../../hooks/useServicePermissions';

/**
 * Test component demonstrating guard components and protected routes
 * This component should be used for development and testing purposes only
 */
export const GuardComponentsTest: React.FC = () => {
  const permissions = useServicePermissions();

  return (
    <div className="max-w-6xl mx-auto p-6 space-y-8">
      <h1 className="text-3xl font-bold text-gray-900 mb-8">Guard Components Test</h1>

      {/* Service Guard Examples */}
      <div className="bg-white rounded-lg shadow p-6">
        <h2 className="text-xl font-semibold mb-4">Service Guard Examples</h2>
        
        <div className="space-y-4">
          <div>
            <h3 className="font-medium text-gray-700 mb-2">Basic Service Guard</h3>
            <ServiceGuard service="access_point_provider" level="read">
              <div className="p-4 bg-green-50 border border-green-200 rounded">
                ✅ You have APP read access!
              </div>
            </ServiceGuard>
          </div>

          <div>
            <h3 className="font-medium text-gray-700 mb-2">APP Guard (Write Level)</h3>
            <AppGuard level="write">
              <div className="p-4 bg-blue-50 border border-blue-200 rounded">
                ✅ You can generate IRNs and submit to FIRS!
              </div>
            </AppGuard>
          </div>

          <div>
            <h3 className="font-medium text-gray-700 mb-2">SI Guard with Custom Fallback</h3>
            <SIGuard 
              level="admin"
              fallback={
                <div className="p-4 bg-yellow-50 border border-yellow-200 rounded">
                  ⚠️ Custom fallback: You need SI admin access for this feature
                </div>
              }
            >
              <div className="p-4 bg-green-50 border border-green-200 rounded">
                ✅ You have SI admin access!
              </div>
            </SIGuard>
          </div>

          <div>
            <h3 className="font-medium text-gray-700 mb-2">Multi-Service Guard (AND)</h3>
            <MultiServiceGuard
              services={[
                { service: 'access_point_provider', level: 'read' },
                { service: 'system_integration', level: 'read' }
              ]}
              operator="AND"
            >
              <div className="p-4 bg-purple-50 border border-purple-200 rounded">
                ✅ You have both APP and SI access (Hybrid User)!
              </div>
            </MultiServiceGuard>
          </div>

          <div>
            <h3 className="font-medium text-gray-700 mb-2">Multi-Service Guard (OR)</h3>
            <MultiServiceGuard
              services={[
                { service: 'access_point_provider', level: 'write' },
                { service: 'system_integration', level: 'write' }
              ]}
              operator="OR"
            >
              <div className="p-4 bg-indigo-50 border border-indigo-200 rounded">
                ✅ You have write access to APP or SI!
              </div>
            </MultiServiceGuard>
          </div>
        </div>
      </div>

      {/* Permission Check Examples */}
      <div className="bg-white rounded-lg shadow p-6">
        <h2 className="text-xl font-semibold mb-4">Permission Check Examples</h2>
        
        <div className="space-y-4">
          <PermissionCheck service="access_point_provider" level="read">
            {(hasAccess) => (
              <div className={`p-4 rounded border ${hasAccess ? 'bg-green-50 border-green-200' : 'bg-red-50 border-red-200'}`}>
                {hasAccess ? '✅ Can view APP features' : '❌ Cannot view APP features'}
              </div>
            )}
          </PermissionCheck>

          <PermissionCheck service="system_integration" level="write">
            {(hasAccess) => (
              <div className={`p-4 rounded border ${hasAccess ? 'bg-green-50 border-green-200' : 'bg-red-50 border-red-200'}`}>
                {hasAccess ? '✅ Can create integrations' : '❌ Cannot create integrations'}
              </div>
            )}
          </PermissionCheck>

          <PermissionCheck service="organization_management" level="admin">
            {(hasAccess) => (
              <div className={`p-4 rounded border ${hasAccess ? 'bg-green-50 border-green-200' : 'bg-red-50 border-red-200'}`}>
                {hasAccess ? '✅ Can manage organization' : '❌ Cannot manage organization'}
              </div>
            )}
          </PermissionCheck>
        </div>
      </div>

      {/* Specialized Guards */}
      <div className="bg-white rounded-lg shadow p-6">
        <h2 className="text-xl font-semibold mb-4">Specialized Guards</h2>
        
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <ComplianceGuard>
            <div className="p-4 bg-green-50 border border-green-200 rounded">
              ✅ Compliance Features Available
            </div>
          </ComplianceGuard>

          <OrgGuard level="admin">
            <div className="p-4 bg-blue-50 border border-blue-200 rounded">
              ✅ Organization Management Available
            </div>
          </OrgGuard>

          <FirsGuard>
            <div className="p-4 bg-purple-50 border border-purple-200 rounded">
              ✅ FIRS API Access Available
            </div>
          </FirsGuard>

          <ServiceGuard service="dashboard_access">
            <div className="p-4 bg-indigo-50 border border-indigo-200 rounded">
              ✅ Dashboard Access Available
            </div>
          </ServiceGuard>
        </div>
      </div>

      {/* Business Logic Examples */}
      <div className="bg-white rounded-lg shadow p-6">
        <h2 className="text-xl font-semibold mb-4">Business Logic Examples</h2>
        
        <div className="space-y-4">
          {/* IRN Generation Button */}
          <ServiceGuard service="access_point_provider" level="write">
            <button className="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700">
              Generate IRN
            </button>
          </ServiceGuard>

          {/* Integration Management */}
          <ServiceGuard service="system_integration" level="write">
            <button className="px-4 py-2 bg-green-600 text-white rounded hover:bg-green-700">
              Create Integration
            </button>
          </ServiceGuard>

          {/* Certificate Management */}
          <ServiceGuard service="access_point_provider" level="admin">
            <button className="px-4 py-2 bg-purple-600 text-white rounded hover:bg-purple-700">
              Manage Certificates
            </button>
          </ServiceGuard>

          {/* User Management */}
          <ServiceGuard service="organization_management" level="admin">
            <button className="px-4 py-2 bg-red-600 text-white rounded hover:bg-red-700">
              Manage Users
            </button>
          </ServiceGuard>
        </div>
      </div>

      {/* Permission Summary */}
      <div className="bg-white rounded-lg shadow p-6">
        <h2 className="text-xl font-semibold mb-4">Current User Permissions</h2>
        
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div className="space-y-2">
            <h3 className="font-medium text-gray-700">Service Access</h3>
            <div className="text-sm space-y-1">
              <div>APP: {permissions.canAccessApp() ? '✅' : '❌'} ({permissions.getAppAccess() || 'None'})</div>
              <div>SI: {permissions.canAccessSI() ? '✅' : '❌'} ({permissions.getSIAccess() || 'None'})</div>
              <div>Compliance: {permissions.canAccessCompliance() ? '✅' : '❌'} ({permissions.getComplianceAccess() || 'None'})</div>
              <div>Organization: {permissions.canManageOrg() ? '✅' : '❌'} ({permissions.getOrgAccess() || 'None'})</div>
            </div>
          </div>

          <div className="space-y-2">
            <h3 className="font-medium text-gray-700">User Type</h3>
            <div className="text-sm space-y-1">
              <div>Owner: {permissions.isOwner() ? '✅' : '❌'}</div>
              <div>Admin: {permissions.isAdmin() ? '✅' : '❌'}</div>
              <div>Hybrid User: {permissions.isHybridUser() ? '✅' : '❌'}</div>
              <div>Pure APP: {permissions.isPureAppUser() ? '✅' : '❌'}</div>
              <div>Pure SI: {permissions.isPureSIUser() ? '✅' : '❌'}</div>
            </div>
          </div>
        </div>
      </div>

      {/* Feature Flags */}
      <div className="bg-white rounded-lg shadow p-6">
        <h2 className="text-xl font-semibold mb-4">Feature Flags</h2>
        
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div className="text-sm">
            <div className="font-medium text-gray-700 mb-2">Beta Features</div>
            <div>{permissions.canUseBetaFeatures() ? '✅ Enabled' : '❌ Disabled'}</div>
          </div>

          <div className="text-sm">
            <div className="font-medium text-gray-700 mb-2">Premium Features</div>
            <div>{permissions.hasPremiumFeatures() ? '✅ Enabled' : '❌ Disabled'}</div>
          </div>

          <div className="text-sm">
            <div className="font-medium text-gray-700 mb-2">Enterprise Features</div>
            <div>{permissions.hasEnterpriseFeatures() ? '✅ Enabled' : '❌ Disabled'}</div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default GuardComponentsTest;