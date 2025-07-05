import React, { useState, useEffect } from 'react';
import { useRouter } from 'next/router';
import { useAuth } from '../../../context/AuthContext';
import { useServicePermissions } from '../../hooks/useServicePermissions';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '../../../components/ui/Card';
import { Button } from '../../../components/ui/Button';
import { Input } from '../../../components/ui/Input';
import { FormField } from '../../../components/ui/FormField';
import { Badge } from '../../../components/ui/Badge';
import { useToast } from '../../../components/ui/Toast';
import { 
  Shield, Database, Building, Users, Check, ArrowRight, ArrowLeft,
  MapPin, Phone, CreditCard, Globe, FileText, Settings,
  CheckCircle, Star, Zap, Target, Award
} from 'lucide-react';

interface OnboardingStep {
  id: string;
  title: string;
  description: string;
  required: boolean;
  userTypes: string[];
}

interface CompanyProfile {
  taxId: string;
  address: string;
  city: string;
  state: string;
  postalCode: string;
  phone: string;
  website: string;
  industry: string;
  size: string;
}

interface ServiceConfiguration {
  selectedServices: string[];
  firsConfiguration: {
    enabled: boolean;
    testMode: boolean;
  };
  integrationPreferences: {
    erp: string[];
    crm: string[];
    pos: string[];
  };
  notificationPreferences: {
    email: boolean;
    sms: boolean;
    webhook: boolean;
  };
}

interface OnboardingData {
  companyProfile: CompanyProfile;
  serviceConfiguration: ServiceConfiguration;
  currentStep: number;
  completed: boolean;
}

const onboardingSteps: OnboardingStep[] = [
  {
    id: 'welcome',
    title: 'Welcome to TaxPoynt',
    description: 'Let\'s get your account set up for FIRS compliance',
    required: true,
    userTypes: ['all']
  },
  {
    id: 'company-profile',
    title: 'Company Information',
    description: 'Complete your business profile for FIRS registration',
    required: true,
    userTypes: ['all']
  },
  {
    id: 'service-setup',
    title: 'Service Configuration',
    description: 'Configure your selected services and preferences',
    required: true,
    userTypes: ['all']
  },
  {
    id: 'integrations',
    title: 'System Integrations',
    description: 'Connect your existing business systems',
    required: false,
    userTypes: ['system_integration', 'hybrid']
  },
  {
    id: 'payment-setup',
    title: 'Payment & Billing',
    description: 'Set up your payment method and billing preferences',
    required: false,
    userTypes: ['all']
  },
  {
    id: 'completion',
    title: 'You\'re All Set!',
    description: 'Welcome to the TaxPoynt platform',
    required: true,
    userTypes: ['all']
  }
];

const nigerianStates = [
  'Abia', 'Adamawa', 'Akwa Ibom', 'Anambra', 'Bauchi', 'Bayelsa', 'Benue', 'Borno',
  'Cross River', 'Delta', 'Ebonyi', 'Edo', 'Ekiti', 'Enugu', 'FCT', 'Gombe',
  'Imo', 'Jigawa', 'Kaduna', 'Kano', 'Katsina', 'Kebbi', 'Kogi', 'Kwara',
  'Lagos', 'Nasarawa', 'Niger', 'Ogun', 'Ondo', 'Osun', 'Oyo', 'Plateau',
  'Rivers', 'Sokoto', 'Taraba', 'Yobe', 'Zamfara'
];

const businessSizes = [
  { value: 'micro', label: 'Micro (1-9 employees)' },
  { value: 'small', label: 'Small (10-49 employees)' },
  { value: 'medium', label: 'Medium (50-249 employees)' },
  { value: 'large', label: 'Large (250+ employees)' }
];

const industries = [
  'Agriculture', 'Banking & Finance', 'Construction', 'Education', 'Energy & Oil',
  'Healthcare', 'Hospitality', 'Information Technology', 'Manufacturing', 'Media',
  'Professional Services', 'Real Estate', 'Retail & Trade', 'Telecommunications',
  'Transportation & Logistics', 'Other'
];

