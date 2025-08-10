/**
 * TaxPoynt Service Package Selector
 * =================================
 * Strategic service package selection with role-aware presentation.
 * Based on SI_UNIFIED_SUBSCRIPTION_ARCHITECTURE.md
 * 
 * User Flow: Home/Dashboard → Service Management → Package Selection
 * Billing Flow: Package Selection → Billing (Separate Page)
 */

import React, { useState } from 'react';
import { Button } from '../../design_system/components/Button';
import { colors, roleThemes } from '../../design_system/tokens';

// Service Package Definitions (from SI_UNIFIED_SUBSCRIPTION_ARCHITECTURE.md)
export interface ServicePackage {
  id: string;
  name: string;
  description: string;
  price: {
    monthly: number;
    annual: number;
  };
  features: string[];
  limits: {
    invoicesPerMonth: number | 'unlimited';
    integrations: number | 'unlimited';
    users: number | 'unlimited';
  };
  popular?: boolean;
  recommended?: boolean;
}

const servicePackages: ServicePackage[] = [
  {
    id: 'starter',
    name: 'Starter',
    description: 'Perfect for small businesses getting started with e-invoicing',
    price: { monthly: 15000, annual: 150000 }, // NGN
    features: [
      'Basic e-invoice generation',
      'FIRS compliance validation',
      'Single ERP integration',
      'Email notifications',
      '24/7 support chat'
    ],
    limits: {
      invoicesPerMonth: 100,
      integrations: 1,
      users: 3
    }
  },
  {
    id: 'professional',
    name: 'Professional',
    description: 'Advanced features for growing businesses',
    price: { monthly: 45000, annual: 450000 },
    features: [
      'Advanced invoice templates',
      'Multiple ERP integrations',
      'Real-time compliance monitoring',
      'Custom reporting',
      'API access',
      'Priority support'
    ],
    limits: {
      invoicesPerMonth: 500,
      integrations: 3,
      users: 10
    },
    popular: true
  },
  {
    id: 'enterprise',
    name: 'Enterprise',
    description: 'Complete solution for large organizations',
    price: { monthly: 150000, annual: 1500000 },
    features: [
      'Unlimited integrations',
      'White-label solutions',
      'Advanced analytics',
      'Custom compliance rules',
      'Dedicated account manager',
      'SLA guarantees'
    ],
    limits: {
      invoicesPerMonth: 'unlimited',
      integrations: 'unlimited',
      users: 'unlimited'
    },
    recommended: true
  },
  {
    id: 'hybrid',
    name: 'Hybrid Premium',
    description: 'SI + APP combined services (Highest tier automatically)',
    price: { monthly: 200000, annual: 2000000 },
    features: [
      'All Enterprise features',
      'APP grant revenue sharing',
      'Priority compliance processing',
      'Advanced integration framework',
      'Custom development support',
      'Revenue optimization tools'
    ],
    limits: {
      invoicesPerMonth: 'unlimited',
      integrations: 'unlimited',
      users: 'unlimited'
    }
  }
];

interface PackageSelectorProps {
  currentRole: 'si' | 'app' | 'hybrid' | 'admin';
  currentPackage?: string;
  onPackageSelect: (packageId: string) => void;
  onUpgrade: (packageId: string) => void;
}

