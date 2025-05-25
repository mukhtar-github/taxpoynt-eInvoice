import React, { ReactNode } from 'react';
import { AlertCircle, CheckCircle, Info } from 'lucide-react';

interface AlertProps {
  children: ReactNode;
  variant?: 'default' | 'success' | 'error' | 'warning';
  className?: string;
}

interface AlertTitleProps {
  children: ReactNode;
  className?: string;
}

interface AlertDescriptionProps {
  children: ReactNode;
  className?: string;
}

export const Alert: React.FC<AlertProps> = ({
  children,
  variant = 'default',
  className = '',
}) => {
  const variantClasses = {
    default: 'bg-blue-50 border-blue-200 text-blue-800',
    success: 'bg-green-50 border-green-200 text-green-800',
    error: 'bg-red-50 border-red-200 text-red-800',
    warning: 'bg-yellow-50 border-yellow-200 text-yellow-800',
  };

  const IconComponent = {
    default: Info,
    success: CheckCircle,
    error: AlertCircle,
    warning: AlertCircle,
  }[variant];

  return (
    <div
      className={`flex items-start p-4 mb-4 border rounded-md ${variantClasses[variant]} ${className}`}
      role="alert"
    >
      <div className="flex items-start">
        <div className="flex-shrink-0 mr-3">
          <IconComponent size={20} />
        </div>
        <div>{children}</div>
      </div>
    </div>
  );
};

export const AlertTitle: React.FC<AlertTitleProps> = ({
  children,
  className = '',
}) => {
  return (
    <h5 className={`text-sm font-medium mb-1 ${className}`}>{children}</h5>
  );
};

export const AlertDescription: React.FC<AlertDescriptionProps> = ({
  children,
  className = '',
}) => {
  return <div className={`text-sm ${className}`}>{children}</div>;
};
