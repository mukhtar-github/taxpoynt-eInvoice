import React, { ReactNode } from 'react';
import {
  Box,
  Flex,
  Text,
  BoxProps,
  FlexProps
} from '@chakra-ui/react';
import { useColorModeValue } from '../ui/ChakraColorMode';
import { useDisclosure } from '../ui/ChakraDisclosure';
import { CloseButton } from '../ui/ChakraCloseButton';
import { Drawer, DrawerContent } from '../ui/ChakraDrawer';
import { HStack } from '../ui/ChakraStack';
import { Icon } from '../ui/ChakraIcon';
import { IconButton } from '../ui/ChakraButton';
import { 
  FiHome, FiTrendingUp, FiList, FiSettings, FiMenu, FiBell, FiUser
} from 'react-icons/fi';
import Link from 'next/link';
import { IconType } from 'react-icons';

interface NavItemProps extends FlexProps {
  icon: IconType;
  children: ReactNode;
  href: string;
}

interface SidebarProps extends BoxProps {
  onClose: () => void;
}

// Navigation Items
const NavItems = [
  { name: 'Dashboard', icon: FiHome, href: '/dashboard' },
  { name: 'Integrations', icon: FiTrendingUp, href: '/integrations' },
  { name: 'IRN Management', icon: FiList, href: '/irn' },
  { name: 'Settings', icon: FiSettings, href: '/settings' },
];

// Sidebar Navigation Item
const NavItem = ({ icon, children, href, ...rest }: NavItemProps) => {
  return (
    <Link href={href} passHref>
      <Flex
        align="center"
        p="4"
        mx="4"
        borderRadius="lg"
        role="group"
        cursor="pointer"
        _hover={{
          bg: 'blue.50',
          color: 'blue.600',
        }}
        {...rest}
      >
        {icon && (
          <Icon
            mr="4"
            fontSize="16"
            as={icon}
          />
        )}
        {children}
      </Flex>
    </Link>
  );
};

// Sidebar Component
const Sidebar = ({ onClose, ...rest }: SidebarProps) => {
  const bgColor = useColorModeValue('white', 'gray.800');
  
  return (
    <Box
      transition="3s ease"
      bg={bgColor}
      borderRight="1px"
      borderRightColor={useColorModeValue('gray.200', 'gray.700')}
      w={{ base: 'full', md: 60 }}
      pos="fixed"
      h="full"
      {...rest}
    >
      <Flex h="20" alignItems="center" mx="8" justifyContent="space-between">
        <Text fontSize="2xl" fontWeight="bold">
          TaxPoynt
        </Text>
        <CloseButton display={{ base: 'flex', md: 'none' }} onClick={onClose} />
      </Flex>
      
      {NavItems.map((nav) => (
        <NavItem key={nav.name} icon={nav.icon} href={nav.href}>
          {nav.name}
        </NavItem>
      ))}
    </Box>
  );
};

// Header Component
const Header = ({ onOpen, ...rest }: { onOpen: () => void }) => {
  const bgColor = useColorModeValue('white', 'gray.800');
  
  return (
    <Flex
      ml={{ base: 0, md: 60 }}
      px={{ base: 4, md: 4 }}
      height="20"
      alignItems="center"
      bg={bgColor}
      borderBottomWidth="1px"
      borderBottomColor={useColorModeValue('gray.200', 'gray.700')}
      justifyContent={{ base: 'space-between', md: 'flex-end' }}
      {...rest}
    >
      <IconButton
        display={{ base: 'flex', md: 'none' }}
        onClick={onOpen}
        variant="outline"
        aria-label="open menu"
        icon={<FiMenu />}
      />
      
      <Text
        display={{ base: 'flex', md: 'none' }}
        fontSize="2xl"
        fontWeight="bold"
      >
        TaxPoynt
      </Text>
      
      <HStack spacing={{ base: '0', md: '6' }}>
        <IconButton
          size="lg"
          variant="ghost"
          aria-label="notifications"
          icon={<FiBell />}
        />
        <IconButton
          size="lg"
          variant="ghost"
          aria-label="profile"
          icon={<FiUser />}
        />
      </HStack>
    </Flex>
  );
};

// Main Dashboard Layout
interface DashboardLayoutProps {
  children: ReactNode;
}

const DashboardLayout = ({ children }: DashboardLayoutProps) => {
  const { isOpen, onOpen, onClose } = useDisclosure();
  
  return (
    <Box minH="100vh" bg={useColorModeValue('gray.50', 'gray.900')}>
      <Sidebar
        onClose={() => onClose}
        display={{ base: 'none', md: 'block' }}
      />
      <Drawer
        autoFocus={false}
        isOpen={isOpen}
        placement="left"
        onClose={onClose}
        returnFocusOnClose={false}
        onOverlayClick={onClose}
        size="full"
      >
        <DrawerContent>
          <Sidebar onClose={onClose} />
        </DrawerContent>
      </Drawer>
      
      {/* Header */}
      <Header onOpen={onOpen} />
      
      {/* Main Content */}
      <Box ml={{ base: 0, md: 60 }} p="4">
        {children}
      </Box>
    </Box>
  );
};

export default DashboardLayout; 