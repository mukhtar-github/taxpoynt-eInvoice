# Frontend Service-Based UI Implementation Plan

**Document**: Frontend Implementation Strategy for Service-Based Permissions  
**Date**: June 26, 2025  
**Context**: Next.js Frontend Integration with Service-Based Backend  
**Status**: Implementation Plan - Ready for Execution  

---

## 🎯 **Implementation Overview**

Transform the TaxPoynt frontend to dynamically display UI components based on user's service access permissions, creating personalized experiences for different user types.

### **Key Objectives**
1. **Dynamic Navigation**: Show only accessible services
2. **Role-Based Dashboards**: Customized UI per user type
3. **Service-Specific Onboarding**: Guided setup flows
4. **Permission-Aware Components**: Hide/show features based on access
5. **Business Package Integration**: Support flexible pricing models

---

## 📋 **Phase 1: Core Infrastructure (Week 1)**

### **1.1 Service Access Context & Hooks**

#### **Create Service Context**
```typescript
// frontend/src/contexts/ServiceAccessContext.tsx
import React, { createContext, useContext, useEffect, useState } from 'react';
import { User } from '@/types/auth';

interface ServiceAccess {
  serviceType: string;
  accessLevel: string;
  expiresAt?: string;
}

interface ServiceContextType {
  userServices: ServiceAccess[];
  hasAccess: (service: string, level?: string) => boolean;
  getAccessLevel: (service: string) => string | null;
  isLoading: boolean;
  refreshServices: () => Promise<void>;
}

const ServiceAccessContext = createContext<ServiceContextType | undefined>(undefined);

export const ServiceAccessProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [userServices, setUserServices] = useState<ServiceAccess[]>([]);
  const [isLoading, setIsLoading] = useState(true);

  const hasAccess = (service: string, level: string = 'read'): boolean => {
    const accessLevels = { read: 1, write: 2, admin: 3, owner: 4 };
    
    const userAccess = userServices.find(s => s.serviceType === service);
    if (!userAccess) return false;
    
    // Check expiration
    if (userAccess.expiresAt && new Date(userAccess.expiresAt) < new Date()) {
      return false;
    }
    
    return accessLevels[userAccess.accessLevel] >= accessLevels[level];
  };

  const getAccessLevel = (service: string): string | null => {
    const userAccess = userServices.find(s => s.serviceType === service);
    return userAccess?.accessLevel || null;
  };

  const refreshServices = async () => {
    try {
      setIsLoading(true);
      const response = await fetch('/api/v1/service-access/services/available', {
        headers: { Authorization: `Bearer ${getToken()}` }
      });
      const services = await response.json();
      setUserServices(services.map(s => ({
        serviceType: s.service_type,
        accessLevel: s.access_level,
        expiresAt: s.expires_at
      })));
    } catch (error) {
      console.error('Failed to fetch user services:', error);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    refreshServices();
  }, []);

  return (
    <ServiceAccessContext.Provider value={{
      userServices,
      hasAccess,
      getAccessLevel,
      isLoading,
      refreshServices
    }}>
      {children}
    </ServiceAccessContext.Provider>
  );
};

export const useServiceAccess = () => {
  const context = useContext(ServiceAccessContext);
  if (!context) {
    throw new Error('useServiceAccess must be used within ServiceAccessProvider');
  }
  return context;
};
```

