import React, { ReactNode, useState, useEffect } from 'react';
import { useRouter } from 'next/router';
import Link from 'next/link';
import { 
  FiHome, FiTrendingUp, FiList, FiSettings, FiMenu, FiBell, FiUser, FiX, FiBarChart2
} from 'react-icons/fi';
import { Typography } from '../ui/Typography';
import { Button } from '../ui/Button';
import { cn } from '../../utils/cn';
import MainLayout from './MainLayout';
import { useAuth } from '../../context/AuthContext';
import { Spinner } from '../ui/Spinner';
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
}

// Navigation Items - matched to the screenshot
const NavItems = [
  { name: 'Dashboard', icon: FiHome, href: '/dashboard' },
  { name: 'Integrations', icon: FiTrendingUp, href: '/integrations' },
  { name: 'IRN Management', icon: FiList, href: '/irn' },
  { name: 'Submission Dashboard', icon: FiBarChart2, href: '/submission-dashboard' },
  { name: 'Settings', icon: FiSettings, href: '/settings' },
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

// Sidebar Navigation Item - matched exactly to screenshot
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

// Sidebar Component - simplified to match screenshot
const Sidebar = ({ onClose, className }: SidebarProps) => {
  return (
    <div className={cn(
      "transition-all duration-300 ease-in-out bg-indigo-900 text-white",
      "w-full md:w-64 fixed h-full z-20",
      className
    )}>
      <div className="h-20 flex items-center px-6 justify-between border-b border-indigo-800">
        <div className="flex items-center">
          <div className="bg-white rounded-full w-8 h-8 flex items-center justify-center mr-3">
            <svg width="20" height="20" viewBox="0 0 64 64" fill="none" xmlns="http://www.w3.org/2000/svg">
              <path d="M32 0C14.327 0 0 14.327 0 32C0 49.673 14.327 64 32 64C49.673 64 64 49.673 64 32C64 14.327 49.673 0 32 0ZM32 12C38.627 12 44 17.373 44 24C44 30.627 38.627 36 32 36C25.373 36 20 30.627 20 24C20 17.373 25.373 12 32 12ZM32 56C24.36 56 17.56 52.36 13.6 46.64C13.8 39.32 27.2 35.2 32 35.2C36.76 35.2 50.2 39.32 50.4 46.64C46.44 52.36 39.64 56 32 56Z" fill="#4F46E5"/>
            </svg>
          </div>
          <Typography.Heading level="h1" className="text-white text-lg">
            TaxPoynt
          </Typography.Heading>
        </div>
      </div>
      
      <nav className="mt-4">
        {NavItems.map((nav) => (
          <NavItem key={nav.name} icon={nav.icon} href={nav.href}>
            {nav.name}
          </NavItem>
        ))}
      </nav>
    </div>
  );
};

// Header Component - simplified to match screenshot
const Header = () => {
  return (
    <header className="
      ml-0 md:ml-64 px-4 h-16 flex items-center
      bg-white shadow-sm
      border-b border-gray-200
      justify-end sticky top-0 z-10
    ">
      
      <div className="flex md:hidden">
        <Typography.Heading level="h1">
          TaxPoynt
        </Typography.Heading>
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

// Main Dashboard Layout
interface DashboardLayoutProps {
  children: ReactNode;
  title?: string;
  description?: string;
}

const DashboardLayout = ({ children, title = 'Dashboard | Taxpoynt eInvoice', description }: DashboardLayoutProps) => {
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
          <main className="p-4">
            {children}
          </main>
        </div>
      </div>
    </MainLayout>
  );
};

export default DashboardLayout; 