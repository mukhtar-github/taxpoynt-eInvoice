/**
 * TaxPoynt Consent-Integrated Registration
 * =======================================
 * Strategic registration flow with integrated consent management.
 * Based on existing consent_manager.py and taxpayer_onboarding.py
 * 
 * User Flow: Registration Steps → Consent Integration → Service Selection
 * Follows Steve Jobs' principle: Consent at point-of-need, not separate consent center
 */

import React, { useState } from 'react';
import { Button } from '../../design_system/components/Button';
import { MonoConsentIntegration } from '../../si_interface/components/financial_systems/banking_integration/MonoConsentIntegration';

interface RegistrationStep {
  id: string;
  title: string;
  description: string;
  required: boolean;
}

interface ConsentItem {
  id: string;
  category: 'financial' | 'operational' | 'marketing' | 'analytics';
  title: string;
  description: string;
  required: boolean;
  legalBasis: string;
  dataTypes: string[];
  retentionPeriod: string;
  thirdParties?: string[];
}

// Based on existing consent_manager.py structure
const consentItems: ConsentItem[] = [
  {
    id: 'financial_data_access',
    category: 'financial',
    title: 'Financial System Data Access',
    description: 'Access to your ERP, accounting, and business system data for invoice generation and FIRS compliance.',
    required: true,
    legalBasis: 'Contract performance - Required for e-invoicing service delivery',
    dataTypes: ['Transaction records', 'Invoice data', 'Customer information', 'Product details'],
    retentionPeriod: '7 years (FIRS compliance requirement)',
    thirdParties: ['FIRS (Federal Inland Revenue Service)', 'Central Bank of Nigeria (for verification)']
  },
  {
    id: 'banking_integration_intent',
    category: 'financial',
    title: 'Banking Integration (Optional)',
    description: 'Intent to connect banking systems for automated transaction processing. Detailed banking consent will be requested separately.',
    required: false,
    legalBasis: 'Consent - Enhanced automation features',
    dataTypes: ['Banking integration preferences', 'Service configuration'],
    retentionPeriod: 'Duration of service agreement',
    thirdParties: ['Open Banking Providers (when selected)']
  },
  {
    id: 'compliance_monitoring',
    category: 'operational',
    title: 'Compliance Monitoring',
    description: 'Monitor your invoicing compliance status and provide automated FIRS submissions.',
    required: true,
    legalBasis: 'Legal obligation - FIRS e-invoicing compliance',
    dataTypes: ['Compliance status', 'Submission records', 'Audit trails'],
    retentionPeriod: '10 years (FIRS audit requirement)',
    thirdParties: ['FIRS (Federal Inland Revenue Service)']
  },
  {
    id: 'system_integration',
    category: 'operational',
    title: 'Business System Integration',
    description: 'Connect and synchronize data with your ERP, CRM, POS, and other business systems.',
    required: true,
    legalBasis: 'Contract performance - Core service functionality',
    dataTypes: ['System configurations', 'API credentials', 'Integration logs'],
    retentionPeriod: 'Duration of service agreement',
    thirdParties: ['Your selected ERP/CRM vendors (for data synchronization)']
  },
  {
    id: 'service_improvement',
    category: 'analytics',
    title: 'Service Improvement Analytics',
    description: 'Analyze usage patterns to improve our platform and provide better recommendations.',
    required: false,
    legalBasis: 'Legitimate interest - Service improvement',
    dataTypes: ['Usage analytics', 'Performance metrics', 'Feature utilization'],
    retentionPeriod: '2 years',
  },
  {
    id: 'marketing_communications',
    category: 'marketing',
    title: 'Marketing Communications',
    description: 'Receive updates about new features, Nigerian tax law changes, and TaxPoynt news.',
    required: false,
    legalBasis: 'Consent - Marketing communications',
    dataTypes: ['Contact preferences', 'Communication history'],
    retentionPeriod: 'Until consent withdrawn',
  }
];

const registrationSteps: RegistrationStep[] = [
  {
    id: 'company_info',
    title: 'Company Information',
    description: 'Basic company details and contact information',
    required: true
  },
  {
    id: 'business_details',
    title: 'Business Details',
    description: 'Industry, size, and business system information',
    required: true
  },
  {
    id: 'consent_management',
    title: 'Data & Privacy Consent',
    description: 'Control how TaxPoynt can access and use your data',
    required: true
  },
  {
    id: 'service_selection',
    title: 'Service Package',
    description: 'Choose your TaxPoynt service package',
    required: true
  }
];

