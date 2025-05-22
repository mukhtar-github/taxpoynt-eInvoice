import React, { useState, useEffect } from 'react';
import { Card, CardHeader, CardContent, Button, Typography, Badge } from '../ui';
import firsApiService from '../../services/firsApiService';
import { SubmissionStatusResponse, SubmissionStatus } from '../../types/firs/api-types';

interface FIRSStatusCheckProps {
  sandboxMode: boolean;
  initialSubmissionId?: string;
}

const FIRSStatusCheck: React.FC<FIRSStatusCheckProps> = ({ 
  sandboxMode,
  initialSubmissionId = ''
}) => {
  const [submissionId, setSubmissionId] = useState(initialSubmissionId);
  const [status, setStatus] = useState<string>('');
  const [response, setResponse] = useState<any>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Update submission ID if initialSubmissionId changes
  useEffect(() => {
    if (initialSubmissionId) {
      setSubmissionId(initialSubmissionId);
    }
  }, [initialSubmissionId]);

  const getStatusColor = (status: string): string => {
    const statusMap: Record<string, string> = {
      'COMPLETED': 'success',
      'PROCESSING': 'default',
      'PENDING': 'warning',
      'REJECTED': 'destructive',
      'FAILED': 'destructive',
      'ERROR': 'destructive'
    };
    
    return statusMap[status] || 'secondary';
  };

  const checkStatus = async () => {
    if (!submissionId.trim()) {
      setError('Please enter a submission ID');
      return;
    }

    try {
      setLoading(true);
      setError(null);
      setResponse(null);

      // Use the API service to check status
      const result = await firsApiService.checkSubmissionStatus(
        submissionId.trim(),
        sandboxMode
      );

      if (result.success) {
        // Set response data
        setResponse(result.data);
        
        // Update status display if available
        if (result.data.status) {
          setStatus(result.data.status);
        }
      } else {
        // Handle API error
        setError(result.error || 'Failed to check submission status');
        
        // Store response for debugging if available
        if (result.data) {
          setResponse(result.data);
        }
      }
    } catch (err: any) {
      console.error('Error checking status:', err);
      setError(err.message || 'An unexpected error occurred');
    } finally {
      setLoading(false);
    }
  };

  return (
    <>
      <Card className="mb-6">
        <CardHeader className="bg-warning text-dark">
          <Typography.Heading level="h3">
            Check Submission Status
          </Typography.Heading>
        </CardHeader>
        <CardContent>
          <div className="mb-4">
            <label htmlFor="submissionId" className="block mb-2">
              Submission ID
            </label>
            <input
              id="submissionId"
              type="text"
              className="w-full p-2 border border-gray-300 rounded mb-4"
              value={submissionId}
              onChange={(e) => setSubmissionId(e.target.value)}
              placeholder="Enter submission ID"
            />
          </div>
          
          <div className="mb-4">
            <label className="block mb-2">Current Status</label>
            <div>
              {status ? (
                <Badge 
                  variant={getStatusColor(status) as any}
                  className="px-3 py-1 text-sm"
                >
                  {status}
                </Badge>
              ) : (
                <Badge 
                  variant="secondary"
                  className="px-3 py-1 text-sm"
                >
                  Unknown
                </Badge>
              )}
            </div>
          </div>
          
          <Button onClick={checkStatus} disabled={loading}>
            {loading ? 'Checking...' : 'Check Status'}
          </Button>
        </CardContent>
      </Card>

      {error && (
        <Card className="mb-6 border-red-500">
          <CardHeader className="bg-red-500 text-white">
            <Typography.Heading level="h3" className="text-white">Error</Typography.Heading>
          </CardHeader>
          <CardContent>
            <Typography.Text>{error}</Typography.Text>
          </CardContent>
        </Card>
      )}

      {response && (
        <Card className="mb-6">
          <CardHeader>
            <Typography.Heading level="h3">Response</Typography.Heading>
          </CardHeader>
          <CardContent>
            <pre className="bg-gray-100 p-4 rounded overflow-auto max-h-96">
              {JSON.stringify(response, null, 2)}
            </pre>
          </CardContent>
        </Card>
      )}
    </>
  );
};

export default FIRSStatusCheck;
