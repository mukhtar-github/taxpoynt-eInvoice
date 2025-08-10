/**
 * Document Processing Component
 * ============================
 * 
 * System Integrator interface for processing business documents through the TaxPoynt pipeline.
 * Handles document ingestion, transformation, validation, and FIRS-compliant output generation.
 * 
 * Features:
 * - Multi-format document processing (PDF, XML, JSON, CSV, Excel)
 * - Intelligent document parsing and data extraction
 * - FIRS e-invoicing format conversion
 * - Nigerian tax compliance validation
 * - Batch processing with progress tracking
 * - Quality assurance and error handling
 * - Document workflow management
 */

import React, { useState, useEffect } from 'react';
import { Button } from '../../../design_system/components/Button';

interface DocumentTemplate {
  id: string;
  name: string;
  description: string;
  documentType: 'invoice' | 'receipt' | 'purchase_order' | 'delivery_note' | 'credit_note';
  inputFormat: 'pdf' | 'xml' | 'json' | 'csv' | 'excel' | 'image';
  outputFormat: 'firs_json' | 'firs_xml' | 'pdf' | 'json';
  processingRules: ProcessingRule[];
  fieldMappings: FieldMapping[];
  validationRules: ValidationRule[];
  nigerianCompliance: {
    firsCompliant: boolean;
    vatCalculation: boolean;
    tinValidation: boolean;
    currencyNormalization: boolean;
  };
  usage: {
    timesUsed: number;
    lastUsed?: string;
    successRate: number;
  };
}

interface ProcessingRule {
  id: string;
  name: string;
  description: string;
  enabled: boolean;
  order: number;
  ruleType: 'extraction' | 'transformation' | 'validation' | 'formatting';
  conditions: Array<{
    field: string;
    operator: 'exists' | 'equals' | 'contains' | 'matches' | 'greater_than' | 'less_than';
    value: any;
  }>;
  actions: Array<{
    type: 'extract' | 'transform' | 'validate' | 'format' | 'calculate';
    parameters: Record<string, any>;
  }>;
}

interface FieldMapping {
  id: string;
  sourceField: string;
  targetField: string;
  dataType: 'string' | 'number' | 'date' | 'boolean' | 'array' | 'object';
  required: boolean;
  transformation?: {
    type: 'format' | 'calculate' | 'lookup' | 'conditional';
    formula?: string;
    lookupTable?: Record<string, any>;
    conditions?: Array<{
      condition: string;
      value: any;
    }>;
  };
  validation?: {
    pattern?: string;
    min?: number;
    max?: number;
    enum?: string[];
  };
}

interface ValidationRule {
  id: string;
  name: string;
  field: string;
  ruleType: 'required' | 'format' | 'range' | 'custom';
  parameters: Record<string, any>;
  errorMessage: string;
  severity: 'info' | 'warning' | 'error' | 'critical';
}

interface ProcessingJob {
  id: string;
  name: string;
  templateId: string;
  templateName: string;
  status: 'queued' | 'processing' | 'completed' | 'failed' | 'cancelled';
  startTime: string;
  endTime?: string;
  progress: number; // 0-100
  documentsTotal: number;
  documentsProcessed: number;
  documentsSuccessful: number;
  documentsFailed: number;
  currentStage: 'ingestion' | 'parsing' | 'extraction' | 'transformation' | 'validation' | 'output';
  errors: ProcessingError[];
  outputFiles: Array<{
    filename: string;
    format: string;
    size: number;
    downloadUrl: string;
  }>;
  qualityScore: number; // 0-100
  complianceStatus: {
    firsCompliant: boolean;
    vatValid: boolean;
    tinValid: boolean;
    currencyValid: boolean;
    overallScore: number;
  };
}

interface ProcessingError {
  id: string;
  documentId?: string;
  stage: ProcessingJob['currentStage'];
  severity: 'info' | 'warning' | 'error' | 'critical';
  category: 'parsing' | 'extraction' | 'transformation' | 'validation' | 'compliance';
  message: string;
  details: string;
  field?: string;
  suggestion: string;
  timestamp: string;
  autoFixable: boolean;
}

interface ProcessingStats {
  totalJobs: number;
  activeJobs: number;
  completedJobs: number;
  failedJobs: number;
  documentsProcessedToday: number;
  averageProcessingTime: number; // seconds
  qualityScore: number; // 0-100
  complianceRate: number; // 0-100
}

