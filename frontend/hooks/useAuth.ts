import { useEffect, useState } from 'react';
import { apiClient } from '@/utils/apiClient';

interface User {
  organization_id: string;
  id: string;
  email: string;
  name?: string;
}

interface Organization {
  id: string;
  name: string;
}

interface AuthState {
  user: User | null;
  organization: Organization | null;
  isLoading: boolean;
  error: string | null;
}

export function useAuth() {
  const [authState, setAuthState] = useState<AuthState>({
    user: null,
    organization: null,
    isLoading: true,
    error: null
  });

  useEffect(() => {
    const fetchUserData = async () => {
      try {
        const response = await apiClient.get('/api/v1/auth/me');
        setAuthState({
          user: response.data.user,
          organization: response.data.organization,
          isLoading: false,
          error: null
        });
      } catch (err) {
        console.error('Failed to fetch user data:', err);
        setAuthState({
          user: null,
          organization: null,
          isLoading: false,
          error: 'Failed to authenticate user'
        });
      }
    };

    fetchUserData();
  }, []);

  return {
    user: authState.user,
    organization: authState.organization,
    isLoading: authState.isLoading,
    error: authState.error
  };
}
