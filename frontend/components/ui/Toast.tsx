import React, { createContext, useContext, useState, useEffect } from 'react';
import { cva, type VariantProps } from 'class-variance-authority';
import { cn } from '../../utils/cn';
import { X, CheckCircle, XCircle, AlertTriangle, Info } from 'lucide-react';

// Toast variants
const toastVariants = cva(
  "pointer-events-auto relative w-full max-w-sm overflow-hidden rounded-lg shadow-lg p-4 flex items-start gap-3 border",
  {
    variants: {
      variant: {
        default: "bg-background border-border text-text-primary",
        success: "bg-success-light border-success text-success-dark",
        error: "bg-error-light border-error text-error-dark",
        warning: "bg-warning-light border-warning text-warning-dark",
        info: "bg-info-light border-info text-info-dark",
      },
    },
    defaultVariants: {
      variant: "default",
    },
  }
);

// Types for toast content
type ToastType = 'success' | 'error' | 'warning' | 'info' | 'default';

interface Toast {
  id: string;
  title: string;
  description?: string;
  type: ToastType;
  duration?: number;
  onClose?: () => void;
}

// Context for managing toasts
interface ToastContextType {
  toasts: Toast[];
  addToast: (toast: Omit<Toast, 'id'>) => void;
  removeToast: (id: string) => void;
}

const ToastContext = createContext<ToastContextType | undefined>(undefined);

export const useToast = () => {
  const context = useContext(ToastContext);
  if (!context) {
    throw new Error('useToast must be used within a ToastProvider');
  }
  
  // Simplified API that mimics Chakra's useToast
  return ({
    title,
    description,
    status = 'default',
    duration = 5000,
    isClosable = true,
    onClose,
  }: {
    title: string;
    description?: string;
    status?: 'success' | 'error' | 'warning' | 'info' | 'default';
    duration?: number;
    isClosable?: boolean;
    onClose?: () => void;
  }) => {
    context.addToast({
      title,
      description,
      type: status,
      duration,
      onClose,
    });
  };
};

// Individual Toast component
export interface ToastProps extends VariantProps<typeof toastVariants> {
  toast: Toast;
  onDismiss: (id: string) => void;
  className?: string;
}

export const ToastComponent: React.FC<ToastProps> = ({ toast, onDismiss, variant, className }) => {
  const iconMap = {
    success: <CheckCircle className="h-5 w-5" />,
    error: <XCircle className="h-5 w-5" />,
    warning: <AlertTriangle className="h-5 w-5" />,
    info: <Info className="h-5 w-5" />,
    default: null,
  };

  useEffect(() => {
    if (toast.duration) {
      const timer = setTimeout(() => {
        onDismiss(toast.id);
        if (toast.onClose) toast.onClose();
      }, toast.duration);
      
      return () => clearTimeout(timer);
    }
  }, [toast, onDismiss]);

  return (
    <div 
      className={cn(
        toastVariants({ variant: toast.type as any, className }),
        "animate-slide-in-up"
      )}
      role="alert"
      aria-live="assertive"
    >
      {iconMap[toast.type] && (
        <div className="flex-shrink-0">
          {iconMap[toast.type]}
        </div>
      )}
      
      <div className="flex-1 min-w-0">
        {toast.title && (
          <h4 className="font-medium text-sm mb-1">{toast.title}</h4>
        )}
        {toast.description && (
          <p className="text-sm opacity-90">{toast.description}</p>
        )}
      </div>
      
      <button
        onClick={() => {
          onDismiss(toast.id);
          if (toast.onClose) toast.onClose();
        }}
        className="ml-auto flex-shrink-0 inline-flex text-text-secondary hover:text-text-primary"
        aria-label="Close toast"
      >
        <X className="h-5 w-5" />
      </button>
    </div>
  );
};

// Toast container
export interface ToastContainerProps {
  position?: 'top-right' | 'top-left' | 'bottom-right' | 'bottom-left' | 'top-center' | 'bottom-center';
}

export const ToastContainer: React.FC<ToastContainerProps> = ({ 
  position = 'top-right', 
}) => {
  const { toasts, removeToast } = useContext(ToastContext) as ToastContextType;

  // Determine position classes
  const positionClasses = {
    'top-right': 'top-0 right-0',
    'top-left': 'top-0 left-0',
    'bottom-right': 'bottom-0 right-0',
    'bottom-left': 'bottom-0 left-0',
    'top-center': 'top-0 left-1/2 -translate-x-1/2',
    'bottom-center': 'bottom-0 left-1/2 -translate-x-1/2',
  };
  
  return (
    <div 
      className={`fixed z-50 p-4 flex flex-col gap-2 ${positionClasses[position]}`}
      aria-live="polite"
    >
      {toasts.map((toast) => (
        <ToastComponent 
          key={toast.id} 
          toast={toast} 
          onDismiss={removeToast} 
        />
      ))}
    </div>
  );
};

// Toast provider
export interface ToastProviderProps {
  children: React.ReactNode;
  position?: ToastContainerProps['position'];
}

export const ToastProvider: React.FC<ToastProviderProps> = ({ 
  children,
  position = 'top-right',
}) => {
  const [toasts, setToasts] = useState<Toast[]>([]);

  const addToast = (toast: Omit<Toast, 'id'>) => {
    const id = Math.random().toString(36).substring(2, 9);
    setToasts((prevToasts) => [...prevToasts, { id, ...toast }]);
  };

  const removeToast = (id: string) => {
    setToasts((prevToasts) => prevToasts.filter((toast) => toast.id !== id));
  };

  return (
    <ToastContext.Provider value={{ toasts, addToast, removeToast }}>
      {children}
      <ToastContainer position={position} />
    </ToastContext.Provider>
  );
};

export { ToastContext, toastVariants };
