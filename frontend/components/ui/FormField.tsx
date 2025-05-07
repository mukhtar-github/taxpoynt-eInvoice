import React, { ReactNode } from 'react';
import { cn } from '../../utils/cn';
import { Typography } from './Typography';

export interface FormFieldProps {
  children: ReactNode;
  label?: string;
  htmlFor?: string;
  helpText?: string;
  error?: boolean;
  errorMessage?: string;
  required?: boolean;
  className?: string;
}

/**
 * FormField component
 * 
 * A wrapper for form elements that provides consistent labeling, help text, and error handling
 * Used to create a standardized form layout throughout the application
 */
export const FormField: React.FC<FormFieldProps> = ({
  children,
  label,
  htmlFor,
  helpText,
  error = false,
  errorMessage,
  required = false,
  className,
}) => {
  return (
    <div className={cn('space-y-2', className)}>
      {label && (
        <Typography.Label 
          htmlFor={htmlFor} 
          required={required}
          variant={error ? 'secondary' : 'default'}
          className={cn(error && 'text-error')}
        >
          {label}
        </Typography.Label>
      )}
      
      {children}
      
      {helpText && !error && (
        <Typography.Text size="sm" variant="secondary" className="mt-1">
          {helpText}
        </Typography.Text>
      )}
      
      {error && errorMessage && (
        <Typography.Text size="sm" variant="error" className="mt-1">
          {errorMessage}
        </Typography.Text>
      )}
    </div>
  );
};

export default FormField;
