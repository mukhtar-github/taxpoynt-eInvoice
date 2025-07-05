import React, { useState, useEffect } from 'react';
import { useRouter } from 'next/router';
import Link from 'next/link';
import { useAuth } from '../../context/AuthContext';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '../ui/Card';
import { Button } from '../ui/Button';
import { Input } from '../ui/Input';
import { FormField } from '../ui/FormField';
import { Typography } from '../ui/Typography';
import { Badge } from '../ui/Badge';
import { useToast } from '../ui/Toast';
import { 
  Shield, Database, Building, Users, Check, ArrowRight, 
  Star, Zap, Globe, Lock, Headphones, CheckCircle 
} from 'lucide-react';

interface ServicePlan {
  id: string;
  name: string;
  icon: React.ElementType;
  description: string;
  features: string[];
  price: string;
  popular?: boolean;
  recommended?: boolean;
  color: string;
}

interface RegistrationData {
  name: string;
  email: string;
  password: string;
  confirmPassword: string;
  companyName: string;
  selectedServices: string[];
  agreeToTerms: boolean;
}

const servicePlans: ServicePlan[] = [
  {
    id: 'access_point_provider',
    name: 'Access Point Provider',
    icon: Shield,
    description: 'FIRS-certified e-invoicing for tax compliance',
    features: [
      'Generate IRN numbers',
      'Submit to FIRS directly',
      'Digital certificate management',
      'Secure transmission',
      'Compliance reporting'
    ],
    price: '₦15,000/month',
    popular: true,
    color: 'cyan'
  },
  {
    id: 'system_integration',
    name: 'System Integration',
    icon: Database,
    description: 'Connect your ERP, CRM, and POS systems',
    features: [
      'Odoo integration',
      'SAP connectivity',
      'Custom API development',
      'Real-time sync',
      'Multi-system support'
    ],
    price: '₦25,000/month',
    recommended: true,
    color: 'blue'
  },
  {
    id: 'nigerian_compliance',
    name: 'Nigerian Compliance',
    icon: Building,
    description: 'Complete regulatory and tax compliance',
    features: [
      'Tax calculation engine',
      'Regulatory reporting',
      'Audit trail management',
      'Compliance monitoring',
      'Legal updates'
    ],
    price: '₦20,000/month',
    color: 'purple'
  },
  {
    id: 'enterprise',
    name: 'Enterprise Suite',
    icon: Users,
    description: 'All services with priority support',
    features: [
      'All APP features',
      'All SI features',
      'All compliance features',
      'Dedicated support',
      'Custom training',
      'SLA guarantee'
    ],
    price: '₦50,000/month',
    popular: false,
    color: 'green'
  }
];

interface EnhancedRegistrationFormProps {
  onStepComplete?: (step: number, data: Partial<RegistrationData>) => void;
  className?: string;
}

