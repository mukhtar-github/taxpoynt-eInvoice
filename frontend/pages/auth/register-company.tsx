import { useState, useRef } from 'react';
import { useRouter } from 'next/router';
import Link from 'next/link';
import Image from 'next/image';
import { useForm, SubmitHandler } from 'react-hook-form';
import { yupResolver } from '@hookform/resolvers/yup';
import * as yup from 'yup';
import { Alert } from '../../components/ui/Alert';
import { Button } from '../../components/ui/Button';
import { Input } from '../../components/ui/Input';
import { FormField } from '../../components/ui/FormField';
import { Label } from '../../components/ui/Label';
import { Container } from '../../components/ui/Container';
import { Typography } from '../../components/ui/Typography';
import { Spinner } from '../../components/ui/Spinner';
import MainLayout from '../../components/layouts/MainLayout';
import { useAuth } from '../../context/AuthContext';
import axios from 'axios';

// Company registration form schema
const schema = yup.object().shape({
  companyName: yup.string().required('Company name is required'),
  taxId: yup.string().required('Tax ID is required'),
  address: yup.string().required('Address is required'),
  phone: yup.string().required('Phone number is required'),
  email: yup.string().email('Invalid email format').required('Email is required'),
  website: yup.string().url('Invalid URL format').transform((value) => value === '' ? undefined : value).optional(),
  username: yup.string().required('Username is required'),
  password: yup.string().min(8, 'Password must be at least 8 characters').required('Password is required'),
  confirmPassword: yup.string()
    .oneOf([yup.ref('password')], 'Passwords must match')
    .required('Confirm password is required'),
});

// Explicitly define the form data type with website as optional
interface RegistrationFormData {
  companyName: string;
  taxId: string;
  address: string;
  phone: string;
  email: string;
  website?: string; // Make website optional with the ? modifier
  username: string;
  password: string;
  confirmPassword: string;
}

