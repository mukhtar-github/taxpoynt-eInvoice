import React from 'react';
import { cva, type VariantProps } from 'class-variance-authority';

const dividerVariants = cva(
  "border-t border-border w-full my-4",
  {
    variants: {
      variant: {
        default: "border-border",
        subtle: "border-border/50",
        light: "border-border/30",
      },
      size: {
        default: "my-4",
        sm: "my-2",
        lg: "my-6",
      },
    },
    defaultVariants: {
      variant: "default",
      size: "default",
    },
  }
);

export interface DividerProps
  extends React.HTMLAttributes<HTMLHRElement>,
    VariantProps<typeof dividerVariants> {}

const Divider: React.FC<DividerProps> = ({ 
  className, 
  variant, 
  size,
  ...props 
}) => {
  return (
    <hr
      className={dividerVariants({ variant, size, className })}
      {...props}
    />
  );
};

Divider.displayName = "Divider";

export { Divider, dividerVariants };
