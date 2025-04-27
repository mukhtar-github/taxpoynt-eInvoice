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
  display?: any;
}

export const IconButton: React.FC<IconButtonProps> = ({ 
  icon, 
  'aria-label': ariaLabel, 
  size = 'md',
  colorScheme = 'gray',
  variant = 'solid',
  ...props 
}) => {
  // Size mapping
  const sizeMap = {
    xs: { padding: '0.25rem', fontSize: '0.75rem' },
    sm: { padding: '0.5rem', fontSize: '0.875rem' },
    md: { padding: '0.75rem', fontSize: '1rem' },
    lg: { padding: '1rem', fontSize: '1.25rem' },
    xl: { padding: '1.25rem', fontSize: '1.5rem' }
  };
  
  // Variant mapping
  const getVariantStyles = () => {
    switch (variant) {
      case 'outline':
        return {
          border: '1px solid',
          borderColor: `${colorScheme}.500`,
          backgroundColor: 'transparent'
        };
      case 'ghost':
        return {
          backgroundColor: 'transparent'
        };
      default:
        return {
          backgroundColor: `${colorScheme}.500`,
          color: 'white'
        };
    }
  };
  
  const { padding, fontSize } = sizeMap[size];
  
  return (
    <button 
      aria-label={ariaLabel} 
      style={{
        display: 'inline-flex',
        alignItems: 'center',
        justifyContent: 'center',
        padding,
        fontSize,
        borderRadius: '0.375rem',
        border: 'none',
        cursor: 'pointer',
        ...getVariantStyles(),
        ...props.display && { display: props.display },
        marginRight: props.mr ? `${props.mr * 0.25}rem` : undefined
      }}
      onClick={props.onClick}
    >
      {icon}
    </button>
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