export default function RegisterCompany() {
  const router = useRouter();
  const { register: authRegister } = useAuth();
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [companyLogo, setCompanyLogo] = useState<File | null>(null);
  const [logoPreview, setLogoPreview] = useState<string | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const { register, handleSubmit, formState: { errors } } = useForm<RegistrationFormData>({
    resolver: yupResolver(schema) as any,
    defaultValues: {
      website: '',
    },
  });

  const handleLogoChange = (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0] || null;
    if (file) {
      // Validate file type
      if (!file.type.startsWith('image/')) {
        setError('Please upload an image file');
        return;
      }
      
      // Validate file size (max 2MB)
      if (file.size > 2 * 1024 * 1024) {
        setError('Logo file size should not exceed 2MB');
        return;
      }
      
      setCompanyLogo(file);
      
      // Create preview
      const reader = new FileReader();
      reader.onload = (e) => {
        setLogoPreview(e.target?.result as string);
      };
      reader.readAsDataURL(file);
    }
  };

  const handleLogoBrowse = () => {
    fileInputRef.current?.click();
  };

  const onSubmit = async (data: RegistrationFormData) => {
    try {
      setIsLoading(true);
      setError(null);
      
      // 1. Register the user first - Pass the whole 'data' object
      //    authRegister will be modified to return { id: string }
      const userCreationResponse = await authRegister(data);
      
      if (!userCreationResponse || !userCreationResponse.id) {
        throw new Error('Failed to create user account or retrieve user ID');
      }
      
      // 2. Create the organization
      const organizationData = {
        name: data.companyName,
        tax_id: data.taxId,
        address: data.address,
        phone_number: data.phone,
        email: data.email,
        website: data.website || '',
        user_id: userCreationResponse.id, // Use the ID from the modified authRegister
        // TODO: Add industry, country, etc. if needed by backend
      };
      
      const orgResponse = await axios.post('/api/v1/organizations', organizationData);
      
      // 3. Upload logo if provided
      if (companyLogo && orgResponse.data.id) {
        const formData = new FormData();
        formData.append('logo', companyLogo);
        
        await axios.post(`/api/v1/organizations/${orgResponse.data.id}/logo`, formData, {
          headers: {
            'Content-Type': 'multipart/form-data'
          }
        });
      }
      
      // Success - redirect to dashboard
      router.push('/dashboard');
      
    } catch (err) {
      console.error('Registration error:', err);
      setError(err instanceof Error ? err.message : 'An error occurred during registration');
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <MainLayout title="Register Your Company | TaxPoynt eInvoice" description="Register your company with TaxPoynt eInvoice platform">
      <Container className="py-12">
        <div className="max-w-4xl mx-auto">
          <div className="flex flex-col md:flex-row shadow-lg rounded-lg overflow-hidden">
            {/* Left side - Branding */}
            <div className="w-full md:w-2/5 bg-gradient-to-br from-indigo-600 to-indigo-800 p-8 text-white">
              <div className="h-full flex flex-col justify-between">
                <div>
                  <Typography.Heading level="h1" className="text-white mb-4">
                    TaxPoynt eInvoice
                  </Typography.Heading>
                  <Typography.Text className="text-indigo-100 mb-6">
                    Join the future of e-invoicing in Nigeria. Register your company to get started with our platform.
                  </Typography.Text>
                </div>
                
                <div className="space-y-4">
                  <div className="flex items-center">
                    <div className="rounded-full bg-indigo-700 p-2 mr-3">
                      <svg width="20" height="20" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                        <path d="M22 11.08V12a10 10 0 1 1-5.93-9.14" stroke="white" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
                        <path d="M22 4L12 14.01l-3-3" stroke="white" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
                      </svg>
                    </div>
                    <Typography.Text className="text-indigo-100">Connect to your ERP system</Typography.Text>
                  </div>
                  <div className="flex items-center">
                    <div className="rounded-full bg-indigo-700 p-2 mr-3">
                      <svg width="20" height="20" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                        <path d="M22 11.08V12a10 10 0 1 1-5.93-9.14" stroke="white" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
                        <path d="M22 4L12 14.01l-3-3" stroke="white" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
                      </svg>
                    </div>
                    <Typography.Text className="text-indigo-100">Automated invoice processing</Typography.Text>
                  </div>
                  <div className="flex items-center">
                    <div className="rounded-full bg-indigo-700 p-2 mr-3">
                      <svg width="20" height="20" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                        <path d="M22 11.08V12a10 10 0 1 1-5.93-9.14" stroke="white" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
                        <path d="M22 4L12 14.01l-3-3" stroke="white" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
                      </svg>
                    </div>
                    <Typography.Text className="text-indigo-100">FIRS compliant e-invoicing</Typography.Text>
                  </div>
                </div>
                
                <div className="mt-8">
                  <Typography.Text className="text-indigo-200 text-sm">
                    Already have an account?{' '}
                    <Link href="/auth/login" className="text-white underline">
                      Sign in
                    </Link>
                  </Typography.Text>
                </div>
              </div>
            </div>
            
            {/* Right side - Registration Form */}
            <div className="w-full md:w-3/5 bg-white p-8">
              <Typography.Heading level="h2" className="mb-6">
                Register Your Company
              </Typography.Heading>
              
              {error && (
                <Alert variant="error" className="mb-4">
                  {error}
                </Alert>
              )}
              
              <form onSubmit={handleSubmit(onSubmit)} className="space-y-6">
                {/* Company Logo Upload */}
                <div className="mb-6">
                  <Label htmlFor="logo" className="mb-2 block">Company Logo</Label>
                  <div className="flex items-center space-x-4">
                    <div 
                      className="w-24 h-24 border-2 border-dashed border-gray-300 rounded-lg flex items-center justify-center bg-gray-50"
                      onClick={handleLogoBrowse}
                    >
                      {logoPreview ? (
                        <img 
                          src={logoPreview} 
                          alt="Company logo preview" 
                          className="max-w-full max-h-full object-contain" 
                        />
                      ) : (
                        <svg width="36" height="36" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                          <path d="M12 5v14M5 12h14" stroke="#6B7280" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
                        </svg>
                      )}
                    </div>
                    <div>
                      <input 
                        type="file"
                        id="logo"
                        ref={fileInputRef}
                        onChange={handleLogoChange}
                        accept="image/*"
                        className="hidden"
                      />
                      <Button 
                        type="button" 
                        variant="outline" 
                        onClick={handleLogoBrowse}
                      >
                        Browse Logo
                      </Button>
                      <Typography.Text className="text-gray-500 text-sm mt-1">
                        Upload your company logo (max 2MB)
                      </Typography.Text>
                    </div>
                  </div>
                </div>
                
                {/* Company Information */}
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <FormField
                    label="Company Name"
                    error={!!errors.companyName?.message}
                    errorMessage={errors.companyName?.message}
                  >
                    <Input
                      id="companyName"
                      placeholder="MT Garba Global Ventures"
                      {...register('companyName')}
                    />
                  </FormField>
                  
                  <FormField
                    label="Tax ID"
                    error={!!errors.taxId?.message}
                    errorMessage={errors.taxId?.message}
                  >
                    <Input
                      id="taxId"
                      placeholder="12345678-0001"
                      {...register('taxId')}
                    />
                  </FormField>
                </div>
                
                <FormField
                  label="Address"
                  error={!!errors.address?.message}
                  errorMessage={errors.address?.message}
                >
                  <Input
                    id="address"
                    placeholder="Company address"
                    {...register('address')}
                  />
                </FormField>
                
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <FormField
                    label="Phone"
                    error={!!errors.phone?.message}
                    errorMessage={errors.phone?.message}
                  >
                    <Input
                      id="phone"
                      placeholder="+234 800 123 4567"
                      {...register('phone')}
                    />
                  </FormField>
                  
                  <FormField
                    label="Email"
                    error={!!errors.email?.message}
                    errorMessage={errors.email?.message}
                  >
                    <Input
                      id="email"
                      type="email"
                      placeholder="company@example.com"
                      {...register('email')}
                    />
                  </FormField>
                </div>
                
                <FormField
                  label="Website (Optional)"
                  error={!!errors.website?.message}
                  errorMessage={errors.website?.message}
                >
                  <Input
                    id="website"
                    placeholder="https://www.example.com"
                    {...register('website')}
                  />
                </FormField>
                
                <hr className="my-6" />
                
                {/* Admin Account Information */}
                <Typography.Heading level="h3" className="mb-4">
                  Admin Account Details
                </Typography.Heading>
                
                <FormField
                  label="Username"
                  error={!!errors.username?.message}
                  errorMessage={errors.username?.message}
                >
                  <Input
                    id="username"
                    placeholder="admin_username"
                    {...register('username')}
                  />
                </FormField>
                
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <FormField
                    label="Password"
                    error={!!errors.password?.message}
                    errorMessage={errors.password?.message}
                  >
                    <Input
                      id="password"
                      type="password"
                      placeholder="••••••••"
                      {...register('password')}
                    />
                  </FormField>
                  
                  <FormField
                    label="Confirm Password"
                    error={!!errors.confirmPassword?.message}
                    errorMessage={errors.confirmPassword?.message}
                  >
                    <Input
                      id="confirmPassword"
                      type="password"
                      placeholder="••••••••"
                      {...register('confirmPassword')}
                    />
                  </FormField>
                </div>
                
                <Button 
                  type="submit" 
                  className="w-full"
                  disabled={isLoading}
                >
                  {isLoading ? (
                    <>
                      <Spinner size="sm" className="mr-2" />
                      Registering...
                    </>
                  ) : (
                    'Register Company'
                  )}
                </Button>
              </form>
            </div>
          </div>
        </div>
      </Container>
    </MainLayout>
  );
}
