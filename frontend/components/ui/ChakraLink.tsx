/**
 * @deprecated This component is deprecated and will be removed in a future version.
 * Please use Next.js Link directly or Button with variant="link" for consistent styling.
 */

import React from 'react';
import NextLink from 'next/link';
import { cn } from '../../utils/cn';

/**
 * @deprecated Use Next.js Link component directly with Tailwind classes
 */
interface LinkProps {
  children: React.ReactNode;
  href: string;
  className?: string;
  variant?: 'default' | 'primary' | 'secondary' | 'destructive'; 
  external?: boolean;
  onClick?: () => void;
}

/**
 * @deprecated Use Next.js Link component directly with Tailwind classes or Button with variant="link"
 */
export const Link: React.FC<LinkProps> = ({ 
  children, 
  href, 
  className = '',
  variant = 'default',
  external = false,
  onClick
}) => {
  const baseStyles = 'inline-flex items-center transition-colors';
  
  const variantStyles = {
    default: 'text-text-primary hover:text-primary',
    primary: 'text-primary hover:text-primary-600 font-medium',
    secondary: 'text-text-secondary hover:text-text-primary',
    destructive: 'text-error hover:text-error-600'
  };
  
  const linkClass = cn(
    baseStyles,
    variantStyles[variant],
    className
  );
  
  // External links render as standard anchor tags
  if (external) {
    return (
      <a 
        href={href}
        className={linkClass}
        target="_blank"
        rel="noopener noreferrer"
        onClick={onClick}
      >
        {children}
      </a>
    );
  }
  
  // Internal links use Next.js Link component
  return (
    <NextLink 
      href={href} 
      className={linkClass}
      onClick={onClick}
    >
      {children}
    </NextLink>
  );
}; 