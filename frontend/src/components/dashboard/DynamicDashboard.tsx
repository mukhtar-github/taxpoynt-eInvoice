import React from 'react';
import { useServicePermissions } from '../../hooks/useServicePermissions';
import { PureAppDashboard } from './PureAppDashboard';
import { PureSIDashboard } from './PureSIDashboard';
import { HybridDashboard } from './HybridDashboard';
import { OwnerDashboard } from './OwnerDashboard';
import { BasicDashboard } from './BasicDashboard';

/**
 * Dynamic Dashboard Component
 * 
 * Routes users to the appropriate dashboard based on their service permissions:
 * - Owner: Full access to all services and administrative features
 * - Hybrid: Access to both APP and SI services
 * - Pure APP: Access Point Provider services only (certificates, compliance, transmission)
 * - Pure SI: System Integration services only (ERP, CRM, POS connections)
 * - Basic: Limited access fallback for users with minimal permissions
 */
export const DynamicDashboard: React.FC = () => {
  const permissions = useServicePermissions();

  // Determine dashboard type based on user permissions
  if (permissions.isOwner()) {
    return <OwnerDashboard />;
  }

  if (permissions.isHybridUser()) {
    return <HybridDashboard />;
  }

  if (permissions.isPureAppUser()) {
    return <PureAppDashboard />;
  }

  if (permissions.isPureSIUser()) {
    return <PureSIDashboard />;
  }

  // Fallback for users with limited access
  return <BasicDashboard />;
};

export default DynamicDashboard;