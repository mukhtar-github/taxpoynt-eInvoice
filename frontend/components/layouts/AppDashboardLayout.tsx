import React, { ReactNode, useState, useEffect } from 'react';
import { useRouter } from 'next/router';
import Link from 'next/link';
import { 
  Home, TrendingUp, List, Settings, Menu, Bell, User, X, BarChart2,
  FileText, Users, Link as LinkIcon, Compass, HardDrive
} from 'lucide-react';
import { Typography } from '../ui/Typography';
import { Button } from '../ui/Button';
import { cn } from '../../utils/cn';
import MainLayout from './MainLayout';
import { useAuth } from '../../context/AuthContext';
import { Spinner } from '../ui/Spinner';
import Image from 'next/image';

interface NavItemProps {
  icon: React.ElementType;
  children: ReactNode;
  href: string;
  isActive?: boolean;
  className?: string;
}

interface SidebarProps {
  onClose: () => void;
  className?: string;
  branding?: {
    companyName?: string;
    logoUrl?: string;
    primaryColor?: string;
  };
}

interface AppDashboardLayoutProps {
  children: ReactNode;
  title?: string;
  description?: string;
  branding?: {
    companyName?: string;
    logoUrl?: string;
    primaryColor?: string;
  };
}

// Navigation Items - consolidated from both dashboard layouts
const NavItems = [
  { name: 'Dashboard', icon: Home, href: '/dashboard' },
  { name: 'Integrations', icon: LinkIcon, href: '/dashboard/integrations' },
  { name: 'IRN Management', icon: FileText, href: '/dashboard/irn' },
  { name: 'Customers', icon: Users, href: '/dashboard/customers' },
  { name: 'Submission', icon: BarChart2, href: '/dashboard/submission' },
  { name: 'Reports', icon: FileText, href: '/dashboard/reports' },
  { name: 'Settings', icon: Settings, href: '/dashboard/settings' },
];

// Simpler toggle button that matches the screenshot
const SidebarToggle = ({ onClick }: { onClick: () => void }) => {
  return (
    <button 
      onClick={onClick}
      className="fixed right-4 top-4 bg-indigo-100 text-indigo-800 rounded-md p-2 shadow-sm hover:bg-indigo-200 transition-colors z-30 md:hidden"
      aria-label="Toggle sidebar"
    >
      <svg width="16" height="16" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
        <path d="M4 6H20M4 12H20M4 18H20" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
      </svg>
    </button>
  );
};

// Sidebar Navigation Item with active state detection
const NavItem = ({ icon: Icon, children, href, isActive: forcedActive, className }: NavItemProps) => {
  const router = useRouter();
  const isActive = forcedActive !== undefined ? forcedActive : 
                  router.pathname === href || router.pathname.startsWith(`${href}/`);
  
  return (
    <Link href={href} className={cn(
      "flex items-center py-3 px-6 cursor-pointer transition-all duration-200",
      isActive ? "bg-indigo-800 text-white" : "text-indigo-200 hover:text-white hover:bg-indigo-800/70",
      className
    )}>
      {Icon && (
        <Icon className="mr-3 h-5 w-5" />
      )}
      <span>{children}</span>
    </Link>
  );
};

// Enhanced Sidebar Component with branding support
const Sidebar = ({ onClose, branding, className }: SidebarProps) => {
  const logoColor = branding?.primaryColor || '#4F46E5';
  
  return (
    <div className={cn(
      "transition-all duration-300 ease-in-out bg-indigo-900 text-white",
      "w-full md:w-64 fixed h-full z-20 overflow-y-auto",
      className
    )}>
      <div className="h-20 flex items-center px-6 justify-between border-b border-indigo-800">
        <div className="flex items-center">
          {branding?.logoUrl ? (
            <div className="mr-3">
              <Image 
                src={branding.logoUrl} 
                alt={branding.companyName || 'Company logo'}
                width={32}
                height={32}
                className="rounded-full object-cover"
              />
            </div>
          ) : (
            <div className="bg-white rounded-full w-8 h-8 flex items-center justify-center mr-3">
              <svg width="20" height="20" viewBox="0 0 64 64" fill="none" xmlns="http://www.w3.org/2000/svg">
                <path d="M32 0C14.327 0 0 14.327 0 32C0 49.673 14.327 64 32 64C49.673 64 64 49.673 64 32C64 14.327 49.673 0 32 0ZM32 12C38.627 12 44 17.373 44 24C44 30.627 38.627 36 32 36C25.373 36 20 30.627 20 24C20 17.373 25.373 12 32 12ZM32 56C24.36 56 17.56 52.36 13.6 46.64C13.8 39.32 27.2 35.2 32 35.2C36.76 35.2 50.2 39.32 50.4 46.64C46.44 52.36 39.64 56 32 56Z" fill={logoColor}/>
              </svg>
            </div>
          )}
          <h2 className="font-bold text-lg truncate">{branding?.companyName || 'Taxpoynt'}</h2>
        </div>
        <button 
          onClick={onClose}
          className="md:hidden text-indigo-200 hover:text-white transition-colors"
          aria-label="Close sidebar"
        >
          <X className="h-6 w-6" />
        </button>
      </div>
      
      <nav className="mt-4">
        {NavItems.map(item => (
          <NavItem
            key={item.name}
            icon={item.icon}
            href={item.href}
          >
            {item.name}
          </NavItem>
        ))}
      </nav>
    </div>
  );
};

