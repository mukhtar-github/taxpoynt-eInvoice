import React, { useState, useEffect } from 'react';
import { useRouter } from 'next/router';
import Link from 'next/link';
import { useAuth } from '../../../context/AuthContext';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '../../../components/ui/Card';
import { Button } from '../../../components/ui/Button';
import { Input } from '../../../components/ui/Input';
import { FormField } from '../../../components/ui/FormField';
import { Typography } from '../../../components/ui/Typography';
import { Badge } from '../../../components/ui/Badge';
import { useToast } from '../../../components/ui/Toast';
import { 
  Shield, Check, ArrowLeft, CheckCircle, Eye, EyeOff,
  Star, Zap, Building, CreditCard 
} from 'lucide-react';

interface PlanInfo {
  name: string;
  price: string;
  period: string;
  features: string[];
  icon: React.ElementType;
  color: string;
}

interface RegistrationData {
  name: string;
  email: string;
  password: string;
  confirmPassword: string;
  companyName: string;
  agreeToTerms: boolean;
}

// Plan mapping from pricing page
const planMapping: Record<string, PlanInfo> = {
  starter: {
    name: 'Starter',
    price: '₦25,000',
    period: 'per month',
    features: [
      'Up to 100 invoices per month',
      'Basic FIRS compliance & IRN generation',
      '2 business system integrations',
      'Digital invoice signing',
      'Email support'
    ],
    icon: Shield,
    color: 'blue'
  },
  business: {
    name: 'Business',
    price: '₦75,000',
    period: 'per month',
    features: [
      'Up to 1,000 invoices per month',
      'Complete FIRS certification',
      '5 business system integrations',
      'CRM & POS integrations',
      'Priority support & onboarding'
    ],
    icon: Zap,
    color: 'purple'
  },
  enterprise: {
    name: 'Enterprise',
    price: '₦150,000',
    period: 'per month',
    features: [
      'Unlimited invoices',
      'All business system integrations',
      'Custom connector development',
      'Dedicated account manager',
      'API access & developer tools'
    ],
    icon: Building,
    color: 'green'
  }
};

interface StreamlinedRegistrationFormProps {
  className?: string;
}

