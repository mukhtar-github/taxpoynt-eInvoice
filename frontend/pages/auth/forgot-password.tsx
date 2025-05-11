import React, { useState } from 'react';
import Link from 'next/link';
import MainLayout from '../../components/layouts/MainLayout';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '../../components/ui/Card';
import { Button } from '../../components/ui/Button';
import { Input } from '../../components/ui/Input';
import { FormField } from '../../components/ui/FormField';
import { Typography } from '../../components/ui/Typography';
import { useToast } from '../../components/ui/Toast';
import { AxiosError } from 'axios';

// Properly typing our API error responses following the established pattern
interface ApiErrorResponse {
  detail?: string;
  message?: string;
  error?: string;
}

const ForgotPasswordPage: React.FC = () => {
  const [email, setEmail] = useState('');
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const toast = useToast();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setSuccess(false);
    setIsLoading(true);
    
    try {
      // In a real app, call the password reset API
      // For mock version, simulate API call delay
      await new Promise(resolve => setTimeout(resolve, 1500));
      
      setSuccess(true);
      toast({
        title: "Reset Link Sent",
        description: "If an account exists with that email, you'll receive password reset instructions.",
        status: "success",
        duration: 5000,
        isClosable: true
      });
      
    } catch (err) {
      // Following the established TypeScript error handling pattern
      let errorMessage = 'An unknown error occurred';
      
      if (err instanceof AxiosError) {
        // Properly typed error handling for Axios responses
        const errorResponse = err.response?.data as ApiErrorResponse | undefined;
        errorMessage = errorResponse?.detail || 
                      errorResponse?.message || 
                      errorResponse?.error || 
                      err.message || 
                      errorMessage;
      } else if (err && typeof err === 'object') {
        // Fallback for non-Axios errors
        if ('message' in err) {
          errorMessage = (err as { message: string }).message;
        }
      }
      
      setError(errorMessage);
      setSuccess(false);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <MainLayout title="Forgot Password | Taxpoynt eInvoice">
      <div className="flex items-center justify-center min-h-[calc(100vh-200px)] p-4">
        <Card className="w-full max-w-md">
          <CardHeader>
            <CardTitle>Reset your password</CardTitle>
            <CardDescription>
              Enter your email address and we'll send you instructions to reset your password
            </CardDescription>
          </CardHeader>
          <CardContent>
            {success ? (
              <div className="text-center space-y-4">
                <div className="p-4 bg-success-50 text-success-700 dark:bg-success-900 dark:text-success-300 rounded-md mb-4">
                  <Typography.Text>
                    We've sent password reset instructions to <strong>{email}</strong>. 
                    Please check your email inbox.
                  </Typography.Text>
                </div>
                
                <Typography.Text>
                  Didn't receive the email? Check your spam folder or 
                  <Button 
                    variant="link" 
                    className="p-0 h-auto ml-1 text-primary"
                    onClick={handleSubmit}
                    disabled={isLoading}
                  >
                    try again
                  </Button>
                </Typography.Text>
                
                <div className="mt-4">
                  <Link href="/auth/login">
                    <Button variant="outline" className="w-full">
                      Back to Login
                    </Button>
                  </Link>
                </div>
              </div>
            ) : (
              <form onSubmit={handleSubmit} className="space-y-4">
                {error && (
                  <div className="p-3 bg-error-50 text-error-600 dark:bg-error-900 dark:text-error-300 rounded-md">
                    {error}
                  </div>
                )}
                
                <FormField label="Email Address" htmlFor="email" required>
                  <Input 
                    id="email"
                    type="email"
                    value={email}
                    onChange={(e) => setEmail(e.target.value)}
                    placeholder="your@email.com"
                    disabled={isLoading}
                  />
                </FormField>
                
                <Button 
                  variant="default" 
                  type="submit" 
                  className="w-full" 
                  loading={isLoading}
                >
                  Send Reset Link
                </Button>
                
                <div className="text-center mt-4">
                  <Typography.Text variant="secondary">
                    Remember your password?{' '}
                    <Link href="/auth/login" className="text-primary hover:underline">
                      Back to login
                    </Link>
                  </Typography.Text>
                </div>
                
                <div className="mt-6 p-3 bg-blue-50 text-blue-700 dark:bg-blue-900 dark:text-blue-300 rounded-md">
                  <Typography.Text size="sm">
                    <strong>Testing Mode:</strong> This form simulates the password reset process 
                    without sending actual emails.
                  </Typography.Text>
                </div>
              </form>
            )}
          </CardContent>
        </Card>
      </div>
    </MainLayout>
  );
};

export default ForgotPasswordPage;
