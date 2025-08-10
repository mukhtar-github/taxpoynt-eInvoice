/**
 * TaxPoynt Business Interface - Strategic Frontend Architecture
 * ============================================================
 * Comprehensive business interface with role-aware navigation and strategic user flows.
 * 
 * User Flows Implemented:
 * 1. Home/Dashboard → Service Management → Package Selection → Billing (Full Page)
 * 2. Registration → Consent Integration → Service Selection
 * 3. Admin → Grant Dashboard → KPI Monitoring (Admin-only)
 * 
 * Architecture Features:
 * - Role-based visibility (SI, APP, Hybrid, Admin)
 * - Consent-integrated registration (NDPR compliant)
 * - Full-page billing flows (professional financial operations)
 * - Admin-only grant tracking and KPI dashboards
 * - Strategic information disclosure (simple UI, detailed T&C)
 * 
 * Steve Jobs Principles Applied:
 * - Simplicity as the ultimate sophistication
 * - Hide technical complexity behind elegant interfaces
 * - Every interaction should feel magical and delightful
 * - Perfection in details matters
 */

// Core Business Interface Components
export { LandingPage } from './LandingPage';
export { HomePage } from './HomePage';
export { PackageSelector } from './service_packages/PackageSelector';
export { BillingPage } from './billing_management/BillingPage';
export { ConsentIntegratedRegistration } from './onboarding_flows/ConsentIntegratedRegistration';

// Admin-Only Components (Internal Use)
export { AdminGrantDashboard } from './grant_dashboard/AdminGrantDashboard';

// Design System Components
export { Button } from '../design_system/components/Button';
export { colors, typography, spacing, roleThemes } from '../design_system/tokens';

// Type Definitions
export interface UserRole {
  type: 'si' | 'app' | 'hybrid' | 'admin';
  permissions: string[];
  packageAccess: string[];
}

export interface ServicePackage {
  id: string;
  name: string;
  description: string;
  price: { monthly: number; annual: number };
  features: string[];
  limits: {
    invoicesPerMonth: number | 'unlimited';
    integrations: number | 'unlimited';
    users: number | 'unlimited';
  };
  popular?: boolean;
  recommended?: boolean;
}

export interface ConsentChoice {
  id: string;
  category: 'financial' | 'operational' | 'marketing' | 'analytics';
  granted: boolean;
  timestamp: string;
  ndprCompliant: boolean;
}

// Strategic Navigation Configuration
export const navigationConfig = {
  si: {
    // System Integrator (Commercial) Navigation
    mainMenu: [
      { path: '/dashboard', label: 'Dashboard', icon: '📊' },
      { path: '/integrations', label: 'Integrations', icon: '🔗' },
      { path: '/invoices', label: 'Invoices', icon: '📄' },
      { path: '/compliance', label: 'Compliance', icon: '✅' },
      { path: '/service-packages', label: 'Service Packages', icon: '📦' },
      { path: '/billing', label: 'Billing & Payments', icon: '💳' },
      { path: '/support', label: 'Support', icon: '🎧' }
    ],
    billing: {
      visible: true,
      packages: ['starter', 'professional', 'enterprise']
    }
  },
  
  app: {
    // Access Point Provider (Grant-funded) Navigation
    mainMenu: [
      { path: '/dashboard', label: 'Dashboard', icon: '📊' },
      { path: '/taxpayers', label: 'Taxpayer Management', icon: '👥' },
      { path: '/compliance', label: 'FIRS Compliance', icon: '🏛️' },
      { path: '/reports', label: 'Grant Reports', icon: '📈' },
      { path: '/support', label: 'Support', icon: '🎧' }
    ],
    billing: {
      visible: false, // APP users don't manage commercial billing
      packages: []
    }
  },
  
  hybrid: {
    // Hybrid (SI + APP) Navigation
    mainMenu: [
      { path: '/dashboard', label: 'Dashboard', icon: '📊' },
      { path: '/integrations', label: 'Integrations', icon: '🔗' },
      { path: '/taxpayers', label: 'Taxpayer Management', icon: '👥' },
      { path: '/invoices', label: 'Invoices', icon: '📄' },
      { path: '/compliance', label: 'Compliance', icon: '✅' },
      { path: '/revenue', label: 'Revenue Analytics', icon: '💰' },
      { path: '/billing', label: 'Premium Services', icon: '👑' },
      { path: '/support', label: 'Support', icon: '🎧' }
    ],
    billing: {
      visible: true,
      packages: ['hybrid'] // Hybrid users automatically get highest tier
    }
  },
  
  admin: {
    // Admin (TaxPoynt Staff) Navigation
    mainMenu: [
      { path: '/admin-dashboard', label: 'Admin Dashboard', icon: '⚙️' },
      { path: '/grant-tracking', label: 'Grant Tracking', icon: '🎯' },
      { path: '/kpi-dashboard', label: 'KPI Monitoring', icon: '📊' },
      { path: '/user-management', label: 'User Management', icon: '👥' },
      { path: '/system-health', label: 'System Health', icon: '💚' },
      { path: '/evidence-vault', label: 'Evidence Vault', icon: '📋' },
      { path: '/firs-reporting', label: 'FIRS Reporting', icon: '🏛️' }
    ],
    billing: {
      visible: true, // Admins can see all billing for management
      packages: ['starter', 'professional', 'enterprise', 'hybrid']
    }
  }
};

