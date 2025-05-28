import React, { useState, useEffect } from 'react';
import { Search, Filter, RefreshCw, Loader2 } from 'lucide-react';
import { apiClient } from '@/utils/apiClient';
import { formatDate, formatCurrency } from '@/utils/dateUtils';
import ErrorAlert from '@/components/common/ErrorAlert';

interface Invoice {
  id: number;
  name: string;
  partner_id: {
    id: number;
    name: string;
  };
  date: string;
  amount_total: number;
  state: string;
  currency?: string;
}

interface OdooInvoicesTabProps {
  organizationId?: string;
  integrationId: string;
}

const OdooInvoicesTab: React.FC<OdooInvoicesTabProps> = ({ 
  organizationId, 
  integrationId 
}) => {
  const [invoices, setInvoices] = useState<Invoice[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [page, setPage] = useState(0);
  const [rowsPerPage, setRowsPerPage] = useState(10);
  const [totalInvoices, setTotalInvoices] = useState(0);
  const [searchTerm, setSearchTerm] = useState('');
  const [includeDraft, setIncludeDraft] = useState(false);
  const [currency, setCurrency] = useState('NGN'); // Default currency

  useEffect(() => {
    if (!organizationId || !integrationId) return;
    
    fetchInvoices();
  }, [organizationId, integrationId, page, rowsPerPage, includeDraft]);

  const fetchInvoices = async () => {
    if (!organizationId || !integrationId) return;
    
    try {
      setLoading(true);
      
      const queryParams = new URLSearchParams({
        page: String(page + 1), // API uses 1-indexed pages
        page_size: String(rowsPerPage),
        include_draft: String(includeDraft)
      });
      
      const response = await apiClient.get(
        `/api/v1/organizations/${organizationId}/integrations/${integrationId}/odoo/invoices?${queryParams}`
      );
      
      setInvoices(response.data.invoices || []);
      setTotalInvoices(response.data.total || 0);
      setCurrency(response.data.invoices?.[0]?.currency || 'NGN');
      setError(null);
    } catch (err: any) {
      console.error('Failed to fetch invoices:', err);
      setError(err.response?.data?.detail || 'Failed to fetch invoices from Odoo');
      setInvoices([]);
    } finally {
      setLoading(false);
    }
  };

  const handleChangePage = (_event: unknown, newPage: number) => {
    setPage(newPage);
  };

  const handleChangeRowsPerPage = (event: React.ChangeEvent<HTMLInputElement>) => {
    setRowsPerPage(parseInt(event.target.value, 10));
    setPage(0);
  };

  const handleToggleDraftInvoices = () => {
    setIncludeDraft(!includeDraft);
    setPage(0);
  };

  const handleRefresh = () => {
    fetchInvoices();
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'posted':
        return 'bg-green-100 text-green-800';
      case 'draft':
        return 'bg-gray-100 text-gray-800';
      case 'cancel':
        return 'bg-red-100 text-red-800';
      default:
        return 'bg-blue-100 text-blue-800';
    }
  };

  const getStatusLabel = (status: string) => {
    switch (status) {
      case 'posted':
        return 'Posted';
      case 'draft':
        return 'Draft';
      case 'cancel':
        return 'Cancelled';
      default:
        return status.charAt(0).toUpperCase() + status.slice(1);
    }
  };

  return (
    <div>
      <div className="mb-6 flex justify-between items-center flex-wrap">
        <h2 className="text-lg font-medium mb-2">
          Invoices from Odoo
        </h2>
        <div className="flex gap-2">
          <button
            className={`px-3 py-1.5 text-sm border rounded-md flex items-center gap-1.5 ${includeDraft ? 'border-blue-600 text-blue-600' : 'border-gray-300 text-gray-700'}`}
            onClick={handleToggleDraftInvoices}
          >
            <Filter size={16} />
            {includeDraft ? 'Hide Draft' : 'Show Draft'}
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
          <p className="text-gray-500">
            No invoices found in your Odoo instance.
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
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-200">
                {invoices.map((invoice) => (
                  <tr key={invoice.id} className="hover:bg-gray-50">
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">{invoice.name}</td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">{invoice.partner_id.name}</td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">{formatDate(invoice.date)}</td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900 text-right">
                      {formatCurrency(invoice.amount_total, invoice.currency || currency)}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <span className={`px-2 py-1 text-xs rounded-full ${getStatusColor(invoice.state)}`}>
                        {getStatusLabel(invoice.state)}
                      </span>
                    </td>
                  </tr>
                ))}
                {loading && (
                  <tr>
                    <td colSpan={5} className="px-6 py-4 text-center">
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
                className="border border-gray-300 rounded px-2 py-1 text-sm"
                value={rowsPerPage}
                onChange={(e) => {
                  setRowsPerPage(parseInt(e.target.value, 10));
                  setPage(0);
                }}
              >
                {[5, 10, 25, 50].map((option) => (
                  <option key={option} value={option}>{option}</option>
                ))}
              </select>
            </div>
            <div className="flex items-center space-x-2">
              <span className="text-sm text-gray-700">
                {page * rowsPerPage + 1}-{Math.min((page + 1) * rowsPerPage, totalInvoices)} of {totalInvoices}
              </span>
              <div className="flex">
                <button
                  className="p-1 rounded border border-gray-300 disabled:opacity-50 disabled:cursor-not-allowed"
                  disabled={page === 0}
                  onClick={() => handleChangePage(null, page - 1)}
                >
                  <svg className="h-5 w-5" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
                  </svg>
                </button>
                <button
                  className="p-1 rounded border border-gray-300 ml-1 disabled:opacity-50 disabled:cursor-not-allowed"
                  disabled={(page + 1) * rowsPerPage >= totalInvoices}
                  onClick={() => handleChangePage(null, page + 1)}
                >
                  <svg className="h-5 w-5" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
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

export default OdooInvoicesTab;
