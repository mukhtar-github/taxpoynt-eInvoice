/**
 * Validation Process Workflow
 * ==========================
 * 
 * System Integrator workflow for comprehensive document validation and quality assurance.
 * Multi-layer validation including business rules, Nigerian compliance, and FIRS requirements.
 * 
 * Features:
 * - Multi-tier validation process (syntax, business, compliance, FIRS)
 * - Real-time validation feedback and scoring
 * - Nigerian tax law compliance validation
 * - Batch validation with detailed reporting
 * - Auto-correction suggestions and implementation
 * - Validation rule customization and management
 */

import React, { useState, useEffect } from 'react';
import { Button } from '../../design_system/components/Button';

interface ValidationTier {
  id: string;
  name: string;
  description: string;
  order: number;
  enabled: boolean;
  rules: ValidationRule[];
  passRate: number;
  status: 'pending' | 'running' | 'completed' | 'failed';
}

interface ValidationRule {
  id: string;
  tierId: string;
  name: string;
  description: string;
  category: 'syntax' | 'business_logic' | 'compliance' | 'data_quality' | 'security';
  severity: 'info' | 'warning' | 'error' | 'critical';
  enabled: boolean;
  autoFixable: boolean;
  conditions: Array<{
    field: string;
    operator: 'exists' | 'equals' | 'not_equals' | 'greater_than' | 'less_than' | 'matches_pattern' | 'in_range';
    value: any;
    errorMessage: string;
  }>;
  nigerianCompliance?: {
    regulatoryBody: 'FIRS' | 'CBN' | 'NDPR' | 'CAC';
    requirement: string;
    penalty?: string;
  };
}

interface ValidationResult {
  documentId: string;
  documentType: string;
  overallScore: number; // 0-100
  tierResults: Array<{
    tierId: string;
    tierName: string;
    passed: boolean;
    score: number;
    issues: ValidationIssue[];
    executionTime: number;
  }>;
  summary: {
    totalIssues: number;
    criticalIssues: number;
    errorIssues: number;
    warningIssues: number;
    infoIssues: number;
    autoFixableIssues: number;
  };
  nigerianCompliance: {
    firsCompliant: boolean;
    vatCompliant: boolean;
    cbnCompliant: boolean;
    ndprCompliant: boolean;
    overallComplianceScore: number;
  };
  recommendations: string[];
  canSubmitToFIRS: boolean;
}

interface ValidationIssue {
  id: string;
  ruleId: string;
  ruleName: string;
  severity: 'info' | 'warning' | 'error' | 'critical';
  category: string;
  field?: string;
  message: string;
  currentValue?: any;
  expectedValue?: any;
  suggestion: string;
  autoFixable: boolean;
  nigerianCompliance?: {
    regulatoryBody: string;
    requirement: string;
    impact: string;
  };
}

interface ValidationBatch {
  id: string;
  name: string;
  createdDate: string;
  status: 'queued' | 'processing' | 'completed' | 'failed';
  totalDocuments: number;
  processedDocuments: number;
  validDocuments: number;
  invalidDocuments: number;
  averageScore: number;
  progress: number;
  estimatedTimeRemaining?: number;
  results: ValidationResult[];
}