#### **Service Permission Hook**
```typescript
// frontend/src/hooks/useServicePermissions.ts
import { useServiceAccess } from '@/contexts/ServiceAccessContext';

export const useServicePermissions = () => {
  const { hasAccess, getAccessLevel } = useServiceAccess();

  return {
    // Service access checkers
    canAccessApp: (level = 'read') => hasAccess('access_point_provider', level),
    canAccessSI: (level = 'read') => hasAccess('system_integration', level),
    canAccessCompliance: (level = 'read') => hasAccess('nigerian_compliance', level),
    canManageOrg: (level = 'read') => hasAccess('organization_management', level),
    
    // Specific permission checks
    canGenerateIRN: () => hasAccess('access_point_provider', 'write'),
    canManageIntegrations: () => hasAccess('system_integration', 'write'),
    canViewCompliance: () => hasAccess('nigerian_compliance', 'read'),
    canManageUsers: () => hasAccess('organization_management', 'admin'),
    
    // Access level getters
    getAppAccess: () => getAccessLevel('access_point_provider'),
    getSIAccess: () => getAccessLevel('system_integration'),
    getComplianceAccess: () => getAccessLevel('nigerian_compliance'),
    getOrgAccess: () => getAccessLevel('organization_management'),
    
    // User type identification
    isOwner: () => ['access_point_provider', 'system_integration', 'nigerian_compliance', 'organization_management']
      .some(service => getAccessLevel(service) === 'owner'),
    isHybridUser: () => hasAccess('access_point_provider') && hasAccess('system_integration'),
    isPureAppUser: () => hasAccess('access_point_provider') && !hasAccess('system_integration'),
    isPureSIUser: () => hasAccess('system_integration') && !hasAccess('access_point_provider')
  };
};
```

### **1.2 Protected Route Components**

#### **Service Guard Component**
```typescript
// frontend/src/components/guards/ServiceGuard.tsx
import React from 'react';
import { useServicePermissions } from '@/hooks/useServicePermissions';
import { AccessDenied } from '@/components/ui/AccessDenied';

interface ServiceGuardProps {
  service: string;
  level?: string;
  children: React.ReactNode;
  fallback?: React.ReactNode;
}

export const ServiceGuard: React.FC<ServiceGuardProps> = ({
  service,
  level = 'read',
  children,
  fallback
}) => {
  const { hasAccess } = useServiceAccess();

  if (!hasAccess(service, level)) {
    return fallback || <AccessDenied service={service} requiredLevel={level} />;
  }

  return <>{children}</>;
};

// Usage examples:
// <ServiceGuard service="access_point_provider" level="write">
//   <IRNGenerationButton />
// </ServiceGuard>
```

#### **Route Protection**
```typescript
// frontend/src/components/guards/ProtectedRoute.tsx
import { useRouter } from 'next/router';
import { useEffect } from 'react';
import { useServicePermissions } from '@/hooks/useServicePermissions';

interface ProtectedRouteProps {
  requiredService: string;
  requiredLevel?: string;
  children: React.ReactNode;
}

export const ProtectedRoute: React.FC<ProtectedRouteProps> = ({
  requiredService,
  requiredLevel = 'read',
  children
}) => {
  const router = useRouter();
  const { hasAccess } = useServiceAccess();

  useEffect(() => {
    if (!hasAccess(requiredService, requiredLevel)) {
      router.push('/unauthorized');
    }
  }, [hasAccess, requiredService, requiredLevel, router]);

  if (!hasAccess(requiredService, requiredLevel)) {
    return <div>Checking permissions...</div>;
  }

  return <>{children}</>;
};
```

### **1.3 Dynamic Navigation System**

