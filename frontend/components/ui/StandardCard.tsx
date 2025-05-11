/**
 * @deprecated This component is deprecated and will be removed in a future version.
 * Please use components from '../ui/Card.tsx' for consistent styling.
 * 
 * Migration guide:
 * - StandardCard -> Card with CardHeader and CardContent
 * - CardGrid -> Use CSS Grid with Tailwind (grid grid-cols-X gap-6)
 */

import React from 'react';
import { cn } from '../../utils/cn';
import { Typography } from './Typography';

/**
 * @deprecated Use Card, CardHeader, and CardContent from '../ui/Card.tsx' instead
 */
interface StandardCardProps extends React.HTMLAttributes<HTMLDivElement> {
  children: React.ReactNode;
  title?: string;
  subtitle?: string;
  action?: React.ReactNode;
  variant?: 'default' | 'outlined' | 'elevated';
  noPadding?: boolean;
  className?: string;
}

/**
 * StandardCard component with consistent 16px padding and designed for 24px spacing between cards
 * To ensure proper spacing, place cards in a grid with gap-6 (24px) or m-6
 */
/**
 * @deprecated Use Card, CardHeader, and CardContent from '../ui/Card.tsx' instead
 */
export const StandardCard: React.FC<StandardCardProps> = ({
  children,
  title,
  subtitle,
  action,
  variant = 'default',
  noPadding = false,
  className,
  ...rest
}) => {
  // Card styling based on variant
  const variantStyles = {
    default: 'bg-white border border-border rounded-lg',
    outlined: 'bg-transparent border border-border rounded-lg',
    elevated: 'bg-white rounded-lg shadow-md'
  };

  return (
    <div
      className={cn(
        variantStyles[variant],
        noPadding ? '' : 'p-4',
        className
      )}
      {...rest}
    >
      {(title || subtitle || action) && (
        <div 
          className={cn(
            'flex justify-between items-center',
            children ? 'mb-4' : '',
            noPadding ? 'p-4' : ''
          )}
        >
          <div>
            {title && (
              <Typography.Text 
                size="lg" 
                weight="semibold"
                className="leading-snug"
              >
                {title}
              </Typography.Text>
            )}
            {subtitle && (
              <Typography.Text 
                size="sm" 
                variant="secondary"
                className="mt-1"
              >
                {subtitle}
              </Typography.Text>
            )}
          </div>
          {action && (
            <div>{action}</div>
          )}
        </div>
      )}
      <div className={noPadding && (title || subtitle || action) ? 'p-4' : ''}>
        {children}
      </div>
    </div>
  );
};

/**
 * CardGrid component for displaying multiple cards with consistent spacing
 */
/**
 * @deprecated Use Tailwind grid classes directly (e.g., 'grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6')
 */
interface CardGridProps extends React.HTMLAttributes<HTMLDivElement> {
  children: React.ReactNode;
  columns?: { base?: number; sm?: number; md?: number; lg?: number; xl?: number };
  className?: string;
}

/**
 * @deprecated Use Tailwind grid classes directly (e.g., 'grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6')
 */
export const CardGrid: React.FC<CardGridProps> = ({
  children,
  columns = { base: 1, md: 2, lg: 3 },
  className,
  ...rest
}) => {
  // Create responsive grid classes
  const gridClasses = [
    `grid-cols-${columns.base || 1}`,
    columns.sm && `sm:grid-cols-${columns.sm}`,
    columns.md && `md:grid-cols-${columns.md}`,
    columns.lg && `lg:grid-cols-${columns.lg}`,
    columns.xl && `xl:grid-cols-${columns.xl}`,
  ].filter(Boolean);

  return (
    <div
      className={cn(
        'grid gap-6 w-full',
        gridClasses,
        className
      )}
      {...rest}
    >
      {children}
    </div>
  );
};

export default StandardCard; 