// Default validation tiers for Nigerian e-invoicing
const defaultValidationTiers: ValidationTier[] = [
  {
    id: 'syntax_validation',
    name: 'Syntax Validation',
    description: 'Basic document structure and format validation',
    order: 1,
    enabled: true,
    passRate: 0,
    status: 'pending',
    rules: [
      {
        id: 'json_structure',
        tierId: 'syntax_validation',
        name: 'Valid JSON Structure',
        description: 'Document must be valid JSON format',
        category: 'syntax',
        severity: 'critical',
        enabled: true,
        autoFixable: false,
        conditions: [
          {
            field: '_document',
            operator: 'exists',
            value: true,
            errorMessage: 'Document is not valid JSON'
          }
        ]
      },
      {
        id: 'required_fields',
        tierId: 'syntax_validation',
        name: 'Required Fields Present',
        description: 'All mandatory fields must be present',
        category: 'syntax',
        severity: 'error',
        enabled: true,
        autoFixable: false,
        conditions: [
          {
            field: 'invoice_number',
            operator: 'exists',
            value: true,
            errorMessage: 'Invoice number is required'
          },
          {
            field: 'invoice_date',
            operator: 'exists',
            value: true,
            errorMessage: 'Invoice date is required'
          },
          {
            field: 'supplier_tin',
            operator: 'exists',
            value: true,
            errorMessage: 'Supplier TIN is required'
          }
        ]
      }
    ]
  },
  {
    id: 'business_validation',
    name: 'Business Logic Validation',
    description: 'Business rules and logic validation',
    order: 2,
    enabled: true,
    passRate: 0,
    status: 'pending',
    rules: [
      {
        id: 'amount_consistency',
        tierId: 'business_validation',
        name: 'Amount Calculations',
        description: 'Verify mathematical consistency of amounts',
        category: 'business_logic',
        severity: 'error',
        enabled: true,
        autoFixable: true,
        conditions: [
          {
            field: 'total_amount',
            operator: 'equals',
            value: 'line_items_sum + vat_amount',
            errorMessage: 'Total amount does not match line items sum plus VAT'
          }
        ]
      },
      {
        id: 'date_consistency',
        tierId: 'business_validation',
        name: 'Date Logic',
        description: 'Validate date consistency and logic',
        category: 'business_logic',
        severity: 'warning',
        enabled: true,
        autoFixable: false,
        conditions: [
          {
            field: 'invoice_date',
            operator: 'less_than',
            value: 'due_date',
            errorMessage: 'Invoice date should be before due date'
          }
        ]
      }
    ]
  },
  {
    id: 'nigerian_compliance',
    name: 'Nigerian Compliance',
    description: 'Nigerian tax and regulatory compliance validation',
    order: 3,
    enabled: true,
    passRate: 0,
    status: 'pending',
    rules: [
      {
        id: 'vat_calculation',
        tierId: 'nigerian_compliance',
        name: 'VAT Calculation (7.5%)',
        description: 'Verify VAT is calculated correctly at 7.5%',
        category: 'compliance',
        severity: 'error',
        enabled: true,
        autoFixable: true,
        conditions: [
          {
            field: 'vat_amount',
            operator: 'equals',
            value: 'taxable_amount * 0.075',
            errorMessage: 'VAT amount should be 7.5% of taxable amount'
          }
        ],
        nigerianCompliance: {
          regulatoryBody: 'FIRS',
          requirement: 'VAT Act 2020 - Standard rate of 7.5%',
          penalty: 'Invoice rejection by FIRS'
        }
      },
      {
        id: 'tin_format',
        tierId: 'nigerian_compliance',
        name: 'Nigerian TIN Format',
        description: 'Validate TIN follows Nigerian format (14 digits)',
        category: 'compliance',
        severity: 'critical',
        enabled: true,
        autoFixable: false,
        conditions: [
          {
            field: 'supplier_tin',
            operator: 'matches_pattern',
            value: '^[0-9]{14}$',
            errorMessage: 'TIN must be exactly 14 digits'
          }
        ],
        nigerianCompliance: {
          regulatoryBody: 'FIRS',
          requirement: 'Personal Income Tax Act - TIN format specification',
          penalty: 'Document rejection and potential audit'
        }
      },
      {
        id: 'currency_requirement',
        tierId: 'nigerian_compliance',
        name: 'Naira Currency Requirement',
        description: 'Domestic transactions must be in Nigerian Naira',
        category: 'compliance',
        severity: 'error',
        enabled: true,
        autoFixable: true,
        conditions: [
          {
            field: 'currency',
            operator: 'equals',
            value: 'NGN',
            errorMessage: 'Domestic transactions must be in Nigerian Naira (NGN)'
          }
        ],
        nigerianCompliance: {
          regulatoryBody: 'CBN',
          requirement: 'Foreign Exchange Act - Domestic transaction currency',
          penalty: 'Transaction rejection and compliance violation'
        }
      }
    ]
  },
  {
    id: 'firs_validation',
    name: 'FIRS E-invoicing',
    description: 'FIRS e-invoicing format and submission validation',
    order: 4,
    enabled: true,
    passRate: 0,
    status: 'pending',
    rules: [
      {
        id: 'firs_schema',
        tierId: 'firs_validation',
        name: 'FIRS Schema Compliance',
        description: 'Document must comply with FIRS e-invoicing schema',
        category: 'compliance',
        severity: 'critical',
        enabled: true,
        autoFixable: false,
        conditions: [
          {
            field: '_schema_version',
            operator: 'equals',
            value: 'FIRS_E_INVOICE_v2.1',
            errorMessage: 'Document must comply with FIRS e-invoicing schema v2.1'
          }
        ],
        nigerianCompliance: {
          regulatoryBody: 'FIRS',
          requirement: 'E-invoicing Implementation Guidelines 2024',
          penalty: 'Invoice submission rejection'
        }
      },
      {
        id: 'submission_readiness',
        tierId: 'firs_validation',
        name: 'FIRS Submission Readiness',
        description: 'Document is ready for FIRS submission',
        category: 'compliance',
        severity: 'critical',
        enabled: true,
        autoFixable: false,
        conditions: [
          {
            field: '_validation_status',
            operator: 'equals',
            value: 'ready_for_submission',
            errorMessage: 'Document has validation issues preventing FIRS submission'
          }
        ],
        nigerianCompliance: {
          regulatoryBody: 'FIRS',
          requirement: 'E-invoicing submission requirements',
          penalty: 'Delayed tax compliance and potential penalties'
        }
      }
    ]
  }
];