#### **Service-Aware Navigation**
```typescript
// frontend/src/components/navigation/DynamicNavigation.tsx
import React from 'react';
import Link from 'next/link';
import { useServicePermissions } from '@/hooks/useServicePermissions';

interface NavItem {
  label: string;
  href: string;
  icon: string;
  service: string;
  level?: string;
  description?: string;
}

const navigationItems: NavItem[] = [
  {
    label: 'Dashboard',
    href: '/dashboard',
    icon: '📊',
    service: 'any', // Everyone sees dashboard
    description: 'Overview of your services'
  },
  {
    label: 'e-Invoicing',
    href: '/invoices',
    icon: '📄',
    service: 'access_point_provider',
    level: 'read',
    description: 'FIRS-compliant electronic invoicing'
  },
  {
    label: 'Generate IRN',
    href: '/irn/generate',
    icon: '✨',
    service: 'access_point_provider',
    level: 'write',
    description: 'Create new invoice reference numbers'
  },
  {
    label: 'Integrations',
    href: '/integrations',
    icon: '🔗',
    service: 'system_integration',
    level: 'read',
    description: 'ERP and CRM connections'
  },
  {
    label: 'Integration Setup',
    href: '/integrations/setup',
    icon: '⚙️',
    service: 'system_integration',
    level: 'write',
    description: 'Configure new integrations'
  },
  {
    label: 'Compliance',
    href: '/compliance',
    icon: '🏛️',
    service: 'nigerian_compliance',
    level: 'read',
    description: 'Nigerian regulatory compliance'
  },
  {
    label: 'User Management',
    href: '/admin/users',
    icon: '👥',
    service: 'organization_management',
    level: 'admin',
    description: 'Manage organization users'
  },
  {
    label: 'Platform Admin',
    href: '/admin/platform',
    icon: '🔧',
    service: 'organization_management',
    level: 'owner',
    description: 'TaxPoynt platform administration'
  }
];

export const DynamicNavigation: React.FC = () => {
  const { hasAccess } = useServiceAccess();
  const permissions = useServicePermissions();

  const visibleItems = navigationItems.filter(item => {
    if (item.service === 'any') return true;
    return hasAccess(item.service, item.level || 'read');
  });

  return (
    <nav className="space-y-2">
      {visibleItems.map((item) => (
        <Link
          key={item.href}
          href={item.href}
          className="flex items-center space-x-3 px-4 py-2 rounded-lg hover:bg-gray-100 transition-colors"
        >
          <span className="text-xl">{item.icon}</span>
          <div>
            <div className="font-medium text-gray-900">{item.label}</div>
            {item.description && (
              <div className="text-sm text-gray-500">{item.description}</div>
            )}
          </div>
        </Link>
      ))}
    </nav>
  );
};
```

---

## 📊 **Phase 2: Role-Based Dashboards (Week 2)**

### **2.1 Dashboard Router**

#### **Dynamic Dashboard Component**
```typescript
// frontend/src/components/dashboard/DynamicDashboard.tsx
import React from 'react';
import { useServicePermissions } from '@/hooks/useServicePermissions';
import { PureAppDashboard } from './PureAppDashboard';
import { PureSIDashboard } from './PureSIDashboard';
import { HybridDashboard } from './HybridDashboard';
import { OwnerDashboard } from './OwnerDashboard';

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
```

### **2.2 Specialized Dashboard Components**

#### **Pure APP User Dashboard**
```typescript
// frontend/src/components/dashboard/PureAppDashboard.tsx
import React from 'react';
import { InvoiceStats } from './widgets/InvoiceStats';
import { RecentIRNs } from './widgets/RecentIRNs';
import { FIRSCompliance } from './widgets/FIRSCompliance';
import { QuickActions } from './widgets/QuickActions';

export const PureAppDashboard: React.FC = () => {
  const quickActions = [
    { label: 'Generate IRN', href: '/irn/generate', icon: '✨' },
    { label: 'View Invoices', href: '/invoices', icon: '📄' },
    { label: 'FIRS Status', href: '/firs/status', icon: '🏛️' },
    { label: 'Compliance Check', href: '/compliance', icon: '✅' }
  ];

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <h1 className="text-2xl font-bold text-gray-900">e-Invoicing Dashboard</h1>
        <div className="text-sm text-gray-500">
          Access Point Provider Services
        </div>
      </div>

      <QuickActions actions={quickActions} />
      
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <InvoiceStats />
        <FIRSCompliance />
      </div>
      
      <RecentIRNs limit={10} />
      
      <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
        <h3 className="font-medium text-blue-900">Need More Features?</h3>
        <p className="text-blue-700 mt-1">
          Upgrade to Enterprise Package for ERP integration and advanced features.
        </p>
        <button className="mt-2 px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700">
          View Upgrade Options
        </button>
      </div>
    </div>
  );
};
```