// Mock document templates
const mockTemplates: DocumentTemplate[] = [
  {
    id: 'template_invoice_001',
    name: 'Standard Invoice Template',
    description: 'Template for processing standard business invoices to FIRS format',
    documentType: 'invoice',
    inputFormat: 'pdf',
    outputFormat: 'firs_json',
    processingRules: [],
    fieldMappings: [],
    validationRules: [],
    nigerianCompliance: {
      firsCompliant: true,
      vatCalculation: true,
      tinValidation: true,
      currencyNormalization: true
    },
    usage: {
      timesUsed: 1250,
      lastUsed: '2024-01-15T14:30:00Z',
      successRate: 94.5
    }
  },
  {
    id: 'template_receipt_001',
    name: 'POS Receipt Template',
    description: 'Template for processing POS receipts from Nigerian payment systems',
    documentType: 'receipt',
    inputFormat: 'json',
    outputFormat: 'firs_json',
    processingRules: [],
    fieldMappings: [],
    validationRules: [],
    nigerianCompliance: {
      firsCompliant: true,
      vatCalculation: true,
      tinValidation: true,
      currencyNormalization: true
    },
    usage: {
      timesUsed: 850,
      lastUsed: '2024-01-15T16:45:00Z',
      successRate: 98.2
    }
  },
  {
    id: 'template_excel_001',
    name: 'Excel Invoice Batch',
    description: 'Template for processing Excel files with multiple invoices',
    documentType: 'invoice',
    inputFormat: 'excel',
    outputFormat: 'firs_json',
    processingRules: [],
    fieldMappings: [],
    validationRules: [],
    nigerianCompliance: {
      firsCompliant: true,
      vatCalculation: true,
      tinValidation: true,
      currencyNormalization: true
    },
    usage: {
      timesUsed: 425,
      lastUsed: '2024-01-14T10:20:00Z',
      successRate: 89.7
    }
  }
];

const mockJobs: ProcessingJob[] = [
  {
    id: 'job_001',
    name: 'Morning Invoice Batch',
    templateId: 'template_invoice_001',
    templateName: 'Standard Invoice Template',
    status: 'completed',
    startTime: '2024-01-15T08:00:00Z',
    endTime: '2024-01-15T08:45:00Z',
    progress: 100,
    documentsTotal: 45,
    documentsProcessed: 45,
    documentsSuccessful: 42,
    documentsFailed: 3,
    currentStage: 'output',
    errors: [],
    outputFiles: [
      {
        filename: 'invoice_batch_20240115.json',
        format: 'FIRS JSON',
        size: 125000,
        downloadUrl: '/downloads/invoice_batch_20240115.json'
      }
    ],
    qualityScore: 93.3,
    complianceStatus: {
      firsCompliant: true,
      vatValid: true,
      tinValid: true,
      currencyValid: true,
      overallScore: 96.5
    }
  },
  {
    id: 'job_002',
    name: 'POS Receipt Processing',
    templateId: 'template_receipt_001',
    templateName: 'POS Receipt Template',
    status: 'processing',
    startTime: '2024-01-15T16:30:00Z',
    progress: 65,
    documentsTotal: 120,
    documentsProcessed: 78,
    documentsSuccessful: 76,
    documentsFailed: 2,
    currentStage: 'validation',
    errors: [],
    outputFiles: [],
    qualityScore: 97.4,
    complianceStatus: {
      firsCompliant: true,
      vatValid: true,
      tinValid: true,
      currencyValid: true,
      overallScore: 95.2
    }
  }
];

interface DocumentProcessorProps {
  organizationId?: string;
  onProcessingComplete?: (jobId: string) => void;
}

