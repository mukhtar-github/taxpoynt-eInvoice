import React, { useState } from 'react';
import { Card, CardHeader, CardContent, Button, Typography, Alert } from '../../components/ui';
import { getSampleInvoice, getSampleCompany } from '../../utils/firs-samples';
import firsApiService from '../../services/firsApiService';
import apiProxy from './apiProxy'; // Import our API proxy to handle CORS issues
import { InvoiceSubmitRequest, InvoiceSubmissionResponse, ValidationIssue } from '../../types/firs/api-types';

interface FIRSTestFormProps {
  sandboxMode: boolean;
  onSubmissionSuccess: (submissionId: string) => void;
}

const FIRSTestForm: React.FC<FIRSTestFormProps> = ({ 
  sandboxMode, 
  onSubmissionSuccess 
}) => {
  const [invoiceData, setInvoiceData] = useState('');
  const [companyData, setCompanyData] = useState('');
  const [response, setResponse] = useState<InvoiceSubmissionResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [validationIssues, setValidationIssues] = useState<ValidationIssue[]>([]);

  const handleSubmit = async () => {
    try {
      // Validate JSON input
      if (!invoiceData || !companyData) {
        setError('Please enter both invoice and company data');
        return;
      }

      let parsedInvoice, parsedCompany;
      try {
        parsedInvoice = JSON.parse(invoiceData);
        parsedCompany = JSON.parse(companyData);
      } catch (e) {
        setError('Invalid JSON format. Please check your input.');
        return;
      }

      // Reset states
      setLoading(true);
      setError(null);
      setResponse(null);
      setValidationIssues([]);

      // Prepare request payload
      const requestData: InvoiceSubmitRequest = {
        odoo_invoice: parsedInvoice,
        company_info: parsedCompany,
        sandbox_mode: sandboxMode
      };

      // Try to submit to the regular API service first, then fall back to our proxy if that fails
      try {
        // Attempt to use the standard service first
        const result = await firsApiService.submitInvoice(requestData);
        
        // Handle response
        if (result.success) {
          setResponse(result.data);
          
          // Store validation issues if any
          if (result.data.validation_issues && result.data.validation_issues.length > 0) {
            setValidationIssues(result.data.validation_issues);
          }
          
          // If successful with submission ID, notify parent
          if (result.data.success && result.data.submission_id) {
            onSubmissionSuccess(result.data.submission_id);
          }
        } else {
          // Handle API error
          setError(result.error || 'Failed to submit invoice');
          
          // Store response for debugging
          if (result.data) {
            setResponse(result.data);
            
            // Extract validation issues if available
            if (result.data.validation_issues && result.data.validation_issues.length > 0) {
              setValidationIssues(result.data.validation_issues);
            }
          }
        }
      } catch (apiError) {
        console.log('Primary API service failed, using fallback proxy...', apiError);
        
        // Fall back to our proxy implementation
        try {
          // Use our local API proxy that handles CORS issues
          const proxyResult = await apiProxy.submitInvoice(requestData);
          
          // Create a standardized response format
          const formattedResponse = {
            success: true,
            submission_id: proxyResult.submission_id,
            message: proxyResult.message,
            timestamp: proxyResult.timestamp,
            validation_issues: []
          };
          
          setResponse(formattedResponse);
          
          // If we have a submission ID, call the success handler
          if (proxyResult.submission_id) {
            onSubmissionSuccess(proxyResult.submission_id);
          }
        } catch (proxyError) {
          console.error('Both API services failed:', proxyError);
          setError('All API services failed. Please check your network connection.');
        }
      }
    } catch (err: any) {
      console.error('Error submitting invoice:', err);
      setError(err.message || 'An unexpected error occurred');
    } finally {
      setLoading(false);
    }
  };

  const loadSampleInvoice = () => {
    setInvoiceData(JSON.stringify(getSampleInvoice(), null, 2));
  };

  const loadSampleCompany = () => {
    setCompanyData(JSON.stringify(getSampleCompany(), null, 2));
  };

  return (
    <>
      <Card className="mb-6">
        <CardHeader className="bg-success text-white">
          <Typography.Heading level="h3" className="text-white">
            Submit Odoo Invoice to FIRS
          </Typography.Heading>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <div className="mb-4">
                <label htmlFor="invoiceData" className="block mb-2">
                  Odoo Invoice Data (JSON)
                </label>
                <textarea
                  id="invoiceData"
                  rows={12}
                  className="w-full p-2 border border-gray-300 rounded"
                  value={invoiceData}
                  onChange={(e) => setInvoiceData(e.target.value)}
                />
              </div>
              <div className="flex space-x-2">
                <Button onClick={handleSubmit} disabled={loading}>
                  {loading ? 'Submitting...' : 'Submit Invoice'}
                </Button>
                <Button variant="outline" onClick={loadSampleInvoice}>
                  Load Sample
                </Button>
              </div>
            </div>
            <div>
              <div className="mb-4">
                <label htmlFor="companyData" className="block mb-2">
                  Company Information (JSON)
                </label>
                <textarea
                  id="companyData"
                  rows={12}
                  className="w-full p-2 border border-gray-300 rounded"
                  value={companyData}
                  onChange={(e) => setCompanyData(e.target.value)}
                />
              </div>
              <Button variant="outline" onClick={loadSampleCompany}>
                Load Sample Company
              </Button>
            </div>
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

export default FIRSTestForm;