#### **Hybrid User Dashboard**
```typescript
// frontend/src/components/dashboard/HybridDashboard.tsx
import React, { useState } from 'react';
import { Tab } from '@headlessui/react';

export const HybridDashboard: React.FC = () => {
  const [selectedTab, setSelectedTab] = useState(0);

  const tabs = [
    { name: 'Overview', icon: '📊' },
    { name: 'e-Invoicing', icon: '📄' },
    { name: 'Integrations', icon: '🔗' },
    { name: 'Compliance', icon: '🏛️' }
  ];

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <h1 className="text-2xl font-bold text-gray-900">Enterprise Dashboard</h1>
        <div className="text-sm text-gray-500">
          Full Service Access
        </div>
      </div>

      <Tab.Group selectedIndex={selectedTab} onChange={setSelectedTab}>
        <Tab.List className="flex space-x-1 rounded-xl bg-blue-900/20 p-1">
          {tabs.map((tab, index) => (
            <Tab
              key={tab.name}
              className={({ selected }) =>
                `w-full rounded-lg py-2.5 text-sm font-medium leading-5 text-blue-700
                ${selected 
                  ? 'bg-white shadow' 
                  : 'text-blue-100 hover:bg-white/[0.12] hover:text-white'
                }`
              }
            >
              <span className="mr-2">{tab.icon}</span>
              {tab.name}
            </Tab>
          ))}
        </Tab.List>

        <Tab.Panels>
          <Tab.Panel><HybridOverviewPanel /></Tab.Panel>
          <Tab.Panel><AppServicePanel /></Tab.Panel>
          <Tab.Panel><IntegrationPanel /></Tab.Panel>
          <Tab.Panel><CompliancePanel /></Tab.Panel>
        </Tab.Panels>
      </Tab.Group>
    </div>
  );
};
```

#### **Owner Dashboard**
```typescript
// frontend/src/components/dashboard/OwnerDashboard.tsx
import React from 'react';
import { PlatformMetrics } from './widgets/PlatformMetrics';
import { ComplianceOverview } from './widgets/ComplianceOverview';
import { UserManagement } from './widgets/UserManagement';
import { RevenueStats } from './widgets/RevenueStats';

export const OwnerDashboard: React.FC = () => {
  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <h1 className="text-2xl font-bold text-gray-900">TaxPoynt Platform Overview</h1>
        <div className="text-sm text-gray-500">
          Executive Dashboard
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">
        <PlatformMetrics />
      </div>
      
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <ComplianceOverview />
        <RevenueStats />
      </div>
      
      <UserManagement />
    </div>
  );
};
```

---

## 🎨 **Phase 3: Service-Specific UI Components (Week 3)**

### **3.1 Conditional Feature Display**

#### **Feature Flag Component**
```typescript
// frontend/src/components/ui/FeatureFlag.tsx
import React from 'react';
import { useServicePermissions } from '@/hooks/useServicePermissions';

interface FeatureFlagProps {
  feature: string;
  level?: string;
  children: React.ReactNode;
  fallback?: React.ReactNode;
  showUpgrade?: boolean;
}

export const FeatureFlag: React.FC<FeatureFlagProps> = ({
  feature,
  level = 'read',
  children,
  fallback,
  showUpgrade = false
}) => {
  const { hasAccess } = useServiceAccess();

  if (hasAccess(feature, level)) {
    return <>{children}</>;
  }

  if (showUpgrade) {
    return (
      <div className="bg-gray-50 border border-gray-200 rounded-lg p-4">
        <div className="text-sm text-gray-600">
          This feature requires {feature.replace('_', ' ')} access.
        </div>
        <button className="mt-2 text-blue-600 hover:text-blue-700 text-sm font-medium">
          Upgrade Package →
        </button>
      </div>
    );
  }

  return fallback || null;
};
```

#### **Service Package Badge**
```typescript
// frontend/src/components/ui/ServicePackageBadge.tsx
import React from 'react';
import { useServicePermissions } from '@/hooks/useServicePermissions';

export const ServicePackageBadge: React.FC = () => {
  const permissions = useServicePermissions();

  const getPackageInfo = () => {
    if (permissions.isOwner()) {
      return { name: 'Platform Owner', color: 'bg-purple-100 text-purple-800' };
    }
    if (permissions.isHybridUser()) {
      return { name: 'Enterprise Package', color: 'bg-blue-100 text-blue-800' };
    }
    if (permissions.isPureAppUser()) {
      return { name: 'Starter Package', color: 'bg-green-100 text-green-800' };
    }
    if (permissions.isPureSIUser()) {
      return { name: 'Integration Package', color: 'bg-orange-100 text-orange-800' };
    }
    return { name: 'Basic Access', color: 'bg-gray-100 text-gray-800' };
  };

  const packageInfo = getPackageInfo();

  return (
    <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${packageInfo.color}`}>
      {packageInfo.name}
    </span>
  );
};
```

### **3.2 Service-Specific Onboarding**

#### **Onboarding Flow Router**
```typescript
// frontend/src/components/onboarding/OnboardingFlow.tsx
import React from 'react';
import { useServicePermissions } from '@/hooks/useServicePermissions';
import { AppOnboarding } from './AppOnboarding';
import { SIOnboarding } from './SIOnboarding';
import { HybridOnboarding } from './HybridOnboarding';

