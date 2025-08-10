/**
 * TaxPoynt Strategic Home/Business Page
 * ===================================
 * Role-aware home page for authenticated users with strategic navigation.
 * Simple, elegant interface that connects to our business interface components.
 * 
 * User Flow: Landing → Sign In → Home → Business Actions
 */

import React from 'react';
import { useRouter } from 'next/router';
import { Button } from '../design_system/components/Button';
import { colors, roleThemes } from '../design_system/tokens';

interface HomePageProps {
  user: {
    name: string;
    company: string;
    role: 'si' | 'app' | 'hybrid' | 'admin';
    currentPackage?: string;
    avatar?: string;
  };
  stats: {
    invoicesThisMonth: number;
    successfulTransmissions: number;
    integrations: number;
    // Revenue is only for admin consumption
    adminRevenue?: number;
  };
}

export const HomePage: React.FC<HomePageProps> = ({ user, stats }) => {
  const router = useRouter();
  const roleTheme = roleThemes[user.role];

  // Role-specific welcome messages
  const getWelcomeMessage = () => {
    switch (user.role) {
      case 'si':
        return 'Welcome to your System Integrator dashboard. Manage your e-invoicing operations and grow your business.';
      case 'app':
        return 'Welcome to TaxPoynt APP service. Generate and transmit e-invoices securely through our certified platform.';
      case 'hybrid':
        return 'Hybrid Premium dashboard - access both SI and APP capabilities with advanced features.';
      case 'admin':
        return 'TaxPoynt Admin Console - monitor platform health, revenue, and grant compliance.';
      default:
        return 'Welcome to TaxPoynt - your complete e-invoicing solution.';
    }
  };

  // Role-specific quick actions
  const getQuickActions = () => {
    const baseActions = [
      {
        title: 'Generate Invoice',
        description: 'Create and submit new e-invoices',
        icon: '📄',
        action: () => router.push('/invoices/create'),
        primary: true
      },
      {
        title: 'View Reports',
        description: 'Check compliance and performance',
        icon: '📊',
        action: () => router.push('/reports')
      }
    ];

    switch (user.role) {
      case 'si':
        return [
          ...baseActions,
          {
            title: 'Service Packages',
            description: 'Upgrade or manage your subscription',
            icon: '📦',
            action: () => router.push('/service-packages')
          },
          {
            title: 'Billing',
            description: 'Manage payments and invoices',
            icon: '💳',
            action: () => router.push('/billing')
          }
        ];
        
      case 'app':
        return [
          {
            title: 'Generate Invoice',
            description: 'Create new e-invoices',
            icon: '📄',
            action: () => router.push('/invoices/create'),
            primary: true
          },
          {
            title: 'Transmit to FIRS',
            description: 'Send invoices via TaxPoynt APP',
            icon: '🚀',
            action: () => router.push('/invoices/transmit')
          },
          {
            title: 'View Submissions',
            description: 'Track invoice submissions',
            icon: '📊',
            action: () => router.push('/invoices/status')
          }
        ];
        
      case 'hybrid':
        return [
          ...baseActions,
          {
            title: 'Advanced Analytics',
            description: 'View comprehensive reports',
            icon: '📈',
            action: () => router.push('/analytics')
          },
          {
            title: 'Premium Services',
            description: 'Access hybrid-only features',
            icon: '👑',
            action: () => router.push('/billing')
          }
        ];
        
      case 'admin':
        return [
          {
            title: 'Grant Dashboard',
            description: 'Monitor FIRS grant compliance',
            icon: '🎯',
            action: () => router.push('/admin/grant-tracking'),
            primary: true
          },
          {
            title: 'KPI Monitoring',
            description: 'Platform performance metrics',
            icon: '📊',
            action: () => router.push('/admin/kpi-dashboard')
          },
          {
            title: 'User Management',
            description: 'Manage platform users',
            icon: '👥',
            action: () => router.push('/admin/users')
          }
        ];
        
      default:
        return baseActions;
    }
  };

  const formatNumber = (num: number) => {
    return new Intl.NumberFormat('en-NG').format(num);
  };

  const formatCurrency = (amount: number) => {
    return new Intl.NumberFormat('en-NG', {
      style: 'currency',
      currency: 'NGN',
      minimumFractionDigits: 0
    }).format(amount);
  };

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Strategic Header */}
      <div className="bg-white border-b border-gray-200">
        <div className="max-w-7xl mx-auto px-4 py-6">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-4">
              {/* TaxPoynt Logo */}
              <div className="flex items-center space-x-3">
                <div className="w-10 h-10 bg-blue-600 rounded-lg flex items-center justify-center">
                  <span className="text-white font-bold text-lg">T</span>
                </div>
                <div>
                  <h1 className="text-2xl font-bold text-gray-900">TaxPoynt</h1>
                  <p className="text-sm text-gray-500">E-Invoice Platform</p>
                </div>
              </div>
              
              {/* Role Badge */}
              <div className={`px-3 py-1 rounded-full text-sm font-medium ${
                user.role === 'si' ? 'bg-blue-100 text-blue-800' :
                user.role === 'app' ? 'bg-green-100 text-green-800' :
                user.role === 'hybrid' ? 'bg-purple-100 text-purple-800' :
                'bg-gray-100 text-gray-800'
              }`}>
                {user.role === 'si' ? 'System Integrator' :
                 user.role === 'app' ? 'Access Point Provider' :
                 user.role === 'hybrid' ? 'Hybrid Premium' :
                 'Administrator'}
              </div>
            </div>

            {/* User Info */}
            <div className="flex items-center space-x-4">
              <div className="text-right">
                <div className="font-semibold text-gray-900">{user.name}</div>
                <div className="text-sm text-gray-600">{user.company}</div>
              </div>
              <div className="w-10 h-10 bg-gray-300 rounded-full flex items-center justify-center">
                <span className="text-gray-600 font-medium">
                  {user.name.charAt(0).toUpperCase()}
                </span>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Main Content */}
      <div className="max-w-7xl mx-auto px-4 py-8">
        
        {/* Welcome Section */}
        <div className="mb-8">
          <h2 className="text-3xl font-bold text-gray-900 mb-2">
            Welcome back, {user.name.split(' ')[0]}!
          </h2>
          <p className="text-gray-600 text-lg max-w-3xl">
            {getWelcomeMessage()}
          </p>
        </div>

        {/* Stats Overview */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
          <div className="bg-white rounded-xl border border-gray-200 p-6">
            <div className="flex items-center justify-between">
              <div>
                <div className="text-2xl font-bold text-gray-900">
                  {formatNumber(stats.invoicesThisMonth)}
                </div>
                <div className="text-gray-600">Invoices This Month</div>
              </div>
              <div className="text-3xl">📄</div>
            </div>
          </div>

          <div className="bg-white rounded-xl border border-gray-200 p-6">
            <div className="flex items-center justify-between">
              <div>
                <div className="text-2xl font-bold text-green-600">
                  {stats.successfulTransmissions}
                </div>
                <div className="text-gray-600">Successful Transmissions</div>
              </div>
              <div className="text-3xl">✅</div>
            </div>
          </div>

          <div className="bg-white rounded-xl border border-gray-200 p-6">
            <div className="flex items-center justify-between">
              <div>
                <div className="text-2xl font-bold text-blue-600">
                  {stats.integrations}
                </div>
                <div className="text-gray-600">Active Integrations</div>
              </div>
              <div className="text-3xl">🔗</div>
            </div>
          </div>

          {/* Admin-only revenue display */}
          {user.role === 'admin' && stats.adminRevenue && (
            <div className="bg-white rounded-xl border border-gray-200 p-6">
              <div className="flex items-center justify-between">
                <div>
                  <div className="text-2xl font-bold text-purple-600">
                    {formatCurrency(stats.adminRevenue)}
                  </div>
                  <div className="text-gray-600">Platform Revenue</div>
                </div>
                <div className="text-3xl">💰</div>
              </div>
            </div>
          )}
        </div>

        {/* Quick Actions */}
        <div className="bg-white rounded-xl border border-gray-200 p-8">
          <h3 className="text-xl font-bold text-gray-900 mb-6">Quick Actions</h3>
          
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {getQuickActions().map((action, index) => (
              <div
                key={index}
                className={`p-6 rounded-xl border-2 transition-all cursor-pointer hover:shadow-lg ${
                  action.primary 
                    ? 'border-blue-200 bg-blue-50 hover:border-blue-300' 
                    : 'border-gray-200 bg-gray-50 hover:border-gray-300'
                }`}
                onClick={action.action}
              >
                <div className="flex items-start space-x-4">
                  <div className="text-3xl">{action.icon}</div>
                  <div className="flex-1">
                    <h4 className={`font-semibold mb-2 ${
                      action.primary ? 'text-blue-900' : 'text-gray-900'
                    }`}>
                      {action.title}
                    </h4>
                    <p className={`text-sm ${
                      action.primary ? 'text-blue-700' : 'text-gray-600'
                    }`}>
                      {action.description}
                    </p>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Strategic CTA Section */}
        <div className="mt-8 bg-gradient-to-r from-blue-50 to-purple-50 rounded-xl border border-blue-200 p-8">
          <div className="flex items-center justify-between">
            <div>
              <h3 className="text-xl font-bold text-gray-900 mb-2">
                {user.role === 'si' ? 'Grow Your Business' :
                 user.role === 'app' ? 'Streamline Your E-Invoicing' :
                 user.role === 'hybrid' ? 'Unlock Premium Features' :
                 'Optimize Platform Performance'}
              </h3>
              <p className="text-gray-600">
                {user.role === 'si' ? 'Upgrade your service package to serve more clients and increase revenue.' :
                 user.role === 'app' ? 'Use TaxPoynt\'s certified APP service for secure, compliant invoice transmission.' :
                 user.role === 'hybrid' ? 'Access advanced analytics and premium support features.' :
                 'Monitor platform health, grant compliance, and business optimization.'}
              </p>
            </div>
            <div className="ml-8">
              <Button
                variant="primary"
                size="lg"
                role={user.role}
                onClick={() => {
                  if (user.role === 'si') router.push('/service-packages');
                  else if (user.role === 'app') router.push('/invoices/create');
                  else if (user.role === 'hybrid') router.push('/analytics');
                  else router.push('/admin/grant-tracking');
                }}
              >
                {user.role === 'si' ? 'View Packages' :
                 user.role === 'app' ? 'Create Invoice' :
                 user.role === 'hybrid' ? 'View Analytics' :
                 'View Dashboard'}
              </Button>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};