interface ConsentIntegratedRegistrationProps {
  onRegistrationComplete: (registrationData: any) => void;
  onCancel: () => void;
  showBankingIntegration?: boolean;
}

export const ConsentIntegratedRegistration: React.FC<ConsentIntegratedRegistrationProps> = ({
  onRegistrationComplete,
  onCancel,
  showBankingIntegration = true
}) => {
  const [currentStep, setCurrentStep] = useState(0);
  const [formData, setFormData] = useState<any>({});
  const [consentChoices, setConsentChoices] = useState<Record<string, boolean>>({});
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [showBankingConsent, setShowBankingConsent] = useState(false);
  const [bankingConsentComplete, setBankingConsentComplete] = useState(false);

  // Initialize required consents
  React.useEffect(() => {
    const initialConsents: Record<string, boolean> = {};
    consentItems.forEach(item => {
      if (item.required) {
        initialConsents[item.id] = true; // Required consents are pre-checked
      } else {
        initialConsents[item.id] = false; // Optional consents start unchecked
      }
    });
    setConsentChoices(initialConsents);
  }, []);

  const handleNext = () => {
    if (currentStep < registrationSteps.length - 1) {
      setCurrentStep(currentStep + 1);
    } else {
      handleSubmit();
    }
  };

  const handlePrevious = () => {
    if (currentStep > 0) {
      setCurrentStep(currentStep - 1);
    }
  };

  const handleSubmit = async () => {
    // Check if banking integration was selected and needs consent
    if (consentChoices['banking_integration_intent'] && !bankingConsentComplete && showBankingIntegration) {
      setShowBankingConsent(true);
      return;
    }

    setIsSubmitting(true);
    
    try {
      // Strategic registration processing
      const registrationData = {
        ...formData,
        consentChoices,
        bankingIntegrationEnabled: consentChoices['banking_integration_intent'],
        bankingConsentComplete,
        timestamp: new Date().toISOString(),
        ndprCompliant: true
      };
      
      await new Promise(resolve => setTimeout(resolve, 2000)); // Simulate processing
      onRegistrationComplete(registrationData);
    } catch (error) {
      console.error('Registration failed:', error);
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleBankingConsentComplete = (consents: any) => {
    setBankingConsentComplete(true);
    setShowBankingConsent(false);
    // Continue with registration completion
    handleSubmit();
  };

  const handleMonoWidgetReady = (monoUrl: string) => {
    // Mono widget is ready - user will complete banking setup
    console.log('Mono widget ready:', monoUrl);
  };

  const renderCompanyInfoStep = () => (
    <div className="space-y-6">
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Company Name *
          </label>
          <input
            type="text"
            required
            className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
            placeholder="Enter your company name"
            value={formData.companyName || ''}
            onChange={(e) => setFormData({...formData, companyName: e.target.value})}
          />
        </div>
        
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            RC Number *
          </label>
          <input
            type="text"
            required
            className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
            placeholder="RC Number (CAC Registration)"
            value={formData.rcNumber || ''}
            onChange={(e) => setFormData({...formData, rcNumber: e.target.value})}
          />
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Business Email *
          </label>
          <input
            type="email"
            required
            className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
            placeholder="business@company.com"
            value={formData.email || ''}
            onChange={(e) => setFormData({...formData, email: e.target.value})}
          />
        </div>
        
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Phone Number *
          </label>
          <input
            type="tel"
            required
            className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
            placeholder="+234 800 000 0000"
            value={formData.phone || ''}
            onChange={(e) => setFormData({...formData, phone: e.target.value})}
          />
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
          placeholder="Complete business address"
          value={formData.address || ''}
          onChange={(e) => setFormData({...formData, address: e.target.value})}
        />
      </div>
    </div>
  );

  const renderBusinessDetailsStep = () => (
    <div className="space-y-6">
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Industry Sector *
          </label>
          <select
            required
            className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
            value={formData.industry || ''}
            onChange={(e) => setFormData({...formData, industry: e.target.value})}
          >
            <option value="">Select your industry</option>
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
            value={formData.companySize || ''}
            onChange={(e) => setFormData({...formData, companySize: e.target.value})}
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
          Current Business Systems
        </label>
        <p className="text-sm text-gray-600 mb-3">Select all systems you currently use:</p>
        <div className="grid grid-cols-2 md:grid-cols-3 gap-3">
          {['SAP', 'Oracle', 'QuickBooks', 'Sage', 'Odoo', 'Custom ERP', 'Excel/Manual', 'Other'].map((system) => (
            <label key={system} className="flex items-center">
              <input
                type="checkbox"
                className="h-4 w-4 text-blue-600 border-gray-300 rounded focus:ring-blue-500"
                checked={(formData.businessSystems || []).includes(system)}
                onChange={(e) => {
                  const systems = formData.businessSystems || [];
                  if (e.target.checked) {
                    setFormData({...formData, businessSystems: [...systems, system]});
                  } else {
                    setFormData({...formData, businessSystems: systems.filter((s: string) => s !== system)});
                  }
                }}
              />
              <span className="ml-2 text-sm text-gray-700">{system}</span>
            </label>
          ))}
        </div>
      </div>

      <div>
        <label className="block text-sm font-medium text-gray-700 mb-2">
          Monthly Invoice Volume (Estimate)
        </label>
        <select
          className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
          value={formData.invoiceVolume || ''}
          onChange={(e) => setFormData({...formData, invoiceVolume: e.target.value})}
        >
          <option value="">Select invoice volume</option>
          <option value="0-50">0-50 invoices/month</option>
          <option value="51-200">51-200 invoices/month</option>
          <option value="201-500">201-500 invoices/month</option>
          <option value="501-1000">501-1,000 invoices/month</option>
          <option value="1000+">1,000+ invoices/month</option>
        </select>
      </div>
    </div>
  );

  const renderConsentStep = () => (
    <div className="space-y-6">
      <div className="bg-blue-50 border border-blue-200 rounded-xl p-6 mb-6">
        <div className="flex items-start">
          <svg className="h-6 w-6 text-blue-600 mr-3 mt-1" fill="currentColor" viewBox="0 0 20 20">
            <path fillRule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7-4a1 1 0 11-2 0 1 1 0 012 0zM9 9a1 1 0 000 2v3a1 1 0 001 1h1a1 1 0 100-2v-3a1 1 0 00-1-1H9z" clipRule="evenodd" />
          </svg>
          <div>
            <h3 className="font-semibold text-blue-900 mb-2">Your Data, Your Control</h3>
            <p className="text-blue-800 text-sm">
              TaxPoynt follows strict NDPR (Nigerian Data Protection Regulation) compliance. 
              You control what data we can access and how we use it. Required permissions are 
              necessary for core e-invoicing functionality.
            </p>
          </div>
        </div>
      </div>

      <div className="space-y-4">
        {consentItems.map((item) => (
          <div key={item.id} className={`
            border rounded-xl p-6 transition-all
            ${item.required ? 'border-blue-200 bg-blue-50' : 'border-gray-200 bg-white'}
          `}>
            <div className="flex items-start justify-between">
              <div className="flex-1 mr-4">
                <div className="flex items-center mb-2">
                  <h4 className="font-semibold text-gray-900">{item.title}</h4>
                  {item.required && (
                    <span className="ml-2 px-2 py-1 text-xs font-medium bg-blue-100 text-blue-800 rounded-full">
                      Required
                    </span>
                  )}
                </div>
                <p className="text-gray-600 mb-3">{item.description}</p>
                
                <details className="text-sm text-gray-500">
                  <summary className="cursor-pointer hover:text-gray-700 font-medium">
                    View Privacy Details
                  </summary>
                  <div className="mt-2 space-y-2 pl-4 border-l-2 border-gray-200">
                    <div><strong>Legal Basis:</strong> {item.legalBasis}</div>
                    <div><strong>Data Types:</strong> {item.dataTypes.join(', ')}</div>
                    <div><strong>Retention:</strong> {item.retentionPeriod}</div>
                    {item.thirdParties && (
                      <div><strong>Shared With:</strong> {item.thirdParties.join(', ')}</div>
                    )}
                  </div>
                </details>
              </div>
              
              <label className="flex items-center cursor-pointer">
                <input
                  type="checkbox"
                  disabled={item.required}
                  checked={consentChoices[item.id] || false}
                  onChange={(e) => setConsentChoices({
                    ...consentChoices,
                    [item.id]: e.target.checked
                  })}
                  className="h-5 w-5 text-blue-600 border-gray-300 rounded focus:ring-blue-500 disabled:opacity-50"
                />
              </label>
            </div>
          </div>
        ))}
      </div>

      <div className="bg-gray-50 border border-gray-200 rounded-xl p-6">
        <h4 className="font-semibold text-gray-900 mb-2">Your Rights</h4>
        <div className="text-sm text-gray-600 space-y-1">
          <div>• <strong>Access:</strong> Request a copy of your personal data</div>
          <div>• <strong>Rectification:</strong> Correct inaccurate personal data</div>
          <div>• <strong>Erasure:</strong> Request deletion of your personal data</div>
          <div>• <strong>Portability:</strong> Transfer your data to another service</div>
          <div>• <strong>Withdraw Consent:</strong> Change your consent preferences anytime</div>
        </div>
        <p className="text-xs text-gray-500 mt-3">
          For data protection inquiries, contact: privacy@taxpoynt.com
        </p>
      </div>
    </div>
  );

  const currentStepData = registrationSteps[currentStep];

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Progress Header */}
      <div className="bg-white border-b border-gray-200">
        <div className="max-w-4xl mx-auto px-4 py-6">
          <div className="flex items-center justify-between mb-6">
            <h1 className="text-3xl font-bold text-gray-900">Join TaxPoynt</h1>
            <button
              onClick={onCancel}
              className="text-gray-500 hover:text-gray-700 transition-colors"
            >
              <svg className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
              </svg>
            </button>
          </div>
          
          {/* Progress Indicator */}
          <div className="flex items-center">
            {registrationSteps.map((step, index) => (
              <React.Fragment key={step.id}>
                <div className={`
                  flex items-center justify-center w-8 h-8 rounded-full text-sm font-medium
                  ${index <= currentStep 
                    ? 'bg-blue-600 text-white' 
                    : 'bg-gray-200 text-gray-500'
                  }
                `}>
                  {index + 1}
                </div>
                {index < registrationSteps.length - 1 && (
                  <div className={`
                    h-1 w-16 mx-2
                    ${index < currentStep ? 'bg-blue-600' : 'bg-gray-200'}
                  `} />
                )}
              </React.Fragment>
            ))}
          </div>
        </div>
      </div>

      {/* Step Content */}
      <div className="max-w-4xl mx-auto px-4 py-8">
        <div className="bg-white rounded-2xl border border-gray-200 p-8">
          <div className="mb-8">
            <h2 className="text-2xl font-bold text-gray-900 mb-2">{currentStepData.title}</h2>
            <p className="text-gray-600">{currentStepData.description}</p>
          </div>

          {/* Step Content */}
          {!showBankingConsent ? (
            <>
              {currentStep === 0 && renderCompanyInfoStep()}
              {currentStep === 1 && renderBusinessDetailsStep()}
              {currentStep === 2 && renderConsentStep()}
              {currentStep === 3 && (
                <div className="text-center py-12">
                  <div className="text-6xl mb-4">🎉</div>
                  <h3 className="text-2xl font-bold text-gray-900 mb-2">Almost Ready!</h3>
                  <p className="text-gray-600 mb-6">
                    {consentChoices['banking_integration_intent'] && showBankingIntegration
                      ? 'Complete banking integration to finish registration'
                      : 'Choose your service package to complete registration'
                    }
                  </p>
                </div>
              )}
            </>
          ) : (
            <div>
              <div className="mb-6">
                <h3 className="text-xl font-semibold text-gray-900 mb-2">
                  Banking Integration Setup
                </h3>
                <p className="text-gray-600">
                  You selected banking integration. Complete the banking consent process to continue.
                </p>
              </div>
              <MonoConsentIntegration
                existingConsents={consentChoices}
                onConsentUpdate={handleBankingConsentComplete}
                onMonoWidgetReady={handleMonoWidgetReady}
                compactMode={false}
              />
            </div>
          )}

          {/* Navigation */}
          {!showBankingConsent && (
            <div className="flex justify-between items-center mt-12 pt-6 border-t border-gray-200">
              <Button
                variant="outline"
                size="lg"
                onClick={handlePrevious}
                disabled={currentStep === 0}
              >
                Previous
              </Button>
              
              <Button
                variant="primary"
                size="lg"
                loading={isSubmitting}
                onClick={handleNext}
              >
                {currentStep === registrationSteps.length - 1 
                  ? (isSubmitting ? 'Creating Account...' : 'Complete Registration')
                  : 'Continue'
                }
              </Button>
            </div>
          )}
          
          {/* Banking Consent Navigation */}
          {showBankingConsent && (
            <div className="flex justify-between items-center mt-12 pt-6 border-t border-gray-200">
              <Button
                variant="outline"
                size="lg"
                onClick={() => {
                  setShowBankingConsent(false);
                  setConsentChoices({...consentChoices, 'banking_integration_intent': false});
                }}
              >
                Skip Banking Integration
              </Button>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};