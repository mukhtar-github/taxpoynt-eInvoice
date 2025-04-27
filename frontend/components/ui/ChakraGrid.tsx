import React from 'react';

interface SimpleGridProps {
  children: React.ReactNode;
  columns: number | { base: number; md: number; lg?: number };
  spacing: number;
}

export const SimpleGrid: React.FC<SimpleGridProps> = ({ children, columns, spacing }) => {
  const getColumns = () => {
    if (typeof columns === 'number') {
      return columns;
    }
    
    // Simple responsive handling (this would be more sophisticated with media queries)
    return columns.md;
  };
  
  return (
    <div 
      style={{ 
        display: 'grid',
        gridTemplateColumns: `repeat(${getColumns()}, 1fr)`,
        gap: `${spacing * 4}px`,
      }}
    >
      {children}
    </div>
  );
}; 