export const StreamlinedRegistrationForm: React.FC<StreamlinedRegistrationFormProps> = ({
  className
}) => {
  const [formData, setFormData] = useState<RegistrationData>({
    name: '',
    email: '',
    password: '',
    confirmPassword: '',
    companyName: '',
    agreeToTerms: false
  });
  const [selectedPlan, setSelectedPlan] = useState<string>('');
  const [errors, setErrors] = useState<Record<string, string>>({});
  const [isLoading, setIsLoading] = useState(false);
  const [showPassword, setShowPassword] = useState(false);
  const [showConfirmPassword, setShowConfirmPassword] = useState(false);
  
  const { login, register } = useAuth();
  const router = useRouter();
  const toast = useToast();

  // Get plan from URL params
  useEffect(() => {
    const { plan } = router.query;
    if (plan && typeof plan === 'string') {
      setSelectedPlan(plan.toLowerCase());
    }
  }, [router.query]);

  const selectedPlanInfo = selectedPlan ? planMapping[selectedPlan] : null;

  const validateForm = (): boolean => {
    const newErrors: Record<string, string> = {};

    if (!formData.name.trim()) newErrors.name = 'Full name is required';
    if (!formData.email.trim()) newErrors.email = 'Email is required';
    if (!formData.email.includes('@')) newErrors.email = 'Please enter a valid email';
    if (!formData.companyName.trim()) newErrors.companyName = 'Company name is required';
    if (!formData.password) newErrors.password = 'Password is required';
    if (formData.password.length < 8) newErrors.password = 'Password must be at least 8 characters';
    if (formData.password !== formData.confirmPassword) {
      newErrors.confirmPassword = 'Passwords do not match';
    }
    if (!formData.agreeToTerms) {
      newErrors.terms = 'You must agree to the terms and conditions';
    }

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!validateForm()) return;

    setIsLoading(true);
    try {
      // Register user
      await register({
        companyName: formData.companyName,
        taxId: '', // Will be collected during onboarding
        address: '', // Will be collected during onboarding
        phone: '', // Will be collected during onboarding
        email: formData.email,
        username: formData.email,
        password: formData.password
      });

      // Store selected plan for onboarding
      if (selectedPlan) {
        localStorage.setItem('selected_plan', selectedPlan);
      }

      toast({
        title: "Registration Successful!",
        description: "Welcome to TaxPoynt eInvoice. Let's get you set up.",
        status: "success",
        duration: 5000,
        isClosable: true
      });

      // Auto-login and redirect to onboarding
      await login(formData.email, formData.password);
      router.push('/onboarding/welcome');

    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Registration failed';
      setErrors({ submit: errorMessage });
      toast({
        title: "Registration Failed",
        description: errorMessage,
        status: "error",
        duration: 5000,
        isClosable: true
      });
    } finally {
      setIsLoading(false);
    }
  };

  const getPasswordStrength = () => {
    const password = formData.password;
    let score = 0;
    if (password.length >= 8) score++;
    if (/[A-Z]/.test(password)) score++;
    if (/[a-z]/.test(password)) score++;
    if (/[0-9]/.test(password)) score++;
    if (/[^A-Za-z0-9]/.test(password)) score++;
    return score;
  };

  const getPasswordStrengthColor = () => {
    const strength = getPasswordStrength();
    if (strength <= 2) return 'bg-red-400';
    if (strength <= 3) return 'bg-yellow-400';
    return 'bg-green-400';
  };

  const getPasswordStrengthText = () => {
    const strength = getPasswordStrength();
    if (strength <= 2) return 'Weak';
    if (strength <= 3) return 'Fair';
    if (strength <= 4) return 'Good';
    return 'Strong';
  };

  return (
    <div className={`max-w-2xl mx-auto space-y-8 ${className}`}>
      {/* Selected Plan Display */}
      {selectedPlanInfo && (
        <Card className="border-blue-200 bg-blue-50">
          <CardContent className="p-6">
            <div className="flex items-center justify-between">
              <div className="flex items-center space-x-4">
                <div className={`p-3 rounded-lg bg-${selectedPlanInfo.color}-100`}>
                  <selectedPlanInfo.icon className={`h-6 w-6 text-${selectedPlanInfo.color}-600`} />
                </div>
                <div>
                  <h3 className="font-semibold text-gray-900">{selectedPlanInfo.name} Plan</h3>
                  <div className="flex items-center space-x-2">
                    <span className="text-2xl font-bold text-gray-900">{selectedPlanInfo.price}</span>
                    <span className="text-gray-600">{selectedPlanInfo.period}</span>
                    <Badge variant="success" className="text-xs">
                      14-day free trial
                    </Badge>
                  </div>
                </div>
              </div>
              <Button
                variant="outline"
                size="sm"
                onClick={() => router.push('/pricing')}
                className="flex items-center"
              >
                <ArrowLeft className="mr-2 h-4 w-4" />
                Change Plan
              </Button>
            </div>
            
            <div className="mt-4 grid grid-cols-1 md:grid-cols-2 gap-2">
              {selectedPlanInfo.features.slice(0, 4).map((feature, index) => (
                <div key={index} className="flex items-center text-sm text-gray-700">
                  <Check className="h-4 w-4 text-green-500 mr-2 flex-shrink-0" />
                  {feature}
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      )}

      {/* Registration Form */}
      <Card>
        <CardHeader>
          <CardTitle>Create Your Account</CardTitle>
          <CardDescription>
            {selectedPlanInfo 
              ? `Complete your registration to start your ${selectedPlanInfo.name} plan free trial`
              : 'Join TaxPoynt eInvoice to manage your invoices and tax compliance'
            }
          </CardDescription>
        </CardHeader>

        <CardContent>
          <form onSubmit={handleSubmit} className="space-y-6">
            {/* Error Display */}
            {errors.submit && (
              <div className="p-4 bg-red-50 border border-red-200 text-red-600 rounded-md">
                {errors.submit}
              </div>
            )}

            {/* Personal Information */}
            <div className="space-y-4">
              <h3 className="font-medium text-gray-900">Personal Information</h3>
              
              <FormField label="Full Name" htmlFor="name" required error={errors.name}>
                <Input
                  id="name"
                  value={formData.name}
                  onChange={(e) => setFormData(prev => ({ ...prev, name: e.target.value }))}
                  placeholder="John Doe"
                  disabled={isLoading}
                />
              </FormField>

              <FormField label="Email Address" htmlFor="email" required error={errors.email}>
                <Input
                  id="email"
                  type="email"
                  value={formData.email}
                  onChange={(e) => setFormData(prev => ({ ...prev, email: e.target.value }))}
                  placeholder="john@company.com"
                  disabled={isLoading}
                />
                <div className="mt-1 text-sm text-gray-500">
                  This will be your login email
                </div>
              </FormField>
            </div>

            {/* Company Information */}
            <div className="space-y-4">
              <h3 className="font-medium text-gray-900">Company Information</h3>
              
              <FormField label="Company Name" htmlFor="companyName" required error={errors.companyName}>
                <Input
                  id="companyName"
                  value={formData.companyName}
                  onChange={(e) => setFormData(prev => ({ ...prev, companyName: e.target.value }))}
                  placeholder="Your Company Ltd."
                  disabled={isLoading}
                />
                <div className="mt-1 text-sm text-gray-500">
                  Additional company details will be collected during setup
                </div>
              </FormField>
            </div>

            {/* Security */}
            <div className="space-y-4">
              <h3 className="font-medium text-gray-900">Account Security</h3>
              
              <FormField label="Password" htmlFor="password" required error={errors.password}>
                <div className="relative">
                  <Input
                    id="password"
                    type={showPassword ? 'text' : 'password'}
                    value={formData.password}
                    onChange={(e) => setFormData(prev => ({ ...prev, password: e.target.value }))}
                    placeholder="8+ characters"
                    disabled={isLoading}
                  />
                  <button
                    type="button"
                    onClick={() => setShowPassword(!showPassword)}
                    className="absolute right-3 top-1/2 transform -translate-y-1/2 text-gray-400 hover:text-gray-600"
                  >
                    {showPassword ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
                  </button>
                </div>
                
                {/* Password Strength Indicator */}
                {formData.password && (
                  <div className="mt-2 space-y-2">
                    <div className="flex justify-between text-sm">
                      <span className="text-gray-600">Password strength:</span>
                      <span className={`font-medium ${getPasswordStrength() >= 4 ? 'text-green-600' : getPasswordStrength() >= 3 ? 'text-yellow-600' : 'text-red-600'}`}>
                        {getPasswordStrengthText()}
                      </span>
                    </div>
                    <div className="flex space-x-1">
                      {[1, 2, 3, 4, 5].map((level) => (
                        <div
                          key={level}
                          className={`h-2 flex-1 rounded ${
                            getPasswordStrength() >= level ? getPasswordStrengthColor() : 'bg-gray-200'
                          }`}
                        />
                      ))}
                    </div>
                  </div>
                )}
              </FormField>

              <FormField label="Confirm Password" htmlFor="confirmPassword" required error={errors.confirmPassword}>
                <div className="relative">
                  <Input
                    id="confirmPassword"
                    type={showConfirmPassword ? 'text' : 'password'}
                    value={formData.confirmPassword}
                    onChange={(e) => setFormData(prev => ({ ...prev, confirmPassword: e.target.value }))}
                    placeholder="Confirm your password"
                    disabled={isLoading}
                  />
                  <button
                    type="button"
                    onClick={() => setShowConfirmPassword(!showConfirmPassword)}
                    className="absolute right-3 top-1/2 transform -translate-y-1/2 text-gray-400 hover:text-gray-600"
                  >
                    {showConfirmPassword ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
                  </button>
                </div>
              </FormField>
            </div>

            {/* Terms and Conditions */}
            <div className="space-y-4">
              <label className="flex items-start space-x-3">
                <input
                  type="checkbox"
                  checked={formData.agreeToTerms}
                  onChange={(e) => setFormData(prev => ({ ...prev, agreeToTerms: e.target.checked }))}
                  className="mt-1 rounded border-gray-300"
                />
                <div className="text-sm text-gray-600">
                  I agree to TaxPoynt's{' '}
                  <Link href="/terms" className="text-blue-600 hover:underline">
                    Terms of Service
                  </Link>
                  {' '}and{' '}
                  <Link href="/privacy" className="text-blue-600 hover:underline">
                    Privacy Policy
                  </Link>
                  , and consent to receive marketing communications.
                </div>
              </label>
              {errors.terms && (
                <div className="text-red-600 text-sm">{errors.terms}</div>
              )}
            </div>

            {/* Submit Button */}
            <Button 
              type="submit" 
              className="w-full" 
              loading={isLoading}
              size="lg"
            >
              {selectedPlanInfo ? 'Start Free Trial' : 'Create Account'}
              <CheckCircle className="ml-2 h-5 w-5" />
            </Button>

            {/* Login Link */}
            <div className="text-center text-sm text-gray-600">
              Already have an account?{' '}
              <Link 
                href={`/auth/login${selectedPlan ? `?plan=${selectedPlan}` : ''}`} 
                className="text-blue-600 hover:underline font-medium"
              >
                Sign in
              </Link>
            </div>

            {/* Security Notice */}
            <div className="p-4 bg-gray-50 rounded-lg">
              <div className="flex items-start space-x-3">
                <Shield className="h-5 w-5 text-green-600 mt-0.5" />
                <div className="text-sm text-gray-600">
                  <div className="font-medium text-gray-900 mb-1">Your data is secure</div>
                  <div>
                    We use bank-grade encryption and are NDPR compliant. 
                    {selectedPlanInfo && (
                      <> Start your {selectedPlanInfo.name} plan with a 14-day free trial - no credit card required.</>
                    )}
                  </div>
                </div>
              </div>
            </div>
          </form>
        </CardContent>
      </Card>

      {/* What Happens Next */}
      <Card className="bg-blue-50 border-blue-200">
        <CardContent className="p-6">
          <h3 className="font-semibold text-gray-900 mb-4">What happens next?</h3>
          <div className="space-y-3">
            <div className="flex items-center space-x-3">
              <div className="w-6 h-6 bg-blue-600 text-white rounded-full flex items-center justify-center text-sm font-medium">1</div>
              <span className="text-sm text-gray-700">Complete company setup and FIRS integration</span>
            </div>
            <div className="flex items-center space-x-3">
              <div className="w-6 h-6 bg-blue-600 text-white rounded-full flex items-center justify-center text-sm font-medium">2</div>
              <span className="text-sm text-gray-700">Connect your business systems (optional)</span>
            </div>
            <div className="flex items-center space-x-3">
              <div className="w-6 h-6 bg-blue-600 text-white rounded-full flex items-center justify-center text-sm font-medium">3</div>
              <span className="text-sm text-gray-700">Start generating FIRS-compliant invoices</span>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
};

export default StreamlinedRegistrationForm;