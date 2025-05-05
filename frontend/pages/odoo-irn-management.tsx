import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { Container } from '../components/ui/Container';
import { 
  Card, 
  CardHeader, 
  CardTitle, 
  CardDescription, 
  CardContent, 
  CardFooter 
} from '../components/ui/Card';
import { Button } from '../components/ui/Button';
import { 
  TableContainer, 
  Table, 
  TableHeader, 
  TableBody, 
  TableRow, 
  TableHead, 
  TableCell 
} from '../components/ui/Table';
import { AlertCircle, CheckCircle, Clock, ArrowUpRight, FileText } from 'lucide-react';

// Define types
interface OdooInvoice {
  id: number;
  name: string;
  invoice_date: string;
  amount_total: number;
  currency_symbol: string;
  partner: {
    name: string;
  };
  line_count: number;
  state: string;
  has_irn?: boolean;
}

interface IRN {
  irn: string;
  invoice_number: string;
  status: string;
  generated_at: string;
  valid_until: string;
  used_at?: string;
}

interface Integration {
  id: string;
  name: string;
  integration_type: string;
  status: string;
}

const statusColors = {
  unused: 'bg-info bg-opacity-10 text-info',
  active: 'bg-success bg-opacity-10 text-success',
  expired: 'bg-error bg-opacity-10 text-error',
  revoked: 'bg-warning bg-opacity-10 text-warning',
  invalid: 'bg-error bg-opacity-10 text-error'
};