interface ValidationProcessProps {
  documentIds?: string[];
  batchId?: string;
  onValidationComplete?: (results: ValidationResult[]) => void;
}

export const ValidationProcess: React.FC<ValidationProcessProps> = ({
  documentIds,
  batchId,
  onValidationComplete
}) => {
  const [validationTiers, setValidationTiers] = useState<ValidationTier[]>(defaultValidationTiers);
  const [currentBatch, setCurrentBatch] = useState<ValidationBatch | null>(null);
  const [validationResults, setValidationResults] = useState<ValidationResult[]>([]);
  const [selectedResult, setSelectedResult] = useState<ValidationResult | null>(null);
  const [isProcessing, setIsProcessing] = useState(false);
  const [showTierConfig, setShowTierConfig] = useState(false);

  useEffect(() => {
    if (batchId) {
      loadValidationBatch();
    }
  }, [batchId]);

  const loadValidationBatch = async () => {
    try {
      const response = await fetch(`/api/v1/si/validation/batches/${batchId}`, {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('taxpoynt_auth_token')}`
        }
      });

      if (response.ok) {
        const data = await response.json();
        setCurrentBatch(data.batch);
        setValidationResults(data.batch.results || []);
      }
    } catch (error) {
      console.error('Failed to load validation batch:', error);
    }
  };

  const handleStartValidation = async () => {
    if (!documentIds || documentIds.length === 0) {
      alert('No documents selected for validation');
      return;
    }

    setIsProcessing(true);
    try {
      const response = await fetch('/api/v1/si/validation/process', {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('taxpoynt_auth_token')}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          document_ids: documentIds,
          validation_tiers: validationTiers.filter(tier => tier.enabled),
          auto_fix_enabled: true,
          generate_report: true
        })
      });

      if (response.ok) {
        const data = await response.json();
        const newBatch = data.batch;
        setCurrentBatch(newBatch);
        
        // Start polling for progress
        pollValidationProgress(newBatch.id);
        
        alert('✅ Validation process started successfully!');
      } else {
        alert('❌ Failed to start validation process');
      }
    } catch (error) {
      console.error('Failed to start validation:', error);
      alert('❌ Failed to start validation process');
    } finally {
      setIsProcessing(false);
    }
  };

  const pollValidationProgress = (batchId: string) => {
    const pollInterval = setInterval(async () => {
      try {
        const response = await fetch(`/api/v1/si/validation/batches/${batchId}/status`, {
          headers: {
            'Authorization': `Bearer ${localStorage.getItem('taxpoynt_auth_token')}`
          }
        });

        if (response.ok) {
          const data = await response.json();
          const updatedBatch = data.batch;
          setCurrentBatch(updatedBatch);
          setValidationResults(updatedBatch.results || []);

          if (['completed', 'failed'].includes(updatedBatch.status)) {
            clearInterval(pollInterval);
            if (updatedBatch.status === 'completed' && onValidationComplete) {
              onValidationComplete(updatedBatch.results);
            }
          }
        }
      } catch (error) {
        console.error('Failed to poll validation progress:', error);
        clearInterval(pollInterval);
      }
    }, 2000);
  };

  const handleAutoFix = async (resultId: string, issueIds: string[]) => {
    try {
      setIsProcessing(true);
      const response = await fetch('/api/v1/si/validation/auto-fix', {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('taxpoynt_auth_token')}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          result_id: resultId,
          issue_ids: issueIds
        })
      });

      if (response.ok) {
        const data = await response.json();
        alert(`✅ Auto-fixed ${data.fixed_count} issues successfully!`);
        
        // Refresh validation results
        if (currentBatch) {
          loadValidationBatch();
        }
      } else {
        alert('❌ Failed to auto-fix issues');
      }
    } catch (error) {
      console.error('Failed to auto-fix:', error);
      alert('❌ Failed to auto-fix issues');
    } finally {
      setIsProcessing(false);
    }
  };

  const getScoreColor = (score: number) => {
    if (score >= 90) return 'text-green-600';
    if (score >= 70) return 'text-yellow-600';
    if (score >= 50) return 'text-orange-600';
    return 'text-red-600';
  };

  const getScoreBackground = (score: number) => {
    if (score >= 90) return 'bg-green-100';
    if (score >= 70) return 'bg-yellow-100';
    if (score >= 50) return 'bg-orange-100';
    return 'bg-red-100';
  };

  const getSeverityColor = (severity: ValidationIssue['severity']) => {
    switch (severity) {
      case 'critical': return 'text-red-800 bg-red-100';
      case 'error': return 'text-red-700 bg-red-50';
      case 'warning': return 'text-yellow-700 bg-yellow-50';
      case 'info': return 'text-blue-700 bg-blue-50';
      default: return 'text-gray-700 bg-gray-50';
    }
  };

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <div className="bg-white border-b">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-3xl font-bold text-gray-900">Validation Process</h1>
              <p className="text-gray-600 mt-2">
                Comprehensive document validation for Nigerian compliance and FIRS submission
              </p>
            </div>
            
            <div className="flex items-center space-x-4">
              <Button
                onClick={() => setShowTierConfig(!showTierConfig)}
                variant="outline"
              >
                ⚙️ Configure Tiers
              </Button>
              
              <Button
                onClick={handleStartValidation}
                disabled={!documentIds || documentIds.length === 0 || isProcessing}
                loading={isProcessing}
              >
                🔍 Start Validation
              </Button>
            </div>
          </div>
        </div>
      </div>

      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
          
          {/* Validation Tiers */}
          <div>
            <div className="bg-white rounded-lg border">
              <div className="p-6 border-b">
                <h2 className="text-lg font-semibold text-gray-900">Validation Tiers</h2>
                <p className="text-gray-600 text-sm mt-1">Multi-layer validation process</p>
              </div>
              
              <div className="p-6 space-y-4">
                {validationTiers.map((tier, index) => (
                  <div key={tier.id} className="border rounded-lg p-4">
                    <div className="flex items-center justify-between mb-2">
                      <div className="flex items-center space-x-3">
                        <div className={`
                          w-6 h-6 rounded-full flex items-center justify-center text-xs font-medium
                          ${index === 0 ? 'bg-blue-600 text-white' :
                            tier.status === 'completed' ? 'bg-green-600 text-white' :
                            tier.status === 'running' ? 'bg-yellow-600 text-white' :
                            tier.status === 'failed' ? 'bg-red-600 text-white' :
                            'bg-gray-300 text-gray-600'
                          }
                        `}>
                          {tier.status === 'completed' ? '✓' :
                           tier.status === 'running' ? '⏳' :
                           tier.status === 'failed' ? '✗' :
                           index + 1}
                        </div>
                        <div>
                          <h3 className="font-medium text-gray-900">{tier.name}</h3>
                          <p className="text-sm text-gray-600">{tier.rules.length} rules</p>
                        </div>
                      </div>
                      
                      <label className="flex items-center">
                        <input
                          type="checkbox"
                          checked={tier.enabled}
                          onChange={(e) => setValidationTiers(prev => prev.map(t => 
                            t.id === tier.id ? { ...t, enabled: e.target.checked } : t
                          ))}
                          className="h-4 w-4 text-blue-600 border-gray-300 rounded focus:ring-blue-500"
                        />
                      </label>
                    </div>
                    
                    <p className="text-sm text-gray-600 mb-3">{tier.description}</p>
                    
                    {tier.passRate > 0 && (
                      <div className="flex items-center justify-between text-sm">
                        <span className="text-gray-600">Pass Rate</span>
                        <span className={`font-medium ${getScoreColor(tier.passRate)}`}>
                          {tier.passRate.toFixed(1)}%
                        </span>
                      </div>
                    )}
                  </div>
                ))}
              </div>
            </div>

            {/* Nigerian Compliance Summary */}
            <div className="bg-white rounded-lg border mt-6">
              <div className="p-6 border-b">
                <h2 className="text-lg font-semibold text-gray-900">🇳🇬 Nigerian Compliance</h2>
              </div>
              
              <div className="p-6 space-y-3">
                <div className="flex items-center justify-between text-sm">
                  <span className="flex items-center">
                    <span className="w-3 h-3 bg-red-500 rounded-full mr-2"></span>
                    FIRS E-invoicing
                  </span>
                  <span className="font-medium">Required</span>
                </div>
                <div className="flex items-center justify-between text-sm">
                  <span className="flex items-center">
                    <span className="w-3 h-3 bg-orange-500 rounded-full mr-2"></span>
                    VAT Compliance (7.5%)
                  </span>
                  <span className="font-medium">Required</span>
                </div>
                <div className="flex items-center justify-between text-sm">
                  <span className="flex items-center">
                    <span className="w-3 h-3 bg-blue-500 rounded-full mr-2"></span>
                    CBN Currency Rules
                  </span>
                  <span className="font-medium">Required</span>
                </div>
                <div className="flex items-center justify-between text-sm">
                  <span className="flex items-center">
                    <span className="w-3 h-3 bg-green-500 rounded-full mr-2"></span>
                    TIN Format Validation
                  </span>
                  <span className="font-medium">Required</span>
                </div>
              </div>
            </div>
          </div>

          {/* Validation Results */}
          <div className="lg:col-span-2">
            <div className="bg-white rounded-lg border">
              <div className="p-6 border-b">
                <h2 className="text-lg font-semibold text-gray-900">Validation Results</h2>
                {currentBatch && (
                  <div className="flex items-center justify-between mt-2">
                    <p className="text-gray-600 text-sm">
                      Batch: {currentBatch.name} • {currentBatch.processedDocuments}/{currentBatch.totalDocuments} processed
                    </p>
                    <span className={`px-2 py-1 text-xs font-medium rounded-full ${
                      currentBatch.status === 'completed' ? 'bg-green-100 text-green-800' :
                      currentBatch.status === 'processing' ? 'bg-blue-100 text-blue-800' :
                      currentBatch.status === 'failed' ? 'bg-red-100 text-red-800' :
                      'bg-gray-100 text-gray-800'
                    }`}>
                      {currentBatch.status}
                    </span>
                  </div>
                )}
              </div>
              
              {/* Progress Bar */}
              {currentBatch && currentBatch.status === 'processing' && (
                <div className="p-6 border-b">
                  <div className="flex items-center justify-between text-sm text-gray-600 mb-2">
                    <span>Validation Progress</span>
                    <span>{currentBatch.progress}%</span>
                  </div>
                  <div className="w-full bg-gray-200 rounded-full h-2">
                    <div
                      className="bg-blue-500 h-2 rounded-full transition-all duration-300"
                      style={{ width: `${currentBatch.progress}%` }}
                    />
                  </div>
                  {currentBatch.estimatedTimeRemaining && (
                    <div className="text-xs text-gray-500 mt-1">
                      ETA: {Math.ceil(currentBatch.estimatedTimeRemaining / 60)} minutes
                    </div>
                  )}
                </div>
              )}

              {/* Results List */}
              <div className="divide-y divide-gray-200">
                {validationResults.length === 0 ? (
                  <div className="text-center py-12 text-gray-500">
                    <div className="text-4xl mb-4">🔍</div>
                    <h3 className="text-lg font-medium mb-2">No validation results</h3>
                    <p className="mb-4">Start a validation process to see results here</p>
                  </div>
                ) : (
                  validationResults.map(result => (
                    <div key={result.documentId} className="p-6">
                      <div className="flex items-center justify-between mb-4">
                        <div>
                          <h3 className="text-lg font-medium text-gray-900">
                            Document: {result.documentId}
                          </h3>
                          <p className="text-sm text-gray-600">{result.documentType}</p>
                        </div>
                        
                        <div className="flex items-center space-x-4">
                          <div className={`text-center px-3 py-2 rounded-lg ${getScoreBackground(result.overallScore)}`}>
                            <div className={`text-2xl font-bold ${getScoreColor(result.overallScore)}`}>
                              {result.overallScore}
                            </div>
                            <div className="text-xs text-gray-600">Score</div>
                          </div>
                          
                          <div className={`px-3 py-1 rounded-full text-sm font-medium ${
                            result.canSubmitToFIRS 
                              ? 'bg-green-100 text-green-800' 
                              : 'bg-red-100 text-red-800'
                          }`}>
                            {result.canSubmitToFIRS ? '✅ FIRS Ready' : '❌ Issues Found'}
                          </div>
                        </div>
                      </div>

                      {/* Tier Results */}
                      <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-4">
                        {result.tierResults.map(tierResult => (
                          <div key={tierResult.tierId} className="bg-gray-50 rounded-lg p-3">
                            <div className="flex items-center justify-between mb-2">
                              <span className="font-medium text-gray-900">{tierResult.tierName}</span>
                              <span className={`px-2 py-1 text-xs font-medium rounded-full ${
                                tierResult.passed ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'
                              }`}>
                                {tierResult.passed ? 'Pass' : 'Fail'}
                              </span>
                            </div>
                            <div className="flex items-center justify-between text-sm">
                              <span className="text-gray-600">Score: {tierResult.score}/100</span>
                              <span className="text-gray-600">{tierResult.issues.length} issues</span>
                            </div>
                          </div>
                        ))}
                      </div>

                      {/* Issues Summary */}
                      <div className="grid grid-cols-4 gap-4 mb-4">
                        <div className="text-center bg-red-50 rounded-lg p-3">
                          <div className="text-xl font-bold text-red-600">{result.summary.criticalIssues}</div>
                          <div className="text-xs text-gray-600">Critical</div>
                        </div>
                        <div className="text-center bg-orange-50 rounded-lg p-3">
                          <div className="text-xl font-bold text-orange-600">{result.summary.errorIssues}</div>
                          <div className="text-xs text-gray-600">Errors</div>
                        </div>
                        <div className="text-center bg-yellow-50 rounded-lg p-3">
                          <div className="text-xl font-bold text-yellow-600">{result.summary.warningIssues}</div>
                          <div className="text-xs text-gray-600">Warnings</div>
                        </div>
                        <div className="text-center bg-blue-50 rounded-lg p-3">
                          <div className="text-xl font-bold text-blue-600">{result.summary.autoFixableIssues}</div>
                          <div className="text-xs text-gray-600">Auto-fixable</div>
                        </div>
                      </div>

                      {/* Nigerian Compliance Status */}
                      <div className="bg-blue-50 border border-blue-200 rounded-lg p-4 mb-4">
                        <h4 className="font-medium text-blue-900 mb-2">🇳🇬 Nigerian Compliance Status</h4>
                        <div className="grid grid-cols-2 gap-4 text-sm">
                          <div className="flex items-center justify-between">
                            <span className="text-blue-800">FIRS Compliant</span>
                            <span className={result.nigerianCompliance.firsCompliant ? 'text-green-600' : 'text-red-600'}>
                              {result.nigerianCompliance.firsCompliant ? '✅' : '❌'}
                            </span>
                          </div>
                          <div className="flex items-center justify-between">
                            <span className="text-blue-800">VAT Compliant</span>
                            <span className={result.nigerianCompliance.vatCompliant ? 'text-green-600' : 'text-red-600'}>
                              {result.nigerianCompliance.vatCompliant ? '✅' : '❌'}
                            </span>
                          </div>
                          <div className="flex items-center justify-between">
                            <span className="text-blue-800">CBN Compliant</span>
                            <span className={result.nigerianCompliance.cbnCompliant ? 'text-green-600' : 'text-red-600'}>
                              {result.nigerianCompliance.cbnCompliant ? '✅' : '❌'}
                            </span>
                          </div>
                          <div className="flex items-center justify-between">
                            <span className="text-blue-800">Overall Score</span>
                            <span className={`font-medium ${getScoreColor(result.nigerianCompliance.overallComplianceScore)}`}>
                              {result.nigerianCompliance.overallComplianceScore}/100
                            </span>
                          </div>
                        </div>
                      </div>

                      {/* Actions */}
                      <div className="flex items-center space-x-3">
                        <Button
                          onClick={() => setSelectedResult(result)}
                          size="sm"
                          variant="outline"
                        >
                          📋 View Details
                        </Button>
                        
                        {result.summary.autoFixableIssues > 0 && (
                          <Button
                            onClick={() => {
                              const autoFixableIssueIds = result.tierResults
                                .flatMap(tr => tr.issues)
                                .filter(issue => issue.autoFixable)
                                .map(issue => issue.id);
                              handleAutoFix(result.documentId, autoFixableIssueIds);
                            }}
                            disabled={isProcessing}
                            size="sm"
                            variant="outline"
                          >
                            🔧 Auto-fix ({result.summary.autoFixableIssues})
                          </Button>
                        )}
                        
                        {result.canSubmitToFIRS && (
                          <Button
                            size="sm"
                          >
                            🇳🇬 Submit to FIRS
                          </Button>
                        )}
                      </div>
                    </div>
                  ))
                )}
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Detailed Result Modal */}
      {selectedResult && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg max-w-6xl w-full m-4 max-h-screen overflow-y-auto">
            <div className="p-6 border-b">
              <div className="flex items-center justify-between">
                <h2 className="text-xl font-semibold text-gray-900">
                  Validation Details: {selectedResult.documentId}
                </h2>
                <button
                  onClick={() => setSelectedResult(null)}
                  className="text-gray-400 hover:text-gray-600"
                >
                  <svg className="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                  </svg>
                </button>
              </div>
            </div>
            
            <div className="p-6">
              {/* All Issues */}
              <div className="space-y-4">
                <h3 className="font-semibold text-gray-900">All Issues ({selectedResult.summary.totalIssues})</h3>
                
                {selectedResult.tierResults.map(tierResult => (
                  <div key={tierResult.tierId}>
                    {tierResult.issues.length > 0 && (
                      <div className="border rounded-lg p-4">
                        <h4 className="font-medium text-gray-900 mb-3">{tierResult.tierName} Issues</h4>
                        <div className="space-y-3">
                          {tierResult.issues.map(issue => (
                            <div key={issue.id} className="border-l-4 border-gray-200 pl-4">
                              <div className="flex items-start justify-between">
                                <div className="flex-1">
                                  <div className="flex items-center space-x-2 mb-1">
                                    <span className={`px-2 py-1 text-xs font-medium rounded-full ${getSeverityColor(issue.severity)}`}>
                                      {issue.severity}
                                    </span>
                                    <span className="font-medium text-gray-900">{issue.ruleName}</span>
                                    {issue.autoFixable && (
                                      <span className="px-2 py-1 text-xs bg-green-100 text-green-800 rounded-full">
                                        Auto-fixable
                                      </span>
                                    )}
                                  </div>
                                  <p className="text-gray-700 mb-2">{issue.message}</p>
                                  <p className="text-blue-600 text-sm mb-2">{issue.suggestion}</p>
                                  
                                  {issue.field && (
                                    <div className="text-xs text-gray-500 mb-1">
                                      <strong>Field:</strong> {issue.field}
                                    </div>
                                  )}
                                  
                                  {issue.currentValue && (
                                    <div className="text-xs text-gray-500 mb-1">
                                      <strong>Current Value:</strong> {JSON.stringify(issue.currentValue)}
                                    </div>
                                  )}
                                  
                                  {issue.expectedValue && (
                                    <div className="text-xs text-gray-500 mb-1">
                                      <strong>Expected Value:</strong> {JSON.stringify(issue.expectedValue)}
                                    </div>
                                  )}

                                  {issue.nigerianCompliance && (
                                    <div className="bg-blue-50 border border-blue-200 rounded p-2 mt-2">
                                      <div className="text-xs text-blue-800">
                                        <div><strong>🇳🇬 Regulatory Body:</strong> {issue.nigerianCompliance.regulatoryBody}</div>
                                        <div><strong>Requirement:</strong> {issue.nigerianCompliance.requirement}</div>
                                        <div><strong>Impact:</strong> {issue.nigerianCompliance.impact}</div>
                                      </div>
                                    </div>
                                  )}
                                </div>
                              </div>
                            </div>
                          ))}
                        </div>
                      </div>
                    )}
                  </div>
                ))}

                {/* Recommendations */}
                {selectedResult.recommendations.length > 0 && (
                  <div className="bg-green-50 border border-green-200 rounded-lg p-4">
                    <h4 className="font-medium text-green-900 mb-2">💡 Recommendations</h4>
                    <ul className="list-disc list-inside text-sm text-green-800 space-y-1">
                      {selectedResult.recommendations.map((recommendation, index) => (
                        <li key={index}>{recommendation}</li>
                      ))}
                    </ul>
                  </div>
                )}
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default ValidationProcess;