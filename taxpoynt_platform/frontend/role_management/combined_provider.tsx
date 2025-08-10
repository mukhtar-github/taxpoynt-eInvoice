/**
 * Combined Role Management Provider
 * ================================
 * 
 * Combines all role management providers into a single convenient wrapper.
 * Provides the complete role management system with proper provider nesting
 * and configuration.
 * 
 * Features:
 * - Single provider setup for entire role management system
 * - Proper provider nesting order
 * - Shared configuration between providers
 * - Error boundary for role management failures
 * - Loading states and fallbacks
 */

import React, { ReactNode, useState, useEffect } from 'react';
import { RoleDetectorProvider, PlatformRole, useRoleDetector } from './role_detector';
import { PermissionProvider, Permission, usePermissions } from './permission_provider';
import { FeatureFlagProvider, useFeatureFlags } from './feature_flag_provider';

// Combined provider props
interface CombinedRoleProviderProps {
  children: ReactNode;
  
  // Authentication
  authToken?: string;
  fallbackRole?: PlatformRole;
  
  // Feature flags
  featureFlags?: Record<string, any>;
  remoteFeatureFlagConfig?: {
    endpoint?: string;
    apiKey?: string;
    syncInterval?: number;
  };
  
  // Permissions
  customPermissions?: Permission[];
  
  // Error handling
  onError?: (error: Error, context: string) => void;
  errorFallback?: ReactNode;
  
  // Loading
  loadingComponent?: ReactNode;
  
  // Development
  enableDevTools?: boolean;
  enableAuditLogging?: boolean;
}

// Error boundary for role management
class RoleManagementErrorBoundary extends React.Component<
  { children: ReactNode; fallback?: ReactNode; onError?: (error: Error, context: string) => void },
  { hasError: boolean; error: Error | null }
> {
  constructor(props: any) {
    super(props);
    this.state = { hasError: false, error: null };
  }

  static getDerivedStateFromError(error: Error) {
    return { hasError: true, error };
  }

  componentDidCatch(error: Error, errorInfo: React.ErrorInfo) {
    console.error('Role Management Error:', error, errorInfo);
    this.props.onError?.(error, 'role_management');
  }

  render() {
    if (this.state.hasError) {
      return this.props.fallback || (
        <div className="bg-red-50 border border-red-200 rounded-lg p-4 m-4">
          <div className="flex items-center">
            <svg className="h-5 w-5 text-red-400 mr-2" fill="currentColor" viewBox="0 0 20 20">
              <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clipRule="evenodd" />
            </svg>
            <div>
              <h3 className="text-sm font-medium text-red-800">Role Management Error</h3>
              <p className="text-sm text-red-700 mt-1">
                There was an error initializing the role management system. Some features may not work correctly.
              </p>
              {this.state.error && (
                <details className="mt-2">
                  <summary className="text-xs text-red-600 cursor-pointer">Error Details</summary>
                  <pre className="text-xs text-red-600 mt-1 overflow-auto">
                    {this.state.error.message}
                  </pre>
                </details>
              )}
            </div>
          </div>
        </div>
      );
    }

    return this.props.children;
  }
}

// Default loading component
const DefaultLoadingComponent: React.FC = () => (
  <div className="flex items-center justify-center min-h-screen">
    <div className="text-center">
      <svg className="animate-spin h-8 w-8 text-blue-600 mx-auto mb-4" fill="none" viewBox="0 0 24 24">
        <circle cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" className="opacity-25"/>
        <path fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" className="opacity-75"/>
      </svg>
      <h3 className="text-lg font-medium text-gray-900 mb-2">Initializing TaxPoynt</h3>
      <p className="text-gray-600">Setting up your role and permissions...</p>
    </div>
  </div>
);

// Development tools component
const DevTools: React.FC<{ enabled: boolean }> = ({ enabled }) => {
  const [isOpen, setIsOpen] = useState(false);
  
  if (!enabled || process.env.NODE_ENV === 'production') {
    return null;
  }

  return (
    <div className="fixed bottom-4 right-4 z-50">
      <button
        onClick={() => setIsOpen(!isOpen)}
        className="bg-purple-600 text-white p-2 rounded-full shadow-lg hover:bg-purple-700 transition-colors"
        title="Role Management Dev Tools"
      >
        🛠️
      </button>
      
      {isOpen && (
        <div className="absolute bottom-12 right-0 bg-white border rounded-lg shadow-xl p-4 w-80 max-h-96 overflow-auto">
          <h4 className="font-medium text-gray-900 mb-3">Role Management Dev Tools</h4>
          
          <div className="space-y-3">
            <RoleDebugInfo />
            <PermissionDebugInfo />
            <FeatureFlagDebugInfo />
          </div>
          
          <button
            onClick={() => setIsOpen(false)}
            className="mt-3 text-sm text-gray-500 hover:text-gray-700"
          >
            Close
          </button>
        </div>
      )}
    </div>
  );
};

