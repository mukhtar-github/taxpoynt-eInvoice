/**
 * ERP Onboarding Workflow
 * =======================
 * 
 * System Integrator workflow for onboarding new organizations with ERP system integration.
 * Complete end-to-end process from organization setup to production deployment.
 * 
 * Features:
 * - Organization registration and verification
 * - ERP system selection and configuration
 * - Data mapping and validation
 * - Nigerian compliance setup (FIRS, VAT, CBN)
 * - Testing and production deployment
 * - Progress tracking and status updates
 */

import React, { useState, useEffect } from 'react';
import { Button } from '../../design_system/components/Button';

interface OnboardingStep {
  id: string;
  title: string;
  description: string;
  required: boolean;
  completed: boolean;
  estimatedDuration: string;
  dependencies?: string[];
}

interface OrganizationProfile {
  basicInfo: {
    name: string;
    rcNumber: string;
    tinNumber: string;
    email: string;
    phone: string;
    address: string;
    industry: string;
    size: string;
  };
  compliance: {
    vatRegistered: boolean;
    vatNumber?: string;
    firsRegistered: boolean;
    firsId?: string;
    cbnCompliant: boolean;
  };
  businessSystems: {
    primaryErp?: string;
    secondaryErp?: string;
    currentSoftware: string[];
    invoiceVolume: string;
    integrationRequirements: string[];
  };
}

interface ERPConfiguration {
  systemType: string;
  version?: string;
  credentials: {
    server?: string;
    database?: string;
    username?: string;
    apiKey?: string;
    oauthToken?: string;
  };
  dataSources: {
    customers: boolean;
    products: boolean;
    invoices: boolean;
    payments: boolean;
    inventory: boolean;
  };
  mappingRules: Array<{
    sourceField: string;
    targetField: string;
    transformation?: string;
  }>;
}

interface OnboardingProgress {
  organizationId: string;
  currentStep: number;
  stepsCompleted: string[];
  startDate: string;
  expectedCompletion?: string;
  actualCompletion?: string;
  assignedIntegrator?: string;
  notes: string[];
  issues: Array<{
    stepId: string;
    issue: string;
    severity: 'low' | 'medium' | 'high';
    resolved: boolean;
  }>;
}

const onboardingSteps: OnboardingStep[] = [
  {
    id: 'organization_setup',
    title: 'Organization Setup',
    description: 'Register organization and verify business credentials',
    required: true,
    completed: false,
    estimatedDuration: '30-45 minutes'
  },
  {
    id: 'compliance_verification',
    title: 'Compliance Verification',
    description: 'Verify FIRS registration, VAT status, and Nigerian compliance',
    required: true,
    completed: false,
    estimatedDuration: '20-30 minutes',
    dependencies: ['organization_setup']
  },
  {
    id: 'erp_selection',
    title: 'ERP System Selection',
    description: 'Choose and configure ERP system integration',
    required: true,
    completed: false,
    estimatedDuration: '15-30 minutes',
    dependencies: ['organization_setup']
  },
  {
    id: 'erp_configuration',
    title: 'ERP Configuration',
    description: 'Set up ERP credentials and connection parameters',
    required: true,
    completed: false,
    estimatedDuration: '45-60 minutes',
    dependencies: ['erp_selection']
  },
  {
    id: 'data_mapping',
    title: 'Data Mapping Setup',
    description: 'Configure data field mapping for FIRS compliance',
    required: true,
    completed: false,
    estimatedDuration: '60-90 minutes',
    dependencies: ['erp_configuration']
  },
  {
    id: 'testing_validation',
    title: 'Testing & Validation',
    description: 'Test integration and validate data flow',
    required: true,
    completed: false,
    estimatedDuration: '30-45 minutes',
    dependencies: ['data_mapping']
  },
  {
    id: 'compliance_setup',
    title: 'Compliance Configuration',
    description: 'Configure Nigerian tax compliance and FIRS integration',
    required: true,
    completed: false,
    estimatedDuration: '45-60 minutes',
    dependencies: ['testing_validation']
  },
  {
    id: 'production_deployment',
    title: 'Production Deployment',
    description: 'Deploy to production and activate live processing',
    required: true,
    completed: false,
    estimatedDuration: '15-30 minutes',
    dependencies: ['compliance_setup']
  },
  {
    id: 'training_handover',
    title: 'Training & Handover',
    description: 'Client training and system handover',
    required: true,
    completed: false,
    estimatedDuration: '60-90 minutes',
    dependencies: ['production_deployment']
  }
];

