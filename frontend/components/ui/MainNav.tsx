import React, { useState } from 'react';
import Link from 'next/link';
import Image from 'next/image';
import { useRouter } from 'next/router';
import { cn } from '../../utils/cn';
import { Typography } from './Typography';
import { Button } from './Button';
import { 
  Home, 
  TrendingUp, 
  FileText, 
  Settings, 
  Bell, 
  User, 
  Menu, 
  X, 
  ChevronDown 
} from 'lucide-react';

interface NavItem {
  name: string;
  href: string;
  icon: React.ComponentType<any>;
  children?: NavItem[];
}

interface MainNavProps {
  title?: string;
  logo?: React.ReactNode;
  userInfo?: {
    name: string;
    email: string;
    avatar?: string;
  };
  authButtons?: React.ReactNode;
  onLogout?: () => void;
}

// Define the navigation items
const navItems: NavItem[] = [
  {
    name: 'Dashboard',
    href: '/dashboard',
    icon: Home
  },
  {
    name: 'Integrations',
    href: '/integrations',
    icon: TrendingUp,
    children: [
      {
        name: 'Odoo',
        href: '/integrations/odoo',
        icon: FileText
      },
      {
        name: 'New Integration',
        href: '/integrations/new',
        icon: FileText
      }
    ]
  },
  {
    name: 'Pricing',
    href: '/pricing',
    icon: TrendingUp
  },
  {
    name: 'IRN Management',
    href: '/odoo-irn-management',
    icon: FileText
  },
  {
    name: 'Settings',
    href: '/settings',
    icon: Settings
  }
];

/**
 * MainNav Component
 * 
 * Main navigation component that includes both desktop and mobile navigation.
 * Replaces the previous Chakra UI navigation with Tailwind CSS styling.
 */
