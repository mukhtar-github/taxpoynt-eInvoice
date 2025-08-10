/**
 * Role Switcher Component
 * ======================
 * 
 * Allows users to switch between different roles (SI, APP, Hybrid) when they have
 * multiple role assignments. Provides a seamless interface for role-based view
 * switching with proper state management and UI updates.
 * 
 * Features:
 * - Visual role switching interface
 * - Role-specific navigation updates
 * - Permission context updates
 * - Smooth transitions between role views
 * - Integration with role detector and permission provider
 * - Accessibility support
 */

import React, { useState, useEffect } from 'react';
import { useRoleDetector, PlatformRole } from './role_detector';
import { usePermissions } from './permission_provider';

// Role metadata for UI display
interface RoleMetadata {
  role: PlatformRole;
  displayName: string;
  description: string;
  icon: string;
  color: string;
  capabilities: string[];
  primaryFeatures: string[];
}

// Role switching state
interface RoleSwitchState {
  isLoading: boolean;
  error: string | null;
  previousRole: PlatformRole | null;
  switchHistory: Array<{
    role: PlatformRole;
    timestamp: Date;
    reason?: string;
  }>;
}

// Component props
interface RoleSwitcherProps {
  variant?: 'dropdown' | 'tabs' | 'cards';
  size?: 'sm' | 'md' | 'lg';
  showDescription?: boolean;
  showCapabilities?: boolean;
  className?: string;
  onRoleSwitch?: (newRole: PlatformRole, previousRole: PlatformRole) => void;
  disabled?: boolean;
}

// Role metadata definitions
const ROLE_METADATA: Record<PlatformRole, RoleMetadata> = {
  [PlatformRole.SYSTEM_INTEGRATOR]: {
    role: PlatformRole.SYSTEM_INTEGRATOR,
    displayName: 'System Integrator',
    description: 'Manage integrations with ERPs, CRMs, and business systems',
    icon: '🔗',
    color: 'blue',
    capabilities: [
      'ERP Integration',
      'Certificate Management', 
      'Schema Validation',
      'Commercial Billing'
    ],
    primaryFeatures: [
      'Connect business systems',
      'Generate e-invoices',
      'Manage service packages',
      'Access billing dashboard'
    ]
  },
  [PlatformRole.ACCESS_POINT_PROVIDER]: {
    role: PlatformRole.ACCESS_POINT_PROVIDER,
    displayName: 'Access Point Provider',
    description: 'Submit invoices to FIRS and manage compliance',
    icon: '🏛️',
    color: 'green',
    capabilities: [
      'FIRS Submission',
      'Compliance Monitoring',
      'Grant Management',
      'Taxpayer Services'
    ],
    primaryFeatures: [
      'Submit to FIRS',
      'Monitor compliance',
      'Track grant status',
      'Manage taxpayers'
    ]
  },
  [PlatformRole.HYBRID]: {
    role: PlatformRole.HYBRID,
    displayName: 'Hybrid Premium',
    description: 'Full access to both SI and APP capabilities',
    icon: '👑',
    color: 'purple',
    capabilities: [
      'Complete SI Access',
      'Complete APP Access',
      'Advanced Analytics',
      'Premium Support'
    ],
    primaryFeatures: [
      'All SI features',
      'All APP features',
      'Advanced reporting',
      'Priority support'
    ]
  },
  [PlatformRole.PLATFORM_ADMIN]: {
    role: PlatformRole.PLATFORM_ADMIN,
    displayName: 'Platform Admin',
    description: 'Administer the entire TaxPoynt platform',
    icon: '⚙️',
    color: 'red',
    capabilities: [
      'User Management',
      'System Configuration',
      'Grant Administration',
      'Platform Monitoring'
    ],
    primaryFeatures: [
      'Manage all users',
      'Configure platform',
      'Monitor grants',
      'System health'
    ]
  },
  [PlatformRole.TENANT_ADMIN]: {
    role: PlatformRole.TENANT_ADMIN,
    displayName: 'Tenant Admin',
    description: 'Administer your organization',
    icon: '👥',
    color: 'orange',
    capabilities: [
      'Organization Management',
      'User Administration',
      'Settings Configuration',
      'Usage Monitoring'
    ],
    primaryFeatures: [
      'Manage organization',
      'Add/remove users',
      'Configure settings',
      'View usage reports'
    ]
  },
  [PlatformRole.USER]: {
    role: PlatformRole.USER,
    displayName: 'User',
    description: 'Basic platform access',
    icon: '👤',
    color: 'gray',
    capabilities: [
      'View Invoices',
      'Basic Reporting',
      'Profile Management'
    ],
    primaryFeatures: [
      'View data',
      'Generate reports',
      'Update profile'
    ]
  }
};