export const OnboardingFlow: React.FC = () => {
  const permissions = useServicePermissions();

  if (permissions.isHybridUser()) {
    return <HybridOnboarding />;
  }

  if (permissions.isPureAppUser()) {
    return <AppOnboarding />;
  }

  if (permissions.isPureSIUser()) {
    return <SIOnboarding />;
  }

  return <BasicOnboarding />;
};
```

---

## 📱 **Phase 4: Public Trust Page (Week 4)**

### **4.1 Trust Badges Component**

#### **Compliance Trust Section**
```typescript
// frontend/src/components/public/TrustSection.tsx
import React, { useEffect, useState } from 'react';

interface ComplianceStatus {
  nitdaCertified: boolean;
  ndprCompliant: boolean;
  firsApproved: boolean;
  iso27001: boolean;
}

export const TrustSection: React.FC = () => {
  const [complianceStatus, setComplianceStatus] = useState<ComplianceStatus | null>(null);

  useEffect(() => {
    // Fetch public compliance status
    fetch('/api/v1/public/compliance-status')
      .then(res => res.json())
      .then(setComplianceStatus);
  }, []);

  const trustBadges = [
    {
      title: 'NITDA Certified',
      description: 'Nigerian IT Development Agency Accredited',
      icon: '🏛️',
      verified: complianceStatus?.nitdaCertified,
      color: 'green'
    },
    {
      title: 'NDPR Compliant',
      description: 'Data Protection Regulation Compliant',
      icon: '🔒',
      verified: complianceStatus?.ndprCompliant,
      color: 'blue'
    },
    {
      title: 'FIRS Approved',
      description: 'Federal Inland Revenue Service Certified',
      icon: '💼',
      verified: complianceStatus?.firsApproved,
      color: 'purple'
    },
    {
      title: 'ISO 27001',
      description: 'Information Security Management',
      icon: '🛡️',
      verified: complianceStatus?.iso27001,
      color: 'orange'
    }
  ];

  return (
    <section className="bg-green-50 py-16">
      <div className="max-w-6xl mx-auto px-4">
        <div className="text-center mb-12">
          <h2 className="text-3xl font-bold text-gray-900 mb-4">
            Fully Compliant Nigerian e-Invoicing Platform
          </h2>
          <p className="text-xl text-gray-600">
            Certified and approved by all major Nigerian regulatory bodies
          </p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
          {trustBadges.map((badge) => (
            <TrustBadge key={badge.title} {...badge} />
          ))}
        </div>

        <div className="mt-12 text-center">
          <p className="text-sm text-gray-500">
            Last verified: {new Date().toLocaleDateString()}
          </p>
        </div>
      </div>
    </section>
  );
};

const TrustBadge: React.FC<{
  title: string;
  description: string;
  icon: string;
  verified?: boolean;
  color: string;
}> = ({ title, description, icon, verified, color }) => {
  const colorClasses = {
    green: 'border-green-200 bg-green-50',
    blue: 'border-blue-200 bg-blue-50',
    purple: 'border-purple-200 bg-purple-50',
    orange: 'border-orange-200 bg-orange-50'
  };

  return (
    <div className={`relative p-6 rounded-lg border-2 ${colorClasses[color]} transition-transform hover:scale-105`}>
      {verified && (
        <div className="absolute top-2 right-2">
          <span className="inline-flex items-center justify-center w-6 h-6 bg-green-500 rounded-full">
            <span className="text-white text-xs">✓</span>
          </span>
        </div>
      )}
      
      <div className="text-center">
        <div className="text-4xl mb-3">{icon}</div>
        <h3 className="font-semibold text-gray-900 mb-2">{title}</h3>
        <p className="text-sm text-gray-600">{description}</p>
      </div>
    </div>
  );
};
```

---

## ⚙️ **Phase 5: Service Package Management UI (Week 5)**

### **5.1 Package Upgrade Flow**

#### **Package Comparison Component**
```typescript
// frontend/src/components/billing/PackageComparison.tsx
import React from 'react';
import { useServicePermissions } from '@/hooks/useServicePermissions';

