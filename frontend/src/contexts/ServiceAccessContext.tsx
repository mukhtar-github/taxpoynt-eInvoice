import React, { createContext, useContext, useEffect, useState } from 'react';
import apiService from '../../utils/apiService';

export interface ServiceAccess {
  serviceType: string;
  accessLevel: string;
  expiresAt?: string;
  organizationId?: string;
}

interface ServiceContextType {
  userServices: ServiceAccess[];
  hasAccess: (service: string, level?: string) => boolean;
  getAccessLevel: (service: string) => string | null;
  isLoading: boolean;
  refreshServices: () => Promise<void>;
  error: string | null;
}

const ServiceAccessContext = createContext<ServiceContextType | undefined>(undefined);

export const ServiceAccessProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [userServices, setUserServices] = useState<ServiceAccess[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const hasAccess = (service: string, level: string = 'read'): boolean => {
    const accessLevels = { read: 1, write: 2, admin: 3, owner: 4 };
    
    const userAccess = userServices.find(s => s.serviceType === service);
    if (!userAccess) return false;
    
    // Check expiration
    if (userAccess.expiresAt && new Date(userAccess.expiresAt) < new Date()) {
      return false;
    }
    
    const userLevel = accessLevels[userAccess.accessLevel as keyof typeof accessLevels];
    const requiredLevel = accessLevels[level as keyof typeof accessLevels];
    
    return userLevel >= requiredLevel;
  };

  const getAccessLevel = (service: string): string | null => {
    const userAccess = userServices.find(s => s.serviceType === service);
    return userAccess?.accessLevel || null;
  };

  const refreshServices = async () => {
    // Skip if not in browser environment
    if (typeof window === 'undefined') {
      setIsLoading(false);
      return;
    }

    try {
      setIsLoading(true);
      setError(null);
      
      // Check if user is authenticated
      const token = localStorage.getItem('token');
      if (!token) {
        setUserServices([]);
        setIsLoading(false);
        return;
      }

      // Fetch user services from API
      const response = await apiService.get('/api/v1/service-access/services/available');
      
      if (response.data) {
        const services = Array.isArray(response.data) ? response.data : [response.data];
        setUserServices(services.map((s: any) => ({
          serviceType: s.service_type || s.serviceType,
          accessLevel: s.access_level || s.accessLevel,
          expiresAt: s.expires_at || s.expiresAt,
          organizationId: s.organization_id || s.organizationId
        })));
      }
    } catch (err) {
      console.error('Failed to fetch user services:', err);
      
      // Fall back to localStorage permissions for compatibility
      try {
        const storedPermissions = localStorage.getItem('user_permissions');
        if (storedPermissions) {
          const permissions = JSON.parse(storedPermissions);
          const fallbackServices = permissions.map((permission: string) => ({
            serviceType: permission,
            accessLevel: 'read',
            expiresAt: undefined,
            organizationId: undefined
          }));
          setUserServices(fallbackServices);
          setError('Using cached permissions - some features may be limited');
        } else {
          setError('Failed to load user permissions');
        }
      } catch (fallbackError) {
        setError('Failed to load user permissions');
        setUserServices([]);
      }
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    refreshServices();
    
    // Listen for storage changes (e.g., logout from another tab)
    const handleStorageChange = (e: StorageEvent) => {
      if (e.key === 'token' || e.key === 'user_permissions') {
        refreshServices();
      }
    };
    
    if (typeof window !== 'undefined') {
      window.addEventListener('storage', handleStorageChange);
      return () => window.removeEventListener('storage', handleStorageChange);
    }
  }, []);

  // For server-side rendering, provide safe defaults
  if (typeof window === 'undefined') {
    return (
      <ServiceAccessContext.Provider value={{
        userServices: [],
        hasAccess: () => false,
        getAccessLevel: () => null,
        isLoading: false,
        refreshServices: async () => {},
        error: null
      }}>
        {children}
      </ServiceAccessContext.Provider>
    );
  }

  return (
    <ServiceAccessContext.Provider value={{
      userServices,
      hasAccess,
      getAccessLevel,
      isLoading,
      refreshServices,
      error
    }}>
      {children}
    </ServiceAccessContext.Provider>
  );
};

export const useServiceAccess = () => {
  const context = useContext(ServiceAccessContext);
  
  // For server-side rendering, return safe defaults
  if (typeof window === 'undefined') {
    return {
      userServices: [],
      hasAccess: () => false,
      getAccessLevel: () => null,
      isLoading: false,
      refreshServices: async () => {},
      error: null
    };
  }
  
  if (!context) {
    throw new Error('useServiceAccess must be used within ServiceAccessProvider');
  }
  
  return context;
};