export const RoleSwitcher: React.FC<RoleSwitcherProps> = ({
  variant = 'dropdown',
  size = 'md',
  showDescription = true,
  showCapabilities = false,
  className = '',
  onRoleSwitch,
  disabled = false
}) => {
  const { detectionResult, switchRole, isLoading: roleLoading } = useRoleDetector();
  const { refreshPermissions } = usePermissions();
  
  const [switchState, setSwitchState] = useState<RoleSwitchState>({
    isLoading: false,
    error: null,
    previousRole: null,
    switchHistory: []
  });

  const [isDropdownOpen, setIsDropdownOpen] = useState(false);

  // Get available roles for switching
  const availableRoles = detectionResult?.availableRoles || [];
  const currentRole = detectionResult?.primaryRole;
  const canSwitchRoles = detectionResult?.canSwitchRoles || false;

  // Filter available roles (exclude current role)
  const switchableRoles = availableRoles.filter(role => role !== currentRole);

  // Handle role switch
  const handleRoleSwitch = async (newRole: PlatformRole) => {
    if (disabled || !canSwitchRoles || newRole === currentRole) return;

    setSwitchState(prev => ({
      ...prev,
      isLoading: true,
      error: null
    }));

    try {
      const success = await switchRole(newRole);
      
      if (success) {
        // Update switch history
        setSwitchState(prev => ({
          ...prev,
          isLoading: false,
          previousRole: currentRole || null,
          switchHistory: [
            ...prev.switchHistory,
            {
              role: newRole,
              timestamp: new Date(),
              reason: 'User initiated switch'
            }
          ].slice(-10) // Keep last 10 switches
        }));

        // Refresh permissions after role switch
        await refreshPermissions();
        
        // Notify parent component
        if (onRoleSwitch && currentRole) {
          onRoleSwitch(newRole, currentRole);
        }

        // Close dropdown if open
        setIsDropdownOpen(false);

        // Show success message (optional)
        console.log(`Successfully switched to ${ROLE_METADATA[newRole].displayName}`);
        
      } else {
        throw new Error('Role switch failed');
      }
      
    } catch (error) {
      setSwitchState(prev => ({
        ...prev,
        isLoading: false,
        error: error instanceof Error ? error.message : 'Role switch failed'
      }));
    }
  };

  // Size classes
  const sizeClasses = {
    sm: 'text-sm px-2 py-1',
    md: 'text-base px-3 py-2',
    lg: 'text-lg px-4 py-3'
  };

  // Color classes for roles
  const getColorClasses = (role: PlatformRole) => {
    const color = ROLE_METADATA[role].color;
    return {
      blue: 'bg-blue-50 text-blue-700 border-blue-200 hover:bg-blue-100',
      green: 'bg-green-50 text-green-700 border-green-200 hover:bg-green-100',
      purple: 'bg-purple-50 text-purple-700 border-purple-200 hover:bg-purple-100',
      red: 'bg-red-50 text-red-700 border-red-200 hover:bg-red-100',
      orange: 'bg-orange-50 text-orange-700 border-orange-200 hover:bg-orange-100',
      gray: 'bg-gray-50 text-gray-700 border-gray-200 hover:bg-gray-100'
    }[color];
  };

  // Don't render if user can't switch roles or has only one role
  if (!canSwitchRoles || switchableRoles.length === 0 || !currentRole) {
    return null;
  }

  // Dropdown variant
  if (variant === 'dropdown') {
    return (
      <div className={`relative inline-block text-left ${className}`}>
        {/* Current Role Button */}
        <button
          type="button"
          className={`
            inline-flex items-center justify-center w-full rounded-lg border
            ${getColorClasses(currentRole)} ${sizeClasses[size]}
            ${disabled ? 'opacity-50 cursor-not-allowed' : 'cursor-pointer'}
            font-medium focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500
            transition-colors duration-200
          `}
          onClick={() => setIsDropdownOpen(!isDropdownOpen)}
          disabled={disabled || switchState.isLoading}
          aria-haspopup="true"
          aria-expanded={isDropdownOpen}
        >
          <span className="mr-2">{ROLE_METADATA[currentRole].icon}</span>
          <span>{ROLE_METADATA[currentRole].displayName}</span>
          {switchState.isLoading ? (
            <svg className="ml-2 w-4 h-4 animate-spin" fill="none" viewBox="0 0 24 24">
              <circle cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" className="opacity-25"/>
              <path fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" className="opacity-75"/>
            </svg>
          ) : (
            <svg className="ml-2 w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M19 9l-7 7-7-7"/>
            </svg>
          )}
        </button>

        {/* Dropdown Menu */}
        {isDropdownOpen && (
          <div className="origin-top-right absolute right-0 mt-2 w-72 rounded-lg shadow-lg bg-white ring-1 ring-black ring-opacity-5 focus:outline-none z-50">
            <div className="py-1" role="menu">
              {switchableRoles.map((role) => {
                const metadata = ROLE_METADATA[role];
                return (
                  <button
                    key={role}
                    className={`
                      group flex items-start w-full px-4 py-3 text-left
                      hover:bg-gray-50 focus:bg-gray-50 focus:outline-none
                      transition-colors duration-150
                    `}
                    role="menuitem"
                    onClick={() => handleRoleSwitch(role)}
                  >
                    <span className="mr-3 text-lg">{metadata.icon}</span>
                    <div className="flex-1">
                      <div className="font-medium text-gray-900">
                        {metadata.displayName}
                      </div>
                      {showDescription && (
                        <div className="text-sm text-gray-500 mt-1">
                          {metadata.description}
                        </div>
                      )}
                      {showCapabilities && (
                        <div className="flex flex-wrap gap-1 mt-2">
                          {metadata.capabilities.slice(0, 2).map((capability) => (
                            <span
                              key={capability}
                              className="inline-block px-2 py-1 text-xs bg-gray-100 text-gray-600 rounded"
                            >
                              {capability}
                            </span>
                          ))}
                          {metadata.capabilities.length > 2 && (
                            <span className="text-xs text-gray-400">
                              +{metadata.capabilities.length - 2} more
                            </span>
                          )}
                        </div>
                      )}
                    </div>
                  </button>
                );
              })}
            </div>
          </div>
        )}

        {/* Error Display */}
        {switchState.error && (
          <div className="absolute top-full left-0 right-0 mt-1 p-2 bg-red-50 border border-red-200 rounded text-red-700 text-sm">
            {switchState.error}
          </div>
        )}
      </div>
    );
  }

  // Tabs variant
  if (variant === 'tabs') {
    return (
      <div className={`border-b border-gray-200 ${className}`}>
        <nav className="-mb-px flex space-x-8">
          {/* Current Role Tab */}
          <div
            className={`
              py-2 px-1 border-b-2 border-blue-500 text-blue-600 font-medium text-sm
              ${sizeClasses[size]}
            `}
          >
            <span className="mr-2">{ROLE_METADATA[currentRole].icon}</span>
            {ROLE_METADATA[currentRole].displayName}
          </div>

          {/* Switchable Role Tabs */}
          {switchableRoles.map((role) => {
            const metadata = ROLE_METADATA[role];
            return (
              <button
                key={role}
                className={`
                  py-2 px-1 border-b-2 border-transparent text-gray-500 hover:text-gray-700 
                  hover:border-gray-300 font-medium text-sm cursor-pointer
                  ${sizeClasses[size]}
                  ${disabled ? 'opacity-50 cursor-not-allowed' : ''}
                  transition-colors duration-200
                `}
                onClick={() => handleRoleSwitch(role)}
                disabled={disabled || switchState.isLoading}
              >
                <span className="mr-2">{metadata.icon}</span>
                {metadata.displayName}
              </button>
            );
          })}
        </nav>
      </div>
    );
  }

  // Cards variant
  if (variant === 'cards') {
    return (
      <div className={`grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4 ${className}`}>
        {/* Current Role Card */}
        <div className={`
          border-2 border-blue-500 rounded-lg p-4 bg-blue-50
          ${sizeClasses[size]}
        `}>
          <div className="flex items-center justify-between mb-2">
            <span className="text-2xl">{ROLE_METADATA[currentRole].icon}</span>
            <span className="text-xs bg-blue-100 text-blue-800 px-2 py-1 rounded-full">
              Current
            </span>
          </div>
          <h3 className="font-medium text-blue-900">
            {ROLE_METADATA[currentRole].displayName}
          </h3>
          {showDescription && (
            <p className="text-sm text-blue-700 mt-1">
              {ROLE_METADATA[currentRole].description}
            </p>
          )}
        </div>

        {/* Switchable Role Cards */}
        {switchableRoles.map((role) => {
          const metadata = ROLE_METADATA[role];
          return (
            <button
              key={role}
              className={`
                border-2 border-gray-200 rounded-lg p-4 bg-white hover:border-gray-300
                hover:shadow-sm text-left transition-all duration-200
                ${disabled ? 'opacity-50 cursor-not-allowed' : 'cursor-pointer'}
                ${sizeClasses[size]}
                focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500
              `}
              onClick={() => handleRoleSwitch(role)}
              disabled={disabled || switchState.isLoading}
            >
              <div className="flex items-center justify-between mb-2">
                <span className="text-2xl">{metadata.icon}</span>
                <span className="text-xs bg-gray-100 text-gray-600 px-2 py-1 rounded-full">
                  Switch to
                </span>
              </div>
              <h3 className="font-medium text-gray-900">
                {metadata.displayName}
              </h3>
              {showDescription && (
                <p className="text-sm text-gray-600 mt-1">
                  {metadata.description}
                </p>
              )}
              {showCapabilities && (
                <div className="flex flex-wrap gap-1 mt-3">
                  {metadata.capabilities.slice(0, 3).map((capability) => (
                    <span
                      key={capability}
                      className="inline-block px-2 py-1 text-xs bg-gray-100 text-gray-600 rounded"
                    >
                      {capability}
                    </span>
                  ))}
                </div>
              )}
            </button>
          );
        })}
      </div>
    );
  }

  return null;
};

// Quick role switch hook for programmatic switching
export const useRoleSwitch = () => {
  const { detectionResult, switchRole } = useRoleDetector();
  const { refreshPermissions } = usePermissions();

  const quickSwitch = async (targetRole: PlatformRole): Promise<boolean> => {
    if (!detectionResult?.canSwitchRoles) return false;
    
    const success = await switchRole(targetRole);
    if (success) {
      await refreshPermissions();
    }
    return success;
  };

  return {
    currentRole: detectionResult?.primaryRole,
    availableRoles: detectionResult?.availableRoles || [],
    canSwitch: detectionResult?.canSwitchRoles || false,
    quickSwitch
  };
};

export default RoleSwitcher;