import { useState, useRef, useEffect } from 'react';
import { useForm, SubmitHandler } from 'react-hook-form';
import { yupResolver } from '@hookform/resolvers/yup';
import * as yup from 'yup';
import CompanyDashboardLayout from '../../components/layouts/CompanyDashboardLayout';
import { Typography } from '../../components/ui/Typography';
import { Card, CardHeader, CardContent } from '../../components/ui/Card';
import { Button } from '../../components/ui/Button';
import { Alert } from '../../components/ui/Alert';
import { Input } from '../../components/ui/Input';
import { FormField } from '../../components/ui/FormField';
import { Label } from '../../components/ui/Label';
import { Spinner } from '../../components/ui/Spinner';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '../../components/ui/Tabs';
import { Divider } from '../../components/ui/Divider';
import axios from 'axios';

// Form validation schema for organization profile
const profileSchema = yup.object().shape({
  name: yup.string().required('Company name is required'),
  tax_id: yup.string().required('Tax ID is required'),
  address: yup.string().required('Address is required'),
  phone: yup.string().required('Phone number is required'),
  email: yup.string().email('Invalid email format').required('Email is required'),
  website: yup.string().url('Invalid URL format').nullable().optional().transform((value) => value === '' ? undefined : value),
});

// Form validation schema for branding settings
const brandingSchema = yup.object().shape({
  primary_color: yup.string().required('Primary color is required'),
  secondary_color: yup.string().required('Secondary color is required'),
  accent_color: yup.string().required('Accent color is required'),
  display_name: yup.string().required('Display name is required'),
  theme: yup.string().required('Theme is required'),
});

// Interface for organization profile form
interface ProfileFormData {
  name: string;
  tax_id: string;
  address: string;
  phone: string;
  email: string;
  website?: string | null | undefined;
}

// Interface for branding settings form
interface BrandingFormData {
  primary_color: string;
  secondary_color: string;
  accent_color: string;
  display_name: string;
  theme: string;
}

// Interface for organization data
interface OrganizationData {
  id: string;
  name: string;
  tax_id: string;
  address: string;
  phone: string;
  email: string;
  website: string | null;
  logo_url: string | null;
  branding_settings: {
    primary_color: string;
    secondary_color: string;
    accent_color: string;
    display_name: string;
    theme: string;
  } | null;
}