interface ServicePackage {
  id: string;
  name: string;
  price: number;
  description: string;
  features: string[];
  services: {
    access_point_provider?: string;
    system_integration?: string;
    nigerian_compliance?: string;
    organization_management?: string;
  };
  recommended?: boolean;
}

const packages: ServicePackage[] = [
  {
    id: 'starter',
    name: 'Starter Package',
    price: 50,
    description: 'Perfect for small businesses needing basic e-invoicing',
    features: [
      'FIRS-compliant e-invoicing',
      'IRN generation',
      'Basic compliance monitoring',
      'Email support'
    ],
    services: {
      access_point_provider: 'write',
      nigerian_compliance: 'read'
    }
  },
  {
    id: 'integration',
    name: 'Integration Package',
    price: 200,
    description: 'For consultants and system integrators',
    features: [
      'ERP/CRM integration tools',
      'Odoo, SAP, Salesforce connectors',
      'Custom mapping tools',
      'Priority support'
    ],
    services: {
      system_integration: 'admin'
    }
  },
  {
    id: 'enterprise',
    name: 'Enterprise Package',
    price: 400,
    description: 'Complete solution for large businesses',
    features: [
      'Full e-invoicing capabilities',
      'All ERP/CRM integrations',
      'Compliance monitoring',
      'User management',
      'Dedicated support'
    ],
    services: {
      access_point_provider: 'write',
      system_integration: 'write',
      nigerian_compliance: 'read',
      organization_management: 'admin'
    },
    recommended: true
  },
  {
    id: 'compliance_plus',
    name: 'Compliance Plus',
    price: 600,
    description: 'For regulated industries requiring full compliance',
    features: [
      'Everything in Enterprise',
      'Advanced compliance reporting',
      'Audit trail management',
      'Regulatory change notifications',
      'Compliance consulting'
    ],
    services: {
      access_point_provider: 'admin',
      system_integration: 'admin',
      nigerian_compliance: 'admin',
      organization_management: 'admin'
    }
  }
];

export const PackageComparison: React.FC = () => {
  const permissions = useServicePermissions();

  const getCurrentPackage = (): string => {
    if (permissions.isOwner()) return 'owner';
    if (permissions.isHybridUser()) return 'enterprise';
    if (permissions.isPureAppUser()) return 'starter';
    if (permissions.isPureSIUser()) return 'integration';
    return 'none';
  };

  const currentPackage = getCurrentPackage();

  return (
    <div className="py-12">
      <div className="text-center mb-12">
        <h2 className="text-3xl font-bold text-gray-900 mb-4">
          Choose Your Service Package
        </h2>
        <p className="text-xl text-gray-600">
          Flexible pricing for every business need
        </p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-4 gap-8">
        {packages.map((pkg) => (
          <PackageCard
            key={pkg.id}
            package={pkg}
            isCurrent={pkg.id === currentPackage}
            permissions={permissions}
          />
        ))}
      </div>
    </div>
  );
};
```

### **5.2 Service Access Management UI**

#### **User Service Management Component**
```typescript
// frontend/src/components/admin/UserServiceManagement.tsx
import React, { useState, useEffect } from 'react';

interface UserServiceAccess {
  id: string;
  serviceType: string;
  accessLevel: string;
  grantedAt: string;
  expiresAt?: string;
  isActive: boolean;
}

