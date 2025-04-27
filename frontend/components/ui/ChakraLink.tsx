import React from 'react';
import { Box } from '@chakra-ui/react';

interface LinkProps {
  children: React.ReactNode;
  href: string;
  color?: string;
  fontSize?: string;
}

export const Link: React.FC<LinkProps> = ({ children, href, color, fontSize }) => {
  return (
    <a 
      href={href}
      style={{ 
        color: color || 'inherit',
        fontSize: fontSize || 'inherit',
        textDecoration: 'none'
      }}
    >
      {children}
    </a>
  );
}; 