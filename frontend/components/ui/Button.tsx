import React, { forwardRef, ButtonHTMLAttributes } from 'react';
import { cva, type VariantProps } from 'class-variance-authority';

// Define button variants using class-variance-authority
const buttonVariants = cva(
  // Base styles applied to all buttons - Enhanced with mobile-first approach
  "inline-flex items-center justify-center rounded-md text-sm font-medium transition-all duration-200 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary focus-visible:ring-offset-2 disabled:opacity-50 disabled:pointer-events-none shadow-sm hover:shadow-md active:scale-95 min-h-touch min-w-touch",
  {
    variants: {
      variant: {
        default: "bg-primary text-white hover:bg-primary-dark font-semibold hover:animate-pulse-subtle",
        destructive: "bg-error text-white hover:bg-error/90 font-semibold hover:animate-bounce-subtle",
        outline: "border border-border bg-background hover:bg-background-alt text-text-primary font-medium hover:border-primary/50",
        secondary: "bg-background-alt text-text-primary hover:bg-background-alt/80 font-medium",
        ghost: "hover:bg-background-alt hover:text-text-primary text-text-primary",
        link: "text-primary underline-offset-4 hover:underline font-medium hover:text-primary-dark",
      },
      size: {
        default: "h-10 py-2 px-4 text-base xs:text-sm",
        sm: "h-9 px-3 rounded-md text-sm xs:text-xs",
        lg: "h-12 px-8 rounded-md text-lg xs:h-11 xs:text-base",
        icon: "h-10 w-10 xs:h-12 xs:w-12",
        touch: "h-12 px-6 text-base", // Optimized for mobile touch
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