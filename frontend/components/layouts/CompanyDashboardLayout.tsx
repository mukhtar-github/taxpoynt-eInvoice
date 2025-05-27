import React, { ReactNode, useState, useEffect } from 'react';
import { useRouter } from 'next/router';
import Link from 'next/link';
import Image from 'next/image';
import { 
  FiHome, FiTrendingUp, FiList, FiSettings, FiMenu, FiBell, FiUser, FiX, FiBarChart2,
  FiGrid, FiDatabase, FiUsers, FiCreditCard, FiCheckSquare
} from 'react-icons/fi';
import { Typography } from '../ui/Typography';
import { Button } from '../ui/Button';
import { Spinner } from '../ui/Spinner';
import { cn } from '../../utils/cn';
import MainLayout from './MainLayout';
import { useAuth } from '../../context/AuthContext';
import axios from 'axios';
import { IconType } from 'react-icons';

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

// Main Company Dashboard Layout
interface CompanyDashboardLayoutProps {
  children: ReactNode;
  title?: string;
  description?: string;
}

const CompanyDashboardLayout = ({ 
  children, 
  title = 'Dashboard | Taxpoynt eInvoice',
  description 
}: CompanyDashboardLayoutProps) => {
  const [isOpen, setIsOpen] = useState(false);
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
    name: 'MT Garba Global Ventures',
    logo_url: null,
    branding_settings: null
  });
  const [isLoading, setIsLoading] = useState(true);
  const { isAuthenticated, isLoading: authLoading } = useAuth();
  const router = useRouter();
  
  // Handle authentication status
  useEffect(() => {
    if (!authLoading && !isAuthenticated) {
      router.push('/auth/login?returnUrl=' + encodeURIComponent(router.pathname));
    }
  }, [isAuthenticated, authLoading, router]);
  
  // Fetch company information
  useEffect(() => {
    const fetchCompanyInfo = async () => {
      try {
        // In a real implementation, this would fetch from the API
        // For now, we'll use a placeholder with MT Garba Global Ventures
        setCompanyInfo({
          name: 'MT Garba Global Ventures',
          logo_url: null, // This would be the actual logo URL
          branding_settings: {
            primary_color: '#4F46E5', // Default indigo color
            theme: 'light'
          }
        });
        setIsLoading(false);
      } catch (error) {
        console.error('Error fetching company info:', error);
        setIsLoading(false);
      }
    };
    
    if (isAuthenticated) {
      fetchCompanyInfo();
    }
  }, [isAuthenticated]);
  
  // Handle sidebar for mobile - auto-close on route change
  useEffect(() => {
    const handleRouteChange = () => {
      if (window.innerWidth < 768) {
        setIsOpen(false);
      }
    };
    
    router.events.on('routeChangeComplete', handleRouteChange);
    
    return () => {
      router.events.off('routeChangeComplete', handleRouteChange);
    };
  }, [router.events]);
  
  // Handle sidebar toggle
  const toggleSidebar = () => {
    setIsOpen(!isOpen);
  };
  
  const closeSidebar = () => setIsOpen(false);
  
  // If still checking auth or loading company info, show loading
  if (authLoading || isLoading) {
    return (
      <div className="flex min-h-screen items-center justify-center">
        <Spinner size="lg" />
        <span className="ml-2">Loading dashboard...</span>
      </div>
    );
  }
  
  // If not authenticated, don't render anything (will redirect)
  if (!isAuthenticated) {
    return null;
  }
  
  return (
    <MainLayout title={title} description={description}>
      <div className="flex min-h-screen bg-gray-50">
        {/* Fixed Sidebar - always visible on desktop */}
        <Sidebar
          onClose={closeSidebar}
          className="hidden md:block"
          companyName={companyInfo.name}
          companyLogo={companyInfo.logo_url || undefined}
          primaryColor={companyInfo.branding_settings?.primary_color}
        />
        
        {/* Mobile Sidebar - visible only when open */}
        {isOpen && (
          <>
            <div 
              className="fixed inset-0 bg-gray-900 bg-opacity-50 z-10 md:hidden"
              onClick={closeSidebar}
              aria-hidden="true"
            />
            <Sidebar
              onClose={closeSidebar}
              className="md:hidden block"
              companyName={companyInfo.name}
              companyLogo={companyInfo.logo_url || undefined}
              primaryColor={companyInfo.branding_settings?.primary_color}
            />
          </>
        )}
        
        {/* Mobile menu button */}
        <button
          className="md:hidden fixed top-4 right-4 z-30 bg-white p-2 rounded-md shadow-sm"
          onClick={toggleSidebar}
          aria-label="Open menu"
        >
          <FiMenu className="h-5 w-5 text-gray-700" />
        </button>
        
        {/* Main Content */}
        <div className="flex-1 ml-0 md:ml-64">
          <Header companyName={companyInfo.name} />
          <main className="p-6">
            {children}
          </main>
        </div>
      </div>
    </MainLayout>
  );
};

export default CompanyDashboardLayout;