export const DocumentProcessor: React.FC<DocumentProcessorProps> = ({
  organizationId,
  onProcessingComplete
}) => {
  const [templates, setTemplates] = useState<DocumentTemplate[]>(mockTemplates);
  const [processingJobs, setProcessingJobs] = useState<ProcessingJob[]>(mockJobs);
  const [stats, setStats] = useState<ProcessingStats | null>(null);
  const [selectedTemplate, setSelectedTemplate] = useState<DocumentTemplate | null>(null);
  const [selectedJob, setSelectedJob] = useState<ProcessingJob | null>(null);
  const [showNewJob, setShowNewJob] = useState(false);
  const [uploadedFiles, setUploadedFiles] = useState<File[]>([]);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    fetchTemplates();
    fetchProcessingJobs();
    calculateStats();
  }, [organizationId]);

  const fetchTemplates = async () => {
    try {
      const response = await fetch('/api/v1/si/document-processing/templates', {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('taxpoynt_auth_token')}`
        }
      });

      if (response.ok) {
        const data = await response.json();
        setTemplates(data.templates || mockTemplates);
      }
    } catch (error) {
      console.error('Failed to fetch templates:', error);
      setTemplates(mockTemplates);
    } finally {
      setIsLoading(false);
    }
  };

  const fetchProcessingJobs = async () => {
    try {
      const response = await fetch('/api/v1/si/document-processing/jobs', {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('taxpoynt_auth_token')}`
        }
      });

      if (response.ok) {
        const data = await response.json();
        setProcessingJobs(data.jobs || mockJobs);
      }
    } catch (error) {
      console.error('Failed to fetch processing jobs:', error);
      setProcessingJobs(mockJobs);
    }
  };

  const calculateStats = () => {
    const totalJobs = processingJobs.length;
    const activeJobs = processingJobs.filter(job => ['queued', 'processing'].includes(job.status)).length;
    const completedJobs = processingJobs.filter(job => job.status === 'completed').length;
    const failedJobs = processingJobs.filter(job => job.status === 'failed').length;
    
    const documentsProcessedToday = processingJobs
      .filter(job => new Date(job.startTime).toDateString() === new Date().toDateString())
      .reduce((sum, job) => sum + job.documentsProcessed, 0);

    const completedJobsWithTime = processingJobs.filter(job => job.endTime);
    const averageProcessingTime = completedJobsWithTime.length > 0
      ? completedJobsWithTime.reduce((sum, job) => {
          const duration = new Date(job.endTime!).getTime() - new Date(job.startTime).getTime();
          return sum + (duration / 1000);
        }, 0) / completedJobsWithTime.length
      : 0;

    const qualityScore = processingJobs.length > 0
      ? processingJobs.reduce((sum, job) => sum + job.qualityScore, 0) / processingJobs.length
      : 100;

    const complianceRate = processingJobs.length > 0
      ? processingJobs.reduce((sum, job) => sum + job.complianceStatus.overallScore, 0) / processingJobs.length
      : 100;

    setStats({
      totalJobs,
      activeJobs,
      completedJobs,
      failedJobs,
      documentsProcessedToday,
      averageProcessingTime,
      qualityScore,
      complianceRate
    });
  };

  const handleFileUpload = (event: React.ChangeEvent<HTMLInputElement>) => {
    const files = Array.from(event.target.files || []);
    setUploadedFiles(files);
  };

  const handleStartProcessing = async (templateId: string) => {
    if (uploadedFiles.length === 0) {
      alert('Please upload files to process');
      return;
    }

    try {
      const formData = new FormData();
      formData.append('template_id', templateId);
      formData.append('organization_id', organizationId || '');
      
      uploadedFiles.forEach((file, index) => {
        formData.append(`files[${index}]`, file);
      });

      const response = await fetch('/api/v1/si/document-processing/jobs/create', {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('taxpoynt_auth_token')}`
        },
        body: formData
      });

      if (response.ok) {
        const data = await response.json();
        const newJob = data.job;
        setProcessingJobs(prev => [newJob, ...prev]);
        setUploadedFiles([]);
        setShowNewJob(false);
        alert('✅ Document processing job started successfully!');
        
        // Start polling for progress
        pollJobProgress(newJob.id);
        
        if (onProcessingComplete) {
          onProcessingComplete(newJob.id);
        }
      } else {
        alert('❌ Failed to start document processing job');
      }
    } catch (error) {
      console.error('Failed to start processing:', error);
      alert('❌ Failed to start document processing job');
    }
  };

  const pollJobProgress = (jobId: string) => {
    const pollInterval = setInterval(async () => {
      try {
        const response = await fetch(`/api/v1/si/document-processing/jobs/${jobId}/status`, {
          headers: {
            'Authorization': `Bearer ${localStorage.getItem('taxpoynt_auth_token')}`
          }
        });

        if (response.ok) {
          const data = await response.json();
          const updatedJob = data.job;
          
          setProcessingJobs(prev => prev.map(job => 
            job.id === jobId ? updatedJob : job
          ));

          if (['completed', 'failed', 'cancelled'].includes(updatedJob.status)) {
            clearInterval(pollInterval);
            if (updatedJob.status === 'completed' && onProcessingComplete) {
              onProcessingComplete(jobId);
            }
          }
        }
      } catch (error) {
        console.error('Failed to poll job progress:', error);
        clearInterval(pollInterval);
      }
    }, 3000);
  };

  const getStatusIcon = (status: ProcessingJob['status']) => {
    switch (status) {
      case 'completed': return '✅';
      case 'failed': return '❌';
      case 'processing': return '🔄';
      case 'queued': return '⏳';
      case 'cancelled': return '🚫';
      default: return '❓';
    }
  };

  const getStatusColor = (status: ProcessingJob['status']) => {
    switch (status) {
      case 'completed': return 'text-green-600 bg-green-100';
      case 'failed': return 'text-red-600 bg-red-100';
      case 'processing': return 'text-blue-600 bg-blue-100';
      case 'queued': return 'text-yellow-600 bg-yellow-100';
      case 'cancelled': return 'text-gray-600 bg-gray-100';
      default: return 'text-gray-600 bg-gray-100';
    }
  };

  const getStageIcon = (stage: ProcessingJob['currentStage']) => {
    switch (stage) {
      case 'ingestion': return '📥';
      case 'parsing': return '🔍';
      case 'extraction': return '📊';
      case 'transformation': return '🔄';
      case 'validation': return '✔️';
      case 'output': return '📤';
      default: return '❓';
    }
  };

  if (isLoading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <div className="text-4xl mb-4">📄</div>
          <h2 className="text-xl font-semibold text-gray-900 mb-2">Loading Document Processor</h2>
          <p className="text-gray-600">Fetching templates and processing jobs...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Stats Dashboard */}
      {stats && (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
          <div className="bg-white rounded-lg border p-6">
            <div className="flex items-center">
              <div className="p-3 rounded-full bg-blue-100">
                <span className="text-blue-600 text-xl">📄</span>
              </div>
              <div className="ml-4">
                <p className="text-sm font-medium text-gray-600">Active Jobs</p>
                <p className="text-2xl font-bold text-gray-900">{stats.activeJobs}</p>
              </div>
            </div>
          </div>

          <div className="bg-white rounded-lg border p-6">
            <div className="flex items-center">
              <div className="p-3 rounded-full bg-green-100">
                <span className="text-green-600 text-xl">📊</span>
              </div>
              <div className="ml-4">
                <p className="text-sm font-medium text-gray-600">Docs Today</p>
                <p className="text-2xl font-bold text-gray-900">{stats.documentsProcessedToday}</p>
              </div>
            </div>
          </div>

          <div className="bg-white rounded-lg border p-6">
            <div className="flex items-center">
              <div className="p-3 rounded-full bg-purple-100">
                <span className="text-purple-600 text-xl">🎯</span>
              </div>
              <div className="ml-4">
                <p className="text-sm font-medium text-gray-600">Quality Score</p>
                <p className="text-2xl font-bold text-gray-900">{stats.qualityScore.toFixed(1)}%</p>
              </div>
            </div>
          </div>

          <div className="bg-white rounded-lg border p-6">
            <div className="flex items-center">
              <div className="p-3 rounded-full bg-yellow-100">
                <span className="text-yellow-600 text-xl">🇳🇬</span>
              </div>
              <div className="ml-4">
                <p className="text-sm font-medium text-gray-600">Compliance</p>
                <p className="text-2xl font-bold text-gray-900">{stats.complianceRate.toFixed(1)}%</p>
              </div>
            </div>
          </div>
        </div>
      )}

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        
        {/* Document Templates */}
        <div className="bg-white rounded-lg border">
          <div className="p-6 border-b">
            <div className="flex items-center justify-between">
              <div>
                <h2 className="text-lg font-semibold text-gray-900">Processing Templates</h2>
                <p className="text-gray-600 text-sm mt-1">Document processing templates</p>
              </div>
              
              <Button
                onClick={() => setShowNewJob(true)}
              >
                📤 Process Documents
              </Button>
            </div>
          </div>
          
          <div className="divide-y divide-gray-200">
            {templates.map(template => (
              <div key={template.id} className="p-6">
                <div className="flex items-center justify-between mb-3">
                  <div>
                    <h3 className="font-medium text-gray-900">{template.name}</h3>
                    <p className="text-sm text-gray-600">{template.description}</p>
                  </div>
                  
                  <div className="flex items-center space-x-2">
                    <span className="px-2 py-1 text-xs bg-gray-100 text-gray-700 rounded-full">
                      {template.inputFormat.toUpperCase()}
                    </span>
                    <span className="text-gray-400">→</span>
                    <span className="px-2 py-1 text-xs bg-blue-100 text-blue-700 rounded-full">
                      {template.outputFormat.toUpperCase()}
                    </span>
                  </div>
                </div>

                <div className="grid grid-cols-2 gap-4 mb-3 text-sm">
                  <div>
                    <span className="text-gray-600">Usage:</span>
                    <span className="font-medium text-gray-900 ml-2">{template.usage.timesUsed}</span>
                  </div>
                  <div>
                    <span className="text-gray-600">Success Rate:</span>
                    <span className="font-medium text-gray-900 ml-2">{template.usage.successRate}%</span>
                  </div>
                </div>

                {/* Nigerian Compliance Status */}
                <div className="bg-blue-50 border border-blue-200 rounded-lg p-3 mb-3">
                  <div className="text-blue-900 text-sm font-medium mb-2">🇳🇬 Nigerian Compliance</div>
                  <div className="grid grid-cols-2 gap-2 text-xs">
                    <div className="flex items-center">
                      <span className={template.nigerianCompliance.firsCompliant ? 'text-green-600' : 'text-red-600'}>
                        {template.nigerianCompliance.firsCompliant ? '✅' : '❌'}
                      </span>
                      <span className="ml-1 text-blue-800">FIRS Format</span>
                    </div>
                    <div className="flex items-center">
                      <span className={template.nigerianCompliance.vatCalculation ? 'text-green-600' : 'text-red-600'}>
                        {template.nigerianCompliance.vatCalculation ? '✅' : '❌'}
                      </span>
                      <span className="ml-1 text-blue-800">VAT Calc</span>
                    </div>
                    <div className="flex items-center">
                      <span className={template.nigerianCompliance.tinValidation ? 'text-green-600' : 'text-red-600'}>
                        {template.nigerianCompliance.tinValidation ? '✅' : '❌'}
                      </span>
                      <span className="ml-1 text-blue-800">TIN Valid</span>
                    </div>
                    <div className="flex items-center">
                      <span className={template.nigerianCompliance.currencyNormalization ? 'text-green-600' : 'text-red-600'}>
                        {template.nigerianCompliance.currencyNormalization ? '✅' : '❌'}
                      </span>
                      <span className="ml-1 text-blue-800">Currency</span>
                    </div>
                  </div>
                </div>

                {template.usage.lastUsed && (
                  <div className="text-xs text-gray-500 mb-3">
                    Last used: {new Date(template.usage.lastUsed).toLocaleString()}
                  </div>
                )}

                <div className="flex items-center space-x-2">
                  <Button
                    onClick={() => setSelectedTemplate(template)}
                    size="sm"
                    variant="outline"
                  >
                    📋 Details
                  </Button>
                  
                  <Button
                    onClick={() => {
                      setSelectedTemplate(template);
                      setShowNewJob(true);
                    }}
                    size="sm"
                  >
                    🚀 Use Template
                  </Button>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Processing Jobs */}
        <div className="lg:col-span-2 bg-white rounded-lg border">
          <div className="p-6 border-b">
            <h2 className="text-lg font-semibold text-gray-900">Processing Jobs</h2>
            <p className="text-gray-600 text-sm mt-1">Recent document processing jobs</p>
          </div>
          
          <div className="divide-y divide-gray-200">
            {processingJobs.length === 0 ? (
              <div className="text-center py-12 text-gray-500">
                <div className="text-4xl mb-4">📄</div>
                <h3 className="text-lg font-medium mb-2">No processing jobs</h3>
                <p className="mb-4">Upload documents to start processing</p>
              </div>
            ) : (
              processingJobs.map(job => (
                <div key={job.id} className="p-6">
                  <div className="flex items-center justify-between mb-4">
                    <div>
                      <h3 className="font-medium text-gray-900">{job.name}</h3>
                      <p className="text-sm text-gray-600">Template: {job.templateName}</p>
                      <p className="text-xs text-gray-500">Started: {new Date(job.startTime).toLocaleString()}</p>
                    </div>
                    
                    <div className="flex items-center space-x-2">
                      <span className={`px-2 py-1 text-xs font-medium rounded-full ${getStatusColor(job.status)}`}>
                        {getStatusIcon(job.status)} {job.status}
                      </span>
                      
                      {job.status === 'processing' && (
                        <span className="px-2 py-1 text-xs bg-blue-100 text-blue-700 rounded-full">
                          {getStageIcon(job.currentStage)} {job.currentStage}
                        </span>
                      )}
                    </div>
                  </div>

                  {/* Progress Bar */}
                  {job.status === 'processing' && (
                    <div className="mb-4">
                      <div className="flex items-center justify-between text-sm text-gray-600 mb-1">
                        <span>Progress</span>
                        <span>{job.progress}%</span>
                      </div>
                      <div className="w-full bg-gray-200 rounded-full h-2">
                        <div
                          className="bg-blue-500 h-2 rounded-full transition-all duration-300"
                          style={{ width: `${job.progress}%` }}
                        />
                      </div>
                    </div>
                  )}

                  <div className="grid grid-cols-4 gap-4 mb-4">
                    <div className="text-center bg-gray-50 rounded p-3">
                      <div className="text-lg font-bold text-gray-900">{job.documentsTotal}</div>
                      <div className="text-xs text-gray-600">Total</div>
                    </div>
                    <div className="text-center bg-blue-50 rounded p-3">
                      <div className="text-lg font-bold text-blue-600">{job.documentsProcessed}</div>
                      <div className="text-xs text-gray-600">Processed</div>
                    </div>
                    <div className="text-center bg-green-50 rounded p-3">
                      <div className="text-lg font-bold text-green-600">{job.documentsSuccessful}</div>
                      <div className="text-xs text-gray-600">Success</div>
                    </div>
                    <div className="text-center bg-red-50 rounded p-3">
                      <div className="text-lg font-bold text-red-600">{job.documentsFailed}</div>
                      <div className="text-xs text-gray-600">Failed</div>
                    </div>
                  </div>

                  {/* Quality and Compliance Scores */}
                  <div className="grid grid-cols-2 gap-4 mb-4">
                    <div className="bg-purple-50 border border-purple-200 rounded-lg p-3">
                      <div className="text-purple-900 text-sm font-medium">Quality Score</div>
                      <div className="text-2xl font-bold text-purple-600">{job.qualityScore.toFixed(1)}%</div>
                    </div>
                    <div className="bg-blue-50 border border-blue-200 rounded-lg p-3">
                      <div className="text-blue-900 text-sm font-medium">🇳🇬 Compliance</div>
                      <div className="text-2xl font-bold text-blue-600">{job.complianceStatus.overallScore.toFixed(1)}%</div>
                    </div>
                  </div>

                  {/* Output Files */}
                  {job.outputFiles.length > 0 && (
                    <div className="mb-4">
                      <div className="text-sm font-medium text-gray-900 mb-2">Output Files</div>
                      {job.outputFiles.map((file, index) => (
                        <div key={index} className="flex items-center justify-between bg-gray-50 rounded p-2">
                          <div>
                            <div className="text-sm font-medium text-gray-900">{file.filename}</div>
                            <div className="text-xs text-gray-600">{file.format} • {(file.size / 1024).toFixed(1)} KB</div>
                          </div>
                          <Button
                            onClick={() => window.open(file.downloadUrl, '_blank')}
                            size="sm"
                            variant="outline"
                          >
                            💾 Download
                          </Button>
                        </div>
                      ))}
                    </div>
                  )}

                  {/* Errors */}
                  {job.errors.length > 0 && (
                    <div className="mb-4">
                      <div className="text-sm font-medium text-red-800 mb-2">
                        ❌ {job.errors.length} Error{job.errors.length !== 1 ? 's' : ''}
                      </div>
                      <div className="space-y-2">
                        {job.errors.slice(0, 2).map(error => (
                          <div key={error.id} className="text-xs text-red-600 bg-red-50 p-2 rounded">
                            <div className="font-medium">{error.message}</div>
                            <div className="text-red-500">{error.suggestion}</div>
                          </div>
                        ))}
                        {job.errors.length > 2 && (
                          <div className="text-xs text-red-600">
                            ... and {job.errors.length - 2} more errors
                          </div>
                        )}
                      </div>
                    </div>
                  )}

                  <div className="flex items-center space-x-2">
                    <Button
                      onClick={() => setSelectedJob(job)}
                      size="sm"
                      variant="outline"
                    >
                      📄 Details
                    </Button>
                    
                    {job.status === 'processing' && (
                      <Button
                        size="sm"
                        variant="outline"
                      >
                        ⏹️ Cancel
                      </Button>
                    )}
                    
                    {job.status === 'completed' && job.outputFiles.length > 0 && (
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

      {/* New Job Modal */}
      {showNewJob && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg max-w-2xl w-full m-4 max-h-screen overflow-y-auto">
            <div className="p-6 border-b">
              <div className="flex items-center justify-between">
                <h2 className="text-xl font-semibold text-gray-900">
                  Process Documents
                </h2>
                <button
                  onClick={() => {
                    setShowNewJob(false);
                    setUploadedFiles([]);
                  }}
                  className="text-gray-400 hover:text-gray-600"
                >
                  <svg className="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                  </svg>
                </button>
              </div>
            </div>
            
            <div className="p-6">
              <div className="space-y-6">
                {/* Template Selection */}
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Processing Template
                  </label>
                  <select
                    value={selectedTemplate?.id || ''}
                    onChange={(e) => setSelectedTemplate(templates.find(t => t.id === e.target.value) || null)}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                  >
                    <option value="">Select a template</option>
                    {templates.map(template => (
                      <option key={template.id} value={template.id}>
                        {template.name} ({template.inputFormat.toUpperCase()} → {template.outputFormat.toUpperCase()})
                      </option>
                    ))}
                  </select>
                </div>

                {/* File Upload */}
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Upload Documents
                  </label>
                  <div className="border-2 border-dashed border-gray-300 rounded-lg p-6 text-center">
                    <input
                      type="file"
                      multiple
                      onChange={handleFileUpload}
                      accept={selectedTemplate ? `.${selectedTemplate.inputFormat}` : '*'}
                      className="hidden"
                      id="file-upload"
                    />
                    <label htmlFor="file-upload" className="cursor-pointer">
                      <div className="text-4xl mb-2">📁</div>
                      <div className="text-sm text-gray-600">
                        Click to select files or drag and drop
                      </div>
                      {selectedTemplate && (
                        <div className="text-xs text-gray-500 mt-1">
                          Accepts: {selectedTemplate.inputFormat.toUpperCase()} files
                        </div>
                      )}
                    </label>
                  </div>
                  
                  {uploadedFiles.length > 0 && (
                    <div className="mt-4">
                      <div className="text-sm font-medium text-gray-700 mb-2">
                        Selected Files ({uploadedFiles.length})
                      </div>
                      <div className="space-y-2 max-h-32 overflow-y-auto">
                        {uploadedFiles.map((file, index) => (
                          <div key={index} className="flex items-center justify-between bg-gray-50 rounded p-2">
                            <div>
                              <div className="text-sm font-medium text-gray-900">{file.name}</div>
                              <div className="text-xs text-gray-600">{(file.size / 1024).toFixed(1)} KB</div>
                            </div>
                            <button
                              onClick={() => setUploadedFiles(prev => prev.filter((_, i) => i !== index))}
                              className="text-red-600 hover:text-red-800"
                            >
                              ❌
                            </button>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}
                </div>

                {/* Template Info */}
                {selectedTemplate && (
                  <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
                    <h3 className="font-medium text-blue-900 mb-2">Template: {selectedTemplate.name}</h3>
                    <p className="text-blue-800 text-sm mb-3">{selectedTemplate.description}</p>
                    <div className="grid grid-cols-2 gap-4 text-xs text-blue-700">
                      <div>
                        <strong>Success Rate:</strong> {selectedTemplate.usage.successRate}%
                      </div>
                      <div>
                        <strong>Times Used:</strong> {selectedTemplate.usage.timesUsed}
                      </div>
                    </div>
                  </div>
                )}
              </div>

              <div className="flex items-center justify-end space-x-4 mt-8">
                <Button
                  onClick={() => {
                    setShowNewJob(false);
                    setUploadedFiles([]);
                  }}
                  variant="outline"
                >
                  Cancel
                </Button>
                
                <Button
                  onClick={() => selectedTemplate && handleStartProcessing(selectedTemplate.id)}
                  disabled={!selectedTemplate || uploadedFiles.length === 0}
                >
                  🚀 Start Processing
                </Button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default DocumentProcessor;