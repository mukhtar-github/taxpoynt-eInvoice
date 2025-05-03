import React, { InputHTMLAttributes, forwardRef } from 'react';
import { cva, type VariantProps } from 'class-variance-authority';

const inputVariants = cva(
  "flex h-10 w-full rounded-md border border-border bg-background px-3 py-2 text-sm ring-offset-background file:border-0 file:bg-transparent file:text-sm file:font-medium placeholder:text-text-muted focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary focus-visible:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50",
  {
    variants: {
      variant: {
        default: "",
        error: "border-error focus-visible:ring-error",
      },
      size: {
        default: "h-10 px-3 py-2",
        sm: "h-8 px-2 py-1 text-xs",
        lg: "h-12 px-4 py-3 text-base",
      },
    },
    defaultVariants: {
      variant: "default",
      size: "default",
    },
  }
);

export interface InputProps
  extends Omit<InputHTMLAttributes<HTMLInputElement>, 'size'>,
    VariantProps<typeof inputVariants> {
  error?: boolean;
}

const Input = forwardRef<HTMLInputElement, InputProps>(
  ({ className, variant, size, error, ...props }, ref) => {
    // Use error variant if error prop is true
    const inputVariant = error ? "error" : variant;
    
    return (
      <input
        className={inputVariants({ variant: inputVariant, size, className })}
        ref={ref}
        {...props}
      />
    );
  }
);

Input.displayName = "Input";

export { Input, inputVariants };
