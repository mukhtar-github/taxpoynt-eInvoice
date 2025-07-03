import React from 'react';

/**
 * Usage examples and documentation for Guard Components
 * This component demonstrates best practices and common patterns
 */
export const GuardUsageExamples: React.FC = () => {
  return (
    <div className="max-w-4xl mx-auto p-6 space-y-8">
      <h1 className="text-3xl font-bold text-gray-900 mb-8">Guard Components Usage Guide</h1>

      {/* Basic Usage */}
      <div className="bg-white rounded-lg shadow p-6">
        <h2 className="text-xl font-semibold mb-4">Basic Usage</h2>
        
        <div className="space-y-4">
          <div>
            <h3 className="font-medium text-gray-700 mb-2">ServiceGuard</h3>
            <pre className="bg-gray-100 p-4 rounded text-sm overflow-x-auto">
{`import { ServiceGuard } from '@/components/guards/ServiceGuard';

// Basic usage
<ServiceGuard service="access_point_provider" level="read">
  <DashboardContent />
</ServiceGuard>

// With custom fallback
<ServiceGuard 
  service="system_integration" 
  level="write"
  fallback={<div>You need SI write access</div>}
>
  <IntegrationForm />
</ServiceGuard>`}
            </pre>
          </div>

          <div>
            <h3 className="font-medium text-gray-700 mb-2">ProtectedRoute</h3>
            <pre className="bg-gray-100 p-4 rounded text-sm overflow-x-auto">
{`import { ProtectedRoute } from '@/components/guards/ProtectedRoute';

// Basic authentication check
<ProtectedRoute>
  <DashboardPage />
</ProtectedRoute>

// With service requirement
<ProtectedRoute 
  requiredService="access_point_provider" 
  requiredLevel="write"
>
  <IRNGenerationPage />
</ProtectedRoute>`}
            </pre>
          </div>
        </div>
      </div>

      {/* Specialized Components */}
      <div className="bg-white rounded-lg shadow p-6">
        <h2 className="text-xl font-semibold mb-4">Specialized Components</h2>
        
        <div className="space-y-4">
          <div>
            <h3 className="font-medium text-gray-700 mb-2">Service-Specific Guards</h3>
            <pre className="bg-gray-100 p-4 rounded text-sm overflow-x-auto">
{`import { AppGuard, SIGuard, ComplianceGuard, OrgGuard } from '@/components/guards/ServiceGuard';

// APP features
<AppGuard level="write">
  <IRNGenerationButton />
</AppGuard>

// SI features
<SIGuard level="admin">
  <IntegrationManagement />
</SIGuard>

// Compliance features
<ComplianceGuard>
  <ComplianceReports />
</ComplianceGuard>

// Organization management
<OrgGuard level="admin">
  <UserManagement />
</OrgGuard>`}
            </pre>
          </div>

          <div>
            <h3 className="font-medium text-gray-700 mb-2">Service-Specific Routes</h3>
            <pre className="bg-gray-100 p-4 rounded text-sm overflow-x-auto">
{`import { AppProtectedRoute, SIProtectedRoute } from '@/components/guards/ProtectedRoute';

// APP protected pages
<AppProtectedRoute requiredLevel="write">
  <IRNGenerationPage />
</AppProtectedRoute>

// SI protected pages
<SIProtectedRoute requiredLevel="admin">
  <IntegrationManagementPage />
</SIProtectedRoute>`}
            </pre>
          </div>
        </div>
      </div>

      {/* Advanced Patterns */}
      <div className="bg-white rounded-lg shadow p-6">
        <h2 className="text-xl font-semibold mb-4">Advanced Patterns</h2>
        
        <div className="space-y-4">
          <div>
            <h3 className="font-medium text-gray-700 mb-2">Multi-Service Requirements</h3>
            <pre className="bg-gray-100 p-4 rounded text-sm overflow-x-auto">
{`import { MultiServiceGuard, MultiServiceProtectedRoute } from '@/components/guards/ServiceGuard';

// Require ALL services (AND operator)
<MultiServiceGuard
  services={[
    { service: 'access_point_provider', level: 'read' },
    { service: 'system_integration', level: 'read' }
  ]}
  operator="AND"
>
  <HybridUserFeatures />
</MultiServiceGuard>

// Require ANY service (OR operator)
<MultiServiceGuard
  services={[
    { service: 'access_point_provider', level: 'write' },
    { service: 'system_integration', level: 'write' }
  ]}
  operator="OR"
>
  <AdvancedFeatures />
</MultiServiceGuard>`}
            </pre>
          </div>

          <div>
            <h3 className="font-medium text-gray-700 mb-2">Permission-Based Rendering</h3>
            <pre className="bg-gray-100 p-4 rounded text-sm overflow-x-auto">
{`import { PermissionCheck } from '@/components/guards/ServiceGuard';

<PermissionCheck service="access_point_provider" level="write">
  {(hasAccess) => (
    <button 
      disabled={!hasAccess}
      className={hasAccess ? 'btn-primary' : 'btn-disabled'}
    >
      {hasAccess ? 'Generate IRN' : 'Access Required'}
    </button>
  )}
</PermissionCheck>`}
            </pre>
          </div>

          <div>
            <h3 className="font-medium text-gray-700 mb-2">HOC Pattern</h3>
            <pre className="bg-gray-100 p-4 rounded text-sm overflow-x-auto">
{`import { withProtectedRoute } from '@/components/guards/ProtectedRoute';

// Wrap component with protection
const ProtectedDashboard = withProtectedRoute(DashboardComponent, {
  requiredService: 'access_point_provider',
  requiredLevel: 'read'
});

// Use like any other component
<ProtectedDashboard />`}
            </pre>
          </div>
        </div>
      </div>

      {/* Navigation and Conditional Features */}
      <div className="bg-white rounded-lg shadow p-6">
        <h2 className="text-xl font-semibold mb-4">Navigation and Conditional Features</h2>
        
        <div className="space-y-4">
          <div>
            <h3 className="font-medium text-gray-700 mb-2">Conditional Navigation Items</h3>
            <pre className="bg-gray-100 p-4 rounded text-sm overflow-x-auto">
{`import { ServiceGuard } from '@/components/guards/ServiceGuard';

const Navigation = () => (
  <nav>
    <ServiceGuard service="access_point_provider">
      <NavItem href="/dashboard">Dashboard</NavItem>
    </ServiceGuard>
    
    <ServiceGuard service="system_integration">
      <NavItem href="/integrations">Integrations</NavItem>
    </ServiceGuard>
    
    <ServiceGuard service="organization_management" level="admin">
      <NavItem href="/admin">Admin</NavItem>
    </ServiceGuard>
  </nav>
);`}
            </pre>
          </div>

          <div>
            <h3 className="font-medium text-gray-700 mb-2">Feature Flags</h3>
            <pre className="bg-gray-100 p-4 rounded text-sm overflow-x-auto">
{`import { useServicePermissions } from '@/hooks/useServicePermissions';

const FeatureComponent = () => {
  const permissions = useServicePermissions();
  
  return (
    <div>
      {permissions.canUseBetaFeatures() && (
        <BetaFeatureSection />
      )}
      
      {permissions.hasEnterpriseFeatures() && (
        <EnterpriseFeatureSection />
      )}
      
      {permissions.hasPremiumFeatures() && (
        <PremiumFeatureSection />
      )}
    </div>
  );
};`}
            </pre>
          </div>
        </div>
      </div>

      {/* Error Handling */}
      <div className="bg-white rounded-lg shadow p-6">
        <h2 className="text-xl font-semibold mb-4">Error Handling and Fallbacks</h2>
        
        <div className="space-y-4">
          <div>
            <h3 className="font-medium text-gray-700 mb-2">Custom Error Messages</h3>
            <pre className="bg-gray-100 p-4 rounded text-sm overflow-x-auto">
{`<ServiceGuard 
  service="access_point_provider" 
  level="write"
  message="You need APP write access to generate IRNs"
  showUpgrade={true}
>
  <IRNGenerationForm />
</ServiceGuard>`}
            </pre>
          </div>

          <div>
            <h3 className="font-medium text-gray-700 mb-2">Redirect on Access Denied</h3>
            <pre className="bg-gray-100 p-4 rounded text-sm overflow-x-auto">
{`<ProtectedRoute 
  requiredService="access_point_provider"
  requiredLevel="write"
  redirectTo="/pricing"
>
  <IRNGenerationPage />
</ProtectedRoute>`}
            </pre>
          </div>
        </div>
      </div>

      {/* Best Practices */}
      <div className="bg-white rounded-lg shadow p-6">
        <h2 className="text-xl font-semibold mb-4">Best Practices</h2>
        
        <div className="space-y-4">
          <div>
            <h3 className="font-medium text-gray-700 mb-2">Do's</h3>
            <ul className="text-sm space-y-1 list-disc list-inside text-gray-600">
              <li>Use specialized guards (AppGuard, SIGuard) for better readability</li>
              <li>Provide meaningful fallback messages</li>
              <li>Use PermissionCheck for conditional rendering</li>
              <li>Implement proper loading states</li>
              <li>Use HOC pattern for page-level protection</li>
            </ul>
          </div>

          <div>
            <h3 className="font-medium text-gray-700 mb-2">Don'ts</h3>
            <ul className="text-sm space-y-1 list-disc list-inside text-gray-600">
              <li>Don't nest guards unnecessarily</li>
              <li>Don't show features users can't access without guards</li>
              <li>Don't rely only on client-side protection</li>
              <li>Don't forget to handle loading states</li>
              <li>Don't use generic error messages</li>
            </ul>
          </div>
        </div>
      </div>
    </div>
  );
};

export default GuardUsageExamples;