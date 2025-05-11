/**
 * @deprecated These components are deprecated and will be removed in a future version.
 * Please use components from '../ui/Button.tsx' directly for consistent styling.
 * 
 * Migration guide:
 * - Button -> Button
 * - IconButton -> Button with size="icon" and appropriate icon as children
 */

import React from 'react';
import { Button as TailwindButton } from './Button';
import { cn } from '../../utils/cn';

/**
 * @deprecated Use Button from '../ui/Button.tsx' directly
 */
interface ChakraButtonProps {
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
  className?: string;
}

// This is a compatibility layer for the old Chakra Button
// It maps Chakra props to our new Tailwind Button component
/**
 * @deprecated Use Button from '../ui/Button.tsx' directly
 */
export const Button: React.FC<ChakraButtonProps> = ({ 
  leftIcon, 
  children, 
  colorScheme = 'blue',
  variant = 'solid',
  size = 'md',
  isLoading,
  onClick,
  type,
  width,
  mt,
  className,
  ...props 
}) => {
  // Map Chakra variants to Tailwind Button variants
  const variantMap: Record<string, any> = {
    solid: colorScheme === 'red' ? 'destructive' : 'primary',
    outline: 'outline',
    ghost: 'ghost',
    link: 'link',
  };

  // Map Chakra sizes to Tailwind Button sizes
  const sizeMap: Record<string, any> = {
    xs: 'xs',
    sm: 'sm',
    md: 'default',
    lg: 'lg',
    xl: 'xl',
  };

  const mappedVariant = variantMap[variant] || 'primary';
  const mappedSize = sizeMap[size] || 'default';
  
  return (
    <TailwindButton
      variant={mappedVariant}
      size={mappedSize}
      loading={isLoading}
      onClick={onClick}
      type={type}
      className={cn(
        width && `w-${width}`,
        mt && `mt-${mt}`,
        className
      )}
      {...props}
    >
      {leftIcon && <span className="mr-2 inline-flex">{leftIcon}</span>}
      {children}
    </TailwindButton>
  );
};

/**
 * @deprecated Use Button with size="icon" from '../ui/Button.tsx' instead
 */
interface IconButtonProps {
  'aria-label': string;
  icon: React.ReactElement;
  size?: 'xs' | 'sm' | 'md' | 'lg' | 'xl';
  colorScheme?: string;
  variant?: string;
  mr?: number;
  onClick?: () => void;
  display?: any;
  className?: string;
}

// This is a compatibility layer for the old Chakra IconButton
/**
 * @deprecated Use Button with size="icon" from '../ui/Button.tsx' instead
 */
export const IconButton: React.FC<IconButtonProps> = ({ 
  icon, 
  'aria-label': ariaLabel, 
  size = 'md',
  colorScheme = 'gray',
  variant = 'solid',
  mr,
  onClick,
  display,
  className,
  ...props 
}) => {
  // Map Chakra variants to Tailwind Button variants
  const variantMap: Record<string, any> = {
    solid: colorScheme === 'red' ? 'destructive' : 'primary',
    outline: 'outline',
    ghost: 'ghost',
    link: 'link',
  };

  // Map Chakra sizes to Tailwind Button sizes
  const sizeMap: Record<string, any> = {
    xs: 'xs',
    sm: 'sm',
    md: 'default',
    lg: 'lg',
    xl: 'xl',
  };

  const mappedVariant = variantMap[variant] || 'primary';
  const mappedSize = sizeMap[size] || 'default';
  
  return (
    <TailwindButton
      variant={mappedVariant}
      size={mappedSize}
      onClick={onClick}
      type="button"
      aria-label={ariaLabel}
      className={cn(
        'p-0',
        mr && `mr-${mr}`,
        display && display !== 'inline-flex' ? display : '',
        className
      )}
      {...props}
    >
      {icon}
    </TailwindButton>
  );
};

// Redirect to our custom toast implementation
export { useToast } from './Toast';