import React, { ReactNode, useState, useEffect } from 'react';
import { useRouter } from 'next/router';
import Link from 'next/link';
import { 
  Home, TrendingUp, List, Settings, Menu, Bell, User, X, BarChart2,
  FileText, Users, Link as LinkIcon, Compass, HardDrive, Shield, Send,
  Key, ShieldCheck, UserPlus
} from 'lucide-react';
import { Typography } from '../ui/Typography';
import { Button } from '../ui/Button';
import { Badge } from '../ui/Badge';
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
  isPlatform?: boolean;
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

// Navigation Items - separated by Platform and SI functionality
const NavItems = [
  // System Integration (SI) Items
  { name: 'Dashboard', icon: Home, href: '/dashboard', isPlatform: false },
  { name: 'Company Dashboard', icon: Users, href: '/dashboard/company-home', isPlatform: false },
  { name: 'ERP Integrations', icon: LinkIcon, href: '/dashboard/integrations', isPlatform: false },
  { name: 'CRM Integrations', icon: UserPlus, href: '/dashboard/crm', isPlatform: false },
  { name: 'Submission', icon: BarChart2, href: '/dashboard/submission', isPlatform: false },
  { name: 'Organization', icon: Users, href: '/dashboard/organization', isPlatform: false },
  { name: 'Metrics', icon: BarChart2, href: '/dashboard/metrics', isPlatform: false },
  { name: 'ERP Connection', icon: LinkIcon, href: '/dashboard/erp-connection', isPlatform: false },
  
  // Platform Items (formerly APP) - with visual indicators
  { name: 'Secure Transmission', icon: Shield, href: '/dashboard/transmission', isPlatform: true },
  { name: 'Certificate Management', icon: Key, href: '/dashboard/certificates', isPlatform: true },
  { name: 'Crypto Stamping', icon: ShieldCheck, href: '/dashboard/crypto-stamping', isPlatform: true },
  { name: 'Signature Management', icon: ShieldCheck, href: '/platform/signature-management', isPlatform: true },
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

// Sidebar Navigation Item with active state detection and platform indicators
const NavItem = ({ icon: Icon, children, href, isActive: forcedActive, isPlatform, className }: NavItemProps) => {
  const router = useRouter();
  const isActive = forcedActive !== undefined ? forcedActive : 
                  router.pathname === href || router.pathname.startsWith(`${href}/`);
  
  return (
    <Link href={href} className={cn(
      "flex items-center py-3 px-6 cursor-pointer transition-all duration-200",
      isActive ? "bg-indigo-800 text-white" : "text-indigo-200 hover:text-white hover:bg-indigo-800/70",
      isPlatform && "border-l-4 border-cyan-500",
      className
    )}>
      <div className="flex items-center flex-1">
        {Icon && (
          <Icon className={cn("mr-3 h-5 w-5", isPlatform && "text-cyan-400")} />
        )}
        <span>{children}</span>
      </div>
      {isPlatform && (
        <Badge className="ml-2 bg-cyan-200 text-cyan-800 text-xs">
          Platform
        </Badge>
      )}
    </Link>
  );
};

// Enhanced Sidebar Component with branding support
const Sidebar = ({ onClose, branding, className }: SidebarProps) => {
  const { logout } = useAuth();
  const logoColor = branding?.primaryColor || '#4F46E5';
  
  return (
    <div className={cn(
      "transition-all duration-300 ease-in-out bg-indigo-900 text-white",
      "w-full md:w-64 fixed h-full z-20 overflow-y-auto",
      className
    )}>
      <div className="h-20 flex items-center px-6 justify-between border-b border-indigo-800">
        <div className="flex items-center">
          {/* TaxPoynt Logo (official) */}
          <div className="w-8 h-8 flex items-center justify-center mr-3 rounded-full overflow-hidden bg-white">
            <Image 
              src="/logo.svg" 
              alt="TaxPoynt Logo" 
              width={32} 
              height={32}
              className="object-contain"
            />
          </div>
          <h2 className="font-bold text-lg truncate">TaxPoynt eInvoice</h2>
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
        {/* Divider and heading for SI section */}
        <div className="px-6 py-2 text-xs font-semibold text-indigo-300 uppercase tracking-wider">
          System Integration
        </div>
        
        {/* SI Nav Items */}
        {NavItems.filter(item => !item.isPlatform).map(item => (
          <NavItem
            key={item.name}
            icon={item.icon}
            href={item.href}
            isPlatform={item.isPlatform}
          >
            {item.name}
          </NavItem>
        ))}
        
        {/* Divider and heading for Platform section */}
        <div className="mt-6 mb-2 px-6 py-2 text-xs font-semibold text-cyan-300 uppercase tracking-wider border-t border-indigo-800">
          Platform
        </div>
        
        {/* Platform Nav Items */}
        {NavItems.filter(item => item.isPlatform).map(item => (
          <NavItem
            key={item.name}
            icon={item.icon}
            href={item.href}
            isPlatform={item.isPlatform}
          >
            {item.name}
          </NavItem>
        ))}
        
        <div className="px-4 mt-8">
          <Button
            variant="ghost"
            onClick={logout}
            className="w-full flex items-center space-x-3 text-indigo-100 hover:text-white hover:bg-indigo-800 px-4 py-3 rounded-md transition-colors"
          >
            <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5" viewBox="0 0 20 20" fill="currentColor">
              <path fillRule="evenodd" d="M3 3a1 1 0 00-1 1v12a1 1 0 001 1h10a1 1 0 001-1v-3a1 1 0 10-2 0v3H3V4h9v3a1 1 0 102 0V4a1 1 0 00-1-1H3z" clipRule="evenodd" />
              <path fillRule="evenodd" d="M13.293 7.293a1 1 0 011.414 0l3 3a1 1 0 010 1.414l-3 3a1 1 0 01-1.414-1.414L15.586 11H7a1 1 0 110-2h8.586l-2.293-2.293a1 1 0 010-1.414z" clipRule="evenodd" />
            </svg>
            <span>Logout</span>
          </Button>
        </div>
      </nav>
    </div>
  );
};

// Enhanced Header Component with title detection
const Header = () => {
  const router = useRouter();
  const { user, logout } = useAuth();
  
  const getPageTitle = () => {
    if (router.pathname === '/dashboard') return 'Dashboard Overview';
    if (router.pathname.startsWith('/dashboard/integrations')) return 'Integrations';
    if (router.pathname.startsWith('/dashboard/irn')) return 'IRN Management';
    if (router.pathname.startsWith('/dashboard/customers')) return 'Customers';
    if (router.pathname.startsWith('/dashboard/submission')) return 'Submission Dashboard';
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
        >
          <Bell className="h-5 w-5" />
        </Button>
        
        <div className="relative group">
          <Button 
            variant="ghost"
            size="icon"
            aria-label="profile"
            className="rounded-full"
          >
            <User className="h-5 w-5" />
          </Button>
          
          <div className="absolute right-0 mt-2 w-48 bg-white rounded-md shadow-lg py-1 z-50 hidden group-hover:block border">
            <div className="px-4 py-2 text-sm text-gray-700 border-b">
              {user?.name || 'User'}
            </div>
            <Button
              variant="ghost"
              onClick={logout}
              className="w-full text-left px-4 py-2 text-sm text-gray-700 hover:bg-gray-100 flex items-center"
            >
              <svg xmlns="http://www.w3.org/2000/svg" className="h-4 w-4 mr-2" viewBox="0 0 20 20" fill="currentColor">
                <path fillRule="evenodd" d="M3 3a1 1 0 0 0-1 1v12a1 1 0 0 0 1 1h10a1 1 0 0 0 1-1v-3a1 1 0 1 1 2 0v3a3 3 0 0 1-3 3H3a3 3 0 0 1-3-3V4a3 3 0 0 1 3-3h10a3 3 0 0 1 3 3v3a1 1 0 1 1-2 0V4a1 1 0 0 0-1-1H3z" clipRule="evenodd" />
                <path fillRule="evenodd" d="M13.293 7.293a1 1 0 0 1 1.414 0l3 3a1 1 0 0 1 0 1.414l-3 3a1 1 0 0 1-1.414-1.414L15.586 11H7a1 1 0 1 1 0-2h8.586l-2.293-2.293a1 1 0 0 1 0-1.414z" clipRule="evenodd" />
              </svg>
              Logout
            </Button>
          </div>
        </div>
      </div>
    </header>
  );
};

// Main App Dashboard Layout
const AppDashboardLayout = ({ 
  children, 
  title = 'Dashboard | TaxPoynt eInvoice', 
  description,
  branding
}: AppDashboardLayoutProps) => {
  const [isOpen, setIsOpen] = useState(false);
  const { user, isAuthenticated, isLoading, logout } = useAuth();
  const router = useRouter();
  
  // Determine if this is a company dashboard view based on the router path
  const isCompanyDashboard = router.pathname.includes('/dashboard/company');
  
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
