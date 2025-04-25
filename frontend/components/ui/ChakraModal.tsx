import React from 'react';
import { Box, Flex, CloseButton } from '@chakra-ui/react';

interface ModalProps {
  isOpen: boolean;
  onClose: () => void;
  children: React.ReactNode;
  size?: 'sm' | 'md' | 'lg' | 'xl' | 'full';
}

export const Modal: React.FC<ModalProps> = ({ 
  isOpen, 
  onClose, 
  children, 
  size = 'md' 
}) => {
  if (!isOpen) return null;
  
  const sizeMap = {
    sm: '400px',
    md: '500px',
    lg: '600px',
    xl: '800px',
    full: '90vw',
  };
  
  return (
    <Box
      position="fixed"
      top={0}
      left={0}
      width="100vw"
      height="100vh"
      zIndex={1000}
      display="flex"
      justifyContent="center"
      alignItems="center"
      onClick={onClose}
    >
      {children}
    </Box>
  );
};

export const ModalOverlay: React.FC = () => {
  return (
    <Box
      position="fixed"
      top={0}
      left={0}
      width="100vw"
      height="100vh"
      bg="blackAlpha.600"
      zIndex={1001}
    />
  );
};

interface ModalContentProps {
  children: React.ReactNode;
}

export const ModalContent: React.FC<ModalContentProps> = ({ children }) => {
  return (
    <Box
      position="relative"
      bg="white"
      _dark={{ bg: 'gray.800' }}
      borderRadius="md"
      zIndex={1002}
      maxWidth="800px"
      width="90%"
      boxShadow="lg"
      onClick={(e) => e.stopPropagation()}
    >
      {children}
    </Box>
  );
};

interface ModalHeaderProps {
  children: React.ReactNode;
}

export const ModalHeader: React.FC<ModalHeaderProps> = ({ children }) => {
  return (
    <Box
      p={4}
      fontWeight="bold"
      fontSize="lg"
      borderBottomWidth="1px"
      borderColor="gray.200"
      _dark={{ borderColor: 'gray.600' }}
    >
      {children}
    </Box>
  );
};

interface ModalBodyProps {
  children: React.ReactNode;
}

export const ModalBody: React.FC<ModalBodyProps> = ({ children }) => {
  return (
    <Box p={4}>
      {children}
    </Box>
  );
};

interface ModalFooterProps {
  children: React.ReactNode;
}

export const ModalFooter: React.FC<ModalFooterProps> = ({ children }) => {
  return (
    <Flex
      p={4}
      justifyContent="flex-end"
      borderTopWidth="1px"
      borderColor="gray.200"
      _dark={{ borderColor: 'gray.600' }}
    >
      {children}
    </Flex>
  );
};

interface ModalCloseButtonProps {
  onClick: () => void;
}

export const ModalCloseButton: React.FC<ModalCloseButtonProps> = ({ onClick }) => {
  return (
    <Box position="absolute" top={3} right={3}>
      <CloseButton onClick={onClick} />
    </Box>
  );
};

// Custom useDisclosure hook that matches the API we need
export function useDisclosure() {
  const [isOpen, setIsOpen] = React.useState(false);
  
  const onOpen = React.useCallback(() => setIsOpen(true), []);
  const onClose = React.useCallback(() => setIsOpen(false), []);
  const onToggle = React.useCallback(() => setIsOpen(prev => !prev), []);
  
  return {
    isOpen,
    onOpen,
    onClose,
    onToggle
  };
} 