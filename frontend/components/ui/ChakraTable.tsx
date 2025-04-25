import React from 'react';
import { Box } from '@chakra-ui/react';

interface TableProps {
  variant?: string;
  children: React.ReactNode;
}

export const Table: React.FC<TableProps> = ({ children, variant }) => {
  return (
    <Box as="table" width="100%" borderCollapse="collapse">
      {children}
    </Box>
  );
};

export const Thead: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  return <Box as="thead">{children}</Box>;
};

export const Tbody: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  return <Box as="tbody">{children}</Box>;
};

export const Tr: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  return <Box as="tr">{children}</Box>;
};

interface ThProps {
  children: React.ReactNode;
  textAlign?: 'left' | 'center' | 'right';
}

export const Th: React.FC<ThProps> = ({ children, textAlign = 'left' }) => {
  return (
    <Box 
      as="th" 
      p={3} 
      borderBottom="1px" 
      borderColor="gray.200" 
      textAlign={textAlign}
      fontWeight="bold"
    >
      {children}
    </Box>
  );
};

interface TdProps {
  children: React.ReactNode;
  fontWeight?: string;
}

export const Td: React.FC<TdProps> = ({ children, fontWeight }) => {
  return (
    <Box 
      as="td" 
      p={3} 
      borderBottom="1px" 
      borderColor="gray.100"
      fontWeight={fontWeight}
    >
      {children}
    </Box>
  );
}; 