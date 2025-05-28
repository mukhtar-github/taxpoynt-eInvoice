import React, { useState, useEffect } from 'react';
import { Search, RefreshCw, Loader2, AlertCircle, User, Building, Phone, Mail } from 'lucide-react';
import { apiClient } from '@/utils/apiClient';
import { formatDate } from '@/utils/dateUtils';
import ErrorAlert from '@/components/common/ErrorAlert';

// Generic customer interface that can accommodate different ERP systems
interface GenericCustomer {
  id: string | number;
  name: string;
  email?: string;
  phone?: string;
  address?: {
    street?: string;
    city?: string;
    state?: string;
    zip?: string;
    country?: string;
  };
  taxId?: string;
  type?: string;  // 'company', 'individual', etc.
  createdAt?: string;
  [key: string]: any;  // Allow additional fields
}

interface ERPCustomersTabProps {
  organizationId?: string;
  integrationId: string;
  erpType: 'odoo' | 'quickbooks' | 'sap' | 'oracle' | 'dynamics';
  title?: string;
  mapResponseToCustomers?: (data: any) => GenericCustomer[];
  customEndpoint?: string;
}

const ERPCustomersTab: React.FC<ERPCustomersTabProps> = ({
  organizationId,
  integrationId,
  erpType,
  title,
  mapResponseToCustomers,
  customEndpoint
}) => {
  const [customers, setCustomers] = useState<GenericCustomer[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [page, setPage] = useState(0);
  const [rowsPerPage, setRowsPerPage] = useState(10);
  const [totalCustomers, setTotalCustomers] = useState(0);
  const [searchTerm, setSearchTerm] = useState('');

  // Default customer mapper (can be overridden with prop)
  const defaultMapResponseToCustomers = (data: any): GenericCustomer[] => {
    // Handle Odoo format
    if (data.customers && Array.isArray(data.customers)) {
      return data.customers.map((customer: any) => ({
        id: customer.id,
        name: customer.name,
        email: customer.email,
        phone: customer.phone,
        address: {
          street: customer.street,
          city: customer.city,
          state: customer.state_id?.name,
          zip: customer.zip,
          country: customer.country_id?.name
        },
        taxId: customer.vat,
        type: customer.is_company ? 'company' : 'individual',
        createdAt: customer.create_date
      }));
    }
    
    // Handle QuickBooks format
    if (data.Customers && Array.isArray(data.Customers)) {
      return data.Customers.map((customer: any) => {
        const primaryAddress = customer.BillAddr || {};
        return {
          id: customer.Id,
          name: customer.DisplayName || customer.CompanyName || `${customer.GivenName || ''} ${customer.FamilyName || ''}`.trim(),
          email: customer.PrimaryEmailAddr?.Address,
          phone: customer.PrimaryPhone?.FreeFormNumber,
          address: {
            street: primaryAddress.Line1,
            city: primaryAddress.City,
            state: primaryAddress.CountrySubDivisionCode,
            zip: primaryAddress.PostalCode,
            country: primaryAddress.Country
          },
          taxId: customer.TaxIdentifier,
          type: customer.CompanyName ? 'company' : 'individual',
          createdAt: customer.MetaData?.CreateTime
        };
      });
    }
    
    // For other ERP systems, return the raw data and log a warning
    console.warn('No specific mapper found for this ERP data, using raw data');
    return Array.isArray(data) ? data : [];
  };

  // Use the provided mapper or fall back to the default
  const customerMapper = mapResponseToCustomers || defaultMapResponseToCustomers;

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
        queryParams.append('search', searchTerm);
      }
      
      // Use custom endpoint if provided, otherwise generate based on ERP type
      const endpoint = customEndpoint || 
        `/api/v1/organizations/${organizationId}/integrations/${integrationId}/${erpType}/customers`;
      
      const response = await apiClient.get(`${endpoint}?${queryParams}`);
      
      // Transform the response data into our generic format
      const mappedCustomers = customerMapper(response.data);
      setCustomers(mappedCustomers);
      
      // Handle pagination info from response
      setTotalCustomers(response.data.total || mappedCustomers.length);
      
      setError(null);
    } catch (err: any) {
      console.error('Error fetching customers:', err);
      setError(err.message || 'Failed to fetch customers');
      setCustomers([]);
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

  const handleRefresh = () => {
    fetchCustomers();
  };

  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault();
    fetchCustomers();
  };

  // Helper to format address
  const formatAddress = (address?: GenericCustomer['address']) => {
    if (!address) return 'N/A';
    
    const parts: string[] = [];
    if (address.street) parts.push(address.street);
    if (address.city) parts.push(address.city);
    if (address.state) parts.push(address.state);
    if (address.zip) parts.push(address.zip);
    if (address.country) parts.push(address.country);
    
    return parts.join(', ') || 'N/A';
  };

  return (
    <div>
      <div className="mb-6 flex justify-between items-center flex-wrap">
        <h2 className="text-lg font-medium mb-2">
          {title || `Customers from ${erpType.charAt(0).toUpperCase() + erpType.slice(1)}`}
        </h2>
        <div className="flex gap-2">
          <form onSubmit={handleSearch} className="relative">
            <input
              type="text"
              placeholder="Search customers..."
              className="py-1.5 pl-8 pr-3 text-sm border border-gray-300 rounded-md w-56"
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
            />
            <Search size={16} className="absolute left-2.5 top-1/2 transform -translate-y-1/2 text-gray-400" />
          </form>
          
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
      
      {loading && customers.length === 0 ? (
        <div className="flex justify-center my-8">
          <Loader2 className="h-8 w-8 animate-spin text-gray-400" />
        </div>
      ) : customers.length === 0 ? (
        <div className="p-6 text-center bg-white rounded-md shadow-sm border border-gray-100">
          <AlertCircle className="h-8 w-8 text-gray-400 mx-auto mb-2" />
          <p className="text-gray-500">
            No customers found in your {erpType.charAt(0).toUpperCase() + erpType.slice(1)} instance.
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
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Contact Info</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Address</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Type</th>
                  {erpType === 'odoo' && (
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Tax ID</th>
                  )}
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-200">
                {customers.map((customer) => (
                  <tr key={customer.id} className="hover:bg-gray-50">
                    <td className="px-6 py-4 whitespace-nowrap">
                      <div className="flex items-center">
                        {customer.type === 'company' ? (
                          <Building className="h-5 w-5 text-gray-400 mr-2" />
                        ) : (
                          <User className="h-5 w-5 text-gray-400 mr-2" />
                        )}
                        <div className="text-sm font-medium text-gray-900">{customer.name}</div>
                      </div>
                    </td>
                    <td className="px-6 py-4">
                      <div className="text-sm text-gray-900">
                        {customer.email && (
                          <div className="flex items-center mb-1">
                            <Mail className="h-4 w-4 text-gray-400 mr-1.5" />
                            <a href={`mailto:${customer.email}`} className="text-blue-600 hover:text-blue-800">{customer.email}</a>
                          </div>
                        )}
                        {customer.phone && (
                          <div className="flex items-center">
                            <Phone className="h-4 w-4 text-gray-400 mr-1.5" />
                            <span>{customer.phone}</span>
                          </div>
                        )}
                        {!customer.email && !customer.phone && <span className="text-gray-500">No contact info</span>}
                      </div>
                    </td>
                    <td className="px-6 py-4">
                      <div className="text-sm text-gray-900">{formatAddress(customer.address)}</div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <span className={`px-2 py-1 text-xs rounded-full ${customer.type === 'company' ? 'bg-blue-100 text-blue-800' : 'bg-green-100 text-green-800'}`}>
                        {customer.type === 'company' ? 'Company' : 'Individual'}
                      </span>
                    </td>
                    {erpType === 'odoo' && (
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                        {customer.taxId || 'N/A'}
                      </td>
                    )}
                  </tr>
                ))}
                {loading && (
                  <tr>
                    <td colSpan={erpType === 'odoo' ? 5 : 4} className="px-6 py-4 text-center">
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
                {page * rowsPerPage + 1}-{Math.min((page + 1) * rowsPerPage, totalCustomers)} of {totalCustomers}
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
                  disabled={page >= Math.ceil(totalCustomers / rowsPerPage) - 1}
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

export default ERPCustomersTab;
