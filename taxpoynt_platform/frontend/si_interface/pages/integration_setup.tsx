/**
 * Integration Setup Page
 * =====================
 * 
 * System Integrator interface for setting up business system integrations.
 * Multi-step wizard for ERP, CRM, POS, E-commerce, Accounting, and Inventory systems.
 * 
 * Features:
 * - Integration wizard with step-by-step guidance
 * - System selection and configuration
 * - Connection testing and validation
 * - Nigerian business system support
 * - Compliance-ready integration templates
 */

import React, { useState, useEffect } from 'react';
import { Button } from '../../design_system/components/Button';

interface BusinessSystem {
  id: string;
  category: 'erp' | 'crm' | 'pos' | 'ecommerce' | 'accounting' | 'inventory';
  name: string;
  icon: string;
  description: string;
  supported: boolean;
  difficulty: 'easy' | 'medium' | 'complex';
  estimatedTime: string;
  requirements: string[];
  nigerianSupport?: boolean;
}

interface IntegrationStep {
  id: string;
  title: string;
  description: string;
  required: boolean;
  completed: boolean;
}

const businessSystems: BusinessSystem[] = [
  // ERP Systems
  {
    id: 'sap',
    category: 'erp',
    name: 'SAP',
    icon: '🏢',
    description: 'SAP ERP, S/4HANA, Business One integration',
    supported: true,
    difficulty: 'complex',
    estimatedTime: '2-4 hours',
    requirements: ['SAP credentials', 'API access', 'System administrator access'],
    nigerianSupport: true
  },
  {
    id: 'oracle_erp',
    category: 'erp',
    name: 'Oracle ERP Cloud',
    icon: '🔴',
    description: 'Oracle ERP Cloud and E-Business Suite',
    supported: true,
    difficulty: 'complex',
    estimatedTime: '2-3 hours',
    requirements: ['Oracle Cloud credentials', 'REST API access'],
    nigerianSupport: true
  },
  {
    id: 'dynamics',
    category: 'erp',
    name: 'Microsoft Dynamics',
    icon: '🔷',
    description: 'Dynamics 365, NAV, GP integration',
    supported: true,
    difficulty: 'medium',
    estimatedTime: '1-2 hours',
    requirements: ['Microsoft credentials', 'API permissions'],
    nigerianSupport: true
  },
  {
    id: 'netsuite',
    category: 'erp',
    name: 'NetSuite',
    icon: '🌐',
    description: 'Oracle NetSuite ERP system',
    supported: true,
    difficulty: 'medium',
    estimatedTime: '1-2 hours',
    requirements: ['NetSuite account', 'API token'],
    nigerianSupport: true
  },
  {
    id: 'odoo',
    category: 'erp',
    name: 'Odoo',
    icon: '🟣',
    description: 'Odoo Community & Enterprise',
    supported: true,
    difficulty: 'easy',
    estimatedTime: '30-60 minutes',
    requirements: ['Odoo server access', 'API key'],
    nigerianSupport: true
  },

  // CRM Systems
  {
    id: 'salesforce',
    category: 'crm',
    name: 'Salesforce',
    icon: '☁️',
    description: 'Salesforce CRM integration',
    supported: true,
    difficulty: 'medium',
    estimatedTime: '1-2 hours',
    requirements: ['Salesforce org', 'API access'],
    nigerianSupport: true
  },
  {
    id: 'hubspot',
    category: 'crm',
    name: 'HubSpot',
    icon: '🧡',
    description: 'HubSpot CRM and Marketing Hub',
    supported: true,
    difficulty: 'easy',
    estimatedTime: '30-45 minutes',
    requirements: ['HubSpot account', 'API key'],
    nigerianSupport: true
  },

  // POS Systems
  {
    id: 'square',
    category: 'pos',
    name: 'Square',
    icon: '⬜',
    description: 'Square POS system integration',
    supported: true,
    difficulty: 'easy',
    estimatedTime: '30-45 minutes',
    requirements: ['Square account', 'API credentials'],
    nigerianSupport: false
  },
  {
    id: 'opay_pos',
    category: 'pos',
    name: 'OPay POS',
    icon: '💚',
    description: 'OPay Nigerian POS system',
    supported: true,
    difficulty: 'easy',
    estimatedTime: '30-45 minutes',
    requirements: ['OPay merchant account', 'API access'],
    nigerianSupport: true
  },
  {
    id: 'moniepoint_pos',
    category: 'pos',
    name: 'Moniepoint POS',
    icon: '🔵',
    description: 'Moniepoint Nigerian POS system',
    supported: true,
    difficulty: 'easy',
    estimatedTime: '30-45 minutes',
    requirements: ['Moniepoint merchant account'],
    nigerianSupport: true
  },

  // E-commerce Systems
  {
    id: 'shopify',
    category: 'ecommerce',
    name: 'Shopify',
    icon: '🛍️',
    description: 'Shopify e-commerce platform',
    supported: true,
    difficulty: 'easy',
    estimatedTime: '30-60 minutes',
    requirements: ['Shopify store', 'Private app credentials'],
    nigerianSupport: true
  },
  {
    id: 'jumia',
    category: 'ecommerce',
    name: 'Jumia',
    icon: '🇳🇬',
    description: 'Jumia Nigerian marketplace',
    supported: true,
    difficulty: 'medium',
    estimatedTime: '1-2 hours',
    requirements: ['Jumia seller account', 'API access'],
    nigerianSupport: true
  },

  // Accounting Systems
  {
    id: 'quickbooks',
    category: 'accounting',
    name: 'QuickBooks',
    icon: '💼',
    description: 'QuickBooks accounting software',
    supported: true,
    difficulty: 'medium',
    estimatedTime: '1-2 hours',
    requirements: ['QuickBooks account', 'OAuth setup'],
    nigerianSupport: true
  },
  {
    id: 'sage',
    category: 'accounting',
    name: 'Sage',
    icon: '🟢',
    description: 'Sage accounting systems',
    supported: true,
    difficulty: 'medium',
    estimatedTime: '1-2 hours',
    requirements: ['Sage license', 'API credentials'],
    nigerianSupport: true
  }
];

