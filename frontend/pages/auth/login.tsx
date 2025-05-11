import React, { useState, useEffect } from 'react';
import { useRouter } from 'next/router';
import Link from 'next/link';
import { useAuth } from '../../context/AuthContext';
import MainLayout from '../../components/layouts/MainLayout';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '../../components/ui/Card';
import { Button } from '../../components/ui/Button';
import { Input } from '../../components/ui/Input';
import { FormField } from '../../components/ui/FormField';
import { Typography } from '../../components/ui/Typography';

interface ApiError {
  detail: string;
  message?: string;
  error?: string;
}

const LoginPage: React.FC = () => {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const { login, isAuthenticated } = useAuth();
  const router = useRouter();
  
  // Get redirect destination from URL query params
  const redirectTo = typeof router.query.redirect === 'string' 
    ? router.query.redirect 
    : '/dashboard';

  // If already authenticated, redirect
  useEffect(() => {
    if (isAuthenticated) {
      router.push(redirectTo);
    }
  }, [isAuthenticated, redirectTo, router]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setIsLoading(true);
    
    try {
      await login(email, password);
      // The redirect will happen automatically due to the useEffect above
    } catch (err) {
      // Using the error handling approach from previous TypeScript work
      let errorMessage = 'An unknown error occurred';
      
      // Handle API errors with proper type assertions
      if (err && typeof err === 'object') {
        if ('message' in err) {
          errorMessage = (err as { message: string }).message;
        } else if ('detail' in err) {
          errorMessage = (err as ApiError).detail;
        } else if ('error' in err) {
          errorMessage = (err as ApiError).error || errorMessage;
        }
      }
      
      setError(errorMessage);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <MainLayout title="Login | Taxpoynt eInvoice">
      <div className="flex items-center justify-center min-h-[calc(100vh-200px)] p-4">
        <Card className="w-full max-w-md">
          <CardHeader>
            <CardTitle>Log in to your account</CardTitle>
            <CardDescription>
              Enter your credentials to access your dashboard
            </CardDescription>
          </CardHeader>
          <CardContent>
            <form onSubmit={handleSubmit} className="space-y-4">
              {error && (
                <div className="p-3 bg-error-50 text-error-600 dark:bg-error-900 dark:text-error-300 rounded-md">
                  {error}
                </div>
              )}
              
              <FormField label="Email" htmlFor="email" required>
                <Input 
                  id="email"
                  type="email"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  placeholder="your@email.com"
                  disabled={isLoading}
                />
              </FormField>
              
              <FormField label="Password" htmlFor="password" required>
                <Input 
                  id="password"
                  type="password"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  placeholder="Enter your password"
                  disabled={isLoading}
                />
              </FormField>
              
              <div className="text-right">
                <Link href="/auth/forgot-password" className="text-primary text-sm hover:underline">
                  Forgot password?
                </Link>
              </div>
              
              <Button 
                variant="default" 
                type="submit" 
                className="w-full" 
                loading={isLoading}
              >
                Log In
              </Button>
              
              <div className="text-center mt-4">
                <Typography.Text variant="secondary">
                  Don't have an account?{' '}
                  <Link href="/auth/signup" className="text-primary hover:underline">
                    Create account
                  </Link>
                </Typography.Text>
              </div>
              
              <div className="mt-6 p-3 bg-blue-50 text-blue-700 dark:bg-blue-900 dark:text-blue-300 rounded-md">
                <Typography.Text size="sm">
                  <strong>Testing Mode:</strong> During development, you can use any email 
                  with a password of at least 6 characters to log in.
                </Typography.Text>
              </div>
            </form>
          </CardContent>
        </Card>
      </div>
    </MainLayout>
  );
};

export default LoginPage;
