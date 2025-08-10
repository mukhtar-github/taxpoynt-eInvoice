/**
 * Mono Banking Consent Integration
 * ================================
 * 
 * Harmonizes TaxPoynt's consent management with Mono's banking consent widget.
 * Provides unified consent flow for both TaxPoynt platform access and banking data access.
 * 
 * Features:
 * - Integration with existing ConsentIntegratedRegistration
 * - Mono widget consent flow integration
 * - Nigerian Data Protection Regulation (NDPR) compliance
 * - Central Bank of Nigeria (CBN) banking consent requirements
 * - Unified consent state management
 * - Consent withdrawal and management
 */

import React, { useState, useEffect } from 'react';
import { Button } from '../../../role_management';

// Mono-specific consent items that extend TaxPoynt's base consent structure
interface MonoBankingConsent {
  id: string;
  category: 'financial_banking' | 'mono_specific';
  title: string;
  description: string;
  required: boolean;
  legalBasis: string;
  dataTypes: string[];
  retentionPeriod: string;
  thirdParties: string[];
  regulatoryBasis: string; // CBN, NDPR requirements
  monoScope: string[]; // Mono API scopes
}

// Banking-specific consent items based on Mono's requirements and Nigerian regulations
const monoBankingConsents: MonoBankingConsent[] = [
  {
    id: 'mono_account_information',
    category: 'financial_banking',
    title: 'Bank Account Information Access',
    description: 'Access your bank account details, balance, and account holder information through Mono Open Banking.',
    required: true,
    legalBasis: 'Contract performance - Required for banking integration and e-invoicing',
    dataTypes: [
      'Account number and details',
      'Account balance and currency',
      'Account holder name and BVN',
      'Bank institution information'
    ],
    retentionPeriod: 'Duration of service agreement + 7 years (FIRS compliance)',
    thirdParties: [
      'Mono Technologies (Open Banking Provider)',
      'Your Bank (Account data source)',
      'FIRS (For invoice compliance)',
      'CBN (Regulatory oversight)'
    ],
    regulatoryBasis: 'CBN Open Banking Framework, NDPR Article 6',
    monoScope: ['auth', 'account']
  },
  {
    id: 'mono_transaction_data',
    category: 'financial_banking',
    title: 'Transaction History Access',
    description: 'Access your transaction history to automatically generate e-invoices and track business payments.',
    required: true,
    legalBasis: 'Contract performance - Core functionality for automated invoicing',
    dataTypes: [
      'Transaction amounts and dates',
      'Transaction descriptions and references',
      'Sender/receiver information',
      'Transaction categories and types'
    ],
    retentionPeriod: '7 years (FIRS audit requirements)',
    thirdParties: [
      'Mono Technologies (Transaction data provider)',
      'Your Bank (Transaction source)',
      'FIRS (Compliance reporting)'
    ],
    regulatoryBasis: 'CBN Payment System Rules, FIRS E-invoicing Regulations',
    monoScope: ['transactions']
  },
  {
    id: 'mono_identity_verification',
    category: 'financial_banking',
    title: 'Identity and KYC Information',
    description: 'Access identity information for business verification and compliance with Nigerian financial regulations.',
    required: true,
    legalBasis: 'Legal obligation - KYC/AML compliance requirements',
    dataTypes: [
      'Full name and personal details',
      'BVN (Bank Verification Number)',
      'Phone number and email',
      'Address information'
    ],
    retentionPeriod: '5 years after service termination (KYC requirements)',
    thirdParties: [
      'Mono Technologies (Identity data provider)',
      'NIBSS (BVN verification)',
      'CBN (Regulatory compliance)'
    ],
    regulatoryBasis: 'CBN KYC Requirements, NDPR Article 6, AML Act 2011',
    monoScope: ['identity']
  },
  {
    id: 'mono_income_analysis',
    category: 'financial_banking',
    title: 'Income and Financial Analysis',
    description: 'Analyze income patterns to provide better invoicing insights and business intelligence.'
    required: false,
    legalBasis: 'Consent - Value-added service',
    dataTypes: [
      'Income patterns and frequency',
      'Financial stability metrics',
      'Business cash flow analysis'
    ],
    retentionPeriod: '2 years or until consent withdrawn',
    thirdParties: [
      'Mono Technologies (Analysis provider)',
      'TaxPoynt Universal Transaction Aggregator'
    ],
    regulatoryBasis: 'NDPR Article 7 (Consent-based processing)',
    monoScope: ['income']
  },
  {
    id: 'mono_real_time_webhooks',
    category: 'mono_specific',
    title: 'Real-time Transaction Notifications',
    description: 'Receive real-time notifications when new transactions occur for instant invoice generation.',
    required: false,
    legalBasis: 'Consent - Enhanced service functionality',
    dataTypes: [
      'Real-time transaction alerts',
      'Account status changes',
      'Balance update notifications'
    ],
    retentionPeriod: 'Duration of service agreement',
    thirdParties: [
      'Mono Technologies (Webhook provider)',
      'TaxPoynt Real-time Engine'
    ],
    regulatoryBasis: 'NDPR Article 7, CBN Real-time Payment Guidelines',
    monoScope: ['webhooks']
  }
];

