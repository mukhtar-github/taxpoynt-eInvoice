import React from 'react';
import { Database } from 'lucide-react';
import { formatDate } from '@/utils/dateUtils';

interface Integration {
  id: string;
  name: string;
  description: string;
  integration_type: string;
  status: string;
  created_at: string;
  last_sync?: string;
  config: Record<string, any>;
}

interface CompanyInfo {
  id: number;
  name: string;
  vat?: string;
  email?: string;
  phone?: string;
  website?: string;
  currency?: string;
  logo?: string;
  address?: {
    street?: string;
    city?: string;
    country?: string;
  };
}

interface IntegrationInfoProps {
  integration: Integration;
  companyInfo: CompanyInfo | null;
}

const IntegrationInfo: React.FC<IntegrationInfoProps> = ({ integration, companyInfo }) => {
  const getStatusColor = (status: string) => {
    switch (status) {
      case 'configured':
        return 'bg-green-100 text-green-800';
      case 'pending':
        return 'bg-yellow-100 text-yellow-800';
      case 'error':
        return 'bg-red-100 text-red-800';
      default:
        return 'bg-gray-100 text-gray-800';
    }
  };

  const formatAddress = (address?: { street?: string; city?: string; country?: string }) => {
    if (!address) return 'N/A';
    
    const parts: string[] = [];
    if (address.street) parts.push(address.street);
    if (address.city) parts.push(address.city);
    if (address.country) parts.push(address.country);
    
    return parts.join(', ') || 'N/A';
  };

  return (
    <div className="p-6">
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <div>
          <div className="flex items-center mb-4">
            <div className="mr-4 text-blue-600">
              <Database className="h-6 w-6" />
            </div>
            <div>
              <h2 className="text-lg font-medium">
                {integration.name}
              </h2>
              <div className="flex items-center mt-1">
                <span className="text-sm text-gray-500 mr-2">
                  {integration.integration_type.toUpperCase()}
                </span>
                <span 
                  className={`px-2 py-1 text-xs rounded-full ${getStatusColor(integration.status)}`}
                >
                  {integration.status}
                </span>
              </div>
            </div>
          </div>

          {integration.description && (
            <p className="text-sm text-gray-600 mb-4">
              {integration.description}
            </p>
          )}

          <div className="grid grid-cols-2 gap-4 mt-2">
            <div>
              <span className="text-xs text-gray-500 block">
                Created on
              </span>
              <span className="text-sm">
                {formatDate(integration.created_at)}
              </span>
            </div>
            {integration.last_sync && (
              <div>
                <span className="text-xs text-gray-500 block">
                  Last synchronized
                </span>
                <span className="text-sm">
                  {formatDate(integration.last_sync)}
                </span>
              </div>
            )}
          </div>
        </div>

        {companyInfo && (
          <div>
            <div className="flex items-center mb-4">
              {companyInfo.logo ? (
                <img 
                  src={`data:image/png;base64,${companyInfo.logo}`} 
                  alt={companyInfo.name}
                  className="w-16 h-16 mr-4 rounded-full object-cover"
                />
              ) : (
                <div className="w-16 h-16 mr-4 rounded-full bg-blue-100 text-blue-600 flex items-center justify-center text-xl font-medium">
                  {companyInfo.name.charAt(0)}
                </div>
              )}
              <div>
                <h3 className="text-lg font-medium">
                  {companyInfo.name}
                </h3>
                {companyInfo.vat && (
                  <p className="text-sm text-gray-500">
                    VAT: {companyInfo.vat}
                  </p>
                )}
              </div>
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 mt-2">
              {companyInfo.email && (
                <div>
                  <span className="text-xs text-gray-500 block">
                    Email
                  </span>
                  <span className="text-sm truncate block">
                    {companyInfo.email}
                  </span>
                </div>
              )}
              {companyInfo.phone && (
                <div>
                  <span className="text-xs text-gray-500 block">
                    Phone
                  </span>
                  <span className="text-sm">
                    {companyInfo.phone}
                  </span>
                </div>
              )}
              {companyInfo.website && (
                <div>
                  <span className="text-xs text-gray-500 block">
                    Website
                  </span>
                  <span className="text-sm truncate block">
                    {companyInfo.website}
                  </span>
                </div>
              )}
              {companyInfo.currency && (
                <div>
                  <span className="text-xs text-gray-500 block">
                    Currency
                  </span>
                  <span className="text-sm">
                    {companyInfo.currency}
                  </span>
                </div>
              )}
              <div className="col-span-1 sm:col-span-2">
                <span className="text-xs text-gray-500 block">
                  Address
                </span>
                <span className="text-sm">
                  {formatAddress(companyInfo.address)}
                </span>
              </div>
            </div>
          </div>
        )}

        <div className="col-span-1 md:col-span-2">
          <div className="h-px bg-gray-200 my-4" />
          <h4 className="text-sm font-medium mb-3">
            Connection Details
          </h4>
          <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-4 gap-4">
            <div>
              <span className="text-xs text-gray-500 block">
                URL
              </span>
              <span className="text-sm truncate block">
                {integration.config.url || 'N/A'}
              </span>
            </div>
            <div>
              <span className="text-xs text-gray-500 block">
                Database
              </span>
              <span className="text-sm">
                {integration.config.database || 'N/A'}
              </span>
            </div>
            <div>
              <span className="text-xs text-gray-500 block">
                Username
              </span>
              <span className="text-sm">
                {integration.config.username || 'N/A'}
              </span>
            </div>
            <div>
              <span className="text-xs text-gray-500 block">
                Authentication
              </span>
              <span className="text-sm capitalize">
                {integration.config.auth_method || 'Password'}
              </span>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default IntegrationInfo;
