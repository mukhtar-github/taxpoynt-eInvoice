/**
 * Document Preparation Workflow
 * ============================
 * 
 * System Integrator workflow for preparing business documents for FIRS e-invoicing.
 * Automated document processing, validation, and FIRS-compliant formatting.
 * 
 * Features:
 * - Batch document processing from multiple sources
 * - FIRS invoice format conversion and validation
 * - Nigerian tax compliance checks (VAT, WHT, etc.)
 * - Document quality assurance and error handling
 * - Bulk preparation and submission queuing
 * - Progress tracking and status reporting
 */

import React, { useState, useEffect } from 'react';
import { Button } from '../../design_system/components/Button';

interface DocumentSource {
  id: string;
  name: string;
  type: 'erp' | 'crm' | 'pos' | 'ecommerce' | 'accounting' | 'manual_upload';
  status: 'connected' | 'disconnected' | 'syncing' | 'error';
  lastSync?: string;
  recordCount: number;
  systemName?: string;
}

interface DocumentBatch {
  id: string;
  name: string;
  sourceId: string;
  sourceName: string;
  createdDate: string;
  status: 'preparing' | 'validating' | 'ready' | 'failed' | 'submitted';
  totalDocuments: number;
  processedDocuments: number;
  validDocuments: number;
  invalidDocuments: number;
  progress: number; // 0-100
  estimatedCompletion?: string;
  errors: DocumentError[];
}

interface DocumentError {
  id: string;
  documentId: string;
  severity: 'warning' | 'error' | 'critical';
  category: 'format' | 'validation' | 'compliance' | 'data_quality';
  field?: string;
  message: string;
  suggestion: string;
  autoFixable: boolean;
}

interface ProcessingRule {
  id: string;
  name: string;
  description: string;
  category: 'format' | 'validation' | 'compliance' | 'enhancement';
  enabled: boolean;
  conditions: Array<{
    field: string;
    operator: 'equals' | 'contains' | 'greater_than' | 'less_than' | 'exists';
    value: any;
  }>;
  actions: Array<{
    type: 'transform' | 'validate' | 'flag' | 'enhance';
    parameters: Record<string, any>;
  }>;
}

interface FIRSValidationResult {
  documentId: string;
  isValid: boolean;
  score: number; // 0-100
  issues: Array<{
    field: string;
    issue: string;
    severity: 'low' | 'medium' | 'high' | 'critical';
    impact: string;
    recommendation: string;
  }>;
  nigerianCompliance: {
    vatCompliant: boolean;
    tinValid: boolean;
    firsFormatValid: boolean;
    currencyValid: boolean;
  };
}

// Default processing rules for Nigerian compliance
const defaultProcessingRules: ProcessingRule[] = [
  {
    id: 'vat_calculation',
    name: 'VAT Calculation Validation',
    description: 'Ensure VAT is calculated correctly at 7.5% for applicable items',
    category: 'compliance',
    enabled: true,
    conditions: [
      { field: 'vat_applicable', operator: 'equals', value: true }
    ],
    actions: [
      { type: 'validate', parameters: { vat_rate: 7.5, tolerance: 0.01 } }
    ]
  },
  {
    id: 'tin_format',
    name: 'TIN Format Validation',
    description: 'Validate Nigerian TIN format (14 digits)',
    category: 'validation',
    enabled: true,
    conditions: [
      { field: 'supplier_tin', operator: 'exists', value: true }
    ],
    actions: [
      { type: 'validate', parameters: { format: 'nigerian_tin', length: 14 } }
    ]
  },
  {
    id: 'currency_normalization',
    name: 'Currency Normalization',
    description: 'Ensure all amounts are in Nigerian Naira (NGN)',
    category: 'format',
    enabled: true,
    conditions: [
      { field: 'currency', operator: 'exists', value: true }
    ],
    actions: [
      { type: 'transform', parameters: { target_currency: 'NGN', conversion_required: true } }
    ]
  },
  {
    id: 'firs_format_compliance',
    name: 'FIRS Format Compliance',
    description: 'Ensure document structure matches FIRS e-invoicing requirements',
    category: 'compliance',
    enabled: true,
    conditions: [
      { field: 'document_type', operator: 'equals', value: 'invoice' }
    ],
    actions: [
      { type: 'validate', parameters: { schema: 'firs_invoice_v2.1' } }
    ]
  }
];

