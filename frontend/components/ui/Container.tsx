import React from 'react';

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
  // Max width values mapped to Tailwind classes
  const maxWidthClasses = {
    xs: 'max-w-xs', // 320px
    sm: 'max-w-sm', // 640px
    md: 'max-w-md', // 768px
    lg: 'max-w-lg', // 1024px
    xl: 'max-w-xl', // 1280px
    full: 'max-w-full', // 100%
  };

  // Padding values mapped to Tailwind classes
  const paddingClasses = {
    none: 'p-0',
    small: 'px-2 py-2 md:px-3 md:py-3',
    medium: 'px-4 py-4 md:px-6 md:py-6',
    large: 'px-6 py-6 md:px-8 md:py-8',
  };

  return (
    <div
      id={id}
      className={`w-full mx-auto ${maxWidthClasses[maxWidth]} ${paddingClasses[padding]} ${className}`}
    >
      {children}
    </div>
  );
};

export default Container; 