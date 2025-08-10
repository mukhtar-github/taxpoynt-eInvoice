/**
 * Data Extraction Component
 * ========================
 * 
 * System Integrator interface for extracting data from various business systems.
 * Supports multiple data sources, formats, and extraction strategies.
 * 
 * Features:
 * - Multi-source data extraction (ERP, CRM, POS, Databases, Files)
 * - Real-time and batch extraction modes
 * - Data transformation and normalization
 * - Nigerian business data format support
 * - Quality validation and error handling
 * - Progress tracking and scheduling
 */

import React, { useState, useEffect } from 'react';
import { Button } from '../../../design_system/components/Button';

interface DataSource {
  id: string;
  name: string;
  type: 'erp' | 'crm' | 'pos' | 'database' | 'file' | 'api' | 'webhook';
  systemName: string;
  connectionStatus: 'connected' | 'disconnected' | 'error' | 'testing';
  lastExtraction?: string;
  totalRecords: number;
  extractableRecords: number;
  dataTypes: string[];
  configuration: {
    endpoint?: string;
    database?: string;
    tableName?: string;
    filePath?: string;
    credentials?: any;
    extractionRules?: any;
  };
  organizationId?: string;
  organizationName?: string;
}

interface ExtractionJob {
  id: string;
  name: string;
  sourceId: string;
  sourceName: string;
  status: 'queued' | 'running' | 'completed' | 'failed' | 'cancelled';
  type: 'real_time' | 'batch' | 'scheduled';
  startTime: string;
  endTime?: string;
  progress: number; // 0-100
  recordsExtracted: number;
  recordsTotal: number;
  recordsValid: number;
  recordsInvalid: number;
  extractionRules: ExtractionRule[];
  outputFormat: 'json' | 'csv' | 'xml' | 'firs_format';
  errors: ExtractionError[];
  schedule?: {
    frequency: 'hourly' | 'daily' | 'weekly' | 'monthly';
    time?: string;
    timezone?: string;
    enabled: boolean;
  };
}

interface ExtractionRule {
  id: string;
  name: string;
  description: string;
  enabled: boolean;
  sourceField: string;
  targetField: string;
  transformation?: {
    type: 'format' | 'calculate' | 'lookup' | 'conditional' | 'validate';
    parameters: Record<string, any>;
  };
  validation?: {
    required: boolean;
    dataType: 'string' | 'number' | 'date' | 'boolean' | 'email' | 'phone' | 'tin';
    pattern?: string;
    min?: number;
    max?: number;
  };
  nigerianCompliance?: {
    required: boolean;
    format: string;
    validationRule: string;
  };
}

interface ExtractionError {
  id: string;
  severity: 'info' | 'warning' | 'error' | 'critical';
  category: 'connection' | 'transformation' | 'validation' | 'format';
  message: string;
  details: string;
  recordId?: string;
  field?: string;
  suggestion: string;
  timestamp: string;
}

interface ExtractionStats {
  totalSources: number;
  activeSources: number;
  totalExtractions: number;
  successfulExtractions: number;
  failedExtractions: number;
  recordsExtractedToday: number;
  averageExtractionTime: number; // seconds
  dataQualityScore: number; // 0-100
}

// Mock data for demonstration
const mockDataSources: DataSource[] = [
  {
    id: 'source_sap_001',
    name: 'SAP Production System',
    type: 'erp',
    systemName: 'SAP S/4HANA',
    connectionStatus: 'connected',
    lastExtraction: '2024-01-15T14:30:00Z',
    totalRecords: 125000,
    extractableRecords: 98500,
    dataTypes: ['invoices', 'customers', 'products', 'payments'],
    configuration: {
      endpoint: 'https://sap.client.com:8443/api',
      credentials: { username: 'taxpoynt_user' }
    },
    organizationId: 'org_001',
    organizationName: 'Nigerian Manufacturing Ltd'
  },
  {
    id: 'source_pos_001',
    name: 'OPay POS Terminal Data',
    type: 'pos',
    systemName: 'OPay POS',
    connectionStatus: 'connected',
    lastExtraction: '2024-01-15T15:45:00Z',
    totalRecords: 45000,
    extractableRecords: 44800,
    dataTypes: ['transactions', 'payments', 'receipts'],
    configuration: {
      endpoint: 'https://api.opay.ng/pos',
      credentials: { merchant_id: 'NG_MERCHANT_123' }
    },
    organizationId: 'org_002',
    organizationName: 'Lagos Retail Chain'
  },
  {
    id: 'source_db_001',
    name: 'Customer Database',
    type: 'database',
    systemName: 'PostgreSQL',
    connectionStatus: 'connected',
    lastExtraction: '2024-01-15T12:00:00Z',
    totalRecords: 85000,
    extractableRecords: 85000,
    dataTypes: ['customers', 'orders', 'products'],
    configuration: {
      database: 'customer_db',
      tableName: 'invoices',
      endpoint: 'postgresql://db.client.com:5432'
    },
    organizationId: 'org_003',
    organizationName: 'Abuja Services Ltd'
  }
];