const OrganizationPage = () => {
  // State management
  const [activeTab, setActiveTab] = useState('profile');
  const [isLoading, setIsLoading] = useState(true);
  const [isSaving, setIsSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);
  const [organization, setOrganization] = useState<OrganizationData | null>(null);
  const [companyLogo, setCompanyLogo] = useState<File | null>(null);
  const [logoPreview, setLogoPreview] = useState<string | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  // React Hook Form for profile
  const { 
    register: registerProfile, 
    handleSubmit: handleSubmitProfile, 
    formState: { errors: profileErrors },
    setValue: setProfileValue,
    reset: resetProfile
  } = useForm({
    resolver: yupResolver(profileSchema),
    defaultValues: {
      name: '',
      tax_id: '',
      address: '',
      phone: '',
      email: '',
      website: '',
    },
  });

  // React Hook Form for branding
  const { 
    register: registerBranding, 
    handleSubmit: handleSubmitBranding, 
    formState: { errors: brandingErrors },
    setValue: setBrandingValue,
    reset: resetBranding
  } = useForm({
    resolver: yupResolver(brandingSchema),
    defaultValues: {
      primary_color: '#4F46E5',
      secondary_color: '#818CF8',
      accent_color: '#3730A3',
      display_name: '',
      theme: 'light',
    }
  });

  // Fetch organization data
  useEffect(() => {
    const fetchOrganization = async () => {
      try {
        setIsLoading(true);
        setError(null);
        
        // In a real implementation, this would fetch from the API
        // For now, we'll use placeholder data for MT Garba Global Ventures
        const mockData: OrganizationData = {
          id: '123e4567-e89b-12d3-a456-426614174000',
          name: 'MT Garba Global Ventures',
          tax_id: '12345678-0001',
          address: '123 Business Avenue, Lagos, Nigeria',
          phone: '+234 800 123 4567',
          email: 'contact@mtgarba.com',
          website: 'https://www.mtgarba.com',
          logo_url: null,
          branding_settings: {
            primary_color: '#4F46E5',
            secondary_color: '#818CF8',
            accent_color: '#3730A3',
            display_name: 'MT Garba',
            theme: 'light',
          }
        };
        
        setOrganization(mockData);
        
        // Set form values for profile
        setProfileValue('name', mockData.name);
        setProfileValue('tax_id', mockData.tax_id);
        setProfileValue('address', mockData.address);
        setProfileValue('phone', mockData.phone);
        setProfileValue('email', mockData.email);
        setProfileValue('website', mockData.website || '');
        
        // Set form values for branding
        if (mockData.branding_settings) {
          setBrandingValue('primary_color', mockData.branding_settings.primary_color);
          setBrandingValue('secondary_color', mockData.branding_settings.secondary_color);
          setBrandingValue('accent_color', mockData.branding_settings.accent_color);
          setBrandingValue('display_name', mockData.branding_settings.display_name);
          setBrandingValue('theme', mockData.branding_settings.theme);
        }
        
        // Set logo preview if available
        if (mockData.logo_url) {
          setLogoPreview(mockData.logo_url);
        }
        
      } catch (err) {
        console.error('Error fetching organization:', err);
        setError('Failed to load organization data');
      } finally {
        setIsLoading(false);
      }
    };
    
    fetchOrganization();
  }, [setProfileValue, setBrandingValue]);

  // Handle logo file selection
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

  // Handle logo upload button click
  const handleLogoBrowse = () => {
    fileInputRef.current?.click();
  };

  // Handle logo upload submission
  const handleLogoUpload = async () => {
    if (!companyLogo || !organization) return;
    
    try {
      setIsSaving(true);
      setError(null);
      
      // In a real implementation, this would upload to the API
      // For now, we'll simulate a successful upload
      
      // Create form data for file upload
      const formData = new FormData();
      formData.append('logo', companyLogo);
      
      // Simulate API call
      await new Promise(resolve => setTimeout(resolve, 1500));
      
      // Update success message
      setSuccess('Company logo updated successfully');
      
      // Clear success message after 3 seconds
      setTimeout(() => {
        setSuccess(null);
      }, 3000);
      
    } catch (err) {
      console.error('Error uploading logo:', err);
      setError('Failed to upload logo');
    } finally {
      setIsSaving(false);
    }
  };

  // Handle profile form submission
  const onProfileSubmit: SubmitHandler<ProfileFormData> = async (data) => {
    if (!organization) return;
    
    try {
      setIsSaving(true);
      setError(null);
      
      // In a real implementation, this would update via the API
      // For now, we'll simulate a successful update
      await new Promise(resolve => setTimeout(resolve, 1500));
      
      // Update local state with new data
      setOrganization({
        ...organization,
        ...data,
      });
      
      // Update success message
      setSuccess('Company profile updated successfully');
      
      // Clear success message after 3 seconds
      setTimeout(() => {
        setSuccess(null);
      }, 3000);
      
    } catch (err) {
      console.error('Error updating profile:', err);
      setError('Failed to update company profile');
    } finally {
      setIsSaving(false);
    }
  };

  // Handle branding form submission
  const onBrandingSubmit: SubmitHandler<BrandingFormData> = async (data) => {
    if (!organization) return;
    
    try {
      setIsSaving(true);
      setError(null);
      
      // In a real implementation, this would update via the API
      // For now, we'll simulate a successful update
      await new Promise(resolve => setTimeout(resolve, 1500));
      
      // Update local state with new branding settings
      setOrganization({
        ...organization,
        branding_settings: data,
      });
      
      // Update success message
      setSuccess('Company branding updated successfully');
      
      // Clear success message after 3 seconds
      setTimeout(() => {
        setSuccess(null);
      }, 3000);
      
    } catch (err) {
      console.error('Error updating branding:', err);
      setError('Failed to update company branding');
    } finally {
      setIsSaving(false);
    }
  };

  return (
    <CompanyDashboardLayout title="Organization Settings | TaxPoynt eInvoice">
      <div className="max-w-6xl mx-auto">
        <div className="flex justify-between items-center mb-6">
          <div>
            <Typography.Heading level="h1" className="mb-2">
              Organization Settings
            </Typography.Heading>
            <Typography.Text className="text-gray-500">
              Manage your company profile, branding, and integrations
            </Typography.Text>
          </div>
        </div>
        
        {/* Error and success alerts */}
        {error && (
          <Alert variant="error" className="mb-6">
            {error}
          </Alert>
        )}
        
        {success && (
          <Alert variant="success" className="mb-6">
            {success}
          </Alert>
        )}
        
        {isLoading ? (
          <div className="flex justify-center items-center h-64">
            <Spinner size="lg" />
            <span className="ml-3">Loading organization data...</span>
          </div>
        ) : (
          <Tabs defaultValue="profile" onValueChange={setActiveTab} value={activeTab}>
            <TabsList className="mb-6">
              <TabsTrigger value="profile">Company Profile</TabsTrigger>
              <TabsTrigger value="branding">Branding</TabsTrigger>
              <TabsTrigger value="logo">Company Logo</TabsTrigger>
            </TabsList>
            
            {/* Profile Tab */}
            <TabsContent value="profile">
              <Card>
                <CardHeader>
                  <Typography.Heading level="h2">
                    Company Profile
                  </Typography.Heading>
                  <Typography.Text className="text-gray-500">
                    Update your company's basic information
                  </Typography.Text>
                </CardHeader>
                <CardContent>
                  <form onSubmit={handleSubmitProfile(onProfileSubmit)} className="space-y-6">
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                      <FormField
                        label="Company Name"
                        error={!!profileErrors.name}
                        errorMessage={profileErrors.name?.message}
                      >
                        <Input
                          id="name"
                          placeholder="MT Garba Global Ventures"
                          {...registerProfile('name')}
                        />
                      </FormField>
                      
                      <FormField
                        label="Tax ID"
                        error={!!profileErrors.tax_id}
                        errorMessage={profileErrors.tax_id?.message}
                      >
                        <Input
                          id="tax_id"
                          placeholder="12345678-0001"
                          {...registerProfile('tax_id')}
                        />
                      </FormField>
                    </div>
                    
                    <FormField
                      label="Address"
                      error={!!profileErrors.address?.message}
                    >
                      <Input
                        id="address"
                        placeholder="Company address"
                        {...registerProfile('address')}
                      />
                    </FormField>
                    
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                      <FormField
                        label="Phone"
                        error={!!profileErrors.phone?.message}
                      >
                        <Input
                          id="phone"
                          placeholder="+234 800 123 4567"
                          {...registerProfile('phone')}
                        />
                      </FormField>
                      
                      <FormField
                        label="Email"
                        error={!!profileErrors.email?.message}
                      >
                        <Input
                          id="email"
                          type="email"
                          placeholder="company@example.com"
                          {...registerProfile('email')}
                        />
                      </FormField>
                    </div>
                    
                    <FormField
                      label="Website (Optional)"
                      error={!!profileErrors.website?.message}
                    >
                      <Input
                        id="website"
                        placeholder="https://www.example.com"
                        {...registerProfile('website')}
                      />
                    </FormField>
                    
                    <div className="flex justify-end">
                      <Button
                        type="submit"
                        disabled={isSaving}
                      >
                        {isSaving ? (
                          <>
                            <Spinner size="sm" className="mr-2" />
                            Saving...
                          </>
                        ) : (
                          'Save Changes'
                        )}
                      </Button>
                    </div>
                  </form>
                </CardContent>
              </Card>
            </TabsContent>
            
            {/* Branding Tab */}
            <TabsContent value="branding">
              <Card>
                <CardHeader>
                  <Typography.Heading level="h2">
                    Brand Settings
                  </Typography.Heading>
                  <Typography.Text className="text-gray-500">
                    Customize how your company brand appears in the dashboard
                  </Typography.Text>
                </CardHeader>
                <CardContent>
                  <form onSubmit={handleSubmitBranding(onBrandingSubmit)} className="space-y-6">
                    <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                      <FormField
                        label="Primary Color"
                        error={!!brandingErrors.primary_color}
                        errorMessage={brandingErrors.primary_color?.message}
                      >
                        <div className="flex items-center">
                          <input
                            type="color"
                            id="primary_color"
                            className="w-10 h-10 p-1 rounded border border-gray-300 mr-2"
                            {...registerBranding('primary_color')}
                          />
                          <Input
                            placeholder="#4F46E5"
                            {...registerBranding('primary_color')}
                          />
                        </div>
                      </FormField>
                      
                      <FormField
                        label="Secondary Color"
                        error={!!brandingErrors.secondary_color}
                        errorMessage={brandingErrors.secondary_color?.message}
                      >
                        <div className="flex items-center">
                          <input
                            type="color"
                            id="secondary_color"
                            className="w-10 h-10 p-1 rounded border border-gray-300 mr-2"
                            {...registerBranding('secondary_color')}
                          />
                          <Input
                            placeholder="#818CF8"
                            {...registerBranding('secondary_color')}
                          />
                        </div>
                      </FormField>
                      
                      <FormField
                        label="Accent Color"
                        error={!!brandingErrors.accent_color}
                        errorMessage={brandingErrors.accent_color?.message}
                      >
                        <div className="flex items-center">
                          <input
                            type="color"
                            id="accent_color"
                            className="w-10 h-10 p-1 rounded border border-gray-300 mr-2"
                            {...registerBranding('accent_color')}
                          />
                          <Input
                            placeholder="#3730A3"
                            {...registerBranding('accent_color')}
                          />
                        </div>
                      </FormField>
                    </div>
                    
                    <Divider />
                    
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                      <FormField
                        label="Display Name (Optional)"
                        error={!!brandingErrors.display_name}
                        errorMessage={brandingErrors.display_name?.message}
                        helpText="A shorter name to display in the dashboard"
                      >
                        <Input
                          id="display_name"
                          placeholder="MT Garba"
                          {...registerBranding('display_name')}
                        />
                      </FormField>
                      
                      <FormField
                        label="Theme"
                        error={!!brandingErrors.theme}
                        errorMessage={brandingErrors.theme?.message}
                      >
                        <select
                          id="theme"
                          className="w-full px-3 py-2 border border-gray-300 rounded-md"
                          {...registerBranding('theme')}
                        >
                          <option value="light">Light</option>
                          <option value="dark">Dark</option>
                          <option value="system">System Default</option>
                        </select>
                      </FormField>
                    </div>
                    
                    <div className="flex justify-end">
                      <Button
                        type="submit"
                        disabled={isSaving}
                      >
                        {isSaving ? (
                          <>
                            <Spinner size="sm" className="mr-2" />
                            Saving...
                          </>
                        ) : (
                          'Save Branding'
                        )}
                      </Button>
                    </div>
                  </form>
                </CardContent>
              </Card>
            </TabsContent>
            
            {/* Logo Tab */}
            <TabsContent value="logo">
              <Card>
                <CardHeader>
                  <Typography.Heading level="h2">
                    Company Logo
                  </Typography.Heading>
                  <Typography.Text className="text-gray-500">
                    Upload or update your company logo
                  </Typography.Text>
                </CardHeader>
                <CardContent>
                  <div className="flex flex-col md:flex-row md:items-center gap-8">
                    <div className="flex-shrink-0">
                      <div className="w-48 h-48 border-2 border-dashed border-gray-300 rounded-lg flex items-center justify-center bg-gray-50 overflow-hidden">
                        {logoPreview ? (
                          <img 
                            src={logoPreview} 
                            alt="Company logo preview" 
                            className="max-w-full max-h-full object-contain" 
                          />
                        ) : (
                          <div className="text-center p-4">
                            <svg width="64" height="64" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg" className="mx-auto mb-2">
                              <path d="M12 5v14M5 12h14" stroke="#6B7280" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
                            </svg>
                            <Typography.Text className="text-gray-500">
                              No logo uploaded
                            </Typography.Text>
                          </div>
                        )}
                      </div>
                    </div>
                    
                    <div className="flex-grow space-y-6">
                      <div>
                        <Typography.Heading level="h3" className="mb-2">
                          Upload New Logo
                        </Typography.Heading>
                        <Typography.Text className="text-gray-500 mb-4">
                          Your logo will appear on your dashboard and in your invoices.
                        </Typography.Text>
                        
                        <input 
                          type="file"
                          id="logo"
                          ref={fileInputRef}
                          onChange={handleLogoChange}
                          accept="image/*"
                          className="hidden"
                        />
                        
                        <div className="flex items-center gap-4">
                          <Button 
                            type="button" 
                            variant="outline" 
                            onClick={handleLogoBrowse}
                          >
                            Browse Logo
                          </Button>
                          
                          <Button 
                            type="button"
                            disabled={!companyLogo || isSaving}
                            onClick={handleLogoUpload}
                          >
                            {isSaving ? (
                              <>
                                <Spinner size="sm" className="mr-2" />
                                Uploading...
                              </>
                            ) : (
                              'Upload Logo'
                            )}
                          </Button>
                        </div>
                      </div>
                      
                      <div className="border-t border-gray-200 pt-4">
                        <Typography.Text className="text-gray-500 text-sm">
                          <strong>Recommended:</strong> Square format (1:1 ratio), minimum 200x200 pixels, maximum file size 2MB.
                          <br/>
                          Supported formats: JPG, PNG, GIF
                        </Typography.Text>
                      </div>
                    </div>
                  </div>
                </CardContent>
              </Card>
            </TabsContent>
          </Tabs>
        )}
      </div>
    </CompanyDashboardLayout>
  );
};

export default OrganizationPage;
