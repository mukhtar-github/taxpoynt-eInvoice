import React, { useState } from 'react';
import { Card, CardHeader, CardContent, Button, Typography, Alert } from '@/components/ui';
import { getSampleInvoice, getSampleCompany } from '../../utils/firs-samples';
import firsApiService from '../../services/firsApiService';
import { InvoiceSubmitRequest, BatchSubmissionResponse, ValidationIssue } from '../../types/firs/api-types';

interface FIRSBatchSubmitProps {
  sandboxMode: boolean;
}

const FIRSBatchSubmit: React.FC<FIRSBatchSubmitProps> = ({ sandboxMode }) => {
  const [batchData, setBatchData] = useState('');
  const [response, setResponse] = useState<BatchSubmissionResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [validationIssues, setValidationIssues] = useState<ValidationIssue[]>([]);

  const handleSubmit = async () => {
    try {
      // Validate JSON input
      if (!batchData) {
        setError('Please enter batch invoice data');
        return;
      }

      let parsedBatch;
      try {
        parsedBatch = JSON.parse(batchData);
        
        if (!Array.isArray(parsedBatch)) {
          setError('Batch data must be a JSON array');
          return;
        }
        
        // Validate each item in the batch has required Odoo structure
        // This supports our ERP-first integration strategy (Phase 1 focus on Odoo)
        for (let i = 0; i < parsedBatch.length; i++) {
          const item = parsedBatch[i];
          if (!item.odoo_invoice || !item.company_info) {
            setError(`Item at index ${i} is missing required 'odoo_invoice' or 'company_info' fields`);
            return;
          }
          
          // Ensure each item has sandbox_mode consistent with the component setting
          item.sandbox_mode = sandboxMode;
        }
      } catch (e) {
        setError('Invalid JSON format. Please check your input.');
        return;
      }

      // Reset states
      setLoading(true);
      setError(null);
      setResponse(null);
      setValidationIssues([]);

      // Submit batch to API using our service
      const result = await firsApiService.submitBatch(parsedBatch);

      // Handle response
      if (result.success) {
        setResponse(result.data);
        
        // Extract validation issues if any
        if (result.data.validation_issues && result.data.validation_issues.length > 0) {
          setValidationIssues(result.data.validation_issues);
          
          // If we have validation issues but the submission was technically successful,
          // show a notification about partial success
          if (result.data.success && result.data.validation_issues.length > 0) {
            console.warn(`Batch submitted with ${result.data.validation_issues.length} validation issues`);
          }
        }
        
        // Show success notification with metrics
        if (result.data.success && result.data.batch_id) {
          const successMessage = `Batch ID: ${result.data.batch_id}\n` +
            `Total: ${result.data.invoice_count || parsedBatch.length} invoices\n` +
            `Success: ${result.data.success_count || parsedBatch.length} invoices\n` +
            `Failed: ${result.data.failed_count || 0} invoices`;
            
          console.log('Batch submitted successfully:', successMessage);
        }
      } else {
        // Handle API error
        setError(result.error || 'Failed to submit batch');
        
        // Store response for debugging
        if (result.data) {
          setResponse(result.data);
          
          // Extract validation issues if available
          if (result.data.validation_issues && result.data.validation_issues.length > 0) {
            setValidationIssues(result.data.validation_issues);
          }
        }
      }
    } catch (err: any) {
      console.error('Error submitting batch:', err);
      setError(err.message || 'An unexpected error occurred');
    } finally {
      setLoading(false);
    }
  };

  const loadSampleBatch = () => {
    // Create a sample batch with two invoices
    const sampleBatch = [
      { 
        odoo_invoice: getSampleInvoice(1), 
        company_info: getSampleCompany(), 
        sandbox_mode: sandboxMode 
      },
      { 
        odoo_invoice: getSampleInvoice(2), 
        company_info: getSampleCompany(), 
        sandbox_mode: sandboxMode 
      }
    ];
    
    setBatchData(JSON.stringify(sampleBatch, null, 2));
  };

  return (
    <>
      <Card className="mb-6">
        <CardHeader className="bg-primary text-white">
          <Typography.Heading level="h3" className="text-white">
            Batch Submit Invoices
          </Typography.Heading>
        </CardHeader>
        <CardContent>
          <div className="mb-4">
            <label htmlFor="batchData" className="block mb-2">
              Batch Invoices (JSON Array)
            </label>
            <textarea
              id="batchData"
              rows={10}
              className="w-full p-2 border border-gray-300 rounded"
              value={batchData}
              onChange={(e) => setBatchData(e.target.value)}
            />
          </div>
          <div className="flex space-x-2">
            <Button onClick={handleSubmit} disabled={loading}>
              {loading ? 'Submitting Batch...' : 'Submit Batch'}
            </Button>
            <Button variant="outline" onClick={loadSampleBatch}>
              Load Sample Batch
            </Button>
          </div>
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

export default FIRSBatchSubmit;