export const MainNav: React.FC<MainNavProps> = ({
  title = 'Taxpoynt E-Invoice',
  logo,
  userInfo,
  authButtons,
  onLogout
}) => {
  const router = useRouter();
  const [isMobileMenuOpen, setIsMobileMenuOpen] = useState(false);
  const [openDropdown, setOpenDropdown] = useState<string | null>(null);

  const toggleMobileMenu = () => {
    setIsMobileMenuOpen(prev => !prev);
  };

  const handleDropdownToggle = (name: string) => {
    setOpenDropdown(curr => curr === name ? null : name);
  };

  const isActive = (href: string) => {
    return router.pathname === href || router.pathname.startsWith(`${href}/`);
  };

  return (
    <>
      {/* Desktop Navigation */}
      <header className="hidden lg:block bg-background border-b border-border sticky top-0 z-50">
        <div className="container mx-auto px-4 max-w-7xl">
          <div className="flex h-16 items-center justify-between">
            {/* Logo and Brand */}
            <div className="flex items-center">
              {logo ? (
                logo
              ) : (
                <Link href="/" className="flex items-center space-x-2">
                  <div className="relative w-8 h-8">
                    <Image src="/logo.svg" alt="Taxpoynt Logo" fill className="object-contain" priority />
                  </div>
                  <Typography.Text className="text-base font-semibold text-primary-700" style={{height: '32px', display: 'flex', alignItems: 'center'}}>{title}</Typography.Text>
                </Link>
              )}
            </div>

            {/* Desktop Navigation Links */}
            <nav className="mx-6 flex items-center space-x-4 lg:space-x-6">
              {navItems.map((item) => (
                <div key={item.name} className="relative group">
                  {item.children ? (
                    <button 
                      onClick={() => handleDropdownToggle(item.name)}
                      className={cn(
                        "inline-flex items-center px-1 pt-1 text-sm font-medium transition-colors hover:text-primary",
                        isActive(item.href) 
                          ? "text-primary border-b-2 border-primary" 
                          : "text-text-secondary"
                      )}
                    >
                      <item.icon className="w-4 h-4 mr-2" />
                      {item.name}
                      <ChevronDown className="ml-1 h-4 w-4" />
                    </button>
                  ) : (
                    <Link
                      href={item.href}
                      className={cn(
                        "inline-flex items-center px-1 pt-1 text-sm font-medium transition-colors hover:text-primary",
                        isActive(item.href) 
                          ? "text-primary border-b-2 border-primary" 
                          : "text-text-secondary"
                      )}
                    >
                      <item.icon className="w-4 h-4 mr-2" />
                      {item.name}
                    </Link>
                  )}

                  {/* Dropdown Menu */}
                  {item.children && openDropdown === item.name && (
                    <div className="absolute left-0 mt-2 w-48 rounded-md shadow-lg bg-background ring-1 ring-black ring-opacity-5 z-10">
                      <div className="py-1" role="menu" aria-orientation="vertical">
                        {item.children.map((child) => (
                          <Link
                            key={child.name}
                            href={child.href}
                            className={cn(
                              "block px-4 py-2 text-sm hover:bg-background-alt",
                              isActive(child.href) ? "text-primary" : "text-text-primary"
                            )}
                            role="menuitem"
                          >
                            <div className="flex items-center">
                              <child.icon className="w-4 h-4 mr-2" />
                              {child.name}
                            </div>
                          </Link>
                        ))}
                      </div>
                    </div>
                  )}
                </div>
              ))}
            </nav>

            {/* User Menu and Notifications */}
            <div className="flex items-center space-x-4">
              <Button variant="ghost" size="icon" className="relative">
                <Bell className="h-5 w-5" />
                <span className="absolute top-1 right-1 w-2 h-2 bg-error rounded-full"></span>
              </Button>

              {/* Desktop Auth or User Menu */}
              {authButtons ? (
                /* Auth Buttons for logged out state */
                <div className="ml-4 relative flex-shrink-0">
                  {authButtons}
                </div>
              ) : userInfo ? (
                /* User Menu for logged in state */
                <div className="ml-4 relative flex-shrink-0">
                  <div className="flex items-center">
                    <button 
                      className="flex items-center text-sm rounded-full focus:outline-none focus:ring-2 focus:ring-primary focus:ring-offset-2"
                      onClick={() => handleDropdownToggle('user')}
                    >
                      <span className="sr-only">Open user menu</span>
                      {/* User Icon or Avatar */}
                      <div className="h-8 w-8 rounded-full bg-primary-500 flex items-center justify-center text-white">
                        <span>{userInfo.name.charAt(0).toUpperCase()}</span>
                      </div>
                    </button>
                  </div>

                  {/* User Dropdown Menu */}
                  {openDropdown === 'user' && (
                    <div className="absolute right-0 mt-2 w-48 rounded-md shadow-lg py-1 bg-white dark:bg-gray-800 ring-1 ring-black ring-opacity-5 focus:outline-none z-10">
                      <div className="px-4 py-2 border-b border-border">
                        <Typography.Text className="text-sm font-medium">{userInfo.name}</Typography.Text>
                        <Typography.Text size="xs" variant="secondary">{userInfo.email}</Typography.Text>
                      </div>
                      <Link 
                        href="/profile" 
                        className="block px-4 py-2 text-sm text-text-primary hover:bg-gray-100 dark:hover:bg-gray-700" 
                      >
                        Profile
                      </Link>
                      <Link 
                        href="/settings/account" 
                        className="block px-4 py-2 text-sm text-text-primary hover:bg-gray-100 dark:hover:bg-gray-700"
                      >
                        Account Settings
                      </Link>
                      <button 
                        onClick={() => {
                          if (onLogout) onLogout();
                          setOpenDropdown(null);
                        }}
                        className="block w-full text-left px-4 py-2 text-sm text-error hover:bg-gray-100 dark:hover:bg-gray-700"
                      >
                        Logout
                      </button>
                    </div>
                  )}
                </div>
              ) : (
                /* No user or auth buttons fallback */
                <div></div>
              )}
            </div>
          </div>
        </div>
      </header>

      {/* Mobile Navigation */}
      <header className="lg:hidden bg-background border-b border-border sticky top-0 z-50">
        <div className="container mx-auto px-4">
          <div className="flex h-14 items-center justify-between">
            {/* Logo and Brand */}
            <div className="flex items-center">
              {logo ? (
                logo
              ) : (
                <Link href="/" className="flex items-center space-x-2">
                  <div className="relative w-7 h-7">
                    <Image src="/logo.svg" alt="Taxpoynt Logo" fill className="object-contain" priority />
                  </div>
                  <Typography.Text className="text-sm font-semibold text-primary-700" style={{height: '28px', display: 'flex', alignItems: 'center'}}>{title}</Typography.Text>
                </Link>
              )}
            </div>

            {/* Mobile Menu Button */}
            <Button
              variant="ghost"
              size="icon"
              onClick={toggleMobileMenu}
              aria-label="Toggle menu"
            >
              {isMobileMenuOpen ? (
                <X className="h-5 w-5" />
              ) : (
                <Menu className="h-5 w-5" />
              )}
            </Button>
          </div>
        </div>

        {/* Mobile Menu Dropdown */}
        {isMobileMenuOpen && (
          <div className="lg:hidden bg-background border-b border-border">
            <div className="container mx-auto px-4 py-3">
              {/* User Info Section */}
              {userInfo ? (
                <div className="flex items-center space-x-3 py-3 border-b border-border mb-3">
                  <div className="w-10 h-10 rounded-full bg-background-alt flex items-center justify-center">
                    {userInfo.avatar ? (
                      <img src={userInfo.avatar} alt={userInfo.name} className="w-10 h-10 rounded-full" />
                    ) : (
                      <User className="h-6 w-6" />
                    )}
                  </div>
                  <div>
                    <Typography.Text className="font-medium">{userInfo.name}</Typography.Text>
                    <Typography.Text className="text-xs text-text-secondary">{userInfo.email}</Typography.Text>
                  </div>
                </div>
              ) : null}

              {/* Navigation Links */}
              <nav className="space-y-1">
                {navItems.map((item) => (
                  <div key={item.name}>
                    {item.children ? (
                      <>
                        <button 
                          onClick={() => handleDropdownToggle(item.name)}
                          className={cn(
                            "flex items-center justify-between w-full px-3 py-2 text-base font-medium rounded-md",
                            isActive(item.href) 
                              ? "bg-primary-light text-primary" 
                              : "text-text-primary hover:bg-background-alt"
                          )}
                        >
                          <span className="flex items-center">
                            <item.icon className="mr-3 h-5 w-5 flex-shrink-0" />
                            {item.name}
                          </span>
                          <ChevronDown className={cn(
                            "h-5 w-5 transition-transform",
                            openDropdown === item.name && "transform rotate-180"
                          )} />
                        </button>

                        {openDropdown === item.name && (
                          <div className="pl-10 space-y-1 mt-1">
                            {item.children.map((child) => (
                              <Link
                                key={child.name}
                                href={child.href}
                                className={cn(
                                  "block px-3 py-2 text-base font-medium rounded-md",
                                  isActive(child.href) 
                                    ? "bg-primary-light text-primary" 
                                    : "text-text-primary hover:bg-background-alt"
                                )}
                              >
                                <span className="flex items-center">
                                  <child.icon className="mr-3 h-5 w-5 flex-shrink-0" />
                                  {child.name}
                                </span>
                              </Link>
                            ))}
                          </div>
                        )}
                      </>
                    ) : (
                      <Link
                        href={item.href}
                        className={cn(
                          "flex items-center px-3 py-2 text-base font-medium rounded-md",
                          isActive(item.href) 
                            ? "bg-primary-light text-primary" 
                            : "text-text-primary hover:bg-background-alt"
                        )}
                      >
                        <item.icon className="mr-3 h-5 w-5 flex-shrink-0" />
                        {item.name}
                      </Link>
                    )}
                  </div>
                ))}
              </nav>

              {/* Mobile Menu Footer with Logout */}
              {onLogout && (
                <div className="pt-4 mt-4 border-t border-border">
                  <Button
                    variant="ghost"
                    className="flex w-full items-center text-error justify-start"
                    onClick={onLogout}
                  >
                  <svg 
                    xmlns="http://www.w3.org/2000/svg" 
                    className="mr-3 h-5 w-5 flex-shrink-0" 
                    viewBox="0 0 24 24" 
                    fill="none" 
                    stroke="currentColor" 
                    strokeWidth="2" 
                    strokeLinecap="round" 
                    strokeLinejoin="round"
                  >
                    <path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4" />
                    <polyline points="16 17 21 12 16 7" />
                    <line x1="21" y1="12" x2="9" y2="12" />
                  </svg>
                  Logout
                </Button>
              </div>
              )}
            </div>
          </div>
        )}
      </header>
    </>
  );
};

export default MainNav;
