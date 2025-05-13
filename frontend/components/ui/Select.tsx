import React, { SelectHTMLAttributes, forwardRef, HTMLAttributes, createContext, useContext, useState } from 'react';
import { cva, type VariantProps } from 'class-variance-authority';

const selectVariants = cva(
  "flex h-10 w-full rounded-md border border-border bg-background px-3 py-2 text-sm ring-offset-background focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary focus-visible:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50 appearance-none",
  {
    variants: {
      variant: {
        default: "",
        error: "border-error focus-visible:ring-error",
      },
      selectSize: {
        default: "h-10 px-3 py-2",
        sm: "h-8 px-2 py-1 text-xs",
        lg: "h-12 px-4 py-3 text-base",
      },
    },
    defaultVariants: {
      variant: "default",
      selectSize: "default",
    },
  }
);

export interface SelectProps
  extends SelectHTMLAttributes<HTMLSelectElement> {
  variant?: "default" | "error";
  selectSize?: "default" | "sm" | "lg";
  error?: boolean;
}

// Legacy basic Select component for backwards compatibility
const LegacySelect = forwardRef<HTMLSelectElement, SelectProps>(
  ({ className, variant, selectSize = "default", error, ...props }, ref) => {
    // Use error variant if error prop is true
    const selectVariant = error ? "error" : variant;
    
    return (
      <div className="relative">
        <select
          className={selectVariants({ variant: selectVariant, selectSize, className })}
          ref={ref}
          {...props}
        />
        <div className="pointer-events-none absolute inset-y-0 right-0 flex items-center pr-3">
          <svg 
            xmlns="http://www.w3.org/2000/svg" 
            width="16" 
            height="16" 
            viewBox="0 0 24 24" 
            fill="none" 
            stroke="currentColor" 
            strokeWidth="2" 
            strokeLinecap="round" 
            strokeLinejoin="round" 
            className="text-text-muted"
          >
            <path d="m6 9 6 6 6-6"/>
          </svg>
        </div>
      </div>
    );
  }
);

LegacySelect.displayName = "LegacySelect";

// Modern Select component that acts as a wrapper around SelectRoot
const Select = React.forwardRef<
  HTMLDivElement,
  { 
    children: React.ReactNode;
    value?: string;
    onValueChange?: (value: string) => void;
    defaultValue?: string;
    className?: string;
  }
>((props, ref) => {
  return <SelectRoot {...props} />;
});

Select.displayName = "Select";

// Create a context to manage the select state
type SelectContextType = {
  open: boolean;
  setOpen: (open: boolean) => void;
  value: string;
  onValueChange: (value: string) => void;
};

const SelectContext = createContext<SelectContextType | undefined>(undefined);

function useSelectContext() {
  const context = useContext(SelectContext);
  if (!context) {
    throw new Error('Select compound components must be used within a Select component');
  }
  return context;
}

// Enhanced Select components
function SelectRoot({ 
  children, 
  value, 
  onValueChange, 
  defaultValue 
}: { 
  children: React.ReactNode;
  value?: string;
  onValueChange?: (value: string) => void;
  defaultValue?: string;
}) {
  const [_value, _setValue] = useState<string>(defaultValue || '');
  const [open, setOpen] = useState(false);
  
  const handleValueChange = (newValue: string) => {
    if (onValueChange) {
      onValueChange(newValue);
    } else {
      _setValue(newValue);
    }
    setOpen(false);
  };
  
  return (
    <SelectContext.Provider value={{
      open,
      setOpen,
      value: value !== undefined ? value : _value,
      onValueChange: handleValueChange
    }}>
      {children}
    </SelectContext.Provider>
  );
}

function SelectTrigger({ 
  children, 
  className, 
  ...props 
}: HTMLAttributes<HTMLDivElement>) {
  const { open, setOpen, value } = useSelectContext();
  
  return (
    <div 
      className={`flex items-center justify-between h-10 w-full rounded-md border border-border bg-background px-3 py-2 text-sm ring-offset-background focus-visible:outline-none cursor-pointer ${className || ''}`}
      onClick={() => setOpen(!open)}
      {...props}
    >
      {children}
    </div>
  );
}

function SelectValue({ placeholder }: { placeholder: string }) {
  const { value } = useSelectContext();
  
  return (
    <span className="truncate">{value || placeholder}</span>
  );
}

function SelectContent({ 
  children, 
  className, 
  ...props 
}: HTMLAttributes<HTMLDivElement>) {
  const { open } = useSelectContext();
  
  if (!open) return null;
  
  return (
    <div 
      className={`absolute z-10 mt-1 w-full rounded-md border border-border bg-background shadow-lg ${className || ''}`}
      {...props}
    >
      <div className="py-1">
        {children}
      </div>
    </div>
  );
}

function SelectItem({ 
  children, 
  value, 
  className, 
  ...props 
}: HTMLAttributes<HTMLDivElement> & { value: string }) {
  const { onValueChange } = useSelectContext();
  
  return (
    <div 
      className={`px-3 py-2 hover:bg-muted cursor-pointer ${className || ''}`}
      onClick={() => onValueChange(value)}
      {...props}
    >
      {children}
    </div>
  );
}

export { Select, LegacySelect, selectVariants };
export { SelectRoot, SelectTrigger, SelectValue, SelectContent, SelectItem };
