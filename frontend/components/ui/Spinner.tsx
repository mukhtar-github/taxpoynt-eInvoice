import React from 'react';
import { cva, type VariantProps } from 'class-variance-authority';

// Define spinner variants using class-variance-authority
const spinnerVariants = cva(
  "animate-spin rounded-full border-current border-t-transparent",
  {
    variants: {
      size: {
        xs: "h-3 w-3 border-[2px]",
        sm: "h-4 w-4 border-[2px]",
        md: "h-6 w-6 border-[2px]",
        lg: "h-8 w-8 border-[3px]",
        xl: "h-12 w-12 border-[3px]",
      },
      variant: {
        default: "text-primary",
        primary: "text-primary",
        secondary: "text-text-secondary",
        white: "text-white",
      },
    },
    defaultVariants: {
      size: "md",
      variant: "default",
    },
  }
);

export interface SpinnerProps extends React.HTMLAttributes<HTMLDivElement>, VariantProps<typeof spinnerVariants> {
  label?: string;
  center?: boolean;
}

/**
 * Spinner component for loading states
 */
export const Spinner: React.FC<SpinnerProps> = ({
  size,
  variant,
  label,
  center = false,
  className,
  ...props
}) => {
  const spinner = (
    <div
      role="status"
      aria-label={label || "Loading"}
      className={spinnerVariants({ size, variant, className })}
      {...props}
    >
      {label && <span className="sr-only">{label}</span>}
    </div>
  );

  if (center) {
    return (
      <div className="flex justify-center items-center w-full">
        {spinner}
      </div>
    );
  }

  return spinner;
};

export default Spinner;
