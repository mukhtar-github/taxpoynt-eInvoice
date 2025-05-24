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

// Navigation Items
const NavItems = [
  { name: 'Dashboard', icon: FiHome, href: '/dashboard' },
  { name: 'Integrations', icon: FiTrendingUp, href: '/integrations' },
  { name: 'IRN Management', icon: FiList, href: '/irn' },
  { name: 'Submission Dashboard', icon: FiBarChart2, href: '/submission-dashboard' },
  { name: 'Settings', icon: FiSettings, href: '/settings' },
];

// Sidebar Navigation Item
const NavItem = ({ icon: Icon, children, href, className }: NavItemProps) => {
  const router = useRouter();
  const isActive = router.pathname === href || router.pathname.startsWith(`${href}/`);
  
  return (
    <Link href={href} className={cn(
      "flex items-center p-3 mx-3 my-1 rounded-lg cursor-pointer transition-all duration-200",
      "hover:bg-indigo-800/60 hover:shadow-md",
      isActive ? "bg-indigo-800/50 border-l-4 border-white shadow-md" : "border-l-4 border-transparent",
      className
    )}>
      {Icon && (
        <Icon className={cn("ml-1 mr-3 h-5 w-5", isActive ? "text-white" : "text-indigo-200")} />
      )}
      <span className={isActive ? "font-medium" : "font-normal"}>{children}</span>
    </Link>
  );
};

// Sidebar Component
const Sidebar = ({ onClose, className }: SidebarProps) => {
  return (
    <div className={cn(
      "transition-all duration-300 ease-in-out bg-gradient-to-b from-indigo-900 to-blue-800 text-white",
      "border-r border-indigo-700",
      "w-full md:w-64 fixed h-full shadow-xl z-20",
      className
    )}>
      <div className="h-24 flex items-center px-6 justify-between border-b border-indigo-700/50">
        <div className="flex items-center">
          <div className="bg-white p-2 rounded-lg shadow-md flex items-center justify-center mr-3" style={{ width: '40px', height: '40px' }}>
            {/* Embedded logo SVG */}
            <svg width="28" height="28" viewBox="0 0 64 64" fill="none" xmlns="http://www.w3.org/2000/svg">
              <path d="M32 0C14.327 0 0 14.327 0 32C0 49.673 14.327 64 32 64C49.673 64 64 49.673 64 32C64 14.327 49.673 0 32 0ZM32 12C38.627 12 44 17.373 44 24C44 30.627 38.627 36 32 36C25.373 36 20 30.627 20 24C20 17.373 25.373 12 32 12ZM32 56C24.36 56 17.56 52.36 13.6 46.64C13.8 39.32 27.2 35.2 32 35.2C36.76 35.2 50.2 39.32 50.4 46.64C46.44 52.36 39.64 56 32 56Z" fill="#4F46E5"/>
            </svg>
          </div>
          <Typography.Heading level="h1" className="text-white text-xl">
            TaxPoynt
          </Typography.Heading>
        </div>
        <button 
          className="md:hidden flex items-center justify-center rounded-md p-2 bg-indigo-800 hover:bg-indigo-700 transition-colors"
          onClick={onClose}
          aria-label="Close menu"
        >
          <FiX className="h-5 w-5" />
        </button>
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

// Header Component
const Header = ({ onOpen }: { onOpen: () => void }) => {
  return (
    <header className="
      ml-0 md:ml-64 px-4 h-16 flex items-center
      bg-white shadow-sm
      border-b border-gray-200
      justify-between sticky top-0 z-10
    ">
      <button
        className="flex items-center justify-center p-2 rounded-md text-gray-700 hover:bg-gray-100 transition-colors"
        onClick={onOpen}
        aria-label="Toggle menu"
      >
        <FiMenu className="h-6 w-6" />
      </button>
      
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
  
  // Handle sidebar toggle
  const toggleSidebar = () => setIsOpen(!isOpen);
  const closeSidebar = () => setIsOpen(false);
  
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
      <div className="flex min-h-screen bg-gray-50">
        {/* Mobile Sidebar Backdrop */}
        {isOpen && (
          <div 
            className="fixed inset-0 bg-gray-900 bg-opacity-50 z-10 md:hidden"
            onClick={closeSidebar}
            aria-hidden="true"
          />
        )}
        
        {/* Sidebar */}
        <Sidebar
          onClose={closeSidebar}
          className={cn(
            "md:translate-x-0 transform transition-transform duration-200 ease-in-out z-20",
            isOpen ? "translate-x-0" : "-translate-x-full"
          )}
        />
        
        {/* Main Content */}
        <div className="flex-1 transition-all duration-200 ease-in-out ml-0 md:ml-64">
          <Header onOpen={toggleSidebar} />
          <main className="min-h-[calc(100vh-4rem)] bg-gray-50 p-4">
            {children}
          </main>
        </div>
      </div>
    </MainLayout>
  );
};

export default DashboardLayout; 