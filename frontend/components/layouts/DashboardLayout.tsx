import React, { ReactNode, useState, useEffect } from 'react';
import { useRouter } from 'next/router';
import Link from 'next/link';
import { 
  FiHome, FiTrendingUp, FiList, FiSettings, FiMenu, FiBell, FiUser, FiX
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
  { name: 'Settings', icon: FiSettings, href: '/settings' },
];

// Sidebar Navigation Item
const NavItem = ({ icon: Icon, children, href, className }: NavItemProps) => {
  return (
    <Link href={href} className={cn(
      "flex items-center p-4 mx-4 rounded-lg cursor-pointer transition-colors",
      "hover:bg-primary-50 hover:text-primary-600 dark:hover:bg-primary-900 dark:hover:text-primary-400",
      className
    )}>
      {Icon && (
        <Icon className="mr-4 h-4 w-4" />
      )}
      <span>{children}</span>
    </Link>
  );
};

// Sidebar Component
const Sidebar = ({ onClose, className }: SidebarProps) => {
  return (
    <div className={cn(
      "transition-all duration-300 ease-in-out bg-white dark:bg-gray-800",
      "border-r border-gray-200 dark:border-gray-700",
      "w-full md:w-60 fixed h-full",
      className
    )}>
      <div className="h-20 flex items-center mx-8 justify-between">
        <Typography.Heading level="h1">
          TaxPoynt
        </Typography.Heading>
        <button 
          className="md:hidden flex items-center justify-center rounded-md p-2"
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
      ml-0 md:ml-60 px-4 h-20 flex items-center
      bg-white dark:bg-gray-800
      border-b border-gray-200 dark:border-gray-700
      justify-between md:justify-end
    ">
      <button
        className="flex md:hidden items-center justify-center p-2 rounded-md border border-gray-300 dark:border-gray-600"
        onClick={onOpen}
        aria-label="open menu"
      >
        <FiMenu className="h-5 w-5" />
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
  
  const onOpen = () => setIsOpen(true);
  const onClose = () => setIsOpen(false);
  
  // Redirect to login if not authenticated
  useEffect(() => {
    if (!isLoading && !isAuthenticated) {
      router.push('/auth/login?redirect=' + encodeURIComponent(router.pathname));
    }
  }, [isAuthenticated, isLoading, router]);
  
  // Show loading state while checking auth
  if (isLoading) {
    return (
      <MainLayout title={title} showNav={false}>
        <div className="flex items-center justify-center min-h-screen">
          <Spinner size="lg" />
          <Typography.Text className="ml-3">Loading dashboard...</Typography.Text>
        </div>
      </MainLayout>
    );
  }
  
  // If not authenticated, don't render dashboard content
  if (!isAuthenticated) {
    return null; // Will redirect via the useEffect
  }
  
  return (
    <MainLayout title={title} description={description} showNav={false}>
      <div className="min-h-screen bg-gray-50 dark:bg-gray-900">
        {/* Desktop Sidebar - always visible on md and above */}
        <Sidebar
          onClose={onClose}
          className="hidden md:block"
        />
        
        {/* Mobile Sidebar - only visible when isOpen is true */}
        {isOpen && (
          <div className="fixed inset-0 z-40 md:hidden">
            {/* Overlay */}
            <div 
              className="fixed inset-0 bg-gray-600 bg-opacity-75 transition-opacity"
              onClick={onClose}
              aria-hidden="true"
            />
            
            {/* Drawer */}
            <div className="fixed inset-0 flex z-40">
              <div className="relative flex-1 flex flex-col w-full max-w-xs bg-white dark:bg-gray-800">
                <Sidebar onClose={onClose} />
              </div>
            </div>
          </div>
        )}
        
        {/* Header */}
        <Header onOpen={onOpen} />
        
        {/* Main Content */}
        <main className="ml-0 md:ml-60 p-4">
          {children}
        </main>
      </div>
    </MainLayout>
  );
};

export default DashboardLayout; 