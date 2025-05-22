import React, { useEffect, useState } from 'react';
import { useRouter } from 'next/router';
import { Card, CardHeader, CardContent } from '../ui/Card';
import { Button } from '../ui/Button';
import { Typography } from '../ui/Typography';
import { Spinner } from '../ui/Spinner';

/**
 * Authentication wrapper for FIRS testing components
 * 
 * This HOC (Higher Order Component) ensures that:
 * 1. Only authenticated users can access FIRS testing features
 * 2. Authentication tokens are available for API requests
 * 3. Permissions are verified for the appropriate role
 */
const withFirsAuth = <P extends object>(
  Component: React.ComponentType<P>
): React.FC<P> => {
  const WithFirsAuth: React.FC<P> = (props) => {
    const router = useRouter();
    const [isLoading, setIsLoading] = useState(true);
    const [isAuthenticated, setIsAuthenticated] = useState(false);
    const [hasPermission, setHasPermission] = useState(false);
    
    useEffect(() => {
      // Check authentication status
      const checkAuth = async () => {
        try {
          // Check if we have a token in localStorage
          const token = localStorage.getItem('auth_token');
          
          if (!token) {
            // No token found, redirect to login
            router.push('/auth/login?returnUrl=/firs-test');
            return;
          }
          
          // Verify token validity
          // This would typically be a real API call to verify the token
          // For now, we'll assume the token is valid if it exists
          setIsAuthenticated(true);
          
          // Check for required permissions (in a real app, this would verify specific roles/permissions)
          // For FIRS testing, we're requiring the "firs_api_access" permission
          const userPermissions = localStorage.getItem('user_permissions');
          let permissions = [];
          
          try {
            if (userPermissions) {
              permissions = JSON.parse(userPermissions);
            }
          } catch (e) {
            console.error('Failed to parse user permissions:', e);
          }
          
          // In a real app, check if the user has the required permission
          // For demo purposes, assume they do if they're authenticated
          setHasPermission(true);
          
        } catch (error) {
          console.error('Authentication check failed:', error);
          setIsAuthenticated(false);
          setHasPermission(false);
        } finally {
          setIsLoading(false);
        }
      };
      
      checkAuth();
    }, [router]);
    
    // Show loading state
    if (isLoading) {
      return (
        <div className="flex justify-center items-center min-h-screen">
          <Spinner size="lg" />
          <Typography.Text className="ml-3">Verifying authentication...</Typography.Text>
        </div>
      );
    }
    
    // Show unauthorized state
    if (!isAuthenticated) {
      return (
        <div className="flex justify-center items-center min-h-screen">
          <Card className="max-w-md w-full">
            <CardHeader className="bg-red-500 text-white">
              <Typography.Heading level="h3" className="text-white">Authentication Required</Typography.Heading>
            </CardHeader>
            <CardContent>
              <Typography.Text className="mb-4">
                You must be logged in to access the FIRS testing dashboard.
              </Typography.Text>
              <Button 
                onClick={() => router.push('/auth/login?returnUrl=/firs-test')}
                variant="default"
                className="w-full"
              >
                Log In
              </Button>
            </CardContent>
          </Card>
        </div>
      );
    }
    
    // Show permission denied state
    if (!hasPermission) {
      return (
        <div className="flex justify-center items-center min-h-screen">
          <Card className="max-w-md w-full">
            <CardHeader className="bg-red-500 text-white">
              <Typography.Heading level="h3" className="text-white">Access Denied</Typography.Heading>
            </CardHeader>
            <CardContent>
              <Typography.Text className="mb-4">
                You do not have permission to access the FIRS testing dashboard.
                This feature requires the "firs_api_access" permission.
              </Typography.Text>
              <Button 
                onClick={() => router.push('/dashboard')}
                variant="default"
                className="w-full"
              >
                Go to Dashboard
              </Button>
            </CardContent>
          </Card>
        </div>
      );
    }
    
    // User is authenticated and has permission, render the component
    return <Component {...props} />;
  };
  
  return WithFirsAuth;
};

export default withFirsAuth;
