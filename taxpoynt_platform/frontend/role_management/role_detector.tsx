/**
 * Role Detector
 * =============
 * 
 * Detects and manages user roles from authentication context, integrating with
 * TaxPoynt's backend role management system. Provides role detection functionality
 * for the frontend application.
 * 
 * Features:
 * - Detects user roles from JWT tokens and session data
 * - Integrates with backend PlatformRole and RoleScope enums
 * - Provides role validation and permission checking
 * - Manages role context throughout the application
 */

import React, { createContext, useContext, useEffect, useState, ReactNode } from 'react';
import { useRouter } from 'next/router';

// Types based on backend role management system
export enum PlatformRole {
  SYSTEM_INTEGRATOR = 'system_integrator',
  ACCESS_POINT_PROVIDER = 'access_point_provider', 
  HYBRID = 'hybrid',
  PLATFORM_ADMIN = 'platform_admin',
  TENANT_ADMIN = 'tenant_admin',
  USER = 'user'
}

export enum RoleScope {
  GLOBAL = 'global',
  TENANT = 'tenant',
  SERVICE = 'service',
  ENVIRONMENT = 'environment'
}

export enum RoleStatus {
  ACTIVE = 'active',
  INACTIVE = 'inactive',
  SUSPENDED = 'suspended',
  PENDING = 'pending',
  EXPIRED = 'expired'
}

export interface UserRoleAssignment {
  assignmentId: string;
  userId: string;
  platformRole: PlatformRole;
  scope: RoleScope;
  status: RoleStatus;
  permissions: string[];
  tenantId?: string;
  organizationId?: string;
  expiresAt?: Date;
  assignedAt: Date;
  metadata: Record<string, any>;
}

export interface RoleDetectionResult {
  primaryRole: PlatformRole;
  allRoles: UserRoleAssignment[];
  activePermissions: string[];
  canSwitchRoles: boolean;
  availableRoles: PlatformRole[];
  isHybridUser: boolean;
  currentScope: RoleScope;
  organizationId?: string;
  tenantId?: string;
}

export interface RoleDetectorContextValue {
  detectionResult: RoleDetectionResult | null;
  isLoading: boolean;
  error: string | null;
  refreshRoles: () => Promise<void>;
  switchRole: (role: PlatformRole) => Promise<boolean>;
  hasPermission: (permission: string) => boolean;
  hasRole: (role: PlatformRole) => boolean;
  canAccessRoute: (route: string) => boolean;
}

// Create context
const RoleDetectorContext = createContext<RoleDetectorContextValue | undefined>(undefined);

// Hook for using role detector context
export const useRoleDetector = (): RoleDetectorContextValue => {
  const context = useContext(RoleDetectorContext);
  if (!context) {
    throw new Error('useRoleDetector must be used within a RoleDetectorProvider');
  }
  return context;
};

// Role detection utility class
class FrontendRoleDetector {
  private static instance: FrontendRoleDetector;
  
  static getInstance(): FrontendRoleDetector {
    if (!this.instance) {
      this.instance = new FrontendRoleDetector();
    }
    return this.instance;
  }

  /**
   * Detect roles from authentication token
   */
  async detectRolesFromToken(token: string): Promise<RoleDetectionResult | null> {
    try {
      // Parse JWT token to extract role information
      const payload = this.parseJWTPayload(token);
      
      if (!payload) {
        throw new Error('Invalid token payload');
      }

      // Extract role assignments from token claims
      const roleAssignments = this.extractRoleAssignments(payload);
      
      if (roleAssignments.length === 0) {
        throw new Error('No valid role assignments found');
      }

      // Determine primary role and capabilities
      return this.buildDetectionResult(roleAssignments, payload);
      
    } catch (error) {
      console.error('Role detection failed:', error);
      return null;
    }
  }

  /**
   * Detect roles from session storage or API
   */
  async detectRolesFromSession(): Promise<RoleDetectionResult | null> {
    try {
      // Check session storage first
      const sessionRoles = sessionStorage.getItem('taxpoynt_user_roles');
      if (sessionRoles) {
        const parsed = JSON.parse(sessionRoles);
        if (this.isValidRoleData(parsed)) {
          return parsed;
        }
      }

      // Fallback to API call
      return await this.fetchRolesFromAPI();
      
    } catch (error) {
      console.error('Session role detection failed:', error);
      return null;
    }
  }

