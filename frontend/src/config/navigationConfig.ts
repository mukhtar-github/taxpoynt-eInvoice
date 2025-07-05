import { 
  Home, Shield, Users, Database, BarChart2, FileText, Link as LinkIcon, 
  UserPlus, Send, Key, ShieldCheck, Activity, Settings, Zap, Building,
  BookOpen, CreditCard, Globe, Search, Filter, Download, Upload,
  Calendar, Clock, AlertCircle, CheckCircle, XCircle, Eye, Edit,
  Plus, Minus, ArrowUp, ArrowDown, TrendingUp, TrendingDown,
  DollarSign, PieChart, Target, Award, Star, Heart, Bookmark
} from 'lucide-react';

export interface NavItem {
  id: string;
  label: string;
  href: string;
  icon: React.ElementType;
  service: string;
  level?: string;
  description?: string;
  category?: string;
  badge?: string;
  isNew?: boolean;
  isBeta?: boolean;
  requiredFeature?: string;
  children?: NavItem[];
}

export interface NavigationCategory {
  id: string;
  label: string;
  color: string;
  icon: React.ElementType;
  description: string;
}

// Navigation categories with styling
export const navigationCategories: NavigationCategory[] = [
  {
    id: 'main',
    label: 'Service Hub',
    color: 'yellow',
    icon: Home,
    description: 'Central service selection and overview'
  },
  {
    id: 'si',
    label: 'System Integration',
    color: 'blue',
    icon: Database,
    description: 'ERP, CRM, and POS system integrations'
  },
  {
    id: 'access_point',
    label: 'Access Point Provider',
    color: 'cyan',
    icon: Shield,
    description: 'FIRS-certified e-invoicing services'
  },
  {
    id: 'compliance',
    label: 'Nigerian Compliance',
    color: 'purple',
    icon: BookOpen,
    description: 'Nigerian regulatory and tax compliance'
  },
  {
    id: 'organization',
    label: 'Organization Management',
    color: 'green',
    icon: Building,
    description: 'User, role, and organization administration'
  },
  {
    id: 'shared',
    label: 'Shared Services',
    color: 'gray',
    icon: Activity,
    description: 'Cross-platform analytics and reporting'
  }
];

