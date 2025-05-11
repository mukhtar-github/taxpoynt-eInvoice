/**
 * @deprecated These components are deprecated and will be removed in a future version.
 * Please use the Tailwind versions from '../ui/Table.tsx' instead.
 * 
 * Migration guide:
 * - Table -> Table
 * - Thead -> TableHeader
 * - Tbody -> TableBody
 * - Tr -> TableRow
 * - Th -> TableHead
 * - Td -> TableCell
 */

import React from 'react';
import { cn } from '../../utils/cn';

/**
 * @deprecated Use Table from '../ui/Table.tsx' instead
 */
interface TableProps extends React.HTMLAttributes<HTMLTableElement> {
  variant?: 'default' | 'simple';
  className?: string;
  children: React.ReactNode;
}

/**
 * @deprecated Use Table from '../ui/Table.tsx' instead
 */
export const Table: React.FC<TableProps> = ({ 
  children, 
  variant = 'default',
  className,
  ...props 
}) => {
  return (
    <table 
      className={cn(
        'w-full border-collapse',
        variant === 'simple' ? 'table-simple' : 'table-default',
        className
      )}
      {...props}
    >
      {children}
    </table>
  );
};

/**
 * @deprecated Use TableHeader from '../ui/Table.tsx' instead
 */
interface TheadProps extends React.HTMLAttributes<HTMLTableSectionElement> {
  className?: string;
  children: React.ReactNode;
}

/**
 * @deprecated Use TableHeader from '../ui/Table.tsx' instead
 */
export const Thead: React.FC<TheadProps> = ({ children, className, ...props }) => {
  return <thead className={className} {...props}>{children}</thead>;
};

/**
 * @deprecated Use TableBody from '../ui/Table.tsx' instead
 */
interface TbodyProps extends React.HTMLAttributes<HTMLTableSectionElement> {
  className?: string;
  children: React.ReactNode;
}

/**
 * @deprecated Use TableBody from '../ui/Table.tsx' instead
 */
export const Tbody: React.FC<TbodyProps> = ({ children, className, ...props }) => {
  return <tbody className={className} {...props}>{children}</tbody>;
};

/**
 * @deprecated Use TableRow from '../ui/Table.tsx' instead
 */
interface TrProps extends React.HTMLAttributes<HTMLTableRowElement> {
  className?: string;
  children: React.ReactNode;
}

/**
 * @deprecated Use TableRow from '../ui/Table.tsx' instead
 */
export const Tr: React.FC<TrProps> = ({ children, className, ...props }) => {
  return <tr className={className} {...props}>{children}</tr>;
};

/**
 * @deprecated Use TableHead from '../ui/Table.tsx' instead
 */
interface ThProps extends React.ThHTMLAttributes<HTMLTableCellElement> {
  children: React.ReactNode;
  textAlign?: 'left' | 'center' | 'right';
  className?: string;
}

/**
 * @deprecated Use TableHead from '../ui/Table.tsx' instead
 */
export const Th: React.FC<ThProps> = ({ 
  children, 
  textAlign = 'left',
  className,
  ...props 
}) => {
  return (
    <th 
      className={cn(
        'p-3 border-b border-gray-200 font-semibold',
        textAlign === 'left' ? 'text-left' : 
        textAlign === 'center' ? 'text-center' : 'text-right',
        className
      )}
      {...props}
    >
      {children}
    </th>
  );
};

/**
 * @deprecated Use TableCell from '../ui/Table.tsx' instead
 */
interface TdProps extends React.TdHTMLAttributes<HTMLTableCellElement> {
  children: React.ReactNode;
  fontWeight?: 'normal' | 'medium' | 'semibold' | 'bold';
  className?: string;
}

/**
 * @deprecated Use TableCell from '../ui/Table.tsx' instead
 */
export const Td: React.FC<TdProps> = ({ 
  children, 
  fontWeight = 'normal',
  className,
  ...props 
}) => {
  const fontWeightClasses = {
    normal: 'font-normal',
    medium: 'font-medium',
    semibold: 'font-semibold',
    bold: 'font-bold'
  };

  return (
    <td 
      className={cn(
        'p-3 border-b border-gray-100',
        fontWeightClasses[fontWeight],
        className
      )}
      {...props}
    >
      {children}
    </td>
  );
}; 