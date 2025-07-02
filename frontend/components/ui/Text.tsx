import React from 'react';

export interface TextProps {
  children: React.ReactNode;
  className?: string;
  [key: string]: any;
}

export const Text: React.FC<TextProps> = ({ 
  children, 
  className = "", 
  ...props 
}) => {
  return <p className={className} {...props}>{children}</p>;
};