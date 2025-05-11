import React, { Fragment } from 'react';
import { cva, type VariantProps } from 'class-variance-authority';
import { X } from 'lucide-react';
import { Button } from './Button';
import { cn } from '../../utils/cn';

// Define modal variants
const modalVariants = cva(
  "fixed inset-0 z-50 flex items-center justify-center p-4 sm:p-6",
  {
    variants: {
      position: {
        center: "items-center justify-center",
        top: "items-start justify-center",
        bottom: "items-end justify-center",
        left: "items-center justify-start",
        right: "items-center justify-end",
      },
    },
    defaultVariants: {
      position: "center",
    },
  }
);

// Define modal content variants
const modalContentVariants = cva(
  "bg-white rounded-lg shadow-lg relative flex flex-col w-full max-h-[90vh] overflow-hidden",
  {
    variants: {
      size: {
        sm: "max-w-sm",
        md: "max-w-md",
        lg: "max-w-lg",
        xl: "max-w-xl",
        "2xl": "max-w-2xl",
        "3xl": "max-w-3xl",
        "4xl": "max-w-4xl",
        "5xl": "max-w-5xl",
        full: "max-w-full",
      },
    },
    defaultVariants: {
      size: "md",
    },
  }
);

export interface ModalProps extends VariantProps<typeof modalVariants>, VariantProps<typeof modalContentVariants> {
  isOpen: boolean;
  onClose: () => void;
  children?: React.ReactNode;
  closeOnOverlayClick?: boolean;
  closeOnEsc?: boolean;
  hideCloseButton?: boolean;
  contentClassName?: string;
  overlayClassName?: string;
}

const Modal: React.FC<ModalProps> = ({
  isOpen,
  onClose,
  position,
  size,
  children,
  closeOnOverlayClick = true,
  closeOnEsc = true,
  hideCloseButton = false,
  contentClassName,
  overlayClassName,
}) => {
  if (!isOpen) return null;

  // Handle ESC key press
  React.useEffect(() => {
    const handleKeyDown = (event: KeyboardEvent) => {
      if (closeOnEsc && event.key === 'Escape') {
        onClose();
      }
    };

    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [closeOnEsc, onClose]);

  // Handle overlay click
  const handleOverlayClick = (e: React.MouseEvent<HTMLDivElement>) => {
    if (closeOnOverlayClick && e.target === e.currentTarget) {
      onClose();
    }
  };

  // Focus trap (accessibility)
  React.useEffect(() => {
    if (isOpen) {
      // Prevent scrolling on body
      document.body.style.overflow = 'hidden';
      
      // Focus the modal when it opens
      const modalElement = document.getElementById('modal-content');
      if (modalElement) {
        modalElement.focus();
      }
    }
    
    return () => {
      // Re-enable scrolling when modal closes
      document.body.style.overflow = '';
    };
  }, [isOpen]);

  return (
    <Fragment>
      {/* Backdrop */}
      <div 
        className={cn(
          "fixed inset-0 bg-black bg-opacity-50 transition-opacity duration-300", 
          overlayClassName
        )} 
      />
      
      {/* Modal container */}
      <div 
        className={modalVariants({ position })}
        onClick={handleOverlayClick}
        role="dialog"
        aria-modal="true"
        aria-labelledby="modal-title"
      >
        {/* Modal content */}
        <div 
          id="modal-content"
          className={modalContentVariants({ size, className: contentClassName })}
          tabIndex={-1}
        >
          {!hideCloseButton && (
            <Button
              className="absolute right-2 top-2 text-text-secondary hover:text-text-primary"
              size="icon"
              variant="ghost"
              onClick={onClose}
              aria-label="Close modal"
            >
              <X className="h-5 w-5" />
            </Button>
          )}
          
          {children}
        </div>
      </div>
    </Fragment>
  );
};

export interface ModalHeaderProps {
  children: React.ReactNode;
  className?: string;
}

export const ModalHeader: React.FC<ModalHeaderProps> = ({ children, className }) => (
  <div 
    className={cn("px-6 py-4 border-b border-border flex-shrink-0", className)}
    id="modal-title"
  >
    {typeof children === 'string' ? (
      <h2 className="text-xl font-semibold">{children}</h2>
    ) : (
      children
    )}
  </div>
);

export interface ModalBodyProps {
  children: React.ReactNode;
  className?: string;
}

export const ModalBody: React.FC<ModalBodyProps> = ({ children, className }) => (
  <div className={cn("p-6 overflow-auto flex-grow", className)}>
    {children}
  </div>
);

export interface ModalFooterProps {
  children: React.ReactNode;
  className?: string;
}

export const ModalFooter: React.FC<ModalFooterProps> = ({ children, className }) => (
  <div className={cn("px-6 py-4 border-t border-border flex justify-end gap-2 flex-shrink-0", className)}>
    {children}
  </div>
);

export { Modal, modalVariants, modalContentVariants };
export default Modal;
