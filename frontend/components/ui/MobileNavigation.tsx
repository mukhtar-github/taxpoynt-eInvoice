import React from 'react';
import { 
  Box, 
  Flex, 
  Text
} from '@chakra-ui/react';
import { useRouter } from 'next/router';
import Link from 'next/link';
import { FiMenu, FiHome, FiTrendingUp, FiList, FiSettings, FiLogOut } from 'react-icons/fi';

// Use native HTML button instead of our custom components
// This avoids TypeScript errors with the custom components

interface NavItem {
  name: string;
  icon: React.ElementType;
  href: string;
}

interface MobileNavigationProps {
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

/**
 * Mobile Navigation component with drawer triggered by hamburger icon
 * Includes responsive design for mobile-first approach
 */
export const MobileNavigation: React.FC<MobileNavigationProps> = ({
  title = 'TaxPoynt',
  logo,
  showProfileInfo = true,
  userInfo,
  navItems,
  onLogout,
}) => {
  const [isOpen, setIsOpen] = React.useState(false);
  const onOpen = () => setIsOpen(true);
  const onClose = () => setIsOpen(false);
  const router = useRouter();

  // Default navigation items if not provided
  const defaultNavItems: NavItem[] = [
    { name: 'Dashboard', icon: FiHome, href: '/dashboard' },
    { name: 'Integrations', icon: FiTrendingUp, href: '/integrations' },
    { name: 'IRN Management', icon: FiList, href: '/irn' },
    { name: 'Settings', icon: FiSettings, href: '/settings' },
  ];

  const items = navItems || defaultNavItems;

  return (
    <>
      <Flex
        as="nav"
        align="center"
        justify="space-between"
        wrap="wrap"
        w="100%"
        p="var(--spacing-4)"
        bg="white"
        borderBottom="1px solid"
        borderColor="var(--color-border)"
        display={{ base: 'flex', md: 'none' }}
      >
        <Flex align="center">
          {logo || <Text fontSize="xl" fontWeight="bold">{title}</Text>}
        </Flex>

        {/* Use native button instead of IconButton */}
        <button
          aria-label="Open menu"
          onClick={onOpen}
          style={{
            background: 'transparent',
            border: 'none',
            cursor: 'pointer',
            padding: '8px',
            borderRadius: '4px',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center'
          }}
        >
          <FiMenu size={24} />
        </button>
      </Flex>

      {/* Mobile drawer */}
      {isOpen && (
        <>
          {/* Overlay */}
          <div
            onClick={onClose}
            style={{
              position: 'fixed',
              top: 0,
              left: 0,
              right: 0,
              bottom: 0,
              backgroundColor: 'rgba(0, 0, 0, 0.4)',
              zIndex: 998
            }}
          />
          
          {/* Drawer content */}
          <div
            style={{
              position: 'fixed',
              top: 0,
              left: 0,
              bottom: 0,
              width: '280px',
              backgroundColor: 'white',
              zIndex: 999,
              boxShadow: '0 0 15px rgba(0, 0, 0, 0.1)',
              overflowY: 'auto'
            }}
          >
            {/* Header */}
            <div style={{ 
              display: 'flex', 
              justifyContent: 'space-between', 
              alignItems: 'center',
              padding: 'var(--spacing-4)',
              borderBottom: '1px solid var(--color-border)'
            }}>
              {logo || <Text fontSize="xl" fontWeight="bold">{title}</Text>}
              <button
                onClick={onClose}
                aria-label="Close menu"
                style={{
                  background: 'transparent',
                  border: 'none',
                  cursor: 'pointer',
                  width: '32px',
                  height: '32px',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  borderRadius: '50%'
                }}
              >
                <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                  <line x1="18" y1="6" x2="6" y2="18" />
                  <line x1="6" y1="6" x2="18" y2="18" />
                </svg>
              </button>
            </div>

            {/* Body */}
            <div>
              {showProfileInfo && userInfo && (
                <Box p="var(--spacing-4)" borderBottomWidth="1px">
                  <Flex align="center">
                    <div style={{
                      width: '40px',
                      height: '40px',
                      borderRadius: '50%',
                      backgroundColor: 'var(--color-primary-light)',
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'center',
                      marginRight: '12px',
                      color: 'var(--color-primary-dark)',
                      fontWeight: 'bold'
                    }}>
                      {userInfo.avatar ? (
                        <img 
                          src={userInfo.avatar} 
                          alt={userInfo.name} 
                          style={{
                            width: '100%',
                            height: '100%',
                            borderRadius: '50%',
                            objectFit: 'cover'
                          }}
                        />
                      ) : (
                        userInfo.name.charAt(0)
                      )}
                    </div>
                    <Box>
                      <Text fontWeight="medium">{userInfo.name}</Text>
                      <Text fontSize="sm" color="var(--color-text-secondary)">
                        {userInfo.email}
                      </Text>
                    </Box>
                  </Flex>
                </Box>
              )}

              <Flex direction="column" mt="var(--spacing-2)">
                {items.map((item) => {
                  const isActive = router.pathname === item.href;
                  return (
                    <Link href={item.href} key={item.name} passHref>
                      <Flex
                        p="var(--spacing-4)"
                        mx="var(--spacing-2)"
                        borderRadius="var(--border-radius-md)"
                        role="group"
                        cursor="pointer"
                        fontWeight={isActive ? 'medium' : 'normal'}
                        bg={isActive ? 'var(--color-primary-light)' : 'transparent'}
                        color={isActive ? 'var(--color-primary-dark)' : 'inherit'}
                        _hover={{
                          bg: 'var(--color-background-alt)',
                        }}
                        onClick={onClose}
                      >
                        <Box as={item.icon} mr="var(--spacing-3)" />
                        {item.name}
                      </Flex>
                    </Link>
                  );
                })}

                {onLogout && (
                  <Flex
                    p="var(--spacing-4)"
                    mx="var(--spacing-2)"
                    borderRadius="var(--border-radius-md)"
                    role="group"
                    cursor="pointer"
                    mt="auto"
                    onClick={() => {
                      onClose();
                      onLogout();
                    }}
                    _hover={{
                      bg: 'var(--color-background-alt)',
                    }}
                  >
                    <Box as={FiLogOut} mr="var(--spacing-3)" />
                    Logout
                  </Flex>
                )}
              </Flex>
            </div>
          </div>
        </>
      )}
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
    <Flex
      as="nav"
      align="center"
      justify="space-between"
      wrap="wrap"
      w="100%"
      p="var(--spacing-4)"
      bg="white"
      borderBottom="1px solid"
      borderColor="var(--color-border)"
      display={{ base: 'flex', md: 'none' }}
    >
      <Flex align="center">
        {logo || <Text fontSize="xl" fontWeight="bold">{title}</Text>}
      </Flex>

      {/* Use native button instead of IconButton */}
      <button
        aria-label="Open menu"
        onClick={onMenuClick}
        style={{
          background: 'transparent',
          border: 'none',
          cursor: 'pointer',
          padding: '8px',
          borderRadius: '4px',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center'
        }}
      >
        <FiMenu size={24} />
      </button>
    </Flex>
  );
};

export default MobileNavigation; 