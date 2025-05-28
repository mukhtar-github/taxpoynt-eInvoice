import React from 'react';
import { X, AlertCircle } from 'lucide-react';

interface ErrorAlertProps extends React.HTMLAttributes<HTMLDivElement> {
  message: string;
  onClose?: () => void;
  className?: string;
}

const ErrorAlert: React.FC<ErrorAlertProps> = ({ 
  message, 
  onClose, 
  className = '',
  ...props 
}) => {
  return (
    <div 
      className={`flex items-center justify-between p-4 rounded-md bg-red-50 border border-red-200 text-red-800 ${className}`}
      role="alert"
      {...props}
    >
      <div className="flex items-center space-x-3">
        <AlertCircle className="h-5 w-5 text-red-500" aria-hidden="true" />
        <span className="text-sm">{message}</span>
      </div>
      {onClose && (
        <button
          type="button"
          onClick={onClose}
          className="ml-auto -mx-1.5 -my-1.5 bg-red-50 text-red-500 rounded-lg focus:ring-2 focus:ring-red-400 p-1.5 hover:bg-red-100 inline-flex items-center justify-center h-8 w-8"
          aria-label="Close"
        >
          <span className="sr-only">Close</span>
          <X className="h-4 w-4" aria-hidden="true" />
        </button>
      )}
    </div>
  );
};

export default ErrorAlert;