  /**
   * Fetch current user roles from API
   */
  private async fetchRolesFromAPI(): Promise<RoleDetectionResult | null> {
    try {
      const response = await fetch('/api/v1/auth/user-roles', {
        method: 'GET',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${this.getAuthToken()}`
        },
        credentials: 'include'
      });

      if (!response.ok) {
        throw new Error(`API request failed: ${response.status}`);
      }

      const data = await response.json();
      return this.processAPIRoleResponse(data);
      
    } catch (error) {
      console.error('API role fetch failed:', error);
      return null;
    }
  }

  /**
   * Parse JWT token payload
   */
  private parseJWTPayload(token: string): any {
    try {
      const parts = token.split('.');
      if (parts.length !== 3) {
        throw new Error('Invalid JWT format');
      }

      const payload = parts[1];
      const decoded = atob(payload.replace(/-/g, '+').replace(/_/g, '/'));
      return JSON.parse(decoded);
      
    } catch (error) {
      console.error('JWT parsing failed:', error);
      return null;
    }
  }

  /**
   * Extract role assignments from token payload
   */
  private extractRoleAssignments(payload: any): UserRoleAssignment[] {
    const assignments: UserRoleAssignment[] = [];
    
    try {
      // Extract from custom claims
      const roles = payload.roles || payload.user_roles || [];
      const permissions = payload.permissions || payload.user_permissions || [];
      
      // Process each role assignment
      roles.forEach((roleData: any) => {
        const assignment: UserRoleAssignment = {
          assignmentId: roleData.assignment_id || `temp_${Date.now()}`,
          userId: payload.sub || payload.user_id,
          platformRole: this.validatePlatformRole(roleData.role || roleData.platform_role),
          scope: this.validateRoleScope(roleData.scope || RoleScope.TENANT),
          status: this.validateRoleStatus(roleData.status || RoleStatus.ACTIVE),
          permissions: roleData.permissions || permissions,
          tenantId: roleData.tenant_id || payload.tenant_id,
          organizationId: roleData.organization_id || payload.organization_id,
          expiresAt: roleData.expires_at ? new Date(roleData.expires_at) : undefined,
          assignedAt: new Date(roleData.assigned_at || payload.iat * 1000),
          metadata: roleData.metadata || {}
        };
        
        assignments.push(assignment);
      });
      
      return assignments;
      
    } catch (error) {
      console.error('Role extraction failed:', error);
      return [];
    }
  }

  /**
   * Build complete role detection result
   */
  private buildDetectionResult(assignments: UserRoleAssignment[], payload: any): RoleDetectionResult {
    // Filter active assignments
    const activeAssignments = assignments.filter(a => a.status === RoleStatus.ACTIVE);
    
    // Determine primary role (preference: HYBRID > PLATFORM_ADMIN > SYSTEM_INTEGRATOR > ACCESS_POINT_PROVIDER > USER)
    const rolePriority = {
      [PlatformRole.HYBRID]: 5,
      [PlatformRole.PLATFORM_ADMIN]: 4,
      [PlatformRole.SYSTEM_INTEGRATOR]: 3,
      [PlatformRole.ACCESS_POINT_PROVIDER]: 2,
      [PlatformRole.TENANT_ADMIN]: 1,
      [PlatformRole.USER]: 0
    };
    
    const primaryAssignment = activeAssignments.reduce((prev, current) => 
      rolePriority[current.platformRole] > rolePriority[prev.platformRole] ? current : prev
    );

    // Collect all permissions
    const allPermissions = new Set<string>();
    activeAssignments.forEach(assignment => {
      assignment.permissions.forEach(permission => allPermissions.add(permission));
    });

    // Determine available roles for switching
    const availableRoles = Array.from(new Set(activeAssignments.map(a => a.platformRole)));
    
    // Check if user can switch between SI and APP roles
    const canSwitchRoles = availableRoles.includes(PlatformRole.HYBRID) || 
                          (availableRoles.includes(PlatformRole.SYSTEM_INTEGRATOR) && 
                           availableRoles.includes(PlatformRole.ACCESS_POINT_PROVIDER));

    return {
      primaryRole: primaryAssignment.platformRole,
      allRoles: activeAssignments,
      activePermissions: Array.from(allPermissions),
      canSwitchRoles,
      availableRoles,
      isHybridUser: availableRoles.includes(PlatformRole.HYBRID),
      currentScope: primaryAssignment.scope,
      organizationId: primaryAssignment.organizationId,
      tenantId: primaryAssignment.tenantId
    };
  }

  /**
   * Validation helpers
   */
  private validatePlatformRole(role: string): PlatformRole {
    if (Object.values(PlatformRole).includes(role as PlatformRole)) {
      return role as PlatformRole;
    }
    return PlatformRole.USER; // Default fallback
  }

  private validateRoleScope(scope: string): RoleScope {
    if (Object.values(RoleScope).includes(scope as RoleScope)) {
      return scope as RoleScope;
    }
    return RoleScope.TENANT; // Default fallback
  }

  private validateRoleStatus(status: string): RoleStatus {
    if (Object.values(RoleStatus).includes(status as RoleStatus)) {
      return status as RoleStatus;
    }
    return RoleStatus.ACTIVE; // Default fallback
  }

  /**
   * Utility methods
   */
  private isValidRoleData(data: any): boolean {
    return data && 
           data.primaryRole && 
           Array.isArray(data.allRoles) && 
           Array.isArray(data.activePermissions);
  }

  private processAPIRoleResponse(data: any): RoleDetectionResult | null {
    // Process API response and convert to RoleDetectionResult
    // This would be implemented based on your API response format
    return data.role_detection_result || null;
  }

  private getAuthToken(): string {
    // Get auth token from localStorage, cookies, or context
    return localStorage.getItem('taxpoynt_auth_token') || '';
  }
}

// Provider component props
interface RoleDetectorProviderProps {
  children: ReactNode;
  authToken?: string;
  fallbackRole?: PlatformRole;
}

// Provider component
export const RoleDetectorProvider: React.FC<RoleDetectorProviderProps> = ({
  children,
  authToken,
  fallbackRole = PlatformRole.USER
}) => {
  const [detectionResult, setDetectionResult] = useState<RoleDetectionResult | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const router = useRouter();

  const detector = FrontendRoleDetector.getInstance();

  // Initialize role detection
  useEffect(() => {
    detectRoles();
  }, [authToken]);

  const detectRoles = async () => {
    setIsLoading(true);
    setError(null);
    
    try {
      let result: RoleDetectionResult | null = null;

      // Try token-based detection first
      if (authToken) {
        result = await detector.detectRolesFromToken(authToken);
      }

      // Fallback to session-based detection
      if (!result) {
        result = await detector.detectRolesFromSession();
      }

      if (!result) {
        throw new Error('Unable to detect user roles');
      }

      setDetectionResult(result);
      
      // Cache roles in session storage
      sessionStorage.setItem('taxpoynt_user_roles', JSON.stringify(result));
      
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Role detection failed');
      console.error('Role detection error:', err);
    } finally {
      setIsLoading(false);
    }
  };

  const switchRole = async (targetRole: PlatformRole): Promise<boolean> => {
    if (!detectionResult) return false;

    try {
      // Check if role switching is allowed
      if (!detectionResult.canSwitchRoles) {
        throw new Error('Role switching not allowed for this user');
      }

      if (!detectionResult.availableRoles.includes(targetRole)) {
        throw new Error(`Role ${targetRole} not available for switching`);
      }

      // Update local state
      const updatedResult = { ...detectionResult, primaryRole: targetRole };
      setDetectionResult(updatedResult);
      
      // Update session storage
      sessionStorage.setItem('taxpoynt_user_roles', JSON.stringify(updatedResult));
      
      // Optionally notify backend about role switch
      try {
        await fetch('/api/v1/auth/switch-role', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${authToken}`
          },
          body: JSON.stringify({ target_role: targetRole }),
          credentials: 'include'
        });
      } catch (apiError) {
        console.warn('Backend role switch notification failed:', apiError);
        // Continue anyway as local switch succeeded
      }

