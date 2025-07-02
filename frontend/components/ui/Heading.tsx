import React from 'react';

export interface HeadingProps {
  children: React.ReactNode;
  level?: 1 | 2 | 3 | 4 | 5 | 6;
  className?: string;
  [key: string]: any;
}

export const Heading: React.FC<HeadingProps> = ({ 
  children, 
  level = 1, 
  className = "", 
  ...props 
}) => {
  const Tag = `h${level}` as keyof JSX.IntrinsicElements;
  return <Tag className={`font-bold ${className}`} {...props}>{children}</Tag>;
};