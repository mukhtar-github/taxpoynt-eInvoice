import React, { ReactNode } from 'react';
import AppDashboardLayout from '../layouts/AppDashboardLayout';

/**
 * DashboardLayout - Compatibility Wrapper
 * 
 * This component wraps the AppDashboardLayout to maintain backward compatibility
 * with code that was using the previous component/dashboard/DashboardLayout.tsx.
 * 
 * @deprecated Use AppDashboardLayout from '../layouts/DashboardLayout' instead
 */

// Interface for organization
interface Organization {
  id: string;
  name: string;
  tax_id: string;
  logo_url: string | null;
  branding_settings: {
    primary_color: string;
    theme: string;
  };
}

// Interface for the component props
interface DashboardLayoutProps {
  children: ReactNode;
  organization: Organization;
}

/**
 * DashboardLayout (Compatibility Wrapper)
 * 
 * This component wraps AppDashboardLayout to provide backward compatibility
 * while redirecting usage to the consolidated layout system.
 */
const DashboardLayout = ({ children, organization }: DashboardLayoutProps) => {
  return (
    <AppDashboardLayout
      title={`${organization?.name || 'Dashboard'} | Taxpoynt eInvoice`}
      branding={{
        companyName: organization?.name,
        logoUrl: organization?.logo_url || undefined,
        primaryColor: organization?.branding_settings?.primary_color
      }}
    >
      {children}
    </AppDashboardLayout>
  );
};

export default DashboardLayout;