const mockJobs: ExtractionJob[] = [
  {
    id: 'job_001',
    name: 'Daily Invoice Extraction',
    sourceId: 'source_sap_001',
    sourceName: 'SAP Production System',
    status: 'completed',
    type: 'scheduled',
    startTime: '2024-01-15T06:00:00Z',
    endTime: '2024-01-15T06:25:00Z',
    progress: 100,
    recordsExtracted: 1250,
    recordsTotal: 1250,
    recordsValid: 1245,
    recordsInvalid: 5,
    extractionRules: [],
    outputFormat: 'firs_format',
    errors: [],
    schedule: {
      frequency: 'daily',
      time: '06:00',
      timezone: 'Africa/Lagos',
      enabled: true
    }
  },
  {
    id: 'job_002',
    name: 'POS Transaction Sync',
    sourceId: 'source_pos_001',
    sourceName: 'OPay POS Terminal Data',
    status: 'running',
    type: 'real_time',
    startTime: '2024-01-15T16:00:00Z',
    progress: 75,
    recordsExtracted: 850,
    recordsTotal: 1200,
    recordsValid: 840,
    recordsInvalid: 10,
    extractionRules: [],
    outputFormat: 'json',
    errors: []
  }
];

// Default extraction rules for Nigerian compliance
const defaultExtractionRules: ExtractionRule[] = [
  {
    id: 'rule_tin_validation',
    name: 'TIN Validation',
    description: 'Validate Nigerian Tax Identification Number format',
    enabled: true,
    sourceField: 'tax_id',
    targetField: 'supplier_tin',
    validation: {
      required: true,
      dataType: 'tin',
      pattern: '^[0-9]{14}$'
    },
    nigerianCompliance: {
      required: true,
      format: 'FIRS_TIN_14_DIGIT',
      validationRule: 'Nigerian TIN must be exactly 14 digits'
    }
  },
  {
    id: 'rule_currency_normalization',
    name: 'Currency Normalization',
    description: 'Convert all amounts to Nigerian Naira (NGN)',
    enabled: true,
    sourceField: 'amount',
    targetField: 'amount_ngn',
    transformation: {
      type: 'format',
      parameters: {
        target_currency: 'NGN',
        decimal_places: 2,
        conversion_required: true
      }
    },
    nigerianCompliance: {
      required: true,
      format: 'NGN_CURRENCY',
      validationRule: 'Domestic transactions must be in Nigerian Naira'
    }
  },
  {
    id: 'rule_vat_calculation',
    name: 'VAT Calculation',
    description: 'Calculate VAT at 7.5% for applicable items',
    enabled: true,
    sourceField: 'taxable_amount',
    targetField: 'vat_amount',
    transformation: {
      type: 'calculate',
      parameters: {
        formula: 'taxable_amount * 0.075',
        round_to: 2
      }
    },
    nigerianCompliance: {
      required: true,
      format: 'VAT_7_5_PERCENT',
      validationRule: 'Nigerian VAT rate is 7.5%'
    }
  }
];

interface DataExtractorProps {
  organizationId?: string;
  onExtractionComplete?: (jobId: string, recordCount: number) => void;
}

