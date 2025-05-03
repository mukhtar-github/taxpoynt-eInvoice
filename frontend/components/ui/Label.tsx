import React, { LabelHTMLAttributes, forwardRef } from 'react';
import { cva, type VariantProps } from 'class-variance-authority';

const labelVariants = cva(
  "text-sm font-medium leading-none peer-disabled:cursor-not-allowed peer-disabled:opacity-70",
  {
    variants: {
      size: {
        default: "text-sm",
        sm: "text-xs",
        lg: "text-base",
      },
    },
    defaultVariants: {
      size: "default",
    },
  }
);

export interface LabelProps
  extends LabelHTMLAttributes<HTMLLabelElement>,
    VariantProps<typeof labelVariants> {
  isRequired?: boolean;
}

const Label = forwardRef<HTMLLabelElement, LabelProps>(
  ({ className, size, isRequired, children, ...props }, ref) => {
    return (
      <label
        className={labelVariants({ size, className })}
        ref={ref}
        {...props}
      >
        {children}
        {isRequired && <span className="ml-1 text-error">*</span>}
      </label>
    );
  }
);

Label.displayName = "Label";

export { Label, labelVariants };
