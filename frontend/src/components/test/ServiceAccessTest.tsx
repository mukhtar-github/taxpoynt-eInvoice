import React from 'react';
import { useServiceAccess } from '../../contexts/ServiceAccessContext';
import { useServicePermissions } from '../../hooks/useServicePermissions';

/**
 * Test component to verify Service Access Context and Permissions Hook
 * This component should be used for development and testing purposes only
 */
export const ServiceAccessTest: React.FC = () => {
  const { userServices, isLoading, error } = useServiceAccess();
  const permissions = useServicePermissions();

  if (isLoading) {
    return <div>Loading service access...</div>;
  }

  if (error) {
    return <div>Error: {error}</div>;
  }

  return (
    <div style={{ padding: '20px', fontFamily: 'monospace' }}>
      <h2>Service Access Test</h2>
      
      <div style={{ marginBottom: '20px' }}>
        <h3>User Services ({userServices.length})</h3>
        {userServices.length === 0 ? (
          <p>No services available</p>
        ) : (
          <ul>
            {userServices.map((service, index) => (
              <li key={index}>
                {service.serviceType} - {service.accessLevel}
                {service.expiresAt && (
                  <span> (expires: {new Date(service.expiresAt).toLocaleDateString()})</span>
                )}
              </li>
            ))}
          </ul>
        )}
      </div>

      <div style={{ marginBottom: '20px' }}>
        <h3>Core Service Access</h3>
        <ul>
          <li>Access Point Provider: {permissions.canAccessApp() ? '✅' : '❌'}</li>
          <li>System Integration: {permissions.canAccessSI() ? '✅' : '❌'}</li>
          <li>Nigerian Compliance: {permissions.canAccessCompliance() ? '✅' : '❌'}</li>
          <li>Organization Management: {permissions.canManageOrg() ? '✅' : '❌'}</li>
        </ul>
      </div>

      <div style={{ marginBottom: '20px' }}>
        <h3>Specific Permissions</h3>
        <ul>
          <li>Generate IRN: {permissions.canGenerateIRN() ? '✅' : '❌'}</li>
          <li>Manage Integrations: {permissions.canManageIntegrations() ? '✅' : '❌'}</li>
          <li>View Compliance: {permissions.canViewCompliance() ? '✅' : '❌'}</li>
          <li>Manage Users: {permissions.canManageUsers() ? '✅' : '❌'}</li>
          <li>Manage Certificates: {permissions.canManageCertificates() ? '✅' : '❌'}</li>
        </ul>
      </div>

      <div style={{ marginBottom: '20px' }}>
        <h3>User Type</h3>
        <ul>
          <li>Owner: {permissions.isOwner() ? '✅' : '❌'}</li>
          <li>Admin: {permissions.isAdmin() ? '✅' : '❌'}</li>
          <li>Hybrid User: {permissions.isHybridUser() ? '✅' : '❌'}</li>
          <li>Pure APP User: {permissions.isPureAppUser() ? '✅' : '❌'}</li>
          <li>Pure SI User: {permissions.isPureSIUser() ? '✅' : '❌'}</li>
        </ul>
      </div>

      <div style={{ marginBottom: '20px' }}>
        <h3>Access Levels</h3>
        <ul>
          <li>APP Access: {permissions.getAppAccess() || 'None'}</li>
          <li>SI Access: {permissions.getSIAccess() || 'None'}</li>
          <li>Compliance Access: {permissions.getComplianceAccess() || 'None'}</li>
          <li>Org Access: {permissions.getOrgAccess() || 'None'}</li>
        </ul>
      </div>

      <div style={{ marginBottom: '20px' }}>
        <h3>Navigation</h3>
        <p>Default Route: {permissions.getDefaultRoute()}</p>
        <p>All Services: {permissions.getAllServices().join(', ') || 'None'}</p>
      </div>

      <div style={{ marginBottom: '20px' }}>
        <h3>Feature Flags</h3>
        <ul>
          <li>Beta Features: {permissions.canUseBetaFeatures() ? '✅' : '❌'}</li>
          <li>API Keys: {permissions.canAccessAPIKeys() ? '✅' : '❌'}</li>
          <li>Webhooks: {permissions.canManageWebhooks() ? '✅' : '❌'}</li>
          <li>Enterprise Features: {permissions.hasEnterpriseFeatures() ? '✅' : '❌'}</li>
          <li>Premium Features: {permissions.hasPremiumFeatures() ? '✅' : '❌'}</li>
        </ul>
      </div>

      <div style={{ marginBottom: '20px' }}>
        <h3>Legacy Compatibility</h3>
        <ul>
          <li>FIRS Access: {permissions.canAccessFirs() ? '✅' : '❌'}</li>
          <li>Dashboard Access: {permissions.canAccessDashboard() ? '✅' : '❌'}</li>
        </ul>
      </div>
    </div>
  );
};

export default ServiceAccessTest;