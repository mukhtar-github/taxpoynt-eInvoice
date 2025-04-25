import React from 'react';
import { Button as ChakraButton } from '@chakra-ui/react';

interface ButtonProps {
  leftIcon?: React.ReactElement;
  children: React.ReactNode;
  colorScheme?: string;
  onClick?: () => void;
  variant?: string;
  size?: 'xs' | 'sm' | 'md' | 'lg' | 'xl';
  width?: string;
  isLoading?: boolean;
  type?: 'button' | 'submit' | 'reset';
  mt?: number;
}

export const Button: React.FC<ButtonProps> = ({ 
  leftIcon, 
  children, 
  ...props 
}) => {
  return (
    <ChakraButton {...props as any}>
      {leftIcon && <span style={{ marginRight: '0.5rem', display: 'inline-flex' }}>{leftIcon}</span>}
      {children}
    </ChakraButton>
  );
};

interface IconButtonProps {
  'aria-label': string;
  icon: React.ReactElement;
  size?: 'xs' | 'sm' | 'md' | 'lg' | 'xl';
  colorScheme?: string;
  variant?: string;
  mr?: number;
  onClick?: () => void;
}

export const IconButton: React.FC<IconButtonProps> = ({ 
  icon, 
  'aria-label': ariaLabel, 
  ...props 
}) => {
  return (
    <ChakraButton 
      aria-label={ariaLabel} 
      p={2} 
      display="inline-flex" 
      alignItems="center" 
      justifyContent="center"
      {...props as any}
    >
      {icon}
    </ChakraButton>
  );
};

// Custom toast hook
export function useToast() {
  return ({ 
    title, 
    description, 
    status, 
    duration, 
    isClosable 
  }: {
    title: string;
    description?: string;
    status?: 'info' | 'warning' | 'success' | 'error';
    duration?: number;
    isClosable?: boolean;
  }) => {
    console.log(`Toast: ${title} - ${description} (${status})`);
    // In a real implementation, you'd show a real toast
  };
} 