interface OnboardingWizardProps {
  className?: string;
}

export const OnboardingWizard: React.FC<OnboardingWizardProps> = ({
  className
}) => {
  const [onboardingData, setOnboardingData] = useState<OnboardingData>({
    companyProfile: {
      taxId: '',
      address: '',
      city: '',
      state: '',
      postalCode: '',
      phone: '',
      website: '',
      industry: '',
      size: ''
    },
    serviceConfiguration: {
      selectedServices: [],
      firsConfiguration: {
        enabled: true,
        testMode: true
      },
      integrationPreferences: {
        erp: [],
        crm: [],
        pos: []
      },
      notificationPreferences: {
        email: true,
        sms: false,
        webhook: false
      }
    },
    currentStep: 0,
    completed: false
  });

  const [errors, setErrors] = useState<Record<string, string>>({});
  const [isLoading, setIsLoading] = useState(false);
  const { user } = useAuth();
  const permissions = useServicePermissions();
  const router = useRouter();
  const toast = useToast();

  // Load selected plan/services from registration
  useEffect(() => {
    const selectedPlan = localStorage.getItem('selected_plan');
    const selectedServices = localStorage.getItem('selected_services');
    
    if (selectedPlan || selectedServices) {
      const services = selectedServices ? JSON.parse(selectedServices) : [selectedPlan].filter(Boolean);
      setOnboardingData(prev => ({
        ...prev,
        serviceConfiguration: {
          ...prev.serviceConfiguration,
          selectedServices: services
        }
      }));
    }
  }, []);

  // Determine which steps to show based on user type
  const getRelevantSteps = (): OnboardingStep[] => {
    const userType = permissions.isHybridUser() ? 'hybrid' 
      : permissions.isPureAppUser() ? 'access_point_provider'
      : permissions.isPureSIUser() ? 'system_integration'
      : 'all';

    return onboardingSteps.filter(step => 
      step.userTypes.includes('all') || step.userTypes.includes(userType)
    );
  };

  const currentSteps = getRelevantSteps();
  const currentStepData = currentSteps[onboardingData.currentStep];

  const validateStep = (stepId: string): boolean => {
    const newErrors: Record<string, string> = {};

    switch (stepId) {
      case 'company-profile':
        if (!onboardingData.companyProfile.taxId.trim()) {
          newErrors.taxId = 'Tax ID is required';
        }
        if (!onboardingData.companyProfile.address.trim()) {
          newErrors.address = 'Address is required';
        }
        if (!onboardingData.companyProfile.city.trim()) {
          newErrors.city = 'City is required';
        }
        if (!onboardingData.companyProfile.state) {
          newErrors.state = 'State is required';
        }
        if (!onboardingData.companyProfile.phone.trim()) {
          newErrors.phone = 'Phone number is required';
        }
        if (!onboardingData.companyProfile.industry) {
          newErrors.industry = 'Industry is required';
        }
        if (!onboardingData.companyProfile.size) {
          newErrors.size = 'Business size is required';
        }
        break;

      case 'service-setup':
        if (onboardingData.serviceConfiguration.selectedServices.length === 0) {
          newErrors.services = 'Please select at least one service';
        }
        break;
    }

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleNext = () => {
    if (currentStepData && !validateStep(currentStepData.id)) {
      return;
    }

    if (onboardingData.currentStep < currentSteps.length - 1) {
      setOnboardingData(prev => ({
        ...prev,
        currentStep: prev.currentStep + 1
      }));
    }
  };

  const handleBack = () => {
    if (onboardingData.currentStep > 0) {
      setOnboardingData(prev => ({
        ...prev,
        currentStep: prev.currentStep - 1
      }));
    }
  };

  const handleComplete = async () => {
    setIsLoading(true);
    try {
      // Save onboarding data to backend
      // In a real app, this would call an API
      
      // Mark onboarding as completed
      localStorage.setItem('onboarding_completed', 'true');
      localStorage.removeItem('selected_plan');
      localStorage.removeItem('selected_services');

      toast({
        title: "Onboarding Complete!",
        description: "Welcome to TaxPoynt eInvoice. Let's start with your first invoice.",
        status: "success",
        duration: 5000,
        isClosable: true
      });

      // Redirect to appropriate dashboard
      const defaultRoute = permissions.getDefaultRoute();
      router.push(defaultRoute);

    } catch (err) {
      toast({
        title: "Setup Error",
        description: "There was an issue completing your setup. Please try again.",
        status: "error",
        duration: 5000,
        isClosable: true
      });
    } finally {
      setIsLoading(false);
    }
  };

  const updateCompanyProfile = (field: keyof CompanyProfile, value: string) => {
    setOnboardingData(prev => ({
      ...prev,
      companyProfile: {
        ...prev.companyProfile,
        [field]: value
      }
    }));
  };

  const updateServiceConfiguration = (field: string, value: any) => {
    setOnboardingData(prev => ({
      ...prev,
      serviceConfiguration: {
        ...prev.serviceConfiguration,
        [field]: value
      }
    }));
  };

  const renderWelcomeStep = () => (
    <div className="text-center space-y-6">
      <div className="w-16 h-16 bg-blue-100 rounded-full flex items-center justify-center mx-auto">
        <Star className="h-8 w-8 text-blue-600" />
      </div>
      
      <div>
        <h2 className="text-2xl font-bold text-gray-900 mb-2">
          Welcome to TaxPoynt eInvoice!
        </h2>
        <p className="text-gray-600 max-w-md mx-auto">
          Let's get you set up for FIRS-compliant e-invoicing. This will only take a few minutes.
        </p>
      </div>

      {onboardingData.serviceConfiguration.selectedServices.length > 0 && (
        <div className="bg-blue-50 rounded-lg p-4">
          <h3 className="font-medium text-gray-900 mb-2">Selected Services</h3>
          <div className="flex flex-wrap gap-2 justify-center">
            {onboardingData.serviceConfiguration.selectedServices.map(service => (
              <Badge key={service} variant="secondary">
                {service.replace('_', ' ').toUpperCase()}
              </Badge>
            ))}
          </div>
        </div>
      )}

      <div className="grid grid-cols-1 md:grid-cols-3 gap-4 text-sm">
        <div className="flex items-center justify-center space-x-2">
          <CheckCircle className="h-5 w-5 text-green-500" />
          <span>FIRS Certified</span>
        </div>
        <div className="flex items-center justify-center space-x-2">
          <Shield className="h-5 w-5 text-blue-500" />
          <span>Secure Setup</span>
        </div>
        <div className="flex items-center justify-center space-x-2">
          <Zap className="h-5 w-5 text-yellow-500" />
          <span>Quick & Easy</span>
        </div>
      </div>
    </div>
  );

  const renderCompanyProfileStep = () => (
    <div className="space-y-6">
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <FormField 
          label="Tax Identification Number" 
          htmlFor="taxId" 
          required 
          error={errors.taxId}
        >
          <Input
            id="taxId"
            value={onboardingData.companyProfile.taxId}
            onChange={(e) => updateCompanyProfile('taxId', e.target.value)}
            placeholder="12345678-0001"
          />
        </FormField>

        <FormField 
          label="Industry" 
          htmlFor="industry" 
          required 
          error={errors.industry}
        >
          <select
            id="industry"
            value={onboardingData.companyProfile.industry}
            onChange={(e) => updateCompanyProfile('industry', e.target.value)}
            className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
          >
            <option value="">Select your industry</option>
            {industries.map(industry => (
              <option key={industry} value={industry}>{industry}</option>
            ))}
          </select>
        </FormField>
      </div>

      <FormField 
        label="Business Address" 
        htmlFor="address" 
        required 
        error={errors.address}
      >
        <Input
          id="address"
          value={onboardingData.companyProfile.address}
          onChange={(e) => updateCompanyProfile('address', e.target.value)}
          placeholder="123 Business Street"
        />
      </FormField>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <FormField 
          label="City" 
          htmlFor="city" 
          required 
          error={errors.city}
        >
          <Input
            id="city"
            value={onboardingData.companyProfile.city}
            onChange={(e) => updateCompanyProfile('city', e.target.value)}
            placeholder="Lagos"
          />
        </FormField>

        <FormField 
          label="State" 
          htmlFor="state" 
          required 
          error={errors.state}
        >
          <select
            id="state"
            value={onboardingData.companyProfile.state}
            onChange={(e) => updateCompanyProfile('state', e.target.value)}
            className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
          >
            <option value="">Select state</option>
            {nigerianStates.map(state => (
              <option key={state} value={state}>{state}</option>
            ))}
          </select>
        </FormField>

        <FormField 
          label="Postal Code" 
          htmlFor="postalCode"
        >
          <Input
            id="postalCode"
            value={onboardingData.companyProfile.postalCode}
            onChange={(e) => updateCompanyProfile('postalCode', e.target.value)}
            placeholder="100001"
          />
        </FormField>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <FormField 
          label="Phone Number" 
          htmlFor="phone" 
          required 
          error={errors.phone}
        >
          <Input
            id="phone"
            value={onboardingData.companyProfile.phone}
            onChange={(e) => updateCompanyProfile('phone', e.target.value)}
            placeholder="+234 801 234 5678"
          />
        </FormField>

        <FormField 
          label="Website" 
          htmlFor="website"
        >
          <Input
            id="website"
            value={onboardingData.companyProfile.website}
            onChange={(e) => updateCompanyProfile('website', e.target.value)}
            placeholder="https://yourcompany.com"
          />
        </FormField>
      </div>

      <FormField 
        label="Business Size" 
        htmlFor="size" 
        required 
        error={errors.size}
      >
        <select
          id="size"
          value={onboardingData.companyProfile.size}
          onChange={(e) => updateCompanyProfile('size', e.target.value)}
          className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
        >
          <option value="">Select business size</option>
          {businessSizes.map(size => (
            <option key={size.value} value={size.value}>{size.label}</option>
          ))}
        </select>
      </FormField>
    </div>
  );

  const renderServiceSetupStep = () => (
    <div className="space-y-6">
      <div>
        <h3 className="font-medium text-gray-900 mb-4">FIRS Configuration</h3>
        <div className="bg-blue-50 rounded-lg p-4 space-y-3">
          <label className="flex items-center space-x-3">
            <input
              type="checkbox"
              checked={onboardingData.serviceConfiguration.firsConfiguration.enabled}
              onChange={(e) => updateServiceConfiguration('firsConfiguration', {
                ...onboardingData.serviceConfiguration.firsConfiguration,
                enabled: e.target.checked
              })}
              className="rounded"
            />
            <span className="text-sm font-medium">Enable FIRS e-invoicing</span>
          </label>
          
          <label className="flex items-center space-x-3">
            <input
              type="checkbox"
              checked={onboardingData.serviceConfiguration.firsConfiguration.testMode}
              onChange={(e) => updateServiceConfiguration('firsConfiguration', {
                ...onboardingData.serviceConfiguration.firsConfiguration,
                testMode: e.target.checked
              })}
              className="rounded"
            />
            <span className="text-sm">Start in test mode (recommended)</span>
          </label>
        </div>
      </div>

      <div>
        <h3 className="font-medium text-gray-900 mb-4">Notification Preferences</h3>
        <div className="space-y-3">
          <label className="flex items-center space-x-3">
            <input
              type="checkbox"
              checked={onboardingData.serviceConfiguration.notificationPreferences.email}
              onChange={(e) => updateServiceConfiguration('notificationPreferences', {
                ...onboardingData.serviceConfiguration.notificationPreferences,
                email: e.target.checked
              })}
              className="rounded"
            />
            <span className="text-sm">Email notifications</span>
          </label>
          
          <label className="flex items-center space-x-3">
            <input
              type="checkbox"
              checked={onboardingData.serviceConfiguration.notificationPreferences.sms}
              onChange={(e) => updateServiceConfiguration('notificationPreferences', {
                ...onboardingData.serviceConfiguration.notificationPreferences,
                sms: e.target.checked
              })}
              className="rounded"
            />
            <span className="text-sm">SMS notifications</span>
          </label>
          
          <label className="flex items-center space-x-3">
            <input
              type="checkbox"
              checked={onboardingData.serviceConfiguration.notificationPreferences.webhook}
              onChange={(e) => updateServiceConfiguration('notificationPreferences', {
                ...onboardingData.serviceConfiguration.notificationPreferences,
                webhook: e.target.checked
              })}
              className="rounded"
            />
            <span className="text-sm">Webhook notifications</span>
          </label>
        </div>
      </div>
    </div>
  );

  const renderCompletionStep = () => (
    <div className="text-center space-y-6">
      <div className="w-16 h-16 bg-green-100 rounded-full flex items-center justify-center mx-auto">
        <Award className="h-8 w-8 text-green-600" />
      </div>
      
      <div>
        <h2 className="text-2xl font-bold text-gray-900 mb-2">
          Congratulations, {user?.name}!
        </h2>
        <p className="text-gray-600 max-w-md mx-auto">
          Your TaxPoynt eInvoice account is now ready. You can start generating FIRS-compliant invoices immediately.
        </p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-4 text-sm">
        <div className="flex items-center justify-center space-x-2">
          <Target className="h-5 w-5 text-blue-500" />
          <span>Ready for FIRS</span>
        </div>
        <div className="flex items-center justify-center space-x-2">
          <Shield className="h-5 w-5 text-green-500" />
          <span>Fully Compliant</span>
        </div>
        <div className="flex items-center justify-center space-x-2">
          <Zap className="h-5 w-5 text-yellow-500" />
          <span>Start Invoicing</span>
        </div>
      </div>

      <div className="bg-blue-50 rounded-lg p-4">
        <h3 className="font-medium text-gray-900 mb-2">What's Next?</h3>
        <ul className="text-sm text-gray-600 space-y-1">
          <li>• Generate your first FIRS-compliant invoice</li>
          <li>• Explore the dashboard and analytics</li>
          <li>• Set up integrations with your business systems</li>
          <li>• Review compliance requirements and settings</li>
        </ul>
      </div>
    </div>
  );

  if (!currentStepData) {
    return <div>Loading...</div>;
  }

  return (
    <div className={`max-w-2xl mx-auto ${className}`}>
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <div>
              <CardTitle>{currentStepData.title}</CardTitle>
              <CardDescription>{currentStepData.description}</CardDescription>
            </div>
            <div className="text-sm text-gray-500">
              Step {onboardingData.currentStep + 1} of {currentSteps.length}
            </div>
          </div>
          
          {/* Progress bar */}
          <div className="w-full bg-gray-200 rounded-full h-2 mt-4">
            <div
              className="bg-blue-600 h-2 rounded-full transition-all duration-300"
              style={{ width: `${((onboardingData.currentStep + 1) / currentSteps.length) * 100}%` }}
            />
          </div>
        </CardHeader>

        <CardContent className="space-y-6">
          {/* Step content */}
          {currentStepData.id === 'welcome' && renderWelcomeStep()}
          {currentStepData.id === 'company-profile' && renderCompanyProfileStep()}
          {currentStepData.id === 'service-setup' && renderServiceSetupStep()}
          {currentStepData.id === 'completion' && renderCompletionStep()}

          {/* Navigation buttons */}
          <div className="flex justify-between">
            <Button
              variant="outline"
              onClick={handleBack}
              disabled={onboardingData.currentStep === 0}
            >
              <ArrowLeft className="mr-2 h-4 w-4" />
              Back
            </Button>

            {onboardingData.currentStep < currentSteps.length - 1 ? (
              <Button onClick={handleNext}>
                Next
                <ArrowRight className="ml-2 h-4 w-4" />
              </Button>
            ) : (
              <Button onClick={handleComplete} loading={isLoading}>
                Complete Setup
                <CheckCircle className="ml-2 h-4 w-4" />
              </Button>
            )}
          </div>
        </CardContent>
      </Card>
    </div>
  );
};

export default OnboardingWizard;