      return true;
      
    } catch (err) {
      console.error('Role switch failed:', err);
      return false;
    }
  };

  const hasPermission = (permission: string): boolean => {
    return detectionResult?.activePermissions.includes(permission) || false;
  };

  const hasRole = (role: PlatformRole): boolean => {
    return detectionResult?.availableRoles.includes(role) || false;
  };

  const canAccessRoute = (route: string): boolean => {
    if (!detectionResult) return false;

    // Route access rules based on role
    const routeRules: Record<string, PlatformRole[]> = {
      '/admin': [PlatformRole.PLATFORM_ADMIN],
      '/billing': [PlatformRole.SYSTEM_INTEGRATOR, PlatformRole.HYBRID, PlatformRole.PLATFORM_ADMIN],
      '/service-packages': [PlatformRole.SYSTEM_INTEGRATOR, PlatformRole.HYBRID, PlatformRole.PLATFORM_ADMIN],
      '/firs-integration': [PlatformRole.ACCESS_POINT_PROVIDER, PlatformRole.HYBRID, PlatformRole.PLATFORM_ADMIN],
      '/grant-tracking': [PlatformRole.PLATFORM_ADMIN]
    };

    // Check if any of user's roles can access the route
    const allowedRoles = routeRules[route];
    if (!allowedRoles) return true; // Allow access to unprotected routes

    return detectionResult.availableRoles.some(role => allowedRoles.includes(role));
  };

  const contextValue: RoleDetectorContextValue = {
    detectionResult,
    isLoading,
    error,
    refreshRoles: detectRoles,
    switchRole,
    hasPermission,
    hasRole,
    canAccessRoute
  };

  return (
    <RoleDetectorContext.Provider value={contextValue}>
      {children}
    </RoleDetectorContext.Provider>
  );
};

// Export hook and utilities
export default RoleDetectorProvider;