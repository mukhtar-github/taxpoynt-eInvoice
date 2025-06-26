/**
 * Nigerian Mobile Optimized Components
 * Components specifically optimized for Nigerian mobile networks and usage patterns
 */

import React, { useState, useEffect } from 'react';
import { useNigerianNetwork } from '../../hooks/useNigerianNetwork';

interface MobileOptimizedImageProps {
  src: string;
  alt: string;
  className?: string;
  priority?: boolean;
}

export const MobileOptimizedImage: React.FC<MobileOptimizedImageProps> = ({
  src,
  alt,
  className = '',
  priority = false
}) => {
  const { nigerianOptimizations, networkState } = useNigerianNetwork();
  const [imageSrc, setImageSrc] = useState<string>('');
  const [isLoading, setIsLoading] = useState(true);
  const [hasError, setHasError] = useState(false);

  useEffect(() => {
    // Use optimized image URL based on network conditions
    const optimizedSrc = nigerianOptimizations.getOptimizedImageUrl(src);
    setImageSrc(optimizedSrc);
  }, [src, nigerianOptimizations]);

  const handleLoad = () => setIsLoading(false);
  const handleError = () => {
    setHasError(true);
    setIsLoading(false);
  };

  if (hasError) {
    return (
      <div className={`bg-gray-200 flex items-center justify-center ${className}`}>
        <span className="text-gray-500 text-sm">Image unavailable</span>
      </div>
    );
  }

  return (
    <div className={`relative ${className}`}>
      {isLoading && (
        <div className="absolute inset-0 bg-gray-200 animate-pulse" />
      )}
      <img
        src={imageSrc}
        alt={alt}
        className={`${className} ${isLoading ? 'opacity-0' : 'opacity-100'} transition-opacity`}
        onLoad={handleLoad}
        onError={handleError}
        loading={priority ? 'eager' : 'lazy'}
      />
      {networkState.isSlowConnection && (
        <div className="absolute top-2 right-2 bg-yellow-500 text-white text-xs px-2 py-1 rounded">
          Slow
        </div>
      )}
    </div>
  );
};

interface DataSaverNoticeProps {
  onOptimize: () => void;
  onProceed: () => void;
}

