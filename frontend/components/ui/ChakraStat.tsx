import React from 'react';

interface StatProps {
  children: React.ReactNode;
}

export const Stat: React.FC<StatProps> = ({ children }) => {
  return (
    <div>
      {children}
    </div>
  );
};

interface StatLabelProps {
  children: React.ReactNode;
  fontSize?: string;
  color?: string;
}

export const StatLabel: React.FC<StatLabelProps> = ({ 
  children, 
  fontSize,
  color 
}) => {
  return (
    <div style={{ 
      fontSize: fontSize || 'inherit',
      color: color || 'inherit',
      marginBottom: '0.25rem'
    }}>
      {children}
    </div>
  );
};

interface StatNumberProps {
  children: React.ReactNode;
  fontSize?: string;
  fontWeight?: string;
}

export const StatNumber: React.FC<StatNumberProps> = ({
  children,
  fontSize,
  fontWeight
}) => {
  return (
    <div style={{ 
      fontSize: fontSize || '2rem',
      fontWeight: fontWeight || 'bold'
    }}>
      {children}
    </div>
  );
}; 