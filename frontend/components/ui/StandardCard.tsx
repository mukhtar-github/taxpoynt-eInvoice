import React from 'react';
import { Box, Flex, Text, BoxProps } from '@chakra-ui/react';

interface StandardCardProps extends BoxProps {
  children: React.ReactNode;
  title?: string;
  subtitle?: string;
  action?: React.ReactNode;
  variant?: 'default' | 'outlined' | 'elevated';
  noPadding?: boolean;
}

/**
 * StandardCard component with consistent 16px padding and designed for 24px spacing between cards
 * To ensure proper spacing, place cards in a grid with gap="24px" or margin="24px"
 */
export const StandardCard: React.FC<StandardCardProps> = ({
  children,
  title,
  subtitle,
  action,
  variant = 'default',
  noPadding = false,
  ...rest
}) => {
  // Card styling based on variant
  const cardStyles = {
    default: {
      bg: 'white',
      borderWidth: '1px',
      borderColor: 'var(--color-border)',
      borderRadius: 'var(--border-radius-lg)',
    },
    outlined: {
      bg: 'transparent',
      borderWidth: '1px',
      borderColor: 'var(--color-border)',
      borderRadius: 'var(--border-radius-lg)',
    },
    elevated: {
      bg: 'white',
      borderRadius: 'var(--border-radius-lg)',
      boxShadow: '0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06)',
    },
  };

  return (
    <Box
      {...cardStyles[variant]}
      p={noPadding ? 0 : 'var(--spacing-4)'}  // 16px padding
      {...rest}
    >
      {(title || subtitle || action) && (
        <Flex 
          justifyContent="space-between" 
          alignItems="center" 
          mb={children ? 'var(--spacing-4)' : 0}
          p={noPadding ? 'var(--spacing-4)' : 0}
        >
          <Box>
            {title && (
              <Text 
                fontSize="var(--font-size-lg)" 
                fontWeight="var(--font-weight-semibold)"
                lineHeight="var(--line-height-snug)"
              >
                {title}
              </Text>
            )}
            {subtitle && (
              <Text 
                fontSize="var(--font-size-sm)" 
                color="var(--color-text-secondary)"
                mt="var(--spacing-1)"
              >
                {subtitle}
              </Text>
            )}
          </Box>
          {action && (
            <Box>{action}</Box>
          )}
        </Flex>
      )}
      <Box p={noPadding && (title || subtitle || action) ? 'var(--spacing-4)' : 0}>
        {children}
      </Box>
    </Box>
  );
};

/**
 * CardGrid component for displaying multiple cards with consistent spacing
 */
interface CardGridProps extends BoxProps {
  children: React.ReactNode;
  columns?: { base?: number; sm?: number; md?: number; lg?: number; xl?: number };
}

export const CardGrid: React.FC<CardGridProps> = ({
  children,
  columns = { base: 1, md: 2, lg: 3 },
  ...rest
}) => {
  // Convert columns object to responsive template string
  const templateColumns = {
    base: `repeat(${columns.base || 1}, 1fr)`,
    sm: columns.sm ? `repeat(${columns.sm}, 1fr)` : undefined,
    md: columns.md ? `repeat(${columns.md}, 1fr)` : undefined,
    lg: columns.lg ? `repeat(${columns.lg}, 1fr)` : undefined,
    xl: columns.xl ? `repeat(${columns.xl}, 1fr)` : undefined,
  };

  return (
    <Box
      display="grid"
      gridTemplateColumns={templateColumns}
      gap="var(--spacing-6)" // 24px gap between cards
      width="100%"
      {...rest}
    >
      {children}
    </Box>
  );
};

export default StandardCard; 