export const PackageSelector: React.FC<PackageSelectorProps> = ({
  currentRole,
  currentPackage,
  onPackageSelect,
  onUpgrade
}) => {
  const [billingCycle, setBillingCycle] = useState<'monthly' | 'annual'>('annual');

  // Strategic package filtering based on role
  const availablePackages = servicePackages.filter(pkg => {
    if (currentRole === 'hybrid') {
      // Hybrid users automatically get the highest tier
      return pkg.id === 'hybrid';
    }
    if (currentRole === 'app') {
      // APP users (grant-funded) don't see commercial packages
      return false; // APP users don't manage commercial subscriptions
    }
    if (currentRole === 'admin') {
      // Admins see all packages for management
      return true;
    }
    // SI users see commercial packages (not hybrid)
    return pkg.id !== 'hybrid';
  });

  const formatPrice = (price: number) => {
    return new Intl.NumberFormat('en-NG', {
      style: 'currency',
      currency: 'NGN',
      minimumFractionDigits: 0
    }).format(price);
  };

  return (
    <div className="max-w-7xl mx-auto px-4 py-8">
      {/* Strategic Header */}
      <div className="text-center mb-12">
        <h1 className="text-4xl font-bold text-gray-900 mb-4">
          {currentRole === 'hybrid' ? 'Your Premium Hybrid Package' : 'Choose Your Service Package'}
        </h1>
        <p className="text-xl text-gray-600 max-w-3xl mx-auto">
          {currentRole === 'hybrid' 
            ? 'You have access to our premium hybrid package with all features included.'
            : 'Select the perfect package for your business needs. Upgrade or downgrade anytime.'
          }
        </p>
        
        {/* Billing Cycle Toggle - Hidden for hybrid users */}
        {currentRole !== 'hybrid' && (
          <div className="flex items-center justify-center mt-8">
            <span className={`mr-3 ${billingCycle === 'monthly' ? 'font-semibold' : 'text-gray-500'}`}>
              Monthly
            </span>
            <button
              onClick={() => setBillingCycle(billingCycle === 'monthly' ? 'annual' : 'monthly')}
              className={`
                relative inline-flex h-6 w-11 items-center rounded-full transition-colors
                ${billingCycle === 'annual' ? 'bg-blue-600' : 'bg-gray-200'}
              `}
            >
              <span
                className={`
                  inline-block h-4 w-4 transform rounded-full bg-white transition-transform
                  ${billingCycle === 'annual' ? 'translate-x-6' : 'translate-x-1'}
                `}
              />
            </button>
            <span className={`ml-3 ${billingCycle === 'annual' ? 'font-semibold' : 'text-gray-500'}`}>
              Annual
            </span>
            {billingCycle === 'annual' && (
              <span className="ml-2 px-2 py-1 text-xs font-medium bg-green-100 text-green-800 rounded-full">
                Save 17%
              </span>
            )}
          </div>
        )}
      </div>

      {/* Package Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8">
        {availablePackages.map((pkg) => {
          const isCurrentPackage = currentPackage === pkg.id;
          const roleTheme = roleThemes[currentRole];
          
          return (
            <div
              key={pkg.id}
              className={`
                relative rounded-2xl border-2 p-8 shadow-lg transition-all duration-300
                ${isCurrentPackage 
                  ? 'border-blue-500 ring-2 ring-blue-500 ring-opacity-20 scale-105' 
                  : 'border-gray-200 hover:border-gray-300 hover:shadow-xl'
                }
                ${pkg.popular ? 'border-blue-500' : ''}
                ${pkg.recommended ? 'border-green-500' : ''}
              `}
            >
              {/* Popular Badge */}
              {pkg.popular && (
                <div className="absolute -top-4 left-1/2 transform -translate-x-1/2">
                  <span className="bg-blue-600 text-white px-4 py-1 rounded-full text-sm font-medium">
                    Most Popular
                  </span>
                </div>
              )}
              
              {/* Recommended Badge */}
              {pkg.recommended && (
                <div className="absolute -top-4 left-1/2 transform -translate-x-1/2">
                  <span className="bg-green-600 text-white px-4 py-1 rounded-full text-sm font-medium">
                    Recommended
                  </span>
                </div>
              )}

              {/* Package Header */}
              <div className="text-center mb-6">
                <h3 className="text-2xl font-bold text-gray-900 mb-2">{pkg.name}</h3>
                <p className="text-gray-600 mb-4">{pkg.description}</p>
                
                <div className="mb-4">
                  <span className="text-4xl font-bold text-gray-900">
                    {formatPrice(pkg.price[billingCycle])}
                  </span>
                  <span className="text-gray-500 ml-2">
                    /{billingCycle === 'monthly' ? 'month' : 'year'}
                  </span>
                </div>
              </div>

              {/* Features List */}
              <ul className="space-y-3 mb-8">
                {pkg.features.map((feature, index) => (
                  <li key={index} className="flex items-start">
                    <svg
                      className="h-5 w-5 text-green-500 mr-3 mt-0.5 flex-shrink-0"
                      fill="currentColor"
                      viewBox="0 0 20 20"
                    >
                      <path
                        fillRule="evenodd"
                        d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z"
                        clipRule="evenodd"
                      />
                    </svg>
                    <span className="text-gray-700">{feature}</span>
                  </li>
                ))}
              </ul>

              {/* Limits */}
              <div className="border-t pt-6 mb-6">
                <h4 className="font-semibold text-gray-900 mb-3">Package Limits</h4>
                <div className="space-y-2 text-sm text-gray-600">
                  <div>Invoices: {pkg.limits.invoicesPerMonth === 'unlimited' ? 'Unlimited' : `${pkg.limits.invoicesPerMonth}/month`}</div>
                  <div>Integrations: {pkg.limits.integrations === 'unlimited' ? 'Unlimited' : pkg.limits.integrations}</div>
                  <div>Users: {pkg.limits.users === 'unlimited' ? 'Unlimited' : pkg.limits.users}</div>
                </div>
              </div>

              {/* Action Button */}
              <div className="text-center">
                {isCurrentPackage ? (
                  <Button variant="outline" size="lg" className="w-full" disabled>
                    Current Package
                  </Button>
                ) : (
                  <Button
                    variant="primary"
                    size="lg"
                    role={currentRole}
                    className="w-full"
                    onClick={() => {
                      // Strategic navigation: Always redirect to billing page
                      if (currentPackage && pkg.id !== currentPackage) {
                        onUpgrade(pkg.id); // Navigates to billing page
                      } else {
                        onPackageSelect(pkg.id); // Navigates to billing page
                      }
                    }}
                  >
                    {currentPackage ? 'Upgrade to This Package' : 'Select Package'}
                  </Button>
                )}
              </div>
            </div>
          );
        })}
      </div>

      {/* Strategic Information */}
      <div className="mt-12 text-center">
        <div className="bg-gray-50 rounded-2xl p-8 max-w-4xl mx-auto">
          <h3 className="text-xl font-semibold text-gray-900 mb-4">
            Why Choose TaxPoynt?
          </h3>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6 text-center">
            <div>
              <div className="text-3xl font-bold text-blue-600 mb-2">99.9%</div>
              <div className="text-gray-600">FIRS Compliance Rate</div>
            </div>
            <div>
              <div className="text-3xl font-bold text-green-600 mb-2">24/7</div>
              <div className="text-gray-600">Expert Support</div>
            </div>
            <div>
              <div className="text-3xl font-bold text-purple-600 mb-2">50+</div>
              <div className="text-gray-600">ERP Integrations</div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};