export const EnhancedRegistrationForm: React.FC<EnhancedRegistrationFormProps> = ({
  onStepComplete,
  className
}) => {
  const [currentStep, setCurrentStep] = useState(1);
  const [formData, setFormData] = useState<RegistrationData>({
    name: '',
    email: '',
    password: '',
    confirmPassword: '',
    companyName: '',
    selectedServices: [],
    agreeToTerms: false
  });
  const [errors, setErrors] = useState<Record<string, string>>({});
  const [isLoading, setIsLoading] = useState(false);
  const { login, register } = useAuth();
  const router = useRouter();
  const toast = useToast();

  // Get plan from URL params
  useEffect(() => {
    const { plan, service } = router.query;
    if (plan && typeof plan === 'string') {
      const planService = servicePlans.find(s => s.id === plan);
      if (planService) {
        setFormData(prev => ({
          ...prev,
          selectedServices: [plan]
        }));
      }
    }
    if (service && typeof service === 'string') {
      setFormData(prev => ({
        ...prev,
        selectedServices: [service]
      }));
    }
  }, [router.query]);

  const validateStep = (step: number): boolean => {
    const newErrors: Record<string, string> = {};

    if (step === 1) {
      if (!formData.name.trim()) newErrors.name = 'Full name is required';
      if (!formData.email.trim()) newErrors.email = 'Email is required';
      if (!formData.email.includes('@')) newErrors.email = 'Please enter a valid email';
      if (!formData.companyName.trim()) newErrors.companyName = 'Company name is required';
    }

    if (step === 2) {
      if (!formData.password) newErrors.password = 'Password is required';
      if (formData.password.length < 8) newErrors.password = 'Password must be at least 8 characters';
      if (formData.password !== formData.confirmPassword) {
        newErrors.confirmPassword = 'Passwords do not match';
      }
    }

    if (step === 3) {
      if (formData.selectedServices.length === 0) {
        newErrors.services = 'Please select at least one service';
      }
      if (!formData.agreeToTerms) {
        newErrors.terms = 'You must agree to the terms and conditions';
      }
    }

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleNext = () => {
    if (validateStep(currentStep)) {
      const nextStep = currentStep + 1;
      setCurrentStep(nextStep);
      onStepComplete?.(currentStep, formData);
    }
  };

  const handleBack = () => {
    setCurrentStep(Math.max(1, currentStep - 1));
  };

  const handleServiceToggle = (serviceId: string) => {
    setFormData(prev => ({
      ...prev,
      selectedServices: prev.selectedServices.includes(serviceId)
        ? prev.selectedServices.filter(s => s !== serviceId)
        : [...prev.selectedServices, serviceId]
    }));
  };

  const handleSubmit = async () => {
    if (!validateStep(3)) return;

    setIsLoading(true);
    try {
      // Register user with selected services
      await register({
        companyName: formData.companyName,
        taxId: '', // Will be collected later in onboarding
        address: '', // Will be collected later
        phone: '', // Will be collected later
        email: formData.email,
        username: formData.email,
        password: formData.password
      });

      // Store selected services for onboarding
      localStorage.setItem('selected_services', JSON.stringify(formData.selectedServices));

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

  const getStepTitle = () => {
    switch (currentStep) {
      case 1: return "Let's get started";
      case 2: return "Secure your account";
      case 3: return "Choose your services";
      default: return "Registration";
    }
  };

  const getStepDescription = () => {
    switch (currentStep) {
      case 1: return "Tell us about you and your business";
      case 2: return "Create a strong password for your account";
      case 3: return "Select the services that match your needs";
      default: return "";
    }
  };

  const renderStep1 = () => (
    <div className="space-y-4">
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
      </FormField>

      <FormField label="Company Name" htmlFor="companyName" required error={errors.companyName}>
        <Input
          id="companyName"
          value={formData.companyName}
          onChange={(e) => setFormData(prev => ({ ...prev, companyName: e.target.value }))}
          placeholder="Your Company Ltd."
          disabled={isLoading}
        />
      </FormField>
    </div>
  );

  const renderStep2 = () => (
    <div className="space-y-4">
      <FormField label="Password" htmlFor="password" required error={errors.password}>
        <Input
          id="password"
          type="password"
          value={formData.password}
          onChange={(e) => setFormData(prev => ({ ...prev, password: e.target.value }))}
          placeholder="8+ characters"
          disabled={isLoading}
        />
        <div className="mt-2 text-sm text-gray-600">
          Password should contain at least 8 characters with letters and numbers
        </div>
      </FormField>

      <FormField label="Confirm Password" htmlFor="confirmPassword" required error={errors.confirmPassword}>
        <Input
          id="confirmPassword"
          type="password"
          value={formData.confirmPassword}
          onChange={(e) => setFormData(prev => ({ ...prev, confirmPassword: e.target.value }))}
          placeholder="Confirm your password"
          disabled={isLoading}
        />
      </FormField>

      {/* Password strength indicator */}
      <div className="space-y-2">
        <div className="text-sm font-medium text-gray-700">Password strength:</div>
        <div className="flex space-x-1">
          {[1, 2, 3, 4].map((level) => (
            <div
              key={level}
              className={`h-2 flex-1 rounded ${
                formData.password.length >= level * 2
                  ? level <= 2 ? 'bg-red-400' : level === 3 ? 'bg-yellow-400' : 'bg-green-400'
                  : 'bg-gray-200'
              }`}
            />
          ))}
        </div>
      </div>
    </div>
  );

  const renderStep3 = () => (
    <div className="space-y-6">
      {errors.services && (
        <div className="p-3 bg-red-50 text-red-600 rounded-md text-sm">
          {errors.services}
        </div>
      )}

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {servicePlans.map((plan) => {
          const Icon = plan.icon;
          const isSelected = formData.selectedServices.includes(plan.id);
          
          return (
            <div
              key={plan.id}
              onClick={() => handleServiceToggle(plan.id)}
              className={`relative p-4 border-2 rounded-lg cursor-pointer transition-all ${
                isSelected
                  ? 'border-blue-500 bg-blue-50'
                  : 'border-gray-200 hover:border-gray-300 hover:bg-gray-50'
              }`}
            >
              {/* Selection indicator */}
              {isSelected && (
                <div className="absolute top-2 right-2">
                  <CheckCircle className="h-5 w-5 text-blue-500" />
                </div>
              )}

              {/* Popular/Recommended badges */}
              {plan.popular && (
                <Badge className="absolute -top-2 left-4 bg-orange-500 text-white">
                  Popular
                </Badge>
              )}
              {plan.recommended && (
                <Badge className="absolute -top-2 left-4 bg-green-500 text-white">
                  Recommended
                </Badge>
              )}

              <div className="flex items-start space-x-3">
                <div className={`p-2 rounded-lg bg-${plan.color}-100`}>
                  <Icon className={`h-6 w-6 text-${plan.color}-600`} />
                </div>
                
                <div className="flex-1">
                  <h3 className="font-semibold text-gray-900">{plan.name}</h3>
                  <p className="text-sm text-gray-600 mt-1">{plan.description}</p>
                  
                  <div className="mt-3">
                    <div className="font-semibold text-lg text-gray-900">{plan.price}</div>
                  </div>

                  <ul className="mt-3 space-y-1">
                    {plan.features.slice(0, 3).map((feature, index) => (
                      <li key={index} className="flex items-center text-sm text-gray-600">
                        <Check className="h-3 w-3 text-green-500 mr-2 flex-shrink-0" />
                        {feature}
                      </li>
                    ))}
                    {plan.features.length > 3 && (
                      <li className="text-sm text-gray-500">
                        +{plan.features.length - 3} more features
                      </li>
                    )}
                  </ul>
                </div>
              </div>
            </div>
          );
        })}
      </div>

      {/* Terms and conditions */}
      <div className="space-y-4">
        <label className="flex items-start space-x-3">
          <input
            type="checkbox"
            checked={formData.agreeToTerms}
            onChange={(e) => setFormData(prev => ({ ...prev, agreeToTerms: e.target.checked }))}
            className="mt-1"
          />
          <div className="text-sm text-gray-600">
            I agree to the{' '}
            <Link href="/terms" className="text-blue-600 hover:underline">
              Terms of Service
            </Link>
            {' '}and{' '}
            <Link href="/privacy" className="text-blue-600 hover:underline">
              Privacy Policy
            </Link>
          </div>
        </label>
        {errors.terms && (
          <div className="text-red-600 text-sm">{errors.terms}</div>
        )}
      </div>
    </div>
  );

  return (
    <Card className={`w-full max-w-2xl mx-auto ${className}`}>
      <CardHeader>
        <div className="flex items-center justify-between">
          <div>
            <CardTitle>{getStepTitle()}</CardTitle>
            <CardDescription>{getStepDescription()}</CardDescription>
          </div>
          <div className="text-sm text-gray-500">
            Step {currentStep} of 3
          </div>
        </div>
        
        {/* Progress bar */}
        <div className="w-full bg-gray-200 rounded-full h-2 mt-4">
          <div
            className="bg-blue-600 h-2 rounded-full transition-all duration-300"
            style={{ width: `${(currentStep / 3) * 100}%` }}
          />
        </div>
      </CardHeader>

      <CardContent className="space-y-6">
        {/* Step content */}
        {currentStep === 1 && renderStep1()}
        {currentStep === 2 && renderStep2()}
        {currentStep === 3 && renderStep3()}

        {/* Submit error */}
        {errors.submit && (
          <div className="p-3 bg-red-50 text-red-600 rounded-md">
            {errors.submit}
          </div>
        )}

        {/* Navigation buttons */}
        <div className="flex justify-between">
          <Button
            variant="outline"
            onClick={handleBack}
            disabled={currentStep === 1 || isLoading}
          >
            Back
          </Button>

          {currentStep < 3 ? (
            <Button onClick={handleNext} disabled={isLoading}>
              Next
              <ArrowRight className="ml-2 h-4 w-4" />
            </Button>
          ) : (
            <Button onClick={handleSubmit} loading={isLoading}>
              Create Account
              <CheckCircle className="ml-2 h-4 w-4" />
            </Button>
          )}
        </div>

        {/* Login link */}
        <div className="text-center text-sm text-gray-600">
          Already have an account?{' '}
          <Link href="/auth/login" className="text-blue-600 hover:underline">
            Sign in
          </Link>
        </div>
      </CardContent>
    </Card>
  );
};

export default EnhancedRegistrationForm;