// Strategic User Flow Definitions
export const userFlows = {
  // Primary Flow: Package Selection → Billing
  packageToBilling: {
    steps: [
      { component: 'PackageSelector', path: '/service-packages' },
      { component: 'BillingPage', path: '/billing' }
    ],
    roles: ['si', 'hybrid', 'admin']
  },
  
  // Registration Flow: Registration → Consent → Service Selection
  registration: {
    steps: [
      { component: 'ConsentIntegratedRegistration', path: '/register' },
      { component: 'PackageSelector', path: '/service-packages' },
      { component: 'BillingPage', path: '/billing' }
    ],
    roles: ['anonymous'] // Before authentication
  },
  
  // Admin Flow: Grant Tracking → Evidence Management
  adminGrantManagement: {
    steps: [
      { component: 'AdminGrantDashboard', path: '/admin/grant-tracking' }
    ],
    roles: ['admin']
  }
};

// Strategic Component Export Map
export const componentMap = {
  // Public Components (Role-based visibility)
  LandingPage: {
    component: 'LandingPage',
    roles: ['anonymous'],
    description: 'Marketing landing page for unauthenticated visitors'
  },
  
  HomePage: {
    component: 'HomePage',
    roles: ['si', 'app', 'hybrid', 'admin'],
    description: 'Role-aware dashboard for authenticated users'
  },
  
  PackageSelector: {
    component: 'PackageSelector',
    roles: ['si', 'hybrid', 'admin'],
    description: 'Service package selection with role-aware presentation'
  },
  
  BillingPage: {
    component: 'BillingPage',
    roles: ['si', 'hybrid', 'admin'],
    description: 'Full-page billing interface with Nigerian payment methods'
  },
  
  ConsentIntegratedRegistration: {
    component: 'ConsentIntegratedRegistration',
    roles: ['anonymous'],
    description: 'NDPR-compliant registration with integrated consent management'
  },
  
  // Admin-Only Components (Internal Use)
  AdminGrantDashboard: {
    component: 'AdminGrantDashboard',
    roles: ['admin'],
    description: 'Internal grant tracking and FIRS compliance evidence management'
  }
};

// Utility Functions
export const getUserFlowsForRole = (role: UserRole['type']) => {
  return Object.entries(userFlows)
    .filter(([_, flow]) => flow.roles.includes(role))
    .map(([key, flow]) => ({ key, ...flow }));
};

export const getNavigationForRole = (role: UserRole['type']) => {
  return navigationConfig[role] || navigationConfig.si; // Default to SI navigation
};

export const canAccessComponent = (componentName: string, userRole: UserRole['type']) => {
  const component = componentMap[componentName as keyof typeof componentMap];
  return component ? component.roles.includes(userRole) : false;
};

// Strategic Implementation Status
export const implementationStatus = {
  designSystem: {
    status: 'completed',
    components: ['Button', 'Design Tokens', 'Role Themes'],
    description: 'Foundation design system with Steve Jobs principles'
  },
  
  businessInterface: {
    status: 'completed',
    components: ['PackageSelector', 'BillingPage', 'ConsentIntegratedRegistration'],
    description: 'Core business interface with strategic user flows'
  },
  
  adminInterface: {
    status: 'completed',
    components: ['AdminGrantDashboard'],
    description: 'Admin-only grant tracking and KPI monitoring'
  },
  
  nextSteps: [
    'Integrate with existing Next.js frontend structure',
    'Connect to taxpayer_onboarding.py and consent_manager.py APIs',
    'Implement real Nigerian payment processor integrations',
    'Add comprehensive error handling and loading states',
    'Create responsive mobile interfaces',
    'Add comprehensive testing suite'
  ]
};

/**
 * Strategic Architecture Summary
 * =============================
 * 
 * ✅ Completed Components:
 * 1. Design System Foundation - Role-aware tokens and components
 * 2. Package Selector - Strategic service package presentation
 * 3. Billing Page - Full-page professional financial operations
 * 4. Consent Registration - NDPR-compliant onboarding flow
 * 5. Admin Grant Dashboard - Internal compliance tracking
 * 
 * ✅ Strategic Principles Applied:
 * 1. Role-based visibility (SI, APP, Hybrid, Admin)
 * 2. Consent-first registration (integrated, not separate)
 * 3. Full-page billing flows (professional separation)
 * 4. Admin-only compliance tools (not public consumption)
 * 5. Steve Jobs UI/UX principles (simplicity + sophistication)
 * 
 * ✅ User Flow Implementation:
 * 1. Business Users: Home → Service Packages → Billing (Separate Page)
 * 2. New Users: Registration → Consent → Service Selection
 * 3. Hybrid Users: Automatic highest tier, simplified billing
 * 4. Admins: Grant tracking, KPI monitoring, evidence management
 * 
 * 🎯 Ready for Integration with Existing TaxPoynt Architecture
 */