export const UserServiceManagement: React.FC<{ userId: string }> = ({ userId }) => {
  const [userAccess, setUserAccess] = useState<UserServiceAccess[]>([]);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    fetchUserAccess();
  }, [userId]);

  const fetchUserAccess = async () => {
    try {
      const response = await fetch(`/api/v1/service-access/users/${userId}`);
      const data = await response.json();
      setUserAccess(data.access_records);
    } catch (error) {
      console.error('Failed to fetch user access:', error);
    } finally {
      setIsLoading(false);
    }
  };

  const grantAccess = async (serviceType: string, accessLevel: string) => {
    try {
      await fetch(`/api/v1/service-access/users/${userId}/grant`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ service_type: serviceType, access_level: accessLevel })
      });
      fetchUserAccess(); // Refresh
    } catch (error) {
      console.error('Failed to grant access:', error);
    }
  };

  const revokeAccess = async (accessId: string) => {
    try {
      await fetch(`/api/v1/service-access/users/${userId}/access/${accessId}`, {
        method: 'DELETE'
      });
      fetchUserAccess(); // Refresh
    } catch (error) {
      console.error('Failed to revoke access:', error);
    }
  };

  if (isLoading) return <div>Loading...</div>;

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <h3 className="text-lg font-medium">Service Access Management</h3>
        <button
          onClick={() => setShowGrantModal(true)}
          className="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700"
        >
          Grant Access
        </button>
      </div>

      <div className="bg-white shadow overflow-hidden sm:rounded-md">
        <ul className="divide-y divide-gray-200">
          {userAccess.map((access) => (
            <ServiceAccessItem
              key={access.id}
              access={access}
              onRevoke={() => revokeAccess(access.id)}
            />
          ))}
        </ul>
      </div>
    </div>
  );
};
```

---

## 🧪 **Phase 6: Testing Strategy**

### **6.1 Permission Testing**

#### **Service Access Test Utils**
```typescript
// frontend/src/utils/test/serviceAccessMocks.ts
export const createMockUser = (services: Array<{service: string, level: string}>) => ({
  id: '123',
  email: 'test@example.com',
  serviceAccess: services.map(s => ({
    serviceType: s.service,
    accessLevel: s.level,
    isActive: true
  }))
});

export const mockServiceAccessProvider = (userServices: any[]) => ({
  userServices,
  hasAccess: (service: string, level: string = 'read') => {
    // Mock implementation
    return userServices.some(s => s.serviceType === service);
  },
  getAccessLevel: (service: string) => {
    const access = userServices.find(s => s.serviceType === service);
    return access?.accessLevel || null;
  },
  isLoading: false,
  refreshServices: jest.fn()
});

// Test examples
describe('Service Access Components', () => {
  test('shows APP features for APP users', () => {
    const appUser = createMockUser([
      { service: 'access_point_provider', level: 'write' }
    ]);
    
    render(
      <ServiceAccessProvider value={mockServiceAccessProvider(appUser.serviceAccess)}>
        <DynamicNavigation />
      </ServiceAccessProvider>
    );
    
    expect(screen.getByText('e-Invoicing')).toBeInTheDocument();
    expect(screen.queryByText('Integrations')).not.toBeInTheDocument();
  });
});
```

---

## 📋 **Implementation Timeline Summary**

### **Week 1: Core Infrastructure**
- ✅ Service access context and hooks
- ✅ Permission guards and protected routes
- ✅ Dynamic navigation system

### **Week 2: Dashboard Specialization**
- ✅ Role-based dashboard routing
- ✅ User type specific interfaces
- ✅ Dashboard widgets and components

### **Week 3: Feature Integration**
- ✅ Conditional component rendering
- ✅ Service-specific onboarding flows
- ✅ Feature flagging system

### **Week 4: Public Interface**
- ✅ Trust page with compliance badges
- ✅ Public API for compliance status
- ✅ Marketing integration

### **Week 5: Business Integration**
- ✅ Package comparison and upgrade flows
- ✅ Service access management UI
- ✅ Billing integration

### **Week 6: Testing & Optimization**
- ✅ Comprehensive testing strategy
- ✅ Performance optimization
- ✅ User acceptance testing

This implementation plan provides a complete roadmap for the frontend team to build a sophisticated, service-aware user interface that dynamically adapts to user permissions while supporting flexible business models.