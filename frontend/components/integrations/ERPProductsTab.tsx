import React, { useState, useEffect } from 'react';
import { Search, RefreshCw, Loader2, AlertCircle, Package, Tag } from 'lucide-react';
import { apiClient } from '@/utils/apiClient';
import { formatCurrency } from '@/utils/dateUtils';
import ErrorAlert from '@/components/common/ErrorAlert';

// Generic product interface that can accommodate different ERP systems
interface GenericProduct {
  id: string | number;
  name: string;
  code?: string;
  description?: string;
  price: number;
  currency?: string;
  category?: string;
  type?: string;
  taxRate?: number;
  taxable?: boolean;
  stockQuantity?: number;
  [key: string]: any;  // Allow additional fields
}

interface ERPProductsTabProps {
  organizationId?: string;
  integrationId: string;
  erpType: 'odoo' | 'quickbooks' | 'sap' | 'oracle' | 'dynamics';
  title?: string;
  mapResponseToProducts?: (data: any) => GenericProduct[];
  customEndpoint?: string;
  defaultCurrency?: string;
}

const ERPProductsTab: React.FC<ERPProductsTabProps> = ({
  organizationId,
  integrationId,
  erpType,
  title,
  mapResponseToProducts,
  customEndpoint,
  defaultCurrency = 'NGN'
}) => {
  const [products, setProducts] = useState<GenericProduct[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [page, setPage] = useState(0);
  const [rowsPerPage, setRowsPerPage] = useState(10);
  const [totalProducts, setTotalProducts] = useState(0);
  const [searchTerm, setSearchTerm] = useState('');
  const [currency, setCurrency] = useState(defaultCurrency);
  const [selectedCategory, setSelectedCategory] = useState<string>('');
  const [categories, setCategories] = useState<string[]>([]);

  // Default product mapper (can be overridden with prop)
  const defaultMapResponseToProducts = (data: any): GenericProduct[] => {
    // Handle Odoo format
    if (data.products && Array.isArray(data.products)) {
      const mappedProducts = data.products.map((product: any) => ({
        id: product.id,
        name: product.name,
        code: product.default_code,
        description: product.description,
        price: product.list_price,
        currency: product.currency_id?.name || defaultCurrency,
        category: product.categ_id?.name,
        type: product.type,
        taxRate: product.taxes_id?.rate || 0,
        taxable: Array.isArray(product.taxes_id) && product.taxes_id.length > 0,
        stockQuantity: product.qty_available
      }));

      // Extract unique categories for filtering
      const uniqueCategories = Array.from(
        new Set(mappedProducts.map(p => p.category).filter(Boolean))
      ) as string[];
      setCategories(uniqueCategories);

      return mappedProducts;
    }
    
    // Handle QuickBooks format
    if (data.Items && Array.isArray(data.Items)) {
      const mappedProducts = data.Items.map((product: any) => ({
        id: product.Id,
        name: product.Name,
        code: product.Sku,
        description: product.Description,
        price: product.UnitPrice,
        currency: product.CurrencyRef?.value || defaultCurrency,
        category: product.Category,
        type: product.Type,
        taxRate: product.SalesTaxIncluded ? product.SalesTaxRate : 0,
        taxable: product.SalesTaxIncluded,
        stockQuantity: product.QtyOnHand
      }));

      // Extract unique categories for filtering
      const uniqueCategories = Array.from(
        new Set(mappedProducts.map(p => p.category).filter(Boolean))
      ) as string[];
      setCategories(uniqueCategories);

      return mappedProducts;
    }
    
    // For other ERP systems, return the raw data and log a warning
    console.warn('No specific mapper found for this ERP data, using raw data');
    return Array.isArray(data) ? data : [];
  };

  // Use the provided mapper or fall back to the default
  const productMapper = mapResponseToProducts || defaultMapResponseToProducts;

  useEffect(() => {
    if (!organizationId || !integrationId) return;
    
    fetchProducts();
  }, [organizationId, integrationId, page, rowsPerPage, selectedCategory]);

  const fetchProducts = async () => {
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

      if (selectedCategory) {
        queryParams.append('category', selectedCategory);
      }
      
      // Use custom endpoint if provided, otherwise generate based on ERP type
      const endpoint = customEndpoint || 
        `/api/v1/organizations/${organizationId}/integrations/${integrationId}/${erpType}/products`;
      
      const response = await apiClient.get(`${endpoint}?${queryParams}`);
      
      // Transform the response data into our generic format
      const mappedProducts = productMapper(response.data);
      setProducts(mappedProducts);
      
      // Handle pagination info from response
      setTotalProducts(response.data.total || mappedProducts.length);
      
      // Set currency if available from response
      if (response.data.currency) {
        setCurrency(response.data.currency);
      }
      
      setError(null);
    } catch (err: any) {
      console.error('Error fetching products:', err);
      setError(err.message || 'Failed to fetch products');
      setProducts([]);
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
    fetchProducts();
  };

  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault();
    setPage(0); // Reset to first page
    fetchProducts();
  };

  const handleCategoryChange = (e: React.ChangeEvent<HTMLSelectElement>) => {
    setSelectedCategory(e.target.value);
    setPage(0); // Reset to first page
  };

  return (
    <div>
      <div className="mb-6 flex justify-between items-center flex-wrap">
        <h2 className="text-lg font-medium mb-2">
          {title || `Products from ${erpType.charAt(0).toUpperCase() + erpType.slice(1)}`}
        </h2>
        <div className="flex gap-2">
          <form onSubmit={handleSearch} className="relative">
            <input
              type="text"
              placeholder="Search products..."
              className="py-1.5 pl-8 pr-3 text-sm border border-gray-300 rounded-md w-56"
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
            />
            <Search size={16} className="absolute left-2.5 top-1/2 transform -translate-y-1/2 text-gray-400" />
          </form>
          
          {categories.length > 0 && (
            <select
              className="py-1.5 px-3 text-sm border border-gray-300 rounded-md"
              value={selectedCategory}
              onChange={handleCategoryChange}
            >
              <option value="">All Categories</option>
              {categories.map((category) => (
                <option key={category} value={category}>
                  {category}
                </option>
              ))}
            </select>
          )}
          
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
      
      {loading && products.length === 0 ? (
        <div className="flex justify-center my-8">
          <Loader2 className="h-8 w-8 animate-spin text-gray-400" />
        </div>
      ) : products.length === 0 ? (
        <div className="p-6 text-center bg-white rounded-md shadow-sm border border-gray-100">
          <AlertCircle className="h-8 w-8 text-gray-400 mx-auto mb-2" />
          <p className="text-gray-500">
            No products found in your {erpType.charAt(0).toUpperCase() + erpType.slice(1)} instance.
            {selectedCategory && " Try selecting a different category or clear the category filter."}
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
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Product</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Code</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Category</th>
                  <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">Price</th>
                  <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">Stock</th>
                  <th className="px-6 py-3 text-center text-xs font-medium text-gray-500 uppercase tracking-wider">Taxable</th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-200">
                {products.map((product) => (
                  <tr key={product.id} className="hover:bg-gray-50">
                    <td className="px-6 py-4">
                      <div className="flex items-start">
                        <Package className="h-5 w-5 text-gray-400 mr-2 mt-0.5 flex-shrink-0" />
                        <div>
                          <div className="text-sm font-medium text-gray-900">{product.name}</div>
                          {product.description && (
                            <div className="text-xs text-gray-500 mt-1 line-clamp-2">{product.description}</div>
                          )}
                        </div>
                      </div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                      {product.code || 'N/A'}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      {product.category ? (
                        <div className="flex items-center">
                          <Tag className="h-4 w-4 text-gray-400 mr-1.5" />
                          <span className="text-sm text-gray-900">{product.category}</span>
                        </div>
                      ) : (
                        <span className="text-sm text-gray-500">Uncategorized</span>
                      )}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900 text-right">
                      {formatCurrency(product.price, product.currency || currency)}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-right">
                      {typeof product.stockQuantity === 'number' ? (
                        <span className={`font-medium ${product.stockQuantity > 0 ? 'text-green-600' : 'text-red-600'}`}>
                          {product.stockQuantity}
                        </span>
                      ) : (
                        <span className="text-gray-500">N/A</span>
                      )}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-center">
                      {product.taxable ? (
                        <span className="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-blue-100 text-blue-800">
                          {product.taxRate ? `${product.taxRate}%` : 'Yes'}
                        </span>
                      ) : (
                        <span className="text-gray-500 text-sm">No</span>
                      )}
                    </td>
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
                {page * rowsPerPage + 1}-{Math.min((page + 1) * rowsPerPage, totalProducts)} of {totalProducts}
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
                  disabled={page >= Math.ceil(totalProducts / rowsPerPage) - 1}
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

export default ERPProductsTab;
