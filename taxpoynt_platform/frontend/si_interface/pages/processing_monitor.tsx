/**
 * Processing Monitor Page
 * ======================
 * 
 * System Integrator interface for monitoring data processing, invoice generation,
 * and FIRS submission status in real-time.
 * 
 * Features:
 * - Real-time processing status monitoring
 * - Invoice generation pipeline tracking
 * - FIRS submission status updates
 * - Error handling and retry mechanisms
 * - Nigerian compliance monitoring
 * - Performance metrics and analytics
 */

import React, { useState, useEffect } from 'react';
import { Button } from '../../design_system/components/Button';

interface ProcessingJob {
  id: string;
  type: 'data_extraction' | 'invoice_generation' | 'firs_submission' | 'compliance_validation';
  organizationId: string;
  organizationName: string;
  status: 'pending' | 'processing' | 'completed' | 'failed' | 'retrying';
  progress: number; // 0-100
  startTime: string;
  endTime?: string;
  duration?: number;
  recordsTotal: number;
  recordsProcessed: number;
  recordsSucceeded: number;
  recordsFailed: number;
  errors?: ProcessingError[];
  metadata?: {
    systemType?: string;
    batchId?: string;
    firsRef?: string;
  };
}

interface ProcessingError {
  code: string;
  message: string;
  recordId?: string;
  field?: string;
  severity: 'warning' | 'error' | 'critical';
  timestamp: string;
}

interface ProcessingStats {
  totalJobs: number;
  activeJobs: number;
  completedJobs: number;
  failedJobs: number;
  totalRecords: number;
  processingRate: number; // records per minute
  successRate: number; // percentage
  averageDuration: number; // seconds
}

interface ProcessingMonitorProps {
  organizationId?: string;
  systemId?: string;
}

