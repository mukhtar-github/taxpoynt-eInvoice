import React, { HTMLAttributes, forwardRef } from 'react';
import { cva, type VariantProps } from 'class-variance-authority';

// Define card variants using class-variance-authority
const cardVariants = cva(
  "rounded-lg border border-border bg-white shadow-sm",
  {
    variants: {
      variant: {
        default: "p-4",
        compact: "p-3",
        spacious: "p-6",
        elevated: "p-4 shadow-md border-none",
      },
    },
    defaultVariants: {
      variant: "default",
    },
  }
);

export interface CardProps 
  extends HTMLAttributes<HTMLDivElement>,
    VariantProps<typeof cardVariants> {}

const Card = forwardRef<HTMLDivElement, CardProps>(
  ({ className, variant, ...props }, ref) => {
    return (
      <div
        className={cardVariants({ variant, className })}
        ref={ref}
        {...props}
      />
    );
  }
);
Card.displayName = "Card";

// Card Header component
interface CardHeaderProps extends HTMLAttributes<HTMLDivElement> {
  title?: string;
  subtitle?: string;
  action?: React.ReactNode;
}

const CardHeader = forwardRef<
  HTMLDivElement, 
  CardHeaderProps
>(({ className, title, subtitle, action, ...props }, ref) => (
  <div
    ref={ref}
    className={`flex flex-col space-y-1.5 pb-4 ${className || ''}`}
    {...props}
  >
    {title && <CardTitle>{title}</CardTitle>}
    {subtitle && <CardDescription>{subtitle}</CardDescription>}
    {action && (
      <div className="mt-2">
        {action}
      </div>
    )}
    {props.children}
  </div>
));
CardHeader.displayName = "CardHeader";

// Card Title component
const CardTitle = forwardRef<
  HTMLParagraphElement,
  HTMLAttributes<HTMLHeadingElement>
>(({ className, ...props }, ref) => (
  <h3
    ref={ref}
    className={`font-semibold text-xl text-text-primary ${className || ''}`}
    {...props}
  />
));
CardTitle.displayName = "CardTitle";

// Card Description component
const CardDescription = forwardRef<
  HTMLParagraphElement,
  HTMLAttributes<HTMLParagraphElement>
>(({ className, ...props }, ref) => (
  <p
    ref={ref}
    className={`text-sm text-text-secondary ${className || ''}`}
    {...props}
  />
));
CardDescription.displayName = "CardDescription";

// Card Content component
const CardContent = forwardRef<
  HTMLDivElement,
  HTMLAttributes<HTMLDivElement>
>(({ className, ...props }, ref) => (
  <div ref={ref} className={`py-2 ${className || ''}`} {...props} />
));
CardContent.displayName = "CardContent";

// Card Footer component
const CardFooter = forwardRef<
  HTMLDivElement,
  HTMLAttributes<HTMLDivElement>
>(({ className, ...props }, ref) => (
  <div
    ref={ref}
    className={`flex items-center pt-4 ${className || ''}`}
    {...props}
  />
));
CardFooter.displayName = "CardFooter";

// Helper component to organize multiple cards with 24px gap
export const CardGrid = forwardRef<
  HTMLDivElement,
  HTMLAttributes<HTMLDivElement> & {
    columns?: { base?: number; sm?: number; md?: number; lg?: number; xl?: number }
  }
>(({ className, columns = { base: 1, md: 2, lg: 3 }, ...props }, ref) => {
  const getGridCols = () => {
    return `grid-cols-${columns.base || 1} ${
      columns.sm ? `sm:grid-cols-${columns.sm}` : ''
    } ${
      columns.md ? `md:grid-cols-${columns.md}` : ''
    } ${
      columns.lg ? `lg:grid-cols-${columns.lg}` : ''
    } ${
      columns.xl ? `xl:grid-cols-${columns.xl}` : ''
    }`;
  };

  return (
    <div 
      ref={ref}
      className={`grid ${getGridCols()} gap-6 w-full ${className || ''}`}
      {...props}
    />
  );
});
CardGrid.displayName = "CardGrid";

export { 
  Card, 
  CardHeader, 
  CardTitle, 
  CardDescription, 
  CardContent, 
  CardFooter 
};

// Metric Card - specialized card for dashboard metrics
interface MetricCardProps {
  title: string;
  value: string | number;
  icon?: React.ReactNode;
  change?: {
    value: string | number;
    type: 'increase' | 'decrease' | 'neutral';
  };
  footer?: React.ReactNode;
  className?: string;
  onClick?: () => void;
}

export const MetricCard: React.FC<MetricCardProps> = ({
  title,
  value,
  icon,
  change,
  footer,
  className = '',
  onClick,
}) => {
  const changeColors = {
    increase: 'var(--color-success)',
    decrease: 'var(--color-error)',
    neutral: 'var(--color-text-secondary)',
  };

  const changeIcons = {
    increase: '↑',
    decrease: '↓',
    neutral: '→',
  };

  return (
    <Card 
      className={className} 
      variant="elevated" 
      onClick={onClick}
    >
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
        <div>
          <h3 style={{ 
            fontSize: 'var(--font-size-sm)', 
            color: 'var(--color-text-secondary)',
            margin: 0,
            marginBottom: 'var(--spacing-2)',
            fontWeight: 'var(--font-weight-medium)'
          }}>
            {title}
          </h3>
          <div style={{ 
            fontSize: 'var(--font-size-3xl)',
            fontWeight: 'var(--font-weight-semibold)',
            lineHeight: 'var(--line-height-tight)',
            marginBottom: change ? 'var(--spacing-1)' : 0
          }}>
            {value}
          </div>
          
          {change && (
            <div style={{ 
              display: 'flex', 
              alignItems: 'center',
              color: changeColors[change.type],
              fontSize: 'var(--font-size-sm)'
            }}>
              <span style={{ marginRight: 'var(--spacing-1)' }}>
                {changeIcons[change.type]}
              </span>
              {change.value}
            </div>
          )}
        </div>
        
        {icon && (
          <div style={{ 
            backgroundColor: 'var(--color-background-alt)',
            padding: 'var(--spacing-2)',
            borderRadius: 'var(--border-radius-md)'
          }}>
            {icon}
          </div>
        )}
      </div>
      
      {footer && (
        <CardFooter>
          {footer}
        </CardFooter>
      )}
    </Card>
  );
}; 