interface MonoConsentState {
  taxpoynt: Record<string, boolean>; // Existing TaxPoynt consents
  mono: Record<string, boolean>; // Mono banking consents
  unified: boolean; // Overall consent status
}

interface MonoConsentIntegrationProps {
  existingConsents?: Record<string, boolean>; // From ConsentIntegratedRegistration
  onConsentUpdate: (consents: MonoConsentState) => void;
  onMonoWidgetReady: (monoUrl: string) => void;
  showDetailed?: boolean;
  compactMode?: boolean;
  onComplete?: () => void; // Called when banking consent process is complete
  onSkip?: () => void; // Called when user chooses to skip banking
}

export const MonoConsentIntegration: React.FC<MonoConsentIntegrationProps> = ({
  existingConsents = {},
  onConsentUpdate,
  onMonoWidgetReady,
  showDetailed = true,
  compactMode = false,
  onComplete,
  onSkip
}) => {
  const [consentState, setConsentState] = useState<MonoConsentState>({
    taxpoynt: existingConsents,
    mono: {},
    unified: false
  });

  const [showDetails, setShowDetails] = useState(!compactMode);
  const [monoWidgetUrl, setMonoWidgetUrl] = useState<string | null>(null);
  const [isGeneratingLink, setIsGeneratingLink] = useState(false);

  // Initialize Mono consents
  useEffect(() => {
    const initialMonoConsents: Record<string, boolean> = {};
    monoBankingConsents.forEach(consent => {
      initialMonoConsents[consent.id] = consent.required; // Required consents start as true
    });
    
    setConsentState(prev => ({
      ...prev,
      mono: initialMonoConsents
    }));
  }, []);

  // Update unified consent status
  useEffect(() => {
    const allRequired = [
      ...monoBankingConsents.filter(c => c.required).map(c => c.id)
    ];
    
    const allRequiredGranted = allRequired.every(id => 
      consentState.mono[id] === true
    );
    
    const updatedState = {
      ...consentState,
      unified: allRequiredGranted
    };
    
    setConsentState(updatedState);
    onConsentUpdate(updatedState);
  }, [consentState.mono, consentState.taxpoynt]);

  const handleMonoConsentChange = (consentId: string, granted: boolean) => {
    setConsentState(prev => ({
      ...prev,
      mono: {
        ...prev.mono,
        [consentId]: granted
      }
    }));
  };

  const generateMonoWidgetLink = async () => {
    if (!consentState.unified) {
      alert('Please grant all required consents before proceeding with bank linking');
      return;
    }

    setIsGeneratingLink(true);
    
    try {
      // Get the granted scopes for Mono
      const grantedScopes = monoBankingConsents
        .filter(consent => consentState.mono[consent.id])
        .flatMap(consent => consent.monoScope)
        .filter((scope, index, array) => array.indexOf(scope) === index); // Remove duplicates

      const response = await fetch('/api/v1/si/banking/open-banking/mono/link', {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('taxpoynt_auth_token')}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          customer: {
            name: 'Business User', // This would come from user context
            email: 'user@business.com' // This would come from user context
          },
          scope: grantedScopes.join(' '), // Join scopes for Mono
          redirect_url: `${window.location.origin}/si/banking/callback`,
          meta: {
            ref: `taxpoynt_consent_${Date.now()}`,
            consents_granted: Object.keys(consentState.mono).filter(k => consentState.mono[k]),
            consent_timestamp: new Date().toISOString()
          }
        })
      });

      if (!response.ok) {
        throw new Error('Failed to generate Mono widget link');
      }

      const data = await response.json();
      
      if (data.data?.mono_url) {
        setMonoWidgetUrl(data.data.mono_url);
        onMonoWidgetReady(data.data.mono_url);
        
        // Call onComplete when banking setup is ready
        if (onComplete) {
          onComplete();
        }
      }

    } catch (error) {
      console.error('Failed to generate Mono widget link:', error);
      alert('Failed to generate banking link. Please try again.');
    } finally {
      setIsGeneratingLink(false);
    }
  };

  const renderConsentItem = (consent: MonoBankingConsent) => (
    <div
      key={consent.id}
      className={`border rounded-lg p-4 ${
        consent.required 
          ? 'border-blue-200 bg-blue-50' 
          : 'border-gray-200 bg-white'
      }`}
    >
      <div className="flex items-start space-x-3">
        <div className="flex-shrink-0 mt-1">
          <input
            type="checkbox"
            id={consent.id}
            checked={consentState.mono[consent.id] || false}
            onChange={(e) => handleMonoConsentChange(consent.id, e.target.checked)}
            disabled={consent.required}
            className="w-4 h-4 text-blue-600 border-gray-300 rounded focus:ring-blue-500"
          />
        </div>
        
        <div className="flex-1">
          <div className="flex items-center justify-between">
            <label 
              htmlFor={consent.id}
              className={`font-medium cursor-pointer ${
                consent.required ? 'text-blue-900' : 'text-gray-900'
              }`}
            >
              {consent.title}
              {consent.required && (
                <span className="ml-2 px-2 py-1 text-xs bg-blue-100 text-blue-800 rounded-full">
                  Required
                </span>
              )}
            </label>
          </div>
          
          <p className={`text-sm mt-1 ${
            consent.required ? 'text-blue-700' : 'text-gray-600'
          }`}>
            {consent.description}
          </p>
          
          {showDetails && (
            <div className="mt-3 space-y-2 text-xs text-gray-600">
              <div>
                <strong>Legal Basis:</strong> {consent.legalBasis}
              </div>
              <div>
                <strong>Data Types:</strong> {consent.dataTypes.join(', ')}
              </div>
              <div>
                <strong>Regulatory Basis:</strong> {consent.regulatoryBasis}
              </div>
              <div>
                <strong>Retention Period:</strong> {consent.retentionPeriod}
              </div>
              <div>
                <strong>Third Parties:</strong> {consent.thirdParties.join(', ')}
              </div>
              <div>
                <strong>Mono Scopes:</strong> {consent.monoScope.join(', ')}
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );

  if (compactMode) {
    return (
      <div className="bg-white border rounded-lg p-6">
        <div className="flex items-center justify-between mb-4">
          <div>
            <h3 className="text-lg font-semibold text-gray-900">
              Banking Data Access Consent
            </h3>
            <p className="text-sm text-gray-600">
              Required for Mono Open Banking integration
            </p>
          </div>
          <div className={`px-3 py-1 rounded-full text-sm font-medium ${
            consentState.unified 
              ? 'bg-green-100 text-green-800' 
              : 'bg-yellow-100 text-yellow-800'
          }`}>
            {consentState.unified ? 'Consents Granted' : 'Consent Required'}
          </div>
        </div>
        
        <div className="flex items-center justify-between">
          <button
            onClick={() => setShowDetails(!showDetails)}
            className="text-blue-600 hover:text-blue-800 text-sm"
          >
            {showDetails ? 'Hide Details' : 'Show Details'}
          </button>
          
          <div className="flex space-x-2">
            {onSkip && (
              <Button
                onClick={onSkip}
                variant="outline"
                size="sm"
              >
                Skip Banking
              </Button>
            )}
            <Button
              onClick={generateMonoWidgetLink}
              disabled={!consentState.unified || isGeneratingLink}
              size="sm"
            >
              {isGeneratingLink ? 'Generating...' : 'Connect Bank Account'}
            </Button>
          </div>
        </div>
        
        {showDetails && (
          <div className="mt-6 space-y-4">
            {monoBankingConsents.map(renderConsentItem)}
          </div>
        )}
      </div>
    );
  }

  return (
    <div className="max-w-4xl mx-auto">
      {/* Header */}
      <div className="text-center mb-8">
        <h2 className="text-2xl font-bold text-gray-900 mb-2">
          Banking Integration Consent
        </h2>
        <p className="text-gray-600">
          Grant permissions for secure banking data access through Mono Open Banking
        </p>
        <div className="mt-4 flex items-center justify-center space-x-4 text-sm text-gray-500">
          <span className="flex items-center">
            🔒 <span className="ml-1">NDPR Compliant</span>
          </span>
          <span className="flex items-center">
            🏛️ <span className="ml-1">CBN Licensed</span>
          </span>
          <span className="flex items-center">
            🛡️ <span className="ml-1">Bank-grade Security</span>
          </span>
        </div>
      </div>

      {/* Nigerian Banking Context */}
      <div className="bg-blue-50 border border-blue-200 rounded-lg p-6 mb-8">
        <h3 className="text-lg font-semibold text-blue-900 mb-3">
          🇳🇬 Nigerian Banking & Privacy Compliance
        </h3>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-sm text-blue-800">
          <div>
            <h4 className="font-medium mb-2">Central Bank of Nigeria (CBN)</h4>
            <ul className="space-y-1">
              <li>• Open Banking Framework compliance</li>
              <li>• Payment System Rules adherence</li>
              <li>• KYC/AML requirements</li>
            </ul>
          </div>
          <div>
            <h4 className="font-medium mb-2">Nigerian Data Protection Regulation (NDPR)</h4>
            <ul className="space-y-1">
              <li>• Explicit consent for data processing</li>
              <li>• Right to withdraw consent</li>
              <li>• Data minimization principles</li>
            </ul>
          </div>
        </div>
      </div>

      {/* Consent Items */}
      <div className="space-y-4 mb-8">
        <h3 className="text-lg font-semibold text-gray-900">
          Banking Data Access Permissions
        </h3>
        {monoBankingConsents.map(renderConsentItem)}
      </div>

      {/* Consent Summary */}
      <div className="bg-gray-50 border border-gray-200 rounded-lg p-6 mb-8">
        <h3 className="text-lg font-semibold text-gray-900 mb-4">
          Consent Summary
        </h3>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <div>
            <h4 className="font-medium text-gray-700 mb-2">Required Consents</h4>
            <div className="space-y-1">
              {monoBankingConsents.filter(c => c.required).map(consent => (
                <div key={consent.id} className="flex items-center text-sm">
                  <span className={`w-2 h-2 rounded-full mr-2 ${
                    consentState.mono[consent.id] ? 'bg-green-500' : 'bg-red-500'
                  }`}></span>
                  {consent.title}
                </div>
              ))}
            </div>
          </div>
          <div>
            <h4 className="font-medium text-gray-700 mb-2">Optional Consents</h4>
            <div className="space-y-1">
              {monoBankingConsents.filter(c => !c.required).map(consent => (
                <div key={consent.id} className="flex items-center text-sm">
                  <span className={`w-2 h-2 rounded-full mr-2 ${
                    consentState.mono[consent.id] ? 'bg-green-500' : 'bg-gray-300'
                  }`}></span>
                  {consent.title}
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>

      {/* Action Buttons */}
      <div className="flex items-center justify-between">
        <div className="text-sm text-gray-600">
          {consentState.unified ? (
            <span className="text-green-600">✅ All required consents granted</span>
          ) : (
            <span className="text-orange-600">⚠️ Required consents needed to proceed</span>
          )}
        </div>
        
        <div className="flex space-x-4">
          <button
            onClick={() => setShowDetails(!showDetails)}
            className="text-gray-600 hover:text-gray-800"
          >
            {showDetails ? 'Hide' : 'Show'} Technical Details
          </button>
          
          <Button
            onClick={generateMonoWidgetLink}
            disabled={!consentState.unified || isGeneratingLink}
            size="lg"
          >
            {isGeneratingLink ? (
              <>
                <span className="animate-spin mr-2">⏳</span>
                Generating Secure Link...
              </>
            ) : (
              'Proceed to Bank Account Linking'
            )}
          </Button>
        </div>
      </div>

      {/* Mono Widget Link */}
      {monoWidgetUrl && (
        <div className="mt-8 bg-green-50 border border-green-200 rounded-lg p-6">
          <h3 className="text-lg font-semibold text-green-900 mb-2">
            🔗 Bank Account Linking Ready
          </h3>
          <p className="text-green-700 mb-4">
            Your secure Mono banking link has been generated. Click below to connect your Nigerian bank account.
          </p>
          <div className="flex items-center space-x-4">
            <Button
              onClick={() => window.open(monoWidgetUrl, '_blank')}
              variant="primary"
            >
              Open Mono Banking Widget
            </Button>
            <button
              onClick={() => {
                navigator.clipboard.writeText(monoWidgetUrl);
                alert('Link copied to clipboard');
              }}
              className="text-green-600 hover:text-green-800 text-sm"
            >
              📋 Copy Link
            </button>
          </div>
        </div>
      )}
    </div>
  );
};

export default MonoConsentIntegration;