// Main navigation items with service-based access control
export const navigationItems: NavItem[] = [
  // Main Service Hub
  {
    id: 'dashboard',
    label: 'Service Hub',
    href: '/dashboard',
    icon: Home,
    service: 'any',
    description: 'Overview of your services and quick access',
    category: 'main'
  },

  // System Integration (SI) Services
  {
    id: 'si-dashboard',
    label: 'SI Dashboard',
    href: '/dashboard/si',
    icon: Database,
    service: 'system_integration',
    level: 'read',
    description: 'System integration overview and management',
    category: 'si'
  },
  {
    id: 'company-home',
    label: 'Company Home',
    href: '/dashboard/company-home',
    icon: Building,
    service: 'system_integration',
    level: 'read',
    description: 'Company dashboard and quick actions',
    category: 'si'
  },
  {
    id: 'erp-integrations',
    label: 'ERP Integrations',
    href: '/dashboard/integrations',
    icon: LinkIcon,
    service: 'system_integration',
    level: 'read',
    description: 'Enterprise Resource Planning system connections',
    category: 'si'
  },
  {
    id: 'crm-integrations',
    label: 'CRM Integrations',
    href: '/dashboard/crm',
    icon: UserPlus,
    service: 'system_integration',
    level: 'read',
    description: 'Customer Relationship Management integrations',
    category: 'si'
  },
  {
    id: 'erp-connection',
    label: 'ERP Connection',
    href: '/dashboard/erp-connection',
    icon: LinkIcon,
    service: 'system_integration',
    level: 'write',
    description: 'Configure and manage ERP connections',
    category: 'si'
  },
  {
    id: 'integration-setup',
    label: 'Integration Setup',
    href: '/integrations/setup',
    icon: Settings,
    service: 'system_integration',
    level: 'write',
    description: 'Configure new system integrations',
    category: 'si'
  },

  // Access Point Provider (APP) Services
  {
    id: 'app-dashboard',
    label: 'APP Dashboard',
    href: '/dashboard/access-point',
    icon: Shield,
    service: 'access_point_provider',
    level: 'read',
    description: 'Access Point Provider service overview',
    category: 'access_point'
  },
  {
    id: 'app-services',
    label: 'APP Services',
    href: '/dashboard/app-services',
    icon: Shield,
    service: 'access_point_provider',
    level: 'read',
    description: 'Access Point Provider service management',
    category: 'access_point'
  },
  {
    id: 'e-invoicing',
    label: 'e-Invoicing',
    href: '/invoices',
    icon: FileText,
    service: 'access_point_provider',
    level: 'read',
    description: 'FIRS-compliant electronic invoicing',
    category: 'access_point'
  },
  {
    id: 'generate-irn',
    label: 'Generate IRN',
    href: '/irn/generate',
    icon: Plus,
    service: 'access_point_provider',
    level: 'write',
    description: 'Create new invoice reference numbers',
    category: 'access_point',
    badge: 'Primary'
  },
  {
    id: 'transmission',
    label: 'Transmission',
    href: '/dashboard/transmission',
    icon: Send,
    service: 'access_point_provider',
    level: 'write',
    description: 'Secure data transmission to FIRS',
    category: 'access_point'
  },
  {
    id: 'certificates',
    label: 'Certificates',
    href: '/dashboard/certificates',
    icon: Key,
    service: 'access_point_provider',
    level: 'read',
    description: 'Digital certificates and keys management',
    category: 'access_point'
  },
  {
    id: 'signature-management',
    label: 'Signature Management',
    href: '/app-services/signature-management',
    icon: ShieldCheck,
    service: 'access_point_provider',
    level: 'admin',
    description: 'Digital signature management and validation',
    category: 'access_point'
  },

  // Nigerian Compliance Services
  {
    id: 'compliance-dashboard',
    label: 'Compliance Dashboard',
    href: '/compliance',
    icon: BookOpen,
    service: 'nigerian_compliance',
    level: 'read',
    description: 'Nigerian regulatory compliance overview',
    category: 'compliance'
  },
  {
    id: 'tax-compliance',
    label: 'Tax Compliance',
    href: '/compliance/tax',
    icon: DollarSign,
    service: 'nigerian_compliance',
    level: 'read',
    description: 'Nigerian tax compliance and reporting',
    category: 'compliance'
  },
  {
    id: 'regulatory-reports',
    label: 'Regulatory Reports',
    href: '/compliance/reports',
    icon: FileText,
    service: 'nigerian_compliance',
    level: 'read',
    description: 'Generate regulatory compliance reports',
    category: 'compliance'
  },
  {
    id: 'firs-submissions',
    label: 'FIRS Submissions',
    href: '/dashboard/submission',
    icon: Upload,
    service: 'nigerian_compliance',
    level: 'read',
    description: 'Track FIRS submission status and history',
    category: 'compliance'
  },

  // Organization Management Services
  {
    id: 'organization',
    label: 'Organization',
    href: '/dashboard/organization',
    icon: Building,
    service: 'organization_management',
    level: 'read',
    description: 'Organization settings and information',
    category: 'organization'
  },
  {
    id: 'user-management',
    label: 'User Management',
    href: '/admin/users',
    icon: Users,
    service: 'organization_management',
    level: 'admin',
    description: 'Manage organization users and permissions',
    category: 'organization'
  },
  {
    id: 'role-management',
    label: 'Role Management',
    href: '/admin/roles',
    icon: ShieldCheck,
    service: 'organization_management',
    level: 'admin',
    description: 'Manage user roles and permissions',
    category: 'organization'
  },
  {
    id: 'platform-admin',
    label: 'Platform Admin',
    href: '/admin/platform',
    icon: Settings,
    service: 'organization_management',
    level: 'owner',
    description: 'TaxPoynt platform administration',
    category: 'organization',
    badge: 'Admin'
  },

  // Shared Services
  {
    id: 'metrics-analytics',
    label: 'Metrics & Analytics',
    href: '/dashboard/metrics',
    icon: BarChart2,
    service: 'any',
    description: 'Business intelligence and analytics dashboard',
    category: 'shared'
  },
  {
    id: 'reports',
    label: 'Reports',
    href: '/reports',
    icon: FileText,
    service: 'any',
    description: 'Generate and download business reports',
    category: 'shared'
  },
  {
    id: 'activity-logs',
    label: 'Activity Logs',
    href: '/logs',
    icon: Clock,
    service: 'any',
    description: 'System activity and audit logs',
    category: 'shared'
  },

  // Legacy/Compatibility Items
  {
    id: 'dashboard-legacy',
    label: 'Dashboard',
    href: '/dashboard/legacy',
    icon: BarChart2,
    service: 'dashboard_access',
    level: 'read',
    description: 'Legacy dashboard access',
    category: 'shared'
  },
  {
    id: 'firs-api',
    label: 'FIRS API',
    href: '/firs',
    icon: Globe,
    service: 'firs_api_access',
    level: 'read',
    description: 'Direct FIRS API access and testing',
    category: 'shared'
  }
];

// Feature flags for beta/new features
export const featureFlags = {
  betaFeatures: ['signature-management', 'platform-admin'],
  newFeatures: ['generate-irn', 'transmission'],
  experimentalFeatures: ['firs-api']
};

// Navigation utility functions
export const getNavigationByCategory = (category: string): NavItem[] => {
  return navigationItems.filter(item => item.category === category);
};

export const getNavigationByService = (service: string): NavItem[] => {
  return navigationItems.filter(item => item.service === service || item.service === 'any');
};

export const getCategoryConfig = (categoryId: string): NavigationCategory | undefined => {
  return navigationCategories.find(cat => cat.id === categoryId);
};

export const getNavigationItemById = (id: string): NavItem | undefined => {
  return navigationItems.find(item => item.id === id);
};

export default navigationItems;