import React, { ReactNode, useState, useEffect } from 'react';
import { useRouter } from 'next/router';
import Link from 'next/link';
import Image from 'next/image';
import { 
  Home, TrendingUp, FileText, Settings, Menu, Bell, User, X, BarChart2,
  Grid, Database, Users, CreditCard, CheckSquare, LucideIcon
} from 'lucide-react';
import { Typography } from '../ui/Typography';
import { Button } from '../ui/Button';
import { Spinner } from '../ui/Spinner';
import { cn } from '../../utils/cn';
import AppDashboardLayout from './AppDashboardLayout';
import { useAuth } from '../../context/AuthContext';
import axios from 'axios';
import { FiBarChart2, FiBell, FiCheckSquare, FiCreditCard, FiDatabase, FiGrid, FiHome, FiList, FiSettings, FiUser, FiUsers } from 'react-icons/fi';

interface NavItemProps {
  icon: React.ElementType;
  children: ReactNode;
  href: string;
  className?: string;
}

interface SidebarProps {
  onClose: () => void;
  className?: string;
  companyName?: string;
  companyLogo?: string;
  primaryColor?: string;
}

// Navigation Items
const NavItems = [
  { name: 'Dashboard', icon: FiHome, href: '/dashboard' },
  { name: 'ERP Connection', icon: FiDatabase, href: '/dashboard/erp-connection' },
  { name: 'Invoices', icon: FiList, href: '/dashboard/invoices' },
  { name: 'Customers', icon: FiUsers, href: '/dashboard/customers' },
  { name: 'Products', icon: FiGrid, href: '/dashboard/products' },
  { name: 'Reporting', icon: FiBarChart2, href: '/dashboard/reporting' },
  { name: 'Organization', icon: FiCreditCard, href: '/dashboard/organization' },
  { name: 'Settings', icon: FiSettings, href: '/dashboard/settings' },
];

// Sidebar Navigation Item
const NavItem = ({ icon: Icon, children, href, className }: NavItemProps) => {
  const router = useRouter();
  const isActive = router.pathname === href || router.pathname.startsWith(`${href}/`);
  
  return (
    <Link href={href} className={cn(
      "flex items-center py-3 px-6 cursor-pointer transition-all duration-200",
      isActive ? "bg-indigo-800 text-white" : "text-indigo-200 hover:text-white",
      className
    )}>
      {Icon && (
        <Icon className="mr-3 h-5 w-5" />
      )}
      <span>{children}</span>
    </Link>
  );
};

// Sidebar Component with company branding
const Sidebar = ({ onClose, className, companyName, companyLogo, primaryColor }: SidebarProps) => {
  // Use custom primary color if provided, otherwise default to indigo
  const bgColor = primaryColor ? primaryColor : 'bg-indigo-900';
  const bgColorDarker = primaryColor ? primaryColor.replace('900', '950') : 'bg-indigo-950';
  
  return (
    <div className={cn(
      "transition-all duration-300 ease-in-out bg-indigo-900 text-white",
      "w-full md:w-64 fixed h-full z-20 overflow-y-auto",
      className
    )}>
      <div className="h-24 flex items-center px-6 justify-between border-b border-indigo-800">
        <div className="flex items-center">
          {companyLogo ? (
            <div className="w-10 h-10 bg-white rounded-full flex items-center justify-center overflow-hidden mr-3">
              <img
                src={companyLogo}
                alt={`${companyName || 'Company'} logo`}
                className="max-w-full max-h-full object-contain"
              />
            </div>
          ) : (
            <div className="bg-white rounded-full w-10 h-10 flex items-center justify-center mr-3">
              <svg width="24" height="24" viewBox="0 0 64 64" fill="none" xmlns="http://www.w3.org/2000/svg">
                <path d="M32 0C14.327 0 0 14.327 0 32C0 49.673 14.327 64 32 64C49.673 64 64 49.673 64 32C64 14.327 49.673 0 32 0ZM32 12C38.627 12 44 17.373 44 24C44 30.627 38.627 36 32 36C25.373 36 20 30.627 20 24C20 17.373 25.373 12 32 12ZM32 56C24.36 56 17.56 52.36 13.6 46.64C13.8 39.32 27.2 35.2 32 35.2C36.76 35.2 50.2 39.32 50.4 46.64C46.44 52.36 39.64 56 32 56Z" fill="#4F46E5"/>
              </svg>
            </div>
          )}
          <div>
            <Typography.Heading level="h1" className="text-white text-base">
              {companyName || 'TaxPoynt'}
            </Typography.Heading>
            <Typography.Text className="text-indigo-200 text-xs">
              eInvoice Dashboard
            </Typography.Text>
          </div>
        </div>
      </div>
      
      <nav className="mt-4">
        {NavItems.map((nav) => (
          <NavItem key={nav.name} icon={nav.icon} href={nav.href}>
            {nav.name}
          </NavItem>
        ))}
      </nav>
      
      <div className="p-4 mt-6">
        <div className="bg-indigo-800 rounded-lg p-4">
          <div className="flex items-center mb-3">
            <FiCheckSquare className="text-indigo-300 mr-2" />
            <Typography.Heading level="h3" className="text-white text-sm">ERP Status</Typography.Heading>
          </div>
          <div className="flex items-center">
            <div className="h-2 w-2 rounded-full bg-green-400 mr-2"></div>
            <Typography.Text className="text-indigo-100 text-xs">
              Odoo Connection Active
            </Typography.Text>
          </div>
          <Button
            variant="ghost"
            size="sm"
            className="w-full mt-3 text-indigo-100 border border-indigo-700 hover:bg-indigo-700"
          >
            Manage Connection
          </Button>
        </div>
      </div>
    </div>
  );
};

