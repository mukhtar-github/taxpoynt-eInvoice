import React from 'react';
import { Box } from '@chakra-ui/react';

interface ContainerProps {
  children: React.ReactNode;
  maxWidth?: 'xs' | 'sm' | 'md' | 'lg' | 'xl' | 'full';
  padding?: 'none' | 'small' | 'medium' | 'large';
  className?: string;
  id?: string;
}

/**
 * A responsive container component with consistent padding across screen sizes.
 * Mobile-first design with customizable max-width and padding options.
 */
export const Container: React.FC<ContainerProps> = ({
  children,
  maxWidth = 'lg',
  padding = 'medium',
  className = '',
  id,
}) => {
  // Max width values in pixels
  const maxWidthValues = {
    xs: '320px',
    sm: '640px',
    md: '768px',
    lg: '1024px',
    xl: '1280px',
    full: '100%',
  };

  // Responsive padding values
  const paddingValues = {
    none: { base: '0', md: '0' },
    small: { base: 'var(--spacing-2)', md: 'var(--spacing-3)' },
    medium: { base: 'var(--spacing-4)', md: 'var(--spacing-6)' },
    large: { base: 'var(--spacing-6)', md: 'var(--spacing-8)' },
  };

  return (
    <Box
      id={id}
      className={`container ${className}`}
      width="100%"
      maxWidth={maxWidthValues[maxWidth]}
      marginX="auto"
      paddingX={paddingValues[padding]}
      paddingY={paddingValues[padding]}
    >
      {children}
    </Box>
  );
};

export default Container; 