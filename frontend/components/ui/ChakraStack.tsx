import React from 'react';

interface StackProps {
  children: React.ReactNode;
  spacing?: string | number | { base: string; md: string };
  direction?: 'row' | 'column';
  align?: string;
  justify?: string;
}

const getSpacing = (spacing: any) => {
  if (typeof spacing === 'number') {
    return `${spacing * 0.25}rem`;
  }
  if (typeof spacing === 'string') {
    return spacing;
  }
  
  // For responsive values, use the md value (simplification)
  if (spacing && typeof spacing === 'object' && spacing.md) {
    return spacing.md;
  }
  
  return '0';
};

export const HStack: React.FC<StackProps> = ({
  children,
  spacing = '0.5rem',
  align = 'center',
  justify = 'flex-start'
}) => {
  const gap = getSpacing(spacing);
  
  return (
    <div
      style={{
        display: 'flex',
        flexDirection: 'row',
        alignItems: align,
        justifyContent: justify,
        gap
      }}
    >
      {children}
    </div>
  );
};

export const VStack: React.FC<StackProps> = ({
  children,
  spacing = '0.5rem',
  align = 'stretch',
  justify = 'flex-start'
}) => {
  const gap = getSpacing(spacing);
  
  return (
    <div
      style={{
        display: 'flex',
        flexDirection: 'column',
        alignItems: align,
        justifyContent: justify,
        gap
      }}
    >
      {children}
    </div>
  );
}; 