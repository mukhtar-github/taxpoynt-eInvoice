import React, { useState } from 'react';
import { Menu, X, Home, TrendingUp, List, Settings, LogOut } from 'lucide-react';
import Link from 'next/link';
import { useRouter } from 'next/router';

interface NavItem {
  name: string;
  icon: React.ComponentType<any>;
  href: string;
}

interface MobileNavProps {
  title?: string;
  logo?: React.ReactNode;
  showProfileInfo?: boolean;
  userInfo?: {
    name: string;
    email: string;
    avatar?: string;
  };
  navItems?: NavItem[];
  onLogout?: () => void;
}

export const MobileNav: React.FC<MobileNavProps> = ({
  title = 'TaxPoynt',
  logo,
  showProfileInfo = true,
  userInfo,
  navItems,
  onLogout,
}) => {
  const [isOpen, setIsOpen] = useState(false);
  const router = useRouter();

  const toggleDrawer = () => setIsOpen(!isOpen);
  const closeDrawer = () => setIsOpen(false);

  // Default navigation items
  const defaultNavItems: NavItem[] = [
    { name: 'Dashboard', icon: Home, href: '/dashboard' },
    { name: 'Integrations', icon: TrendingUp, href: '/integrations' },
    { name: 'IRN Management', icon: List, href: '/irn' },
    { name: 'Settings', icon: Settings, href: '/settings' },
  ];

  const items = navItems || defaultNavItems;

  return (
    <>
      {/* Mobile Navigation Bar */}
      <div className="flex items-center justify-between w-full p-4 bg-white border-b border-border md:hidden">
        <div className="flex items-center">
          {logo || <span className="text-xl font-bold">{title}</span>}
        </div>

        <button
          aria-label="Toggle menu"
          onClick={toggleDrawer}
          className="p-2 transition-colors rounded-md hover:bg-background-alt"
        >
          <Menu size={24} />
        </button>
      </div>

      {/* Drawer Backdrop */}
      {isOpen && (
        <div 
          className="fixed inset-0 bg-black bg-opacity-40 z-40 md:hidden"
          onClick={closeDrawer}
        />
      )}

      {/* Drawer */}
      <div className={`
        fixed top-0 left-0 bottom-0 w-[280px] bg-white z-50 shadow-lg transform transition-transform duration-200 ease-in-out
        ${isOpen ? 'translate-x-0' : '-translate-x-full'} md:hidden overflow-y-auto
      `}>
        {/* Drawer Header */}
        <div className="flex items-center justify-between p-4 border-b border-border">
          {logo || <span className="text-xl font-bold">{title}</span>}
          <button
            aria-label="Close menu"
            onClick={closeDrawer}
            className="p-2 rounded-full hover:bg-background-alt"
          >
            <X size={20} />
          </button>
        </div>

        {/* User Profile */}
        {showProfileInfo && userInfo && (
          <div className="p-4 border-b border-border">
            <div className="flex items-center">
              <div className="flex items-center justify-center w-10 h-10 mr-3 text-primary-dark bg-primary-light rounded-full font-bold">
                {userInfo.avatar ? (
                  <img 
                    src={userInfo.avatar} 
                    alt={userInfo.name} 
                    className="w-full h-full rounded-full object-cover"
                  />
                ) : (
                  userInfo.name.charAt(0)
                )}
              </div>
              <div>
                <div className="font-medium">{userInfo.name}</div>
                <div className="text-sm text-text-secondary">{userInfo.email}</div>
              </div>
            </div>
          </div>
        )}

        {/* Navigation Items */}
        <div className="flex flex-col mt-2">
          {items.map((item) => {
            const isActive = router.pathname === item.href;
            const IconComponent = item.icon;
            
            return (
              <Link 
                href={item.href} 
                key={item.name}
                onClick={closeDrawer}
                className={`
                  flex items-center p-4 mx-2 rounded-md cursor-pointer transition-colors
                  ${isActive 
                    ? 'bg-primary-light text-primary-dark font-medium' 
                    : 'hover:bg-background-alt'
                  }
                `}
              >
                <IconComponent size={20} className="mr-3 shrink-0" />
                <span>{item.name}</span>
              </Link>
            );
          })}

          {/* Logout Button */}
          {onLogout && (
            <button
              onClick={() => {
                closeDrawer();
                onLogout();
              }}
              className="flex items-center p-4 mx-2 mt-auto rounded-md cursor-pointer hover:bg-background-alt transition-colors"
            >
              <LogOut size={20} className="mr-3 shrink-0" />
              <span>Logout</span>
            </button>
          )}
        </div>
      </div>
    </>
  );
};

/**
 * MobileNavBar component - more minimal version with just hamburger icon
 */
export const MobileNavBar: React.FC<{
  title?: string;
  logo?: React.ReactNode;
  onMenuClick: () => void;
}> = ({
  title = 'TaxPoynt',
  logo,
  onMenuClick,
}) => {
  return (
    <div className="flex items-center justify-between w-full p-4 bg-white border-b border-border md:hidden">
      <div className="flex items-center">
        {logo || <span className="text-xl font-bold">{title}</span>}
      </div>

      <button
        aria-label="Open menu"
        onClick={onMenuClick}
        className="p-2 transition-colors rounded-md hover:bg-background-alt"
      >
        <Menu size={24} />
      </button>
    </div>
  );
};

export default MobileNav; 