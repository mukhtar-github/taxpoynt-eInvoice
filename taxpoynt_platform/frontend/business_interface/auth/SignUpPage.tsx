/**
 * TaxPoynt Strategic Sign Up Page
 * ==============================
 * Simple sign-up interface that leads to the ConsentIntegratedRegistration flow.
 * Maintains simplicity while providing clear role selection.
 */

import React, { useState } from 'react';
import { useRouter } from 'next/router';
import Link from 'next/link';
import { Button } from '../../design_system/components/Button';

interface SignUpPageProps {
  onContinueToRegistration: (basicInfo: {
    email: string;
    password: string;
    selectedRole: 'si' | 'app' | 'hybrid';
  }) => void;
  isLoading?: boolean;
  error?: string;
}

export const SignUpPage: React.FC<SignUpPageProps> = ({ 
  onContinueToRegistration, 
  isLoading, 
  error 
}) => {
  const router = useRouter();
  const [formData, setFormData] = useState({
    email: '',
    password: '',
    confirmPassword: '',
    selectedRole: 'si' as 'si' | 'app' | 'hybrid',
    acceptTerms: false
  });

  const [formErrors, setFormErrors] = useState<Record<string, string>>({});

  const validateForm = () => {
    const errors: Record<string, string> = {};

    if (!formData.email.trim()) {
      errors.email = 'Email is required';
    } else if (!formData.email.includes('@')) {
      errors.email = 'Please enter a valid email';
    }

    if (!formData.password) {
      errors.password = 'Password is required';
    } else if (formData.password.length < 6) {
      errors.password = 'Password must be at least 6 characters';
    }

    if (formData.password !== formData.confirmPassword) {
      errors.confirmPassword = 'Passwords do not match';
    }

    if (!formData.acceptTerms) {
      errors.acceptTerms = 'You must accept the terms and conditions';
    }

    setFormErrors(errors);
    return Object.keys(errors).length === 0;
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!validateForm()) return;

    onContinueToRegistration({
      email: formData.email,
      password: formData.password,
      selectedRole: formData.selectedRole
    });
  };

  const roleOptions = [
    {
      id: 'si',
      title: 'System Integrator',
      description: 'Commercial e-invoicing service for your business',
      icon: '🔗',
      features: ['ERP Integrations', 'Commercial Billing', 'Business Growth'],
      recommended: false
    },
    {
      id: 'app',
      title: 'Access Point Provider',
      description: 'Secure invoice transmission via TaxPoynt APP',
      icon: '🚀',
      features: ['FIRS Transmission', 'Invoice Generation', 'Secure Processing'],
      recommended: true
    },
    {
      id: 'hybrid',
      title: 'Hybrid Premium',
      description: 'Combined SI + APP with advanced features',
      icon: '👑',
      features: ['All SI Features', 'All APP Features', 'Premium Support'],
      recommended: false
    }
  ];

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-gray-100 py-8 px-4">
      <div className="max-w-4xl mx-auto">
        
        {/* Header */}
        <div className="text-center mb-8">
          <div className="flex items-center justify-center space-x-3 mb-4">
            <div className="w-12 h-12 bg-blue-600 rounded-xl flex items-center justify-center">
              <span className="text-white font-bold text-xl">T</span>
            </div>
            <div>
              <h1 className="text-2xl font-bold text-gray-900">TaxPoynt</h1>
              <p className="text-sm text-gray-600">E-Invoice Platform</p>
            </div>
          </div>
          <h2 className="text-2xl font-bold text-gray-900">Create Your Account</h2>
          <p className="text-gray-600">Choose your service type and get started</p>
        </div>

        <div className="bg-white rounded-2xl border border-gray-200 shadow-lg p-8">
          
          {/* Error Display */}
          {error && (
            <div className="mb-6 p-4 bg-red-50 border border-red-200 rounded-lg">
              <div className="flex items-center">
                <span className="text-red-600 mr-2">❌</span>
                <span className="text-red-700 text-sm">{error}</span>
              </div>
            </div>
          )}

          <form onSubmit={handleSubmit} className="space-y-8">
            
            {/* Role Selection */}
            <div>
              <h3 className="text-lg font-semibold text-gray-900 mb-4">Choose Your Service Type</h3>
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                {roleOptions.map((role) => (
                  <div
                    key={role.id}
                    className={`relative p-6 border-2 rounded-xl cursor-pointer transition-all ${
                      formData.selectedRole === role.id
                        ? 'border-blue-500 bg-blue-50'
                        : 'border-gray-200 hover:border-gray-300'
                    } ${role.recommended ? 'ring-2 ring-green-200' : ''}`}
                    onClick={() => setFormData({ ...formData, selectedRole: role.id as any })}
                  >
                    {role.recommended && (
                      <div className="absolute -top-2 left-1/2 transform -translate-x-1/2">
                        <span className="bg-green-500 text-white px-3 py-1 text-xs font-medium rounded-full">
                          Recommended
                        </span>
                      </div>
                    )}
                    
                    <div className="text-center">
                      <div className="text-3xl mb-3">{role.icon}</div>
                      <h4 className="font-semibold text-gray-900 mb-2">{role.title}</h4>
                      <p className="text-gray-600 text-sm mb-4">{role.description}</p>
                      
                      <ul className="space-y-1">
                        {role.features.map((feature, index) => (
                          <li key={index} className="text-xs text-gray-500 flex items-center justify-center">
                            <span className="mr-1">✓</span>
                            {feature}
                          </li>
                        ))}
                      </ul>
                    </div>
                    
                    <input
                      type="radio"
                      name="role"
                      value={role.id}
                      checked={formData.selectedRole === role.id}
                      onChange={() => {}} // Handled by div click
                      className="absolute top-4 right-4"
                    />
                  </div>
                ))}
              </div>
            </div>

            {/* Account Information */}
            <div className="space-y-6">
              <h3 className="text-lg font-semibold text-gray-900">Account Information</h3>
              
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                {/* Email */}
                <div>
                  <label htmlFor="email" className="block text-sm font-medium text-gray-700 mb-2">
                    Email Address *
                  </label>
                  <input
                    id="email"
                    type="email"
                    required
                    value={formData.email}
                    onChange={(e) => setFormData({ ...formData, email: e.target.value })}
                    className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-colors"
                    placeholder="your@company.com"
                    disabled={isLoading}
                  />
                  {formErrors.email && (
                    <p className="mt-1 text-sm text-red-600">{formErrors.email}</p>
                  )}
                </div>

                {/* Password */}
                <div>
                  <label htmlFor="password" className="block text-sm font-medium text-gray-700 mb-2">
                    Password *
                  </label>
                  <input
                    id="password"
                    type="password"
                    required
                    value={formData.password}
                    onChange={(e) => setFormData({ ...formData, password: e.target.value })}
                    className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-colors"
                    placeholder="Minimum 6 characters"
                    disabled={isLoading}
                  />
                  {formErrors.password && (
                    <p className="mt-1 text-sm text-red-600">{formErrors.password}</p>
                  )}
                </div>
              </div>

              {/* Confirm Password */}
              <div>
                <label htmlFor="confirmPassword" className="block text-sm font-medium text-gray-700 mb-2">
                  Confirm Password *
                </label>
                <input
                  id="confirmPassword"
                  type="password"
                  required
                  value={formData.confirmPassword}
                  onChange={(e) => setFormData({ ...formData, confirmPassword: e.target.value })}
                  className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-colors"
                  placeholder="Confirm your password"
                  disabled={isLoading}
                />
                {formErrors.confirmPassword && (
                  <p className="mt-1 text-sm text-red-600">{formErrors.confirmPassword}</p>
                )}
              </div>
            </div>

            {/* Terms and Conditions */}
            <div>
              <label className="flex items-start">
                <input
                  type="checkbox"
                  checked={formData.acceptTerms}
                  onChange={(e) => setFormData({ ...formData, acceptTerms: e.target.checked })}
                  className="h-4 w-4 text-blue-600 border-gray-300 rounded focus:ring-blue-500 mt-1"
                  disabled={isLoading}
                />
                <span className="ml-2 text-sm text-gray-600">
                  I agree to the{' '}
                  <Link href="/terms" className="text-blue-600 hover:text-blue-700 underline">
                    Terms of Service
                  </Link>{' '}
                  and{' '}
                  <Link href="/privacy" className="text-blue-600 hover:text-blue-700 underline">
                    Privacy Policy
                  </Link>
                </span>
              </label>
              {formErrors.acceptTerms && (
                <p className="mt-1 text-sm text-red-600">{formErrors.acceptTerms}</p>
              )}
            </div>

            {/* Continue Button */}
            <Button
              type="submit"
              variant="primary"
              size="lg"
              loading={isLoading}
              className="w-full"
            >
              {isLoading ? 'Processing...' : 'Continue to Registration'}
            </Button>
          </form>
        </div>

        {/* Sign In Link */}
        <div className="text-center mt-6">
          <p className="text-gray-600">
            Already have an account?{' '}
            <Link 
              href="/auth/signin"
              className="text-blue-600 hover:text-blue-700 font-medium hover:underline"
            >
              Sign in
            </Link>
          </p>
        </div>

        {/* Next Steps Preview */}
        <div className="mt-8 bg-blue-50 border border-blue-200 rounded-xl p-6">
          <h4 className="font-semibold text-blue-900 mb-2">Next Steps</h4>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4 text-sm text-blue-800">
            <div className="flex items-center">
              <span className="mr-2">1️⃣</span>
              Complete company information
            </div>
            <div className="flex items-center">
              <span className="mr-2">2️⃣</span>
              Configure data permissions
            </div>
            <div className="flex items-center">
              <span className="mr-2">3️⃣</span>
              Choose service package
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};