// Header Component with company branding
const Header = ({ companyName }: { companyName?: string }) => {
  return (
    <header className="
      ml-0 md:ml-64 px-6 h-16 flex items-center
      bg-white shadow-sm
      border-b border-gray-200
      justify-between sticky top-0 z-10
    ">
      <div className="flex md:hidden">
        <Typography.Heading level="h1" className="text-gray-800">
          {companyName || 'TaxPoynt'}
        </Typography.Heading>
      </div>
      
      <div className="hidden md:block">
        <Typography.Text className="text-gray-500">
          Welcome back, Admin
        </Typography.Text>
      </div>
      
      <div className="flex items-center space-x-0 md:space-x-6">
        <Button 
          variant="ghost"
          size="icon"
          aria-label="notifications"
          className="rounded-full"
          onClick={() => {}}
        >
          <FiBell className="h-5 w-5" />
        </Button>
        <Button 
          variant="ghost"
          size="icon"
          aria-label="profile"
          className="rounded-full"
          onClick={() => {}}
        >
          <FiUser className="h-5 w-5" />
        </Button>
      </div>
    </header>
  );
};

// Main Company Dashboard Layout - extends AppDashboardLayout
interface CompanyDashboardLayoutProps {
  children: ReactNode;
  title?: string;
  description?: string;
}

/**
 * CompanyDashboardLayout Component
 * 
 * This layout extends the AppDashboardLayout to provide company-specific features,
 * such as fetching and displaying company branding and information.
 * It handles retrieving company data from the API and passes it to AppDashboardLayout.
 */
const CompanyDashboardLayout = ({ 
  children, 
  title = 'Company Dashboard | Taxpoynt eInvoice',
  description 
}: CompanyDashboardLayoutProps) => {
  interface BrandingSettings {
    primary_color: string;
    theme: string;
  }

  interface CompanyInfo {
    name: string;
    logo_url: string | null;
    branding_settings: BrandingSettings | null;
  }

  const [companyInfo, setCompanyInfo] = useState<CompanyInfo>({
    name: 'Company Dashboard',
    logo_url: null,
    branding_settings: null
  });
  const [isLoading, setIsLoading] = useState(true);
  const { isAuthenticated, user, isLoading: authLoading } = useAuth();
  const router = useRouter();

  // Fetch company information when component mounts
  useEffect(() => {
    const fetchCompanyInfo = async () => {
      if (!isAuthenticated || authLoading) return;
      
      try {
        setIsLoading(true);
        // Safely access organizationId from router query or use type assertion for user object
        const organizationId = router.query.organizationId as string || (user as any)?.default_organization_id;
        if (!organizationId) return;

        const response = await axios.get(`/api/v1/organizations/${organizationId}`);
        const data = response.data;
        
        setCompanyInfo({
          name: data.name,
          logo_url: data.logo_url,
          branding_settings: data.branding_settings
        });
      } catch (error) {
        console.error('Error fetching company information:', error);
      } finally {
        setIsLoading(false);
      }
    };

    fetchCompanyInfo();
  }, [isAuthenticated, authLoading, user, router.query]);

  // If still checking company info, show loading
  if (isLoading) {
    return (
      <AppDashboardLayout title={title} description={description}>
        <div className="flex items-center justify-center h-[calc(100vh-120px)]">
          <Spinner size="lg" />
          <span className="ml-2">Loading company information...</span>
        </div>
      </AppDashboardLayout>
    );
  }

  // Once company information is loaded, render with the branding
  return (
    <AppDashboardLayout 
      title={`${companyInfo.name} - Dashboard`}
      description={description} 
      branding={{
        companyName: companyInfo.name,
        logoUrl: companyInfo.logo_url || undefined,
        primaryColor: companyInfo.branding_settings?.primary_color || '#4F46E5'
      }}
    >
      {children}
    </AppDashboardLayout>
  );
};

export default CompanyDashboardLayout;