// Enhanced Header Component with title detection
const Header = () => {
  const router = useRouter();
  
  // Determine current page title based on route
  const getPageTitle = () => {
    if (router.pathname === '/dashboard') return 'Dashboard Overview';
    if (router.pathname.startsWith('/dashboard/integrations')) return 'Integrations';
    if (router.pathname.startsWith('/dashboard/irn')) return 'IRN Management';
    if (router.pathname.startsWith('/dashboard/customers')) return 'Customers';
    if (router.pathname.startsWith('/dashboard/reports')) return 'Reports';
    if (router.pathname.startsWith('/dashboard/settings')) return 'Settings';
    
    // Extract last part of URL for other pages
    const pathParts = router.pathname.split('/');
    const lastPart = pathParts[pathParts.length - 1];
    return lastPart.charAt(0).toUpperCase() + lastPart.slice(1);
  };
  
  return (
    <header className="bg-white border-b py-4 px-6 flex justify-between items-center h-20 sticky top-0">
      <div className="flex items-center">
        <h1 className="text-xl font-bold">
          {getPageTitle()}
        </h1>
      </div>
      
      <div className="flex items-center space-x-2">
        <Button 
          variant="ghost"
          size="icon"
          aria-label="notifications"
          className="rounded-full"
          onClick={() => {}}
        >
          <Bell className="h-5 w-5" />
        </Button>
        <Button 
          variant="ghost"
          size="icon"
          aria-label="profile"
          className="rounded-full"
          onClick={() => {}}
        >
          <User className="h-5 w-5" />
        </Button>
      </div>
    </header>
  );
};

// Main App Dashboard Layout
const AppDashboardLayout = ({ 
  children, 
  title = 'Dashboard | Taxpoynt eInvoice', 
  description,
  branding
}: AppDashboardLayoutProps) => {
  const [isOpen, setIsOpen] = useState(false);
  const { isAuthenticated, isLoading } = useAuth();
  const router = useRouter();
  
  // Handle authentication status
  useEffect(() => {
    if (!isLoading && !isAuthenticated) {
      router.push('/auth/login?returnUrl=' + encodeURIComponent(router.pathname));
    }
  }, [isAuthenticated, isLoading, router]);
  
  // Handle sidebar for mobile - auto-close on route change
  useEffect(() => {
    // Close sidebar on mobile when route changes
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
  
  // Handle sidebar toggle - store preference in localStorage
  const toggleSidebar = () => {
    const newState = !isOpen;
    setIsOpen(newState);
    // Store preference in localStorage for persistence
    if (typeof window !== 'undefined') {
      localStorage.setItem('sidebar_collapsed', newState ? 'false' : 'true');
    }
  };
  const closeSidebar = () => setIsOpen(false);
  
  // Initialize sidebar state from localStorage
  useEffect(() => {
    if (typeof window !== 'undefined') {
      const savedState = localStorage.getItem('sidebar_collapsed');
      if (savedState === 'true') {
        setIsOpen(false);
      } else {
        setIsOpen(true); // Default to open
      }
    }
  }, []);
  
  // If still checking auth, show loading
  if (isLoading) {
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
      <div className="flex min-h-screen bg-white">
        {/* Fixed Sidebar - always visible */}
        <Sidebar
          onClose={closeSidebar}
          className="hidden md:block"
          branding={branding}
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
              branding={branding}
            />
          </>
        )}
        
        <div className="flex-1 md:ml-64">
          {/* Mobile Toggle */}
          <div className="md:hidden">
            <button 
              onClick={toggleSidebar}
              className="fixed left-4 top-4 bg-indigo-100 text-indigo-800 rounded-md p-2 shadow-sm hover:bg-indigo-200 transition-colors z-10"
              aria-label="Toggle sidebar"
            >
              <Menu className="h-5 w-5" />
            </button>
          </div>
          
          <Header />
          
          <main className="p-6">
            {children}
          </main>
        </div>
      </div>
    </MainLayout>
  );
};

export default AppDashboardLayout;
