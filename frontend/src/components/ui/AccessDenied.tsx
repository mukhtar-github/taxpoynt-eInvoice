import React from 'react';
import { useRouter } from 'next/router';
import { useServicePermissions } from '../../hooks/useServicePermissions';

interface AccessDeniedProps {
  service?: string;
  requiredLevel?: string;
  message?: string;
  showRetry?: boolean;
  showUpgrade?: boolean;
}

export const AccessDenied: React.FC<AccessDeniedProps> = ({
  service,
  requiredLevel,
  message,
  showRetry = true,
  showUpgrade = false
}) => {
  const router = useRouter();
  const permissions = useServicePermissions();

  const getServiceDisplayName = (serviceType: string): string => {
    const serviceNames = {
      'access_point_provider': 'Access Point Provider',
      'system_integration': 'System Integration',
      'nigerian_compliance': 'Nigerian Compliance',
      'organization_management': 'Organization Management',
      'firs_api_access': 'FIRS API Access',
      'dashboard_access': 'Dashboard Access'
    };
    return serviceNames[serviceType as keyof typeof serviceNames] || serviceType;
  };

  const handleRetry = () => {
    window.location.reload();
  };

  const handleGoBack = () => {
    if (window.history.length > 1) {
      router.back();
    } else {
      router.push(permissions.getDefaultRoute());
    }
  };

  const handleUpgrade = () => {
    router.push('/pricing');
  };

  const defaultMessage = service 
    ? `You don't have ${requiredLevel || 'read'} access to ${getServiceDisplayName(service)}`
    : 'You don\'t have permission to access this feature';

  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-50">
      <div className="max-w-md w-full mx-auto">
        <div className="bg-white shadow-lg rounded-lg p-8 text-center">
          {/* Icon */}
          <div className="mx-auto flex items-center justify-center h-16 w-16 rounded-full bg-red-100 mb-6">
            <svg 
              className="h-8 w-8 text-red-600" 
              fill="none" 
              stroke="currentColor" 
              viewBox="0 0 24 24"
            >
              <path 
                strokeLinecap="round" 
                strokeLinejoin="round" 
                strokeWidth={2} 
                d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.964-.833-2.732 0L3.732 16.5c-.77.833.192 2.5 1.732 2.5z" 
              />
            </svg>
          </div>

          {/* Title */}
          <h2 className="text-2xl font-bold text-gray-900 mb-4">
            Access Denied
          </h2>

          {/* Message */}
          <p className="text-gray-600 mb-6">
            {message || defaultMessage}
          </p>

          {/* Service Info */}
          {service && (
            <div className="bg-gray-50 rounded-lg p-4 mb-6">
              <div className="text-sm text-gray-700">
                <p><strong>Required Service:</strong> {getServiceDisplayName(service)}</p>
                {requiredLevel && (
                  <p><strong>Required Level:</strong> {requiredLevel}</p>
                )}
                {permissions.getAccessLevel(service) && (
                  <p><strong>Your Level:</strong> {permissions.getAccessLevel(service)}</p>
                )}
              </div>
            </div>
          )}

          {/* Action Buttons */}
          <div className="flex flex-col sm:flex-row gap-3 justify-center">
            <button
              onClick={handleGoBack}
              className="px-6 py-3 bg-gray-600 text-white rounded-lg hover:bg-gray-700 transition-colors duration-200 font-medium"
            >
              Go Back
            </button>

            {showRetry && (
              <button
                onClick={handleRetry}
                className="px-6 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors duration-200 font-medium"
              >
                Retry
              </button>
            )}

            {showUpgrade && (
              <button
                onClick={handleUpgrade}
                className="px-6 py-3 bg-green-600 text-white rounded-lg hover:bg-green-700 transition-colors duration-200 font-medium"
              >
                Upgrade Access
              </button>
            )}
          </div>

          {/* Help Text */}
          <div className="mt-6 text-sm text-gray-500">
            <p>
              If you believe this is an error, please contact your administrator or 
              <a href="mailto:support@taxpoynt.com" className="text-blue-600 hover:underline ml-1">
                support
              </a>
            </p>
          </div>
        </div>
      </div>
    </div>
  );
};

export default AccessDenied;