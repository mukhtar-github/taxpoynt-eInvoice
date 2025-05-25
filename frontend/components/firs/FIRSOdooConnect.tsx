import React, { useState, useEffect } from 'react';
import { Card, CardHeader, CardContent, CardFooter } from '../ui/Card';
import { Button } from '../ui/Button';
import { Label } from '../ui/Label';
import { Input } from '../ui/Input';
import { Checkbox } from '../ui/Checkbox';
import { Alert, AlertTitle, AlertDescription } from '../ui/Alert';
import { Spinner } from '../ui/Spinner';
import { Plus, AlertCircle, CheckCircle, Database } from 'lucide-react';
import { getFirsFormattedInvoice } from '../../utils/firs-samples';
import firsApiService from '../../services/firsApiService';

interface FIRSOdooConnectProps {
  sandboxMode: boolean;
  onSubmissionSuccess: (submissionId: string) => void;
}

const FIRSOdooConnect: React.FC<FIRSOdooConnectProps> = ({
  sandboxMode,
  onSubmissionSuccess
}) => {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);
  const [useOdooData, setUseOdooData] = useState(true);
  const [selectedInvoiceId, setSelectedInvoiceId] = useState('');
  const [odooInvoices, setOdooInvoices] = useState<any[]>([]);
  const [convertedInvoice, setConvertedInvoice] = useState<any>(null);
  const [showPayload, setShowPayload] = useState(false);

  // Fetch available Odoo invoices on component mount
  useEffect(() => {
    fetchOdooInvoices();
  }, []);

  const fetchOdooInvoices = async () => {
    try {
      setLoading(true);
      const response = await firsApiService.fetchOdooInvoices();
      
      if (response.success) {
        setOdooInvoices(response.data);
      } else {
        setError('Failed to fetch Odoo invoices');
      }
    } catch (err) {
      setError('Error connecting to Odoo server');
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const convertOdooToFirs = async () => {
    try {
      setLoading(true);
      setError(null);
      setSuccess(null);
      
      let response;
      if (useOdooData && selectedInvoiceId) {
        response = await firsApiService.convertOdooInvoice(selectedInvoiceId);
      } else {
        // For sample data we need a different approach
        // You might need to implement a method in firsApiService for sample data
        // or use the existing methods in a different way
        // For now we'll keep error handling for this case
        setError('Sample data conversion not implemented');
        setLoading(false);
        return;
      }
      
      if (response.success) {
        setConvertedInvoice(response.data);
        setSuccess('Successfully converted to FIRS format with UUID4 business ID');
      } else {
        setError(response.message || 'Failed to convert invoice');
      }
    } catch (err) {
      setError('Error during conversion process');
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const submitToFirs = async () => {
    if (!convertedInvoice) {
      setError('Please convert invoice to FIRS format first');
      return;
    }
    
    try {
      setLoading(true);
      setError(null);
      
      const response = await firsApiService.submitInvoice(
        convertedInvoice,
        { useSandbox: sandboxMode }
      );
      
      if (response.success) {
        setSuccess('Successfully submitted to FIRS API');
        if (response.data && response.data.submission_id) {
          onSubmissionSuccess(response.data.submission_id);
        } else {
          console.warn('Submission successful but no submission_id was returned');
        }
      } else {
        setError(response.message || 'Failed to submit to FIRS');
      }
    } catch (err) {
      setError('Error during submission process');
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  return (
    <Card className="w-full">
      <CardHeader>
        <div className="flex items-center space-x-2">
          <Database className="h-5 w-5 text-primary" />
          <h3 className="text-lg font-semibold">Odoo to FIRS Integration</h3>
        </div>
        <p className="text-sm text-muted-foreground">
          Convert Odoo invoices to FIRS format using UUID4 business IDs
        </p>
      </CardHeader>
      
      <CardContent className="space-y-4">
        {error && (
          <Alert variant="error">
            <AlertCircle className="h-4 w-4" />
            <AlertTitle>Error</AlertTitle>
            <AlertDescription>{error}</AlertDescription>
          </Alert>
        )}
        
        {success && (
          <Alert variant="success" className="bg-green-50 border-green-200">
            <CheckCircle className="h-4 w-4 text-green-500" />
            <AlertTitle className="text-green-700">Success</AlertTitle>
            <AlertDescription className="text-green-600">{success}</AlertDescription>
          </Alert>
        )}
        
        <div className="flex items-center space-x-2">
          <Checkbox 
            id="useOdooData" 
            checked={useOdooData} 
            onChange={(e) => setUseOdooData(e.target.checked)}
          />
          <Label htmlFor="useOdooData">Use real Odoo invoice data</Label>
        </div>
        
        {useOdooData && (
          <div className="space-y-2">
            <Label htmlFor="invoiceSelect">Select Odoo Invoice</Label>
            <div className="flex space-x-2">
              <select 
                id="invoiceSelect"
                className="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background file:border-0 file:bg-transparent file:text-sm file:font-medium placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50"
                value={selectedInvoiceId}
                onChange={(e) => setSelectedInvoiceId(e.target.value)}
                disabled={loading || odooInvoices.length === 0}
              >
                <option value="">Select an invoice</option>
                {odooInvoices.map((invoice: any) => (
                  <option key={invoice.id} value={invoice.id}>
                    {invoice.name} - {invoice.partner_id?.name || 'Unknown'} ({invoice.amount_total})
                  </option>
                ))}
              </select>
              <Button
                variant="outline"
                size="icon"
                onClick={fetchOdooInvoices}
                disabled={loading}
              >
                <Plus className="h-4 w-4" />
              </Button>
            </div>
            {odooInvoices.length === 0 && !loading && (
              <p className="text-sm text-muted-foreground">No invoices available from Odoo</p>
            )}
          </div>
        )}
        
        <div className="flex space-x-2 pt-4">
          <Button 
            onClick={convertOdooToFirs} 
            disabled={loading || (useOdooData && !selectedInvoiceId)}
            variant="outline"
          >
            {loading ? <Spinner className="mr-2 h-4 w-4" /> : null}
            Convert to FIRS Format
          </Button>
          
          <Button 
            onClick={submitToFirs} 
            disabled={loading || !convertedInvoice}
            variant="default"
          >
            {loading ? <Spinner className="mr-2 h-4 w-4" /> : null}
            Submit to FIRS API
          </Button>
        </div>
        
        {convertedInvoice && (
          <div className="mt-4 space-y-2">
            <div className="flex items-center justify-between">
              <h4 className="text-sm font-medium">FIRS Formatted Payload (UUID4)</h4>
              <Button 
                variant="ghost" 
                size="sm" 
                onClick={() => setShowPayload(!showPayload)}
              >
                {showPayload ? 'Hide' : 'Show'} Payload
              </Button>
            </div>
            
            {showPayload && (
              <pre className="mt-2 rounded-md bg-slate-950 p-4 text-white text-xs overflow-auto max-h-80">
                {JSON.stringify(convertedInvoice, null, 2)}
              </pre>
            )}
            
            <div className="bg-blue-50 p-3 rounded-md text-blue-800 text-sm">
              <p className="font-medium">UUID4 Business ID: {convertedInvoice.business_id}</p>
              <p className="text-xs text-blue-600 mt-1">
                Associated with TIN: {convertedInvoice.supplier?.tin || 'Unknown'}
              </p>
            </div>
          </div>
        )}
      </CardContent>
    </Card>
  );
};

export default FIRSOdooConnect;
