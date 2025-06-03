import React, { useState, useEffect } from 'react';
import { Search, Filter, RefreshCw, Loader2, AlertCircle } from 'lucide-react';
import { apiClient } from '@/utils/apiClient';
import { formatDate, formatCurrency } from '@/utils/dateUtils';
import ErrorAlert from '@/components/common/ErrorAlert';
import InvoiceSignatureVisualizer from '@/components/platform/signature/InvoiceSignatureVisualizer';

// Generic invoice interface that can accommodate different ERP systems
interface GenericInvoice {
  id: string | number;
  number: string;  // Invoice number/reference (e.g., "INV-001", "SO123")
  customerName: string;
  date: string;
  amount: number;
  status: string;
  currency?: string;
  // Additional fields that might be specific to certain ERPs
  [key: string]: any;
  csid?: string;
}

// Props needed for any ERP invoice tab
interface ERPInvoicesTabProps {
  organizationId?: string;
  integrationId: string;
  erpType: 'odoo' | 'quickbooks' | 'sap' | 'oracle' | 'dynamics';
  title?: string;
  mapResponseToInvoices?: (data: any) => GenericInvoice[];
  customEndpoint?: string;
  statusMapping?: Record<string, { label: string, color: string }>;
  defaultCurrency?: string;
}

const ERPInvoicesTab: React.FC<ERPInvoicesTabProps> = ({ 
  organizationId, 
  integrationId,
  erpType,
  title,
  mapResponseToInvoices,
  customEndpoint,
  statusMapping,
  defaultCurrency = 'NGN'
}) => {
  const [invoices, setInvoices] = useState<GenericInvoice[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [page, setPage] = useState(0);
  const [rowsPerPage, setRowsPerPage] = useState(10);
  const [totalInvoices, setTotalInvoices] = useState(0);
  const [searchTerm, setSearchTerm] = useState('');
  const [showDraft, setShowDraft] = useState(false);
  const [currency, setCurrency] = useState(defaultCurrency);

  // Default invoice mapper (can be overridden with prop)
  const defaultMapResponseToInvoices = (data: any): GenericInvoice[] => {
    // Handle Odoo format by default
    if (data.invoices && Array.isArray(data.invoices)) {
      return data.invoices.map((invoice: any) => ({
        id: invoice.id,
        number: invoice.name,
        customerName: invoice.partner_id?.name || 'Unknown Customer',
        date: invoice.date,
        amount: invoice.amount_total,
        status: invoice.state,
        currency: invoice.currency
      }));
    }
    
    // Handle QuickBooks format
    if (data.Invoices && Array.isArray(data.Invoices)) {
      return data.Invoices.map((invoice: any) => ({
        id: invoice.Id,
        number: invoice.DocNumber || `INV-${invoice.Id}`,
        customerName: invoice.CustomerRef?.name || 'Unknown Customer',
        date: invoice.TxnDate,
        amount: invoice.TotalAmt,
        status: invoice.status || 'unknown',
        currency: invoice.CurrencyRef?.value || defaultCurrency
      }));
    }
    
    // For other ERP systems, return the raw data and log a warning
    console.warn('No specific mapper found for this ERP data, using raw data');
    return Array.isArray(data) ? data : [];
  };

  // Use the provided mapper or fall back to the default
  const invoiceMapper = mapResponseToInvoices || defaultMapResponseToInvoices;

  useEffect(() => {
    if (!organizationId || !integrationId) return;
    
    fetchInvoices();
  }, [organizationId, integrationId, page, rowsPerPage, showDraft]);

  const fetchInvoices = async () => {
    if (!organizationId || !integrationId) return;
    
    try {
      setLoading(true);
      
      const queryParams = new URLSearchParams({
        page: String(page + 1), // API uses 1-indexed pages
        page_size: String(rowsPerPage),
        include_draft: String(showDraft)
      });
      
      if (searchTerm) {
        queryParams.append('search', searchTerm);
      }
      
      // Use custom endpoint if provided, otherwise generate based on ERP type
      const endpoint = customEndpoint || 
        `/api/v1/organizations/${organizationId}/integrations/${integrationId}/${erpType}/invoices`;
      
      const response = await apiClient.get(`${endpoint}?${queryParams}`);
      
      // Transform the response data into our generic format
      const mappedInvoices = invoiceMapper(response.data);
      setInvoices(mappedInvoices);
      
      // Handle pagination info from response
      setTotalInvoices(response.data.total || mappedInvoices.length);
      
      // Set currency if available from response
      if (response.data.currency) {
        setCurrency(response.data.currency);
      }
      
      setError(null);
    } catch (err: any) {
      console.error('Error fetching invoices:', err);
      setError(err.message || 'Failed to fetch invoices');
      setInvoices([]);
    } finally {
      setLoading(false);
    }
  };

  const handleChangePage = (newPage: number) => {
    setPage(newPage);
  };

  const handleChangeRowsPerPage = (event: React.ChangeEvent<HTMLSelectElement>) => {
    setRowsPerPage(parseInt(event.target.value, 10));
    setPage(0); // Reset to first page
  };

  const handleToggleDraftInvoices = () => {
    setShowDraft(!showDraft);
    setPage(0); // Reset to first page
  };

  const handleRefresh = () => {
    fetchInvoices();
  };

  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault();
    fetchInvoices();
  };

  // Default status styling
  const defaultStatusMapping = {
    'posted': { label: 'Posted', color: 'bg-green-100 text-green-800' },
    'draft': { label: 'Draft', color: 'bg-gray-100 text-gray-800' },
    'cancel': { label: 'Cancelled', color: 'bg-red-100 text-red-800' },
    'paid': { label: 'Paid', color: 'bg-blue-100 text-blue-800' },
    'open': { label: 'Open', color: 'bg-yellow-100 text-yellow-800' },
    'overdue': { label: 'Overdue', color: 'bg-orange-100 text-orange-800' },
    'void': { label: 'Void', color: 'bg-gray-100 text-gray-800' },
    'error': { label: 'Error', color: 'bg-red-100 text-red-800' },
    'synced': { label: 'Synced', color: 'bg-green-100 text-green-800' }
  };

  // Merge provided status mapping with defaults
  const mergedStatusMapping = { ...defaultStatusMapping, ...(statusMapping || {}) };

  const getStatusInfo = (status: string) => {
    const normalizedStatus = status.toLowerCase();
    if (mergedStatusMapping[normalizedStatus]) {
      return mergedStatusMapping[normalizedStatus];
    }
    
    // Default fallback for unknown statuses
    return { 
      label: status.charAt(0).toUpperCase() + status.slice(1), 
      color: 'bg-gray-100 text-gray-800' 
    };
  };

  return (
    <div>
      <div className="mb-6 flex justify-between items-center flex-wrap">
        <h2 className="text-lg font-medium mb-2">
          {title || `Invoices from ${erpType.charAt(0).toUpperCase() + erpType.slice(1)}`}
        </h2>
        <div className="flex gap-2">
          <form onSubmit={handleSearch} className="relative">
            <input
              type="text"
              placeholder="Search invoices..."
              className="py-1.5 pl-8 pr-3 text-sm border border-gray-300 rounded-md w-56"
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
            />
            <Search size={16} className="absolute left-2.5 top-1/2 transform -translate-y-1/2 text-gray-400" />
          </form>
          
          <button
            className={`px-3 py-1.5 text-sm border rounded-md flex items-center gap-1.5 ${showDraft ? 'border-blue-600 text-blue-600' : 'border-gray-300 text-gray-700'}`}
            onClick={handleToggleDraftInvoices}
          >
            <Filter size={16} />
            {showDraft ? 'Hide Draft' : 'Show Draft'}
          </button>
          
          <button
            className="px-3 py-1.5 text-sm border border-gray-300 rounded-md flex items-center gap-1.5 text-gray-700 hover:bg-gray-50"
            onClick={handleRefresh}
          >
            <RefreshCw size={16} />
            Refresh
          </button>
        </div>
      </div>

      {error && <ErrorAlert message={error} onClose={() => setError(null)} className="mb-4" />}
      
      {loading && invoices.length === 0 ? (
        <div className="flex justify-center my-8">
          <Loader2 className="h-8 w-8 animate-spin text-gray-400" />
        </div>
      ) : invoices.length === 0 ? (
        <div className="p-6 text-center bg-white rounded-md shadow-sm border border-gray-100">
          <AlertCircle className="h-8 w-8 text-gray-400 mx-auto mb-2" />
          <p className="text-gray-500">
            No invoices found in your {erpType.charAt(0).toUpperCase() + erpType.slice(1)} instance.
            {!showDraft && " Try showing draft invoices."}
          </p>
          <button 
            className="mt-4 px-4 py-2 text-sm border border-gray-300 rounded-md flex items-center gap-1.5 mx-auto text-gray-700 hover:bg-gray-50"
            onClick={handleRefresh} 
          >
            <RefreshCw size={16} />
            Refresh
          </button>
        </div>
      ) : (
        <>
          <div className="overflow-x-auto rounded-md border border-gray-200 bg-white">
            <table className="min-w-full divide-y divide-gray-200">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Invoice Number</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Customer</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Date</th>
                  <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">Amount</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Status</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Signature</th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-200">
                {invoices.map((invoice) => {
                  const statusInfo = getStatusInfo(invoice.status);
                  return (
                    <tr key={invoice.id} className="hover:bg-gray-50">
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">{invoice.number}</td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">{invoice.customerName}</td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">{formatDate(invoice.date)}</td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900 text-right">
                        {formatCurrency(invoice.amount, invoice.currency || currency)}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <span className={`px-2 py-1 text-xs rounded-full ${statusInfo.color}`}>
                          {statusInfo.label}
                        </span>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        {invoice.csid ? (
                          <InvoiceSignatureVisualizer 
                            invoiceData={invoice} 
                            compact={true} 
                          />
                        ) : (
                          <span className="text-xs text-gray-500">No signature</span>
                        )}
                      </td>
                    </tr>
                  );
                })}
                {loading && (
                  <tr>
                    <td colSpan={6} className="px-6 py-4 text-center">
                      <Loader2 className="h-5 w-5 animate-spin text-gray-400 mx-auto" />
                    </td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>
          
          <div className="flex items-center justify-between py-3 bg-white border-t border-gray-200 px-4 mt-1 rounded-md">
            <div className="flex items-center space-x-2">
              <span className="text-sm text-gray-700">
                Rows per page:
              </span>
              <select
                className="border border-gray-300 rounded p-1 text-sm"
                value={rowsPerPage}
                onChange={handleChangeRowsPerPage}
              >
                {[5, 10, 25, 50].map((option) => (
                  <option key={option} value={option}>
                    {option}
                  </option>
                ))}
              </select>
            </div>
            
            <div className="flex items-center">
              <span className="text-sm text-gray-700 mr-4">
                {page * rowsPerPage + 1}-{Math.min((page + 1) * rowsPerPage, totalInvoices)} of {totalInvoices}
              </span>
              <div className="flex space-x-1">
                <button
                  className="p-1 rounded border border-gray-300 disabled:opacity-50"
                  onClick={() => handleChangePage(page - 1)}
                  disabled={page === 0}
                >
                  <svg className="h-5 w-5 text-gray-500" fill="currentColor" viewBox="0 0 20 20">
                    <path fillRule="evenodd" d="M12.707 5.293a1 1 0 010 1.414L9.414 10l3.293 3.293a1 1 0 01-1.414 1.414l-4-4a1 1 0 010-1.414l4-4a1 1 0 011.414 0z" clipRule="evenodd" />
                  </svg>
                </button>
                <button
                  className="p-1 rounded border border-gray-300 disabled:opacity-50"
                  onClick={() => handleChangePage(page + 1)}
                  disabled={page >= Math.ceil(totalInvoices / rowsPerPage) - 1}
                >
                  <svg className="h-5 w-5 text-gray-500" fill="currentColor" viewBox="0 0 20 20">
                    <path fillRule="evenodd" d="M7.293 14.707a1 1 0 010-1.414L10.586 10 7.293 6.707a1 1 0 011.414-1.414l4 4a1 1 0 010 1.414l-4 4a1 1 0 01-1.414 0z" clipRule="evenodd" />
                  </svg>
                </button>
              </div>
            </div>
          </div>
        </>
      )}
    </div>
  );
};

export default ERPInvoicesTab;