const OdooIRNManagement: React.FC = () => {
  // State
  const [integrations, setIntegrations] = useState<Integration[]>([]);
  const [selectedIntegration, setSelectedIntegration] = useState<string>('');
  const [invoices, setInvoices] = useState<OdooInvoice[]>([]);
  const [loading, setLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);
  const [irnDetails, setIrnDetails] = useState<IRN[]>([]);
  const [selectedInvoice, setSelectedInvoice] = useState<OdooInvoice | null>(null);
  const [generatingIRN, setGeneratingIRN] = useState<boolean>(false);
  const [validationResult, setValidationResult] = useState<any>(null);
  const [validatingIRN, setValidatingIRN] = useState<boolean>(false);
  const [searchTerm, setSearchTerm] = useState<string>('');

  // Fetch integrations on mount
  useEffect(() => {
    fetchIntegrations();
  }, []);

  // Fetch invoices when integration is selected
  useEffect(() => {
    if (selectedIntegration) {
      fetchInvoices(selectedIntegration);
    }
  }, [selectedIntegration]);

  // Fetch Odoo integrations
  const fetchIntegrations = async () => {
    try {
      setLoading(true);
      setError(null);
      
      const response = await axios.get('/api/integrations', {
        params: { type: 'odoo' }
      });
      
      setIntegrations(response.data.filter((i: Integration) => i.integration_type === 'odoo'));
      
      if (response.data.length > 0) {
        const odooIntegrations = response.data.filter((i: Integration) => i.integration_type === 'odoo');
        if (odooIntegrations.length > 0) {
          setSelectedIntegration(odooIntegrations[0].id);
        }
      }
    } catch (error) {
      console.error('Error fetching integrations:', error);
      setError('Failed to fetch integrations. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  // Fetch invoices from Odoo
  const fetchInvoices = async (integrationId: string) => {
    try {
      setLoading(true);
      setError(null);
      
      const response = await axios.get(`/api/integrations/${integrationId}/odoo/invoices`);
      
      // Check IRN status for each invoice
      const invoicesWithIRN = await Promise.all(
        response.data.map(async (invoice: OdooInvoice) => {
          try {
            const irnResponse = await axios.get(`/api/irn/odoo/${invoice.id}`);
            return {
              ...invoice,
              has_irn: irnResponse.data.length > 0
            };
          } catch (err) {
            // If 404, no IRN exists
            return {
              ...invoice,
              has_irn: false
            };
          }
        })
      );
      
      setInvoices(invoicesWithIRN);
    } catch (error) {
      console.error('Error fetching invoices:', error);
      setError('Failed to fetch invoices. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  // Generate IRN for an invoice
  const generateIRN = async (invoice: OdooInvoice) => {
    try {
      setGeneratingIRN(true);
      setError(null);
      
      const response = await axios.post('/api/irn/odoo/generate', {
        integration_id: selectedIntegration,
        odoo_invoice_id: invoice.id
      });
      
      // Update invoices list
      setInvoices(invoices.map(inv => 
        inv.id === invoice.id ? { ...inv, has_irn: true } : inv
      ));
      
      // Set IRN details
      fetchIRNDetails(invoice.id);
      
      return response.data;
    } catch (error: any) {
      console.error('Error generating IRN:', error);
      setError(error.response?.data?.detail || 'Failed to generate IRN. Please try again.');
      return null;
    } finally {
      setGeneratingIRN(false);
    }
  };

  // Fetch IRN details for an invoice
  const fetchIRNDetails = async (invoiceId: number) => {
    try {
      setLoading(true);
      setError(null);
      
      const response = await axios.get(`/api/irn/odoo/${invoiceId}`);
      setIrnDetails(response.data);
      
      return response.data;
    } catch (error) {
      console.error('Error fetching IRN details:', error);
      setError('Failed to fetch IRN details. Please try again.');
      return [];
    } finally {
      setLoading(false);
    }
  };

  // Validate an IRN
  const validateIRN = async (irn: string) => {
    try {
      setValidatingIRN(true);
      setError(null);
      
      const response = await axios.get(`/api/irn/validate/${irn}`);
      setValidationResult(response.data);
      
      return response.data;
    } catch (error) {
      console.error('Error validating IRN:', error);
      setError('Failed to validate IRN. Please try again.');
      return null;
    } finally {
      setValidatingIRN(false);
    }
  };

  // View IRN details for an invoice
  const viewIRNDetails = async (invoice: OdooInvoice) => {
    setSelectedInvoice(invoice);
    await fetchIRNDetails(invoice.id);
  };

  // Filter invoices by search term
  const filteredInvoices = invoices.filter(invoice => 
    invoice.name?.toLowerCase().includes(searchTerm.toLowerCase()) ||
    invoice.partner.name?.toLowerCase().includes(searchTerm.toLowerCase()) ||
    invoice.id.toString().includes(searchTerm)
  );

  // Format date for display
  const formatDate = (dateString: string) => {
    if (!dateString) return 'N/A';
    return new Date(dateString).toLocaleDateString();
  };

  // Get status badge class based on status
  const getStatusBadgeClass = (status: string) => {
    return statusColors[status as keyof typeof statusColors] || 'bg-gray-200 text-gray-800';
  };

  return (
    <div className="min-h-screen bg-background">
      <Container maxWidth="xl" padding="medium" className="pt-8 md:pt-12">
        <h1 className="text-3xl font-heading font-semibold mb-6">Odoo IRN Management</h1>
        
        {/* Integration Selection */}
        <Card className="mb-8">
          <CardHeader>
            <CardTitle>Odoo Integration</CardTitle>
            <CardDescription>
              Select an Odoo integration to manage invoices and IRNs
            </CardDescription>
          </CardHeader>
          <CardContent>
            {loading && integrations.length === 0 ? (
              <div className="text-center py-4">Loading integrations...</div>
            ) : integrations.length === 0 ? (
              <div className="text-center py-4 text-text-secondary">
                No Odoo integrations found. Please configure an integration first.
              </div>
            ) : (
              <div className="flex flex-col sm:flex-row gap-4">
                <div className="flex-grow">
                  <select 
                    className="w-full p-2 border border-border rounded-md bg-background" 
                    value={selectedIntegration}
                    onChange={(e) => setSelectedIntegration(e.target.value)}
                  >
                    {integrations.map(integration => (
                      <option key={integration.id} value={integration.id}>
                        {integration.name} - {integration.status}
                      </option>
                    ))}
                  </select>
                </div>
                <Button 
                  onClick={() => fetchInvoices(selectedIntegration)}
                  disabled={loading || !selectedIntegration}
                >
                  Refresh Invoices
                </Button>
              </div>
            )}
          </CardContent>
        </Card>
        
        {/* Invoices List */}
        <Card className="mb-8">
          <CardHeader>
            <CardTitle>Odoo Invoices</CardTitle>
            <CardDescription>
              View and manage invoices from your Odoo integration
            </CardDescription>
          </CardHeader>
          <CardContent>
            {/* Search */}
            <div className="mb-4">
              <input 
                type="text" 
                placeholder="Search invoices by number, customer name, or ID..." 
                className="w-full p-2 border border-border rounded-md bg-background"
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
              />
            </div>
            
            {loading && invoices.length === 0 ? (
              <div className="text-center py-8">Loading invoices...</div>
            ) : error ? (
              <div className="text-center py-8 text-error flex items-center justify-center">
                <AlertCircle className="mr-2" size={20} />
                {error}
              </div>
            ) : filteredInvoices.length === 0 ? (
              <div className="text-center py-8 text-text-secondary">
                No invoices found. Please select a different integration or try again.
              </div>
            ) : (
              <TableContainer>
                <Table minWidth="768px">
                  <TableHeader>
                    <TableRow>
                      <TableHead>ID</TableHead>
                      <TableHead>Invoice Number</TableHead>
                      <TableHead>Date</TableHead>
                      <TableHead>Customer</TableHead>
                      <TableHead>Amount</TableHead>
                      <TableHead>Status</TableHead>
                      <TableHead>IRN</TableHead>
                      <TableHead className="text-right">Actions</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {filteredInvoices.map((invoice) => (
                      <TableRow key={invoice.id}>
                        <TableCell className="font-medium">{invoice.id}</TableCell>
                        <TableCell>{invoice.name || `INV-${invoice.id}`}</TableCell>
                        <TableCell>{formatDate(invoice.invoice_date)}</TableCell>
                        <TableCell>{invoice.partner.name}</TableCell>
                        <TableCell>
                          {invoice.currency_symbol}{invoice.amount_total.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
                        </TableCell>
                        <TableCell>
                          <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${
                            invoice.state === 'draft' ? 'bg-info bg-opacity-10 text-info' :
                            invoice.state === 'posted' ? 'bg-success bg-opacity-10 text-success' :
                            'bg-warning bg-opacity-10 text-warning'
                          }`}>
                            {invoice.state.charAt(0).toUpperCase() + invoice.state.slice(1)}
                          </span>
                        </TableCell>
                        <TableCell>
                          {invoice.has_irn ? (
                            <span className="inline-flex items-center text-success">
                              <CheckCircle size={16} className="mr-1" />
                              Yes
                            </span>
                          ) : (
                            <span className="inline-flex items-center text-text-secondary">
                              <Clock size={16} className="mr-1" />
                              No
                            </span>
                          )}
                        </TableCell>
                        <TableCell className="text-right">
                          <div className="flex justify-end gap-2">
                            <Button 
                              size="sm" 
                              variant="outline"
                              className="h-8 px-2"
                              onClick={() => viewIRNDetails(invoice)}
                              title="View IRN Details"
                            >
                              <FileText size={16} />
                            </Button>
                            {!invoice.has_irn && (
                              <Button 
                                size="sm" 
                                className="h-8 px-2"
                                onClick={() => generateIRN(invoice)}
                                disabled={generatingIRN}
                                title="Generate IRN"
                              >
                                <ArrowUpRight size={16} />
                              </Button>
                            )}
                          </div>
                        </TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              </TableContainer>
            )}
          </CardContent>
        </Card>
        
        {/* IRN Details */}
        {selectedInvoice && (
          <Card className="mb-8">
            <CardHeader>
              <CardTitle>
                IRN Details - Invoice {selectedInvoice.name || `INV-${selectedInvoice.id}`}
              </CardTitle>
              <CardDescription>
                View and manage IRNs for this invoice
              </CardDescription>
            </CardHeader>
            <CardContent>
              {loading ? (
                <div className="text-center py-4">Loading IRN details...</div>
              ) : irnDetails.length === 0 ? (
                <div className="flex flex-col items-center justify-center py-8 gap-4">
                  <div className="text-center text-text-secondary">
                    No IRNs found for this invoice.
                  </div>
                  <Button 
                    onClick={() => generateIRN(selectedInvoice)}
                    disabled={generatingIRN}
                  >
                    Generate IRN
                  </Button>
                </div>
              ) : (
                <div className="space-y-6">
                  {irnDetails.map((irn) => (
                    <div key={irn.irn} className="border border-border rounded-lg p-4">
                      <div className="flex flex-col md:flex-row md:justify-between mb-4">
                        <h3 className="text-lg font-semibold mb-2 md:mb-0">
                          {irn.irn}
                        </h3>
                        <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${getStatusBadgeClass(irn.status)}`}>
                          {irn.status.charAt(0).toUpperCase() + irn.status.slice(1)}
                        </span>
                      </div>
                      
                      <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-4">
                        <div>
                          <p className="text-sm text-text-secondary mb-1">Original Invoice</p>
                          <p className="font-medium">{irn.invoice_number}</p>
                        </div>
                        <div>
                          <p className="text-sm text-text-secondary mb-1">Generated At</p>
                          <p className="font-medium">{formatDate(irn.generated_at)}</p>
                        </div>
                        <div>
                          <p className="text-sm text-text-secondary mb-1">Valid Until</p>
                          <p className="font-medium">{formatDate(irn.valid_until)}</p>
                        </div>
                        <div>
                          <p className="text-sm text-text-secondary mb-1">Used At</p>
                          <p className="font-medium">{irn.used_at ? formatDate(irn.used_at) : 'Not used yet'}</p>
                        </div>
                      </div>
                      
                      <div className="flex flex-col sm:flex-row gap-2">
                        <Button 
                          size="sm" 
                          variant="outline"
                          onClick={() => validateIRN(irn.irn)}
                          disabled={validatingIRN}
                        >
                          Validate IRN
                        </Button>
                        <Button 
                          size="sm" 
                          variant="outline"
                          onClick={() => {
                            navigator.clipboard.writeText(irn.irn);
                            alert("IRN copied to clipboard!");
                          }}
                        >
                          Copy IRN
                        </Button>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </CardContent>
          </Card>
        )}
        
        {/* Validation Result */}
        {validationResult && (
          <Card className="mb-8">
            <CardHeader>
              <CardTitle>IRN Validation Result</CardTitle>
              <CardDescription>
                Details of the validation check
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className={`mb-4 p-4 rounded-lg ${validationResult.success ? 'bg-success bg-opacity-10' : 'bg-error bg-opacity-10'}`}>
                <div className="flex items-center mb-2">
                  {validationResult.success ? (
                    <CheckCircle className="text-success mr-2" size={20} />
                  ) : (
                    <AlertCircle className="text-error mr-2" size={20} />
                  )}
                  <span className={`font-semibold ${validationResult.success ? 'text-success' : 'text-error'}`}>
                    {validationResult.message}
                  </span>
                </div>
                
                {validationResult.details && (
                  <div className="mt-4">
                    <h4 className="font-semibold mb-2">Details</h4>
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                      {validationResult.details.status && (
                        <div>
                          <p className="text-sm text-text-secondary mb-1">Status</p>
                          <p className="font-medium">
                            <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${getStatusBadgeClass(validationResult.details.status)}`}>
                              {validationResult.details.status.charAt(0).toUpperCase() + validationResult.details.status.slice(1)}
                            </span>
                          </p>
                        </div>
                      )}
                      
                      {validationResult.details.invoice_number && (
                        <div>
                          <p className="text-sm text-text-secondary mb-1">Invoice Number</p>
                          <p className="font-medium">{validationResult.details.invoice_number}</p>
                        </div>
                      )}
                      
                      {validationResult.details.valid_until && (
                        <div>
                          <p className="text-sm text-text-secondary mb-1">Valid Until</p>
                          <p className="font-medium">{formatDate(validationResult.details.valid_until)}</p>
                        </div>
                      )}
                      
                      {validationResult.details.invoice_data && (
                        <div className="col-span-2">
                          <p className="text-sm text-text-secondary mb-1">Invoice Data</p>
                          <div className="grid grid-cols-1 md:grid-cols-2 gap-4 bg-background p-3 rounded-md">
                            <div>
                              <p className="text-sm text-text-secondary mb-1">Customer</p>
                              <p className="font-medium">{validationResult.details.invoice_data.customer_name}</p>
                            </div>
                            <div>
                              <p className="text-sm text-text-secondary mb-1">Invoice Date</p>
                              <p className="font-medium">{formatDate(validationResult.details.invoice_data.invoice_date)}</p>
                            </div>
                            <div>
                              <p className="text-sm text-text-secondary mb-1">Amount</p>
                              <p className="font-medium">
                                {validationResult.details.invoice_data.currency_code} 
                                {validationResult.details.invoice_data.total_amount.toLocaleString(undefined, { 
                                  minimumFractionDigits: 2, 
                                  maximumFractionDigits: 2 
                                })}
                              </p>
                            </div>
                          </div>
                        </div>
                      )}
                      
                      {validationResult.details.error_type && (
                        <div>
                          <p className="text-sm text-text-secondary mb-1">Error Type</p>
                          <p className="font-medium">{validationResult.details.error_type}</p>
                        </div>
                      )}
                    </div>
                  </div>
                )}
              </div>
            </CardContent>
            <CardFooter>
              <Button 
                variant="outline" 
                className="ml-auto"
                onClick={() => setValidationResult(null)}
              >
                Close
              </Button>
            </CardFooter>
          </Card>
        )}
      </Container>
    </div>
  );
};

export default OdooIRNManagement;
