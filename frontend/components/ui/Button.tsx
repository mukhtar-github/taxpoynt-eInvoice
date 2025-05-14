import React, { forwardRef, ButtonHTMLAttributes } from 'react';
import { cva, type VariantProps } from 'class-variance-authority';

// Define button variants using class-variance-authority
const buttonVariants = cva(
  // Base styles applied to all buttons
  "inline-flex items-center justify-center rounded-md text-sm font-medium transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary focus-visible:ring-offset-2 disabled:opacity-50 disabled:pointer-events-none shadow-sm",
  {
    variants: {
      variant: {
        default: "bg-primary text-white hover:bg-primary-dark font-semibold",
        destructive: "bg-error text-white hover:bg-error/90 font-semibold",
        outline: "border border-border bg-background hover:bg-background-alt text-text-primary font-medium",
        secondary: "bg-background-alt text-text-primary hover:bg-background-alt/80 font-medium",
        ghost: "hover:bg-background-alt hover:text-text-primary text-text-primary",
        link: "text-primary underline-offset-4 hover:underline font-medium",
      },
      size: {
        default: "h-10 py-2 px-4",
        sm: "h-9 px-3 rounded-md",
        lg: "h-11 px-8 rounded-md",
        icon: "h-10 w-10",
      },
    },
    defaultVariants: {
      variant: "default",
      size: "default",
    },
  }
);

// Define props interface with HTMLButton attributes and variant props
export interface ButtonProps 
  extends ButtonHTMLAttributes<HTMLButtonElement>,
    VariantProps<typeof buttonVariants> {
  asChild?: boolean;
  loading?: boolean;
}

// Create button component with forwarded ref
const Button = forwardRef<HTMLButtonElement, ButtonProps>(
  ({ className, variant, size, asChild = false, loading = false, ...props }, ref) => {
    return (
      <button
        className={buttonVariants({ variant, size, className })}
        ref={ref}
        disabled={loading || props.disabled}
        {...props}
      >
        {loading ? (
          <span className="mr-2 inline-block h-4 w-4 animate-spin rounded-full border-2 border-solid border-current border-r-transparent align-[-0.125em] motion-reduce:animate-[spin_1.5s_linear_infinite]"></span>
        ) : null}
        {props.children}
      </button>
    );
  }
);

Button.displayName = "Button";

export { Button, buttonVariants }; 