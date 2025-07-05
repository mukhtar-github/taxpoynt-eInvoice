import React, { useState, useEffect } from 'react';
import { useRouter } from 'next/router';
import Link from 'next/link';
import { useAuth } from '../../../context/AuthContext';
import { useServicePermissions } from '../../hooks/useServicePermissions';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '../../../components/ui/Card';
import { Button } from '../../../components/ui/Button';
import { Input } from '../../../components/ui/Input';
import { FormField } from '../../../components/ui/FormField';
import { Typography } from '../../../components/ui/Typography';
import { Badge } from '../../../components/ui/Badge';
import { useToast } from '../../../components/ui/Toast';
import { 
  Eye, EyeOff, Shield, ArrowRight, CheckCircle,
  User, Lock, AlertCircle, Coffee
} from 'lucide-react';

interface LoginData {
  email: string;
  password: string;
  rememberMe: boolean;
}

interface EnhancedLoginFormProps {
  className?: string;
}

export const EnhancedLoginForm: React.FC<EnhancedLoginFormProps> = ({
  className
}) => {
  const [formData, setFormData] = useState<LoginData>({
    email: '',
    password: '',
    rememberMe: false
  });
  const [errors, setErrors] = useState<Record<string, string>>({});
  const [isLoading, setIsLoading] = useState(false);
  const [showPassword, setShowPassword] = useState(false);
  const [redirectTo, setRedirectTo] = useState('/dashboard');
  const [showDemoHint, setShowDemoHint] = useState(false);

  const { login, isAuthenticated } = useAuth();
  const permissions = useServicePermissions();
  const router = useRouter();
  const toast = useToast();

  // Handle redirect logic
  useEffect(() => {
    const { redirect, returnUrl, plan } = router.query;
    
    // Priority: redirect > returnUrl > plan-based route > default
    if (redirect && typeof redirect === 'string') {
      setRedirectTo(decodeURIComponent(redirect));
    } else if (returnUrl && typeof returnUrl === 'string') {
      setRedirectTo(decodeURIComponent(returnUrl));
    } else if (plan) {
      // If coming from pricing, redirect to appropriate onboarding
      setRedirectTo('/onboarding/welcome');
    }
  }, [router.query]);

  // If already authenticated, redirect
  useEffect(() => {
    if (isAuthenticated) {
      // Use permissions to determine best landing page
      const defaultRoute = permissions.getDefaultRoute();
      router.push(redirectTo === '/dashboard' ? defaultRoute : redirectTo);
    }
  }, [isAuthenticated, redirectTo, router, permissions]);

  const validateForm = (): boolean => {
    const newErrors: Record<string, string> = {};

    if (!formData.email.trim()) {
      newErrors.email = 'Email is required';
    } else if (!formData.email.includes('@')) {
      newErrors.email = 'Please enter a valid email';
    }

    if (!formData.password) {
      newErrors.password = 'Password is required';
    }

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!validateForm()) return;

    setIsLoading(true);
    try {
      await login(formData.email, formData.password);
      
      // Store remember me preference
      if (formData.rememberMe) {
        localStorage.setItem('remember_login', 'true');
      } else {
        localStorage.removeItem('remember_login');
      }

      toast({
        title: "Welcome back!",
        description: "You've been successfully logged in.",
        status: "success",
        duration: 3000,
        isClosable: true
      });

      // Redirect will happen automatically via useEffect
    } catch (err) {
      let errorMessage = 'Login failed. Please check your credentials.';
      
      if (err && typeof err === 'object') {
        if ('message' in err) {
          errorMessage = (err as { message: string }).message;
        } else if ('detail' in err) {
          errorMessage = (err as { detail: string }).detail;
        }
      }
      
      setErrors({ submit: errorMessage });
      
      toast({
        title: "Login Failed",
        description: errorMessage,
        status: "error",
        duration: 5000,
        isClosable: true
      });
    } finally {
      setIsLoading(false);
    }
  };

  const fillDemoCredentials = () => {
    setFormData({
      email: 'demo@taxpoynt.com',
      password: 'demo123',
      rememberMe: false
    });
    setShowDemoHint(false);
  };

  return (
    <div className={`max-w-md mx-auto ${className}`}>
      <Card>
        <CardHeader className="text-center">
          <CardTitle className="text-2xl">Welcome back</CardTitle>
          <CardDescription>
            Sign in to your TaxPoynt eInvoice account
          </CardDescription>
        </CardHeader>

        <CardContent>
          <form onSubmit={handleSubmit} className="space-y-6">
            {/* Error Display */}
            {errors.submit && (
              <div className="p-4 bg-red-50 border border-red-200 text-red-600 rounded-md flex items-start space-x-2">
                <AlertCircle className="h-5 w-5 mt-0.5 flex-shrink-0" />
                <div>
                  <div className="font-medium">Login Error</div>
                  <div className="text-sm">{errors.submit}</div>
                </div>
              </div>
            )}

            {/* Demo Hint */}
            {showDemoHint && (
              <div className="p-4 bg-blue-50 border border-blue-200 rounded-md">
                <div className="flex items-start space-x-2">
                  <Coffee className="h-5 w-5 text-blue-600 mt-0.5" />
                  <div className="flex-1">
                    <div className="font-medium text-blue-900 text-sm">Try the Demo</div>
                    <div className="text-blue-700 text-sm mt-1">
                      Use demo credentials to explore the platform
                    </div>
                    <Button
                      type="button"
                      variant="outline"
                      size="sm"
                      onClick={fillDemoCredentials}
                      className="mt-2 border-blue-300 text-blue-700 hover:bg-blue-100"
                    >
                      Fill Demo Credentials
                    </Button>
                  </div>
                </div>
              </div>
            )}

            {/* Email Field */}
            <FormField 
              label="Email Address" 
              htmlFor="email" 
              required 
              error={errors.email}
            >
              <div className="relative">
                <User className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-gray-400" />
                <Input
                  id="email"
                  type="email"
                  value={formData.email}
                  onChange={(e) => setFormData(prev => ({ ...prev, email: e.target.value }))}
                  placeholder="your@email.com"
                  disabled={isLoading}
                  className="pl-10"
                />
              </div>
            </FormField>

            {/* Password Field */}
            <FormField 
              label="Password" 
              htmlFor="password" 
              required 
              error={errors.password}
            >
              <div className="relative">
                <Lock className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-gray-400" />
                <Input
                  id="password"
                  type={showPassword ? 'text' : 'password'}
                  value={formData.password}
                  onChange={(e) => setFormData(prev => ({ ...prev, password: e.target.value }))}
                  placeholder="Enter your password"
                  disabled={isLoading}
                  className="pl-10 pr-10"
                />
                <button
                  type="button"
                  onClick={() => setShowPassword(!showPassword)}
                  className="absolute right-3 top-1/2 transform -translate-y-1/2 text-gray-400 hover:text-gray-600"
                  disabled={isLoading}
                >
                  {showPassword ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
                </button>
              </div>
            </FormField>

            {/* Remember Me & Forgot Password */}
            <div className="flex items-center justify-between">
              <label className="flex items-center space-x-2">
                <input
                  type="checkbox"
                  checked={formData.rememberMe}
                  onChange={(e) => setFormData(prev => ({ ...prev, rememberMe: e.target.checked }))}
                  className="rounded border-gray-300"
                  disabled={isLoading}
                />
                <span className="text-sm text-gray-600">Remember me</span>
              </label>

              <Link 
                href="/auth/forgot-password" 
                className="text-sm text-blue-600 hover:underline"
              >
                Forgot password?
              </Link>
            </div>

            {/* Submit Button */}
            <Button 
              type="submit" 
              className="w-full" 
              loading={isLoading}
              size="lg"
            >
              {isLoading ? 'Signing in...' : 'Sign In'}
              <ArrowRight className="ml-2 h-4 w-4" />
            </Button>

            {/* Demo Button */}
            <Button
              type="button"
              variant="outline"
              onClick={() => setShowDemoHint(true)}
              className="w-full"
              disabled={isLoading}
            >
              <Coffee className="mr-2 h-4 w-4" />
              Try Demo
            </Button>

            {/* Sign Up Link */}
            <div className="text-center text-sm text-gray-600">
              Don't have an account?{' '}
              <Link 
                href={`/auth/enhanced-signup${router.query.plan ? `?plan=${router.query.plan}` : ''}`}
                className="text-blue-600 hover:underline font-medium"
              >
                Create account
              </Link>
            </div>

            {/* Security Notice */}
            <div className="p-3 bg-gray-50 rounded-lg">
              <div className="flex items-start space-x-2">
                <Shield className="h-4 w-4 text-green-600 mt-0.5 flex-shrink-0" />
                <div className="text-sm text-gray-600">
                  <div className="font-medium text-gray-900">Secure Login</div>
                  <div>Protected by bank-grade encryption and NDPR compliance</div>
                </div>
              </div>
            </div>

            {/* Testing Mode Notice */}
            <div className="p-3 bg-blue-50 border border-blue-200 rounded-md">
              <div className="flex items-start space-x-2">
                <CheckCircle className="h-4 w-4 text-blue-600 mt-0.5 flex-shrink-0" />
                <div className="text-sm text-blue-700">
                  <div className="font-medium">Development Mode</div>
                  <div>
                    Use any email with 6+ character password, or try the demo credentials
                  </div>
                </div>
              </div>
            </div>
          </form>
        </CardContent>
      </Card>

      {/* Redirect Info */}
      {redirectTo !== '/dashboard' && (
        <div className="mt-4 text-center">
          <div className="inline-flex items-center px-3 py-1 bg-blue-100 text-blue-800 text-sm rounded-full">
            <ArrowRight className="mr-1 h-3 w-3" />
            You'll be redirected after login
          </div>
        </div>
      )}
    </div>
  );
};

export default EnhancedLoginForm;