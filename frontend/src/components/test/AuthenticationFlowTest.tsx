import React, { useState } from 'react';
import Link from 'next/link';
import { useRouter } from 'next/router';
import { useAuth } from '../../context/AuthContext';
import { useNavigationState, SmartNavigation, NavigationTransition } from '../navigation/NavigationProvider';
import { useServicePermissions } from '../../hooks/useServicePermissions';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '../ui/Card';
import { Button } from '../ui/Button';
import { Badge } from '../ui/Badge';
import { 
  User, LogOut, RefreshCw, Eye, Settings, 
  Shield, Database, Building, Users, CheckCircle,
  ArrowRight, ExternalLink, Play, Pause, RotateCcw
} from 'lucide-react';

/**
 * Comprehensive test component for the authentication flow
 * Tests the complete user journey from public → registration → login → onboarding → dashboard
 */
export const AuthenticationFlowTest: React.FC = () => {
  const [testMode, setTestMode] = useState<'auto' | 'manual'>('manual');
  const [autoTestStep, setAutoTestStep] = useState(0);
  const [testResults, setTestResults] = useState<Record<string, boolean>>({});

  const { user, isAuthenticated, logout } = useAuth();
  const permissions = useServicePermissions();
  const router = useRouter();
  const navigationState = useNavigationState();

  const testSteps = [
    {
      id: 'public-nav',
      title: 'Public Navigation',
      description: 'Test public marketing navigation',
      path: '/',
      expectedNav: 'public'
    },
    {
      id: 'pricing-page',
      title: 'Pricing Page',
      description: 'Test pricing page and plan selection',
      path: '/pricing',
      expectedNav: 'public'
    },
    {
      id: 'registration',
      title: 'Registration Flow',
      description: 'Test streamlined registration with plan selection',
      path: '/auth/enhanced-signup?plan=business',
      expectedNav: 'public'
    },
    {
      id: 'login',
      title: 'Login Flow',
      description: 'Test enhanced login with redirect handling',
      path: '/auth/enhanced-login',
      expectedNav: 'public'
    },
    {
      id: 'onboarding',
      title: 'Onboarding',
      description: 'Test user onboarding wizard',
      path: '/onboarding/welcome',
      expectedNav: 'authenticated',
      requiresAuth: true
    },
    {
      id: 'dashboard',
      title: 'Dashboard',
      description: 'Test authenticated dashboard with dynamic navigation',
      path: '/dashboard',
      expectedNav: 'authenticated',
      requiresAuth: true
    }
  ];

  const runAutoTest = async () => {
    setTestMode('auto');
    setTestResults({});
    
    for (let i = 0; i < testSteps.length; i++) {
      const step = testSteps[i];
      setAutoTestStep(i);
      
      // Skip auth-required steps if not authenticated
      if (step.requiresAuth && !isAuthenticated) {
        setTestResults(prev => ({ ...prev, [step.id]: false }));
        continue;
      }
      
      // Navigate to step
      router.push(step.path);
      
      // Wait for navigation
      await new Promise(resolve => setTimeout(resolve, 1000));
      
      // Check if navigation mode matches expected
      const success = navigationState.navigationMode === step.expectedNav;
      setTestResults(prev => ({ ...prev, [step.id]: success }));
      
      // Wait before next step
      await new Promise(resolve => setTimeout(resolve, 500));
    }
    
    setTestMode('manual');
    setAutoTestStep(0);
  };

  const resetTest = () => {
    setTestResults({});
    setAutoTestStep(0);
    setTestMode('manual');
  };

  const getServiceIcon = (service: string) => {
    const icons = {
      'access_point_provider': Shield,
      'system_integration': Database,
      'nigerian_compliance': Building,
      'organization_management': Users
    };
    return icons[service as keyof typeof icons] || Shield;
  };

  return (
    <div className="max-w-6xl mx-auto p-6 space-y-8">
      <div className="text-center">
        <h1 className="text-3xl font-bold text-gray-900 mb-4">Authentication Flow Test Suite</h1>
        <p className="text-gray-600 max-w-2xl mx-auto">
          Comprehensive testing environment for the complete user authentication journey,
          from public navigation through registration, login, onboarding, and dashboard access.
        </p>
      </div>

      {/* Current State */}
      <Card className="bg-blue-50 border-blue-200">
        <CardHeader>
          <CardTitle className="flex items-center">
            <Eye className="mr-2 h-5 w-5" />
            Current State
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 text-sm">
            <div>
              <div className="font-medium text-gray-700">Authentication</div>
              <div className={`flex items-center ${isAuthenticated ? 'text-green-600' : 'text-red-600'}`}>
                {isAuthenticated ? <CheckCircle className="mr-1 h-4 w-4" /> : <User className="mr-1 h-4 w-4" />}
                {isAuthenticated ? 'Authenticated' : 'Not Authenticated'}
              </div>
            </div>
            
            <div>
              <div className="font-medium text-gray-700">Navigation Mode</div>
              <div className="flex items-center">
                <Badge variant={navigationState.navigationMode === 'public' ? 'secondary' : 'default'}>
                  {navigationState.navigationMode}
                </Badge>
              </div>
            </div>
            
            <div>
              <div className="font-medium text-gray-700">Current Route</div>
              <div className="font-mono text-gray-900">{router.pathname}</div>
            </div>
            
            <div>
              <div className="font-medium text-gray-700">User</div>
              <div className="text-gray-900">{user?.name || 'Anonymous'}</div>
            </div>
          </div>

          {/* Navigation State Details */}
          <div className="mt-4 p-3 bg-white rounded border">
            <div className="text-sm font-medium text-gray-700 mb-2">Navigation State Details</div>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-2 text-xs">
              <div>Loading: {navigationState.isLoading ? '✅' : '❌'}</div>
              <div>Public Nav: {navigationState.shouldShowPublicNav ? '✅' : '❌'}</div>
              <div>Dynamic Nav: {navigationState.shouldShowDynamicNav ? '✅' : '❌'}</div>
              <div>Auth State: {navigationState.isAuthenticated ? '✅' : '❌'}</div>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Test Controls */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center">
            <Settings className="mr-2 h-5 w-5" />
            Test Controls
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="flex flex-wrap gap-4">
            <Button 
              onClick={runAutoTest} 
              disabled={testMode === 'auto'}
              className="flex items-center"
            >
              <Play className="mr-2 h-4 w-4" />
              {testMode === 'auto' ? 'Running Auto Test...' : 'Run Auto Test'}
            </Button>
            
            <Button 
              variant="outline" 
              onClick={resetTest}
              className="flex items-center"
            >
              <RotateCcw className="mr-2 h-4 w-4" />
              Reset Test
            </Button>
            
            <Button 
              variant="outline" 
              onClick={navigationState.refreshNavigation}
              className="flex items-center"
            >
              <RefreshCw className="mr-2 h-4 w-4" />
              Refresh Navigation
            </Button>
            
            {isAuthenticated && (
              <Button 
                variant="outline" 
                onClick={logout}
                className="flex items-center text-red-600 border-red-200"
              >
                <LogOut className="mr-2 h-4 w-4" />
                Logout
              </Button>
            )}
          </div>

          {testMode === 'auto' && (
            <div className="mt-4 p-3 bg-blue-50 rounded">
              <div className="text-sm font-medium text-blue-900">
                Auto Test Progress: Step {autoTestStep + 1} of {testSteps.length}
              </div>
              <div className="text-sm text-blue-700">
                Testing: {testSteps[autoTestStep]?.title}
              </div>
            </div>
          )}
        </CardContent>
      </Card>

      {/* Test Steps */}
      <Card>
        <CardHeader>
          <CardTitle>Test Steps</CardTitle>
          <CardDescription>
            Manual testing of each step in the authentication flow
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            {testSteps.map((step, index) => {
              const isActive = testMode === 'auto' && autoTestStep === index;
              const testResult = testResults[step.id];
              const canTest = !step.requiresAuth || isAuthenticated;
              
              return (
                <div 
                  key={step.id}
                  className={`p-4 border rounded-lg transition-all ${
                    isActive ? 'border-blue-500 bg-blue-50' : 'border-gray-200 hover:border-gray-300'
                  }`}
                >
                  <div className="flex items-center justify-between">
                    <div className="flex-1">
                      <div className="flex items-center space-x-3">
                        <div className={`w-8 h-8 rounded-full flex items-center justify-center text-sm font-medium ${
                          testResult === true ? 'bg-green-100 text-green-800' :
                          testResult === false ? 'bg-red-100 text-red-800' :
                          'bg-gray-100 text-gray-600'
                        }`}>
                          {testResult === true ? '✓' : 
                           testResult === false ? '✗' : 
                           index + 1}
                        </div>
                        
                        <div>
                          <h3 className="font-medium text-gray-900">{step.title}</h3>
                          <p className="text-sm text-gray-600">{step.description}</p>
                          <div className="text-xs text-gray-500 mt-1">
                            Route: <code>{step.path}</code> | Expected Nav: <code>{step.expectedNav}</code>
                            {step.requiresAuth && <Badge variant="warning" className="ml-2 text-xs">Requires Auth</Badge>}
                          </div>
                        </div>
                      </div>
                    </div>
                    
                    <div className="flex items-center space-x-2">
                      {!canTest && (
                        <Badge variant="secondary" className="text-xs">
                          Auth Required
                        </Badge>
                      )}
                      
                      <Link href={step.path}>
                        <Button 
                          variant="outline" 
                          size="sm"
                          disabled={!canTest}
                          className="flex items-center"
                        >
                          Test
                          <ExternalLink className="ml-1 h-3 w-3" />
                        </Button>
                      </Link>
                    </div>
                  </div>
                </div>
              );
            })}
          </div>
        </CardContent>
      </Card>

      {/* User Permissions (if authenticated) */}
      {isAuthenticated && (
        <Card>
          <CardHeader>
            <CardTitle>User Permissions & Services</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              {/* Service Access */}
              <div>
                <h3 className="font-medium text-gray-900 mb-3">Service Access</h3>
                <div className="space-y-2">
                  {[
                    { key: 'canAccessApp', label: 'Access Point Provider', level: permissions.getAppAccess() },
                    { key: 'canAccessSI', label: 'System Integration', level: permissions.getSIAccess() },
                    { key: 'canAccessCompliance', label: 'Nigerian Compliance', level: permissions.getComplianceAccess() },
                    { key: 'canManageOrg', label: 'Organization Management', level: permissions.getOrgAccess() }
                  ].map(service => {
                    const hasAccess = permissions[service.key as keyof typeof permissions]();
                    const ServiceIcon = getServiceIcon(service.key.replace('canAccess', '').replace('canManage', '').toLowerCase());
                    
                    return (
                      <div key={service.key} className="flex items-center justify-between p-2 border rounded">
                        <div className="flex items-center space-x-2">
                          <ServiceIcon className="h-4 w-4 text-gray-600" />
                          <span className="text-sm">{service.label}</span>
                        </div>
                        <div className="flex items-center space-x-2">
                          {service.level && (
                            <Badge variant="secondary" className="text-xs">
                              {service.level}
                            </Badge>
                          )}
                          <div className={`w-2 h-2 rounded-full ${hasAccess ? 'bg-green-500' : 'bg-red-500'}`} />
                        </div>
                      </div>
                    );
                  })}
                </div>
              </div>

              {/* User Type */}
              <div>
                <h3 className="font-medium text-gray-900 mb-3">User Type & Features</h3>
                <div className="space-y-2">
                  {[
                    { key: 'isOwner', label: 'Owner' },
                    { key: 'isAdmin', label: 'Admin' },
                    { key: 'isHybridUser', label: 'Hybrid User' },
                    { key: 'isPureAppUser', label: 'Pure APP User' },
                    { key: 'isPureSIUser', label: 'Pure SI User' },
                    { key: 'hasEnterpriseFeatures', label: 'Enterprise Features' },
                    { key: 'hasPremiumFeatures', label: 'Premium Features' },
                    { key: 'canUseBetaFeatures', label: 'Beta Features' }
                  ].map(item => {
                    const hasFeature = permissions[item.key as keyof typeof permissions]();
                    
                    return (
                      <div key={item.key} className="flex items-center justify-between p-2 border rounded">
                        <span className="text-sm">{item.label}</span>
                        <div className={`w-2 h-2 rounded-full ${hasFeature ? 'bg-green-500' : 'bg-gray-300'}`} />
                      </div>
                    );
                  })}
                </div>
              </div>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Navigation Preview */}
      <Card>
        <CardHeader>
          <CardTitle>Live Navigation Preview</CardTitle>
          <CardDescription>
            Current navigation component being rendered based on authentication state
          </CardDescription>
        </CardHeader>
        <CardContent>
          <NavigationTransition className="border rounded-lg overflow-hidden">
            <SmartNavigation variant="horizontal" showCategories={false} />
          </NavigationTransition>
        </CardContent>
      </Card>

      {/* Quick Actions */}
      <Card>
        <CardHeader>
          <CardTitle>Quick Actions</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <Link href="/pricing">
              <Button variant="outline" className="w-full">
                View Pricing
              </Button>
            </Link>
            
            <Link href="/auth/enhanced-signup">
              <Button variant="outline" className="w-full">
                Test Signup
              </Button>
            </Link>
            
            <Link href="/auth/enhanced-login">
              <Button variant="outline" className="w-full">
                Test Login
              </Button>
            </Link>
            
            {isAuthenticated ? (
              <Link href="/dashboard">
                <Button variant="outline" className="w-full">
                  Go to Dashboard
                </Button>
              </Link>
            ) : (
              <Button variant="outline" className="w-full" disabled>
                Dashboard (Login Required)
              </Button>
            )}
          </div>
        </CardContent>
      </Card>
    </div>
  );
};

export default AuthenticationFlowTest;