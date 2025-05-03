import React, { forwardRef } from 'react';
import { cn } from '../../utils/cn';
import { Button, ButtonProps } from './Button';
import { LucideProps } from 'lucide-react';

interface IconButtonProps extends ButtonProps {
  icon: React.ComponentType<LucideProps>;
  iconPosition?: 'left' | 'right';
  iconSize?: number;
  iconClassName?: string;
}

const IconButton = forwardRef<HTMLButtonElement, IconButtonProps>(
  ({ 
    className, 
    children, 
    icon: Icon, 
    iconPosition = 'left', 
    iconSize = 16, 
    iconClassName,
    ...props 
  }, ref) => {
    return (
      <Button
        ref={ref}
        className={cn(
          "inline-flex items-center gap-2",
          className
        )}
        {...props}
      >
        {iconPosition === 'left' && (
          <Icon 
            size={iconSize} 
            className={cn("shrink-0", iconClassName)} 
            aria-hidden="true" 
          />
        )}
        {children}
        {iconPosition === 'right' && (
          <Icon 
            size={iconSize} 
            className={cn("shrink-0", iconClassName)} 
            aria-hidden="true" 
          />
        )}
      </Button>
    );
  }
);

IconButton.displayName = "IconButton";

export { IconButton }; 