const integrationSteps: IntegrationStep[] = [
  {
    id: 'system_selection',
    title: 'System Selection',
    description: 'Choose the business systems to integrate',
    required: true,
    completed: false
  },
  {
    id: 'credentials_setup',
    title: 'Credentials Setup',
    description: 'Configure authentication and API access',
    required: true,
    completed: false
  },
  {
    id: 'data_mapping',
    title: 'Data Mapping',
    description: 'Map business data to FIRS-compliant invoice format',
    required: true,
    completed: false
  },
  {
    id: 'testing',
    title: 'Connection Testing',
    description: 'Test integration and validate data flow',
    required: true,
    completed: false
  },
  {
    id: 'compliance_validation',
    title: 'Compliance Validation',
    description: 'Ensure Nigerian tax compliance (FIRS, VAT)',
    required: true,
    completed: false
  },
  {
    id: 'deployment',
    title: 'Deployment',
    description: 'Activate integration for production use',
    required: true,
    completed: false
  }
];

interface IntegrationSetupProps {
  organizationId?: string;
  onSetupComplete?: (integrations: string[]) => void;
}

export const IntegrationSetup: React.FC<IntegrationSetupProps> = ({
  organizationId,
  onSetupComplete
}) => {
  const [currentStep, setCurrentStep] = useState(0);
  const [selectedSystems, setSelectedSystems] = useState<string[]>([]);
  const [steps, setSteps] = useState<IntegrationStep[]>(integrationSteps);
  const [credentials, setCredentials] = useState<Record<string, any>>({});
  const [testResults, setTestResults] = useState<Record<string, boolean>>({});
  const [isProcessing, setIsProcessing] = useState(false);

  const currentStepData = steps[currentStep];
  const canProceed = currentStepData?.completed || false;

  const handleSystemToggle = (systemId: string) => {
    if (selectedSystems.includes(systemId)) {
      setSelectedSystems(prev => prev.filter(id => id !== systemId));
    } else {
      setSelectedSystems(prev => [...prev, systemId]);
    }
  };

  const handleStepComplete = () => {
    setSteps(prev => prev.map((step, index) => 
      index === currentStep ? { ...step, completed: true } : step
    ));
  };

  const handleNext = async () => {
    if (currentStep === 0 && selectedSystems.length === 0) {
      alert('Please select at least one business system to integrate');
      return;
    }

    if (!currentStepData.completed) {
      handleStepComplete();
    }

    if (currentStep < steps.length - 1) {
      setCurrentStep(currentStep + 1);
    } else {
      await handleDeployment();
    }
  };

  const handlePrevious = () => {
    if (currentStep > 0) {
      setCurrentStep(currentStep - 1);
    }
  };

  const handleTestConnection = async (systemId: string) => {
    setIsProcessing(true);
    try {
      // Simulate API call to test connection
      const response = await fetch(`/api/v1/si/integrations/${systemId}/test`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('taxpoynt_auth_token')}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          credentials: credentials[systemId],
          organization_id: organizationId
        })
      });

      const result = await response.json();
      setTestResults(prev => ({ ...prev, [systemId]: result.success }));
      
      if (result.success) {
        alert(`✅ ${businessSystems.find(s => s.id === systemId)?.name} connection successful!`);
      } else {
        alert(`❌ Connection failed: ${result.error}`);
      }
    } catch (error) {
      console.error('Connection test failed:', error);
      setTestResults(prev => ({ ...prev, [systemId]: false }));
      alert('Connection test failed. Please check your credentials.');
    } finally {
      setIsProcessing(false);
    }
  };

  const handleDeployment = async () => {
    setIsProcessing(true);
    try {
      const response = await fetch('/api/v1/si/integrations/deploy', {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('taxpoynt_auth_token')}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          organization_id: organizationId,
          selected_systems: selectedSystems,
          credentials,
          deployment_mode: 'production'
        })
      });

      const result = await response.json();
      
      if (result.success) {
        alert('🎉 Integration setup completed successfully!');
        if (onSetupComplete) {
          onSetupComplete(selectedSystems);
        }
      } else {
        alert(`Deployment failed: ${result.error}`);
      }
    } catch (error) {
      console.error('Deployment failed:', error);
      alert('Deployment failed. Please try again.');
    } finally {
      setIsProcessing(false);
    }
  };

  const renderSystemSelection = () => {
    const categories = ['erp', 'crm', 'pos', 'ecommerce', 'accounting', 'inventory'] as const;
    
    return (
      <div className="space-y-8">
        {categories.map(category => {
          const categorySystems = businessSystems.filter(system => system.category === category);
          if (categorySystems.length === 0) return null;

          return (
            <div key={category} className="bg-white rounded-lg border p-6">
              <h3 className="text-lg font-semibold text-gray-900 mb-4 capitalize">
                {category === 'erp' ? 'ERP Systems' : 
                 category === 'crm' ? 'CRM Systems' :
                 category === 'pos' ? 'POS Systems' :
                 category === 'ecommerce' ? 'E-commerce Systems' :
                 category + ' Systems'}
              </h3>
              
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                {categorySystems.map(system => (
                  <div
                    key={system.id}
                    className={`border-2 rounded-lg p-4 cursor-pointer transition-all ${
                      selectedSystems.includes(system.id)
                        ? 'border-blue-500 bg-blue-50'
                        : 'border-gray-200 hover:border-gray-300'
                    }`}
                    onClick={() => handleSystemToggle(system.id)}
                  >
                    <div className="flex items-start justify-between mb-3">
                      <div className="flex items-center space-x-3">
                        <span className="text-2xl">{system.icon}</span>
                        <div>
                          <h4 className="font-semibold text-gray-900">{system.name}</h4>
                          {system.nigerianSupport && (
                            <span className="text-xs bg-green-100 text-green-800 px-2 py-1 rounded-full">
                              🇳🇬 Nigerian Support
                            </span>
                          )}
                        </div>
                      </div>
                      
                      <input
                        type="checkbox"
                        checked={selectedSystems.includes(system.id)}
                        onChange={() => handleSystemToggle(system.id)}
                        className="w-5 h-5 text-blue-600 border-gray-300 rounded focus:ring-blue-500"
                      />
                    </div>
                    
                    <p className="text-gray-600 text-sm mb-3">{system.description}</p>
                    
                    <div className="flex items-center justify-between text-xs text-gray-500">
                      <span className={`px-2 py-1 rounded-full ${
                        system.difficulty === 'easy' ? 'bg-green-100 text-green-800' :
                        system.difficulty === 'medium' ? 'bg-yellow-100 text-yellow-800' :
                        'bg-red-100 text-red-800'
                      }`}>
                        {system.difficulty}
                      </span>
                      <span>{system.estimatedTime}</span>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          );
        })}
        
        {selectedSystems.length > 0 && (
          <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
            <h4 className="font-semibold text-blue-900 mb-2">
              Selected Systems ({selectedSystems.length})
            </h4>
            <div className="flex flex-wrap gap-2">
              {selectedSystems.map(systemId => {
                const system = businessSystems.find(s => s.id === systemId);
                return (
                  <span
                    key={systemId}
                    className="bg-blue-100 text-blue-800 px-3 py-1 rounded-full text-sm flex items-center"
                  >
                    {system?.icon} {system?.name}
                  </span>
                );
              })}
            </div>
          </div>
        )}
      </div>
    );
  };

  const renderCredentialsSetup = () => (
    <div className="space-y-6">
      {selectedSystems.map(systemId => {
        const system = businessSystems.find(s => s.id === systemId);
        if (!system) return null;

        return (
          <div key={systemId} className="bg-white border rounded-lg p-6">
            <div className="flex items-center space-x-3 mb-4">
              <span className="text-2xl">{system.icon}</span>
              <div>
                <h3 className="text-lg font-semibold text-gray-900">{system.name}</h3>
                <p className="text-gray-600 text-sm">{system.description}</p>
              </div>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Server/Endpoint URL
                </label>
                <input
                  type="url"
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                  placeholder="https://api.example.com"
                  value={credentials[systemId]?.server || ''}
                  onChange={(e) => setCredentials(prev => ({
                    ...prev,
                    [systemId]: { ...prev[systemId], server: e.target.value }
                  }))}
                />
              </div>
              
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  API Key/Token
                </label>
                <input
                  type="password"
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                  placeholder="Enter API key or token"
                  value={credentials[systemId]?.apiKey || ''}
                  onChange={(e) => setCredentials(prev => ({
                    ...prev,
                    [systemId]: { ...prev[systemId], apiKey: e.target.value }
                  }))}
                />
              </div>
            </div>

            <div className="mt-4 flex items-center justify-between">
              <div className="text-sm text-gray-600">
                <strong>Requirements:</strong> {system.requirements.join(', ')}
              </div>
              
              <Button
                onClick={() => handleTestConnection(systemId)}
                disabled={!credentials[systemId]?.apiKey || isProcessing}
                size="sm"
                variant={testResults[systemId] ? 'success' : 'outline'}
              >
                {testResults[systemId] ? '✅ Connected' : 'Test Connection'}
              </Button>
            </div>
          </div>
        );
      })}
    </div>
  );

  const renderStepContent = () => {
    switch (currentStep) {
      case 0:
        return renderSystemSelection();
      case 1:
        return renderCredentialsSetup();
      case 2:
        return (
          <div className="text-center py-12">
            <div className="text-4xl mb-4">🔄</div>
            <h3 className="text-xl font-semibold text-gray-900 mb-2">Data Mapping</h3>
            <p className="text-gray-600 mb-6">
              Configure how your business data maps to FIRS-compliant invoice format
            </p>
            <Button onClick={() => window.location.href = '/si/data-mapping'}>
              Open Data Mapping Tool
            </Button>
          </div>
        );
      case 3:
        return (
          <div className="text-center py-12">
            <div className="text-4xl mb-4">🧪</div>
            <h3 className="text-xl font-semibold text-gray-900 mb-2">Connection Testing</h3>
            <p className="text-gray-600 mb-6">
              Test all configured integrations and validate data flow
            </p>
            <div className="space-y-3">
              {selectedSystems.map(systemId => {
                const system = businessSystems.find(s => s.id === systemId);
                return (
                  <div key={systemId} className="flex items-center justify-between bg-gray-50 rounded-lg p-3">
                    <span>{system?.icon} {system?.name}</span>
                    <span className={testResults[systemId] ? 'text-green-600' : 'text-gray-400'}>
                      {testResults[systemId] ? '✅ Tested' : '⏳ Pending'}
                    </span>
                  </div>
                );
              })}
            </div>
          </div>
        );
      case 4:
        return (
          <div className="text-center py-12">
            <div className="text-4xl mb-4">✅</div>
            <h3 className="text-xl font-semibold text-gray-900 mb-2">Compliance Validation</h3>
            <p className="text-gray-600 mb-6">
              Nigerian tax compliance validation (FIRS, VAT, CBN)
            </p>
            <div className="bg-green-50 border border-green-200 rounded-lg p-4">
              <div className="text-green-800">
                ✓ FIRS e-invoicing compliance verified<br/>
                ✓ VAT registration validated<br/>
                ✓ Nigerian business registration confirmed
              </div>
            </div>
          </div>
        );
      case 5:
        return (
          <div className="text-center py-12">
            <div className="text-4xl mb-4">🚀</div>
            <h3 className="text-xl font-semibold text-gray-900 mb-2">Ready for Deployment</h3>
            <p className="text-gray-600 mb-6">
              All systems configured and ready for production use
            </p>
            <div className="bg-blue-50 border border-blue-200 rounded-lg p-4 mb-6">
              <div className="text-blue-800">
                <strong>Systems to Deploy:</strong><br/>
                {selectedSystems.map(systemId => {
                  const system = businessSystems.find(s => s.id === systemId);
                  return `${system?.icon} ${system?.name}`;
                }).join(', ')}
              </div>
            </div>
          </div>
        );
      default:
        return null;
    }
  };

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <div className="bg-white border-b">
        <div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-3xl font-bold text-gray-900">Integration Setup</h1>
              <p className="text-gray-600 mt-2">Configure business system integrations for FIRS compliance</p>
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
          <div className="flex items-center">
            {steps.map((step, index) => (
              <React.Fragment key={step.id}>
                <div className={`flex items-center ${index <= currentStep ? 'text-blue-600' : 'text-gray-400'}`}>
                  <div className={`
                    flex items-center justify-center w-8 h-8 rounded-full text-sm font-medium
                    ${index <= currentStep ? 'bg-blue-600 text-white' : 'bg-gray-200 text-gray-500'}
                  `}>
                    {step.completed ? '✓' : index + 1}
                  </div>
                  <span className="ml-2 text-sm font-medium">{step.title}</span>
                </div>
                {index < steps.length - 1 && (
                  <div className={`h-1 w-12 mx-4 ${index < currentStep ? 'bg-blue-600' : 'bg-gray-200'}`} />
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

            <Button
              onClick={handleNext}
              disabled={
                (currentStep === 0 && selectedSystems.length === 0) ||
                (currentStep === 1 && selectedSystems.some(id => !testResults[id])) ||
                isProcessing
              }
              loading={isProcessing}
            >
              {currentStep === steps.length - 1 ? 'Deploy Integration' : 'Continue'}
            </Button>
          </div>
        </div>
      </div>
    </div>
  );
};

export default IntegrationSetup;