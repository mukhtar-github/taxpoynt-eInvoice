import React from 'react';

interface IconProps {
  as: React.ElementType;
  boxSize?: string;
  mr?: string;
  fontSize?: string;
}

export const Icon: React.FC<IconProps> = ({ 
  as: IconComponent, 
  boxSize = '1em',
  mr,
  fontSize,
  ...rest
}) => {
  const size = fontSize || boxSize;
  
  return (
    <span 
      style={{ 
        display: 'inline-flex',
        marginRight: mr,
        fontSize: size,
        width: size,
        height: size
      }}
      {...rest}
    >
      <IconComponent style={{ width: '100%', height: '100%' }} />
    </span>
  );
}; 