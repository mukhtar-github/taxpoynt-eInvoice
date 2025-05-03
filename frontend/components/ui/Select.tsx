import React, { SelectHTMLAttributes, forwardRef } from 'react';
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

const Select = forwardRef<HTMLSelectElement, SelectProps>(
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

Select.displayName = "Select";

export { Select, selectVariants };
