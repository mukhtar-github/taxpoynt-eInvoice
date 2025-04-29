import React from 'react';

type Columns = 1 | 2 | 3 | 4 | 5 | 6 | 7 | 8 | 9 | 10 | 11 | 12;
type Breakpoints = 'sm' | 'md' | 'lg' | 'xl';

interface BreakpointProps {
  sm?: Columns;
  md?: Columns;
  lg?: Columns;
  xl?: Columns;
}

interface ContainerProps {
  children: React.ReactNode;
  className?: string;
  fluid?: boolean;
  style?: React.CSSProperties;
}

interface RowProps {
  children: React.ReactNode;
  className?: string;
  gap?: number; // gap in multiples of 4px (0.25rem)
  style?: React.CSSProperties;
}

interface ColProps extends BreakpointProps {
  children: React.ReactNode;
  className?: string;
  span?: Columns;
  style?: React.CSSProperties;
}

// Container component - provides max-width constraints at different breakpoints
export const Container: React.FC<ContainerProps> = ({ 
  children, 
  className = '', 
  fluid = false,
  style = {}
}) => {
  const maxWidthClass = fluid ? '' : 'max-w-screen-xl mx-auto';
  
  return (
    <div className={`px-4 md:px-6 lg:px-8 ${maxWidthClass} ${className}`} style={style}>
      {children}
    </div>
  );
};

// Row component - provides horizontal row with flexbox
export const Row: React.FC<RowProps> = ({ 
  children, 
  className = '', 
  gap = 4, // Default gap of 4 (16px)
  style = {}
}) => {
  // Convert gap to rem value (multiply by 0.25rem)
  const gapValue = `${gap * 0.25}rem`;
  
  return (
    <div 
      className={`flex flex-wrap -mx-${gap / 2} ${className}`}
      style={{ 
        display: 'flex', 
        flexWrap: 'wrap',
        margin: `0 -${Number(gap) * 0.125}rem`,
        ...style
      }}
    >
      {React.Children.map(children, child => (
        React.isValidElement(child) 
          ? React.cloneElement(child as React.ReactElement<any>, {
              style: {
                ...(child as React.ReactElement<any>).props.style,
                padding: `0 ${Number(gap) * 0.125}rem`
              }
            })
          : child
      ))}
    </div>
  );
};

// Column component - provides columns within a row
export const Col: React.FC<ColProps> = ({ 
  children, 
  className = '', 
  span = 12, // Default to full width
  sm,
  md, 
  lg,
  xl,
  style = {}
}) => {
  // Calculate column width as percentage
  const getColWidth = (columns: number) => `${(columns / 12) * 100}%`;
  
  // Create responsive styles
  const baseStyle: React.CSSProperties = {
    width: getColWidth(span),
    flexBasis: getColWidth(span),
    maxWidth: getColWidth(span),
    ...style
  };
  
  // Generate classes for media queries
  const getMediaQueryStyles = () => {
    const mediaQueries: { [key: string]: React.CSSProperties } = {};
    
    if (sm) {
      mediaQueries['@media (min-width: 640px)'] = {
        width: getColWidth(sm),
        flexBasis: getColWidth(sm),
        maxWidth: getColWidth(sm),
      };
    }
    
    if (md) {
      mediaQueries['@media (min-width: 768px)'] = {
        width: getColWidth(md),
        flexBasis: getColWidth(md),
        maxWidth: getColWidth(md),
      };
    }
    
    if (lg) {
      mediaQueries['@media (min-width: 1024px)'] = {
        width: getColWidth(lg),
        flexBasis: getColWidth(lg),
        maxWidth: getColWidth(lg),
      };
    }
    
    if (xl) {
      mediaQueries['@media (min-width: 1280px)'] = {
        width: getColWidth(xl),
        flexBasis: getColWidth(xl),
        maxWidth: getColWidth(xl),
      };
    }
    
    return mediaQueries;
  };
  
  return (
    <div 
      className={`col ${className}`}
      style={{
        ...baseStyle,
        ...getMediaQueryStyles()
      }}
    >
      {children}
    </div>
  );
};

// Grid component - provides a simple grid layout using CSS Grid
interface GridProps {
  children: React.ReactNode;
  columns?: number | BreakpointProps;
  gap?: number;
  className?: string;
  style?: React.CSSProperties;
}

export const Grid: React.FC<GridProps> = ({ 
  children, 
  columns = 12,
  gap = 4,
  className = '',
  style = {}
}) => {
  // Calculate grid columns
  const getGridTemplateColumns = () => {
    if (typeof columns === 'number') {
      return `repeat(${columns}, 1fr)`;
    }
    return 'repeat(1, 1fr)'; // Default to single column
  };
  
  // Convert gap to rem
  const gapValue = `${gap * 0.25}rem`;
  
  const baseStyle: React.CSSProperties = {
    display: 'grid',
    gridTemplateColumns: getGridTemplateColumns(),
    gap: gapValue,
    ...style
  };
  
  // Generate media query styles for responsive columns
  const getMediaQueryStyles = () => {
    if (typeof columns !== 'object') return {};
    
    const mediaQueries: { [key: string]: React.CSSProperties } = {};
    
    if (columns.sm) {
      mediaQueries['@media (min-width: 640px)'] = {
        gridTemplateColumns: `repeat(${columns.sm}, 1fr)`
      };
    }
    
    if (columns.md) {
      mediaQueries['@media (min-width: 768px)'] = {
        gridTemplateColumns: `repeat(${columns.md}, 1fr)`
      };
    }
    
    if (columns.lg) {
      mediaQueries['@media (min-width: 1024px)'] = {
        gridTemplateColumns: `repeat(${columns.lg}, 1fr)`
      };
    }
    
    if (columns.xl) {
      mediaQueries['@media (min-width: 1280px)'] = {
        gridTemplateColumns: `repeat(${columns.xl}, 1fr)`
      };
    }
    
    return mediaQueries;
  };
  
  return (
    <div 
      className={`grid ${className}`}
      style={{
        ...baseStyle,
        ...getMediaQueryStyles()
      }}
    >
      {children}
    </div>
  );
}; 