interface ERPOnboardingProps {
  organizationId?: string;
  onComplete?: (organizationId: string) => void;
}

export const ERPOnboarding: React.FC<ERPOnboardingProps> = ({
  organizationId,
  onComplete
}) => {
  const [currentStep, setCurrentStep] = useState(0);
  const [steps, setSteps] = useState<OnboardingStep[]>(onboardingSteps);
  const [organizationProfile, setOrganizationProfile] = useState<OrganizationProfile>({
    basicInfo: {
      name: '',
      rcNumber: '',
      tinNumber: '',
      email: '',
      phone: '',
      address: '',
      industry: '',
      size: ''
    },
    compliance: {
      vatRegistered: false,
      firsRegistered: false,
      cbnCompliant: false
    },
    businessSystems: {
      currentSoftware: [],
      invoiceVolume: '',
      integrationRequirements: []
    }
  });
  const [erpConfiguration, setErpConfiguration] = useState<ERPConfiguration>({
    systemType: '',
    credentials: {},
    dataSources: {
      customers: false,
      products: false,
      invoices: false,
      payments: false,
      inventory: false
    },
    mappingRules: []
  });
  const [progress, setProgress] = useState<OnboardingProgress | null>(null);
  const [isProcessing, setIsProcessing] = useState(false);
  const [testResults, setTestResults] = useState<any>(null);

  // Load existing onboarding progress
  useEffect(() => {
    if (organizationId) {
      loadOnboardingProgress();
    }
  }, [organizationId]);

  const loadOnboardingProgress = async () => {
    try {
      const response = await fetch(`/api/v1/si/onboarding/${organizationId}/progress`, {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('taxpoynt_auth_token')}`
        }
      });

      if (response.ok) {
        const data = await response.json();
        if (data.progress) {
          setProgress(data.progress);
          setCurrentStep(data.progress.currentStep);
          
          // Update step completion status
          setSteps(prev => prev.map(step => ({
            ...step,
            completed: data.progress.stepsCompleted.includes(step.id)
          })));
        }
      }
    } catch (error) {
      console.error('Failed to load onboarding progress:', error);
    }
  };

  const handleStepComplete = async () => {
    const stepId = steps[currentStep].id;
    
    try {
      setIsProcessing(true);
      
      // Save step completion
      const response = await fetch(`/api/v1/si/onboarding/${organizationId}/step-complete`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('taxpoynt_auth_token')}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          step_id: stepId,
          step_data: getCurrentStepData(),
          organization_profile: organizationProfile,
          erp_configuration: erpConfiguration
        })
      });

      if (response.ok) {
        // Update local state
        setSteps(prev => prev.map((step, index) => 
          index === currentStep ? { ...step, completed: true } : step
        ));

        alert(`✅ ${steps[currentStep].title} completed successfully!`);
      } else {
        alert('❌ Failed to save step progress');
      }
    } catch (error) {
      console.error('Failed to complete step:', error);
      alert('❌ Failed to complete step');
    } finally {
      setIsProcessing(false);
    }
  };

  const getCurrentStepData = () => {
    switch (steps[currentStep].id) {
      case 'organization_setup':
        return { organization_profile: organizationProfile.basicInfo };
      case 'compliance_verification':
        return { compliance: organizationProfile.compliance };
      case 'erp_selection':
      case 'erp_configuration':
        return { erp_configuration: erpConfiguration };
      case 'data_mapping':
        return { mapping_rules: erpConfiguration.mappingRules };
      case 'testing_validation':
        return { test_results: testResults };
      default:
        return {};
    }
  };

  const handleNext = () => {
    if (currentStep < steps.length - 1) {
      setCurrentStep(currentStep + 1);
    } else {
      handleComplete();
    }
  };

  const handlePrevious = () => {
    if (currentStep > 0) {
      setCurrentStep(currentStep - 1);
    }
  };

  const handleComplete = async () => {
    try {
      setIsProcessing(true);

      const response = await fetch(`/api/v1/si/onboarding/${organizationId}/complete`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('taxpoynt_auth_token')}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          organization_profile: organizationProfile,
          erp_configuration: erpConfiguration,
          completion_date: new Date().toISOString()
        })
      });

      if (response.ok) {
        alert('🎉 ERP onboarding completed successfully!');
        if (onComplete && organizationId) {
          onComplete(organizationId);
        }
      } else {
        alert('❌ Failed to complete onboarding');
      }
    } catch (error) {
      console.error('Failed to complete onboarding:', error);
      alert('❌ Failed to complete onboarding');
    } finally {
      setIsProcessing(false);
    }
  };

  const renderOrganizationSetup = () => (
    <div className="space-y-6">
      <div className="bg-blue-50 border border-blue-200 rounded-lg p-4 mb-6">
        <h3 className="font-semibold text-blue-900 mb-2">🏢 Organization Registration</h3>
        <p className="text-blue-800 text-sm">
          Register the organization and verify business credentials for Nigerian compliance.
        </p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Company Name *
          </label>
          <input
            type="text"
            required
            className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
            value={organizationProfile.basicInfo.name}
            onChange={(e) => setOrganizationProfile(prev => ({
              ...prev,
              basicInfo: { ...prev.basicInfo, name: e.target.value }
            }))}
          />
        </div>
        
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            RC Number (CAC) *
          </label>
          <input
            type="text"
            required
            className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
            value={organizationProfile.basicInfo.rcNumber}
            onChange={(e) => setOrganizationProfile(prev => ({
              ...prev,
              basicInfo: { ...prev.basicInfo, rcNumber: e.target.value }
            }))}
          />
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            TIN Number *
          </label>
          <input
            type="text"
            required
            className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
            value={organizationProfile.basicInfo.tinNumber}
            onChange={(e) => setOrganizationProfile(prev => ({
              ...prev,
              basicInfo: { ...prev.basicInfo, tinNumber: e.target.value }
            }))}
          />
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Business Email *
          </label>
          <input
            type="email"
            required
            className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
            value={organizationProfile.basicInfo.email}
            onChange={(e) => setOrganizationProfile(prev => ({
              ...prev,
              basicInfo: { ...prev.basicInfo, email: e.target.value }
            }))}
          />
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Industry Sector *
          </label>
          <select
            required
            className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
            value={organizationProfile.basicInfo.industry}
            onChange={(e) => setOrganizationProfile(prev => ({
              ...prev,
              basicInfo: { ...prev.basicInfo, industry: e.target.value }
            }))}
          >
            <option value="">Select industry</option>
            <option value="manufacturing">Manufacturing</option>
            <option value="retail">Retail & E-commerce</option>
            <option value="services">Professional Services</option>
            <option value="technology">Technology</option>
            <option value="healthcare">Healthcare</option>
            <option value="education">Education</option>
            <option value="hospitality">Hospitality</option>
            <option value="construction">Construction</option>
            <option value="agriculture">Agriculture</option>
            <option value="other">Other</option>
          </select>
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Company Size *
          </label>
          <select
            required
            className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
            value={organizationProfile.basicInfo.size}
            onChange={(e) => setOrganizationProfile(prev => ({
              ...prev,
              basicInfo: { ...prev.basicInfo, size: e.target.value }
            }))}
          >
            <option value="">Select company size</option>
            <option value="startup">Startup (1-10 employees)</option>
            <option value="small">Small (11-50 employees)</option>
            <option value="medium">Medium (51-200 employees)</option>
            <option value="large">Large (201-1000 employees)</option>
            <option value="enterprise">Enterprise (1000+ employees)</option>
          </select>
        </div>
      </div>

      <div>
        <label className="block text-sm font-medium text-gray-700 mb-2">
          Business Address *
        </label>
        <textarea
          required
          rows={3}
          className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
          value={organizationProfile.basicInfo.address}
          onChange={(e) => setOrganizationProfile(prev => ({
            ...prev,
            basicInfo: { ...prev.basicInfo, address: e.target.value }
          }))}
        />
      </div>
    </div>
  );

  const renderComplianceVerification = () => (
    <div className="space-y-6">
      <div className="bg-green-50 border border-green-200 rounded-lg p-4 mb-6">
        <h3 className="font-semibold text-green-900 mb-2">🇳🇬 Nigerian Compliance Verification</h3>
        <p className="text-green-800 text-sm">
          Verify FIRS registration, VAT status, and other Nigerian regulatory requirements.
        </p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <div className="border rounded-lg p-4">
          <h4 className="font-semibold text-gray-900 mb-3">FIRS Registration</h4>
          <div className="space-y-3">
            <label className="flex items-center">
              <input
                type="checkbox"
                checked={organizationProfile.compliance.firsRegistered}
                onChange={(e) => setOrganizationProfile(prev => ({
                  ...prev,
                  compliance: { ...prev.compliance, firsRegistered: e.target.checked }
                }))}
                className="h-4 w-4 text-blue-600 border-gray-300 rounded focus:ring-blue-500"
              />
              <span className="ml-2 text-gray-700">Organization is registered with FIRS</span>
            </label>
            
            {organizationProfile.compliance.firsRegistered && (
              <input
                type="text"
                placeholder="FIRS ID"
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                value={organizationProfile.compliance.firsId || ''}
                onChange={(e) => setOrganizationProfile(prev => ({
                  ...prev,
                  compliance: { ...prev.compliance, firsId: e.target.value }
                }))}
              />
            )}
          </div>
        </div>

        <div className="border rounded-lg p-4">
          <h4 className="font-semibold text-gray-900 mb-3">VAT Registration</h4>
          <div className="space-y-3">
            <label className="flex items-center">
              <input
                type="checkbox"
                checked={organizationProfile.compliance.vatRegistered}
                onChange={(e) => setOrganizationProfile(prev => ({
                  ...prev,
                  compliance: { ...prev.compliance, vatRegistered: e.target.checked }
                }))}
                className="h-4 w-4 text-blue-600 border-gray-300 rounded focus:ring-blue-500"
              />
              <span className="ml-2 text-gray-700">Organization is VAT registered</span>
            </label>
            
            {organizationProfile.compliance.vatRegistered && (
              <input
                type="text"
                placeholder="VAT Number"
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                value={organizationProfile.compliance.vatNumber || ''}
                onChange={(e) => setOrganizationProfile(prev => ({
                  ...prev,
                  compliance: { ...prev.compliance, vatNumber: e.target.value }
                }))}
              />
            )}
          </div>
        </div>

        <div className="border rounded-lg p-4">
          <h4 className="font-semibold text-gray-900 mb-3">CBN Compliance</h4>
          <label className="flex items-center">
            <input
              type="checkbox"
              checked={organizationProfile.compliance.cbnCompliant}
              onChange={(e) => setOrganizationProfile(prev => ({
                ...prev,
                compliance: { ...prev.compliance, cbnCompliant: e.target.checked }
              }))}
              className="h-4 w-4 text-blue-600 border-gray-300 rounded focus:ring-blue-500"
            />
            <span className="ml-2 text-gray-700">Compliant with CBN regulations</span>
          </label>
        </div>

        <div className="border rounded-lg p-4">
          <h4 className="font-semibold text-gray-900 mb-3">Invoice Volume</h4>
          <select
            className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
            value={organizationProfile.businessSystems.invoiceVolume}
            onChange={(e) => setOrganizationProfile(prev => ({
              ...prev,
              businessSystems: { ...prev.businessSystems, invoiceVolume: e.target.value }
            }))}
          >
            <option value="">Select monthly invoice volume</option>
            <option value="0-50">0-50 invoices/month</option>
            <option value="51-200">51-200 invoices/month</option>
            <option value="201-500">201-500 invoices/month</option>
            <option value="501-1000">501-1,000 invoices/month</option>
            <option value="1000+">1,000+ invoices/month</option>
          </select>
        </div>
      </div>
    </div>
  );

  const renderERPSelection = () => (
    <div className="space-y-6">
      <div className="bg-purple-50 border border-purple-200 rounded-lg p-4 mb-6">
        <h3 className="font-semibold text-purple-900 mb-2">🔧 ERP System Selection</h3>
        <p className="text-purple-800 text-sm">
          Choose the primary ERP system for integration with TaxPoynt e-invoicing.
        </p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {[
          { id: 'sap', name: 'SAP', icon: '🏢', description: 'SAP ERP, S/4HANA, Business One' },
          { id: 'oracle', name: 'Oracle ERP', icon: '🔴', description: 'Oracle ERP Cloud, E-Business Suite' },
          { id: 'dynamics', name: 'Microsoft Dynamics', icon: '🔷', description: 'Dynamics 365, NAV, GP' },
          { id: 'netsuite', name: 'NetSuite', icon: '🌐', description: 'Oracle NetSuite ERP' },
          { id: 'odoo', name: 'Odoo', icon: '🟣', description: 'Odoo Community & Enterprise' },
          { id: 'custom', name: 'Custom ERP', icon: '⚙️', description: 'Custom or proprietary ERP system' }
        ].map(erp => (
          <div
            key={erp.id}
            className={`border-2 rounded-lg p-4 cursor-pointer transition-all ${
              erpConfiguration.systemType === erp.id
                ? 'border-blue-500 bg-blue-50'
                : 'border-gray-200 hover:border-gray-300'
            }`}
            onClick={() => setErpConfiguration(prev => ({ ...prev, systemType: erp.id }))}
          >
            <div className="text-center">
              <div className="text-3xl mb-2">{erp.icon}</div>
              <h4 className="font-semibold text-gray-900">{erp.name}</h4>
              <p className="text-sm text-gray-600 mt-1">{erp.description}</p>
            </div>
          </div>
        ))}
      </div>

      {erpConfiguration.systemType && (
        <div className="bg-gray-50 rounded-lg p-4">
          <h4 className="font-semibold text-gray-900 mb-3">Selected: {erpConfiguration.systemType.toUpperCase()}</h4>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                System Version
              </label>
              <input
                type="text"
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                placeholder="e.g., S/4HANA 2021"
                value={erpConfiguration.version || ''}
                onChange={(e) => setErpConfiguration(prev => ({ ...prev, version: e.target.value }))}
              />
            </div>
            
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Implementation Status
              </label>
              <select className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500">
                <option value="">Select status</option>
                <option value="live">Live/Production</option>
                <option value="testing">Testing Phase</option>
                <option value="implementation">Under Implementation</option>
                <option value="planning">Planning Phase</option>
              </select>
            </div>
          </div>
        </div>
      )}
    </div>
  );

  const renderStepContent = () => {
    switch (steps[currentStep].id) {
      case 'organization_setup':
        return renderOrganizationSetup();
      case 'compliance_verification':
        return renderComplianceVerification();
      case 'erp_selection':
        return renderERPSelection();
      case 'erp_configuration':
        return (
          <div className="text-center py-12">
            <div className="text-4xl mb-4">⚙️</div>
            <h3 className="text-xl font-semibold text-gray-900 mb-2">ERP Configuration</h3>
            <p className="text-gray-600 mb-6">Set up ERP system credentials and connection parameters</p>
            <Button onClick={() => window.location.href = '/si/integration-setup'}>
              Open Integration Setup
            </Button>
          </div>
        );
      case 'data_mapping':
        return (
          <div className="text-center py-12">
            <div className="text-4xl mb-4">🔄</div>
            <h3 className="text-xl font-semibold text-gray-900 mb-2">Data Mapping</h3>
            <p className="text-gray-600 mb-6">Configure data field mapping for FIRS compliance</p>
            <Button onClick={() => window.location.href = '/si/data-mapping'}>
              Open Data Mapping Tool
            </Button>
          </div>
        );
      case 'testing_validation':
        return (
          <div className="text-center py-12">
            <div className="text-4xl mb-4">🧪</div>
            <h3 className="text-xl font-semibold text-gray-900 mb-2">Testing & Validation</h3>
            <p className="text-gray-600 mb-6">Test integration and validate data flow</p>
            <div className="space-y-4">
              <Button>Run Connection Test</Button>
              <Button variant="outline">Validate Sample Data</Button>
            </div>
          </div>
        );
      default:
        return (
          <div className="text-center py-12">
            <div className="text-4xl mb-4">⚠️</div>
            <h3 className="text-xl font-semibold text-gray-900 mb-2">{steps[currentStep].title}</h3>
            <p className="text-gray-600">{steps[currentStep].description}</p>
          </div>
        );
    }
  };

  const currentStepData = steps[currentStep];
  const canProceed = currentStepData?.completed || false;

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <div className="bg-white border-b">
        <div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-3xl font-bold text-gray-900">ERP Onboarding Workflow</h1>
              <p className="text-gray-600 mt-2">Complete organization setup and ERP integration</p>
            </div>
            <div className="text-sm text-gray-500">
              Step {currentStep + 1} of {steps.length}
            </div>
          </div>
        </div>
      </div>

      {/* Progress Steps */}
      <div className="bg-white border-b">
        <div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
          <div className="flex items-center overflow-x-auto pb-2">
            {steps.map((step, index) => (
              <React.Fragment key={step.id}>
                <div className={`flex items-center ${index <= currentStep ? 'text-blue-600' : 'text-gray-400'} whitespace-nowrap`}>
                  <div className={`
                    flex items-center justify-center w-8 h-8 rounded-full text-sm font-medium flex-shrink-0
                    ${index <= currentStep ? 'bg-blue-600 text-white' : 'bg-gray-200 text-gray-500'}
                  `}>
                    {step.completed ? '✓' : index + 1}
                  </div>
                  <div className="ml-2">
                    <div className="text-sm font-medium">{step.title}</div>
                    <div className="text-xs text-gray-500">{step.estimatedDuration}</div>
                  </div>
                </div>
                {index < steps.length - 1 && (
                  <div className={`h-1 w-8 mx-4 flex-shrink-0 ${index < currentStep ? 'bg-blue-600' : 'bg-gray-200'}`} />
                )}
              </React.Fragment>
            ))}
          </div>
        </div>
      </div>

      {/* Main Content */}
      <div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="bg-white rounded-lg border p-8">
          <div className="mb-6">
            <h2 className="text-xl font-semibold text-gray-900 mb-2">{currentStepData?.title}</h2>
            <p className="text-gray-600">{currentStepData?.description}</p>
            <div className="text-sm text-gray-500 mt-1">
              Estimated time: {currentStepData?.estimatedDuration}
            </div>
          </div>

          {renderStepContent()}

          {/* Navigation */}
          <div className="flex items-center justify-between mt-8 pt-6 border-t">
            <Button
              onClick={handlePrevious}
              disabled={currentStep === 0}
              variant="outline"
            >
              Previous
            </Button>

            <div className="flex items-center space-x-4">
              {!currentStepData?.completed && (
                <Button
                  onClick={handleStepComplete}
                  disabled={isProcessing}
                  variant="outline"
                  loading={isProcessing}
                >
                  Mark Complete
                </Button>
              )}
              
              <Button
                onClick={handleNext}
                disabled={!canProceed || isProcessing}
                loading={currentStep === steps.length - 1 && isProcessing}
              >
                {currentStep === steps.length - 1 ? 'Complete Onboarding' : 'Continue'}
              </Button>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default ERPOnboarding;