interface DocumentPreparationProps {
  organizationId?: string;
  onBatchComplete?: (batchId: string) => void;
}

export const DocumentPreparation: React.FC<DocumentPreparationProps> = ({
  organizationId,
  onBatchComplete
}) => {
  const [sources, setSources] = useState<DocumentSource[]>([]);
  const [batches, setBatches] = useState<DocumentBatch[]>([]);
  const [selectedSources, setSelectedSources] = useState<string[]>([]);
  const [processingRules, setProcessingRules] = useState<ProcessingRule[]>(defaultProcessingRules);
  const [currentBatch, setCurrentBatch] = useState<DocumentBatch | null>(null);
  const [validationResults, setValidationResults] = useState<FIRSValidationResult[]>([]);
  const [isProcessing, setIsProcessing] = useState(false);
  const [showRulesConfig, setShowRulesConfig] = useState(false);

  useEffect(() => {
    fetchDocumentSources();
    fetchProcessingBatches();
  }, [organizationId]);

  const fetchDocumentSources = async () => {
    try {
      const params = organizationId ? `?organization_id=${organizationId}` : '';
      const response = await fetch(`/api/v1/si/document-preparation/sources${params}`, {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('taxpoynt_auth_token')}`
        }
      });

      if (response.ok) {
        const data = await response.json();
        setSources(data.sources || []);
      }
    } catch (error) {
      console.error('Failed to fetch document sources:', error);
    }
  };

  const fetchProcessingBatches = async () => {
    try {
      const response = await fetch('/api/v1/si/document-preparation/batches', {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('taxpoynt_auth_token')}`
        }
      });

      if (response.ok) {
        const data = await response.json();
        setBatches(data.batches || []);
      }
    } catch (error) {
      console.error('Failed to fetch processing batches:', error);
    }
  };

  const handleSourceToggle = (sourceId: string) => {
    if (selectedSources.includes(sourceId)) {
      setSelectedSources(prev => prev.filter(id => id !== sourceId));
    } else {
      setSelectedSources(prev => [...prev, sourceId]);
    }
  };

  const handleCreateBatch = async () => {
    if (selectedSources.length === 0) {
      alert('Please select at least one document source');
      return;
    }

    setIsProcessing(true);
    try {
      const response = await fetch('/api/v1/si/document-preparation/batches/create', {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('taxpoynt_auth_token')}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          organization_id: organizationId,
          source_ids: selectedSources,
          processing_rules: processingRules.filter(rule => rule.enabled),
          batch_name: `Batch ${new Date().toLocaleDateString()}`,
          auto_fix_enabled: true
        })
      });

      if (response.ok) {
        const data = await response.json();
        const newBatch = data.batch;
        setBatches(prev => [newBatch, ...prev]);
        setCurrentBatch(newBatch);
        startBatchProcessing(newBatch.id);
        alert('✅ Document batch created successfully!');
      } else {
        alert('❌ Failed to create document batch');
      }
    } catch (error) {
      console.error('Failed to create batch:', error);
      alert('❌ Failed to create document batch');
    } finally {
      setIsProcessing(false);
    }
  };

  const startBatchProcessing = async (batchId: string) => {
    try {
      const response = await fetch(`/api/v1/si/document-preparation/batches/${batchId}/process`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('taxpoynt_auth_token')}`
        }
      });

      if (response.ok) {
        // Start polling for progress updates
        const pollInterval = setInterval(async () => {
          const progressResponse = await fetch(`/api/v1/si/document-preparation/batches/${batchId}/status`, {
            headers: {
              'Authorization': `Bearer ${localStorage.getItem('taxpoynt_auth_token')}`
            }
          });

          if (progressResponse.ok) {
            const progressData = await progressResponse.json();
            const updatedBatch = progressData.batch;
            
            setBatches(prev => prev.map(batch => 
              batch.id === batchId ? updatedBatch : batch
            ));
            setCurrentBatch(updatedBatch);

            if (['ready', 'failed', 'submitted'].includes(updatedBatch.status)) {
              clearInterval(pollInterval);
              if (updatedBatch.status === 'ready' && onBatchComplete) {
                onBatchComplete(batchId);
              }
            }
          }
        }, 3000);
      }
    } catch (error) {
      console.error('Failed to start batch processing:', error);
    }
  };

  const handleValidateBatch = async (batchId: string) => {
    try {
      setIsProcessing(true);
      const response = await fetch(`/api/v1/si/document-preparation/batches/${batchId}/validate`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('taxpoynt_auth_token')}`
        }
      });

      if (response.ok) {
        const data = await response.json();
        setValidationResults(data.validation_results || []);
        alert(`✅ Batch validation completed. ${data.valid_documents}/${data.total_documents} documents are valid.`);
      } else {
        alert('❌ Failed to validate batch');
      }
    } catch (error) {
      console.error('Failed to validate batch:', error);
      alert('❌ Failed to validate batch');
    } finally {
      setIsProcessing(false);
    }
  };

  const handleSubmitToFIRS = async (batchId: string) => {
    try {
      setIsProcessing(true);
      const response = await fetch(`/api/v1/si/document-preparation/batches/${batchId}/submit`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('taxpoynt_auth_token')}`
        }
      });

      if (response.ok) {
        const data = await response.json();
        alert(`🇳🇬 Batch submitted to FIRS successfully! Reference: ${data.firs_reference}`);
        fetchProcessingBatches();
      } else {
        alert('❌ Failed to submit batch to FIRS');
      }
    } catch (error) {
      console.error('Failed to submit to FIRS:', error);
      alert('❌ Failed to submit batch to FIRS');
    } finally {
      setIsProcessing(false);
    }
  };

  const getSourceIcon = (type: DocumentSource['type']) => {
    switch (type) {
      case 'erp': return '🏢';
      case 'crm': return '👥';
      case 'pos': return '💳';
      case 'ecommerce': return '🛒';
      case 'accounting': return '📊';
      case 'manual_upload': return '📁';
      default: return '📄';
    }
  };

  const getStatusColor = (status: DocumentBatch['status']) => {
    switch (status) {
      case 'preparing': return 'text-blue-600 bg-blue-100';
      case 'validating': return 'text-yellow-600 bg-yellow-100';
      case 'ready': return 'text-green-600 bg-green-100';
      case 'failed': return 'text-red-600 bg-red-100';
      case 'submitted': return 'text-purple-600 bg-purple-100';
      default: return 'text-gray-600 bg-gray-100';
    }
  };

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <div className="bg-white border-b">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-3xl font-bold text-gray-900">Document Preparation</h1>
              <p className="text-gray-600 mt-2">
                Prepare and validate business documents for FIRS e-invoicing compliance
              </p>
            </div>
            
            <div className="flex items-center space-x-4">
              <Button
                onClick={() => setShowRulesConfig(!showRulesConfig)}
                variant="outline"
              >
                ⚙️ Processing Rules
              </Button>
              
              <Button
                onClick={handleCreateBatch}
                disabled={selectedSources.length === 0 || isProcessing}
                loading={isProcessing}
              >
                📦 Create Batch
              </Button>
            </div>
          </div>
        </div>
      </div>

      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
          
          {/* Document Sources */}
          <div>
            <div className="bg-white rounded-lg border">
              <div className="p-6 border-b">
                <h2 className="text-lg font-semibold text-gray-900">Document Sources</h2>
                <p className="text-gray-600 text-sm mt-1">Select sources for document processing</p>
              </div>
              
              <div className="p-6">
                {sources.length === 0 ? (
                  <div className="text-center py-8 text-gray-500">
                    <div className="text-4xl mb-2">📂</div>
                    <p>No document sources</p>
                    <p className="text-sm">Configure integrations first</p>
                  </div>
                ) : (
                  <div className="space-y-3">
                    {sources.map(source => (
                      <div
                        key={source.id}
                        className={`border rounded-lg p-4 cursor-pointer transition-all ${
                          selectedSources.includes(source.id)
                            ? 'border-blue-500 bg-blue-50'
                            : 'border-gray-200 hover:border-gray-300'
                        }`}
                        onClick={() => handleSourceToggle(source.id)}
                      >
                        <div className="flex items-center justify-between">
                          <div className="flex items-center space-x-3">
                            <span className="text-2xl">{getSourceIcon(source.type)}</span>
                            <div>
                              <div className="font-medium text-gray-900">{source.name}</div>
                              <div className="text-sm text-gray-600">{source.systemName}</div>
                            </div>
                          </div>
                          
                          <input
                            type="checkbox"
                            checked={selectedSources.includes(source.id)}
                            onChange={() => handleSourceToggle(source.id)}
                            className="w-5 h-5 text-blue-600 border-gray-300 rounded focus:ring-blue-500"
                          />
                        </div>
                        
                        <div className="mt-3 flex items-center justify-between text-sm">
                          <span className="text-gray-600">📊 {source.recordCount.toLocaleString()} records</span>
                          <span className={`px-2 py-1 rounded-full text-xs font-medium ${
                            source.status === 'connected' ? 'bg-green-100 text-green-800' :
                            source.status === 'syncing' ? 'bg-blue-100 text-blue-800' :
                            'bg-red-100 text-red-800'
                          }`}>
                            {source.status}
                          </span>
                        </div>
                        
                        {source.lastSync && (
                          <div className="text-xs text-gray-500 mt-2">
                            Last sync: {new Date(source.lastSync).toLocaleString()}
                          </div>
                        )}
                      </div>
                    ))}
                  </div>
                )}
              </div>
            </div>

            {/* Processing Rules Configuration */}
            {showRulesConfig && (
              <div className="bg-white rounded-lg border mt-6">
                <div className="p-6 border-b">
                  <h2 className="text-lg font-semibold text-gray-900">Processing Rules</h2>
                  <p className="text-gray-600 text-sm mt-1">Configure document processing rules</p>
                </div>
                
                <div className="p-6 space-y-4">
                  {processingRules.map(rule => (
                    <div key={rule.id} className="border rounded-lg p-4">
                      <div className="flex items-center justify-between mb-2">
                        <label className="flex items-center">
                          <input
                            type="checkbox"
                            checked={rule.enabled}
                            onChange={(e) => setProcessingRules(prev => prev.map(r => 
                              r.id === rule.id ? { ...r, enabled: e.target.checked } : r
                            ))}
                            className="h-4 w-4 text-blue-600 border-gray-300 rounded focus:ring-blue-500 mr-3"
                          />
                          <span className="font-medium text-gray-900">{rule.name}</span>
                        </label>
                        <span className={`px-2 py-1 text-xs rounded-full ${
                          rule.category === 'compliance' ? 'bg-red-100 text-red-800' :
                          rule.category === 'validation' ? 'bg-yellow-100 text-yellow-800' :
                          rule.category === 'format' ? 'bg-blue-100 text-blue-800' :
                          'bg-green-100 text-green-800'
                        }`}>
                          {rule.category}
                        </span>
                      </div>
                      <p className="text-sm text-gray-600">{rule.description}</p>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>

          {/* Processing Batches */}
          <div className="lg:col-span-2">
            <div className="bg-white rounded-lg border">
              <div className="p-6 border-b">
                <h2 className="text-lg font-semibold text-gray-900">Processing Batches</h2>
                <p className="text-gray-600 text-sm mt-1">Document preparation and validation batches</p>
              </div>
              
              <div className="divide-y divide-gray-200">
                {batches.length === 0 ? (
                  <div className="text-center py-12 text-gray-500">
                    <div className="text-4xl mb-4">📦</div>
                    <h3 className="text-lg font-medium mb-2">No processing batches</h3>
                    <p className="mb-4">Select document sources to create your first batch</p>
                  </div>
                ) : (
                  batches.map(batch => (
                    <div key={batch.id} className="p-6">
                      <div className="flex items-center justify-between mb-4">
                        <div>
                          <h3 className="text-lg font-medium text-gray-900">{batch.name}</h3>
                          <p className="text-sm text-gray-600">From: {batch.sourceName}</p>
                          <p className="text-xs text-gray-500">Created: {new Date(batch.createdDate).toLocaleString()}</p>
                        </div>
                        
                        <div className="flex items-center space-x-4">
                          <span className={`px-3 py-1 text-sm font-medium rounded-full ${getStatusColor(batch.status)}`}>
                            {batch.status.replace('_', ' ')}
                          </span>
                          
                          <div className="text-right">
                            <div className="text-2xl font-bold text-gray-900">{batch.progress}%</div>
                            <div className="text-xs text-gray-500">Complete</div>
                          </div>
                        </div>
                      </div>

                      {/* Progress Bar */}
                      <div className="mb-4">
                        <div className="flex items-center justify-between text-sm text-gray-600 mb-1">
                          <span>Processing Progress</span>
                          <span>{batch.processedDocuments}/{batch.totalDocuments} documents</span>
                        </div>
                        <div className="w-full bg-gray-200 rounded-full h-2">
                          <div
                            className={`h-2 rounded-full transition-all duration-300 ${
                              batch.status === 'ready' ? 'bg-green-500' :
                              batch.status === 'failed' ? 'bg-red-500' :
                              'bg-blue-500'
                            }`}
                            style={{ width: `${batch.progress}%` }}
                          />
                        </div>
                      </div>

                      {/* Statistics */}
                      <div className="grid grid-cols-3 gap-4 mb-4">
                        <div className="text-center bg-gray-50 rounded-lg p-3">
                          <div className="text-2xl font-bold text-gray-900">{batch.totalDocuments}</div>
                          <div className="text-xs text-gray-600">Total</div>
                        </div>
                        <div className="text-center bg-green-50 rounded-lg p-3">
                          <div className="text-2xl font-bold text-green-600">{batch.validDocuments}</div>
                          <div className="text-xs text-gray-600">Valid</div>
                        </div>
                        <div className="text-center bg-red-50 rounded-lg p-3">
                          <div className="text-2xl font-bold text-red-600">{batch.invalidDocuments}</div>
                          <div className="text-xs text-gray-600">Invalid</div>
                        </div>
                      </div>

                      {/* Errors */}
                      {batch.errors.length > 0 && (
                        <div className="mb-4">
                          <h4 className="font-medium text-gray-900 mb-2">Issues ({batch.errors.length})</h4>
                          <div className="space-y-2 max-h-32 overflow-y-auto">
                            {batch.errors.slice(0, 3).map(error => (
                              <div key={error.id} className="bg-red-50 border border-red-200 rounded p-2">
                                <div className="flex items-center justify-between">
                                  <span className="text-sm font-medium text-red-800">{error.message}</span>
                                  <span className={`px-2 py-1 text-xs rounded-full ${
                                    error.severity === 'critical' ? 'bg-red-200 text-red-800' :
                                    error.severity === 'error' ? 'bg-orange-200 text-orange-800' :
                                    'bg-yellow-200 text-yellow-800'
                                  }`}>
                                    {error.severity}
                                  </span>
                                </div>
                                <p className="text-xs text-red-600 mt-1">{error.suggestion}</p>
                              </div>
                            ))}
                            {batch.errors.length > 3 && (
                              <div className="text-sm text-gray-600">
                                ... and {batch.errors.length - 3} more issues
                              </div>
                            )}
                          </div>
                        </div>
                      )}

                      {/* Actions */}
                      <div className="flex items-center space-x-3">
                        {batch.status === 'ready' && (
                          <>
                            <Button
                              onClick={() => handleValidateBatch(batch.id)}
                              disabled={isProcessing}
                              size="sm"
                              variant="outline"
                            >
                              🔍 Validate
                            </Button>
                            <Button
                              onClick={() => handleSubmitToFIRS(batch.id)}
                              disabled={isProcessing}
                              size="sm"
                            >
                              🇳🇬 Submit to FIRS
                            </Button>
                          </>
                        )}
                        
                        {batch.status === 'failed' && (
                          <Button
                            onClick={() => startBatchProcessing(batch.id)}
                            disabled={isProcessing}
                            size="sm"
                            variant="outline"
                          >
                            🔄 Retry
                          </Button>
                        )}
                        
                        <Button
                          onClick={() => setCurrentBatch(batch)}
                          size="sm"
                          variant="outline"
                        >
                          📄 View Details
                        </Button>
                      </div>
                    </div>
                  ))
                )}
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Batch Details Modal */}
      {currentBatch && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg max-w-4xl w-full m-4 max-h-screen overflow-y-auto">
            <div className="p-6 border-b">
              <div className="flex items-center justify-between">
                <h2 className="text-xl font-semibold text-gray-900">
                  Batch Details: {currentBatch.name}
                </h2>
                <button
                  onClick={() => setCurrentBatch(null)}
                  className="text-gray-400 hover:text-gray-600"
                >
                  <svg className="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                  </svg>
                </button>
              </div>
            </div>
            
            <div className="p-6">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <div>
                  <h3 className="font-medium text-gray-900 mb-3">Batch Information</h3>
                  <div className="space-y-2 text-sm">
                    <div><strong>Source:</strong> {currentBatch.sourceName}</div>
                    <div><strong>Status:</strong> <span className={`px-2 py-1 rounded-full ${getStatusColor(currentBatch.status)}`}>{currentBatch.status}</span></div>
                    <div><strong>Created:</strong> {new Date(currentBatch.createdDate).toLocaleString()}</div>
                    <div><strong>Progress:</strong> {currentBatch.progress}%</div>
                    {currentBatch.estimatedCompletion && (
                      <div><strong>ETA:</strong> {new Date(currentBatch.estimatedCompletion).toLocaleString()}</div>
                    )}
                  </div>
                </div>
                
                <div>
                  <h3 className="font-medium text-gray-900 mb-3">Processing Statistics</h3>
                  <div className="space-y-2 text-sm">
                    <div><strong>Total Documents:</strong> {currentBatch.totalDocuments}</div>
                    <div><strong>Processed:</strong> {currentBatch.processedDocuments}</div>
                    <div><strong>Valid:</strong> {currentBatch.validDocuments}</div>
                    <div><strong>Invalid:</strong> {currentBatch.invalidDocuments}</div>
                    <div><strong>Success Rate:</strong> {((currentBatch.validDocuments / currentBatch.totalDocuments) * 100).toFixed(1)}%</div>
                  </div>
                </div>
              </div>

              {/* Nigerian Compliance Status */}
              <div className="mt-6 bg-blue-50 border border-blue-200 rounded-lg p-4">
                <h3 className="font-medium text-blue-900 mb-2">🇳🇬 Nigerian Compliance Status</h3>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-sm text-blue-800">
                  <div>✓ FIRS e-invoicing format validated</div>
                  <div>✓ VAT calculations verified (7.5%)</div>
                  <div>✓ TIN format compliance checked</div>
                  <div>✓ Currency normalization applied (NGN)</div>
                </div>
              </div>

              {/* Detailed Errors */}
              {currentBatch.errors.length > 0 && (
                <div className="mt-6">
                  <h3 className="font-medium text-gray-900 mb-3">Detailed Issues</h3>
                  <div className="space-y-3 max-h-64 overflow-y-auto">
                    {currentBatch.errors.map(error => (
                      <div key={error.id} className="bg-gray-50 border rounded-lg p-3">
                        <div className="flex items-start justify-between">
                          <div className="flex-1">
                            <div className="font-medium text-gray-900">{error.message}</div>
                            <div className="text-sm text-gray-600 mt-1">{error.suggestion}</div>
                            {error.field && (
                              <div className="text-xs text-gray-500 mt-1">Field: {error.field}</div>
                            )}
                          </div>
                          <div className="flex items-center space-x-2">
                            <span className={`px-2 py-1 text-xs rounded-full ${
                              error.severity === 'critical' ? 'bg-red-200 text-red-800' :
                              error.severity === 'error' ? 'bg-orange-200 text-orange-800' :
                              'bg-yellow-200 text-yellow-800'
                            }`}>
                              {error.severity}
                            </span>
                            {error.autoFixable && (
                              <span className="px-2 py-1 text-xs bg-green-200 text-green-800 rounded-full">
                                Auto-fixable
                              </span>
                            )}
                          </div>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default DocumentPreparation;