export const ProcessingMonitor: React.FC<ProcessingMonitorProps> = ({
  organizationId,
  systemId
}) => {
  const [jobs, setJobs] = useState<ProcessingJob[]>([]);
  const [stats, setStats] = useState<ProcessingStats | null>(null);
  const [selectedJob, setSelectedJob] = useState<ProcessingJob | null>(null);
  const [filter, setFilter] = useState<'all' | 'active' | 'completed' | 'failed'>('all');
  const [autoRefresh, setAutoRefresh] = useState(true);
  const [isLoading, setIsLoading] = useState(true);

  // Real-time updates via WebSocket or polling
  useEffect(() => {
    fetchJobs();
    fetchStats();

    let interval: NodeJS.Timeout;
    if (autoRefresh) {
      interval = setInterval(() => {
        fetchJobs();
        fetchStats();
      }, 5000); // Refresh every 5 seconds
    }

    return () => {
      if (interval) clearInterval(interval);
    };
  }, [organizationId, systemId, autoRefresh]);

  const fetchJobs = async () => {
    try {
      const params = new URLSearchParams();
      if (organizationId) params.append('organization_id', organizationId);
      if (systemId) params.append('system_id', systemId);

      const response = await fetch(`/api/v1/si/processing/jobs?${params}`, {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('taxpoynt_auth_token')}`
        }
      });

      if (response.ok) {
        const data = await response.json();
        setJobs(data.jobs || []);
      }
    } catch (error) {
      console.error('Failed to fetch processing jobs:', error);
    } finally {
      setIsLoading(false);
    }
  };

  const fetchStats = async () => {
    try {
      const response = await fetch('/api/v1/si/processing/stats', {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('taxpoynt_auth_token')}`
        }
      });

      if (response.ok) {
        const data = await response.json();
        setStats(data.stats);
      }
    } catch (error) {
      console.error('Failed to fetch processing stats:', error);
    }
  };

  const handleRetryJob = async (jobId: string) => {
    try {
      const response = await fetch(`/api/v1/si/processing/jobs/${jobId}/retry`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('taxpoynt_auth_token')}`
        }
      });

      if (response.ok) {
        alert('✅ Job retry initiated successfully');
        fetchJobs();
      } else {
        alert('❌ Failed to retry job');
      }
    } catch (error) {
      console.error('Failed to retry job:', error);
      alert('❌ Failed to retry job');
    }
  };

  const handleCancelJob = async (jobId: string) => {
    try {
      const response = await fetch(`/api/v1/si/processing/jobs/${jobId}/cancel`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('taxpoynt_auth_token')}`
        }
      });

      if (response.ok) {
        alert('✅ Job cancelled successfully');
        fetchJobs();
      } else {
        alert('❌ Failed to cancel job');
      }
    } catch (error) {
      console.error('Failed to cancel job:', error);
      alert('❌ Failed to cancel job');
    }
  };

  const getStatusIcon = (status: ProcessingJob['status']) => {
    switch (status) {
      case 'pending':
        return '⏳';
      case 'processing':
        return '🔄';
      case 'completed':
        return '✅';
      case 'failed':
        return '❌';
      case 'retrying':
        return '🔁';
      default:
        return '❓';
    }
  };

  const getStatusColor = (status: ProcessingJob['status']) => {
    switch (status) {
      case 'pending':
        return 'text-yellow-600 bg-yellow-100';
      case 'processing':
        return 'text-blue-600 bg-blue-100';
      case 'completed':
        return 'text-green-600 bg-green-100';
      case 'failed':
        return 'text-red-600 bg-red-100';
      case 'retrying':
        return 'text-orange-600 bg-orange-100';
      default:
        return 'text-gray-600 bg-gray-100';
    }
  };

  const getJobTypeLabel = (type: ProcessingJob['type']) => {
    switch (type) {
      case 'data_extraction':
        return 'Data Extraction';
      case 'invoice_generation':
        return 'Invoice Generation';
      case 'firs_submission':
        return 'FIRS Submission';
      case 'compliance_validation':
        return 'Compliance Validation';
      default:
        return type;
    }
  };

  const filteredJobs = jobs.filter(job => {
    switch (filter) {
      case 'active':
        return ['pending', 'processing', 'retrying'].includes(job.status);
      case 'completed':
        return job.status === 'completed';
      case 'failed':
        return job.status === 'failed';
      default:
        return true;
    }
  });

  if (isLoading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <div className="text-4xl mb-4">🔄</div>
          <h2 className="text-xl font-semibold text-gray-900 mb-2">Loading Processing Monitor</h2>
          <p className="text-gray-600">Fetching processing status...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <div className="bg-white border-b">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-3xl font-bold text-gray-900">Processing Monitor</h1>
              <p className="text-gray-600 mt-2">
                Real-time monitoring of data processing and FIRS submissions
              </p>
            </div>
            
            <div className="flex items-center space-x-4">
              <label className="flex items-center text-sm text-gray-600">
                <input
                  type="checkbox"
                  checked={autoRefresh}
                  onChange={(e) => setAutoRefresh(e.target.checked)}
                  className="h-4 w-4 text-blue-600 border-gray-300 rounded focus:ring-blue-500 mr-2"
                />
                Auto-refresh
              </label>
              
              <Button onClick={fetchJobs} variant="outline" size="sm">
                🔄 Refresh
              </Button>
            </div>
          </div>
        </div>
      </div>

      {/* Stats Dashboard */}
      {stats && (
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
            <div className="bg-white rounded-lg border p-6">
              <div className="flex items-center">
                <div className="p-3 rounded-full bg-blue-100">
                  <span className="text-blue-600 text-xl">📊</span>
                </div>
                <div className="ml-4">
                  <p className="text-sm font-medium text-gray-600">Total Jobs</p>
                  <p className="text-2xl font-bold text-gray-900">{stats.totalJobs}</p>
                </div>
              </div>
            </div>

            <div className="bg-white rounded-lg border p-6">
              <div className="flex items-center">
                <div className="p-3 rounded-full bg-yellow-100">
                  <span className="text-yellow-600 text-xl">⚡</span>
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
                  <span className="text-green-600 text-xl">✅</span>
                </div>
                <div className="ml-4">
                  <p className="text-sm font-medium text-gray-600">Success Rate</p>
                  <p className="text-2xl font-bold text-gray-900">{stats.successRate.toFixed(1)}%</p>
                </div>
              </div>
            </div>

            <div className="bg-white rounded-lg border p-6">
              <div className="flex items-center">
                <div className="p-3 rounded-full bg-purple-100">
                  <span className="text-purple-600 text-xl">⚡</span>
                </div>
                <div className="ml-4">
                  <p className="text-sm font-medium text-gray-600">Processing Rate</p>
                  <p className="text-2xl font-bold text-gray-900">{stats.processingRate}</p>
                  <p className="text-xs text-gray-500">records/min</p>
                </div>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Filter Tabs */}
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="bg-white rounded-lg border">
          <div className="border-b border-gray-200">
            <nav className="-mb-px flex space-x-8 px-6">
              {[
                { key: 'all', label: 'All Jobs', count: jobs.length },
                { key: 'active', label: 'Active', count: jobs.filter(j => ['pending', 'processing', 'retrying'].includes(j.status)).length },
                { key: 'completed', label: 'Completed', count: jobs.filter(j => j.status === 'completed').length },
                { key: 'failed', label: 'Failed', count: jobs.filter(j => j.status === 'failed').length }
              ].map(tab => (
                <button
                  key={tab.key}
                  onClick={() => setFilter(tab.key as any)}
                  className={`py-2 px-1 border-b-2 font-medium text-sm ${
                    filter === tab.key
                      ? 'border-blue-500 text-blue-600'
                      : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                  }`}
                >
                  {tab.label} ({tab.count})
                </button>
              ))}
            </nav>
          </div>

          {/* Jobs List */}
          <div className="divide-y divide-gray-200">
            {filteredJobs.length === 0 ? (
              <div className="text-center py-12">
                <div className="text-4xl mb-4">📭</div>
                <h3 className="text-lg font-medium text-gray-900 mb-2">No jobs found</h3>
                <p className="text-gray-600">No processing jobs match the current filter.</p>
              </div>
            ) : (
              filteredJobs.map(job => (
                <div key={job.id} className="p-6 hover:bg-gray-50">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center space-x-4">
                      <span className="text-2xl">{getStatusIcon(job.status)}</span>
                      
                      <div>
                        <div className="flex items-center space-x-2">
                          <h3 className="text-lg font-medium text-gray-900">
                            {getJobTypeLabel(job.type)}
                          </h3>
                          <span className={`px-2 py-1 text-xs font-medium rounded-full ${getStatusColor(job.status)}`}>
                            {job.status}
                          </span>
                        </div>
                        
                        <div className="text-sm text-gray-600 mt-1">
                          {job.organizationName} • Started {new Date(job.startTime).toLocaleString()}
                        </div>
                        
                        <div className="flex items-center space-x-4 mt-2 text-sm text-gray-500">
                          <span>📊 {job.recordsProcessed}/{job.recordsTotal} records</span>
                          <span>✅ {job.recordsSucceeded} succeeded</span>
                          {job.recordsFailed > 0 && (
                            <span className="text-red-600">❌ {job.recordsFailed} failed</span>
                          )}
                        </div>
                      </div>
                    </div>

                    <div className="flex items-center space-x-4">
                      {/* Progress Bar */}
                      <div className="w-32">
                        <div className="flex items-center justify-between text-xs text-gray-600 mb-1">
                          <span>Progress</span>
                          <span>{job.progress}%</span>
                        </div>
                        <div className="w-full bg-gray-200 rounded-full h-2">
                          <div
                            className={`h-2 rounded-full transition-all duration-300 ${
                              job.status === 'completed' ? 'bg-green-500' :
                              job.status === 'failed' ? 'bg-red-500' :
                              'bg-blue-500'
                            }`}
                            style={{ width: `${job.progress}%` }}
                          />
                        </div>
                      </div>

                      {/* Actions */}
                      <div className="flex items-center space-x-2">
                        <Button
                          onClick={() => setSelectedJob(job)}
                          variant="outline"
                          size="sm"
                        >
                          View Details
                        </Button>
                        
                        {job.status === 'failed' && (
                          <Button
                            onClick={() => handleRetryJob(job.id)}
                            variant="outline"
                            size="sm"
                          >
                            🔁 Retry
                          </Button>
                        )}
                        
                        {['pending', 'processing'].includes(job.status) && (
                          <Button
                            onClick={() => handleCancelJob(job.id)}
                            variant="outline"
                            size="sm"
                          >
                            ⏹️ Cancel
                          </Button>
                        )}
                      </div>
                    </div>
                  </div>

                  {/* FIRS Submission Status */}
                  {job.type === 'firs_submission' && job.metadata?.firsRef && (
                    <div className="mt-4 bg-blue-50 border border-blue-200 rounded-lg p-3">
                      <div className="flex items-center text-blue-800">
                        <span className="text-blue-600 mr-2">🇳🇬</span>
                        <span className="font-medium">FIRS Reference: {job.metadata.firsRef}</span>
                      </div>
                    </div>
                  )}

                  {/* Errors Preview */}
                  {job.errors && job.errors.length > 0 && (
                    <div className="mt-4">
                      <div className="text-sm font-medium text-red-800 mb-2">
                        ❌ Recent Errors ({job.errors.length})
                      </div>
                      <div className="space-y-1">
                        {job.errors.slice(0, 3).map((error, index) => (
                          <div key={index} className="text-sm text-red-600 bg-red-50 p-2 rounded">
                            {error.message}
                            {error.field && <span className="text-red-500"> (Field: {error.field})</span>}
                          </div>
                        ))}
                        {job.errors.length > 3 && (
                          <div className="text-sm text-red-600">
                            ... and {job.errors.length - 3} more errors
                          </div>
                        )}
                      </div>
                    </div>
                  )}
                </div>
              ))
            )}
          </div>
        </div>
      </div>

      {/* Job Details Modal */}
      {selectedJob && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg max-w-4xl w-full m-4 max-h-screen overflow-y-auto">
            <div className="p-6 border-b">
              <div className="flex items-center justify-between">
                <h2 className="text-xl font-semibold text-gray-900">
                  Job Details: {getJobTypeLabel(selectedJob.type)}
                </h2>
                <button
                  onClick={() => setSelectedJob(null)}
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
                  <h3 className="font-medium text-gray-900 mb-3">Job Information</h3>
                  <div className="space-y-2 text-sm">
                    <div><strong>Job ID:</strong> {selectedJob.id}</div>
                    <div><strong>Organization:</strong> {selectedJob.organizationName}</div>
                    <div><strong>Status:</strong> <span className={`px-2 py-1 rounded-full ${getStatusColor(selectedJob.status)}`}>{selectedJob.status}</span></div>
                    <div><strong>Started:</strong> {new Date(selectedJob.startTime).toLocaleString()}</div>
                    {selectedJob.endTime && (
                      <div><strong>Completed:</strong> {new Date(selectedJob.endTime).toLocaleString()}</div>
                    )}
                    {selectedJob.duration && (
                      <div><strong>Duration:</strong> {selectedJob.duration}s</div>
                    )}
                  </div>
                </div>
                
                <div>
                  <h3 className="font-medium text-gray-900 mb-3">Processing Statistics</h3>
                  <div className="space-y-2 text-sm">
                    <div><strong>Total Records:</strong> {selectedJob.recordsTotal}</div>
                    <div><strong>Processed:</strong> {selectedJob.recordsProcessed}</div>
                    <div><strong>Succeeded:</strong> {selectedJob.recordsSucceeded}</div>
                    <div><strong>Failed:</strong> {selectedJob.recordsFailed}</div>
                    <div><strong>Progress:</strong> {selectedJob.progress}%</div>
                  </div>
                </div>
              </div>

              {/* Errors */}
              {selectedJob.errors && selectedJob.errors.length > 0 && (
                <div className="mt-6">
                  <h3 className="font-medium text-gray-900 mb-3">Error Details</h3>
                  <div className="space-y-3 max-h-64 overflow-y-auto">
                    {selectedJob.errors.map((error, index) => (
                      <div key={index} className="bg-red-50 border border-red-200 rounded-lg p-3">
                        <div className="flex items-start justify-between">
                          <div>
                            <div className="font-medium text-red-800">{error.code}</div>
                            <div className="text-red-700 mt-1">{error.message}</div>
                            {error.field && (
                              <div className="text-red-600 text-sm mt-1">Field: {error.field}</div>
                            )}
                            {error.recordId && (
                              <div className="text-red-600 text-sm">Record: {error.recordId}</div>
                            )}
                          </div>
                          <span className={`px-2 py-1 text-xs rounded-full ${
                            error.severity === 'critical' ? 'bg-red-200 text-red-800' :
                            error.severity === 'error' ? 'bg-orange-200 text-orange-800' :
                            'bg-yellow-200 text-yellow-800'
                          }`}>
                            {error.severity}
                          </span>
                        </div>
                        <div className="text-xs text-gray-500 mt-2">
                          {new Date(error.timestamp).toLocaleString()}
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

export default ProcessingMonitor;