import React, { HTMLAttributes, forwardRef } from 'react';
import { cva, type VariantProps } from 'class-variance-authority';
import { cn } from '../../utils/cn';

/**
 * Typography Component
 * 
 * This component system provides consistent typography throughout the application.
 * It uses Inter for headings and Source Sans Pro for body text as specified in the 
 * core typography requirements.
 */

// Heading variants
const headingVariants = cva(
  "font-heading text-text-primary tracking-tight",
  {
    variants: {
      level: {
        h1: "text-4xl font-semibold",
        h2: "text-3xl font-semibold",
        h3: "text-2xl font-semibold",
        h4: "text-xl font-semibold",
        h5: "text-lg font-medium",
        h6: "text-base font-medium",
      },
      weight: {
        light: "font-light",
        normal: "font-normal",
        medium: "font-medium",
        semibold: "font-semibold",
        bold: "font-bold",
      },
    },
    defaultVariants: {
      level: "h1",
    },
  }
);

export interface HeadingProps
  extends HTMLAttributes<HTMLHeadingElement>,
    VariantProps<typeof headingVariants> {
  as?: 'h1' | 'h2' | 'h3' | 'h4' | 'h5' | 'h6';
}

export const Heading = forwardRef<HTMLHeadingElement, HeadingProps>(
  ({ className, level, weight, as, ...props }, ref) => {
    const Component = as || (level as any) || 'h1';
    
    return (
      <Component
        className={cn(headingVariants({ level, weight, className }))}
        ref={ref}
        {...props}
      />
    );
  }
);

Heading.displayName = "Heading";

// Text variants
const textVariants = cva(
  "font-body text-text-primary",
  {
    variants: {
      size: {
        xs: "text-xs",
        sm: "text-sm",
        base: "text-base",
        lg: "text-lg",
        xl: "text-xl",
      },
      weight: {
        light: "font-light",
        normal: "font-normal",
        medium: "font-medium",
        semibold: "font-semibold",
        bold: "font-bold",
      },
      variant: {
        default: "text-text-primary",
        secondary: "text-text-secondary",
        muted: "text-text-muted",
        success: "text-success",
        error: "text-error",
        warning: "text-warning",
        info: "text-info",
      },
    },
    defaultVariants: {
      size: "base",
      weight: "normal",
      variant: "default",
    },
  }
);

export interface TextProps
  extends HTMLAttributes<HTMLParagraphElement>,
    VariantProps<typeof textVariants> {
  as?: 'p' | 'span' | 'div';
}

export const Text = forwardRef<HTMLParagraphElement, TextProps>(
  ({ className, size, weight, variant, as = 'p', ...props }, ref) => {
    const Component = as as any;
    
    return (
      <Component
        className={cn(textVariants({ size, weight, variant, className }))}
        ref={ref}
        {...props}
      />
    );
  }
);

Text.displayName = "Text";

// Label variants
const labelVariants = cva(
  "font-body block",
  {
    variants: {
      size: {
        sm: "text-xs",
        base: "text-sm",
        lg: "text-base",
      },
      variant: {
        default: "text-text-primary",
        secondary: "text-text-secondary",
      },
      weight: {
        normal: "font-normal",
        medium: "font-medium",
        semibold: "font-semibold",
      },
    },
    defaultVariants: {
      size: "base",
      variant: "default",
      weight: "medium",
    },
  }
);

export interface LabelProps
  extends HTMLAttributes<HTMLLabelElement>,
    VariantProps<typeof labelVariants> {
  htmlFor?: string;
  required?: boolean;
}

export const Label = forwardRef<HTMLLabelElement, LabelProps>(
  ({ className, size, variant, weight, required, ...props }, ref) => {
    return (
      <label
        className={cn(labelVariants({ size, variant, weight, className }))}
        ref={ref}
        {...props}
      >
        {props.children}
        {required && <span className="text-error ml-1">*</span>}
      </label>
    );
  }
);

Label.displayName = "Label";

// Export all typography components
export const Typography = {
  Heading,
  Text,
  Label,
};

export default Typography;