export const DataSaverNotice: React.FC<DataSaverNoticeProps> = ({
  onOptimize,
  onProceed
}) => {
  const { networkState } = useNigerianNetwork();

  if (!networkState.saveData && !networkState.isSlowConnection) {
    return null;
  }

  return (
    <div className="bg-orange-50 border border-orange-200 rounded-lg p-4 mb-4">
      <div className="flex items-start">
        <div className="flex-shrink-0">
          <svg className="h-5 w-5 text-orange-400" viewBox="0 0 20 20" fill="currentColor">
            <path fillRule="evenodd" d="M8.257 3.099c.765-1.36 2.722-1.36 3.486 0l5.58 9.92c.75 1.334-.213 2.98-1.742 2.98H4.42c-1.53 0-2.493-1.646-1.743-2.98l5.58-9.92zM11 13a1 1 0 11-2 0 1 1 0 012 0zm-1-8a1 1 0 00-1 1v3a1 1 0 002 0V6a1 1 0 00-1-1z" clipRule="evenodd" />
          </svg>
        </div>
        <div className="ml-3 flex-1">
          <h3 className="text-sm font-medium text-orange-800">
            {networkState.saveData ? 'Data Saver Mode Detected' : 'Slow Connection Detected'}
          </h3>
          <p className="mt-1 text-sm text-orange-700">
            We can optimize content to use less data and load faster.
          </p>
          <div className="mt-3 flex space-x-3">
            <button
              onClick={onOptimize}
              className="bg-orange-500 text-white px-3 py-1 rounded text-sm hover:bg-orange-600"
            >
              Optimize for {networkState.carrier || 'your network'}
            </button>
            <button
              onClick={onProceed}
              className="bg-gray-200 text-gray-800 px-3 py-1 rounded text-sm hover:bg-gray-300"
            >
              Continue normally
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};

interface NetworkStatusIndicatorProps {
  className?: string;
}

export const NetworkStatusIndicator: React.FC<NetworkStatusIndicatorProps> = ({
  className = ''
}) => {
  const { networkState } = useNigerianNetwork();

  const getStatusColor = () => {
    if (networkState.isOffline) return 'bg-red-500';
    if (networkState.isSlowConnection) return 'bg-yellow-500';
    if (networkState.effectiveType === '4g') return 'bg-green-500';
    return 'bg-blue-500';
  };

  const getStatusText = () => {
    if (networkState.isOffline) return 'Offline';
    if (networkState.effectiveType === '4g') return '4G';
    if (networkState.effectiveType === '3g') return '3G';
    if (networkState.effectiveType === '2g') return '2G';
    return 'Connected';
  };

  return (
    <div className={`flex items-center space-x-2 ${className}`}>
      <div className={`w-2 h-2 rounded-full ${getStatusColor()}`} />
      <span className="text-xs text-gray-600">
        {getStatusText()}
        {networkState.carrier && ` (${networkState.carrier})`}
      </span>
      {networkState.saveData && (
        <span className="text-xs bg-blue-100 text-blue-800 px-2 py-0.5 rounded">
          Data Saver
        </span>
      )}
    </div>
  );
};

interface ProgressiveLoadingProps {
  children: React.ReactNode;
  fallback?: React.ReactNode;
  threshold?: number;
}

export const ProgressiveLoading: React.FC<ProgressiveLoadingProps> = ({
  children,
  fallback,
  threshold = 2000
}) => {
  const { nigerianOptimizations, networkState } = useNigerianNetwork();
  const [shouldLoad, setShouldLoad] = useState(false);

  useEffect(() => {
    if (nigerianOptimizations.shouldLoadHeavyComponents()) {
      setShouldLoad(true);
    } else {
      // Delay loading for slow connections
      const timer = setTimeout(() => {
        setShouldLoad(true);
      }, threshold);

      return () => clearTimeout(timer);
    }
  }, [nigerianOptimizations, threshold]);

  if (!shouldLoad) {
    return (
      <div className="flex flex-col items-center justify-center p-8">
        {fallback || (
          <>
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-green-500 mb-4" />
            <p className="text-sm text-gray-600">
              Optimizing for {networkState.carrier || 'your network'}...
            </p>
          </>
        )}
      </div>
    );
  }

  return <>{children}</>;
};

interface TouchOptimizedButtonProps {
  children: React.ReactNode;
  onClick: () => void;
  variant?: 'primary' | 'secondary' | 'danger';
  size?: 'small' | 'medium' | 'large';
  disabled?: boolean;
  className?: string;
}

export const TouchOptimizedButton: React.FC<TouchOptimizedButtonProps> = ({
  children,
  onClick,
  variant = 'primary',
  size = 'medium',
  disabled = false,
  className = ''
}) => {
  const baseClasses = 'font-medium rounded-lg transition-colors focus:outline-none focus:ring-2 focus:ring-offset-2';
  
  const variantClasses = {
    primary: 'bg-green-600 hover:bg-green-700 text-white focus:ring-green-500',
    secondary: 'bg-gray-200 hover:bg-gray-300 text-gray-900 focus:ring-gray-500',
    danger: 'bg-red-600 hover:bg-red-700 text-white focus:ring-red-500'
  };

  const sizeClasses = {
    small: 'min-h-[36px] px-3 py-2 text-sm',
    medium: 'min-h-[44px] px-4 py-3 text-base',
    large: 'min-h-[52px] px-6 py-4 text-lg'
  };

  const disabledClasses = disabled 
    ? 'opacity-50 cursor-not-allowed' 
    : 'cursor-pointer active:scale-95';

  return (
    <button
      onClick={onClick}
      disabled={disabled}
      className={`
        ${baseClasses}
        ${variantClasses[variant]}
        ${sizeClasses[size]}
        ${disabledClasses}
        ${className}
      `}
    >
      {children}
    </button>
  );
};

export const MobileDashboardGrid: React.FC<{ children: React.ReactNode }> = ({
  children
}) => {
  return (
    <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4 p-4">
      {children}
    </div>
  );
};

export const NigerianCarrierOptimization: React.FC = () => {
  const { networkState } = useNigerianNetwork();

  const carrierTips = {
    MTN: 'MTN users: Use Wi-Fi when available for faster loading',
    Airtel: 'Airtel users: Data saver mode is automatically enabled',
    Glo: 'Glo users: Consider upgrading to 4G for better performance',
    '9mobile': '9mobile users: Limited 4G coverage, optimizing for 3G'
  };

  if (!networkState.carrier || !carrierTips[networkState.carrier as keyof typeof carrierTips]) {
    return null;
  }

  return (
    <div className="bg-blue-50 border border-blue-200 rounded-lg p-3 text-sm">
      <p className="text-blue-800">
        💡 {carrierTips[networkState.carrier as keyof typeof carrierTips]}
      </p>
    </div>
  );
};