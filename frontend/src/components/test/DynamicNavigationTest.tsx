import React, { useState } from 'react';
import { DynamicNavigation } from '../navigation/DynamicNavigation';
import { PublicNavigation } from '../navigation/PublicNavigation';
import { useNavigation, useBreadcrumbs, useNavigationRecommendations } from '../../hooks/useNavigation';
import { useServicePermissions } from '../../hooks/useServicePermissions';
import { navigationCategories } from '../../config/navigationConfig';
import { Button } from '../ui/Button';
import { Badge } from '../ui/Badge';
import { 
  Eye, Settings, Zap, Users, Shield, Database, 
  ChevronRight, Home, Search, Filter, BarChart3 
} from 'lucide-react';

/**
 * Comprehensive test component for the Dynamic Navigation System
 * Demonstrates all navigation variants and features
 */
export const DynamicNavigationTest: React.FC = () => {
  const [selectedVariant, setSelectedVariant] = useState<'sidebar' | 'horizontal' | 'dropdown'>('sidebar');
  const [showCategories, setShowCategories] = useState(true);
  const [showDescriptions, setShowDescriptions] = useState(false);
  const [showBadges, setShowBadges] = useState(true);
  const [searchQuery, setSearchQuery] = useState('');

  const navigation = useNavigation();
  const { breadcrumbs } = useBreadcrumbs();
  const { recommendations } = useNavigationRecommendations();
  const permissions = useServicePermissions();

  const variants = [
    { value: 'sidebar' as const, label: 'Sidebar', icon: Eye },
    { value: 'horizontal' as const, label: 'Horizontal', icon: Settings },
    { value: 'dropdown' as const, label: 'Dropdown', icon: Zap }
  ];

  return (
    <div className="max-w-7xl mx-auto p-6 space-y-8">
      <div className="text-center">
        <h1 className="text-3xl font-bold text-gray-900 mb-4">Dynamic Navigation System Test</h1>
        <p className="text-gray-600 max-w-2xl mx-auto">
          Comprehensive test environment for the service-aware navigation system with permission filtering,
          public/authenticated navigation separation, and responsive design patterns.
        </p>
      </div>

      {/* Navigation State Debug */}
      <div className="bg-gray-50 rounded-lg p-6">
        <h2 className="text-xl font-semibold mb-4 flex items-center">
          <BarChart3 className="mr-2 h-5 w-5" />
          Navigation State
        </h2>
        
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 text-sm">
          <div>
            <div className="font-medium text-gray-700">Current Path</div>
            <div className="text-gray-900 font-mono">{navigation.currentPath}</div>
          </div>
          
          <div>
            <div className="font-medium text-gray-700">Current Item</div>
            <div className="text-gray-900">{navigation.currentItem?.label || 'None'}</div>
          </div>
          
          <div>
            <div className="font-medium text-gray-700">Visible Items</div>
            <div className="text-gray-900">{navigation.visibleItems.length}</div>
          </div>
          
          <div>
            <div className="font-medium text-gray-700">Available Services</div>
            <div className="text-gray-900">{navigation.getAvailableServices().length}</div>
          </div>
        </div>

        {/* Breadcrumbs */}
        {breadcrumbs.length > 0 && (
          <div className="mt-4">
            <div className="font-medium text-gray-700 mb-2">Breadcrumbs</div>
            <nav className="flex items-center space-x-2 text-sm">
              <Home className="h-4 w-4 text-gray-500" />
              {breadcrumbs.map((crumb, index) => (
                <React.Fragment key={crumb.id}>
                  <ChevronRight className="h-4 w-4 text-gray-400" />
                  <span className="text-gray-900">{crumb.label}</span>
                </React.Fragment>
              ))}
            </nav>
          </div>
        )}

        {/* Recommendations */}
        {recommendations.length > 0 && (
          <div className="mt-4">
            <div className="font-medium text-gray-700 mb-2">Recommended Actions</div>
            <div className="flex flex-wrap gap-2">
              {recommendations.map((rec) => (
                <Badge key={rec.id} variant="secondary" className="flex items-center">
                  <rec.icon className="mr-1 h-3 w-3" />
                  {rec.label}
                </Badge>
              ))}
            </div>
          </div>
        )}
      </div>

      {/* User Permissions Overview */}
      <div className="bg-white rounded-lg shadow p-6">
        <h2 className="text-xl font-semibold mb-4 flex items-center">
          <Shield className="mr-2 h-5 w-5" />
          User Permissions
        </h2>
        
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          {/* Service Access */}
          <div className="space-y-2">
            <h3 className="font-medium text-gray-700">Service Access</h3>
            <div className="space-y-1 text-sm">
              <div>APP: {permissions.canAccessApp() ? '✅' : '❌'} ({permissions.getAppAccess() || 'None'})</div>
              <div>SI: {permissions.canAccessSI() ? '✅' : '❌'} ({permissions.getSIAccess() || 'None'})</div>
              <div>Compliance: {permissions.canAccessCompliance() ? '✅' : '❌'} ({permissions.getComplianceAccess() || 'None'})</div>
              <div>Organization: {permissions.canManageOrg() ? '✅' : '❌'} ({permissions.getOrgAccess() || 'None'})</div>
            </div>
          </div>

          {/* User Type */}
          <div className="space-y-2">
            <h3 className="font-medium text-gray-700">User Type</h3>
            <div className="space-y-1 text-sm">
              <div>Owner: {permissions.isOwner() ? '✅' : '❌'}</div>
              <div>Admin: {permissions.isAdmin() ? '✅' : '❌'}</div>
              <div>Hybrid: {permissions.isHybridUser() ? '✅' : '❌'}</div>
              <div>Pure APP: {permissions.isPureAppUser() ? '✅' : '❌'}</div>
              <div>Pure SI: {permissions.isPureSIUser() ? '✅' : '❌'}</div>
            </div>
          </div>

          {/* Specific Permissions */}
          <div className="space-y-2">
            <h3 className="font-medium text-gray-700">Key Permissions</h3>
            <div className="space-y-1 text-sm">
              <div>Generate IRN: {permissions.canGenerateIRN() ? '✅' : '❌'}</div>
              <div>Manage Integrations: {permissions.canManageIntegrations() ? '✅' : '❌'}</div>
              <div>Manage Users: {permissions.canManageUsers() ? '✅' : '❌'}</div>
              <div>Manage Certificates: {permissions.canManageCertificates() ? '✅' : '❌'}</div>
            </div>
          </div>

          {/* Feature Flags */}
          <div className="space-y-2">
            <h3 className="font-medium text-gray-700">Feature Flags</h3>
            <div className="space-y-1 text-sm">
              <div>Beta Features: {permissions.canUseBetaFeatures() ? '✅' : '❌'}</div>
              <div>Premium Features: {permissions.hasPremiumFeatures() ? '✅' : '❌'}</div>
              <div>Enterprise Features: {permissions.hasEnterpriseFeatures() ? '✅' : '❌'}</div>
              <div>API Keys: {permissions.canAccessAPIKeys() ? '✅' : '❌'}</div>
            </div>
          </div>
        </div>
      </div>

      {/* Public Navigation Demo */}
      <div className="bg-white rounded-lg shadow overflow-hidden">
        <div className="px-6 py-4 border-b border-gray-200">
          <h2 className="text-xl font-semibold flex items-center">
            <Users className="mr-2 h-5 w-5" />
            Public Navigation (Marketing Pages)
          </h2>
          <p className="text-gray-600 text-sm mt-1">
            Clean navigation for unauthenticated users on landing pages
          </p>
        </div>
        <div className="border border-gray-200">
          <PublicNavigation />
        </div>
      </div>

      {/* Dynamic Navigation Controls */}
      <div className="bg-white rounded-lg shadow p-6">
        <h2 className="text-xl font-semibold mb-4 flex items-center">
          <Settings className="mr-2 h-5 w-5" />
          Dynamic Navigation Controls
        </h2>
        
        <div className="space-y-4">
          {/* Variant Selection */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">Navigation Variant</label>
            <div className="flex flex-wrap gap-2">
              {variants.map(({ value, label, icon: Icon }) => (
                <Button
                  key={value}
                  variant={selectedVariant === value ? "default" : "outline"}
                  size="sm"
                  onClick={() => setSelectedVariant(value)}
                  className="flex items-center"
                >
                  <Icon className="mr-2 h-4 w-4" />
                  {label}
                </Button>
              ))}
            </div>
          </div>

          {/* Display Options */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <label className="flex items-center">
              <input
                type="checkbox"
                checked={showCategories}
                onChange={(e) => setShowCategories(e.target.checked)}
                className="mr-2"
              />
              Show Categories
            </label>
            
            <label className="flex items-center">
              <input
                type="checkbox"
                checked={showDescriptions}
                onChange={(e) => setShowDescriptions(e.target.checked)}
                className="mr-2"
              />
              Show Descriptions
            </label>
            
            <label className="flex items-center">
              <input
                type="checkbox"
                checked={showBadges}
                onChange={(e) => setShowBadges(e.target.checked)}
                className="mr-2"
              />
              Show Badges
            </label>
          </div>

          {/* Search */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">Search Navigation</label>
            <div className="relative">
              <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-gray-400" />
              <input
                type="text"
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                placeholder="Search navigation items..."
                className="pl-10 pr-4 py-2 border border-gray-300 rounded-md w-full"
              />
            </div>
          </div>
        </div>
      </div>

      {/* Dynamic Navigation Demo */}
      <div className="bg-white rounded-lg shadow overflow-hidden">
        <div className="px-6 py-4 border-b border-gray-200">
          <h2 className="text-xl font-semibold flex items-center">
            <Database className="mr-2 h-5 w-5" />
            Dynamic Navigation ({selectedVariant})
          </h2>
          <p className="text-gray-600 text-sm mt-1">
            Service-aware navigation with permission filtering and responsive design
          </p>
        </div>
        
        <div className="p-6">
          <DynamicNavigation
            variant={selectedVariant}
            showCategories={showCategories}
            showDescriptions={showDescriptions}
            showBadges={showBadges}
            className={selectedVariant === 'horizontal' ? 'w-full overflow-x-auto' : 'max-w-md'}
          />
        </div>
      </div>

      {/* Categories Overview */}
      <div className="bg-white rounded-lg shadow p-6">
        <h2 className="text-xl font-semibold mb-4 flex items-center">
          <Filter className="mr-2 h-5 w-5" />
          Navigation Categories
        </h2>
        
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {navigationCategories.map((category) => {
            const categoryItems = navigation.itemsByCategory[category.id] || [];
            const CategoryIcon = category.icon;
            
            return (
              <div key={category.id} className="border border-gray-200 rounded-lg p-4">
                <div className="flex items-center mb-2">
                  <CategoryIcon className="mr-2 h-5 w-5 text-gray-600" />
                  <h3 className="font-medium text-gray-900">{category.label}</h3>
                </div>
                <p className="text-sm text-gray-600 mb-2">{category.description}</p>
                <div className="text-sm">
                  <span className="font-medium">Items:</span> {categoryItems.length}
                </div>
                {categoryItems.length > 0 && (
                  <div className="mt-2 flex flex-wrap gap-1">
                    {categoryItems.slice(0, 3).map((item) => (
                      <Badge key={item.id} variant="outline" className="text-xs">
                        {item.label}
                      </Badge>
                    ))}
                    {categoryItems.length > 3 && (
                      <Badge variant="outline" className="text-xs">
                        +{categoryItems.length - 3} more
                      </Badge>
                    )}
                  </div>
                )}
              </div>
            );
          })}
        </div>
      </div>

      {/* Available Services */}
      <div className="bg-white rounded-lg shadow p-6">
        <h2 className="text-xl font-semibold mb-4">Available Services</h2>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {navigation.getAvailableServices().map((service) => (
            <div key={service} className="flex items-center p-3 border border-gray-200 rounded-lg">
              <div className="w-3 h-3 bg-green-400 rounded-full mr-3"></div>
              <span className="font-medium">{service.replace('_', ' ').toUpperCase()}</span>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};

export default DynamicNavigationTest;