import React from 'react';

interface CardProps {
  children: React.ReactNode;
  className?: string;
  variant?: 'default' | 'outlined' | 'elevated';
  padding?: 'none' | 'small' | 'medium' | 'large';
  onClick?: () => void;
  style?: React.CSSProperties;
}

export const Card: React.FC<CardProps> = ({
  children,
  className = '',
  variant = 'default',
  padding = 'medium',
  onClick,
  style = {},
}) => {
  // Base styles
  const baseStyles = {
    borderRadius: 'var(--border-radius-lg)',
    backgroundColor: 'var(--color-white)',
    transition: 'box-shadow 0.2s ease, transform 0.2s ease',
  };

  // Variant-specific styles
  const variantStyles = {
    default: {
      border: '1px solid var(--color-border)',
    },
    outlined: {
      border: '1px solid var(--color-border)',
      boxShadow: 'none',
    },
    elevated: {
      border: 'none',
      boxShadow: '0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06)',
    },
  };

  // Padding styles
  const paddingStyles = {
    none: {
      padding: '0',
    },
    small: {
      padding: 'var(--spacing-2)',
    },
    medium: {
      padding: 'var(--spacing-4)',
    },
    large: {
      padding: 'var(--spacing-6)',
    },
  };

  // Interactive styles
  const hoverStyles = onClick ? {
    cursor: 'pointer',
    '&:hover': {
      transform: 'translateY(-2px)',
      boxShadow: '0 10px 15px -3px rgba(0, 0, 0, 0.1), 0 4px 6px -2px rgba(0, 0, 0, 0.05)',
    },
  } : {};

  return (
    <div
      className={`card ${className}`}
      style={{
        ...baseStyles,
        ...variantStyles[variant],
        ...paddingStyles[padding],
        ...style
      }}
      onClick={onClick}
    >
      {children}
    </div>
  );
};

interface CardHeaderProps {
  children?: React.ReactNode;
  className?: string;
  title?: string;
  subtitle?: string;
  action?: React.ReactNode;
}

export const CardHeader: React.FC<CardHeaderProps> = ({
  children,
  className = '',
  title,
  subtitle,
  action,
}) => {
  return (
    <div
      className={`card-header ${className}`}
      style={{
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        marginBottom: 'var(--spacing-4)',
      }}
    >
      <div>
        {title && (
          <h3
            style={{
              fontSize: 'var(--font-size-lg)',
              fontWeight: 'var(--font-weight-semibold)',
              margin: 0,
              marginBottom: subtitle ? 'var(--spacing-1)' : 0,
            }}
          >
            {title}
          </h3>
        )}
        {subtitle && (
          <p
            style={{
              fontSize: 'var(--font-size-sm)',
              color: 'var(--color-text-secondary)',
              margin: 0,
            }}
          >
            {subtitle}
          </p>
        )}
        {children}
      </div>
      {action && <div className="card-action">{action}</div>}
    </div>
  );
};

interface CardContentProps {
  children: React.ReactNode;
  className?: string;
}

export const CardContent: React.FC<CardContentProps> = ({
  children,
  className = '',
}) => {
  return (
    <div
      className={`card-content ${className}`}
    >
      {children}
    </div>
  );
};

interface CardFooterProps {
  children: React.ReactNode;
  className?: string;
  align?: 'left' | 'center' | 'right' | 'space-between';
}

export const CardFooter: React.FC<CardFooterProps> = ({
  children,
  className = '',
  align = 'left',
}) => {
  const alignStyles = {
    left: 'flex-start',
    center: 'center',
    right: 'flex-end',
    'space-between': 'space-between',
  };

  return (
    <div
      className={`card-footer ${className}`}
      style={{
        display: 'flex',
        alignItems: 'center',
        justifyContent: alignStyles[align],
        marginTop: 'var(--spacing-4)',
        paddingTop: 'var(--spacing-4)',
        borderTop: '1px solid var(--color-border)',
      }}
    >
      {children}
    </div>
  );
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
      padding="medium"
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