import React, { useState, useEffect } from 'react';
import { Search, RefreshCw, X, Loader2 } from 'lucide-react';
import { apiClient } from '@/utils/apiClient';
import { formatCurrency } from '@/utils/dateUtils';
import ErrorAlert from '@/components/common/ErrorAlert';

interface Product {
  id: number;
  name: string;
  code?: string;
  price: number;
  currency?: string;
  category?: string;
  type?: string;
  uom?: string;
}

interface OdooProductsTabProps {
  organizationId?: string;
  integrationId: string;
}

const OdooProductsTab: React.FC<OdooProductsTabProps> = ({ 
  organizationId, 
  integrationId 
}) => {
  const [products, setProducts] = useState<Product[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [page, setPage] = useState(0);
  const [rowsPerPage, setRowsPerPage] = useState(10);
  const [totalProducts, setTotalProducts] = useState(0);
  const [searchTerm, setSearchTerm] = useState('');
  const [hasMore, setHasMore] = useState(false);
  const [currency, setCurrency] = useState('NGN'); // Default currency

  useEffect(() => {
    if (!organizationId || !integrationId) return;
    
    fetchProducts();
  }, [organizationId, integrationId, page, rowsPerPage]);

  const fetchProducts = async () => {
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
        `/api/v1/organizations/${organizationId}/integrations/${integrationId}/odoo/products?${queryParams}`
      );
      
      setProducts(response.data.data || []);
      setTotalProducts(response.data.total || 0);
      setHasMore(response.data.has_more || false);
      
      // Set default currency from first product if available
      if (response.data.data && response.data.data.length > 0 && response.data.data[0].currency) {
        setCurrency(response.data.data[0].currency);
      }
      
      setError(null);
    } catch (err: any) {
      console.error('Failed to fetch products:', err);
      setError(err.response?.data?.detail || 'Failed to fetch products from Odoo');
      setProducts([]);
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
    fetchProducts();
  };

  const handleSearch = () => {
    setPage(0);
    fetchProducts();
  };

  const handleClearSearch = () => {
    setSearchTerm('');
    setPage(0);
    setTimeout(fetchProducts, 0);
  };

  const handleSearchKeyDown = (event: React.KeyboardEvent) => {
    if (event.key === 'Enter') {
      handleSearch();
    }
  };

  const getProductTypeColor = (type?: string) => {
    switch (type) {
      case 'service':
        return 'bg-blue-100 text-blue-800';
      case 'product':
        return 'bg-green-100 text-green-800';
      case 'consu':
        return 'bg-yellow-100 text-yellow-800';
      default:
        return 'bg-gray-100 text-gray-800';
    }
  };

  const getProductTypeLabel = (type?: string) => {
    switch (type) {
      case 'service':
        return 'Service';
      case 'product':
        return 'Storable';
      case 'consu':
        return 'Consumable';
      default:
        return type || 'Unknown';
    }
  };

  return (
    <div>
      <div className="mb-6 flex justify-between items-center flex-wrap">
        <h2 className="text-lg font-medium mb-2">
          Products from Odoo
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
            placeholder="Search products by name or code..."
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
      
      {loading && products.length === 0 ? (
        <div className="flex justify-center my-8">
          <Loader2 className="h-8 w-8 animate-spin text-gray-400" />
        </div>
      ) : products.length === 0 ? (
        <div className="p-6 text-center bg-white rounded-md shadow-sm border border-gray-100">
          <p className="text-gray-500">
            {searchTerm 
              ? `No products found matching "${searchTerm}"`
              : 'No products found in your Odoo instance.'
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
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Code</th>
                  <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">Price</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Category</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Type</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">UoM</th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-200">
                {products.map((product) => (
                  <tr key={product.id} className="hover:bg-gray-50">
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">{product.name}</td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">{product.code || '-'}</td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900 text-right">
                      {formatCurrency(product.price, product.currency || currency)}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">{product.category || '-'}</td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <span className={`px-2 py-1 text-xs rounded-full ${getProductTypeColor(product.type)}`}>
                        {getProductTypeLabel(product.type)}
                      </span>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">{product.uom || '-'}</td>
                  </tr>
                ))}
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
                  : `${page * rowsPerPage + 1}-${Math.min((page + 1) * rowsPerPage, totalProducts)} of ${totalProducts}`
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
                  disabled={!hasMore && (page + 1) * rowsPerPage >= totalProducts}
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

export default OdooProductsTab;
