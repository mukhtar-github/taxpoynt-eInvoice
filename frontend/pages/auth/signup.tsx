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
import { useToast } from '../../components/ui/Toast';

// Using the proper API error type pattern as established
interface ApiError {
  detail?: string;
  message?: string;
  error?: string;
}

const SignupPage: React.FC = () => {
  const [name, setName] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [error, setError] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [selectedPlan, setSelectedPlan] = useState<string>('');
  const { login, isAuthenticated } = useAuth();
  const router = useRouter();
  const toast = useToast();
  
  // Get plan from URL params (coming from pricing page)
  useEffect(() => {
    const { plan } = router.query;
    if (plan && typeof plan === 'string') {
      setSelectedPlan(plan);
    }
  }, [router.query]);
  
  // If already authenticated, redirect to dashboard
  useEffect(() => {
    if (isAuthenticated) {
      router.push('/dashboard');
    }
  }, [isAuthenticated, router]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    
    // Form validation
    if (password !== confirmPassword) {
      setError('Passwords do not match');
      return;
    }
    
    if (password.length < 6) {
      setError('Password must be at least 6 characters long');
      return;
    }
    
    setIsLoading(true);
    
    try {
      // In a real app, we would call a signup API here
      // For the mock version, we'll just display a success message and log in
      
      // Simulate API call delay
      await new Promise(resolve => setTimeout(resolve, 1500));
      
      toast({
        title: "Registration Successful",
        description: "Your account has been created successfully.",
        status: "success",
        duration: 5000,
        isClosable: true
      });
      
      // Auto-login after signup
      await login(email, password);
      
      // Navigation will be handled by the useEffect hook
    } catch (err) {
      // Using the same error handling pattern as in login page
      let errorMessage = 'An unknown error occurred';
      
      // Following the TypeScript pattern established in previous work
      if (err && typeof err === 'object') {
        if ('message' in err) {
          errorMessage = (err as { message: string }).message;
        } else if ('detail' in err) {
          errorMessage = (err as ApiError).detail || errorMessage;
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
    <MainLayout title="Create Account | Taxpoynt eInvoice">
      <div className="flex items-center justify-center min-h-[calc(100vh-200px)] p-4">
        <Card className="w-full max-w-lg">
          <CardHeader>
            <CardTitle>Create your account</CardTitle>
            <CardDescription>
              Join Taxpoynt eInvoice to manage your invoices and tax compliance
            </CardDescription>
          </CardHeader>
          <CardContent>
            <form onSubmit={handleSubmit} className="space-y-4">
              {error && (
                <div className="p-3 bg-error-50 text-error-600 dark:bg-error-900 dark:text-error-300 rounded-md">
                  {error}
                </div>
              )}
              
              <FormField label="Full Name" htmlFor="name" required>
                <Input 
                  id="name"
                  value={name}
                  onChange={(e) => setName(e.target.value)}
                  placeholder="Enter your full name"
                  disabled={isLoading}
                />
              </FormField>
              
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
              
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <FormField label="Password" htmlFor="password" required>
                  <Input 
                    id="password"
                    type="password"
                    value={password}
                    onChange={(e) => setPassword(e.target.value)}
                    placeholder="6+ characters"
                    disabled={isLoading}
                  />
                </FormField>
                
                <FormField label="Confirm Password" htmlFor="confirmPassword" required>
                  <Input 
                    id="confirmPassword"
                    type="password"
                    value={confirmPassword}
                    onChange={(e) => setConfirmPassword(e.target.value)}
                    placeholder="Confirm password"
                    disabled={isLoading}
                  />
                </FormField>
              </div>
              
              <div className="mt-2">
                <Typography.Text size="sm" variant="secondary">
                  By creating an account, you agree to our{' '}
                  <Link href="#" className="text-primary hover:underline">Terms of Service</Link>
                  {' '}and{' '}
                  <Link href="#" className="text-primary hover:underline">Privacy Policy</Link>
                </Typography.Text>
              </div>
              
              <Button 
                variant="default" 
                type="submit" 
                className="w-full mt-4" 
                loading={isLoading}
              >
                Create Account
              </Button>
              
              <div className="text-center mt-4">
                <Typography.Text variant="secondary">
                  Already have an account?{' '}
                  <Link href="/auth/login" className="text-primary hover:underline">
                    Sign in
                  </Link>
                </Typography.Text>
              </div>
              
              <div className="mt-6 p-3 bg-blue-50 text-blue-700 dark:bg-blue-900 dark:text-blue-300 rounded-md">
                <Typography.Text size="sm">
                  <strong>Testing Mode:</strong> This form simulates the registration process 
                  without making actual API calls. You can use it to test the UI flow.
                </Typography.Text>
              </div>
            </form>
          </CardContent>
        </Card>
      </div>
    </MainLayout>
  );
};

export default SignupPage;
