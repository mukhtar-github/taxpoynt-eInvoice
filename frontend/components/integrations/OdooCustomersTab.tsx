import React, { useState, useEffect } from 'react';
import { Search, RefreshCw, X, Loader2 } from 'lucide-react';
import { apiClient } from '@/utils/apiClient';
import ErrorAlert from '@/components/common/ErrorAlert';

interface Customer {
  id: number;
  name: string;
  email?: string;
  phone?: string;
  vat?: string;
  street?: string;
  city?: string;
  country?: string;
}

interface OdooCustomersTabProps {
  organizationId?: string;
  integrationId: string;
}

const OdooCustomersTab: React.FC<OdooCustomersTabProps> = ({ 
  organizationId, 
  integrationId 
}) => {
  const [customers, setCustomers] = useState<Customer[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [page, setPage] = useState(0);
  const [rowsPerPage, setRowsPerPage] = useState(10);
  const [totalCustomers, setTotalCustomers] = useState(0);
  const [searchTerm, setSearchTerm] = useState('');
  const [hasMore, setHasMore] = useState(false);

  useEffect(() => {
    if (!organizationId || !integrationId) return;
    
    fetchCustomers();
  }, [organizationId, integrationId, page, rowsPerPage]);

  const fetchCustomers = async () => {
    if (!organizationId || !integrationId) return;
    
    try {
      setLoading(true);
      
      const queryParams = new URLSearchParams({
        page: String(page + 1), // API uses 1-indexed pages
        page_size: String(rowsPerPage)
      });
      
      if (searchTerm) {
        queryParams.append('search_term', searchTerm);
      }
      
      const response = await apiClient.get(
        `/api/v1/organizations/${organizationId}/integrations/${integrationId}/odoo/customers?${queryParams}`
      );
      
      setCustomers(response.data.data || []);
      setTotalCustomers(response.data.total || 0);
      setHasMore(response.data.has_more || false);
      setError(null);
    } catch (err: any) {
      console.error('Failed to fetch customers:', err);
      setError(err.response?.data?.detail || 'Failed to fetch customers from Odoo');
      setCustomers([]);
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

  const handleRefresh = () => {
    fetchCustomers();
  };

  const handleSearch = () => {
    setPage(0);
    fetchCustomers();
  };

  const handleClearSearch = () => {
    setSearchTerm('');
    setPage(0);
    setTimeout(fetchCustomers, 0);
  };

  const handleSearchKeyDown = (event: React.KeyboardEvent) => {
    if (event.key === 'Enter') {
      handleSearch();
    }
  };

  return (
    <div>
      <div className="mb-6 flex justify-between items-center flex-wrap">
        <h2 className="text-lg font-medium mb-2">
          Customers from Odoo
        </h2>
        <button
          className="px-3 py-1.5 text-sm border border-gray-300 rounded-md flex items-center gap-1.5 text-gray-700 hover:bg-gray-50"
          onClick={handleRefresh}
        >
          <RefreshCw size={16} />
          Refresh
        </button>
      </div>

      <div className="mb-6">
        <div className="relative mb-2">
          <div className="absolute inset-y-0 left-0 flex items-center pl-3 pointer-events-none">
            <Search className="h-4 w-4 text-gray-400" />
          </div>
          <input
            type="text"
            className="block w-full pl-10 pr-10 py-2 border border-gray-300 rounded-md focus:ring-blue-500 focus:border-blue-500 text-sm"
            placeholder="Search customers by name, email, or VAT..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            onKeyDown={handleSearchKeyDown}
          />
          {searchTerm && (
            <button 
              className="absolute inset-y-0 right-12 flex items-center pr-3"
              onClick={handleClearSearch}
            >
              <X className="h-4 w-4 text-gray-400 hover:text-gray-500" />
            </button>
          )}
        </div>
        <button 
          className="px-4 py-2 bg-blue-600 text-white rounded-md text-sm hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed"
          onClick={handleSearch} 
          disabled={loading}
        >
          Search
        </button>
      </div>

      {error && <ErrorAlert message={error} onClose={() => setError(null)} className="mb-4" />}
      
      {loading && customers.length === 0 ? (
        <div className="flex justify-center my-8">
          <Loader2 className="h-8 w-8 animate-spin text-gray-400" />
        </div>
      ) : customers.length === 0 ? (
        <div className="p-6 text-center bg-white rounded-md shadow-sm border border-gray-100">
          <p className="text-gray-500">
            {searchTerm 
              ? `No customers found matching "${searchTerm}"`
              : 'No customers found in your Odoo instance.'
            }
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
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Name</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Email</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Phone</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">VAT</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Address</th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-200">
                {customers.map((customer) => (
                  <tr key={customer.id} className="hover:bg-gray-50">
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">{customer.name}</td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">{customer.email || '-'}</td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">{customer.phone || '-'}</td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">{customer.vat || '-'}</td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                      {[customer.street, customer.city, customer.country]
                        .filter(Boolean)
                        .join(', ') || '-'}
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
                {hasMore 
                  ? `${page * rowsPerPage + 1}-${(page + 1) * rowsPerPage} (more available)`
                  : `${page * rowsPerPage + 1}-${Math.min((page + 1) * rowsPerPage, totalCustomers)} of ${totalCustomers}`
                }
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
                  disabled={!hasMore && (page + 1) * rowsPerPage >= totalCustomers}
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

export default OdooCustomersTab;