// Debug components
const RoleDebugInfo: React.FC = () => {
  const { detectionResult } = useRoleDetector();
  
  return (
    <div className="border rounded p-2">
      <h5 className="text-sm font-medium text-gray-700 mb-1">Current Role</h5>
      <div className="text-xs text-gray-600">
        <div>Primary: {detectionResult?.primaryRole || 'None'}</div>
        <div>All: {detectionResult?.availableRoles.join(', ') || 'None'}</div>
        <div>Can Switch: {detectionResult?.canSwitchRoles ? 'Yes' : 'No'}</div>
      </div>
    </div>
  );
};

const PermissionDebugInfo: React.FC = () => {
  const { getUserPermissions } = usePermissions();
  const permissions = getUserPermissions();
  
  return (
    <div className="border rounded p-2">
      <h5 className="text-sm font-medium text-gray-700 mb-1">Permissions ({permissions.length})</h5>
      <div className="text-xs text-gray-600 max-h-20 overflow-auto">
        {permissions.length > 0 ? permissions.join(', ') : 'None'}
      </div>
    </div>
  );
};

const FeatureFlagDebugInfo: React.FC = () => {
  const { getEnabledFlags } = useFeatureFlags();
  const enabledFlags = getEnabledFlags();
  
  return (
    <div className="border rounded p-2">
      <h5 className="text-sm font-medium text-gray-700 mb-1">Feature Flags ({enabledFlags.length})</h5>
      <div className="text-xs text-gray-600 max-h-20 overflow-auto">
        {enabledFlags.length > 0 ? enabledFlags.join(', ') : 'None'}
      </div>
    </div>
  );
};

// Main combined provider component
export const CombinedRoleProvider: React.FC<CombinedRoleProviderProps> = ({
  children,
  authToken,
  fallbackRole,
  featureFlags = {},
  remoteFeatureFlagConfig,
  customPermissions = [],
  onError,
  errorFallback,
  loadingComponent,
  enableDevTools = false,
  enableAuditLogging = false
}) => {
  const [isInitialized, setIsInitialized] = useState(false);
  const [initializationError, setInitializationError] = useState<string | null>(null);

  // Initialize the system
  useEffect(() => {
    const initializeRoleSystem = async () => {
      try {
        // Any async initialization logic would go here
        // For now, we'll just simulate initialization
        await new Promise(resolve => setTimeout(resolve, 100));
        
        setIsInitialized(true);
      } catch (error) {
        const errorMessage = error instanceof Error ? error.message : 'Unknown initialization error';
        setInitializationError(errorMessage);
        onError?.(error instanceof Error ? error : new Error(errorMessage), 'initialization');
      }
    };

    initializeRoleSystem();
  }, [authToken, onError]);

  // Show loading while initializing
  if (!isInitialized && !initializationError) {
    return loadingComponent || <DefaultLoadingComponent />;
  }

  // Show error if initialization failed
  if (initializationError) {
    return errorFallback || (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-center">
          <h2 className="text-xl font-semibold text-red-600 mb-2">Initialization Failed</h2>
          <p className="text-gray-600 mb-4">{initializationError}</p>
          <button
            onClick={() => window.location.reload()}
            className="bg-blue-600 text-white px-4 py-2 rounded hover:bg-blue-700"
          >
            Reload Page
          </button>
        </div>
      </div>
    );
  }

  return (
    <RoleManagementErrorBoundary fallback={errorFallback} onError={onError}>
      <RoleDetectorProvider 
        authToken={authToken}
        fallbackRole={fallbackRole}
      >
        <PermissionProvider 
          customPermissions={customPermissions}
          featureFlags={featureFlags}
        >
          <FeatureFlagProvider
            remoteConfig={remoteFeatureFlagConfig}
            initialOverrides={featureFlags}
          >
            {children}
            <DevTools enabled={enableDevTools} />
          </FeatureFlagProvider>
        </PermissionProvider>
      </RoleDetectorProvider>
    </RoleManagementErrorBoundary>
  );
};

// Quick setup hook for common configurations
export const useRoleManagementSetup = (config: {
  authToken?: string;
  enableDevMode?: boolean;
}) => {
  return {
    Provider: ({ children }: { children: ReactNode }) => (
      <CombinedRoleProvider
        authToken={config.authToken}
        enableDevTools={config.enableDevMode}
        enableAuditLogging={config.enableDevMode}
      >
        {children}
      </CombinedRoleProvider>
    )
  };
};

// HOC for automatic role provider setup
export const withRoleManagement = (
  Component: React.ComponentType<any>,
  config?: Partial<CombinedRoleProviderProps>
) => {
  return (props: any) => (
    <CombinedRoleProvider {...config}>
      <Component {...props} />
    </CombinedRoleProvider>
  );
};

export default CombinedRoleProvider;