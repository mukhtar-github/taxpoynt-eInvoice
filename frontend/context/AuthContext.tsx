import React, { createContext, useContext, useState, useEffect, ReactNode } from 'react';
import { useToast } from '../components/ui/Toast';

export interface User {
  id: string;
  name: string;
  email: string;
  role: string;
}

interface AuthContextType {
  user: User | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  login: (email: string, password: string) => Promise<void>;
  logout: () => void;
  register: (userData: {
    companyName: string;
    taxId: string;
    address: string;
    phone: string;
    email: string;
    website?: string;
    username: string;
    password: string;
  }) => Promise<{ id: string }>;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export const AuthProvider: React.FC<{children: ReactNode}> = ({ children }) => {
  const [user, setUser] = useState<User | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const toast = useToast();

  // For testing, we'll check localStorage on initial load
  useEffect(() => {
    const checkAuth = async () => {
      setIsLoading(true);
      try {
        // Check if we're in a browser environment
        if (typeof window !== 'undefined') {
          const storedUser = localStorage.getItem('taxpoynt_user');
          if (storedUser) {
            // Add a small delay to simulate network request for testing
            await new Promise(resolve => setTimeout(resolve, 500));
            setUser(JSON.parse(storedUser));
          }
        }
      } catch (error) {
        console.error('Error loading auth state:', error);
      } finally {
        setIsLoading(false);
      }
    };
    
    checkAuth();
  }, []);

  // Register function
  const register = async (userData: {
    companyName: string;
    taxId: string;
    address: string;
    phone: string;
    email: string;
    website?: string;
    username: string;
    password: string;
  }): Promise<{ id: string }> => {
    setIsLoading(true);
    try {
      // Here you would typically make an API call to your backend registration endpoint
      // For now, we'll simulate a successful registration and return a mock user ID
      await new Promise(resolve => setTimeout(resolve, 1000));
      
      const mockUserId = `user_${Date.now()}`;

      // After successful registration, you might want to automatically log the user in
      // or redirect them to the login page. For now, just show a toast.
      toast({
        title: 'Registration successful',
        description: 'Please log in with your credentials',
        status: 'success'
      });
      return { id: mockUserId }; // Return the mock user ID
    } catch (error) {
      console.error('Registration error:', error);
      toast({
        title: 'Registration failed',
        description: error instanceof Error ? error.message : 'An error occurred during registration',
        status: 'error'
      });
      throw error;
    } finally {
      setIsLoading(false);
    }
  };

  // Mock login function - in real app, this would call an API
  const login = async (email: string, password: string) => {
    setIsLoading(true);
    
    try {
      // Simulate API call delay
      await new Promise(resolve => setTimeout(resolve, 1000));
      
      // For testing, accept any credentials with basic validation
      if (email && password.length >= 6) {
        const mockUser = {
          id: '1',
          name: email.split('@')[0],
          email,
          role: 'admin'
        };
        
        setUser(mockUser);
        if (typeof window !== 'undefined') {
          localStorage.setItem('taxpoynt_user', JSON.stringify(mockUser));
        }
        
        toast({
          title: "Login Successful",
          description: `Welcome back, ${mockUser.name}!`,
          status: "success",
          duration: 3000,
          isClosable: true
        });
      } else {
        throw new Error('Invalid credentials');
      }
    } catch (error) {
      toast({
        title: "Login Failed",
        description: error instanceof Error ? error.message : 'An unknown error occurred',
        status: "error",
        duration: 5000,
        isClosable: true
      });
      throw error;
    } finally {
      setIsLoading(false);
    }
  };

  const logout = () => {
    setUser(null);
    if (typeof window !== 'undefined') {
      localStorage.removeItem('taxpoynt_user');
    }
    toast({
      title: "Logged Out",
      description: "You have been successfully logged out.",
      status: "info",
      duration: 3000,
      isClosable: true
    });
  };

  return (
    <AuthContext.Provider value={{
      user,
      isAuthenticated: !!user,
      isLoading,
      login,
      logout,
      register,
    }}>
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = () => {
  const context = useContext(AuthContext);
  
  // For server-side rendering, return a default context
  if (context === undefined) {
    // Check if we're on the server
    if (typeof window === 'undefined') {
      // Return a default non-functional auth context for SSR
      return {
        user: null,
        isAuthenticated: false,
        isLoading: false,
        login: async () => { 
          console.warn('Auth functions not available during SSR'); 
        },
        logout: () => { 
          console.warn('Auth functions not available during SSR'); 
        },
        register: async () => {
          console.warn('Auth functions not available during SSR');
          return { id: 'ssr-mock-id' }; // Ensure SSR mock also matches new signature
        }
      };
    }
    
    // In the browser, we should always have a provider
    throw new Error('useAuth must be used within an AuthProvider');
  }
  
  return context;
};