export const DataExtractor: React.FC<DataExtractorProps> = ({
  organizationId,
  onExtractionComplete
}) => {
  const [dataSources, setDataSources] = useState<DataSource[]>(mockDataSources);
  const [extractionJobs, setExtractionJobs] = useState<ExtractionJob[]>(mockJobs);
  const [stats, setStats] = useState<ExtractionStats | null>(null);
  const [selectedSource, setSelectedSource] = useState<DataSource | null>(null);
  const [selectedJob, setSelectedJob] = useState<ExtractionJob | null>(null);
  const [extractionRules, setExtractionRules] = useState<ExtractionRule[]>(defaultExtractionRules);
  const [isCreatingJob, setIsCreatingJob] = useState(false);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    fetchDataSources();
    fetchExtractionJobs();
    calculateStats();
  }, [organizationId]);

  const fetchDataSources = async () => {
    try {
      const params = organizationId ? `?organization_id=${organizationId}` : '';
      const response = await fetch(`/api/v1/si/data-extraction/sources${params}`, {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('taxpoynt_auth_token')}`
        }
      });

      if (response.ok) {
        const data = await response.json();
        setDataSources(data.sources || mockDataSources);
      }
    } catch (error) {
      console.error('Failed to fetch data sources:', error);
      setDataSources(mockDataSources);
    } finally {
      setIsLoading(false);
    }
  };

  const fetchExtractionJobs = async () => {
    try {
      const response = await fetch('/api/v1/si/data-extraction/jobs', {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('taxpoynt_auth_token')}`
        }
      });

      if (response.ok) {
        const data = await response.json();
        setExtractionJobs(data.jobs || mockJobs);
      }
    } catch (error) {
      console.error('Failed to fetch extraction jobs:', error);
      setExtractionJobs(mockJobs);
    }
  };

  const calculateStats = () => {
    const totalSources = dataSources.length;
    const activeSources = dataSources.filter(source => source.connectionStatus === 'connected').length;
    const totalExtractions = extractionJobs.length;
    const successfulExtractions = extractionJobs.filter(job => job.status === 'completed').length;
    const failedExtractions = extractionJobs.filter(job => job.status === 'failed').length;
    const recordsExtractedToday = extractionJobs
      .filter(job => new Date(job.startTime).toDateString() === new Date().toDateString())
      .reduce((sum, job) => sum + job.recordsExtracted, 0);
    
    const completedJobs = extractionJobs.filter(job => job.endTime);
    const averageExtractionTime = completedJobs.length > 0 
      ? completedJobs.reduce((sum, job) => {
          const duration = new Date(job.endTime!).getTime() - new Date(job.startTime).getTime();
          return sum + (duration / 1000);
        }, 0) / completedJobs.length
      : 0;

    const totalRecords = extractionJobs.reduce((sum, job) => sum + job.recordsExtracted, 0);
    const validRecords = extractionJobs.reduce((sum, job) => sum + job.recordsValid, 0);
    const dataQualityScore = totalRecords > 0 ? (validRecords / totalRecords) * 100 : 100;

    setStats({
      totalSources,
      activeSources,
      totalExtractions,
      successfulExtractions,
      failedExtractions,
      recordsExtractedToday,
      averageExtractionTime,
      dataQualityScore
    });
  };

  const handleTestConnection = async (sourceId: string) => {
    try {
      const response = await fetch(`/api/v1/si/data-extraction/sources/${sourceId}/test`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('taxpoynt_auth_token')}`
        }
      });

      if (response.ok) {
        const data = await response.json();
        alert(data.success ? '✅ Connection successful!' : '❌ Connection failed!');
        fetchDataSources();
      } else {
        alert('❌ Connection test failed');
      }
    } catch (error) {
      console.error('Connection test failed:', error);
      alert('❌ Connection test failed');
    }
  };

  const handleStartExtraction = async (sourceId: string, extractionType: 'real_time' | 'batch') => {
    try {
      const response = await fetch('/api/v1/si/data-extraction/jobs/create', {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('taxpoynt_auth_token')}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          source_id: sourceId,
          extraction_type: extractionType,
          extraction_rules: extractionRules.filter(rule => rule.enabled),
          output_format: 'firs_format',
          organization_id: organizationId
        })
      });

      if (response.ok) {
        const data = await response.json();
        const newJob = data.job;
        setExtractionJobs(prev => [newJob, ...prev]);
        alert('✅ Extraction job started successfully!');
        
        // Start polling for progress
        pollJobProgress(newJob.id);
        
        if (onExtractionComplete) {
          onExtractionComplete(newJob.id, 0);
        }
      } else {
        alert('❌ Failed to start extraction job');
      }
    } catch (error) {
      console.error('Failed to start extraction:', error);
      alert('❌ Failed to start extraction job');
    }
  };

  const pollJobProgress = (jobId: string) => {
    const pollInterval = setInterval(async () => {
      try {
        const response = await fetch(`/api/v1/si/data-extraction/jobs/${jobId}/status`, {
          headers: {
            'Authorization': `Bearer ${localStorage.getItem('taxpoynt_auth_token')}`
          }
        });

        if (response.ok) {
          const data = await response.json();
          const updatedJob = data.job;
          
          setExtractionJobs(prev => prev.map(job => 
            job.id === jobId ? updatedJob : job
          ));

          if (['completed', 'failed', 'cancelled'].includes(updatedJob.status)) {
            clearInterval(pollInterval);
            if (updatedJob.status === 'completed' && onExtractionComplete) {
              onExtractionComplete(jobId, updatedJob.recordsExtracted);
            }
          }
        }
      } catch (error) {
        console.error('Failed to poll job progress:', error);
        clearInterval(pollInterval);
      }
    }, 3000);
  };

  const getStatusIcon = (status: DataSource['connectionStatus'] | ExtractionJob['status']) => {
    switch (status) {
      case 'connected':
      case 'completed':
        return '✅';
      case 'disconnected':
      case 'failed':
        return '❌';
      case 'error':
        return '⚠️';
      case 'testing':
      case 'running':
        return '🔄';
      case 'queued':
        return '⏳';
      case 'cancelled':
        return '🚫';
      default:
        return '❓';
    }
  };

  const getStatusColor = (status: DataSource['connectionStatus'] | ExtractionJob['status']) => {
    switch (status) {
      case 'connected':
      case 'completed':
        return 'text-green-600 bg-green-100';
      case 'disconnected':
      case 'failed':
        return 'text-red-600 bg-red-100';
      case 'error':
        return 'text-yellow-600 bg-yellow-100';
      case 'testing':
      case 'running':
        return 'text-blue-600 bg-blue-100';
      case 'queued':
        return 'text-gray-600 bg-gray-100';
      case 'cancelled':
        return 'text-gray-600 bg-gray-100';
      default:
        return 'text-gray-600 bg-gray-100';
    }
  };

  const getTypeIcon = (type: DataSource['type']) => {
    switch (type) {
      case 'erp': return '🏢';
      case 'crm': return '👥';
      case 'pos': return '💳';
      case 'database': return '🗄️';
      case 'file': return '📁';
      case 'api': return '🔌';
      case 'webhook': return '🪝';
      default: return '📄';
    }
  };

  if (isLoading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <div className="text-4xl mb-4">📊</div>
          <h2 className="text-xl font-semibold text-gray-900 mb-2">Loading Data Extractor</h2>
          <p className="text-gray-600">Fetching data sources and extraction jobs...</p>
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
                <span className="text-blue-600 text-xl">🔌</span>
              </div>
              <div className="ml-4">
                <p className="text-sm font-medium text-gray-600">Active Sources</p>
                <p className="text-2xl font-bold text-gray-900">{stats.activeSources}/{stats.totalSources}</p>
              </div>
            </div>
          </div>

          <div className="bg-white rounded-lg border p-6">
            <div className="flex items-center">
              <div className="p-3 rounded-full bg-green-100">
                <span className="text-green-600 text-xl">📊</span>
              </div>
              <div className="ml-4">
                <p className="text-sm font-medium text-gray-600">Records Today</p>
                <p className="text-2xl font-bold text-gray-900">{stats.recordsExtractedToday.toLocaleString()}</p>
              </div>
            </div>
          </div>

          <div className="bg-white rounded-lg border p-6">
            <div className="flex items-center">
              <div className="p-3 rounded-full bg-purple-100">
                <span className="text-purple-600 text-xl">✅</span>
              </div>
              <div className="ml-4">
                <p className="text-sm font-medium text-gray-600">Success Rate</p>
                <p className="text-2xl font-bold text-gray-900">{stats.totalExtractions > 0 ? ((stats.successfulExtractions / stats.totalExtractions) * 100).toFixed(1) : '100'}%</p>
              </div>
            </div>
          </div>

          <div className="bg-white rounded-lg border p-6">
            <div className="flex items-center">
              <div className="p-3 rounded-full bg-yellow-100">
                <span className="text-yellow-600 text-xl">🎯</span>
              </div>
              <div className="ml-4">
                <p className="text-sm font-medium text-gray-600">Data Quality</p>
                <p className="text-2xl font-bold text-gray-900">{stats.dataQualityScore.toFixed(1)}%</p>
              </div>
            </div>
          </div>
        </div>
      )}

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
        
        {/* Data Sources */}
        <div className="bg-white rounded-lg border">
          <div className="p-6 border-b">
            <h2 className="text-lg font-semibold text-gray-900">Data Sources</h2>
            <p className="text-gray-600 text-sm mt-1">Connected business systems and data sources</p>
          </div>
          
          <div className="divide-y divide-gray-200">
            {dataSources.length === 0 ? (
              <div className="text-center py-12 text-gray-500">
                <div className="text-4xl mb-4">🔌</div>
                <h3 className="text-lg font-medium mb-2">No data sources</h3>
                <p className="mb-4">Configure integrations to start extracting data</p>
              </div>
            ) : (
              dataSources.map(source => (
                <div key={source.id} className="p-6">
                  <div className="flex items-center justify-between mb-4">
                    <div className="flex items-center space-x-3">
                      <span className="text-2xl">{getTypeIcon(source.type)}</span>
                      <div>
                        <h3 className="font-medium text-gray-900">{source.name}</h3>
                        <p className="text-sm text-gray-600">{source.systemName}</p>
                        {source.organizationName && (
                          <p className="text-xs text-gray-500">{source.organizationName}</p>
                        )}
                      </div>
                    </div>
                    
                    <span className={`px-2 py-1 text-xs font-medium rounded-full ${getStatusColor(source.connectionStatus)}`}>
                      {getStatusIcon(source.connectionStatus)} {source.connectionStatus}
                    </span>
                  </div>

                  <div className="grid grid-cols-2 gap-4 mb-4 text-sm">
                    <div>
                      <span className="text-gray-600">Total Records:</span>
                      <span className="font-medium text-gray-900 ml-2">{source.totalRecords.toLocaleString()}</span>
                    </div>
                    <div>
                      <span className="text-gray-600">Extractable:</span>
                      <span className="font-medium text-gray-900 ml-2">{source.extractableRecords.toLocaleString()}</span>
                    </div>
                  </div>

                  <div className="mb-4">
                    <div className="text-sm text-gray-600 mb-2">Data Types:</div>
                    <div className="flex flex-wrap gap-2">
                      {source.dataTypes.map(type => (
                        <span key={type} className="px-2 py-1 text-xs bg-gray-100 text-gray-700 rounded-full">
                          {type}
                        </span>
                      ))}
                    </div>
                  </div>

                  {source.lastExtraction && (
                    <div className="text-xs text-gray-500 mb-4">
                      Last extraction: {new Date(source.lastExtraction).toLocaleString()}
                    </div>
                  )}

                  <div className="flex items-center space-x-2">
                    <Button
                      onClick={() => handleTestConnection(source.id)}
                      size="sm"
                      variant="outline"
                    >
                      🔍 Test
                    </Button>
                    
                    <Button
                      onClick={() => handleStartExtraction(source.id, 'batch')}
                      disabled={source.connectionStatus !== 'connected'}
                      size="sm"
                      variant="outline"
                    >
                      📦 Extract Batch
                    </Button>
                    
                    <Button
                      onClick={() => handleStartExtraction(source.id, 'real_time')}
                      disabled={source.connectionStatus !== 'connected'}
                      size="sm"
                    >
                      ⚡ Real-time
                    </Button>
                    
                    <Button
                      onClick={() => setSelectedSource(source)}
                      size="sm"
                      variant="outline"
                    >
                      ⚙️ Configure
                    </Button>
                  </div>
                </div>
              ))
            )}
          </div>
        </div>

        {/* Extraction Jobs */}
        <div className="bg-white rounded-lg border">
          <div className="p-6 border-b">
            <h2 className="text-lg font-semibold text-gray-900">Extraction Jobs</h2>
            <p className="text-gray-600 text-sm mt-1">Recent and active data extraction jobs</p>
          </div>
          
          <div className="divide-y divide-gray-200">
            {extractionJobs.length === 0 ? (
              <div className="text-center py-12 text-gray-500">
                <div className="text-4xl mb-4">📊</div>
                <h3 className="text-lg font-medium mb-2">No extraction jobs</h3>
                <p className="mb-4">Start extracting data from your sources</p>
              </div>
            ) : (
              extractionJobs.slice(0, 10).map(job => (
                <div key={job.id} className="p-6">
                  <div className="flex items-center justify-between mb-3">
                    <div>
                      <h3 className="font-medium text-gray-900">{job.name}</h3>
                      <p className="text-sm text-gray-600">From: {job.sourceName}</p>
                      <p className="text-xs text-gray-500">Started: {new Date(job.startTime).toLocaleString()}</p>
                    </div>
                    
                    <div className="flex items-center space-x-2">
                      <span className={`px-2 py-1 text-xs font-medium rounded-full ${getStatusColor(job.status)}`}>
                        {getStatusIcon(job.status)} {job.status}
                      </span>
                      <span className="px-2 py-1 text-xs bg-gray-100 text-gray-700 rounded-full">
                        {job.type}
                      </span>
                    </div>
                  </div>

                  {/* Progress Bar */}
                  {job.status === 'running' && (
                    <div className="mb-3">
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

                  <div className="grid grid-cols-3 gap-4 mb-3 text-sm">
                    <div className="text-center bg-gray-50 rounded p-2">
                      <div className="font-medium text-gray-900">{job.recordsExtracted}</div>
                      <div className="text-xs text-gray-600">Extracted</div>
                    </div>
                    <div className="text-center bg-green-50 rounded p-2">
                      <div className="font-medium text-green-600">{job.recordsValid}</div>
                      <div className="text-xs text-gray-600">Valid</div>
                    </div>
                    <div className="text-center bg-red-50 rounded p-2">
                      <div className="font-medium text-red-600">{job.recordsInvalid}</div>
                      <div className="text-xs text-gray-600">Invalid</div>
                    </div>
                  </div>

                  {job.errors.length > 0 && (
                    <div className="mb-3">
                      <div className="text-sm font-medium text-red-800 mb-1">
                        ❌ {job.errors.length} Error{job.errors.length !== 1 ? 's' : ''}
                      </div>
                      <div className="text-xs text-red-600 bg-red-50 p-2 rounded">
                        {job.errors[0].message}
                        {job.errors.length > 1 && ` ... and ${job.errors.length - 1} more`}
                      </div>
                    </div>
                  )}

                  {job.schedule && (
                    <div className="mb-3 text-xs text-blue-600 bg-blue-50 p-2 rounded">
                      📅 Scheduled: {job.schedule.frequency} at {job.schedule.time} ({job.schedule.timezone})
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
                    
                    {job.status === 'running' && (
                      <Button
                        size="sm"
                        variant="outline"
                      >
                        ⏹️ Cancel
                      </Button>
                    )}
                    
                    {job.status === 'completed' && (
                      <Button
                        size="sm"
                        variant="outline"
                      >
                        💾 Download
                      </Button>
                    )}
                  </div>
                </div>
              ))
            )}
          </div>
        </div>
      </div>

      {/* Nigerian Compliance Rules */}
      <div className="bg-white rounded-lg border">
        <div className="p-6 border-b">
          <h2 className="text-lg font-semibold text-gray-900">🇳🇬 Nigerian Compliance Rules</h2>
          <p className="text-gray-600 text-sm mt-1">Data extraction rules for Nigerian tax compliance</p>
        </div>
        
        <div className="p-6">
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            {extractionRules.map(rule => (
              <div key={rule.id} className="border rounded-lg p-4">
                <div className="flex items-center justify-between mb-2">
                  <h3 className="font-medium text-gray-900">{rule.name}</h3>
                  <label className="flex items-center">
                    <input
                      type="checkbox"
                      checked={rule.enabled}
                      onChange={(e) => setExtractionRules(prev => prev.map(r => 
                        r.id === rule.id ? { ...r, enabled: e.target.checked } : r
                      ))}
                      className="h-4 w-4 text-blue-600 border-gray-300 rounded focus:ring-blue-500"
                    />
                  </label>
                </div>
                
                <p className="text-sm text-gray-600 mb-3">{rule.description}</p>
                
                <div className="text-xs text-gray-500 space-y-1">
                  <div><strong>Source:</strong> {rule.sourceField}</div>
                  <div><strong>Target:</strong> {rule.targetField}</div>
                  {rule.nigerianCompliance && (
                    <div className="bg-blue-50 border border-blue-200 rounded p-2 mt-2">
                      <div className="text-blue-800">
                        <strong>🇳🇬 Compliance:</strong> {rule.nigerianCompliance.validationRule}
                      </div>
                    </div>
                  )}
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
};

export default DataExtractor;